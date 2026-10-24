"""Native Elmer VTU fields -> readable Gmsh view and scientific plots."""
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import gmsh
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.ticker import NullFormatter
def main():
    report=OUT/'reports/elmer_cfd_qualification.json'; result=json.loads(report.read_text()); fine=result['results'][-1]
    fig,axes=plt.subplots(1,2,figsize=(11,4.5)); yy=np.linspace(0,1,200)
    axes[0].plot(6*yy*(1-yy),yy,'k--',label='Exact fully developed solution')
    for row in result['results']:
        r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(row['VTU']);r.Update();g=r.GetOutput()
        pts=vtk_to_numpy(g.GetPoints().GetData());v=vtk_to_numpy(g.GetPointData().GetArray('velocity'))
        mask=np.isclose(pts[:,0],2);y=pts[mask,1];idx=np.argsort(y)
        axes[0].plot(v[mask,0][idx],y[idx],'o-',ms=3,label='n='+str(row['mesh_n']))
    axes[0].set(xlabel='Axial velocity [m/s]',ylabel='y [m]',title='Native Elmer Navier-Stokes channel')
    axes[1].loglog([r['fluid_cells'] for r in result['results']],[r['velocity_relative_L2_error'] for r in result['results']],'o-',label='Velocity error')
    axes[1].loglog([r['fluid_cells'] for r in result['results']],[r['pressure_relative_L2_error'] for r in result['results']],'s-',label='Pressure error')
    axes[1].set_xticks([200,800,3200],labels=['200','800','3200']);axes[1].xaxis.set_minor_formatter(NullFormatter())
    axes[1].set(xlabel='Fluid cells',ylabel='Relative error',title='Independent exact-solution comparison')
    for ax in axes:ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'plots/elmer_cfd_verification.png',dpi=160);plt.close(fig)
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(fine['VTU']);reader.Update();g=reader.GetOutput()
    pts=vtk_to_numpy(g.GetPoints().GetData());triangles=[]
    for i in range(g.GetNumberOfCells()):
        cell=g.GetCell(i)
        if cell.GetCellDimension()==2 and cell.GetNumberOfPoints()==3:triangles.append([cell.GetPointId(j) for j in range(3)])
    triangles=np.asarray(triangles); pressure=vtk_to_numpy(g.GetPointData().GetArray('pressure'))
    velocity=vtk_to_numpy(g.GetPointData().GetArray('velocity'))[:,0]
    tri=mtri.Triangulation(pts[:,0],pts[:,1],triangles=triangles)
    fig,axes=plt.subplots(2,1,figsize=(11,6.2))
    for ax,values,label in zip(axes,[velocity,pressure],['Axial velocity [m/s]','Pressure [Pa]']):
        im=ax.tricontourf(tri,values,levels=24,cmap='viridis');fig.colorbar(im,ax=ax,label=label)
        ax.triplot(tri,color='white',lw=.12,alpha=.25);ax.set(xlabel='x [m]',ylabel='y [m]',aspect='equal')
    fig.suptitle('Actual native Elmer Navier-Stokes fields, Re_H=100');fig.tight_layout();fig.savefig(OUT/'plots/elmer_cfd_fields.png',dpi=160);plt.close(fig)
    dest=Path(fine['folder'])/'pressure.pos'
    with dest.open('w',encoding='ascii') as f:
        f.write('View "Elmer pressure [Pa]" {\n')
        for ids in triangles:
            f.write('ST('+','.join(f'{v:.10g}' for v in pts[ids].reshape(-1))+'){'+','.join(f'{v:.10g}' for v in pressure[ids])+'};\n')
        f.write('};\n')
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(dest));tags=gmsh.view.getTags();counts=gmsh.view.getListData(tags[0])[1]
        accepted=len(tags)==1 and counts[0]==fine['fluid_cells']
    finally:gmsh.finalize()
    result['field_view']={'gmsh_pressure':str(dest),'readback_passed':bool(accepted),'triangles':len(triangles),'plot':'outputs/plots/elmer_cfd_fields.png'}
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['field_view'])
if __name__=='__main__':main()
