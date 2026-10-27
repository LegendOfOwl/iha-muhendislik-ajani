"""Complete the verified object cache with one explicit per-TU include fix.

The original failed receipt stays failed. A new control archives a byte-identical
source snapshot and copied EXE; its actual compilation worktree is recorded.
"""
from pathlib import Path
import os,sys,shutil,subprocess,copy
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
OLD_BASE=ROOT/'work/su2_build_20261027'
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now,memory
sys.path.insert(0,str(OLD_BASE))
from build_su2 import tree_files,verify_copy,fingerprint,inside,PIN
from build_runner import run_build
HOME=ROOT/'tools/su2-build/v8.5.0/controls'
ORIGINAL=HOME/'p32a';CONTROL=HOME/'p32r'
TARGET='SU2_CFD/src/SU2_CFD.exe'

def environment():
    from compiler_smoke import environment as original
    env=original()
    for key in ('CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','CPATH','C_INCLUDE_PATH',
                'CPLUS_INCLUDE_PATH','LIBRARY_PATH','COMPILER_PATH','GCC_EXEC_PREFIX',
                'CL','_CL_','LINK','PYTHONPATH','PYTHONHOME','CCACHE_PREFIX'):
        env.pop(key,None)
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    return env

def cache():
    return {str(p.relative_to(ORIGINAL/'build')):{'sha256':sha(p),'bytes':p.stat().st_size}
            for p in sorted((ORIGINAL/'build').rglob('*.obj'))}

def check_inputs():
    c=read(CONTROL/'contract.json');before=read(BASE/'cache_before.json')
    assert sha(ORIGINAL/'status.json')==c['original_failure_status_sha256']
    assert sha(ORIGINAL/'build/build.ninja')==c['original_ninja_sha256']
    assert sha(BASE/'recovery.ninja')==c['recovery_ninja_sha256']
    verify_copy(c['prepared_files'],tree_files(ORIGINAL/'source',ignore=('su2preconfig.timestamp',)))
    for rel,value in before['objects'].items():assert sha(ORIGINAL/'build'/rel)==value['sha256'],rel
    for rel,h in c['compiler_manifest']['binaries'].items():assert sha(ROOT/rel)==h,rel
    for rel,h in c['runtime_DLL_sha256'].items():assert sha(ROOT/rel)==h,rel
    for rel,h in c['recovery_code_sha256'].items():assert sha(ROOT/rel)==h,rel
    return c

