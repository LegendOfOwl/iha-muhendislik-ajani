from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
import zipfile
ROOT=Path(__file__).resolve().parents[2]
release=json.loads((ROOT/'work/qualification/su2_release.json').read_text())
asset=next(a for a in release['assets'] if a['name'].endswith('win64-omp.zip'))
archive=ROOT/'work/setup/downloads'/asset['name']; archive.parent.mkdir(exist_ok=True)
def digest(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
if not archive.exists() or archive.stat().st_size!=asset['size']:
    with urlopen(Request(asset['browser_download_url'],headers={'User-Agent':'Engineering-toolchain/1.0'}),timeout=90) as r,archive.open('wb') as f:
        while data:=r.read(2**20): f.write(data)
expected=asset['digest'].split(':',1)[1]; assert digest(archive)==expected
dest=ROOT/'tools/su2'/release['tag_name']; dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        if not (dest/name).resolve().is_relative_to(dest.resolve()): raise ValueError('Unsafe archive path')
    z.extractall(dest)
for nested in dest.glob('*.zip'):
    with zipfile.ZipFile(nested) as z:
        for name in z.namelist():
            if not (dest/name).resolve().is_relative_to(dest.resolve()): raise ValueError('Unsafe nested archive path')
        z.extractall(dest)
exes=list(dest.rglob('SU2_CFD.exe')); assert len(exes)==1
manifest={'installed_utc':datetime.now(timezone.utc).isoformat(),'version':release['tag_name'],
    'source_url':asset['browser_download_url'],'archive_sha256':expected,'upstream_sha256_verified':True,
    'archive_bytes':asset['size'],'executable':str(exes[0]),'integration':'Native Windows OpenMP; no global PATH change',
    'status':'installed; actual CFD qualification pending'}
(ROOT/'work/setup/su2_install.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2),flush=True)
dest=ROOT/'work/qualification/sources'; dest.mkdir(exist_ok=True)
files={
 'inv_NACA0012.cfg':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/QuickStart/inv_NACA0012.cfg',
 'mesh_NACA0012_inv.su2':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/QuickStart/mesh_NACA0012_inv.su2',
 'turb_naca0012.cfg':'https://raw.githubusercontent.com/su2code/Tutorials/master/incompressible_flow/Inc_Turbulent_NACA0012/turb_naca0012.cfg',
 'n0012_113-33.su2':'https://raw.githubusercontent.com/su2code/TestCases/master/rans/naca0012/n0012_113-33.su2',
 'n0012_225-65.su2':'https://raw.githubusercontent.com/su2code/TestCases/master/rans/naca0012/n0012_225-65.su2',
 'n0012_449-129.su2':'https://raw.githubusercontent.com/su2code/TestCases/master/rans/naca0012/n0012_449-129.su2',
 'naca2412.dat':'https://m-selig.ae.illinois.edu/ads/coord/naca2412.dat',
 'nasa_naca0012_validation.html':'https://turbmodels.larc.nasa.gov/naca0012_val.html',
}
sources=[]
for name,url in files.items():
    p=dest/name
    try:
        if not p.exists():
            with urlopen(Request(url,headers={'User-Agent':'Engineering-qualification/1.0'}),timeout=60) as r: p.write_bytes(r.read(30*2**20))
        sources.append({'file':str(p.relative_to(ROOT)),'url':url,'bytes':p.stat().st_size,'sha256':digest(p)})
        print(name,p.stat().st_size,flush=True)
    except Exception as e: print(name,type(e).__name__,str(e),flush=True)
(dest/'source_manifest.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
