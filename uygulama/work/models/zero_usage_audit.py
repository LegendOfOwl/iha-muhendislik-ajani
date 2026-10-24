"""Check greedy inference on original dataset views as well as local synthetic views."""
from datetime import datetime,timezone
import ast
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from benchmark import run_command
from validate_geometry import response
ROOT=Path(__file__).resolve().parents[2]
def save(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    run=ROOT/'outputs/simulations'/('zero_usage_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    row=json.loads((ROOT/'work/research/zero_usage/test_row.json').read_text())['rows'][0]['row']
    source=run/'dataset_views'; source.mkdir()
    for i in range(8):
        raw=base64.b64decode(row[f'image_{i}'],validate=True)
        assert raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(256,256)
        (source/f'view_{i}.png').write_bytes(raw)
    (source/'reference.stl').write_bytes(base64.b64decode(row['stl_file'],validate=True))
    (source/'reference.step').write_bytes(base64.b64decode(row['step_file'],validate=True))
    (source/'reference_code_NOT_EXECUTED.txt').write_bytes(base64.b64decode(row['cadquery_file'],validate=True))
    local=ROOT/'outputs/simulations/models_20261018_173055_d8b8/zero/views'
    assert all((local/f'view_{i}.png').exists() for i in range(8))
    protocol={'started_utc':datetime.now(timezone.utc).isoformat(),'dataset_uuid':row['uuid'],
      'dataset_split':'test','dataset_offset':0,'source':'https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m',
      'image_size_px':[256,256],'image_order':'image_0 to image_7 unchanged',
      'system_prompt':'You are a CAD code assistant. Given multiple rendered views of a 3D shape, generate clean, well-structured CadQuery Python code that accurately reproduces the geometry.',
      'user_prompt':'Generate CadQuery code for this shape.','max_new_tokens':4096,'context':8192,
      'sampling':'greedy: temperature=0; no penalties; extra sampling filters disabled',
      'weights':'Previously installed third-party Q6_K + f16 mmproj; not original BF16 Transformers path',
      'reference_program_executed':False,'script_sha256':sha(__file__),
      'source_row_sha256':sha(ROOT/'work/research/zero_usage/test_row.json'),
      'input_view_sha256':{f'view_{i}.png':sha(source/f'view_{i}.png') for i in range(8)}}
    save(run/'protocol.json',protocol); results=[]
    for label,views in [('original_dataset',source),('local_synthetic',local)]:
        folder=run/label; folder.mkdir()
        command=[ROOT/'tools/llama-cad/llama-cli.exe','-m',ROOT/'tools/cad-model/Zero-To-CAD-Qwen3-VL-2B.Q6_K.gguf','--mmproj',ROOT/'tools/cad-model/Zero-To-CAD-Qwen3-VL-2B.mmproj-f16.gguf',
          '--image',','.join(str(views/f'view_{i}.png') for i in range(8)),'-sys',protocol['system_prompt'],'-p',protocol['user_prompt'],'-c','8192','-n','4096','-ngl','99','-t','6',
          '--temp','0','--samplers','temperature','--top-k','0','--top-p','1','--min-p','0','--repeat-penalty','1','--seed','42',
          '--no-warmup','--single-turn','--simple-io','--no-display-prompt','--color','off','--jinja','--log-verbosity','3']
        result={'input':label,'folder':str(folder)}
        try:
            code,seconds=run_command(command,folder); result.update(inference_exit_code=code,seconds=seconds)
            generated=response((folder/'stdout.txt').read_text(encoding='utf-8',errors='replace'))
            (folder/'generated.py').write_text(generated,encoding='utf-8')
            # Inspect the generated program before a separate restricted CAD worker evaluates it.
            ast.parse(generated); result['python_syntax_valid']=True
            from cad_worker import checked_tree
            checked_tree(generated); result['worker_supported_program']=True
            with (folder/'cad_worker.log').open('w',encoding='utf-8') as log:
                proc=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'work/models/cad_worker.py'),str(folder)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
            result['cad_worker_exit_code']=proc.returncode
            result['valid_solid']=proc.returncode==0 and (folder/'cad_metrics.json').exists()
            if result['valid_solid']: result['cad_metrics']=json.loads((folder/'cad_metrics.json').read_text())
            result['geometry_accepted']=False; result['acceptance_note']='Valid execution does not establish shape similarity; no complete vendor IoU benchmark reproduced.'
        except Exception as e: result.update(valid_solid=False,geometry_accepted=False,error=f'{type(e).__name__}: {e}')
        results.append(result); save(run/'results_in_progress.json',results); print(label,json.dumps(result),flush=True)
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'results':results,'protocol':protocol,'run_directory':str(run),
      'passed':all(r.get('inference_exit_code')==0 for r in results),'quality_passed':all(r.get('geometry_accepted') for r in results)}
    save(run/'audit_results.json',obj); save(ROOT/'outputs/reports/zero_usage_audit.json',obj)
    return 0 if obj['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
