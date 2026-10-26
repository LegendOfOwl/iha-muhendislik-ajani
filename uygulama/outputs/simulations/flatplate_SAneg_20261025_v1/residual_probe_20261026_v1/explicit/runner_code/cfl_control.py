"""Execute the previously registered fixed-CFL pair; never overwrite a prediction."""
from prepare import ROOT, CASE, read, save, sha, now
from common import run_native, memory
from run import history
import math
import os
import shutil
import sys
sys.path.insert(0, str(ROOT / 'work/reliability'))
from paired_control import evaluate

PAIR = CASE / 'fixed_cfl_pair_v1'
REGISTERED = CASE / 'next_numerical_control_not_run.json'
REPORT = ROOT / 'outputs/reports/flatplate_fixed_cfl_control_20261025.json'


def prepare():
    assert not PAIR.exists(), 'A registered run directory must not be reused'
    registered = read(REGISTERED)
    seed, mesh = (ROOT / registered[k] for k in ('seed', 'mesh'))
    assert sha(seed) == registered['seed_sha256']
    assert sha(mesh) == registered['mesh_sha256']
    prior = read(CASE / 'fine_nested/prediction_frozen.json')
    assert prior['files_sha256'][str(seed.relative_to(ROOT))] == sha(seed)
    source = (CASE / 'fine_nested/case.cfg').read_text()
    replacements = {'ITER= 2000': 'ITER= 400', 'CFL_ADAPT= YES': 'CFL_ADAPT= NO',
                    'CONV_STARTITER= 200': 'CONV_STARTITER= 1000',
                    'MESH_FILENAME= ../meshes/fine.su2': 'MESH_FILENAME= ../../meshes/fine.su2'}
    for old, new in replacements.items():
        assert source.splitlines().count(old) == 1
        source = source.replace(old, new)
    PAIR.mkdir()
    cases = {}
    for name, cfl in [('cfl100', 100), ('cfl10', 10)]:
        folder = PAIR / name
        folder.mkdir()
        text = source.replace('CFL_NUMBER= 100\n', f'CFL_NUMBER= {cfl}\n')
        (folder / 'case.cfg').write_text(text, encoding='utf-8')
        shutil.copyfile(seed, folder / 'seed.dat')
        cases[name] = {'cfg_sha256': sha(folder / 'case.cfg'), 'seed_sha256': sha(folder / 'seed.dat')}
    lines = [(PAIR / name / 'case.cfg').read_text().splitlines() for name in cases]
    diff = [(a, b) for a, b in zip(*lines) if a != b]
    assert len(lines[0]) == len(lines[1]) and diff == [('CFL_NUMBER= 100', 'CFL_NUMBER= 10')]
    contract = {'created_utc': now(), 'registered_contract': str(REGISTERED.relative_to(ROOT)),
                'registered_sha256': sha(REGISTERED), 'original_prepared_status_preserved': True,
                'cases': cases, 'mesh_sha256': sha(mesh), 'seed_sha256': sha(seed),
                'only_config_difference': diff, 'common_policy_changes_from_adaptive_parent': replacements,
                'comparison_iteration': 399, 'iterations_each': 400, 'seconds_each': 240,
                'threads_each': 4, 'density_log10_gain_min': .3, 'SA_log10_worsening_max': .1,
                'physical_acceptance_contract_sha256': sha(CASE / 'contract.json'),
                'no_automatic_extension': True, 'not_blind': True}
    save(PAIR / 'contract.json', contract)
    sys.path.insert(0, str(ROOT / 'work/agent'))
    from project import make_task
    from learning import instruction_snapshot
    taskpath = make_task('Düz plaka yakınsaması: ön kayıtlı sabit CFL100/10 kontrolü ve kaynaklı neden araştırması',
                         kind='qualification', project_id='qualification')
    task = read(taskpath)
    task.update(status='çalışıyor', phase='aynı başlangıçlı sayısal hipotez kontrolü',
                acceptance=['400 ortak adım; yalnız CFL_NUMBER farkı', 'Ham başarısızlıkları ve aynı iterasyon alan/geçmişini mühürle',
                            'Etki eşiğini fiziksel yeterlilikten ayır; kaynakla sonraki mekanizmayı seç'],
                applied_lesson_ids=['L04', 'L05', 'L07', 'L08', 'L09', 'L10', 'R01', 'R03'],
                agent_instruction_snapshot=instruction_snapshot(ROOT), contract=str((PAIR / 'contract.json').relative_to(ROOT)),
                contract_sha256=sha(PAIR / 'contract.json'))
    save(taskpath, task)
    save(PAIR / 'task.json', {'path': str(taskpath.relative_to(ROOT))})
    print({'prepared': str(PAIR), 'task': str(taskpath), 'resources': memory()}, flush=True)


