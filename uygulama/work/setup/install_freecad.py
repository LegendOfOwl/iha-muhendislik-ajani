"""Install official portable FreeCAD, checking the upstream SHA256 before extraction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import py7zr
import subprocess

ROOT = Path(__file__).resolve().parents[2]
meta = json.loads((ROOT/'work/research/freecad_release.json').read_text(encoding='utf-8'))
asset = next(a for a in meta['assets'] if a['name'].endswith('Windows-x86_64-py311.7z'))
checksum_asset = next(a for a in meta['assets'] if a['name'] == asset['name']+'-SHA256.txt')
dest = ROOT/'work/setup/downloads'/asset['name']
dest.parent.mkdir(parents=True, exist_ok=True)
headers={'User-Agent':'UAV-engineering-workspace/1.0'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120)
if not dest.exists() or dest.stat().st_size != asset['size']:
    partial=dest.with_suffix('.partial')
    with get(asset['browser_download_url']) as src, partial.open('wb') as out:
        total=0
        while block:=src.read(2**20):
            out.write(block); total+=len(block)
            if total % (32*2**20)<len(block): print(f'Downloaded {total/2**20:.0f} MiB',flush=True)
    partial.replace(dest)
with get(checksum_asset['browser_download_url']) as response:
    checksum_text=response.read().decode()
(dest.parent/checksum_asset['name']).write_text(checksum_text)
expected=checksum_text.strip().split()[0].lower()
with dest.open('rb') as stream:
    actual=hashlib.file_digest(stream,'sha256').hexdigest()
assert actual==expected, 'Upstream SHA256 mismatch'
print('Upstream SHA256 verified',actual,flush=True)
target=(ROOT/'tools/freecad').resolve()
target.mkdir(parents=True,exist_ok=True)
with py7zr.SevenZipFile(dest) as archive:
    for name in archive.getnames():
        assert (target/name).resolve().is_relative_to(target), 'Unsafe archive path'
    print('Extracting portable FreeCAD',flush=True)
    try:
        archive.extractall(target)
    except py7zr.exceptions.UnsupportedCompressionMethodError:
        # Official FreeCAD uses BCJ2, unsupported by Python's liblzma decoder.
        helper=ROOT/'tools/archive/7zr.exe'
        helper.parent.mkdir(parents=True,exist_ok=True)
        if not helper.exists():
            with get('https://www.7-zip.org/a/7zr.exe') as src:
                helper.write_bytes(src.read())
        with helper.open('rb') as stream: helper_sha=hashlib.file_digest(stream,'sha256').hexdigest()
        (ROOT/'work/setup/7zr_source.json').write_text(json.dumps({'url':'https://www.7-zip.org/a/7zr.exe','sha256':helper_sha}))
        assert target.is_relative_to(ROOT/'tools')
        with (ROOT/'work/setup/freecad_extract.log').open('w') as log:
            result=subprocess.run([str(helper),'x','-y','-o'+str(target),str(dest)],stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode==0, 'Read work/setup/freecad_extract.log'
executables={p.name:str(p) for p in target.rglob('*.exe') if p.name.lower() in {'freecad.exe','freecadcmd.exe','ccx.exe','gmsh.exe'} or p.name.lower().startswith('ccx_')}
for alias,canonical in [('freecad.exe','FreeCAD.exe'),('freecadcmd.exe','FreeCADCmd.exe')]:
    if alias in executables and canonical in executables:
        del executables[alias]
manifest={'version':meta['tag_name'],'installed_utc':datetime.now(timezone.utc).isoformat(),
          'source_url':asset['browser_download_url'],'archive_bytes':dest.stat().st_size,
          'archive_sha256':actual,'upstream_sha256_verified':True,
          'install_directory':str(target),'executables':executables,'verified':False}
(ROOT/'work/setup/freecad_install.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2),flush=True)
