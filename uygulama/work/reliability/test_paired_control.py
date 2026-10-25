"""Counterexamples to invalid numerical-effect acceptance; no CFD targets here."""
import copy
from paired_control import evaluate


def main():
    a = {'native_status': {'exit_code': 0, 'stop_reason': None},
         'matched': {'field_iteration': 399, 'terminal_history_iteration': 399, 'last100_samples': 100,
                     'rms[Rho]': -8., 'rms[nu]': -9., 'CD': .003, 'CD_last100_range': 1e-6}}
    b = copy.deepcopy(a)
    b['matched'].update({'rms[Rho]': -8.5, 'rms[nu]': -9.2})
    def effect(x): return evaluate(a, x, 399, .3, .1,normalizations=('SI2D','SI2D'))
    assert effect(b)['effect_passed'] and not effect(b)['physical_qualification_passed']
    tested = ['valid effect still not physical acceptance']
    cases = [
        ('missing field tuple', lambda x: x.update(matched=None)),
        ('wrong field399/history400', lambda x: x['matched'].update(terminal_history_iteration=400)),
        ('wrong checkpoint', lambda x: x['matched'].update(field_iteration=398)),
        ('short force window', lambda x: x['matched'].update(last100_samples=99)),
        ('native failure with fields', lambda x: x['native_status'].update(exit_code=1)),
        ('budget stop with fields', lambda x: x['native_status'].update(stop_reason='time_budget_exceeded')),
        ('nonfinite density', lambda x: x['matched'].update({'rms[Rho]': float('nan')})),
        ('missing SA residual', lambda x: x['matched'].pop('rms[nu]')),
    ]
    for name, change in cases:
        x = copy.deepcopy(b); change(x); r = effect(x)
        assert not r['comparable'] and not r['effect_passed'] and r['density_log10_gain'] is None, name
        tested.append(name)
    for name, changes in [('gain below raw threshold', {'rms[Rho]': -8.299999999}),
                          ('SA worsens despite density gain', {'rms[nu]': -8.899999999})]:
        x = copy.deepcopy(b); x['matched'].update(changes); r = effect(x)
        assert r['comparable'] and not r['effect_passed'], name
        tested.append(name)
    for name,norms in [('missing normalization',None),('incompatible SI and ND',('SI2D','ND2D'))]:
        r=evaluate(a,b,399,.3,.1,normalizations=norms)
        assert not r['comparable'] and not r['effect_passed'],name
        tested.append(name)
    print({'passed': len(tested), 'checks': tested})
    return tested


if __name__ == '__main__': main()
