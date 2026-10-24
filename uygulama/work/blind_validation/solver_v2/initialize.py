"""Interpolate ONLY own predicted fields as a starting guess for a new mesh."""
from pathlib import Path
import struct,hashlib,json,sys,time
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree
from audit_mesh_family import parse_mesh
ROOT=Path(__file__).resolve().parents[3];SIM=ROOT/'outputs/projects/proje-15cce2de02/simulations'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_binary(p):
    b=Path(p).read_bytes();h=struct.unpack('<5i',b[:20]);assert h[0]==535532 and h[1]==7
    labels=b[20:20+33*h[1]];data=np.frombuffer(b,dtype='<f8',offset=20+33*h[1],count=h[1]*h[2]).reshape(h[2],h[1]).copy()
    return h,labels,data
def initialize(name,source):
    folder=SIM/name;source=Path(source);head,labels,a=read_binary(source);p,con,mark=parse_mesh(folder/'mesh.su2')
    cond=json.loads((ROOT/'work/blind_validation/analysis_input/conditions.json').read_text());alpha=np.deg2rad(cond['alpha_deg']);gamma=1.4;M=cond['Mach'];Re=cond['Re_chord']
    # Stored restart variables use rho_inf=U_inf=1 (REF_DIMENSIONALIZATION velocity=1).
    fstate=np.array([1.,np.cos(alpha),np.sin(alpha),1./(gamma*M*M)/(gamma-1)+.5,3./Re])
    start=time.monotonic();near,ids=cKDTree(a[:,:2]).query(p);exact=near<1e-11
    values=LinearNDInterpolator(a[:,:2],a[:,2:])(p)
    outside=~np.all(np.isfinite(values),axis=1);values[outside]=fstate
    values[exact]=a[ids[exact],2:]
    wall=np.unique(mark['AIRFOIL']);values[wall,1:3]=0.;values[wall,4]=0.
    pressure=(gamma-1)*(values[:,3]-.5*np.sum(values[:,1:3]**2,axis=1)/values[:,0])
    assert np.all(np.isfinite(values)) and np.min(values[:,0])>0 and np.min(pressure)>0 and np.min(values[:,4])>=0
    data=np.c_[p,values].astype('<f8');dest=folder/'initial_guess.dat'
    with dest.open('wb') as f:f.write(struct.pack('<5i',head[0],7,len(p),0,0));f.write(labels);f.write(data.tobytes())
    provenance={'purpose':'Initial guess only; final field must independently converge on this new mesh/geometry/farfield. No expected result is used.','source_own_restart':str(source.relative_to(ROOT)),'source_sha256':sha(source),'destination_sha256':sha(dest),'target_mesh_sha256':sha(folder/'mesh.su2'),'variable_names':['x','y','Density','Momentum_x','Momentum_y','Energy','Nu_Tilde'],'stored_units':'coordinates_m; rho_inf=U_inf=1 nondimensional conservative variables and nu_tilde/(U_inf*c); same authoritative physical config','interpolation':'LinearNDInterpolator of own conservative state; exact coordinate matches copied unchanged; points outside old convex hull use freestream. Wall momentum and nu_tilde initialized to zero, no-slip SA boundary. This is neither a solution transfer acceptance nor a physical correction.','exact_coordinate_matches':int(exact.sum()),'interpolated_points':int((~exact&~outside).sum()),'freestream_outside_old_hull':int(outside.sum()),'nodes':len(p),'minimum_density_nondimensional':float(values[:,0].min()),'minimum_pressure_nondimensional':float(pressure.min()),'free_stream_state':fstate.tolist(),'SA_nu_factor':3.,'SA_nu_factor_note':'Unchanged SU2 default verified from own v1 farfield restart and official v8.5.0 CConfig.cpp. FREESTREAM_TURB2LAMVISCRATIO10 is not the SA nu_tilde initialization factor.','seconds':time.monotonic()-start}
    (folder/'initialization_provenance.json').write_text(json.dumps(provenance,indent=2));print(json.dumps(provenance,indent=2));return dest
if __name__=='__main__':initialize(sys.argv[1],ROOT/sys.argv[2])
