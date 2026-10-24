import json
from pathlib import Path
from urllib.request import Request,urlopen
DEST=Path(__file__).resolve().parent/'k1b_deep'
urls={
 'cadmonkey_models.json':'https://huggingface.co/api/models?author=ThomasTheMaker&search=cadmonkey&limit=100&full=true',
 'cadmonkey32.json':'https://huggingface.co/api/models/ThomasTheMaker/cadmonkey-1b-data-32-gguf?blobs=true',
 'cadmonkey32_base.json':'https://huggingface.co/api/models/ThomasTheMaker/cadmonkey-1b-data-32?blobs=true',
 'cadmonkey16.json':'https://huggingface.co/api/models/ThomasTheMaker/cadmonkey-1b-data-16-gguf?blobs=true',
}
for name,url in urls.items():
    data=urlopen(Request(url,headers={'User-Agent':'Engineering-research/1.0'}),timeout=45).read()
    (DEST/name).write_bytes(data); obj=json.loads(data)
    if isinstance(obj,list): print([(x['id'],x.get('lastModified')) for x in obj],flush=True)
    else: print(name,obj.get('sha'),obj.get('lastModified'),obj.get('cardData'),[(a['rfilename'],a.get('size')) for a in obj.get('siblings',[])],flush=True)
