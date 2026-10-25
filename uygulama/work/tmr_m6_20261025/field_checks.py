"""Independent forces and direct native-node boundary profiles for the source case."""
from common import ROOT,BASE,PROJECT,CASE,read,save,sha,now
from mesh_audit import load_mesh,FACES,normal_lines,stats
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import os
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def field(path):
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(path));reader.Update();g=reader.GetOutput()
    xyz=vtk_to_numpy(g.GetPoints().GetData()).astype(float)
    arrays={g.GetPointData().GetArrayName(i):vtk_to_numpy(g.GetPointData().GetArray(i)) for i in range(g.GetPointData().GetNumberOfArrays())}
    return g,xyz,arrays


def cfg(path):return {k.strip():v.strip() for k,v in (x.split('=',1) for x in path.read_text().splitlines() if '=' in x)}


def face_quadrature(points):
    if len(points)==3:
        av=np.cross(points[1]-points[0],points[2]-points[0])/2
        for i in range(3):
            N=np.full(3,1/6);N[i]=2/3
            yield N,av/3,N@points
    else:
        assert len(points)==4
        signs=np.array([[-1,-1],[1,-1],[1,1],[-1,1]],float)
        nodes,weights=np.polynomial.legendre.leggauss(3)
        for r,wr in zip(nodes,weights):
            for s,ws in zip(nodes,weights):
                N=(1+signs[:,0]*r)*(1+signs[:,1]*s)/4
                dr=signs[:,0]*(1+signs[:,1]*s)/4;ds=signs[:,1]*(1+signs[:,0]*r)/4
                yield N,np.cross(dr@points,ds@points)*wr*ws,N@points


def dual_node_normals(points):
    cg=points.mean(0);normal=np.zeros_like(points)
    for i,p in enumerate(points):
        nxt=(p+points[(i+1)%len(points)])/2;prev=(p+points[(i-1)%len(points)])/2
        normal[i]=(np.cross(nxt-p,cg-p)+np.cross(cg-p,prev-p))/2
    return normal


def integrate(mesh,surface,config,expected,scheme='bilinear_v2'):
    xyz,cells,markers=load_mesh(mesh);faces=markers['WING3D'];wall=np.unique(np.concatenate(faces));iswall=np.zeros(len(xyz),bool);iswall[wall]=True
    keys={tuple(sorted(f)):i for i,f in enumerate(faces)};centers={};counts={}
    for typ,ids in cells.items():
        for face in FACES[typ]:
            conn=ids[:,face];possible=np.flatnonzero(np.all(iswall[conn],axis=1))
            for j in possible:
                key=tuple(sorted(conn[j]))
                if key in keys:
                    i=keys[key];centers[i]=xyz[ids[j]].mean(0);counts[i]=counts.get(i,0)+1
    assert len(centers)==len(faces) and all(v==1 for v in counts.values())
    _,points,a=field(surface);distance,index=cKDTree(points).query(xyz[wall]);assert distance.max()<1e-6
    lookup=dict(zip(wall,index));cp=a['Pressure_Coefficient'];cf=a['Skin_Friction_Coefficient'];assert cf.shape==(len(points),3)
    d=cfg(config);area=float(d['REF_AREA']);length=float(d['REF_LENGTH']);origin=np.array([float(d['REF_ORIGIN_MOMENT_'+k]) for k in ['X','Y','Z']])
    pressure=np.zeros(3);viscous=np.zeros(3);moment=np.zeros(3);dual=np.zeros_like(xyz)
    for i,ids in enumerate(faces):
        if scheme=='nodal_dual_v3':
            normals=dual_node_normals(xyz[ids]);center=xyz[ids].mean(0)
            if np.dot(normals.sum(0),centers[i]-center)<0:normals=-normals
            dual[ids]+=normals
            continue
        if scheme=='triangle_v1':
            rules=[]
            for tri in [ids[:3]]+([[ids[0],ids[2],ids[3]]] if len(ids)==4 else []):
                p=xyz[tri];rules.append((tri,np.full(3,1/3),np.cross(p[1]-p[0],p[2]-p[0])/2,p.mean(0)))
        else:rules=[(ids,N,av,center) for N,av,center in face_quadrature(xyz[ids])]
        for used,N,av,center in rules:
            dot=np.dot(av,centers[i]-center);assert dot!=0
            if dot<0:av=-av
            j=[lookup[n] for n in used];fp=-float(N@cp[j])*av/area;fv=(N@cf[j])*np.linalg.norm(av)/area
            pressure+=fp;viscous+=fv;moment+=np.cross(center-origin,fp+fv)/length
    if scheme=='nodal_dual_v3':
        j=[lookup[n] for n in wall];normals=dual[wall]
        fp=-cp[j,None]*normals/area;fv=cf[j]*np.linalg.norm(normals,axis=1)[:,None]/area
        pressure=fp.sum(0);viscous=fv.sum(0);moment=np.cross(xyz[wall]-origin,fp+fv).sum(0)/length
    angle=np.deg2rad(float(d['AOA']));drag=np.array([np.cos(angle),0,np.sin(angle)]);lift=np.array([-np.sin(angle),0,np.cos(angle)])
    cl=float(lift@(pressure+viscous));cd=float(drag@(pressure+viscous))
    method={'bilinear_v2':'bilinear quad3x3 Gauss and triangle3point quadrature',
            'triangle_v1':'diagonal triangle mean v1','nodal_dual_v3':'node-centered median-dual normal assembled before nodal Cp/vectorCf summation'}[scheme]
    return {'method':'Native wing topology; sole fluid neighbor sets normal; '+method,
        'quadrature_scheme':scheme,
        'matched_surface_sha256':sha(surface),'native_CL':expected['CL'],'native_CD':expected['CD'],'independent_CL':cl,'independent_CD':cd,
        'CL_relative_difference':abs(cl/expected['CL']-1),'CD_relative_difference':abs(cd/expected['CD']-1),
        'CL_pressure':float(lift@pressure),'CL_viscous':float(lift@viscous),'CD_pressure':float(drag@pressure),'CD_viscous':float(drag@viscous),
        'moment_total_xyz':moment.tolist(),'mapping_max_distance':float(distance.max()),'all_wall_faces_one_fluid_neighbour':True,
        'scope':'Quadrature/Float32 differences measured; agreement is not convergence or physical accuracy.'}


