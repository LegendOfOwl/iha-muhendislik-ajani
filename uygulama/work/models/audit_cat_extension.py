"""Check whether upstream cat demonstrations were simply cut by token budget."""
from datetime import datetime,timezone
import json
from pathlib import Path
from benchmark import run_command
from validate_geometry import response
from audit_usage import export,save
ROOT=Path(__file__).resolve().parents[2]
def main():
    run=ROOT/'outputs/simulations'/('cat_budget_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    k=json.loads((ROOT/'work/setup/k_model_install.json').read_text()); n=json.loads((ROOT/'work/setup/cadmonkey32_install.json').read_text())
    rows=[]
    for name,model in [('k1b',k['model']['path']),('cadmonkey32',n['model_path'])]:
        folder=run/name; folder.mkdir()
        command=[ROOT/'tools/llama-cad/llama-cli.exe','-m',model,'-p','Hey cadmonkey, make me a cat','-c','12288','-n','8192','-ngl','99','-t','6','--seed','42','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--jinja','--log-verbosity','3']
        row={'model':name,'folder':str(folder),'context':12288,'max_tokens':8192,'note':'Larger budget than initial 2048-token short demo; no engineering dimension acceptance'}
        try:
            code,seconds=run_command(command,folder); row.update(inference_exit_code=code,seconds=seconds)
            generated=response((folder/'stdout.txt').read_text(encoding='utf-8',errors='replace')); (folder/'generated.scad').write_text(generated,encoding='utf-8')
            row['openscad_exit_code']=export(folder,folder/'generated.scad',folder/'generated.stl',k['executable'])
            row['CAD_created']=row['openscad_exit_code']==0 and (folder/'generated.stl').exists()
        except Exception as e: row.update(CAD_created=False,error=f'{type(e).__name__}: {e}')
        rows.append(row); print(json.dumps(row),flush=True)
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'results':rows,'run_directory':str(run),'scope':'Token-budget diagnostic; STL existence does not verify cat appearance or geometry.'}
    save(run/'results.json',obj); save(ROOT/'outputs/reports/cat_budget_audit.json',obj)
    return 0 if all(r.get('inference_exit_code')==0 for r in rows) else 1
if __name__=='__main__': raise SystemExit(main())
