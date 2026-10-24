from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3];REP=ROOT/'outputs/projects/proje-15cce2de02/reports'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=REP/'prediction_v2_frozen.json';d=json.loads(p.read_text());mismatches=[];checked=0
for section in ['input_sha256','source_script_sha256','case_files_sha256','prediction_report_sha256','work_log_sha256']:
    for path,wanted in d[section].items():
        target=ROOT/path;checked+=1
        if not target.is_file() or sha(target)!=wanted:mismatches.append({'section':section,'path':path,'reason':'missing or SHA256 mismatch'})
for case in d['selected_case_manifest']['main_cases']:
    iterations=[int(re.search(r'_(\d+)\.',case[k]).group(1)) for k in ['surface','volume','restart']]
    if len(set(iterations))!=1 or iterations[0]!=case['field_checkpoint_iteration']:mismatches.append({'case':case['case_name'],'reason':'checkpoint suffix mismatch'})
report={'frozen_file_sha256':sha(p),'files_checked':checked,'mismatches':mismatches,'all_frozen_files_unchanged':not mismatches,'note':'Integrity verification only; does not turn a numerical or physical failure into acceptance.'}
(REP/'prediction_v2_freeze_integrity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if mismatches:raise SystemExit(1)
