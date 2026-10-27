"""One preregistered additive-preconditioner partition test; four OpenMP threads remain."""
from pathlib import Path
import sys,os,shutil,math
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/flatplate_20261025'))
from prepare import CASE as OLD,read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder,evaluate
from scaled_restart import dimensional_matched
from linear_work_control import work
from run import history
PAIR=ROOT/'outputs/simulations/flatplate_20261027_v1/prec_partition'
REPORT=ROOT/'outputs/reports/prec_partition_control_20261027.json'

def decide(quality,work_ratio,time_ratio,e):
    def number(x):return not isinstance(x,bool) and isinstance(x,(int,float)) and math.isfinite(x) and x>=0
    valid=number(work_ratio) and number(time_ratio)
    checks={'matched_pair':quality['comparable'],'density_and_SA_effect':quality['effect_passed'],
      'finite_nonnegative_cost':valid,'Krylov_work':valid and work_ratio<=e['work_ratio_max'],
      'observed_elapsed':valid and time_ratio<=e['observed_time_ratio_max']}
    return {'checks':checks,'effect_passed':all(checks.values()),'physical_qualification_passed':False}

def prepare():
    assert not PAIR.exists();parent=OLD/'inner_cap_20261026_v1/cap40';s=read(parent/'prediction_frozen.json')
    for p,h in s['files_sha256'].items():assert sha(ROOT/p)==h,p
    coverage=read(ROOT/'outputs/reports/linelet_coverage_20261027.json');assert coverage['native_membership_accepted']
    text=(parent/'case.cfg').read_text();assert 'LINEAR_SOLVER_PREC_THREADS' not in text
    cases={};files=[Path(__file__),ROOT/'work/flatplate_20261025/prepare.py',ROOT/'work/flatplate_20261025/run.py',
      ROOT/'work/flatplate_20261025/cfl_control.py',ROOT/'work/flatplate_20261025/scaled_restart.py',
      ROOT/'work/flatplate_20261025/linear_work_control.py',ROOT/'work/tmr_m6_20261025/common.py',ROOT/'work/reliability/paired_control.py']
    for name,value in [('auto4',0),('single',1)]:
        f=PAIR/name;f.mkdir(parents=True);mesh=OLD/'meshes/fine.su2'
        rel=os.path.relpath(mesh,f).replace('\\','/')
        cfg=text.replace('MESH_FILENAME= ../../meshes/fine.su2','MESH_FILENAME= '+rel)
        cfg+='LINEAR_SOLVER_PREC_THREADS= '+str(value)+'\n'
        (f/'case.cfg').write_text(cfg,encoding='utf-8');shutil.copyfile(parent/'seed.dat',f/'seed.dat')
        code=f/'runner_code';code.mkdir()
        for p in files:shutil.copyfile(p,code/p.name)
        save(f/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in files}})
        cases[name]={'config_sha256':sha(f/'case.cfg'),'seed_sha256':sha(f/'seed.dat')}
    a,b=[(PAIR/n/'case.cfg').read_text().splitlines() for n in cases]
    diff=[(x,y) for x,y in zip(a,b) if x!=y];assert len(a)==len(b) and diff==[('LINEAR_SOLVER_PREC_THREADS= 0','LINEAR_SOLVER_PREC_THREADS= 1')]
    anchors=[ROOT/'work/flatplate_20261026/residual_sources/CConfig.cpp',ROOT/'work/flatplate_20261026/linelet_sources/CSysMatrix.cpp']
    c={'created_utc':now(),'not_blind':True,'source_config':str((parent/'case.cfg').relative_to(ROOT)),'source_seal_sha256':sha(parent/'prediction_frozen.json'),
      'seed_sha256':sha(parent/'seed.dat'),'mesh':str(mesh.relative_to(ROOT)),'mesh_sha256':sha(mesh),'cases':cases,'only_config_difference':diff,
      'source_anchors_sha256':{str(p.relative_to(ROOT)):sha(p) for p in anchors},
      'source_coverage_report_sha256':sha(ROOT/'outputs/reports/linelet_coverage_20261027.json'),
      'hypothesis':'Removing additive LU_SGS thread partitions may recover neglected cross-partition triangular coupling; localization/linelet coverage alone does not prove this cause.',
      'source_semantics':'CSysMatrix uses maxOpenMPThreads when PREC_THREADS=0, value1 gives one triangular domain; LowerProduct/UpperProduct are bounded by partition begin/end.',
      'unchanged':'Native-t4 and OMP_NUM_THREADS4, LU_SGS40, inner1e-3, same adaptive policy, source geometry/mesh/physics, fresh sameNDseed. Applies flow andSA.',
      'common_mesh_path_alias':'Relative filename remap only; mesh bytes unchanged.',
      'iterations':200,'comparison_iteration':199,'seconds_each':240,'threads_each':4,'max_working_set_GiB':2.5,
      'effect':{'density_gain_min':.3,'SA_worsening_max':.1,'work_ratio_max':1.5,'observed_time_ratio_max':1.5},
      'cost_rationale':'Serializing triangular sweeps can reduce iteration count but increase elapsed time; both cost gates registered before native runs. Single pair timing only, no general speedup claim.',
      'no_parameter_sweep_or_automatic_extension':True,'physical_qualification_passed':False,'M6_qualification_passed':False}
    save(PAIR/'contract.json',c)
    tpath=ROOT/read(BASE/'task.json')['path'];t=read(tpath);t.update(phase='tek değişkenli önkoşullayıcı bölünme kontrolü',partition_contract=str((PAIR/'contract.json').relative_to(ROOT)),partition_contract_sha256=sha(PAIR/'contract.json'));save(tpath,t)
    print({'registered':str(PAIR),'resources':memory()},flush=True)

