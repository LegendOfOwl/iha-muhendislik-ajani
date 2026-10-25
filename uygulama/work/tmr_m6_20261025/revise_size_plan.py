from common import ROOT,CASE,TASK,read,save,sha,now
import shutil

old=CASE/'contract_v2_before_size_measurement.json'
assert not old.exists()
shutil.copyfile(CASE/'contract.json',old)
c=read(old)
# Exact source family count: six hemisphere sectors + six cylinder sectors.
# nr=16, span=16, radial=128 gives393216, above the registered320000 cap.
# Largest multiple-of4 nr satisfying the same cap is12. Do not change the cap.
valid=[nr for nr in range(4,17,4) if 6*nr*(nr+16)*128<=c['mesh_resource_budget']['fine_max_cells']]
nr=max(valid)
assert nr==12
c['version']='tmr_sharp_20261025_v3_size_budget'
c['revision_size']={'created_utc':now(),'prior_contract_sha256':sha(old),
    'observed':'First family393216 cells/396417 nodes exceeds registered320000 budget. Retained and not sent to CFD.',
    'source_count_formula':'Ncells=6*nr_gs*(nr_gs+span_elements)*radial_elements',
    'source_formula_matches_first_mesh':6*16*(16+16)*128==393216,
    'selected_largest_multiple_of4_under_original_cap':nr,
    'predicted_cells':6*nr*(nr+16)*128,'predicted_first_three_levels':[6*nr*(nr+16)*128//8**i for i in range(3)],
    'change':'nr_gs16 ->12 before any CFD, same source geometry/physics/y+ design and acceptance.',
    'physical_or_flow_causal_claim':False}
c['planned_fine_mesh']['nr_gs']=nr
save(CASE/'contract.json',c)
t=read(TASK);t['contract_sha256']=sha(CASE/'contract.json');save(TASK,t)
print(c['revision_size'])
