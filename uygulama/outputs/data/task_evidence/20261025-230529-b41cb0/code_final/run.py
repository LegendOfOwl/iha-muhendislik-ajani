from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native,memory
import csv,math,os,sys

def history(folder):
    p=folder/'history.csv'
    if not p.exists():return []
    with p.open() as f:
        rows=list(csv.DictReader(f,skipinitialspace=True))
    return [{k.strip(' "'):float(v) for k,v in row.items()} for row in rows]

def freeze(role):
    folder=CASE/role;target=folder/'prediction_frozen.json';assert not target.exists()
    h=history(folder);fields=[]
    for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')]:
        fields.append({int(p.stem.rsplit('_',1)[-1]) for p in folder.glob(f'{prefix}_*.{ext}') if p.stem.rsplit('_',1)[-1].isdigit()})
    common=set.intersection(*fields)&{int(r['Inner_Iter']) for r in h};matched=None
    if common:
        i=max(common);row=next(r for r in h if r['Inner_Iter']==i);tail=[r for r in h if i-99<=r['Inner_Iter']<=i]
        matched={'field_iteration':i,'terminal_history_iteration':int(h[-1]['Inner_Iter']),**{k:row[k] for k in ['CL','CD','rms[Rho]','rms[nu]']},
            'last100_samples':len(tail),'CD_last100_range':max(r['CD'] for r in tail)-min(r['CD'] for r in tail)}
        assert all(math.isfinite(v) for v in matched.values())
    result={'created_utc':now(),'not_blind':True,'matched':matched,'native_status':read(folder/'solver.status.json'),
        'contract_sha256':sha(CASE/'contract.json'),'plan_sha256':sha(CASE/'plan.json'),
        'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in folder.iterdir() if p.is_file()},
        'mesh_sha256':read(CASE/'plan.json')['cases'][role]['mesh_sha256'],'new_reference_score_accessed':False}
    save(target,result);print('FROZEN',role,matched,flush=True)
    return result

def run(role):
    plan=read(CASE/'plan.json');contract=read(CASE/'contract.json');c=plan['cases'][role];folder=ROOT/c['folder']
    assert sha(CASE/'contract.json')==plan['contract_sha256']
    assert sha(ROOT/c['mesh'])==c['mesh_sha256'] and sha(folder/'case.cfg')==c['cfg_sha256']
    if role!='smoke':
        smoke=read(CASE/'smoke/prediction_frozen.json');assert smoke['matched'] and smoke['native_status']['exit_code']==0
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
    print('START',role,memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',contract['budgets']['seconds'][role],env,memory_cap_gib=2.5)
    print('END',role,status,flush=True);frozen=freeze(role)
    if role=='smoke':assert status['exit_code']==0 and frozen['matched'],'Preserve parser/smoke failure before changes'

if __name__=='__main__':
    for role in (['smoke','coarse','medium','fine'] if sys.argv[1]=='all' else [sys.argv[1]]):run(role)
