"""Create a fresh full mesher revision for the independently found tail cap bug.

The original generator and all existing case meshes stay byte-for-byte intact.
No claim that this distant correction solves the shock convergence failure.
"""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    old=HERE/'build_cgrid.py';new=HERE/'build_cgrid_tail_r2.py'
    assert sha(old)=='9d385936e598c2371179f8a5a4fe44e44964b2ccc1c5a6d674b1f62912a48637'
    assert not new.exists(),'Preserve the created revision'
    source=old.read_text()
    before='    x[-1]=L\n    return np.array(x)'
    after='''    x[-1]=L
    x=np.array(x)
    cap=.05/scale
    firstcap=int(np.flatnonzero(np.isclose(np.diff(x),cap,rtol=1e-10,atol=1e-13))[0])
    start=x[firstcap];n=int(np.ceil((L-start)/cap))
    revised=np.r_[x[:firstcap+1],np.linspace(start,L,n+1)[1:]]
    assert revised[-1]==L and np.diff(revised).min()>0 and np.diff(revised).max()<=cap+1e-12
    return revised'''
    assert source.count(before)==1
    assert source.count("name='v3_cgrid_'+level")==1
    source=source.replace(before,after).replace("name='v3_cgrid_'+level","name='v3_cgrid_tailr2_'+level")
    new.write_text('# Tail r2: redistribute final constant-step wake tail; source geometry unchanged.\n'+source)
    (HERE/'tail_r2_revision_manifest.json').write_text(json.dumps({'original_script':str(old.relative_to(ROOT)),'original_sha256':sha(old),'revised_script':str(new.relative_to(ROOT)),'revised_sha256':sha(new),'changed':'Only final constant-step wake tail and output namespace; source r2 geometry and all body/normal distributions unchanged. New fluid-grid revision, not same-mesh convergence.','all_prior_cases_unchanged':True,'not_a_validated_CFD_fix':True},indent=2))
    print(new)
if __name__=='__main__':main()
