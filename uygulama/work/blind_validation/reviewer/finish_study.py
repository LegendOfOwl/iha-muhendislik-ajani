"""Seal the completed test/review task while keeping failed physical acceptance explicit."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
from datetime import datetime,timezone
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation';OUT=ROOT/'outputs/projects/proje-15cce2de02';R=OUT/'reports'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
timestamp=datetime.now(timezone.utc).isoformat();q=read(R/'review_v2_qualification.json');seal=read(BASE/'pre_analysis_seal.json')
assert sha(BASE/'contract.json')==seal['contract_sha256']
assert all(sha(BASE/'analysis_input'/n)==h for n,h in seal['input_sha256'].items())
v1=read(R/'prediction_frozen.json');v1files={**v1['case_files_sha256'],**v1['source_script_sha256']};assert all(sha(ROOT/p)==h for p,h in v1files.items())
integrity=read(R/'review_v2_integrity.json');assert integrity['all_unchanged']
assert all(row['all_checked_inputs_match_contract'] and not row['differences_from_v1_baseline'] for row in read(R/'review_physical_config_audit.json')['cases'])
assert not q['minimum_qualification_passed'] and q['critical_regional_mesh_issue_open'] and not q['farfield_sensitivity']['evaluated']
assert all(c['original_table_corrected_reference']['all']['points']==103 for c in q['case_results'] if c.get('surface_file'))
assert q['numerical_results']['fine']['values']['field_iteration']==3400
uav={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'outputs/data/project').glob('*.json')};matches=[]
for p in (ROOT/'outputs/data/tasks').glob('*.json'):
 t=read(p);hs={k.replace('\\','/'):v for k,v in t.get('input_sha256',{}).items()}
 if all(hs.get(k)==h for k,h in uav.items()):matches.append(p.name)
class Links(HTMLParser):
 def __init__(self,base):super().__init__();self.base=base;self.local=[];self.missing=[]
 def handle_starttag(self,t,attrs):
  for k,v in attrs:
   if k not in ('href','src') or not v or urlparse(v).scheme or v.startswith('#'):continue
   p=(self.base/unquote(v.split('#')[0])).resolve();self.local.append(str(p))
   if not p.exists():self.missing.append(str(p))
reports={}
for p in [R/'blind_cfd_validation.html',ROOT/'outputs/reports/kaynak_geometri_ve_kor_cfd.html',ROOT/'outputs/Proje-Ozeti.html']:
 parser=Links(p.parent);parser.feed(p.read_text(encoding='utf-8'));reports[str(p.relative_to(ROOT))]={'local_references':len(parser.local),'missing':parser.missing};assert not parser.missing
raw=['cp.exp.gen','cfpost.cp.com','cp.wind.gen','forces.lis','case.html','study4.html'];assert all(sha(BASE/'reviewer_only'/n)==sha(OUT/'data/reference'/n) for n in raw)
quality={'timestamp':timestamp,'scope':'Completed source-geometry agent benchmark execution, failure diagnosis and independent review; failed physical qualification is not completion of a general CFD service','test_and_review_work_completed':True,'minimum_physical_qualification_passed':False,'v1_frozen_case_and_script_hashes_unchanged':len(v1files),'v2_verified_hash_records':integrity['verified_file_hash_records'],'v2_prediction_unchanged':True,'initial_inputs_and_contract_unchanged':True,'all103_experimental_points_retained':True,'raw_NASA_reference_preserved':True,'original_published_reference_sign_correction_documented':True,'all_checked_physics_consistent':True,'missing_freeze_negative_control':read(R/'review_workflow_checks.json'),'report_links':reports,'actual_UAV_current_hashes':uav,'actual_UAV_matching_prior_task_snapshots':matches,'actual_UAV_inputs_unchanged_from_matching_snapshot':bool(matches),'fine_Cp_RMSE_original_table':q['case_results'][2]['original_table_corrected_reference']['all']['RMSE'],'fine_Cp_RMSE_limit':.03,'farfield_400c_solution_available':False,'GCI_reported':False,'next_step':'Source-preserving aft normal C-grid/block and controlled TE/wake transition; not yet built or qualified','limitations':['No security/memorization-proof blinding','No general3D/UAV qualification','Fully turbulent model does not resolve experimental trip','No verified fine normal-layer family and farfield acceptance','3D M6/VLM/RANS previous open gates remain open']}
save(ROOT/'outputs/reports/source_geometry_validation_quality.json',quality)
info=read(BASE/'project.json');taskpath=ROOT/info['task'];task=read(taskpath);task.update(status='tamamlandı',finished_utc=timestamp,completion_scope='Test çalıştırma, başarısızlık teşhisi ve bağımsız rapor tamamlandı; asgari fiziksel yeterlilik sağlanmadı',physical_minimum_qualification_passed=False,benchmark_version_status={'v1':'frozen_and_reviewed_failed','v2':'frozen_and_reviewed_failed'},blocked_by=[],open_quality_gates=['aft normal mesh/BL sensitivity','400c farfield solution not run under numerical mesh hold','experimental Cp error'],evidence=['outputs/reports/kaynak_geometri_ve_kor_cfd.html','outputs/reports/source_geometry_validation_quality.json','outputs/projects/proje-15cce2de02/reports/prediction_frozen.json','outputs/projects/proje-15cce2de02/reports/prediction_v2_frozen.json','outputs/projects/proje-15cce2de02/reports/review_v2_qualification.json','outputs/projects/proje-15cce2de02/reports/review_reference_source_audit.json'])
archive=ROOT/'outputs/reports/task_evidence'/task['id'];archive.mkdir(parents=True,exist_ok=True);records=[]
for p in sorted(R.glob('*.json'))+[R/'blind_cfd_validation.html',ROOT/'outputs/reports/source_geometry_validation_quality.json']:
 target=archive/p.name;shutil.copy2(p,target);records.append({'original_path':str(p.relative_to(ROOT)).replace('\\','/'),'archive':str(target.relative_to(ROOT)).replace('\\','/'),'sha256':sha(target)})
save(archive/'manifest.json',{'timestamp':timestamp,'scope':'Immutable report copies; raw fields remain at the paths and SHA values in the frozen prediction manifests. Archived HTML stores original bytes; use live report for relative-link navigation.','files':records})
task['evidence_manifest']=str((archive/'manifest.json').relative_to(ROOT)).replace('\\','/');task['evidence_manifest_sha256']=sha(archive/'manifest.json');save(taskpath,task)
print(json.dumps({'reported':True,'physical_minimum_qualification_passed':False,'links':reports,'UAV_matching_snapshots':matches,'archived_reports':len(records)},ensure_ascii=False,indent=2))
