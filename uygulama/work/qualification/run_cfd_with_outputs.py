from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
for python,script in [(ROOT/'.venv/Scripts/python.exe','run_cfd.py'),(ROOT/'.venv-cad/Scripts/python.exe','postprocess.py')]:
    code=subprocess.call([str(python),'-X','utf8',str(ROOT/'work/qualification'/script)],cwd=ROOT)
    if code: raise SystemExit(code)
