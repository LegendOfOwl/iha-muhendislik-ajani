"""Independent primal mesh checks and before/after location-based quality audit.

Reads the actual SU2 exports; never imports reviewer modules or solver fields.
Tail-r2 medium/fine comparators are reproducible geometry-only meshes in work/.
"""
from pathlib import Path
import os,json,hashlib,time,ast,datetime,importlib.util
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent;OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.interpolate import BSpline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
import build_cgrid_tail_r2 as old
from interface_distance_r4 import InterfaceSizing

READS=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):READS.append(str(p.relative_to(ROOT)));return json.loads(p.read_text())
def save(p,a):p.write_text(json.dumps(a,indent=2,ensure_ascii=False),encoding='utf-8')
def stat(a):
    a=np.asarray(a)
    return {'min':float(a.min()),'median':float(np.median(a)),'p99':float(np.quantile(a,.99)),'max':float(a.max())} if len(a) else None
def parse(p):
    READS.append(str(p.relative_to(ROOT)));lines=p.read_text().splitlines();i=0;qq=[];tt=[];marks={}
    while i<len(lines):
        line=lines[i]
        if line.startswith('NELEM='):
            n=int(line.split('=')[1])
            for y in lines[i+1:i+n+1]:
                vals=list(map(int,y.split()))
                if vals[0]==9:qq.append(vals[1:5])
                elif vals[0]==5:tt.append(vals[1:4])
                else:raise ValueError(vals[0])
            i+=n
        elif line.startswith('NPOIN='):
            n=int(line.split('=')[1]);pnts=np.array([[float(z) for z in y.split()[:2]] for y in lines[i+1:i+n+1]]);i+=n
        elif line.startswith('MARKER_TAG='):
            name=line.split('=')[1].strip();n=int(lines[i+1].split('=')[1]);marks[name]=np.array([[int(z) for z in y.split()[1:3]] for y in lines[i+2:i+2+n]]);i+=n+1
        i+=1
    return pnts,np.asarray(qq),np.asarray(tt),marks
def distance_end(c):
    center=np.tan(np.deg2rad(2.31))*7;ylo=center-.3;yhi=center+.3
    return np.hypot(c[:,0]-8,np.maximum.reduce([ylo-c[:,1],c[:,1]-yhi,np.zeros(len(c))]))
def quality(p,q,t):
    areas=[];jacs=[];centers=[];skews=[];angles=[];nonorth=[];edge=[];minsJ=[]
    for co in [q,t]:
        v=p[co];v2=np.roll(v,-1,axis=1);e=v2-v;pre=np.roll(e,1,axis=1)
        area=.5*np.sum(v[:,:,0]*v2[:,:,1]-v2[:,:,0]*v[:,:,1],axis=1)
        J=pre[:,:,0]*e[:,:,1]-pre[:,:,1]*e[:,:,0];lens=np.linalg.norm(e,axis=2)
        ang=np.rad2deg(np.arccos(np.clip(np.sum(-pre*e,axis=2)/(np.linalg.norm(pre,axis=2)*lens),-1,1)))
        ideal=90 if co.shape[1]==4 else 60;skew=np.maximum(np.max((ang-ideal)/(180-ideal),axis=1),np.max((ideal-ang)/ideal,axis=1))
        cen=v.mean(1);dc=(v+v2)/2-cen[:,None,:];normal=np.stack([e[:,:,1],-e[:,:,0]],axis=2)
        orth=np.rad2deg(np.arccos(np.clip(np.abs(np.sum(dc*normal,axis=2))/(np.linalg.norm(dc,axis=2)*lens),0,1))).max(1)
        areas.append(area);jacs.append(J.min(1));centers.append(cen);skews.append(skew);angles.append(np.stack([ang.min(1),ang.max(1)],axis=1));nonorth.append(orth);edge.append(np.stack([lens.min(1),lens.max(1)],axis=1));minsJ.append((J/(np.linalg.norm(pre,axis=2)*lens)).min(1))
    return {k:np.concatenate(v) for k,v in zip(['area','jac','center','skew','angle','nonorth','edge','scaled_jac'],[areas,jacs,centers,skews,angles,nonorth,edge,minsJ])}
