"""Project-local portable Elmer GUI/solver; no installer or global PATH changes."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import Request,urlopen
import zipfile
ROOT=Path(__file__).resolve().parents[2]
URL='https://www.nic.funet.fi/pub/sci/physics/elmer/bin/windows/ElmerFEM-gui-nompi-Windows-AMD64.zip'
dest=ROOT/'work/setup/downloads/elmer-gui-nompi-20260805.zip'; dest.parent.mkdir(exist_ok=True)
headers={'User-Agent':'UAV-Engineering-local-setup/1.0'}
if not dest.exists():
    part=dest.with_suffix('.zip.part')
    print('Downloading official portable Elmer with native Windows TLS verification',flush=True)
    subprocess.run(['curl.exe','--fail','--location','--proto','=https','--proto-redir','=https','--retry','2',
        '--connect-timeout','30','--max-time','900','--output',str(part),URL],check=True)
    part.replace(dest)
with dest.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
target=(ROOT/'tools/elmer').resolve(); target.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(dest) as archive:
    for name in archive.namelist():
        if not (target/name).resolve().is_relative_to(target): raise ValueError('Unsafe archive member')
    bad=archive.testzip()
    if bad: raise ValueError('Corrupt ZIP: '+bad)
    archive.extractall(target)
executables={name:str(next(target.rglob(name))) for name in ['ElmerSolver.exe','ElmerGrid.exe','ElmerGUI.exe']}
meta={'installed_utc':datetime.now(timezone.utc).isoformat(),'source_url':URL,
      'distribution':'Official CSC portable non-MPI GUI archive, listing dated 2026-08-05; actual solver build pending native run',
      'archive_bytes':dest.stat().st_size,'archive_sha256':digest,'upstream_sha256_verified':False,
      'checksum_note':'Local SHA256 and ZIP CRC recorded; no upstream SHA256 was provided by the download listing',
      'directory':str(target),'executables':executables,'runtime_verified':False,
      'integration':'Project-local native Windows GUI and FEM flow solver; no global PATH or registry changes'}
(ROOT/'work/setup/elmer_install.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)
