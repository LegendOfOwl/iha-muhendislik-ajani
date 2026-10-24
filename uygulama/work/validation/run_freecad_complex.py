import json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    meta=json.loads((ROOT/'work/setup/freecad_install.json').read_text());env=dict(os.environ,UAV_VALIDATION_ROOT=str(ROOT))
    for key,sub in [('FREECAD_USER_HOME','home'),('FREECAD_USER_DATA','data'),('FREECAD_USER_TEMP','temp')]:env[key]=str(ROOT/'work/freecad'/sub)
    with (ROOT/'work/validation/freecad_complex.log').open('w',encoding='utf-8') as log:r=subprocess.run([meta['executables']['FreeCADCmd.exe'],str(ROOT/'work/validation/freecad_complex.py')],cwd=ROOT,env=env,input='',text=True,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    print('Native FreeCAD exit',r.returncode)
    print((ROOT/'work/validation/freecad_complex.log').read_text()[-1600:])
    if r.returncode or 'COMPLEX_NATIVE_CAD_COMPLETE' not in (ROOT/'work/validation/freecad_complex.log').read_text():raise ValueError('Native CAD test did not complete')
if __name__=='__main__':main()
