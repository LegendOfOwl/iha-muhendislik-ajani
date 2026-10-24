"""Controlled local CAD-model study: model/version, prompt style and sampling."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
from benchmark import K_CASES,run_command
from validate_geometry import response,mesh_metrics

def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf-8')
def main():
    run=ROOT/'outputs/simulations'/('k_family_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    run.mkdir(parents=True)
    k=json.loads((ROOT/'work/setup/k_model_install.json').read_text())
    new=json.loads((ROOT/'work/setup/cadmonkey32_install.json').read_text())
    models={'k1b':Path(k['model']['path']),'cadmonkey32':Path(new['model_path'])}
    identities={'k1b':{'revision':k['revision'],'sha256':k['model']['sha256']},
                'cadmonkey32':{'revision':new['revision'],'sha256':new['sha256']}}
    for name,p in models.items():
        with p.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
        assert sha==identities[name]['sha256']
    modes=[('baseline',0.,[42]),('training_prefix',0.,[42]),('training_sampled',.8,[42,43]),('explicit_rules',0.,[42])]
    protocol={'started_utc':datetime.now(timezone.utc).isoformat(),'scope':'Three synthetic geometric specifications, not broad accuracy benchmark',
        'models':identities,'cases':K_CASES,'modes':modes,'max_new_tokens':1024,'context_tokens':4096,
        'temperature_sampled':.8,'top_p':.95,'top_k':64,'sampled_repetition_penalty':1.1,
        'prompt_assembly':'For create-me-a prefix remove the case leading indefinite article; baseline preserves original MakeMe prompt',
        'acceptance':'Unchanged original bounding-box/volume 1%, requested centering 0.001 mm, bore point probes and closed STL',
        'rules':'Preserve all millimeter sizes exactly. Use d for a stated diameter, not r. Use difference to subtract through-holes. Use center=true on all axes when centered at the origin is requested. Return only OpenSCAD code.',
        'limits':['Only three small part specifications','Two seeds for sampled setting; no statistical reliability claim',
                  'No human changes to generated code','These variants are exploratory and evaluated on the same cases',
                  'Loading and file-cache state are not controlled performance variables']}
    save(run/'protocol.json',protocol)
    results=[]
    for model,path in models.items():
        for mode,temperature,seeds in modes:
            for seed in seeds:
                for case in K_CASES:
                    folder=run/f'{model}_{mode}_{seed}_{case["id"]}'; folder.mkdir()
                    prefix='Hey cadmonkey, make me ' if mode=='baseline' else 'hey cadmonkey, create me a '
                    description=case['prompt'] if mode=='baseline' else re.sub(r'^an?\s+', '', case['prompt'])
                    prompt=prefix+description
                    if mode=='explicit_rules': prompt+=' '+protocol['rules']
                    command=[ROOT/'tools/llama-cad/llama-cli.exe','-m',path,'-p',prompt,'-c','4096','-n','1024',
                             '-ngl','99','-t','6','--temp',str(temperature),'--seed',str(seed),
                             '--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--jinja']
                    if mode=='training_sampled': command+=['--top-p','.95','--top-k','64','--repeat-penalty','1.1']
                    row={'model':model,'mode':mode,'seed':seed,'case':case['id'],'folder':str(folder),'prompt':prompt,
                         'expected_bbox_mm':case['bbox_mm'],'expected_volume_mm3':case['volume_mm3']}
                    try:
                        code,seconds=run_command(command,folder)
                        raw=(folder/'stdout.txt').read_text(encoding='utf-8',errors='replace')
                        generated=response(raw)
                        row.update(inference_exit_code=code,seconds=seconds)
                        perf=re.search(r'Generation:\s*([\d.]+) t/s',raw)
                        row['reported_generation_tok_s']=float(perf[1]) if perf else None
                        (folder/'generated.scad').write_text(generated,encoding='utf-8')
                        if code: raise ValueError('Model process failed')
                        if not generated.strip(): raise ValueError('Empty model response')
                        if re.search(r'\b(import|surface|include|use)\b',re.sub(r'//[^\n]*','',generated)): raise ValueError('External-file OpenSCAD operation rejected')
                        with (folder/'openscad.log').open('w',encoding='utf-8') as log:
                            p=subprocess.run([k['executable'],'-o',str(folder/'generated.stl'),str(folder/'generated.scad')],
                                cwd=folder,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
                        row['openscad_exit_code']=p.returncode
                        log=(folder/'openscad.log').read_text(errors='replace')
                        row['warnings']=[line for line in log.splitlines() if 'WARNING' in line or 'ERROR' in line]
                        if p.returncode or not (folder/'generated.stl').exists(): raise ValueError('OpenSCAD could not export STL')
                        row.update(mesh_metrics(folder/'generated.stl',case))
                        row['CAD_created']=True
                    except Exception as exc:
                        row.update(CAD_created=False,geometry_accepted=False,error=f'{type(exc).__name__}: {exc}')
                    results.append(row)
                    save(run/'results_in_progress.json',results)
                    print(f'{model} {mode} s{seed} {case["id"]}: CAD={row["CAD_created"]}; geometry={row["geometry_accepted"]}',flush=True)
    summary=[]
    for model in models:
        for mode,_,_ in modes:
            group=[r for r in results if r['model']==model and r['mode']==mode]
            summary.append({'model':model,'mode':mode,'trials':len(group),
                            'CAD_created':sum(r['CAD_created'] for r in group),
                            'accepted':sum(r['geometry_accepted'] for r in group),
                            'case_results':[{key:r.get(key) for key in ['case','seed','geometry_accepted','error']} for r in group]})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(r.get('inference_exit_code')==0 for r in results),
            'quality_passed':all(r['geometry_accepted'] for r in results),
            'meaning_of_passed':'All scheduled native model processes completed; geometry acceptance is reported separately',
            'accepted_trials':sum(r['geometry_accepted'] for r in results),'total_trials':len(results),
            'results':results,'summary':summary,'protocol':protocol,'run_directory':str(run)}
    save(run/'study_results.json',result)
    save(ROOT/'outputs/reports/k_family_study.json',result)
    new.update(verified_inference=all(r.get('inference_exit_code')==0 for r in results if r['model']=='cadmonkey32'),
               acceptance_by_mode=[s for s in summary if s['model']=='cadmonkey32'],status='experimental; measured on three specifications',
               engineering_auto_use=False,last_test_report='outputs/reports/k_family_study.json')
    save(ROOT/'work/setup/cadmonkey32_install.json',new)
    print(json.dumps({'accepted':result['accepted_trials'],'trials':len(results),'summary':summary,'run':str(run)},ensure_ascii=False,indent=2),flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
