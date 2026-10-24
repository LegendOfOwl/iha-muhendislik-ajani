"""Close the bounded RAE tests without declaring physical qualification."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02';REP=OUT/'reports'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    closed=REP/'v3_test_batch_closed.json';assert not closed.exists(),'Preserve the closed batch'
    frozen=REP/'v3_firstorder_control_prediction_frozen.json';assert not frozen.exists()
    names=['v3_r4roe_coarse_firstorder_control','v3_r4roe_firstorder_cont4200'];files={};metrics={}
    for n in names:
        d=OUT/'simulations'/n;assert (d/'run_status.json').exists() and (d/'prediction_metrics.json').exists()
        metrics[n]=json.loads((d/'prediction_metrics.json').read_text())
        for p in d.rglob('*'):
            if p.is_file():files[str(p.relative_to(ROOT))]=sha(p)
    freeze={'frozen_utc':datetime.now(timezone.utc).isoformat(),'cases':names,'files_sha256':files,
            'source_script_sha256':{str(Path(__file__).relative_to(ROOT)):sha(__file__)},
            'contract_sha256':sha(ROOT/'work/blind_validation/contract.json'),
            'scope':'First-order numerical diagnostics only; no experimental candidate selection; not fine validation',
            'experimental_score_computed':False,'minimum_physical_qualification_passed':False}
    frozen.write_text(json.dumps(freeze,indent=2))
    assert all(sha(ROOT/p)==h for p,h in files.items())
    for script in ['build_report.py','verify_evidence.py']:
        r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'work/mesh_research'/script)],cwd=ROOT,capture_output=True,text=True)
        assert r.returncode==0,(script,r.stderr)
    integrity=json.loads((REP/'v3_evidence_integrity.json').read_text());assert integrity['evidence_checks_passed']
    summary=json.loads((REP/'v3_research_summary.json').read_text())
    record={'closed_utc':datetime.now(timezone.utc).isoformat(),'bounded_test_and_review_completed':True,
            'task_id':'20261019-201609-ab8031','native_attempts_with_result_records':len(summary['completed_native_cases']),
            'firstorder_diagnostics':{n:{k:a[k] for k in ['field_checkpoint_iteration','density_log10_residual','CL_final200_range','CD_final200_range','max_wall_yplus','checks']} for n,a in metrics.items()},
            'minimum_physical_qualification_passed':False,'open_gates':summary['required_missing'],
            'evidence_integrity_sha256':sha(REP/'v3_evidence_integrity.json'),
            'report':summary['report'],'report_sha256':sha(REP/'v3_research_diagnosis.html'),
            'next_authorized_step':'New ONERA M6 3D native RANS test, as requested on2026-10-24',
            'no_claim':'Not a successful general CFD service, validated RAE airfoil or flightworthy aircraft'}
    closed.write_text(json.dumps(record,indent=2))
    task=ROOT/'outputs/data/tasks/20261019-201609-ab8031.json';t=json.loads(task.read_text())
    t.update(status='tamamlandı',completed_utc=record['closed_utc'],completion_scope='Sınırlı kaynak araştırması, gerçek denemeler ve başarısızlık dahil raporlama tamamlandı; fiziksel yeterlilik geçmedi',minimum_physical_qualification_passed=False,
             engineering_work_remaining=summary['required_missing'])
    t['evidence']=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [closed,REP/'v3_research_diagnosis.html',REP/'v3_evidence_integrity.json',frozen]]
    task.write_text(json.dumps(t,indent=2,ensure_ascii=False));print(json.dumps(record,indent=2))
if __name__=='__main__':main()
