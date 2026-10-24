"""Unapplied proposal: cap the wake tail without changing frozen grid files."""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/projects/proje-15cce2de02'

def redistribute_constant_tail(x,cap):
    x=np.asarray(x);dx=np.diff(x)
    firstcap=int(np.flatnonzero(np.isclose(dx,cap,rtol=1e-10,atol=1e-13))[0])
    start=x[firstcap];length=x[-1]-start;n=int(np.ceil(length/cap))
    return np.r_[x[:firstcap+1],np.linspace(start,x[-1],n+1)[1:]],firstcap

if __name__=='__main__':
    results=[]
    for name,scale in [('coarse',2/3),('medium',1),('fine',1.5)]:
        p=OUT/'simulations'/('v3_cgrid_'+name)/'near_design.json';x=np.array(json.loads(p.read_text())['wake_distribution_x_m']);cap=.05/scale
        new,k=redistribute_constant_tail(x,cap)
        assert np.array_equal(x[:k+1],new[:k+1]) and new[-1]==8 and np.all(np.diff(new)>0) and np.diff(new).max()<=cap+1e-12
        results.append({'level':name,'first_redistributed_x_m':float(x[k]),'unchanged_prefix_nodes':k+1,'old_nodes':len(x),'proposed_nodes':len(new),'old_last_dx_m':float(x[-1]-x[-2]),'proposed_tail_dx_m':float(new[-1]-new[-2]),'cap_m':cap,'max_proposed_dx_m':float(np.diff(new).max()),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    report={'scope':'1D distribution proposal only; not applied to any mesh, config, field or frozen generator. Requires a new mesh revision if authorized. Does not claim to fix shock instability.','results':results,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'reports/prediction_v3_cgrid_unapplied_tail_proposal.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
