"""Operational boundary-layer edge/resolution checks from OWN native volume fields only."""
from pathlib import Path
import sys,json,csv,os,shutil
import numpy as np,vtk
from vtk.util.numpy_support import vtk_to_numpy,numpy_to_vtk
from scipy.interpolate import BSpline
from scipy.optimize import brentq
from postprocess import read_vtu,OUT,ROOT
from audit_mesh_family import parse_mesh
os.environ['MPLCONFIGDIR']=str(Path(__file__).parent/'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def inspect(name):
    folder=OUT/'simulations'/name;sel=json.loads((folder/'checkpoint_selection.json').read_text());d,xyz,a=read_vtu(ROOT/sel['volume'])
    profile_dir=folder/f'profiles_iter{sel["iteration"]:06d}';profile_dir.mkdir(exist_ok=True)
    p,c,markers=parse_mesh(folder/'mesh.su2');ar=json.loads((folder/'mesh_audit.json').read_text());layer=float(ar['BL_thickness_m']);edge_set=set()
    for co in c:
        for i,j in zip(co,np.roll(co,-1)):edge_set.add(tuple(sorted([int(i),int(j)])))
    edges=np.array(list(edge_set));ea=p[edges[:,0]];ev=p[edges[:,1]]-ea
    wall=markers['AIRFOIL'];tab=np.loadtxt(ROOT/'work/blind_validation/analysis_input/geom.txt',skiprows=5)
    records=[];fig,axs=plt.subplots(2,3,figsize=(14,8));fig2,axs2=plt.subplots(2,3,figsize=(14,8))
    for row,side in enumerate(['upper','lower']):
        pay=ar['interpolation_payload'][row];bs=BSpline(pay['knots'],pay['coefficients_m'],pay['degree']);tmin=bs.t[3];tmax=bs.t[-4]
        for col,station in enumerate([.4,.8,.95]):
            tt=brentq(lambda t:float(bs(t)[0]-station),tmin,tmax);tan=bs.derivative()(tt);tan/=np.linalg.norm(tan);normal=np.array([-tan[1],tan[0]]);flowtan=tan if tan[0]>0 else -tan
            # Use an actual solver boundary-segment origin at this x, rather than a point inside a curved CAD edge.
            wa=p[wall[:,0]];wb=p[wall[:,1]];mid=(wa+wb)/2
            yl=-np.interp(mid[:,0],tab[:,0],tab[:,1]);yu=np.interp(mid[:,0],tab[:,0],tab[:,2]);isup=np.abs(mid[:,1]-yu)<np.abs(mid[:,1]-yl)
            mask=(np.minimum(wa[:,0],wb[:,0])<=station)&(np.maximum(wa[:,0],wb[:,0])>=station)&(isup==(side=='upper'))
            ids=np.where(mask)[0];assert len(ids)>=1
            j=ids[0];u=(station-wa[j,0])/(wb[j,0]-wa[j,0]);origin=(1-u)*wa[j]+u*wb[j]
            # Exact line intersections with every exported cell edge give the true normal grid cuts.
            den=normal[0]*ev[:,1]-normal[1]*ev[:,0];q=ea-origin;validden=abs(den)>1e-15
            dist=np.full(len(den),np.nan);along=np.full(len(den),np.nan)
            dist[validden]=(q[validden,0]*ev[validden,1]-q[validden,1]*ev[validden,0])/den[validden]
            along[validden]=(q[validden,0]*normal[1]-q[validden,1]*normal[0])/den[validden]
            cut=dist[(dist>=0)&(dist<=.1000001)&(along>=-1e-9)&(along<=1+1e-9)]
            cut=np.sort(np.r_[0,cut]);cut=cut[np.r_[True,np.diff(cut)>1e-10]];dn=np.diff(cut)
            ns=np.unique(np.r_[0,np.geomspace(1e-7,.1,180),np.linspace(.001,.1,200),cut[cut<=.1]])
            coords=np.c_[origin[None,:]+ns[:,None]*normal,np.zeros(len(ns))]
            points=vtk.vtkPoints();points.SetData(numpy_to_vtk(coords,deep=True));poly=vtk.vtkPolyData();poly.SetPoints(points)
            probe=vtk.vtkProbeFilter();probe.SetInputData(poly);probe.SetSourceData(d);probe.SetComputeTolerance(False);probe.SetTolerance(1e-10);probe.Update();pd=probe.GetOutput().GetPointData()
            aa={pd.GetArrayName(i):vtk_to_numpy(pd.GetArray(i)) for i in range(pd.GetNumberOfArrays())}
            mask=aa['vtkValidPointMask'].astype(bool);vel=aa['Velocity'][:,:2];ut=vel@flowtan;un=vel@normal;ratio=aa['Eddy_Viscosity']/np.maximum(aa['Laminar_Viscosity'],1e-30);cp=aa['Pressure_Coefficient']
            candidates={}
            valid_indices=np.where(mask)[0]
            for label,lo,hi in [('near_outer',.025,.045),('far_outer',.05,.08)]:
                outer=(ns>=lo)&(ns<=hi)&mask;ue=float(np.median(ut[outer]))
                found=[]
                for vk,k in enumerate(valid_indices):
                    if ns[k]<1e-7 or ns[k]>=lo or ut[k]<.99*ue:continue
                    # Failed VTK probes contain zeros and cannot define a physical edge.
                    # Five successive VALID samples must satisfy the99% criterion.
                    following=valid_indices[vk:vk+5]
                    if len(following)==5 and np.all(ut[following]>=.99*ue):found.append(k)
                delta=float(ns[found[0]]) if found else None
                candidates[label]={'Ue_over_Uinf':ue,'outer_distance_window_c':[lo,hi],'outer_relative_velocity_range':float(np.ptp(ut[outer])/abs(ue)),'operational_delta99_c':delta}
            ue=candidates['far_outer']['Ue_over_Uinf'];delta=candidates['far_outer']['operational_delta99_c'];k=int(np.searchsorted(ns,.01));inter=int(np.clip(np.searchsorted(cut,.01)-1,0,len(dn)-1))
            normal_info={'first_normal_interval_m':float(dn[0]),'normal_interval_containing_layer_edge_0p01_m':float(dn[inter]),'normal_intervals_near_0p01_m':dn[max(0,inter-3):inter+5].tolist(),'normal_cells_within_0p01':int(np.sum(cut<=.01)-1),'normal_cell_intersections_to_0p1':cut.tolist(),'max_normal_interval_below_operational_delta99_m':float(dn[cut[:-1]<delta].max()) if delta is not None and np.any(cut[:-1]<delta) else None,'normal_cells_below_operational_delta99':int(np.sum(cut<delta)-1) if delta is not None else None}
            rec={'station_x_over_c':station,'side':side,'actual_mesh_wall_origin_m':origin.tolist(),'source_spline_outward_normal':normal.tolist(),'valid_samples':int(mask.sum()),'invalid_sample_distances_c':ns[~mask].tolist(),'edge_definitions':candidates,'at_BL_outer_boundary_0p01':{'Ut_over_Ue_far_window':float(ut[k]/ue),'mu_t_over_mu':float(ratio[k]),'Cp':float(cp[k])},'max_mu_t_over_mu':float(ratio[mask].max()),'layer0p01_covers_operational_delta99':bool(delta is not None and delta<=.01),'normal_resolution':normal_info,'interpretation':'delta99 uses median tangential velocity in the explicitly recorded outer window, not a known experiment. Pressure gradients/potential-flow variation can make a unique Ue ambiguous; two edge-window definitions and their outer velocity ranges are retained. A y+ pass does not establish full boundary-layer coverage.'}
            rec['at_BL_outer_boundary_0p01']={'Ut_over_Ue_far_window':float(np.interp(.01,ns[mask],ut[mask])/ue),'mu_t_over_mu':float(np.interp(.01,ns[mask],ratio[mask])),'Cp':float(np.interp(.01,ns[mask],cp[mask])),'sampling':'interpolated from valid native-field probes only'}
            kl=int(np.searchsorted(ns,layer));il=int(np.clip(np.searchsorted(cut,layer)-1,0,len(dn)-1))
            rec.update({'prescribed_quad_layer_thickness_c':layer,'at_prescribed_quad_layer_edge':{'Ut_over_Ue_far_window':float(ut[kl]/ue),'mu_t_over_mu':float(ratio[kl]),'Cp':float(cp[kl])},'quad_layer_covers_operational_delta99':bool(delta is not None and delta<=layer)})
            rec['at_prescribed_quad_layer_edge']={'Ut_over_Ue_far_window':float(np.interp(layer,ns[mask],ut[mask])/ue),'mu_t_over_mu':float(np.interp(layer,ns[mask],ratio[mask])),'Cp':float(np.interp(layer,ns[mask],cp[mask])),'sampling':'interpolated from valid native-field probes only'}
            rec['normal_resolution'].update({'normal_interval_containing_prescribed_layer_edge_m':float(dn[il]),'normal_cells_within_prescribed_quad_layer':int(np.sum(cut<=layer)-1)})
            records.append(rec)
            csvfile=profile_dir/f'BL_profile_{side}_x{station:.2f}.csv'
            with csvfile.open('w',newline='') as f:
                w=csv.writer(f);w.writerow(['normal_distance_over_c','Ut_over_Uinf','Un_over_Uinf','Ut_over_Ue_far_window','eddy_to_laminar_viscosity','Cp','valid_probe']);w.writerows(zip(ns,ut,un,ut/ue,ratio,cp,mask.astype(int)))
            shutil.copy2(csvfile,folder/csvfile.name)
            ax=axs[row,col];ax.plot(ut[mask]/ue,ns[mask],lw=1);ax.axhline(layer,color='r',ls='--',label=f'quad-layer thickness{layer}c');ax.axvline(.99,color='gray',ls=':');ax.set(xlim=(-.05,1.15),ylim=(0,.06),xlabel='Ut / operational Ue',ylabel='normal distance / c',title=f'{side}, x/c={station}');ax.grid(alpha=.25)
            ax2=axs2[row,col];ax2.plot(ratio[mask],ns[mask],lw=1);ax2.axhline(layer,color='r',ls='--');ax2.set(ylim=(0,.06),xlabel='eddy / laminar viscosity',ylabel='normal distance / c',title=f'{side}, x/c={station}');ax2.grid(alpha=.25)
    for figx,key in [(fig,'velocity'),(fig2,'eddy')]:figx.suptitle(name+f' own native field iter{sel["iteration"]}; red=structured-layer outer edge');figx.tight_layout();figx.savefig(OUT/'plots'/f'prediction_v2_BL_{key}_{name}_iter{sel["iteration"]:06d}.png',dpi=150);plt.close(figx)
    report={'run':name,'field_checkpoint':sel,'profile_algorithm_revision':2,'delta99_validity_note':'Edge search uses5 successive VALID VTK probes; invalid-probe locations remain explicitly listed and in CSV but their zero placeholder velocities are excluded. Earlier algorithm audits are preserved in profiles_algorithm_v1. No native field is modified.','data_scope':'Only own native volume and own source-defined wall; no experimental profile used','profiles':records,'coverage_warning':any(not r['quad_layer_covers_operational_delta99'] for r in records),'coverage_warning_meaning':f'One or more operational99% velocity edges lie beyond the{layer}c quad block, or were not identified. Exterior triangles also resolve fluid, but their measured normal cuts must be assessed; maxY+ alone does not close this check. This postprocess is a diagnostic, not a post-hoc tolerance relaxation.'}
    (folder/'boundary_layer_profile_audit.json').write_text(json.dumps(report,indent=2));(profile_dir/'boundary_layer_profile_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({'run':name,'coverage_warning':report['coverage_warning'],'profiles':[{'side':r['side'],'x':r['station_x_over_c'],'edge':r['edge_definitions'],'at_BL_edge':r['at_BL_outer_boundary_0p01'],'normal_cells':r['normal_resolution']['normal_cells_below_operational_delta99']} for r in records]},indent=2));return report
if __name__=='__main__':inspect(sys.argv[1])
