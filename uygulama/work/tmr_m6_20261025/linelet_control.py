"""A source-motivated line-normal preconditioner test, not a parameter sweep."""
from common import ROOT,CASE,PROJECT,read,save,sha,now,run_native
from run_flow import rows
import numpy as np
import os
import shutil


def main():
    root=CASE/'medium_linelet_pair';assert not root.exists();root.mkdir()
    source=CASE/'flow_v2_medium';seal=read(source/'prediction_frozen.json');i=seal['matched']['field_iteration'];assert i==2400
    seed=source/f'restart_flow_{i:06d}.dat'
    text=(source/'case.cfg').read_text().replace('RESTART_SOL= NO','RESTART_SOL= YES').replace('SOLUTION_FILENAME= restart_flow','SOLUTION_FILENAME= seed')
    text=text.replace('ITER= 4000','ITER= 200').replace('MESH_FILENAME= ../mesh_family_budget_v3/','MESH_FILENAME= ../../mesh_family_budget_v3/')
    cases={}
    for name,prec in [('lusgs','LU_SGS'),('linelet','LINELET')]:
        f=root/name;f.mkdir();cfg=text.replace('LINEAR_SOLVER_PREC= LU_SGS','LINEAR_SOLVER_PREC= '+prec)
        (f/'case.cfg').write_text(cfg,encoding='utf-8');shutil.copyfile(seed,f/'seed.dat')
        cases[name]={'cfg_sha256':sha(f/'case.cfg'),'seed_sha256':sha(f/'seed.dat')}
    assert cases['lusgs']['seed_sha256']==cases['linelet']['seed_sha256']
    diffs=[(a,b) for a,b in zip((root/'lusgs/case.cfg').read_text().splitlines(),(root/'linelet/case.cfg').read_text().splitlines()) if a!=b]
    assert diffs==[('LINEAR_SOLVER_PREC= LU_SGS','LINEAR_SOLVER_PREC= LINELET')]
    plan={'created_utc':now(),'source_seed_sha256':sha(seed),'source_field_iteration':i,'source_mesh_sha256':read(CASE/'flow_plan_v2.json')['cases']['medium']['mesh_sha256'],
          'only_config_change':diffs,'cases':cases,'source':'https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/',
          'mechanism':'Solve wall-normal tridiagonal linelets to address highly anisotropic layer coupling; Jacobi elsewhere. Different from merely raising the inner iteration cap.',
          'iterations':200,'budget_seconds_each':180,'threads_each':4,'common_comparison_iteration':199,
          'primary_nonlinear_effect_log10_min':.3,'secondary_Krylov_work_ratio_max':.8,
          'secondary_requires_both_median_linear_residual_log10_below':-5.,
          'cost_warning':'Krylov iterations are a work proxy, not equal per-iteration cost or measured speedup. Other CFD jobs may run concurrently.',
          'physical_and_acceptance_unchanged':True}
    save(root/'contract.json',plan)
    results={}
    for name in ['lusgs','linelet']:
        f=root/name;exe=read(ROOT/'work/setup/su2_install.json')['executable'];env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
        print('START linelet control',name,flush=True)
        status=run_native([exe,'case.cfg','-t','4'],f,'solver',180,env,memory_cap_gib=.6)
        history=rows(f/'history.csv') if (f/'history.csv').exists() else [];common=next((x for x in history if x['Inner_Iter']==199),None)
        tail=history[-100:]
        sets=[]
        for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')]:
            sets.append({int(p.stem.rsplit('_',1)[1]) for p in f.glob(f'{prefix}_*.{ext}') if p.stem.rsplit('_',1)[1].isdigit()})
        fields=set.intersection(*sets)&{int(x['Inner_Iter']) for x in history}
        result={'native':status,'common_history':common,'matched_field_iteration':max(fields) if fields else None,
                'total_Krylov_iterations':sum(x['Linear_Solver_Iterations'] for x in history),
                'last100_linear_residual_log10_median':float(np.median([x['LinSolRes'] for x in tail])) if tail else None}
        save(f/'prediction_frozen.json',{'frozen_utc':now(),'contract_sha256':sha(root/'contract.json'),
            'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in f.iterdir() if p.is_file()},'result':result,
            'not_blind':True,'no_new_reference_scores_yet':True,'physical_qualification_passed':False})
        results[name]=result;print('END linelet control',name,status,flush=True)
    a=results['lusgs'];b=results['linelet'];gain=None;ratio=None;secondary=False
    if a['common_history'] is not None and b['common_history'] is not None:
        gain=a['common_history']['rms[Rho]']-b['common_history']['rms[Rho]']
        ratio=b['total_Krylov_iterations']/a['total_Krylov_iterations']
        secondary=ratio<=.8 and a['last100_linear_residual_log10_median']< -5 and b['last100_linear_residual_log10_median']< -5
    save(PROJECT/'reports/tmr_linelet_control_20261025.json',{'created_utc':now(),'contract_sha256':sha(root/'contract.json'),
         'results':results,'additional_density_log10_reduction':gain,'primary_effect_passed':gain is not None and gain>=.3,
         'Krylov_iteration_ratio':ratio,'secondary_work_proxy_effect_passed':secondary,
         'physical_qualification_passed':False,'timing_speedup_not_claimed':True})
    print({'density_gain':gain,'Krylov_iteration_ratio':ratio,'secondary_effect':secondary},flush=True)


if __name__=='__main__':main()
