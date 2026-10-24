"""Prolong an OWN native checkpoint onto a new grid as an initial guess only.

Invalid probes are explicitly counted, never treated as zero. Only tiny
geometric wall discrepancies may use nearest-source-node seed values. Every
seed must subsequently converge under the native equations and original gates.
"""
from pathlib import Path
import json,sys,hashlib,struct
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy,numpy_to_vtk
from scipy.spatial import cKDTree

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readpoints(path):
    lines=path.read_text().splitlines();wall=set()
    for i,line in enumerate(lines):
        if line.startswith('NPOIN'):
            n=int(line.split('=')[1].split()[0]);p=np.array([[float(v) for v in row.split()[:2]] for row in lines[i+1:i+1+n]])
        if line.startswith('MARKER_TAG') and line.split('=')[1].strip()=='AIRFOIL':
            n=int(lines[i+1].split('=')[1]);wall=set(v for row in lines[i+2:i+2+n] for v in map(int,row.split()[1:3]))
    return p,np.array(sorted(wall),int)

def run(source_name,target_name):
    src=OUT/'simulations'/source_name;dst=OUT/'simulations'/target_name
    assert not (dst/'seed.dat').exists() and not (dst/'process.json').exists()
    selection=json.loads((src/'checkpoint_selection.json').read_text())
    restart=ROOT/selection['restart'];volume=ROOT/selection['volume']
    b=restart.read_bytes();header=list(struct.unpack('<5i',b[:20]));nfields,npoints=header[1:3]
    assert nfields==7 and len(b)==20+33*nfields+8*nfields*npoints
    raw=np.frombuffer(b,dtype='<f8',offset=20+33*nfields).reshape(npoints,nfields)
    names=[b[20+33*k:20+33*(k+1)].split(b'\0')[0].decode() for k in range(nfields)]
    assert names==['x','y','Density','Momentum_x','Momentum_y','Energy','Nu_Tilde']
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(volume));reader.Update();grid=reader.GetOutput()
    vtkp=vtk_to_numpy(grid.GetPoints().GetData())[:,:2]
    assert len(vtkp)==npoints
    coordinate_difference=np.max(abs(vtkp-raw[:,:2]))
    assert np.allclose(vtkp,raw[:,:2],rtol=2e-7,atol=2e-7)
    # Native restart retains double precision; replace Float32 output geometry
    # to avoid artificial collapse near sub-micron viscous layers.
    points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.c_[raw[:,:2],np.zeros(npoints)],deep=True));grid.SetPoints(points)
    for k in range(2,nfields):
        array=numpy_to_vtk(raw[:,k].copy(),deep=True);array.SetName('seed_'+names[k]);grid.GetPointData().AddArray(array)
    target,wall=readpoints(dst/'mesh.su2');points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.c_[target,np.zeros(len(target))],deep=True));poly=vtk.vtkPolyData();poly.SetPoints(points)
    probe=vtk.vtkProbeFilter();probe.SetInputData(poly);probe.SetSourceData(grid);probe.ComputeToleranceOff();probe.SetTolerance(1e-14);probe.Update()
    result=probe.GetOutput();mask=vtk_to_numpy(result.GetPointData().GetArray('vtkValidPointMask')).astype(bool)
    values=np.empty((len(target),7));values[:,:2]=target
    for k in range(2,nfields):values[:,k]=vtk_to_numpy(result.GetPointData().GetArray('seed_'+names[k]))
    invalid=np.flatnonzero(~mask);distances=np.empty(0);near=np.empty(0,dtype=int)
    if len(invalid):
        distances,near=cKDTree(raw[:,:2]).query(target[invalid]);assert distances.max()<.003,distances.max()
        # Never retain VTK zero placeholders as physical values. This fallback
        # populates only an initial guess, with all indices/coordinates logged.
        values[invalid,2:]=raw[near,2:]
    values[wall,3:5]=0.;values[wall,6]=0.
    pressure=.4*(values[:,5]-.5*(values[:,3]**2+values[:,4]**2)/values[:,2])
    assert np.isfinite(values).all() and np.all(values[:,2]>0) and np.all(pressure>0) and np.all(values[:,6]>=0)
    header[2]=len(target)
    data=struct.pack('<5i',*header)+b[20:20+33*nfields]+np.asarray(values,dtype='<f8').tobytes()
    (dst/'seed.dat').write_bytes(data)
    detail={'purpose':'Initial guess from own native CFD only; not a prediction or accepted final field.',
      'source_case':source_name,'source_iteration':selection['iteration'],'source_restart':str(restart.relative_to(ROOT)),'source_restart_sha256':sha(restart),'source_volume_sha256':sha(volume),
      'target_mesh_sha256':sha(dst/'mesh.su2'),'seed_sha256':sha(dst/'seed.dat'),'fields':names,'target_nodes':len(target),
      'source_restart_vs_vtu_coordinate_max_abs_m':float(coordinate_difference),'geometry_for_probe':'Double-precision coordinates from native restart after confirming same VTK order; no source/output fields altered.',
      'valid_probes':int(mask.sum()),'invalid_probes':len(invalid),'invalid_node_ids':invalid.tolist(),'invalid_coordinates_m':target[invalid].tolist(),'nearest_seed_distances_m':distances.tolist(),
      'fallback':'Nearest source node for initial guess only, with all invalid probes retained in log. Native wall momentum and nu_tilde set zero.',
      'seed_minimum_density':float(values[:,2].min()),'seed_minimum_pressure':float(pressure.min()),'physical_scope':'Same conditions, SA-noft2, Reynolds/chord and nondimensionalization; native solver must recompute the final field.'}
    (dst/'seed_interpolation.json').write_text(json.dumps(detail,indent=2))
    print(json.dumps({k:v for k,v in detail.items() if k not in ['invalid_node_ids','invalid_coordinates_m','nearest_seed_distances_m']},indent=2))

if __name__=='__main__':run(*sys.argv[1:3])
