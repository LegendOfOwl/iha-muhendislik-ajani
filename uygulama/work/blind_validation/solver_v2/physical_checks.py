from pathlib import Path
import numpy as np,json,sys
from initialize import read_binary
from audit_mesh_family import parse_mesh,OUT,ROOT
from postprocess import read_vtu
def check(name):
    folder=OUT/'simulations'/name;sel=json.loads((folder/'checkpoint_selection.json').read_text());h,labels,data=read_binary(ROOT/sel['restart']);p,c,marks=parse_mesh(folder/'mesh.su2');assert len(p)==len(data)
    cond=json.loads((ROOT/'work/blind_validation/analysis_input/conditions.json').read_text());ga=1.4;R=287.058;T=cond['T_K'];U=cond['Mach']*np.sqrt(ga*R*T);mu=1.716e-5*(T/273.15)**1.5*(273.15+110.4)/(T+110.4);rho=cond['Re_chord']*mu/(U*cond['chord_m']);press=rho*R*T;q=.5*rho*U**2
    xyerr=float(np.max(np.linalg.norm(data[:,:2]-p,axis=1)));assert xyerr<1e-10
    r=data[:,2];mom=data[:,3:5];en=data[:,5];vel=mom/r[:,None];pst=(ga-1)*(en-.5*np.sum(mom*mom,1)/r);pinf=1/(ga*cond['Mach']**2);alpha=np.deg2rad(cond['alpha_deg']);uv=np.array([np.cos(alpha),np.sin(alpha)])
    far=marks['FARFIELD'];a=p[far[:,0]];b=p[far[:,1]];dv=b-a;n=np.c_[dv[:,1],-dv[:,0]];mid=(a+b)/2;flip=np.sum(n*mid,1)<0;n[flip]*=-1
    flux=np.zeros(2);mass=0.
    for k in [0,1]:
        ids=far[:,k];mn=np.sum(mom[ids]*n,1);un0=n@uv
        mass+=.5*np.sum(mn-un0)
        flux+=.5*np.sum(mn[:,None]*vel[ids]-un0[:,None]*uv+(pst[ids]-pinf)[:,None]*n,axis=0)
    force=-2*flux;CL=float(-force[0]*np.sin(alpha)+force[1]*np.cos(alpha));CD=float(force[0]*np.cos(alpha)+force[1]*np.sin(alpha));met=json.loads((folder/'prediction_metrics.json').read_text())
    vd,vxyz,va=read_vtu(ROOT/sel['volume']);from scipy.spatial import cKDTree
    dd,ii=cKDTree(vxyz[:,:2]).query(p);cp_check=2*(pst-pinf);cperr=np.abs(cp_check-va['Pressure_Coefficient'][ii])
    sum_area=sum(.5*np.sum(p[co,0]*p[np.roll(co,-1),1]-p[np.roll(co,-1),0]*p[co,1]) for co in c)
    w=marks['AIRFOIL'];wallarea=abs(.5*np.sum(p[w[:,0],0]*p[w[:,1],1]-p[w[:,1],0]*p[w[:,0],1]));fararea=abs(.5*np.sum(p[far[:,0],0]*p[far[:,1],1]-p[far[:,1],0]*p[far[:,0],1]))
    result={'run':name,'checkpoint_iteration':sel['iteration'],'physical_freestream_from_authoritative_conditions_and_constitutive_air_assumptions':{'T_K':T,'Mach':cond['Mach'],'alpha_deg':cond['alpha_deg'],'Re_chord':cond['Re_chord'],'chord_m':cond['chord_m'],'gamma':ga,'R_J_kg_K':R,'U_m_s':float(U),'mu_Pa_s':float(mu),'rho_kg_m3':float(rho),'p_Pa':float(press),'dynamic_pressure_Pa':float(q),'calculation':'Sutherland mu at source computational temperature; U=M*sqrt(gamma*R*T); rho=Re*mu/(U*c); p=rho*R*T. Pressure is derived, not fitted.'},'stored_solution_scaling':{'rho_ref_kg_m3':float(rho),'velocity_ref_m_s':float(U),'pressure_ref_Pa':float(rho*U**2),'temperature_ref_K':T,'note':'Native restart and VTU primitive fields are nondimensional under REF_DIMENSIONALIZATION=FREESTREAM_VEL_EQ_ONE; Cp/Cf are already dimensionless.'},'restart_vs_mesh_max_xy_error_m':xyerr,'restart_vs_VTU_max_xy_error_m':float(dd.max()),'Cp_recomputed_from_conservative_state_max_difference':float(cperr.max()),'Cp_recomputed_RMS_difference':float(np.sqrt(np.mean(cperr**2))),'mass_flux_farfield_nondimensional':float(mass),'farfield_physical_momentum_flux_quadrature':{'CL':CL,'CD':CD,'relative_difference_to_native_wall_CL':abs(CL-met['CL'])/abs(met['CL']),'relative_difference_to_native_wall_CD':abs(CD-met['CD'])/abs(met['CD']),'method':'Trapezoid nodal physical momentum/pressure perturbation flux at outer boundary, subtracting uniform freestream analytically; far viscous traction neglected. This is not the solver discrete flux including JST dissipation and is not an automatic acceptance test.'},'domain_area_check':{'fluid_cell_area_sum_m2':float(sum_area),'outer_polygon_area_m2':float(fararea),'wall_polygon_area_m2':float(wallarea),'balance_error_m2':float(sum_area-(fararea-wallarea))},'wall_force_dimensional_per_unit_span':{'lift_N_per_m':float(q*cond['chord_m']*met['CL']),'drag_N_per_m':float(q*cond['chord_m']*met['CD']),'scope':'2D section per unit span; not total wing/aircraft loads'}}
    (folder/'physical_units_force_balance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return result
if __name__=='__main__':check(sys.argv[1])
