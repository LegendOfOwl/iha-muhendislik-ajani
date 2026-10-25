"""Guard an empirical curvature priority by geometric support and scale agreement."""
import os
os.environ['MPLCONFIGDIR']=str(__import__('pathlib').Path(__file__).resolve().parent/'mpl_cache')
from curvature import reconstruct, indicator
import numpy as np
from scipy.spatial import cKDTree, ConvexHull, QhullError
from linear_pair import ROOT, PROJECT, RUN, read, save, sha, now


def support_covered(stencil, vertices):
    """Exact convex-hull containment after whitening; mask flat/degenerate support."""
    stencil=np.asarray(stencil,dtype=float);vertices=np.asarray(vertices,dtype=float)
    origin=stencil.mean(axis=0);delta=stencil-origin
    _,s,vh=np.linalg.svd(delta,full_matrices=False)
    if s[-1]<=s[0]*1e-8 or s[0]<=0:return False
    transform=vh.T/s[None,:]
    q=delta@transform;v=(vertices-origin)@transform
    try:hull=ConvexHull(q)
    except QhullError:return False
    return bool(np.all(v@hull.equations[:,:3].T+hull.equations[:,3] <= 1e-9))


def main():
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy,numpy_to_vtk
    folder=RUN/'lin10';seal=read(folder/'prediction_frozen.json');iteration=seal['matched']['field_iteration']
    source=folder/f'flow_{iteration:06d}.vtu';assert sha(source)==seal['files_sha256'][str(source.relative_to(ROOT))]
    oldreport=PROJECT/'reports/m6_curvature_20261024.json';old=read(oldreport)
    out=PROJECT/'data/reliability_v2_20261025';assert not out.exists();out.mkdir()
    save(out/'contract.json',{'created_utc':now(),'source_sha256':sha(source),'v1_report_sha256':sha(oldreport),
         'reason':'V1 priorities could extrapolate a thin-point stencil across a larger cell and grow without physical scale support.',
         'neighbors':[40,80],'maximum_design_condition':1e4,'maximum_relative_fit_RMSE':.1,
         'support':'All four actual tetrahedron vertices must lie within the whitened convex hull of the40-nearest-point stencil.',
         'scale_agreement':'abs(I40-I80)/max(I40,I80,1e-12)<=0.5',
         'priority':'Largest1% of eligible I80; noneligible cells kept as masked diagnostics.',
         'not_error_bound':True,'no_target_values':True,'not_blind_session':True,'code_sha256':sha(__file__)})
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(source));reader.Update();grid=reader.GetOutput()
    points=vtk_to_numpy(grid.GetPoints().GetData()).astype(float);mach=vtk_to_numpy(grid.GetPointData().GetArray('Mach')).astype(float)
    types=vtk_to_numpy(grid.GetCellTypes());tet=np.flatnonzero(types==vtk.VTK_TETRA)
    conn=vtk_to_numpy(grid.GetCells().GetConnectivityArray());off=vtk_to_numpy(grid.GetCells().GetOffsetsArray())
    ids=conn[off[tet,None]+np.arange(4)[None,:]];vertices=points[ids];centers=vertices.mean(axis=1)
    sr=vtk.vtkXMLUnstructuredGridReader();sr.SetFileName(str(folder/f'surface_flow_{iteration:06d}.vtu'));sr.Update()
    wall=vtk_to_numpy(sr.GetOutput().GetPoints().GetData()).astype(float)
    distances,_=cKDTree(wall).query(centers);candidate=np.flatnonzero(distances<2*.64607)
    n=len(tet);value40=np.full(n,np.nan);value80=np.full(n,np.nan)
    supported=np.zeros(n,dtype=bool);fitgood=np.zeros(n,dtype=bool);scalegood=np.zeros(n,dtype=bool)
    fit_error=np.full(n,np.nan);directions=np.full((n,3),np.nan);direction_valid=np.zeros(n,dtype=bool)
    tree=cKDTree(points)
    for start in range(0,len(candidate),512):
        take=candidate[start:start+512];c=centers[take]
        a,ma,ca,ea=reconstruct(points,mach,c,40);b,mb,cb,eb=reconstruct(points,mach,c,80)
        common=ma&mb
        good=take[common]
        if not len(good):continue
        va,da=indicator(a[common],vertices[good]);vb,db=indicator(b[common],vertices[good])
        value40[good],value80[good]=va,vb
        fit_error[take]=np.maximum(ea,eb)
        fg=common&(ca<1e4)&(cb<1e4)&(ea<=.1)&(eb<=.1)
        fitgood[take]=fg
        scalegood[good]=np.abs(va-vb)/np.maximum(np.maximum(va,vb),1e-12)<=.5
        valid_direction=(np.abs(np.einsum('ni,ni->n',da,db))>=np.cos(np.pi/6))
        ev=np.sort(np.abs(np.linalg.eigvalsh(b[common])),axis=1)
        valid_direction &= ev[:,-1]>2*np.maximum(ev[:,-2],1e-20)
        directions[good[valid_direction]]=db[valid_direction];direction_valid[good[valid_direction]]=True
        for local in np.flatnonzero(fg):
            i=take[local]
            _,near=tree.query(centers[i],k=40)
            supported[i]=support_covered(points[near],vertices[i])
    eligible=fitgood&supported&scalegood
    threshold=float(np.quantile(value80[eligible],.99)) if eligible.any() else None
    selected=eligible&(value80>=threshold) if threshold is not None else np.zeros(n,dtype=bool)
    import csv
    path=out/'curvature_v2_cells.csv'
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['cell_id','x_m','y_m','z_m','I40','I80','fit_good','support_covered','scale_agreement','eligible','selected','fit_relative_rmse','direction_valid','dir_x','dir_y','dir_z'])
        for i in candidate:
            nullable=lambda v:float(v) if np.isfinite(v) else ''
            w.writerow([int(tet[i]),*centers[i],nullable(value40[i]),nullable(value80[i]),int(fitgood[i]),int(supported[i]),int(scalegood[i]),int(eligible[i]),int(selected[i]),nullable(fit_error[i]),int(direction_valid[i]),*[nullable(v) for v in directions[i]]])
    for name,data in [('GuardedCurvature',np.where(eligible,value80,np.nan)),('FitGood',fitgood),('SupportCovered',supported),('ScaleAgreement',scalegood),('Eligible',eligible),('Selected',selected)]:
        full=np.full(grid.GetNumberOfCells(),np.nan);full[tet]=data
        ar=numpy_to_vtk(full,deep=True);ar.SetName(name);grid.GetCellData().AddArray(ar)
    writer=vtk.vtkXMLUnstructuredGridWriter();writer.SetFileName(str(out/'curvature_v2_view.vtu'));writer.SetInputData(grid);assert writer.Write()
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(12,5))
    show=np.flatnonzero(eligible);show=show[np.argsort(value80[show])]
    if len(show):
        sc=ax[0].scatter(centers[show,0],centers[show,1],c=np.log10(np.maximum(value80[show],1e-12)),s=2,cmap='viridis')
        fig.colorbar(sc,ax=ax[0],label='log10 guarded indicator')
    ax[1].scatter(centers[selected,0],centers[selected,1],s=8,c='#ce7040')
    for a in ax:a.scatter(wall[:,0],wall[:,1],s=.1,c='#555',alpha=.1);a.set(xlabel='x [m]',ylabel='y [m]');a.set_aspect('equal');a.grid(alpha=.2)
    ax[0].set_title('Supported, fit and scale-consistent cells')
    ax[1].set_title('Top 1% of eligible cells; projection')
    fig.suptitle('Guarded inspection priority v2; NOT an error bound or remeshed result')
    fig.tight_layout();plot=PROJECT/'plots/m6_curvature_v2_20261025.png';fig.savefig(plot,dpi=150);plt.close(fig)
    with (PROJECT/'data/reliability_20261024/curvature_cells.csv').open() as f:
        old_max=max(float(r['indicator']) for r in csv.DictReader(f) if r['selected']=='1')
    result={'created_utc':now(),'source_field':str(source.relative_to(ROOT)),'source_sha256':sha(source),
            'version':2,'region_candidates':len(candidate),'fit_quality_passed':int(fitgood.sum()),
            'support_covered_among_good_fits':int((supported&fitgood).sum()),'eligible':int(eligible.sum()),
            'not_eligible':int(len(candidate)-eligible.sum()),'selected_cells':int(selected.sum()),'quantile99':threshold,
            'selected_direction_valid':int((selected&direction_valid).sum()),
            'selected_bbox_m':{'min':centers[selected].min(axis=0).tolist(),'max':centers[selected].max(axis=0).tolist()} if selected.any() else None,
            'v1_preserved':str(oldreport.relative_to(ROOT)),'v1_selected_max_indicator_warning':old_max,
            'scope':'Geometric/fit/scale checks improve rejection of unreliable stencils. No proof of CFD error estimation or unseen generalisation.',
            'minimum_qualification_passed':False,'permission_to_claim_error_bound':False,
            'artifacts':{str(p.relative_to(ROOT)):sha(p) for p in [out/'contract.json',path,out/'curvature_v2_view.vtu',plot]}}
    save(PROJECT/'reports/m6_curvature_v2_20261025.json',result);print(__import__('json').dumps(result,indent=2))


if __name__=='__main__':main()
