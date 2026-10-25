"""Fail-closed evaluation of a registered matched-checkpoint SA control pair."""
import math


def evaluate(a, b, iteration, density_gain_min, sa_worsening_max, *, normalizations=None):
    reasons = []
    if normalizations is None or len(normalizations) != 2 or not all(normalizations):
        reasons.append('Residual normalization evidence missing')
    elif normalizations[0] != normalizations[1]:
        reasons.append('Residual normalizations differ; convert and verify before comparison')
    for name, seal in [('A', a), ('B', b)]:
        status, matched = seal.get('native_status', {}), seal.get('matched')
        if status.get('exit_code') != 0 or status.get('stop_reason') is not None:
            reasons.append(name + ': native run incomplete or failed')
        if not matched:
            reasons.append(name + ': no complete field/surface/restart/history tuple')
            continue
        if matched.get('field_iteration') != iteration or matched.get('terminal_history_iteration') != iteration:
            reasons.append(name + ': not the registered completed iteration')
        if matched.get('last100_samples') != 100:
            reasons.append(name + ': incomplete final100 history window')
        for key in ['rms[Rho]', 'rms[nu]', 'CD', 'CD_last100_range']:
            value = matched.get(key)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                reasons.append(name + ': missing/nonfinite ' + key)
    gain = worsening = None
    if not reasons:
        gain = a['matched']['rms[Rho]'] - b['matched']['rms[Rho]']
        worsening = b['matched']['rms[nu]'] - a['matched']['rms[nu]']
    return {'evaluation_version': 2, 'residual_normalizations': normalizations,
            'comparable': not reasons, 'comparison_rejected_because': reasons,
            'density_log10_gain': gain, 'SA_log10_worsening': worsening,
            'effect_passed': not reasons and gain >= density_gain_min and worsening <= sa_worsening_max,
            'physical_qualification_passed': False}
