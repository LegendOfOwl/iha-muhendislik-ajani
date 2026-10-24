"""Source numerical curve diagnostic; never call WIND data an experiment."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
sys.path.insert(0,str(ROOT/'work/blind_validation/reviewer'))
from evaluate import reference,metrics,sha
import numpy as np

def main():
    dest=OUT/'reports/v3_published_WIND_diagnostic.json'
    # First scratch comparison reused the experiment's upper-first convention.
    # Preserve it; the correction is established from the published grid indexing
    # and CFPOST subset, not agreement with our predictions.
    if dest.exists():
        old=json.loads(dest.read_text())
        if old.get('algorithm_version')==2:raise RuntimeError('Version2 already exists')
        (OUT/'reports/v3_published_WIND_diagnostic_v1_wrong_branch_order.json').write_bytes(dest.read_bytes())
    ref,upper=reference('cp.exp.gen');corrected=ref.copy()
    mask=upper&np.isclose(ref[:,0],.0002,atol=1e-10);assert mask.sum()==1;corrected[mask,1]=.4219
    curve,beforeLE=reference('cp.wind.gen')
    gridvalues=np.fromstring((ROOT/'work/blind_validation/reviewer/additional_sources/raetaf.x.fmt').read_text(),sep=' ')
    xy=gridvalues[2:].reshape(2,65,369).transpose(1,2,0)[0,32:337]
    assert len(curve)==305 and np.max(abs(curve[:,0]-xy[:,0]))<1e-6
    # CFPOST 'subset i33 337 j1 k1' follows lower TE -> LE -> upper TE,
    # documented by NASA Study1's Grid section. The experiment is upper-first.
    assert 'subset i 33 337 j 1 k 1' in (ROOT/'work/blind_validation/reviewer_only/cfpost.cp.com').read_text()
    pred=np.empty(len(ref))
    ile=int(np.argmin(curve[:,0]))
    for side,isupper in [('upper',True),('lower',False)]:
        # The same measured LE endpoint belongs to both contiguous branches;
        # include it in each, rather than extrapolating the first upper sample.
        b=curve[ile:] if isupper else curve[:ile+1];b=b[np.argsort(b[:,0])]
        m=upper==isupper;assert ref[m,0].min()>=b[:,0].min() and ref[m,0].max()<=b[:,0].max()
        pred[m]=np.interp(ref[m,0],b[:,0],b[:,1])
    a={'algorithm_version':2,'role':'Published WIND numerical curve, not our solver and not experimental coefficients',
       'source':'https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html',
       'branch_order_evidence':'https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf01/raetaf01.html#grid; lower TE I33 to upper TE I337; CFPOST exact subset and all305 x values verified against source grid.',
       'source_file_sha256':sha(ROOT/'work/blind_validation/reviewer_only/cp.wind.gen'),
       'misleading_file_header':'Experiment label in cp.wind.gen comes from CFPOST curve1 title; source page identifies generated WIND data.',
       'raw_reference':metrics(pred,ref[:,1]),'original_table_reference':metrics(pred,corrected[:,1]),'upper':metrics(pred[upper],corrected[upper,1]),'lower':metrics(pred[~upper],corrected[~upper,1]),
       'correction_scope':'Only this published numerical diagnostic branch classifier corrected. Native SU2 predictions, original sources, contract and v1/v2 reviewers unchanged. Initial wrong-order score preserved separately.',
       'threshold_unchanged':.03,'our_qualification_unchanged':False}
    dest.write_text(json.dumps(a,indent=2))
    np.savetxt(OUT/'data/review/v3_published_WIND_all103.csv',np.c_[ref[:,0],upper.astype(int),corrected[:,1],pred,pred-corrected[:,1]],delimiter=',',header='x_over_c,is_upper,Cp_original_experiment,Cp_published_WIND,Cp_difference',comments='')
    print(json.dumps(a,indent=2))
if __name__=='__main__':main()