def topology(p,q,t,m):
    nc=len(q)+len(t);n=len(p)
    es=np.concatenate([np.stack([q,np.roll(q,-1,axis=1)],axis=2).reshape(-1,2),np.stack([t,np.roll(t,-1,axis=1)],axis=2).reshape(-1,2)])
    cid=np.r_[np.repeat(np.arange(len(q)),4),np.repeat(np.arange(len(q),nc),3)]
    low=es.min(1);hi=es.max(1);key=low*n+hi;order=np.argsort(key);skey=key[order]
    uk,start,count=np.unique(skey,return_index=True,return_counts=True);single=uk[count==1]
    twostart=start[count==2];pairs=np.stack([cid[order[twostart]],cid[order[twostart+1]]],axis=1)
    graph=coo_matrix((np.ones(len(pairs)),(pairs[:,0],pairs[:,1])),shape=(nc,nc)).tocsr();ncomp,lab=connected_components(graph,directed=False)
    marked=np.concatenate(list(m.values()));mk=marked.min(1)*n+marked.max(1)
    orientation=(es[order[twostart],0]<es[order[twostart],1])==(es[order[twostart+1],0]<es[order[twostart+1],1])
    loops={}
    for tag,e in m.items():
        degree=np.bincount(e.ravel(),minlength=n);active=degree[degree>0];loops[tag]={'edges':len(e),'nodes':len(active),'all_degree2':bool(np.all(active==2))}
    return {'cells':nc,'nodes':n,'connected_fluid_components':int(ncomp),'component_cell_counts':np.bincount(lab).tolist(),'nonmanifold_edges':int(np.sum(count>2)),'interior_edge_direction_disagreements':int(orientation.sum()),'unmarked_boundary_edges':int(len(np.setdiff1d(single,mk))),'declared_edges_not_single_fluid_neighbor':int(len(np.setdiff1d(mk,single))),'duplicate_marker_edges':int(len(mk)-len(np.unique(mk))),'exact_duplicate_node_coordinates':int(n-len(np.unique(p,axis=0))),'closed_markers':loops}
def worst(k,p,q,t,mask=None):
    ids=np.flatnonzero(mask) if mask is not None else np.arange(len(k['skew']))
    take=ids[np.argsort(k['skew'][ids])[-5:][::-1]] if len(ids) else []
    return [{'cell_id':int(i),'type':'quad' if i<len(q) else 'triangle','center_m':k['center'][i].tolist(),'skew':float(k['skew'][i]),'angle_min_max_deg':k['angle'][i].tolist(),'vertices_m':p[q[i] if i<len(q) else t[i-len(q)]].tolist()} for i in take]
def summary(k,p,q,t):
    tri=np.arange(len(k['area']))>=len(q);D=distance_end(k['center']);mask=tri&(D<.25)
    return {'cells':len(q)+len(t),'quads':len(q),'triangles':len(t),'all_positive_areas':bool(np.all(k['area']>0)),'all_positive_corner_Jacobians':bool(np.all(k['jac']>0)),'area_m2':stat(k['area']),'corner_Jacobian_m2_reference_unit_square_or_triangle':stat(k['jac']),'scaled_corner_Jacobian':stat(k['scaled_jac']),'equiangle_skew':stat(k['skew']),'worst_global':worst(k,p,q,t),'tail_local_region':'exterior triangles; Euclidean centroid distance to x=8,end-segment <0.25c','tail_local':{'cells':int(mask.sum()),'skew':stat(k['skew'][mask]),'angle_min_deg':stat(k['angle'][mask,0]),'angle_max_deg':stat(k['angle'][mask,1]),'center_to_face_nonorthogonality_deg':stat(k['nonorth'][mask]),'max_edge_m':stat(k['edge'][mask,1]),'worst':worst(k,p,q,t,mask)},'exterior_triangle_distance_bins':{f'{lo:g}..{hi:g}c':{'cells':int((tri&(D>=lo)&(D<hi)).sum()),'skew':stat(k['skew'][tri&(D>=lo)&(D<hi)])} for lo,hi in [(0,.02),(.02,.05),(.05,.1),(.1,.25),(.25,.5),(.5,1),(1,2),(2,5),(5,10),(10,20),(20,1000)]}}
