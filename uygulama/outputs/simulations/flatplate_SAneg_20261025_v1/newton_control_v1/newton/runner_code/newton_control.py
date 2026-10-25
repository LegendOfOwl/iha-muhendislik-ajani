"""Source-recipe matrix-free Newton/approximate-Jacobian pair on one shared scaled seed."""
from prepare import ROOT, BASE, CASE, read, save, sha, now, config
from common import run_native
from run import history
from cfl_control import freeze_folder, evaluate
import os
import shutil
import sys
import numpy as np

PAIR = CASE / 'newton_control_v1'
MESH = CASE / 'meshes/medium.su2'
REPORT = ROOT / 'outputs/reports/flatplate_newton_control_20261025.json'


def recipe():
    text, _ = config('../../meshes/medium.su2', 400)
    changes = {'LINEAR_SOLVER_PREC= LU_SGS': 'LINEAR_SOLVER_PREC= ILU',
               'LINEAR_SOLVER_ERROR= 1e-06': 'LINEAR_SOLVER_ERROR= 0.2',
               'LINEAR_SOLVER_ITER= 40': 'LINEAR_SOLVER_ITER= 8',
               'CFL_NUMBER= 100': 'CFL_NUMBER= 10',
               'CFL_ADAPT_PARAM= (0.1,2,100,1e5,0.001,50)': 'CFL_ADAPT_PARAM= (1,1.05,10,400,0.2,0)',
               'CONV_STARTITER= 200': 'CONV_STARTITER= 1000'}
    for a, b in changes.items():
        assert text.splitlines().count(a) == 1
        text = text.replace(a, b)
    text += ('REF_DIMENSIONALIZATION= FREESTREAM_VEL_EQ_MACH\n'
             'NEWTON_KRYLOV= NO\nNEWTON_KRYLOV_IPARAM= (200,0,1)\n'
             'NEWTON_KRYLOV_DPARAM= (0,0,0,1e-5,1)\n')
    return text, changes


def snapshot(folder):
    target = folder / 'runner_code'
    assert not target.exists()
    target.mkdir()
    files = [BASE / name for name in ['newton_control.py', 'cfl_control.py', 'prepare.py', 'run.py']]
    files += [ROOT / 'work/reliability/paired_control.py', ROOT / 'work/tmr_m6_20261025/common.py']
    for p in files: shutil.copyfile(p, target / p.name)
    save(folder / 'runner_code_before_native.json', {'created_utc': now(),
         'files_sha256': {str((target / p.name).relative_to(ROOT)): sha(target / p.name) for p in files}})


