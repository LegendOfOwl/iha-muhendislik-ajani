"""Read-only diagnosis of own v3 grid/fields, separate from frozen generator."""
from pathlib import Path
import os,json,hashlib,csv
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02';WORK=Path(__file__).parent
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stat(a):
    a=np.asarray(a);return {'min':float(a.min()),'median':float(np.median(a)),'max':float(a.max()),'p99':float(np.quantile(a,.99))}
def parse(p):
    lines=p.read_text().splitlines();i=0;cells=[];marks={}
    while i<len(lines):
        x=lines[i]
        if x.startswith('NELEM='):
            n=int(x.split('=')[1]);cells=[np.array(list(map(int,y.split()))[1:5 if y.split()[0]=='9' else 4]) for y in lines[i+1:i+n+1]];i+=n
        elif x.startswith('NPOIN='):
            n=int(x.split('=')[1]);pts=np.array([[float(z) for z in y.split()[:2]] for y in lines[i+1:i+n+1]]);i+=n
        elif x.startswith('MARKER_TAG='):
            name=x.split('=')[1].strip();n=int(lines[i+1].split('=')[1]);marks[name]=np.array([[int(z) for z in y.split()[1:3]] for y in lines[i+2:i+2+n]]);i+=n+1
        i+=1
    return pts,cells,marks

base=OUT/'simulations/v3_cgrid_coarse';p,cells,marks=parse(base/'mesh.su2')
near=np.load(base/'near_arrays.npz');gid=near['grid_ids'];grid=p[gid];q=np.array(cells[:len(near['quads'])]);vv=p[q];ev=np.roll(vv,-1,axis=1)-vv;prev=np.roll(ev,1,axis=1)
jac=prev[:,:,0]*ev[:,:,1]-prev[:,:,1]*ev[:,:,0]
area=.5*np.sum(vv[:,:,0]*np.roll(vv,-1,axis=1)[:,:,1]-np.roll(vv,-1,axis=1)[:,:,0]*vv[:,:,1],axis=1)
angles=np.rad2deg(np.arccos(np.clip(np.sum(-prev*ev,axis=2)/(np.linalg.norm(prev,axis=2)*np.linalg.norm(ev,axis=2)),-1,1)))
cen=vv.mean(1);local=(cen[:,0]>.50)&(cen[:,0]<.54)&(cen[:,1]>.095)&(cen[:,1]<.125)
lenedge=np.linalg.norm(ev,axis=2)
interface=set(near['interface'].tolist());localnodes=np.unique(q[local]);distI=cKDTree(p[list(interface)]).query(p[localnodes])[0]

# Rebuild the median-dual faces independently from actual SU2 polygons.
face={};incidence={};subarea=np.zeros(len(p));submin=1e99
for ci,co in enumerate(cells):
    v=p[co];center=v.mean(0);m=(v+np.roll(v,-1,axis=0))/2
    for k,(a,b) in enumerate(zip(co,np.roll(co,-1))):
        e=tuple(sorted((int(a),int(b))));seg=center-m[k];normal=np.array([seg[1],-seg[0]])*(1 if a<b else -1)
        face[e]=face.get(e,np.zeros(2))+normal;incidence.setdefault(e,[]).append(ci)
        poly=np.array([v[k],m[k],center,m[k-1]])
        ar=.5*np.sum(poly[:,0]*np.roll(poly,-1,axis=0)[:,1]-poly[:,1]*np.roll(poly,-1,axis=0)[:,0]);subarea[a]+=ar;submin=min(submin,ar)
