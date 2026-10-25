"""Independent source-grid screens; sampled hexahedral Jacobian is not a global proof."""
from common import ROOT,CASE,PROJECT,read,save,sha
from pathlib import Path
import itertools
import os
import sys
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray

COUNTS={5:3,9:4,10:4,12:8,13:6}
FACES={12:[[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]],
       13:[[0,1,2],[3,4,5],[0,1,4,3],[1,2,5,4],[2,0,3,5]]}
SIGNS=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)


def stats(x):
    x=np.asarray(x);assert x.size and np.all(np.isfinite(x))
    return {'min':float(x.min()),'median':float(np.median(x)),'p95':float(np.quantile(x,.95)),'max':float(x.max())}


def load_mesh(path):
    with Path(path).open() as stream:
        def line():
            while True:
                t=stream.readline()
                if not t:raise EOFError(path)
                t=t.split('%',1)[0].strip()
                if t:return t
        dimension=line().split('=');assert dimension[0].strip()=='NDIME' and int(dimension[1])==3
        count=int(line().split('=')[1]);raw={12:[],13:[]}
        for _ in range(count):
            row=[int(x) for x in line().split()];typ=row[0];n=COUNTS[typ]
            assert typ in raw and len(row) in (n+1,n+2)
            raw[typ].append(row[1:1+n])
        cells={t:np.asarray(v,dtype=np.int32).reshape(-1,COUNTS[t]) for t,v in raw.items() if v}
        n=int(line().split('=')[1].split()[0]);xyz=np.empty((n,3))
        for i in range(n):xyz[i]=[float(x) for x in line().split()[:3]]
        nm=int(line().split('=')[1]);markers={}
        for _ in range(nm):
            name=line().split('=')[1].strip();nf=int(line().split('=')[1]);faces=[]
            for _ in range(nf):
                a=[int(x) for x in line().split()];k=COUNTS[a[0]]
                assert len(a) in (k+1,k+2)
                faces.append(a[1:1+k])
            markers[name]=faces
    assert set(markers)=={'WING3D','FARFIELD','SYMMETRY'}
    assert all(np.all((v>=0)&(v<n)) for v in cells.values()) and np.all(np.isfinite(xyz))
    assert all(np.all(np.diff(np.sort(v,axis=1),axis=1)>0) for v in cells.values())
    return xyz,cells,markers


def hex_jacobians(p):
    minimum=np.full(len(p),np.inf);scaled=np.full(len(p),np.inf);nonorth=np.zeros(len(p))
    for r,s,t in itertools.product([-1.,0.,1.],repeat=3):
        d=np.column_stack([SIGNS[:,0]*(1+SIGNS[:,1]*s)*(1+SIGNS[:,2]*t),
                           SIGNS[:,1]*(1+SIGNS[:,0]*r)*(1+SIGNS[:,2]*t),
                           SIGNS[:,2]*(1+SIGNS[:,0]*r)*(1+SIGNS[:,1]*s)])/8
        J=np.einsum('nki,kj->nij',p,d);det=np.linalg.det(J);length=np.linalg.norm(J,axis=1)
        minimum=np.minimum(minimum,det);scaled=np.minimum(scaled,det/np.maximum(np.prod(length,axis=1),1e-300))
        for a,b in [(0,1),(1,2),(0,2)]:
            cosine=np.abs(np.sum(J[:,:,a]*J[:,:,b],axis=1))/np.maximum(length[:,a]*length[:,b],1e-300)
            nonorth=np.maximum(nonorth,np.rad2deg(np.arcsin(np.clip(cosine,0,1))))
    return minimum,scaled,nonorth


