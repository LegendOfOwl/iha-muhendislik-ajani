"""Review frozen source-case fields. Never select a mesh by best experiment fit."""
from common import ROOT,BASE,CASE,PROJECT,read,save,sha,now
from field_checks import field,cfg
import os
import re
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ETAS=[.2,.44,.65,.8,.9,.96,.99]


def zones(path,ncols):
    out=[];data=[];label=''
    for number,line in enumerate(path.read_text().splitlines(),1):
        s=line.strip()
        if not s or s.startswith('#'):continue
        if s.lower().startswith('zone'):
            if data:out.append((label,np.asarray(data)));data=[]
            label=s;continue
        try:row=[float(x.replace('D','E')) for x in s.split()]
        except ValueError:continue
        if len(row)!=ncols:raise ValueError(f'Unexpected numeric reference row {path.name}:{number}, {len(row)}cols')
        assert np.all(np.isfinite(row));data.append(row)
    if data:out.append((label,np.asarray(data)))
    return out


def slice_surface(grid,eta):
    plane=vtk.vtkPlane();plane.SetOrigin(0,eta*1.4760179762198,0);plane.SetNormal(0,1,0)
    cutter=vtk.vtkCutter();cutter.GenerateTrianglesOff();cutter.SetCutFunction(plane);cutter.SetInputData(grid);cutter.Update();cut=cutter.GetOutput()
    pts=vtk_to_numpy(cut.GetPoints().GetData()).astype(float)
    chord=float(np.ptp(pts[:,0]));leading=float(pts[:,0].min());xy=np.column_stack([(pts[:,0]-leading)/chord,pts[:,2]/chord])
    cp=vtk_to_numpy(cut.GetPointData().GetArray('Pressure_Coefficient'))
    cf=vtk_to_numpy(cut.GetPointData().GetArray('Skin_Friction_Coefficient'))
    pairs=[]
    for i in range(cut.GetNumberOfCells()):
        cell=cut.GetCell(i)
        for j in range(cell.GetNumberOfPoints()-1):pairs.append([cell.GetPointId(j),cell.GetPointId(j+1)])
    assert pairs
    return xy,cp,cf,np.asarray(pairs),chord


def project_values(xy,cp,edges,targets):
    a=xy[edges[:,0]];b=xy[edges[:,1]];v=b-a;den=np.sum(v*v,axis=1);pred=[];distance=[]
    for target in targets:
        t=np.clip(np.sum((target-a)*v,axis=1)/np.maximum(den,1e-300),0,1)
        d=np.linalg.norm(a+t[:,None]*v-target,axis=1);j=int(np.argmin(d))
        pred.append(float((1-t[j])*cp[edges[j,0]]+t[j]*cp[edges[j,1]]));distance.append(float(d[j]))
    return np.asarray(pred),np.asarray(distance)


