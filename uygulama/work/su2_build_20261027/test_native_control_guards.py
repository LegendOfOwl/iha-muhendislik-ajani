"""Controller counterexamples using tiny fake build artifacts, never a solver.

Only the native launcher, field freezer and environment/memory readers are
stubbed. Contract/source/tool hash guards execute against temporary real files.
The fake .exe files are inert text and are never executed.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import native_control as controller
from build_su2 import CAP_FILE, PIN, fingerprint, patch_cap, tree_files


REPORT = Path(__file__).resolve().parents[2] / 'outputs/reports/su2_native_controller_checks_20261027.json'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2), encoding='utf-8')


def binary(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


class NativeControllerGuards(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='su2-controller-guard-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / 'work/su2_build_20261027'
        self.case = self.root / 'outputs/simulations/controller-fixture'
        self.home = self.root / 'tools/su2-build/v8.5.0/controls'
        for folder in (self.base, self.case, self.home):
            folder.mkdir(parents=True)
        replacement = patch.multiple(controller, ROOT=self.root, BASE=self.base,
                                     CASE=self.case, HOME=self.home)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.native = Mock(name='native_launcher', side_effect=RuntimeError('Native must remain stubbed'))
        replacement = patch.multiple(controller, run_native=self.native,
                                     freeze_folder=Mock(name='field_freezer'), memory=Mock(return_value={}))
        replacement.start()
        self.addCleanup(replacement.stop)
        self.compiler = binary(self.root / 'fixture/compiler.exe', b'fake compiler, never execute')
        self.runtime = binary(self.root / 'fixture/runtime.dll', b'fake runtime, never load')
        self.statuses, self.contracts = {}, {}
        self.make_build('p32', 32)
        self.make_build('p256', 256)
        live = binary(self.base / 'live_handler.py', b'original handler\n')
        copied = binary(self.case / 'runner_code/live_handler.py', live.read_bytes())
        mesh = binary(self.root / 'fixture/mesh.su2', b'fake mesh; not read by a solver')
        seed = b'fake seed; never read by a solver'
        cases = {}
        for arm in ('release32', 'build32', 'build256'):
            folder = self.case / arm
            cfg = binary(folder / 'case.cfg', b'fixture configuration, never executed\n')
            seed_path = binary(folder / 'seed.dat', seed)
            cases[arm] = {'config_sha256': controller.sha(cfg), 'seed_sha256': controller.sha(seed_path)}
        write(self.base / 'method_design.json', {
            'decision_contract_limits': {'density_gain_min': .3, 'SA_worsening_max': .1}})
        self.case_contract = {
            'design_sha256': controller.sha(self.base / 'method_design.json'),
            'decision_contract': {'density_gain_min': .3, 'SA_worsening_max': .1,
                                  'pristine_source_tree_sha256': self.statuses['p32']['source_tree_sha256']},
            'live_code_before_native_sha256': {str(live.relative_to(self.root)): controller.sha(live)},
            'code_before_native_sha256': {str(copied.relative_to(self.root)): controller.sha(copied)},
            'cases': cases, 'mesh': str(mesh.relative_to(self.root)), 'mesh_sha256': controller.sha(mesh),
            'pristine_build': 'p32',
            'pristine_build_status_sha256': controller.sha(self.home / 'p32/status.json'),
            'native_resources': {'seconds_each': 240},
        }
        self.reseal_case()
        write(self.case / 'reproduction.json', {'accepted': True})

    def make_build(self, label, cap):
        folder = self.home / label
        original = b'enum : unsigned long { MAX_LINELET_POINTS = 32 };\n'
        binary(folder / 'source' / CAP_FILE, original if cap == 32 else patch_cap(original))
        binary(folder / 'source/other.cpp', b'unchanged engineering source\n')
        executable = binary(folder / 'build/SU2_CFD.exe', b'inert fake executable ' + str(cap).encode())
        patch_path = binary(folder / 'source.patch', b'' if cap == 32 else b'fixture cap32 -> cap256 diff\n')
        runtime = {str(self.runtime.relative_to(self.root)): controller.sha(self.runtime)}
        compiler = {'binaries': {str(self.compiler.relative_to(self.root)): controller.sha(self.compiler)}}
        prepared = tree_files(folder / 'source')
        contract = {
            'variant': 'pristine32' if cap == 32 else 'cap256', 'cap': cap, 'source_commit': PIN,
            'source_tree_sha256': fingerprint(prepared), 'prepared_files': prepared,
            'pristine_archive_tree_sha256': 'a' * 64,
            'dependency_tree_sha256': {'eigen': 'b' * 64, 'mel': 'c' * 64},
            'runtime_DLL_sha256': runtime, 'runtime_manifest': runtime,
            'runtime_manifest_sha256': fingerprint(runtime), 'compiler_manifest': compiler,
            'compiler_manifest_sha256': fingerprint(compiler), 'source_patch_sha256': controller.sha(patch_path),
            'patch_changed_files': [] if cap == 32 else [CAP_FILE], 'reference_control': None,
        }
        if cap == 256:
            contract['reference_control'] = {
                'label': 'p32', 'status_sha256': controller.sha(self.home / 'p32/status.json'),
                'contract_sha256': controller.sha(self.home / 'p32/contract.json'),
                'exe_sha256': self.statuses['p32']['exe_sha256']}
        status = {key: copy.deepcopy(contract[key]) for key in (
            *controller.IDENTITY, 'cap', 'source_commit', 'source_patch_sha256',
            'pristine_archive_tree_sha256', 'dependency_tree_sha256')}
        status.update(succeeded=True, exe=str(executable), exe_sha256=controller.sha(executable))
        self.contracts[label], self.statuses[label] = contract, status
        self.reseal_build(label)

    def reseal_build(self, label):
        write(self.home / label / 'contract.json', self.contracts[label])
        self.statuses[label]['contract_sha256'] = controller.sha(self.home / label / 'contract.json')
        write(self.home / label / 'status.json', self.statuses[label])

    def reseal_case(self):
        write(self.case / 'contract.json', self.case_contract)
        write(self.base / 'native_contract_anchor.json', {
            'contract_sha256': controller.sha(self.case / 'contract.json'),
            'design_sha256': controller.sha(self.base / 'method_design.json')})

    def assert_blocked_before_native(self):
        with self.assertRaises((AssertionError, KeyError, ValueError, FileNotFoundError)):
            controller.run('build256', 'p256')
        self.native.assert_not_called()
        self.assertFalse((self.case / 'build256/executable_before_native.json').exists())

    def test_valid_fixture_passes_real_contract_build_and_single_change_guards(self):
        c = controller.check_contract()
        self.assertEqual(controller.build('p32')[0]['cap'], 32)
        candidate, change = controller.checked_change('p256', c)
        self.assertEqual(candidate['cap'], 256)
        self.assertIs(change['verified'], True)
        self.native.assert_not_called()

    def test_changed_limit_rejected_even_if_case_anchor_is_refreshed(self):
        self.case_contract['decision_contract']['density_gain_min'] = .01
        self.reseal_case()  # Isolate the independent method-design comparison.
        self.assert_blocked_before_native()

    def test_contract_edit_rejected_by_original_external_anchor(self):
        changed = copy.deepcopy(self.case_contract)
        changed['decision_contract']['SA_worsening_max'] = 10
        write(self.case / 'contract.json', changed)
        self.assert_blocked_before_native()

    def test_live_code_change_rejected_while_snapshot_remains_intact(self):
        copied = self.case / 'runner_code/live_handler.py'
        before = controller.sha(copied)
        (self.base / 'live_handler.py').write_bytes(b'changed live behavior\n')
        self.assertEqual(controller.sha(copied), before)
        self.assert_blocked_before_native()

    def test_unintended_source_patch_rejected_before_native(self):
        folder = self.home / 'p256'
        (folder / 'source/other.cpp').write_bytes(b'unregistered extra source change\n')
        self.contracts['p256']['prepared_files'] = tree_files(folder / 'source')
        self.contracts['p256']['source_tree_sha256'] = fingerprint(self.contracts['p256']['prepared_files'])
        self.statuses['p256']['source_tree_sha256'] = self.contracts['p256']['source_tree_sha256']
        self.reseal_build('p256')
        self.assertEqual(controller.build('p256')[0]['cap'], 256)  # Internally consistent fake build.
        self.assert_blocked_before_native()  # Yet the single-change comparison must fail.

    def test_wrong_pristine_reference_rejected_before_native(self):
        self.contracts['p256']['reference_control']['label'] = 'different-pristine'
        self.reseal_build('p256')
        controller.build('p256')
        self.assert_blocked_before_native()

    def test_different_valid_compiler_manifest_rejected_before_native(self):
        tool = binary(self.root / 'fixture/other-compiler.exe', b'another inert compiler')
        manifest = {'binaries': {str(tool.relative_to(self.root)): controller.sha(tool)}}
        self.contracts['p256'].update(compiler_manifest=manifest, compiler_manifest_sha256=fingerprint(manifest))
        self.statuses['p256']['compiler_manifest_sha256'] = fingerprint(manifest)
        self.reseal_build('p256')
        controller.build('p256')
        self.assert_blocked_before_native()

    def test_different_valid_runtime_manifest_rejected_before_native(self):
        dll = binary(self.root / 'fixture/other-runtime.dll', b'another inert runtime')
        manifest = {str(dll.relative_to(self.root)): controller.sha(dll)}
        self.contracts['p256'].update(runtime_DLL_sha256=manifest, runtime_manifest=manifest,
                                     runtime_manifest_sha256=fingerprint(manifest))
        self.statuses['p256']['runtime_manifest_sha256'] = fingerprint(manifest)
        self.reseal_build('p256')
        controller.build('p256')
        self.assert_blocked_before_native()

    def test_current_runtime_and_compiler_bytes_are_rechecked(self):
        for path in (self.runtime, self.compiler):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + b' changed after build')
                self.assert_blocked_before_native()
                path.write_bytes(original)

    def test_unaccepted_or_missing_extraction_never_reaches_decision_gates(self):
        for value in ('missing', False, 1):
            for action in ('compare', 'effect'):
                with self.subTest(accepted=value, action=action):
                    for arm in ('release32', 'build32', 'build256'):
                        record = {'payload': {'fixture': True}, 'accepted_for_decision': True}
                        if arm == 'build32':
                            if value == 'missing':
                                del record['accepted_for_decision']
                            else:
                                record['accepted_for_decision'] = value
                        write(self.case / (arm + '_payload.json'), record)
                    with patch.object(controller, 'reproducibility_gate') as reproduction, \
                         patch.object(controller, 'linecap_effect_gate') as effect:
                        with self.assertRaises((AssertionError, KeyError)):
                            controller.compare() if action == 'compare' else controller.effect('p256')
                        reproduction.assert_not_called()
                        effect.assert_not_called()
                    self.native.assert_not_called()


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'test': test.id(), 'passed': True})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.records.append({'test': test.id(), 'passed': False, 'kind': 'failure'})

    def addError(self, test, error):
        super().addError(test, error)
        self.records.append({'test': test.id(), 'passed': False, 'kind': 'error'})


def main():
    if REPORT.exists():
        raise FileExistsError('Preserve existing controller check report: ' + str(REPORT))
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeControllerGuards))
    report = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'passed': result.wasSuccessful(),
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'tests': result.records,
              'failure_details': [{'test': t.id(), 'traceback': text} for t, text in result.failures + result.errors],
              'test_file_sha256': controller.sha(Path(__file__)),
              'controller_sha256': controller.sha(Path(controller.__file__)),
              'scope': 'Temporary fake artifacts and real controller hash/source guards; native launcher is stubbed.',
              'actual_CFD_runs': 0, 'actual_builds': 0, 'prior_check_reports_modified': False,
              'physical_qualification_passed': False, 'LLM_improvement_demonstrated': False}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
