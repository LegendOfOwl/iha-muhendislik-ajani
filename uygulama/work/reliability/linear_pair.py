"""Pre-registered, bounded M6 linear-solver discrimination; never tune physics."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'outputs/projects/proje-e9319baef1'
BASE = PROJECT / 'simulations/m6_jst_wallnormal_20261024_v3'
RUN = PROJECT / 'simulations/m6_linear_pair_20261024'
REPORT = PROJECT / 'reports/m6_linear_pair_20261024.json'
TASK = ROOT / 'outputs/data/tasks/20261024-235336-d874a2.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def save(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    tmp.replace(p)


def cfg(p):
    result = {}
    for line in Path(p).read_text().splitlines():
        s = line.split('%', 1)[0].strip()
        if '=' in s:
            k, v = (a.strip() for a in s.split('=', 1))
            if k in result:
                raise ValueError('Duplicate config key: ' + k)
            result[k] = v
    return result


def history(p):
    with Path(p).open(newline='') as f:
        return [{k.strip().strip('"'): float(v) for k, v in row.items()}
                for row in csv.DictReader(f)]


def prepare():
    if RUN.exists():
        raise FileExistsError('Preserve every prior trial: ' + str(RUN))
    seal = PROJECT / 'reports/m6_wallnormal_prediction_frozen_20261024_v3.json'
    prior = read(seal)
    bad = [p for p, h in prior['files_sha256'].items() if sha(ROOT / p) != h]
    if bad:
        raise ValueError('Changed frozen source: ' + str(bad))
    selected = prior['selection']['field_iteration']
    assert selected == 2999
    original = cfg(BASE / 'case.cfg')
    assert original['LINEAR_SOLVER_ITER'] == '10'
    assert original['LINEAR_SOLVER_ERROR'] == '1e-05'
    assert original['CFL_ADAPT'] == 'NO' and original['CFL_NUMBER'] == '4'
    assert original['CONV_NUM_METHOD_FLOW'] == 'JST' and original['MUSCL_FLOW'] == 'NO'
    RUN.mkdir(parents=True)
    executable = Path(read(ROOT / 'work/setup/su2_install.json')['executable'])
    source = {str(p.relative_to(ROOT)): sha(p) for p in
              [BASE / 'case.cfg', BASE / 'mesh.su2', BASE / f'restart_flow_{selected:06d}.dat', seal]}
    for limit in [10, 40]:
        folder = RUN / f'lin{limit}'
        folder.mkdir()
        shutil.copyfile(BASE / 'mesh.su2', folder / 'mesh.su2')
        shutil.copyfile(BASE / f'restart_flow_{selected:06d}.dat', folder / 'seed.dat')
        d = dict(original)
        d.update(ITER='1000', LINEAR_SOLVER_ITER=str(limit), SOLUTION_FILENAME='seed')
        (folder / 'case.cfg').write_text('\n'.join(f'{k}= {v}' for k, v in d.items()) + '\n', encoding='ascii')
    a, b = [cfg(RUN / f'lin{n}/case.cfg') for n in [10, 40]]
    different = [k for k in a.keys() | b.keys() if a.get(k) != b.get(k)]
    assert different == ['LINEAR_SOLVER_ITER']
    assert sha(RUN / 'lin10/seed.dat') == sha(RUN / 'lin40/seed.dat')
    assert sha(RUN / 'lin10/mesh.su2') == sha(RUN / 'lin40/mesh.su2')
    contract = {
        'version': 1, 'created_utc': now(), 'project_id': 'proje-e9319baef1',
        'hypothesis': 'The active linear iteration cap materially limits nonlinear convergence. This is a hypothesis, not an established cause.',
        'source_hashes': source, 'source_frozen_files_verified': len(prior['files_sha256']),
        'same_source_checkpoint': selected, 'only_pair_difference': different,
        'executable': str(executable.relative_to(ROOT)), 'executable_sha256': sha(executable),
        'iterations_each': 1000, 'max_seconds_each': 1500, 'threads': 4,
        'order': ['lin10', 'lin40'], 'concurrent_runs': False,
        'thresholds_unchanged': read(BASE / 'contract.json')['thresholds'],
        'diagnostic_effect_rule': {
            'native_outcome_required': 'Both native exits zero and matched complete checkpoints at iteration999',
            'meaningful_extra_log10_reduction': 0.3,
            'interpretation': 'A preselected diagnostic effect size, not a physical acceptance threshold or a statistical confidence level.',
            'insufficient_effect_action': 'Reject the cap increase as an evidenced cure; do not sweep more caps.',
            'cost': 'Report both equal nonlinear iteration counts and observed time/linear work; single-order timing is not a hardware benchmark.'},
        'not_blind': True, 'no_targets_in_configs': True,
        'scope': 'Numerical mechanism discrimination on one fixed M6 mesh; no new mesh independence, physical validation, or LLM-behaviour evaluation.',
        'plan_after': 'Compare coupled residuals and force windows; if iteration error remains, do not interpret spatial indicators as quantified discretization error.',
        'code_sha256': sha(__file__),
        'cases': {f'lin{n}': {p.name: sha(p) for p in (RUN / f'lin{n}').iterdir()} for n in [10, 40]},
    }
    save(RUN / 'contract.json', contract)
    sys.path.insert(0, str(ROOT / 'work/agent'))
    from learning import instruction_snapshot
    task = read(TASK)
    task.update(status='çalışıyor', phase='araç doğrulama',
                applied_lesson_ids=['L03', 'L04', 'L05', 'L07', 'L08', 'L09'],
                agent_instruction_snapshot=instruction_snapshot(ROOT),
                acceptance=['Kaynaklı yöntem araştırması', 'Aynı kaynakla mühürlü tek değişkenli native karşılaştırma',
                            'Yanlış kabulü durduran ve sonraki denemeyi gerekçelendiren denetçi',
                            'Gerçek alanla konumsal gösterge; hata bandı ve fizik kabulüyle karıştırmama',
                            'Başarısızlıklar ve açık kapılar dahil rapor'],
                experiment_contract=str((RUN / 'contract.json').relative_to(ROOT)))
    save(TASK, task)
    print(json.dumps({'prepared': True, 'source_files_verified': len(prior['files_sha256']), 'folder': str(RUN)}, ensure_ascii=False))


def run():
    contract = read(RUN / 'contract.json')
    executable = ROOT / contract['executable']
    assert sha(executable) == contract['executable_sha256']
    for name in contract['order']:
        folder = RUN / name
        assert not (folder / 'process.json').exists(), 'Do not repeat an attempt in place'
        for f, h in contract['cases'][name].items():
            assert sha(folder / f) == h
        start = time.monotonic()
        stamp = now()
        with (folder / 'solver.log').open('w', encoding='utf-8') as log:
            p = subprocess.Popen([str(executable), 'case.cfg', '-t', str(contract['threads'])], cwd=folder,
                                 env=dict(os.environ, OMP_NUM_THREADS=str(contract['threads']), OMP_WAIT_POLICY='PASSIVE'),
                                 stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            save(folder / 'process.json', {'pid': p.pid, 'started_utc': stamp,
                                          'budget_seconds': contract['max_seconds_each'], 'threads': contract['threads']})
            print(json.dumps({'started': name, 'pid': p.pid}), flush=True)
            try:
                code = p.wait(timeout=contract['max_seconds_each'])
                status = 'exited'
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
                code, status = None, 'timeout_partial_preserved'
        save(folder / 'run_status.json', {'status': status, 'exit_code': code, 'started_utc': stamp,
                                         'ended_utc': now(), 'seconds': time.monotonic() - start})
        print(json.dumps({'ended': name, 'status': status, 'exit_code': code}), flush=True)


def freeze():
    contract = read(RUN / 'contract.json')
    for name in contract['order']:
        folder = RUN / name
        assert (folder / 'run_status.json').exists()
        seal = folder / 'prediction_frozen.json'
        assert not seal.exists(), 'Never replace a frozen prediction'
        rows = history(folder / 'history.csv') if (folder / 'history.csv').exists() else []
        sets = []
        for prefix, ext in [('flow', 'vtu'), ('surface_flow', 'vtu'), ('restart_flow', 'dat')]:
            sets.append({int(p.stem.rsplit('_', 1)[-1]) for p in folder.glob(f'{prefix}_*.{ext}')
                         if p.stem.rsplit('_', 1)[-1].isdigit()})
        common = set.intersection(*sets) & {int(r['Inner_Iter']) for r in rows}
        selected = max(common) if common else None
        matched = None
        if selected is not None:
            row = next(r for r in rows if r['Inner_Iter'] == selected)
            tail = [r for r in rows if selected - 99 <= r['Inner_Iter'] <= selected]
            assert len(tail) == 100
            limits = contract['thresholds_unchanged']
            values = {k: row[k] for k in ['CL', 'CD', 'rms[Rho]', 'rms[nu]']}
            assert all(math.isfinite(v) for v in values.values())
            matched = {'field_iteration': selected, 'terminal_history_iteration': rows[-1]['Inner_Iter'],
                       **values, 'CL_last100_range': max(r['CL'] for r in tail) - min(r['CL'] for r in tail),
                       'CD_last100_range': max(r['CD'] for r in tail) - min(r['CD'] for r in tail),
                       'linear_cap_fraction_last100': sum(r['Linear_Solver_Iterations'] >= int(name[3:]) for r in tail) / 100,
                       'linear_iterations_mean_last100': sum(r['Linear_Solver_Iterations'] for r in tail) / 100,
                       'linear_log10_median_last100': sorted(r['LinSolRes'] for r in tail)[50],
                       'linear_work_total': sum(r['Linear_Solver_Iterations'] for r in rows),
                       'turb_linear_work_total': sum(r['LinSolIterTurb'] for r in rows)}
            matched['iteration_checks'] = {
                'density': row['rms[Rho]'] < limits['density_log10_max'],
                'CL_window': matched['CL_last100_range'] < limits['CL_last100_range_max'],
                'CD_window': matched['CD_last100_range'] < limits['CD_last100_range_max']}
        save(seal, {'frozen_utc': now(), 'no_new_experimental_score_yet': True, 'not_blind': True,
                    'matched': matched, 'contract_sha256': sha(RUN / 'contract.json'),
                    'files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in folder.rglob('*') if p.is_file()}})
    print(json.dumps({'frozen': contract['order']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run', 'freeze'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run, 'freeze': freeze}[args.action]()
