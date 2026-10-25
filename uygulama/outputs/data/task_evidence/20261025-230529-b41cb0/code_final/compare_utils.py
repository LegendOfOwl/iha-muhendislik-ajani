"""Strict reference reading and error accounting; invalid samples cannot disappear."""
import re,numpy as np

def zones(path,columns):
    output=[];label='unlabelled';values=[]
    def flush():
        nonlocal values
        if values:
            assert len(values)%columns==0,(path,label,len(values),columns)
            output.append((label,np.array(values).reshape(-1,columns)));values=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        s=line.strip()
        if s.lower().startswith('zone'):
            flush();label=s
        elif re.match(r'^[+\-.]?\d',s):
            values.extend(float(v.replace('D','E').replace('d','e')) for v in s.split())
    flush();assert output
    return output

def relative_l2(pred,reference,valid):
    pred=np.asarray(pred);reference=np.asarray(reference);valid=np.asarray(valid)
    if not valid.all() or not np.isfinite(pred).all() or not np.isfinite(reference).all() or np.linalg.norm(reference)==0:return None
    return float(np.linalg.norm(pred-reference)/np.linalg.norm(reference))

def interpolate(x,v,requested):
    order=np.argsort(x);x=np.asarray(x)[order];v=np.asarray(v)[order];requested=np.asarray(requested)
    assert np.all(np.diff(x)>0)
    valid=np.isfinite(requested)&(requested>=x[0])&(requested<=x[-1])
    value=np.full(requested.shape,np.nan);value[valid]=np.interp(requested[valid],x,v)
    return value,valid

def check():
    assert relative_l2([1,2],[1,2],[True,True])==0
    assert relative_l2([1,0],[1,2],[True,False]) is None
    v,m=interpolate([0,1],[0,1],[-.1,.5]);assert not m[0] and np.isnan(v[0]) and v[1]==.5
    assert relative_l2(v,[0,.5],m) is None
    return {'analytic_identity':True,'invalid_profile_not_scored':True,'out_of_domain_no_extrapolation':True}

if __name__=='__main__':print(check())
