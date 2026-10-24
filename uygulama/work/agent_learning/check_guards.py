"""Adversarial artifact tests, not an LLM or engineering expertise benchmark."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'work/agent'))
from guards import boundary_nodes, complete_checkpoint, raw_below, required_gates, su2_policy
from learning import instruction_snapshot
import project

RESULTS = []


def check(name, operation):
    try:
        operation()
        RESULTS.append({'name': name, 'passed': True})
    except Exception as exc:
        RESULTS.append({'name': name, 'passed': False, 'error': repr(exc)})


def equal(actual, expected):
    assert actual == expected, (actual, expected)


def rejects(operation):
    try:
        operation()
    except ValueError:
        return
    raise AssertionError('Invalid case was accepted')


def main():
    check('triangle with a trailing ID that is also a valid node',
          lambda: equal(boundary_nodes('5 4 1 7 2', 9), (4, 1, 7)))
    check('quad with trailing ID larger than point count',
          lambda: equal(boundary_nodes('9 4 1 7 2 999', 9), (4, 1, 7, 2)))
    check('triangle without trailing ID', lambda: equal(boundary_nodes('5 4 1 7', 9), (4, 1, 7)))
    check('2D edge uses the dimension-specific type', lambda: equal(boundary_nodes('3 7 2 3', 9, 2), (7, 2)))
    for label, text in [('truncated', '9 0 1 2'), ('extra', '5 0 1 2 3 4'),
                        ('repeated', '5 0 1 1'), ('range', '5 0 1 9'),
                        ('volume-type-as-boundary', '10 0 1 2 3')]:
        check('boundary rejects ' + label, lambda text=text: rejects(lambda: boundary_nodes(text, 9)))

    m6 = ROOT / 'outputs/projects/proje-e9319baef1'
    bad = (m6 / 'simulations/m6_jst_control_20261024/case.cfg').read_text()
    good = (m6 / 'simulations/m6_jst_control_20261024_v2/case.cfg').read_text()
    check('archived native-rejected JST config is caught', lambda: rejects(lambda: su2_policy(bad, '8.5.0')))
    check('archived corrected config is covered', lambda: equal(su2_policy(good, '8.5.0')['covered'], True))
    check('other version is not silently certified', lambda: equal(su2_policy(good, '9.0')['covered'], False))
    check('missing MUSCL is not guessed', lambda: rejects(lambda: su2_policy('CONV_NUM_METHOD_FLOW=JST', '8.5.0')))

    # The actual frozen production checker is exercised without running its main.
    spec = importlib.util.spec_from_file_location('frozen_wedge', ROOT / 'work/m6_followup/wallnormal_mesh.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    unit = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                      [0., 0., 1.], [1., 0., 1.], [0., 1., 1.]]])
    check('analytic unit wedge has determinant 0.5',
          lambda: equal(abs(float(module.wedge_minimum(unit)[0]) - .5) < 1e-14, True))
    check('inverted wedge remains rejected',
          lambda: equal(float(module.wedge_minimum(unit[:, [0, 2, 1, 3, 5, 4]])[0]) < 0, True))
    collapsed = unit.copy(); collapsed[:, 3:] = collapsed[:, :3]
    check('collapsed wedge remains rejected', lambda: equal(float(module.wedge_minimum(collapsed)[0]) <= 0, True))
    folded = unit.copy(); folded[:, 5, 2] = -1.
    check('locally folded wedge remains rejected', lambda: equal(float(module.wedge_minimum(folded)[0]) < 0, True))

    with tempfile.TemporaryDirectory(prefix='agent_guard_') as folder:
        temp = Path(folder)
        records = []
        identity = {'geometry': 'test-geometry', 'mesh': 'test-mesh', 'conditions': 'test-conditions'}
        for role in ('surface', 'volume', 'restart'):
            path = temp / (role + '.bin'); path.write_bytes(role.encode())
            records.append({'role': role, 'path': str(path), 'iteration': 40,
                            'case_identity': identity,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        check('later terminal history does not replace selected complete field',
              lambda: equal(complete_checkpoint(records, [40, 47], identity)['iteration'], 40))
        check('requested newer history without fields rejected',
              lambda: rejects(lambda: complete_checkpoint(records, [40, 47], identity, requested=47)))
        check('missing volume rejected', lambda: rejects(lambda: complete_checkpoint(records[::2], [40], identity)))
        check('no matching history rejected', lambda: rejects(lambda: complete_checkpoint(records, [47], identity)))
        wrong = copy.deepcopy(records); wrong[1]['case_identity']['mesh'] = 'other-mesh'
        check('cross-mesh field mix rejected', lambda: rejects(lambda: complete_checkpoint(wrong, [40], identity)))
        changed = copy.deepcopy(records); changed[1]['sha256'] = '0' * 64
        check('changed field bytes rejected', lambda: rejects(lambda: complete_checkpoint(changed, [40], identity)))

        # Test the real GUI launch function with an isolated task and mocked process.
        sandbox = temp / 'launch'; tasks = sandbox / 'outputs/data/tasks'; tasks.mkdir(parents=True)
        for relative in instruction_snapshot(ROOT)['files']:
            dest = sandbox / relative; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, dest)
        cli = sandbox / 'fake-codex.exe'; cli.write_text('never executed')
        cfg = sandbox / 'work/setup/tool_config.json'; cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({'codex_cli': str(cli)}))
        task = tasks / 'fixture.json'; initial = {'id': 'fixture', 'request': 'new geometry validation', 'status': 'bekliyor'}
        task.write_text(json.dumps(initial))
        with patch.object(project, 'ROOT', sandbox), patch.object(project, 'OUT', sandbox / 'outputs'):
            before = task.read_bytes(); dry = project.launch(task, dry=True)
            check('dry launch leaves task unchanged', lambda: equal(task.read_bytes(), before))
            check('launch carries current operational prompt version',
                  lambda: equal(dry['instruction_snapshot'], instruction_snapshot(sandbox)))
            check('launch explicitly loads operational lessons',
                  lambda: equal('references/operational_lessons.json' in dry['prompt'], True))
            with patch.object(project.subprocess, 'Popen') as process:
                project.launch(task, dry=False)
                saved = json.loads(task.read_text())
                check('actual launch branch persists the same instruction snapshot',
                      lambda: equal(saved['agent_instruction_snapshot'], dry['instruction_snapshot']))
                check('launch calls process exactly once without running a live agent',
                      lambda: equal(process.call_count, 1))

    rae = json.loads((ROOT / 'outputs/projects/proje-15cce2de02/simulations/v3_r4roe_firstorder_cont4200/prediction_metrics.json').read_text())
    check('archived residual near threshold still fails before rounding',
          lambda: equal(raw_below(rae['density_log10_residual'], -8), False))
    check('exact threshold does not pass strict inequality', lambda: equal(raw_below(-8., -8.), False))
    check('genuinely lower value passes strict inequality', lambda: equal(raw_below(-8.001, -8.), True))
    for label, value in [('missing', None), ('nan', float('nan')), ('infinite', float('-inf')), ('bool', True)]:
        check('raw comparison rejects ' + label, lambda value=value: equal(raw_below(value, 1), False))
    check('missing required gate fails', lambda: equal(required_gates(['mesh', 'experiment'], {'mesh': True})['passed'], False))
    check('truthy string is not a passing gate', lambda: equal(required_gates(['mesh'], {'mesh': 'true'})['passed'], False))
    check('empty contract is rejected', lambda: rejects(lambda: required_gates([], {})))
    result = json.loads((m6 / 'reports/m6_wallnormal_results_20261024_v3.json').read_text())
    check('stable forces with failed residual remain unqualified',
          lambda: equal(required_gates(['density', 'CL_window', 'CD_window'], result['matched']['iteration_checks'])['passed'], False))
    # Fault reproductions are hand-written coding counterexamples, not old LLM scores.
    counterexamples = {
        'all_tokens_parser': tuple(int(v) for v in '5 4 1 7 2'.split()[1:]) != (4, 1, 7),
        'rounded_residual_pass': round(rae['density_log10_residual'], 1) <= -8,
        'terminal_history_field_mix': max([40, 47]) != 40,
        'any_gate_instead_of_all': any(result['matched']['iteration_checks'].values()),
    }
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Artifact/coding guard tests and launcher integration; no new LLM, CAD or CFD physical evaluation',
              'passed': all(r['passed'] for r in RESULTS), 'checks': RESULTS,
              'passed_count': sum(r['passed'] for r in RESULTS), 'total': len(RESULTS),
              'fault_reproductions_caught': counterexamples,
              'llm_behavior_improvement_measured': False,
              'unseen_engineering_task_tested': False, 'expert_qualification_passed': False,
              'instruction_snapshot': instruction_snapshot(ROOT)}
    dest = ROOT / 'outputs/reports/agent_learning_checks_20261024.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'checks': f"{report['passed_count']}/{report['total']}",
                      'failures': [r for r in RESULTS if not r['passed']]}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