def prepare():
    from ninja_recipe import derive_manifest,EXTRA_ARG
    assert not CONTROL.exists(),'New control only'
    prior=read(ORIGINAL/'contract.json');status=read(ORIGINAL/'status.json')
    assert status['succeeded'] is False and status['phases'][-1]['exit_code']==1
    assert status['phases'][-1]['cleanup_confirmed'] is True
    assert prior['source_commit']==PIN and prior['cap']==32
    verify_copy(prior['prepared_files'],tree_files(ORIGINAL/'source',ignore=('su2preconfig.timestamp',)))
    objects=cache();assert len(objects)==258
    raw=(ORIGINAL/'build/build.ninja').read_bytes();modified=derive_manifest(raw)
    audit=read(BASE/'recipe_audit_v1/audit.json')
    import hashlib
    assert hashlib.sha256(raw).hexdigest()==audit['original_manifest_sha256']
    assert hashlib.sha256(modified).hexdigest()==audit['recovery_manifest_sha256']
    assert audit['command_delta']['unchanged_command_count']==289 and audit['inventory']['existing']==258
    assert not (BASE/'recovery.ninja').exists()
    (BASE/'recovery.ninja').write_bytes(modified)
    before=BASE/'before';before.mkdir()
    for name in ('build.ninja','.ninja_log','.ninja_deps','compile_commands.json'):
        shutil.copy2(ORIGINAL/'build'/name,before/name)
    save(BASE/'cache_before.json',{'created_utc':now(),'objects':objects,
         'source':'Completed objects from preserved failed p32a worktree; not labelled with later global cpp_args recipe.'})
    cm=copy.deepcopy(prior['compiler_manifest'])
    for name in ('gcc-ar.exe',):
        path=Path(shutil.which(name,path=environment()['PATH']));assert path.is_file()
        cm['binaries'][str(inside(path,ROOT/'tools').relative_to(ROOT))]=sha(path)
    compiler=ROOT/prior['compiler']['path']
    collect=Path(subprocess.check_output([str(compiler),'-print-prog-name=collect2'],env=environment(),text=True).strip()).resolve()
    cm['binaries'][str(inside(collect,ROOT/'tools').relative_to(ROOT))]=sha(collect)
    cm['per_translation_unit_extra_cpp_args']={'SU2_CFD/src/interfaces/fsi/CFlowTractionInterface.cpp':[EXTRA_ARG]}
    cm['coverage_note']='Pinned declared compiler/linker/archive binaries and per-TU recipe; not a full OS/SDK image. Cached object provenance is retained separately.'
    CONTROL.mkdir();(CONTROL/'source.patch').write_bytes(b'')
    c=copy.deepcopy(prior)
    c.update(label='p32r',variant='pristine32',created_utc=now(),compiler_manifest=cm,
        compiler_manifest_sha256=fingerprint(cm),source_patch_sha256=sha(CONTROL/'source.patch'),
        original_failure_status_sha256=sha(ORIGINAL/'status.json'),original_ninja_sha256=sha(ORIGINAL/'build/build.ninja'),
        recovery_ninja_sha256=sha(BASE/'recovery.ninja'),recovery_cache_before_sha256=sha(BASE/'cache_before.json'),
        recipe_audit_sha256=sha(BASE/'recipe_audit_v1/audit.json'),
        actual_compilation_worktree=str(ORIGINAL.relative_to(ROOT)),
        source_snapshot_semantics='CONTROL/source is an archived byte-identical snapshot, not the actual compilation path; EXE is copied from recorded actual worktree after success.',
        reused_objects=258,common_recipe='Original Meson options + one recorded per-TU header-search addition; not the global cpp_args v2 recipe.',
        commands={'compile':[str(ROOT/'.venv/Scripts/ninja.exe'),'-C',str(ORIGINAL/'build'),'-f',str(BASE/'recovery.ninja'),'-j','1',TARGET]},
        recovery_seconds_budget=1800-status['seconds'],previous_build_seconds=status['seconds'],
        recovery_code_sha256={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),BASE/'ninja_recipe.py',OLD_BASE/'build_runner.py')},
        driver_sha256=sha(Path(__file__)))
    assert c['recovery_seconds_budget']>0
    save(CONTROL/'contract.json',c)
    taskpath=ROOT/read(OLD_BASE/'task.json')['path'];t=read(taskpath)
    t.update(status='çalışıyor',phase='kaynak korunarak kalan derleme hedefleri',blocked_by=[],
             recovery_contract=str((CONTROL/'contract.json').relative_to(ROOT)),recovery_contract_sha256=sha(CONTROL/'contract.json'))
    save(taskpath,t)
    print({'prepared':'p32r','cached_objects':258,'remaining_seconds_budget':c['recovery_seconds_budget'],'memory':memory()},flush=True)

def run():
    c=check_inputs();assert not (BASE/'run_result.json').exists()
    print('START remaining native build',memory(),flush=True)
    result=run_build(c['commands']['compile'],ORIGINAL/'source','p32r-compile',c['recovery_seconds_budget'],environment(),max_tree_gib=3,min_available_gib=1)
    save(BASE/'run_result.json',result)
    print({'succeeded':result['succeeded'],'exit_code':result['exit_code'],'stop_reason':result['stop_reason']},flush=True)

def finalize():
    c=check_inputs();result=read(BASE/'run_result.json');assert not (CONTROL/'status.json').exists()
    s={key:c[key] for key in ('label','variant','cap','source_commit','source_tree_sha256','pristine_archive_tree_sha256',
             'dependency_tree_sha256','compiler_manifest_sha256','runtime_manifest_sha256','source_patch_sha256')}
    s.update(succeeded=False,contract_sha256=sha(CONTROL/'contract.json'),phases=[result],seconds=result['seconds'],
             cumulative_native_build_seconds=c['previous_build_seconds']+result['seconds'],physical_qualification_passed=False)
    assert s['cumulative_native_build_seconds']<=1801
    if result['succeeded']:
        source=CONTROL/'source'
        for rel in c['prepared_files']:
            target=source/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ORIGINAL/'source'/rel,target)
        verify_copy(c['prepared_files'],tree_files(source))
        exe=CONTROL/'build'/TARGET;exe.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ORIGINAL/'build'/TARGET,exe)
        assert sha(exe)==sha(ORIGINAL/'build'/TARGET)
        s.update(succeeded=True,exe=str(exe),exe_sha256=sha(exe),bytes=exe.stat().st_size,
                 actual_worktree_executable=str((ORIGINAL/'build'/TARGET).relative_to(ROOT)))
    save(CONTROL/'status.json',s)
    out=BASE/'build_evidence';out.mkdir()
    for name in ('contract.json','status.json','source.patch'):shutil.copy2(CONTROL/name,out/name)
    print({'succeeded':s['succeeded'],'exe':s.get('exe'),'old_objects_preserved':len(read(BASE/'cache_before.json')['objects'])},flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run,'finalize':finalize}[sys.argv[1]]()
