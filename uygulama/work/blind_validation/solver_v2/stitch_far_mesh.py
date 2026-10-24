"""Keep the 200c near mesh exactly, joining the independently generated 400c outer annulus."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,gmsh
from audit_mesh_family import parse_mesh,OUT,ROOT
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stitch():
    base=OUT/'simulations/v2_r2_medium';far=OUT/'simulations/v2_r2_medium_far'
    assert not (far/'run_status.json').exists()
    sourcefar=far/('mesh_unstitched.su2' if (far/'mesh_unstitched.su2').exists() else 'mesh.su2')
    bp,bc,bm=parse_mesh(base/'mesh.su2');fp,fc,fm=parse_mesh(sourcefar)
    inner=[c for c in bc if np.max(np.abs(bp[c]))<=20.+1e-10]
    outer=[c for c in fc if np.max(np.abs(fp[c]))>20.+1e-10]
    used=np.unique(np.concatenate(inner));points=bp[used].tolist();bmap={int(a):i for i,a in enumerate(used)}
    interfaces={tuple(np.round(bp[a],12)):bmap[int(a)] for a in used if abs(np.max(np.abs(bp[a]))-20.)<1e-10}
    fmap={};matched=0
    for a in np.unique(np.concatenate(outer)):
        xy=fp[a];key=tuple(np.round(xy,12))
        if abs(np.max(np.abs(xy))-20.)<1e-10:
            assert key in interfaces;fmap[int(a)]=interfaces[key];matched+=1
        else:fmap[int(a)]=len(points);points.append(xy.tolist())
    assert matched==len(interfaces)
    cells=[np.array([bmap[int(v)] for v in c]) for c in inner]+[np.array([fmap[int(v)] for v in c]) for c in outer]
    markers={'AIRFOIL':np.array([[bmap[int(v)] for v in e] for e in bm['AIRFOIL']]),'FARFIELD':np.array([[fmap[int(v)] for v in e] for e in fm['FARFIELD']])}
    old_sha=sha(sourcefar)
    if not (far/'mesh_unstitched.su2').exists():shutil.copy2(far/'mesh.su2',far/'mesh_unstitched.su2');shutil.copy2(far/'mesh_audit.json',far/'mesh_unstitched_audit.json')
    p=np.array(points)
    with (far/'mesh.su2').open('w') as f:
        f.write('NDIME= 2\nNELEM= '+str(len(cells))+'\n')
        for i,c in enumerate(cells):f.write(str(5 if len(c)==3 else 9)+' '+' '.join(str(int(v)) for v in c)+' '+str(i)+'\n')
        f.write('NPOIN= '+str(len(p))+'\n')
        for i,xy in enumerate(p):f.write(f'{xy[0]:.17g} {xy[1]:.17g} {i}\n')
        f.write('NMARK= 2\n')
        for name,es in markers.items():
            f.write('MARKER_TAG= '+name+'\nMARKER_ELEMS= '+str(len(es))+'\n')
            for e in es:f.write(f'3 {e[0]} {e[1]}\n')
    gmsh.initialize();gmsh.model.add('stitched_fluid_mesh');entity=gmsh.model.addDiscreteEntity(2,1)
    gmsh.model.mesh.addNodes(2,entity,list(range(1,len(p)+1)),np.c_[p,np.zeros(len(p))].ravel().tolist())
    for nv,typ in [(3,2),(4,3)]:
        selected=[(i,c) for i,c in enumerate(cells) if len(c)==nv]
        gmsh.model.mesh.addElementsByType(entity,typ,[i+1 for i,c in selected],np.concatenate([c+1 for i,c in selected]).tolist())
    ts,es,ns=gmsh.model.mesh.getElements(2);et=np.concatenate(es).astype(np.uint64)
    jac=gmsh.model.mesh.getElementQualities(et.tolist(),'minSJ');sicn=gmsh.model.mesh.getElementQualities(et.tolist(),'minSICN')
    gmsh.write(str(far/'mesh_stitched.msh'));gmsh.finalize()
    report=json.loads((far/'mesh_audit.json').read_text());report.update({'nodes':len(p),'cells':len(cells),'min_scaled_jacobian':float(min(jac)),'min_inverse_condition':float(min(sicn)),'element_counts':{'Triangle 3':sum(len(c)==3 for c in cells),'Quadrilateral 4':sum(len(c)==4 for c in cells)},'construction':'200c medium mesh cells entirely inside the common20c interface plus400c outer ring cells. Exact matching100 interface coordinates merged; no remeshing or geometry motion.'})
    (far/'mesh_audit.json').write_text(json.dumps(report,indent=2))
    np.savez_compressed(far/'mesh_arrays_stitched.npz',points=p,cells=np.array(cells,dtype=object))
    provenance={'base200_mesh':str((base/'mesh.su2').relative_to(ROOT)),'base200_sha256':sha(base/'mesh.su2'),'source400_unstitched_sha256':old_sha,'selected400_mesh_sha256':sha(far/'mesh.su2'),'inner200_cells_preserved_exactly':len(inner),'outer400_cells':len(outer),'exact_shared_interface_nodes':matched,'source_coordinates_moved':False,'geometry_curve_hash_unchanged':report['curve_definition_sha256'],'reason':'Gmsh global generation produced small internal triangulation differences despite same sizing and conformal20c interface; joining exact inner cells makes the farfield comparison independent of those interior differences. Both original generated far mesh and selected stitched solver mesh retained.'}
    (far/'mesh_stitch_provenance.json').write_text(json.dumps(provenance,indent=2));print(json.dumps(provenance,indent=2))
if __name__=='__main__':stitch()
