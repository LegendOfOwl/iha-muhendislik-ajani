"""Separate late-stage Jacobian behavior from the earlier cold-start transient."""
from prepare import ROOT, BASE, CASE, read, save, sha, now
from common import run_native
from cfl_control import freeze_folder, evaluate
from newton_control import recipe, snapshot
from scaled_restart import dimensional_matched
from run import history
import os
import shutil
import sys

PAIR = CASE / 'newton_warm_control_v1'
REPORT = ROOT / 'outputs/reports/flatplate_newton_warm_control_20261025.json'
SEED = CASE / 'warm_scaling_pair_v1/scaled/seed.dat'


def prepare():
    assert not PAIR.exists()
    check = read(CASE / 'warm_scaling_pair_v1/contract.json')
    assert sha(SEED) == check['target_seed_sha256']
    PAIR.mkdir()
    text, _ = recipe()
    text = text.replace('RESTART_SOL= NO', 'RESTART_SOL= YES').replace('SOLUTION_FILENAME= restart_flow', 'SOLUTION_FILENAME= seed')
    text = text.replace('NEWTON_KRYLOV_IPARAM= (200,0,1)', 'NEWTON_KRYLOV_IPARAM= (0,0,1)')
    cases = {}
    for name, flag in [('quasi', 'NO'), ('newton', 'YES')]:
        f = PAIR / name; f.mkdir()
        (f / 'case.cfg').write_text(text.replace('NEWTON_KRYLOV= NO', 'NEWTON_KRYLOV= ' + flag), encoding='utf-8')
        shutil.copyfile(SEED, f / 'seed.dat'); snapshot(f)
        shutil.copyfile(BASE / 'newton_warm_control.py', f / 'runner_code/newton_warm_control.py')
        code = read(f / 'runner_code_before_native.json')
        code['files_sha256'][str((f / 'runner_code/newton_warm_control.py').relative_to(ROOT))] = sha(f / 'runner_code/newton_warm_control.py')
        save(f / 'runner_code_before_native.json', code)
        cases[name] = {'config_sha256': sha(f / 'case.cfg'), 'seed_sha256': sha(f / 'seed.dat')}
    a, b = [(PAIR / n / 'case.cfg').read_text().splitlines() for n in cases]
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    assert len(a) == len(b) and diff == [('NEWTON_KRYLOV= NO', 'NEWTON_KRYLOV= YES')]
    save(PAIR / 'contract.json', {'created_utc': now(), 'cases': cases, 'seed_sha256': sha(SEED),
         'same_physical_seed_conversion_contract_sha256': sha(CASE / 'warm_scaling_pair_v1/contract.json'),
         'mesh_sha256': sha(CASE / 'meshes/medium.su2'), 'only_config_difference': diff,
         'hypothesis': 'The cold-start control does not isolate late-stage Jacobian behavior. Use the same developed source state in both arms, with Newton active immediately.',
         'comparison_iteration': 399, 'iterations': 400, 'seconds_each': 180, 'threads': 4,
         'density_log10_gain_min': .3, 'SA_log10_worsening_max': .1,
         'sources': ['https://raw.githubusercontent.com/su2code/SU2/v8.5.0/TestCases/rans/oneram6/turb_ONERAM6_nk.cfg',
                     'https://arxiv.org/html/1805.03756v1'],
         'no_cold_vs_warm_causal_attribution': 'The source-based startup delay changes from200 to0 in both warm arms. Only within-pair Newton on/off has causal interpretation.',
         'no_further_extension_or_sweep_in_this_batch': True, 'physical_changes': None, 'not_blind': True})
    print('WARM PAIR REGISTERED', cases, flush=True)


def run(name):
    c = read(PAIR / 'contract.json'); f = PAIR / name
    assert not (f / 'solver.process.json').exists()
    assert sha(f / 'case.cfg') == c['cases'][name]['config_sha256'] and sha(f / 'seed.dat') == c['seed_sha256']
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    s = run_native([exe, 'case.cfg', '-t', '4'], f, 'solver', c['seconds_each'],
                   dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    frozen = freeze_folder(f, PAIR / 'contract.json', CASE / 'meshes/medium.su2')
    print('FROZEN', name, s, frozen['matched'], flush=True)


def compare():
    c = read(PAIR / 'contract.json'); free = read(CASE / 'contract.json')['derived_freestream']
    a, b = [read(PAIR / n / 'prediction_frozen.json') for n in ['quasi', 'newton']]
    count = 0
    for seal in [a, b]:
        for p, h in seal['files_sha256'].items(): assert sha(ROOT / p) == h; count += 1
    ad, bd = [dimensional_matched(s, free) for s in [a, b]]
    decision = evaluate(ad, bd, c['comparison_iteration'], c['density_log10_gain_min'], c['SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    save(REPORT, {'created_utc': now(), 'contract_sha256': sha(PAIR / 'contract.json'), 'quasi_raw': a, 'newton_raw': b,
                  'quasi_SI': ad, 'newton_SI': bd, 'verified_files': count, **decision})
    print(decision, flush=True)


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': prepare()
    elif action == 'run': run(sys.argv[2])
    elif action == 'compare': compare()
    else: raise ValueError(action)
