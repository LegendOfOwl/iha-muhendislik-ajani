"""A one-step explicit RHS observation; never a substitute convergence solution."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder
import urllib.request,sys,os,shutil

PROBE=CASE/'residual_probe_20261026_v1'
SOURCES=ROOT/'work/flatplate_20261026/residual_sources'
PATHS=['SU2_CFD/include/solvers/CFVMFlowSolverBase.hpp','SU2_CFD/include/solvers/CScalarSolver.inl',
       'SU2_CFD/src/solvers/CSolver.cpp','SU2_CFD/src/output/CFlowCompOutput.cpp',
       'Common/src/CConfig.cpp','Common/src/linear_algebra/CSysSolve.cpp']

def sources():
    assert not SOURCES.exists();SOURCES.mkdir(parents=True)
    manifest=[]
    for path in PATHS:
        url='https://raw.githubusercontent.com/su2code/SU2/v8.5.0/'+path
        request=urllib.request.Request(url,headers={'User-Agent':'UAV-engineering-source-audit'})
        with urllib.request.urlopen(request,timeout=40) as response:data=response.read();final=response.url
        f=SOURCES/path.rsplit('/',1)[-1];f.write_bytes(data)
        manifest.append({'url':url,'final_url':final,'fetched_utc':now(),'path':str(f.relative_to(ROOT)),'sha256':sha(f),'bytes':len(data)})
    save(SOURCES/'manifest.json',manifest);print({'source_files':len(manifest)},flush=True)

def prepare():
    assert not PROBE.exists()
    parent=CASE/'reduced_family_20261026_v1/fine';seal=read(parent/'prediction_frozen.json')
    for p,h in seal['files_sha256'].items():assert sha(ROOT/p)==h,p
    for row in read(SOURCES/'manifest.json'):assert sha(ROOT/row['path'])==row['sha256']
    seed=parent/'restart_flow_003999.dat';mesh=CASE/'meshes/fine.su2'
    text=(parent/'case.cfg').read_text();changes={
      'ITER= 4000':'ITER= 1','CFL_NUMBER= 100':'CFL_NUMBER= 1e-6','CFL_ADAPT= YES':'CFL_ADAPT= NO',
      'TIME_DISCRE_FLOW= EULER_IMPLICIT':'TIME_DISCRE_FLOW= EULER_EXPLICIT',
      'TIME_DISCRE_TURB= EULER_IMPLICIT':'TIME_DISCRE_TURB= EULER_EXPLICIT',
      'OUTPUT_WRT_FREQ= (200,200,200,200)':'OUTPUT_WRT_FREQ= (1,1,1,1)',
      'HISTORY_OUTPUT= (ITER,RMS_RES,AERO_COEFF,LINSOL,CFL_NUMBER)':'HISTORY_OUTPUT= (ITER,RMS_RES,MAX_RES,AERO_COEFF,LINSOL,CFL_NUMBER)',
      'VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE)':'VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE,RESIDUAL)'}
    for old,new in changes.items():assert text.splitlines().count(old)==1; text=text.replace(old+'\n',new+'\n')
    folder=PROBE/'explicit';folder.mkdir(parents=True);(folder/'case.cfg').write_text(text,encoding='utf-8');shutil.copyfile(seed,folder/'seed.dat')
    code=folder/'runner_code';code.mkdir();files=[BASE/n for n in ['prepare_residual_probe.py','prepare.py','run.py','cfl_control.py','scaled_restart.py']]+[ROOT/'work/tmr_m6_20261025/common.py']
    for p in files:shutil.copyfile(p,code/p.name)
    save(folder/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in files}})
    rects=[('leading_edge',-.02,.05,0,.05),('near_wall',0,2,0,.02),('upstream',-.33333,0,0,1),
       ('inlet_strip',-.33333,-.32333,0,1),('outlet_strip',1.98,2,0,1),('top_strip',-.33333,2,.98,1),
       ('aft_boundary_layer',.5,2,0,.05),('outer_core',0,1.98,.05,.98)]
    exe=ROOT/read(ROOT/'work/setup/su2_install.json')['executable']
    contract={'created_utc':now(),'purpose':'Check that explicit exported RHS matches cached native RMS/MAX before using spatial residual diagnostics.',
      'not_blind':True,'not_a_convergence_control':True,'native_folder':'explicit','seed_path':str(seed.relative_to(ROOT)),'seed_sha256':sha(seed),
      'mesh_path':str(mesh.relative_to(ROOT)),'mesh_sha256':sha(mesh),'config_sha256':sha(folder/'case.cfg'),
      'source_manifest':str((SOURCES/'manifest.json').relative_to(ROOT)),'source_manifest_sha256':sha(SOURCES/'manifest.json'),
      'parent_seal_sha256':sha(parent/'prediction_frozen.json'),'physical_contract_sha256':sha(CASE/'contract.json'),
      'native_executable_sha256':sha(exe),'native_version':'8.5.0','parent_changes':changes,
      'iterations':1,'seconds':60,'threads':4,'CFL':1e-6,'MGLEVEL':0,'no_automatic_retry':True,
      'gates':{'residual_log10_error_max':1e-6,'coordinate_mapping_max_m':2e-7,
        'conservative_global_relative_drift_max':2e-6,'expected_points':52689,'all5_RMS_and_MAX_required':True},
      'gate_rationale':'Same native RHS exported float32 vs cached double reductions;1e-6log margin exceeds float32 normal rounding and history decimal print. Drift uses per-variable L2 ratio from native double restart, not VTU quantization.',
      'owned_domain':'Native one-rank OpenMP sourceSU2 mesh has52689 domain points and no halos; owned wall/BC nodes included, no volume weighting.',
      'drift_definition':'Native restart0 vs seed: each density,momentum_x,momentum_y,energy L2 difference divided by its seed L2. Max of4 must be below bound; nu_tilde separately reported.',
      'regions':[dict(name=n,x_min=a,x_max=b,y_min=c,y_max=d) for n,a,b,c,d in rects],
      'regions_overlap':True,'stage_semantics':'Flow RHS precedes flow explicit update; SA RHS follows flow update and precedes SA update. Cached stage observation, not recomputed residual of final output state.',
      'physical_qualification_passed':False,'M6_qualification_passed':False}
    save(PROBE/'contract.json',contract)
    taskpath=ROOT/read(CASE/'inner_cap_20261026_v1/task.json')['path'];task=read(taskpath)
    task.update(phase='kaynakla gerekçeli tek-adım residual ölçümü',probe_contract=str((PROBE/'contract.json').relative_to(ROOT)),probe_contract_sha256=sha(PROBE/'contract.json'))
    save(taskpath,task);print({'prepared':str(PROBE),'gates':contract['gates']},flush=True)

def run():
    c=read(PROBE/'contract.json');folder=PROBE/'explicit';assert not (folder/'solver.process.json').exists()
    for key,p in [('config_sha256',folder/'case.cfg'),('seed_sha256',folder/'seed.dat'),('mesh_sha256',ROOT/c['mesh_path']),('source_manifest_sha256',ROOT/c['source_manifest'])]:assert sha(p)==c[key]
    for p,h in read(folder/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/p)==h
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];assert sha(ROOT/exe)==c['native_executable_sha256']
    print('START explicit probe',memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',c['seconds'],dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=2.5)
    seal=freeze_folder(folder,PROBE/'contract.json',ROOT/c['mesh_path']);print('FROZEN',status,seal['matched'],flush=True)

if __name__=='__main__':{'sources':sources,'prepare':prepare,'run':run}[sys.argv[1]]()
