from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[2]
metadata=json.loads((ROOT/'work/research/k1b_deep/cadmonkey32.json').read_text())
entry=next(a for a in metadata['siblings'] if a['rfilename'].endswith('.gguf'))
path=ROOT/'tools/cad-model'/entry['rfilename']
url=f'https://huggingface.co/{metadata["id"]}/resolve/{metadata["sha"]}/{entry["rfilename"]}'
if not path.exists() or path.stat().st_size!=entry['size']:
    temp=path.with_suffix('.partial')
    with urlopen(Request(url,headers={'User-Agent':'Engineering-model-research/1.0'}),timeout=120) as src,temp.open('wb') as dest:
        total=0
        while data:=src.read(2**20):
            dest.write(data); total+=len(data)
            if total%(128*2**20)<len(data): print('Cadmonkey data-32:',round(total/2**20),'MiB',flush=True)
    assert temp.stat().st_size==entry['size']
    temp.replace(path)
with path.open('rb') as src: sha=hashlib.file_digest(src,'sha256').hexdigest()
assert sha==entry['lfs']['sha256'],'Upstream checksum mismatch'
sys.path.insert(0,str(ROOT/'work/models'))
from gguf_metadata import read_metadata
meta=read_metadata(path)
(ROOT/'work/research/k1b_deep/cadmonkey32_gguf_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
result={'installed_utc':datetime.now(timezone.utc).isoformat(),'repository':metadata['id'],'revision':metadata['sha'],
        'model_path':str(path),'source_url':url,'bytes':path.stat().st_size,'sha256':sha,'upstream_sha256_verified':True,
        'architecture':meta.get('general.architecture'),'quantization':'Q8_0','engineering_auto_use':False,
        'status':'experimental; inference and geometry pending'}
(ROOT/'work/setup/cadmonkey32_install.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
