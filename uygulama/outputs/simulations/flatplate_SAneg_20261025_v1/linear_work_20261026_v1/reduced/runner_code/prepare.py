"""Preserve source coordinates, convert indexing only, register before CFD/reference scoring."""
from pathlib import Path
import sys,zipfile,gzip,json,math,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now
CASE=ROOT/'outputs/simulations/flatplate_SAneg_20261025_v1'

def parse(data):
    a=np.fromstring(data.decode().replace('D','E'),sep=' ')
    assert a[0]==1
    ni,nj=map(int,a[1:3]);assert len(a)==3+2*ni*nj
    return a[3:].reshape(2,nj,ni).transpose(1,2,0)

def convert(xy,path):
    nj,ni,_=xy.shape;indices=np.arange(ni*nj).reshape(nj,ni)
    q=np.stack([indices[:-1,:-1],indices[:-1,1:],indices[1:,1:],indices[1:,:-1]],axis=-1).reshape(-1,4)
    p=xy.reshape(-1,2);v=p[q]
    cross=[]
    for k in range(4):
        a=v[:,(k+1)%4]-v[:,k];b=v[:,(k-1)%4]-v[:,k]
        cross.append(a[:,0]*b[:,1]-a[:,1]*b[:,0])
    assert np.min(cross)>0
    seg={'wall':[],'symmetry':[],'inlet':[],'outlet':[],'farfield':[]}
    for i in range(ni-1):seg['symmetry' if xy[0,i+1,0]<=0 else 'wall'].append((indices[0,i],indices[0,i+1]))
    seg['inlet']=[(indices[j,0],indices[j+1,0]) for j in range(nj-1)]
    seg['outlet']=[(indices[j,-1],indices[j+1,-1]) for j in range(nj-1)]
    seg['farfield']=[(indices[-1,i],indices[-1,i+1]) for i in range(ni-1)]
    counts={}
    for face in q:
        for k in range(4):
            edge=tuple(sorted((int(face[k]),int(face[(k+1)%4]))));counts[edge]=counts.get(edge,0)+1
    boundary={tuple(sorted(map(int,e))) for vals in seg.values() for e in vals}
    assert boundary=={e for e,n in counts.items() if n==1} and max(counts.values())==2
    assert len(boundary)==sum(len(v) for v in seg.values())
    with path.open('w') as f:
        f.write(f'NDIME= 2\nNELEM= {len(q)}\n')
        for k,row in enumerate(q):f.write('9 '+' '.join(map(str,row))+f' {k}\n')
        f.write(f'NPOIN= {len(p)}\n')
        for k,row in enumerate(p):f.write(f'{row[0]:.17g} {row[1]:.17g} {k}\n')
        f.write(f'NMARK= {len(seg)}\n')
        for name,edges in seg.items():
            f.write(f'MARKER_TAG= {name}\nMARKER_ELEMS= {len(edges)}\n')
            for a,b in edges:f.write(f'3 {a} {b}\n')
    restored=[]
    lines=path.read_text().splitlines();start=next(i for i,s in enumerate(lines) if s.startswith('NPOIN'))+1
    for row in lines[start:start+len(p)]:restored.append([float(t) for t in row.split()[:2]])
    assert np.array_equal(np.array(restored),p)
    wall=xy[0,:,0]>=0
    return {'nodes':len(p),'cells':len(q),'dimensions':[ni,nj],'positive_corner_cross_min':float(np.min(cross)),
        'boundary_edges':{k:len(v) for k,v in seg.items()},'source_coordinate_roundtrip_bitwise':True,
        'wall_first_y_m':float(xy[1,wall,1].min()),'normal_growth_max':float(np.max(np.diff(xy[:,:,1],axis=0)[1:]/np.diff(xy[:,:,1],axis=0)[:-1])),
        'wall_dx_min_max_m':[float(np.diff(xy[0,wall,0]).min()),float(np.diff(xy[0,wall,0]).max())],
        'extent_m':{'min':p.min(0).tolist(),'max':p.max(0).tolist()}}

