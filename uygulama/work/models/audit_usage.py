"""Audit upstream prompt/template/sampling/rendering choices without repairing outputs."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from benchmark import K_CASES,run_command
from validate_geometry import response,mesh_metrics
ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False,default=str),encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def export(folder,source,target,exe):
    command=[exe,'-o',str(target),'-D','$fn=100','-D','$fs=0.1','-D','$fa=1',str(source)]
    save(folder/'openscad_command.json',command)
    with (folder/'openscad.log').open('w',encoding='utf-8') as log:
        p=subprocess.run(command,cwd=folder,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
    return p.returncode
def main():
    run=ROOT/'outputs/simulations'/('usage_audit_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    k=read(ROOT/'work/setup/k_model_install.json'); new=read(ROOT/'work/setup/cadmonkey32_install.json')
    models={'k1b':k['model']['path'],'cadmonkey32':new['model_path']}
    strict=['--temp','.8','--top-p','.95','--top-k','64','--min-p','0','--repeat-penalty','1.1','--repeat-last-n','4096','--samplers','penalties;temperature;top_k;top_p']
    transfer=read(ROOT/'outputs/reports/k_family_new_tasks.json'); study=read(ROOT/'outputs/reports/k_family_study.json')
    template=ROOT/'work/research/k1b_deep/k_chat_template.jinja'
    protocol={'started_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':sha(__file__),
      'models':{n:{'path':p,'sha256':sha(p)} for n,p in models.items()},
      'sources':['https://github.com/ThomasVuNguyen/MakeMe/blob/main/main.go','https://github.com/ThomasVuNguyen/K/blob/main/train/train.py','https://github.com/ThomasVuNguyen/K/blob/main/train/config.json'],
      'strict_sampling_flags':strict,'external_template_sha256':sha(template),
      'rendering_flags':['-D','$fn=100','-D','$fs=0.1','-D','$fa=1'],
      'limits':['Native Q8 runtime, not exact BF16 Hugging Face/Unsloth reproduction','Random sequences differ between llama.cpp and Transformers even with same seed','Short demo render success is not object or dimensional correctness','No generated program manually changed']}
    save(run/'protocol.json',protocol); results=[]
    def trial(model,group,case,prompt,flags,seed=42,reference=None):
        folder=run/f'{model}_{group}_{seed}_{case}'; folder.mkdir()
        command=[ROOT/'tools/llama-cad/llama-cli.exe','-m',models[model],'-p',prompt,'-c','4096','-n','2048','-ngl','99','-t','6','--seed',str(seed),'--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--jinja']+flags
        row={'model':model,'group':group,'case':case,'seed':seed,'prompt':prompt,'folder':str(folder)}
        try:
            code,seconds=run_command(command,folder); row.update(inference_exit_code=code,seconds=seconds)
            generated=response((folder/'stdout.txt').read_text(encoding='utf-8',errors='replace'))
            (folder/'generated.scad').write_text(generated,encoding='utf-8')
            if code or not generated.strip(): raise ValueError('Inference failed or empty response')
            if re.search(r'\b(import|surface|include|use)\b',re.sub(r'//[^\n]*','',generated)): raise ValueError('External file operation rejected')
            row['openscad_exit_code']=export(folder,folder/'generated.scad',folder/'generated.stl',k['executable'])
            row['CAD_created']=row['openscad_exit_code']==0 and (folder/'generated.stl').exists()
            if not row['CAD_created']: raise ValueError('STL export failed')
            if reference: row.update(mesh_metrics(folder/'generated.stl',reference))
            if group=='external_template':
                original=next(r for r in study['results'] if r['model']==model and r['mode']=='training_prefix' and r['case']==case)
                original_code=(Path(original['folder'])/'generated.scad').read_text(encoding='utf-8')
                row['matches_metadata_template_output']=generated.strip()==original_code.strip()
        except Exception as e: row.update(CAD_created=False,geometry_accepted=False,error=f'{type(e).__name__}: {e}')
        results.append(row); save(run/'results_in_progress.json',results)
        print(model,group,case,seed,'CAD=',row['CAD_created'],'geometry=',row.get('geometry_accepted'),flush=True)
    for model in models:
        # Actual README examples, actual MakeMe prefix, runtime defaults preserved.
        for name in ['a box','a coffee mug','a cat']:
            trial(model,'upstream_demo',name.replace(' ','_'),'Hey cadmonkey, make me '+name,[])
        # Match the current training recipe more closely, disabling native extra samplers.
        for seed in [42,43]:
            for case in K_CASES:
                prompt='hey cadmonkey, create me a '+re.sub(r'^an?\s+','',case['prompt'])
                trial(model,'recipe_sampling',case['id'],prompt,strict,seed,case)
        # Remove the request to output code: upstream recipe does not add that suffix.
        for case in transfer['protocol']['cases']:
            trial(model,'no_output_suffix',case['id'],'hey cadmonkey, create me a '+case['prompt'],['--temp','0'],42,case)
        case=K_CASES[0]; prompt='hey cadmonkey, create me a '+re.sub(r'^an?\s+','',case['prompt'])
        trial(model,'external_template','box',prompt,['--temp','0','--chat-template-file',str(template),'--verbose-prompt','--log-verbosity','3'],42,case)
    replay=[]
    for previous in study['results']+transfer['results']:
        ref=(next(c for c in K_CASES if c['id']==previous['case']) if previous in study['results'] else next(c for c in transfer['protocol']['cases'] if c['id']==previous['case']))
        folder=run/'rerender'/Path(previous['folder']).name; folder.mkdir(parents=True)
        row={'source_folder':previous['folder'],'case':previous['case'],'model':previous['model'],'previous_accepted':previous['geometry_accepted']}
        try:
            row['exit_code']=export(folder,Path(previous['folder'])/'generated.scad',folder/'official_resolution.stl',k['executable'])
            if row['exit_code']: raise ValueError('Official-resolution STL export failed')
            row.update(mesh_metrics(folder/'official_resolution.stl',ref))
        except Exception as e: row.update(geometry_accepted=False,error=str(e))
        replay.append(row)
    summary=[]
    for model in models:
        for group in ['upstream_demo','recipe_sampling','no_output_suffix','external_template']:
            rows=[r for r in results if r['model']==model and r['group']==group]
            summary.append({'model':model,'group':group,'trials':len(rows),'CAD_created':sum(r['CAD_created'] for r in rows),
                'geometry_accepted':None if group=='upstream_demo' else sum(r.get('geometry_accepted',False) for r in rows)})
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(r.get('inference_exit_code')==0 for r in results),
      'quality_passed':all(r.get('geometry_accepted',False) for r in results if r['group']!='upstream_demo'),
      'results':results,'summary':summary,'resolution_replay':replay,'resolution_changed_acceptance':[r for r in replay if r['previous_accepted']!=r['geometry_accepted']],
      'external_template_outputs_match':all(r.get('matches_metadata_template_output') for r in results if r['group']=='external_template'),
      'run_directory':str(run),'protocol':protocol}
    save(run/'audit_results.json',obj); save(ROOT/'outputs/reports/model_usage_audit.json',obj)
    print(json.dumps({'summary':summary,'template_parity':obj['external_template_outputs_match'],'resolution_changes':len(obj['resolution_changed_acceptance'])},indent=2))
    return 0 if obj['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
