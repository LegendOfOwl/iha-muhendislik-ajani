"""Audit matched frozen control fields without altering old benchmark reports."""
from prepare import ROOT, BASE, CASE, read, save, sha, now
from field_audit import audit
from compare_utils import zones, interpolate, relative_l2
from run import history
import numpy as np
import os
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def score(folder, label, meshrole='fine',normalization=None):
    a = audit(meshrole, meshrole, folder=folder, output_label=label,normalization=normalization)
    out = ROOT / 'outputs/data/qualification/flatplate_SAneg_20261025_v1' / label
    wall = np.genfromtxt(out / 'wall.csv', delimiter=',', names=True)
    errors = {'Cf_curve': [], 'velocity': [], 'eddy_viscosity': []}
    for source, refs in [('Cf_curve', zones(BASE / 'sources/cf_plate.dat', 2)),
                         ('velocity', zones(BASE / 'sources/flatplate_u.dat', 2)),
                         ('eddy_viscosity', zones(BASE / 'sources/mut_0.97.dat', 3))]:
        for index, (name, ref) in enumerate(refs):
            if source == 'Cf_curve':
                x, y, target, actual = wall['x_m'], wall['Cfx'], ref[:, 0], ref[:, 1]
                window = (target >= .1) & (target <= 1.9)
            else:
                p = a['profiles'][index if source == 'velocity' else 0]
                data = np.genfromtxt(ROOT / p['csv'], delimiter=',', names=True)
                assert np.all(data['valid_sample'] == 1)
                x, y = data['y_m'], data['u_over_Uinf' if source == 'velocity' else 'mut_over_muinf']
                target, actual = (ref[:, 1], ref[:, 0]) if source == 'velocity' else (ref[:, 1], ref[:, 2])
                window = np.ones(len(target), dtype=bool)
            pred, valid = interpolate(x, y, target)
            csv = out / f'{source}_{index}.csv'
            np.savetxt(csv, np.column_stack([target, actual, pred, pred - actual, valid.astype(int), window.astype(int)]),
                       delimiter=',', header='coordinate,reference,native,error,valid_sample,scoring_window', comments='')
            errors[source].append({'source_zone': name, 'points': len(ref), 'invalid_points': int((~valid).sum()),
                                   'relative_L2': relative_l2(pred[window], actual[window], valid[window]),
                                   'relative_L2_all_points': relative_l2(pred, actual, valid), 'csv': str(csv.relative_to(ROOT))})
    gates = {'iteration': a['iterative_gate'], 'max_yplus': a['max_yplus'] < 1,
             **{key: all(r['relative_L2'] is not None and r['relative_L2'] < limit for r in errors[key])
                for key, limit in [('Cf_curve', .03), ('velocity', .03), ('eddy_viscosity', .05)]}}
    a.update(reference_errors=errors, diagnostic_screens=gates, all_diagnostic_screens=all(gates.values()))
    return a


def main():
    folders = {'fixed100': CASE / 'fixed_cfl_pair_v1/cfl100', 'fixed10': CASE / 'fixed_cfl_pair_v1/cfl10',
               'mg2': CASE / 'mg_control_v1/mg2'}
    if (CASE / 'adaptive_toggle_v1/adaptive/prediction_frozen.json').exists():
        folders['adaptive'] = CASE / 'adaptive_toggle_v1/adaptive'
    result = {label: score(folder, 'control_' + label) for label, folder in folders.items()}
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for label, folder in folders.items():
        h = history(folder)
        for axis, name in zip(axes, ['rms[Rho]', 'rms[nu]', 'CD']):
            axis.plot([r['Inner_Iter'] for r in h], [r[name] for r in h], label=label)
            axis.set(xlabel='Restart iteration', ylabel=name)
            axis.grid(alpha=.2)
            axis.legend()
    axes[0].axhline(-10, color='gray', ls=':')
    axes[1].axhline(-11, color='gray', ls=':')
    fig.suptitle('Same fine mesh and checkpoint800; fixed CFL and FAS controls')
    fig.tight_layout()
    fig.savefig(ROOT / 'outputs/plots/flatplate_convergence_controls_20261025.png', dpi=160)
    plt.close(fig)
    save(ROOT / 'outputs/reports/flatplate_control_fields_20261025.json',
         {'created_utc': now(), 'cases': result, 'not_blind': True, 'physical_qualification_passed': False,
          'limits': ['Diagnostic controls do not replace the preregistered three-grid family.',
                     'All source comparison points retained; endpoint window unchanged.']})


if __name__ == '__main__': main()
