"""Second blinded numerical revision; never mutates v1 artifacts."""
from pathlib import Path
import os,sys,json,subprocess,time,hashlib,shutil,re
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02';SIM=OUT/'simulations'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcfg(p):
    d={}
    for l in Path(p).read_text().splitlines():
        l=l.split('%')[0].strip()
        if '=' in l:k,v=l.split('=',1);d[k.strip()]=v.strip()
    return d
def prepare(name,mesh=None,seed=None,method='JST_MAT',iterations=6000,base=None,more=None):
    assert name.startswith('v2_')
    folder=SIM/name;folder.mkdir(parents=True,exist_ok=True)
    if (folder/'run_status.json').exists():raise RuntimeError('Never overwrite an executed attempt: '+name)
    base=Path(base) if base else SIM/'medium_far/case.cfg';d=readcfg(base);original=d.copy()
    if mesh:shutil.copy2(mesh,folder/'mesh.su2')
    if seed:
        ext=Path(seed).suffix;shutil.copy2(seed,folder/('seed'+ext))
        d['SOLUTION_FILENAME']='seed';d['READ_BINARY_RESTART']='YES' if ext=='.dat' else 'NO';d['RESTART_SOL']='YES'
    else:d['RESTART_SOL']='NO'
    d.update({'ITER':str(iterations),'CONV_NUM_METHOD_FLOW':method,'ENTROPY_FIX_COEFF':'0.05','CENTRAL_JACOBIAN_FIX_FACTOR':'4.0','WRT_RESTART_OVERWRITE':'NO','WRT_SURFACE_OVERWRITE':'NO','WRT_VOLUME_OVERWRITE':'NO','EXT_ITER_OFFSET':'0'})
    if more:d.update({k:str(v) for k,v in more.items()})
    # Reynolds/temperature initialization and all physical conditions remain the authoritative v1 values.
    physical=['SOLVER','KIND_TURB_MODEL','SA_OPTIONS','KIND_TRANS_MODEL','MACH_NUMBER','AOA','REYNOLDS_NUMBER','REYNOLDS_LENGTH','FREESTREAM_TEMPERATURE','GAMMA_VALUE','GAS_CONSTANT','MU_REF','MU_T_REF','SUTHERLAND_CONSTANT','FREESTREAM_TURB2LAMVISCRATIO','MARKER_HEATFLUX','MARKER_FAR','REF_AREA','REF_LENGTH']
    assert all(d[k]==original[k] for k in physical)
    (folder/'case.cfg').write_text('\n'.join(f'{k}= {v}' for k,v in d.items())+'\n')
    manifest={'base_config':str(base.relative_to(ROOT)),'base_config_sha256':sha(base),'config_sha256':sha(folder/'case.cfg'),'physical_fields_unchanged':True,'mesh_sha256':sha(folder/'mesh.su2'),'seed_source':str(Path(seed).relative_to(ROOT)) if seed else None,'seed_source_sha256':sha(seed) if seed else None,'overrides':{k:{'base':original.get(k),'new':v} for k,v in d.items() if original.get(k)!=v},'method_reference':'https://su2code.github.io/docs_v7/Convective-Schemes/','numerical_rationale':'Test matrix JST dissipation on the same own flow/restart after scalar JST grid drag differences. No expected result or experimental target is used. ENTROPY_FIX0.05 is the lower documented recommended matrix range, held identical in JST control (inactive there). Jacobian fix4 and bounded adaptive CFL1..6 are unchanged.'}
    (folder/'configuration_overrides.json').write_text(json.dumps(manifest,indent=2));return folder
def execute(name,budget=1800):
    folder=SIM/name;exe=Path(json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'])
    env=os.environ.copy();env['OMP_NUM_THREADS']='4';env['OMP_WAIT_POLICY']='PASSIVE';start=time.monotonic();t0=time.time()
    with (folder/'solver.log').open('w',encoding='utf-8') as log:
        p=subprocess.Popen([str(exe),'case.cfg','-t','4'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,env=env)
        (folder/'process.json').write_text(json.dumps({'pid':p.pid,'start_epoch':t0,'budget_s':budget}))
        try:code=p.wait(timeout=budget);status='exited'
        except subprocess.TimeoutExpired:p.kill();p.wait();code=None;status='timeout_partial_preserved'
    meta={'status':status,'exit_code':code,'wall_seconds':time.monotonic()-start,'start_epoch':t0,'iteration_budget':int(readcfg(folder/'case.cfg')['ITER']),'time_budget_seconds':budget,'threads':4,'config_sha256':sha(folder/'case.cfg'),'mesh_sha256':sha(folder/'mesh.su2'),'executable_sha256':sha(exe),'checkpoint_frequency':200,'overwrite':False}
    (folder/'run_status.json').write_text(json.dumps(meta,indent=2));print(name,json.dumps(meta),flush=True);return meta
def diagnostics():
    src=SIM/'medium_far'
    for name,method,it,budget in [('v2_diag_jst','JST',800,350),('v2_diag_mat','JST_MAT',3000,1000)]:
        prepare(name,src/'mesh.su2',src/'restart_flow.dat',method,it)
        execute(name,budget)
if __name__=='__main__':
    if sys.argv[1]=='diagnostics':diagnostics()
    else:execute(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 1800)