def run(name):
    c=read(PAIR/'contract.json');f=PAIR/name;assert not (f/'solver.process.json').exists()
    assert sha(f/'case.cfg')==c['cases'][name]['config_sha256'] and sha(f/'seed.dat')==c['seed_sha256'] and sha(ROOT/c['mesh'])==c['mesh_sha256']
    for p,h in c['source_anchors_sha256'].items():assert sha(ROOT/p)==h
    for p,h in read(f/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/p)==h
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];print('START',name,memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],f,'solver',c['seconds_each'],dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=c['max_working_set_GiB'])
    s=freeze_folder(f,PAIR/'contract.json',ROOT/c['mesh']);print('FROZEN',name,status,s['matched'],flush=True)

def compare():
    c=read(PAIR/'contract.json');e=c['effect'];free=read(OLD/'contract.json')['derived_freestream'];raw=[read(PAIR/n/'prediction_frozen.json') for n in c['cases']];verified=0
    for s in raw:
        for p,h in s['files_sha256'].items():assert sha(ROOT/p)==h,p;verified+=1
    si=[dimensional_matched(s,free) for s in raw]
    q=evaluate(*si,c['comparison_iteration'],e['density_gain_min'],e['SA_worsening_max'],normalizations=('SI2D','SI2D'))
    counts=[work(history(PAIR/n),199) for n in c['cases']] if q['comparable'] else [None,None]
    ratio=counts[1]['total']/counts[0]['total'] if q['comparable'] else None
    timing=raw[1]['native_status']['seconds']/raw[0]['native_status']['seconds'] if q['comparable'] else None
    r={'reviewed_utc':now(),'contract_sha256':sha(PAIR/'contract.json'),'raw':raw,'SI':si,'quality':q,'work_counts':counts,'work_ratio':ratio,'observed_time_ratio':timing,
      'verified_file_records':verified,**decide(q,ratio,timing,e),'runtime_partition_count_directly_exported':False,
      'limits':['Native config accepted; partition semantics inferred from matched release source, not runtime partition array instrumentation.',
       'Same adaptive policy, not forced same CFL trajectory.','One source grid and seed, all physical gates unchanged.']}
    save(REPORT,r);print({k:r[k] for k in ['quality','work_ratio','observed_time_ratio','checks','effect_passed']},flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run(sys.argv[2])
    elif sys.argv[1]=='compare':compare()
    else:raise ValueError(sys.argv[1])
