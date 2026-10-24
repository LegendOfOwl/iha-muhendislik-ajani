"""Inventory primary-source snapshots and verify prior project evidence hashes."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'work/research/k1b_deep'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
tree=read(DEST/'k_tree.json')
sources=[]
for a in tree['tree']:
    p=DEST/a['path'].replace('/','__')
    if a['type']=='blob' and p.exists():
        data=p.read_bytes(); git_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        sources.append({'local_path':str(p.relative_to(ROOT)),'sha256':sha(p),
          'source_url':'https://github.com/ThomasVuNguyen/K/blob/'+tree['sha']+'/'+a['path'],
          'github_blob_sha':a['sha'],'matches_github_tree_blob':git_sha==a['sha']})
for name,repo in [('k_model.json','k-1b'),('k_gguf.json','k-1b-gguf'),('cadmonkey32_base.json','cadmonkey-1b-data-32'),('cadmonkey32.json','cadmonkey-1b-data-32-gguf'),('cadmonkey16.json','cadmonkey-1b-data-16-gguf')]:
    p=DEST/name; meta=read(p)
    sources.append({'local_path':str(p.relative_to(ROOT)),'sha256':sha(p),'source_url':'https://huggingface.co/ThomasTheMaker/'+repo+'/tree/'+meta['sha'],
       'model_revision':meta['sha'],'last_modified':meta['lastModified']})
for name,url in [('cadmonkey_models.json','https://huggingface.co/api/models?author=ThomasTheMaker&search=cadmonkey&limit=100&full=true'),
   ('dataset_rows.json','https://huggingface.co/datasets/ThomasTheMaker/Synthetic-OpenSCAD-16WSL'),
   ('k_chat_template.jinja','https://huggingface.co/ThomasTheMaker/k-1b/blob/dec2e81164e7f01b30d475d6b27fd931f423cf5a/chat_template.jinja'),
   ('makeme_issues.json','https://github.com/ThomasVuNguyen/MakeMe/issues?q=is%3Aissue')]:
    sources.append({'local_path':str((DEST/name).relative_to(ROOT)),'sha256':sha(DEST/name),'source_url':url})
sources.append({'local_path':'work/research/makeme_main.txt','sha256':sha(ROOT/'work/research/makeme_main.txt'),'source_url':'https://github.com/ThomasVuNguyen/MakeMe/blob/main/main.go'})
old=read(ROOT/'outputs/reports/verification_summary.json')
checks=[]
for name,entry in old['evidence'].items():
    p=Path(entry['path']); checks.append({'report':name,'exists':p.exists(),'sha256':sha(p) if p.exists() else None,'matches_prior_record':p.exists() and sha(p)==entry['sha256']})
k=read(DEST/'k_gguf_metadata.json'); new=read(DEST/'cadmonkey32_gguf_metadata.json')
template=(DEST/'k_chat_template.jinja').read_text().strip()
obj={'timestamp':datetime.now(timezone.utc).isoformat(),'sources':sources,'prior_project_evidence':checks,
    'prior_evidence_hashes_match':all(c['matches_prior_record'] for c in checks),
    'github_source_snapshots_match_tree':all(s['matches_github_tree_blob'] for s in sources if 'matches_github_tree_blob' in s),
    'k_chat_template_matches_upstream':k['tokenizer.chat_template'].strip()==template,
    'new_and_old_chat_templates_equal':k['tokenizer.chat_template'].strip()==new['tokenizer.chat_template'].strip(),
    'note':'Source code read as text only. Prior physical solver results audited, not rerun for this research report.'}
(ROOT/'outputs/reports/research_evidence.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in obj.items() if k not in ['sources','prior_project_evidence']},ensure_ascii=False,indent=2))
