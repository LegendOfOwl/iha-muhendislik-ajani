"""Position-dependent normal redistribution of the original M6 prism columns.

Wall, farfield, outer prism interface and every cell connection remain fixed.
No expected experimental pressure is read or used by this mesher.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import vtk_to_numpy
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-e9319baef1'
BASE=OUT/'simulations/m6_bounded_cfl_20261019_123823';DEST=OUT/'simulations/m6_wallnormal_mesh_20261024'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,a):p.write_text(json.dumps(a,indent=2,allow_nan=False))
def stats(a):a=np.array(a);return {'min':float(a.min()),'median':float(np.median(a)),'p95':float(np.quantile(a,.95)),'max':float(a.max())}
def wedge_minimum(p):
    # det(J) is affine in(r,s) and quadratic in t for a straight6-node wedge.
    # Therefore check3 triangular vertices and exact interior minima in t.
    result=[]
    for r,s in [(0.,0.),(1.,0.),(0.,1.)]:
        values=[]
        for t in [-1.,0.,1.]:
            d=np.array([[-.5*(1-t),-.5*(1-t),-.5*(1-r-s)],
                [.5*(1-t),0,-.5*r],[0,.5*(1-t),-.5*s],
                [-.5*(1+t),-.5*(1+t),.5*(1-r-s)],
                [.5*(1+t),0,.5*r],[0,.5*(1+t),.5*s]])
            values.append(np.linalg.det(np.einsum('nki,kj->nij',p,d)))
        fm,f0,fp=values;a=(fp+fm)/2-f0;b=(fp-fm)/2
        tstar=np.divide(-b,2*a,out=np.full_like(a,2.),where=a>0)
        minimum=np.minimum(fm,fp);use=(a>0)&(tstar>-1)&(tstar<1)
        minimum[use]=np.minimum(minimum[use],(a*tstar*tstar+b*tstar+f0)[use]);result.append(minimum)
    return np.min(np.array(result),axis=0)
def main():
    assert not DEST.exists(),'Preserve every previous geometry revision';DEST.mkdir()
    source=BASE/'mesh.su2';lines=source.read_text().splitlines();assert lines[0].strip()=='NDIME= 3'
    nc=int(lines[1].split('=')[1]);cellrows=[[int(v) for v in line.split()] for line in lines[2:2+nc]]
    prism=np.array([a[1:7] for a in cellrows if a[0]==13]);tet=np.array([a[1:5] for a in cellrows if a[0]==10]);assert len(prism)+len(tet)==nc
    ni=2+nc;n=int(lines[ni].split('=')[1].split()[0]);start=ni+1
    points=np.array([[float(v) for v in line.split()[:3]] for line in lines[start:start+n]])
    i=start+n;nm=int(lines[i].split('=')[1]);i+=1;markers={}
    for _ in range(nm):
        tag=lines[i].split('=')[1].strip();num=int(lines[i+1].split('=')[1]);i+=2
        faces=[[int(v) for v in line.split()][1:] for line in lines[i:i+num]];i+=num;markers[tag]=faces
    wall=np.unique(np.concatenate(markers['WING']));far=np.unique(np.concatenate(markers['FARFIELD']))
    neighbour={}
    for a,b in prism[:,[[0,3],[1,4],[2,5]]].reshape(-1,2):
        neighbour.setdefault(int(a),set()).add(int(b));neighbour.setdefault(int(b),set()).add(int(a))
    assert all(len(v)<=2 for v in neighbour.values()),'Branched prism columns require a different method'
    columns=[];covered=set()
    for w in wall:
        assert len(neighbour[int(w)])==1
        chain=[int(w)];previous=None;current=int(w)
        while True:
            candidates=neighbour[current]-({previous} if previous is not None else set())
            if not candidates:break
            assert len(candidates)==1;nextnode=next(iter(candidates));assert nextnode not in chain
            chain.append(nextnode);previous,current=current,nextnode
        assert not covered.intersection(chain),'Two wall columns merge';covered.update(chain);columns.append(chain)
    lengths=np.array([len(a) for a in columns]);assert np.all(lengths==26),np.unique(lengths)
    assert len(covered)==len(neighbour)
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(BASE/'surface_flow.vtu'));r.Update();g=r.GetOutput()
    xyz=vtk_to_numpy(g.GetPoints().GetData());yplus=vtk_to_numpy(g.GetPointData().GetArray('Y_Plus'))
    distance,index=cKDTree(xyz).query(points[wall]);assert distance.max()<2e-7
    target=.5;factor=np.clip(target/np.maximum(yplus[index],target),.25,1.)
    plan={'created_utc':datetime.now(timezone.utc).isoformat(),'source_mesh_sha256':sha(source),
        'own_yplus_field':str((BASE/'surface_flow.vtu').relative_to(ROOT)),'own_field_sha256':sha(BASE/'surface_flow.vtu'),
        'algorithm':'Per-column a=clip(0.5/max(own_yplus,0.5),0.25,1); arclength target f(s)=a*s+(1-a)*(2*s^2-s^3). Source-column piecewise-linear interpolation.',
        'target_yplus_design':target,'strict_solution_max_yplus_remains':1.,'normal_layers_unchanged':25,'cells_unchanged':nc,
        'wall_geometry_unchanged':True,'farfield_and_outer_prism_interface_unchanged':True,
        'source_used_for_design':'Own prior native Y_Plus only; no experiment, expected Cp or shock position used',
        'mesh_qualification_only':True,'future_native_solution_required':True,'minimum_physical_qualification_passed':False}
    save(DEST/'normal_design_preseal.json',plan)
    changed=points.copy();oldfirst=[];newfirst=[];oldgrowth=[];newgrowth=[];height=[]
    for chain,a in zip(columns,factor):
        ids=np.array(chain);p=points[ids];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];assert np.all(np.diff(arc)>0)
        s=arc/arc[-1];dest=arc[-1]*(a*s+(1-a)*(2*s*s-s*s*s))
        q=np.column_stack([np.interp(dest,arc,p[:,j]) for j in range(3)]);q[0]=p[0];q[-1]=p[-1];changed[ids]=q
        before=np.linalg.norm(np.diff(p,axis=0),axis=1);after=np.linalg.norm(np.diff(q,axis=0),axis=1)
        oldfirst.append(before[0]);newfirst.append(after[0]);oldgrowth.extend(before[1:]/before[:-1]);newgrowth.extend(after[1:]/after[:-1]);height.append(arc[-1])
    assert np.array_equal(changed[wall],points[wall]) and np.array_equal(changed[far],points[far])
    assert np.array_equal(changed[tet],points[tet]),'Tetrahedra must remain unchanged'
    p=points[prism];q=changed[prism]
    # Source SU2 ordering has the standard positive wedge orientation.
    oldmin=wedge_minimum(p);newmin=wedge_minimum(q)
    audit={'source_minimum_wedge_jacobian':float(oldmin.min()),'new_minimum_wedge_jacobian':float(newmin.min()),
        'source_nonpositive_wedges':int(np.sum(oldmin<=0)),'new_nonpositive_wedges':int(np.sum(newmin<=0)),
        'exact_wedge_Jacobian_minimum_method':'Affine triangle domain vertices plus quadratic t endpoints/interior vertex',
        'wall_nodes':len(wall),'prism_columns':len(columns),'column_lengths_in_nodes':np.unique(lengths).tolist(),
        'tetrahedra_unchanged':len(tet),'prisms':len(prism),'first_normal_m_before':stats(oldfirst),'first_normal_m_after':stats(newfirst),
        'normal_growth_before':stats(oldgrowth),'normal_growth_after':stats(newgrowth),'total_source_column_arclength_m':stats(height),
        'factor':stats(factor),'wall_source_coordinates_bitwise_unchanged':True,'farfield_coordinates_bitwise_unchanged':True,
        'cell_and_boundary_connectivity_unchanged':True,'reference_yplus_max':float(yplus.max()),
        'primal_geometry_check_passed':bool(np.all(oldmin>0) and np.all(newmin>0)),
        'not_flow_acceptance':'A designed first-height change does not prove actualy+, layer resolution, convergence or experiment accuracy'}
    save(DEST/'normal_mesh_audit.json',audit)
    if not audit['primal_geometry_check_passed']:raise RuntimeError('Preserved rejected mesh design; no solver mesh emitted')
    targetfile=DEST/'mesh.su2'
    with targetfile.open('w') as f:
        f.write('\n'.join(lines[:start])+'\n')
        for i,p in enumerate(changed):f.write(' '.join(format(float(v),'.17g') for v in p)+f' {i}\n')
        f.write('\n'.join(lines[start+n:])+'\n')
    readback=np.loadtxt(targetfile,skiprows=start,max_rows=n,usecols=(0,1,2));assert np.array_equal(readback,changed)
    audit.update(mesh_sha256=sha(targetfile),coordinate_readback_bitwise_passed=True)
    save(DEST/'normal_mesh_audit.json',audit);print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
