"""Self-contained offline project report; regenerated when project status changes."""
from html import escape as esc
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'
def load(name):
    p=OUT/'reports'/name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def render(state):
    core=load('test_results.json'); native=load('external_test_summary.json'); fem=load('fem_results.json')
    study=load('wing_study_results.json'); models=load('cad_model_benchmark.json'); repairs=load('checked_parts_results.json')
    family=load('k_family_study.json'); transfer=load('k_family_new_tasks.json')
    cad=load('parametric_cad_qualification.json'); cfd=load('cfd_qualification.json'); cfd_ref=load('cfd_reference_comparison.json'); vlm=load('complex_vlm_qualification.json')
    engineering_section=''
    workflow_section=''
    reliability_section=''
    if (OUT/'reports/guvenilirlik_gelistirme_20261025.html').exists():
        reliability_section='''<section><h2>25 Ekim: kanıt odaklı güvenilirlik geliştirmesi</h2><p>Aynı başlangıçla kontrollü M6 karşılaştırmaları, ham geçmişten yeniden hesaplanan denetim ve konumsal mesh göstergeleri. Desteklenmeyen nedenler ve geçersiz yerel şablonlar ayrı saklanıyor. Genel fizik kabulü açık.</p><div class="links"><a href="reports/guvenilirlik_gelistirme_20261025.html">Yöntemler, gerçek deneyler ve açık kabuller</a></div></section>'''
    learning_checks=load('agent_learning_checks_20261024.json');learning_section=''
    if learning_checks:
        learning_section=f'''<section><h2>Ajan talimatı ve hata hafızası</h2><p>Kanıtlı hatalar, önlenen riskler ve açık hipotezler ayrı kaydedildi. Operasyonel dersler ajan başlatıcısına bağlandı; {learning_checks['passed_count']}/{learning_checks['total']} kod ve dosya kontrolü geçti. Görülmemiş mühendislik görevinde LLM iyileşmesi ve uzmanlık henüz kanıtlanmadı.</p><div class="links"><a href="reports/ajan_talimat_gelisimi_20261024.html">Dersler, düzeltmeler ve değerlendirme planı</a></div></section>'''
    m6_followup=load('m6_followup_index.json');m6_followup_section=''
    if m6_followup:
        m6_followup_section=f'''<section><h2>24 Ekim: ONERA M6 gerçek3B testleri</h2><p>RAE test paketi kapatıldıktan sonra kaynak M6 kanadında iki yeni RANS koşusu ve bütün271 rüzgâr tüneli noktasıyla kıyas yapıldı. Konuma göre duvar-normal aralıklar değiştirildi; hücre sayısı korundu. Son maksimum y+={m6_followup['normal_yplus_max']:.3f}. Genel kabul henüz geçmedi; kalıntı, deney ve diğer açık kapılar raporda.</p><div class="links"><a href="reports/onera_m6_24_ekim.html">Yeni M6 sonuçları, karşılaştırmalar ve gerçek alanlar</a></div></section>'''
    mesh_research=load('mesh_research_index.json');mesh_research_section=''
    if mesh_research:
        mesh_research_section=f'''<section><h2>Kaynaklı CFD teşhisi ve bölgesel C-grid</h2><p>Kaynak araştırmasıyla hazırlanan kontrollü native denemeler, ayrı sayısal alan denetimi ve konuma göre ağ düzeltmeleri raporlandı. Asgari yeterlilik henüz geçmedi; tamamlanmayan ağ/uzak alan ve deney kapıları açık tutuluyor.</p><div class="links"><a href="reports/kaynakli_cfd_teshisi.html">Güncel araştırma, ölçümler ve gerçek alanlar</a><a href="projects/{mesh_research['project_id']}/reports/v3_research_summary.json">Yeni çalışma kaydı</a></div></section>'''
    blind=load('blind_cfd_validation_index.json');blind_section=''
    if blind:
        blind_section=f'''<section><h2>Kaynak geometriden ayrı ajanla CFD sınaması</h2><p>RAE2822'nin yayımlanmış koordinatlarından yeni bölgesel ağlar ve gerçek RANS çözümleri üretildi. Tahminler deney kıyasından önce donduruldu. Hücum kenarı eğri aktarımı ve özgün deney dosyasındaki bir işaret uyuşmazlığı kaynakla denetlendi. Asgari yeterlilik: {"geçti" if blind["minimum_qualification_passed"] else "henüz geçmedi"}. Bütün hatalar ve açık kontroller raporda.</p><div class="links"><a href="reports/kaynak_geometri_ve_kor_cfd.html">Güncel deney, ağ ve geometri raporu</a><a href="projects/{blind["project_id"]}/reports/review_v1_qualification.json">İlk serinin kalite kapıları</a></div></section>'''
    validation=load('validation_benchmark_index.json');validation_section=''
    if validation:
        vp=validation['projects'];vm=validation['cfd']
        validation_section=f'''<section><h2>Gerçek kıyas: karmaşık NIST CAD ve NASA deney verisi</h2><p>Üç CAD parçasında kaynak yardımlı yeniden üretim/düzenleme ve native FreeCAD ölçü değişikliği test edildi. ONERA M6, iki kaynak ağda gerçek 3D RANS ile çözüldü; yedi kesitte 271 deney noktasıyla karşılaştırıldı. Kalite kabulü: {"geçti" if vm["quality_passed"] else "açık"}. Ayrıntılı hata ve kapsam raporda.</p><div class="links"><a href="reports/karmasik_cad_ve_nasa_testleri.html">Yeni test sonuçları ve dosyalar</a><a href="projects/{vp["cad"]}/reports/cad_validation.html">Karmaşık CAD testleri</a><a href="projects/{vp["cfd"]}/reports/m6_validation.html">NASA rüzgâr tüneli kıyası</a></div></section>'''
    elmer=load('elmer_cfd_qualification.json')
    if elmer:
        last=elmer['results'][-1]
        workflow_section=f'''<section><h2>Önceki çalışma: kısıt girişi ve hafif CFD</h2>
<p>Önceki üç sekmeli arayüz proje merkezli yeni EXE ile yenilendi; aşağıdaki görünüm tarihsel kayıttır. Birimli kısıtlar ve araştırma, CAD, ön analiz, CFD ve rapor adımları görev kaydında kanıtlarıyla izlenir.</p>
<p>Taşınabilir Elmer 26.2 eklendi; native Navier–Stokes üç ağda analitik kanal çözümüyle sınandı. İnce ağda hız hatası %{100*last['velocity_relative_L2_error']:.3f}, basınç hatası %{100*last['pressure_relative_L2_error']:.3f}. Bu, uçak CFD kabulü değildir; mevcut SU2 sürükleme yakınsaması açık kalır.</p>
<div class="gallery"><figure><img src="plots/engineering_desk_tab1.png"><figcaption>Görev ve kısıt girişi; boş alanlar bilinmiyor kalır.</figcaption></figure><figure><img src="plots/elmer_cfd_verification.png"><figcaption>Native Elmer akış çözümü, bağımsız referans ve üç ağ.</figcaption></figure></div>
<div class="links"><a href="reports/hafif_cfd_ve_is_akisi.html">Yeni iş akışı ve hazır/eksik kapsam</a><a href="reports/candidate_comparison.html">Koşullu aday karşılaştırması</a><a href="reports/elmer_cfd_qualification.json">Elmer ölçümleri</a></div></section>'''
    if cad and cfd and vlm:
        fine=next(r for r in cfd['results'] if r['case']=='rans_fine')
        fc=cfd_ref['force_comparison']
        engineering_section=f'''<section><h2>Yeni: deterministik CAD, karmaşık VLM ve gerçek CFD</h2>
<p>Kaynak NACA2412 profilinden süpürmeli, daralan, burulmalı kanat ve dört nervür üretildi. CAD {cad['passed_checks']}/{cad['total_checks']} kontrolü geçti; sekiz deliğin çapı ve eksenleri ayrıca STEP dosyalarından ölçüldü. Boyutlar araç sınaması için varsayımdır.</p>
<div class="gallery"><figure><img src="plots/parametric_wing_cad.png"><figcaption>Gerçek STEP dosyalarından kanat ve nervür görünümü.</figcaption></figure><figure><img src="plots/cfd_pressure_and_mesh.png"><figcaption>SU2'nin çözdüğü basınç alanı ve gerçek yakın-cisim ağı.</figcaption></figure></div>
<table><tr><th>Çalışma</th><th>Gerçek sonuç</th><th>Açık kabul</th></tr>
<tr><td>Deterministik CAD</td><td>1,80 m açıklık; 4 nervür; STEP/SVG</td><td>Bu geometri ailesi sınandı; imalat/yapı kabulü yok</td></tr>
<tr><td>Native VSPAERO</td><td>0/3/6°; iki panel sıklığı</td><td>İz CDiw değişimi ~%2; yüzey CDi değişimi %17–18</td></tr>
<tr><td>SU2 INC_RANS</td><td>57.344 hücre; CL={fine['CL']:.6f}, CD={fine['CD']:.6f}</td><td>Orta→ince CD farkı %{100*fc['medium_to_fine_CD_relative_change']:.2f}; ağ kabulü geçmedi</td></tr>
<tr><td>Resmi Fusion MCP</td><td>Sunucu kaydı ve Autodesk girişi tamam</td><td>Bağlantı yenilemesi, lisans/hub ve motor testi bekliyor</td></tr></table>
<p class="warn">CFD ve yeni VLM çalışıyor; tüm kalite ölçütleri sağlanmadı. Bunlar gerçek İHA tasarımı veya genel airfoil doğruluğu kanıtı değildir.</p>
<div class="links"><a href="reports/muhendislik_seviyesi_ve_cfd.html">Ayrıntılı yeni rapor</a><a href="data/parametric_wing_case.json">Kanat girdisi</a><a href="cad/parametric_wing/review_envelope_and_ribs.step">Kanat STEP</a><a href="reports/cfd_reference_comparison.json">CFD referans ve ağ kontrolleri</a><a href="reports/complex_vlm_force_audit.json">VLM kuvvet kontrolü</a></div></section>'''
    mode_names={'baseline':'MakeMe istemi, T=0','training_prefix':'Eğitimdeki istem, T=0','training_sampled':'Eğitimdeki istem, T=0,8 / iki seed','explicit_rules':'Ek ölçü kuralları, T=0'}
    family_rows=''.join(f'<tr><td>{esc("K-1B" if r["model"]=="k1b" else "Cadmonkey data-32")}</td><td>{esc(mode_names[r["mode"]])}</td><td>{r["accepted"]}/{r["trials"]}</td></tr>' for r in family.get('summary',[]))
    transfer_text='; '.join(('K-1B' if r['model']=='k1b' else 'data-32')+f': {r["accepted"]}/{r["trials"]}' for r in transfer.get('summary',[]))
    suites=[('Hesap ve girdi kontrolleri',core.get('passed_checks'),core.get('total_checks'),'setup_report.md'),
            ('OpenVSP / XFOIL / çizim',native.get('passed_checks'),native.get('total_checks'),'external_tools_report.md'),
            ('FreeCAD / Gmsh / CalculiX',fem.get('passed_checks'),fem.get('total_checks'),'engineering_toolchain_report.md'),
            ('Parametreli kanat karşılaştırması',study.get('passed_checks'),study.get('total_checks'),'wing_study_results.json'),
            ('Hatalı CAD taslaklarının düzeltilmesi',sum(c['passed'] for c in repairs.get('checks',[])),len(repairs.get('checks',[])),'checked_parts_results.json')]
    suite_rows=''.join(f'<tr><td>{esc(name)}</td><td>{passed if passed is not None else "bekliyor"}/{total if total is not None else "—"}</td><td><a href="reports/{path}">Kanıtı aç</a></td></tr>' for name,passed,total,path in suites)
    model_rows=''
    for r in models.get('results',[]):
        label=('K-1B / '+r.get('id','')) if r['model']=='k' else 'Zero-to-CAD / sekiz görünüş'
        model_rows+=f'<tr><td>{esc(label)}</td><td>{"çalıştı" if r["inference_completed"] else "başarısız"}</td><td class="warn">{"kabul edildi" if r["geometry_accepted"] else "kabul edilmedi"}</td><td>{r["seconds"]:.2f} s</td></tr>'
    candidates=''
    for r in study.get('candidates',[]):
        candidates+=f'<tr><td>{r["AR"]}</td><td>{r["span_m"]:.3f} m</td><td>{r["chord_m"]:.3f} m</td><td>{r["Re"]:,.0f}</td><td>{r["CDi_scaled"]:.5f}</td><td>{r["CDprofile_estimated"]:.5f}</td></tr>'
    phase_rows=''.join(f'<tr><td>{a["step"]}. {esc(a["title"])}</td><td>{esc(a["status"])}</td></tr>' for a in state['conceptual_steps'])
    tasks=''.join(f'<li><strong>{esc(t["status"])}</strong> · {esc(t["request"])}</li>' for t in state['tasks']) or '<li>Merkezde görevini yazdığında burada izlenir.</li>'
    html=f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>İHA Mühendislik · Proje</title>
