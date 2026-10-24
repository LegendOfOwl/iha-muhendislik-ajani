"""Single-change reconstruction diagnostic, never a validation substitute."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,importlib.util
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    src=OUT/'simulations/v3_r4roe_coarse_warmstart';dst=OUT/'simulations/v3_r4roe_coarse_firstorder_control'
    assert not dst.exists();dst.mkdir()
    for name in ['mesh.su2','seed.dat']:shutil.copy2(src/name,dst/name)
    parser=load('old_config_readonly',ROOT/'work/blind_validation/solver_v2/solve.py')
    old=parser.readcfg(src/'case.cfg');new=dict(old);new['MUSCL_FLOW']='NO'
    assert [k for k in new if new[k]!=old[k]]==['MUSCL_FLOW']
    (dst/'case.cfg').write_text('\n'.join(f'{k}= {v}' for k,v in new.items())+'\n')
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'reference_case':src.name,
            'changed':{'MUSCL_FLOW':{'old':'YES','new':'NO'}},'same_initial_seed':sha(src/'seed.dat')==sha(dst/'seed.dat'),
            'mesh_sha256':sha(dst/'mesh.su2'),'seed_sha256':sha(dst/'seed.dat'),'config_sha256':sha(dst/'case.cfg'),
            'contract_sha256':sha(ROOT/'work/blind_validation/contract.json'),
            'rationale':'work/mesh_research/research_addendum_03.md','rationale_sha256':sha(ROOT/'work/mesh_research/research_addendum_03.md'),
            'scope':'First-order reconstruction-isolation diagnostic only; cannot replace second-order fine validation',
            'minimum_qualification_passed':False}
    (dst/'controlled_trial.json').write_text(json.dumps(record,indent=2))
    (dst/'configuration_overrides.json').write_text(json.dumps(record,indent=2))
    (OUT/'reports/v3_firstorder_control_preseal.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
