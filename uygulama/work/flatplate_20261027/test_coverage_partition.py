"""Counterexamples for misleading coverage and cost acceptance."""
import unittest
import numpy as np
from coverage_audit import measure
from prec_partition_control import decide


class CoverageGuards(unittest.TestCase):
    def test_graph_color_is_membership_not_line_ID(self):
        r = measure([0, 1, 1, 3], [.2, .3, .4, .1], [.7, .1, .1, .1])
        self.assertEqual(r['linelet_nodes'], 3)
        self.assertAlmostEqual(r['covered_Rho_squared_share'], .8)
        self.assertAlmostEqual(r['covered_nu_squared_share'], .3)

    def test_negative_color(self):
        with self.assertRaises(ValueError): measure([0, -1], [.5, .5], [.5, .5])

    def test_fractional_color(self):
        with self.assertRaises(ValueError): measure([0, .5], [.5, .5], [.5, .5])

    def test_nonfinite_color(self):
        with self.assertRaises(ValueError): measure([0, np.nan], [.5, .5], [.5, .5])

    def test_negative_share_cannot_cancel_to_one(self):
        with self.assertRaises(ValueError): measure([0, 1], [-.2, 1.2], [.5, .5])

    def test_missing_share(self):
        with self.assertRaises(ValueError): measure([0, 1], [.2, .2], [.5, .5])

    def test_nonfinite_share(self):
        with self.assertRaises(ValueError): measure([0, 1], [.5, .5], [np.inf, 0])

    def test_shape_mismatch(self):
        with self.assertRaises(ValueError): measure([0, 1], [.5, .5, 0], [.5, .5])

    def test_all_inside(self):
        with self.assertRaises(ValueError): measure([1, 3], [.5, .5], [.5, .5])

    def test_all_outside(self):
        with self.assertRaises(ValueError): measure([0, 0], [.5, .5], [.5, .5])


class PartitionAcceptanceGuards(unittest.TestCase):
    def setUp(self):
        self.q = {'comparable': True, 'effect_passed': True}
        self.e = {'work_ratio_max': 1.5, 'observed_time_ratio_max': 1.5}

    def accept(self, work=1., seconds=1., quality=None):
        return decide(self.q if quality is None else quality, work, seconds, self.e)

    def test_valid_diagnostic_does_not_qualify_physics(self):
        r = self.accept()
        self.assertTrue(r['effect_passed'])
        self.assertFalse(r['physical_qualification_passed'])

    def test_lower_iteration_cost_cannot_hide_elapsed_regression(self):
        self.assertFalse(self.accept(.8, 1.500000001)['effect_passed'])

    def test_faster_elapsed_cannot_hide_excess_work(self):
        self.assertFalse(self.accept(1.500000001, .8)['effect_passed'])

    def test_exact_registered_cost_boundary(self):
        self.assertTrue(self.accept(1.5, 1.5)['effect_passed'])

    def test_unmatched_pair(self):
        self.assertFalse(self.accept(quality={'comparable': False, 'effect_passed': True})['effect_passed'])

    def test_failed_residual_effect(self):
        self.assertFalse(self.accept(quality={'comparable': True, 'effect_passed': False})['effect_passed'])

    def test_invalid_costs_fail_closed(self):
        for bad in (None, True, '1', float('nan'), float('inf'), -1):
            with self.subTest(cost=bad):
                self.assertFalse(self.accept(bad, 1)['effect_passed'])
                self.assertFalse(self.accept(1, bad)['effect_passed'])


if __name__ == '__main__':
    unittest.main()
