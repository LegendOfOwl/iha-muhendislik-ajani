import json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
meta=json.loads((ROOT/'work/setup/freecad_install.json').read_text());env=dict(os.environ,UAV_VALIDATION_ROOT=str(ROOT))
for key,sub in [('FREECAD_USER_HOME','home'),('FREECAD_USER_DATA','data'),('FREECAD_USER_TEMP','temp')]:env[key]=str(ROOT/'work/freecad'/sub)
started=time.time()
with (ROOT/'work/validation/freecad_views.log').open('w',encoding='utf-8') as log:r=subprocess.run([meta['executables']['FreeCAD.exe'],str(ROOT/'work/validation/finish_freecad_views.py')],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
pid=json.loads((ROOT/'work/validation/projects.json').read_text())['cad'];proof=ROOT/'outputs/projects'/pid/'reports/native_view_checks.json'
while time.time()-started<90 and (not proof.exists() or proof.stat().st_mtime<started):time.sleep(.2)
print('FreeCAD GUI process exit',r.returncode)
print((ROOT/'work/validation/freecad_views.log').read_text()[-500:])
if r.returncode or not proof.exists() or proof.stat().st_mtime<started or not json.loads(proof.read_text())['passed']:raise ValueError('Native GUI view save failed')
