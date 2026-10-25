"""Reviewer-only evidence; no benchmark answers in the operational addendum."""
from linear_pair import ROOT, PROJECT, RUN, REPORT, TASK, read, save, sha, now


def main():
    target=ROOT/'outputs/data/agent_learning/reviewer_ledger_v2_20261025.json'
    assert not target.exists()
    pair=read(REPORT);curv=read(PROJECT/'reports/m6_curvature_v2_20261025.json')
    cfl=read(PROJECT/'reports/m6_cfl_feedback_20261025.json')
    def evidence(*paths):return [{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in paths]
    import sys
    sys.path.insert(0,str(ROOT/'work/agent'));from learning import instruction_snapshot
    ledger={'schema_version':2,'version':'2026-10-25.1','created_utc':now(),'role':'reviewer_only',
        'task_id':TASK.stem,'predecessor':evidence(ROOT/'outputs/data/agent_learning/reviewer_ledger_v1.json'),
        'operational_addendum':evidence(ROOT/'work/reliability/protocol_v1.json'),
        'baseline_instruction_snapshot':read(TASK)['agent_instruction_snapshot'],
        'updated_instruction_snapshot':instruction_snapshot(ROOT),
        'scope':'Guard reliability and scoped numerical discrimination; not unseen LLM improvement or physical qualification.',
        'expert_status':'not_established','new_unseen_engineering_test':False,
        'entries':[
            {'id':'R01','status':'confirmed_error','observed':'Missing json import raised after native child launch; the child was still running.',
             'enabling_behavior_inference':'Post-launch monitoring path was not exercised before the expensive run; behaviour cause beyond the visible code is unmeasured.',
             'correction':'Verify executable/PID creation time, adopt the same process handle with the original budget, capture actual OS exit; never relaunch in place.',
             'evidence':evidence(ROOT/'work/reliability/cfl_feedback_v1_wrapper_error.py',PROJECT/'simulations/m6_cfl_feedback_20261025/fixed/wrapper_recovery.json',PROJECT/'simulations/m6_cfl_feedback_20261025/fixed/run_status.json'),
             'counterexample':'A recovered child returning7 remains unsuccessful; measured by test_wrapper_recovery_preserves_nonzero_exit.',
             'promotion':'scoped_guard_tested','unseen_llm_behaviour_measured':False},
            {'id':'R02','status':'confirmed_prototype_limitation','observed':{'v1_max_selected_indicator':curv['v1_selected_max_indicator_warning'],
               'v2_eligible':curv['eligible'],'v2_masked':curv['not_eligible']},
             'enabling_behavior_inference':'Passing exact quadratic examples was insufficient for using local derivatives on the actual ill-conditioned/multiscale stencils.',
             'correction':'Convex support, fit condition, fit residual and two-stencil scale consistency are separate guards; uncertain cells remain visible and ineligible.',
             'evidence':evidence(PROJECT/'reports/m6_curvature_20261024.json',PROJECT/'reports/m6_curvature_v2_20261025.json',ROOT/'outputs/reports/reliability_method_tests.json'),
             'counterexample':'Inside a componentwise bounding box but outside the actual tetrahedral support must be rejected.',
             'promotion':'support_guard_tested_not_CFD_error_verified','unseen_llm_behaviour_measured':False},
            {'id':'L09-control','status':'disproven_diagnosis_scoped','hypothesis':'The active cap increase cures the nonlinear convergence deficit in this fixed M6 case.',
             'observation':pair['pair'],'interpretation':'Not supported by this equal-seed/equal-iteration control. This is not a universal statement about linear solvers.',
             'correction':'Do not sweep further cap values under the same unsupported diagnosis.',
             'evidence':evidence(REPORT,RUN/'contract.json'),'preserve_original_hypothesis':True},
            {'id':'CFL-control','status':'bounded_policy_test','observation':cfl['pair'],
             'interpretation':'Built-in bounded feedback tested once against fixedCFL with the same seed. No physical gate is relaxed.',
             'evidence':evidence(PROJECT/'reports/m6_cfl_feedback_20261025.json',PROJECT/'simulations/m6_cfl_feedback_20261025/contract.json')}
        ],'minimum_physical_qualification_passed':False}
    save(target,ledger)
    task=read(TASK);task['updated_agent_instruction_snapshot']=instruction_snapshot(ROOT)
    task['applied_reliability_policy']='2026-10-25.1';task['reviewer_ledger']=str(target.relative_to(ROOT));save(TASK,task)
    print(str(target))


if __name__=='__main__':main()
