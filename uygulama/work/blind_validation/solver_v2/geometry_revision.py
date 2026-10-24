"""Source-point interpolation audit: a fluid boundary representation, not a new profile design."""
from pathlib import Path
import gmsh,json,hashlib,numpy as np,os
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(Path(__file__).parent/'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
INTERPOLATION_PAYLOAD=[]
def source():
    a=np.loadtxt(ROOT/'work/blind_validation/analysis_input/geom.txt',skiprows=5)
    return np.c_[a[:,0],a[:,2]],np.c_[a[:,0],-a[:,1]]
def create_occ():
    upper,lower=source();g=gmsh.model.occ
    le=g.addPoint(0,0,0);te=g.addPoint(1,0,0)
    # LE direction is the secant through the nearest source lower/upper points:
    # same x/c=.00060 on both sides -> vertical. Retain distinct TE end directions.
    du=upper[-1]-upper[-2];dl=lower[-2]-lower[-1];du/=np.linalg.norm(du);dl/=np.linalg.norm(dl)
    curves=[];INTERPOLATION_PAYLOAD.clear()
    # Explicit chord-length parametrization avoids OCC addSpline's opaque endpoint tangent scaling.
    # Convert an exactly interpolating, derivative-clamped SciPy spline into an OCC B-spline.
    for points,start,end,tan0,tan1 in [(upper,le,te,np.array([0.,1.]),du),(lower[::-1],te,le,dl,np.array([0.,1.]))]:
        arclength=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        bs=make_interp_spline(arclength,points,k=3,bc_type=([(1,tan0)],[(1,tan1)]))
        INTERPOLATION_PAYLOAD.append({'degree':3,'knots':bs.t.tolist(),'coefficients_m':bs.c.tolist(),'source_arclength_parameters_m':arclength.tolist(),'LE_direction_rule':'nearest equal-x source secant; vertical','TE_direction_rule':'one-sided source final secant'})
        poles=[start]+[g.addPoint(float(x),float(y),0) for x,y in bs.c[1:-1]]+[end]
        knots,mults=np.unique(bs.t,return_counts=True)
        curves.append(g.addBSpline(poles,degree=3,knots=knots.tolist(),multiplicities=mults.tolist()))
    g.synchronize();return g,curves,le,te,upper,lower
def audit():
    gmsh.initialize();gmsh.model.add('source_C1_revision');g,curves,le,te,upper,lower=create_occ();data={};denses=[];te_der=[];le_der=[]
    for side,c,src in zip(['upper','lower'],curves,[upper,lower[::-1]]):
        mn,mx=gmsh.model.getParametrizationBounds(1,c);pars=np.linspace(mn[0],mx[0],10001);dense=np.array(gmsh.model.getValue(1,c,pars)).reshape(-1,3)
        uv=np.array(gmsh.model.getParametrization(1,c,np.c_[src,np.zeros(len(src))].ravel().tolist()))
        for _ in range(8):
            val=np.array(gmsh.model.getValue(1,c,uv)).reshape(-1,3)[:,:2];der=np.array(gmsh.model.getDerivative(1,c,uv)).reshape(-1,3)[:,:2]
            uv-=np.sum((val-src)*der,1)/np.sum(der*der,1)
        val=np.array(gmsh.model.getValue(1,c,uv)).reshape(-1,3)[:,:2]
        first=np.array(gmsh.model.getDerivative(1,c,[mn[0]]));last=np.array(gmsh.model.getDerivative(1,c,[mx[0]]))
        ld=first if side=='upper' else last;td=last if side=='upper' else first;le_der.append(ld);te_der.append(td);denses.append(dense)
        dx=np.diff(dense[:,0]);data[side]={'source_point_max_deviation_m':float(np.max(np.linalg.norm(val-src,axis=1))),'LE_derivative':ld.tolist(),'TE_derivative':td.tolist(),'x_m_min':float(dense[:,0].min()),'x_m_max':float(dense[:,0].max()),'monotonic_x':bool(np.all(dx>=-1e-12) if side=='upper' else np.all(dx<=1e-12))}
    angle=lambda a,b:float(np.rad2deg(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
    # Independent higher-density PLOT3D surface is only a shape check; it is not fitted or substituted.
    ref=np.loadtxt(ROOT/'work/blind_validation/geometry_reference_v2/source_surface_305.csv',skiprows=1,delimiter=',')
    deviations=[]
    for point in ref:
        ds=[]
        for c in curves:
            coord,par=gmsh.model.getClosestPoint(1,c,[float(point[0]),float(point[1]),0.])
            ds.append(np.linalg.norm(np.array(coord[:2])-point))
        deviations.append(min(ds))
    report={'revision':'v2_geometry_r2_C1_LE_explicit_arclength','geometry_source_file':'work/blind_validation/analysis_input/geom.txt','geometry_source_sha256':hashlib.sha256((ROOT/'work/blind_validation/analysis_input/geom.txt').read_bytes()).hexdigest(),'representation':'Two exactly interpolating C2 cubic B-splines, parameterized by source-polyline arclength, through all65 signed published points on each branch. Explicit clamped endpoint derivative directions: shared LE vertical from same-x nearest source secant; separate TE one-sided unit source secants. SciPy coefficient/knots -> OCC addBSpline, avoiding opaque OCC interpolation tangent scaling. No source point moved; this is a recorded interpolation assumption, not new published geometry.','source_point_coordinates_unchanged':True,'LE_join_angle_deg':angle(*le_der),'TE_turn_angle_deg':angle(*te_der),'branches':data,'independent_305_geometry_check':{'input':'work/blind_validation/geometry_reference_v2/source_surface_305.csv','sha256':hashlib.sha256((ROOT/'work/blind_validation/geometry_reference_v2/source_surface_305.csv').read_bytes()).hexdigest(),'direction':'Each published305point -> closest point on either65point spline','max_distance_m':float(max(deviations)),'rms_distance_m':float(np.sqrt(np.mean(np.array(deviations)**2))),'distances_m':deviations,'not_fitted_or_substituted':True},'comparison_reference_read':'Only reviewer/leading_edge_tangent_audit.json was explicitly allowed; no flow/experiment target was read. Geometry-only source_surface_305.csv and manifest.json were explicitly allowed afterwards.','status':'geometry representation audit; reject unless source passage, C1 LE, finite TE, monotone x and chord bounds pass'}
    (OUT/'reports/prediction_v2_geometry_revision.json').write_text(json.dumps(report,indent=2))
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,xlim,ylim in zip(axs,[(-.002,.03),(.98,1.002)],[(-.025,.025),(-.003,.008)]):
        for dense,src,lab in zip(denses,[upper,lower],['upper','lower']):ax.plot(dense[:,0],dense[:,1],label=lab);ax.plot(src[:,0],src[:,1],'k.',ms=4)
        ax.plot(ref[:,0],ref[:,1],'rx',ms=3,label='independent305 points')
        ax.set(xlim=xlim,ylim=ylim,aspect='equal',xlabel='x/c',ylabel='y/c');ax.grid(alpha=.3)
    axs[0].set_title('LE: source points and C1 interpolation');axs[1].set_title('TE: separate finite tangent directions');fig.tight_layout();fig.savefig(OUT/'plots/prediction_v2_geometry_revision.png',dpi=170);plt.close(fig)
    gmsh.finalize();print(json.dumps(report,indent=2))
if __name__=='__main__':audit()
