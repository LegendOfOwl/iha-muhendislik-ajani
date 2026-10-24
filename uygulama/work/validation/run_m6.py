"""Native 3-D compressible viscous CFD on two official source grids.
Acceptance limits are written before the first solver call; experimental checks follow.
"""
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'work/validation/sources'
PID=json.loads((ROOT/'work/validation/projects.json').read_text())['cfd'];OUT=ROOT/'outputs/projects'/PID
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def replace(text,key,value):
    pat=r'^\s*'+re.escape(key)+r'\s*=.*$'
    return re.sub(pat,key+'= '+str(value),text,flags=re.M) if re.search(pat,text,re.M) else text+'\n'+key+'= '+str(value)+'\n'
def read_mesh(path):
    with path.open() as f:
        def line():
            s=f.readline()
            while s.startswith('%') or not s.strip():s=f.readline()
            return s
        assert line().strip()=='NDIME= 3'
        n=int(line().split('=')[1]);types={}
        for _ in range(n):t=int(f.readline().split()[0]);types[t]=types.get(t,0)+1
        count=int(line().split('=')[1].split()[0]);xyz=np.array([[float(v) for v in f.readline().split()[:3]] for _ in range(count)])
        markers={};number=int(line().split('=')[1])
        for _ in range(number):
            tag=line().split('=')[1].strip();ne=int(line().split('=')[1]);faces=[]
            for _ in range(ne):v=[int(s) for s in f.readline().split()];faces.append(v[1:1+{5:3,9:4}[v[0]]])
            markers[tag]=faces
    wing=markers['WING'];ids=np.unique(np.concatenate(wing));pts=xyz[ids];tri=[]
    for face in wing:
        tri.append(face[:3])
        if len(face)==4:tri.append([face[0],face[2],face[3]])
    t=xyz[np.array(tri)];vectors=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])/2
    area=float(np.sum(np.abs(vectors[:,2]))/2)
    ymin=pts[:,1].min();ymax=pts[:,1].max();root=pts[np.abs(pts[:,1]-ymin)<1e-6];tip=pts[np.abs(pts[:,1]-ymax)<1e-6]
    return {'volume_cells':n,'nodes':count,'element_types':types,'wing_faces':len(wing),'wing_points':len(ids),'bounds_m':[pts.min(axis=0).tolist(),pts.max(axis=0).tolist()],'domain_bounds_m':[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],
            'semispan_m':float(ymax-ymin),'root_chord_m':float(np.ptp(root[:,0])),'tip_chord_m':float(np.ptp(tip[:,0])),'projected_semispan_area_m2':area,'mesh_sha256':sha(path)}
