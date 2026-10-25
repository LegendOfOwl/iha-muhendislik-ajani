"""Isolate the adaptive controller, not another CFL-value sweep."""
from prepare import ROOT, CASE, BASE, read, save, sha, now
from common import run_native
import cfl_control
import os
import shutil
import sys

PAIR = CASE / 'adaptive_toggle_v1'
CONTROL = CASE / 'fixed_cfl_pair_v1/cfl100'
REPORT = ROOT / 'outputs/reports/flatplate_adaptive_toggle_20261025.json'


def prepare():
    assert not PAIR.exists()
    fixed = read(CONTROL / 'prediction_frozen.json')
    for p, h in fixed['files_sha256'].items(): assert sha(ROOT / p) == h
    assert not read(ROOT / 'outputs/reports/flatplate_fixed_cfl_control_20261025.json')['effect_passed']
    PAIR.mkdir(); folder = PAIR / 'adaptive'; folder.mkdir()
    source = (CONTROL / 'case.cfg').read_text()
    text = source.replace('CFL_ADAPT= NO', 'CFL_ADAPT= YES')
    diff = [(a, b) for a, b in zip(source.splitlines(), text.splitlines()) if a != b]
    assert diff == [('CFL_ADAPT= NO', 'CFL_ADAPT= YES')]
    (folder / 'case.cfg').write_text(text, encoding='utf-8')
    shutil.copyfile(CONTROL / 'seed.dat', folder / 'seed.dat')
    contract = {'created_utc': now(), 'not_blind': True,
                'hypothesis': 'The adaptive growth/reset policy, rather than simply CFL100 itself, disrupts late convergence. Fixed100 is predicted to outperform the unchanged adaptive100..1e5 recipe.',
                'source': 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/config_template.cfg',
                'source_sha256': sha(BASE / 'convergence_sources/config_template.cfg'),
                'baseline_fixed100': str(CONTROL.relative_to(ROOT)), 'baseline_seal_sha256': sha(CONTROL / 'prediction_frozen.json'),
                'baseline_reused_without_rerun': True, 'baseline_before_new_hypothesis': True,
                'seed_sha256': sha(folder / 'seed.dat'), 'mesh_sha256': sha(CASE / 'meshes/fine.su2'),
                'config_sha256': sha(folder / 'case.cfg'), 'only_config_difference': diff,
                'comparison_iteration': 399, 'iterations': 400, 'seconds': 240, 'threads': 4,
                'effect_orientation': 'A=adaptive, B=fixed100; positive gain favors fixed100',
                'density_log10_gain_min': .3, 'SA_log10_worsening_max': .1,
                'physical_changes': None, 'physical_acceptance_contract_sha256': sha(CASE / 'contract.json'),
                'conditional_next': 'Only if effect passes, register a finite fixed100 continuation family with the original three meshes and frozen prior seeds. No further CFL-value sweep.',
                'no_automatic_extension_of_this_pair': True}
    save(PAIR / 'contract.json', contract)
    print({'prepared': str(PAIR), 'only_difference': diff}, flush=True)


def run():
    c = read(PAIR / 'contract.json'); folder = PAIR / 'adaptive'
    assert not (folder / 'solver.process.json').exists()
    assert sha(folder / 'case.cfg') == c['config_sha256'] and sha(folder / 'seed.dat') == c['seed_sha256']
    assert sha(CASE / 'meshes/fine.su2') == c['mesh_sha256']
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    status = run_native([exe, 'case.cfg', '-t', '4'], folder, 'solver', c['seconds'],
                        dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    seal = cfl_control.freeze_folder(folder, PAIR / 'contract.json')
    print('FROZEN', status, seal['matched'], flush=True)


def compare():
    c = read(PAIR / 'contract.json')
    adaptive, fixed = [read(p / 'prediction_frozen.json') for p in [PAIR / 'adaptive', CONTROL]]
    verified = 0
    for seal in [adaptive, fixed]:
        for p, h in seal['files_sha256'].items(): assert sha(ROOT / p) == h; verified += 1
    effect = cfl_control.evaluate(adaptive, fixed, c['comparison_iteration'], c['density_log10_gain_min'], c['SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    save(REPORT, {'created_utc': now(), 'contract_sha256': sha(PAIR / 'contract.json'), 'adaptive': adaptive,
                  'fixed100': fixed, 'verified_files': verified, **effect})
    print(effect, flush=True)


if __name__ == '__main__': {'prepare': prepare, 'run': run, 'compare': compare}[sys.argv[1]]()
