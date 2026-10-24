"""One command runs native analyses, CAD conversion, plots and the final report."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
steps=[(ROOT/'.venv/Scripts/python.exe',ROOT/'work/native/run_external.py'),
       (ROOT/'.venv-cad/Scripts/python.exe',ROOT/'work/native/draw_aircraft.py'),
       (ROOT/'.venv/Scripts/python.exe',ROOT/'work/native/finish_report.py')]
for python,script in steps:
    result=subprocess.run([str(python),'-X','utf8',str(script)],cwd=ROOT)
    if result.returncode:
        print(f'FAILED: {script.name}; inspect its output and raw logs.',flush=True)
        sys.exit(result.returncode)
node=Path('C:/Users/Urungu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
result=subprocess.run([str(node),str(ROOT/'work/native/render_drawings.cjs')],cwd=ROOT)
sys.exit(result.returncode)
