from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=OUT/'reports/v3_research_plan_seal.json'
    if dest.exists():raise RuntimeError('Do not overwrite a plan seal.')
    paths=[ROOT/'work/blind_validation/contract.json',ROOT/'work/mesh_research/research_plan.md',ROOT/'work/mesh_research/cgrid/build_cgrid.py',ROOT/'work/mesh_research/reference/run_reference_control.py',ROOT/'work/mesh_research/run_case.py']
    a={'created_utc':datetime.now(timezone.utc).isoformat(),'role':'Research-motivated continuation, main agent knows v1/v2 experiment scores; not independent blind validation.',
       'source_grid_role':'diagnostic only; run already in progress, no Cp comparison made yet',
       'new_family_roles':{'coarse':'v3_cgrid_coarse','medium':'v3_cgrid_medium','fine_validation':'v3_cgrid_fine'},
       'scales':[2/3,1,1.5],'same_geometry_curve_sha256':'050ee43ead96df3cbc2a34649cf06c0839ed6fe47ae8aaf4955744d19f49cf5a',
       'initial_family_numerics':'v2 medium settings, uniform freestream. If a case stagnates, preserve it and change one numerical policy in a separately named attempt.',
       'minimum_acceptance':False,'gates':'All existing contract gates remain conjunctive. Missing farfield or regional sensitivity remains open.',
       'sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths}}
    dest.write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
if __name__=='__main__':main()
