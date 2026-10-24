"""Read upstream Zero-to-CAD inference configuration and a single dataset example."""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[2]
dest=ROOT/'work/research/zero_usage'; dest.mkdir(exist_ok=True)
urls={
  'generation_config.json':'https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B/resolve/8cf9260904aa6eb29f0826e3585f25b7df61ff89/generation_config.json',
  'model_readme.md':'https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B/resolve/8cf9260904aa6eb29f0826e3585f25b7df61ff89/README.md',
  'test_row.json':'https://datasets-server.huggingface.co/rows?'+urlencode({'dataset':'ADSKAILab/Zero-To-CAD-1m','config':'default','split':'test','offset':0,'length':1}),
}
for name,url in urls.items():
    try:
        body=urlopen(Request(url,headers={'User-Agent':'Engineering-usage-audit/1.0'}),timeout=60).read(16*1024*1024+1)
        if len(body)>16*1024*1024: raise ValueError('Response exceeds 16 MiB cap')
        (dest/name).write_bytes(body)
        if name=='test_row.json':
            row=json.loads(body)['rows'][0]['row']; print({key:{'type':type(v).__name__,'preview':str(v)[:150]} for key,v in row.items()})
        else: print(name,len(body),body.decode() if name.endswith('.json') else 'saved')
    except Exception as e: print(name,type(e).__name__,str(e))
