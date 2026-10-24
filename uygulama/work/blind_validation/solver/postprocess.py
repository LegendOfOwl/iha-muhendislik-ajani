from pathlib import Path
import json,csv,sys,hashlib,re,os
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def read_vtu(p):
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(p));r.Update();d=r.GetOutput()
    if not d.GetNumberOfPoints():raise ValueError(str(p))
    xyz=vtk_to_numpy(d.GetPoints().GetData()).copy()
    data={d.GetPointData().GetArrayName(i):vtk_to_numpy(d.GetPointData().GetArray(i)).copy() for i in range(d.GetPointData().GetNumberOfArrays())}
    return d,xyz,data
def hist(p):
    with p.open() as f:rows=list(csv.DictReader(f,skipinitialspace=True))
    return {k.strip():np.array([float(r[k]) for r in rows]) for k in rows[0]}
def process(name,makeplots=True):
    folder=OUT/'simulations'/name;h=hist(folder/'history.csv');d,xyz,a=read_vtu(folder/'surface_flow.vtu');xy=xyz[:,:2]
    table=np.loadtxt(ROOT/'work/blind_validation/analysis_input/geom.txt',skiprows=5)
    # Source-camberline classification, never y>=0. Check nearest signed published surface.
    yl=-np.interp(xy[:,0],table[:,0],table[:,1]);yu=np.interp(xy[:,0],table[:,0],table[:,2])
    upper=np.abs(xy[:,1]-yu)<=np.abs(xy[:,1]-yl)
    # Reconstruct a clockwise boundary from the native surface element connectivity.
    edges=[]
    for i in range(d.GetNumberOfCells()):
        ce=d.GetCell(i)
        if ce.GetNumberOfPoints()==2:edges.append([ce.GetPointId(0),ce.GetPointId(1)])
    adj={i:[] for i in range(len(xy))}
    for i,j in edges:adj[i].append(j);adj[j].append(i)
    assert all(len(v)==2 for v in adj.values())
    seq=[int(np.argmin(xy[:,0]))];prev=-1
    while len(seq)<len(xy):
        nxt=[v for v in adj[seq[-1]] if v!=prev]
        nx=nxt[0] if len(seq)>1 else max(nxt,key=lambda k:xy[k,1])
        prev=seq[-1];seq.append(nx)
    seq=np.array(seq);poly=xy[seq];area=.5*np.sum(poly[:,0]*np.roll(poly[:,1],-1)-np.roll(poly[:,0],-1)*poly[:,1])
    if area>0:seq=seq[::-1];poly=xy[seq];area=-area
    vec=np.roll(poly,-1,axis=0)-poly;mid=(poly+np.roll(poly,-1,axis=0))/2
    cp=a['Pressure_Coefficient'][seq];cpedge=(cp+np.roll(cp,-1))/2
    ds=np.linalg.norm(vec,axis=1);pcell=cpedge[:,None]*np.c_[vec[:,1],-vec[:,0]]
    cf=a['Skin_Friction_Coefficient'][seq,:2];vcell=(cf+np.roll(cf,-1,axis=0))/2*ds[:,None]
    pf=pcell.sum(0);vf=vcell.sum(0);force=pf+vf
    alpha=np.deg2rad(json.loads((ROOT/'work/blind_validation/analysis_input/conditions.json').read_text())['alpha_deg'])
    lift=lambda f:float(-f[0]*np.sin(alpha)+f[1]*np.cos(alpha))
    drag=lambda f:float(f[0]*np.cos(alpha)+f[1]*np.sin(alpha))
    terminal={k:float(v[-1]) for k,v in h.items()}
    log=(folder/'solver.log').read_text(errors='replace')
    before=log[:log.rfind('File Writing Summary')]
    printed=re.findall(r'\|\s*(\d+)\|\s*[-0-9.eE]+\|',before)
    fi=int(printed[-1]) if printed else int(terminal['Inner_Iter'])
    ids=np.where(h['Inner_Iter']<=fi)[0];hh={k:v[ids] for k,v in h.items()}
    last={k:float(v[-1]) for k,v in hh.items()};clrange=float(np.ptp(hh['CL'][-200:]));cdrange=float(np.ptp(hh['CD'][-200:]))
    surface={'x_m':xy[:,0].tolist(),'y_m':xy[:,1].tolist(),'side':['upper' if t else 'lower' for t in upper],'Cp':a['Pressure_Coefficient'].tolist(),'Cf_x':a['Skin_Friction_Coefficient'][:,0].tolist(),'Cf_y':a['Skin_Friction_Coefficient'][:,1].tolist(),'y_plus':a['Y_Plus'].tolist()}
    with (folder/'wall_audit.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(surface)
        w.writerows(zip(*surface.values()))
    # The strongest non-LE/TE gradients are predictions, not a prescribed reference shock.
    gradient={};cpdict={}
    for side,mask in [('upper',upper),('lower',~upper)]:
        ids=np.where(mask)[0];ids=ids[np.argsort(xy[ids,0])];x=xy[ids,0];c=a['Pressure_Coefficient'][ids]
        unique=np.r_[True,np.diff(x)>1e-8];ids=ids[unique];x=x[unique];c=c[unique]
        grad=np.gradient(c,x);allowed=(x>.08)&(x<.92)
        ii=np.where(allowed)[0][np.argmax(abs(grad[allowed]))]
        gradient[side]={'x_over_c':float(x[ii]),'dCp_dx_max_abs':float(abs(grad[ii])),'selection':'argmax |dCp/dx| on own predicted surface for 0.08<x/c<0.92; no reference position accessed'}
        cpdict[side]={'x':x.tolist(),'Cp':c.tolist()}
    metrics={'name':name,'iteration':last['Inner_Iter'],'history_rows':len(h['CL']),'history_last':last,'history_terminal':terminal,'field_checkpoint_iteration':fi,'density_log10_residual':last['rms[Rho]'],'CL':last['CL'],'CD':last['CD'],'CL_final200_range':clrange,'CD_final200_range':cdrange,'max_wall_yplus':float(a['Y_Plus'].max()),'p99_wall_yplus':float(np.quantile(a['Y_Plus'],.99)),'checks':{'density_log10_below_minus8':last['rms[Rho]']< -8,'CL_final200_range_below_5e_5':len(hh['CL'])>=200 and clrange<5e-5,'CD_final200_range_below_2e_6':len(hh['CD'])>=200 and cdrange<2e-6,'max_wall_yplus_below1':float(a['Y_Plus'].max())<1},'source_camberline_surface_classification':True,'clockwise_boundary_signed_area_m2':float(area),'pressure_force_coefficient_xy':pf.tolist(),'viscous_force_coefficient_xy':vf.tolist(),'independent_surface_force':{'CL':lift(force),'CD':drag(force),'CL_pressure':lift(pf),'CD_pressure':drag(pf),'CL_viscous':lift(vf),'CD_viscous':drag(vf),'relative_difference_CL':abs(lift(force)-last['CL'])/abs(last['CL']),'relative_difference_CD':abs(drag(force)-last['CD'])/abs(last['CD']),'method':'native wall edge topology; trapezoid Cp normal integration and vector skin-friction integration; matched checkpoint history; comparison includes quadrature/output precision error'},'own_predicted_gradient':gradient,'Cp_by_side':cpdict,'field_time_note':'Final field checkpoint matched to the iteration printed before the last File Writing Summary; later terminal history is kept separately.'}
    (folder/'prediction_metrics.json').write_text(json.dumps(metrics,indent=2))
    if makeplots:
        fig,axs=plt.subplots(1,3,figsize=(15,4))
        for side,mask in [('upper',upper),('lower',~upper)]:
            ids=np.where(mask)[0];ids=ids[np.argsort(xy[ids,0])]
            for ax,field in zip(axs,['Pressure_Coefficient','Skin_Friction_Coefficient','Y_Plus']):
                v=a[field][ids];v=v[:,0] if v.ndim>1 else v
                ax.plot(xy[ids,0],v,'.-',ms=2,lw=.7,label=side)
        axs[0].invert_yaxis()
        for ax,lab in zip(axs,['Cp','Cf x-component','wall y+']):ax.set(xlabel='x/c',ylabel=lab);ax.grid(alpha=.25);ax.legend()
        fig.suptitle(name);fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_wall_{name}.png',dpi=160);plt.close(fig)
        fig,axs=plt.subplots(1,3,figsize=(15,4))
        for key in ['rms[Rho]','rms[RhoU]','rms[RhoV]','rms[RhoE]','rms[nu]']:axs[0].plot(h['Inner_Iter'],h[key],label=key,lw=.7)
        axs[0].legend(fontsize=7);axs[1].plot(h['Inner_Iter'],h['CL']);axs[2].plot(h['Inner_Iter'],h['CD'])
        for ax,lab in zip(axs,['log10 RMS','CL','CD']):ax.set(xlabel='iteration',ylabel=lab);ax.grid(alpha=.25)
        fig.suptitle(name);fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_history_{name}.png',dpi=160);plt.close(fig)
        vd,vxyz,va=read_vtu(folder/'flow.vtu');tris=[]
        for i in range(vd.GetNumberOfCells()):
            c=vd.GetCell(i);ids=[c.GetPointId(k) for k in range(c.GetNumberOfPoints())]
            tris.append(ids[:3])
            if len(ids)==4:tris.append([ids[0],ids[2],ids[3]])
        tri=mtri.Triangulation(vxyz[:,0],vxyz[:,1],np.array(tris))
        fig,axs=plt.subplots(1,2,figsize=(14,4.5))
        for ax,key in zip(axs,['Pressure_Coefficient','Mach']):
            pc=ax.tripcolor(tri,va[key],shading='gouraud',cmap='turbo');ax.set(xlim=(-.2,1.7),ylim=(-.35,.4),aspect='equal',title=key,xlabel='x/c',ylabel='y/c');fig.colorbar(pc,ax=ax)
        fig.suptitle(name+' actual native fluid field (quads split only for plotting)');fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_field_{name}.png',dpi=160);plt.close(fig)
    print(json.dumps({k:v for k,v in metrics.items() if k not in ['Cp_by_side','history_last']},indent=2))
    return metrics
if __name__=='__main__':process(sys.argv[1])
