"""Numerical stabilization from identical-grid native restarts; all first-run evidence retained."""
from copy import deepcopy
from datetime import datetime,timezone
import json,os,shutil,subprocess,time
from pathlib import Path
import numpy as np,pandas as pd
from run_m6 import ROOT,OUT,sha,save,replace
def main():
    old=json.loads((OUT/'reports/m6_rans_results.json').read_text());previous=Path(old['run_directory'])
    if not (previous/'initial_experiment_comparison.json').exists():shutil.copy2(OUT/'reports/m6_experiment_comparison.json',previous/'initial_experiment_comparison.json')
    run=OUT/'simulations'/('m6_rans_continue_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    shutil.copy2(Path(__file__),run/'continuation_program.py')
    changes={'CFL_NUMBER':20,'CFL_ADAPT':'NO','LINEAR_SOLVER_ITER':20,'LINEAR_SOLVER_ERROR':1e-6,'LIMITER_ITER':50,'ITER':500,'OUTPUT_WRT_FREQ':500,'RESTART_SOL':'YES','SOLUTION_FILENAME':'restart_flow.dat'}
    save(run/'continuation_contract.json',{'conditions':old['conditions'],'thresholds':old['thresholds'],'changes':changes,'note':'Only numerical controls/restart; no experiment fitting, no mesh or physical-condition change','conditions_sha256':old['conditions_sha256']})
    binary=json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'];rows=[]
    for source in old['results']:
        src=Path(source['folder']);dest=run/source['grid'];dest.mkdir()
        for name in ['mesh.su2','restart_flow.dat','case.cfg']:shutil.copy2(src/name,dest/name)
        assert sha(dest/'mesh.su2')==source['mesh']['mesh_sha256']
        cfg=(dest/'case.cfg').read_text()
        for k,v in changes.items():cfg=replace(cfg,k,v)
        (dest/'case.cfg').write_text(cfg);command=[binary,'case.cfg','-t','4'];save(dest/'command.json',command)
        row=deepcopy(source);row.update(folder=str(dest),restart_from=str(src),restart_input_sha256=sha(src/'restart_flow.dat'),numerical_changes=changes)
        print('M6_FIXED_CFL_CONTINUATION',source['grid'],flush=True);start=time.perf_counter()
        with (dest/'native.log').open('w',encoding='utf-8') as log:p=subprocess.run(command,cwd=dest,env=dict(os.environ,OMP_NUM_THREADS='4'),stdout=log,stderr=subprocess.STDOUT,timeout=900,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode:raise ValueError('Continuation failed; initial result unchanged, inspect '+str(dest/'native.log'))
        h=pd.read_csv(dest/'history.csv');h.columns=h.columns.str.strip().str.strip('"');last=h.iloc[-1];tail=h.tail(100)
        seconds=time.perf_counter()-start;row.update(seconds=seconds,total_native_seconds=source.get('total_native_seconds',source['seconds'])+seconds,CL=float(last['CL']),CD=float(last['CD']),log10_density_residual=float(last['rms[Rho]']),log10_turbulence_residual=float(last['rms[nu]']),iterations=len(h),first_run_iterations=source['iterations'],CL_tail_range=float(np.ptp(tail['CL'])),CD_tail_range=float(np.ptp(tail['CD'])))
        row['iterative_passed']=row['log10_density_residual']<-7 and row['CL_tail_range']<2e-4 and row['CD_tail_range']<2e-5;rows.append(row);save(run/'results_in_progress.json',rows);print(json.dumps(row),flush=True)
    result=deepcopy(old);result.update(timestamp=datetime.now(timezone.utc).isoformat(),results=rows,run_directory=str(run),previous_run_directory=str(previous),experimental_comparison_status='pending continuation postprocessing',quality_passed=False,continuation_note='500 iterations each, fixed CFL20; limiter frozen after50, linear tolerance tightened. Initial failures preserved; acceptance unchanged.')
    save(run/'results.json',result);save(OUT/'reports/m6_rans_results.json',result)
if __name__=='__main__':main()
