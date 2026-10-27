"""Fetch fixed archives through normal HTTPS; never use floating Eigen fallback."""
from pathlib import Path
import sys,urllib.request,zipfile,stat,time,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now
HOME=ROOT/'tools/su2-build/v8.5.0';CACHE=HOME/'archives'

def fetch(url,name,destination):
    plan=read(BASE/'setup_plan.json');CACHE.mkdir(parents=True,exist_ok=True)
    target=CACHE/name
    if not target.exists():
        partial=target.with_suffix(target.suffix+'.partial')
        assert not partial.exists(),'Preserve interrupted transfer; review before retry'
        print('DOWNLOAD',name,flush=True)
        urls=[url]
        if name.startswith('SU2-'):
            commit=read(BASE/'upstream_tag.json')['commit']
            urls += ['https://api.github.com/repos/su2code/SU2/zipball/'+commit]
        for attempt,actual in enumerate(urls,1):
            req=urllib.request.Request(actual,headers={'User-Agent':'UAV-engineering-source-control/1'})
            began=time.monotonic()
            try:
                with urllib.request.urlopen(req,timeout=45) as response,partial.open('wb') as out:
                    total=0
                    while True:
                        chunk=response.read(2**20)
                        if not chunk:break
                        total+=len(chunk)
                        assert total<=plan['download_byte_cap_each'] and time.monotonic()-began<600
                        out.write(chunk)
                        if total%(10*2**20)==0:print('BYTES',name,total,flush=True)
                row_url=actual
                break
            except Exception:
                log=BASE/(name+f'.attempt{attempt}.failure.txt')
                assert not log.exists(),'Preserve earlier attempt record'
                log.write_text(traceback.format_exc(),encoding='utf-8')
                if partial.exists():
                    partial.rename(partial.with_name(partial.name+f'.failed{attempt}'))
                if attempt==len(urls):raise
                print('ALTERNATE_OFFICIAL_ENDPOINT',name,flush=True)
                time.sleep(1)
        partial.replace(target)
    row={'url':url,'downloaded_utc':now(),'path':str(target.relative_to(ROOT)),
         'sha256':sha(target),'bytes':target.stat().st_size,'destination':str(destination.relative_to(ROOT))}
    manifest=BASE/'downloads.json';records=read(manifest) if manifest.exists() else []
    prior=next((x for x in records if x['path']==row['path']),None)
    if prior:assert prior['sha256']==row['sha256']
    else:records.append(row);save(manifest,records)
    if destination.exists():
        assert (destination/'archive_origin.json').exists();return
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        members=z.infolist();assert sum(x.file_size for x in members)<=plan['expanded_source_byte_cap_each']
        roots={x.filename.split('/')[0] for x in members};assert len(roots)==1
        root=next(iter(roots));base=destination.resolve();destination.mkdir(parents=True)
        for member in members:
            parts=Path(member.filename).parts
            assert parts[0]==root and not Path(member.filename).is_absolute() and '..' not in parts
            mode=(member.external_attr>>16)&0o170000
            assert mode!=stat.S_IFLNK,'Archive symlink requires separate review'
            relative=Path(*parts[1:])
            if not str(relative) or str(relative)=='.':continue
            dest=(destination/relative).resolve();assert dest.is_relative_to(base)
            if member.is_dir():dest.mkdir(parents=True,exist_ok=True)
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(member) as src,dest.open('wb') as out:
                    while chunk:=src.read(2**20):out.write(chunk)
    save(destination/'archive_origin.json',row)
    print('EXTRACTED',name,row['bytes'],flush=True)

def main(which):
    commit=read(BASE/'upstream_tag.json')['commit'];src=HOME/'source'
    if which=='su2':fetch('https://codeload.github.com/su2code/SU2/zip/'+commit,'SU2-'+commit+'.zip',src)
    elif which=='eigen':
        c='d71c30c47858effcbd39967097a2d99ee48db464'
        fetch('https://gitlab.com/libeigen/eigen/-/archive/'+c+'/eigen-'+c+'.zip','Eigen-'+c+'.zip',HOME/'eigen-pinned')
    elif which=='mel':
        c='46205ab019e5224559091375a6d71aabae6bc5b9'
        fetch('https://codeload.github.com/pcarruscag/MEL/zip/'+c,'MEL-'+c+'.zip',HOME/'mel-pinned')
    else:raise ValueError(which)

if __name__=='__main__':main(sys.argv[1])
