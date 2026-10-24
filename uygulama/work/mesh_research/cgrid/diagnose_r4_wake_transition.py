"""Separate numerical diagnosis; reads own numbered R4 native fields only.

No solver launches, source mesh mutation, reviewer imports or expected results.
"""
from pathlib import Path
import os,json,csv,datetime
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent
OUT=ROOT/'outputs/projects/proje-15cce2de02'
CASE=OUT/'simulations/v3_cgrid_interfacer4_coarse_warmstart'
BASE=OUT/'simulations/v3_cgrid_interfacer4_coarse'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from audit_interface_r4 import parse,sha,stat

ITERATIONS=[1200,1400,4000]
p,q,t,marks=parse(CASE/'mesh.su2');near=np.load(BASE/'near_arrays.npz')
assert sha(CASE/'mesh.su2')==sha(BASE/'mesh.su2')
iface=near['interface'];edges=np.stack([iface,np.roll(iface,-1)],axis=1)
n=len(p);keys=edges.min(1)*n+edges.max(1)
def adjacent(co):
    ee=np.stack([co,np.roll(co,-1,axis=1)],axis=2).reshape(-1,2)
    kk=ee.min(1)*n+ee.max(1);order=np.argsort(kk);ss=kk[order]
    l=np.searchsorted(ss,keys);r=np.searchsorted(ss,keys,side='right')
    assert np.all(r-l==1)
    return order[l]//co.shape[1]
qi=adjacent(q);ti=adjacent(t);a=p[edges[:,0]];b=p[edges[:,1]];v=b-a
L=np.linalg.norm(v,axis=1);mid=(a+b)/2
def height(co,indices,den):
    vv=p[co[indices]]-a[:,None,:]
    return np.abs(v[:,None,0]*vv[:,:,1]-v[:,None,1]*vv[:,:,0]).sum(1)/(den*L)
hq=height(q,qi,2);ht=height(t,ti,1);ratio=ht/hq
adj_nodes=[np.unique(np.r_[q[j],t[k]]) for j,k in zip(qi,ti)]
worst=np.argsort(np.maximum(ratio,1/ratio))[-8:][::-1]
highmask=ratio>20
band=np.unique(np.concatenate([adj_nodes[k] for k in np.flatnonzero(highmask)]))
result={'scope':'Own native 1200/1400/4000 fields at actual R4 interface; no expected result, no CFD run.',
        'residual_scope':'Native exported LinSysRes working vector, not reconstructed and not substituted for history GetRes_RMS. Unweighted nodal squared sums describe these exported arrays only.',
        'field_precision':'VTU Float32 states/residuals mapped to original double SU2 coordinates.',
        'mesh_sha256':sha(CASE/'mesh.su2'),
        'interface_metric':'h_quad=mean perpendicular distance of two off-edge quad vertices; h_tri=perpendicular height of off-edge triangle vertex; ratio=h_tri/h_quad.',
        'high_ratio_band_selection':'All real interface edges with h_triangle/h_quad>20; threshold used only to summarize a diagnosed geometric region, never as a mesh pass cutoff.',
        'high_ratio_edges':int(highmask.sum()),'high_ratio_adjacent_unique_nodes':len(band),
        'high_ratio_midpoint_bbox_m':[mid[highmask].min(0).tolist(),mid[highmask].max(0).tolist()],
        'worst_edges':[], 'iterations':[]}
for k in worst:
    result['worst_edges'].append({'interface_edge_id':int(k),'midpoint_m':mid[k].tolist(),
        'quad_id':int(qi[k]),'triangle_id':int(ti[k]),'interface_nodes':edges[k].tolist(),
        'quad_nodes':q[qi[k]].tolist(),'triangle_nodes':t[ti[k]].tolist(),
        'quad_height_m':float(hq[k]),'triangle_height_m':float(ht[k]),'outside_over_inside_height':float(ratio[k])})

fields={};rows=[]
for it in ITERATIONS:
    path=CASE/f'flow_{it:06d}.vtu';r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(path));r.Update();g=r.GetOutput()
    d,mp=cKDTree(vtk_to_numpy(g.GetPoints().GetData())[:,:2]).query(p)
    assert len(np.unique(mp))==len(p) and d[np.linalg.norm(p,axis=1)<12].max()<1e-6
    data={g.GetPointData().GetArrayName(j):vtk_to_numpy(g.GetPointData().GetArray(j))[mp].astype(float) for j in range(g.GetPointData().GetNumberOfArrays())}
    fields[it]=data
    rr={'density':abs(data['Residual_Density']),'momentum_norm':np.linalg.norm(data['Residual_Momentum'],axis=1),'energy':abs(data['Residual_Energy']),'SA':abs(data['Residual_Nu_Tilde'])}
    rec={'iteration':it,'field_path':str(path.relative_to(ROOT)),'field_sha256':sha(path),'high_ratio_band':{},'worst_edge_local_fields':[]}
    for key,val in rr.items():
        imax=int(np.argmax(val));rec['high_ratio_band'][key]={'fraction_exported_nodal_sum_squared':float(np.sum(val[band]**2)/np.sum(val**2)),
            'band_abs_max_over_global':float(val[band].max()/val.max()),'band_abs_max':float(val[band].max()),
            'global_abs_max':float(val[imax]),'global_max_xy_m':p[imax].tolist(),
            'global_max_distance_to_nearest_high_ratio_edge_midpoint_m':float(np.linalg.norm(mid[highmask]-p[imax],axis=1).min())}
    for k in range(len(edges)):
        ids=adj_nodes[k];row={'iteration':it,'edge_id':k,'x':mid[k,0],'y':mid[k,1],
             'h_quad':hq[k],'h_tri':ht[k],'height_ratio':ratio[k],
             **{key+'_local_abs_max':val[ids].max() for key,val in rr.items()},
             **{key+'_range':np.ptp(data[key][ids]) for key in ['Mach','Density','Pressure']}}
        rows.append(row)
        if k in worst:
            edge_set=set(edges[k]);offq=[int(i) for i in q[qi[k]] if i not in edge_set];offt=[int(i) for i in t[ti[k]] if i not in edge_set]
            normal=np.array([-v[k,1],v[k,0]])/L[k]
            if np.dot(p[offt[0]]-mid[k],normal)<0:normal=-normal
            item={'interface_edge_id':k,'local_abs_max_over_global':{key:float(val[ids].max()/val.max()) for key,val in rr.items()},
                  'local_state_ranges':{key:stat(data[key][ids]) for key in ['Mach','Density','Pressure']},
                  'normal_projection_samples':[]}
            for label,pp in [('inner_quad_opposite_nodes',offq),('interface_nodes',list(edges[k])),('outer_triangle_vertex',offt)]:
                item['normal_projection_samples'].append({'label':label,'ids':[int(i) for i in pp],
                    'mean_xy_m':p[pp].mean(0).tolist(),'mean_normal_s_m':float(np.dot(p[pp].mean(0)-mid[k],normal)),
                    **{key:float(np.mean(data[key][pp])) for key in ['Mach','Density','Pressure']}})
            rec['worst_edge_local_fields'].append(item)
    result['iterations'].append(rec)

