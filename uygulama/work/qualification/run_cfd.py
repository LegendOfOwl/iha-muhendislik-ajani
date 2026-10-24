"""Run native volume-mesh CFD; retain convergence and field files without claiming universal validation."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'; SOURCE=ROOT/'work/qualification/sources'
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def replace(text,key,value):
    pattern=r'^\s*'+re.escape(key)+r'\s*=.*$'
    if re.search(pattern,text,re.M): return re.sub(pattern,key+'= '+str(value),text,flags=re.M)
    return text+'\n'+key+'= '+str(value)+'\n'
def main():
    meta=json.loads((ROOT/'work/setup/su2_install.json').read_text())
    run=OUT/'simulations'/('cfd_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    results=[]
    cases=[('euler_shock','inv_NACA0012.cfg','mesh_NACA0012_inv.su2','EULER',600),
      ('rans_coarse','turb_naca0012.cfg','n0012_113-33.su2','INC_RANS',3000),
      ('rans_medium','turb_naca0012.cfg','n0012_225-65.su2','INC_RANS',4000),
      ('rans_fine','turb_naca0012.cfg','n0012_449-129.su2','INC_RANS',5000)]
    for label,cfg_name,mesh,solver,iters in cases:
        folder=run/label; folder.mkdir(); shutil.copy2(SOURCE/mesh,folder/mesh)
        text=(SOURCE/cfg_name).read_text()
        settings={'ITER':iters,'MESH_FILENAME':mesh,'OUTPUT_FILES':'(RESTART, PARAVIEW, SURFACE_CSV)',
          'OUTPUT_WRT_FREQ':iters,'CONV_RESIDUAL_MINVAL':-9,'CONV_STARTITER':50,
          'HISTORY_OUTPUT':'(ITER, RMS_RES, AERO_COEFF)',
          'SCREEN_OUTPUT':'(INNER_ITER, RMS_DENSITY, LIFT, DRAG)' if solver=='EULER' else '(INNER_ITER, RMS_PRESSURE, RMS_NU_TILDE, LIFT, DRAG)'}
        if solver=='INC_RANS': settings.update(FREESTREAM_NU_FACTOR=3.0,LINEAR_SOLVER_ERROR=1e-6)
        for key,value in settings.items(): text=replace(text,key,value)
        (folder/'case.cfg').write_text(text,encoding='utf-8')
        command=[meta['executable'],'case.cfg','-t','4']; save(folder/'command.json',command)
        save(folder/'inputs.json',{'solver':solver,'settings_overrides':settings,'mesh_sha256':sha(folder/mesh),
             'base_config_sha256':sha(SOURCE/cfg_name),'script_sha256':sha(Path(__file__)),
             'classification':'source-based verification/validation case; not actual UAV conditions',
             'physical_conditions':({'Mach':.8,'alpha_deg':1.25,'viscous':False} if solver=='EULER' else
                  {'rho_kg_m3':2.13163,'velocity_m_s':[51.36481493540834,9.05700273220962,0],
                   'mu_Pa_s':1.853e-5,'chord_m':1.,'alpha_deg':10.,'turbulence_model':'SA; fully turbulent','freestream_nu_factor':3.})})
        start=time.perf_counter(); env=os.environ.copy(); env['OMP_NUM_THREADS']='4'
        row={'case':label,'folder':str(folder),'solver':solver}
        try:
            print('RUN',label,flush=True)
            with (folder/'native.log').open('w',encoding='utf-8') as log:
                p=subprocess.run(command,cwd=folder,stdout=log,stderr=subprocess.STDOUT,timeout=1200,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            row.update(exit_code=p.returncode,seconds=round(time.perf_counter()-start,3))
            if p.returncode: raise RuntimeError('Native CFD process failed; inspect native.log')
            frame=pd.read_csv(folder/'history.csv'); frame.columns=[c.strip().strip('"') for c in frame.columns]
            frame.to_csv(folder/'history_clean.csv',index=False)
            row['columns']=list(frame.columns); row['iterations']=int(frame.iloc[-1]['Inner_Iter']) if 'Inner_Iter' in frame else len(frame)
            clcol=next(c for c in frame if c in ['CL','Lift']); cdcol=next(c for c in frame if c in ['CD','Drag'])
            residual=next(c for c in frame if c in ['rms[Rho]','rms[P]','rms[Pressure]'])
            tail=frame.tail(100)
            row.update(CL=float(frame[clcol].iloc[-1]),CD=float(frame[cdcol].iloc[-1]),residual_field=residual,
               final_log10_residual=float(frame[residual].iloc[-1]),
               CL_tail_range=float(tail[clcol].max()-tail[clcol].min()),CD_tail_range=float(tail[cdcol].max()-tail[cdcol].min()),
               volume_output_exists=bool(list(folder.glob('flow*.vtu'))),surface_output_exists=(folder/'surface_flow.csv').exists())
            required=[row['CL'],row['CD'],row['final_log10_residual']]
            row['runtime_passed']=True
            row['iterative_convergence_passed']=bool(np.isfinite(required).all() and row['final_log10_residual']<-7 and row['CL_tail_range']<2e-4 and row['CD_tail_range']<2e-5)
            print(label,{k:row[k] for k in ['CL','CD','final_log10_residual','CL_tail_range','CD_tail_range','seconds']},flush=True)
        except Exception as e:
            row.update(runtime_passed=False,iterative_convergence_passed=False,error=f'{type(e).__name__}: {e}')
            print(label,row['error'],flush=True)
        results.append(row); save(run/'results_in_progress.json',results)
        # Stop config/runtime failures; preserve the failed run before repairing.
        if not row['runtime_passed']: break
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':len(results)==len(cases) and all(r['runtime_passed'] for r in results),
      'quality_passed':len(results)==len(cases) and all(r['iterative_convergence_passed'] for r in results),
      'results':results,'run_directory':str(run),'scope':'One Euler and three-grid 2D turbulent RANS source cases; no whole-aircraft CFD acceptance',
      'limits':['Grid/experimental agreement and y+ are evaluated separately','2D SA at one angle does not establish stall, transition, 3D aircraft drag or a general airfoil service']}
    save(run/'results.json',obj); save(OUT/'reports/cfd_qualification.json',obj)
    return 0 if obj['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
