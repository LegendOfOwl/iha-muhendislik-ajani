"""Freeze decision limits before any new native CFD; bind build identity later."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now

def main():
    target=BASE/'method_design.json';assert not target.exists()
    old=ROOT/'outputs/simulations/flatplate_SAneg_20261025_v1'
    mesh=old/'meshes/fine.su2';seed=old/'linelet_20261026_v1/linelet/seed.dat'
    source=old/'linelet_20261026_v1/linelet/case.cfg'
    probe=ROOT/'outputs/reports/residual_probe_20261026.json';p=read(probe)
    assert p['map_authorized'] and p['all_five_RMS_and_MAX_match']
    csv=ROOT/p['all_points_csv']
    c={'normalization':'SI2D','iterations':200,'comparison_iteration':199,
       'last_window_samples':100,'CD_window_range_max':1e-7,
       'rms_components':['Rho','RhoU','RhoV','RhoE','nu'],
       'reproduction_max_abs_log10_difference':.03,
       'reproduction_final_CD_abs_difference_max':1e-8,
       'reproduction_Krylov_relative_difference_max':.05,
       'membership_expected_nodes':52689,'coordinate_mapping_max_m':2e-7,
       'density_gain_min':.3,'SA_worsening_max':.1,'work_ratio_max':1.5,
       'elapsed_ratio_max':1.5,'Rho_share_gain_min':1e-12,
       'reference_cap':32,'candidate_cap':256}
    record={'registered_utc':now(),'state':'limits_frozen; actual pristine source identity must be bound before CFD',
       'not_blind':True,'purpose':'One line-length-cap mechanism, with pristine source-build reproduction before modification.',
       'decision_contract_limits':c,
       'tolerance_basis':{'reproduction_log10':'.03 is an operational numerical-reproduction screen, one tenth of the .3 effect threshold; not a universal floating-point or physical accuracy bound.',
          'reproduction_CD':'1e-8 absolute difference, below the unchanged1e-7 last-window stability screen.',
          'reproduction_Krylov':'.05 relative combined flow+SA work; compiler differences cannot be silently assigned to the cap.',
          'effect':'.3 density gain, <=.1 SA worsening, <=1.5 Krylov and observed elapsed ratios retained from the preceding registered mechanism test.',
          'coverage':'Strictly greater old-RHS coverage by >1e-12 numerical noise floor, plus increased native member count; no exact line ID claims.'},
       'inputs':{str(x.relative_to(ROOT)):sha(x) for x in [mesh,seed,source,probe,csv,old/'contract.json']},
       'mesh':str(mesh.relative_to(ROOT)),'seed':str(seed.relative_to(ROOT)),
       'parent_config':str(source.relative_to(ROOT)),'fixed_RHS_csv':str(csv.relative_to(ROOT)),
       'common_config_changes':{'VOLUME_OUTPUT':'Add LINELET to COORDINATES,SOLUTION,PRIMITIVE in all three arms; old200 field has no Linelet array.',
                               'MESH_FILENAME':'Path alias to the exact same mesh; no physical/numerical input change.'},
       'arms':['fresh release32','fresh pristine source32','fresh source256 only after accepted pristine reproduction'],
       'native_resources':read(BASE/'setup_plan.json')['native_resources'],
       'source_plan_sha256':sha(BASE/'setup_plan.json'),
       'no_automatic_extension_or_sweep':True,'old_fine3999_role_preserved':True,
       'physical_qualification_passed':False,'M6_qualification_passed':False,'LLM_improvement_demonstrated':False}
    save(target,record);print({'design':str(target.relative_to(ROOT)),'sha256':sha(target)},flush=True)

if __name__=='__main__':main()