def profiles(mesh,volume,config,role,source_level,iterative_passed):
    xyz,cells,markers=load_mesh(mesh);_,native,a=field(volume)
    if 'Momentum' in a:velocity=a['Momentum']/a['Density'][:,None]
    elif 'Velocity' in a:velocity=a['Velocity']
    else:raise KeyError('No supported native velocity/momentum field: '+str(a.keys()))
    tree=cKDTree(native);lines=normal_lines(mesh.with_suffix('.lines_fmt_all'))
    wall=np.array([x[0] for x in lines]);wp=xyz[wall];eta=wp[:,1]/1.4760179762198
    chord=1+(0.5625159852668158-1)*np.minimum(eta,1);le=np.tan(np.deg2rad(29.999))*np.minimum(wp[:,1],1.4760179762198)
    xc=(wp[:,0]-le)/chord
    selected=[];fig,axs=plt.subplots(2,4,figsize=(14,7));datadir=PROJECT/'data/tmr_sharp_20261025_v1'/role;datadir.mkdir(exist_ok=True)
    for j,(station,x_target) in enumerate((e,x) for e in [.2,.8] for x in [.2,.5,.8,.95]):
        ax=axs.flat[j]
        for upper,color in [(True,'#167a82'),(False,'#c57d37')]:
            allowed=(wp[:,2]>0) if upper else (wp[:,2]<0)
            score=(eta-station)**2+(xc-x_target)**2;score[~allowed]=np.inf;k=int(np.argmin(score))
            ids=lines[k];p=xyz[ids];s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]/chord[k]
            distance,indices=tree.query(p);valid=distance<1e-6
            # Direct source mesh nodes; retain invalid flags instead of zero placeholders.
            vel=velocity[indices].copy();valid &= np.all(np.isfinite(vel),axis=1)
            normal=p[1]-p[0];normal/=np.linalg.norm(normal)
            tangent=vel-(vel@normal)[:,None]*normal;speed=np.linalg.norm(tangent,axis=1);speed[~valid]=np.nan
            windows=[]
            for lo,hi in [(.03,.06),(.04,.08),(.06,.12)]:
                outer=valid&(s>=lo)&(s<=hi);ue=float(np.median(speed[outer])) if outer.any() else None;delta=None
                if ue is not None and ue>0:
                    for n in range(1,len(s)-2):
                        if valid[n-1:n+3].all() and np.all(speed[n:n+3]>=.99*ue):
                            den=speed[n]-speed[n-1]
                            delta=float(s[n-1]+np.clip((.99*ue-speed[n-1])/den,0,1)*(s[n]-s[n-1])) if den>0 else float(s[n])
                            break
                windows.append({'outer_s_over_c':[lo,hi],'valid_outer_nodes':int(outer.sum()),'Ue_operational_m_s':ue,'delta99_radial_over_c':delta})
            mu=a.get('Laminar_Viscosity');mut=a.get('Eddy_Viscosity')
            ratio=np.full(len(ids),np.nan)
            if mu is not None and mut is not None:
                mask=valid&(mu[indices]>0);ratio[mask]=mut[indices[mask]]/mu[indices[mask]]
            filename=f"eta{station:g}_xc{x_target:g}_{'u' if upper else 'l'}.csv"
            np.savetxt(datadir/filename,np.column_stack([s,p,valid.astype(int),speed,ratio]),delimiter=',',
                       header='radial_s_over_c,x,y,z,valid_sample,tangential_speed_m_s,eddy_to_laminar_viscosity',comments='')
            selected.append({'station_request':station,'xc_request':x_target,'side':'u' if upper else 'l','actual_eta':float(eta[k]),
                'actual_xc':float(xc[k]),'wall_node':int(ids[0]),'invalid_samples':int((~valid).sum()),'profiles':windows,'csv':str((datadir/filename).relative_to(ROOT))})
            ue=windows[1]['Ue_operational_m_s']
            if ue:ax.plot(speed/ue,s,color=color,label='upper' if upper else 'lower')
        ax.set(xlim=(0,1.4),ylim=(0,.08),xlabel='|tangential U| / operational Ue',ylabel='radial s/c',title=f'eta≈{station:g}, x/c≈{x_target:g}');ax.grid(alpha=.15)
    axs.flat[0].legend();fig.suptitle(f'{role}: matched native node profiles; iterative gate={iterative_passed}; diagnostic only');fig.tight_layout()
    fig.savefig(PROJECT/f'plots/tmr_{role}_BL_profiles_20261025.png',dpi=150);plt.close(fig)
    return {'source_level':source_level,'native_arrays':list(a),'profiles':selected,'iterative_gate_passed':iterative_passed,
        'sampling':'Direct source radial nodes mapped by coordinate distance to the same native volume field; validity retained through edge search.',
        'limits':'Radial arclength and operational99% crossing; window sensitivity shown. Not a full 3D compressible BL qualification or accepted uncertainty.'}


