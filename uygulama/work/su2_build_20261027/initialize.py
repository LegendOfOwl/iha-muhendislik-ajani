"""Initialize an explicit source-build control; benchmark roles remain frozen."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now,memory
sys.path.insert(0,str(ROOT/'work/agent'))
from learning import instruction_snapshot

def main():
    taskpath=ROOT/'outputs/data/tasks/20261027-154600-18828f.json'
    t=read(taskpath);assert t['status']=='bekliyor'
    t.update(status='çalışıyor',phase='sabit kaynak/derleme hazırlığı',
        applied_lesson_ids=['L04','L05','L07','L08','L09','L10','R01','R03'],
        agent_instruction_snapshot=instruction_snapshot(ROOT),
        acceptance=['Pinned source and dependencies, compiler/OpenMP/runtime manifest',
                    'Pristine32 control before cap256; no compiler difference attributed to cap',
                    'Preregister all numerical, spatial membership and cost gates; preserve failures',
                    'No promotion into old three-grid family; general physical qualification remains false'])
    save(taskpath,t);save(BASE/'task.json',{'path':str(taskpath.relative_to(ROOT))})
    save(BASE/'setup_plan.json',{'created_utc':now(),'memory':memory(),
        'source_commit':read(BASE/'upstream_tag.json')['commit'],
        'scope':'Standalone native Windows OpenMP CFD executable, no global setup changes',
        'pristine_definition':'Upstream source and fixed Eigen/MEL commits; no engineering-source patch',
        'compiler':str(ROOT/'tools/fortran_msys2/ucrt64/bin/g++.exe'),
        'compiler_sha256':sha(ROOT/'tools/fortran_msys2/ucrt64/bin/g++.exe'),
        'release_executable_sha256':sha(Path(read(ROOT/'work/setup/su2_install.json')['executable'])),
        'build_resources':{'parallel_jobs':1,'seconds_each_build_budget':1800,
                           'process_tree_working_set_sum_GiB_max':3.,'system_free_GiB_min':1.},
        'native_resources':{'iterations':200,'seconds_each':240,'threads':4,'working_set_GiB_max':2.5},
        'download_byte_cap_each':250*2**20,'expanded_source_byte_cap_each':700*2**20,
        'large_system_installation':False,'physical_qualification_passed':False})
    print({'task':t['id'],'memory':memory()})

if __name__=='__main__':main()