edges=np.array(list(face));norm=np.array(list(face.values()));disp=p[edges[:,1]]-p[edges[:,0]];proj=np.sum(norm*disp,axis=1)
closure=np.zeros_like(p);np.add.at(closure,edges[:,0],norm);np.add.at(closure,edges[:,1],-norm)
bn=set(np.concatenate(list(marks.values())).ravel().tolist());interior=np.array([i for i in range(len(p)) if i not in bn]);cl=np.linalg.norm(closure[interior],axis=1)
incident=[set() for _ in p]
for a,b in edges:incident[a].add(int(b));incident[b].add(int(a))
read_files=[base/'mesh.su2',base/'near_arrays.npz',base/'mesh_arrays.npz',base/'near_design.json',base/'case.cfg',base/'own_residual_hotspots.json']
cases=[('v3_cgrid_coarse',1000),('v3_cgrid_coarse_cfl1',1000),('v3_cgrid_coarse_cfl1_mg0',1200),('v3_cgrid_coarse_entropy0p2',1200)]
result={'scope':'Own numerical mesh and native checkpoint fields only; no expected/reference flow data. Diagnostic, not validation. No solver launched.','mesh_sha256':sha(base/'mesh.su2'),'generator_sha256':sha(WORK/'build_cgrid.py'),'frozen_generator_unchanged':sha(WORK/'build_cgrid.py')==json.loads((base/'build_metadata.json').read_text())['script_sha256'],'actual_SU2_vs_near_arrays_quads_equal':bool(np.array_equal(q,near['quads'])),'actual_SU2_vs_near_arrays_coordinates_max_m':float(np.max(np.abs(p[:len(near['points'])]-near['points']))),'shock_region_definition_m':[.50,.54,.095,.125],'local_mesh':{'cells':int(local.sum()),'corner_jacobian_m2':stat(jac[local].ravel()),'area_m2':stat(area[local]),'angles_deg':stat(angles[local].ravel()),'edge_length_m':stat(lenedge[local].ravel()),'aspect_edge_ratio':stat(lenedge[local].max(1)/lenedge[local].min(1)),'distance_to_quad_triangle_interface_m':stat(distI),'all_quads':True},'median_dual':{'minimum_subpolygon_area_m2':float(submin),'minimum_dual_volume_m2':float(subarea.min()),'nonpositive_dual_subpolygons':bool(submin<=0),'minimum_dual_face_dot_primal_edge_m2':float(proj.min()),'nonpositive_face_projections':int(np.count_nonzero(proj<=0)),'interior_constant_flux_face_vector_closure_m':stat(cl),'local_neighbor_count':stat([len(incident[i]) for i in localnodes]),'scope':'Independent median-dual geometric reconstruction; not SU2 internal agglomerated coarse-grid audit.'},'fields':[]}

