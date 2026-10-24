"""Run published OAS examples; check optimizer constraints and coupled sensitivities.
Published examples are software qualification, not a validated UAV/CRM design.
"""
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import runpy
import time
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ.get('UAV_OUTPUT_ROOT',str(ROOT/'outputs')))
os.environ['OPENMDAO_REPORTS']='0';os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def main():
    sources=ROOT/'work/openaerostruct/sources';manifest=json.loads((sources/'manifest.json').read_text())
    for r in manifest['records']:
        if r.get('example') and sha(ROOT/r['example'])!=r['example_sha256']:raise ValueError('Published example changed')
    folder=OUT/'simulations'/('openaerostruct_'+datetime.now().strftime('%Y%m%d_%H%M%S'));folder.mkdir(parents=True)
    records=[];start=time.perf_counter();previous=Path.cwd()
    try:
        os.chdir(folder)
        for name in ['quick','tube']:
            print('Published OAS example:',name,flush=True);t=time.perf_counter()
            with (folder/(name+'.log')).open('w',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
                data=runpy.run_path(str(sources/(name+'_official.py')));p=data['prob']
                constraints={k:np.asarray(v).tolist() for k,v in p.driver.get_constraint_values().items()}
                objectives={k:np.asarray(v).tolist() for k,v in p.driver.get_objective_values().items()}
                row={'example':name,'seconds':time.perf_counter()-t,'optimizer_success':bool(p.driver.result.success),'constraints':constraints,'driver_scaled_objectives':objectives,'source_sha256':sha(sources/(name+'_official.py'))}
                if name=='quick':
                    row.update(CL=float(p.get_val('aero_point_0.wing_perf.CL')[0]),CD=float(p.get_val('aero_point_0.wing_perf.CD')[0]))
                    row['constraints_passed']=abs(row['CL']-.5)<1e-6
                else:
                    row.update(failure_max=float(np.max(p.get_val('AS_point_0.wing_perf.failure'))),thickness_intersects_max_m=float(np.max(p.get_val('AS_point_0.wing_perf.thickness_intersects'))),L_equals_W=float(p.get_val('AS_point_0.L_equals_W')[0]),fuelburn_kg=float(p.get_val('AS_point_0.fuelburn',units='kg')[0]),structural_mass_kg=float(p.get_val('wing.structural_mass',units='kg')[0]))
                    row['constraints_passed']=row['failure_max']<=1e-5 and row['thickness_intersects_max_m']<=1e-7 and abs(row['L_equals_W'])<1e-6
                    coupled=p.model.AS_point_0.coupled
                    row['nonlinear_error_on_nonconvergence']=bool(coupled.nonlinear_solver.options['err_on_non_converge'])
                    row['nonlinear_absolute_tolerance']=float(coupled.nonlinear_solver.options['atol'])
                    totals=p.check_totals(of=['AS_point_0.fuelburn','AS_point_0.L_equals_W'],wrt=['alpha','wing.thickness_cp'],method='fd',step=1e-5,out_stream=log)
                    derivatives=[]
                    for key,r in totals.items():
                        analytic=r.get('J_rev',r.get('J_fwd'));fd=r['J_fd'];error=float(np.linalg.norm(analytic-fd)/max(1.,np.linalg.norm(fd)))
                        derivatives.append({'of':key[0],'wrt':key[1],'relative_norm_error_with_unit_floor':error,'analytic':analytic.tolist(),'finite_difference':fd.tolist()})
                    row['derivatives']=derivatives;row['derivative_check_passed']=all(r['relative_norm_error_with_unit_floor']<.005 for r in derivatives)
                    mesh=p.get_val('AS_point_0.coupled.wing.def_mesh',units='m');original=p.get_val('wing.mesh',units='m');disp=p.get_val('AS_point_0.coupled.wing.disp')
                    np.savez(folder/'coupled_geometry.npz',deformed_mesh_m=mesh,undeformed_mesh_m=original,displacements=disp)
                    fig,ax=plt.subplots(figsize=(9,4.5))
                    for array,label,style in [(original,'Undeformed','--'),(mesh,'Coupled deformed','-')]:ax.plot(array[0,:,1],array[0,:,2],style,marker='o',label=label)
                    ax.set(xlabel='Half-wing span coordinate y (m)',ylabel='Leading-edge z (m)',title='Published CRM tube example: actual coupled mesh');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(OUT/'plots/openaerostruct_deformation.png',dpi=150);plt.close(fig)
                row['passed']=row['optimizer_success'] and row['constraints_passed'] and row.get('derivative_check_passed',True)
                p.cleanup();records.append(row)
            save(folder/(name+'_results.json'),row)
    finally:os.chdir(previous)
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(r['passed'] for r in records) and len(records)==2,'seconds':time.perf_counter()-start,'versions':{k:metadata.version(k) for k in ['openaerostruct','openmdao','numpy','scipy']},'results':records,'run_directory':str(folder),'scope':'Published low-fidelity CRM aerodynamic/tube aerostructural optimization examples; not a UAV, CFD, mesh-independent solution or structural certification','quality_passed':None,'physical_design_acceptance':'not evaluated','thresholds':{'CL_equality_absolute':1e-6,'failure_upper_with_tolerance':1e-5,'thickness_intersects_upper_m':1e-7,'L_equals_W_absolute':1e-6,'derivative_relative_norm_error_with_unit_floor':.005},'source_manifest_sha256':sha(sources/'manifest.json')}
    save(folder/'results.json',result);save(OUT/'reports/openaerostruct_examples.json',result);print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
