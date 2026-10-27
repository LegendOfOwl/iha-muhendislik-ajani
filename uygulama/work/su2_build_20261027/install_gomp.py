"""Add only the missing, exact-version OpenMP package from the pinned MSYS2 DB."""
from pathlib import Path
import sys,urllib.request,io,tarfile,hashlib,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now
from compiler_plan import decompress

def main():
    plan=read(BASE/'libgomp_plan.json');db=ROOT/'work/tmr_m6_20261025/sources/ucrt64.db'
    assert sha(db)==plan['db_sha256'] and plan['VERSION']=='16.2.0-6'
    cache=ROOT/'tools/su2-build/packages';path=cache/plan['FILENAME']
    if not path.exists():
        attempts=[]
        for url in [plan['url'],plan['url'].replace('mirror.msys2.org','repo.msys2.org')]:
            try:
                with urllib.request.urlopen(url,timeout=45) as src:raw=src.read(int(plan['CSIZE'])+1)
                assert len(raw)==int(plan['CSIZE']) and hashlib.sha256(raw).hexdigest()==plan['SHA256SUM']
                attempts.append({'url':url,'utc':now(),'verified':True});break
            except Exception:
                attempts.append({'url':url,'utc':now(),'verified':False,'error':traceback.format_exc()})
        record=BASE/('libgomp_download_'+now().replace(':','-')+'.json');save(record,attempts)
        assert attempts[-1]['verified'],'No verified OpenMP package downloaded; see '+str(record)
        path.write_bytes(raw)
    assert sha(path)==plan['SHA256SUM']
    dest=ROOT/'tools/fortran_msys2';files=[]
    with tarfile.open(fileobj=io.BytesIO(decompress(path.read_bytes()))) as archive:
        for entry in archive:
            if not entry.name.startswith('ucrt64/') or not entry.isfile():continue
            assert not entry.issym() and not entry.islnk()
            p=(dest/entry.name).resolve();assert p.is_relative_to(dest.resolve())
            data=archive.extractfile(entry).read();h=hashlib.sha256(data).hexdigest()
            if p.exists():assert sha(p)==h,'Existing toolchain file would change: '+str(p)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            files.append({'path':str(p.relative_to(ROOT)),'sha256':h})
    assert (dest/'ucrt64/bin/libgomp-1.dll').exists()
    save(BASE/'libgomp_install.json',{'installed_utc':now(),'source_plan_sha256':sha(BASE/'libgomp_plan.json'),
        'package_sha256':sha(path),'files':files,'system_PATH_changed':False,'scope':'Exact-version portable OpenMP runtime only'})
    print({'OpenMP_package_bytes':path.stat().st_size,'files_verified':len(files)})

if __name__=='__main__':main()