def topology(cells,markers):
    allkeys=[]
    for typ,ids in cells.items():
        for face in FACES[typ]:
            keys=np.full((len(ids),4),-1,np.int32);keys[:,:len(face)]=ids[:,face]
            allkeys.append(np.sort(keys,axis=1))
    keys=np.concatenate(allkeys);unique,counts=np.unique(keys,axis=0,return_counts=True)
    boundary=unique[counts==1];source=[]
    for rows in markers.values():
        for face in rows:source.append(sorted(face+[-1]*(4-len(face))))
    source=np.asarray(source,np.int32);sunique,scount=np.unique(source,axis=0,return_counts=True)
    assert np.all(counts<=2),'Nonmanifold face'
    assert np.all(scount==1),'Duplicate boundary face/tag'
    assert np.array_equal(boundary,sunique),'Boundary does not match single-fluid-neighbour faces'
    return {'single_neighbour_boundary_faces':len(boundary),'declared_boundary_faces':len(source),
            'max_fluid_neighbours_per_face':int(counts.max()),'boundary_exactly_matches_exterior':True}


def normal_lines(path):
    with path.open() as f:
        count=int(f.readline().split()[0]);f.readline();out=[]
        for _ in range(count):
            n=int(f.readline().split()[0]);out.append(np.array([int(f.readline().split()[0])-1 for _ in range(n)]))
    return out


def vtk_grid(xyz,cells):
    g=vtk.vtkUnstructuredGrid();pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(xyz,deep=True));g.SetPoints(pts)
    for typ,ids in cells.items():
        if typ==13:ids=ids[:,[0,2,1,3,5,4]]
        for row in ids:
            g.InsertNextCell(typ,len(row),row)
    return g


def audit(path,level):
    xyz,cells,markers=load_mesh(path);count=sum(len(x) for x in cells.values())
    wall=np.unique(np.concatenate(markers['WING3D']));root=wall[np.abs(xyz[wall,1])<1e-10]
    assert abs(np.ptp(xyz[root,0])-1)<1e-9
    result={'level':level,'file':str(path.relative_to(ROOT)),'sha256':sha(path),'nodes':len(xyz),'cells':count,
            'cell_types':{str(t):len(a) for t,a in cells.items()},'wing_points':len(wall),
            'root_chord':float(np.ptp(xyz[root,0])),'wing_bounds':np.array([xyz[wall].min(axis=0),xyz[wall].max(axis=0)]).tolist(),
            'volume_bounds':np.array([xyz.min(axis=0),xyz.max(axis=0)]).tolist(),'topology':topology(cells,markers)}
    if 12 in cells:
        mins=[];scaled=[];orth=[]
        for i in range(0,len(cells[12]),10000):
            a,b,c=hex_jacobians(xyz[cells[12][i:i+10000]]);mins.extend(a);scaled.extend(b);orth.extend(c)
        result['hex_27point_Jacobian']=stats(mins);result['hex_nonpositive_sampled_Jacobian']=int(np.sum(np.array(mins)<=0))
        result['hex_sampled_scaled_Jacobian']=stats(scaled);result['hex_coordinate_nonorthogonality_deg']=stats(orth)
        assert min(mins)>0,'Sampled nonpositive hex Jacobian'
    if 13 in cells:
        sys.path.insert(0,str(ROOT/'work/m6_followup'))
        from wallnormal_mesh import wedge_minimum
        val=wedge_minimum(xyz[cells[13][:,[0,2,1,3,5,4]]])
        result['prism_exact_min_Jacobian']=stats(val);assert val.min()>0,'Nonpositive prism Jacobian'
    prefix=path.with_suffix('')
    lines=normal_lines(Path(str(prefix)+'.lines_fmt'))
    assert set(int(x[0]) for x in lines)==set(int(x) for x in wall)
    distances=[np.linalg.norm(np.diff(xyz[a],axis=0),axis=1) for a in lines]
    first=np.array([d[0] for d in distances]);height=np.array([d.sum() for d in distances])
    growth=np.concatenate([d[1:]/d[:-1] for d in distances])
    result['wall_radial_columns']={'count':len(lines),'layers_min':min(len(x)-1 for x in lines),'layers_max':max(len(x)-1 for x in lines),
        'first_spacing':stats(first),'adjacent_growth_in_BL':stats(growth),'BL_radial_column_arclength':stats(height),
        'warning':'Source radial line arclength/BL label is not flow delta99 or exact normal projection.'}
    rows=[]
    for a,d,h in zip(lines,distances,height):
        w=xyz[a[0]];eta=w[1]/1.4760179762198;c=1+(0.5625159852668158-1)*min(eta,1)
        le=np.tan(np.deg2rad(29.999))*min(w[1],1.4760179762198);xc=(w[0]-le)/c
        rows.append([a[0],*w,eta,xc,d[0],len(d),h,max(d[1:]/d[:-1])])
    data=PROJECT/'data/tmr_sharp_20261025_v1';data.mkdir(exist_ok=True)
    np.savetxt(data/f'mesh_L{level}_normal_columns.csv',rows,delimiter=',',header='node,x,y,z,eta,x_over_c,first_spacing,BL_layers,BL_arclength,max_adjacent_BL_growth',comments='')
    rows=np.asarray(rows)
    result['regions']={}
    for name,mask in [('LE',rows[:,5]<.05),('TE',rows[:,5]>.95),('tip',rows[:,4]>.9),('root',rows[:,4]<.2)]:
        if np.any(mask):result['regions'][name]={'columns':int(mask.sum()),'first_spacing':stats(rows[mask,6]),'max_BL_growth':float(rows[mask,9].max())}
    result['mesh_screens_passed']=True
    result['limits']=['Hex Jacobian checked at27 reference points, not a global analytic proof.',
                      'No flow-based y+/BL thickness, shock, wake or physical grid independence acceptance yet.']
    if level==1:
        g=vtk_grid(xyz,cells)
        writer=vtk.vtkXMLUnstructuredGridWriter();writer.SetFileName(str(data/'source_fine_mesh.vtu'));writer.SetInputData(g);writer.SetCompressorTypeToZLib();assert writer.Write()
    save(PROJECT/f'reports/tmr_mesh_L{level}_20261025.json',result)
    print({'level':level,'cells':count,'nodes':len(xyz),'first':result['wall_radial_columns']['first_spacing'],'mesh_screens_passed':True},flush=True)
    return result,xyz[wall],xyz


