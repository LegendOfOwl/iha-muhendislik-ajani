"""Versioned native runs for researched mesh studies; never alter frozen v2."""
from pathlib import Path
import sys,json,hashlib,os,subprocess,time,importlib.util,shutil
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def prepare(name,seed=None,more=None):
    assert name.startswith('v3_');folder=OUT/'simulations'/name
    assert (folder/'mesh.su2').exists()
    assert not (folder/'case.cfg').exists(),'Never overwrite a prepared attempt'
    base=OUT/'simulations/v2_r2_medium/case.cfg';helper=load('readcfg_only',ROOT/'work/blind_validation/solver_v2/solve.py');d=helper.readcfg(base);original=d.copy()
    d['RESTART_SOL']='NO';d['SOLUTION_FILENAME']='solution';d['ITER']='10000'
    if seed:
        seed=Path(seed)
        if seed.resolve()!=(folder/'seed.dat').resolve():shutil.copy2(seed,folder/'seed.dat')
        d.update(RESTART_SOL='YES',SOLUTION_FILENAME='seed',READ_BINARY_RESTART='YES')
    if more:d.update({k:str(v) for k,v in more.items()})
    physical=['SOLVER','KIND_TURB_MODEL','SA_OPTIONS','KIND_TRANS_MODEL','MACH_NUMBER','AOA','FREESTREAM_TEMPERATURE','REYNOLDS_NUMBER','REYNOLDS_LENGTH','REF_AREA','REF_LENGTH','MARKER_HEATFLUX','MARKER_FAR','GAMMA_VALUE','GAS_CONSTANT','FREESTREAM_NU_FACTOR']
    assert all(d[k]==original[k] for k in physical)
    (folder/'case.cfg').write_text('\n'.join(f'{k}= {v}' for k,v in d.items())+'\n')
    (folder/'configuration_overrides.json').write_text(json.dumps({'base_config':str(base.relative_to(ROOT)),'base_sha256':sha(base),'mesh_sha256':sha(folder/'mesh.su2'),'config_sha256':sha(folder/'case.cfg'),'overrides':{k:{'base':original.get(k),'new':v} for k,v in d.items() if original.get(k)!=v},'physical_fields_unchanged':True,'contract_sha256':sha(ROOT/'work/blind_validation/contract.json'),'seed_path':str(seed) if seed else None,'seed_sha256':sha(seed) if seed else None,'rationale':'Same v2 RANS/SA numerical method on a research-motivated source-preserving explicit C-block. Target forces and Cp not provided to native solver; main agent knows earlier evaluation so this is not a new independent blind trial.'},indent=2))
def run(name,budget):
    folder=OUT/'simulations'/name;assert not (folder/'process.json').exists(),'Never overwrite an executed attempt'
    exe=Path(json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable']);env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
    t=time.monotonic();epoch=time.time()
    with (folder/'solver.log').open('w',encoding='utf-8') as f:
        p=subprocess.Popen([str(exe),'case.cfg','-t','4'],cwd=folder,stdout=f,stderr=subprocess.STDOUT,env=env)
        (folder/'process.json').write_text(json.dumps({'pid':p.pid,'budget_seconds':budget,'start_epoch':epoch}))
        try:code=p.wait(timeout=budget);status='exited'
        except subprocess.TimeoutExpired:p.kill();p.wait();code=None;status='timeout_partial_preserved'
    a={'name':name,'status':status,'exit_code':code,'seconds':time.monotonic()-t,'start_epoch':epoch,'threads':4,'config_sha256':sha(folder/'case.cfg'),'mesh_sha256':sha(folder/'mesh.su2'),'executable_sha256':sha(exe)}
    (folder/'run_status.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
def post(name):
    helper=load('audited_checkpoint_post',ROOT/'work/blind_validation/solver_v2/postprocess.py');helper.process(name)
if __name__=='__main__':
    mode,name=sys.argv[1:3]
    if mode=='prepare':prepare(name,seed=OUT/'simulations'/name/'seed.dat' if '--seed-existing' in sys.argv else None)
    elif mode=='run':run(name,int(sys.argv[3]) if len(sys.argv)>3 else 1800)
    elif mode=='post':post(name)
