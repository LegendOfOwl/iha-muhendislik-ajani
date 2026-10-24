"""Own numbered R4 warmstart fields only. No solver/mesh mutation or reference data."""
from pathlib import Path
import os,json,csv,hashlib,datetime
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent;OUT=ROOT/'outputs/projects/proje-15cce2de02';CASE=OUT/'simulations/v3_cgrid_interfacer4_coarse_warmstart';MESHCASE=OUT/'simulations/v3_cgrid_interfacer4_coarse'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from audit_interface_r4 import parse,quality,stat,sha
from interface_distance_r4 import InterfaceSizing

ITERATIONS=[1200,1400]
assert sha(CASE/'mesh.su2')==sha(MESHCASE/'mesh.su2')
p,q,t,marks=parse(CASE/'mesh.su2');k=quality(p,q,t);near=np.load(MESHCASE/'near_arrays.npz');gid=near['grid_ids'];grid=p[gid];des=json.loads((MESHCASE/'near_design.json').read_text());nj,ni=gid.shape;nw=des['wake_segments_each_side'];nl=des['wall_lower_segments'];nu=des['wall_upper_segments'];normald=np.array(des['near_rows_distance_m']);interface=InterfaceSizing(p[near['interface']])
flat=np.unique(gid.ravel(),return_index=True)[1];lookup={int(v):(int(j),int(i)) for j,row in enumerate(gid) for i,v in enumerate(row)}
es=np.concatenate([np.stack([q,np.roll(q,-1,axis=1)],axis=2).reshape(-1,2),np.stack([t,np.roll(t,-1,axis=1)],axis=2).reshape(-1,2)]);es=np.unique(np.sort(es,axis=1),axis=0)
neighbors=[[] for _ in p]
for a,b in es:neighbors[a].append(int(b));neighbors[b].append(int(a))
labels=np.full(len(p),'exterior_far',dtype=object)
for nid,(j,i) in lookup.items():
    if nw<=i<=nw+nl+nu:labels[nid]='body_logical_d_le_0.01' if normald[j]<=.01 else 'body_logical_d_gt_0.01'
    else:labels[nid]='structured_wake'
labels[near['interface']]='interface_nodes';labels[marks['AIRFOIL'].ravel()]='wall_nodes'
for idx in range(len(near['points']),len(p)):
    if interface.nearest(p[idx],compact=True) is not None:labels[idx]='exterior_within_1c'
# A broad-phase hit can include d>=1; correct classification explicitly.
for idx in np.flatnonzero(labels=='exterior_within_1c'):
    if interface.nearest(p[idx],compact=False)[0]>=1:labels[idx]='exterior_far'

with (CASE/'history.csv').open(newline='') as f:
    reader=csv.reader(f);header=[x.strip().strip('"') for x in next(reader)];hrows=[]
    for row in reader:
        if len(row)!=len(header):continue
        try:vals=[float(v) for v in row]
        except ValueError:continue
        if vals[header.index('Inner_Iter')]<=max(ITERATIONS):hrows.append(vals)
hist=np.array(hrows);history={int(r[header.index('Inner_Iter')]):dict(zip(header,r)) for r in hist}
snap=WORK/'r4_warmstart_history_through001400.csv'
with snap.open('w',newline='') as f:w=csv.writer(f);w.writerow(header);w.writerows(hist)

def load(it):
    path=CASE/f'flow_{it:06d}.vtu';reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(path));reader.Update();g=reader.GetOutput();vp=vtk_to_numpy(g.GetPoints().GetData())[:,:2];d,mp=cKDTree(vp).query(p)
    assert len(np.unique(mp))==len(p) and d[np.linalg.norm(p,axis=1)<2].max()<1e-7
    arrays={g.GetPointData().GetArrayName(i):vtk_to_numpy(g.GetPointData().GetArray(i))[mp].astype(float) for i in range(g.GetPointData().GetNumberOfArrays())}
    return arrays,{'field':str(path.relative_to(ROOT)),'field_sha256':sha(path),'VTU_points':g.GetNumberOfPoints(),'VTU_cells':g.GetNumberOfCells(),'max_nearbody_mapping_error_m':float(d[np.linalg.norm(p,axis=1)<2].max()),'native_data_precision':'VTU Float32; native nonlinear residual arrays read directly; gradients below reconstructed from states, not native saved gradients'}

def info_node(nid,data):
    loc=lookup.get(int(nid));hit=interface.nearest(p[nid],compact=False)
    result={'point_id':int(nid),'xy_m':p[nid].tolist(),'region':str(labels[nid]),'interface_distance_m':hit[0],'neighbors':len(neighbors[nid]),'Mach':float(data['Mach'][nid]),'Density':float(data['Density'][nid]),'Pressure':float(data['Pressure'][nid])}
    if loc is not None:result.update({'grid_row_column':list(loc),'logical_normal_d_m':float(normald[loc[0]])})
    return result

