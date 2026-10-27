"""Pure guard cases and small Python-only Windows job/process smoke checks."""
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import unittest
from unittest import mock
import uuid

_path = Path(__file__).with_name('build_runner.py')
_spec = importlib.util.spec_from_file_location('su2_build_process_guard_runner_20261027', _path)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


class PureProcessGuards(unittest.TestCase):
    def test_valid_sample(self):
        self.assertIsNone(runner.resource_stop_reason(1, .1, 2, 10, 3, 1))

    def test_exact_memory_bounds(self):
        self.assertIsNone(runner.resource_stop_reason(1, 3, 1, 10, 3, 1))

    def test_timeout(self):
        self.assertEqual(runner.resource_stop_reason(10, .1, 2, 10, 3, 1), 'time_budget_exceeded')

    def test_tree_not_only_root_memory(self):
        self.assertEqual(runner.resource_stop_reason(1, .05 + 2 + 1.1, 2, 10, 3, 1), 'process_tree_working_set_exceeded')

    def test_low_available(self):
        self.assertEqual(runner.resource_stop_reason(1, .1, .99, 10, 3, 1), 'system_available_memory_below_minimum')

    def test_nonfinite_sample_fails_closed(self):
        self.assertEqual(runner.resource_stop_reason(1, math.nan, 2, 10, 3, 1), 'invalid_resource_sample_or_budget')

    def test_negative_sample_fails_closed(self):
        self.assertEqual(runner.resource_stop_reason(1, -1, 2, 10, 3, 1), 'invalid_resource_sample_or_budget')

    def test_boolean_budget_fails_closed(self):
        self.assertEqual(runner.resource_stop_reason(1, .1, 2, True, 3, 1), 'invalid_resource_sample_or_budget')

    def test_path_and_device_labels_rejected(self):
        for value in ('../escape', 'x/y', 'C:\\outside', 'NUL', 'CON.log', 'trailing.', ''):
            with self.assertRaises(ValueError, msg=value):
                runner.validated_label(value)


@unittest.skipUnless(os.name == 'nt' and importlib.util.find_spec('psutil'), 'Windows and psutil required for native process smoke')
class WindowsJobSmoke(unittest.TestCase):
    def label(self, suffix):
        return 'guard-' + suffix + '-' + uuid.uuid4().hex[:10]

    def metadata(self, label):
        return json.loads((runner.BASE / (label + '.process.json')).read_text(encoding='utf-8'))

    def test_small_parent_child_success_and_no_overwrite(self):
        label = self.label('success')
        child = "import time; time.sleep(.4)"
        code = "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c',%r]); print('CHILD',p.pid,flush=True); raise SystemExit(p.wait())" % child
        result = runner.run_build([sys.executable, '-c', code], runner.BASE, label, 10, dict(os.environ))
        self.assertTrue(result['succeeded'], result)
        self.assertEqual(result['exit_code'], 0)
        self.assertGreaterEqual(result['observed_process_count'], 2)
        self.assertTrue(result['cleanup_confirmed'])
        identities = self.metadata(label)['observed_processes']
        self.assertTrue(all(p['creation_filetime_100ns'] > 0 and p['confirmed_exited'] for p in identities))
        before = (runner.BASE / (label + '.status.json')).read_bytes()
        with self.assertRaises(FileExistsError):
            runner.run_build([sys.executable, '-c', 'pass'], runner.BASE, label, 10, dict(os.environ))
        self.assertEqual(before, (runner.BASE / (label + '.status.json')).read_bytes())

    def test_timeout_kills_parent_and_child(self):
        label = self.label('timeout')
        child = "import time; time.sleep(60)"
        code = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c',%r]); print('CHILD',p.pid,flush=True); time.sleep(60)" % child
        result = runner.run_build([sys.executable, '-c', code], runner.BASE, label, 1.2, dict(os.environ))
        self.assertFalse(result['succeeded'])
        self.assertEqual(result['stop_reason'], 'time_budget_exceeded')
        self.assertEqual(result['exit_code'], 124)
        self.assertTrue(result['job_termination_requested'])
        self.assertGreaterEqual(result['observed_process_count'], 2)
        self.assertEqual(result['job_active_pids_before_final_close'], [])
        self.assertTrue(result['cleanup_confirmed'], result)
        self.assertTrue(all(p['confirmed_exited'] for p in self.metadata(label)['observed_processes']))

    def test_assignment_failure_never_resumes(self):
        label = self.label('assignment-fail')
        with mock.patch.object(runner, 'assign_process', side_effect=OSError('injected job assignment denial')):
            result = runner.run_build([sys.executable, '-c', "print('MUST_NOT_RUN',flush=True)"], runner.BASE, label, 10, dict(os.environ))
        self.assertFalse(result['build_started'])
        self.assertFalse(result['succeeded'])
        self.assertFalse(result['assigned_to_private_job'])
        self.assertEqual(result['exit_code'], 125)
        self.assertTrue(result['all_observed_processes_confirmed_exited'])
        self.assertNotIn('MUST_NOT_RUN', (runner.BASE / (label + '.log')).read_text(encoding='utf-8'))

    def test_nonzero_root_exit_is_real_failure(self):
        label = self.label('exit7')
        result = runner.run_build([sys.executable, '-c', 'raise SystemExit(7)'], runner.BASE, label, 10, dict(os.environ))
        self.assertEqual(result['exit_code'], 7)
        self.assertFalse(result['succeeded'])
        self.assertEqual(result['stop_reason'], 'build_root_nonzero_exit')

    def test_root_exit_does_not_leave_live_child(self):
        label = self.label('orphan')
        code = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print('CHILD',p.pid,flush=True); time.sleep(.4); raise SystemExit(7)"
        result = runner.run_build([sys.executable, '-c', code], runner.BASE, label, 10, dict(os.environ))
        self.assertEqual(result['exit_code'], 7)
        self.assertEqual(result['stop_reason'], 'root_exited_with_live_job_children')
        self.assertTrue(result['job_termination_requested'])
        self.assertTrue(result['cleanup_confirmed'], result)
        self.assertFalse(result['succeeded'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
