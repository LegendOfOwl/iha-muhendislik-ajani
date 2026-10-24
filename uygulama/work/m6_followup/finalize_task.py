"""Record completed requested tests while keeping physical qualification false."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-e9319baef1';REP=OUT/'reports'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    integrity=REP/'m6_followup_integrity_20261024.json';a=read(integrity)
    reference=REP/'m6_reference_recheck_20261024.json';r=read(reference);assert r['matches_preserved_original_bytes']
    assert sha(ROOT/'work/validation/sources/ONERAb114.tec')==r['sha256']
    a['fresh_Tecplot_reference']={'record':str(reference.relative_to(ROOT)),'record_sha256':sha(reference),'original_matches_fresh_NASA_bytes':True,'sha256':r['sha256']}
    s=importlib.util.spec_from_file_location('link_check_only',ROOT/'work/m6_followup/verify_evidence.py');mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod)
    a['report_links']=[mod.links(REP/'m6_24_ekim.html'),mod.links(ROOT/'outputs/reports/onera_m6_24_ekim.html')]
    assert all(not x['missing'] for x in a['report_links']) and a['evidence_checks_passed']
    a['final_verified_utc']=datetime.now(timezone.utc).isoformat();integrity.write_text(json.dumps(a,indent=2))
    reports=[REP/'m6_24_ekim.html',integrity,REP/'m6_jst_control_results_20261024_v2.json',REP/'m6_wallnormal_results_20261024_v3.json',
        REP/'m6_jst_prediction_frozen_20261024_v2.json',REP/'m6_wallnormal_prediction_frozen_20261024_v3.json',
        REP/'m6_jst_force_integral_20261024_v2.json',REP/'m6_wallnormal_force_integral_20261024_v3.json',reference,
        REP/'m6_field_view_main_20261024_v2.json',REP/'m6_field_view_normal_20261024_v2.json']
    task=ROOT/'outputs/data/tasks/20261024-153804-27f425.json';t=read(task)
    t.update(status='tamamlandı',phase='araç doğrulama',completed_utc=a['final_verified_utc'],
        completion_scope='RAE testlerinin kapanışından sonra istenen iki3B M6 testini çalıştırma, kaynak deneyle kıyas ve raporlama tamamlandı; genel fizik kabulü geçmedi',
        minimum_physical_qualification_passed=False,
        engineering_work_remaining=['density residual below-7','all14 section/side experimental Cp gates','systematic same-geometry mesh family','full boundary-layer profiles/normal sensitivity','farfield sensitivity'],
        evidence=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in reports])
    t['reproduction_code_sha256']={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'work/m6_followup').glob('*.py')}
    task.write_text(json.dumps(t,indent=2,ensure_ascii=False))
    normal=read(REP/'m6_wallnormal_results_20261024_v3.json')
    print(json.dumps({'task':str(task.relative_to(ROOT)),'tests_and_report_completed':True,'minimum_physical_qualification':False,
        'native_runs':2,'points_per_run':normal['experiment_points'],'normal_yplus':normal['Cp']['yplus_max'],
        'normal_Cp_RMSE':normal['Cp']['all_point_Cp_RMSE'],'normal_section_side_passes':sum(normal['experimental_checks'].values()),
        'evidence_files':len(reports),'integrity':True},indent=2))
if __name__=='__main__':main()
