import json
from pathlib import Path
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
def render(grid,out,folder):
    geom=vtk.vtkGeometryFilter();geom.SetInputData(grid);tri=vtk.vtkTriangleFilter();tri.SetInputConnection(geom.GetOutputPort());tri.Update();poly=tri.GetOutput()
    pts=vtk_to_numpy(poly.GetPoints().GetData());cells=vtk_to_numpy(poly.GetPolys().GetConnectivityArray()).reshape(-1,3);cp=vtk_to_numpy(poly.GetPointData().GetArray('Pressure_Coefficient'));yp=vtk_to_numpy(poly.GetPointData().GetArray('Y_Plus'))
    p=pts[cells];normal=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);upper=(p[:,:,2].mean(axis=1)>0)&(abs(normal[:,2])>1e-12);uv=cells[upper]
    fig,axs=plt.subplots(1,2,figsize=(12,7))
    mesh=mtri.Triangulation(pts[:,0],pts[:,1],triangles=uv)
    for ax,v,label in [(axs[0],cp,'Cp, native 3D RANS'),(axs[1],yp,'Wall y+, native 3D RANS')]:
        im=ax.tripcolor(mesh,v,shading='gouraud',cmap='coolwarm' if label.startswith('Cp') else 'viridis');fig.colorbar(im,ax=ax,label=label);ax.set(xlabel='x (m)',ylabel='y (m)',aspect='equal',title=label)
    fig.tight_layout();fig.savefig(out/'plots/m6_surface_fields.png',dpi=160);plt.close(fig)
    pos=folder/'wing_pressure.pos'
    with pos.open('w',encoding='ascii') as f:
        f.write('View "ONERA M6 - native RANS Cp" {\n')
        for ids in cells:f.write('ST('+','.join(f'{v:.10g}' for v in pts[ids].reshape(-1))+'){'+','.join(f'{v:.10g}' for v in cp[ids])+'};\n')
        f.write('};\n')
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(pos));tags=gmsh.view.getTags();ok=len(tags)==1 and list(gmsh.view.getListData(tags[0])[1])==[len(cells)]
    finally:gmsh.finalize()
    if not ok:raise ValueError('Gmsh field readback failed')
    return {'path':str(pos),'triangles':len(cells),'native_field_finite':bool(np.all(np.isfinite(cp)) and np.all(np.isfinite(yp))),'gmsh_readback_passed':ok,'note':'Triangles are for viewing original native surface fields; the CFD volume mesh was not changed.'}
