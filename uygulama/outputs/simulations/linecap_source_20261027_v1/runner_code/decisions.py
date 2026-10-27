"""Pure, fail-closed decisions for one registered source-build LINELET test.

Public API:
    reproducibility_gate(release_run, build32_run, contract)
    linecap_effect_gate(build32_run, build256_run, contract,
                        reproduction, source_change)

Inputs are JSON-compatible dictionaries. No files, solver, clock or environment
are read. All numerical decision limits are required in ``contract``; its
``rms_components`` must list Rho, RhoU, RhoV, RhoE and nu exactly once.

A run contains normalization, native_exit_code, field_iteration,
history_iteration, last100_samples, CD_last100_range, elapsed_seconds,
field_validity, identity, history and membership. Each history row contains
iteration, rms (component -> log10 SI RMS), CD, flow_iterations and
SA_iterations. Field-validity evidence has three strict booleans:
rho_positive_finite, pressure_positive_finite and required_arrays_finite.

``identity`` has SHA256 strings for mesh_sha256, seed_sha256,
comparison_config_sha256 and physics_sha256. The config identity represents
all common numerical settings with documented path-only aliases canonicalized.
The local builds additionally have source_tree_sha256,
compiler_manifest_sha256 and runtime_manifest_sha256. These are evidence
identities, not a claim that the release and local binary bytes are identical.

``membership`` contains canonical node_ids [0..N-1], a strict Boolean mask,
and ``mapping`` with passed, reference_points, observed_points,
unique_matches and maximum_distance_m. The effect also requires finite
Rho_squared_share in [0,1] and fixed_RHS_sha256: both arms use the same frozen
old sequential-stage RHS. Color IDs are deliberately absent from the schema.

``source_change`` has verified=True, only_change='MAX_LINELET_POINTS',
reference_cap, candidate_cap, pristine_source_sha256, modified_source_sha256
and patch_sha256. The caller must verify the actual source diff, manifests,
raw fields and mapping before supplying these evidence records. This module
decides from that evidence; it does not authenticate a caller's assertions.
"""
import hashlib
import json
import math
import re


_COMPONENTS = {'Rho', 'RhoU', 'RhoV', 'RhoE', 'nu'}
_COMMON_IDENTITIES = ('mesh_sha256', 'seed_sha256',
                      'comparison_config_sha256', 'physics_sha256')