def scalar_gradient(nid,f):
    nei=np.array(neighbors[nid]);delta=p[nei]-p[nid];dist=np.linalg.norm(delta,axis=1);A=delta/dist[:,None];rhs=(f[nei]-f[nid])/dist
    grad,_,_,_=np.linalg.lstsq(A,rhs,rcond=None);fit=A@grad
    exact,_,_,_=np.linalg.lstsq(A,((p[nei,0]+2*p[nei,1])-(p[nid,0]+2*p[nid,1]))/dist,rcond=None)
    return {'gradient_per_m':grad.tolist(),'weighted_normal_matrix_condition':float(np.linalg.cond(A.T@A)),'relative_stencil_fit_residual':float(np.linalg.norm(fit-rhs)/(np.linalg.norm(rhs)+1e-30)),'linear_function_x_plus_2y_gradient_error':float(np.linalg.norm(exact-[1,2])),'scope':'WEIGHTED_LEAST_SQUARES diagnostic reconstructed from Float32 VTU states on original double mesh coordinates; not an exported native solver gradient.'}

def line_measure(ids,field):
    xyz=p[ids];s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xyz,axis=0),axis=1))];v=field[ids]
    pred=((s[2:]-s[1:-1])*v[:-2]+(s[1:-1]-s[:-2])*v[2:])/(s[2:]-s[:-2]);hf=v[1:-1]-pred;diff=np.diff(v)
    return {'n':len(ids),'value_range':[float(v.min()),float(v.max())],'interpolated_neighbor_difference_RMS':float(np.sqrt(np.mean(hf**2))),'interpolated_neighbor_difference_abs_max':float(abs(hf).max()),'adjacent_slope_sign_reversals':int(np.sum(diff[:-1]*diff[1:]<0)),'definition':'At each interior point subtract straight interpolation between its two neighbors using real nonuniform arclength; a diagnostic high-frequency indicator, not an acceptance tolerance.'}

fields={};result={'scope':'Own R4 numbered1200/1400 fields only; full native residual arrays, geometry unchanged. No solver run. No expected/reference flow result read.','mesh_sha256':sha(CASE/'mesh.su2'),'mesh_matches_geometrically_audited_R4':True,'selected_history_snapshot':str(snap.relative_to(ROOT)),'selected_history_snapshot_sha256':sha(snap),'iterations':[]};clusters=[]
for it in ITERATIONS:
    data,meta=load(it);fields[it]=data;hr=history[it];residuals={'density':data['Residual_Density'],'momentum_norm':np.linalg.norm(data['Residual_Momentum'],axis=1),'energy':data['Residual_Energy'],'SA':data['Residual_Nu_Tilde']};records={}
    for key,raw in residuals.items():
        rr=abs(raw);top=np.argsort(rr)[-20:][::-1];total=np.sum(rr**2);regions={str(reg):{'nodes':int(np.sum(labels==reg)),'fraction_nodal_sum_squared_residual':float(np.sum(rr[labels==reg]**2)/total),'abs_max':float(rr[labels==reg].max()),'RMS':float(np.sqrt(np.mean(rr[labels==reg]**2)))} for reg in np.unique(labels)}
        records[key]={'RMS_from_native_nodal_field':float(np.sqrt(np.mean(rr**2))),'log10_RMS_from_field':float(np.log10(np.sqrt(np.mean(rr**2)))),'absolute_max':float(rr.max()),'top20':[dict(info_node(int(i),data),native_residual_signed_or_norm=float(raw[i])) for i in top],'regions':regions}
    # Choose density anchors globally by residual magnitude, not by old shock box.
    for i in np.argsort(abs(data['Residual_Density']))[::-1]:
        if int(i) not in lookup:continue
        if len(clusters)>=6:break
        if all(np.linalg.norm(p[i]-p[a['point_id']])>.025 for a in clusters):clusters.append({'point_id':int(i),'selected_from_iteration':it,'selection':'global |native density residual|, at least0.025c from earlier anchors; structured node required for row/column diagnostics'})
        if sum(a['selected_from_iteration']==it for a in clusters)>=3:break
    oldbox=(p[:,0]>.5)&(p[:,0]<.54)&(p[:,1]>.095)&(p[:,1]<.125)
    aftermeta={'checkpoint_iteration_local':it,**meta,'history_at_exact_iteration':hr,'residuals':records,'old_original_hotbox_density_sum_square_fraction':float(np.sum(data['Residual_Density'][oldbox]**2)/np.sum(data['Residual_Density']**2))}
    window=hist[(hist[:,header.index('Inner_Iter')]>it-200)&(hist[:,header.index('Inner_Iter')]<=it)];aftermeta['last200_history_force_range']={key:float(np.ptp(window[:,header.index(key)])) for key in ['CL','CD']};aftermeta['last200_linear_solver']={key:stat(window[:,header.index(key)]) for key in ['Linear_Solver_Iterations','LinSolRes','LinSolIterTurb','LinSolResTurb']}
    for kind in ['surface_flow','restart_flow']:
        ext='vtu' if kind=='surface_flow' else 'dat';f=CASE/f'{kind}_{it:06d}.{ext}';assert f.exists();aftermeta[kind+'_same_checkpoint']={'path':str(f.relative_to(ROOT)),'sha256':sha(f)}
    result['iterations'].append(aftermeta)

