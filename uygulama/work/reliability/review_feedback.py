"""Evaluate the registered fixed/feedback pair after frozen predictions."""
from linear_pair import ROOT, PROJECT, TASK, cfg, read, save, sha, history, now
from cfl_feedback import RUN, REPORT
from review_pair import load
from advisor import verify_evidence, choose_next
import shutil


def main():
    assert not REPORT.exists()
    contract=read(RUN/'contract.json')
    task=read(TASK)
    project_manifest=task['project_manifest']
    assert sha(ROOT/project_manifest)==task['input_sha256'][project_manifest], 'Project context changed since task start'
    comparator=load('m6_compare',ROOT/'work/validation/compare_m6.py')
    integrator=load('m6_integral',ROOT/'work/m6_followup/force_integral.py')
    groups,signs=comparator.experimental()
    results={};evidence={str((RUN/'contract.json').relative_to(ROOT)):sha(RUN/'contract.json'),
                        project_manifest:task['input_sha256'][project_manifest]}
    for name in contract['order']:
        folder=RUN/name;sealpath=folder/'prediction_frozen.json';seal=read(sealpath)
        assert not verify_evidence(ROOT,seal['files_sha256'])
        assert seal['contract_sha256']==sha(RUN/'contract.json')
        evidence.update(seal['files_sha256']);evidence[str(sealpath.relative_to(ROOT))]=sha(sealpath)
        run=read(folder/'run_status.json');matched=seal['matched']
        rows=history(folder/'history.csv')
        if matched is None:
            results[name]={'native_run':run,'matched':None,'Cp':None,'iterative_gate':seal['iterative_gate']}
            continue
        selected=matched['field_iteration'];review=PROJECT/f'data/m6_cfl_feedback_20261025/{name}'
        review.mkdir(parents=True)
        shutil.copyfile(folder/f'surface_flow_{selected:06d}.vtu',review/'surface_flow.vtu')
        cp,_,_=comparator.comparison({'folder':str(review),'grid':name},groups)
        alternate,_,_=comparator.comparison({'folder':str(review),'grid':name},groups,True)
        force=integrator.integrate(folder/'mesh.su2',folder/f'surface_flow_{selected:06d}.vtu',folder/'case.cfg',matched)
        results[name]={'native_run':run,'matched':matched,'iterative_gate':seal['iterative_gate'],'Cp':cp,'alternate_eta0p96':alternate,
            'force_integral':force,'CFL_range':[min(r['Min CFL'] for r in rows),max(r['Max CFL'] for r in rows)],
            'linear_work_total':sum(r['Linear_Solver_Iterations'] for r in rows),
            'experimental_sections_passed':sum(s['Cp_RMSE']<contract['thresholds_unchanged']['per_section_Cp_RMSE_max'] for s in cp['sections']),
            'all_271_points_kept':sum(s['points'] for s in cp['sections'])==271,
            'minimum_qualification_passed':False}
    configs=[cfg(RUN/n/'case.cfg') for n in contract['order']]
    diff=[k for k in configs[0].keys()|configs[1].keys() if configs[0].get(k)!=configs[1].get(k)]
    comparable=all(results[n]['native_run']['exit_code']==0 and results[n]['matched'] is not None
                   and results[n]['matched']['field_iteration']==599 for n in results)
    comparable &= diff==['CFL_ADAPT']
    comparable &= sha(RUN/'fixed/mesh.su2')==sha(RUN/'adaptive/mesh.su2')
    comparable &= sha(RUN/'fixed/seed.dat')==sha(RUN/'adaptive/seed.dat')
    benefit=results['fixed']['matched']['rms[Rho]']-results['adaptive']['matched']['rms[Rho]'] if comparable else None
    pair={'comparable':bool(comparable),'only_config_difference':diff,'additional_log10_reduction':benefit,
          'effect_passed':bool(comparable and benefit>=contract['diagnostic_effect_log10_min']),
          'time_ratio_adaptive_over_fixed':results['adaptive']['native_run']['seconds']/results['fixed']['native_run']['seconds'],
          'not_timing_benchmark':True}
    state={'checkpoint_complete':bool(comparable),'iteration_passed':results['adaptive']['iterative_gate']['passed'],
           'linear_cap_saturated':False,'linear_pair':{'comparable':True,'effect_passed':False},
           'regional_mesh_passed':False,'three_grid_passed':False,'farfield_passed':False,'independent_integral_passed':False,
           'experiment_passed':False,'remaining_native_runs':0}
    report={'reviewed_utc':now(),'project_id':'proje-e9319baef1','contract_sha256':sha(RUN/'contract.json'),
            'pair':pair,'results':results,'sign_checks':signs,'experiment_points':271,'not_blind':True,
            'minimum_qualification_passed':False,'recommendation':choose_next(state),
            'open_gates':['regional full BL/TE/tip/wake resolution','three systematic meshes','farfield sensitivity','experimental Cp'],
            'scope':contract['scope'],'code_sha256':sha(__file__)}
    save(REPORT,report);evidence[str(REPORT.relative_to(ROOT))]=sha(REPORT)
    save(PROJECT/'data/reliability_case_after_feedback.json',{
        'schema_version':1,'project_id':'proje-e9319baef1','contract':str((RUN/'contract.json').relative_to(ROOT)),
        'cases':[{'name':n,'folder':str((RUN/n).relative_to(ROOT))} for n in contract['order']],
        'preselected_case':'adaptive','evidence_sha256':evidence,'state':state,
        'scope':'Latest registered numerical control, fixed before comparison. No physical qualification.'})
    # Keep the prior specification version, switch the registered current audit explicitly.
    current=PROJECT/'data/reliability_case.json';previous=PROJECT/'data/reliability_case_before_feedback.json'
    assert not previous.exists();shutil.copyfile(current,previous)
    shutil.copyfile(PROJECT/'data/reliability_case_after_feedback.json',current)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for name,color in [('fixed','#177e8a'),('adaptive','#bd6238')]:
        rows=history(RUN/name/'history.csv');x=[r['Inner_Iter'] for r in rows]
        for ax,key in zip(axes.ravel(),['rms[Rho]','Avg CFL','CL','CD']):
            ax.plot(x,[r[key] for r in rows],color=color,label=name,lw=1);ax.set(xlabel='Additional iteration',ylabel=key);ax.grid(alpha=.2)
    axes[0,0].axhline(-7,color='#555',ls='--',label='existing density gate');axes[0,0].legend()
    fig.suptitle('Bounded SU2 CFL feedback: same source, one on/off switch')
    fig.tight_layout();fig.savefig(PROJECT/'plots/m6_cfl_feedback_20261025.png',dpi=150);plt.close(fig)
    print(__import__('json').dumps({'pair':pair,'matched':{n:results[n]['matched'] for n in results},
         'Cp_RMSE':{n:results[n]['Cp']['all_point_Cp_RMSE'] for n in results},'next':report['recommendation']},indent=2))


if __name__=='__main__':
    main()
