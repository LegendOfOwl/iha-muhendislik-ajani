"""Decision counterexamples; no CFD, file output or evidence assertions mocked."""
import copy
import math
import unittest
from decisions import reproducibility_gate, linecap_effect_gate


def sha(character):
    return character * 64


def fixture():
    # Small membership cardinality keeps tests light; production registers52689.
    contract = {
        'normalization': 'SI2D', 'iterations': 200, 'comparison_iteration': 199,
        'last_window_samples': 100, 'CD_window_range_max': 1e-7,
        'rms_components': ['Rho', 'RhoU', 'RhoV', 'RhoE', 'nu'],
        'reproduction_max_abs_log10_difference': .03,
        'reproduction_final_CD_abs_difference_max': 1e-8,
        'reproduction_Krylov_relative_difference_max': .05,
        'membership_expected_nodes': 5, 'coordinate_mapping_max_m': 2e-7,
        'density_gain_min': .3, 'SA_worsening_max': .1,
        'work_ratio_max': 1.5, 'elapsed_ratio_max': 1.5,
        'Rho_share_gain_min': 1e-12,
        'reference_cap': 32, 'candidate_cap': 256,
        'pristine_source_tree_sha256': sha('a'),
    }
    run = {
        'normalization': 'SI2D', 'native_exit_code': 0, 'field_iteration': 199,
        'history_iteration': 199, 'last100_samples': 100, 'CD_last100_range': 0.,
        'elapsed_seconds': 10.,
        'field_validity': dict(rho_positive_finite=True, pressure_positive_finite=True,
                               required_arrays_finite=True),
        'identity': dict(mesh_sha256=sha('1'), seed_sha256=sha('2'),
                         comparison_config_sha256=sha('3'), physics_sha256=sha('4'),
                         compiler_manifest_sha256=sha('c'), runtime_manifest_sha256=sha('d'),
                         source_tree_sha256=sha('a')),
        'history': [dict(iteration=i, rms=dict(Rho=-10., RhoU=-11., RhoV=-13.,
                                             RhoE=-11.5, nu=-12.), CD=.0028,
                         flow_iterations=10, SA_iterations=10) for i in range(200)],
        'membership': dict(node_ids=list(range(5)), mask=[True, True, False, False, False],
                           mapping=dict(passed=True, reference_points=5, observed_points=5,
                                        unique_matches=5, maximum_distance_m=0.),
                           Rho_squared_share=.4, fixed_RHS_sha256=sha('e')),
    }
    release, baseline = copy.deepcopy(run), copy.deepcopy(run)
    # Different release compiler identity is allowed at the numerical repro stage.
    release['identity']['compiler_manifest_sha256'] = sha('f')
    candidate = copy.deepcopy(run)
    candidate['identity']['source_tree_sha256'] = sha('b')
    candidate['elapsed_seconds'] = 15.
    for row in candidate['history']:
        row['rms']['Rho'] = -10.4
        row['rms']['nu'] = -11.95
        row['flow_iterations'] = row['SA_iterations'] = 15
    # Deliberately not a superset; greedy reallocation is allowed.
    candidate['membership']['mask'] = [False, True, True, True, False]
    candidate['membership']['Rho_squared_share'] = .6
    patch = dict(verified=True, only_change='MAX_LINELET_POINTS', reference_cap=32,
                 candidate_cap=256, pristine_source_sha256=sha('a'),
                 modified_source_sha256=sha('b'), patch_sha256=sha('9'))
    return contract, release, baseline, candidate, patch


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.c, self.release, self.base, self.new, self.patch = fixture()

    def repro(self):
        return reproducibility_gate(self.release, self.base, self.c)

    def test_valid_reproduction_not_physical_or_binary_identity(self):
        result = self.repro()
        self.assertTrue(result['accepted'])
        self.assertFalse(result['physical_qualification_passed'])
        self.assertFalse(result['M6_qualification_passed'])
        self.assertFalse(result['LLM_improvement_demonstrated'])

    def test_each_of_five_components_is_checked_at_every_iteration(self):
        for component in self.c['rms_components']:
            with self.subTest(component=component):
                run = copy.deepcopy(self.base)
                run['history'][72]['rms'][component] += .04
                result = reproducibility_gate(self.release, run, self.c)
                self.assertFalse(result['accepted'])
                self.assertFalse(result['checks']['five_RMS_curves_reproduced'])

    def test_reproduction_log_boundary_is_inclusive_and_not_rounded(self):
        for run in (self.release, self.base):
            run['history'][0]['rms']['Rho'] = 0.
        self.base['history'][0]['rms']['Rho'] = .03
        self.assertTrue(self.repro()['accepted'])
        self.base['history'][0]['rms']['Rho'] = math.nextafter(.03, math.inf)
        self.assertFalse(self.repro()['accepted'])

    def test_combined_work_includes_SA_and_checks_five_percent(self):
        # +1SA per row is exactly +5% of the combined baseline work.
        for row in self.base['history']:
            row['SA_iterations'] += 1
        self.assertTrue(self.repro()['accepted'])
        self.base['history'][0]['SA_iterations'] += 1
        self.assertFalse(self.repro()['accepted'])

    def test_final_CD_difference_has_its_own_gate(self):
        # A constant offset leaves both last100 CD ranges at zero.
        for row in self.base['history']:
            row['CD'] += 1.0001e-8
        result = self.repro()
        self.assertFalse(result['accepted'])
        self.assertFalse(result['checks']['final_CD_reproduced'])

    def test_missing_duplicate_or_nonfinite_history_fails_closed(self):
        mutations = [lambda r: r['history'].pop(),
                     lambda r: r['history'][1].update(iteration=0),
                     lambda r: r['history'][0]['rms'].update(RhoV=math.nan),
                     lambda r: r['history'][0].update(flow_iterations=True),
                     lambda r: r['history'][0].update(SA_iterations=-1)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                run = copy.deepcopy(self.base); mutate(run)
                self.assertFalse(reproducibility_gate(self.release, run, self.c)['accepted'])

    def test_unrepresentably_large_numbers_fail_closed(self):
        self.base['history'][0]['rms']['Rho'] = 10 ** 1000
        self.assertFalse(self.repro()['accepted'])
        self.base['history'][0]['rms']['Rho'] = -10.
        self.base['history'][0]['flow_iterations'] = 10 ** 1000
        self.assertFalse(self.repro()['accepted'])

    def test_same_count_different_native_mask_fails(self):
        self.base['membership']['mask'] = [True, False, True, False, False]
        self.assertFalse(self.repro()['accepted'])

    def test_color_ids_do_not_define_membership(self):
        self.release['membership']['color_ids'] = [1, 1, 0, 0, 0]
        self.base['membership']['color_ids'] = [5, 6, 0, 0, 0]
        self.assertTrue(self.repro()['accepted'])

    def test_map_must_be_bijective_and_all_nodes_retained(self):
        for key, value in [('unique_matches', 4), ('observed_points', 4),
                           ('maximum_distance_m', 2.000001e-7), ('passed', 1)]:
            with self.subTest(key=key):
                run = copy.deepcopy(self.base)
                run['membership']['mapping'][key] = value
                self.assertFalse(reproducibility_gate(self.release, run, self.c)['accepted'])
        self.base['membership']['node_ids'] = [0, 1, 1, 3, 4]
        self.assertFalse(self.repro()['accepted'])

    def test_positive_numeric_masks_are_not_boolean_membership_proof(self):
        self.base['membership']['mask'][0] = 1
        self.assertFalse(self.repro()['accepted'])

    def test_exit_field_window_and_boolean_validity_are_required(self):
        mutations = [lambda r: r.update(native_exit_code=False),
                     lambda r: r.update(native_exit_code=1),
                     lambda r: r.update(field_iteration=198),
                     lambda r: r.update(last100_samples=99),
                     lambda r: r['field_validity'].update(pressure_positive_finite=1),
                     lambda r: r['field_validity'].pop('rho_positive_finite')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                run = copy.deepcopy(self.base); mutate(run)
                self.assertFalse(reproducibility_gate(self.release, run, self.c)['accepted'])

    def test_window_range_recomputed_instead_of_trusting_metadata(self):
        self.base['history'][-1]['CD'] += 2e-7
        self.assertFalse(self.repro()['accepted'])

    def test_mixed_normalization_and_different_seed_fail(self):
        self.base['normalization'] = 'ND'
        self.assertFalse(self.repro()['accepted'])
        self.base['normalization'] = 'SI2D'
        self.base['identity']['seed_sha256'] = sha('8')
        self.assertFalse(self.repro()['accepted'])

    def test_missing_invalid_contract_has_no_hidden_default(self):
        for key, value in [('density_gain_min', True), ('work_ratio_max', math.inf),
                           ('iterations', True), ('pristine_source_tree_sha256', None)]:
            with self.subTest(key=key):
                c = copy.deepcopy(self.c); c[key] = value
                self.assertFalse(reproducibility_gate(self.release, self.base, c)['accepted'])
        self.c.pop('coordinate_mapping_max_m')
        self.assertFalse(self.repro()['accepted'])


class EffectTests(unittest.TestCase):
    def setUp(self):
        self.c, self.release, self.base, self.new, self.patch = fixture()
        self.proof = reproducibility_gate(self.release, self.base, self.c)

    def effect(self):
        return linecap_effect_gate(self.base, self.new, self.c, self.proof, self.patch)

    def test_valid_effect_at_both_cost_boundaries_without_subset_requirement(self):
        result = self.effect()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['metrics']['work_ratio'], 1.5)
        self.assertEqual(result['metrics']['observed_elapsed_ratio'], 1.5)
        self.assertFalse(result['physical_qualification_passed'])
        self.assertFalse(result['M6_qualification_passed'])

    def test_failed_missing_or_fabricated_reproduction_never_accepts(self):
        for proof in ({}, {'accepted': True}, dict(self.proof, accepted=False)):
            with self.subTest(proof=proof):
                self.assertFalse(linecap_effect_gate(self.base, self.new, self.c, proof, self.patch)['accepted'])

    def test_successful_reproduction_cannot_be_transferred_to_another_baseline(self):
        self.base['elapsed_seconds'] += 1
        result = self.effect()
        self.assertFalse(result['accepted'])
        self.assertFalse(result['checks']['pristine_reproduction_passed_for_same_baseline'])

    def test_reproduction_from_changed_contract_fails(self):
        self.c['density_gain_min'] = .2
        self.assertFalse(self.effect()['accepted'])

    def test_small_or_wrong_sign_density_gain_is_not_success(self):
        for final in (-10.2999, -9.6):
            with self.subTest(final=final):
                self.new['history'][-1]['rms']['Rho'] = final
                self.assertFalse(self.effect()['accepted'])

    def test_SA_degradation_over_limit_fails(self):
        self.new['history'][-1]['rms']['nu'] = -11.899
        self.assertFalse(self.effect()['accepted'])

    def test_each_cost_is_independently_mandatory(self):
        self.new['elapsed_seconds'] = math.nextafter(15., math.inf)
        self.assertFalse(self.effect()['accepted'])
        self.new['elapsed_seconds'] = 15.
        self.new['history'][0]['SA_iterations'] += 1
        self.assertFalse(self.effect()['accepted'])

    def test_nonfinite_boolean_negative_or_zero_cost_fails(self):
        for value in (math.nan, math.inf, True, -1., 0.):
            with self.subTest(value=value):
                self.new['elapsed_seconds'] = value
                self.assertFalse(self.effect()['accepted'])

    def test_changed_compiler_runtime_inputs_and_source_are_separate_failures(self):
        for key in ('compiler_manifest_sha256', 'runtime_manifest_sha256',
                    'mesh_sha256', 'comparison_config_sha256', 'physics_sha256',
                    'source_tree_sha256'):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.new)
                candidate['identity'][key] = sha('7')
                self.assertFalse(linecap_effect_gate(self.base, candidate, self.c, self.proof, self.patch)['accepted'])

    def test_unverified_wrong_or_missing_patch_fails(self):
        for key, value in [('verified', 1), ('only_change', 'another_method'),
                           ('candidate_cap', True), ('reference_cap', 40),
                           ('patch_sha256', None)]:
            with self.subTest(key=key):
                patch = dict(self.patch); patch[key] = value
                self.assertFalse(linecap_effect_gate(self.base, self.new, self.c, self.proof, patch)['accepted'])

    def test_larger_mask_without_more_fixed_RHS_share_fails(self):
        self.new['membership']['Rho_squared_share'] = .4
        self.assertFalse(self.effect()['accepted'])

    def test_more_share_without_more_membership_nodes_fails(self):
        self.new['membership']['mask'] = [False, True, True, False, False]
        self.assertFalse(self.effect()['accepted'])

    def test_fixed_old_RHS_identity_is_mandatory(self):
        self.new['membership']['fixed_RHS_sha256'] = sha('6')
        self.assertFalse(self.effect()['accepted'])

    def test_share_must_be_finite_nonnegative_bounded_and_not_boolean(self):
        for value in (math.nan, math.inf, True, -0.1, 1.1, None):
            with self.subTest(value=value):
                self.new['membership']['Rho_squared_share'] = value
                self.assertFalse(self.effect()['accepted'])

    def test_tiny_share_change_does_not_pass_strict_threshold(self):
        self.new['membership']['Rho_squared_share'] = .4 + 0.5e-12
        self.assertFalse(self.effect()['accepted'])

    def test_missing_values_fail_closed_without_exception(self):
        for key in ('history', 'membership', 'identity', 'field_validity', 'elapsed_seconds'):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.new); candidate.pop(key)
                self.assertFalse(linecap_effect_gate(self.base, candidate, self.c, self.proof, self.patch)['accepted'])
        self.assertFalse(linecap_effect_gate(None, [], {}, None, None)['accepted'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
