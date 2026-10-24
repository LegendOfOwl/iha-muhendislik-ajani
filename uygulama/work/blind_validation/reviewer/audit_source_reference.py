"""Keep the downloaded reference immutable; publish a documented original-table correction."""
from pathlib import Path
import json,hashlib,shutil,sys,os
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation'
sys.path.insert(0,str(Path(__file__).parent))
from evaluate import read,save,sha,metrics
import numpy as np
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=ROOT/read(BASE/'project.json')['output_root']
source=BASE/'reviewer/additional_sources'
shutil.copy2(source/'page_198.png',out/'plots/review_original_table_case6.png')
rows=[];fig,ax=plt.subplots(figsize=(10,5))
contract=read(BASE/'contract.json')['experimental_Cp']
for p in sorted((out/'data/review').glob('[0-9][0-9]_experimental_Cp.csv')):
 a=np.loadtxt(p,delimiter=',',skiprows=1)
 mask=(a[:,1]==1)&np.isclose(a[:,0],.0002,atol=1e-10)
 assert mask.sum()==1 and np.isclose(a[mask,2][0],-.4219)
 b=a.copy();b[mask,2]=.4219;b[:,4]=b[:,3]-b[:,2]
 label=['coarse','medium','fine','medium_far'][int(p.name[:2])]
 dst=p.with_name(p.stem+'_original_table_corrected.csv')
 np.savetxt(dst,b,delimiter=',',header='x_over_c,is_upper,Cp_experiment_original_table,Cp_prediction,error',comments='')
 m=metrics(b[:,3],b[:,2]);upper=b[:,1]==1;u=metrics(b[upper,3],b[upper,2]);l=metrics(b[~upper,3],b[~upper,2])
 checks={'all_RMSE':m['RMSE']<=contract['pointwise_RMSE_max'],'upper_RMSE':u['RMSE']<=contract['per_side_RMSE_max'],'lower_RMSE':l['RMSE']<=contract['per_side_RMSE_max'],'p95_error':m['p95_abs_error']<=contract['p95_absolute_error_max'],'max_error':m['max_abs_error']<=contract['max_absolute_error_max']}
 rows.append({'label':label,'all':m,'upper':u,'lower':l,'checks':checks,'pressure_magnitude_gates_passed':all(checks.values()),'all_103_points_retained':True,'csv':str(dst.relative_to(ROOT)),'surface_prediction_unchanged':True})
 ax.plot(b[:,0],b[:,4],'.',ms=4,label=label)
ax.axhline(0,color='#777',lw=.7);ax.axhline(.15,color='#b4494b',ls='--');ax.axhline(-.15,color='#b4494b',ls='--');ax.set(xlabel='x/c',ylabel='Cp prediction - original published experiment',title='All 103 points, one documented source sign correction');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(out/'plots/review_original_table_corrected_errors.png',dpi=160);plt.close(fig)
result={'source_pdf_url':'https://www.abbottaerospace.com/downloads/agard-r-138/?ind=1461685668841&wpdmdl=3718','source_pdf_sha256':sha(source/'agard_ar138.pdf'),'source_pdf_page_1_based':198,'printed_page':'A6-17','table':'Table 6.7 continued, Case6, upper-surface last row','inspection':'Rendered original table read visually. x/c=0.0002, p/H=0.8142, physical Cp=+0.4219. Neighbour x/c=0.0008 has Cp=+0.1042. NASA GENPLOT file encodes -Cp overall but this one entry has +0.4219, so its decoded physical Cp is -0.4219.','correction':{'side':'upper','x_over_c':.0002,'downloaded_normalized_Cp':-.4219,'original_published_Cp':.4219,'reason':'Original experimental table, not agreement with prediction'},'downloaded_reference_sha256':sha(BASE/'reviewer_only/cp.exp.gen'),'original_reference_preserved':True,'predeclared_thresholds_unchanged':True,'case_results':rows,'qualification_note':'This corrects a documented transcription discrepancy; it does not repair geometry, mesh, convergence, farfield or remaining experimental errors.'}
save(out/'reports/review_reference_source_audit.json',result)
print(json.dumps({r['label']:{'corrected_RMSE':r['all']['RMSE'],'max_error':r['all']['max_abs_error'],'passed':r['pressure_magnitude_gates_passed']} for r in rows},indent=2))
