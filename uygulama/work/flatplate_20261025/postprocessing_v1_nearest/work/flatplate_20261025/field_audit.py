from prepare import ROOT,BASE,CASE,read,save,sha,parse
import sys,os
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
from scipy.spatial import cKDTree
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def field(p):
    reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(p));reader.Update();g=reader.GetOutput()
    assert g.GetNumberOfPoints()>0
    xyz=vtk_to_numpy(g.GetPoints().GetData()).astype(float)
    data={g.GetPointData().GetArrayName(i):vtk_to_numpy(g.GetPointData().GetArray(i)).astype(float) for i in range(g.GetPointData().GetNumberOfArrays())}
    return g,xyz,data

def loadmesh(role):
    p=CASE/'meshes'/(role+'.su2');lines=p.read_text().splitlines();j=next(i for i,s in enumerate(lines) if s.startswith('NPOIN'));n=int(lines[j].split('=')[1])
    return np.array([[float(v) for v in s.split()[:2]] for s in lines[j+1:j+1+n]])

def audit(role,meshrole=None):
    meshrole=meshrole or role
    frozen=read(CASE/role/'prediction_frozen.json')
    for p,h in frozen['files_sha256'].items():assert sha(ROOT/p)==h
    m=frozen['matched'];assert m is not None
    i=m['field_iteration'];g,xyz,data=field(CASE/role/f'flow_{i:06d}.vtu');s,wall,sd=field(CASE/role/f'surface_flow_{i:06d}.vtu')
    order=np.argsort(wall[:,0]);x=wall[order,0];cf=sd['Skin_Friction_Coefficient'][order,0];yp=sd['Y_Plus'][order]
    assert np.all(np.diff(x)>0) and abs(x[0])<1e-10 and abs(x[-1]-2)<1e-10
    datadir=ROOT/'outputs/data/qualification/flatplate_SAneg_20261025_v1'/role;datadir.mkdir(parents=True,exist_ok=True)
    np.savetxt(datadir/'wall.csv',np.column_stack([x,cf,yp]),delimiter=',',header='x_m,Cfx,YPlus',comments='')
    independent=float(np.trapezoid(cf,x)/2)
    mesh=loadmesh(meshrole);shape=read(CASE/'contract.json')['levels'][meshrole]['dimensions'];ni,nj=shape;mesh=mesh.reshape(nj,ni,2)
    profiles=[];tree=cKDTree(xyz[:,:2]);free=read(CASE/'contract.json')['derived_freestream']
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for station,color in [(.97008,'#007c91'),(1.90334,'#b75d38')]:
        col=int(np.argmin(abs(mesh[0,:,0]-station)));pts=mesh[:,col];distance,index=tree.query(pts);valid=distance<1e-6
        vel=data['Velocity'][index,0];mut=data['Eddy_Viscosity'][index]/free['mu_Pa_s'];y=pts[:,1]
        valid &= np.isfinite(vel)&np.isfinite(mut)
        assert valid.all(),'Preserve invalid samples; do not fill with zeros'
        localcf=float(np.interp(pts[0,0],x,cf));rho_wall=data['Density'][index[0]];mu_wall=data['Laminar_Viscosity'][index[0]]
        tau=localcf*.5*free['rho_kg_m3']*free['U_m_s']**2;utau=np.sqrt(abs(tau)/rho_wall)
        uplus=vel/utau;yplus=y*utau/(mu_wall/rho_wall)
        path=datadir/f'profile_x{station:g}.csv'
        np.savetxt(path,np.column_stack([pts,valid.astype(int),vel/free['U_m_s'],mut,yplus,uplus]),delimiter=',',
            header='x_m,y_m,valid_sample,u_over_Uinf,mut_over_muinf,yplus,uplus',comments='')
        profiles.append({'requested_x_m':station,'actual_x_m':float(pts[0,0]),'column':col,'invalid_samples':int((~valid).sum()),
            'coordinate_mapping_max_m':float(distance.max()),'csv':str(path.relative_to(ROOT))})
        label=f'x={pts[0,0]:.5f}'
        axes[0].plot(vel/free['U_m_s'],y,color=color,label=label);axes[1].plot(mut,y,color=color,label=label)
        axes[2].semilogx(yplus[1:],uplus[1:],color=color,label=label)
    axes[0].set(xlabel='u/Uinf',ylabel='y [m]',ylim=(0,.06));axes[1].set(xlabel='mu_t/mu_inf',ylabel='y [m]',ylim=(0,.06));axes[2].set(xlabel='y+',ylabel='u+',xlim=(.1,1e4),ylim=(0,35))
    for ax in axes:ax.grid(alpha=.2);ax.legend()
    fig.suptitle(f'{role}: direct native columns, field iteration{i}; diagnostic profiles');fig.tight_layout()
    fig.savefig(ROOT/f'outputs/plots/flatplate_{role}_profiles_20261025.png',dpi=150);plt.close(fig)
    result={'role':role,'matched':m,'native_status':frozen['native_status'],'wall_points':len(x),'max_yplus':float(yp.max()),
        'all_wall_yplus_below1':bool((yp<1).all()),'Cf_x0p97008':float(np.interp(.97008,x,cf)),
        'CD_independent_trapezoid':independent,'CD_integration_relative_difference':abs(independent/m['CD']-1),
        'iterative_gate':m['rms[Rho]']< -10 and m['rms[nu]']< -11 and m['last100_samples']==100 and m['CD_last100_range']<1e-7,
        'profiles':profiles,'negative_nu_tilde_nodes':int((data['Nu_Tilde']<0).sum()),'native_arrays':list(data),
        'source_field_sha256':sha(CASE/role/f'flow_{i:06d}.vtu'),'source_surface_sha256':sha(CASE/role/f'surface_flow_{i:06d}.vtu')}
    save(ROOT/f'outputs/reports/flatplate_{role}_field_audit_20261025.json',result)
    print({k:result[k] for k in ['role','matched','max_yplus','Cf_x0p97008','iterative_gate']},flush=True)

if __name__=='__main__':
    for role in ['coarse','medium','fine']:audit(role)