def prepare_seed():
    assert not PAIR.exists()
    folder = PAIR / 'seed'; folder.mkdir(parents=True)
    text, changes = recipe()
    (folder / 'case.cfg').write_text(text.replace('ITER= 400', 'ITER= 1'), encoding='utf-8')
    free = read(CASE / 'contract.json')['derived_freestream']
    scaling = {'length_m': 1., 'density_kg_m3': free['rho_kg_m3'], 'velocity_m_s': free['U_m_s'] / .2,
               'temperature_K': 300., 'pressure_Pa': 1.4 * free['p_Pa']}
    save(PAIR / 'seed_contract.json', {'created_utc': now(), 'source_physics_contract_sha256': sha(CASE / 'contract.json'),
         'source_recipe': 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/TestCases/rans/oneram6/turb_ONERAM6_nk.cfg',
         'source_recipe_sha256': sha(BASE / 'convergence_sources/turb_ONERAM6_nk.cfg'),
         'common_changes_from_old_recipe': changes, 'scaling': scaling, 'mesh_sha256': sha(MESH),
         'seed_policy': 'One native iteration from uniform source freestream in the new scaling; identical binary result is copied to both arms. No old dimensional restart is reinterpreted.',
         'newton_adaptation': 'Source200 startup retained; full MUSCL products fixed1 instead of automatic-1 to make the method explicit.',
         'CFL_adaptation': 'Source four-entry list expanded to installed six-entry form; acceptable linear ratio0.2 matches the source-recipe linear tolerance0.2.',
         'not_blind': True, 'physical_changes': None,
         'residual_warning': 'Raw logs are nondimensional and must not be judged against prior dimensional residual thresholds. Pair effect compares the same normalization only.',
         'scope': 'Matrix-free finite-difference flow Jacobian; separately solved SA, not fully coupled flow+SA, not an adjoint or the arXiv smoothing implementation.'})
    snapshot(folder)
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    status = run_native([exe, 'case.cfg', '-t', '4'], folder, 'solver', 45,
                        dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    seal = freeze_folder(folder, PAIR / 'seed_contract.json', MESH)
    assert status['exit_code'] == 0 and seal['matched']['field_iteration'] == 0
    print('SEED FROZEN', seal['matched'], flush=True)


def prepare_pair():
    seed = PAIR / 'seed/restart_flow_000000.dat'
    prior = read(PAIR / 'seed/prediction_frozen.json')
    assert prior['files_sha256'][str(seed.relative_to(ROOT))] == sha(seed)
    text, _ = recipe()
    text = text.replace('RESTART_SOL= NO', 'RESTART_SOL= YES').replace('SOLUTION_FILENAME= restart_flow', 'SOLUTION_FILENAME= seed')
    cases = {}
    for name, enabled in [('quasi', 'NO'), ('newton', 'YES')]:
        folder = PAIR / name; folder.mkdir()
        (folder / 'case.cfg').write_text(text.replace('NEWTON_KRYLOV= NO', 'NEWTON_KRYLOV= ' + enabled), encoding='utf-8')
        shutil.copyfile(seed, folder / 'seed.dat')
        snapshot(folder)
        cases[name] = {'cfg_sha256': sha(folder / 'case.cfg'), 'seed_sha256': sha(folder / 'seed.dat')}
    a, b = [(PAIR / name / 'case.cfg').read_text().splitlines() for name in cases]
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    assert len(a) == len(b) and diff == [('NEWTON_KRYLOV= NO', 'NEWTON_KRYLOV= YES')]
    save(PAIR / 'contract.json', {'created_utc': now(), 'seed_contract_sha256': sha(PAIR / 'seed_contract.json'),
         'startup_policy_note': 'Pair uses source200 startup iterations, not unused20 in the earlier NO-NK seed draft. Cold-seed startup was reviewed before either paired run; seed state unchanged.',
         'seed_sha256': sha(seed), 'mesh_sha256': sha(MESH), 'cases': cases, 'only_config_difference': diff,
         'hypothesis': 'Finite-difference matrix-free mean-flow Jacobian improves late iteration progress relative to the first-order approximate Jacobian.',
         'comparison_iteration': 399, 'iterations': 400, 'seconds_each': 300, 'threads': 4,
         'density_log10_gain_min': .3, 'SA_log10_worsening_max': .1, 'same_nondimensionalization': True,
         'startup_identity_check_first_rows': 20, 'no_automatic_sweep': True,
         'physical_acceptance_claimed': False, 'not_blind': True})
    print('PAIR REGISTERED', cases, flush=True)


def run(name):
    c = read(PAIR / 'contract.json'); folder = PAIR / name
    assert not (folder / 'solver.process.json').exists()
    assert sha(folder / 'case.cfg') == c['cases'][name]['cfg_sha256'] and sha(folder / 'seed.dat') == c['seed_sha256']
    assert sha(MESH) == c['mesh_sha256']
    code = read(folder / 'runner_code_before_native.json')
    for p, h in code['files_sha256'].items(): assert sha(ROOT / p) == h
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    status = run_native([exe, 'case.cfg', '-t', '4'], folder, 'solver', c['seconds_each'],
                        dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    seal = freeze_folder(folder, PAIR / 'contract.json', MESH)
    print('FROZEN', name, status, seal['matched'], flush=True)


def compare():
    c = read(PAIR / 'contract.json')
    a, b = [read(PAIR / name / 'prediction_frozen.json') for name in ['quasi', 'newton']]
    count = 0
    for seal in [a, b]:
        for p, h in seal['files_sha256'].items(): assert sha(ROOT / p) == h; count += 1
    rows = [history(PAIR / name) for name in ['quasi', 'newton']]
    columns = ['rms[Rho]', 'rms[nu]', 'CD']
    delta = float(np.max(np.abs(np.array([[r[k] for k in columns] for r in rows[0][:20]]) -
                               np.array([[r[k] for k in columns] for r in rows[1][:20]]))))
    decision = evaluate(a, b, c['comparison_iteration'], c['density_log10_gain_min'], c['SA_log10_worsening_max'])
    save(REPORT, {'created_utc': now(), 'contract_sha256': sha(PAIR / 'contract.json'), 'quasi': a, 'newton': b,
                  'verified_files': count, 'startup_first20_max_log_or_CD_difference': delta, **decision,
                  'raw_residuals_same_nondimensionalization_only': True})
    print(decision, 'startup delta', delta, flush=True)


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'seed': prepare_seed()
    elif action == 'prepare': prepare_pair()
    elif action == 'run': run(sys.argv[2])
    elif action == 'compare': compare()
    else: raise ValueError(action)
