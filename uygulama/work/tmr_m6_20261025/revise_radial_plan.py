"""Record a mesh-precondition correction before any flow solution or score."""
from common import ROOT,CASE,TASK,read,save,sha,now,memory
import shutil

original=CASE/'contract.json'
retained=CASE/'contract_v1_before_mesh_precondition.json'
assert not retained.exists()
shutil.copyfile(original,retained)
failure=CASE/'generator_smoke/generator.log'
assert 'No grids generated' in failure.read_text()
contract=read(original)
contract['version']='tmr_sharp_20261025_v2_radial_precondition'
contract['revision']={'created_utc':now(),'prior_contract_sha256':sha(retained),'evidence_log_sha256':sha(failure),
    'observed':'Source generator requires 59 wall-normal layers for smoke geometry and given y+ design; requested32 rejected despite exit0.',
    'changes':{'planned_fine_nre':{'before':64,'after':128,'reason':'Provide radial cells beyond the internally estimated BL layers; source recommends increasing radial count.'},
               'planned_fine_span_elements':{'before':32,'after':16,'reason':'Pre-solution RAM budget: ~3.5GiB currently available; shift available mesh budget into required radial and chordwise resolution.'}},
    'not_a_causal_flow_comparison':True,'physical_conditions_and_acceptance_unchanged':True,
    'scope_warning':'This bounded family may be too coarse spanwise; a three-grid family alone is not sufficient validation.'}
contract['planned_fine_mesh']['nre']=128
contract['planned_fine_mesh']['nnodes_cylinder_input']=16
contract['memory_at_revision']=memory()
save(original,contract)
task=read(TASK);task['contract_sha256']=sha(original);save(TASK,task)
print(contract['revision'])