csvpath=OUT/'reports/prediction_v3_cgrid_r4_wake_interface_samples.csv'
with csvpath.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

# Wide wake: same per-equation scales at all three checkpoints, vertical display
# intentionally stretched to make cross-wake localization visible.
fig,axs=plt.subplots(len(ITERATIONS),3,figsize=(16,10))
panels=[('density','Residual_Density',(-10,-3)),('momentum','Residual_Momentum',(-10,-3)),('SA','Residual_Nu_Tilde',(-14,-8))]
for row,it in enumerate(ITERATIONS):
    for col,(name,key,clim) in enumerate(panels):
        ax=axs[row,col];raw=fields[it][key];raw=np.linalg.norm(raw,axis=1) if raw.ndim==2 else abs(raw)
        for co in [q,t]:
            cen=p[co].mean(1);mask=(cen[:,0]>-.1)&(cen[:,0]<11.5)&(cen[:,1]>-.25)&(cen[:,1]<.9)
            coll=PolyCollection(p[co[mask]],array=np.log10(np.maximum(raw[co[mask]].mean(1),1e-18)),cmap='magma',clim=clim,edgecolors='none');ax.add_collection(coll)
        ax.plot(p[iface,0],p[iface,1],color='cyan',lw=.35,alpha=.55)
        ax.plot(mid[worst,0],mid[worst,1],'gs',ms=3,mfc='none')
        imax=int(np.argmax(raw));ax.plot(*p[imax],'cx',ms=7)
        ax.set(xlim=(-.05,11.3),ylim=(-.2,.85),xlabel='x/c',ylabel='y/c (display stretched)',title=f'{it}: native exported {name}')
        fig.colorbar(coll,ax=ax,fraction=.04,pad=.02,label='log10 |exported vector|')
fig.suptitle('R4 wake: cyan outlines near-block interface; green squares = 8 largest normal-height jumps; cyan x = global equation maximum')
fig.tight_layout(rect=(0,0,1,.96));fig.savefig(OUT/'plots/prediction_v3_cgrid_r4_wake_residual_overview.png',dpi=170);plt.close(fig)

# Actual worst-ratio patch, with the full outside triangle and ten inside rows.
k=int(worst[0]);cx,cy=mid[k];fig,axs=plt.subplots(1,4,figsize=(17,4.5))
for co in [q,t]:
    cen=p[co].mean(1);mask=(abs(cen[:,0]-cx)<.13)&(abs(cen[:,1]-cy)<.14)
    axs[0].add_collection(PolyCollection(p[co[mask]],facecolors='none',edgecolors='.4',linewidths=.4))
axs[0].add_collection(PolyCollection([p[q[qi[k]]],p[t[ti[k]]]],facecolors=['tab:blue','tab:orange'],alpha=.4,edgecolors='k'))
axs[0].plot(*mid[k],'rx');axs[0].set(xlim=(cx-.1,cx+.1),ylim=(cy-.02,cy+.12),aspect='equal',title=f'Actual interface edge {k}; ratio={ratio[k]:.2f}',xlabel='x/c',ylabel='y/c')
for ax,key in zip(axs[1:],['Mach','Density','Pressure']):
    for rec in result['iterations']:
        sample=next(x for x in rec['worst_edge_local_fields'] if x['interface_edge_id']==k)['normal_projection_samples']
        ax.plot([s[key] for s in sample],[s['mean_normal_s_m'] for s in sample],'o-',label=str(rec['iteration']))
    ax.axhline(0,color='.5',lw=.6);ax.set(xlabel=key,ylabel='normal projection (m)',title='Actual node means; x may differ');ax.grid(alpha=.25)
axs[1].legend();fig.tight_layout();fig.savefig(OUT/'plots/prediction_v3_cgrid_r4_worst_normal_transition.png',dpi=180);plt.close(fig)
result['samples_csv']={'path':str(csvpath.relative_to(ROOT)),'sha256':sha(csvpath)}
result['source_script_sha256']=sha(__file__);result['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'reports/prediction_v3_cgrid_r4_wake_transition.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({key:result[key] for key in ['high_ratio_edges','high_ratio_adjacent_unique_nodes','high_ratio_midpoint_bbox_m']},indent=2))
for rec in result['iterations']:print(rec['iteration'],rec['high_ratio_band'])