def config(mesh,iterations):
    # Same compressible physical case as TMR and tutorial. Pressure is derived from Re,
    # not copied as rounded dimensional values from a differently scaled implementation.
    T=300.;R=287.058;M=.2;mu0=1.716e-5;T0=273.15;S=110.4
    mu=mu0*(T/T0)**1.5*(T0+S)/(T+S);U=M*math.sqrt(1.4*R*T);rho=5e6*mu/U;p=rho*R*T
    d={'SOLVER':'RANS','KIND_TURB_MODEL':'SA','SA_OPTIONS':'NEGATIVE, WITHFT2','MATH_PROBLEM':'DIRECT','RESTART_SOL':'NO',
       'MACH_NUMBER':M,'AOA':0,'SIDESLIP_ANGLE':0,'FREESTREAM_TEMPERATURE':T,'REYNOLDS_NUMBER':5e6,'REYNOLDS_LENGTH':1,
       'FLUID_MODEL':'STANDARD_AIR','GAMMA_VALUE':1.4,'GAS_CONSTANT':R,'VISCOSITY_MODEL':'SUTHERLAND','MU_REF':mu0,'MU_T_REF':T0,'SUTHERLAND_CONSTANT':S,
       'FREESTREAM_NU_FACTOR':3,'PRANDTL_LAM':.72,'PRANDTL_TURB':.9,'REF_AREA':2,'REF_LENGTH':2,
       'MARKER_HEATFLUX':'(wall,0)','MARKER_SYM':'(symmetry)',
       'MARKER_INLET':f'(inlet,{T*(1+.2*M*M):.15g},{p*(1+.2*M*M)**3.5:.15g},1,0,0)',
       'MARKER_OUTLET':f'(outlet,{p:.15g},farfield,{p:.15g})','MARKER_PLOTTING':'(wall)','MARKER_MONITORING':'(wall)',
       'NUM_METHOD_GRAD':'WEIGHTED_LEAST_SQUARES','CFL_NUMBER':100,'CFL_ADAPT':'YES','CFL_ADAPT_PARAM':'(0.1,2,100,1e5,0.001,50)',
       'MGLEVEL':0,'ITER':iterations,'LINEAR_SOLVER':'FGMRES','LINEAR_SOLVER_PREC':'LU_SGS','LINEAR_SOLVER_ERROR':1e-6,'LINEAR_SOLVER_ITER':40,
       'CONV_NUM_METHOD_FLOW':'ROE','MUSCL_FLOW':'YES','SLOPE_LIMITER_FLOW':'NONE','TIME_DISCRE_FLOW':'EULER_IMPLICIT',
       'CONV_NUM_METHOD_TURB':'SCALAR_UPWIND','MUSCL_TURB':'NO','TIME_DISCRE_TURB':'EULER_IMPLICIT',
       'CONV_FIELD':'(RMS_DENSITY,RMS_NU_TILDE)','CONV_RESIDUAL_MINVAL':-13,'CONV_STARTITER':200,
       'MESH_FILENAME':mesh,'MESH_FORMAT':'SU2','SOLUTION_FILENAME':'restart_flow','READ_BINARY_RESTART':'YES',
       'OUTPUT_FILES':'(RESTART,PARAVIEW,SURFACE_PARAVIEW,SURFACE_CSV)','OUTPUT_WRT_FREQ':'(200,200,200,200)',
       'WRT_RESTART_OVERWRITE':'NO','WRT_SURFACE_OVERWRITE':'NO','WRT_VOLUME_OVERWRITE':'NO','TABULAR_FORMAT':'CSV',
       'CONV_FILENAME':'history','RESTART_FILENAME':'restart_flow','VOLUME_FILENAME':'flow','SURFACE_FILENAME':'surface_flow',
       'SCREEN_OUTPUT':'(INNER_ITER,RMS_DENSITY,RMS_NU_TILDE,DRAG)','HISTORY_OUTPUT':'(ITER,RMS_RES,AERO_COEFF,LINSOL,CFL_NUMBER)',
       'VOLUME_OUTPUT':'(COORDINATES,SOLUTION,PRIMITIVE)'}
    return ''.join(f'{k}= {v}\n' for k,v in d.items()),{'mu_Pa_s':mu,'U_m_s':U,'rho_kg_m3':rho,'p_Pa':p,'inlet_Ttotal_K':T*(1+.2*M*M)}

