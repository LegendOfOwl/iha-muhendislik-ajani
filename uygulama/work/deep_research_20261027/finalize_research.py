"""Close the research deliverable; keep every engineering issue open."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
STEM='acik_sorunlar_ve_derin_arastirma_20261028'


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def main():
    now=datetime.now(timezone.utc).isoformat()
    r=read(ROOT/'outputs/reports'/f'{STEM}.json')
    q=read(ROOT/'outputs/reports/deep_research_checks_20261028.json')
    assert q['passed'] is True and r['issue_count']==26 and r['new_native_CFD_runs']==r['new_builds']==0
    for name,h in q['report_files_sha256'].items():assert sha(ROOT/name)==h
    for name,entry in r['evidence_integrity']['mutable_baseline_snapshots'].items():
        assert sha(ROOT/entry['path'])==entry['sha256']==r['evidence_integrity']['files_sha256'][name]
    taskpath=ROOT/'outputs/data/tasks/20261027-221814-12f67c.json'
    task=read(taskpath)
    for name,h in task['input_sha256'].items():assert sha(ROOT/name)==h
    for name in ('outputs/data/project/mission.json','outputs/data/project/mass_budget.json','outputs/data/project/conceptual_steps.json'):
        assert sha(ROOT/name)==r['evidence_integrity']['files_sha256'][name]
    assert task['project_id']=='qualification'
    evidence=[]
    for path in [ROOT/'outputs/reports'/(STEM+ext) for ext in ('.json','.md','.html')]+[ROOT/'outputs/reports/deep_research_checks_20261028.json']:
        evidence.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
    for name,entry in r['specialist_modules'].items():
        assert sha(BASE/name)==entry['sha256']
        evidence.append({'path':(BASE/name).relative_to(ROOT).as_posix(),'sha256':entry['sha256']})
    task.update(status='tamamlandı',phase='araştırma/öncelik raporu tamamlandı; önerilen uygulamalar çalıştırılmadı',
        finished_utc=now,evidence=evidence,blocked_by=[],
        completion_scope='Inventory and source-backed deep research only; all26 engineering issues remain open',
        issue_count=26,source_addresses=39,priority_counts=r['priority_counts'],
        new_native_CFD_runs=0,new_builds=0,new_installations=0,
        physical_qualification_passed=False,M6_qualification_passed=False,LLM_improvement_demonstrated=False,
        next_required_step='Preregister passive true inner-linear residual measurement; prepare independent geometry/wall-distance audit in parallel')
    save(taskpath,task)
    statepath=ROOT/'PROJECT_STATE.md';state=statepath.read_text(encoding='utf-8')
    marker='## 28 Ekim: açık sorunlar ve derin araştırma'
    assert marker not in state
    state+='\n\n'+marker+'\n\n'
    state+=('- Görev20261027-221814-12f67c yalnız kaynaklı araştırma/öncelik çıktısı olarak kapandı;26mühendislik başlığı açık kalır. '
        '29alt bulgu26başlıkta birleştirildi:7P0/12P1/6P2/1P3.39farklıbirincilkaynak adresi,61hash kaydı/50benzersizyereldosya denetlendi. '
        'Ana rapor outputs/reports/acik_sorunlar_ve_derin_arastirma_20261028.html; yapılandırılmış JSON aynı adla. '
        'Sayısal/mesh/CAD-ajan alt araştırmaları work/deep_research_20261027 altında;klasör tarihi görev başlangıcıdır.\n'
        '- İlk iş U01: assembledFGMRES gerçek b−Aδ ölçümü; küçükmatris/sıfırRHS/pasiflik kontrolü ve değişmeyen kaynak32 yeniden üretimi olmadan native teşhis iddiası yok. '
        'Aynı ilk durum/A,b ve uygulananΔU ayrımı gerekir. U19 kaynak geometri/marker’a bağlı bağımsız wall-distance audit paralel düşükmaliyetli aday;yerelde hata kanıtlanmadı. '
        'SU2gerçekkaynak zaten CGS2 kullanıyor; ikinciortogonalleştirme kopyası önerilmedi. Önbellekliraw görünümü ile yerelkaynak uyuşmazlığı pinnedGitHubcontentsAPI ile çözüldü.\n'
        '- EnyeniM6,25EkimTMRsharp kaynakaile:üçağ zatenüretildi ama üçü de iteratif kabulü geçmedi. Eski blunt/y+iyileşmesi buna taşınmaz. '
        'RAEv3 ve düzplakafine kabulleri açık;GCI null. Kaynak geometri/deney/türbülans/BC/viskozite, regionalmesh, uzakalan ve belirsizlik ayrıca kapanmalı.\n'
        '- GerçekİHA7girdi/6bileşenkütlesi ve8kavramsaladım bekliyor;benchmarkile doldurulmadı. '
        'GenelCAD→CFD→sıralama,yeni proje uçtanucaözerklik,görülmemişgörevdeLLMiyileşmesi,karmaşıkVLM,Fusionmotor/VSPPythonköprüsü ve gerçekkanatFEM/OAS ayrı açık. '
        'ANSYSbilinçliertelenmiş,OpenFOAMikinciyerelRANS seçeneği doğrulanmadı; yeni program sayısı doğruluk ölçütü değil.\n'
        '- YeniCFD/derleme/kurulum0;fizik/RAE/M6/İHA/LLM kabulü değişmedi.28yayınkoruması ve10raporfiltre senaryosu geçti;CFDtesti sayılmadı. '
        'TarayıcıfileURL politikası otomatik görselkontrolü engelledi;alternatifyüzey/geçitdenenmedi,statik45yerelbağlantı ve inertsanalDOMfiltre kontrolü yapıldı. '
        'Araştırma öncesi PROJECT_STATE kopyası baseline_PROJECT_STATE.md ile korundu.\n')
    statepath.write_text(state,encoding='utf-8')
    print({'research_deliverable_complete':True,'engineering_issues_still_open':26,'new_native_CFD_runs':0})


if __name__=='__main__':main()
