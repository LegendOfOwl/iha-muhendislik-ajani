"""Analytic-field probe of mesh edge stencils, NOT native SU2 execution.

Matches the inverse-distance-squared normal equations in SU2 v8.5.0's
computeGradientsLeastSquares.hpp. NumPy arithmetic, no periodic/symmetry
corrections. It cannot attribute a CFD discrepancy to the gradient operator.
"""
from pathlib import Path
import sys,json,os
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
import numpy as np

def mesh(path):
    lines=path.read_text().splitlines();edges=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if line.startswith('NELEM'):
            n=int(line.split('=')[1])
            for row in lines[i+1:i+1+n]:
                z=list(map(int,row.split()));c=z[1:4] if z[0]==5 else z[1:5]
                edges.extend(zip(c,c[1:]+c[:1]))
            i+=n
        elif line.startswith('NPOIN'):
            n=int(line.split('=')[1].split()[0]);p=np.array([[float(v) for v in row.split()[:2]] for row in lines[i+1:i+1+n]]);i+=n
        i+=1
    edge=np.unique(np.sort(np.asarray(edges),axis=1),axis=0)
    return p,edge

def probe(name):
    p,edge=mesh(OUT/'simulations'/name/'mesh.su2')
    # Directed graph of immediate edge neighbors, the LS source-code stencil.
    i=np.r_[edge[:,0],edge[:,1]];j=np.r_[edge[:,1],edge[:,0]]
    delta=p[j]-p[i];w=1/np.sum(delta**2,axis=1);n=len(p)
    xx=np.bincount(i,weights=w*delta[:,0]**2,minlength=n)
    xy=np.bincount(i,weights=w*delta[:,0]*delta[:,1],minlength=n)
    yy=np.bincount(i,weights=w*delta[:,1]**2,minlength=n)
    det=xx*yy-xy**2;assert np.all(det>1e-20)
    x,y=p.T;r=np.sqrt((x-.025)**2+y*y);r=np.maximum(r,1e-10)
    radial=np.exp(-r/.006)
    fields=[('linear',x+2*y,np.tile([1.,2.],(n,1))),
            ('tangential_sine',np.sin(2*np.pi*x),np.c_[2*np.pi*np.cos(2*np.pi*x),np.zeros(n)]),
            ('radial_exponential',radial,-radial[:,None]/.006*np.c_[(x-.025)/r,y/r])]
    regions={'near_body':(x>-.08)&(x<1.1)&(abs(y)<.15),
             'nose':(x>-.035)&(x<.06)&(abs(y)<.08),
             'aft':(x>.7)&(x<1.01)&(abs(y)<.12)}
    result={'case':name,'scope':'Analytic-field edge-stencil calculation in NumPy using documented native WLS weights. No SU2 gradients were exported or compared; not an experimental/solver verification.',
            'reference':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/gradients/computeGradientsLeastSquares.hpp',
            'fields':{}}
    for label,f,exact in fields:
        rhs=w*(f[j]-f[i]);bx=np.bincount(i,weights=rhs*delta[:,0],minlength=n);by=np.bincount(i,weights=rhs*delta[:,1],minlength=n)
        grad=np.c_[(yy*bx-xy*by)/det,(xx*by-xy*bx)/det]
        error=np.linalg.norm(grad-exact,axis=1)
        norms={}
        for region,mask in regions.items():
            norm=np.linalg.norm(exact[mask],axis=1);denom=float(np.max(norm))
            meaningful=denom>1e-12
            norms[region]={'points':int(mask.sum()),'relative_L2':float(np.linalg.norm(error[mask])/np.linalg.norm(norm)) if meaningful else None,
                'maximum_error_over_region_max_exact_gradient':float(np.max(error[mask])/denom) if meaningful else None,
                'p99_error_over_region_max_exact_gradient':float(np.quantile(error[mask],.99)/denom) if meaningful else None,
                'normalization_note':'Exact gradient is effectively zero in this region; relative errors undefined.' if not meaningful else None}
        result['fields'][label]=norms
    return result

if __name__=='__main__':
    dest=OUT/'reports/v3_analytic_gradient_probe_v2.json'
    if dest.exists():raise RuntimeError('Preserve previous diagnostic; choose new output version.')
    result={'algorithm_version':2,'revision':'Near-zero exact gradient regions have null relative error instead of a numerical denominator floor; original probe preserved. No CFD fields changed.','cases':[probe(n) for n in sys.argv[1:]]}
    dest.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
