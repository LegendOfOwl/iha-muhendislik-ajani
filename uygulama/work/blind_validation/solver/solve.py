from pathlib import Path
import os,sys,json,subprocess,time,hashlib,shutil,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def config(folder,iterations=5000,restart=False,cfl=3.):
    cond=json.loads((ROOT/'work/blind_validation/analysis_input/conditions.json').read_text())
    # Preserve numerical-template choices unless an override is recorded below.
    text=(ROOT/'work/validation/sources/turb_SA_RAE2822.cfg').read_text()
    d={}
    for line in text.splitlines():
        line=line.split('%')[0].strip()
        if '=' in line:
            k,v=line.split('=',1);d[k.strip()]=v.strip()
    original=d.copy()
    # Remove adjoint/deformation/optimization-only fields; this is fixed geometry direct RANS.
    for k in list(d):
        if k.startswith(('ADJ_','DV_','OPT_','DEFINITION_DV','HOLD_GRID','OBJECTIVE_')) or k in ['FROZEN_VISC_CONT','CFL_REDUCTION_ADJFLOW','TIME_DISCRE_ADJFLOW','CONV_NUM_METHOD_ADJFLOW']:d.pop(k)
    d.update({'SOLVER':'RANS','KIND_TURB_MODEL':'SA','SA_OPTIONS':'NONE','KIND_TRANS_MODEL':'NONE','MATH_PROBLEM':'DIRECT','SYSTEM_MEASUREMENTS':'SI','INIT_OPTION':'REYNOLDS','FREESTREAM_OPTION':'TEMPERATURE_FS',
    'RESTART_SOL':'YES' if restart else 'NO','MACH_NUMBER':str(cond['Mach']),'AOA':str(cond['alpha_deg']),'REYNOLDS_NUMBER':str(cond['Re_chord']),'REYNOLDS_LENGTH':str(cond['chord_m']),'FREESTREAM_TEMPERATURE':str(cond['T_K']),
    'FREESTREAM_TURB2LAMVISCRATIO':'10.0','GAMMA_VALUE':'1.4','GAS_CONSTANT':'287.058','VISCOSITY_MODEL':'SUTHERLAND','MU_REF':'1.716E-5','MU_T_REF':'273.15','SUTHERLAND_CONSTANT':'110.4','REF_DIMENSIONALIZATION':'FREESTREAM_VEL_EQ_ONE',
    'CFL_NUMBER':str(cfl),'CFL_ADAPT':'YES','CFL_ADAPT_PARAM':f'( 0.5, 1.1, 1.0, {cfl}, 0.1, 100 )','ITER':str(iterations),'LINEAR_SOLVER':'FGMRES','LINEAR_SOLVER_ERROR':'0.05','LINEAR_SOLVER_ITER':'15','LINEAR_SOLVER_PREC':'ILU',
    'MGLEVEL':'3','LIMITER_ITER':'999999','CONV_FIELD':'RMS_DENSITY','CONV_RESIDUAL_MINVAL':'-10','CONV_STARTITER':'500','CONV_CAUCHY_EPS':'1E-12',
    'MESH_FILENAME':'mesh.su2','CONV_FILENAME':'history','SOLUTION_FILENAME':'restart_flow','RESTART_FILENAME':'restart_flow','VOLUME_FILENAME':'flow','SURFACE_FILENAME':'surface_flow','TABULAR_FORMAT':'CSV',
    'OUTPUT_FILES':'( RESTART, PARAVIEW, SURFACE_PARAVIEW, SURFACE_CSV )','OUTPUT_WRT_FREQ':'( 200, 200, 200, 200 )','WRT_RESTART_OVERWRITE':'YES','WRT_SURFACE_OVERWRITE':'YES','WRT_VOLUME_OVERWRITE':'YES','WRT_FORCES_BREAKDOWN':'YES',
    'VOLUME_OUTPUT':'( COORDINATES, SOLUTION, PRIMITIVE, RESIDUAL )','HISTORY_OUTPUT':'( ITER, RMS_RES, AERO_COEFF )','SCREEN_OUTPUT':'( INNER_ITER, RMS_DENSITY, RMS_NU_TILDE, LIFT, DRAG )','SCREEN_WRT_FREQ_INNER':'100','HISTORY_WRT_FREQ_INNER':'1'})
    (folder/'case.cfg').write_text('\n'.join(f'{k}= {v}' for k,v in d.items())+'\n')
    rationale={'FREESTREAM_TEMPERATURE':'authoritative physical conditions, replacing template temperature','MACH_NUMBER':'authoritative physical conditions','AOA':'authoritative physical conditions; fixed, no lift trim','REYNOLDS_NUMBER':'authoritative physical conditions','CFL_NUMBER':'bounded moderate CFL, protects stiff wall layers','CFL_ADAPT':'bounded automatic decrease/increase; upper bound stays moderate','LINEAR_SOLVER':'robust Krylov solve on anisotropic wall mesh','LINEAR_SOLVER_ERROR':'stronger linear reduction than template','LINEAR_SOLVER_ITER':'allow stronger reduction than template 3','CONV_FIELD':'residual stop rather than premature force Cauchy exit','CONV_RESIDUAL_MINVAL':'-10 target to give strict force-history screens opportunity; screens remain -8/CL/CD','OUTPUT_WRT_FREQ':'checkpoints every 200, preserving fields on timeout','SA_OPTIONS':'explicit SU2 v8.5 baseline NONE, without ft2; no transition model','FREESTREAM_TURB2LAMVISCRATIO':'explicit source-template default closure assumption; not supplied experiment datum','GAS_CONSTANT':'SU2 ideal-air constant, explicit constitutive assumption','GAMMA_VALUE':'SU2 ideal-air ratio, explicit constitutive assumption','REF_DIMENSIONALIZATION':'scale equations for conditioning, does not change dimensional flow'}
    overrides={k:{'template':original.get(k),'analysis':v,'reason':rationale.get(k,'explicit direct fixed-geometry analysis/output/restart control; physical boundary conditions and reference chord/area preserved')} for k,v in d.items() if original.get(k)!=v}
    (folder/'configuration_overrides.json').write_text(json.dumps({'numerical_source':'work/validation/sources/turb_SA_RAE2822.cfg','official_option_reference':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/config_template.cfg','overrides':overrides,'removed_only_inactive_fields':[k for k in original if k not in d]},indent=2))
def run(name,iterations=5000,budget=900,restart=False,cfl=3.):
    folder=OUT/'simulations'/name
    config(folder,iterations,restart,cfl)
    exe=Path(json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'])
    env=os.environ.copy();env['OMP_NUM_THREADS']='4';env['OMP_WAIT_POLICY']='PASSIVE'
    t=time.monotonic()
    with (folder/'solver.log').open('w',encoding='utf-8') as log:
        p=subprocess.Popen([str(exe),'case.cfg','-t','4'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,env=env)
        try:code=p.wait(timeout=budget);status='exited'
        except subprocess.TimeoutExpired:p.kill();p.wait();code=None;status='timeout_partial_preserved'
    meta={'status':status,'exit_code':code,'wall_seconds':time.monotonic()-t,'iteration_budget':iterations,'time_budget_seconds':budget,'threads':4,'config_sha256':sha(folder/'case.cfg'),'executable_sha256':sha(exe),'restart':restart}
    (folder/'run_status.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
if __name__=='__main__':run(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 5000,int(sys.argv[3]) if len(sys.argv)>3 else 900,'--restart' in sys.argv,float(sys.argv[4]) if len(sys.argv)>4 and sys.argv[4]!='--restart' else 3.)