anchor_records=[]
for anchor in clusters:
    nid=anchor['point_id'];j,i=lookup[nid];measure=[]
    for it in ITERATIONS:
        data=fields[it];tids=gid[j,max(0,i-8):min(ni,i+9)];nids=gid[max(0,j-8):min(nj,j+9),i]
        rec={'iteration':it,**info_node(nid,data),'directions':{direction:{key:line_measure(ids,data[key]) for key in ['Mach','Density','Pressure']} for direction,ids in [('tangential_row',tids),('normal_column',nids)]},'reconstructed_state_gradient':{key:scalar_gradient(nid,data[key]) for key in ['Mach','Density','Pressure']}}
        measure.append(rec)
    anchor_records.append({**anchor,'measurements':measure})
result['global_density_anchor_diagnostics']=anchor_records

# Native residual distribution: fixed bounds and color range across selected fields.
fig,axs=plt.subplots(2,3,figsize=(15,8))
for row,it in enumerate(ITERATIONS):
    d=fields[it]
    for ax,(name,field) in zip(axs[row],[('density',abs(d['Residual_Density'])),('energy',abs(d['Residual_Energy'])),('SA',abs(d['Residual_Nu_Tilde']))]):
        for co in [q,t]:
            v=p[co];center=v.mean(1);mask=(center[:,0]>-.1)&(center[:,0]<1.2)&(center[:,1]>-.2)&(center[:,1]<.45);coll=PolyCollection(v[mask],array=np.log10(np.maximum(field[co[mask]].mean(1),1e-16)),cmap='magma',clim=(-10,-3),edgecolors='none');ax.add_collection(coll)
        for e in marks['AIRFOIL']:ax.plot(p[e,0],p[e,1],'k-',lw=.45)
        top=np.argmax(field);ax.plot(*p[top],'cx',ms=7);ax.set(xlim=(-.05,1.1),ylim=(-.15,.4),aspect='equal',title=f'local {it}: native {name} residual',xlabel='x/c',ylabel='y/c')
fig.suptitle('Actual numbered R4 warmstart fields; cyan = global maximum; common log10 residual scale')
fig.tight_layout(rect=(0,0,.94,.94));cax=fig.add_axes([.95,.2,.012,.6]);fig.colorbar(coll,cax=cax);fig.savefig(OUT/'plots/prediction_v3_cgrid_r4_warmstart_native_residuals.png',dpi=170);plt.close(fig)

# Fixed spatial anchors for both selected checkpoints, avoid changing the sample
# column to make a cleaner-looking curve.
fig,axs=plt.subplots(len(clusters),3,figsize=(14,3.1*len(clusters)))
for row,anchor in enumerate(clusters):
    nid=anchor['point_id'];j,i=lookup[nid];ids=gid[max(0,j-8):min(nj,j+9),i];s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p[ids],axis=0),axis=1))]
    for col,key in enumerate(['Mach','Density','Residual_Density']):
        ax=axs[row,col]
        for it in ITERATIONS:ax.plot(fields[it][key][ids],s,'o-',ms=3,label=str(it))
        ax.set(xlabel=key,ylabel='column arclength (m)',title=f'anchor ({p[nid,0]:.6f},{p[nid,1]:.6f}), j={j}, i={i}',yscale='linear');ax.grid(alpha=.25)
    axs[row,0].legend()
fig.tight_layout();fig.savefig(OUT/'plots/prediction_v3_cgrid_r4_warmstart_fixed_columns.png',dpi=160);plt.close(fig)
result['input_files_sha256']={str(f.relative_to(ROOT)):sha(f) for f in [CASE/'mesh.su2',CASE/'case.cfg',CASE/'controlled_trial.json',MESHCASE/'near_arrays.npz',MESHCASE/'near_design.json',snap]+[CASE/f'flow_{it:06d}.vtu' for it in ITERATIONS]};result['analysis_script_sha256']=sha(__file__);result['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'reports/prediction_v3_cgrid_r4_warmstart_diagnosis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('anchors',[(a['point_id'],p[a['point_id']].tolist()) for a in clusters]);print([(x['checkpoint_iteration_local'],{k:(v['absolute_max'],v['top20'][0]['xy_m']) for k,v in x['residuals'].items()},x['old_original_hotbox_density_sum_square_fraction']) for x in result['iterations']])
