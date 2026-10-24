"""Build a source-linked learning ledger, bounded evaluation plan and user report."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import html
import json
import os

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'outputs/data/agent_learning'
REP = ROOT / 'outputs/reports'
M6 = 'outputs/projects/proje-e9319baef1/'
RAE = 'outputs/projects/proje-15cce2de02/'
REF = ROOT / '.agents/skills/iha-muhendislik/references'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    destination = DATA / 'reviewer_ledger_v1.json'
    assert not destination.exists(), 'Preserve prior learning revisions'
    now = datetime.now(timezone.utc).isoformat()
    specs = [
        ('L01', 'Sınır satırının son eleman kimliği düğüm olarak okunmuş; ilk kaynak-topoloji teşhisi geçersiz.',
         'Dosya şemasını doğrulamadan satırın tamamını bağlantı kabul etme olası davranışıdır; modelin iç düşüncesi ölçülmedi.',
         [M6+'simulations/m6_wallnormal_mesh_20261024/correction.json', 'work/m6_followup/wallnormal_mesh_v1_marker_parser_error.py'],
         'Düğüm aralığında kalan sonda ID, sonda büyük ID, eksik/fazla/tekrarlı kayıtlar ile guard geçti.', 'guard_verified',
         'Kaynakta prizma sütunu bulunmadığı ilk iddia bu parser hatası nedeniyle çürütüldü.'),
        ('L02', 'Yanlış referans yöneliminde kaynak ve değiştirilmiş bütün prizmalar negatif çıkmış; sabit sözleşme dönüşümüyle pozitif.',
         'Denetçinin koordinat/düğüm sözleşmesini sınamadan işareti fiziksel bozukluk diye yorumlama olası davranışıdır.',
         [M6+'simulations/m6_wallnormal_mesh_20261024_v2/correction.json', M6+'simulations/m6_wallnormal_mesh_20261024_v3/normal_mesh_audit.json'],
         'Gerçek dondurulmuş wedge denetçisinde analitik, ters, çökmüş ve yerel katlanmış hücre sınandı.', 'guard_verified',
         'Kaynak ağın sırf eski determinant işaretiyle ters olduğu teşhisi çürütüldü.'),
        ('L03', 'Native SU2 merkezi akı/MUSCL uyumsuzluğunda programı reddetmiş; gerekli NO ayarı sonraki native koşuda çalışmış.',
         'Yöntem değiştirirken bağımlı seçenekleri önemsiz/etkisiz varsayma olası davranışıdır.',
         [M6+'simulations/m6_jst_control_20261024/solver.log', M6+'simulations/m6_jst_control_20261024/case.cfg', M6+'simulations/m6_jst_control_20261024_v2/run_status.json'],
         'Eski reddedilmiş ve düzeltilmiş gerçek config üzerinde ön kontrol, eksik ayar ve desteklenmeyen sürüm karşı örneği geçti. Yeni native koşu yapılmadı.', 'guard_verified', None),
        ('L04', 'Kesilmiş koşuda history sonu ve son tam alan farklı; mevcut kayıtta başarılı çıkış/süre uydurulmamış.',
         'Son history satırını her zaman son alanla eşleme olası hata riskidir; bu kayıtta yanlış kabul edilmiş sonuç bulunduğu söylenmiyor.',
         [RAE+'simulations/v3_r4roe_coarse_firstorder_control/run_status.json', RAE+'simulations/v3_r4roe_coarse_firstorder_control/checkpoint_selection.json'],
         'Tam üçlü, eksik alan, farklı mesh kimliği, yanlış hash ve son history ile alan karışımı karşı örnekleri geçti. Guard, gerçek alan metadata çıkarımını yapmaz; çağıran doğrulamalı.', 'guard_verified', None),
        ('L05', 'Yuvarlanınca hedefe eşit görünen gerçek kalıntı ham değerde başarısız; M6 kuvvet ekranı geçse de kalıntı ve deney kapıları açık.',
         'Gösterim basamağına göre karar verme veya tek başarılı ölçütü genel kabul sayma önlenen hata riskidir.',
         [RAE+'simulations/v3_r4roe_firstorder_cont4200/prediction_metrics.json', M6+'reports/m6_wallnormal_results_20261024_v3.json'],
         'Gerçek eski ham değer, eşit/eşik altı, null/NaN/inf/bool, eksik kapı ve truthy metin karşı örnekleri geçti.', 'guard_verified', None),
        ('L06', 'Kaynak noktaları taşıyan eski iki spline hücum kenarında yapay teğet açısı oluşturmuş; yeni C1 temsil ayrı sürüm olarak tutulmuş.',
         'Noktadan geçişi tam geometrik eşdeğerlik için yeterli sanma olası davranışıdır.',
         ['work/blind_validation/reviewer/leading_edge_tangent_audit.json', RAE+'reports/review_v2_qualification.json'],
         'Eski geometri denetimi kanıt olarak yeniden okundu; bu tur yeni geometri veya görülmemiş LLM CAD testi yapılmadı.', 'instruction_added', None),
        ('L07', 'Eski C-grid iz son segmenti kaydedilen aralık sınırını aşmış; ayrı tail-r2 temsil ve bağımsız ağ denetimi var.',
         'Dağıtımın son noktasını sonradan değiştirirken bütün komşu oranlarını tekrar denetlememek olası davranışıdır.',
         [RAE+'reports/prediction_v3_cgrid_unapplied_tail_proposal.json', RAE+'simulations/v3_cgrid_tailr2_coarse/independent_cgrid_audit.json'],
         'Önceki konumsal ölçümler korundu; yeni mesh duyarlılık çalışması yapılmadı. Bu hata şok/deney uyuşmazlığının kanıtlanmış kök nedeni değildir.', 'instruction_added', None),
        ('L08', 'Yayınlanmış WIND sayısal eğrisinin yüzey sırası ilk değerlendirmede yanlış eşlenmiş. Native alan vektörü ile history RMS semantiğinin aynı olmadığı ayrıca belgeli.',
         'Başlık/alan adını birim, yüzey sırası ve üretim aşamasını incelemeden fiziksel anlam diye kabul etme olası davranışıdır.',
         [RAE+'reports/v3_published_WIND_diagnostic_v1_wrong_branch_order.json', RAE+'reports/v3_published_WIND_diagnostic.json', RAE+'reports/prediction_v3_cgrid_r4_warmstart_v2_diagnosis.json'],
         'Önceki sıralama/semantik kanıtları okundu; native residual vektörünün tam aşama farkı henüz kanıtlanmadı. Yeni son işlem genel yeterliliği sınanmadı.', 'instruction_added', None),
        ('L09', 'M6 doğrusal çözücü üst sınıra geliyor; bu gözlem tek başına yakınsama sorununun nedeni olduğunu göstermiyor.',
         'Korelasyonu neden sayıp daha çok iterasyonu doğrudan çözüm diye hafızaya yazma riskidir; teşhis açık hipotezdir.',
         [M6+'reports/m6_wallnormal_results_20261024_v3.json'],
         'Aynı tam restart/config/mesh ile yalnız doğrusal sınır değişen eş bütçeli iki koşu planlanmalı. Henüz yapılmadı; düzeltildi denemez.', 'hypothesis_open', None),
    ]
    operational = json.loads((REF / 'operational_lessons.json').read_text(encoding='utf-8'))
    mapping = {r['id']: r for r in operational['lessons']}
    lessons = []
    for ident, observed, inferred, evidence, checked, state, disproven in specs:
        item = {'id': ident, 'knowledge_status': mapping[ident]['knowledge_status'],
                'observed': observed, 'possible_enabling_behavior': inferred,
                'behavior_causation_established': False,
                'scope': mapping[ident]['scope'], 'correction': mapping[ident]['action'],
                'evidence': [{'path': p, 'sha256': sha(ROOT / p)} for p in evidence],
                'verification': checked, 'promotion_state': state,
                'llm_behavior_validated_on_unseen_case': False}
        if disproven:
            item['disproven_diagnosis'] = {'claim': disproven, 'status': 'invalidated_preserved', 'never_reuse_as_fact': True}
        lessons.append(item)
    checks = json.loads((REP / 'agent_learning_checks_20261024.json').read_text(encoding='utf-8'))
    ledger = {'schema_version': 1, 'version': operational['version'], 'created_utc': now,
              'task_id': '20261024-164603-4764e5', 'role': 'reviewer_only',
              'scope': 'Hata kanıtı ve talimat iyileştirmesi; fiziksel CFD nedeni veya uzmanlık kanıtı değildir.',
              'counts': dict(Counter(i['knowledge_status'] for i in lessons)), 'lessons': lessons,
              'sources': [{'url': 'https://arxiv.org/abs/2303.11366', 'checked_utc': now,
                           'supports': 'Reflexion: sonuç geri bildirimi metinsel episodik hafızada sonraki denemeleri yönlendirebilir; ağırlık güncellemesi değildir.'},
                          {'url': 'https://arxiv.org/abs/2303.17651', 'checked_utc': now,
                           'supports': 'Self-Refine: çıktı, geri bildirim ve düzeltme döngüsü farklı görevlerde araştırılmıştır; bu CFD sisteminin uzmanlık testi değildir.'}],
              'llm_before_after_comparison_run': False, 'expert_qualification_passed': False,
              'instruction_snapshot': checks['instruction_snapshot']}
    save(destination, ledger)
    plan = {'version': 1, 'created_utc': now, 'status': 'planned_not_run',
            'expert_status': 'not_established', 'iteration_policy': 'Yetkili sonraki işte başarısızlığı kaydet, bir düzeltme yap, karşı örnek ve görülmemiş vakayla yeniden değerlendir; ilerleme yoksa ayırt edici teşhise geç.',
            'comparison_contract': {'baseline_snapshot': 'work/agent_learning/baseline_20261024',
                'candidate_snapshot': checks['instruction_snapshot'],
                'holdouts_not_selected_yet': True,
                'required_before_running': ['sabit model/araç sürümü', 'aynı girdi ve bütçe', 'önceden sabit vaka eşikleri', 'cevaba erişim kaydı', 'bağımsız değerlendirme'],
                'prohibited': ['Eşik gevşetme', 'görülen vakayı görülmemiş sayma', 'yalnız başarılı tekrarları seçme', 'deney cevabını operasyonel belleğe yazma']},
            'competencies': [
                {'area': 'Geometri/CAD', 'deliverable': 'Önceden kullanılmamış kaynak parçada birim/eksen, katı/topoloji, ölçü ve kritik yüzey geri ölçümü; parametre değişikliğinde yeniden kontrol', 'status': 'not_run'},
                {'area': 'Dosya/API ve sayısal kabul', 'deliverable': 'Yeni dosya düzenlerinde ve geçerli/geçersiz kayıt çiftlerinde doğru davranış; araç/ayar sürüm uyumu; eksik veriyle yanlış kabul yok', 'status': 'coding_guards_only_39_passed'},
                {'area': '2B viskoz CFD', 'deliverable': 'Görülmemiş kaynak geometri/koşulda önceden belirlenen geometri, üç ağ, konumsal BL/iz, yakınsama, uzak alan, integrasyon ve deney kapılarının birlikte kabulü', 'status': 'not_qualified'},
                {'area': '3B viskoz CFD', 'deliverable': 'Görülmemiş kanatta 2B kapılarına ek kök/uç/açıklık kontrolleri ve kaynak deney kıyası; ayrı kabul', 'status': 'not_qualified'},
                {'area': 'Yapı/aeroelastisite', 'deliverable': 'Yetkili yeni görevde doğru malzeme/yük/mesnet ve uygun referansla ayrı doğrulama; CFD başarısından türetilmez', 'status': 'not_evaluated_this_iteration'}],
            'next_single_step': 'Mevcut M6 fizik hipotezini aynı restart ile doğrusal limit çift denemesinde ayırt et; bunu ayrı sayısal test olarak kaydet. Talimat davranışının iyileştiği iddiası için ayrıca yeni CAD/CFD görevlerinde önce/sonra kıyası gerekir.'}
    save(DATA / 'qualification_plan_v1.json', plan)

    memory = '''# Engineering agent learning-loop preference and routing

- User explicitly requested on 2026-10-24 that the UAV engineering agent record likely error-enabling behaviors, add evidence-backed corrections to memory/instructions and improve iteratively. Distinguish observed implementation errors from inferred behavior and untested CFD causal hypotheses. Do not promise that prompts alone produce expert competence or train model weights.
- Scope: C:/Users/Urungu/Documents/Codex/2026-10-18/bu. Read AGENTS.md and .agents/skills/iha-muhendislik/SKILL.md. Operational memory is references/operational_lessons.json and the iteration protocol is references/learning_loop.md inside that skill. Select relevant scoped lesson IDs at task start; preserve instruction version/SHA256 with the task.
- Durable precautions: parse external connectivity by element type rather than all trailing tokens; validate reference-element conventions on known valid/inverted cells; check versioned solver option dependencies; match complete field/restart/history checkpoints; compare raw unrounded values and require every mandatory gate. These are scoped checks, not universal physical solver settings.
- Reviewer evidence belongs in outputs/data/agent_learning/reviewer_ledger_v1.json; it can expose known benchmark answers and must not be fed to a blind analyst. The normal GUI reads historical project results and is not a blind route. Shared disk/history cannot guarantee isolation. Keep target Cp/CL/CD or shock answers out of operational memory.
- This revision's deterministic artifact/launcher checks passed; no independent LLM before/after or unseen engineering evaluation has yet established improvement or expert status. Existing RAE/M6 physical qualification remains false. Use prior failure regressions plus newly held-out geometry/conditions; never relax acceptance gates, hide failed attempts or promote a disproven diagnosis. Future authorized engineering tasks continue the recorded loop; no autonomous background job was created.
'''
    (REP / 'ajan_hafiza_notu_20261024.md').write_text(memory, encoding='utf-8')
    esc = html.escape
    def link(relative, label=None):
        path = ROOT / relative
        ref = os.path.relpath(path, REP).replace(os.sep, '/')
        return f'<a href="{esc(ref, quote=True)}">{esc(label or relative)}</a>'
    rows = []
    labels = {'confirmed_error': 'Kanıtlı uygulama/temsil hatası', 'prevented_failure': 'Önlenmiş hata riski', 'hypothesis': 'Açık hipotez'}
    for item in lessons:
        refs = '<br>'.join(link(e['path'], Path(e['path']).name) for e in item['evidence'])
        rows.append(f'<tr><td><b>{item["id"]}</b><br>{labels[item["knowledge_status"]]}</td><td>{esc(item["observed"])}<p class="note">Muhtemel davranış: {esc(item["possible_enabling_behavior"])}</p></td><td>{esc(item["correction"])}</td><td>{esc(item["verification"])}<p>{refs}</p></td></tr>')
    report = f'''<!doctype html><html lang="tr"><meta charset="utf-8"><title>Ajan talimatı ve hafıza geliştirmesi</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:1500px;margin:36px auto;padding:0 24px;color:#172b3a;background:#f8fafc}}h1{{font-size:30px}}.card{{background:white;padding:20px;border:1px solid #cbd5e1;border-radius:12px;margin:20px 0}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:14px;border:1px solid #cbd5e1;text-align:left;vertical-align:top}}th{{background:#e8eff6}}.note{{font-size:14px;color:#475569}}a{{color:#145da0}}.badge{{font-weight:bold;color:#9a3412}}@media(max-width:900px){{table{{font-size:13px}}td,th{{padding:8px}}}}</style>
<h1>Ajan talimatı ve hafıza geliştirmesi</h1><p>24 Ekim 2026 · Sürüm {esc(operational['version'])}</p>
<div class="card"><b>Yöntem uygun; bu tur uzmanlık kanıtı değildir.</b><p>6 kanıtlı uygulama/temsil hatası, 2 önlenmiş hata riski ve 1 açık hipotez ayrı kaydedildi. Hatalara yol açmış olabilecek davranışlar çıkarım olarak etiketlendi. İki yanlış topoloji/yönelim teşhisi çürütülmüş olarak saklandı.</p>
<p>Operasyonel dersler beceriye ve mevcut EXE/GUI'nin ajan başlatma yoluna bağlandı. Yeni görevde seçilen dersler kaydedilecek; başlatıcı talimat sürümünü ve dört dosyanın SHA256 değerini görevle birlikte saklıyor. Model ağırlıkları değiştirilmedi.</p></div>
<div class="card"><b>Gerçekten kontrol edilen: {checks['passed_count']}/{checks['total']} kod ve dosya karşı örneği geçti.</b><p>Yanlış bağlantı okuma, geçersiz ayar, bozuk referans hücre, alan/geçmiş karışması, eksik kalite kapısı ve yuvarlama ile yanlış kabul sınandı. Başlatıcının hem değişiklik yapmayan önizlemesi hem de süreç başlatma dalı izole dosyalarla kontrol edildi; yeni LLM oturumu başlatılmadı. Bu sayılar LLM başarı oranı değildir.</p><p class="badge">Görülmemiş mühendislik göreviyle önce/sonra LLM kıyası: yapılmadı. Uzmanlık: henüz kanıtlanmadı. RAE/M6 fizik kabulü: başarısız/açık.</p></div>
<h2>Hata, olası davranış ve dar kapsamlı düzeltme</h2><table><thead><tr><th>Ders</th><th>Kanıtlanan olay / çıkarım</th><th>Uygulanacak düzeltme</th><th>Kontrolün sınırı ve kanıt</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<div class="card"><h2>Sonraki iterasyon nasıl işleyecek?</h2><p>İlgili dersleri seç → özgün hatayı/logu koru → tek değişiklik ve geçme ölçütünü kaydet → karşı örnekle sınayıp yeni sürümü dene → tahmini dondur → bağımsız değerlendir → kanıtlı düzeltmeyi dar kapsamlı kurala ekle. Sonuç belirsizse hipotez olarak bırak. Yeni görevlerde eski kontroller ve önceden görülmemiş kaynak geometriler birlikte kullanılacak; geliştirmede kullanılan vaka tekrar kör test sayılmayacak.</p>
<p>CAD, 2B/3B viskoz CFD, yapı ve aeroelastisite ayrı yetkinliklerdir. Her birinde ilgili geometri, konumsal ağ, yakınsama, ağ/uzak alan duyarlılığı, bağımsız integrasyon ve deney kapıları gerekir. Promptu uzatmak veya bir vakayı tekrar tekrar tutturmak uzmanlık ölçüsü değildir.</p>
<p>Mevcut M6 için doğrusal çözücü sınırını karşılaştıran çift deneme gelecekteki ayırt edici sayısal testtir; bu tur çalışılmadı. Eksik fizik kontrolleri talimat düzenlemesiyle kapatılmadı.</p></div>
<div class="card"><h2>Kaynak ve kayıtlar</h2><p><a href="https://arxiv.org/abs/2303.11366">Reflexion</a> sonuç geri bildirimini metinsel bellekte kullanmayı; <a href="https://arxiv.org/abs/2303.17651">Self-Refine</a> geri bildirimle yinelemeli düzeltmeyi araştırır. Bu çalışmaların görev sonuçları bu CFD ajanının uzmanlaştığını göstermez.</p>
<ul><li>{link('outputs/data/agent_learning/reviewer_ledger_v1.json', 'Sürümlü değerlendirici defteri ve kanıt hashleri')}</li><li>{link('outputs/data/agent_learning/qualification_plan_v1.json', 'Yeni görevlerde davranış ve yeterlilik değerlendirme planı')}</li><li>{link('outputs/reports/agent_learning_checks_20261024.json', '39 kontrolün ayrıntısı')}</li><li>{link('outputs/reports/ajan_hafiza_notu_20261024.md', 'Kalıcı hafıza notunun kopyası')}</li></ul>
<p class="note">Değerlendirme defteri geçmiş deney cevaplarını açığa çıkarabilir; analizciye yalnız hedef içermeyen operasyonel dersler verilir. Normal GUI geçmiş AGENTS/PROJECT_STATE okuduğu için kör analiz aracı değildir. Bu ayrım dosya erişimi veya model belleği için güvenlik yalıtımı sağlamaz.</p></div></html>'''
    (REP / 'ajan_talimat_gelisimi_20261024.html').write_text(report, encoding='utf-8')
    print(json.dumps({'counts': ledger['counts'], 'checks_passed': checks['passed'],
                      'report': 'outputs/reports/ajan_talimat_gelisimi_20261024.html'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
