"""Independent 3D wall force integral with fluid-neighbour normal orientation."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import vtk_to_numpy
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-e9319baef1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def settings(path):
    d={}
    for s in path.read_text().splitlines():
        s=s.split('%',1)[0].strip()
        if '=' in s:k,v=s.split('=',1);d[k.strip()]=v.strip()
    return d
def integrate(mesh,surface,config,expected):
    with mesh.open() as f:
        def line():
            while True:
                s=f.readline()
                if not s:raise EOFError('Mesh ended early')
                if s.strip() and not s.startswith('%'):return s
        assert line().strip()=='NDIME= 3'
        count=int(line().split('=')[1]);cells=[]
        for _ in range(count):
            a=[int(v) for v in f.readline().split()];assert a[0] in [10,13]
            cells.append(a[1:1+({10:4,13:6}[a[0]])])
        n=int(line().split('=')[1].split()[0]);pts=np.array([[float(v) for v in f.readline().split()[:3]] for _ in range(n)])
        markers={}
        for _ in range(int(line().split('=')[1])):
            tag=line().split('=')[1].strip();faces=[]
            for _ in range(int(line().split('=')[1])):
                a=[int(v) for v in f.readline().split()];faces.append(a[1:1+({5:3,9:4}[a[0]])])
            markers[tag]=faces
    faces=markers['WING'];keys={tuple(sorted(a)):i for i,a in enumerate(faces)};adjacent={};multiplicity={}
    tet=[(0,1,2),(0,1,3),(0,2,3),(1,2,3)]
    prism=[(0,1,2),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
    for ids in cells:
        for local in (tet if len(ids)==4 else prism):
            key=tuple(sorted(ids[i] for i in local))
            if key in keys:
                k=keys[key];adjacent[k]=np.mean(pts[ids],axis=0);multiplicity[k]=multiplicity.get(k,0)+1
    assert len(adjacent)==len(faces) and all(n==1 for n in multiplicity.values()),'Not exactly one fluid neighbour per wall face'
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(surface));reader.Update();g=reader.GetOutput()
    xy=vtk_to_numpy(g.GetPoints().GetData());cp=vtk_to_numpy(g.GetPointData().GetArray('Pressure_Coefficient'))
    cf=vtk_to_numpy(g.GetPointData().GetArray('Skin_Friction_Coefficient'));assert cf.shape==(len(xy),3)
    wallids=np.unique(np.concatenate(faces));distance,j=cKDTree(xy).query(pts[wallids]);assert distance.max()<2e-7
    lookup=dict(zip(wallids,j));d=settings(config);area=float(d['REF_AREA']);cref=float(d['REF_LENGTH'])
    origin=np.array([float(d['REF_ORIGIN_MOMENT_'+v]) for v in ['X','Y','Z']])
    fp=np.zeros(3);fv=np.zeros(3);mp=np.zeros(3);mv=np.zeros(3);area_total=0.;min_orientation=np.inf
    for k,ids in enumerate(faces):
        for tri in [ids[:3]]+([[ids[0],ids[2],ids[3]]] if len(ids)==4 else []):
            p=pts[tri];center=p.mean(0);av=np.cross(p[1]-p[0],p[2]-p[0])/2
            orient=float(np.dot(av,adjacent[k]-center));assert orient!=0
            if orient<0:av=-av
            min_orientation=min(min_orientation,abs(orient));a=np.linalg.norm(av);indices=[lookup[i] for i in tri]
            pressure=-cp[indices].mean()*av/area;viscous=cf[indices].mean(0)*a/area
            fp+=pressure;fv+=viscous;mp+=np.cross(center-origin,pressure)/cref;mv+=np.cross(center-origin,viscous)/cref;area_total+=a
    alpha=np.deg2rad(float(d['AOA']));drag=np.array([np.cos(alpha),0,np.sin(alpha)]);lift=np.array([-np.sin(alpha),0,np.cos(alpha)])
    total=fp+fv;cl=float(lift@total);cd=float(drag@total)
    return {'method':'Exact SU2 wall topology; each face oriented toward its sole adjacent fluid-cell centroid; triangle-mean Cp/vectorCf integration, without a force-sign fit',
            'mesh_sha256':sha(mesh),'surface_sha256':sha(surface),'wall_faces':len(faces),'sole_fluid_neighbour_verified':True,
            'wall_mapping_max_distance_m':float(distance.max()),'minimum_nonzero_orientation_product_m3':float(min_orientation),
            'wetted_surface_area_m2':float(area_total),'reference_area_m2':area,'reference_chord_m':cref,'moment_origin_m':origin.tolist(),
            'pressure_force_xyz':fp.tolist(),'viscous_force_xyz':fv.tolist(),'force_xyz':total.tolist(),
            'CL_pressure':float(lift@fp),'CL_viscous':float(lift@fv),'CD_pressure':float(drag@fp),'CD_viscous':float(drag@fv),
            'CL':cl,'CD':cd,'CL_native':expected['CL'],'CD_native':expected['CD'],
            'CL_relative_difference':float(abs(cl/expected['CL']-1)),'CD_relative_difference':float(abs(cd/expected['CD']-1)),
            'moment_pressure_xyz':mp.tolist(),'moment_viscous_xyz':mv.tolist(),'moment_total_xyz':(mp+mv).tolist(),
            'note':'Surface quadrature and Float32 field interpolation errors remain; no new after-result physical acceptance threshold.'}
def main(mode):
    if mode=='baseline':
        folder=OUT/'simulations/m6_bounded_cfl_20261019_123823';surface=folder/'surface_flow.vtu';output=OUT/'reports/m6_baseline_force_integral_20261024.json'
        with (folder/'history.csv').open() as f:rows=list(csv.DictReader(f))
        expected={k.strip().strip('"'):float(v) for k,v in rows[-1].items()}
    elif mode=='new':
        folder=OUT/'simulations/m6_jst_control_20261024_v2';a=json.loads((folder/'matched_checkpoint.json').read_text());expected=a
        surface=folder/f'surface_flow_{a["field_iteration"]:06d}.vtu';output=OUT/'reports/m6_jst_force_integral_20261024_v2.json'
    else:
        assert mode=='normal'
        folder=OUT/'simulations/m6_jst_wallnormal_20261024_v3';a=json.loads((folder/'matched_checkpoint.json').read_text());expected=a
        surface=folder/f'surface_flow_{a["field_iteration"]:06d}.vtu';output=OUT/'reports/m6_wallnormal_force_integral_20261024_v3.json'
    assert not output.exists();a=integrate(folder/'mesh.su2',surface,folder/'case.cfg',expected)
    output.write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
if __name__=='__main__':main(sys.argv[1])
