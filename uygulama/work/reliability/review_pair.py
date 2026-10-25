"""Evaluate only after both predictions are frozen; retain every experimental point."""
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from linear_pair import ROOT, PROJECT, RUN, REPORT, cfg, sha, read, save, history, now
from advisor import iterative_gate, choose_next, verify_evidence


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    assert not REPORT.exists(), 'Keep all evaluations versioned'
    contract=read(RUN/'contract.json')
    comparator=load('source_m6_comparator',ROOT/'work/validation/compare_m6.py')
    integrator=load('source_force_integrator',ROOT/'work/m6_followup/force_integral.py')
    groups,sign_checks=comparator.experimental()
    results={}
    frozenfiles={}
    for name in contract['order']:
        folder=RUN/name;sealpath=folder/'prediction_frozen.json';seal=read(sealpath)
        errors=verify_evidence(ROOT,seal['files_sha256'])
        assert not errors, errors
        assert seal['contract_sha256']==sha(RUN/'contract.json')
        frozenfiles[str(sealpath.relative_to(ROOT))]=sha(sealpath)
        frozenfiles.update(seal['files_sha256'])
        matched=seal['matched'];run=read(folder/'run_status.json')
        if matched is None:
            results[name]={'run':run,'matched':None,'Cp':None,'force_integral':None}
            continue
        n=matched['field_iteration']
        evaluation=PROJECT/f'data/m6_linear_pair_20261024/{name}'
        evaluation.mkdir(parents=True)
        shutil.copyfile(folder/f'surface_flow_{n:06d}.vtu',evaluation/'surface_flow.vtu')
        cp,curves,_=comparator.comparison({'folder':str(evaluation),'grid':name},groups)
        alternate,_,_=comparator.comparison({'folder':str(evaluation),'grid':name},groups,True)
        forces=integrator.integrate(folder/'mesh.su2',folder/f'surface_flow_{n:06d}.vtu',folder/'case.cfg',matched)
        gate=iterative_gate(history(folder/'history.csv'),n,contract['thresholds_unchanged'])
        results[name]={'run':run,'matched':matched,'raw_recomputed_iteration':gate,'Cp':cp,
                       'alternate_eta0p96':alternate,'force_integral':forces,
                       'experimental_sections_passed':sum(s['Cp_RMSE'] < contract['thresholds_unchanged']['per_section_Cp_RMSE_max'] for s in cp['sections']),
                       'all_271_points_kept':sum(s['points'] for s in cp['sections'])==271,
                       'minimum_qualification_passed':False}
    # Pair comparability is recomputed from bytes and full config, not a user flag.
    configs=[cfg(RUN/f'{name}/case.cfg') for name in contract['order']]
    differences=[k for k in configs[0].keys()|configs[1].keys() if configs[0].get(k)!=configs[1].get(k)]
    comparable=all(results[n]['run']['exit_code']==0 and results[n]['matched'] is not None
                   and results[n]['matched']['field_iteration']==999 for n in contract['order'])
    comparable &= differences==['LINEAR_SOLVER_ITER']
    comparable &= sha(RUN/'lin10/mesh.su2')==sha(RUN/'lin40/mesh.su2')
    comparable &= sha(RUN/'lin10/seed.dat')==sha(RUN/'lin40/seed.dat')
    benefit=results['lin10']['matched']['rms[Rho]']-results['lin40']['matched']['rms[Rho]'] if comparable else None
    pair={'comparable':bool(comparable),'additional_log10_reduction':benefit,
          'registered_effect_size':contract['diagnostic_effect_rule']['meaningful_extra_log10_reduction'],
          'effect_passed':comparable and benefit>=contract['diagnostic_effect_rule']['meaningful_extra_log10_reduction'],
          'only_config_difference':differences,
          'time_ratio_40_over10':results['lin40']['run']['seconds']/results['lin10']['run']['seconds'],
          'claim_limit':'One fixed seed/mesh, one run order; no universal causation, no timing confidence interval.'}
    state={'evidence_errors':[],'checkpoint_complete':comparable,
           'iteration_passed':results['lin10'].get('raw_recomputed_iteration',{}).get('passed',False),
           'linear_cap_saturated':True,'linear_pair':pair,'regional_mesh_passed':False,
           'three_grid_passed':False,'farfield_passed':False,'experiment_passed':False,
           'remaining_native_runs':0}
    report={'reviewed_utc':now(),'project_id':'proje-e9319baef1','contract_sha256':sha(RUN/'contract.json'),
            'results':results,'pair':pair,'experiment_points':271,'sign_checks':sign_checks,
            'recommendation':choose_next(state),'minimum_qualification_passed':False,
            'source_frozen_integrity_after':not verify_evidence(ROOT,read(PROJECT/'reports/m6_wallnormal_prediction_frozen_20261024_v3.json')['files_sha256']),
            'not_blind':True,'scope':contract['scope'],
            'open_gates':['M6 iterative density','full regional BL/TE/tip/wake resolution','systematic three meshes','farfield sensitivity','experimental Cp'],
            'review_code_sha256':sha(__file__)}
    save(REPORT,report)
    evidence={str((RUN/'contract.json').relative_to(ROOT)):sha(RUN/'contract.json'),
              str(REPORT.relative_to(ROOT)):sha(REPORT),**frozenfiles}
    save(PROJECT/'data/reliability_case.json',{
        'schema_version':1,'project_id':'proje-e9319baef1','contract':str((RUN/'contract.json').relative_to(ROOT)),
        'cases':[{'name':n,'folder':str((RUN/n).relative_to(ROOT))} for n in contract['order']],
        'preselected_case':'lin10','evidence_sha256':evidence,'state':state,
        'scope':'Saved engineering evidence audit; no automatic native runs or physical approval.'})
    # Plot actual histories of both equations and monitored engineering quantities.
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for name,color in [('lin10','#177e8a'),('lin40','#bd6238')]:
        rows=history(RUN/f'{name}/history.csv');x=[r['Inner_Iter'] for r in rows]
        for ax,key in zip(axs.ravel(),['rms[Rho]','LinSolRes','CL','CD']):
            ax.plot(x,[r[key] for r in rows],label=name,color=color,lw=1)
            ax.set(xlabel='Additional nonlinear iteration',ylabel=key);ax.grid(alpha=.2)
    axs[0,0].axhline(contract['thresholds_unchanged']['density_log10_max'],color='#555',ls='--',label='existing density gate')
    axs[0,0].legend();fig.suptitle('Same mesh, physics and restart; only linear cap changes')
    fig.tight_layout();fig.savefig(PROJECT/'plots/m6_linear_pair_20261024.png',dpi=150);plt.close(fig)
    print(json.dumps({'pair':pair,'iteration':{n:results[n]['raw_recomputed_iteration'] for n in results},
                      'Cp_RMSE':{n:results[n]['Cp']['all_point_Cp_RMSE'] for n in results},
                      'recommendation':report['recommendation']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