def freeze(name):
    folder = PAIR / name
    return freeze_folder(folder, PAIR / 'contract.json')


def freeze_folder(folder, contract, mesh=None):
    target = folder / 'prediction_frozen.json'
    assert not target.exists()
    rows = history(folder)
    sets = []
    for prefix, ext in [('flow', 'vtu'), ('surface_flow', 'vtu'), ('restart_flow', 'dat')]:
        sets.append({int(p.stem.rsplit('_', 1)[-1]) for p in folder.glob(f'{prefix}_*.{ext}')
                     if p.stem.rsplit('_', 1)[-1].isdigit()})
    common = set.intersection(*sets) & {int(r['Inner_Iter']) for r in rows}
    matched = None
    if common:
        i = max(common)
        row = next(r for r in rows if r['Inner_Iter'] == i)
        tail = [r for r in rows if i - 99 <= r['Inner_Iter'] <= i]
        keys = [k for k in row if k.startswith('rms[')] + ['CL', 'CD', 'LinSolRes', 'Linear_Solver_Iterations']
        matched = {'field_iteration': i, 'terminal_history_iteration': int(rows[-1]['Inner_Iter']),
                   **{k: row[k] for k in keys}, 'last100_samples': len(tail),
                   'CD_last100_range': max(r['CD'] for r in tail) - min(r['CD'] for r in tail)}
        assert all(math.isfinite(v) for v in matched.values())
    seal = {'frozen_utc': now(), 'not_blind': True, 'contract_sha256': sha(contract),
            'mesh_sha256': sha(mesh or CASE / 'meshes/fine.su2'), 'matched': matched,
            'native_status': read(folder / 'solver.status.json'),
            'files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in folder.iterdir() if p.is_file()}}
    save(target, seal)
    return seal


def run(name):
    contract = read(PAIR / 'contract.json')
    folder = PAIR / name
    assert not (folder / 'solver.process.json').exists(), 'Do not duplicate a native process'
    assert sha(REGISTERED) == contract['registered_sha256']
    assert sha(CASE / 'meshes/fine.su2') == contract['mesh_sha256']
    assert sha(folder / 'seed.dat') == contract['seed_sha256']
    assert sha(folder / 'case.cfg') == contract['cases'][name]['cfg_sha256']
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    print('START', name, memory(), flush=True)
    status = run_native([exe, 'case.cfg', '-t', '4'], folder, 'solver', contract['seconds_each'],
                        dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    seal = freeze(name)
    print('FROZEN', name, status, seal['matched'], flush=True)


def compare():
    contract = read(PAIR / 'contract.json')
    cases = {name: read(PAIR / name / 'prediction_frozen.json') for name in contract['cases']}
    verified = 0
    for name, seal in cases.items():
        for p, expected in seal['files_sha256'].items():
            assert sha(ROOT / p) == expected, p
            verified += 1
    a, b = [cases[name]['matched'] for name in ('cfl100', 'cfl10')]
    decision = evaluate(cases['cfl100'], cases['cfl10'], contract['comparison_iteration'],
                        contract['density_log10_gain_min'], contract['SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    comparable, gain, worsening, effect = [decision[k] for k in ['comparable', 'density_log10_gain', 'SA_log10_worsening', 'effect_passed']]
    save(REPORT, {'created_utc': now(), 'contract_sha256': sha(PAIR / 'contract.json'),
                  'cases': cases, 'verified_files': verified, 'comparison_decision': decision, 'comparable_at_preregistered_iteration': comparable,
                  'density_log10_gain_B_over_A': gain, 'SA_log10_worsening_B_over_A': worsening,
                  'effect_passed': effect, 'physical_qualification_passed': False,
                  'limits': ['One fine-grid checkpoint; not adaptive-on/off isolation or general optimal CFL.',
                             'Effect test is separate from original three-grid physical acceptance.']})
    print({'comparable': comparable, 'density_gain': gain, 'SA_worsening': worsening, 'effect_passed': effect}, flush=True)


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': prepare()
    elif action == 'run': run(sys.argv[2])
    elif action == 'compare': compare()
    else: raise ValueError(action)
