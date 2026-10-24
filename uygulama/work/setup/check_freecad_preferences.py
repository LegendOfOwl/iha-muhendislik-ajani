"""Check portable FEM preferences survive a fresh native FreeCAD process."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
meta=json.loads((ROOT/'work/setup/freecad_install.json').read_text())
env=dict(os.environ,UAV_PROJECT_ROOT=str(ROOT))
for key,rel in [('FREECAD_USER_HOME','home'),('FREECAD_USER_DATA','data'),('FREECAD_USER_TEMP','temp')]:
    p=ROOT/'work/freecad'/rel; p.mkdir(parents=True,exist_ok=True); env[key]=str(p)
checks=[]
for label in ['write','fresh_process_read']:
    if label!='write': env['UAV_PREFERENCES_CHECK_ONLY']='1'
    log=ROOT/'work/setup'/('freecad_preferences_'+label+'.log')
    with log.open('w') as stream:
        p=subprocess.run([meta['executables']['FreeCADCmd.exe'],str(ROOT/'work/setup/freecad_preferences.py')],
              env=env,input='',text=True,stdout=stream,stderr=subprocess.STDOUT,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
    ok=p.returncode==0 and 'PORTABLE_FEM_PREFERENCES_OK' in log.read_text(errors='replace')
    checks.append({'name':label,'passed':ok,'log':str(log)})
gmsh=subprocess.run([meta['executables']['gmsh.exe'],'-version'],capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
checks.append({'name':'bundled_gmsh_binary','passed':gmsh.returncode==0,'version_output':(gmsh.stdout+gmsh.stderr).strip()})
result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,
        'profile_directory':env['FREECAD_USER_DATA'],'system_preferences_changed':False}
(ROOT/'outputs/reports/freecad_portable_profile.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
