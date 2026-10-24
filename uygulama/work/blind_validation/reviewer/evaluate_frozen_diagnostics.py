"""Additional frozen numerical prototypes: never substitute them for the selected family."""
from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02'
sys.path.insert(0,str(Path(__file__).parent))
from evaluate import read,save,sha,evaluate_one,metrics
snap=read(OUT/'reports/prediction_v2_frozen.json');files=snap['case_files_sha256'];results=[]
for name in ['v2_diag_jst','v2_diag_mat','v2_r3_medium']:
 folder=OUT/'simulations'/name;sel=read(folder/'checkpoint_selection.json');p=ROOT/sel['surface'];key=str(p.relative_to(ROOT)).replace('\\','/')
 assert files[key]==sha(p)
 raw,ref,sides,pred,b=evaluate_one(p);mask=(sides=='upper')&np.isclose(ref[:,0],.0002,atol=1e-10);assert mask.sum()==1;corrected=ref.copy();corrected[mask,1]=.4219
 m=metrics(pred,corrected[:,1]);results.append({'case':name,'field_iteration':sel['iteration'],'source_surface_sha256':sha(p),'original_table_corrected_all103_Cp':m,'downloaded_reference_Cp':raw['all'],'source_numerical_metrics':read(folder/'prediction_metrics.json')['checks'],'accepted_as_main_family':False})
 np.savetxt(OUT/'data/review'/f'diagnostic_{name}_all103.csv',np.column_stack([ref[:,0],(sides=='upper').astype(int),corrected[:,1],pred,pred-corrected[:,1]]),delimiter=',',header='x_over_c,is_upper,Cp_original_table,Cp_prediction,error',comments='')
save(OUT/'reports/review_frozen_diagnostics.json',{'frozen_sha256':sha(OUT/'reports/prediction_v2_frozen.json'),'selection_rule':'These are ALL three completed post-v1 numerical diagnostics named in the frozen study; chosen main family remains unchanged. Single medium BL prototype cannot replace a three-level family. No physical condition adjusted after review.','case_results':results})
print(json.dumps({r['case']:r['original_table_corrected_all103_Cp']['RMSE'] for r in results},indent=2))
