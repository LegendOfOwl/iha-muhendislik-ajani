# Açık sorunlar, önem sırası ve derin araştırma

28 Ekim2026 · Son deney kanıtı:v0.17.0 · Yeni CFD/derleme/kurulum:0.

28 Ekim2026:29 uzmanlık-alt başlığı, yinelenmeler birleştirilerek26 açık başlıkta önceliklendirildi (P0=7,P1=12,P2=6,P3=1). 39 farklı birincil kaynak adresi; 50 benzersiz yerel kanıt dosyasının SHA256 değeri yeniden kontrol edildi. En kritik sıra gerçek iç artık/dış yakınsama, bölgesel ağ, geometri eşdeğerliği, sistematik ağ/uzak alan ve deney kabulüdür. Gerçek İHA girdileri eksik; genel uçtan uca ajan ve görülmemiş görevlerde iyileşme kanıtı yok. Araştırmadan pasif b−Aδ ölçümü ve bağımsız wall-distance denetimi somut adaylar olarak çıktı; bunlar henüz uygulanmadı. Yeni CFD, kaynak derlemesi veya kurulum yapılmadı; mevcut fizik/RAE/M6/İHA/LLM kabulü değişmedi.

## Önceliklerin anlamı

P0, ilgili kapsamda mühendislik kabulünü veya gerçek tasarımın başlamasını engeller. P1, güvenilir genel iş akışını tamamlamak için gereklidir. P2, kapsam/entegrasyon ve yöntem geliştirmesidir. P3, ikincil kurulum seçeneğidir. Sıra bir risk olasılığı hesabı değildir; karar etkisi, bağımlılık ve bilgi kazanımı/maliyet değerlendirmesidir. U07’nin verileri gerçek İHA’yı bekletir; diğer bağımsız araştırmaları durdurmaz. Hipotez ve eksik yetenek, kanıtlanmış yazılım hatası diye etiketlenmedi.

## Kayıtlardaki bütün açık başlıklar

| Sıra | Öncelik | Başlık | Tür |
|---|---|---|---|
| 1 / U01 | P0 | İnce ağın sayısal yakınsaması ve gerçek iç artık ölçümü | Kabul açık |
| 2 / U02 | P0 | Konuma göre BL/LE/TE/iz/uç çözünürlüğü ve bütün Cf eğrisi | Çözünürlük açık |
| 3 / U03 | P0 | Kaynak CAD, mesh, VLM ve OAS temsil eşdeğerliği | Eşdeğerlik açık |
| 4 / U04 | P0 | Üç yakınsamış sistematik ağ ve geçerli GCI | Kabul açık |
| 5 / U05 | P0 | Uzak alan ve sınır etkisinin bağımsız ölçülmesi | Duyarlılık eksik |
| 6 / U06 | P0 | RAE2822/M6 deney kıyası ve fiziksel koşul eşlemesi | Kabul açık |
| 7 / U07 | P0 | Gerçek görev, kütle ve kabul girdileri | Girdi eksik |
| 8 / U08 | P1 | Keyfi kullanıcı CAD’inden kaliteli hacim ağı | Yetenek sınanmadı |
| 9 / U09 | P1 | Bütün uçak performansı, trim, kararlılık ve3B kapsam | Yetenek sınanmadı |
| 10 / U10 | P1 | Yeni projede araştırmadan sıralamaya uçtan uca ajan | Yetenek sınanmadı |
| 11 / U11 | P1 | Talimat/hafıza iyileşmesinin görülmemiş görevlerde ölçülmesi | Davranış ölçülmedi |
| 12 / U12 | P1 | Belirsizlik bütçesi ve savunulabilir aday sıralaması | Belirsizlik eksik |
| 13 / U13 | P1 | Karmaşık kanatta VLM sürükleme panel kabulü | Kabul açık |
| 14 / U14 | P1 | Yeni karmaşık CAD ailelerinde ölçü ve topoloji güvencesi | Yetenek sınanmadı |
| 15 / U15 | P1 | Ölçülü teknik resim, montaj ve üretime aktarım kapsamı | Yetenek sınanmadı |
| 16 / U16 | P1 | Gerçek kanada özel FEM ve aeroelastik optimizasyon | Yetenek sınanmadı |
| 17 / U17 | P1 | Güncel iç sistemle eşleşen artık konum haritası | Ölçüm eksik |
| 18 / U18 | P1 | Doygun Krylov sayımı ve tek çift süre ölçüsü | Ölçüt sınırlı |
| 19 / U19 | P1 | Duvar mesafesi hesabının bağımsız denetimi | Sınanmamış hipotez |
| 20 / U20 | P2 | Hessian’dan tam anizotropik/adjoint ağ döngüsüne geçiş | Prototip |
| 21 / U21 | P2 | Fusion motoru, hub ve lisans yetkisi | Motor sınanmadı |
| 22 / U22 | P2 | OpenVSP Python→OAS köprüsü | Köprü eksik |
| 23 / U23 | P2 | Küçük CAD modellerinin geometri/topoloji güvenilirliği | Geometri redleri |
| 24 / U24 | P2 | Zero-to-CAD özgün çalışma yolunun ayrıştırılması | Referans yol sınanmadı |
| 25 / U25 | P2 | EXE dağıtımı ve yeni ortamda gerçek görev kullanımı | Taşınabilirlik sınanmadı |
| 26 / U26 | P3 | İkinci yerel RANS çözücüsü / OpenFOAM kurulumu | İkincil seçenek |

## Araştırmanın somut katkıları

### İç artık: ölçülecek nicelik eksik

