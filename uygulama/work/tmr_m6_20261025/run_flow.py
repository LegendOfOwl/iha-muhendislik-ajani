"""Budgeted actual SU2 runs on the registered source mesh family; freeze before review."""
from common import ROOT,BASE,PROJECT,CASE,TASK,read,save,sha,now,memory,run_native
import csv
import math
import os
import shutil
import sys
PLAN=CASE/'flow_plan_v2.json'
PREFIX='flow_v2_'


def config_text(mesh,iterations):
    p=read(CASE/'contract.json')['physical']
    d={'SOLVER':'RANS','KIND_TURB_MODEL':'SA','SA_OPTIONS':'NEGATIVE, WITHFT2','MATH_PROBLEM':'DIRECT','RESTART_SOL':'NO',
       'MACH_NUMBER':p['Mach'],'AOA':p['alpha_deg'],'SIDESLIP_ANGLE':0,'FREESTREAM_TEMPERATURE':p['T_K'],
       'REYNOLDS_NUMBER':p['Re_root'],'REYNOLDS_LENGTH':1.,'FREESTREAM_NU_FACTOR':3.,
       'FLUID_MODEL':'STANDARD_AIR','GAMMA_VALUE':1.4,'GAS_CONSTANT':287.058,'VISCOSITY_MODEL':'SUTHERLAND',
       'MU_REF':p['mu_ref'],'MU_T_REF':p['T_mu_ref_K'],'SUTHERLAND_CONSTANT':p['Sutherland_K'],
       'CONDUCTIVITY_MODEL':'CONSTANT_PRANDTL','PRANDTL_LAM':.72,'PRANDTL_TURB':.9,
       'REF_ORIGIN_MOMENT_X':0.,'REF_ORIGIN_MOMENT_Y':0.,'REF_ORIGIN_MOMENT_Z':0.,
       'REF_LENGTH':p['MAC_m'],'REF_AREA':p['S_ref_half_wing_m2'],'SEMI_SPAN':p['nominal_semispan_m'],
       'MARKER_HEATFLUX':'(WING3D, 0.0)','MARKER_FAR':'(FARFIELD)','MARKER_SYM':'(SYMMETRY)',
       'MARKER_PLOTTING':'(WING3D)','MARKER_MONITORING':'(WING3D)',
       'NUM_METHOD_GRAD':'GREEN_GAUSS','CFL_NUMBER':5.,'CFL_ADAPT':'YES','CFL_ADAPT_PARAM':'(0.5,1.2,5.0,100.0,0.001,50)',
       'MGLEVEL':0,'ITER':iterations,'LINEAR_SOLVER':'FGMRES','LINEAR_SOLVER_PREC':'LU_SGS','LINEAR_SOLVER_ERROR':1e-5,
       'LINEAR_SOLVER_ITER':40,'CONV_NUM_METHOD_FLOW':'JST','MUSCL_FLOW':'NO','JST_SENSOR_COEFF':'(0.5,0.02)',
       'TIME_DISCRE_FLOW':'EULER_IMPLICIT','CONV_NUM_METHOD_TURB':'SCALAR_UPWIND','MUSCL_TURB':'NO','TIME_DISCRE_TURB':'EULER_IMPLICIT',
       'CONV_FIELD':'(RMS_DENSITY)','CONV_RESIDUAL_MINVAL':-9.,'CONV_STARTITER':1000,'CONV_CAUCHY_ELEMS':100,
       'CONV_CAUCHY_EPS':1e-6,'MESH_FILENAME':mesh,'MESH_FORMAT':'SU2','SOLUTION_FILENAME':'restart_flow',
       'OUTPUT_FILES':'(RESTART,PARAVIEW,SURFACE_PARAVIEW,SURFACE_CSV)','OUTPUT_WRT_FREQ':'(200,200,200,200)',
       'TABULAR_FORMAT':'CSV','CONV_FILENAME':'history','RESTART_FILENAME':'restart_flow','VOLUME_FILENAME':'flow',
       'SURFACE_FILENAME':'surface_flow','SCREEN_OUTPUT':'(INNER_ITER,RMS_DENSITY,RMS_NU_TILDE,LIFT,DRAG)',
       'HISTORY_OUTPUT':'(ITER,RMS_RES,MAX_RES,AERO_COEFF,LINSOL,CFL_NUMBER)','VOLUME_OUTPUT':'(COORDINATES,SOLUTION,PRIMITIVE,RESIDUAL)',
       'WRT_RESTART_OVERWRITE':'NO','WRT_SURFACE_OVERWRITE':'NO','WRT_VOLUME_OVERWRITE':'NO','READ_BINARY_RESTART':'YES'}
    return ''.join(f'{k}= {v}\n' for k,v in d.items())


