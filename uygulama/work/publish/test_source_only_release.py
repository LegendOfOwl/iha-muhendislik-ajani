"""Check the real source-only restoration branch without launching restore/network."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import verify_incremental as v


class SourceOnlyRelease(unittest.TestCase):
    def check_not_applicable(self,files):
        with patch.object(v,'read',return_value={'archives':[]}),patch.object(v,'module',side_effect=AssertionError('Restore must not run')):
            result=v.full_restore({'files':files})
        self.assertIs(result['performed'],False)
        self.assertEqual(result['restored_original_paths'],0)
        self.assertIsNone(result['all_sha256_passed'])
    def test_source_only_is_not_fake_raw_success(self):
        self.check_not_applicable([{'storage':'git','version':v.VERSION}])
    def test_old_raw_data_does_not_become_current_restore(self):
        self.check_not_applicable([{'storage':'release_asset','release_tag':'v0.17.0'}])
    def test_missing_current_archive_is_rejected(self):
        with patch.object(v,'read',return_value={'archives':[]}),patch.object(v,'module',side_effect=AssertionError('Restore must not run')):
            with self.assertRaisesRegex(AssertionError,'Current raw rows'):
                v.full_restore({'files':[{'storage':'release_asset','release_tag':v.VERSION}]})


if __name__=='__main__':
    import io
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceOnlyRelease))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    record={'checked_utc':datetime.now(timezone.utc).isoformat(),'version':v.VERSION,'tests_run':result.testsRun,
        'passed':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),
        'scope':'Source-only publication branch; no native CFD, restore, build, network or publication launched',
        'code_sha256':{p.relative_to(v.ROOT).as_posix():sha(p) for p in (Path(v.__file__),Path(__file__))},
        'raw_output':stream.getvalue(),'new_native_CFD_runs':0}
    (v.ROOT/'outputs/reports/source_only_publication_checks_20261028.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(stream.getvalue());raise SystemExit(0 if result.wasSuccessful() else 1)
