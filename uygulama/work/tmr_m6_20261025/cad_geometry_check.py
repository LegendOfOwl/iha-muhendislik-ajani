"""Compare downloaded source STEP with actual grid wall nodes; no CAD reconstruction."""
from common import ROOT,BASE,CASE,PROJECT,sha,save,now
from mesh_audit import load_mesh,stats
import cadquery as cq
import numpy as np
import time

start=time.monotonic()
source=BASE/'sources/AileM6_with_sharp_TE.stp'
original=cq.importers.importStep(str(source)).val()
box=original.BoundingBox()
root_chord_mm=810.491484086
shape=original.scale(1/root_chord_mm)
xyz,cells,markers=load_mesh(CASE/'mesh_family_budget_v3/wing_strct.1.su2')
wall=np.unique(np.concatenate(markers['WING3D']))
distances=[]
for i,node in enumerate(wall):
    p=xyz[node]
    distances.append(shape.distance(cq.Vertex.makeVertex(*[float(x) for x in p])))
    if i and i%400==0:print('Measured source-CAD distances',i,'of',len(wall),flush=True)
    if time.monotonic()-start>180:raise TimeoutError('CAD distance audit exceeds180s; no unmeasured values assigned')
data=np.column_stack([wall,xyz[wall],distances])
target=PROJECT/'data/tmr_sharp_20261025_v1/source_CAD_wall_distances.csv'
np.savetxt(target,data,delimiter=',',header='node,x_normalized,y_normalized,z_normalized,CAD_distance_over_root_chord',comments='')
result={'created_utc':now(),'source_STEP_sha256':sha(source),'source_STEP_unit':'mm per TMR page',
        'original_CAD_bounds_mm':{'xmin':box.xmin,'xmax':box.xmax,'ymin':box.ymin,'ymax':box.ymax,'zmin':box.zmin,'zmax':box.zmax},
        'normalization':'All source CAD coordinates divided by published sharp root chord810.491484086mm; grid root chord=1.',
        'source_geometry_redesigned':False,'actual_fine_wall_points_compared':len(wall),
        'distance_over_root_chord':stats(distances),'worst_node':int(wall[np.argmax(distances)]),'worst_location_normalized':xyz[wall[np.argmax(distances)]].tolist(),
        'csv_sha256':sha(target),'seconds':time.monotonic()-start,
        'geometry_equivalence_acceptance':'Not asserted: source generator curve and independent source CAD have a measured difference. No after-the-fact tolerance chosen.'}
save(PROJECT/'reports/tmr_source_CAD_distances_20261025.json',result)
print(result,flush=True)
