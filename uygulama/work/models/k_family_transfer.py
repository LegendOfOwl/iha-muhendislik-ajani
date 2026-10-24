"""New dimensional tasks, fixed generation settings, unchanged model outputs."""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from benchmark import run_command
from validate_geometry import response,mesh_metrics
ROOT=Path(__file__).resolve().parents[2]
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=str),encoding='utf-8')
def digest(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    cases=[
      {'id':'wide_box','prompt':'rectangular solid box exactly 72 mm long, 24 mm wide and 5 mm high, centered at the origin. No holes.',
       'bbox_mm':[72,24,5],'volume_mm3':72*24*5,'center_at_origin':True},
      {'id':'compact_box','prompt':'rectangular solid box exactly 19 mm long, 17 mm wide and 11 mm high, centered at the origin. No holes.',
       'bbox_mm':[19,17,11],'volume_mm3':19*17*11,'center_at_origin':True},
      {'id':'centered_plate','prompt':'rectangular plate exactly 60 mm along X, 40 mm along Y and 6 mm thick along Z, centered at the origin, with one 8 mm diameter cylindrical through-hole along Z at X=0, Y=0.',
       'bbox_mm':[60,40,6],'volume_mm3':60*40*6-math.pi*4**2*6,'center_at_origin':True,
       'probes_mm':[[0,0,-2.4],[0,0,0],[0,0,2.4],[3.6,0,0],[4.4,0,0],[24,0,0]],'expected_inside':[False,False,False,False,True,True]},
      {'id':'offset_plate','prompt':'rectangular plate exactly 54 mm along X, 36 mm along Y and 4 mm thick along Z. The rectangular plate is centered at the origin. It has one 6 mm diameter cylindrical through-hole along Z whose center is at X=12 mm, Y=0 mm.',
       'bbox_mm':[54,36,4],'volume_mm3':54*36*4-math.pi*3**2*4,'center_at_origin':True,
       'probes_mm':[[12,0,-1.6],[12,0,0],[12,0,1.6],[14.7,0,0],[15.3,0,0],[0,0,0]],'expected_inside':[False,False,False,False,True,True]},
      {'id':'double_plate','prompt':'rectangular plate exactly 60 mm along X, 24 mm along Y and 4 mm thick along Z, centered at the origin, with two separate 4 mm diameter cylindrical through-holes along Z. The hole centers are at X=-15 mm,Y=0 mm and X=15 mm,Y=0 mm.',
       'bbox_mm':[60,24,4],'volume_mm3':60*24*4-2*math.pi*2**2*4,'center_at_origin':True,
       'probes_mm':[[-15,0,-1.6],[-15,0,0],[-15,0,1.6],[15,0,-1.6],[15,0,0],[15,0,1.6],[0,0,0],[17.3,0,0]],'expected_inside':[False]*6+[True,True]},
      {'id':'new_spacer','prompt':'cylindrical spacer exactly 7 mm high along Z, 26 mm outer diameter and one concentric 10 mm diameter through-hole along Z. The spacer is centered at the origin on all three axes.',
       'bbox_mm':[26,26,7],'volume_mm3':math.pi*(13**2-5**2)*7,'center_at_origin':True,
       'probes_mm':[[0,0,-2.8],[0,0,0],[0,0,2.8],[4.5,0,0],[5.5,0,0],[12,0,0],[13.5,0,0]],'expected_inside':[False,False,False,False,True,True,False]},
    ]
    run=ROOT/'outputs/simulations'/('k_transfer_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    k=json.loads((ROOT/'work/setup/k_model_install.json').read_text())
    new=json.loads((ROOT/'work/setup/cadmonkey32_install.json').read_text())
    models={'k1b':{'path':k['model']['path'],'sha256':k['model']['sha256']},'cadmonkey32':{'path':new['model_path'],'sha256':new['sha256']}}
    for m in models.values(): assert digest(m['path'])==m['sha256']
    protocol={'started_utc':datetime.now(timezone.utc).isoformat(),'cases':cases,'models':models,
        'settings':{'temperature':0,'seed':42,'context':4096,'max_tokens':1024,'gpu_layers':99},
        'prefix':'hey cadmonkey, create me a ','suffix':' Output only OpenSCAD code.',
        'generated_code_modified':False,'training_set_overlap':'unknown; these are new local tasks, not certified held-out training examples',
        'acceptance':'bbox and volume <1% error, origin centering <0.001 mm, finite interior/exterior probes, closed manifold STL',
        'limitations':['Six simple parts, not a broad benchmark','Probe points and total volume do not establish complete shape equivalence','No human correction or best-of-N selection'],
        'script_sha256':digest(__file__),'validator_sha256':digest(ROOT/'work/models/validate_geometry.py')}
    save(run/'protocol.json',protocol); results=[]
    for name,meta in models.items():
        for case in cases:
            folder=run/f'{name}_{case["id"]}'; folder.mkdir()
            prompt=protocol['prefix']+case['prompt']+protocol['suffix']
            command=[ROOT/'tools/llama-cad/llama-cli.exe','-m',meta['path'],'-p',prompt,'-c','4096','-n','1024','-ngl','99','-t','6','--temp','0','--seed','42','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--jinja']
            row={'model':name,'case':case['id'],'folder':str(folder),'prompt':prompt}
            try:
                code,seconds=run_command(command,folder)
                raw=(folder/'stdout.txt').read_text(encoding='utf-8',errors='replace'); generated=response(raw)
                row.update(inference_exit_code=code,seconds=seconds)
                match=re.search(r'Generation:\s*([\d.]+) t/s',raw)
                row['reported_generation_tok_s']=float(match[1]) if match else None
                (folder/'generated.scad').write_text(generated,encoding='utf-8')
                if code or not generated.strip(): raise ValueError('Inference failed or empty response')
                if re.search(r'\b(import|surface|include|use)\b',re.sub(r'//[^\n]*','',generated)): raise ValueError('External-file operation rejected')
                with (folder/'openscad.log').open('w',encoding='utf-8') as log:
                    proc=subprocess.run([k['executable'],'-o',str(folder/'generated.stl'),str(folder/'generated.scad')],cwd=folder,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
                row['openscad_exit_code']=proc.returncode
                row['warnings']=[s for s in (folder/'openscad.log').read_text(errors='replace').splitlines() if 'WARNING' in s or 'ERROR' in s]
                if proc.returncode or not (folder/'generated.stl').exists(): raise ValueError('STL export failed')
                row.update(mesh_metrics(folder/'generated.stl',case)); row['CAD_created']=True
            except Exception as e: row.update(CAD_created=False,geometry_accepted=False,error=f'{type(e).__name__}: {e}')
            results.append(row); save(run/'results_in_progress.json',results)
            print(name,case['id'],'geometry=',row['geometry_accepted'],flush=True)
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(r.get('inference_exit_code')==0 for r in results),
         'quality_passed':all(r['geometry_accepted'] for r in results),'results':results,'protocol':protocol,'run_directory':str(run),
         'summary':[{'model':m,'trials':len([r for r in results if r['model']==m]),'accepted':sum(r['geometry_accepted'] for r in results if r['model']==m)} for m in models]}
    save(run/'study_results.json',obj); save(ROOT/'outputs/reports/k_family_new_tasks.json',obj)
    print(json.dumps(obj['summary']),flush=True)
    return 0 if obj['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
