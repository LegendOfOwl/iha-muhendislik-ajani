"""Read primary-source model/training metadata; never execute downloaded code."""
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'work/research/k1b_deep'; DEST.mkdir(parents=True,exist_ok=True)
def fetch(name,url):
    try:
        with urlopen(Request(url,headers={'User-Agent':'Engineering-model-research/1.0'}),timeout=45) as r:
            body=r.read(4*1024*1024+1)
        if len(body)>4*1024*1024: raise ValueError('Metadata exceeds size limit')
        (DEST/name).write_bytes(body)
        return json.loads(body)
    except Exception as e:
        print(name,type(e).__name__,str(e),flush=True)
sources={
 'k_tree.json':'https://api.github.com/repos/ThomasVuNguyen/K/git/trees/main?recursive=1',
 'makeme_issues.json':'https://api.github.com/repos/ThomasVuNguyen/MakeMe/issues?state=all&per_page=30',
 'author_models.json':'https://huggingface.co/api/models?author=ThomasTheMaker&limit=100&full=true',
 'k_model.json':'https://huggingface.co/api/models/ThomasTheMaker/k-1b?blobs=true',
 'k_gguf.json':'https://huggingface.co/api/models/ThomasTheMaker/k-1b-gguf?blobs=true',
 'k_tokenizer.json':'https://huggingface.co/ThomasTheMaker/k-1b/resolve/main/tokenizer_config.json',
 'dataset_rows.json':'https://datasets-server.huggingface.co/rows?'+urlencode({'dataset':'ThomasTheMaker/Synthetic-OpenSCAD-16WSL','config':'default','split':'train','offset':0,'length':3}),
}
for name,url in sources.items():
    obj=fetch(name,url)
    if obj is None: continue
    if name=='k_tree.json': print(name,[a['path'] for a in obj['tree'] if a['path'].endswith(('.py','.json','.md'))],flush=True)
    elif name=='makeme_issues.json': print(name,[(a['number'],a['title'],a.get('state')) for a in obj],flush=True)
    elif name=='author_models.json': print(name,[(a['id'],a.get('lastModified')) for a in obj],flush=True)
    elif name=='k_tokenizer.json': print(name,'chat_template=',obj.get('chat_template'),flush=True)
    elif name=='dataset_rows.json': print(name,'features=',obj.get('features'),'sample=',str(obj.get('rows'))[:5000],flush=True)
    else: print(name,'revision',obj.get('sha'),'files',[(a['rfilename'],a.get('size')) for a in obj.get('siblings',[])],flush=True)
