"""Mechanical snapshot of the analyst's completed automatic plan, including timeouts."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
    info=read(BASE/'project.json');out=ROOT/info['output_root'];snapshot=out/'reports/prediction_frozen.json'
    if snapshot.exists():raise ValueError('Already frozen; preserve prior snapshot')
    seal=read(BASE/'pre_analysis_seal.json');assert sha(BASE/'contract.json')==seal['contract_sha256']
    for name,h in seal['input_sha256'].items():assert sha(BASE/'analysis_input'/name)==h
    cases=[];digests={}
    for name in ['coarse','medium','fine','medium_far']:
        folder=out/'simulations'/name;m=read(folder/'prediction_metrics.json');status=read(folder/'run_status.json')
        for p in folder.glob('*'):
            if p.is_file():digests[str(p.relative_to(ROOT))]=sha(p)
        cases.append({'label':name,'folder':str(folder.relative_to(ROOT)),'surface_file':str((folder/'surface_flow.vtu').relative_to(ROOT)),'surface_sha256':sha(folder/'surface_flow.vtu'),'field_checkpoint_iteration':m['field_checkpoint_iteration'],'status':status,'numerical':{k:v for k,v in m.items() if k not in ['Cp_by_side','history_last','history_terminal']}})
    source={str(p.relative_to(ROOT)):sha(p) for p in (BASE/'solver').glob('*.py')}
    frozen={'timestamp':datetime.now(timezone.utc).isoformat(),'scope':'Agent-generated RAE2822 RANS plan; original four runs, two completed and two timed out with matched checkpoint fields','input_sha256':seal['input_sha256'],'contract_sha256':seal['contract_sha256'],'source_script_sha256':source,'case_files_sha256':digests,'cases':cases,'access_log_sha256':sha(BASE/'solver/access_log.json'),'autonomy_limit':'Analyst LLM hit account usage limit after automatic run suite. Reviewer mechanically sealed already-produced predictions, before experimental comparison; no new analyst inference or target fitting claimed.'}
    save(snapshot,frozen);save(BASE/'reviewer/review_manifest.json',{'cases':[{k:r[k] for k in ['label','folder','surface_file','surface_sha256']} for r in cases]})
    print(json.dumps({'snapshot':str(snapshot),'cases':len(cases),'sealed_files':len(digests),'script_files':len(source)}))
if __name__=='__main__':main()
