"""Source-motivated mean-flow FAS control, reusing the identical sealed MG0 arm."""
from prepare import ROOT, CASE, BASE, read, save, sha, now
from common import run_native, memory
from run import history
import cfl_control
import os
import shutil
import sys

PAIR = CASE / 'mg_control_v1'
CONTROL = CASE / 'fixed_cfl_pair_v1/cfl100'
REPORT = ROOT / 'outputs/reports/flatplate_multigrid_control_20261025.json'


def prepare():
    assert not PAIR.exists()
    a = read(CONTROL / 'prediction_frozen.json')
    for p, expected in a['files_sha256'].items(): assert sha(ROOT / p) == expected
    assert a['matched']['field_iteration'] == 399 and a['native_status']['exit_code'] == 0
    PAIR.mkdir()
    source = (CONTROL / 'case.cfg').read_text()
    for role, iterations in [('smoke', 20), ('mg2', 400)]:
        folder = PAIR / role
        folder.mkdir()
        text = source.replace('MGLEVEL= 0', 'MGLEVEL= 2').replace('ITER= 400', f'ITER= {iterations}')
        (folder / 'case.cfg').write_text(text, encoding='utf-8')
        shutil.copyfile(CONTROL / 'seed.dat', folder / 'seed.dat')
    target = (PAIR / 'mg2/case.cfg').read_text()
    differences = [(a, b) for a, b in zip(source.splitlines(), target.splitlines()) if a != b]
    assert len(source.splitlines()) == len(target.splitlines()) and differences == [('MGLEVEL= 0', 'MGLEVEL= 2')]
    contract = {'created_utc': now(), 'not_blind': True,
                'hypothesis': 'Agglomerated FAS mean-flow corrections reduce slowly damped error components; this is a test, not an observed error-spectrum diagnosis.',
                'sources': ['https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf',
                            'https://arxiv.org/html/1805.03756v1',
                            'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/CConfig.cpp'],
                'baseline': str(CONTROL.relative_to(ROOT)), 'baseline_seal_sha256': sha(CONTROL / 'prediction_frozen.json'),
                'baseline_reused_without_rerun': True, 'baseline_before_new_hypothesis': True,
                'seed_sha256': sha(CONTROL / 'seed.dat'), 'mesh_sha256': sha(CASE / 'meshes/fine.su2'),
                'only_config_difference': differences, 'target_config_sha256': sha(PAIR / 'mg2/case.cfg'),
                'comparison_iteration': 399, 'iterations': 400, 'seconds': 240, 'threads': 4,
                'density_log10_gain_min': .3, 'SA_log10_worsening_max': .1,
                'native_smoke_required': {'iterations': 20, 'seconds': 45},
                'policy': {'V_cycle': 'restart forces V cycle in CConfig', 'default_pre_smooth': [1, 2, 3],
                           'default_post_smooth': [0, 0, 0], 'default_correction_smooth': [0, 0, 0],
                           'restriction_and_prolongation_damping': [.5, .5],
                           'fine_flux': 'unchanged second-order Roe',
                           'coarse_flux': 'native agglomeration policy; first-order Roe on coarse levels',
                           'SA_transport': 'same fine-grid-only transport, same dt reduction default1'},
                'limits': ['Native FAS is not the residual-smoothed exact Newton method in the arXiv paper.',
                           'MG iterations have different work cost; no timing speedup inferred from iteration count.',
                           'This is a new flat-plate case test; prior M6 MG effect is not transferred as proof.'],
                'physical_changes': None, 'physical_acceptance_contract_sha256': sha(CASE / 'contract.json'),
                'conditional_next': 'Only if effect passes, register bounded same-policy continuation of fixed mesh roles. Otherwise no automatic MG/CFL sweep.'}
    save(PAIR / 'contract.json', contract)
    print({'prepared': str(PAIR), 'resources': memory()}, flush=True)


def run(role):
    c = read(PAIR / 'contract.json')
    folder = PAIR / role
    assert not (folder / 'solver.process.json').exists()
    assert sha(folder / 'seed.dat') == c['seed_sha256'] and sha(CASE / 'meshes/fine.su2') == c['mesh_sha256']
    if role == 'mg2':
        smoke = read(PAIR / 'smoke/prediction_frozen.json')
        assert smoke['native_status']['exit_code'] == 0 and smoke['matched']['field_iteration'] == 19
        assert sha(folder / 'case.cfg') == c['target_config_sha256']
    exe = read(ROOT / 'work/setup/su2_install.json')['executable']
    seconds = 45 if role == 'smoke' else c['seconds']
    status = run_native([exe, 'case.cfg', '-t', '4'], folder, 'solver', seconds,
                        dict(os.environ, OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE'), memory_cap_gib=2.5)
    seal = cfl_control.freeze_folder(folder, PAIR / 'contract.json')
    print('FROZEN', role, status, seal['matched'], flush=True)


def compare():
    c = read(PAIR / 'contract.json')
    a, b = [read(p / 'prediction_frozen.json') for p in [CONTROL, PAIR / 'mg2']]
    verified = 0
    for seal in [a, b]:
        for p, expected in seal['files_sha256'].items(): assert sha(ROOT / p) == expected; verified += 1
    am, bm = a['matched'], b['matched']
    decision = cfl_control.evaluate(a, b, c['comparison_iteration'], c['density_log10_gain_min'], c['SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    comparable, gain, worsening, effect = [decision[k] for k in ['comparable', 'density_log10_gain', 'SA_log10_worsening', 'effect_passed']]
    save(REPORT, {'created_utc': now(), 'contract_sha256': sha(PAIR / 'contract.json'), 'baseline': a, 'mg2': b,
                  'verified_files': verified, 'comparison_decision': decision, 'comparable': comparable, 'density_log10_gain': gain,
                  'SA_log10_worsening': worsening, 'effect_passed': effect, 'physical_qualification_passed': False})
    print({'gain': gain, 'SA_worsening': worsening, 'effect_passed': effect}, flush=True)


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': prepare()
    elif action == 'run': run(sys.argv[2])
    elif action == 'compare': compare()
    else: raise ValueError(action)
