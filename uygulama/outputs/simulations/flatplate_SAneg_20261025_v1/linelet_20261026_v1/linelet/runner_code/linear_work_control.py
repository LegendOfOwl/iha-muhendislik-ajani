"""Execute the registered linear-tolerance work test with unchanged physical gates."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native,memory
from run import history
from cfl_control import freeze_folder,evaluate
from scaled_restart import dimensional_matched
import sys,os,shutil,math

PAIR=CASE/'linear_work_20261026_v1'
REGISTERED=CASE/'next_linear_work_control_not_run.json'
REPORT=ROOT/'outputs/reports/flatplate_linear_work_20261026.json'

def prepare():
    assert not PAIR.exists()
    prior=read(REGISTERED);baseline=ROOT/prior['baseline']
    assert sha(baseline/'prediction_frozen.json')==prior['baseline_seal_sha256']
    for p,h in read(baseline/'prediction_frozen.json')['files_sha256'].items():assert sha(ROOT/p)==h,p
    assert sha(baseline/'seed.dat')==prior['seed_sha256'] and sha(CASE/'meshes/medium.su2')==prior['mesh_sha256']
    folder=PAIR/'reduced';folder.mkdir(parents=True)
    text=(baseline/'case.cfg').read_text();old='LINEAR_SOLVER_ERROR= 1e-06';assert text.splitlines().count(old)==1
    target=text.replace(old,'LINEAR_SOLVER_ERROR= 0.001')
    assert [(a,b) for a,b in zip(text.splitlines(),target.splitlines()) if a!=b]==[(old,'LINEAR_SOLVER_ERROR= 0.001')]
    (folder/'case.cfg').write_text(target,encoding='utf-8');shutil.copyfile(baseline/'seed.dat',folder/'seed.dat')
    code=folder/'runner_code';code.mkdir()
    files=[BASE/n for n in ['linear_work_control.py','prepare.py','cfl_control.py','run.py','scaled_restart.py']]
    files += [ROOT/'work/reliability/paired_control.py',ROOT/'work/tmr_m6_20261025/common.py']
    for p in files:shutil.copyfile(p,code/p.name)
    save(folder/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in files}})
    save(PAIR/'contract.json',{'created_utc':now(),'registered_sha256':sha(REGISTERED),'registered':prior,
       'config_sha256':sha(folder/'case.cfg'),'only_config_difference':[(old,'LINEAR_SOLVER_ERROR= 0.001')],
       'same_seed_bytes':True,'same_mesh_physics_and_normalization':True,'not_blind':True,
       'physical_acceptance_contract_sha256':sha(CASE/'contract.json')})
    sys.path.insert(0,str(ROOT/'work/agent'))
    from project import make_task
    from learning import instruction_snapshot
    path=make_task('Ön kayıtlı iç doğrusal tolerans kontrolü: aynı seed/ağda Krylov işi ve SI kalıntı farkı',kind='qualification',project_id='qualification')
    task=read(path);task.update(status='çalışıyor',phase='kayıtlı maliyet hipotezi',
       applied_lesson_ids=['L04','L05','L08','L09','L10','R01','R03'],agent_instruction_snapshot=instruction_snapshot(ROOT),
       acceptance=['Yalnız LINEAR_SOLVER_ERROR değişsin; eski mühürler korunsun','200 ortak adım ve gerçek OS çıkışı','Krylov işi≤%70; SI kalıntı kötüleşmesi≤0.05log; |CD farkı|<1e-7'],
       contract=str((PAIR/'contract.json').relative_to(ROOT)),contract_sha256=sha(PAIR/'contract.json'))
    save(path,task);save(PAIR/'task.json',{'path':str(path.relative_to(ROOT))});print({'prepared':str(PAIR),'resources':memory()},flush=True)

def run():
    c=read(PAIR/'contract.json');p=c['registered'];folder=PAIR/'reduced'
    assert not (folder/'solver.process.json').exists()
    assert sha(REGISTERED)==c['registered_sha256'] and sha(folder/'case.cfg')==c['config_sha256']
    assert sha(folder/'seed.dat')==p['seed_sha256'] and sha(CASE/'meshes/medium.su2')==p['mesh_sha256']
    for f,h in read(folder/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/f)==h
    exe=read(ROOT/'work/setup/su2_install.json')['executable']
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',p['seconds'],
       dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=2.5)
    seal=freeze_folder(folder,PAIR/'contract.json',CASE/'meshes/medium.su2')
    print('FROZEN',status,seal['matched'],flush=True)

def work(rows,iteration):
    rows=[r for r in rows if r['Inner_Iter']<=iteration]
    assert [r['Inner_Iter'] for r in rows]==list(range(iteration+1))
    values=[r[k] for r in rows for k in ['Linear_Solver_Iterations','LinSolIterTurb']]
    assert all(math.isfinite(x) and x>=0 and x==int(x) for x in values)
    return {'flow':sum(int(r['Linear_Solver_Iterations']) for r in rows),
            'SA':sum(int(r['LinSolIterTurb']) for r in rows),'total':int(sum(values))}

def decision(comparable,ratio,rho_worse,sa_worse,cd_diff,limits):
    values=[ratio,rho_worse,sa_worse,cd_diff]
    finite=all(x is not None and math.isfinite(x) for x in values)
    checks={'complete_matched_pair':bool(comparable),'finite_metrics':finite,
       'Krylov_work':finite and ratio<=limits['total_flow_plus_SA_Krylov_iterations_ratio_max'],
       'density':finite and rho_worse<=limits['density_and_SA_SI_log10_worsening_max'],
       'SA':finite and sa_worse<=limits['density_and_SA_SI_log10_worsening_max'],
       'CD':finite and cd_diff<limits['absolute_CD_difference_max']}
    return {'checks':checks,'effect_passed':all(checks.values()),'physical_qualification_passed':False}

def compare():
    c=read(PAIR/'contract.json');p=c['registered'];baseline=ROOT/p['baseline'];folder=PAIR/'reduced'
    raw=[read(f/'prediction_frozen.json') for f in [baseline,folder]];verified=0
    for s in raw:
        for f,h in s['files_sha256'].items():assert sha(ROOT/f)==h;verified+=1
    free=read(CASE/'contract.json')['derived_freestream'];a,b=[dimensional_matched(s,free) for s in raw]
    quality=evaluate(a,b,p['comparison_iteration'],-.05,.05,normalizations=('SI2D','SI2D'))
    works=[work(history(f),p['comparison_iteration']) for f in [baseline,folder]] if quality['comparable'] else [None,None]
    ratio=works[1]['total']/works[0]['total'] if quality['comparable'] else None
    rho=-quality['density_log10_gain'] if quality['comparable'] else None
    sa=quality['SA_log10_worsening'];cd=abs(b['matched']['CD']-a['matched']['CD']) if quality['comparable'] else None
    result={'reviewed_utc':now(),'contract_sha256':sha(PAIR/'contract.json'),'baseline_raw':raw[0],'reduced_raw':raw[1],
       'baseline_SI':a,'reduced_SI':b,'quality':quality,'work_counts':works,'work_ratio':ratio,
       'density_log10_worsening':rho,'SA_log10_worsening':sa,'absolute_CD_difference':cd,'verified_file_records':verified,
       **decision(quality['comparable'],ratio,rho,sa,cd,p['effect']),
       'wall_seconds_observed':[s['native_status']['seconds'] for s in raw],
       'limits':['Single paired seed and medium grid, no general speedup claim.','Physical accuracy and three-grid acceptance unchanged.']}
    save(REPORT,result);print({k:result[k] for k in ['work_counts','work_ratio','density_log10_worsening','SA_log10_worsening','absolute_CD_difference','effect_passed']},flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run,'compare':compare}[sys.argv[1]]()
