"""Evidence-dependent next experiment selection; heuristic, not a learned expert."""
from pathlib import Path
import hashlib
import json
import math


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_evidence(root, entries):
    root = Path(root).resolve()
    if not entries:
        return ['No evidence supplied']
    errors = []
    for relative, expected in entries.items():
        p = (root / relative).resolve()
        if not p.is_relative_to(root):
            errors.append('Outside project: ' + relative)
        elif not p.is_file():
            errors.append('Missing: ' + relative)
        elif sha(p) != expected:
            errors.append('Changed: ' + relative)
    return errors


def iterative_gate(rows, selected, limits):
    """Use a contiguous matched window, strict raw thresholds, all required values."""
    if not isinstance(selected, int):
        return {'passed':False,'reason':'No matched field iteration'}
    chosen = [r for r in rows if selected - 99 <= r.get('Inner_Iter', -1) <= selected]
    if [r['Inner_Iter'] for r in chosen] != list(range(selected-99, selected+1)):
        return {'passed':False,'reason':'Missing, duplicate or unordered history rows'}
    fields = ['CL', 'CD', 'rms[Rho]']
    if any(not isinstance(r.get(k), (int,float)) or not math.isfinite(r[k]) for r in chosen for k in fields):
        return {'passed':False,'reason':'Missing or non-finite monitored values'}
    observed = {'density_log10':chosen[-1]['rms[Rho]'],
                'CL_last100_range':max(r['CL'] for r in chosen)-min(r['CL'] for r in chosen),
                'CD_last100_range':max(r['CD'] for r in chosen)-min(r['CD'] for r in chosen)}
    checks = {k:observed[k] < limits[k+'_max'] for k in observed}
    return {'passed':all(checks.values()),'observed':observed,'checks':checks,'selected_iteration':selected}


def choose_next(state):
    """Ordered dependencies prevent spending mesh budget on unresolved iteration error.

    This is a transparent policy, not formal Bayesian value-of-information:
    no calibrated likelihoods or guaranteed optimality are available.
    """
    if state.get('evidence_errors'):
        action, reason = 'repair_evidence', 'Inputs/checkpoints changed, missing, or lack provenance.'
    elif state.get('checkpoint_complete') is not True:
        action, reason = 'recover_checkpoint', 'Need a matching native field/restart/history before interpretation.'
    elif state.get('iteration_passed') is not True:
        pair = state.get('linear_pair')
        if pair is None and state.get('linear_cap_saturated') is True:
            action, reason = 'controlled_linear_pair', 'Cap saturation is a hypothesis; compare one cap change at a fixed seed.'
        elif pair and pair.get('comparable') is True and pair.get('effect_passed') is False:
            action, reason = 'localize_nonlinear_stall', 'Cap test did not show the registered effect; no more cap sweep.'
        elif pair and pair.get('comparable') is True and pair.get('effect_passed') is True:
            action, reason = 'bounded_convergence_followup', 'A measured cap effect exists, but required nonlinear gates still fail.'
        else:
            action, reason = 'diagnose_iteration', 'A failed or incomparable control does not establish the cause.'
    elif state.get('regional_mesh_passed') is not True:
        action, reason = 'regional_mesh_control', 'Numerical iteration is acceptable; test BL/TE/tip/wake directions independently.'
    elif state.get('three_grid_passed') is not True:
        action, reason = 'systematic_three_grid', 'Need same-geometry systematic levels with iterative acceptance.'
    elif state.get('farfield_passed') is not True:
        action, reason = 'farfield_control', 'Separate domain truncation from mesh resolution.'
    elif state.get('independent_integral_passed') is not True:
        action, reason = 'independent_force_check', 'Verify the force extraction chain.'
    elif state.get('experiment_passed') is not True:
        action, reason = 'physical_model_review', 'Numerical checks alone cannot remove physical-model discrepancy.'
    else:
        action, reason = 'scope_review', 'All supplied gates passed; a reviewer must still check missing mandatory gates and application scope.'
    native_actions = {'controlled_linear_pair', 'bounded_convergence_followup', 'regional_mesh_control',
                      'systematic_three_grid', 'farfield_control'}
    budget = state.get('remaining_native_runs', 0)
    if type(budget) is not int or budget < 0:
        raise ValueError('A nonnegative explicit native-run budget is required')
    return {'action':action,'reason':reason,'automatically_execute':False,
            'native_budget_available':budget,'native_action_budget_blocked':action in native_actions and budget==0,
            'new_physical_acceptance':False,'strategy':'dependency_ordered_falsifiable_test_v1',
            'strategy_optimality_proved':False}


def audit_registered(root, spec, project_id):
    """Recompute the iterative gate from raw frozen inputs, never trust a GUI flag."""
    from linear_pair import history, read
    root=Path(root)
    errors=verify_evidence(root,spec['evidence_sha256'])
    if spec.get('project_id') != project_id:
        errors.append('Project context mismatch')
    state=dict(spec['state'])
    diagnostics={}
    if not errors:
        contract=read(root/spec['contract'])
        if contract.get('project_id') != project_id:
            errors.append('Contract project mismatch')
        for case in spec['cases']:
            folder=root/case['folder']
            seal=read(folder/'prediction_frozen.json')
            errors.extend(verify_evidence(root,seal['files_sha256']))
            if seal['contract_sha256'] != sha(root/spec['contract']):
                errors.append('Prediction/contract mismatch: '+case['name'])
            if errors:
                continue
            selected=(seal.get('matched') or {}).get('field_iteration')
            rows=history(folder/'history.csv')
            complete=selected is not None and all((folder/f'{prefix}_{selected:06d}.{ext}').exists()
                for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')])
            run=read(folder/'run_status.json')
            complete=complete and run['exit_code']==0 and selected==contract['iterations_each']-1
            gate=iterative_gate(rows,selected,contract['thresholds_unchanged'])
            diagnostics[case['name']]={'checkpoint_complete':complete,'iterative_gate':gate}
        chosen=diagnostics.get(spec['preselected_case'],{})
        state['checkpoint_complete']=chosen.get('checkpoint_complete',False)
        state['iteration_passed']=chosen.get('iterative_gate',{}).get('passed',False)
    state['evidence_errors']=errors
    return {'project_id':project_id,'evidence_errors':errors,'raw_recomputed':diagnostics,
            'quality_passed':False,'passed':not errors,'recommendation':choose_next(state),
            'note':'Kayıtlı ham geçmiş ve mühürler yeniden denetlendi; yeni çözücü koşusu veya fizik kabulü üretilmedi.'}


if __name__ == '__main__':
    import os
    root = Path(__file__).resolve().parents[2]
    project_id = os.environ.get('UAV_PROJECT_ID','proje-e9319baef1')
    manifest = json.loads((root/'outputs/data/projects'/f'{project_id}.json').read_text(encoding='utf-8-sig'))
    output = root / manifest['artifact_root']
    specpath = output/'data/reliability_case.json'
    if not specpath.exists():
        raise SystemExit('Bu projede kaynak ve kabul sözleşmesi tanımlı güvenilirlik kaydı yok.')
    spec = json.loads(specpath.read_text(encoding='utf-8-sig'))
    result = audit_registered(root,spec,project_id)
    result['spec_sha256']=sha(specpath)
    target=output/'reports/reliability_audit.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))