fig,axs=plt.subplots(len(cases),3,figsize=(15,3.7*len(cases)))
for row,(name,it) in enumerate(cases):
    f=OUT/'simulations'/name/f'flow_{it:06d}.vtu'
    if not f.exists():continue
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(f));r.Update();g=r.GetOutput();vp=vtk_to_numpy(g.GetPoints().GetData())[:,:2]
    d,mapidx=cKDTree(vp).query(p);assert np.max(d[p[:,0]**2+p[:,1]**2<4])<1e-7
    dat={g.GetPointData().GetArrayName(k):vtk_to_numpy(g.GetPointData().GetArray(k))[mapidx] for k in range(g.GetPointData().GetNumberOfArrays())}
    mach=dat['Mach'];pres=dat['Pressure'];res=np.abs(dat['Residual_Density']);M=mach[gid];P=pres[gid];R=res[gid]
    hot=(p[:,0]>.50)&(p[:,0]<.54)&(p[:,1]>.095)&(p[:,1]<.125)
    loc=np.flatnonzero(hot);hoti=loc[np.argmax(res[hot])];jr,ir=np.unravel_index(np.argmin(np.linalg.norm(grid-p[hoti],axis=2)),gid.shape)
    # Measure a transverse row oscillation only in the regular cap-spacing part.
    i=ir;jmask=(grid[:,i,1]>.10)&(grid[:,i,1]<.12);jj=np.flatnonzero(jmask);mm=M[jj,i]
    centered=mm[1:-1]-.5*(mm[:-2]+mm[2:]);dv=np.diff(mm);reversals=int(np.count_nonzero(dv[:-1]*dv[1:]<0))
    # Directional undivided pressure differences: sensor cancellation diagnostic,
    # not a replacement for the exact boundary-adjusted native sensor.
    records=[]
    for j in jj[1:-1]:
        pi=P[j,i];dx=P[j,i-1]+P[j,i+1]-2*pi;dy=P[j-1,i]+P[j+1,i]-2*pi
        records.append([int(j),float(grid[j,i,0]),float(grid[j,i,1]),float(M[j,i]),float(R[j,i]),float(dx),float(dy),float(abs(dx+dy)/(abs(dx)+abs(dy)+1e-30))])
    ds=np.array(records)
    globalids=np.argsort(res)[-20:][::-1]
    info={'case':name,'checkpoint_iteration_local':it,'restart_seed_base_iteration':None if name=='v3_cgrid_coarse' else 1000,'field':str(f.relative_to(ROOT)),'field_sha256':sha(f),'VTU_point_mapping_max_nearbody_m':float(d[p[:,0]**2+p[:,1]**2<4].max()),'hotspot':{'point_id_SU2_mesh':int(hoti),'grid_row':int(jr),'grid_column':int(ir),'xy_m':p[hoti].tolist(),'density_residual_abs':float(res[hoti]),'Mach':float(mach[hoti]),'distance_to_interface_m':float(cKDTree(p[list(interface)]).query(p[hoti])[0]),'neighbor_count':len(incident[hoti]),'neighbor_xy_m':[p[k].tolist() for k in sorted(incident[hoti])]},'global_maxima':[{'mesh_point_id':int(k),'xy_m':p[k].tolist(),'density_residual_abs':float(res[k]),'Mach':float(mach[k])} for k in globalids],'hotbox_residual_square_sum_fraction':float(np.sum(res[hot]**2)/np.sum(res**2)),'transverse_column':{'x_m':float(grid[jj[0],i,0]),'y_range_m':[float(grid[jj[0],i,1]),float(grid[jj[-1],i,1])],'sample_count':len(jj),'Mach_min':float(mm.min()),'Mach_max':float(mm.max()),'Mach_linear_detrend_second_difference_rms':float(np.sqrt(np.mean(centered**2))),'Mach_linear_detrend_second_difference_max':float(np.max(abs(centered))),'adjacent_slope_sign_reversals':reversals,'neighbor_pressure_laplacian_direction_cancellation_ratio':stat(ds[:,-1]) if len(ds) else None,'row_records_columns':['j','x','y','Mach','abs_density_residual','lap_i_pressure','lap_j_pressure','abs(lap_i+lap_j)/(abs(lap_i)+abs(lap_j))'],'row_records':records}}
    result['fields'].append(info);read_files.append(f)
    # Native nodal data on the exact mesh coordinates; no interpolated shock.
    for col,(field,label,cmap) in enumerate([(mach,'Mach','viridis'),(np.log10(np.maximum(res,1e-20)),'log10 |density residual|','magma')]):
        ax=axs[row,col];pc=PolyCollection(vv[local],array=field[q[local]].mean(1),cmap=cmap,edgecolors='#ffffff',linewidths=.2);ax.add_collection(pc);ax.set(xlim=(.50,.54),ylim=(.095,.125),aspect='equal',title=f'{name}\nlocal iteration {it}: {label}');fig.colorbar(pc,ax=ax,pad=.02,fraction=.04)
    ax=axs[row,2];ax.plot(mm,grid[jj,i,1],'o-',ms=3);ax.set(xlabel='Mach',ylabel='y/c',title=f'Own column x/c={grid[jj[0],i,0]:.6f}');ax.grid(alpha=.3)
fig.tight_layout();plot=OUT/'plots/prediction_v3_cgrid_shock_diagnosis_v2.png';fig.savefig(plot,dpi=160);plt.close(fig)
result['input_files_sha256']={str(f.relative_to(ROOT)):sha(f) for f in read_files};result['diagnosis_script_sha256']=sha(__file__)
path=OUT/'reports/prediction_v3_cgrid_shock_diagnosis_v2.json';path.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['input_files_sha256','fields']},indent=2));print([(x['case'],x['hotspot'],{k:v for k,v in x['transverse_column'].items() if k!='row_records'}) for x in result['fields']])
