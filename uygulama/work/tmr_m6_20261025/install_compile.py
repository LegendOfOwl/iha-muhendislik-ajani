"""Install verified compiler archives within the project and build untouched NASA sources."""
from compiler_plan import ROOT, BASE, decompress
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile
import hashlib
import io
import json
import os
import subprocess
import tarfile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')


def main():
    plan=json.loads((BASE/'compiler_plan.json').read_text())
    dest=ROOT/plan['install_root'];dest.mkdir(parents=True,exist_ok=True)
    installed=[]
    for pkg in plan['packages']:
        path=BASE/'sources/compiler_packages'/pkg['FILENAME']
        assert path.stat().st_size==int(pkg['CSIZE'])
        assert sha(path)==pkg['SHA256SUM']
        with tarfile.open(fileobj=io.BytesIO(decompress(path.read_bytes()))) as archive:
            members=[x for x in archive.getmembers() if x.name.startswith('ucrt64/')]
            for m in members:
                assert (dest/m.name).resolve().is_relative_to(dest.resolve())
            archive.extractall(dest,members=members,filter='data')
        installed.append(dict(name=pkg['NAME'],version=pkg['VERSION'],archive_sha256=sha(path)))
    compiler=dest/'ucrt64/bin/gfortran.exe'
    env=dict(os.environ);env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
    version=subprocess.run([str(compiler),'--version'],env=env,capture_output=True,text=True,timeout=20)
    (BASE/'compiler_version.txt').write_text(version.stdout+version.stderr,encoding='utf-8')
    assert version.returncode==0
    source_root=ROOT/'tools/tmr_m6/source';source_root.mkdir(parents=True,exist_ok=True)
    source_zip=ROOT/'work/cfd_literature_20261025/sources/wing-release-072319.zip'
    with ZipFile(source_zip) as archive:
        for m in archive.infolist():
            if m.is_dir():continue
            name=Path(m.filename).name
            (source_root/name).write_bytes(archive.read(m))
    build=ROOT/'tools/tmr_m6/bin';build.mkdir(parents=True,exist_ok=True)
    compilations=[]
    for source,out in [('hcf_wing_v5p0.f90','hcf_wing.exe'),('hcf_coarsening_v3p9.f90','hcf_coarsening.exe')]:
        command=[str(compiler),'-O2','-fcheck=bounds','-fbacktrace','-o',str(build/out),str(source_root/source)]
        result=subprocess.run(command,cwd=build,env=env,capture_output=True,text=True,timeout=120)
        (BASE/(out+'.compile.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        compilations.append(dict(command=command,exit_code=result.returncode,source_sha256=sha(source_root/source),
                                 executable_sha256=sha(build/out) if (build/out).exists() else None))
        assert result.returncode==0,result.stderr[-3000:]
    manifest={'installed_utc':datetime.now(timezone.utc).isoformat(),'compiler':str(compiler),'compiler_sha256':sha(compiler),
              'compiler_version':version.stdout.splitlines()[0], 'packages':installed,'source_url':'https://www.nasa.gov/wp-content/uploads/2026/04/wing-release-072319.zip',
              'source_archive_sha256':sha(source_zip),'source_modified':False,'compilations':compilations,
              'executables':{x:str(build/x) for x in ['hcf_wing.exe','hcf_coarsening.exe']},
              'process_PATH_prefix':str(compiler.parent),'system_PATH_changed':False,'runtime_mesh_verified':False}
    save(ROOT/'work/setup/tmr_m6_install.json',manifest)
    print(json.dumps({'compiler_version':manifest['compiler_version'],'native_sources_built':len(compilations),'source_modified':False},ensure_ascii=False))


if __name__=='__main__':main()
