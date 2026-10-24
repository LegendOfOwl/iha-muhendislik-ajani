"""Inspect real CFD volume/surface fields, reference curves and CAD geometry."""
from datetime import datetime,timezone
import csv
import json
import os
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'; SOURCE=ROOT/'work/qualification/sources'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib')); os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,o): path.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def zones(path):
    groups={}; name='default'; values=[]
    for line in path.read_text().splitlines():
        if line.lower().startswith('zone'):
            if values: groups[name]=np.array(values); values=[]
            name=line.split('"')[1]
        else:
            try: values.append([float(s) for s in line.split()])
            except ValueError: pass
    if values: groups[name]=np.array(values)
    return groups
def main():
    result=read(OUT/'reports/cfd_qualification.json'); summaries=[]; fields={}
    for row in result['results']:
        if not row['runtime_passed']: continue
        folder=Path(row['folder']); r=vtk.vtkXMLUnstructuredGridReader(); r.SetFileName(str(folder/'flow.vtu')); r.Update(); grid=r.GetOutput()
        locator=vtk.vtkStaticPointLocator(); locator.SetDataSet(grid); locator.BuildLocator()
        with (folder/'surface_flow.csv').open() as f: wall=list(csv.DictReader(f))
        points=np.array([[float(a['x']),float(a['y']),0.] for a in wall]); ids=[locator.FindClosestPoint(p) for p in points]
        maxdist=max(np.linalg.norm(np.array(grid.GetPoint(i))-p) for i,p in zip(ids,points))
        if maxdist>1e-7: raise ValueError('Surface coordinate to volume-field mapping failed')
        pdata=grid.GetPointData(); cp=vtk_to_numpy(pdata.GetArray('Pressure_Coefficient'))
        info={'case':row['case'],'points':grid.GetNumberOfPoints(),'cells':grid.GetNumberOfCells(),'wall_points':len(ids),'mapping_error_m':float(maxdist)}
        columns=[points[:,0],points[:,1],cp[ids]]; headers=['x_m','y_m','Cp']
        if row['solver']=='INC_RANS':
            yp=vtk_to_numpy(pdata.GetArray('Y_Plus'))[ids]; cf=vtk_to_numpy(pdata.GetArray('Skin_Friction_Coefficient'))[ids]
            info.update(y_plus_max=float(yp.max()),y_plus_p95=float(np.percentile(yp,95)),wall_yplus_below1_fraction=float(np.mean(yp<1)))
            columns.extend([yp,cf[:,0],cf[:,1]]); headers.extend(['Y_plus','Cf_x','Cf_y'])
        table=np.column_stack(columns); np.savetxt(folder/'wall_quantities.csv',table,delimiter=',',header=','.join(headers),comments='')
        summaries.append(info); fields[row['case']]={'grid':grid,'wall':table}
    fine=next(r for r in result['results'] if r['case']=='rans_fine'); medium=next(r for r in result['results'] if r['case']=='rans_medium')
    cfl=zones(SOURCE/'n0012clcd_cfl3d_sa.dat')['default']; reference=cfl[np.isclose(cfl[:,0],10)][0]
    force_comparison={'CFL3D_SA_reference':{'CL':float(reference[1]),'CD':float(reference[2]),'Mach':.15,'Re':6e6,'grid':'897x257','source':'https://tmbwg.github.io/turbmodels/naca0012_val_sa.html'},
      'fine_relative_CL_error':abs(fine['CL']/reference[1]-1),'fine_relative_CD_error':abs(fine['CD']/reference[2]-1),
      'medium_to_fine_CL_relative_change':abs(fine['CL']/medium['CL']-1),'medium_to_fine_CD_relative_change':abs(fine['CD']/medium['CD']-1),
      'limitations':'Our INC_RANS SA-noft2 is incompressible on a coarser grid without the cited farfield point-vortex correction; this is representative agreement, not bit-identical replication.'}
    ladson=zones(SOURCE/'CLCD_Ladson_expdata.dat'); experiments={}
    for name,values in ladson.items():
        alpha=values[:,0]; order=np.argsort(alpha); values=values[order]
        cl=float(np.interp(10,values[:,0],values[:,1])); cd=float(np.interp(10,values[:,0],values[:,2]))
        experiments[name]={'CL_at_10_interpolated':cl,'CD_at_10_interpolated':cd,'relative_CL_difference':abs(fine['CL']/cl-1),'relative_CD_difference':abs(fine['CD']/cd-1)}
    wall=fields['rans_fine']['wall']; upper=wall[wall[:,1]>1e-7]; upper=upper[np.argsort(upper[:,0])]
    gregory=next(v for k,v in zones(SOURCE/'CP_Gregory_expdata.dat').items() if k=='alpha=10')
    mask=(gregory[:,0]>=.005)&(gregory[:,0]<=.95); sample=gregory[mask]
    cp_rmse=float(np.sqrt(np.mean((np.interp(sample[:,0],upper[:,0],upper[:,2])-sample[:,1])**2)))
    # Surface pressure and independent reference data.
    fig,ax=plt.subplots(figsize=(8.5,5))
    colors={'rans_coarse':'#a7afb6','rans_medium':'#c58021','rans_fine':'#087c86'}
    for name,color in colors.items():
        w=fields[name]['wall']; u=w[w[:,1]>1e-7]; u=u[np.argsort(u[:,0])]
        ax.plot(u[:,0],u[:,2],color=color,label=name)
    ax.scatter(gregory[:,0],gregory[:,1],s=22,facecolor='white',edgecolor='#1d344b',label='Gregory upper Cp, Re=2.88M (digitized)')
    ax.set(xlabel='x/c',ylabel='Cp',title='NACA0012, 10°: native SU2 INC_RANS / experimental surface pressure'); ax.invert_yaxis(); ax.grid(alpha=.2); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT/'plots/cfd_cp_validation.png',dpi=160); plt.close(fig)
    # Actual volume cells: preserve their connectivity around the airfoil hole.
    g=fields['rans_fine']['grid']; geom=vtk.vtkGeometryFilter(); geom.SetInputData(g); geom.Update()
    tri=vtk.vtkTriangleFilter(); tri.SetInputConnection(geom.GetOutputPort()); tri.Update(); poly=tri.GetOutput()
    pts=vtk_to_numpy(poly.GetPoints().GetData()); connectivity=vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1,4)[:,1:]
    cp=vtk_to_numpy(poly.GetPointData().GetArray('Pressure_Coefficient')); centers=pts[connectivity].mean(axis=1)
    near=(centers[:,0]>-.3)&(centers[:,0]<1.3)&(np.abs(centers[:,1])<.4); connectivity=connectivity[near]
    triangulation=mtri.Triangulation(pts[:,0],pts[:,1],triangles=connectivity)
    # Native Gmsh post-processing file so the computed field can be opened in an installed app.
    pos=Path(fine['folder'])/'pressure_nearfield.pos'
    with pos.open('w',encoding='ascii') as stream:
        stream.write('View "SU2 INC_RANS pressure coefficient" {\n')
        for ids in connectivity:
            xyz=pts[ids].reshape(-1); vals=cp[ids]
            stream.write('ST('+','.join(f'{x:.10g}' for x in xyz)+'){'+','.join(f'{x:.10g}' for x in vals)+'};\n')
        stream.write('};\n')
    fig,axs=plt.subplots(2,1,figsize=(10,7.5),sharex=True)
    im=axs[0].tricontourf(triangulation,cp,levels=np.linspace(-3.5,1.2,41),cmap='coolwarm',extend='both'); fig.colorbar(im,ax=axs[0],label='Cp from native solution')
    axs[1].triplot(triangulation,color='#395166',linewidth=.28)
    for ax in axs: ax.set(xlim=(-.25,1.25),ylim=(-.3,.3),aspect='equal',ylabel='y/c')
    axs[0].set_title('Native volume-mesh CFD pressure field'); axs[1].set(xlabel='x/c',title='Actual near-body CFD cells, no image model')
    fig.tight_layout(); fig.savefig(OUT/'plots/cfd_pressure_and_mesh.png',dpi=160); plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4.5))
    for row in result['results']:
        if row['solver']!='INC_RANS': continue
        p=Path(row['folder'])/'history_clean.csv'; a=np.genfromtxt(p,delimiter=',',names=True,deletechars='')
        x=a['Inner_Iter'] if 'Inner_Iter' in a.dtype.names else np.arange(len(a))
        axs[0].plot(x,a['CL'],label=row['case']); axs[1].plot(x,a['CD'],label=row['case'])
    axs[0].axhline(reference[1],color='black',ls='--',lw=1,label='CFL3D reference'); axs[1].axhline(reference[2],color='black',ls='--',lw=1)
    for ax,label in zip(axs,['CL','CD']): ax.set(xlabel='Iteration',ylabel=label); ax.grid(alpha=.2); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(OUT/'plots/cfd_force_convergence.png',dpi=160); plt.close(fig)
    assessment={'timestamp':datetime.now(timezone.utc).isoformat(),'volume_surface_metrics':summaries,'force_comparison':force_comparison,
       'Ladson_tripped_Re6M_M015_interpolated':experiments,'Gregory_upper_Cp_RMSE_0p005_to_0p95':cp_rmse,
       'Gregory_limit':'Different Reynolds number 2.88M; digitized upper-surface data; indicative Cp check only',
       'fine_wall_resolution_passed':next(s for s in summaries if s['case']=='rans_fine')['y_plus_max']<2,
       'strict_max_yplus1_passed':next(s for s in summaries if s['case']=='rans_fine')['y_plus_max']<1,
       'wall_screen_note':'max y+ <2 is a provisional screen; stricter max y+ <1 target is evaluated separately',
       'gmsh_pressure_view':str(pos),'gmsh_view_triangles':len(connectivity),
       'grid_acceptance_passed':force_comparison['medium_to_fine_CL_relative_change']<.03 and force_comparison['medium_to_fine_CD_relative_change']<.1,
       'grid_thresholds':{'CL':.03,'CD':.1},'note':'Failure is retained: do not call a mesh-independent airfoil service ready on this evidence alone.'}
    import gmsh
    gmsh.initialize()
    try:
        gmsh.open(str(pos)); tags=gmsh.view.getTags()
        views=[{'tag':int(t),'types':gmsh.view.getListData(t)[0],
                'elements':[int(n) for n in gmsh.view.getListData(t)[1]]} for t in tags]
        assessment['gmsh_readback']={'passed':len(views)==1 and views[0]['elements']==[len(connectivity)],
                                    'views':views,'version':gmsh.__version__}
    finally: gmsh.finalize()
    save(OUT/'reports/cfd_reference_comparison.json',assessment)
    # Show the actual wing/rib CAD with a transparent aerodynamic envelope.
    import cadquery as cq
    dest=ROOT/'work/geometry/views'; dest.mkdir(exist_ok=True)
    renderer=vtk.vtkRenderer(); renderer.SetBackground(.97,.98,.99)
    for i,p in enumerate([OUT/'cad/parametric_wing/envelope.step']+sorted((OUT/'cad/parametric_wing').glob('rib_*.step'))):
        shape=cq.importers.importStep(str(p)).val(); stl=dest/(p.stem+'.stl'); cq.exporters.export(shape,str(stl))
        reader=vtk.vtkSTLReader(); reader.SetFileName(str(stl)); reader.Update(); mapper=vtk.vtkPolyDataMapper(); mapper.SetInputConnection(reader.GetOutputPort())
        actor=vtk.vtkActor(); actor.SetMapper(mapper); actor.GetProperty().SetColor(*((.45,.66,.74) if i==0 else (.10,.42,.57))); actor.GetProperty().SetOpacity(.20 if i==0 else 1); renderer.AddActor(actor)
    window=vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(1500,800); window.AddRenderer(renderer)
    camera=renderer.GetActiveCamera(); camera.SetPosition(1600,-2400,1800); camera.SetFocalPoint(180,0,25); camera.SetViewUp(0,0,1); camera.ParallelProjectionOn(); renderer.ResetCamera(); window.Render()
    capture=vtk.vtkWindowToImageFilter(); capture.SetInput(window); capture.ReadFrontBufferOff(); capture.Update(); writer=vtk.vtkPNGWriter(); writer.SetFileName(str(OUT/'plots/parametric_wing_cad.png')); writer.SetInputConnection(capture.GetOutputPort()); writer.Write(); window.Finalize()
    print(json.dumps(assessment,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__': main()
