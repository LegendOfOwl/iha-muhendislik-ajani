"""Evidence-linked report and bounded development-task closure."""
import json
import os
from html import escape
from pathlib import Path
from linear_pair import ROOT, PROJECT, RUN, REPORT, TASK, read, save, sha, now


def main():
    pair=read(REPORT)
    feedback_path=PROJECT/'reports/m6_cfl_feedback_20261025.json'
    feedback=read(feedback_path) if feedback_path.exists() else None
    curvature=read(PROJECT/'reports/m6_curvature_20261024.json')
    curvature2=read(PROJECT/'reports/m6_curvature_v2_20261025.json')
    tests=read(ROOT/'outputs/reports/reliability_method_tests.json')
    audit=read(PROJECT/'reports/reliability_audit.json')
    sources=read(ROOT/'work/reliability/sources/manifest.json')
    core=read(ROOT/'outputs/reports/test_results.json')
    assert tests['passed'] and audit['passed'] and core['passed_checks']==26
    task=read(TASK)
    action_names={'localize_nonlinear_stall':'Dış çözümdeki yavaşlamayı konuma ve denkleme göre ayır',
                  'regional_mesh_control':'Bölgesel ağ duyarlılığını kontrollü olarak sına',
                  'repair_evidence':'Girdi ve kanıt eşleşmesini düzelt'}
    next_action=action_names.get(audit['recommendation']['action'],audit['recommendation']['action'])
    # Preserved pre-iteration publication catalog; not a new baseline from current inputs.
    oldinputs=read(ROOT/'work/reliability/preexisting_real_inputs_catalog.json')['inputs_sha256']
    realcheck={p:sha(ROOT/p)==h for p,h in oldinputs.items() if p.startswith('outputs/data/project/')}
    assert len(realcheck)==3 and all(realcheck.values())
    oldseal=read(PROJECT/'reports/m6_wallnormal_prediction_frozen_20261024_v3.json')
    assert all(sha(ROOT/p)==h for p,h in oldseal['files_sha256'].items())
    sourcecheck={s['file']:sha(ROOT/'work/reliability/sources'/s['file'])==s['sha256'] for s in sources}
    assert all(sourcecheck.values())
    frozen={}
    for parent in [RUN]+([PROJECT/'simulations/m6_cfl_feedback_20261025'] if feedback else []):
        for sealpath in parent.glob('*/prediction_frozen.json'):
            seal=read(sealpath)
            mismatch=[p for p,h in seal['files_sha256'].items() if sha(ROOT/p)!=h]
            assert not mismatch,mismatch
            frozen[str(sealpath.relative_to(ROOT))]={'sha256':sha(sealpath),'files':len(seal['files_sha256'])}
    integrity={'created_utc':now(),'frozen_predictions':frozen,'source_seal_files':len(oldseal['files_sha256']),
               'real_UAV_inputs_unchanged':realcheck,'research_source_hashes':sourcecheck,
               'real_UAV_baseline':{'path':'work/reliability/preexisting_real_inputs_catalog.json',
                                    'sha256':sha(ROOT/'work/reliability/preexisting_real_inputs_catalog.json')},
               'new_native_runs':2+(2 if feedback else 0),'minimum_qualification_passed':False}
    integritypath=PROJECT/'reports/reliability_integrity_20261025.json';save(integritypath,integrity)
    def render(target):
        def url(p):return os.path.relpath(ROOT/p,target.parent).replace('\\','/')
        def link(p,label):return f'<a href="{escape(url(p),quote=True)}">{escape(label)}</a>'
        rows=''
        for name,r in pair['results'].items():
            m=r['matched'];rows+=f'<tr><td>Doğrusal sınır {name[3:]}</td><td>1000</td><td>{r["run"]["seconds"]:.1f}</td><td>{m["rms[Rho]"]:.9f}</td><td>{m["CL"]:.8f}</td><td>{m["CD"]:.8f}</td><td>{r["Cp"]["all_point_Cp_RMSE"]:.6f}</td></tr>'
        if feedback:
            for name,r in feedback['results'].items():
                m=r['matched'];rows+=f'<tr><td>{"Sabit CFL4" if name=="fixed" else "CFL geribesleme4–40"}</td><td>600</td><td>{r["native_run"]["seconds"]:.1f}</td><td>{m["rms[Rho]"]:.9f}</td><td>{m["CL"]:.8f}</td><td>{m["CD"]:.8f}</td><td>{r["Cp"]["all_point_Cp_RMSE"]:.6f}</td></tr>'
        effect=pair['pair']['additional_log10_reduction']
        feedback_text=''
        if feedback:
            adaptive=feedback['results']['adaptive'];b=feedback['pair']['additional_log10_reduction']
            feedback_text=f'<p>Bu sonuçtan sonra kaynaklı tek politika sınandı: sınırlı CFL geribeslemesi. Aynı yeni seed ile yalnız CFL_ADAPT açılıp kapatıldı. Sabit/geribeslemeli600 adımda ek yoğunluk-artık düşüşü {b:.6f} log10. Geribeslemeli koşuda mevcut iterasyon ekranı: <strong>{"geçti" if adaptive["iterative_gate"]["passed"] else "geçmedi"}</strong>. Bu ekran; deney, tüm sınır tabakası veya ağ bağımsızlığı kabulü değildir.</p><img src="{url(Path("outputs/projects/proje-e9319baef1/plots/m6_cfl_feedback_20261025.png"))}">'
        source_links=''.join(f'<li><a href="{escape(s["url"],quote=True)}">{escape(s["file"])}</a> — {escape(s["use"])}</li>' for s in sources)
        if feedback:
            feedback_text+=f'<p>Bu çift için de önceden seçilen0,3 log10 etki ölçütü {"geçti" if feedback["pair"]["effect_passed"] else "geçmedi"}. Deneme bütçesi uzatılmadı; yeni CFL değerleri taranmadı.</p>'
        curvature_extra=f'''<section><h2>Konumsal göstergenin düzeltilen ikinci sürümü</h2><p class="warn">İlk prototipte bazı yerel türevler şablon desteğinin dışındaki hücrelere taşındı; öncelik grubundaki en büyük gösterge {curvature2['v1_selected_max_indicator_warning']:.1f} oldu. Analitik test başarısı gerçek ağdaki bu kullanım sorununu önleyemedi. İlk sonuçlar silinmedi ve üretim kararı için kabul edilmedi.</p><p>İkinci sürüm aynı alanı yeniden işler: hücre köşeleri fit noktalarının konveks zarfında olmalı,40/80 komşulu fitler tutarlı olmalı ve koşul/fit hatası geçmelidir. {curvature2['region_candidates']:,} adaydan {curvature2['eligible']:,} hücre uygun, {curvature2['not_eligible']:,} hücre maskeli kaldı; {curvature2['selected_cells']} konum öncelikli. Yönün ayrıca kararlı bulunduğu öncelikli hücre sayısı {curvature2['selected_direction_valid']}. Bunlar hâlâ sezgisel inceleme kontrolleridir.</p><img src="{url(Path('outputs/projects/proje-e9319baef1/plots/m6_curvature_v2_20261025.png'))}"><p>{link(Path('outputs/projects/proje-e9319baef1/data/reliability_v2_20261025/curvature_v2_cells.csv'),'İkinci sürüm: maskeler ve iki ölçek')} · {link(Path('outputs/projects/proje-e9319baef1/data/reliability_v2_20261025/curvature_v2_view.vtu'),'İkinci sürüm 3B alan')}</p></section>'''
        auditstate=audit['raw_recomputed']
        gate_rows=''.join(f'<tr><td>{escape(n)} / alan-geçmiş</td><td>{"eşlendi" if r["checkpoint_complete"] else "eksik"}</td></tr><tr><td>{escape(n)} / artık ve kuvvet penceresi</td><td>{"geçti" if r["iterative_gate"]["passed"] else "geçmedi"}</td></tr>' for n,r in auditstate.items())
        docs=Path('work/reliability/README.md')
        html=f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Kanıt odaklı geliştirme · 25 Ekim</title>
