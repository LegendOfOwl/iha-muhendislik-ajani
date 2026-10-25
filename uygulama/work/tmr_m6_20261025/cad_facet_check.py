"""Measure facet interiors/edge midpoints as well as prior wall nodes against source CAD."""
from common import ROOT,BASE,CASE,PROJECT,sha,save,now
from mesh_audit import load_mesh,stats
import cadquery as cq
import numpy as np
import time

start=time.monotonic();source=BASE/'sources/AileM6_with_sharp_TE.stp'
shape=cq.importers.importStep(str(source)).val().scale(1/810.491484086)
results=[]
for level in [3,2,1]:
    mesh=CASE/f'mesh_family_budget_v3/wing_strct.{level}.su2';xyz,cells,markers=load_mesh(mesh)
    points=[];faces=[];kinds=[]
    for i,ids in enumerate(markers['WING3D']):
        p=xyz[ids];points.append(p.mean(0));faces.append(i);kinds.append(0)
        for j in range(len(ids)):
            points.append((p[j]+p[(j+1)%len(ids)])/2);faces.append(i);kinds.append(1)
    points=np.asarray(points);unique,inverse=np.unique(points,axis=0,return_inverse=True)
    distances=[]
    for i,p in enumerate(unique):
        distances.append(shape.distance(cq.Vertex.makeVertex(*[float(v) for v in p])))
        if i and i%1000==0:print('CAD facet check L',level,i,'of',len(unique),flush=True)
        if time.monotonic()-start>240:raise TimeoutError('Facet CAD audit budget240s exceeded; do not assign missing distances')
    expanded=np.asarray(distances)[inverse]
    target=PROJECT/f'data/tmr_sharp_20261025_v1/source_CAD_facet_L{level}.csv'
    np.savetxt(target,np.column_stack([faces,kinds,points,expanded]),delimiter=',',
               header='wing_face,kind_0center_1edge_midpoint,x,y,z,CAD_distance_over_root_chord',comments='')
    kinds=np.asarray(kinds)
    results.append({'level':level,'mesh_sha256':sha(mesh),'unique_samples':len(unique),'total_face_samples':len(points),
                    'facet_center_distance':stats(expanded[kinds==0]),'edge_midpoint_distance':stats(expanded[kinds==1]),
                    'all_sample_distance':stats(expanded),'csv_sha256':sha(target)})
    print('CAD facet level',level,results[-1]['all_sample_distance'],flush=True)
save(PROJECT/'reports/tmr_source_CAD_facets_20261025.json',{'created_utc':now(),'source_STEP_sha256':sha(source),
    'normalization_root_chord_mm':810.491484086,'levels':results,'seconds':time.monotonic()-start,
    'scope':'Additional face centers and edge midpoints; finite sampling, not an exact Hausdorff bound or after-the-fact geometry acceptance.'})
