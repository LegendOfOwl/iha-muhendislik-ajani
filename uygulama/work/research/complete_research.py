"""Verify deliverable links and seal a task-specific copy of the research evidence."""
from datetime import datetime,timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'; REPORTS=OUT/'reports'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links += [v for k,v in attrs if k in {'href','src'}]
checks=[]
for p in [REPORTS/'proje_durum_ve_k1b_arastirma.html',OUT/'Proje-Ozeti.html']:
    parser=Links(); parser.feed(p.read_text(encoding='utf-8'))
    local=[urlsplit(s) for s in parser.links if not urlsplit(s).scheme]
    missing=[s.path for s in local if s.path and not (p.parent/unquote(s.path)).exists()]
    checks.append({'file':str(p.relative_to(ROOT)),'local_links':len(local),'missing':missing,'passed':not missing})
    assert not missing,missing
evidence=read(REPORTS/'research_evidence.json')
assert evidence['prior_evidence_hashes_match'] and evidence['github_source_snapshots_match_tree'] and evidence['explicit_template_runtime_parity']
assert evidence['official_resolution_acceptance_changes']==0
for report in ['k_family_study.json','k_family_new_tasks.json','model_usage_audit.json','zero_usage_audit.json']:
    obj=read(REPORTS/report); assert obj['passed']
    assert Path(obj['run_directory']).exists()
health=read(REPORTS/'tool_health.json'); assert health['all_paths_present']
mission=read(OUT/'data/project/mission.json'); steps=read(OUT/'data/project/conceptual_steps.json')
assert all(v['value'] is None for v in mission['inputs'].values())
assert len(steps)==8 and all(s['status']=='bekliyor' for s in steps)
quality={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':True,'html_link_checks':checks,
   'prior_solver_evidence_hashes_match':True,'template_output_parity':True,'official_resolution_changed_acceptance':0,
   'new_model_comparison_runtime_completed':True,'all_model_outputs_correct':False,
   'real_aircraft_conceptual_steps_completed':0,'physical_solvers_rerun_for_this_report':False,
   'source_compile_check':'outputs/reports/ui_check.json','plot_visually_inspected':'outputs/plots/k_family_comparison.png'}
write(REPORTS/'research_quality_check.json',quality)
task_path=OUT/'data/tasks/20261018-203719-a2da02.json'; task=read(task_path)
task['status']='tamamlandı'; task['completed_utc']=datetime.now(timezone.utc).isoformat()
task['acceptance_results']=[
 {'criterion':'Birincil kaynak ve yeni sürüm araştırması','passed':True,'evidence':'outputs/reports/research_evidence.json'},
 {'criterion':'Aynı geometri ölçütleriyle eski/yeni sürüm karşılaştırması','passed':True,'evidence':'outputs/reports/k_family_study.json'},
 {'criterion':'İstem/şablon/örnekleme/çözünürlük ve özgün Zero görüntüsüyle kullanım denetimi','passed':True,'evidence':'outputs/reports/model_usage_audit.json'},
 {'criterion':'Yapılan iş, kullanılabilir yetenek ve sınırları tek raporda sun','passed':True,'evidence':'outputs/reports/proje_durum_ve_k1b_arastirma.html'}]
task['scope_limits']=['Real UAV design inputs remain unknown and all conceptual steps pending',
 'Original BF16/Transformers/Unsloth model paths not reproduced','ANSYS deferred','Small model outputs not automatically accepted for engineering']
folder=REPORTS/'task_evidence'/task['id']; folder.mkdir(parents=True,exist_ok=True)
paths=[REPORTS/n for n in ['proje_durum_ve_k1b_arastirma.md','proje_durum_ve_k1b_arastirma.html','k_family_study.json','k_family_new_tasks.json','model_usage_audit.json','zero_usage_audit.json','cat_budget_audit.json','research_evidence.json','research_quality_check.json','tool_health.json','ui_check.json']]
paths.append(ROOT/'work/setup/cadmonkey32_install.json')
task['evidence']=[]
for p in paths:
    dst=folder/p.name
    if dst.exists() and sha(dst)!=sha(p): raise ValueError('Refusing to overwrite sealed evidence '+str(dst))
    if not dst.exists(): shutil.copyfile(p,dst)
    task['evidence'].append({'path':str(dst.relative_to(ROOT)),'sha256':sha(dst),'live_path':str(p.relative_to(ROOT))})
task['report']='outputs/reports/proje_durum_ve_k1b_arastirma.html'; write(task_path,task)
print(json.dumps(quality,ensure_ascii=False,indent=2)); print('Task sealed:',task['id'])
