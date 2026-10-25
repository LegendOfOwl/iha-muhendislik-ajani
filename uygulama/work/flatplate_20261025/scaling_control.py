"""Isolate algebraic variable scaling on an existing near-steady physical seed."""
from prepare import ROOT, BASE, CASE, read, save, sha, now
from common import run_native
from cfl_control import freeze_folder, evaluate
from scaled_restart import convert, dimensional_matched
from newton_control import snapshot
import os
import sys

PAIR = CASE / 'warm_scaling_pair_v1'
CONTROL = CASE / 'ilu_pair/lusgs'
REPORT = ROOT / 'outputs/reports/flatplate_scaling_control_20261025.json'


def prepare():
    assert not PAIR.exists()
    prior = read(CONTROL / 'prediction_frozen.json')
    for p, h in prior['files_sha256'].items(): assert sha(ROOT / p) == h
    assert prior['result']['native']['exit_code'] == 0
    folder = PAIR / 'scaled'; folder.mkdir(parents=True)
    free = read(CASE / 'contract.json')['derived_freestream']
    data, check = convert((CONTROL / 'seed.dat').read_bytes(), free)
    (folder / 'seed.dat').write_bytes(data)
    source = (CONTROL / 'case.cfg').read_text()
    assert 'REF_DIMENSIONALIZATION' not in source
    text = source + 'REF_DIMENSIONALIZATION= FREESTREAM_VEL_EQ_MACH\n'
    (folder / 'case.cfg').write_text(text, encoding='utf-8')
    save(PAIR / 'conversion_check.json', check)
    save(PAIR / 'contract.json', {'created_utc': now(), 'not_blind': True,
         'hypothesis': 'Balancing mean-flow conservative-variable magnitudes improves the linear/nonlinear solve, independently of enabling Newton-Krylov.',
         'source': 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/TestCases/rans/oneram6/turb_ONERAM6_nk.cfg',
         'source_implementation': 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/solvers/CEulerSolver.cpp',
         'baseline': str(CONTROL.relative_to(ROOT)), 'baseline_seal_sha256': sha(CONTROL / 'prediction_frozen.json'),
         'baseline_reused_before_new_hypothesis': True, 'source_seed_sha256': sha(CONTROL / 'seed.dat'),
         'target_seed_sha256': sha(folder / 'seed.dat'), 'same_physical_seed': True, 'same_seed_bytes': False,
         'conversion_check_sha256': sha(PAIR / 'conversion_check.json'),
         'only_explicit_config_addition': 'REF_DIMENSIONALIZATION=FREESTREAM_VEL_EQ_MACH; old omitted default is DIMENSIONAL',
         'config_sha256': sha(folder / 'case.cfg'), 'mesh_sha256': sha(CASE / 'meshes/medium.su2'),
         'comparison_iteration': 199, 'iterations': 200, 'seconds': 120, 'threads': 4,
         'density_log10_gain_min': .3, 'SA_log10_worsening_max': .1,
         'comparison_normalization': 'Both results expressed as the original SI integrated residual; density factor rhoRef*URef and SA factor URef^2 for this2D nonconservative scalar, Lref1.',
         'physical_changes': None, 'newton_enabled': False, 'no_automatic_parameter_sweep': True,
         'conditional_next': 'If the SI-normalized effect passes, register a bounded three-mesh family; no three-grid acceptance from this single medium mesh.'})
    snapshot(folder)
    # Include this controller and conversion in the pre-native code archive.
    import shutil
    meta = read(folder / 'runner_code_before_native.json')
    for name in ['scaling_control.py', 'scaled_restart.py']:
        p = folder / 'runner_code' / name; shutil.copyfile(BASE / name, p)
        meta['files_sha256'][str(p.relative_to(ROOT))] = sha(p)
    save(folder / 'runner_code_before_native.json', meta)
    print('SCALING REGISTERED', check, flush=True)


def run():
    c = read(PAIR / 'contract.json'); folder = PAIR / 'scaled'
    assert not (folder / 'solver.process.json').exists()
    assert sha(folder / 'case.cfg') == c['config_sha256'] and sha(folder / 'seed.dat') == c['target_seed_sha256']
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    status = run_native([exe, 'case.cfg', '-t', '4'], folder, 'solver', c['seconds'],
                        dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    seal = freeze_folder(folder, PAIR / 'contract.json', CASE / 'meshes/medium.su2')
    print('FROZEN', status, seal['matched'], flush=True)


def compare():
    c = read(PAIR / 'contract.json'); free = read(CASE / 'contract.json')['derived_freestream']
    a = read(CONTROL / 'prediction_frozen.json')
    # Old ILU control stored a narrower summary; reconstruct the matched tuple from its sealed files.
    from run import history
    h = history(CONTROL); row = next(r for r in h if r['Inner_Iter'] == 199)
    a['native_status'] = a['result']['native']
    a['matched'] = {'field_iteration': 199, 'terminal_history_iteration': int(h[-1]['Inner_Iter']),
                    'last100_samples': len(h[-100:]), 'CD_last100_range': max(r['CD'] for r in h[-100:]) - min(r['CD'] for r in h[-100:]),
                    **{k: row[k] for k in ['CD', 'rms[Rho]', 'rms[nu]']}}
    braw = read(PAIR / 'scaled/prediction_frozen.json'); b = dimensional_matched(braw, free)
    count = 0
    for seal in [a, braw]:
        for p, expected in seal['files_sha256'].items(): assert sha(ROOT / p) == expected; count += 1
    effect = evaluate(a, b, c['comparison_iteration'], c['density_log10_gain_min'], c['SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    mixed_rejected=evaluate(a,braw,c['comparison_iteration'],c['density_log10_gain_min'],c['SA_log10_worsening_max'],normalizations=('SI2D','SU2_ND2D'))
    save(REPORT, {'created_utc': now(), 'contract_sha256': sha(PAIR / 'contract.json'), 'dimensional': a,
                  'scaled_raw': braw, 'scaled_SI_residuals': b, 'verified_files': count, **effect,
                  'mixed_normalization_counterexample':mixed_rejected,
                  'spurious_unconverted_density_gain':a['matched']['rms[Rho]']-braw['matched']['rms[Rho]']})
    print(effect, flush=True)


if __name__ == '__main__': {'prepare': prepare, 'run': run, 'compare': compare}[sys.argv[1]]()
