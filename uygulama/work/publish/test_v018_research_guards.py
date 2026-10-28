"""Counterexamples for research-only release scope; no publishing or native run."""
import copy
import unittest
from release_documents_v018 import (
    REQUIRED_RESEARCH, assert_distribution_scope, assert_research_payloads,
    validate_research_report,
)


def report():
    return {
        'summary_tr': '  Kaynak araştırması tamamlandı.  ',
        'summary_en': '  Source research completed.  ',
        'physical_qualification_passed': False,
        'M6_qualification_passed': False,
        'LLM_improvement_demonstrated': False,
        'new_native_CFD_runs': 0,
        'new_builds': 0,
    }


def plan():
    return {'changed': [
        {'source_path': p, 'storage': 'git', 'repository_path': 'uygulama/' + p}
        for p in sorted(REQUIRED_RESEARCH)
    ]}


class ResearchTruthGuards(unittest.TestCase):
    def test_valid_zero_work_summary_preserved_without_mutation(self):
        value = report()
        before = copy.deepcopy(value)
        self.assertEqual(validate_research_report(value), (
            'Kaynak araştırması tamamlandı.\n', 'Source research completed.\n'))
        self.assertEqual(value, before)

    def test_old_three_run_success_cannot_be_relabelled_research(self):
        value = report()
        value['new_native_CFD_runs'] = 3
        with self.assertRaises(AssertionError):
            validate_research_report(value)

    def test_old_build_count_cannot_be_relabelled_research(self):
        value = report()
        value['new_builds'] = 2
        with self.assertRaises(AssertionError):
            validate_research_report(value)

    def test_boolean_false_is_not_a_measured_zero_work_count(self):
        for key in ('new_native_CFD_runs', 'new_builds'):
            with self.subTest(key=key):
                value = report()
                value[key] = False
                with self.assertRaises(AssertionError):
                    validate_research_report(value)

    def test_missing_count_does_not_default_to_zero(self):
        for key in ('new_native_CFD_runs', 'new_builds'):
            with self.subTest(key=key):
                value = report()
                value.pop(key)
                with self.assertRaises(AssertionError):
                    validate_research_report(value)

    def test_any_positive_qualification_claim_is_rejected(self):
        for key in ('physical_qualification_passed', 'M6_qualification_passed',
                    'LLM_improvement_demonstrated'):
            with self.subTest(key=key):
                value = report()
                value[key] = True
                with self.assertRaises(AssertionError):
                    validate_research_report(value)

    def test_missing_or_numeric_false_qualification_is_rejected(self):
        for replacement in (None, 0, '', 'false'):
            with self.subTest(replacement=replacement):
                value = report()
                value['physical_qualification_passed'] = replacement
                with self.assertRaises(AssertionError):
                    validate_research_report(value)

    def test_both_languages_require_an_actual_nonempty_summary(self):
        for key in ('summary_tr', 'summary_en'):
            with self.subTest(key=key):
                value = report()
                value[key] = ' \n '
                with self.assertRaises(AssertionError):
                    validate_research_report(value)


class ResearchPayloadGuards(unittest.TestCase):
    def test_complete_source_research_needs_no_csv(self):
        value = plan()
        self.assertFalse(any(r['source_path'].endswith('.csv') for r in value['changed']))
        assert_research_payloads(value)
        assert_distribution_scope(value)

    def test_missing_any_research_module_is_not_silently_accepted(self):
        for stem in ('numerics', 'validation_mesh', 'cad_agent'):
            with self.subTest(stem=stem):
                value = plan()
                value['changed'] = [r for r in value['changed']
                                    if not r['source_path'].endswith('/' + stem + '.json')]
                with self.assertRaises(AssertionError):
                    assert_research_payloads(value)

    def test_missing_main_html_is_rejected(self):
        value = plan()
        value['changed'] = [r for r in value['changed'] if not r['source_path'].endswith('.html')]
        with self.assertRaises(AssertionError):
            assert_research_payloads(value)

    def test_research_relegated_to_an_archive_is_not_git_readable_payload(self):
        value = plan()
        value['changed'][0]['storage'] = 'release_asset'
        with self.assertRaises(AssertionError):
            assert_research_payloads(value)

    def test_windows_separators_preserve_expected_source_identity(self):
        value = plan()
        for row in value['changed']:
            row['source_path'] = row['source_path'].replace('/', '\\')
        assert_research_payloads(value)
        assert_distribution_scope(value)

    def test_tools_and_generated_build_binary_are_rejected(self):
        for path in ('tools/su2/SU2_CFD.exe',
                     'work/su2_build_20261027/generated.dll',
                     'work/su2_build_resume_20261027/compiler.zip'):
            with self.subTest(path=path):
                value = plan()
                value['changed'].append({'source_path': path, 'storage': 'git'})
                with self.assertRaises(AssertionError):
                    assert_distribution_scope(value)

    def test_source_path_escape_is_rejected(self):
        for path in ('../tools/hidden.exe', '/absolute/research.json',
                     'C:\\outside\\source.json', 'work/../tools/hidden.exe'):
            with self.subTest(path=path):
                value = plan()
                value['changed'].append({'source_path': path, 'storage': 'git'})
                with self.assertRaises(AssertionError):
                    assert_distribution_scope(value)

    def test_old_build_text_evidence_is_retained_without_new_build_claim(self):
        value = plan()
        value['changed'].append({'source_path': 'work/su2_build_resume_20261027/old-observation.json',
                                 'storage': 'git'})
        assert_distribution_scope(value)
        validate_research_report(report())


if __name__ == '__main__':
    unittest.main()