Jadoui vd. M6 adjoint örneklerinde gerçek ve least-squares artıklarını ayrı izliyor. Bizim primal, ayrık flow/SA sistemimiz aynı sistem değil. Yerel veri, raporlanan iç akış oranının yaklaşık45kat iyileşmesini dış yoğunluk ilerlemesine bağlayamıyor; ilk öneri yeni çözücü değil bağımsız b−Aδ ölçümü. [Comparative study of inner-outer Krylov solvers for linear systems in structured and high-order unstructured CFD problems](https://arxiv.org/html/2404.17870v1), [Pinned SU2v8.5.0 source: FGMRES, implicit update and Newton-Krylov](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/Common/src/linear_algebra/CSysSolve.cpp).

### Duvar mesafesi: ucuz ve ayrı bir kontrol adayı

Park vd.2018, anizotropik M6 ağında yanlış mesafe varsayımının akışı etkileyebildiğini gösteriyor. Bu, SU2’mizde kanıtlanmış neden değil. Önce akış çalıştırmadan geometriye bağlı bağımsız mesafe karşılaştırması yapmak anlamlı. [Park vd.,2018, BölümVI ve Şekil11–13](https://ntrs.nasa.gov/api/citations/20180006169/downloads/20180006169.pdf?attachment=true).

### Önceden var olan düzeltmeyi tekrar eklememek

Derlenen v8.5.0 kaynağı zaten iki geçişli Classical Gram–Schmidt kullanıyor. Fonksiyon adından eski Modified Gram–Schmidt uygulaması varsaymak yanlış öneri üretebilirdi. Önbellekli web raw görünümü yerine hashli yerel kaynak ve pinned GitHub API teyidi kullanıldı. [Pinned SU2v8.5.0 source: FGMRES, implicit update and Newton-Krylov](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/Common/src/linear_algebra/CSysSolve.cpp), [Comparative study of inner-outer Krylov solvers for linear systems in structured and high-order unstructured CFD problems](https://arxiv.org/html/2404.17870v1).

### CAD ve ajan: görünüş başarısı ile görev kabulü ayrı

Text2CAD-Bench daha karmaşık işlem/topoloji değerlendirmesini; AstaBench araç ve bütçe denetimli ajan değerlendirmesini ele alıyor. Bizim için çıkarım, daha uzun talimattan önce görev bazlı ölçü/topoloji hakemi, ayrı yeni görevler ve aynı koşullu önce/sonra deneyidir. [Text2CAD-Bench: A Benchmark for LLM-based Text-to-Parametric CAD Generation](https://arxiv.org/html/2605.18430v1), [AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite](https://arxiv.org/abs/2510.21652v2), [Search-Time Contamination in Deep Research Agents](https://arxiv.org/abs/2606.05241v1).

### Uyarlama ve yeni modeller: daha sonra, kanıtlı ihtiyaçla

Hessian prototipi tam solve–remesh döngüsü değildir. Yeni immersed-boundary veya surrogate–Newton çalışmaları farklı altyapı gerektiriyor. Yakınsamaya yakın mevcut seed için yeni bir sinir ağı başlangıcı, terminal yakınsama sorununu kendiliğinden çözmez; bu yerel kapsam çıkarımıdır. [Balan vd.,2019](https://ntrs.nasa.gov/citations/20200002636), [Núñez-de la Rosa vd.,2026,ön baskı](https://arxiv.org/html/2607.27580v1), [Reliable and efficient steady CFD from surrogate predictions through Newton-Krylov correction](https://arxiv.org/abs/2608.04400).

### Kurulum sayısı başarı ölçütü değil

NASA’nın tarihsel Vision2030 çalışması geometri/ağ ve belirsizlik yönetimini darboğaz olarak ele alıyor. Bizde öncelik aynı adayın kaynak–geometri–mesh–çözüm–kabul zincirini bağlamak. OpenFOAM farklı yöntem kıyası sunabilir; resmî Windows yolu WSL2 ve ayrıca kaynak bütçesi ister. [CFD Vision2030 Study, NASA/CR-2014-218178](https://ntrs.nasa.gov/api/citations/20140003093/downloads/20140003093.pdf), [OpenFOAM Foundation Windows documentation](https://openfoam.org/download/windows/).

## Hangi sonucu hangi vaka için kullanıyoruz?

Düz plakada26Ekim kaynak ailesi ve korunmuş fine3999 rolü esastır; v17 kaynak-sabiti kolları ayrı tanıdır. RAE’de en yeni v3 kapanışı genel kabulü geçmedi; v2’nin dar başarılı ekranları geçmiş kanıttır. M6’da25Ekim TMRsharp üç-ağ ailesi zaten üretildi, üçü de gerekli iteratif kapıyı geçmedi. Eski blunt M6’nın y+ ve Cp iyileşmesi bu yeni aileye taşınmadı. Kaynak CFD kıyası deneysel doğrulama sayılmadı. Ayrıntılar ve dosya mühürleri alt raporlardadır.

## Sorunları kapatmak için yürütme sırası

- **A — Ölçümü önce doğrula (U01):** Küçük bilinen lineer sistemler, sıfır RHS ve zaten çözülmüş başlangıç; sonra pasif ölçüm patch’inin kaynak32 yeniden üretimi. Matris, b, δ ve fizik durumunun değişmediği kanıtlanmalı.
- **B — Geometriyi paralel denetle (U03,U19):** Gerçek wall marker ve kaynak yolu üzerinden nokta–segment/üçgen/sınır mesafesi. Yanlışlık yoksa hipotez kapanır; sonuç kötü diye mesafe değiştirilmez.
- **C — Tek gerçek iç sistemde tanı (U01,U17,U18):** Aynı ilk durum ve A,b kimlikleriyle32/256; gerçek artık, kestirim, δ ve uygulanan ΔU, yerel relaxation/CFL, operatör maliyetleri. Farklı A,b sabit-sistem kıyası sayılmaz.
- **D — Sonuca göre tek mekanizma seç (U01):** Gerçek iç artık yeterliyse dış güncelleme/bağlaşım araştırılır; yetersizse önkoşullandırıcı/operatör tutarlılığı incelenir. Gerçek/kestirim farkı yokken ortogonalleştirme eklenmez. Her kol önceden bütçelenir; otomatik tarama yok.
- **E — Önce kaynak düz plaka ailesi (U02,U04,U05):** Korunan fine rolüyle bütün sayısal kapılar; model/BC/viskozite eşleşmesi; bütün kaynak noktaları ve GCI uygunluğu. Bir tanı kolu eski üç-ağ ailesine sessizce eklenmez.
- **F — RAE, ardından M6 (U06):** RAE’de aynı C1 temsil, normal/TE/iz ve ayrı uzak alan; M6’da TMRsharp sayısal aile ile eski blunt/deney geometrisi ayrımı. Her kapsam kendi koşul ve deney sözleşmesiyle kapanır.
- **G — Görülmemiş yeni proje (U08,U10,U11):** Aynı izlenebilir adayda yeni CAD/mesh/çözüm/karar zinciri; ayrı görevlerde sabit araç/model/bütçeyle davranış ölçümü. Geliştirmede görülen vaka yeni kör test sayılmaz.
- **H — Gerçek İHA kararı (U07,U09,U12,U16):** Kullanıcının güncel gereksinim/kütle girdileriyle güç, enerji, CG, trim, yapı ve görev uygunluğu. Kritik kabul açıkken nihai kazanan veya uygun uçak sonucu yok.

Bu sıra yeni koşu yetkilendirmesinin veya native sözleşmenin yerine geçmez. Önerilen sayısal tolerans/bütçe, yöntem seçildiğinde çalışmadan önce kaydedilir; mevcut başarısız eşikler korunur.

## Her başlık için kanıt, test ve kapanış

### U01 · P0 · İnce ağın sayısal yakınsaması ve gerçek iç artık ölçümü

**Gözlem:** Düz plaka ailesinde ince rolün yoğunluk kapısı açık; RAE ve TMRsharp M6 da genel kabulü geçmedi. v17 üç tanı kolunda tüm200 flow/SA çözümü40 tavanda. LinSolRes, bağımsız b−Aδ normu değil.

**Etkisi:** İterasyon hatası sınırlanmadan ağ ve deney farkının ne kadarının fiziksel olduğu ayrılamaz.

**Bir sonraki test:** Assembled FGMRES çağrısında gerçek A,b,x0,δ,norm0 kimliğini kaydet; scratch vektörle mutlak/bağıl/bileşen gerçek artığını pasif ölç. Analitik matris kontrolleri ve değişmeyen kaynak32 yeniden üretiminden sonra aynı ilk-adım A,b ile kısa32/256 kıyası yap.

**Kapanış:** Ölçüm doğruluğu ve çözümü değiştirmediği ayrı geçmeli; sonra önceden seçilmiş fine ve bütün zorunlu dış kapılar aynı vaka/ailede geçmeli. Yeni ölçüm veya tek bileşen iyileşmesi fizik kabulü değildir.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** N01, N02, VM01.

**Kaynak:** [Pinned SU2v8.5.0 source: FGMRES, implicit update and Newton-Krylov](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/Common/src/linear_algebra/CSysSolve.cpp), [Choosing the Forcing Terms in an Inexact Newton Method](https://epubs.siam.org/doi/10.1137/0917003), [Comparative study of inner-outer Krylov solvers for linear systems in structured and high-order unstructured CFD problems](https://arxiv.org/html/2404.17870v1).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [cfd_ic_cozum_ve_uc_ag_20261026.md](cfd_ic_cozum_ve_uc_ag_20261026.md), [cfd_kalan_artik_20261026.md](cfd_kalan_artik_20261026.md), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html), [su2_kaynak_karsilastirma_20261027.json](su2_kaynak_karsilastirma_20261027.json), [method_design.json](../../work/su2_build_20261027/method_design.json), [independent_review.json](../../work/su2_build_resume_20261027/independent_review.json).

### U02 · P0 · Konuma göre BL/LE/TE/iz/uç çözünürlüğü ve bütün Cf eğrisi

**Gözlem:** y+ bazı kollarda geçti; RAE normal blok değişimi kuvvetleri yaklaşık%4 etkiledi. Düz plaka kabul penceresi Cf normu ile bütün447 noktanın normu farklı. M6 uç/iz ve katman geçişi birlikte kapanmadı.

**Etkisi:** Toplam hücre veya ilk y+ iyi olsa da gerekli akış gradyanı çözülmemiş olabilir.

**Bir sonraki test:** Gerçek normal/teğetsel aralık, son segment büyümesi, toplam katman ve hız/μt profillerini çıkar; yalnız bir bölgesel dağılım/geçişi değiştiren eş kontrol kur. LE dahil bütün kaynak noktalarını koru.

**Kapanış:** Yakınsamış eş çözümlerde ön kayıtlı profil/kuvvet duyarlılığı ve bölgesel mesh kapıları birlikte geçmeli; kötü noktalar puandan çıkarılmamalı.

**Bağımlı olduğu işler:** U01. **Ayrıntılı yerel kayıt:** VM02, N05.

**Kaynak:** [SA Expected Results -2D Zero Pressure Gradient Flat Plate](https://tmbwg.github.io/turbmodels/flatplate_sa.html), [TMR y+ çalışması](https://tmbwg.github.io/turbmodels/flatplate_val_ypluseffect.html).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [cfd_ic_cozum_ve_uc_ag_20261026.md](cfd_ic_cozum_ve_uc_ag_20261026.md), [cfd_kalan_artik_20261026.md](cfd_kalan_artik_20261026.md), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html), [su2_kaynak_karsilastirma_20261027.json](su2_kaynak_karsilastirma_20261027.json), [method_design.json](../../work/su2_build_20261027/method_design.json), [independent_review.json](../../work/su2_build_resume_20261027/independent_review.json).

### U03 · P0 · Kaynak CAD, mesh, VLM ve OAS temsil eşdeğerliği

**Gözlem:** Aynı parametreler farklı interpolasyonlar üretiyor. TMR M6 sınır-yüzeyi örneklerinin max uzaklığı yaklaşık9,78e−4 kök veter; bu tam Hausdorff değil. Önceki solid mesafe denetimi superseded.

**Etkisi:** Farklı geometriyi tek aday veya tek sistematik ağ ailesi saymak karşılaştırmayı bozabilir.

**Bir sonraki test:** Birim/eksen/TE/LE/twist eksenini ve hangi yüzeyin solid/camber/deforme yüzey olduğunu tanımla; iki yönlü boundary mesafesi, normal ve ara istasyon kontrolleriyle ortak aday kimliğine bağla.

**Kapanış:** İlan edilmiş hata bütçesi bütün zorunlu örneklerde geçmeli; kasıtlı ölçek/twist sapması reddedilmeli. Yeni geometri yeni temsil sürümü olmalı.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** VM03, CA02.

**Kaynak:** [OpenVSP API 3.55.0 resmi belgeleri](https://openvsp.org/api_docs/latest/index.html), [OpenAeroStruct 2.12: OpenVSP-generated Mesh Example](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html), [OCCT BRepCheck_Analyzer referansı](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [TMR vaka tanımı](https://tmbwg.github.io/turbmodels/onerawingnumerics_val.html).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [complex_vlm_force_audit.json](complex_vlm_force_audit.json), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [step_bore_measurements.json](step_bore_measurements.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html), [parametric_wing.py](../../work/geometry/parametric_wing.py), [run_complex_vlm.py](../../work/qualification/run_complex_vlm.py).

### U04 · P0 · Üç yakınsamış sistematik ağ ve geçerli GCI

**Gözlem:** Birden fazla gerçek üç-ağ ailesi var; fakat gerekli iteratif/asimptotik şartlar birlikte sağlanmadı. Özellikle TMRsharp M6 üç ağı zaten üretildi, eksik olan üç başarılı çözüm. GCI null.

**Etkisi:** Sadece üç sonuç veya küçük orta–ince fark güvenilir ayrıklaştırma hata bandı vermez.

**Bir sonraki test:** Aynı geometri/dış sınır/fizikte yönsel inceltme oranlarını kaydet; her seviyeyi aynı QoI ve iterasyon kapılarıyla değerlendir. LE/şok tekilliklerini ayrı ele al.

**Kapanış:** Kayıtlı ağ ailesi için iteratif belirsizlik sınırlı ve gözlenen mertebe/asimptotik davranış uygun olmalı; uygunsuz nicelikte GCI açıklamalı null kalmalı.

**Bağımlı olduğu işler:** U01, U02, U03. **Ayrıntılı yerel kayıt:** VM04.

**Kaynak:** [NPARC mekânsal yakınsama](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html), [NASA NPARC CFD verification/validation overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html).

### U05 · P0 · Uzak alan ve sınır etkisinin bağımsız ölçülmesi

**Gözlem:** RAE400c ağı hazırlanmış fakat kabul edilmiş çözümü yok; TMR M6 kaynak100c olması tek başına duyarlılık deneyi değil. Eski farklı dış alanlar salt mesh yakınsaması sayılmadı.

**Etkisi:** Dış sınır etkisi ağ ve model hatasıyla karışabilir.

**Bir sonraki test:** Kaynak gövde ve yakın ağı koruyup yalnız dış bölgeyi değiştiren eş çift çalıştır; aynı matched alan/geçmiş ve kuvvet pencerelerini kullan.

**Kapanış:** İki çözüm de kendi sayısal kapısını geçmeli ve ön kayıtlı QoI sınır duyarlılığı kapanmalı; alanı olmayan hazır ağın sonuçları null kalmalı.

**Bağımlı olduğu işler:** U01, U03. **Ayrıntılı yerel kayıt:** VM05.

**Kaynak:** [NPARC mekânsal yakınsama](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html), [NASA NPARC CFD verification/validation overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html).

### U06 · P0 · RAE2822/M6 deney kıyası ve fiziksel koşul eşlemesi

**Gözlem:** RAE v2 fine CpRMSE≈0,067>0,03; v3 genel kabulü false. Daha yeni TMRsharp M6 kaynak ailesinin hiçbir iteratif kapısı geçmedi. Eski blunt M6 iyileşmeleri ayrı vaka. Model/BC/ölçek ve Sutherland özdeşliği her kodda tam kanıtlanmış değil.

**Etkisi:** Denklemlerin çözülmesi, deneydeki geometri/akış/modelin doğru temsilini kendiliğinden göstermez.

**Bir sonraki test:** Sharp/blunt, root/MAC Reynolds, nominal/düzeltilmiş koşul, trip, SA varyantı, viskozite yasası ve Cp işaretini kaynak matrisiyle eşleştir. Sonra bütün deney noktaları/grupları ve bağımsız kuvvet zinciriyle değerlendir.

**Kapanış:** Vakaya önceden bağlanmış sayısal, geometri, deney ve kapsam kapıları birlikte geçmeli. Koşul/puan/eşik sonuç tutturmak için değiştirilmemeli.

**Bağımlı olduğu işler:** U01, U02, U03, U04, U05. **Ayrıntılı yerel kayıt:** VM06.

**Kaynak:** [TMR vaka tanımı](https://tmbwg.github.io/turbmodels/onerawingnumerics_val.html), [WIND Study4](https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html), [SA Expected Results -2D Zero Pressure Gradient Flat Plate](https://tmbwg.github.io/turbmodels/flatplate_sa.html), [NASA NPARC CFD verification/validation overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html).

### U07 · P0 · Gerçek görev, kütle ve kabul girdileri

**Gözlem:** Kalıcı gerçek İHA mission kaydında7 girdi null; altı bileşen kütlesi bilinmiyor;8 kavramsal adım bekliyor. Bunlar yazılım hatası değildir.

**Etkisi:** Gerçek uçağın güç/enerji/CG/trim veya uygunluğu hesaplanamaz. Bu eksik benchmark araştırmasını engellemez.

**Bir sonraki test:** Kullanıcı gereksinimlerini ve kaynaklı bileşen verilerini değer/aralık, SI birim, kaynak ve geçerlilikle kaydet; çelişki/eksik için kabul matrisi kur.

**Kapanış:** Bağlı hesaplar için kritik girdiler onaylı olmalı; bilinmeyenler sıfır olmamalı. Her aşama kendi kanıtıyla kapanmalı.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** CA01.

**Kaynak:** [ideas-um/openaerostruct-llm-agent](https://github.com/ideas-um/openaerostruct-llm-agent), [NASA-STD-7009B, 2024](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf).

**Yerel kanıt:** [conceptual_steps.json](../data/project/conceptual_steps.json), [mass_budget.json](../data/project/mass_budget.json), [mission.json](../data/project/mission.json).

### U08 · P1 · Keyfi kullanıcı CAD’inden kaliteli hacim ağı

**Gözlem:** Kaynak benchmark ve tanımlı profil/kanat aileleri için betikler var; keyfi yeni parçaya genel RANS ağı ve bütün bölgesel kontroller doğrulanmadı.

**Etkisi:** Hazır örneği çalıştırmak yeni kullanıcı geometrisine ait sonuç üretmez.

**Bir sonraki test:** Önce sınırlı bir yeni geometri ailesi seç; watertight CAD/duvar/sınır etiketleri, bölgesel mesh sözleşmesi, kalite retleri ve aynı geometriyle üç seviye üretimini sınayacak vaka kur.

**Kapanış:** Yeni geometri kendi kimliğiyle CAD→mesh→solver→kabul zincirini geçmeli; destek dışı geometri doğru biçimde reddedilmeli.

**Bağımlı olduğu işler:** U02, U03, U04. **Ayrıntılı yerel kayıt:** CA04.

**Kaynak:** [CFD Vision2030 Study, NASA/CR-2014-218178](https://ntrs.nasa.gov/api/citations/20140003093/downloads/20140003093.pdf), [OCCT BRepCheck_Analyzer referansı](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [Park vd.,2018, BölümVI ve Şekil11–13](https://ntrs.nasa.gov/api/citations/20180006169/downloads/20180006169.pdf?attachment=true).

**Yerel kanıt:** [workflow_readiness.json](workflow_readiness.json), [project.py](../../work/agent/project.py), [projects.py](../../work/agent/projects.py), [projects_desk.ps1](../../work/agent/projects_desk.ps1), [rank_candidates.py](../../work/workflow/rank_candidates.py).

### U09 · P1 · Bütün uçak performansı, trim, kararlılık ve3B kapsam

**Gözlem:** 2B profil, ayrı kanat VLM/OAS ve M6 testleri var; gerçek gövde/kuyruk/itki etkileşimi ile sürekli güç, enerji, CG ve trim birlikte doğrulanmadı.

**Etkisi:** Bir profil/kanat sonucu bütün uçağın görev gereksinimlerini kapatamaz.

**Bir sonraki test:** Aynı gerçek adayda bileşen kütleleri, güç/enerji modeli, CG/trim ve uygun aero/yapı yöntemini bağla; dahil edilmeyen parçaları ve model rejimini kaydet.

**Kapanış:** Gereksinimlerin her biri sağlandı/sağlanmadı/henüz değerlendirilemedi ve kanıt taşımalı; bileşen sonucu uçak sonucu diye aktarılmamalı.

**Bağımlı olduğu işler:** U07, U03. **Ayrıntılı yerel kayıt:** CA01, CA07.

**Kaynak:** [ideas-um/openaerostruct-llm-agent](https://github.com/ideas-um/openaerostruct-llm-agent), [OpenAeroStruct 2.12.0 resmi genel belgeleri](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/), [NASA-STD-7009B, 2024](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf).

**Yerel kanıt:** [conceptual_steps.json](../data/project/conceptual_steps.json), [mass_budget.json](../data/project/mass_budget.json), [mission.json](../data/project/mission.json), [fem_results.json](fem_results.json), [openaerostruct_examples.json](openaerostruct_examples.json), [openaerostruct_install.json](../../work/setup/openaerostruct_install.json).

### U10 · P1 · Yeni projede araştırmadan sıralamaya uçtan uca ajan

**Gözlem:** full_generic_pipeline_verified=false. GUI/EXE ve görev kaydı çalışıyor; yeni ayrı CLI oturumu açılması, yeni projede bütün aşamaların özerk tamamlandığını kanıtlamıyor.

**Etkisi:** Kullanıcının istediği tek görevde araştırma→CAD→analiz→CFD→sıralama→rapor zinciri henüz gösterilmedi.

**Bir sonraki test:** Görülmemiş sınırlı bir proje, aday bütçesi ve kabul sözleşmesiyle gerçekten yeni oturum başlat; eksik veri, araç hatası ve destek dışı CAD dallarını da izle.

**Kapanış:** Aynı project/candidate/geometry/condition kimliği bütün aşamalarda eşleşmeli; final sıra yalnız bütün gerekli kapıları geçen adaylarla ve taranmayan alan açıklamasıyla oluşmalı.

**Bağımlı olduğu işler:** U03, U08, U11. **Ayrıntılı yerel kayıt:** CA04.

**Kaynak:** [AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite](https://arxiv.org/abs/2510.21652v2), [From Reproduction to Replication: Evaluating Research Agents with Progressive Code Masking](https://arxiv.org/abs/2506.19724), [ideas-um/openaerostruct-llm-agent](https://github.com/ideas-um/openaerostruct-llm-agent).

**Yerel kanıt:** [workflow_readiness.json](workflow_readiness.json), [project.py](../../work/agent/project.py), [projects.py](../../work/agent/projects.py), [projects_desk.ps1](../../work/agent/projects_desk.ps1), [rank_candidates.py](../../work/workflow/rank_candidates.py).

### U11 · P1 · Talimat/hafıza iyileşmesinin görülmemiş görevlerde ölçülmesi

**Gözlem:** Talimat sürümleri, yanlış-kabul korumaları ve kod karşı örnekleri var; aynı bütçe/araçlarla bağımsız önce/sonra görülmemiş mühendislik değerlendirmesi yok.

**Etkisi:** Kod kontrolü veya aynı benchmarkın tekrar düzeltilmesi uzman ajan davranışı kanıtı değildir.

**Bir sonraki test:** Yeni geometri/koşulları geliştirme vakalarından ayır; sabit araç/model/bütçede iki talimat sürümünü karşılaştır. Bağımsız sayısal/ölçü hakemi, tüm başarısızlıklar ve kaynak-cevap sızıntısı kaydı olsun.

**Kapanış:** Görev düzeyinde doğruluk, yanlış kabul, maliyet ve tekrarlar raporlanmalı; ortak diskteki rol ayrımı güvenli körlük diye sunulmamalı. Tek başarı genel oran değildir.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** CA03.

**Kaynak:** [AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite](https://arxiv.org/abs/2510.21652v2), [Search-Time Contamination in Deep Research Agents](https://arxiv.org/abs/2606.05241v1), [From Reproduction to Replication: Evaluating Research Agents with Progressive Code Masking](https://arxiv.org/abs/2506.19724).

**Yerel kanıt:** [learning_loop.md](../../.agents/skills/iha-muhendislik/references/learning_loop.md), [qualification_plan_v1.json](../data/agent_learning/qualification_plan_v1.json), [protocol_v1.json](../../work/reliability/protocol_v1.json).

### U12 · P1 · Belirsizlik bütçesi ve savunulabilir aday sıralaması

**Gözlem:** Kanıt/koşul eşleştirmesi ve başarısız CFD’de kazananı engelleme çalışıyor. Kayıtlı adaylarda final_winner=null; sayısal/model/girdi belirsizliğiyle birleşik gerçek tasarım sıralaması yok.

**Etkisi:** İki küçük fark belirsizlik içindeyse tek kazananı savunmak mümkün olmayabilir.

**Bir sonraki test:** Önce tek QoI için girdi, geometri, iterasyon, mesh, BC/model ve deney belirsizliklerini ayrı kur; bağımlılıkları belirt. Sonra aynı sert kısıtlarda duyarlılık/robustlukla adayları kıyasla.

**Kapanış:** Belirsizlik kullanım amacına göre yeterli olmalı; eksik model hatası sıfır sayılmamalı. Sıralama ayrışmıyorsa sonuç eşdeğer/koşullu kalmalı.

**Bağımlı olduğu işler:** U04, U05, U06, U07. **Ayrıntılı yerel kayıt:** Ana karar/iş akışı kayıtları.

**Kaynak:** [NASA NPARC CFD verification/validation overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html), [NASA-STD-7009B, 2024](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf), [CFD Vision2030 Study, NASA/CR-2014-218178](https://ntrs.nasa.gov/api/citations/20140003093/downloads/20140003093.pdf).

**Yerel kanıt:** [candidate_comparison.json](candidate_comparison.json), [rank_candidates.py](../../work/workflow/rank_candidates.py).

### U13 · P1 · Karmaşık kanatta VLM sürükleme panel kabulü

**Gözlem:** Yüzey CDi panel farkı yaklaşık%17–18,46 ile kayıtlı kapı açık. İz CDiw daha kararlı; iki nicelik farklı kestirimlerdir ve uygun sütunu seçerek eski kabul kapatılamaz.

**Etkisi:** CL’nin daha kararlı olması toplam sürükleme ve aday L/D sıralamasını doğrulamaz.

**Bir sonraki test:** Sref/bref/cref, analiz kümesi ve aynı kanat temsiliyle yüzey/iz kuvvetlerini ayrı izleyen panel/iz aileleri kur; kaynak tanımı ve bağımsız uygun referansı kaydet.

**Kapanış:** Başlangıçta seçilmiş nicelikler kendi kapılarını geçmeli; sürtünme/stall/ayrılma gibi model dışı fizik için VLM kabulü kullanılmamalı.

**Bağımlı olduğu işler:** U03. **Ayrıntılı yerel kayıt:** CA05.

**Kaynak:** [OpenVSP resmi VSPAERO Verification and Validation Studies](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/python_scripts/report.md), [OpenVSP geliştiricisi Rob McDonald'ın CDi/CDiw tanım açıklaması](https://groups.google.com/g/openvsp/c/7Bl7y1nGl1Q/m/J4QOlpNJBQAJ).

**Yerel kanıt:** [complex_vlm_force_audit.json](complex_vlm_force_audit.json), [run_complex_vlm.py](../../work/qualification/run_complex_vlm.py).

### U14 · P1 · Yeni karmaşık CAD ailelerinde ölçü ve topoloji güvencesi

**Gözlem:** Tanımlı kanat/nervür ve3 NIST kaynak parçada ölçülü işlemler geçti. Bunlar her yeni loft/sweep/shell/çoklu delik veya kaynak çizimden yeniden kurma görevinin kabulü değildir.

**Etkisi:** Çalışan program ve geçerli katı, tasarım niyetinin veya bütün ölçülerin doğru olduğunu göstermeyebilir.

**Bir sonraki test:** Karmaşıklık basamaklı yeni kaynak parçalarda feature/parametre değişimi ve STEP geri okuması; eksen/merkez/bağlantı/topoloji/kalınlık kontrolleriyle negatif örnekler çalıştır.

**Kapanış:** Göreve özgü bütün ölçü/topoloji kuralları ve düzenleme sonrası aynı kurallar geçmeli. Hacim/bbox/probe tek başına tam şekil kanıtı olmamalı.

**Bağımlı olduğu işler:** U03. **Ayrıntılı yerel kayıt:** CA06.

**Kaynak:** [OCCT BRepCheck_Analyzer referansı](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [Text2CAD-Bench: A Benchmark for LLM-based Text-to-Parametric CAD Generation](https://arxiv.org/html/2605.18430v1).

**Yerel kanıt:** [PROJECT_STATE.md](../../PROJECT_STATE.md), [engineering_extension_quality.json](engineering_extension_quality.json), [step_bore_measurements.json](step_bore_measurements.json), [parametric_wing.py](../../work/geometry/parametric_wing.py).

### U15 · P1 · Ölçülü teknik resim, montaj ve üretime aktarım kapsamı

**Gözlem:** Kaynak PDF/CAD işlemleri ve bazı dışa aktarımlar var; keyfi montajda bağlantılar, çakışma, tam ölçü zinciri ve üretim toleranslarıyla genel teknik resim zinciri gösterilmedi.

**Etkisi:** Güzel3B görüntü imalat veya montaj uygunluğu yerine geçmez.

**Bir sonraki test:** Bir gerçek montaj ailesinde parça/eklem/çakışma kontrolleri ve gerekli ölçüleri taşıyan resim üret; CAD parametre değişince resmin güncellendiğini geri ölç.

**Kapanış:** Önceden tanımlanmış montaj/ölçü ve çıktı sözleşmesi geçmeli; resim bütün gerekli iç özellikleri ve birimleri göstermeli.

**Bağımlı olduğu işler:** U14. **Ayrıntılı yerel kayıt:** CA08.

**Kaynak:** [Text2CAD-Bench: A Benchmark for LLM-based Text-to-Parametric CAD Generation](https://arxiv.org/html/2605.18430v1), [Autodesk Fusion Compute MCP: Public Beta](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/).

**Yerel kanıt:** [PROJECT_STATE.md](../../PROJECT_STATE.md), [fem_results.json](fem_results.json), [step_bore_measurements.json](step_bore_measurements.json), [parametric_wing.py](../../work/geometry/parametric_wing.py).

### U16 · P1 · Gerçek kanada özel FEM ve aeroelastik optimizasyon

**Gözlem:** CAD→Gmsh→CalculiX örneği ve iki OAS kaynak optimizasyonu/türev kontrolü geçti. Gerçek İHA malzeme, yük, bağlantı/mesh, kompozit ve aeroelastik tasarımı doğrulanmadı.

**Etkisi:** Kaynak CRM malzemesi/yakıtı/yükleri gerçek kanada aktarılamaz; optimizatör başarı bayrağı dayanım kanıtı değildir.

**Bir sonraki test:** Göreve özgü yük/malzeme/sınır koşulu ve tasarım değişkenlerini kur; boyutlu denge, izinli sınırlar, bağlı yakınsama, mesh ve türev kontrolleriyle uygula.

**Kapanış:** Gerçek modelin bütün sert kısıtları ve bağımsız fizik kontrolleri geçmeli; VLM+kiriş sonucu detaylı yapı veya hacim CFD sayılmamalı.

**Bağımlı olduğu işler:** U07, U03. **Ayrıntılı yerel kayıt:** CA07.

**Kaynak:** [OpenMDAO Checking Total Derivatives](https://openmdao.org/newdocs/versions/latest/features/core_features/working_with_derivatives/check_total_derivatives.html), [ideas-um/openaerostruct-llm-agent](https://github.com/ideas-um/openaerostruct-llm-agent), [OpenAeroStruct 2.12.0 resmi genel belgeleri](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/).

**Yerel kanıt:** [fem_results.json](fem_results.json), [openaerostruct_examples.json](openaerostruct_examples.json), [openaerostruct_install.json](../../work/setup/openaerostruct_install.json).

### U17 · P1 · Güncel iç sistemle eşleşen artık konum haritası

**Gözlem:** %99,979 kapsam, yeni implicit alanın yeniden hesaplanan artığı değil aynı eski explicit-aşama RHS’sinin üyelik kesişimi. Anlamı düzeltildi; güncel b ve gerçek rL haritası henüz yok.

**Etkisi:** Eski kapsamanın artması bugünkü düzeltme yönünün doğru olduğunu göstermez.

**Bir sonraki test:** U01 çağrısının aynı b ve b−Aδ vektörlerini bütün sahip olunan düğümlerle çıkar; native norm yeniden toplamını doğrula ve flow/SA bölgelerini ayrı raporla.

**Kapanış:** Durum/iterasyon/normalizasyon/düğüm eşleşmesi ve yeniden toplam uyuşmalı; konum haritası nedensel hata veya mesh hata bandı diye adlandırılmamalı.

**Bağımlı olduğu işler:** U01. **Ayrıntılı yerel kayıt:** N03.

**Kaynak:** [Pinned SU2v8.5.0 source: FGMRES, implicit update and Newton-Krylov](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/Common/src/linear_algebra/CSysSolve.cpp), [A Residual Smoothing Strategy for Accelerating Newton Method Continuation](https://arxiv.org/html/1805.03756v1).

**Yerel kanıt:** [cfd_ic_cozum_ve_uc_ag_20261026.md](cfd_ic_cozum_ve_uc_ag_20261026.md), [cfd_kalan_artik_20261026.md](cfd_kalan_artik_20261026.md), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.json](su2_kaynak_karsilastirma_20261027.json), [method_design.json](../../work/su2_build_20261027/method_design.json), [independent_review.json](../../work/su2_build_resume_20261027/independent_review.json).

### U18 · P1 · Doygun Krylov sayımı ve tek çift süre ölçüsü

**Gözlem:** Üç v17kolunda16000 zaten200×(40+40) tavanıdır. Eşit sayım uzun çizgilerin eşit aritmetik maliyetini göstermez; gerçek süre74,125→95,109s tek gözlemdir.

**Etkisi:** Bir yöntemin gerçek doğruluk/maliyet kazancı yalnız bu vekilden çıkarılamaz.

**Bir sonraki test:** Yeni sözleşmede flow/SA ayrı, A×v ve preconditioner build/apply sayaçları, gerçek süre ve RAM ile gerçek hata azalımını birlikte izle.

**Kapanış:** Eski kapı/karar korunmalı; yeni ölçüt native öncesi yazılmalı. Tek çalıştırma çiftinden evrensel hız iddiası çıkarılmamalı.

**Bağımlı olduğu işler:** U01. **Ayrıntılı yerel kayıt:** N04.

**Kaynak:** [SU2 Linear Solvers and Preconditioners](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/), [Comparative study of inner-outer Krylov solvers for linear systems in structured and high-order unstructured CFD problems](https://arxiv.org/html/2404.17870v1).

**Yerel kanıt:** [cfd_ic_cozum_ve_uc_ag_20261026.md](cfd_ic_cozum_ve_uc_ag_20261026.md), [cfd_kalan_artik_20261026.md](cfd_kalan_artik_20261026.md), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.json](su2_kaynak_karsilastirma_20261027.json), [method_design.json](../../work/su2_build_20261027/method_design.json), [independent_review.json](../../work/su2_build_resume_20261027/independent_review.json).

### U19 · P1 · Duvar mesafesi hesabının bağımsız denetimi

**Gözlem:** Yerelde yanlış wall-distance kanıtı yok. NASA2018M6 çalışması anizotropik ağda böyle bir hata sınıfını göstermiş; bu yeni düşük maliyetli denetim adayı.

**Etkisi:** SA kaynakları için kullanılan geometrik mesafe yanlışsa mesh/y+ görseli sorunu gizleyebilir.

**Bir sonraki test:** Önce gerçek wall marker ve source kod yolunu incele. LE/TE/uç/kök/aft noktalarında native mesafeyi bağımsız global nokta–segment/üçgen/CAD-boundary hesabıyla kıyasla; uygun düz plaka yerlerinde analitik mesafeyi kullan.

**Kapanış:** Geometriye bağlı bağımsız mesafe uyuşuyorsa bu hipotezi kapat. Sapma varsa yerini/etkisini kaydet ve yalnız o hesabı değişen ayrı kontrollü test tasarla; yerel kök neden henüz yok.

**Bağımlı olduğu işler:** U03. **Ayrıntılı yerel kayıt:** VM08.

**Kaynak:** [Park vd.,2018, BölümVI ve Şekil11–13](https://ntrs.nasa.gov/api/citations/20180006169/downloads/20180006169.pdf?attachment=true).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html).

### U20 · P2 · Hessian’dan tam anizotropik/adjoint ağ döngüsüne geçiş

**Gözlem:** Yerel türev/öncelik prototipinde maskeli ve yönü kararsız bölgeler var; üretim remesher, adjoint veya CL/CD hata bandı değil.

**Etkisi:** Bir renk haritası önerilen metrikte geçerli yeni ağ ve daha doğru QoI üretildiğini göstermez.

**Bir sonraki test:** Analitik metrikte CAD sınır ve eleman-metrik uyumunu sınayan küçük2B solve→metric→remesh→transfer→solve döngüsü kur; korunumluluk ve pozitiflik ölç.

**Kapanış:** Bütün döngü ve sabit ağ kıyası doğrulanmalı; maskeler saklanmalı. Adjointin denklemi ve türevleri ayrı kontrol edilmeli; yeni makale yerel kurulum sayılmamalı.

**Bağımlı olduğu işler:** U01, U02, U03. **Ayrıntılı yerel kayıt:** VM09, N06.

**Kaynak:** [Park vd.,2018, BölümVI ve Şekil11–13](https://ntrs.nasa.gov/api/citations/20180006169/downloads/20180006169.pdf?attachment=true), [Balan vd.,2019](https://ntrs.nasa.gov/citations/20200002636), [Núñez-de la Rosa vd.,2026,ön baskı](https://arxiv.org/html/2607.27580v1), [A Residual Smoothing Strategy for Accelerating Newton Method Continuation](https://arxiv.org/html/1805.03756v1).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [cfd_ic_cozum_ve_uc_ag_20261026.md](cfd_ic_cozum_ve_uc_ag_20261026.md), [cfd_kalan_artik_20261026.md](cfd_kalan_artik_20261026.md), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html), [su2_kaynak_karsilastirma_20261027.json](su2_kaynak_karsilastirma_20261027.json), [method_design.json](../../work/su2_build_20261027/method_design.json), [independent_review.json](../../work/su2_build_resume_20261027/independent_review.json).

### U21 · P2 · Fusion motoru, hub ve lisans yetkisi

**Gözlem:** 18EkimOAuth doğrulandı; motorun gerçek oturumu, yetki/hub, ölçülü model ve STEP geri ölçümü yapılmadı. Beta erişimi öğrenci masaüstü lisansından çıkarılamaz.

**Etkisi:** Kimlik doğrulama başarılı olsa da CAD işlemlerinin çalışacağı kanıtlanmış değil.

**Bir sonraki test:** Mevcut bağlantıyı güncel araç listesinde doğrula; sürüm/session/hub/entitlement kontrolünden sonra ölçülü basit parça ve parametre değişimi, STEP geri ölçümü yap.

**Kapanış:** Gerçek motor çıktısı ve ölçü kontrolleri geçmeli. Bulut/servis erişimi koşulları ayrıca kanıtlanmalı.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** CA09.

**Kaynak:** [Autodesk Fusion Compute MCP: Public Beta](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/).

**Yerel kanıt:** [engineering_extension_quality.json](engineering_extension_quality.json), [fusion_mcp_install.json](../../work/setup/fusion_mcp_install.json).

### U22 · P2 · OpenVSP Python→OAS köprüsü

**Gözlem:** AngelScript/native OpenVSP çalışıyor. Kurulu paket Python3.11, sayısal ortam3.12; OAS resmî VSP mesh örneğinin istediği Python API köprüsü kurulup doğrulanmadı.

**Etkisi:** Ayrı üretilmiş OAS yüzeyi native VSP3 adayına otomatik bağlanmış sayılamaz.

**Bir sonraki test:** Uyumlu ayrı API ortamı veya kontrollü dosya adaptörü seç; sürüm/birim/simetri/mesh ve referans alanı geri ölçerek tek aday üzerinde doğrula.

**Kapanış:** Köprü gerçek native geometriyi doğru istasyon/analiz yüzeyine taşımalı; yanlış sürüm/ölçek negatif kontrolü reddedilmeli.

**Bağımlı olduğu işler:** U03. **Ayrıntılı yerel kayıt:** CA10.

**Kaynak:** [OpenVSP API 3.55.0 resmi belgeleri](https://openvsp.org/api_docs/latest/index.html), [OpenAeroStruct 2.12: OpenVSP-generated Mesh Example](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html).

**Yerel kanıt:** [openaerostruct_install.json](../../work/setup/openaerostruct_install.json), [openvsp_install.json](../../work/setup/openvsp_install.json), [tool_config.json](../../work/setup/tool_config.json).

### U23 · P2 · Küçük CAD modellerinin geometri/topoloji güvenilirliği

**Gözlem:** Cadmonkeydata32 yeni altı basit parçada4/6 geçti; kaçık/çift delik gibi redler var. Başka kullanım denemesindeki5/6 farklı protokol; genel doğruluk oranı değil.

**Etkisi:** Modelin kod üretmesi veya görüntü benzerliği katı/ölçü/topoloji doğruluğunu garanti etmez.

**Bir sonraki test:** Loft/sweep/shell/çoklu boşluk gibi yeni ailelerde özgün değişmemiş çıktıyı sabit bütçe ve görev bazlı kernel/ölçü hakemiyle değerlendir.

**Kapanış:** Bütün zorunlu kontroller geçmeden taslak kabul edilmemeli; insan/Codex düzeltmesi küçük model başarısı sayılmamalı. Genel oran için bağımsız temsil edici test gerekir.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** CA11.

**Kaynak:** [Text2CAD-Bench: A Benchmark for LLM-based Text-to-Parametric CAD Generation](https://arxiv.org/html/2605.18430v1), [chandar-lab/CADmium](https://github.com/chandar-lab/CADmium), [CAD-Coder: Text-to-CAD Generation with Chain-of-Thought and Geometric Reward](https://arxiv.org/abs/2505.19713v3).

**Yerel kanıt:** [k_family_new_tasks.json](k_family_new_tasks.json), [k_family_study.json](k_family_study.json), [model_usage_audit.json](model_usage_audit.json).

### U24 · P2 · Zero-to-CAD özgün çalışma yolunun ayrıştırılması

**Gözlem:** 2 milyar parametreli Zero-to-CAD modelinin yerel Q6/native köprü testleri geçerli katı üretmedi; özgünBF16/Transformers çalışma yolu yeniden üretilmedi.1m veri ölçeği,1m parametreli model demek değil.

**Etkisi:** Başarısızlık kesin olarak checkpoint kalitesine veya bütün aileye yüklenemez.

**Bir sonraki test:** Özgün modelcard sürümü, sekiz görünüş, processor/template/token bütçesi ve kod temizleme semantiğini yerel köprüyle fark tablosuna bağla; kaynak bütçesi uygunsa ayrı kontrollü referans denemesi tasarla.

**Kapanış:** Referans yol ile native yolun farkı gerçek çıktılarla ayrılmalı; ağır çalışma bütçeye sığmıyorsa doğrulanmadı olarak kalmalı. Tasarım kabulü ayrıca yapılmalı.

**Bağımlı olduğu işler:** Bağımsız hazırlanabilir. **Ayrıntılı yerel kayıt:** CA12.

**Kaynak:** [Zero-to-CAD: Agentic Synthesis of Interpretable CAD Programs at Million-Scale Without Real Data](https://arxiv.org/html/2604.24479v1), [ADSKAILab/Zero-To-CAD-Qwen3-VL-2B model card](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B).

**Yerel kanıt:** [cad_model_benchmark.json](cad_model_benchmark.json), [zero_usage_audit.json](zero_usage_audit.json).

### U25 · P2 · EXE dağıtımı ve yeni ortamda gerçek görev kullanımı

**Gözlem:** EXE çalışır başlatıcı; kurulu Python/araçlar ve proje klasörleri yanında gerekir. Temiz makine solver kurulumu ve GUI’den görülmemiş uçtan uca görev doğrulanmadı.

**Etkisi:** Mevcut PC’de arayüzün açılması bağımsız taşınabilir uygulama ve görev başarı kanıtı değildir.

**Bir sonraki test:** İzole kullanıcı/VM ya da temiz kopyada yollar/bağımlılık/kimlik doğrulama/eksik araç hatası ve bir yeni projenin gerçek oturumunu sınayacak kurulum kabulü yap.

**Kapanış:** Gerekli bileşenler kaydedilmeli; eksik araç anlaşılır hata vermeli; başka proje girdisi kullanılmamalı ve kullanıcı çıktıyı tek projede izleyebilmeli.

**Bağımlı olduğu işler:** U10. **Ayrıntılı yerel kayıt:** CA13.

**Kaynak:** [AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite](https://arxiv.org/abs/2510.21652v2).

**Yerel kanıt:** [Launcher.cs](../../work/agent/Launcher.cs), [project.py](../../work/agent/project.py), [projects.py](../../work/agent/projects.py), [projects_desk.ps1](../../work/agent/projects_desk.ps1).

### U26 · P3 · İkinci yerel RANS çözücüsü / OpenFOAM kurulumu

**Gözlem:** SU2 ve dar laminer Elmer doğrulamaları mevcut. OpenFOAM için doğrulanmış yerel kurulum/aynı3BRANSvaka tekrarı yok; TMR CFL3D/FUN3D kıyasları ayrı mevcut kanıt.

**Etkisi:** Bağımsız yöntem farkı yararlı olabilir; yeni program kurmak tek başına doğruluğu artırmaz.

**Bir sonraki test:** Önce mevcut TMR referanslarıyla tam denklem/BC/model eşlemesini bitir. Sonra read-only ortam/RAM/WSL değerlendirmesi ve küçük eşdeğer vaka ile ikinci çözümü ele al.

**Kapanış:** Sürüm, SA varyantı, sıkıştırılabilirlik, geometri ve koşullar eşleşmeden fark çözücü hatası sayılmamalı. WSL/servis kurulumu ve kaynak bütçesi ayrıca ele alınmalı.

**Bağımlı olduğu işler:** U01, U06. **Ayrıntılı yerel kayıt:** CA14, VM07.

**Kaynak:** [OpenFOAM Foundation Windows documentation](https://openfoam.org/download/windows/), [TMR 2DZP](https://tmbwg.github.io/turbmodels/flatplate.html), [OpenFOAM Foundation Windows documentation](https://openfoam.org/download/windows/).

**Yerel kanıt:** [prediction_v3_cgrid_interfacer4_summary.json](../projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json), [v3_test_batch_closed.json](../projects/proje-15cce2de02/reports/v3_test_batch_closed.json), [tmr_source_CAD_boundary_v2_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json), [tmr_source_case_review_20261025.json](../projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), [engineering_extension_quality.json](engineering_extension_quality.json), [reduced_family_review_20261026.json](reduced_family_review_20261026.json), [su2_kaynak_karsilastirma_20261027.html](su2_kaynak_karsilastirma_20261027.html), [workflow_readiness.json](workflow_readiness.json), [tool_config.json](../../work/setup/tool_config.json).

## Çözülmüş veya dar kapsamında geçen işler

- SU2 kaynak derlemesi ve bu200-adımlık vakada resmî/kaynak32 yeniden üretimi geçti; bunu bekleyen kurulum diye tekrar listelemedim.
- Native OpenVSP/VSPAERO/XFOIL, tanımlı CAD/FEM ve Elmer laminer kanal çalışmaları kendi dar kapsamlarında mevcut; yeni araç gerekliliğiyle karıştırılmadı.
- Proje merkezli GUI/EXE başlatıcı, girdi/birim ve yanlış-CFD-aktarımı/sıralama korumaları çalışıyor; genel uçtan uca başarı ayrıca açık.
- Geçersiz prob maskesi, alan/geçmiş eşlemesi ve katı-içi mesafeyi yüzey mesafesi sanma gibi bilinen olaylarda düzeltme/kanıt var. Bunlar çözümsüz aynı hata olarak yeniden sayılmadı.
- cap32→256 denemesinin kayıtlı dış yoğunluk etki kabulü başarısız kaldı. Sonuç bütün LINELET ailesinin işe yaramadığı veya bütün model hatasının bulunduğu anlamına gelmez.

ANSYS kullanıcı isteğiyle ağır/lisans aşamasına ertelendi; mevcut yakınsama sorunlarının ilk çözümü sayılmadı. OpenFOAM ise U26’da doğrulanmamış ikinci yerel çözücü seçeneği olarak ayrı kaydedildi.

## Araştırma dosyaları ve kaynak kaydı

- [Sayısal yöntemler ve ölçüm tasarımı](../../work/deep_research_20261027/numerics.md)
- [Ağ, geometri, RAE ve M6 doğrulaması](../../work/deep_research_20261027/validation_mesh.md)
- [CAD, modeller, gerçek proje ve ajan iş akışı](../../work/deep_research_20261027/cad_agent.md)
- [Bütün26 başlık, kaynak ve SHA256 kaydı](acik_sorunlar_ve_derin_arastirma_20261028.json)
- [Son gerçek CFD karşılaştırması](su2_kaynak_karsilastirma_20261027.html)

Açılan kaynakların yayın tarihi, okuma derinliği, erişim kısıtı ve uygulanabilirliği alt JSON kayıtlarında korunur. Abstract/publisher özeti ile tam metin ayrıldı; kapalı/başarısız erişim tam okunmuş sayılmadı. Kaynakların tam metni yeniden yayımlanmadı.

- **PS01** [NASA NPARC CFD verification/validation overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html)
- **PS02** [NASA-STD-7009B, 2024](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf)
- **PS03** [CFD Vision2030 Study, NASA/CR-2014-218178](https://ntrs.nasa.gov/api/citations/20140003093/downloads/20140003093.pdf)
- **PS04/CS19/VS07** [OpenFOAM Foundation Windows documentation](https://openfoam.org/download/windows/)
- **NS01** [Pinned SU2v8.5.0 source: FGMRES, implicit update and Newton-Krylov](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/Common/src/linear_algebra/CSysSolve.cpp)
- **NS02** [SU2 Linear Solvers and Preconditioners](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/)
- **NS03** [SA Expected Results -2D Zero Pressure Gradient Flat Plate](https://tmbwg.github.io/turbmodels/flatplate_sa.html)
- **NS04** [Choosing the Forcing Terms in an Inexact Newton Method](https://epubs.siam.org/doi/10.1137/0917003)
- **NS05** [A Residual Smoothing Strategy for Accelerating Newton Method Continuation](https://arxiv.org/html/1805.03756v1)
- **NS06** [Comparative study of inner-outer Krylov solvers for linear systems in structured and high-order unstructured CFD problems](https://arxiv.org/html/2404.17870v1)
- **NS07** [Reliable and efficient steady CFD from surrogate predictions through Newton-Krylov correction](https://arxiv.org/abs/2608.04400)
- **NS08** [LINELET segfaults, no LINELET regression tests -SU2 issue2877](https://github.com/su2code/SU2/issues/2877)
- **CS01** [OpenVSP API 3.55.0 resmi belgeleri](https://openvsp.org/api_docs/latest/index.html)
- **CS02** [OpenAeroStruct 2.12: OpenVSP-generated Mesh Example](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html)
- **CS03** [OCCT BRepCheck_Analyzer referansı](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html)
- **CS04** [OpenVSP resmi VSPAERO Verification and Validation Studies](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/python_scripts/report.md)
- **CS05** [OpenVSP geliştiricisi Rob McDonald'ın CDi/CDiw tanım açıklaması](https://groups.google.com/g/openvsp/c/7Bl7y1nGl1Q/m/J4QOlpNJBQAJ)
- **CS06** [Text2CAD-Bench: A Benchmark for LLM-based Text-to-Parametric CAD Generation](https://arxiv.org/html/2605.18430v1)
- **CS07** [Zero-to-CAD: Agentic Synthesis of Interpretable CAD Programs at Million-Scale Without Real Data](https://arxiv.org/html/2604.24479v1)
- **CS08** [OpenMDAO Checking Total Derivatives](https://openmdao.org/newdocs/versions/latest/features/core_features/working_with_derivatives/check_total_derivatives.html)
- **CS09** [ideas-um/openaerostruct-llm-agent](https://github.com/ideas-um/openaerostruct-llm-agent)
- **CS10** [AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite](https://arxiv.org/abs/2510.21652v2)
- **CS11** [Search-Time Contamination in Deep Research Agents](https://arxiv.org/abs/2606.05241v1)
- **CS12** [From Reproduction to Replication: Evaluating Research Agents with Progressive Code Masking](https://arxiv.org/abs/2506.19724)
- **CS13** [OpenAeroStruct 2.12.0 resmi genel belgeleri](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/)
- **CS14** [Autodesk Fusion Compute MCP: Public Beta](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/)
- **CS15** [chandar-lab/CADmium](https://github.com/chandar-lab/CADmium)
- **CS16** [CAD-Coder: Text-to-CAD Generation with Chain-of-Thought and Geometric Reward](https://arxiv.org/abs/2505.19713v3)
- **CS17** [ADSKAILab/Zero-To-CAD-Qwen3-VL-2B model card](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B)
- **CS18** [CAD-Recode: Reverse Engineering CAD Code from Point Clouds ve özgün repo](https://github.com/filaPro/cad-recode)
- **VS01** [TMR y+ çalışması](https://tmbwg.github.io/turbmodels/flatplate_val_ypluseffect.html)
- **VS02** [TMR vaka tanımı](https://tmbwg.github.io/turbmodels/onerawingnumerics_val.html)
- **VS03** [Park vd.,2018, BölümVI ve Şekil11–13](https://ntrs.nasa.gov/api/citations/20180006169/downloads/20180006169.pdf?attachment=true)
- **VS04** [NPARC mekânsal yakınsama](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)
- **VS05** [WIND Study4](https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html)
- **VS06** [TMR 2DZP](https://tmbwg.github.io/turbmodels/flatplate.html)
- **VS08** [Morrison ve Hemsch,2007](https://ntrs.nasa.gov/citations/20080002265)
- **VS09** [Balan vd.,2019](https://ntrs.nasa.gov/citations/20200002636)
- **VS10** [Núñez-de la Rosa vd.,2026,ön baskı](https://arxiv.org/html/2607.27580v1)

Yerel kanıt kontrolü:61 hash kaydı/50 benzersiz dosya eşleşti. Bu araştırma hata envanteridir; yeni doğruluk, kör LLM değerlendirmesi, CFD yeterliliği veya uçuşa uygunluk kabulü üretmedi.
