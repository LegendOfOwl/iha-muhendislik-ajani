"""First combined integration check of the newly completed recipe/release helpers."""
from pathlib import Path
import sys,unittest,io,hashlib,json
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path[:0]=[str(BASE),str(ROOT/'work/publish')]
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import now,save,sha

def main():
    target=ROOT/'outputs/reports/su2_resume_checks_20261027.json'
    assert not target.exists()
    files=[BASE/'ninja_recipe.py',BASE/'test_ninja_recipe.py',BASE/'build_cap.py',BASE/'test_build_cap.py',
           ROOT/'work/publish/verify_remote_v017.py',ROOT/'work/publish/test_v017_remote_guards.py']
    before={str(p.relative_to(ROOT)):sha(p) for p in files}
    log=io.StringIO();suite=unittest.TestSuite()
    groups=['test_ninja_recipe','test_build_cap','test_v017_remote_guards']
    for name in groups:suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    path=BASE/'component_checks.log';path.write_text(log.getvalue(),encoding='utf-8')
    after={str(p.relative_to(ROOT)):sha(p) for p in files};assert before==after
    record={'checked_utc':now(),'tests_run':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'passed':result.wasSuccessful(),'groups':groups,
        'counts':{'engineering_recipe_and_cap':28,'publication_guards':12},
        'purpose':'Combined root-level imports, provenance and release helper integration; prior70 checks not rerun.',
        'code_sha256':after,'log_path':str(path.relative_to(ROOT)),'log_sha256':sha(path),
        'CFD_runs_launched_by_tests':0,'physical_qualification_passed':False,'LLM_improvement_demonstrated':False}
    save(target,record);print({k:record[k] for k in ('tests_run','failures','errors','passed')},flush=True)
    if not result.wasSuccessful():print(log.getvalue());raise SystemExit(1)

if __name__=='__main__':main()
