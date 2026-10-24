"""Pin and verify a compact CAD vision model plus an official native GPU runtime."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[2]
HEADERS={'User-Agent':'UAV-engineering-workspace/1.0'}
def get(url): return urlopen(Request(url,headers=HEADERS),timeout=120)
def download(item):
    path=ROOT/item['path']; path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.stat().st_size!=item['bytes']:
        partial=path.with_suffix(path.suffix+'.partial')
        with get(item['url']) as src, partial.open('wb') as out:
            total=0
            while block:=src.read(2**20):
                out.write(block); total+=len(block)
                if total%(128*2**20)<len(block): print(path.name,round(total/2**20),'MiB',flush=True)
        assert partial.stat().st_size==item['bytes']
        partial.replace(path)
    with path.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
    assert sha==item['sha256'], f'Checksum mismatch: {path}'
    print('Verified',path.name,flush=True)
    return dict(item,absolute_path=str(path),actual_sha256=sha)

repo='mradermacher/Zero-To-CAD-Qwen3-VL-2B-GGUF'
with get(f'https://huggingface.co/api/models/{repo}?blobs=true') as stream: meta=json.load(stream)
(ROOT/'work/research/zero_gguf.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
names=['Zero-To-CAD-Qwen3-VL-2B.Q6_K.gguf','Zero-To-CAD-Qwen3-VL-2B.mmproj-f16.gguf']
items=[]
for name in names:
    file=next(a for a in meta['siblings'] if a['rfilename']==name)
    items.append({'path':'tools/cad-model/'+name,'url':f'https://huggingface.co/{repo}/resolve/{meta["sha"]}/{quote(name)}',
                  'bytes':file['size'],'sha256':file['lfs']['sha256']})
release=json.loads((ROOT/'work/research/llama_nightly_release.json').read_text())
for name in ['llama-b11719-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-12.4-x64.zip']:
    a=next(a for a in release['assets'] if a['name']==name)
    items.append({'path':'work/setup/downloads/'+name,'url':a['browser_download_url'],'bytes':a['size'],
                  'sha256':a['digest'].split(':')[1]})
with ThreadPoolExecutor(max_workers=2) as pool: records=list(pool.map(download,items))
target=(ROOT/'tools/llama-cad').resolve(); target.mkdir(parents=True,exist_ok=True)
for item in records[2:]:
    with zipfile.ZipFile(item['absolute_path']) as archive:
        assert archive.testzip() is None
        for name in archive.namelist(): assert (target/name).resolve().is_relative_to(target)
        archive.extractall(target)
manifest={'installed_utc':datetime.now(timezone.utc).isoformat(),'upstream_model':'ADSKAILab/Zero-To-CAD-Qwen3-VL-2B',
          'quantized_repository':repo,'revision':meta['sha'],'quantization':'Q6_K','vision_precision':'f16',
          'runtime_release':release['tag_name'],'runtime_directory':str(target),
          'files':records,'verified_inference':False,'license':'Apache-2.0 (model); MIT (llama.cpp)'}
(ROOT/'work/setup/cad_model_install.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('CAD model and runtime installed with upstream SHA256 verification',flush=True)
