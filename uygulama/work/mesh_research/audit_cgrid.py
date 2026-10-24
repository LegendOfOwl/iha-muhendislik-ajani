"""Independent geometric/regional audit of the explicit C-block, no CFD targets."""
from pathlib import Path
import os, sys, json, hashlib, importlib.util
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
import numpy as np
from scipy.interpolate import BSpline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

def stat(x):
    x=np.asarray(x)
    return {'min':float(x.min()),'median':float(np.median(x)),'p99':float(np.quantile(x,.99)),'max':float(x.max())}

def run(name):
    folder=OUT/'simulations'/name
    a=np.load(folder/'near_arrays.npz');p=a['points'];q=a['quads'];g=a['grid'];ids=a['grid_ids']
    design=json.loads((folder/'near_design.json').read_text())
    arrays=np.load(folder/'mesh_arrays.npz');allp=arrays['points'];tri=arrays['triangles']
    spec=importlib.util.spec_from_file_location('primal_audit',ROOT/'work/blind_validation/reviewer/audit_export_topology.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    topology=module.audit(name)
    v=p[q];e=np.roll(v,-1,axis=1)-v;prev=np.roll(e,1,axis=1)
    jac=prev[:,:,0]*e[:,:,1]-prev[:,:,1]*e[:,:,0]
    np.savez_compressed(folder/'jacobian_corners.npz',jacobian=jac)
    # The wall index sequence contains only the actual closed airfoil, no cut.
    nw=design['wake_segments_each_side'];nl=design['wall_lower_segments'];nu=design['wall_upper_segments']
    body=slice(nw,nw+nl+nu+1)
    wallxy=g[0,body];firstvec=g[1,body]-wallxy
    tang=np.gradient(wallxy,axis=0);norm=np.c_[-tang[:,1],tang[:,0]];norm/=np.linalg.norm(norm,axis=1)[:,None]
    projected=np.sum(firstvec*norm,axis=1)
    # TE has a sharp, deliberately finite turning angle; report separately.
    firstcos=projected/np.linalg.norm(firstvec,axis=1)
    regions=[]
    for side,columns in [('lower',np.arange(nw,nw+nl+1)),('upper',np.arange(nw+nl,nw+nl+nu+1))]:
        for xc in [.01,.05,.4,.8,.95,.995]:
            k=int(columns[np.argmin(abs(g[0,columns,0]-xc))])
            normal=np.array([-(g[0,k+1,1]-g[0,k-1,1]),g[0,k+1,0]-g[0,k-1,0]]) if 0<k<g.shape[1]-1 else np.array([0.,1.])
            # Inner curve runs clockwise; its left normal points into fluid.
            normal=normal/np.linalg.norm(normal)
            distances=(g[:,k]-g[0,k])@normal
            edges=np.linalg.norm(np.diff(g[:,k],axis=0),axis=1)
            regions.append({'side':side,'requested_x_over_c':xc,'wall_xy_m':g[0,k].tolist(),'column_index':k,
                'first_edge_m':float(edges[0]),'last_edge_m':float(edges[-1]),
                'projected_distance_at_outer_block_m':float(distances[-1]),
                'cells_within_0p01c':int(np.count_nonzero(distances[1:]<=.01)),
                'cells_within_0p03c':int(np.count_nonzero(distances[1:]<=.03)),
                'edge_lengths_m':edges.tolist(),'projected_distances_m':distances.tolist(),
                'actual_growth_ratio':stat(edges[1:]/edges[:-1])})
    # Distance of all wall vertices to the immutable analytic r2 branches.
    payload=design['geometry_payload'];errors=[]
    for pay,tvalues,upper in zip(payload,[design['wall_parameter_upper'],design['wall_parameter_lower']],[True,False]):
        spline=BSpline(pay['knots'],pay['coefficients_m'],3)
        expected=spline(tvalues)
        actual=g[0,nw+nl:nw+nl+nu+1] if upper else g[0,nw:nw+nl+1][::-1]
        errors.extend(np.linalg.norm(expected-actual,axis=1).tolist())
    geom={'curve_definition_sha256':design['curve_definition_sha256'],'max_vertex_distance_to_exact_r2_curve_m':float(max(errors)),
          'geometry_redesigned':False,'discrete_boundary':'Straight CFD wall segments connecting exact r2 B-spline sample points; finite chord error remains.'}
    results={'name':name,'algorithm_version':2,'topology':topology,'corner_jacobian_m2':stat(jac.ravel()),
        'all_corner_jacobians_positive':bool(np.all(jac>0)),
        'first_wall_edge_length_m':stat(np.linalg.norm(firstvec,axis=1)),
        'first_wall_normal_projection_m':stat(projected[1:-1]),
        'first_edge_angle_to_wall_normal_degrees_excluding_sharp_TE':stat(np.degrees(np.arccos(np.clip(firstcos[1:-1],-1,1)))),
        'regional_normal_columns':regions,'near_block_design':design['normal'], 'geometry':geom,
        'source_design_audit':'Explicit distributions and actual column measurements, not a whole-layer conclusion inferred from y+.',
        'flow_validation':None}
    results['geometry_mesh_checks_passed']=topology['topology_and_positive_area_checks_passed'] and bool(np.all(jac>0)) and max(errors)<1e-12
    dest=folder/'independent_cgrid_audit.json'
    if dest.exists() and 'algorithm_version' not in json.loads(dest.read_text()):
        (folder/'independent_cgrid_audit_v1_wrong_normal_sign.json').write_bytes(dest.read_bytes())
    dest.write_text(json.dumps(results,indent=2))
    fig,axs=plt.subplots(2,3,figsize=(15,8))
    views=[((-.08,1.15),(-.16,.2),'body and explicit 0.06c block'),((-.015,.04),(-.045,.045),'leading edge'),((.89,1.12),(-.045,.06),'trailing edge and shared cut'),((.35,.46),(.06,.12),'upper x/c 0.4 normal cells'),((.76,.84),(.0,.075),'aft upper x/c 0.8'),((1.,1.7),(-.1,.15),'wake transition')]
    for ax,(xl,yl,title) in zip(axs.ravel(),views):
        inside=((v[:,:,0].max(1)>=xl[0])&(v[:,:,0].min(1)<=xl[1])&(v[:,:,1].max(1)>=yl[0])&(v[:,:,1].min(1)<=yl[1]))
        lines=np.stack([v[inside],np.roll(v[inside],-1,axis=1)],axis=2).reshape(-1,2,2)
        ax.add_collection(LineCollection(lines,colors='#305779',linewidths=.22))
        if len(tri):
            t=allp[tri];inside=((t[:,:,0].max(1)>=xl[0])&(t[:,:,0].min(1)<=xl[1])&(t[:,:,1].max(1)>=yl[0])&(t[:,:,1].min(1)<=yl[1]))
            lines=np.stack([t[inside],np.roll(t[inside],-1,axis=1)],axis=2).reshape(-1,2,2)
            ax.add_collection(LineCollection(lines,colors='#808080',linewidths=.22))
        ax.set(xlim=xl,ylim=yl,title=title,xlabel='x/c',ylabel='y/c',aspect='equal')
    fig.suptitle(name+' actual mesh: close-ups, not a schematic');fig.tight_layout()
    fig.savefig(OUT/'plots'/f'{name}_regional_mesh.png',dpi=180);plt.close(fig)
    print(json.dumps({k:v for k,v in results.items() if k not in ['regional_normal_columns','near_block_design','topology']},indent=2))
    return results

if __name__=='__main__':run(sys.argv[1])
