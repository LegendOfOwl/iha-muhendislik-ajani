"""Preselect a separate researched flux family, preserving every old run."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, importlib.util

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
    seal=OUT/'reports/v3_r4roe_family_plan_seal.json'
    assert not seal.exists(),'Do not replace a preselected plan'
    reference=OUT/'simulations/v3_cgrid_interfacer4_coarse_warmstart'
    name='v3_r4roe_coarse_warmstart';case=OUT/'simulations'/name
    assert not case.exists();case.mkdir()
    for f in ['mesh.su2','seed.dat']:shutil.copy2(reference/f,case/f)
    helper=load('fresh_case_helper',ROOT/'work/mesh_research/run_case.py')
    helper.prepare(name,case/'seed.dat',more={
        'CFL_ADAPT':'NO','CFL_NUMBER':'1.0','EXT_ITER_OFFSET':'0',
        'HISTORY_OUTPUT':'( ITER, RMS_RES, MAX_RES, AERO_COEFF, LINSOL, CFL_NUMBER )',
        'CONV_NUM_METHOD_FLOW':'ROE','MUSCL_FLOW':'YES',
        'SLOPE_LIMITER_FLOW':'VENKATAKRISHNAN'})
    parser=load('immutable_config_reader',ROOT/'work/blind_validation/solver_v2/solve.py')
    original=parser.readcfg(reference/'case.cfg');new=parser.readcfg(case/'case.cfg')
    difference={k:{'reference':original.get(k),'new':new.get(k)} for k in set(original)|set(new) if original.get(k)!=new.get(k)}
    assert set(difference)=={'CONV_NUM_METHOD_FLOW','MUSCL_FLOW','SLOPE_LIMITER_FLOW'},difference
    roles={level:'v3_r4roe_'+level+'_warmstart' for level in ['coarse','medium','fine']}
    plan={'created_utc':datetime.now(timezone.utc).isoformat(),'roles':roles,
          'fine_validation_preselected':True,'trial_type':'Separate numerical-method family; not a substitute for earlier JST fine role',
          'source':{'url':'https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf','pages':'23-24/33',
                    'sha256':sha(ROOT/'work/mesh_research/sources/SU2_AIAA2014_0243.pdf')},
          'rationale_record':'work/mesh_research/research_addendum_02.md',
          'rationale_sha256':sha(ROOT/'work/mesh_research/research_addendum_02.md'),
          'coarse_mesh_sha256':sha(case/'mesh.su2'),'coarse_seed_sha256':sha(case/'seed.dat'),
          'reference_case':reference.name,'config_difference':difference,
          'changed_policy':'Roe + second-order mean-flow MUSCL + Venkatakrishnan limiter; turbulence order unchanged',
          'physical_conditions_unchanged':True,'contract_sha256':sha(ROOT/'work/blind_validation/contract.json'),
          'minimum_qualification_passed':False}
    (case/'controlled_trial.json').write_text(json.dumps(plan,indent=2))
    seal.write_text(json.dumps(plan,indent=2))
    print(json.dumps({'case':name,'difference':difference,'seal':str(seal.relative_to(ROOT))},indent=2))
if __name__=='__main__':main()
