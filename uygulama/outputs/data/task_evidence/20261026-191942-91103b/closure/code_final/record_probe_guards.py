from prepare import ROOT,save,sha,now
from pathlib import Path
import unittest,io
import test_probe_residual_analysis,test_explicit_freeze

def main():
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in [test_probe_residual_analysis,test_explicit_freeze])
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    log=ROOT/'work/tests/logs/residual_probe_20261026.txt';log.parent.mkdir(parents=True,exist_ok=True);log.write_text(stream.getvalue(),encoding='utf-8')
    result={'checked_utc':now(),'tests_run':r.testsRun,'passed':r.wasSuccessful(),'failures':len(r.failures),'errors':len(r.errors),
      'log':str(log.relative_to(ROOT)),'log_sha256':sha(log),'test_code_sha256':{str(Path(m.__file__).relative_to(ROOT)):sha(Path(m.__file__)) for m in [test_probe_residual_analysis,test_explicit_freeze]},'physical_qualification':False}
    save(ROOT/'outputs/reports/residual_probe_guards_20261026.json',result);print(result);assert r.wasSuccessful()

if __name__=='__main__':main()
