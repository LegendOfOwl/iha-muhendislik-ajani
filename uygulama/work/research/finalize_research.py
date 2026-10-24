"""Update persistent model inventory and attach usage-audit/source evidence."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]; REPORTS=ROOT/'outputs/reports'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
study=read(REPORTS/'k_family_study.json'); new=read(REPORTS/'k_family_new_tasks.json'); audit=read(REPORTS/'model_usage_audit.json')
audit['quality_passed']=all(r.get('geometry_accepted',False) for r in audit['results'] if r['group']!='upstream_demo')
write(REPORTS/'model_usage_audit.json',audit)
model=read(ROOT/'work/setup/cadmonkey32_install.json')
model.update(new_tasks_summary=next(r for r in new['summary'] if r['model']=='cadmonkey32'),
   usage_audit_summary=[r for r in audit['summary'] if r['model']=='cadmonkey32'],
   engineering_auto_use=False,known_failures=['Offset hole position','Two-hole axis/placement','Unrequested cuts with some prompt variants'],
   use_policy='Experimental text-to-OpenSCAD draft helper; verify each generated shape and engineering assumptions independently',
   reports=['outputs/reports/k_family_study.json','outputs/reports/k_family_new_tasks.json','outputs/reports/model_usage_audit.json'])
write(ROOT/'work/setup/cadmonkey32_install.json',model)
cfg=read(ROOT/'work/setup/tool_config.json'); cfg['cadmonkey32']=model
cfg['preferred_experimental_text_cad_model']='cadmonkey32'; cfg['model_auto_engineering_acceptance']=False
cfg['latest_research_report']='outputs/reports/proje_durum_ve_k1b_arastirma.html'; cfg['last_model_usage_audit_utc']=datetime.now(timezone.utc).isoformat()
write(ROOT/'work/setup/tool_config.json',cfg)
evidence=read(REPORTS/'research_evidence.json')
for name,url in [('model_readme.md','https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B/blob/8cf9260904aa6eb29f0826e3585f25b7df61ff89/README.md'),
    ('generation_config.json','https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B/blob/8cf9260904aa6eb29f0826e3585f25b7df61ff89/generation_config.json'),
    ('test_row.json','https://datasets-server.huggingface.co/rows?dataset=ADSKAILab%2FZero-To-CAD-1m&config=default&split=test&offset=0&length=1')]:
    p=ROOT/'work/research/zero_usage'/name
    if not any(s['local_path']==str(p.relative_to(ROOT)) for s in evidence['sources']): evidence['sources'].append({'local_path':str(p.relative_to(ROOT)),'source_url':url,'sha256':sha(p)})
gg=read(ROOT/'work/research/zero_usage/gguf_metadata.json')
source=read(ROOT/'work/research/zero_model.json')['config']['processor_config']['chat_template']
evidence['zero_chat_template_matches_upstream_metadata']=gg['tokenizer.chat_template'].strip()==source.strip()
evidence['explicit_template_runtime_parity']=audit['external_template_outputs_match']
evidence['official_resolution_acceptance_changes']=len(audit['resolution_changed_acceptance'])
evidence['audit_reports']={str(p.relative_to(ROOT)):{'sha256':sha(p)} for p in [REPORTS/n for n in ['k_family_study.json','k_family_new_tasks.json','model_usage_audit.json','cat_budget_audit.json','zero_usage_audit.json']]}
evidence['finalized_utc']=datetime.now(timezone.utc).isoformat(); write(REPORTS/'research_evidence.json',evidence)
print('Inventory and source/usage evidence updated; geometry acceptance remains conditional.')
