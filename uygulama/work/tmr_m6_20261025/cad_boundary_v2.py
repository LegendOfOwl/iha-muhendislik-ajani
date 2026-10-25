"""Surface-distance audit: a solid's interior distance0 is not a surface match."""
from common import ROOT,BASE,CASE,PROJECT,sha,save,now
from mesh_audit import load_mesh,stats
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
import numpy as np
import time

start=time.monotonic()
cube=cq.Solid.makeBox(1,1,1);center=cq.Vertex.makeVertex(.5,.5,.5)
cube_surface=cq.Compound.makeCompound(cube.Faces())
old_unit=cube.distance(center);correct_unit=cube_surface.distance(center)
assert abs(correct_unit-.5)<1e-12 and old_unit==0
source=BASE/'sources/AileM6_with_sharp_TE.stp'
original=cq.importers.importStep(str(source)).val();scaled=original.scale(1/810.491484086)
boundary=cq.Compound.makeCompound(scaled.Faces())
assert len(original.Solids())>0,'If no solid is present, re-evaluate whether the old distance suffered interior classification'
operator=BRepExtrema_DistShapeShape();operator.LoadS1(boundary.wrapped)
cache={};results=[]
print('Analytic control: solid interior',old_unit,'vs true boundary',correct_unit,'; source solids',len(original.Solids()),flush=True)
for level in [3,2,1]:
    mesh=CASE/f'mesh_family_budget_v3/wing_strct.{level}.su2';xyz,cells,markers=load_mesh(mesh)
    del cells
    wall=np.unique(np.concatenate(markers['WING3D']));points=list(xyz[wall]);ids=list(wall);kinds=[-1]*len(wall)
    for faceid,nodes in enumerate(markers['WING3D']):
        p=xyz[nodes];points.append(p.mean(0));ids.append(faceid);kinds.append(0)
        for j in range(len(nodes)):
            points.append((p[j]+p[(j+1)%len(nodes)])/2);ids.append(faceid);kinds.append(1)
    points=np.asarray(points);unique,inverse=np.unique(points,axis=0,return_inverse=True);distances=[]
    for i,p in enumerate(unique):
        key=tuple(p)
        if key not in cache:
            operator.LoadS2(cq.Vertex.makeVertex(*[float(v) for v in p]).wrapped);operator.Perform();assert operator.IsDone()
            cache[key]=operator.Value()
        distances.append(cache[key])
        if i and i%1500==0:print('Boundary CAD check L',level,i,'of',len(unique),flush=True)
        if time.monotonic()-start>360:raise TimeoutError('CAD boundary audit360s exceeded; no missing distances assigned')
    expanded=np.asarray(distances)[inverse];kinds=np.asarray(kinds)
    target=PROJECT/f'data/tmr_sharp_20261025_v1/source_CAD_boundary_samples_L{level}_v2.csv'
    np.savetxt(target,np.column_stack([ids,kinds,points,expanded]),delimiter=',',
        header='node_or_face_id,kind_minus1vertex_0center_1edge_midpoint,x,y,z,boundary_distance_over_root_chord',comments='')
    results.append({'level':level,'mesh_sha256':sha(mesh),'unique_samples':len(unique),'total_samples':len(points),
        'node_distance':stats(expanded[kinds==-1]),'facet_center_distance':stats(expanded[kinds==0]),
        'edge_midpoint_distance':stats(expanded[kinds==1]),'all_samples':stats(expanded),'csv_sha256':sha(target)})
    print('True CAD boundary L',level,results[-1]['all_samples'],flush=True)
result={'version':2,'created_utc':now(),'source_STEP_sha256':sha(source),'source_CAD_solids':len(original.Solids()),
        'normalization_root_chord_mm':810.491484086,'levels':results,'seconds':time.monotonic()-start,
        'method':'Exact OCC distance to compound of source boundary faces only; reuse distance operator; no interior-of-solid zero classification.',
        'analytic_counterexample':{'solid_interior_distance':old_unit,'boundary_distance':correct_unit,'expected_boundary_distance':.5},
        'superseded_records':['tmr_source_CAD_distances_20261025.json','tmr_source_CAD_facets_20261025.json'],
        'superseded_reason':'Distance to a solid can return0 for inside points; not suitable as an unsigned surface-equivalence distance.',
        'source_or_mesh_changed':False,'scope':'Finite surface sample distances; not an exact Hausdorff bound or a new after-result geometry acceptance.'}
save(PROJECT/'reports/tmr_source_CAD_boundary_v2_20261025.json',result)
