"""Actual native checkpoint fields; fresh display folder, no frozen mutations."""
from pathlib import Path
import json,hashlib,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(ROOT/'work/mesh_research/mpl_cache')
import numpy as np
import vtk,gmsh
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(name,iteration):
    source=OUT/'simulations'/name/f'flow_{iteration:06d}.vtu'
    dest=OUT/'simulations/v3_field_views'/f'{name}_{iteration:06d}'
    assert not (dest/'field_view_checks.json').exists(),'Preserve completed old field views'
    dest.mkdir(parents=True,exist_ok=True)
    initial_sha=sha(source)
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(source));reader.Update();grid=reader.GetOutput()
    geometry=vtk.vtkGeometryFilter();geometry.SetInputData(grid);geometry.Update()
    tr=vtk.vtkTriangleFilter();tr.SetInputConnection(geometry.GetOutputPort());tr.Update();g=tr.GetOutput()
    points=vtk_to_numpy(g.GetPoints().GetData());triangles=vtk_to_numpy(g.GetPolys().GetData()).reshape(-1,4)[:,1:]
    centers=points[triangles].mean(1)
    keep=(centers[:,0]>-.2)&(centers[:,0]<1.3)&(centers[:,1]>-.25)&(centers[:,1]<.32)
    triangles=triangles[keep];mesh=Triangulation(points[:,0],points[:,1],triangles)
    fields={k:vtk_to_numpy(g.GetPointData().GetArray(k)) for k in ['Mach','Pressure_Coefficient','Residual_Density']}
    assert all(np.isfinite(v).all() for v in fields.values())
    pos=dest/'native_nearfield.pos'
    with pos.open('w',encoding='ascii') as f:
        for key,values in fields.items():
            f.write('View "'+key+' | native '+name+' | field '+str(iteration)+'" {\n')
            for ids in triangles:
                f.write('ST('+','.join(f'{v:.10g}' for v in points[ids].reshape(-1))+'){'+','.join(f'{v:.10g}' for v in values[ids])+'};\n')
            f.write('};\n')
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(pos));tags=gmsh.view.getTags()
        counts=[[int(n) for n in gmsh.view.getListData(t)[1]] for t in tags]
        assert len(tags)==3 and all(c==[len(triangles)] for c in counts)
    finally:gmsh.finalize()
    native=ROOT/'tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/gmsh.exe'
    run=subprocess.run([str(native),str(pos),'-parse_and_exit','-nopopup','-v','3'],capture_output=True,text=True,timeout=60)
    (dest/'native_gmsh_readback.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    assert run.returncode==0,(run.returncode,run.stderr)
    plotfields=[('Mach',fields['Mach'],(.2,1.5),'viridis'),('Cp',fields['Pressure_Coefficient'],(-1.5,1),'coolwarm'),
                ('log10 |native density residual|',np.log10(np.maximum(np.abs(fields['Residual_Density']),1e-16)),(-9,-3),'magma')]
    fig,axs=plt.subplots(3,1,figsize=(11,9),sharex=True)
    for ax,(label,values,limits,cmap) in zip(axs,plotfields):
        im=ax.tripcolor(mesh,values,shading='gouraud',cmap=cmap,vmin=limits[0],vmax=limits[1])
        ax.set(xlim=(-.1,1.2),ylim=(-.18,.24),aspect='equal',ylabel='y/c');fig.colorbar(im,ax=ax,label=label)
    axs[0].set_title(f'Native SU2 diagnostic; {name}; matched field {iteration}\nNot a converged/validated engineering prediction')
    axs[-1].set_xlabel('x/c');fig.tight_layout()
    plot=OUT/'plots'/f'{name}_{iteration:06d}_native_fields.png';fig.savefig(plot,dpi=155);plt.close(fig)
    report={'source_checkpoint':str(source.relative_to(ROOT)),'source_sha256':sha(source),'field_iteration':iteration,
            'source_native_cells':grid.GetNumberOfCells(),'display_triangles':len(triangles),
            'display_only_quad_split_and_nearfield_crop':True,'field_values':'Native SU2 arrays, no substitute CFD calculation',
            'gmsh_SDK_version':gmsh.__version__,'SDK_view_counts':counts,'native_gmsh_readback_exit_code':run.returncode,
            'native_executable_sha256':sha(native),'pos':str(pos.relative_to(ROOT)),'pos_sha256':sha(pos),
            'plot':str(plot.relative_to(ROOT)),'residual_plot_floor':'1e-16 for log display only; raw signed residual in POS',
            'native_solution_unchanged':sha(source)==initial_sha,'scope':'Checkpoint diagnostic; does not imply solver or physical acceptance'}
    (dest/'field_view_checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main(sys.argv[1],int(sys.argv[2]))