def main():
    # All three baseline predictions must already be immutable, including failures.
    seals={}
    for role in ['coarse','medium','fine']:
        folder=CASE/('flow_v2_'+role);seal=read(folder/'prediction_frozen.json')
        for p,h in seal['files_sha256'].items():assert sha(ROOT/p)==h
        seals[role]=seal
    experiment=zones(BASE/'sources/case_2308.dat',5);assert len(experiment)==7
    assert sum(len(a) for _,a in experiment)==271
    refs=zones(BASE/'sources/CFL3D_OM6_A3p06_CPCF.dat',8)
    ref1={}
    for label,a in refs:
        if re.search(r'\bL1\b',label):
            eta=float(re.search(r'eta\s*=\s*([0-9.]+)',label).group(1));ref1[eta]=a
    assert len(ref1)==7
    fig,axs=plt.subplots(2,4,figsize=(16,8));fref,aref=plt.subplots(2,4,figsize=(16,8))
    results={};colors={'coarse':'#bf8b3e','medium':'#25858d','fine':'#9c4b60'}
    for role in ['coarse','medium','fine']:
        seal=seals[role];matched=seal['matched'];folder=CASE/('flow_v2_'+role)
        if matched is None:
            results[role]={'matched':None,'reason':'No complete matching native field','quality_passed':False};continue
        i=matched['field_iteration'];surface=folder/f'surface_flow_{i:06d}.vtu';grid,xyz,arrays=field(surface)
        allrows=[];sections=[];code=[]
        for j,((label,ex),eta) in enumerate(zip(experiment,ETAS)):
            assert np.all(ex[:,0]==j+1)
            xy,cp,cf,edges,chord=slice_surface(grid,eta)
            predicted,distance=project_values(xy,cp,edges,ex[:,[2,3]])
            delta=predicted-ex[:,4]
            for side in ['u','l']:
                mask=(ex[:,3]>=0) if side=='u' else (ex[:,3]<0)
                assert mask.any()
                sections.append({'section':j+1,'eta':eta,'side':side,'points':int(mask.sum()),
                    'Cp_RMSE':float(np.sqrt(np.mean(delta[mask]**2))),'Cp_max_absolute_error':float(np.max(abs(delta[mask]))),
                    'max_projection_distance_over_local_chord':float(distance[mask].max())})
            for row,p,d,e in zip(ex,predicted,distance,delta):allrows.append([j+1,eta,row[1],row[2],row[3],row[4],p,e,d])
            ax=axs.flat[j];cfxax=aref.flat[j];reference=ref1[eta]
            for upper,style in [(True,'-'),(False,'--')]:
                mask=xy[:,1]>=0 if upper else xy[:,1]<0;order=np.argsort(xy[mask,0])
                ax.plot(xy[mask,0][order],cp[mask][order],style,color=colors[role],lw=.9,label=role if upper else None)
                cfxax.plot(xy[mask,0][order],cf[mask,0][order],style,color=colors[role],lw=.9,label=role if upper else None)
                if role=='coarse':
                    refmask=reference[:,2]>=0 if upper else reference[:,2]<0;reforder=np.argsort(reference[refmask,7])
                    ax.plot(reference[refmask,7][reforder],reference[refmask,3][reforder],':',color='#243249',lw=1,label='CFL3D L1' if upper else None)
                    cfxax.plot(reference[refmask,7][reforder],reference[refmask,4][reforder],':',color='#243249',lw=1,label='CFL3D L1' if upper else None)
            if role=='coarse':ax.errorbar(ex[:,2],ex[:,4],yerr=.02,fmt='o',ms=2,color='#243249',lw=.5,label='ONERA experiment')
            ax.set(title=f'eta={eta:g}',xlabel='x/c',ylabel='Cp');ax.grid(alpha=.15)
            cfxax.set(title=f'eta={eta:g}',xlabel='x/c',ylabel='Cfx');cfxax.grid(alpha=.15)
        table=np.asarray(allrows);data=PROJECT/f'data/tmr_sharp_20261025_v1/{role}';data.mkdir(exist_ok=True)
        csvpath=data/'experiment_comparison.csv'
        np.savetxt(csvpath,table,delimiter=',',header='section,eta,tap,x_over_c,z_over_c,Cp_experiment,Cp_native,error,projection_distance_over_local_chord',comments='')
        assert len(table)==271
        yp=arrays['Y_Plus'];density=matched['rms[Rho]']< -7
        iteration=density and matched['last100_samples']==100 and matched['CL_last100_range']<1e-4 and matched['CD_last100_range']<1e-5
        results[role]={'matched':matched,'native_status':seal['native_status'],'experiment_points':len(table),
            'all_271_points_kept':True,'Cp_RMSE':float(np.sqrt(np.mean(table[:,7]**2))),
            'Cp_fraction_within_0p02':float(np.mean(abs(table[:,7])<=.02)),'sections':sections,
            'section_screens_passed':sum(s['Cp_RMSE']<.08 for s in sections),'max_yplus':float(yp.max()),
            'wall_points':len(yp),'fraction_yplus_below1':float(np.mean(yp<1)),
            'max_projection_distance_over_local_chord':float(table[:,8].max()),'iterative_gate_passed':bool(iteration),
            'experiment_CSV_sha256':sha(csvpath),'source_surface_sha256':sha(surface),'quality_passed':False}
        print(role,{'Cp_RMSE':results[role]['Cp_RMSE'],'sections':results[role]['section_screens_passed'],
                    'max_yplus':results[role]['max_yplus'],'matched_iteration':i},flush=True)
    for ax in axs.flat[:7]:ax.invert_yaxis()
    for fig,axes,title,dest in [(fig,axs,'TMR source-case diagnostic: all271 experimental points; unconverged runs retained','tmr_Cp_comparison_20261025.png'),
                              (fref,aref,'TMR source-case skin friction: CFD-code comparison, no experimental Cf','tmr_Cfx_CFL3D_comparison_20261025.png')]:
        axes.flat[0].legend(fontsize=7);axes.flat[7].axis('off');axes.flat[7].text(0,.9,'Same source geometry / nested meshes\nM0.84; alpha3.06; Re_root14.6M; T300K\nSA-neg; source sixth station0.96\nCFL3D is numerical reference\nNo GCI or physical qualification',va='top')
        fig.suptitle(title);fig.tight_layout();fig.savefig(PROJECT/'plots'/dest,dpi=150);plt.close(fig)
    save(PROJECT/'reports/tmr_source_case_review_20261025.json',{'reviewed_utc':now(),'results':results,'not_blind':True,
        'reference_source_hashes':{p.name:sha(p) for p in [BASE/'sources/case_2308.dat',BASE/'sources/CFL3D_OM6_A3p06_CPCF.dat']},
        'experiment':'NASA TMR-hosted ONERA pressure measurements; Cp. No experimental force/Cf substituted.',
        'source_case_geometry':'Sharp-TE numerical exercise approximates original blunt experiment; same source definitions as TMR comparison.',
        'chosen_fine_role_before_evaluation':'mesh family L1 (258048cells), never the best Cp run',
        'GCI':None,'GCI_reason':'Three iteratively converged solutions and asymptotic behavior not established.',
        'minimum_physical_qualification_passed':False,'open_gates':['iterative convergence','regional BL/TE/tip/wake','separate farfield sensitivity','experimental acceptance','independent-code grid-asymptotic comparison']})


if __name__=='__main__':main()
