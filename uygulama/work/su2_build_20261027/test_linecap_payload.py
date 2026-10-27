"""Payload extraction counterexamples; synthetic fixtures launch no native work."""
from pathlib import Path
import copy
import csv
import json
import math
import struct
import tempfile
import unittest
import numpy as np
from payload import extract_payload, canonical_config, parse_config, read_history, sha
from decisions import reproducibility_gate
from test_linecap_decisions import fixture as decision_fixture


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='linecap-payload-')
        self.root = Path(self.temp.name)
        self.case = self.root / 'run'; self.case.mkdir()
        self.contract = decision_fixture()[0]
        self.factors = dict(Rho=10., RhoU=100., RhoV=100., RhoE=1000., nu=100.)
        self.xy = np.array([[0., 0.], [1., 0.], [0., .1], [1., .1], [.5, .2]])
        self.mesh = self.root / 'source.su2'
        self.mesh.write_text('NDIME= 2\nNELEM= 0\nNPOIN= 5\n' +
            '\n'.join(f'{x} {y} {i}' for i, (x, y) in enumerate(self.xy)) + '\n', encoding='utf-8')
        self.native_contract = self.root / 'native_contract.json'
        self.native_contract.write_text(json.dumps(self.contract), encoding='utf-8')
        self.rhs = self.root / 'fixed_rhs.csv'
        self.rhs_rows = [dict(mesh_node=i, x_m=x, y_m=y, Rho_residual_ND=i + 1,
                             Rho_finite=1, Rho_squared_share=(i + 1)**2 / 55)
                         for i, (x, y) in enumerate(self.xy)]
        self.write_rhs()
        self.config = '''SOLVER= RANS
KIND_TURB_MODEL= SA
SA_OPTIONS= NEGATIVE, WITHFT2
GAMMA_VALUE= 1.4
MACH_NUMBER= 0.2
REF_DIMENSIONALIZATION= FREESTREAM_VEL_EQ_MACH
RESTART_SOL= YES
READ_BINARY_RESTART= YES
TIME_DISCRE_FLOW= EULER_IMPLICIT
TIME_DISCRE_TURB= EULER_IMPLICIT
MESH_FORMAT= SU2
MESH_FILENAME= ../source.su2
SOLUTION_FILENAME= seed
CONV_FILENAME= history
VOLUME_FILENAME= flow
SURFACE_FILENAME= surface_flow
RESTART_FILENAME= restart_flow
ITER= 200
VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE,LINELET)
OUTPUT_WRT_FREQ= (200,200,200,200)
'''
        (self.case / 'case.cfg').write_text(self.config, encoding='utf-8')
        self.columns = ['Inner_Iter', 'CD', 'Linear_Solver_Iterations', 'LinSolIterTurb']
        self.columns += ['rms[' + key + ']' for key in self.factors] + ['Buffet']
        self.rows = [dict(Inner_Iter=i, CD=.0028, Linear_Solver_Iterations=10,
                          LinSolIterTurb=10, **{'rms[' + key + ']': -12. for key in self.factors},
                          Buffet='nan') for i in range(200)]
        self.write_history()
        self.binary = np.column_stack([self.xy, np.ones(5), np.full(5, .2),
                                       np.zeros(5), np.full(5, 2.52), np.full(5, 1e-5)])
        raw = self.encode_binary()
        self.seed = self.case / 'seed.dat'; self.seed.write_bytes(raw)
        (self.case / 'restart_flow_000199.dat').write_bytes(raw)
        (self.case / 'flow_000199.vtu').write_bytes(b'sealed synthetic volume; reader injected')
        (self.case / 'surface_flow_000199.vtu').write_bytes(b'sealed synthetic surface')
        executable = self.root / 'fixture.exe'; executable.write_bytes(b'fixture, never executed')
        command = [str(executable), 'case.cfg', '-t', '4']
        self.status = dict(started_utc='2026-10-27T00:00:00+00:00', exit_code=0,
                           seconds=10., stop_reason=None, command=command)
        self.process = dict(pid=123, created_filetime=3456, started_utc=self.status['started_utc'],
                            executable=str(executable), command=command)
        self.arrays = {name: np.ones(5) for name in ('Density', 'Pressure', 'Energy',
            'Nu_Tilde', 'Temperature', 'Mach', 'Laminar_Viscosity', 'Eddy_Viscosity')}
        self.arrays.update(Momentum=np.ones((5, 3)), Velocity=np.ones((5, 3)),
                           Linelet=np.array([1., 2., 0., 0., 0.]))
        self.field_xy = np.column_stack([self.xy, np.zeros(5)])
        self.identities = dict(source_tree_sha256='a' * 64,
                               compiler_manifest_sha256='c' * 64,
                               runtime_manifest_sha256='d' * 64)
        self.freeze()

    def tearDown(self):
        self.temp.cleanup()

    def write_rhs(self):
        with self.rhs.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.rhs_rows[0]))
            writer.writeheader(); writer.writerows(self.rhs_rows)

    def write_history(self):
        with (self.case / 'history.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=self.columns)
            writer.writeheader(); writer.writerows(self.rows)

    def encode_binary(self):
        names = ['x', 'y', 'Density', 'Momentum_x', 'Momentum_y', 'Energy', 'Nu_Tilde']
        labels = b''.join(name.encode().ljust(33, b'\0') for name in names)
        return struct.pack('<5i', 535532, 7, 5, 0, 0) + labels + self.binary.astype('<f8').tobytes()

    def freeze(self):
        for name, value in [('solver.status.json', self.status), ('solver.process.json', self.process)]:
            (self.case / name).write_text(json.dumps(value), encoding='utf-8')
        last = self.rows[-1]
        tail = self.rows[-100:]
        cd_range = max(float(row['CD']) for row in tail) - min(float(row['CD']) for row in tail)
        self.seal = dict(contract_sha256=sha(self.native_contract), mesh_sha256=sha(self.mesh),
            native_status=self.status,
            matched=dict(field_iteration=199, terminal_history_iteration=int(last['Inner_Iter']),
                         last100_samples=len(tail), CD_last100_range=cd_range, CD=float(last['CD']),
                         **{'rms[' + key + ']': float(last['rms[' + key + ']']) for key in self.factors}),
            files_sha256={str(path): sha(path) for path in self.case.iterdir()
                          if path.is_file() and path.name != 'prediction_frozen.json'})
        self.write_seal()

    def write_seal(self):
        (self.case / 'prediction_frozen.json').write_text(json.dumps(self.seal), encoding='utf-8')

    def extract(self, **extra):
        options = dict(contract=self.contract, mesh_path=self.mesh, seed_path=self.seed,
                       rhs_csv=self.rhs, rhs_sha256=sha(self.rhs), residual_si_factors=self.factors,
                       native_contract_path=self.native_contract, share_sum_tolerance=1e-12,
                       identities=self.identities, workspace_root=self.root,
                       field_reader=lambda path: (self.field_xy.copy(), copy.deepcopy(self.arrays)))
        options.update(extra)
        return extract_payload(self.case, **options)

    def test_complete_payload_converts_all_five_curves_and_both_work_counts(self):
        result = self.extract()
        self.assertTrue(result['accepted_for_decision'], result['errors'])
        run = result['payload']
        self.assertEqual(len(run['history']), 200)
        self.assertEqual(run['history'][0]['rms'], dict(Rho=-11., RhoU=-10., RhoV=-10., RhoE=-9., nu=-10.))
        self.assertEqual(sum(row['flow_iterations'] + row['SA_iterations'] for row in run['history']), 4000)
        self.assertEqual(run['membership']['mask'], [True, True, False, False, False])
        self.assertAlmostEqual(run['membership']['Rho_squared_share'], 5 / 55)
        self.assertIn('Buffet', result['evidence']['nonfinite_auxiliary_history_columns'])
        self.assertFalse(result['evidence']['physical_qualification_passed'])
        self.assertTrue(reproducibility_gate(run, run, self.contract)['accepted'])

    def test_native_field_order_is_mapped_to_explicit_canonical_node_ids(self):
        order = [2, 0, 4, 1, 3]
        self.field_xy = self.field_xy[order]
        self.arrays = {key: value[order] for key, value in self.arrays.items()}
        result = self.extract()
        self.assertTrue(result['accepted_for_decision'], result['errors'])
        self.assertEqual(result['payload']['membership']['node_ids'], list(range(5)))
        self.assertEqual(result['payload']['membership']['mask'], [True, True, False, False, False])

    def test_path_aliases_only_have_equal_canonical_config(self):
        original = canonical_config(parse_config(self.config))
        aliased = self.config.replace('../source.su2', 'C:/different/location/source.su2')
        aliased = aliased.replace('VOLUME_FILENAME= flow', 'VOLUME_FILENAME= another/output')
        self.assertEqual(original, canonical_config(parse_config(aliased)))
        for before, after in [('MACH_NUMBER= 0.2', 'MACH_NUMBER= 0.3'),
                              ('ITER= 200', 'ITER= 201'),
                              ('200,200,200,200', '100,100,100,100'),
                              ('PRIMITIVE,LINELET', 'PRIMITIVE')]:
            self.assertNotEqual(original, canonical_config(parse_config(self.config.replace(before, after))))

    def test_duplicate_config_key_is_not_silently_overwritten(self):
        with self.assertRaises(ValueError):
            parse_config(self.config + 'MACH_NUMBER= 0.3\n')

    def test_old_field_without_linelet_is_not_backfilled(self):
        self.arrays.pop('Linelet')
        result = self.extract()
        self.assertFalse(result['accepted_for_decision'])
        self.assertIsNone(result['payload']['membership'])
        self.assertTrue(result['checks']['complete_positive_fields'])
        self.assertIn('no old one-step/backfilled', result['errors'][0])

    def test_missing_primary_array_is_not_reconstructed(self):
        for key in ('Pressure', 'Density', 'Energy', 'Nu_Tilde', 'Momentum', 'Velocity'):
            with self.subTest(array=key):
                saved = self.arrays.pop(key)
                result = self.extract()
                self.assertFalse(result['accepted_for_decision'])
                self.assertFalse(result['payload']['field_validity']['required_arrays_finite'])
                self.arrays[key] = saved

    def test_nonfinite_primary_or_auxiliary_arrays_are_not_masked(self):
        self.arrays['Pressure'][3] = math.nan
        self.assertFalse(self.extract()['accepted_for_decision'])
        self.arrays['Pressure'][3] = 1
        self.arrays['extra'] = np.array([1., 1., math.inf, 1., 1.])
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_native_double_pressure_is_checked_independently_of_positive_VTU(self):
        self.binary[1, 5] = -1
        (self.case / 'restart_flow_000199.dat').write_bytes(self.encode_binary())
        self.freeze()
        result = self.extract()
        self.assertFalse(result['accepted_for_decision'])
        self.assertFalse(result['payload']['field_validity']['pressure_positive_finite'])

    def test_partial_duplicate_out_of_plane_or_shifted_coordinates_fail(self):
        saved = self.field_xy.copy()
        for points in (saved[:-1], np.repeat(saved[:1], 5, axis=0), saved + [0., 0., 1e-3], saved + [1e-3, 0., 0.]):
            with self.subTest(points=points.shape):
                self.field_xy = points
                result = self.extract()
                self.assertFalse(result['accepted_for_decision'])
                self.assertIsNone(result['payload']['membership'])

    def test_negative_fractional_or_nonfinite_colors_are_not_membership(self):
        for value in (-1., .5, math.nan):
            with self.subTest(value=value):
                self.arrays['Linelet'][0] = value
                self.assertFalse(self.extract()['accepted_for_decision'])

    def test_terminal_row_and_sealed_iteration_must_be_the_same_199(self):
        for field, terminal in [(198, 199), (199, 198), (199, -1)]:
            with self.subTest(field=field, terminal=terminal):
                self.seal['matched']['field_iteration'] = field
                self.seal['matched']['terminal_history_iteration'] = terminal
                self.write_seal()
                self.assertFalse(self.extract()['accepted_for_decision'])

    def test_missing_coeval_surface_or_wrong_raw_hash_fails(self):
        path = self.case / 'surface_flow_000199.vtu'
        path.unlink()
        self.assertFalse(self.extract()['accepted_for_decision'])
        path.write_bytes(b'replacement')
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_native_nonzero_exit_or_missing_process_identity_fails(self):
        self.status['exit_code'] = 7; self.freeze()
        self.assertFalse(self.extract()['accepted_for_decision'])
        self.status['exit_code'] = 0; self.process.pop('created_filetime'); self.freeze()
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_contract_mesh_seed_and_fixed_RHS_hashes_are_bound(self):
        self.assertFalse(self.extract(rhs_sha256='0' * 64)['accepted_for_decision'])
        self.native_contract.write_text('{}', encoding='utf-8')
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_new_or_reordered_RHS_rows_cannot_replace_original_indices(self):
        self.rhs_rows[1]['mesh_node'] = 0; self.write_rhs()
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_RHS_shares_are_recomputed_from_fixed_raw_Rho(self):
        self.rhs_rows[0]['Rho_squared_share'] += .01
        self.rhs_rows[1]['Rho_squared_share'] -= .01
        self.write_rhs()
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_fractional_work_missing_SA_or_extra_history_row_fails(self):
        self.rows[5]['LinSolIterTurb'] = 1.5; self.write_history(); self.freeze()
        self.assertFalse(self.extract()['accepted_for_decision'])
        self.rows[5]['LinSolIterTurb'] = 10
        self.rows.append(dict(self.rows[-1], Inner_Iter=200)); self.write_history(); self.freeze()
        self.assertFalse(self.extract()['accepted_for_decision'])
        self.rows.pop(); self.columns.remove('LinSolIterTurb')
        for row in self.rows: row.pop('LinSolIterTurb')
        self.write_history(); self.freeze()
        self.assertFalse(self.extract()['accepted_for_decision'])

    def test_missing_bad_or_boolean_SI_factors_fail_without_guessing(self):
        for factors in ({'Rho': 10.}, dict(self.factors, Rho=True), dict(self.factors, nu=0.), dict(self.factors, Rho=math.inf)):
            with self.subTest(factors=factors):
                result = self.extract(residual_si_factors=factors)
                self.assertFalse(result['accepted_for_decision'])
                self.assertEqual(result['payload']['history'], [])

    def test_opaque_source_identities_are_not_fabricated(self):
        result = self.extract(identities=None)
        self.assertTrue(result['accepted_for_decision'])
        self.assertNotIn('source_tree_sha256', result['payload']['identity'])
        self.assertFalse(reproducibility_gate(result['payload'], result['payload'], self.contract)['accepted'])
        self.assertFalse(self.extract(identities={'source_tree_sha256': 'v8.5.0'})['accepted_for_decision'])

    def test_all_missing_files_return_explicit_false_payload(self):
        result = extract_payload(self.root / 'absent', contract=self.contract,
            mesh_path=self.mesh, seed_path=self.seed, rhs_csv=self.rhs, rhs_sha256=sha(self.rhs),
            residual_si_factors=self.factors, native_contract_path=self.native_contract,
            share_sum_tolerance=1e-12, workspace_root=self.root)
        self.assertFalse(result['accepted_for_decision'])
        self.assertIsNone(result['payload']['field_iteration'])
        self.assertIsNone(result['payload']['membership'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
