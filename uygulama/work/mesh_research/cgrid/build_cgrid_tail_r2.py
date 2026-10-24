# Tail r2: redistribute final constant-step wake tail; source geometry unchanged.
"""Geometry-only C-block prototype. No reference flow results, no solver run.

Source-r2 spline is immutable. Only fluid grid coordinates are constructed here.
The near grid uses explicit row distances and a smooth wall-normal/guide mapping;
the cut is an interior, shared wake line, not a boundary condition.
"""
from pathlib import Path
import os,sys,json,hashlib,time,datetime
ROOT=Path(__file__).resolve().parents[3]
WORK=Path(__file__).resolve().parent
OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
from scipy.interpolate import BSpline
from scipy.integrate import cumulative_trapezoid
import gmsh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def writejson(p,a):Path(p).write_text(json.dumps(a,indent=2,ensure_ascii=False),encoding='utf-8')
def stats(a):
    a=np.asarray(a)
    return dict(min=float(a.min()),median=float(np.median(a)),max=float(a.max()),p99=float(np.quantile(a,.99)))

def load_geometry():
    p=OUT/'simulations/v2_r2_medium/mesh_audit.json'
    a=json.loads(p.read_text());pay=a['interpolation_payload']
    signature=hashlib.sha256(json.dumps(pay,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert signature=='050ee43ead96df3cbc2a34649cf06c0839ed6fe47ae8aaf4955744d19f49cf5a'
    return pay,signature,p

def wall_distribution(pay,scale,upper,first):
    b=BSpline(pay['knots'],pay['coefficients_m'],3)
    t=np.linspace(b.t[3],b.t[-4],60001)
    # Work LE->TE for both source branches; payload lower is TE->LE.
    if not upper:t=t[::-1]
    p=b(t);d1=b(t,1)*(1 if upper else -1);d2=b(t,2)
    ds=np.linalg.norm(np.diff(p,axis=0),axis=1);arc=np.r_[0,np.cumsum(ds)]
    x=p[:,0];k=np.abs(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])/np.linalg.norm(d1,axis=1)**3
    h=np.minimum.reduce([np.full(len(t),.004),.00025+.07*np.maximum(x,0),.00030+.05*np.maximum(1-x,0)])
    if upper:h=np.minimum(h,.0013+.05*np.abs(x-.5178287625312805))
    # Curvature-aware tangential refinement: Gamma proxy <=4 at medium base
    # (reported rather than treated as a universal physical acceptance cutoff).
    h=np.minimum(h,np.sqrt(8*.8e-6/np.maximum(k,1e-8)))
    h=h/scale
    metric=cumulative_trapezoid(1/h,arc,initial=0)
    n=int(np.ceil(metric[-1]));target=np.linspace(0,metric[-1],n+1)
    tt=np.interp(target,metric,t);ss=np.interp(target,metric,arc)
    pp=b(tt);tan=b(tt,1)*(1 if upper else -1);tan/=np.linalg.norm(tan,axis=1)[:,None]
    normal=np.c_[-tan[:,1],tan[:,0]] if upper else np.c_[tan[:,1],-tan[:,0]]
    # At the sharp TE a C cut uses vertical rays; smooth in x over aft .1c.
    blend=np.clip((pp[:,0]-.9)/.1,0,1);blend=blend**2*(3-2*blend)
    vertical=np.tile([0.,1. if upper else -1.],(len(tt),1))
    wall_normal=normal*(1-blend[:,None])+vertical*blend[:,None]
    wall_normal/=np.linalg.norm(wall_normal,axis=1)[:,None]
    # Explicit nonsingular guide rays, independent of solution/expected shock.
    # Nose rays turn smoothly from upstream at LE to vertical before x=.3.
    guide=np.c_[-.018/np.sqrt(.018**2+ss**2),(1 if upper else -1)*ss/np.sqrt(.018**2+ss**2)]
    gblend=np.clip((pp[:,0]-.15)/.15,0,1);gblend=gblend**2*(3-2*gblend)
    guide=guide*(1-gblend[:,None])+vertical*gblend[:,None]
    guide/=np.linalg.norm(guide,axis=1)[:,None]
    return dict(points=pp,normal=normal,wall_normal=wall_normal,guide=guide,t=tt,arclength=ss,bspline=b)

def normal_distribution(scale,H=.06):
    first=.8e-6/scale;ratio=1+.14/scale;cap=.00075/scale
    increments=[];total=0.;step=first
    while step<cap and total+step<H:
        increments.append(step);total+=step;step=min(step*ratio,cap)
    # Redistribute the final residual over the constant-spacing section, so that
    # the last cell is not an arbitrarily tiny leftover.
    ncap=max(1,int(np.ceil((H-total)/cap)))
    increments.extend([(H-total)/ncap]*ncap)
    d=np.r_[0,np.cumsum(increments)];d[-1]=H
    return d,dict(first_m=first,growth_design=ratio,cap_m=cap,thickness_m=H,layers=len(increments),increments_m=increments)

def map_wall(w,d):
    blend=1-np.exp(-(d/.003)**2)
    direction=(1-blend[:,None,None])*w['wall_normal'][None,:,:]+blend[:,None,None]*w['guide'][None,:,:]
    direction/=np.linalg.norm(direction,axis=2)[:,:,None]
    return w['points'][None,:,:]+d[:,None,None]*direction

def wake_distribution(scale,L=8.):
    x=[1.];step=.00030/scale
    while x[-1]+step<L:
        x.append(x[-1]+step);step=min(step*(1+.035/scale),.05/scale)
    x[-1]=L
    x=np.array(x)
    cap=.05/scale
    firstcap=int(np.flatnonzero(np.isclose(np.diff(x),cap,rtol=1e-10,atol=1e-13))[0])
    start=x[firstcap];n=int(np.ceil((L-start)/cap))
    revised=np.r_[x[:firstcap+1],np.linspace(start,L,n+1)[1:]]
    assert revised[-1]==L and np.diff(revised).min()>0 and np.diff(revised).max()<=cap+1e-12
    return revised

def mesh_near(scale):
    pay,sig,src=load_geometry();d,nd=normal_distribution(scale)
    w=[wall_distribution(p,scale,i==0,nd['first_m']) for i,p in enumerate(pay)]
    up,lo=[map_wall(a,d) for a in w]
    # Clockwise body contour lower TE -> LE -> upper TE; LE only once.
    body=np.concatenate([lo[:,::-1,:],up[:,1:,:]],axis=1)
    x=wake_distribution(scale);a=np.deg2rad(2.31);center=np.c_[x,np.tan(a)*(x-1)]
    z=np.clip((x-1)/7,0,1);weight=z**2*(3-2*z)
    # Wake rows gradually become nearly uniform across the widening block,
    # avoiding sub-micron streamwise ribbons all the way to the downstream end.
    distance=(1-weight[None,:])*d[:,None]+weight[None,:]*(.06+.24*z)[None,:]*(np.arange(len(d))/(len(d)-1))[:,None]
    wu=np.broadcast_to(center[None,:,:],(len(d),len(x),2)).copy();wl=wu.copy()
    wu[:,:,1]+=distance;wl[:,:,1]-=distance
    # C-shaped index curve downstream lower -> TE -> LE -> TE -> downstream upper.
    grid=np.concatenate([wl[:,1:,:][:,::-1,:],body,wu[:,1:,:]],axis=1)
    nj,ni,_=grid.shape
    ids=np.arange(nj*ni).reshape(nj,ni)
    # The cut is interior. Merge both coincident wake edges and the sharp TE.
    nW=len(x)-1;nL=len(w[1]['points'])-1;nU=len(w[0]['points'])-1
    for k in range(nW+1):ids[0,nW+nL+nU+k]=ids[0,nW-k]
    flat=grid.reshape(-1,2);unique,inv=np.unique(ids.ravel(),return_inverse=True)
    points=flat[unique];idx=inv.reshape(nj,ni)
    # The clockwise inner curve, then outward, yields CCW fluid cells.
    quads=np.stack([idx[:-1,:-1],idx[:-1,1:],idx[1:,1:],idx[1:,:-1]],axis=2).reshape(-1,4)
    wall=np.stack([idx[0,nW:nW+nL+nU],idx[0,nW+1:nW+nL+nU+1]],axis=1)
    # Outer boundary: entire C top row, then downstream vertical closure.
    # Two short row-column paths close at the shared wake centerline node.
    interface=np.concatenate([idx[-1,:],idx[-2::-1,-1],idx[1:-1,0]])
    assert len(set(interface.tolist()))==len(interface)
    detail={'normal':nd,'wall_upper_segments':nU,'wall_lower_segments':nL,'wake_segments_each_side':nW,'body_offset_blend':'exact source normal -> fixed smooth guide: b(d)=1-exp(-(d/.003)^2); TE x>.9 smoothly turns wall ray vertical, preserving sharp vertex','wake_centerline':'y=tan(2.31deg)*(x-1), shared interior cut, x1..8c','wake_distribution_x_m':x.tolist(),'wake_outer_halfwidth_m':(.06+.24*z).tolist(),'near_rows_distance_m':d.tolist(),'geometry_payload':pay,'curve_definition_sha256':sig,'geometry_payload_source':str(src.relative_to(ROOT)),'wake_grid_point_count':len(x),'grid_shape':list(grid.shape),'wall_parameter_upper':w[0]['t'].tolist(),'wall_parameter_lower':w[1]['t'].tolist()}
    return points,quads,wall,interface,grid,idx,w,detail

def outer_mesh(points,interface,scale,R=200.):
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    gmsh.model.add('Cgrid_outer');g=gmsh.model.geo
    bp=[g.addPoint(float(x),float(y),0) for x,y in points[interface]]
    be=[g.addLine(bp[i],bp[(i+1)%len(bp)]) for i in range(len(bp))]
    farpts=[g.addPoint(x,y,0) for x,y in [(-R,-R),(R,-R),(R,R),(-R,R)]]
    fe=[g.addLine(farpts[i],farpts[(i+1)%4]) for i in range(4)]
    s=g.addPlaneSurface([g.addCurveLoop(fe),g.addCurveLoop(be)]);g.synchronize()
    for e in be:gmsh.model.mesh.setTransfiniteCurve(e,2)
    def sizing(dim,tag,x,y,z,lc):
        # Distances here choose ONLY exterior triangle sizes, never the geometry.
        near=np.hypot(max(-x,x-1,0),max(abs(y)-.1,0))
        hwake=.035+.15*abs(y-np.tan(np.deg2rad(2.31))*(x-1)) if 1<x<10 else 1e9
        return min(.012+.24*near,hwake,3.+.12*max(abs(x)-20,abs(y)-20,0))/scale
    gmsh.model.mesh.setSizeCallback(sizing)
    for opt,v in [('Mesh.MeshSizeExtendFromBoundary',0),('Mesh.MeshSizeFromPoints',0),('Mesh.MeshSizeFromCurvature',0),('Mesh.Algorithm',6)]:gmsh.option.setNumber(opt,v)
    gmsh.model.mesh.generate(2)
    tags,xyz,_=gmsh.model.mesh.getNodes();xyz=np.asarray(xyz).reshape(-1,3)[:,:2]
    tagsmap={int(t):i for i,t in enumerate(tags)}
    ty,ets,cons=gmsh.model.mesh.getElements(2)
    triangles=[]
    for t,c in zip(ty,cons):
        assert t==2
        triangles.extend([[tagsmap[int(a)] for a in row] for row in np.asarray(c).reshape(-1,3)])
    far=[]
    for e in fe:
        _,_,ns=gmsh.model.mesh.getElements(1,e)
        far.extend([[tagsmap[int(a)] for a in row] for row in np.asarray(ns[0]).reshape(-1,2)])
    # Exactly the original explicit-block interface nodes are retained by the
    # transfinite 2-node curve constraints; merge by geometric tolerance 2e-12m.
    lookup={tuple(np.round(q,12)):int(i) for i,q in enumerate(points)}
    new=list(points);mapping=[];matched=[]
    for q in xyz:
        key=tuple(np.round(q,12))
        if key in lookup:
            j=lookup[key];assert np.linalg.norm(new[j]-q)<2e-12;matched.append(j)
        else:j=len(new);new.append(q);lookup[key]=j
        mapping.append(j)
    assert set(matched)==set(interface.tolist()),(len(set(matched)),len(interface))
    mapping=np.asarray(mapping);tri=mapping[np.asarray(triangles)];far=mapping[np.asarray(far)]
    gmsh.finalize()
    return np.asarray(new),tri,far

def area_jac(p,q):
    v=p[q];w=np.roll(v,-1,axis=1)
    area=.5*np.sum(v[:,:,0]*w[:,:,1]-w[:,:,0]*v[:,:,1],axis=1)
    e=w-v;prev=np.roll(e,1,axis=1)
    jac=(prev[:,:,0]*e[:,:,1]-prev[:,:,1]*e[:,:,0])
    return area,jac

def write_su2(path,p,quads,tri,wall,far):
    with path.open('w') as f:
        f.write(f'NDIME= 2\nNELEM= {len(quads)+len(tri)}\n')
        for i,c in enumerate(quads):f.write('9 '+' '.join(map(str,c))+f' {i}\n')
        for i,c in enumerate(tri,len(quads)):f.write('5 '+' '.join(map(str,c))+f' {i}\n')
        f.write(f'NPOIN= {len(p)}\n')
        for i,(x,y) in enumerate(p):f.write(f'{x:.17g} {y:.17g} {i}\n')
        f.write('NMARK= 2\n')
        for name,edges in [('AIRFOIL',wall),('FARFIELD',far)]:
            f.write(f'MARKER_TAG= {name}\nMARKER_ELEMS= {len(edges)}\n')
            for a,b in edges:f.write(f'3 {a} {b}\n')

def run(level,outer=True):
    start=time.time();scale={'coarse':2/3,'medium':1.,'fine':1.5}[level]
    name='v3_cgrid_tailr2_'+level;folder=OUT/'simulations'/name;folder.mkdir(exist_ok=True,parents=True)
    if (folder/'mesh.su2').exists():raise RuntimeError('Preserve previous mesh; choose a new revision folder instead of overwriting.')
    p,q,wall,interface,grid,idx,w,detail=mesh_near(scale)
    a,j=area_jac(p,q)
    print(name,'near nodes/cells',len(p),len(q),'area min',a.min(),'cornerjac min',j.min(),flush=True)
    np.savez_compressed(folder/'near_arrays.npz',points=p,quads=q,wall=wall,interface=interface,grid=grid,grid_ids=idx)
    writejson(folder/'near_design.json',detail)
    if not np.all(j>0):
        bad=np.flatnonzero(np.any(j<=0,axis=1));writejson(folder/'FAILED_near_jacobian.json',{'min':float(j.min()),'count':len(bad),'cells':bad.tolist(),'centers_m':p[q[bad]].mean(1).tolist()});return
    if outer:p,tri,far=outer_mesh(p,interface,scale)
    else:tri=np.empty((0,3),int);far=np.stack([interface,np.roll(interface,-1)],axis=1)
    write_su2(folder/'mesh.su2',p,q,tri,wall,far)
    np.savez_compressed(folder/'mesh_arrays.npz',points=p,quads=q,triangles=tri,wall=wall,farfield=far,grid_ids=idx)
    writejson(folder/'build_metadata.json',{'name':name,'level':level,'scale':scale,'elapsed_seconds':time.time()-start,'nodes':len(p),'quads':len(q),'triangles':len(tri),'cells':len(q)+len(tri),'domain_bounds_m':[-200,200,-200,200] if outer else None,'near_detail':'near_design.json','mesh_sha256':sha(folder/'mesh.su2'),'script_sha256':sha(__file__),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print('DONE',len(p),len(q)+len(tri),'seconds',time.time()-start,flush=True)

if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'medium','--near-only' not in sys.argv)
