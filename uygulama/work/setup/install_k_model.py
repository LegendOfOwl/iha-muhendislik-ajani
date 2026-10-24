"""Install the user's referenced small OpenSCAD model and official portable OpenSCAD."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[2]
def get(url): return urlopen(Request(url,headers={'User-Agent':'UAV-workspace/1.0'}),timeout=120)
def fetch(url,path,size=None,expected=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or (size and path.stat().st_size!=size):
        tmp=path.with_suffix('.partial')
        with get(url) as src,tmp.open('wb') as out:
            n=0
            while data:=src.read(2**20):
                out.write(data); n+=len(data)
                if n%(128*2**20)<len(data): print(path.name,round(n/2**20),'MiB',flush=True)
        tmp.replace(path)
    with path.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
    if expected: assert sha==expected
    return {'url':url,'path':str(path),'bytes':path.stat().st_size,'sha256':sha,'upstream_sha256_verified':bool(expected)}
meta=json.loads((ROOT/'work/research/k_gguf.json').read_text())
file=next(a for a in meta['siblings'] if a['rfilename']=='k-1b-q8_0.gguf')
url=f'https://huggingface.co/{meta["id"]}/resolve/{meta["sha"]}/{file["rfilename"]}'
model=fetch(url,ROOT/'tools/cad-model/k-1b-q8_0.gguf',file['size'],file['lfs']['sha256'])
release=json.loads((ROOT/'work/research/openscad_release.json').read_text())
a=next(a for a in release['assets'] if a['name']=='OpenSCAD-2021.01-x86-64.zip')
expected=None
try:
    with get('https://files.openscad.org/'+a['name']+'.sha256') as src: checksum=src.read().decode()
    (ROOT/'work/setup/downloads'/(a['name']+'.sha256')).write_text(checksum)
    expected=checksum.strip().split()[0]
except Exception as exc: print('Published checksum unavailable:',exc,flush=True)
archive=fetch(a['browser_download_url'],ROOT/'work/setup/downloads'/a['name'],a['size'],expected)
target=(ROOT/'tools/openscad').resolve(); target.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive['path']) as zip:
    assert zip.testzip() is None
    for name in zip.namelist(): assert (target/name).resolve().is_relative_to(target)
    zip.extractall(target)
exe=next(target.rglob('openscad.com'),None) or next(target.rglob('openscad.exe'))
manifest={'installed_utc':datetime.now(timezone.utc).isoformat(),'model_repository':meta['id'],
          'revision':meta['sha'],'quantization':'Q8_0','model':model,'openscad_archive':archive,
          'openscad_version':'2021.01','executable':str(exe),'verified_inference':False,
          'license_note':'Card declares Apache-2.0; Gemma base terms also require review before redistribution.'}
(ROOT/'work/setup/k_model_install.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('K-1B and OpenSCAD installed',flush=True)