<style>body{{margin:0;background:#f0f3f7;color:#172d41;font:16px/1.6 "Segoe UI",sans-serif}}main{{max-width:1120px;margin:auto;padding:40px 26px}}header{{background:#132b40;color:white;padding:34px;border-radius:16px}}h1{{font-size:34px;line-height:1.2;margin:6px 0 14px}}h2{{margin:0 0 16px;font-size:23px}}p{{margin:8px 0 16px}}section{{background:white;border:1px solid #dce4ed;border-radius:14px;padding:28px;margin:22px 0}}.eyebrow{{letter-spacing:2px;font-size:12px;opacity:.75}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0}}.card{{background:white;border:1px solid #dce4ed;border-radius:12px;padding:22px}}.card b{{display:block;font-size:20px}}.card span{{font-size:14px;color:#53697a}}.good{{color:#08766f}}.warn{{color:#9c5400}}a{{color:#06767d;text-decoration:none}}a:hover{{text-decoration:underline}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;border-bottom:1px solid #e0e7ef;padding:11px 9px}}th{{background:#f5f8fb;color:#425f77}}.subtle{{font-size:14px;color:#52697d}}code{{background:#edf2f6;padding:3px 6px;border-radius:4px}}img{{width:100%;height:auto;border-radius:8px;border:1px solid #e0e7ef}}.gallery{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.gallery figure{{margin:0}}figcaption{{font-size:13px;color:#53697a;margin-top:7px}}.links{{display:flex;gap:18px;flex-wrap:wrap}}@media(max-width:760px){{.cards,.gallery{{grid-template-columns:1fr}}main{{padding:16px}}section{{padding:18px}}h1{{font-size:28px}}table{{font-size:12px}}}}</style>
<main><header><div class="eyebrow">YEREL MÜHENDİSLİK ÇALIŞMA ALANI</div><h1>İHA Mühendislik</h1><p>Görevler, çizimler, gerçek çözücüler ve kontrol edilmiş çıktılar.</p><p style="margin-bottom:0">Başlamak için <strong>Muhendislik-Merkezi.exe</strong> dosyasını aç ve projeni seç. Aynı dosyalarla bu Codex sohbetinden de çalışabiliriz.</p></header>
{reliability_section}
{m6_followup_section}
{learning_section}
{mesh_research_section}
{blind_section}
{validation_section}
<section><h2>19 Ekim: projeler, EXE ve yeni analizler</h2><p>Dosyalar, görev taslakları, CAD programı ve aktif model proje içinde tutuluyor. Hazır proje tanımı yoksa eski örnek sessizce çalıştırılmıyor. Kaynak DAT'tan yeni SU2 Euler ağı/çözümü ve OpenAeroStruct örnekleri ayrıca sınandı; kabul kapsamları raporda ayrı.</p><div class="gallery"><figure><img src="plots/projects_iha_0.png"><figcaption>Proje içinden görev, CAD ve rapor seçimi.</figcaption></figure></div><div class="links"><a href="reports/projeler_exe_ve_profil_cfd.html">Güncel kullanım ve ölçümler</a><a href="reports/openaerostruct_ajan_yaklasimi.html">Ajan kaynakları ve yeni kurallar</a><a href="projects/proje-0314dcd012/reports/profile_cfd.html">Yeni profil CFD alanı</a></div></section>
<div class="cards"><div class="card"><b class="good">Parametrik CAD çalışıyor</b><span>Geometri ölçümlerle denetleniyor; yerel CAD ve analiz uygulamaları kurulu.</span></div><div class="card"><b class="warn">CFD kabulü sürüyor</b><span>Gerçek SU2 alan çıktısı var; sürükleme ağ hassasiyeti ve Fusion motor testi açık.</span></div><div class="card"><b>Gerçek İHA: veri bekliyor</b><span>Görev, bileşen kütleleri ve kabul ölçütleri girilmeden uygun uçak sonucu verilmez.</span></div></div>
{engineering_section}
{workflow_section}
<section><h2>Nasıl kullanacaksın?</h2><ol><li><strong>Mühendislik Merkezi</strong> içinde görevi kendi cümlelerinle yaz.</li><li>Ajanın dosyaları okumasını, uygun araçları çalıştırmasını ve sonuçları kontrol etmesini iste.</li><li>Çizim, analiz, açık kontroller ve kanıtlar bu proje klasöründe birlikte saklanır.</li></ol><p>Örnek: “İki kanat adayını aynı kısıtlarla karşılaştır; verilerin kaynağını, CAD dosyalarını, yakınsama kontrollerini ve eksikleri raporla.”</p><div class="links"><a href="Baslangic.md">Kullanım kılavuzu</a><a href="reports/cad_model_research.md">Model araştırması ve ölçümler</a><a href="data/project/mission.json">Görev girdileri</a><a href="data/project/mass_budget.json">Kütle bütçesi</a></div></section>
<section><h2>Gerçek çalıştırmalar</h2><table><tr><th>Çalışma</th><th>Geçen / toplam</th><th>Rapor</th></tr>{suite_rows}</table><p class="subtle">Bunlar belirtilen örnekler ve yöntemler için araç kontrolleridir. Fiziksel tasarımın bütün gereksinimlerini doğrulamaz. ANSYS sonraki ağır kurulum aşamasındadır.</p></section>
<section><h2>Yeni araştırma ve kapsamlı proje raporu</h2><p>Geliştiricinin daha yeni Cadmonkey data-32 sürümü indirildi, dosya özeti doğrulandı ve eski K-1B ile aynı ölçülerde karşılaştırıldı. Aşağıdaki sayılar düzeltilmemiş model çıktılarına aittir.</p><table><tr><th>Model</th><th>Koşul</th><th>Geometri kabulü</th></tr>{family_rows}</table><p>Altı farklı yeni parça: {esc(transfer_text)}. Bunlar küçük yerel deneylerdir; genel başarı oranı veya mühendislik güvencesi değildir.</p><div class="links"><a href="reports/proje_durum_ve_k1b_arastirma.html">Bütün proje ve model araştırması raporu</a><a href="reports/k_family_study.json">30 karşılaştırma denemesi</a><a href="reports/k_family_new_tasks.json">12 yeni parça denemesi</a></div></section>
<section><h2>İlk yerel CAD denemeleri</h2><table><tr><th>Deneme</th><th>Yerel üretim</th><th>Geometri kabulü</th><th>Toplam süre</th></tr>{model_rows}</table><p>Eski K-1B kutuyu merkezlemedi; delikli plakada çıkarma işlemi eksikti; ara parçada çap/yarıçap karıştı. Zero-to-CAD Q6 denemesi tamamlanmış katı üretmedi. Sonrasında Codex'in düzelttiği üç parça ayrı kontrollerden geçti.</p><p><a href="reports/cad_model_benchmark.json">İlk ölçümler</a> · <a href="cad/checked_parts/">Codex tarafından düzeltilen parçalar</a></p></section>
<section><h2>Dosyadan yönetilen kanat karşılaştırması</h2><p>Test varsayımları: 0,50 m² alan, 30 m/s, CL=0,35. Değişen veterle Reynolds sayısı yeniden hesaplandı. VSPAERO yük dağılımı ve XFOIL poları birlikte kullanıldı.</p><table><tr><th>AR</th><th>Açıklık</th><th>Veter</th><th>Re</th><th>CDi</th><th>Tahmini profil CD</th></tr>{candidates}</table><p class="subtle">İzole düz kanatlar; profil sürüklemesi yaklaşık 2D eşleştirmedir. Sonuç, tüm uçağın sürüklemesi, optimum tasarım veya sürdürülebilir hız kanıtı değildir. <a href="data/wing_study_case.json">Düzenlenebilir deney girdisi</a>.</p></section>
<section><h2>Çizimler ve analizler</h2><div class="gallery"><figure><img src="plots/wing_comparison.png"><figcaption>Aynı test koşullarında üç kanat.</figcaption></figure><figure><img src="plots/fem_convergence.png"><figcaption>FreeCAD → gerçek ağ → CalculiX. Üç ağ ve analitik kiriş karşılaştırması.</figcaption></figure><figure><img src="plots/aircraft_geometry.png"><figcaption>OpenVSP test geometrisi. Gerçek İHA tasarımı değildir.</figcaption></figure><figure><img src="plots/aircraft_three_view.png"><figcaption>Geometriden alınan üç görünüş. STEP, VSP3 ve DXF dosyaları cad klasöründe.</figcaption></figure></div></section>
<section><h2>Gerçek projenin kavramsal aşaması</h2><table><tr><th>Adım</th><th>Durum</th></tr>{phase_rows}</table><p class="subtle">Test sayıları gerçek proje girdilerine taşınmadı. Bilinmeyen kütleler sıfır sayılmadı.</p></section>
<section><h2>Görev kaydı</h2><ul>{tasks}</ul></section><p class="subtle">Yerel rapor · {esc(state['timestamp'])} · Raporu yenilemek için çalışma merkezindeki bir kontrolü çalıştır veya proje durumunu güncelle.</p></main></html>'''
    (OUT/'Proje-Ozeti.html').write_text(html,encoding='utf-8')
