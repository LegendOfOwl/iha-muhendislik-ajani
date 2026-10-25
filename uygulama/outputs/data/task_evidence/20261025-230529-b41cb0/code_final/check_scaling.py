from prepare import ROOT,CASE,save,now,read
from scaled_restart import convert,decode,primitive,scales
from run import history
import numpy as np
import struct

def main():
    free={'rho_kg_m3':2.,'U_m_s':60.}
    names=['x','y','Density','Momentum_x','Momentum_y','Energy','Nu_Tilde']
    labels=b''.join(n.encode().ljust(33,b'\0') for n in names)
    q=np.array([[.2,.1,2.,120.,6.,253609.,1e-5]],dtype='<f8')
    raw=struct.pack('<5i',535532,7,1,0,0)+labels+q.tobytes()
    nd,check=convert(raw,free);data=decode(nd)[2];rho,u,p=primitive(data)
    assert np.allclose(rho,[1.]) and np.allclose(u,[[.2,.01]])
    assert np.allclose(p,[1e5/(2*300**2)]) and abs(data[0,6]-1e-5/300)<1e-20
    passed=['analytic conservative-variable SI/ND identity']
    for name,bad in [('wrong binary magic',b'xxxx'+raw[4:]),('truncated payload',raw[:-1]),
                     ('nonpositive state',struct.pack('<5i',535532,7,1,0,0)+labels+np.array([[.2,.1,0.,0.,0.,0.,0.]],dtype='<f8').tobytes())]:
        try:
            with np.errstate(all='ignore'):convert(bad,free)
        except (AssertionError,ValueError):passed.append(name)
        else:raise AssertionError('Accepted '+name)
    a=history(CASE/'ilu_pair/lusgs')[0];b=history(CASE/'warm_scaling_pair_v1/scaled')[0]
    factors=scales(read(CASE/'contract.json')['derived_freestream'])['residual']
    errors={k:abs(a[k]-(b[k]+np.log10(v))) for k,v in factors.items()}
    save(ROOT/'outputs/reports/flatplate_scaling_guards_20261025.json',{'checked_utc':now(),'passed':len(passed),
         'checks':passed,'native_first_row_log10_differences_after_conversion':errors,'native_CD_first_row_difference':abs(a['CD']-b['CD']),
         'native_exact_residual_identity_accepted':False,
         'preserved_rejected_draft':'work/flatplate_20261025/check_scaling_v1_rejected.py',
         'draft_failure':'An unmotivated1e-5log all-component identity assertion failed for weak vertical momentum:2.31285e-5log. Analytic scaling is tested separately; this native comparison is retained as observation without a new relaxed pass threshold.',
         'physical_qualification':False})
    print({'passed':len(passed),'native_residual_identity_max_log_difference':max(errors.values())})

if __name__=='__main__':main()