<style>body{{background:#eef2f5;color:#163345;font:16px/1.65 'Segoe UI',sans-serif;margin:0}}main{{max-width:1100px;margin:auto;padding:32px 24px}}header{{background:#123b49;color:white;padding:30px;border-radius:16px}}section{{background:white;padding:26px;border-radius:12px;margin:20px 0}}h1{{font-size:32px;margin:5px 0}}h2{{font-size:23px;margin-top:0}}table{{width:100%;border-collapse:collapse;font-size:14px}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #dce4e9}}img{{width:100%;height:auto}}a{{color:#087887}}.warn{{background:#fff1d7;border-left:5px solid #c78016;padding:16px}}.flow{{display:flex;flex-wrap:wrap;gap:8px}}.flow span{{padding:10px;background:#eef5f5;border-radius:8px}}.small{{font-size:14px;color:#536b79}}</style>
<main><header><div>24–25 EKİM 2026 · GERÇEK NATIVE TESTLER</div><h1>Kanıt odaklı yöntem geliştirme</h1><p>Hipotezi kaydet → aynı başlangıçla ayırt et → faydasız dalı bırak → açık kapıyı koru.</p></header>
<section><h2>Ne değişti?</h2><p>Parametre kombinasyonlarını taramak yerine nedenleri sırayla ayıran bir denetçi eklendi. Dosya mührü veya alan/geçmiş eşlemesi bozuksa yorum durur. İteratif hata açıkken ağ farkı, saf ayrıklaştırma hatası diye sunulmaz. Denetçi önerisinin optimumluğu veya görülmemiş vakalarda başarı artışı henüz gösterilmedi.</p><p class="warn"><strong>Genel M6/RAE fizik kabulü hâlâ false.</strong> Yeni betikler, testler ve bir dar sayısal kapının geçmesi genel İHA CFD hizmetini veya uzman ajanı doğrulamaz.</p><div class="flow"><span>Temsil ve kanıt</span><span>→ İterasyon</span><span>→ Bölgesel ağ</span><span>→ Üç ağ / uzak alan</span><span>→ Deney ve kapsam</span></div></section>
<section><h2>Kontrollü deney sonucu</h2><p>İlk çiftin geometri, fizik, başlangıç alanı ve config'i yalnız doğrusal iterasyon sınırında farklı. İki gerçek1000-adım koşusu: ek artık düşüşü <strong>{effect:.9f} log10</strong>; önceden seçilen0,3 etki ölçütü <strong>{"geçti" if pair["pair"]["effect_passed"] else "geçmedi"}</strong>. İç doğrusal toleransın karşılanması tek başına dış akış yakınsamasını düzeltmedi. Daha fazla sınır değeri taranmadı.</p><table><tr><th>Koşu</th><th>Adım</th><th>Süre [s]</th><th>log10 artık</th><th>CL</th><th>CD</th><th>271 Cp RMSE</th></tr>{rows}</table><p class="small">Süreler tek sırayla yapılan gerçek ölçümlerdir; donanım hız kıyası veya istatistiksel güven aralığı değildir. Katsayılar aynı yarım kanat referans alanı/veterindedir. NASA dosyaları ONERA deneyidir; bütün271 nokta ve14 kesit/yüzey grubu korundu.</p><img src="{url(Path("outputs/projects/proje-e9319baef1/plots/m6_linear_pair_20261024.png"))}">{feedback_text}</section>
<section><h2>Ağda neresi incelenmeli?</h2><p>Önceden seçilmiş lin10 hacim alanından Mach'ın yerel ikinci türevleri ve baskın değişim yönleri çıkarıldı. Kaynak yüze iki referans veterden yakın tetrahedral bölgede {curvature["region_candidates"]:,} hücre incelendi; {curvature["valid_fits"]:,} geçerli ve {curvature["invalid_fits"]:,} geçersiz şablon ayrı tutuldu. Üst yüzde1 eşiğinde {curvature["selected_cells"]:,} hücre inceleme önceliği aldı. Bu seçim deneyin beklenen şok konumunu kullanmıyor.</p><p>Bu, NASA'nın tam Lp uyarlama zincirinin yeniden üretimi değildir. Prizma sınır tabakası kapsanmıyor, yeni mesh üretilmedi. Gösterge ve yönler inceleme içindir; adjoint ağırlıklı CL/CD hata bandı değildir. Şokta düzgün ikinci derece yaklaşımın sınırı ve şablon hata ölçüsü CSV'de saklanır.</p><img src="{url(Path("outputs/projects/proje-e9319baef1/plots/m6_curvature_20261024.png"))}"><p>{link(Path("outputs/projects/proje-e9319baef1/data/reliability_20261024/curvature_cells.csv"),"Konum, yön, geçerlilik ve hata ölçüleri")} · {link(Path("outputs/projects/proje-e9319baef1/data/reliability_20261024/curvature_view.vtu"),"Gerçek 3B alan ve gösterge")}</p></section>
<section><h2>Yanlış kabulü önleyen kontroller</h2><p>{tests["tests"]} test grubu geçti. Değişmiş/eksik dosya, başka proje, bozuk zaman penceresi, NaN ve yuvarlamayla eşik atlama karşı örnekleri var. Kayıtlı geçti etiketi ham sonucun yerine kullanılamıyor. Analitik doğrusal/ikinci derece alan, dönmüş ince şablon, dejenere şablon ve m/mm dönüşümü de sınandı. Temel yazılım kontrolleri26/26 geçti.</p><table>{gate_rows}<tr><td>Tam bölgesel BL/iz/uç çözünürlüğü</td><td>açık</td></tr><tr><td>Üç sistematik ağ ve uzak alan</td><td>açık</td></tr><tr><td>Bütün deney kesitleri</td><td>geçmedi</td></tr><tr><td>Genel fizik yeterliliği</td><td>false</td></tr></table><p>{link(Path("outputs/projects/proje-e9319baef1/reports/reliability_audit.json"),"Yeniden hesaplanan denetim")} · {link(integritypath.relative_to(ROOT),"Mühür ve girdi bütünlüğü")} · {link(Path("outputs/reports/reliability_method_tests.json"),"Karşı örnek sonuçları")}</p></section>
<section><h2>Kullanım ve sıradaki iş</h2><p>Mühendislik Merkezi'nde <strong>NASA ONERA M6 CFD doğrulaması</strong> projesini seç. “Görevler ve çalışmalar” içindeki <strong>Kayıtlı sonuçların güvenilirliğini yeniden denetle</strong> seçeneği mühürleri ve ham geçmişi kontrol eder; CFD'yi tekrar çalıştırmaz. Yeni/başka projede kayıtlı sözleşme olmadan bu seçenek sonuç üretmez.</p><p>Sonraki öneri: <strong>{escape(audit["recommendation"]["action"])}</strong>. {escape(audit["recommendation"]["reason"])} Tam yönlü yeniden ağ üretimi ve bölgesel duyarlılık hâlâ uygulanacak iştir; bu turda bitmiş sayılmaz.</p><p>{link(docs,"Yöntem, kapsam ve yeniden üretim")} · {link(REPORT.relative_to(ROOT),"İlk çiftin tüm ölçümleri")}{(' · '+link(feedback_path.relative_to(ROOT),'CFL çiftinin tüm ölçümleri')) if feedback else ''}</p></section>
<section><h2>Araştırma kaynakları</h2><p>Yedi birincil kaynak URL, indirme zamanı ve SHA256 ile saklandı. Kurulu native pakette ayrık adjoint için _AD çalıştırılabilir dosyası yok. NASA refine ve tam adjoint uyarlaması bu turda kurulmuş/test edilmiş sayılmadı. Kendi katkımız, kaynaklı sayısal araçları koşullu deney seçimi ve kanıt denetimiyle birleştiren açık politikadır.</p><ul>{source_links}</ul></section></main></html>'''
        html=html.replace('<section><h2>Yanlış kabulü önleyen kontroller</h2>',curvature_extra+'<section><h2>Yanlış kabulü önleyen kontroller</h2>')
        html=html.replace(escape(audit['recommendation']['action']),escape(next_action))
        html=html.replace(escape(audit['recommendation']['reason']),'Açık sayısal kapıyı ayırt eden sonraki test gereklidir; desteklenmeyen aynı ayarın yeni değerleri taranmaz.')
        html=html.replace('İlk prototipte bazı yerel türevler şablon desteğinin dışındaki hücrelere taşındı;',
                          'İlk prototip bazı ince/çok ölçekli şablonlarda çok büyük değerler üretti;')
        html=html.replace('hücre maskeli kaldı;', 'hücre maskeli kaldı; maskeli bölgeler düşük hatalı veya güvenli sayılmıyor;')
        return html
    targets=[ROOT/'outputs/reports/guvenilirlik_gelistirme_20261025.html',PROJECT/'reports/guvenilirlik_gelistirme_20261025.html']
    for target in targets:target.write_text(render(target),encoding='utf-8')
    evidence=[REPORT,feedback_path,PROJECT/'reports/m6_curvature_20261024.json',PROJECT/'reports/m6_curvature_v2_20261025.json',integritypath,
              PROJECT/'reports/reliability_audit.json',ROOT/'outputs/reports/reliability_method_tests.json',*targets]
    task.update(status='tamamlandı',finished_utc=now(),bounded_development_iteration_completed=True,
                minimum_physical_qualification_passed=False,
                evidence=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in evidence if p.exists()],
                blocked_by=['Genel fizik kabulü: bölgesel ağ, üç sistematik ağ, uzak alan ve deney kapıları açık.'])
    if feedback and not feedback['results']['adaptive']['iterative_gate']['passed']:
        task['blocked_by'].insert(0,'M6 yoğunluk artığı mevcut iteratif eşiği geçmedi.')
    save(TASK,task)
    print(json.dumps({'report':str(targets[0]),'native_runs':integrity['new_native_runs'],'task_status':task['status'],'physical_qualification':False},ensure_ascii=False))


if __name__=='__main__':main()
