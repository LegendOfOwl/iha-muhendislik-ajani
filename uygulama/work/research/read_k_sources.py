import json
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'work/research/k1b_deep'
paths=['train/train.py','train/config.json','train/eval.py','train/evaluate.py','train/export-gguf.py',
       'train/evaluation/ThomasTheMaker_k-1b_20251125_203139/evaluation_results.json',
       'train/evaluation/ThomasTheMaker_k-1b_20251125_204735/evaluation_results.json','data/v6/filter.py']
urls={p.replace('/','__'):'https://raw.githubusercontent.com/ThomasVuNguyen/K/main/'+p for p in paths}
urls.update({'k_chat_template.jinja':'https://huggingface.co/ThomasTheMaker/k-1b/resolve/dec2e81164e7f01b30d475d6b27fd931f423cf5a/chat_template.jinja',
             'related_models.json':'https://huggingface.co/api/models?author=ThomasTheMaker&search=k-&limit=100&full=true'})
for name,url in urls.items():
    try:
        data=urlopen(Request(url,headers={'User-Agent':'Engineering-research/1.0'}),timeout=45).read(2**20)
        (DEST/name).write_bytes(data)
        print(name,len(data),'bytes',flush=True)
    except Exception as e: print(name,type(e).__name__,str(e),flush=True)
