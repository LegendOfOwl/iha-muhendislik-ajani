"""Recover the exact failed build recipe and retain observed rerun evidence."""
from pathlib import Path
import sys,hashlib
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now

def main():
    source=(BASE/'build_su2.py').read_text(encoding='utf-8')
    after="'wrap_mode': 'nodownload',\n           'cpp_args': ['-I../source/SU2_CFD/src/interfaces']}"
    before="'wrap_mode': 'nodownload'}"
    assert source.count(after)==1
    old=source.replace(after,before).encode()
    expected=read(BASE/'build_evidence/p32a/contract.json')['driver_sha256']
    assert hashlib.sha256(old).hexdigest()==expected
    target=BASE/'build_evidence/p32a/build_su2_v1.py';assert not target.exists();target.write_bytes(old)
    save(BASE/'build_recipe_revision.json',{'recorded_utc':now(),'old_driver_sha256':expected,
        'new_driver_sha256':sha(BASE/'build_su2.py'),'only_driver_change':'Common cpp_args include search directory',
        'old_recipe_exactly_recovered':True,'source_files_changed':False,
        'new_recipe_rerun_tests':{'observed_in_tool_output':True,'command':'.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s work/su2_build_20261027 -p test_build_su2_guards.py -v',
            'native_exit_code':0,'tests':9,'failures':0,'errors':0,'seconds_reported':.090,
            'scope':'Same9 tests rerun after one compiler-option change, not9 additional distinct checks.'}})
    print('Preserved exact first recipe and revision observation',flush=True)

if __name__=='__main__':main()
