"""Post-freeze numerical audit with predeclared tolerances and explicit scope limits."""
from pathlib import Path
import csv,json,hashlib,sys
from collections import Counter
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation'
sys.path.insert(0,str(Path(__file__).parent))
from evaluate import read,save,sha,surface
out=ROOT/read(BASE/'project.json')['output_root'];frozen=read(out/'reports/prediction_frozen.json')
bad=[p for p,h in frozen['case_files_sha256'].items() if sha(ROOT/p)!=h]
assert not bad, bad
contract=read(BASE/'contract.json');limit=contract['minimum_numerical'];cases={}
for name in ['coarse','medium','fine','medium_far']:
 folder=out/'simulations'/name;m=read(folder/'prediction_metrics.json')
 with (folder/'history.csv').open() as f:
  raw=csv.reader(f,skipinitialspace=True);header=[s.strip().strip('"') for s in next(raw)]
  history=[dict(zip(header,map(float,row))) for row in raw]
 n=int(m['field_checkpoint_iteration']);matched=[r for r in history if int(r['Inner_Iter'])==n]
 assert len(matched)==1
 h=matched[0];tail=[r for r in history if n-199<=int(r['Inner_Iter'])<=n]
 assert len(tail)==200
 values={'density_log10':h['rms[Rho]'],'CL':h['CL'],'CD':h['CD'],'CL_tail200_range':float(np.ptp([r['CL'] for r in tail])),'CD_tail200_range':float(np.ptp([r['CD'] for r in tail])),'max_yplus':m['max_wall_yplus']}
 checks={'density':values['density_log10']<=limit['density_log10_max'],'CL_window':values['CL_tail200_range']<=limit['CL_tail_range_max'],'CD_window':values['CD_tail200_range']<=limit['CD_tail_range_max'],'wall_yplus':values['max_yplus']<limit['max_wall_yplus']}
 mesh=read(folder/'mesh_audit.json');export=read(folder/'mesh_export_audit.json')
 cases[name]={'matched_field_iteration':n,'terminal_iteration':int(history[-1]['Inner_Iter']),'values':values,'checks':checks,'numerical_iteration_and_wall_passed':all(checks.values()),'cells':mesh['cells'],'run_status':read(folder/'run_status.json'),'mesh_measured':{k:mesh[k] for k in ['positive_signed_areas','min_scaled_jacobian','equiangle_skewness_max','center_face_nonorthogonality_max_deg','wall_first_layer_design_m','BL_growth','BL_thickness_m','BL_design_layers','farfield_bounds_m','curve_definition_sha256']},'regional_export_measurements':export,'independent_surface_force':m['independent_surface_force']}
def change(a,b):return abs(b-a)/abs(b)
med=cases['medium']['values'];fine=cases['fine']['values'];far=cases['medium_far']['values']
grid={'CL_relative_change':change(med['CL'],fine['CL']),'CD_relative_change':change(med['CD'],fine['CD'])}
b1,_=surface(out/'simulations/medium/surface_flow.vtu');b2,_=surface(out/'simulations/fine/surface_flow.vtu');errors=[]
for side in ['upper','lower']:
 x=np.linspace(0,1,1001);errors.extend(np.interp(x,b1[side][:,0],b1[side][:,2])-np.interp(x,b2[side][:,0],b2[side][:,2]))
grid['Cp_uniform_x_RMSE']=float(np.sqrt(np.mean(np.array(errors)**2)))
grid['checks']={'CL':grid['CL_relative_change']<=limit['CL_finest_grid_relative_change_max'],'CD':grid['CD_relative_change']<=limit['CD_finest_grid_relative_change_max'],'Cp':grid['Cp_uniform_x_RMSE']<=limit['Cp_finest_grid_RMSE_max']}
farfield={'CL_relative_change':change(med['CL'],far['CL']),'CD_relative_change':change(med['CD'],far['CD']),'domains_chords':[20,40]}
farfield['checks']={'CL':farfield['CL_relative_change']<=limit['CL_farfield_relative_change_max'],'CD':farfield['CD_relative_change']<=limit['CD_farfield_relative_change_max']}
iterative=all(c['numerical_iteration_and_wall_passed'] for c in cases.values())
result={'timestamp':datetime.now(timezone.utc).isoformat(),'version':'v1','frozen_files_verified':len(frozen['case_files_sha256']),'contract_sha256':sha(BASE/'contract.json'),'cases':cases,'grid_sensitivity':grid,'farfield_sensitivity':farfield,'GCI':{'reported':False,'reason':'Fine matched field fails iterative force stability; domain sensitivity unresolved; coefficient changes cannot establish asymptotic grid-error bands.'},'geometry_representation_audit':read(BASE/'reviewer/leading_edge_tangent_audit.json'),'geometry_qualification_passed':False,'geometry_reason':'Two endpoint splines introduce artificial C0 leading-edge corner. Source point interpolation alone did not verify smooth source shape. New representation must be a separate revision.','all_required_numerical_gates_passed':iterative and all(grid['checks'].values()) and all(farfield['checks'].values()),'original_NASA_reference_experiment_passed':False,'original_table_corrected_experiment_passed':False,'minimum_qualification_passed':False,'scope':'2D fully turbulent RANS/SA, one corrected-condition RAE2822 benchmark. No 3D M6/UAV acceptance.'}
save(out/'reports/review_v1_qualification.json',result)
print(json.dumps({'v1_numerical_pass':result['all_required_numerical_gates_passed'],'grid':grid,'farfield':farfield,'GCI':result['GCI']},indent=2))
