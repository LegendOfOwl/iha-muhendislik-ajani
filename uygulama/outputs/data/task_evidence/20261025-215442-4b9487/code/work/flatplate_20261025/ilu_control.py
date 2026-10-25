"""Source-motivated matched-seed high-CFL preconditioner test, before reference scoring."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native
from run import history
import shutil,os,numpy as np

def main():
    root=CASE/'ilu_pair';assert not root.exists();root.mkdir()
    seal=read(CASE/'medium/prediction_frozen.json');i=seal['matched']['field_iteration']
    seed=CASE/f'medium/restart_flow_{i:06d}.dat';source=(CASE/'medium/case.cfg').read_text()
    text=source.replace('RESTART_SOL= NO','RESTART_SOL= YES').replace('SOLUTION_FILENAME= restart_flow','SOLUTION_FILENAME= seed')
    text=text.replace('ITER= 8000','ITER= 200').replace('MESH_FILENAME= ../meshes/','MESH_FILENAME= ../../meshes/')
    text=text.replace('CONV_STARTITER= 200','CONV_STARTITER= 1000')
    cases={}
    for name,prec in [('lusgs','LU_SGS'),('ilu','ILU')]:
        folder=root/name;folder.mkdir();(folder/'case.cfg').write_text(text.replace('LINEAR_SOLVER_PREC= LU_SGS','LINEAR_SOLVER_PREC= '+prec),encoding='utf-8')
        shutil.copyfile(seed,folder/'seed.dat');cases[name]={'cfg_sha256':sha(folder/'case.cfg'),'seed_sha256':sha(folder/'seed.dat')}
    diff=[(a,b) for a,b in zip((root/'lusgs/case.cfg').read_text().splitlines(),(root/'ilu/case.cfg').read_text().splitlines()) if a!=b]
    assert diff==[('LINEAR_SOLVER_PREC= LU_SGS','LINEAR_SOLVER_PREC= ILU')]
    contract={'created_utc':now(),'source':'https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/',
       'mechanism':'High-CFL stiff linear systems: source documentation recommends ILU; LU_SGS histories reach40 cap with LinSolRes above tolerance.',
       'baseline_seal_sha256':sha(CASE/'medium/prediction_frozen.json'),'seed_iteration':i,'seed_sha256':sha(seed),'mesh_sha256':sha(CASE/'meshes/medium.su2'),
       'cases':cases,'only_config_difference':diff,'common_comparison_iteration':199,'iterations':200,'seconds_each':120,
       'effect_log10_gain_min':.3,'secondary_last100_linear_log10_median_max':-5,
       'conditional_next_step':'Only if nonlinear gain>=0.3 and ILU medianLinSolRes<-5, create explicitly registered same-physics ILU continuations on all three fixed mesh roles. No parameter sweep.',
       'no_timing_speedup_claim':True,'no_reference_target_access_yet':True,'physical_changes':None}
    save(root/'contract.json',contract);results={}
    for name in ['lusgs','ilu']:
        folder=root/name;exe=read(ROOT/'work/setup/su2_install.json')['executable'];env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
        status=run_native([exe,'case.cfg','-t','4'],folder,'solver',120,env,memory_cap_gib=.6)
        h=history(folder);row=next((r for r in h if r['Inner_Iter']==199),None)
        result={'native':status,'comparison':{k:row[k] for k in ['rms[Rho]','rms[nu]','CD']} if row else None,
           'median_last100_linear_log10':float(np.median([r['LinSolRes'] for r in h[-100:]])) if h else None,
           'Krylov_iterations_sum':sum(r['Linear_Solver_Iterations'] for r in h)}
        save(folder/'prediction_frozen.json',{'frozen_utc':now(),'contract_sha256':sha(root/'contract.json'),
           'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in folder.iterdir() if p.is_file()},'result':result,'not_blind':True})
        results[name]=result;print(name,result,flush=True)
    gain=None
    if all(v['comparison'] for v in results.values()):gain=results['lusgs']['comparison']['rms[Rho]']-results['ilu']['comparison']['rms[Rho]']
    effect=gain is not None and gain>=.3 and results['ilu']['median_last100_linear_log10']< -5
    save(ROOT/'outputs/reports/flatplate_ILU_control_20261025.json',{'created_utc':now(),'results':results,'density_log10_gain':gain,
        'effect_passed':effect,'contract_sha256':sha(root/'contract.json'),'no_timing_speedup_claim':True,'physical_qualification_passed':False})
    print({'gain':gain,'effect_passed':effect},flush=True)

if __name__=='__main__':main()
