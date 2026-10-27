"""Record a source-preserving search-path fix before the second pristine build."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now

def main():
    source=ROOT/'tools/su2-build/v8.5.0/source'
    cpp=source/'SU2_CFD/src/interfaces/fsi/CFlowTractionInterface.cpp'
    token='../../../Common/include/interface_interpolation/CInterpolator.hpp'
    assert ('#include "'+token+'"') in cpp.read_text(encoding='utf-8')
    intended=source/'Common/include/interface_interpolation/CInterpolator.hpp'
    direct=(cpp.parent/token).resolve();search=(source/'SU2_CFD/src/interfaces'/token).resolve()
    assert not direct.exists() and search==intended.resolve() and intended.is_file()
    old=ROOT/'tools/su2-build/v8.5.0/controls/p32a';s=read(old/'status.json')
    assert s['succeeded'] is False and s['phases'][-1]['exit_code']==1
    row={'recorded_utc':now(),'old_build':'p32a','old_status_sha256':sha(old/'status.json'),
      'old_log_sha256':sha(BASE/'p32a-compile.log'),'source_commit':s['source_commit'],
      'observed_error':'CFlowTractionInterface.cpp:34 cannot find quoted ../../../Common/include/interface_interpolation/CInterpolator.hpp',
      'source_cpp_sha256':sha(cpp),'header_sha256':sha(intended),
      'failed_direct_resolution':str(direct.relative_to(ROOT)),'additional_search_resolution':str(search.relative_to(ROOT)),
      'common_build_option':{'cpp_args':['-I../source/SU2_CFD/src/interfaces']},
      'scope':'Additional search directory in both pristine32 and cap256; upstream source bytes unchanged. Native reproduction still mandatory.',
      'diagnosis':'This quoted relative include uses the interfaces-depth path from a file one level deeper in interfaces/fsi; no matching include search directory was in the failed compile command.',
      'not_a_solver_physics_change':True,'source_file_patch_applied':False,'global_settings_changed':False,
      'method_design_sha256':sha(BASE/'method_design.json'),'CFD_already_run':False,
      'physical_qualification_passed':False}
    assert not (BASE/'include_path_diagnosis.json').exists();save(BASE/'include_path_diagnosis.json',row)
    print(row['diagnosis'],flush=True)

if __name__=='__main__':main()
