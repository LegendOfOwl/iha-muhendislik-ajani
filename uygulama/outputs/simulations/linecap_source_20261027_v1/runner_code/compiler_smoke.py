"""Actual compiler/OpenMP preflight, not a CFD or solver qualification."""
from pathlib import Path
import sys,os,subprocess,importlib.metadata,json
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now,memory
sys.path.insert(0,str(BASE))
from build_runner import run_build

def environment():
    folder=ROOT/'tools/fortran_msys2/ucrt64/bin'
    return dict(os.environ,PATH=str(folder)+os.pathsep+str(ROOT/'.venv/Scripts')+os.pathsep+os.environ['PATH'],
                CC=str(folder/'gcc.exe'),CXX=str(folder/'g++.exe'),OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')

def main():
    env=environment();source=BASE/'omp_preflight.cpp';exe=BASE/'omp_preflight.exe'
    label=sys.argv[1] if len(sys.argv)>1 else 'compiler_preflight_v1'
    assert not exe.exists()
    text='#include <omp.h>\n#include <iostream>\nint main(){int count=0;\n#pragma omp parallel reduction(+:count)\n{count+=1;}\nstd::cout << "{\\"threads\\":" << count << ",\\"openmp_macro\\":" << _OPENMP << ",\\"double_bytes\\":" << sizeof(double) << "}" << std::endl;return count==4 && sizeof(double)==8?0:2;}\n'
    if source.exists():assert source.read_text(encoding='utf-8')==text
    else:source.write_text(text,encoding='utf-8')
    flags=['-std=c++17','-O3','-march=haswell','-fopenmp','-ffast-math','-fno-finite-math-only']
    status=run_build([env['CXX'],*flags,str(source),'-o',str(exe)],BASE,label,30,env)
    assert status['succeeded'],status
    result=subprocess.run([str(exe)],env=env,cwd=BASE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10)
    (BASE/'omp_preflight_native.log').write_bytes(result.stdout)
    assert result.returncode==0
    values=json.loads(result.stdout);assert values['threads']==4 and values['double_bytes']==8
    compiler=Path(env['CXX']);cc1=Path(subprocess.check_output([str(compiler),'-print-prog-name=cc1plus'],env=env,text=True).strip()).resolve()
    version=subprocess.check_output([str(compiler),'--version'],env=env,text=True)
    (BASE/'compiler_version.txt').write_text(version,encoding='utf-8')
    dlls={str(p.relative_to(ROOT)):sha(p) for p in compiler.parent.glob('*.dll') if p.name in {'libgomp-1.dll','libstdc++-6.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll'}}
    assert len(dlls)==4
    wheels=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in (ROOT/'tools/su2-build/packages').glob('*.whl')]
    report={'checked_utc':now(),'passed':True,'scope':'Compiler C++17+Haswell+OpenMP four-thread probe only; no SU2 source built yet',
        'installed_packages':{name:importlib.metadata.version(name) for name in ['meson','ninja','psutil']},'wheels':wheels,
        'compiler':{'path':str(compiler.relative_to(ROOT)),'sha256':sha(compiler),'cc1plus_path':str(cc1.relative_to(ROOT)),
                    'cc1plus_sha256':sha(cc1),'version_output_sha256':sha(BASE/'compiler_version.txt')},
        'runtime_DLL_sha256':dlls,'flags':flags,'OpenMP_probe':values,'compile_status':status,
        'source_sha256':sha(source),'executable_sha256':sha(exe),'memory':memory(),
        'global_environment_changed':False,'physical_qualification_passed':False}
    save(ROOT/'outputs/reports/su2_build_preflight_20261027.json',report)
    save(ROOT/'work/setup/su2_source_build_install.json',{'recorded_utc':now(),'status':'light_build_tools_installed; compiler_preflight_passed; SU2source_not_built',
        'packages':report['installed_packages'],'reference':str((ROOT/'outputs/reports/su2_build_preflight_20261027.json').relative_to(ROOT)),
        'native_release_executable_replaced':False,'physical_qualification_passed':False})
    print({'compiler_OpenMP_preflight_passed':True,'native_probe':values,'packages':report['installed_packages']},flush=True)

if __name__=='__main__':main()