_LIMITS = (
    'CD_window_range_max', 'reproduction_max_abs_log10_difference',
    'reproduction_final_CD_abs_difference_max',
    'reproduction_Krylov_relative_difference_max',
    'coordinate_mapping_max_m', 'density_gain_min', 'SA_worsening_max',
    'work_ratio_max', 'elapsed_ratio_max', 'Rho_share_gain_min',
)


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _number(value, minimum=None, strictly_positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        finite = math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False
    if not finite:
        return False
    return ((minimum is None or value >= minimum)
            and (not strictly_positive or value > 0))


def _integer(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _contract_valid(contract):
    c = _mapping(contract)
    components = c.get('rms_components')
    return (
        c.get('normalization') == 'SI2D'
        and isinstance(components, list) and len(components) == 5
        and all(isinstance(x, str) for x in components)
        and set(components) == _COMPONENTS
        and _integer(c.get('iterations'), 1)
        and _integer(c.get('comparison_iteration'))
        and c['comparison_iteration'] == c['iterations'] - 1
        and _integer(c.get('last_window_samples'), 1)
        and c['last_window_samples'] <= c['iterations']
        and _integer(c.get('membership_expected_nodes'), 1)
        and _integer(c.get('reference_cap'), 1)
        and _integer(c.get('candidate_cap'), 1)
        and c['candidate_cap'] > c['reference_cap']
        and _sha(c.get('pristine_source_tree_sha256'))
        and all(_number(c.get(key), minimum=0) for key in _LIMITS)
        and c['CD_window_range_max'] > 0
        and c['work_ratio_max'] > 0 and c['elapsed_ratio_max'] > 0
        and c['Rho_share_gain_min'] > 0
    )


def _history(run, c):
    rows = run.get('history')
    if not isinstance(rows, list) or len(rows) != c['iterations']:
        return None
    for iteration, row in enumerate(rows):
        if not isinstance(row, dict):
            return None
        rms = _mapping(row.get('rms'))
        if not (_integer(row.get('iteration')) and row['iteration'] == iteration
                and all(_number(rms.get(key)) for key in c['rms_components'])
                and _number(row.get('CD'))
                and _integer(row.get('flow_iterations'))
                and _integer(row.get('SA_iterations'))):
            return None
    return rows


def _run_checks(run, c):
    r = _mapping(run)
    rows = _history(r, c)
    field = _mapping(r.get('field_validity'))
    member = _mapping(r.get('membership'))
    mapping = _mapping(member.get('mapping'))
    identity = _mapping(r.get('identity'))
    n = c['membership_expected_nodes']
    node_ids, mask = member.get('node_ids'), member.get('mask')
    valid_ids = (isinstance(node_ids, list) and len(node_ids) == n
                 and all(_integer(node) and node == i for i, node in enumerate(node_ids)))
    valid_mask = (isinstance(mask, list) and len(mask) == n
                  and all(isinstance(value, bool) for value in mask))
    window_range = (max(row['CD'] for row in rows[-c['last_window_samples']:])
                    - min(row['CD'] for row in rows[-c['last_window_samples']:])) if rows else None
    checks = {
        'normalization': r.get('normalization') == c['normalization'],
        'native_exit_and_matched_iteration': (
            _integer(r.get('native_exit_code')) and r['native_exit_code'] == 0
            and _integer(r.get('field_iteration'))
            and _integer(r.get('history_iteration'))
            and r['field_iteration'] == r['history_iteration'] == c['comparison_iteration']),
        'complete_finite_history': rows is not None,
        'complete_stable_CD_window': (
            rows is not None and _integer(r.get('last100_samples'), 1)
            and r['last100_samples'] == c['last_window_samples']
            and _number(r.get('CD_last100_range'), minimum=0)
            and r['CD_last100_range'] == window_range
            and window_range < c['CD_window_range_max']),
        'field_validity_proven': all(field.get(key) is True for key in (
            'rho_positive_finite', 'pressure_positive_finite', 'required_arrays_finite')),
        'positive_finite_elapsed': _number(r.get('elapsed_seconds'), strictly_positive=True),
        'bijective_native_mapping': (
            mapping.get('passed') is True
            and all(_integer(mapping.get(key), 1) and mapping[key] == n for key in (
                'reference_points', 'observed_points', 'unique_matches'))
            and _number(mapping.get('maximum_distance_m'), minimum=0)
            and mapping['maximum_distance_m'] <= c['coordinate_mapping_max_m']),
        'canonical_native_membership': valid_ids and valid_mask,
        'input_identities_present': all(_sha(identity.get(key)) for key in _COMMON_IDENTITIES),
    }
    return checks, rows


def _shared_inputs(a, b):
    x, y = _mapping(a.get('identity')), _mapping(b.get('identity'))
    return all(_sha(x.get(key)) and x[key] == y.get(key) for key in _COMMON_IDENTITIES)


def _fingerprint(run):
    try:
        encoded = json.dumps(run, sort_keys=True, separators=(',', ':'),
                             allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, OverflowError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def _work(rows):
    total = sum(row['flow_iterations'] + row['SA_iterations'] for row in rows)
    return total if _number(total, minimum=0) else None


def _ratio(numerator, denominator):
    if not (_number(numerator, minimum=0) and _number(denominator, strictly_positive=True)):
        return None
    try:
        value = numerator / denominator
    except (OverflowError, ZeroDivisionError):
        return None
    return value if _number(value, minimum=0) else None


def _result(gate, checks, metrics=None, **extra):
    # Each primitive check is a strict bool; truthy strings/numbers are not proof.
    accepted = bool(checks) and all(value is True for value in checks.values())
    return dict(gate=gate, accepted=accepted, checks=checks,
                rejected_because=[key for key, value in checks.items() if value is not True],
                metrics=metrics or {}, physical_qualification_passed=False,
                M6_qualification_passed=False, LLM_improvement_demonstrated=False, **extra)


def reproducibility_gate(release_run, build32_run, contract):
    """Test numerical reproduction, not binary identity or equal runtime."""
    if not _contract_valid(contract):
        return _result('pristine_reproduction', {'valid_contract': False})
    c = contract
    a, b = _mapping(release_run), _mapping(build32_run)
    ca, ra = _run_checks(a, c)
    cb, rb = _run_checks(b, c)
    checks = {'valid_contract': True, **{'release_' + k: v for k, v in ca.items()},
              **{'build32_' + k: v for k, v in cb.items()},
              'shared_input_identities': _shared_inputs(a, b),
              'registered_pristine_source': _mapping(b.get('identity')).get('source_tree_sha256') == c['pristine_source_tree_sha256']}
    metrics = {}
    usable = ra is not None and rb is not None
    differences = ({key: max(abs(x['rms'][key] - y['rms'][key])
                             for x, y in zip(ra, rb)) for key in c['rms_components']}
                   if usable else None)
    cd_difference = abs(ra[-1]['CD'] - rb[-1]['CD']) if usable else None
    wa, wb = (_work(ra), _work(rb)) if usable else (None, None)
    work_difference = _ratio(abs(wb - wa), wa) if _number(wa) and _number(wb) else None
    checks.update(
        five_RMS_curves_reproduced=(differences is not None and all(
            value <= c['reproduction_max_abs_log10_difference'] for value in differences.values())),
        final_CD_reproduced=(_number(cd_difference) and cd_difference <= c['reproduction_final_CD_abs_difference_max']),
        combined_Krylov_reproduced=(_number(work_difference) and work_difference <= c['reproduction_Krylov_relative_difference_max']),
        exact_native_membership=(ca['canonical_native_membership'] and cb['canonical_native_membership']
                                 and a['membership']['mask'] == b['membership']['mask']),
    )
    fingerprint = _fingerprint(b)
    checks['build32_fingerprintable'] = fingerprint is not None
    metrics.update(max_abs_RMS_log10_difference_by_component=differences,
                   final_CD_absolute_difference=cd_difference,
                   reference_Krylov=wa, build32_Krylov=wb,
                   combined_Krylov_relative_difference=work_difference)
    return _result('pristine_reproduction', checks, metrics,
                   build32_run_fingerprint=fingerprint,
                   contract_fingerprint=_fingerprint(c))


def linecap_effect_gate(build32_run, build256_run, contract, reproduction, source_change):
    """Accept only a reproducible, controlled, beneficial and bounded cap test."""
    if not _contract_valid(contract):
        return _result('linelet_cap_effect', {'valid_contract': False})
    c = contract
    a, b = _mapping(build32_run), _mapping(build256_run)
    ca, ra = _run_checks(a, c)
    cb, rb = _run_checks(b, c)
    proof, change = _mapping(reproduction), _mapping(source_change)
    proof_checks = _mapping(proof.get('checks'))
    valid_reproduction = (
        proof.get('gate') == 'pristine_reproduction' and proof.get('accepted') is True
        and bool(proof_checks) and all(value is True for value in proof_checks.values())
        and proof.get('physical_qualification_passed') is False
        and proof.get('contract_fingerprint') == _fingerprint(c)
        and _sha(proof.get('build32_run_fingerprint'))
        and proof['build32_run_fingerprint'] == _fingerprint(a))
    ia, ib = _mapping(a.get('identity')), _mapping(b.get('identity'))
    source_proven = (
        change.get('verified') is True and change.get('only_change') == 'MAX_LINELET_POINTS'
        and _integer(change.get('reference_cap'), 1) and change['reference_cap'] == c['reference_cap']
        and _integer(change.get('candidate_cap'), 1) and change['candidate_cap'] == c['candidate_cap']
        and _sha(change.get('patch_sha256'))
        and change.get('pristine_source_sha256') == c['pristine_source_tree_sha256']
        and ia.get('source_tree_sha256') == c['pristine_source_tree_sha256']
        and _sha(change.get('modified_source_sha256'))
        and change['modified_source_sha256'] != change['pristine_source_sha256']
        and ib.get('source_tree_sha256') == change['modified_source_sha256'])
    checks = {'valid_contract': True, **{'build32_' + k: v for k, v in ca.items()},
              **{'build256_' + k: v for k, v in cb.items()},
              'pristine_reproduction_passed_for_same_baseline': valid_reproduction,
              'shared_input_identities': _shared_inputs(a, b),
              'compiler_options_identity': (_sha(ia.get('compiler_manifest_sha256'))
                  and ia['compiler_manifest_sha256'] == ib.get('compiler_manifest_sha256')),
              'runtime_dependencies_identity': (_sha(ia.get('runtime_manifest_sha256'))
                  and ia['runtime_manifest_sha256'] == ib.get('runtime_manifest_sha256')),
              'only_registered_source_cap_change': source_proven}
    usable = ra is not None and rb is not None
    density_gain = ra[-1]['rms']['Rho'] - rb[-1]['rms']['Rho'] if usable else None
    sa_worse = rb[-1]['rms']['nu'] - ra[-1]['rms']['nu'] if usable else None
    wa, wb = (_work(ra), _work(rb)) if usable else (None, None)
    work_ratio = _ratio(wb, wa)
    elapsed_ratio = (_ratio(b['elapsed_seconds'], a['elapsed_seconds'])
                     if ca['positive_finite_elapsed'] and cb['positive_finite_elapsed'] else None)
    ma, mb = _mapping(a.get('membership')), _mapping(b.get('membership'))
    valid_shares = all(_number(m.get('Rho_squared_share'), minimum=0)
                       and m['Rho_squared_share'] <= 1 for m in (ma, mb))
    share_gain = mb['Rho_squared_share'] - ma['Rho_squared_share'] if valid_shares else None
    valid_masks = ca['canonical_native_membership'] and cb['canonical_native_membership']
    old_count, new_count = (sum(ma['mask']), sum(mb['mask'])) if valid_masks else (None, None)
    checks.update(
        density_gain=(_number(density_gain) and density_gain >= c['density_gain_min']),
        SA_worsening=(_number(sa_worse) and sa_worse <= c['SA_worsening_max']),
        combined_Krylov_cost=(_number(work_ratio, minimum=0) and work_ratio <= c['work_ratio_max']),
        observed_elapsed_cost=(_number(elapsed_ratio, minimum=0) and elapsed_ratio <= c['elapsed_ratio_max']),
        same_fixed_old_RHS=(_sha(ma.get('fixed_RHS_sha256')) and ma['fixed_RHS_sha256'] == mb.get('fixed_RHS_sha256')),
        native_membership_nodes_increased=(valid_masks and new_count > old_count),
        fixed_RHS_Rho_share_increased=(_number(share_gain) and share_gain > c['Rho_share_gain_min']),
    )
    return _result('linelet_cap_effect', checks, {
        'density_log10_gain': density_gain, 'SA_log10_worsening': sa_worse,
        'reference_Krylov': wa, 'candidate_Krylov': wb, 'work_ratio': work_ratio,
        'observed_elapsed_ratio': elapsed_ratio,
        'reference_membership_nodes': old_count, 'candidate_membership_nodes': new_count,
        'fixed_old_RHS_Rho_squared_share_gain': share_gain,
    })
