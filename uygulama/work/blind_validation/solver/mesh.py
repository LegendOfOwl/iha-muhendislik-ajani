"""Fresh viscous meshes from the supplied published coordinate tables only."""
from pathlib import Path
import sys,json,hashlib,time,os
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
import numpy as np
import gmsh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/'work/blind_validation/analysis_input'
OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def generate(level, radius=20.,gradient=None):
    idx={'coarse':0,'medium':1,'fine':2}[level]
    scale=1.5**idx; name=level+('_far' if radius!=20 else '')
    folder=OUT/'simulations'/name;folder.mkdir(parents=True,exist_ok=True)
    table=np.loadtxt(INPUT/'geom.txt',skiprows=5)
    assert table.shape==(65,3)
    # The published Fortran routine negates the lower ordinate column.
    lower=np.c_[table[:,0],-table[:,1]];upper=table[:,[0,2]]
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',1)
    gmsh.model.add(name);g=gmsh.model.geo
    le=g.addPoint(0,0,0);te=g.addPoint(1,0,0)
    up=[le]+[g.addPoint(x,y,0) for x,y in upper[1:-1]]+[te]
    lo=[te]+[g.addPoint(x,y,0) for x,y in lower[-2:0:-1]]+[le]
    curves=[g.addSpline(up),g.addSpline(lo)]
    loop=g.addCurveLoop(curves)
    pts=[g.addPoint(x,y,0) for x,y in [(-radius,-radius),(radius,-radius),(radius,radius),(-radius,radius)]]
    outer=[g.addLine(pts[i],pts[(i+1)%4]) for i in range(4)]
    surf=g.addPlaneSurface([g.addCurveLoop(outer),loop]);g.synchronize()
    gmsh.model.addPhysicalGroup(1,curves,1);gmsh.model.setPhysicalName(1,1,'AIRFOIL')
    gmsh.model.addPhysicalGroup(1,outer,2);gmsh.model.setPhysicalName(1,2,'FARFIELD')
    gmsh.model.addPhysicalGroup(2,[surf],3);gmsh.model.setPhysicalName(2,3,'FLUID')
    n=int(round(180*scale))+1
    if gradient:
        def wall_size(dim,tag,x,y,z,lc):
            if (dim==1 and tag in curves) or (dim==0 and tag in [le,te]):
                h=min(.006,.0005+.07*max(x,0),.0006+.05*max(1-x,0))
                for side,xg in gradient.items():
                    if (side=='upper' and tag==curves[0]) or (side=='lower' and tag==curves[1]):h=min(h,.0016+.05*abs(x-xg))
                return h/scale
            return lc
        gmsh.model.mesh.setSizeCallback(wall_size)
    else:
        for c in curves: gmsh.model.mesh.setTransfiniteCurve(c,n,'Bump',0.12)
    f=gmsh.model.mesh.field
    bl=f.add('BoundaryLayer');f.setNumbers(bl,'CurvesList',curves)
    first=1.2e-6/scale;ratio=1+.26/scale
    f.setNumber(bl,'Size',first);f.setNumber(bl,'Ratio',ratio)
    thickness=.01
    f.setNumber(bl,'Thickness',thickness);f.setNumber(bl,'Quads',1)
    f.setNumbers(bl,'FanPointsList',[te]);f.setNumbers(bl,'FanPointsSizesList',[16*scale])
    f.setAsBoundaryLayer(bl)
    dist=f.add('Distance');f.setNumbers(dist,'CurvesList',curves);f.setNumber(dist,'Sampling',1000)
    near=f.add('Threshold');f.setNumber(near,'InField',dist)
    for k,v in [('SizeMin',.008/scale),('SizeMax',2.4/scale),('DistMin',.015),('DistMax',8.)]:f.setNumber(near,k,v)
    wake=f.add('Box')
    for k,v in [('VIn',.035/scale),('VOut',3.),('XMin',.95),('XMax',6.),('YMin',-.08),('YMax',.18),('Thickness',.7)]:f.setNumber(wake,k,v)
    fields=[near,wake]
    # Any shock refinement is learned from the coarse predicted field, never a reference location.
    if gradient:
        for side,x in gradient.items():
            fld=f.add('Box');ylo,yhi=(-.12,.02) if side=='lower' else (-.02,.18)
            for k,v in [('VIn',.006/scale),('VOut',3.),('XMin',x-.07),('XMax',x+.07),('YMin',ylo),('YMax',yhi),('Thickness',.06)]:f.setNumber(fld,k,v)
            fields.append(fld)
    mi=f.add('Min');f.setNumbers(mi,'FieldsList',fields);f.setAsBackgroundMesh(mi)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0)
    gmsh.option.setNumber('Mesh.Algorithm',6)
    gmsh.option.setNumber('Mesh.Optimize',1)
    gmsh.model.mesh.generate(2)
    tags,coords,_=gmsh.model.mesh.getNodes();coords=np.array(coords).reshape(-1,3)[:,:2]
    order={int(t):i for i,t in enumerate(tags)}
    types,elTags,elNodes=gmsh.model.mesh.getElements(2)
    conn=[];et=[];metrics=[]
    for typ,ts,ns in zip(types,elTags,elNodes):
        nv=gmsh.model.mesh.getElementProperties(typ)[3]
        co=np.array([[order[int(v)] for v in row] for row in np.array(ns).reshape(-1,nv)])
        conn.extend(co);et.extend(np.array(ts).tolist())
    et=np.array(et,dtype=np.uint64)
    areas=[];centers=[];orth=[];skew=[]
    for c in conn:
        p=coords[c];q=np.roll(p,-1,axis=0)
        ar=.5*np.sum(p[:,0]*q[:,1]-q[:,0]*p[:,1]);areas.append(ar);centers.append(p.mean(0))
        vec=q-p;prev=np.roll(vec,1,axis=0)
        ang=np.rad2deg(np.arccos(np.clip(np.sum(-prev*vec,axis=1)/(np.linalg.norm(prev,axis=1)*np.linalg.norm(vec,axis=1)),-1,1)))
        ideal=60. if len(c)==3 else 90.
        skew.append(float(max(np.max((ang-ideal)/(180-ideal)),np.max((ideal-ang)/ideal))))
        # Face-normal vs center-to-edge-midpoint angle; 0 deg is ideal.
        mid=(p+q)/2;d=mid-p.mean(0);normal=np.c_[vec[:,1],-vec[:,0]]
        oa=np.rad2deg(np.arccos(np.clip(np.abs(np.sum(d*normal,1))/(np.linalg.norm(d,axis=1)*np.linalg.norm(normal,axis=1)),0,1)))
        orth.append(float(oa.max()))
    areas=np.array(areas);centers=np.array(centers)
    sizes=np.sqrt(np.abs(areas));regions={}
    for key,mask in {'LE':(centers[:,0]<.05)&(centers[:,0]>-.03)&(abs(centers[:,1])<.1),'TE':(centers[:,0]>.9)&(centers[:,0]<1.05)&(abs(centers[:,1])<.1),'near_wall':(centers[:,0]>=0)&(centers[:,0]<=1)&(abs(centers[:,1])<.09),'wake':(centers[:,0]>1)&(centers[:,0]<6)&(centers[:,1]>-.08)&(centers[:,1]<.18)}.items():
        regions[key]={'cells':int(mask.sum()),'sqrt_area_min_m':float(sizes[mask].min()),'sqrt_area_median_m':float(np.median(sizes[mask])),'sqrt_area_max_m':float(sizes[mask].max())}
    # Audit the mathematical boundary against every published control coordinate and dense boundary samples.
    source_err=[];wall=[];chord_err=[];wall_counts=[]
    from scipy.spatial import cKDTree
    for c,src in zip(curves,[upper,lower[::-1]]):
        uv=np.array(gmsh.model.getParametrization(1,c,np.c_[src,np.zeros(len(src))].ravel().tolist()))
        # Refine Gmsh's approximate inverse parametrization before auditing interpolation.
        for _ in range(8):
            val=np.array(gmsh.model.getValue(1,c,uv.tolist())).reshape(-1,3)[:,:2]
            der=np.array(gmsh.model.getDerivative(1,c,uv.tolist())).reshape(-1,3)[:,:2]
            uv-=np.sum((val-src)*der,axis=1)/np.sum(der*der,axis=1)
        val=np.array(gmsh.model.getValue(1,c,uv)).reshape(-1,3)[:,:2]
        source_err.extend(np.linalg.norm(val-src,axis=1))
        nt,co,par=gmsh.model.mesh.getNodes(1,c,includeBoundary=True,returnParametricCoord=True)
        wc=np.array(co).reshape(-1,3)[:,:2];val=np.array(gmsh.model.getValue(1,c,par)).reshape(-1,3)[:,:2]
        wall.extend(wc.tolist());source_err.extend(np.linalg.norm(wc-val,axis=1))
        si=np.argsort(par);sp=np.array(par)[si];sw=wc[si];wall_counts.append(len(nt))
        for frac in [.25,.5,.75]:
            pm=(1-frac)*sp[:-1]+frac*sp[1:]
            vm=np.array(gmsh.model.getValue(1,c,pm.tolist())).reshape(-1,3)[:,:2]
            linear=(1-frac)*sw[:-1]+frac*sw[1:]
            chord_err.extend(np.linalg.norm(vm-linear,axis=1))
    wall=np.array(wall)
    curve_sig=hashlib.sha256(np.c_[upper,lower].tobytes()).hexdigest()
    qm={q:np.array(gmsh.model.mesh.getElementQualities(et.tolist(),q)) for q in ['minSJ','minSICN']}
    report={'name':name,'geometry_sha256':{p.name:sha(p) for p in INPUT.iterdir() if p.is_file()},'curve_definition':'Gmsh built-in interpolating splines through ALL signed published 65 lower and 65 upper ordinates; shared LE/TE; no analytic airfoil replacement','curve_definition_sha256':curve_sig,'source_points_max_deviation_m':float(max(source_err)),'chord_m':1.,'farfield_bounds_m':[-radius,radius,-radius,radius],'nodes':len(tags),'cells':len(conn),'element_counts':{gmsh.model.mesh.getElementProperties(t)[0]:len(es) for t,es in zip(types,elTags)},'wall_nodes_per_side':n,'wall_first_layer_design_m':first,'wall_first_node_design_yplus':float(first*6.5e6*.045),'BL_growth':ratio,'BL_thickness_m':.02,'BL_design_layers':int(np.ceil(np.log(1+.02*(ratio-1)/first)/np.log(ratio))),'positive_signed_areas':bool(np.all(areas>0)),'area_min_m2':float(areas.min()),'min_scaled_jacobian':float(qm['minSJ'].min()),'min_inverse_condition':float(qm['minSICN'].min()),'equiangle_skewness_max':float(max(skew)),'center_face_nonorthogonality_max_deg':float(max(orth)),'regions':regions,'gradient_refinement_from_own_solution':gradient}
    (folder/'mesh_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    report['wall_nodes_per_source_curve']=wall_counts
    report['BL_thickness_m']=thickness
    report['BL_design_layers']=int(np.ceil(np.log(1+thickness*(ratio-1)/first)/np.log(ratio)))
    report['boundary_linear_edge_to_same_spline_max_sample_deviation_m']=float(max(chord_err))
    report['boundary_deviation_sampling']='25%,50%,75% same parameter within every linear boundary edge; spline control points audited by Newton-refined inverse'
    (folder/'mesh_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    gmsh.write(str(folder/'mesh.su2'));gmsh.write(str(folder/'mesh.msh'))
    np.savez_compressed(folder/'mesh_arrays.npz',points=coords,cells=np.array(conn,dtype=object),wall=wall)
    fig,axs=plt.subplots(2,3,figsize=(16,8))
    views=[('domain',(-radius,radius,-radius,radius)),('near body',(-.1,1.3,-.25,.3)),('LE',(-.012,.055,-.045,.045)),('wall layers',(.38,.42,.055,.09)),('TE',(.92,1.06,-.02,.04)),('wake',(.9,3,-.13,.22))]
    for ax,(lab,lims) in zip(axs.ravel(),views):
        mask=(centers[:,0]>lims[0]-.05)&(centers[:,0]<lims[1]+.05)&(centers[:,1]>lims[2]-.05)&(centers[:,1]<lims[3]+.05)
        polys=[coords[c] for c,m in zip(conn,mask) if m]
        ax.add_collection(PolyCollection(polys,facecolors='none',edgecolors='#213e52',linewidths=.25));ax.set(xlim=lims[:2],ylim=lims[2:],title=lab,aspect='equal');ax.plot(upper[:,0],upper[:,1],'r-',lw=.6);ax.plot(lower[:,0],lower[:,1],'r-',lw=.6)
    fig.suptitle(f'{name}: {len(conn):,} fluid cells; published coordinate splines, chord=1m');fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_mesh_{name}.png',dpi=160);plt.close(fig)
    gmsh.finalize();print(json.dumps(report,indent=2))
if __name__=='__main__':
    gradient=json.loads(Path(sys.argv[3]).read_text()) if len(sys.argv)>3 else None
    generate(sys.argv[1],float(sys.argv[2]) if len(sys.argv)>2 else 20.,gradient)
