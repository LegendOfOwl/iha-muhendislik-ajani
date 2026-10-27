"""Validate fixed official tarballs and extract confined ordinary files only."""
from pathlib import Path, PurePosixPath
import sys, tarfile, gzip
ROOT=Path(__file__).resolve().parents[2]; BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now
HOME=ROOT/'tools/su2-build/v8.5.0'
ROWS=[
 ('SU2-source-transport3.tar.gz.partial','source','12eb826f049ef7f67df974dfcb44cf36ee07c0f8','https://codeload.github.com/su2code/SU2/tar.gz/12eb826f049ef7f67df974dfcb44cf36ee07c0f8',18876892,'316552bdf987a9254093f1179addc2afa2c396c8fe97fbeeae06250dccaea7e4',72.682254),
 ('Eigen-transport3.tar.gz.partial','eigen-pinned','d71c30c47858effcbd39967097a2d99ee48db464','https://gitlab.com/libeigen/eigen/-/archive/d71c30c47858effcbd39967097a2d99ee48db464/eigen-d71c30c47858effcbd39967097a2d99ee48db464.tar.gz',2719400,'f1d28c2205d015490a685b1e5a171c434da87f757746724de3cb85e69621dec2',16.941745),
 ('MEL-transport4.tar.gz.partial','mel-pinned','46205ab019e5224559091375a6d71aabae6bc5b9','https://codeload.github.com/pcarruscag/MEL/tar.gz/46205ab019e5224559091375a6d71aabae6bc5b9',13894,None,1.849606),
]

def main():
    plan=read(BASE/'setup_plan.json'); rows=[]
    for filename,folder,commit,url,expected,expected_sha,elapsed in ROWS:
        src=HOME/filename; dest=HOME/folder
        assert src.stat().st_size==expected and expected<=plan['download_byte_cap_each']
        digest=sha(src);assert expected_sha is None or expected_sha==digest
        assert not dest.exists(),'Preserve existing source tree'
        # Read through the gzip trailer: an early tar EOF alone is insufficient.
        with gzip.open(src,'rb') as stream:
            total=0
            while chunk:=stream.read(2**20):
                total+=len(chunk); assert total<plan['expanded_source_byte_cap_each']+2**20*20
        with tarfile.open(src,'r:gz') as archive:
            members=archive.getmembers(); assert len(members)<50000
            assert sum(x.size for x in members)<=plan['expanded_source_byte_cap_each']
            roots={PurePosixPath(x.name).parts[0] for x in members};assert len(roots)==1
            root=next(iter(roots));assert commit in root
            seen=set(); validated=[]
            for item in members:
                p=PurePosixPath(item.name)
                assert not p.is_absolute() and '..' not in p.parts and '\\' not in item.name and ':' not in item.name
                assert item.isdir() or item.isfile(),'No links, devices or special nodes'
                rel=Path(*p.parts[1:]);target=(dest/rel).resolve()
                assert target.is_relative_to(dest.resolve())
                if not p.parts[1:]:continue
                key=str(rel).casefold();assert key not in seen;seen.add(key)
                validated.append((item,target))
            dest.mkdir(parents=True)
            for item,target in validated:
                if item.isdir():target.mkdir(parents=True,exist_ok=True)
                else:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with archive.extractfile(item) as inp,target.open('xb') as out:
                        while chunk:=inp.read(2**20):out.write(chunk)
        record={'recorded_utc':now(),'url':url,'commit':commit,'path':str(src.relative_to(ROOT)),
                'sha256':digest,'bytes':expected,'members':len(members),'expanded_file_bytes':sum(x.size for x in members),
                'destination':str(dest.relative_to(ROOT)),'transport':'curl8.21 HTTP1.1 HTTPS, default Schannel certificate checks',
                'native_exit_code_observed':0,'http_status_observed':200,'ssl_verify_result_observed':0,
                'elapsed_seconds_observed':elapsed,'gzip_trailer_checked':True,'safe_members_checked':True,
                'receipt_note':'Exit/status/transfer bytes observed in tool output; identity/CRC/paths independently checked from retained archive.'}
        save(dest/'archive_origin.json',record);rows.append(record)
        print({'source':folder,'files':len(members),'bytes':expected,'sha256':digest},flush=True)
    save(BASE/'accepted_archives.json',{'created_utc':now(),'archives':rows,'global_settings_changed':False})

if __name__=='__main__':main()
