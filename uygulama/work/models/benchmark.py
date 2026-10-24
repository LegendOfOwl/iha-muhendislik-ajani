"""Measure native local-model inference; validate geometry in a separate stage."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
OUT=ROOT/'outputs'
RUNTIME=ROOT/'tools/llama-cad'
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=str),encoding='utf-8')
def run_command(command,folder):
    save(folder/'command.json',command)
    start=time.perf_counter()
    with (folder/'stdout.txt').open('w',encoding='utf-8') as stdout,(folder/'stderr.txt').open('w',encoding='utf-8') as stderr:
        p=subprocess.run(list(map(str,command)),cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                         timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    return p.returncode,round(time.perf_counter()-start,3)
K_CASES=[
    {'id':'box','prompt':'a rectangular solid box exactly 40 mm long, 30 mm wide and 8 mm high, centered at the origin. No holes. Output only OpenSCAD code.',
     'bbox_mm':[40,30,8],'volume_mm3':9600},
    {'id':'hole_plate','prompt':'a rectangular plate exactly 40 mm long, 30 mm wide and 8 mm thick, centered at the origin, with one 10 mm diameter cylindrical through-hole along Z at the center. Output only OpenSCAD code.',
     'bbox_mm':[40,30,8],'volume_mm3':40*30*8-3.141592653589793*5**2*8},
    {'id':'spacer','prompt':'a cylindrical spacer exactly 12 mm high, 20 mm outer diameter and one concentric 6 mm diameter through-hole. Cylinder axis Z. Output only OpenSCAD code.',
     'bbox_mm':[20,20,12],'volume_mm3':3.141592653589793*(10**2-3**2)*12},
]
def generate(run,selection):
    records=[]
    if selection in ['all','zero']:
        from render_views import render
        folder=run/'zero'; folder.mkdir(exist_ok=True)
        render(folder/'views')
        views=[str(folder/'views'/f'view_{i}.png') for i in range(8)]
        prompt='Generate CadQuery code for this shape.'
        command=[RUNTIME/'llama-cli.exe','-m',ROOT/'tools/cad-model/Zero-To-CAD-Qwen3-VL-2B.Q6_K.gguf',
                 '--mmproj',ROOT/'tools/cad-model/Zero-To-CAD-Qwen3-VL-2B.mmproj-f16.gguf',
                 '--image',','.join(views),'-sys','You are a CAD code assistant. Given multiple rendered views of a 3D shape, generate clean, well-structured CadQuery Python code that accurately reproduces the geometry.',
                 '-p',prompt,'-c','8192','-n','4096','-ngl','99','-t','6','--temp','0.2','--seed','42','--no-warmup',
                 '--single-turn','--no-display-prompt','--simple-io','--color','off','--jinja']
        print('Running Zero-to-CAD: eight views -> CadQuery',flush=True)
        code,seconds=run_command(command,folder)
        records.append({'model':'zero','folder':str(folder),'exit_code':code,'seconds':seconds,'prompt':prompt})
    if selection in ['all','k']:
        for case in K_CASES:
            folder=run/('k_'+case['id']); folder.mkdir(exist_ok=True)
            prompt='Hey cadmonkey, make me '+case['prompt']
            command=[RUNTIME/'llama-cli.exe','-m',ROOT/'tools/cad-model/k-1b-q8_0.gguf','-p',prompt,
                     '-c','4096','-n','2048','-ngl','99','-t','6','--temp','0','--seed','42',
                     '--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup']
            print('Running K-1B:',case['id'],flush=True)
            code,seconds=run_command(command,folder)
            records.append(dict(case,model='k',folder=str(folder),exit_code=code,seconds=seconds,prompt=prompt))
    save(run/'generations.json',records)
    return records
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--generate-only',action='store_true')
    parser.add_argument('--validate-only',type=Path)
    parser.add_argument('--model',choices=['all','zero','k'],default='all')
    args=parser.parse_args()
    if args.validate_only:
        run=args.validate_only.resolve()
        if not run.is_relative_to(OUT/'simulations'): raise ValueError('Run must be inside outputs/simulations')
    else:
        run=OUT/'simulations'/('models_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4])
        run.mkdir(parents=True)
        generate(run,args.model)
    print('Model raw generation directory:',run,flush=True)
    if args.generate_only: return 0
    import validate_geometry
    return validate_geometry.validate(run)
if __name__=='__main__': raise SystemExit(main())