def main():
    assert not CASE.exists();CASE.mkdir(parents=True);(CASE/'meshes').mkdir()
    archive=zipfile.ZipFile(BASE/'sources/flatplategrids-grids.zip');xyall={};levels={}
    for role,shape,tail in [('coarse','69x49','3levelsdown_69x49.p2dfmt'),('medium','137x97','2levelsdown_137x97.p2dfmt'),('fine','273x193','1leveldown_273x193.p2dfmt.gz')]:
        name=next(n for n in archive.namelist() if n.endswith(tail));data=archive.read(name)
        raw=BASE/'sources'/Path(name).name;raw.write_bytes(data)
        if name.endswith('.gz'):data=gzip.decompress(data)
        xy=parse(data);xyall[role]=xy;mesh=CASE/f'meshes/{role}.su2'
        report=convert(xy,mesh);report.update(source_archive_member=name,source_member_sha256=sha(raw),mesh_sha256=sha(mesh))
        levels[role]=report
    assert np.array_equal(xyall['fine'][::2,::2],xyall['medium'])
    assert np.array_equal(xyall['medium'][::2,::2],xyall['coarse'])
    contract={'version':'2026-10-25.flatplate1','created_utc':now(),'scope':'2D compressible SA-neg implementation comparison; not experimental model validation or M6 qualification',
       'not_blind':True,'source':'NASA TMR VERIF/2DZP; SU2 official tutorial as numerical starting recipe',
       'physical':{'Mach':.2,'Re_per_m':5e6,'T_K':300,'wall_length_m':2,'domain_height_m':1,'SA_variant':'SA-neg standard NEGATIVE,WITHFT2','nu_tilde_inflow_over_nu':3,'wall':'adiabatic no slip'},
       'gates_registered_before_flow':{'density_log10_max':-10,'nu_tilde_log10_max':-11,'last100_CD_range_max':1e-7,'fine_max_yplus':1,
          'fine_Cf_x0p97008_relative_difference_each_code_max':.02,'fine_Cf_curve_relative_RMS_each_code_max':.03,
          'curve_scoring_window_m':[.1,1.9],'all_curve_points_outside_window_retained_and_reported':True,
          'velocity_profile_relative_L2_max':.03,'mut_profile_relative_L2_max':.05,'three_iterative_gates_required':True,
          'medium_fine_Cf_change_max':.01,'medium_fine_CD_change_max':.02},
       'limits':['Leading-edge singularity: global total drag may not admit formal order; no automatic GCI.','Finite volume discretizations differ.','No experimental force substituted.','No absolute turbulence-model proof from one case.'],
       'budgets':{'threads':4,'max_iterations':8000,'seconds':{'smoke':60,'coarse':180,'medium':300,'fine':600},'sampled_working_set_GiB':2.5},
       'levels':levels,'numerical_changes_from_tutorial':{'SA_options':'Use standard SA-neg with ft2 explicitly, compare standard-SA references where passive for positive states',
          'inflow_nu':'Explicit3nu as NASA input tur10=3','pressure':'Derived consistently from chosen SI Sutherland/Re instead of rounded tutorial pressure',
          'CFL':'Same tutorial recipe; expand adaptive parameter syntax for installed8.5', 'linear':'FGMRES/LUSGS40,tolerance1e-6 explicitly',
          'convergence':'Target-13 for both density/SA with8000iteration/time cap; separate registered gates','outputs':'Non-overwritten checkpoints every200'}}
    cases={}
    for role in ['smoke','coarse','medium','fine']:
        folder=CASE/role;folder.mkdir();meshrole='coarse' if role=='smoke' else role
        text,derived=config('../meshes/'+meshrole+'.su2',20 if role=='smoke' else 8000)
        (folder/'case.cfg').write_text(text,encoding='utf-8')
        cases[role]={'folder':str(folder.relative_to(ROOT)),'cfg_sha256':sha(folder/'case.cfg'),'mesh':str((CASE/f'meshes/{meshrole}.su2').relative_to(ROOT)),'mesh_sha256':levels[meshrole]['mesh_sha256']}
    contract['derived_freestream']=derived;save(CASE/'contract.json',contract)
    save(CASE/'plan.json',{'created_utc':now(),'contract_sha256':sha(CASE/'contract.json'),'cases':cases})
    taskpath=ROOT/read(BASE/'task.json')['path'];task=read(taskpath);task.update(contract=str((CASE/'contract.json').relative_to(ROOT)),contract_sha256=sha(CASE/'contract.json'));save(taskpath,task)
    print({r:{k:v[k] for k in ['cells','wall_first_y_m','normal_growth_max']} for r,v in levels.items()});print(derived)

if __name__=='__main__':main()
