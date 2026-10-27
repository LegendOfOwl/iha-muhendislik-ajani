"""No compiler/CFD/download: counterexamples for gated fresh cap build controls."""
from pathlib import Path
import copy
import hashlib
import unittest
from unittest.mock import patch
from build_cap import (CAP_FILE, LABEL, EXTRA_ARG, NO_FETCH, modified_files,
                       verify_options, verify_common_recipe, verify_reproduction_records,
                       commands)
from test_ninja_recipe import commands as sample_commands


class CapBuildTests(unittest.TestCase):
    def test_only_cap_bytes_change(self):
        original = b'// unchanged\r\nenum : unsigned long { MAX_LINELET_POINTS = 32 };\r\n'
        files = {CAP_FILE: {'sha256': hashlib.sha256(original).hexdigest(), 'bytes': len(original)},
                 'other.cpp': {'sha256': 'a' * 64, 'bytes': 7}}
        old = copy.deepcopy(files)
        changed, expected = modified_files(files, original)
        self.assertEqual(changed, original.replace(b'= 32', b'= 256'))
        self.assertEqual(files, old)
        self.assertEqual(expected['other.cpp'], old['other.cpp'])

    def test_cap_manifest_mismatch_rejected(self):
        source = b'enum : unsigned long { MAX_LINELET_POINTS = 32 };'
        with self.assertRaises(ValueError):
            modified_files({CAP_FILE: {'sha256': 'a' * 64, 'bytes': len(source)}}, source)

    def test_historical_options_and_empty_global_args(self):
        options = {'with-omp': True, 'with-mpi': 'disabled', 'cpu-arch': 'haswell'}
        rows = [{'name': key, 'value': value} for key, value in options.items()]
        rows += [{'name': key, 'value': []} for key in ('cpp_args', 'cpp_link_args', 'c_args', 'c_link_args')]
        rows += [{'name': 'backend', 'value': 'ninja'}]
        self.assertEqual(verify_options(rows, options), options)
        for key, value in (('cpp_args', [EXTRA_ARG]), ('cpp_link_args', ['-flto']),
                           ('with-omp', 1), ('cpu-arch', 'native')):
            changed = [dict(row, value=value) if row['name'] == key else row for row in rows]
            with self.assertRaises(ValueError):
                verify_options(changed, options)
        with self.assertRaises(ValueError):
            verify_options(rows, dict(options, cpp_args=[EXTRA_ARG]))
        with self.assertRaises(ValueError):
            verify_options(rows + [rows[0]], options)

    def test_fresh_commands_have_single_job_and_nine_offline_skips(self):
        source, build = Path('source'), Path('build')
        cmds = commands(source, build, {'with-omp': True, 'with-mpi': 'disabled'}, Path('effective.ninja'))
        self.assertEqual(cmds['preconfigure'][-9:], NO_FETCH)
        self.assertEqual(cmds['compile'][-3:], ['-j', '1', 'SU2_CFD/src/SU2_CFD.exe'])
        self.assertIn('-f', cmds['compile'])
        self.assertIn('-Dwith-omp=true', cmds['configure'])
        self.assertFalse(any('cpp_args' in value for value in cmds['configure']))
        self.assertNotIn('install', cmds['compile'])
        with self.assertRaises(ValueError):
            commands(source, build, {'cpp_args': [EXTRA_ARG]}, Path('effective.ninja'))

    def test_saved_reproduction_recomputed_and_exactly_bound(self):
        native = {'pristine_build': 'p32r', 'decision_contract': {'scope': 'fixture'}}
        release = {'accepted_for_decision': True, 'payload': {'role': 'release'}}
        pristine = {'accepted_for_decision': True, 'payload': {'role': 'pristine'}}
        decision = {'accepted': True, 'metrics': {'fixed': 1}, 'build32_run_fingerprint': 'a' * 64}
        with patch('build_cap.reproducibility_gate', return_value=decision) as gate:
            self.assertEqual(verify_reproduction_records(native, release, pristine, decision), decision)
            gate.assert_called_once_with(release['payload'], pristine['payload'], native['decision_contract'])
        with patch('build_cap.reproducibility_gate', return_value=dict(decision, accepted=False)):
            with self.assertRaises(ValueError):
                verify_reproduction_records(native, release, pristine, decision)

    def test_truthy_stale_wrong_baseline_reproduction_rejected(self):
        native = {'pristine_build': 'p32r', 'decision_contract': {}}
        release = {'accepted_for_decision': True, 'payload': {}}
        pristine = {'accepted_for_decision': True, 'payload': {}}
        decision = {'accepted': True, 'build32_run_fingerprint': 'a' * 64}
        with patch('build_cap.reproducibility_gate', return_value=decision):
            for bad_native, bad_release, bad_saved in (
                (dict(native, pristine_build='p32a'), release, decision),
                (native, dict(release, accepted_for_decision='true'), decision),
                (native, release, dict(decision, accepted=1)),
                (native, release, dict(decision, build32_run_fingerprint='b' * 64))):
                with self.assertRaises(ValueError):
                    verify_reproduction_records(bad_native, bad_release, pristine, bad_saved)

    def test_common_recipe_rejects_extra_command_or_flag(self):
        original = sample_commands(' "' + EXTRA_ARG + '"')
        with self.assertRaises(ValueError):
            verify_common_recipe(original, original.replace('"-O3"', '"-O0"', 1))
        with self.assertRaises(ValueError):
            verify_common_recipe(original, original.splitlines()[0])
        # A tiny fixture must not impersonate the real registered 290-command target.
        with self.assertRaises(ValueError):
            verify_common_recipe(original, original)

    def test_common_recipe_accepts_exact_full_set_in_any_order(self):
        from test_ninja_recipe import compilation
        records = [compilation('unit' + str(i) + '.obj', '../source/unit' + str(i) + '.cpp')
                   for i in range(290)]
        result = verify_common_recipe('\n'.join(records), '\n'.join(reversed(records)))
        self.assertTrue(result['passed'])
        self.assertEqual(result['matched_commands'], 290)


if __name__ == '__main__':
    unittest.main(verbosity=2)
