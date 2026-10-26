"""Execute the preregistered40/80 inner-iteration control, once per arm."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder,evaluate
from scaled_restart import dimensional_matched
from linear_work_control import work
from run import history
import sys,os,shutil,math

PAIR=CASE/'inner_cap_20261026_v1'
REGISTERED=CASE/'next_inner_cap_control_not_run_20261026.json'
REPORT=ROOT/'outputs/reports/flatplate_inner_cap_20261026.json'

def decide(quality,ratio,limit):
    valid=not isinstance(ratio,bool) and isinstance(ratio,(int,float)) and math.isfinite(ratio) and ratio>=0
    checks={'matched_pair':quality['comparable'],'density_and_SA':quality['effect_passed'],
       'finite_work':valid,'total_Krylov_work':valid and ratio<=limit}
    return {'checks':checks,'effect_passed':all(checks.values()),'physical_qualification_passed':False}

def prepare():
    assert not PAIR.exists()
    p=read(REGISTERED);seed=ROOT/p['seed'];parent=seed.parent
    old=read(parent/'prediction_frozen.json')
    for f,h in old['files_sha256'].items():assert sha(ROOT/f)==h,f
    assert sha(seed)==p['seed_sha256'] and sha(CASE/'meshes/fine.su2')==p['mesh_sha256']
    source=(parent/'case.cfg').read_text();assert 'REF_DIMENSIONALIZATION= '+p['seed_normalization'] in source
    assert source.splitlines().count('ITER= 4000')==1
    source=source.replace('ITER= 4000\n','ITER= 200\n');PAIR.mkdir()
    files=[BASE/n for n in ['inner_cap_control.py','prepare.py','run.py','cfl_control.py','scaled_restart.py','linear_work_control.py']]
    files += [ROOT/'work/reliability/paired_control.py',ROOT/'work/tmr_m6_20261025/common.py']
    cases={}
    for name,cap in [('cap40',40),('cap80',80)]:
        folder=PAIR/name;folder.mkdir();assert source.splitlines().count('LINEAR_SOLVER_ITER= 40')==1
        (folder/'case.cfg').write_text(source.replace('LINEAR_SOLVER_ITER= 40\n',f'LINEAR_SOLVER_ITER= {cap}\n'),encoding='utf-8')
        shutil.copyfile(seed,folder/'seed.dat');code=folder/'runner_code';code.mkdir()
        for f in files:shutil.copyfile(f,code/f.name)
        save(folder/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/f.name).relative_to(ROOT)):sha(code/f.name) for f in files}})
        cases[name]={'config_sha256':sha(folder/'case.cfg'),'seed_sha256':sha(folder/'seed.dat')}
    a,b=[(PAIR/n/'case.cfg').read_text().splitlines() for n in cases]
    diff=[(x,y) for x,y in zip(a,b) if x!=y]
    assert len(a)==len(b) and diff==[('LINEAR_SOLVER_ITER= 40','LINEAR_SOLVER_ITER= 80')]
    contract={'created_utc':now(),'registered_plan':str(REGISTERED.relative_to(ROOT)),'registered_plan_sha256':sha(REGISTERED),
       'registered':p,'cases':cases,'only_config_difference':diff,'same_seed_bytes':True,'same_mesh_and_physics':True,
       'physical_contract_sha256':sha(CASE/'contract.json'),'parent_seal_sha256':sha(parent/'prediction_frozen.json'),
       'common_parent_changes':{'ITER':'4000→200','seed':'parent complete field3999, same ND bytes for both arms'},
       'adaptive_policy':'Same policy and starting CFL; cap changes may mediate later CFL trajectories. This is not a fixed-CFL cap-only mechanism proof.',
       'not_blind':True,'no_automatic_extension':True}
    save(PAIR/'contract.json',contract)
    sys.path.insert(0,str(ROOT/'work/agent'))
    from project import make_task
    from learning import instruction_snapshot
    taskpath=make_task('İnce kaynak ağda ön kayıtlı iç çözücü40/80 kontrolü ve bağımsız kaynak incelemesi',kind='qualification',project_id='qualification')
    task=read(taskpath);task.update(status='çalışıyor',phase='kayıtlı40/80 kontrolü',
      acceptance=['Aynı ND seed/ağ/fizik ve yalnız LINEAR_SOLVER_ITER farkı','İki200-adımlık180s kol; ortak tam alan199',
         'SI yoğunluk kazancı≥0.3log; SA kötüleşmesi≤0.1log; toplam Krylov oranı≤1.5','Etkiyi2B aile/fizik/M6 kabulünden ayır'],
      applied_lesson_ids=['L04','L05','L08','L09','L10','R01','R03'],agent_instruction_snapshot=instruction_snapshot(ROOT),
      contract=str((PAIR/'contract.json').relative_to(ROOT)),contract_sha256=sha(PAIR/'contract.json'))
    save(taskpath,task);save(PAIR/'task.json',{'path':str(taskpath.relative_to(ROOT))})
    print({'prepared':str(PAIR),'task':str(taskpath),'resources':memory()},flush=True)

def run(name):
    c=read(PAIR/'contract.json');p=c['registered'];folder=PAIR/name
    assert not (folder/'solver.process.json').exists()
    assert sha(REGISTERED)==c['registered_plan_sha256'] and sha(CASE/'contract.json')==c['physical_contract_sha256']
    assert sha(folder/'case.cfg')==c['cases'][name]['config_sha256']
    assert sha(folder/'seed.dat')==p['seed_sha256'] and sha(CASE/'meshes/fine.su2')==p['mesh_sha256']
    for f,h in read(folder/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/f)==h,f
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];print('START',name,memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',p['per_arm_seconds'],
      dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=2.5)
    seal=freeze_folder(folder,PAIR/'contract.json',CASE/'meshes/fine.su2');print('FROZEN',name,status,seal['matched'],flush=True)

def compare():
    c=read(PAIR/'contract.json');p=c['registered'];limits=p['effect'];free=read(CASE/'contract.json')['derived_freestream']
    raw=[read(PAIR/n/'prediction_frozen.json') for n in c['cases']];verified=0
    for s in raw:
        for f,h in s['files_sha256'].items():assert sha(ROOT/f)==h,f;verified+=1
    a,b=[dimensional_matched(s,free) for s in raw]
    quality=evaluate(a,b,199,limits['SI_density_log10_gain_min'],limits['SI_SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    counts=[work(history(PAIR/n),199) for n in c['cases']] if quality['comparable'] else [None,None]
    ratio=counts[1]['total']/counts[0]['total'] if quality['comparable'] and counts[0]['total']>0 else None
    result={'reviewed_utc':now(),'contract_sha256':sha(PAIR/'contract.json'),'raw':raw,'SI':[a,b],'quality':quality,
       'work_counts':counts,'work_ratio':ratio,'verified_file_records':verified,**decide(quality,ratio,limits['total_Krylov_work_ratio_max']),
       'limits':['One fine grid and evolved restart; adaptive CFL is a mediator, not held trajectory.',
          'This does not replace the frozen three-grid family or change any physical gate.','Krylov count is a work proxy, not a universal wall-time speedup.']}
    save(REPORT,result);print({k:result[k] for k in ['quality','work_counts','work_ratio','checks','effect_passed']},flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run(sys.argv[2])
    elif sys.argv[1]=='compare':compare()
    else:raise ValueError(sys.argv[1])
