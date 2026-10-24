"""Native M6 surface fields, fixed colour scales and verified Gmsh views."""
from pathlib import Path
import os,json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-e9319baef1'
os.environ['MPLCONFIGDIR']=str(ROOT/'work/m6_followup/mpl_cache')
import numpy as np
import vtk,gmsh
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(kind):
    if kind=='main':case='m6_jst_control_20261024_v2';report='m6_jst_control_results_20261024_v2.json';label='JST on source grid'
    else:case='m6_jst_wallnormal_20261024_v3';report='m6_wallnormal_results_20261024_v3.json';label='JST with normal redistribution'
    a=json.loads((OUT/'reports'/report).read_text());iteration=a['matched']['field_iteration'];raw=OUT/'simulations'/case
    source=raw/f'surface_flow_{iteration:06d}.vtu';initial=sha(source)
    dest=OUT/'data'/case/'views_v2';assert not dest.exists();dest.mkdir()
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(source));r.Update();g=r.GetOutput()
    geo=vtk.vtkGeometryFilter();geo.SetInputData(g);geo.Update();tri=vtk.vtkTriangleFilter();tri.SetInputConnection(geo.GetOutputPort());tri.Update();p=tri.GetOutput()
    points=vtk_to_numpy(p.GetPoints().GetData());cells=vtk_to_numpy(p.GetPolys().GetConnectivityArray()).reshape(-1,3)
    fields={key:vtk_to_numpy(p.GetPointData().GetArray(key)) for key in ['Pressure_Coefficient','Y_Plus']};assert all(np.isfinite(v).all() for v in fields.values())
    pos=dest/'native_wing_fields.pos'
    with pos.open('w') as f:
        for key,values in fields.items():
            f.write(f'View "{label} | {key} | native field {iteration}" {{\n')
            for ids in cells:f.write('ST('+','.join(f'{v:.10g}' for v in points[ids].reshape(-1))+'){'+','.join(f'{v:.10g}' for v in values[ids])+'};\n')
            f.write('};\n')
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(pos));counts=[[int(n) for n in gmsh.view.getListData(t)[1]] for t in gmsh.view.getTags()]
        assert len(counts)==2 and all(c==[len(cells)] for c in counts)
    finally:gmsh.finalize()
    native=ROOT/'tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/gmsh.exe'
    run=subprocess.run([str(native),str(pos),'-parse_and_exit','-nopopup','-v','3'],capture_output=True,text=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
    (dest/'native_gmsh.log').write_text(run.stdout+'\n'+run.stderr);assert run.returncode==0
    fig=plt.figure(figsize=(13,5.5))
    for i,(key,limits,title) in enumerate([('Pressure_Coefficient',(-1.5,1.),'Cp'),('Y_Plus',(0.,1.5),'y+; strict limit1')],1):
        ax=fig.add_subplot(1,2,i,projection='3d');norm=matplotlib.colors.Normalize(*limits);cm=plt.get_cmap('coolwarm' if i==1 else 'viridis')
        collection=Poly3DCollection(points[cells],facecolors=cm(norm(fields[key][cells].mean(1))),edgecolors='none');ax.add_collection3d(collection)
        ax.set(xlim=(points[:,0].min(),points[:,0].max()),ylim=(0,points[:,1].max()),zlim=(points[:,2].min(),points[:,2].max()),xlabel='x,m',ylabel='y,m',zlabel='z,m',title=title)
        ax.set_box_aspect(np.ptp(points,axis=0));ax.view_init(elev=35,azim=-115);ax.set_zticks([]);ax.set_zlabel('');fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cm),ax=ax,shrink=.65,pad=.1)
    fig.suptitle(f'Actual native SU2 surface | {label} | matched field {iteration}\nSource wing geometry; same colour scales; no general qualification')
    fig.tight_layout();plot=OUT/'plots'/f'm6_{kind}_native_fields_20261024_v2.png';fig.savefig(plot,dpi=155);plt.close(fig)
    yp=fields['Y_Plus'];imax=int(np.argmax(yp));eta=points[:,1]/1.1963
    regional={name:{'points':int(mask.sum()),'yplus_max':float(yp[mask].max()),'fraction_below1':float(np.mean(yp[mask]<1))} for name,mask in [('eta0to0p2',eta<=.2),('eta0p2to0p8',(eta>.2)&(eta<=.8)),('eta_gt0p8',eta>.8)]}
    result={'source_surface':str(source.relative_to(ROOT)),'surface_sha256':initial,'field_iteration':iteration,'points':len(points),'display_triangles':len(cells),
        'gmsh_SDK_version':gmsh.__version__,'gmsh_SDK_counts':counts,'native_gmsh_readback_exit':run.returncode,'native_gmsh_sha256':sha(native),
        'POS':str(pos.relative_to(ROOT)),'POS_sha256':sha(pos),'plot':str(plot.relative_to(ROOT)),
        'yplus_max_location_m':points[imax].tolist(),'yplus_max':float(yp[imax]),'spanwise_yplus':regional,'native_field_unchanged':sha(source)==initial,
        'scope':'Display and reading validation of actual fields; finite/maxy+ and iterative/experimental acceptance remain separate'}
    result['display_revision']='v2 hides overlapping z ticks at true thin-wing aspect; field values and geometry unchanged'
    output=OUT/'reports'/f'm6_field_view_{kind}_20261024_v2.json';assert not output.exists();output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main(sys.argv[1])
