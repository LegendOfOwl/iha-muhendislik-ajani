"""Check actual solver physics against immutable inputs; distinguish defaults from overrides."""
from pathlib import Path
import json,sys,hashlib,re
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation';OUT=ROOT/'outputs/projects/proje-15cce2de02'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def parse(p):
 result={}
 for line in p.read_text().splitlines():
  line=line.split('%')[0].strip()
  if '=' in line:
   k,v=line.split('=',1);result[k.strip()]=v.strip()
 return result
conditions=load(BASE/'analysis_input/conditions.json')
expected={'MACH_NUMBER':conditions['Mach'],'AOA':conditions['alpha_deg'],'REYNOLDS_NUMBER':conditions['Re_chord'],'REYNOLDS_LENGTH':conditions['chord_m'],'FREESTREAM_TEMPERATURE':conditions['T_K'],'REF_LENGTH':1.,'REF_AREA':1.}
fixed={'SOLVER':'RANS','KIND_TURB_MODEL':'SA','SA_OPTIONS':'NONE','INIT_OPTION':'REYNOLDS','FREESTREAM_OPTION':'TEMPERATURE_FS','VISCOSITY_MODEL':'SUTHERLAND','MARKER_HEATFLUX':'( AIRFOIL, 0.0 )','MARKER_FAR':'( FARFIELD )'}
default={'SYSTEM_MEASUREMENTS':'SI','FLUID_MODEL':'STANDARD_AIR','KIND_TRANS_MODEL':'NONE','FREESTREAM_NU_FACTOR':'3.0','SIDESLIP_ANGLE':'0.0'}
keys=list(expected)+list(fixed)+list(default)+['GAMMA_VALUE','GAS_CONSTANT','MU_REF','MU_T_REF','SUTHERLAND_CONSTANT','FREESTREAM_TURB2LAMVISCRATIO','REF_ORIGIN_MOMENT_X','REF_ORIGIN_MOMENT_Y','REF_ORIGIN_MOMENT_Z','REF_DIMENSIONALIZATION']
names=sys.argv[1:] or ['coarse','medium','fine','medium_far','v2_r2_coarse','v2_r2_medium','v2_r2_fine','v2_r2_medium_far']
rows=[]
for name in names:
 p=OUT/'simulations'/name/'case.cfg'
 if not p.exists():continue
 cfg=parse(p);effective={k:cfg.get(k,default.get(k)) for k in keys};checks={k:k in cfg and abs(float(cfg[k])-v)<1e-10*max(1,abs(v)) for k,v in expected.items()}
 checks.update({k:cfg.get(k)==v for k,v in fixed.items()})
 checks['unchanged_SA_nu_factor']=float(effective['FREESTREAM_NU_FACTOR'])==3.
 log=(p.parent/'solver.log').read_text(errors='replace') if (p.parent/'solver.log').exists() else ''
 dimensional={}
 for key in ['Static Pressure','Density','Temperature','Velocity Magnitude','Viscosity']:
  lines=[line for line in log.splitlines() if re.match(r'^\|\s*'+re.escape(key)+r'\s*\|',line)]
  if lines:
   try:dimensional[key]=float(lines[0].split('|')[2])
   except ValueError:pass
 rows.append({'case':name,'config_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'effective_physics':effective,'inherited_defaults':{k:v for k,v in default.items() if k not in cfg},'checks':checks,'all_checked_inputs_match_contract':all(checks.values()),'reported_dimensional_freestream':dimensional})
baseline=rows[0]['effective_physics']
for row in rows:row['differences_from_v1_baseline']={k:[baseline[k],row['effective_physics'][k]] for k in keys if baseline[k]!=row['effective_physics'][k]}
result={'conditions_sha256':hashlib.sha256((BASE/'analysis_input/conditions.json').read_bytes()).hexdigest(),'cases':rows,'default_source':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/CConfig.cpp','SA_nu_factor_note':'FREESTREAM_NU_FACTOR default3.0 verified in exact v8.5.0 CConfig.cpp; v2 writes it explicitly. FREESTREAM_TURB2LAMVISCRATIO10 is not a substitute for the SA nu-factor.','pressure_note':'INIT_OPTION=REYNOLDS and TEMPERATURE_FS determine density/pressure from Re, chord and temperature; physical solver log tables recorded, not fitting pressure to experiment.','limitations':'Config/log checks verify declared implementation inputs. They do not prove that a turbulence model reproduces experiment or that all compiler defaults were independently audited.'}
(OUT/'reports/review_physical_config_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps({r['case']:{'match':r['all_checked_inputs_match_contract'],'physics_differences':r['differences_from_v1_baseline']} for r in rows},indent=2))
