"""Controlled enabled-MG policy test on the completed coarse source baseline."""
from common import ROOT,BASE,CASE,PROJECT,read,save,sha,now,run_native
from run_flow import rows
import os
import re


def main():
    folder=CASE/'coarse_MG2_control';assert not folder.exists();folder.mkdir()
    baseline=CASE/'flow_v2_coarse';seal=read(baseline/'prediction_frozen.json')
    assert seal['matched']['field_iteration']==3999
    text=(baseline/'case.cfg').read_text();updated,n=re.subn(r'(?m)^MGLEVEL= 0$', 'MGLEVEL= 2',text);assert n==1
    (folder/'case.cfg').write_text(updated,encoding='utf-8')
    configdiff=[(a,b) for a,b in zip(text.splitlines(),updated.splitlines()) if a!=b]
    assert configdiff==[('MGLEVEL= 0','MGLEVEL= 2')]
    plan={'created_utc':now(),'source_case_contract_sha256':sha(CASE/'contract.json'),
          'baseline_seal_sha256':sha(baseline/'prediction_frozen.json'),'control_cfg_sha256':sha(folder/'case.cfg'),
          'baseline_cfg_sha256':sha(baseline/'case.cfg'),'only_input_config_change':configdiff,
          'same_source_mesh_sha256':read(CASE/'flow_plan_v2.json')['cases']['coarse']['mesh_sha256'],
          'same_initialization':'RESTART_SOL=NO; same freestream state, mesh, physics and numerical settings except MGLEVEL',
          'effect':'Compare density log10 at matched history iteration1000; MG improves by at least0.3 log10 and is finite.',
          'effect_log10_min':.3,'common_iteration':1000,'budget_s':300,'threads':4,'max_iterations':4000,
          'scope':'Enabling the complete built-in two-level agglomeration policy; coarse operators/smoothers are part of the treatment, not a pure isolated scalar.',
          'timing_comparison_not_controlled':'Other source-family run may execute concurrently; no speedup claim from wall time.',
          'physical_acceptance_unchanged':True}
    save(folder/'control_contract.json',plan)
    env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
    exe=read(ROOT/'work/setup/su2_install.json')['executable']
    result=run_native([exe,'case.cfg','-t','4'],folder,'solver',300,env,memory_cap_gib=.5)
    h=rows(folder/'history.csv') if (folder/'history.csv').exists() else []
    baseline_h=rows(baseline/'history.csv');selected=1000
    b=next(x for x in baseline_h if x['Inner_Iter']==selected)
    current=next((x for x in h if x['Inner_Iter']==selected),None)
    gain=b['rms[Rho]']-current['rms[Rho]'] if current else None
    # Freeze all failed and complete control outputs before any reference assessment.
    files={str(p.relative_to(ROOT)):sha(p) for p in folder.iterdir() if p.is_file()}
    save(folder/'prediction_frozen.json',{'frozen_utc':now(),'files_sha256':files,'native_status':result,
          'not_blind':True,'new_reference_score_read':False,'physical_qualification_passed':False,
          'registered_common_iteration':selected,'control_at_common_iteration':current,'baseline_at_common_iteration':b,
          'additional_density_log10_reduction':gain,'effect_passed':bool(gain is not None and gain>=.3)})
    save(PROJECT/'reports/tmr_MG_control_20261025.json',{'contract_sha256':sha(folder/'control_contract.json'),
         'native_status':result,'compared_iteration':selected,'baseline_density_log10':b['rms[Rho]'],
         'control_density_log10':current['rms[Rho]'] if current else None,'additional_log10_reduction':gain,
         'effect_passed':bool(gain is not None and gain>=.3),'minimum_physical_qualification_passed':False,
         'terminal_history':h[-1] if h else None,'no_timing_speedup_claim':True})
    print({'native':result,'common_iteration_gain':gain,'effect_passed':bool(gain is not None and gain>=.3)},flush=True)


if __name__=='__main__':main()