def prepare():
    target=PLAN;assert not target.exists()
    mesh=read(PROJECT/'reports/tmr_mesh_family_20261025.json')
    contract=read(CASE/'contract.json')
    assert mesh['fine_resource_budget_passed']
    levels={'coarse':3,'medium':2,'fine':1,'smoke':3};cases={}
    for name,level in levels.items():
        folder=CASE/(PREFIX+name);folder.mkdir()
        source=CASE/f'mesh_family_budget_v3/wing_strct.{level}.su2'
        # Use a relative input path to avoid four mesh copies and accidental frozen-file changes.
        rel='../mesh_family_budget_v3/'+source.name
        (folder/'case.cfg').write_text(config_text(rel,20 if name=='smoke' else 4000),encoding='utf-8')
        cases[name]={'folder':str(folder.relative_to(ROOT)),'mesh':str(source.relative_to(ROOT)),
                     'mesh_sha256':sha(source),'cfg_sha256':sha(folder/'case.cfg'),
                     'max_seconds':60 if name=='smoke' else contract['native_budget']['seconds_by_role'][name]}
    plan={'prepared_utc':now(),'contract_sha256':sha(CASE/'contract.json'),'threads':4,'cases':cases,
          'baseline_config_sha256':sha(ROOT/'work/validation/sources/turb_ONERAM6.cfg'),
          'physical_changes_from_old_blunt_case':{'geometry':'normalized sharp TMR source grid', 'Mach':[.8395,.84],
              'Re_and_length':[[11.72e6,.64607],[14.6e6,1.]],'T_K':[288.15,300.],
              'SA_options':['default NONE','NEGATIVE, WITHFT2'],'nu_tilde_freestream':'3nu, explicit tagged source option',
              'Sutherland':'Exact TMR Rankine -> K conversion; mu0=1.716e-5',
              'references':'TMR half-wing area/MAC/nominal semispan/moment center'},
          'not_single_variable_comparison_with_old_case':True,'physical_source':'TMR M6 intro + SAneg case specification',
          'numerical_changes_reason':'New source-case baseline syntax adapted to v8.5; method not tuned to experimental outputs',
          'source_solver_implementation_checks':{'FREESTREAM_NU_FACTOR':'CConfig.cpp option and CTurbSASolver nu_tilde_inf=Factor*mu/rho'},
          'smoke_required_before_full_runs':True,'prediction_freeze_before_reference_review':True,
          'prior_rejected_plan_sha256':sha(CASE/'flow_plan.json'),
          'correction':'The intended standard SA-neg requires WITHFT2 in SU2. NEGATIVE alone was rejected by the native parser before flow. EXPERIMENTAL override was not used.',
          'correction_source':'https://su2code.github.io/docs_v7/Physical-Definition/#spalart-allmaras-sa'}
    save(target,plan)
    print('Prepared source-case configs',flush=True)


def rows(path):
    with path.open(newline='') as f:
        return [{k.strip().strip('"'):float(v) for k,v in r.items()} for r in csv.DictReader(f,skipinitialspace=True)]


def freeze(name):
    folder=CASE/(PREFIX+name);target=folder/'prediction_frozen.json';assert not target.exists()
    plan=read(PLAN);case=plan['cases'][name]
    assert sha(ROOT/case['mesh'])==case['mesh_sha256']
    assert sha(folder/'case.cfg')==case['cfg_sha256']
    h=rows(folder/'history.csv') if (folder/'history.csv').exists() else []
    sets=[]
    for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')]:
        sets.append({int(p.stem.rsplit('_',1)[1]) for p in folder.glob(f'{prefix}_*.{ext}') if p.stem.rsplit('_',1)[1].isdigit()})
    common=set.intersection(*sets)&{int(x['Inner_Iter']) for x in h}
    selected=max(common) if common else None;matched=None
    if selected is not None:
        row=next(x for x in h if x['Inner_Iter']==selected);tail=[x for x in h if selected-99<=x['Inner_Iter']<=selected]
        vals={k:row[k] for k in ['CL','CD','rms[Rho]','rms[nu]']};assert all(math.isfinite(v) for v in vals.values())
        matched={'field_iteration':selected,'terminal_history_iteration':int(h[-1]['Inner_Iter']),**vals,
                 'last100_samples':len(tail),'CL_last100_range':max(x['CL'] for x in tail)-min(x['CL'] for x in tail),
                 'CD_last100_range':max(x['CD'] for x in tail)-min(x['CD'] for x in tail)}
    seal={'frozen_utc':now(),'contract_sha256':sha(CASE/'contract.json'),'flow_plan_sha256':sha(PLAN),
          'matched':matched,'native_status':read(folder/'solver.status.json'),'not_blind':True,'no_new_reference_scores_yet':True,
          'source_mesh_sha256':case['mesh_sha256'],'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in folder.iterdir() if p.is_file()},
          'physical_qualification_passed':False}
    save(target,seal);print('FROZEN',name,matched,flush=True)
    return seal


def run(name):
    plan=read(PLAN);c=plan['cases'][name];folder=ROOT/c['folder']
    assert sha(CASE/'contract.json')==plan['contract_sha256']
    assert sha(ROOT/c['mesh'])==c['mesh_sha256'] and sha(folder/'case.cfg')==c['cfg_sha256']
    if name!='smoke':
        smoke=read(CASE/(PREFIX+'smoke')/'prediction_frozen.json');assert smoke['native_status']['exit_code']==0 and smoke['matched'] is not None
    exe=read(ROOT/'work/setup/su2_install.json')['executable']
    env=dict(os.environ,OMP_NUM_THREADS=str(plan['threads']),OMP_WAIT_POLICY='PASSIVE')
    print('START',name,memory(),flush=True)
    status=run_native([exe,'case.cfg','-t',str(plan['threads'])],folder,'solver',c['max_seconds'],env,memory_cap_gib=2.5)
    print('END',name,status,flush=True)
    seal=freeze(name)
    if name=='smoke':assert status['exit_code']==0 and seal['matched'] is not None,'Native source config rejected; preserve failure before revision'


if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='all':
        for name in ['smoke','coarse','medium','fine']:run(name)
    else:run(action)
