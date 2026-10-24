"""Executed by FreeCADCmd; configure only this project's portable profile."""
import json
import os
from pathlib import Path
import FreeCAD as App
root=Path(os.environ['UAV_PROJECT_ROOT'])
meta=json.loads((root/'work/setup/freecad_install.json').read_text())
expected={'Ccx':('ccxBinaryPath',meta['executables']['ccx.exe']),
          'Gmsh':('gmshBinaryPath',meta['executables']['gmsh.exe'])}
for group,(key,value) in expected.items():
    params=App.ParamGet('User parameter:BaseApp/Preferences/Mod/Fem/'+group)
    if not os.environ.get('UAV_PREFERENCES_CHECK_ONLY'): params.SetString(key,value)
    assert params.GetString(key,'')==value and Path(value).is_file()
if not os.environ.get('UAV_PREFERENCES_CHECK_ONLY'): App.saveParameter()
print('PORTABLE_FEM_PREFERENCES_OK',flush=True)