def payload_source_audit(design,g):
    source=ROOT/'work/blind_validation/analysis_input/geom.txt';READS.append(str(source.relative_to(ROOT)));a=np.loadtxt(source,skiprows=5);errors=[];vertex=[];panel=[]
    nw=design['wake_segments_each_side'];nl=design['wall_lower_segments'];nu=design['wall_upper_segments']
    for pay,ts,points,actual in [(design['geometry_payload'][0],design['wall_parameter_upper'],np.c_[a[:,0],a[:,2]],g[0,nw+nl:nw+nl+nu+1]),(design['geometry_payload'][1],design['wall_parameter_lower'],np.c_[a[::-1,0],-a[::-1,1]],g[0,nw:nw+nl+1][::-1])]:
        bs=BSpline(pay['knots'],pay['coefficients_m'],3);errors.extend(np.linalg.norm(bs(pay['source_arclength_parameters_m'])-points,axis=1));vertex.extend(np.linalg.norm(bs(ts)-actual,axis=1))
        ts=np.asarray(ts)
        for f in [.25,.5,.75]:panel.extend(np.linalg.norm(bs(ts[:-1]*(1-f)+ts[1:]*f)-(actual[:-1]*(1-f)+actual[1:]*f),axis=1))
    return {'source65_interpolation_max_m':float(max(errors)),'actual_wall_vertex_deviation_to_r2_spline_max_m':float(max(vertex)),'linear_panel_same_parameter_sample_deviation_max_m':float(max(panel)),'panel_sample_fractions':[.25,.5,.75],'geometry_payload_sha256':hashlib.sha256(json.dumps(design['geometry_payload'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'source_sha256':sha(source)}

def interface_transition(p,q,t,iface,grid,des):
    n=len(p);edges=np.stack([iface,np.roll(iface,-1)],axis=1);key=edges.min(1)*n+edges.max(1)
    def neighbors(co):
        e=np.stack([co,np.roll(co,-1,axis=1)],axis=2).reshape(-1,2);k=e.min(1)*n+e.max(1);order=np.argsort(k);sk=k[order];left=np.searchsorted(sk,key);right=np.searchsorted(sk,key,side='right');assert np.all(right-left==1)
        return order[left]//co.shape[1]
    qi=neighbors(q);ti=neighbors(t);a=p[edges[:,0]];b=p[edges[:,1]];v=b-a;L=np.linalg.norm(v,axis=1)
    def heights(co,idx,den):
        vv=p[co[idx]]-a[:,None,:];cross=abs(v[:,None,0]*vv[:,:,1]-v[:,None,1]*vv[:,:,0]);return cross.sum(1)/(den*L)
    hq=heights(q,qi,2);ht=heights(t,ti,1);ratio=ht/hq;center=(a+b)/2
    ni=grid.shape[1];nw=des['wake_segments_each_side'];nl=des['wall_lower_segments'];nu=des['wall_upper_segments'];k=np.arange(len(edges));body=(k>=nw)&(k<nw+nl+nu);xwall=np.zeros(len(k));xwall[:ni-1]=(grid[0,:-1,0]+grid[0,1:,0])/2
    masks={'all_interface':np.ones(len(k),bool),'body_interface':body,'LE_interface':body&(xwall<.05),'TE_interface':body&(xwall>.9),'aft_body_interface':body&(xwall>.8),'horizontal_wake_interface':(k<ni-1)&~body,'vertical_end_interface':k>=ni-1}
    regions={name:{'edges':int(mask.sum()),'tangential_edge_m':stat(L[mask]),'near_quad_normal_height_m':stat(hq[mask]),'outside_triangle_normal_height_m':stat(ht[mask]),'outside_over_inside_height_ratio':stat(ratio[mask])} for name,mask in masks.items()}
    bad=np.argsort(np.maximum(ratio,1/ratio))[-8:][::-1]
    return {'definition':'Exact exported interface edges each have one explicit quad and one exterior triangle. Triangle height=2A/edge length; quad height=mean perpendicular distance of two opposite vertices to interface edge.','regions':regions,'largest_symmetric_transition_ratio':[{'interface_edge_id':int(i),'edge_midpoint_m':center[i].tolist(),'quad_height_m':float(hq[i]),'triangle_height_m':float(ht[i]),'outside_over_inside':float(ratio[i])} for i in bad]}

def baseline(level,scale):
    path=OUT/'simulations'/('v3_cgrid_tailr2_'+level)
    if (path/'mesh.su2').exists():
        p,q,t,marks=parse(path/'mesh.su2');return p,q,t,marks,{'kind':'existing actual tail-r2 SU2 export','path':str((path/'mesh.su2').relative_to(ROOT)),'sha256':sha(path/'mesh.su2')}
    prior=WORK/'tailr2_comparison'/level/'mesh.su2'
    if prior.exists():
        p,q,t,marks=parse(prior);return p,q,t,marks,{'kind':'reuse preserved geometry-only tail-r2 comparator created during R3 audit; no CFD','path':str(prior.relative_to(ROOT)),'sha256':sha(prior)}
    p,q,wall,interface,g,idx,w,design=old.mesh_near(scale)
    p,t,far=old.outer_mesh(p,interface,scale)
    b=WORK/'tailr2_comparison'/level;b.mkdir(parents=True,exist_ok=True)
    old.write_su2(b/'mesh.su2',p,q,t,wall,far);np.savez_compressed(b/'mesh_arrays.npz',points=p,quads=q,triangles=t,wall=wall,farfield=far)
    return p,q,t,{'AIRFOIL':wall,'FARFIELD':far},{'kind':'new geometry-only comparator from unchanged tail-r2 functions; never a CFD case','path':str((b/'mesh.su2').relative_to(ROOT)),'sha256':sha(b/'mesh.su2'),'source_script_sha256':sha(WORK/'build_cgrid_tail_r2.py')}

def run(level):
    start=time.time();scale={'coarse':2/3,'medium':1,'fine':1.5}[level];name='v3_cgrid_interfacer4_'+level;folder=OUT/'simulations'/name
    p,q,t,marks=parse(folder/'mesh.su2');des=js(folder/'near_design.json');near=np.load(folder/'near_arrays.npz');READS.append(str((folder/'near_arrays.npz').relative_to(ROOT)))
    p0,q0,t0,m0,prov=baseline(level,scale);before=quality(p0,q0,t0);after=quality(p,q,t)
    # Independently reconstruct tail-r2 near arrays using its unchanged functions.
    expected=old.mesh_near(scale);ep,eq,ew,ei,eg,eid,_,ed=expected
    equal={'points_bitwise_equal':bool(np.array_equal(ep,near['points'])),'quads_bitwise_equal':bool(np.array_equal(eq,near['quads'])),'wall_connectivity_bitwise_equal':bool(np.array_equal(ew,near['wall'])),'structured_grid_bitwise_equal':bool(np.array_equal(eg,near['grid'])),'near_design_equal':ed==des,'actual_export_coordinates_bitwise_equal':bool(np.array_equal(p[:len(ep)],ep)),'actual_export_quads_bitwise_equal':bool(np.array_equal(q,eq)),'actual_export_wall_edges_equal':bool(np.array_equal(marks['AIRFOIL'],ew)),'baseline_near_points_bitwise_equal':bool(np.array_equal(p0[:len(ep)],ep)),'baseline_quads_bitwise_equal':bool(np.array_equal(q0,eq))}
    topo=topology(p,q,t,marks);geom=payload_source_audit(des,near['grid'])
    wallpoly=p[marks['AIRFOIL'][:,0]];wall_area=.5*abs(np.sum(wallpoly[:,0]*np.roll(wallpoly,-1,axis=0)[:,1]-wallpoly[:,1]*np.roll(wallpoly,-1,axis=0)[:,0]));expected_area=400*400-wall_area
    report={'case':name,'scope':'Geometry-only local exterior mesh revision; no CFD and no expected/reference flow data read.','baseline':prov,'before':summary(before,p0,q0,t0),'after':summary(after,p,q,t),'topology':topo,'tailr2_near_block_equality':equal,'geometry':geom,'domain':{'boundary_bounds_m':p[marks['FARFIELD'].ravel()].min(0).tolist()+p[marks['FARFIELD'].ravel()].max(0).tolist(),'exact_target_bounds_m':[-200,-200,200,200],'fluid_cell_area_sum_m2':float(after['area'].sum()),'square_minus_discrete_wall_area_m2':float(expected_area),'area_balance_difference_m2':float(after['area'].sum()-expected_area)},'mesh_files_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [folder/'mesh.su2',folder/'near_arrays.npz',folder/'near_design.json',folder/'mesh_arrays.npz',folder/'exterior_interface_sizing.json']},'sizing':js(folder/'exterior_interface_sizing.json'),'elapsed_audit_seconds':time.time()-start}
    report['checks_passed']=all(equal.values()) and report['after']['all_positive_areas'] and report['after']['all_positive_corner_Jacobians'] and topo['connected_fluid_components']==1 and all(topo[k]==0 for k in ['nonmanifold_edges','unmarked_boundary_edges','declared_edges_not_single_fluid_neighbor','duplicate_marker_edges','exact_duplicate_node_coordinates','interior_edge_direction_disagreements']) and all(x['all_degree2'] for x in topo['closed_markers'].values()) and geom['actual_wall_vertex_deviation_to_r2_spline_max_m']<1e-12 and abs(report['domain']['area_balance_difference_m2'])<1e-7
    report['quality_acceptance_note']='No new skew/angle cutoff introduced. Positive Jacobian/topology pass does not prove CFD convergence or flow accuracy. Local angles and global worst cells remain visible.'
    report['interface_normal_transition_before']=interface_transition(p0,q0,t0,ei,eg,ed)
    report['interface_normal_transition_after']=interface_transition(p,q,t,ei,eg,ed)
    save(folder/'interface_revision_audit.json',report)
    # Display real mesh polygons; local tail and global worst region separately.
    cy=np.tan(np.deg2rad(2.31))*7
    views=[('vertical end',(7.85,8.22,cy-.34,cy+.34)),('top end corner',(7.88,8.10,cy+.22,cy+.38)),('downstream mid-end',(7.96,8.06,cy-.05,cy+.05))]
    fig,axs=plt.subplots(2,3,figsize=(15,9))
    for row,(pp,qq,tt,kk,label) in enumerate([(p0,q0,t0,before,'tail-r2 before'),(p,q,t,after,'interface-r4 after')]):
        for ax,(title,lim) in zip(axs[row],views):
            for co,off in [(qq,0),(tt,len(qq))]:
                vv=pp[co];mask=(vv[:,:,0].max(1)>=lim[0])&(vv[:,:,0].min(1)<=lim[1])&(vv[:,:,1].max(1)>=lim[2])&(vv[:,:,1].min(1)<=lim[3])
                ax.add_collection(PolyCollection(vv[mask],array=kk['skew'][off:off+len(co)][mask],cmap='viridis',norm=Normalize(0,1),edgecolors='#555555',linewidths=.28))
            ax.set(xlim=lim[:2],ylim=lim[2:],aspect='equal',xlabel='x/c',ylabel='y/c',title=label+': '+title)
    fig.suptitle(name+' | actual exported fluid cells; color = equiangle skew, common 0..1 scale');fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_{name}_tail_before_after.png',dpi=170);plt.close(fig)
    print(level,'cells',len(q)+len(t),'before/after local max skew',report['before']['tail_local']['skew']['max'],report['after']['tail_local']['skew']['max'],'global',report['after']['equiangle_skew']['max'],'checks',report['checks_passed'],flush=True)
    return report

if __name__=='__main__':
    READS.extend(['work/mesh_research/cgrid/build_cgrid_tail_r2.py','work/mesh_research/cgrid/build_cgrid_interface_r4.py','outputs/projects/proje-15cce2de02/simulations/v2_r2_medium/mesh_audit.json'])
    src0=ast.parse((WORK/'build_cgrid_tail_r2.py').read_text());src1=ast.parse((WORK/'build_cgrid_interface_r4.py').read_text())
    f0={f.name:ast.dump(f,include_attributes=False) for f in src0.body if isinstance(f,ast.FunctionDef)};f1={f.name:ast.dump(f,include_attributes=False) for f in src1.body if isinstance(f,ast.FunctionDef)}
    same={k:f0[k]==f1[k] for k in ['load_geometry','wall_distribution','normal_distribution','map_wall','wake_distribution','mesh_near','area_jac','write_su2']};assert all(same.values())
    import sys
    results=[run(level) for level in (sys.argv[1:] or ['coarse','medium','fine'])]
    family={'scope':'Three actual geometry-only meshes. No CFD run; no solved y+ or force claim.','all_geometry_topology_checks_passed':all(r['checks_passed'] for r in results),'same_near_function_AST_vs_tailr2':same,'all_same_geometry_payload_sha256':len({r['geometry']['geometry_payload_sha256'] for r in results})==1,'all_same_farfield_bounds':len({tuple(r['domain']['boundary_bounds_m']) for r in results})==1,'levels':[{'case':r['case'],'cells':r['after']['cells'],'before_cells':r['before']['cells'],'cell_change_percent':100*(r['after']['cells']/r['before']['cells']-1),'baseline':r['baseline'],'local_before':r['before']['tail_local'],'local_after':r['after']['tail_local'],'global_before_skew':r['before']['equiangle_skew'],'global_after_skew':r['after']['equiangle_skew'],'global_after_worst':r['after']['worst_global'][0],'equality':r['tailr2_near_block_equality'],'audit_path':str((OUT/'simulations'/r['case']/'interface_revision_audit.json').relative_to(ROOT))} for r in results],'source_script_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [WORK/'build_cgrid.py',WORK/'build_cgrid_tail_r2.py',WORK/'build_cgrid_interface_r4.py',WORK/'audit_interface_r4.py']},'input_sha256':{str(f.relative_to(ROOT)):sha(f) for f in (ROOT/'work/blind_validation/analysis_input').iterdir() if f.is_file()},'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    family['required_cases']=['v3_cgrid_interfacer4_'+x for x in ['coarse','medium','fine']]
    family['all_three_levels_completed']=set(family['required_cases'])=={r['case'] for r in results}
    family['all_geometry_topology_checks_passed']=family['all_three_levels_completed'] and all(r['checks_passed'] for r in results)
    family['source_script_sha256'][str((WORK/'interface_distance_r4.py').relative_to(ROOT))]=sha(WORK/'interface_distance_r4.py')
    save(OUT/'reports/prediction_v3_cgrid_interfacer4_family.json',family)
    save(WORK/'access_log_interface_r4.json',{'files_read':sorted(set(READS)),'other_file_read':'work/mesh_research/audit_cgrid.py read as text; its reviewer-module import was identified and deliberately NOT executed. Independent auditor written here instead. Existing own tailr2_coarse build_metadata/independent_cgrid_audit geometry-only records read.','prohibited_reviewer_module_or_target_results_read':False,'updated_global_state_AGENTS_read':False,'accidental_expected_reference_exposure':None,'CFD_launched':False})