def main(role):
    folder=CASE/('flow_v2_'+role);seal=read(folder/'prediction_frozen.json');matched=seal['matched'];assert matched
    for rel,h in seal['files_sha256'].items():assert sha(ROOT/rel)==h
    level={'coarse':3,'medium':2,'fine':1}[role];mesh=CASE/f'mesh_family_budget_v3/wing_strct.{level}.su2';i=matched['field_iteration']
    passed=matched['last100_samples']==100 and matched['rms[Rho]']< -7 and matched['CL_last100_range']<1e-4 and matched['CD_last100_range']<1e-5
    result={'created_utc':now(),'role':role,'field_iteration':i,'prediction_seal_sha256':sha(folder/'prediction_frozen.json'),
            'forces':integrate(mesh,folder/f'surface_flow_{i:06d}.vtu',folder/'case.cfg',matched),
            'forces_triangle_v1_preserved':integrate(mesh,folder/f'surface_flow_{i:06d}.vtu',folder/'case.cfg',matched,'triangle_v1'),
            'force_nodal_dual_audit_v3':integrate(mesh,folder/f'surface_flow_{i:06d}.vtu',folder/'case.cfg',matched,'nodal_dual_v3'),
            'normal_profiles':profiles(mesh,folder/f'flow_{i:06d}.vtu',folder/'case.cfg',role,level,passed),
            'physical_qualification_passed':False}
    save(PROJECT/f'reports/tmr_{role}_field_checks_v3_20261025.json',result)
    print({'role':role,'forces':result['forces'],'native_dual_audit':result['force_nodal_dual_audit_v3'],
           'profile_count':len(result['normal_profiles']['profiles'])},flush=True)


if __name__=='__main__':
    import sys
    main(sys.argv[1])
