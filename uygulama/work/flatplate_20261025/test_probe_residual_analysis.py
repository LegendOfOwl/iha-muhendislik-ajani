"""Analytic and adverse-input guards, without VTK or a native solver."""
import copy
import math
import unittest
import numpy as np
from probe_residual_analysis import (COMPONENTS, residual_norm_check, coordinate_mapping,
    conservative_drift, analyse_arrays, spatial_summary, region_mask, shares, residual_components)


class ProbeGuards(unittest.TestCase):
    def setUp(self):
        self.xy = np.array([[0., 0.], [1., 0.], [0., 1.]])
        self.values = np.array([1., 2., 3.])
        self.gates = {'residual_log10_error_max': 1e-6, 'coordinate_mapping_max_m': 2e-7,
                      'conservative_global_relative_drift_max': 2e-6, 'expected_points': 3,
                      'all5_RMS_and_MAX_required': True}
        self.solution = np.array([[1., .2, .01, 3., .02], [1., .2, .01, 3., .02], [1., .2, .01, 3., .02]])
        self.residuals = {k: self.values * (i + 1) for i, k in enumerate(COMPONENTS)}
        self.row = {}
        for k, a in self.residuals.items():
            self.row['rms[' + k + ']'] = math.log10(math.sqrt(float(np.mean(a*a))))
            self.row['max[' + k + ']'] = math.log10(float(np.max(np.abs(a))))

    def audit(self, residuals=None, row=None, observed=None, output=None):
        return analyse_arrays(self.xy, self.xy if observed is None else observed,
            self.residuals if residuals is None else residuals, self.row if row is None else row,
            self.xy, self.solution, self.xy, self.solution if output is None else output, self.gates)[0]

    def test_analytic_norm_and_max(self):
        answer = residual_norm_check(np.array([-3., 4.]), math.log10(math.sqrt(12.5)), math.log10(4), 1e-12, 2)
        self.assertTrue(answer['passed'])

    def test_valid_all_five_is_measurement_only(self):
        answer = self.audit()
        self.assertTrue(answer['measurement_accepted'])
        self.assertFalse(answer['physical_qualification_passed'])

    def test_missing_component_rejects_every_map(self):
        a = dict(self.residuals)
        del a['RhoV']
        answer = self.audit(a)
        self.assertFalse(answer['map_authorized'])
        self.assertFalse(any(answer['component_map_authorized'].values()))

    def test_nonfinite_node_is_not_filtered(self):
        a = copy.deepcopy(self.residuals)
        a['Rho'][1] = np.nan
        answer = self.audit(a)
        self.assertFalse(answer['components']['Rho']['passed'])
        self.assertEqual(answer['components']['Rho']['points'], 3)

    def test_missing_max_history_rejects(self):
        row = dict(self.row)
        del row['max[nu]']
        self.assertFalse(self.audit(row=row)['map_authorized'])

    def test_max_mismatch_rejects_even_correct_rms(self):
        row = dict(self.row)
        row['max[nu]'] += 1e-4
        answer = self.audit(row=row)
        self.assertLess(answer['components']['nu']['RMS_log10_error'], 1e-12)
        self.assertFalse(answer['map_authorized'])

    def test_rms_mismatch_rejects_even_correct_max(self):
        row = dict(self.row)
        row['rms[Rho]'] += 1e-4
        self.assertFalse(self.audit(row=row)['map_authorized'])

    def test_permutation_is_bijective(self):
        permutation = [2, 0, 1]
        check, order = coordinate_mapping(self.xy, self.xy[permutation], 1e-12, 3)
        self.assertTrue(check['passed'])
        np.testing.assert_array_equal(self.xy[permutation][order], self.xy)

    def test_duplicate_coordinates_reject(self):
        points = self.xy.copy()
        points[1] = points[0]
        self.assertFalse(self.audit(observed=points)['map_authorized'])

    def test_coordinate_corruption_reject(self):
        points = self.xy.copy()
        points[1, 0] += 1e-3
        self.assertFalse(self.audit(observed=points)['map_authorized'])

    def test_nonfinite_coordinate_reject(self):
        points = self.xy.copy()
        points[1, 0] = np.inf
        self.assertFalse(self.audit(observed=points)['map_authorized'])

    def test_out_of_plane_coordinate_reject(self):
        points = np.column_stack([self.xy, np.zeros(3)])
        points[1, 2] = 1e-3
        self.assertFalse(self.audit(observed=points)['map_authorized'])

    def test_too_much_native_drift_rejects(self):
        output = self.solution.copy()
        output[:, 0] *= 1 + 3e-6
        answer = self.audit(output=output)
        self.assertFalse(answer['native_binary_drift']['passed'])
        self.assertFalse(answer['map_authorized'])

    def test_nonpositive_pressure_rejects(self):
        output = self.solution.copy()
        output[:, 3] = 0
        self.assertFalse(self.audit(output=output)['map_authorized'])

    def test_nonpositive_density_rejects(self):
        output = self.solution.copy()
        output[:, 0] = -1
        self.assertFalse(self.audit(output=output)['map_authorized'])

    def test_zero_reference_momentum_new_drift_rejects(self):
        before = self.solution.copy()
        before[:, 2] = 0
        after = before.copy()
        after[:, 2] = 1e-14
        answer = conservative_drift(before, after, 2e-6)
        self.assertFalse(answer['passed'])
        self.assertIsNone(answer['relative_L2_by_field']['Momentum_y'])

    def test_sa_drift_separate_from_conservative_gate(self):
        output = self.solution.copy()
        output[:, 4] *= 1.1
        answer = conservative_drift(self.solution, output, 2e-6)
        self.assertTrue(answer['passed'])
        self.assertAlmostEqual(answer['Nu_Tilde_relative_L2_observation'], .1)

    def test_registered_count_required(self):
        answer = residual_norm_check(self.values[:-1], 0, 0, 1e-6, 3)
        self.assertFalse(answer['passed'])

    def test_zero_vector_is_not_invented_share_map(self):
        self.assertFalse(residual_norm_check(np.zeros(3), -30, -30, 1e-6, 3)['passed'])
        with self.assertRaises(ValueError):
            shares(np.zeros(3))

    def test_tiny_norm_is_numerically_stable(self):
        check = residual_norm_check(self.values * 1e-250,
            math.log10(math.sqrt(14/3)) - 250, math.log10(3) - 250, 1e-12, 3)
        self.assertTrue(check['passed'])

    def test_squared_share_peak_n90_and_overlapping_regions(self):
        a = np.array([0., 0., 10.])
        regions = [{'name': 'all', 'x': [0., 1.], 'y': [0., 1.]},
                   {'name': 'top', 'y_min': .5, 'y_max': 1.}]
        summary = spatial_summary(self.xy, a, regions)
        self.assertEqual(summary['peak_mesh_node'], 2)
        self.assertEqual(summary['nodes_carrying_90_percent_of_squared_residual'], 1)
        self.assertEqual([r['squared_residual_share'] for r in summary['regions']], [1., 1.])
        self.assertTrue(summary['regions_overlap_and_must_not_be_summed_as_a_partition'])

    def test_reversed_or_unsupported_regions_reject(self):
        with self.assertRaises(ValueError):
            region_mask(self.xy, {'name': 'bad', 'x': [1., 0.]})
        with self.assertRaises(ValueError):
            region_mask(self.xy, {'name': 'bad', 'invented': .1})

    def test_native_grouped_vector_names_supported(self):
        arrays = {'Residual_Density': self.values, 'Residual_Momentum': np.column_stack([2*self.values, 3*self.values, np.zeros(3)]),
                  'Residual_Energy': 4*self.values, 'Residual_Nu_Tilde': 5*self.values}
        a = residual_components(arrays)
        for name in COMPONENTS:
            np.testing.assert_array_equal(a[name], self.residuals[name])


if __name__ == '__main__':
    unittest.main(verbosity=2)
