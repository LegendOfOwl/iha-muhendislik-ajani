"""Review a selected, frozen revision. No outcome-based case selection or threshold changes."""
from pathlib import Path
from datetime import datetime,timezone
import json,csv,sys,os
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation';OUT=ROOT/'outputs/projects/proje-15cce2de02'
sys.path.insert(0,str(Path(__file__).parent))
from evaluate import read,save,sha,evaluate_one,metrics,surface
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def main():
 manifest_path=BASE/'reviewer/review_manifest_v2.json';fp=OUT/'reports/prediction_v2_frozen.json'
 if not fp.exists():raise RuntimeError('No frozen v2 prediction: experimental evaluation forbidden')
 snapshot=read(fp);files=snapshot['case_files_sha256']
 for path,digest in files.items():
  if sha(ROOT/path)!=digest:raise RuntimeError('Frozen file changed: '+path)
 assert snapshot['contract_sha256']==sha(BASE/'contract.json')
 for name,h in snapshot['input_sha256'].items():
  ip=ROOT/name if '/' in name or '\\' in name else BASE/'analysis_input'/name
  assert sha(ip)==h
 contract=read(BASE/'contract.json');limits=contract['minimum_numerical'];elimits=contract['experimental_Cp'];manifest=read(manifest_path)
 cases=[];num={};branches={};fig,axes=plt.subplots(2,2,figsize=(12,9))
 for case_index,case in enumerate(manifest['cases']):
  label=case['label']
  if not case.get('surface_file'):
   cases.append({'label':label,'status':case.get('status','not_run'),'reason':case.get('reason'),'experimental_passed':False,'numerical_passed':False});continue
  path=ROOT/case['surface_file'];folder=ROOT/case['folder'];rel=str(path.relative_to(ROOT))
  assert sha(path)==case['surface_sha256'] and files.get(rel,files.get(rel.replace('\\','/')))==sha(path)
  raw,ref,sides,pred,b=evaluate_one(path);branches[label]=b
  mask=(sides=='upper')&np.isclose(ref[:,0],.0002,atol=1e-10);assert mask.sum()==1
  corrected=ref.copy();assert np.isclose(corrected[mask,1][0],-.4219);corrected[mask,1]=.4219
  upper=sides=='upper';cm={'all':metrics(pred,corrected[:,1]),'upper':metrics(pred[upper],corrected[upper,1]),'lower':metrics(pred[~upper],corrected[~upper,1])}
  checks={'all_RMSE':cm['all']['RMSE']<=elimits['pointwise_RMSE_max'],'upper_RMSE':cm['upper']['RMSE']<=elimits['per_side_RMSE_max'],'lower_RMSE':cm['lower']['RMSE']<=elimits['per_side_RMSE_max'],'p95_error':cm['all']['p95_abs_error']<=elimits['p95_absolute_error_max'],'max_error':cm['all']['max_abs_error']<=elimits['max_absolute_error_max'],'shock_location':raw['shock_location_abs_error_chords']<=elimits['shock_location_abs_error_chords_max']}
  cm['checks']=checks;cm['experimental_passed']=all(checks.values())
  m=read(folder/'prediction_metrics.json');checkpoint=read(folder/'checkpoint_selection.json');fi=int(checkpoint['iteration'])
  assert str(path.relative_to(ROOT))==checkpoint['surface'] or str(path.relative_to(ROOT)).replace('\\','/')==checkpoint['surface']
  for key in ['surface','volume','restart']:
   p=ROOT/checkpoint[key];assert files.get(str(p.relative_to(ROOT)),files.get(str(p.relative_to(ROOT)).replace('\\','/')))==sha(p)
  with (folder/'history.csv').open() as f:
   cr=csv.reader(f,skipinitialspace=True);header=[s.strip().strip('"') for s in next(cr)];history=[dict(zip(header,map(float,r))) for r in cr]
  matches=[r for r in history if int(r['Inner_Iter'])==fi];assert len(matches)==1
  h=matches[0];tail=[r for r in history if fi-199<=int(r['Inner_Iter'])<=fi]
  v={'field_iteration':fi,'terminal_iteration':int(history[-1]['Inner_Iter']),'density_log10':h['rms[Rho]'],'CL':h['CL'],'CD':h['CD'],'CN':h['CFy'],'CL_tail200_range':float(np.ptp([r['CL'] for r in tail])) if len(tail)==200 else None,'CD_tail200_range':float(np.ptp([r['CD'] for r in tail])) if len(tail)==200 else None,'max_yplus':raw['wall']['max_wall_yplus']}
  nc={'density':v['density_log10']<=limits['density_log10_max'],'200_consecutive_samples':len(tail)==200,'CL_window':v['CL_tail200_range'] is not None and v['CL_tail200_range']<=limits['CL_tail_range_max'],'CD_window':v['CD_tail200_range'] is not None and v['CD_tail200_range']<=limits['CD_tail_range_max'],'wall_yplus':v['max_yplus']<limits['max_wall_yplus']}
  mesh=read(ROOT/case['mesh_metadata_source'] if case.get('mesh_metadata_source') else folder/'mesh_audit.json');num[label]={'values':v,'checks':nc,'passed':all(nc.values()),'mesh':{k:mesh.get(k) for k in ['cells','curve_definition_sha256','farfield_bounds_m','BL_thickness_m','BL_growth','wall_first_layer_design_m']},'folder':str(folder.relative_to(ROOT)),'checkpoint':checkpoint,'independent_force':m['independent_surface_force']}
  result={'label':label,'status':case.get('status','available'),'surface_file':str(path.relative_to(ROOT)),'surface_sha256':sha(path),'original_downloaded_reference':raw,'original_table_corrected_reference':cm,'numerical_passed':all(nc.values()),'experimental_passed':cm['experimental_passed']};cases.append(result)
  dst=OUT/'data/review'/f'v2_{label}_all_points.csv';np.savetxt(dst,np.column_stack([ref[:,0],upper.astype(int),ref[:,1],corrected[:,1],pred,pred-corrected[:,1]]),delimiter=',',header='x_over_c,is_upper,Cp_NASA_normalized,Cp_original_table,Cp_prediction,error_original_table',comments='')
  color=plt.get_cmap('tab10')(case_index%10)
  for side,ls in [('upper','-'),('lower','--')]:axes[0,0].plot(b[side][:,0],b[side][:,2],ls,color=color,label=label if side=='upper' else None,lw=1)
  axes[0,1].plot(corrected[:,0],pred-corrected[:,1],'.',color=color,label=label,ms=3)
  axes[1,0].plot([label],[cm['all']['RMSE']],'o',color=color)
  reference_for_plot=corrected
 if not num:raise RuntimeError('No selected matched fields')
 axes[0,0].plot(reference_for_plot[:,0],reference_for_plot[:,1],'ko',ms=2,label='Original experiment,103 taps');axes[0,0].invert_yaxis();axes[0,0].set(xlabel='x/c',ylabel='Cp',title='Frozen revision and original published table');axes[0,0].legend(fontsize=7)
 axes[0,1].axhline(.15,c='#b35454',ls='--');axes[0,1].axhline(-.15,c='#b35454',ls='--');axes[0,1].set(xlabel='x/c',ylabel='Cp prediction - experiment',title='No point excluded');axes[0,1].legend(fontsize=7)
 axes[1,0].axhline(.03,c='#b35454',ls='--');axes[1,0].set(ylabel='Cp RMSE');axes[1,1].axis('off');axes[1,1].text(0,1,'Same predeclared thresholds\nM=.729, alpha=2.31deg, Re=6.5M\nOriginal source coordinates retained\nOne independently documented reference sign correction\n\nAll numerical and regional mesh gates\nmust pass together. Missing runs remain open.\nNo 3D M6/UAV qualification.',va='top')
 for ax in axes.ravel()[:3]:ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(OUT/'plots/review_v2_Cp_comparison.png',dpi=160);plt.close(fig)
 roles=manifest['roles'];all_main=all(roles.get(k) in num for k in ['coarse','medium','fine','farfield'])
 grid={'evaluated':False};far={'evaluated':False};family={'consistent':False}
 if all(roles.get(k) in num for k in ['coarse','medium','fine']):
  familydata=[num[roles[k]]['mesh'] for k in ['coarse','medium','fine']]
  family={'consistent':all(d['curve_definition_sha256']==familydata[0]['curve_definition_sha256'] and d['farfield_bounds_m']==familydata[0]['farfield_bounds_m'] and d['BL_thickness_m']==familydata[0]['BL_thickness_m'] for d in familydata),'geometry_and_BL':familydata}
 if roles.get('medium') in num and roles.get('fine') in num:
  a=num[roles['medium']]['values'];b=num[roles['fine']]['values'];errors=[]
  for side in ['upper','lower']:
   x=np.linspace(0,1,1001);u=branches[roles['medium']][side];v=branches[roles['fine']][side];errors.extend(np.interp(x,u[:,0],u[:,2])-np.interp(x,v[:,0],v[:,2]))
  grid={'evaluated':True,'CL_relative_change':abs(b['CL']-a['CL'])/abs(b['CL']),'CD_relative_change':abs(b['CD']-a['CD'])/abs(b['CD']),'Cp_uniform_x_RMSE':float(np.sqrt(np.mean(np.array(errors)**2))),'converged_inputs':num[roles['medium']]['passed'] and num[roles['fine']]['passed']}
  grid['checks']={'CL':grid['CL_relative_change']<=limits['CL_finest_grid_relative_change_max'],'CD':grid['CD_relative_change']<=limits['CD_finest_grid_relative_change_max'],'Cp':grid['Cp_uniform_x_RMSE']<=limits['Cp_finest_grid_RMSE_max'],'converged_inputs':grid['converged_inputs']}
 if roles.get('medium') in num and roles.get('farfield') in num:
  a=num[roles['medium']]['values'];b=num[roles['farfield']]['values'];far={'evaluated':True,'CL_relative_change':abs(b['CL']-a['CL'])/abs(b['CL']),'CD_relative_change':abs(b['CD']-a['CD'])/abs(b['CD']),'converged_inputs':num[roles['medium']]['passed'] and num[roles['farfield']]['passed']}
  far['checks']={'CL':far['CL_relative_change']<=limits['CL_farfield_relative_change_max'],'CD':far['CD_relative_change']<=limits['CD_farfield_relative_change_max'],'converged_inputs':far['converged_inputs']}
 numerical=all_main and all(num[roles[k]]['passed'] for k in ['coarse','medium','fine','farfield']) and family['consistent'] and all(grid.get('checks',{'missing':False}).values()) and all(far.get('checks',{'missing':False}).values())
 regional_open=manifest.get('critical_regional_mesh_issue_open',True)
 # The finest prescribed mesh is the validation prediction, never the best-fitting case.
 validation=[c for c in cases if c['label']==roles.get('fine')]
 passed=numerical and not regional_open and len(validation)==1 and validation[0].get('experimental_passed',False)
 result={'timestamp':datetime.now(timezone.utc).isoformat(),'frozen_prediction_sha256':sha(fp),'case_selection_manifest_sha256':sha(manifest_path),'case_selection_before_experiment_review':True,'experimental_validation_role':'fine, fixed before v2 unblinding; all other case errors remain reported','frozen_files_verified':len(files),'case_results':cases,'numerical_results':num,'family':family,'grid_sensitivity':grid,'farfield_sensitivity':far,'all_required_numerical_gates_passed':numerical,'critical_regional_mesh_issue_open':regional_open,'regional_mesh_explanation':manifest.get('regional_mesh_explanation'),'minimum_qualification_passed':bool(passed),'GCI':{'reported':False,'reason':'No independently established monotone/asymptotic regime; never present a residual-limited or missing run as a grid-error band.'},'scope':'Only2D RAE2822 corrected-condition benchmark. Original-table one-point correction is documented separately. No3D/UAV or general RANS service acceptance.'}
 save(OUT/'reports/review_v2_qualification.json',result)
 print(json.dumps({'numerical':numerical,'minimum_qualification_passed':bool(passed),'cases':{c['label']:c.get('original_table_corrected_reference',{}).get('all',{}).get('RMSE') for c in cases},'grid':grid,'farfield':far},indent=2))
if __name__=='__main__':main()