def main():
    run=OUT/'simulations'/('m6_rans_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    conditions={'Mach':.8395,'alpha_deg':3.06,'beta_deg':0,'Re':11.72e6,'Re_length_m':.64607,'T_K':288.15,'solver':'3D compressible RANS','turbulence':'SA, fully turbulent, no transition','boundary':'adiabatic no-slip wing; symmetry root; freestream farfield'}
    thresholds={'density_log10_max':-7,'CL_last100_range_max':2e-4,'CD_last100_range_max':2e-5,'strict_max_yplus':1,'grid_CL_relative_change_max':.03,'grid_CD_relative_change_max':.1,'per_section_Cp_RMSE_max':.08,'NASA_Cp_measurement_uncertainty':.02,'note':'Numerical/engineering screens chosen before runs; NASA +/-0.02 is measurement uncertainty, not a universal CFD pass criterion.'}
    save(run/'acceptance_contract.json',{'conditions':conditions,'thresholds':thresholds,'timestamp':datetime.now(timezone.utc).isoformat()})
    rows=[];binary=json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable']
    for label,name in [('coarse_hexa','mesh_ONERAM6_turb_hexa_43008.su2'),('finer_hybrid','mesh_ONERAM6_turb_hybrid_258969.su2')]:
        folder=run/label;folder.mkdir();shutil.copy2(SOURCE/name,folder/'mesh.su2');mesh=read_mesh(folder/'mesh.su2')
        save(folder/'mesh_audit.json',mesh)
        # These are reference benchmark grids, not a claim that arbitrary CAD was meshed.
        text=(SOURCE/'turb_ONERAM6.cfg').read_text();settings={'MESH_FILENAME':'mesh.su2','ITER':4000,'CFL_NUMBER':4,'CFL_ADAPT':'YES','CFL_ADAPT_PARAM':'(0.5, 1.2, 1.0, 100.0)',
            'LINEAR_SOLVER_ERROR':1e-5,'LINEAR_SOLVER_ITER':10,'CONV_RESIDUAL_MINVAL':-8,'CONV_STARTITER':100,'CONV_FIELD':'(RMS_DENSITY)',
            'OUTPUT_FILES':'(RESTART, PARAVIEW, SURFACE_PARAVIEW, SURFACE_CSV)','OUTPUT_WRT_FREQ':4000,'HISTORY_OUTPUT':'(ITER, RMS_RES, AERO_COEFF)',
            'SCREEN_OUTPUT':'(INNER_ITER, RMS_DENSITY, RMS_NU_TILDE, LIFT, DRAG)','REF_AREA':mesh['projected_semispan_area_m2']}
        for key,value in settings.items():text=replace(text,key,value)
        (folder/'case.cfg').write_text(text);command=[binary,'case.cfg','-t','4'];save(folder/'command.json',command)
        save(folder/'inputs.json',{'project_id':PID,'conditions':conditions,'thresholds':thresholds,'source_config_sha256':sha(SOURCE/'turb_ONERAM6.cfg'),'overrides':settings,'mesh':mesh})
        print('NATIVE M6 RANS',label,json.dumps(mesh),flush=True);start=time.perf_counter();row={'grid':label,'folder':str(folder),'mesh':mesh}
        try:
            with (folder/'native.log').open('w',encoding='utf-8') as log:p=subprocess.run(command,cwd=folder,stdout=log,stderr=subprocess.STDOUT,timeout=3600,creationflags=subprocess.CREATE_NO_WINDOW,env=dict(os.environ,OMP_NUM_THREADS='4'))
            row.update(exit_code=p.returncode,seconds=time.perf_counter()-start)
            if p.returncode:raise ValueError('Native solver failed; see native.log')
            h=pd.read_csv(folder/'history.csv');h.columns=h.columns.str.strip().str.strip('"');last=h.iloc[-1];tail=h.tail(100)
            row.update(CL=float(last['CL']),CD=float(last['CD']),log10_density_residual=float(last['rms[Rho]']),log10_turbulence_residual=float(last['rms[nu]']),iterations=len(h),CL_tail_range=float(np.ptp(tail['CL'])),CD_tail_range=float(np.ptp(tail['CD'])),runtime_passed=True)
            row['iterative_passed']=row['log10_density_residual']<-7 and row['CL_tail_range']<2e-4 and row['CD_tail_range']<2e-5
        except Exception as exc:row.update(runtime_passed=False,iterative_passed=False,error=str(exc),seconds=time.perf_counter()-start)
        rows.append(row);save(run/'results_in_progress.json',rows);print(json.dumps(row),flush=True)
        if not row['runtime_passed']:break
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'project_id':PID,'passed':len(rows)==2 and all(r['runtime_passed'] for r in rows),'quality_passed':False,'conditions':conditions,'conditions_sha256':hashlib.sha256(json.dumps(conditions,sort_keys=True).encode()).hexdigest(),'thresholds':thresholds,'results':rows,'run_directory':str(run),'scope':'ONERA M6 Test2308 half-wing only; experiment comparison and y+ assessed separately','experimental_comparison_status':'pending postprocessing','mesh_note':'Two different source grid families; sensitivity comparison is not a systematic Richardson grid-convergence study'}
    save(run/'results.json',result);save(OUT/'reports/m6_rans_results.json',result)
    print('M6_NATIVE_RUNS_FINISHED',str(run),flush=True);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
