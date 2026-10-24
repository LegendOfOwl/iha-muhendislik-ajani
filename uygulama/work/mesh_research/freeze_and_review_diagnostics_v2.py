"""Seal completed diagnostic cases, then compare all source experiment points.

Not a new blind test: the parent knows the older published comparison.
No outcome-dependent change to the preselected fine validation role.
"""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
sys.path.insert(0,str(ROOT/'work/blind_validation/reviewer'))
from evaluate import evaluate_one,metrics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(tag,names):
    family='v3_r4roe_family_plan_seal.json' if all(n.startswith('v3_r4roe_') for n in names) else 'v3_r4_family_plan_seal.json'
    plan_path=OUT/'reports'/family;plan=json.loads(plan_path.read_text())
    assert all(n in plan['roles'].values() for n in names),'Do not mix method families'
    fine_role=plan['roles']['fine']
    frozen=OUT/'reports'/f'v3_diagnostic_freeze_{tag}.json'
    if frozen.exists():raise RuntimeError('Never overwrite a freeze/review; use a fresh tag.')
    files={};selections={}
    for name in names:
        folder=OUT/'simulations'/name
        assert (folder/'run_status.json').exists(),'Native attempt must have ended'
        for p in sorted(folder.rglob('*')):
            if p.is_file():files[str(p.relative_to(ROOT))]=sha(p)
        selections[name]=json.loads((folder/'checkpoint_selection.json').read_text())
    code=[Path(__file__),ROOT/'work/mesh_research/cgrid/build_cgrid_interface_r4.py',ROOT/'work/mesh_research/cgrid/interface_distance_r4.py',ROOT/'work/mesh_research/research_addendum_02.md',ROOT/'work/mesh_research/run_case.py',ROOT/'work/mesh_research/prepare_roe_control.py',ROOT/'work/blind_validation/reviewer/evaluate.py',ROOT/'work/blind_validation/solver_v2/postprocess.py']
    a={'created_utc':datetime.now(timezone.utc).isoformat(),'role':'Completed diagnostic predictions before current-version pointwise scoring; not independent blind validation.',
       'cases':names,'selections':selections,'files_sha256':files,'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in code},'contract_sha256':sha(ROOT/'work/blind_validation/contract.json'),
       'main_family_fine_role_unchanged':fine_role,'family_plan':family,'family_plan_sha256':sha(plan_path)}
    frozen.write_text(json.dumps(a,indent=2))
    # Read back and verify the just-written prediction freeze before scoring.
    a=json.loads(frozen.read_text())
    assert all(sha(ROOT/p)==h for p,h in a['files_sha256'].items())
    contract=json.loads((ROOT/'work/blind_validation/contract.json').read_text());el=contract['experimental_Cp']
    rows=[];fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    for name in names:
        sel=selections[name];raw,ref,sides,pred,branches=evaluate_one(ROOT/sel['surface'])
        upper=sides=='upper';fixed=ref.copy();mask=upper&np.isclose(ref[:,0],.0002,atol=1e-10)
        assert mask.sum()==1 and np.isclose(ref[mask,1][0],-.4219)
        fixed[mask,1]=.4219
        stats={'all':metrics(pred,fixed[:,1]),'upper':metrics(pred[upper],fixed[upper,1]),'lower':metrics(pred[~upper],fixed[~upper,1])}
        checks={'RMSE':stats['all']['RMSE']<=el['pointwise_RMSE_max'],'upper_RMSE':stats['upper']['RMSE']<=el['per_side_RMSE_max'],'lower_RMSE':stats['lower']['RMSE']<=el['per_side_RMSE_max'],'p95':stats['all']['p95_abs_error']<=el['p95_absolute_error_max'],'max_error':stats['all']['max_abs_error']<=el['max_absolute_error_max'],'shock_location':raw['shock_location_abs_error_chords']<=el['shock_location_abs_error_chords_max']}
        stats['checks']=checks;stats['passed']=all(checks.values())
        folder=OUT/'simulations'/name;m=json.loads((folder/'prediction_metrics.json').read_text())
        rows.append({'case':name,'role':'preselected fine' if name==fine_role else 'diagnostic only; cannot replace fine','field_iteration':sel['iteration'],'run':json.loads((folder/'run_status.json').read_text()),'numerical':{k:v for k,v in m.items() if k not in ['Cp_by_side','history_last','own_predicted_gradient']},'raw_downloaded_reference_comparison':raw,'original_table_comparison':stats,'minimum_qualification_passed':False})
        data=np.c_[ref[:,0],upper.astype(int),ref[:,1],fixed[:,1],pred,pred-fixed[:,1]]
        np.savetxt(OUT/'data/review'/f'v3_{tag}_{name}_all103.csv',data,delimiter=',',header='x_over_c,is_upper,Cp_NASA_normalized,Cp_original_table,Cp_prediction,error_original_table',comments='')
        for side,ls in [('upper','-'),('lower','--')]:axs[0].plot(branches[side][:,0],branches[side][:,2],ls,label=name if side=='upper' else None,lw=1)
        axs[1].plot(fixed[:,0],pred-fixed[:,1],'.',label=name,ms=3)
    axs[0].plot(fixed[:,0],fixed[:,1],'ko',ms=2,label='Original experiment, all103');axs[0].invert_yaxis();axs[0].set(xlabel='x/c',ylabel='Cp');axs[0].legend(fontsize=6)
    axs[1].axhline(0,color='gray',lw=.5);axs[1].set(xlabel='x/c',ylabel='prediction - original experiment');axs[1].legend(fontsize=6)
    for ax in axs:ax.grid(alpha=.2)
    fig.suptitle('V3 completed diagnostics, original thresholds and all points retained');fig.tight_layout();fig.savefig(OUT/'plots'/f'v3_{tag}_diagnostic_Cp.png',dpi=170);plt.close(fig)
    result={'created_utc':datetime.now(timezone.utc).isoformat(),'freeze_sha256':sha(frozen),'frozen_file_count':len(files),'frozen_files_verified':True,'cases':rows,
       'reference_correction':'Same independently proven single NASA GENPLOT sign transcription at upperx/c=.0002; raw comparison retained, all103 points retained. Original AGARD Table6.7/A6-17 evidence in v2 review.',
       'main_fine_validation_unchanged':True,'minimum_qualification_passed':False,'scope':'Diagnostic continuation, no general airfoil, M6 or UAV acceptance.'}
    (OUT/'reports'/f'v3_diagnostic_review_{tag}.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'tag':tag,'frozen_files':len(files),'cases':{r['case']:{'Cp_RMSE':r['original_table_comparison']['all']['RMSE'],'experiment_pass':r['original_table_comparison']['passed'],'numerical':r['numerical']['checks']} for r in rows}},indent=2))
if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