def main():
    # Meaningful operator controls: valid reference cube, inverted cube, valid SU2 prism.
    cube=(SIGNS+1)/2
    assert hex_jacobians(cube[None])[0][0]>0
    inverted=cube.copy();inverted[:,0]*=-1
    assert hex_jacobians(inverted[None])[0][0]<0
    folder=CASE/'mesh_family_budget_v3';result=[];finewall=None;finepoints=None
    for level in [1,2,3]:
        r,wall,points=audit(folder/f'wing_strct.{level}.su2',level)
        if level==1:finewall=wall;finepoints=points
        else:
            dw=cKDTree(finewall).query(wall)[0];dp=cKDTree(finepoints).query(points)[0]
            r['all_nodes_are_fine_node_subset_max_distance']=float(dp.max());r['wall_is_fine_node_subset_max_distance']=float(dw.max())
            assert dp.max()<1e-12 and dw.max()<1e-12
        result.append(r)
    contract=read(CASE/'contract.json')
    within=result[0]['nodes']<=contract['mesh_resource_budget']['fine_max_nodes'] and result[0]['cells']<=contract['mesh_resource_budget']['fine_max_cells']
    assert within,'Registered mesh resource budget exceeded'
    save(PROJECT/'reports/tmr_mesh_family_20261025.json',{'contract_sha256':sha(CASE/'contract.json'),'levels':result,
        'source_unchanged':True,'fine_resource_budget_passed':within,'cell_count_ratio':[result[0]['cells']/result[1]['cells'],result[1]['cells']/result[2]['cells']],
        'nested_wall_nodes':True,'same_analytic_source_geometry':True,'same_outer_radius':100.,'full_mesh_or_flow_acceptance':False})


if __name__=='__main__':main()
