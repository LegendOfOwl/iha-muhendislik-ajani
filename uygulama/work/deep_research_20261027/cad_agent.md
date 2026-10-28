# CAD ve ajan iş akışı: açık sorunlar ve kaynaklı araştırma

28 Ekim 2026 · Yerel durum v0.17.0 · Araştırma kolu: CAD, VLM/OAS, ajan değerlendirmesi ve ürün entegrasyonu.

Dar kapsamlı gerçek araç çalışmaları ve güçlü yanlış-kabul önlemleri var. Bunlar keyfi kullanıcı projesinde uçtan uca özerklik, CAD/analiz yüzey eşdeğerliği, imalat uygunluğu veya görülmemiş görevlerde uzman ajan davranışı kanıtı oluşturmuyor. Öncelik yeni model sayısını artırmak değil, geometri ve kabul sözleşmelerini tek bir izlenebilir aday üzerinde bağlamak ve sonra bağımsız görevlerde ölçmek.

Bu çalışma salt okunur envanter ve literatür araştırmasıdır. **Yeni CAD/CFD/LLM çalışması veya kurulum yapılmadı. Aşağıdaki testler öneridir; geçirilmiş test değildir.** CFD yakınsaması, ağ ve deney uyuşmazlığının ayrıntısı ayrı araştırma kolundadır.

## Öncelik anlamı

- **P0:** Yanlış mühendislik kabulünü önlemek veya gerçek İHA görevinin başlayabilmesi için zorunlu kapı. Bu tur hemen bütün P0 işleri çalıştırılmalı anlamına gelmez.
- **P1:** Kullanıcının kaynaklı CAD→analiz→karşılaştırma hedefinde gerekli fakat mevcut durumda kapanmamış yetkinlik.
- **P2:** Belirli aracın/modelin veya ürün kullanımının eksikliği; mevcut doğrulanmış dar yöntemle bazı işler ilerleyebilir.
- **P3:** İkincil kurulum/dağıtım seçeneği; asıl doğruluk engellerinden önce büyütülmemeli.

## Önem sıralı envanter

| Öncelik / Kimlik | Problem | Güncel yerel kanıt | Bağımlılık | Önerilen ölçülebilir test | Kapanış ölçütü | Birincil kaynak |
|---|---|---|---|---|---|---|
| P0 / CA01 | Gerçek İHA tasarımının güncel görev, kütle ve kabul girdileri hâlâ kayıtlı değil. | mission.json içindeki görev, hedef hız, süre, faydalı yük, irtifa, kalkış/iniş ve boyut girdileri null; mass_budget.json içindeki altı bileşen kütlesi null. | Kullanıcının güncel görev ve sınırları; Kaynaklı bileşen/malzeme/enerji verileri | Girdi ön denetiminde bir eksik kritik veri, bir çelişen gereksinim ve bir birim dönüşümü içeren üç görev kaydı kullan. | Tasarım için zorunlu her girdinin değer/aralık, SI birimi, kaynağı ve geçerlilik koşulu kayıtlı; bilinmeyenler sıfıra çevrilmiyor. | [S09](https://github.com/ideas-um/openaerostruct-llm-agent) |
| P0 / CA02 | CAD, OpenVSP/VLM, OAS ve daha sonra CFD geometrisinin aynı adayı temsil ettiği ölçülmüş değil. | CadQuery ruled zarfı ve OpenVSP kesit interpolasyonu aynı JSON parametrelerini kullansa da ayrı temsiller. | Birim/eksen/twist merkezi ve kaynak profil sözleşmesi; Ortak aday kimliği ve temsil sürümü | Tek kaynak adaydan CAD kabuğu ve analiz yüzeyini dışa aktar; önce m↔mm, simetri ve 25% veter twist eksenini kontrol et. | Önceden seçilmiş geometri hata bütçesinde bütün zorunlu istasyon/yüzey kontrolleri geçiyor; temsil/koordinat/geometri hashleri raporda eşleşiyor ve kasıtlı sapma reddediliyor. | [S01](https://openvsp.org/api_docs/latest/index.html), [S02](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html), [S03](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html) |
| P0 / CA03 | Talimat/hafıza değişikliklerinin görülmemiş mühendislik görevlerinde ajan davranışını iyileştirdiği ölçülmedi. | qualification_plan_v1.json planned_not_run; holdouts_not_selected_yet=true; expert_status=not_established. | Sabit model/araç/aday ve süre bütçesi; Önceden ayrılmış yeni geometri ve koşullar; Hedef cevaplardan ayrı değerlendirme | Eski ve aday talimat sürümünü aynı araçlar ve bütçeyle; görülmemiş CAD, dosya/API, 2B CFD ve yapı görevlerinden oluşan ön kayıtlı bir bataryada karşılaştır. | Seçilmiş kapsam ve görev kümesinde önce/sonra sonuç, başarısızlıklar ve belirsizlik raporlanmış; kritik yanlış kabul yok; önce belirlenen iyileşme ölçütü sağlanmış. | [S10](https://arxiv.org/abs/2510.21652v2), [S11](https://arxiv.org/abs/2606.05241v1), [S12](https://arxiv.org/abs/2506.19724) |
| P1 / CA04 | Proje arayüzünden serbest kısıtlar girildiğinde yeni adayları araştırıp CAD/analiz/CFD/sıralama/rapora bağlayan genel uçtan uca koşu doğrulanmadı. | full_generic_pipeline_verified=false. | CA01; CA02; İlgili sayısal kabul kapıları; CA03 | Yeni boş projede bir kapsamı açık tasarım isteğini tek girişten çalıştır. | Seçilmiş görev ailesinde kullanıcı girdisinden rapora gerçek yeni koşu tamamlanmış; her zorunlu adımın taze çıktısı ve SHA'sı var; başarısız adayların gerekçesi korunmuş; geometri/koşul/kapsam uyumsuz aday nihai sıralamaya giremiyor. | [S09](https://github.com/ideas-um/openaerostruct-llm-agent), [S10](https://arxiv.org/abs/2510.21652v2), [S12](https://arxiv.org/abs/2506.19724) |
| P1 / CA05 | Karmaşık kanadın VSPAERO yüzey CDi panel kabulü açık; yüzey ve iz sürüklemesi uyuşmuyor. | 0/3/6°'de orta→ince yüzey CDi değişimleri %18,459/%17,850/%17,026; iz CDiw %2,179/%1,795/%1,786. | CA02; Kurulu VSPAERO 7.2.2'nin kuvvet tanımları; Sabit analiz kümesi ve referanslar | Önce resmi V&V arşivinden kurulu sürümün çalıştırabildiği aynı teorik/deneysel kanat vakasını yeniden üret. | Önceden seçilmiş yüzey CDi kabulü gerekli panel/yük ve bağımsız kıyasla kapanmış ya da ayrı yeni yöntem sözleşmesinde bilimsel olarak gerekçelendirilmiş alternatif raporlanmış. | [S04](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/python_scripts/report.md), [S05](https://groups.google.com/g/openvsp/c/7Bl7y1nGl1Q/m/J4QOlpNJBQAJ) |
| P1 / CA06 | Deterministik CAD ve NIST parça başarıları keyfi yeni karmaşık parçanın doğru parametrik kurulması ve düzenlenmesine genellenemiyor. | Kanat üreticisi tek elemanlı normalize Selig profil, simetrik ruled kanat/nervür ailesi ve ±15° twist kontrolüyle sınırlı. | CA02; Ayrı geometri/topoloji/parametre kabul sözleşmesi | Kaynak ve birimi belli, önce görülmemiş parçaları özellik sınıfına göre seç: loft/sweep, ince kabuk, kaçık çapraz delik, fillet/chamfer, çoklu gövde veya montaj. | Önceden seçilmiş yeni parça ailesindeki kritik boyut/topoloji/yeniden düzenleme kapıları geçiyor; yanlış özellik/delik ve bozuk shell negatif kontrolleri reddediliyor. | [S03](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [S06](https://arxiv.org/html/2605.18430v1), [S07](https://arxiv.org/html/2604.24479v1) |
| P1 / CA07 | Gerçek kanat için aeroelastik/yapısal yük, malzeme ve ağ yeterliliği açık. | OAS 2.12.0/OpenMDAO 3.45.1 ile iki yayımlanmış CRM örneği ve dört toplam türev grubu sınandı; physical_design_acceptance=not evaluated. | CA01; CA02; Kaynaklı malzeme/kesit/yük/mesnet; Yüke uygun model kapsamı | Gerçek proje verisine geçmeden sabit geometri ve bilinen dağıtılmış yükle kiriş/kanat doğrulamasını kur. | Seçilmiş kanat/yük/malzeme için yük dengesi, deplasman ve ilgili dayanım/burkulma kabulleri; ağ duyarlılığı, bağlı yakınsama, tüm kısıtların sayısal toleransı ve türev kontrolleri birlikte geçiyor. | [S02](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html), [S08](https://openmdao.org/newdocs/versions/latest/features/core_features/working_with_derivatives/check_total_derivatives.html), [S13](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/) |
| P1 / CA08 | İnceleme çizimleri ile üretilebilir parça/montaj ve toleranslandırılmış teknik resim arasında açık var. | SVG'ler geometri izdüşümleri; imalat/GD&T resmi değil. | İmalat yöntemi, malzeme ve tolerans gereksinimleri; CA06; CA07 | Tek kaynak parça için ölçülü ön/yan/üst görünüş, kesit, delik çağrısı ve revizyonu üret; bütün ölçüleri modelden geri bağla. | İlgili parça/montaj için zorunlu ölçü/tolerans/yerleşim ve proses kontrolleri imzalı kontrol tablosunda kapanmış; görünüş benzerliği veya geçerli STEP tek kabul değil. | [S06](https://arxiv.org/html/2605.18430v1), [S07](https://arxiv.org/html/2604.24479v1) |
| P2 / CA09 | Fusion Compute MCP'de OAuth doğrulanmış olsa da motor, hub/lisans yetkisi ve STEP döngüsü sınanmadı. | Manifest oauth_login_verified=true, fusion_engine_tested=false, available_in_current_chat=false. | Araçların aktif oturumda görünmesi; Autodesk hesabı/aktif lisans/Fusion Team hub hakkı; Geometri kabul sözleşmesi | Bağlantı görünür olduğunda sürüm/oturum/hub listesini oku ve gerçek oturumu başlat. | Aynı hesapta gerçek motor oturumu, kaydet/aç/düzenle ve STEP geri ölçümü geçmiş; belge konumu ve sürüm kanıtlı. | [S14](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/) |
| P2 / CA10 | OpenVSP Python bağlaması ve OpenVSP→OAS doğrudan yüzey köprüsü kurulu değil. | OpenVSP 3.55.0 dağıtımı Python 3.11 için etiketli; mevcut ana .venv Python 3.12.14. | Uyumlu Python ABI'si ve OpenVSP derlemesi; CA02 | Mevcut çalışan .venv'i değiştirmeden sürümü uygun ayrı ortamda resmi API self-testini yap; .vsp3 oku, sadece izinli taşıyıcı yüzeyleri dışa aktar, yüzey/kanat referanslarını native AngelScript çıktısıyla karşılaştır. | Gerçek yerel Python import/örnek ve .vsp3→OAS yüzey koşusu geçmiş; geometri, alan, span/twist ve analiz kümesi eşleşmiş. | [S01](https://openvsp.org/api_docs/latest/index.html), [S02](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html) |
| P2 / CA11 | Küçük metin→CAD modellerinde ölçü, kaçık delik ve çoklu delik/topoloji güvenilirliği açık. | Ayrı altı basit yeni yerel parçada K-1B 0/6, data-32 4/6. | CA06; CA03; Model/quantization/runtime/istem sürüm kaydı | K-1B ve data-32 için aynı ön kayıtlı yeni ölçülü parça kümesini kullan; deterministik CAD işçisi kontrol kolu olsun. | Yalnız sınanan parça ailesinde ön kayıtlı kritik gereksinimler ve yanlış-kabul ölçütü sağlanırsa yardımcı role terfi. | [S06](https://arxiv.org/html/2605.18430v1), [S15](https://github.com/chandar-lab/CADmium), [S16](https://arxiv.org/abs/2505.19713v3) |
| P2 / CA12 | Zero-to-CAD yerel Q6/native yolunun başarısızlığının model, dönüştürme, görsel işleme veya runtime kaynaklı olduğu ayrıştırılmadı. | Özgün tek test örneğindeki sekiz 256×256 görünüş aynı sırayla verilmiş; 4096 token açgözlü üretimde eksik kod çıktı. | Sabit özgün görüntüler/işlemci/model sürümü; Kaynak modelin bellek/disk bütçesi; CA06 | Aynı az sayıda test görüntüsünde resmi BF16/Transformers referans yolunu, mevcut Q6/native yolla eşleştirilmiş olarak dene; işlemci/chat template, görünüş sırası, token kesilmesi, çıkan kod ve gerçek geometri ölçütleri ayrı kaydedilsin. | Sürüm ve giriş işleme eşliği doğrulanmış referans/yerel kıyas tamamlanmış; geçerli geometri ile hedef benzerliği ayrı ölçülmüş. | [S07](https://arxiv.org/html/2604.24479v1), [S17](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B), [S18](https://github.com/filaPro/cad-recode) |
| P2 / CA13 | EXE kullanışlı başlatıcı olarak doğrulandı; bağımsız taşınabilir mühendislik uygulaması ve baştan sona yeni ajan oturumu testi değil. | Launcher.cs çalışma kökünü EXE'nin üstünden bulup projects_desk.ps1 ve .venv Python yolunu arıyor.7680 bayt EXE'nin yanında proje/araçlar gerekli. | CA04; Kurulum manifestleri ve sürüm kontrolü | Temiz bir hedef klasörde paket geri yükleme, eksik runtime, boş/bozuk aktif CAD ve geçersiz görevle başlatma dene. | İlan edilen dağıtım modelinde sıfırdan kurulum/başlatma ve seçilmiş gerçek görev tamamlanmış; bağımlılık hataları açık; yeni oturum testi yazılım mock/dry-run diye sunulmuyor. | [S10](https://arxiv.org/abs/2510.21652v2), [S12](https://arxiv.org/abs/2506.19724) |
| P3 / CA14 | OpenFOAM/WSL ve ANSYS kurulu değil; ikinci hacim çözücüsüyle aynı dış-akış vakasının bağımsız kıyası da henüz yok. | workflow_readiness.json OpenFOAM_installed=false, ANSYS_installed=false. | Kaynak/disk/RAM ve işletim sistemi değişikliği kapsamı; Eşdeğer fizik/ağ/sınır koşulu sözleşmesi | Kurulum seçilirse sürümü sabit OpenFOAM dağıtımında önce resmi küçük laminer ve türbülanslı doğrulama vakalarını çalıştır; daha sonra SU2 ile aynı geometri/koşulların eşleştirme tablosunu kur. | Kurulum/örnek çalışma ile kodlar-arası kıyas ayrı kapılar halinde geçmiş; deney doğrulaması ayrıca açık. | [S19](https://openfoam.org/download/windows/) |

## Ayrıntı ve kabul tasarımı

### CA01 · P0 · Gerçek İHA tasarımının güncel görev, kütle ve kabul girdileri hâlâ kayıtlı değil.

**Gözlenen durum:** mission.json içindeki görev, hedef hız, süre, faydalı yük, irtifa, kalkış/iniş ve boyut girdileri null; mass_budget.json içindeki altı bileşen kütlesi null. Sekiz kavramsal adımın tamamı bekliyor. Bu verilerin yokluğu yazılım/çözücü hatası değildir; benchmark sayılarıyla doldurulamaz.

**Yerel kanıt:** [E01: mission.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/project/mission.json), [E02: mass_budget.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/project/mass_budget.json), [E03: conceptual_steps.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/project/conceptual_steps.json)

**Bağımlılık:** Kullanıcının güncel görev ve sınırları; Kaynaklı bileşen/malzeme/enerji verileri.

**Önerilen test:** Girdi ön denetiminde bir eksik kritik veri, bir çelişen gereksinim ve bir birim dönüşümü içeren üç görev kaydı kullan. Eksik veri bağlı hesapları durdurmalı; bağımsız kaynak/geometri işleri sürebilmeli. Kullanıcının onayladığı gerçek görevde kütle toplamı ve güç/enerji/CG/trim/kararlılık/yapı için ayrı kabul matrisi üret.

**Kapanış:** Tasarım için zorunlu her girdinin değer/aralık, SI birimi, kaynağı ve geçerlilik koşulu kayıtlı; bilinmeyenler sıfıra çevrilmiyor. Her kavramsal adım kanıtlı tamamlandı, gerekçeli uygulanmıyor veya açık bekliyor durumunda. Gereksinimlerin tümü kapanmadan uçak uygunluğu verilmez.

**Araştırmadan çıkarım:** OAS kaynak ajanının eksik veri sorması ve açık amaç/değişken/kısıt istemesi yerel girdi sözleşmesini destekleyen bir yöntem örneğidir; kaynak CRM varsayımlarını gerçek İHA'ya taşımak çözüm değildir. [S09](https://github.com/ideas-um/openaerostruct-llm-agent)

### CA02 · P0 · CAD, OpenVSP/VLM, OAS ve daha sonra CFD geometrisinin aynı adayı temsil ettiği ölçülmüş değil.

**Gözlenen durum:** CadQuery ruled zarfı ve OpenVSP kesit interpolasyonu aynı JSON parametrelerini kullansa da ayrı temsiller. run_complex_vlm.py bunu açık limit olarak bildiriyor. Dört STEP nervüründe sekiz delik ekseni/çapı 0,001 mm ile doğrulandı; bu dış kanat yüzeyleri arasında tam eşdeğerlik kanıtı değildir.

**Yerel kanıt:** [E04: parametric_wing.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/geometry/parametric_wing.py), [E05: run_complex_vlm.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/qualification/run_complex_vlm.py), [E06: complex_vlm_force_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/complex_vlm_force_audit.json), [E07: step_bore_measurements.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/step_bore_measurements.json)

**Bağımlılık:** Birim/eksen/twist merkezi ve kaynak profil sözleşmesi; Ortak aday kimliği ve temsil sürümü.

**Önerilen test:** Tek kaynak adaydan CAD kabuğu ve analiz yüzeyini dışa aktar; önce m↔mm, simetri ve 25% veter twist eksenini kontrol et. Aynı açıklık istasyonlarında LE/TE, veter, burulma, camber ve normal yönünü geri ölç. Ara istasyonları da örnekle; iki yönlü yüzeye uzaklık, referans alan ve kesit farkını raporla. Katı dış yüzeyi, sıfır kalınlıklı VLM camber yüzeyi ve aeroelastik deforme yüzeyi ayrı tanımla. Bir istasyonda kasıtlı twist/ölçek sapması negatif kontrolü olsun.

**Kapanış:** Önceden seçilmiş geometri hata bütçesinde bütün zorunlu istasyon/yüzey kontrolleri geçiyor; temsil/koordinat/geometri hashleri raporda eşleşiyor ve kasıtlı sapma reddediliyor. Sonlu örnekleme tam Hausdorff üst sınırı diye etiketlenmiyor. VLM camber yüzeyi ile katı kabuğun farkı beklenen dönüşüm olarak açıklanıyor.

**Araştırmadan çıkarım:** Bir ortak CAD kaynağından programatik yüzey çıkarma, iki ayrı yeniden çizime göre izlenebilirliği artırabilir; otomatik yüzey eşdeğerliği yine ayrıca ölçülmelidir. MCP bağlantısı bu denetimin yerine geçmez. [S01](https://openvsp.org/api_docs/latest/index.html), [S02](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html), [S03](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html)

### CA03 · P0 · Talimat/hafıza değişikliklerinin görülmemiş mühendislik görevlerinde ajan davranışını iyileştirdiği ölçülmedi.

**Gözlenen durum:** qualification_plan_v1.json planned_not_run; holdouts_not_selected_yet=true; expert_status=not_established. Protokol R01–R03 ve yerel kod karşı örnekleri var; unseen_llm_behaviour_validated=false. Normal başlatıcı AGENTS.md ve PROJECT_STATE.md içindeki geçmiş sonuçları okuyor; o yol kör sınama değil.

**Yerel kanıt:** [E08: qualification_plan_v1.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/agent_learning/qualification_plan_v1.json), [E09: learning_loop.md](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/.agents/skills/iha-muhendislik/references/learning_loop.md), [E10: protocol_v1.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/reliability/protocol_v1.json)

**Bağımlılık:** Sabit model/araç/aday ve süre bütçesi; Önceden ayrılmış yeni geometri ve koşullar; Hedef cevaplardan ayrı değerlendirme.

**Önerilen test:** Eski ve aday talimat sürümünü aynı araçlar ve bütçeyle; görülmemiş CAD, dosya/API, 2B CFD ve yapı görevlerinden oluşan ön kayıtlı bir bataryada karşılaştır. Her görevde tüm tekrarlar, Pass@1, yanlış-kabul sayısı, zaman/maliyet, kritik adım atlama ve kanıt bütünlüğü ölçülsün. Geliştirmede kullanılan vaka holdout olmasın. Analizciye hedef değerler verilmesin; web aramaları ve erişimler kaydedilsin. Gerçek erişim yalıtımı yoksa buna güvenlik/körlük garantisi denmesin.

**Kapanış:** Seçilmiş kapsam ve görev kümesinde önce/sonra sonuç, başarısızlıklar ve belirsizlik raporlanmış; kritik yanlış kabul yok; önce belirlenen iyileşme ölçütü sağlanmış. Bu yalnız o yetkinlik kapsamını kapatır; tek başarı genel uzmanlık/halüsinasyonsuzluk değildir.

**Araştırmadan çıkarım:** AstaBench kontrollü ortam, araç erişimi ve maliyet eşliğini öne çıkarıyor. Arama zamanı cevap sızıntısı çalışması, internete açık benchmarkta yalnız ayrı sohbet kurmanın yeterli olmadığını gösteren ilgili bir ön baskıdır. Bunlar yerel ajanın başarısını ölçmüş çalışmalar değildir. [S10](https://arxiv.org/abs/2510.21652v2), [S11](https://arxiv.org/abs/2606.05241v1), [S12](https://arxiv.org/abs/2506.19724)

### CA04 · P1 · Proje arayüzünden serbest kısıtlar girildiğinde yeni adayları araştırıp CAD/analiz/CFD/sıralama/rapora bağlayan genel uçtan uca koşu doğrulanmadı.

**Gözlenen durum:** full_generic_pipeline_verified=false. Arayüz ve proje izolasyonu sınandı. project.py ayrı Codex konsolu başlatıyor; mevcut sohbete mesaj göndermiyor. projects.py hazır JSON yoksa analizi kapatıyor ve geometry/complex-vlm/profile-cfd dışındaki çoğu grubun yeni proje verisine bağlanmadığını söylüyor. rank_candidates.py kayıtlı üç kanat örneğini okuyor; yeni araştırma/CFD çalıştırmıyor; nihai kazanan null.

**Yerel kanıt:** [E11: workflow_readiness.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/workflow_readiness.json), [E12: project.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/project.py), [E13: projects.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/projects.py), [E14: projects_desk.ps1](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/projects_desk.ps1), [E15: rank_candidates.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/workflow/rank_candidates.py)

**Bağımlılık:** CA01; CA02; İlgili sayısal kabul kapıları; CA03.

**Önerilen test:** Yeni boş projede bir kapsamı açık tasarım isteğini tek girişten çalıştır. Arama alanı ve aday bütçesini dondur; her adayın kaynak→parametre→CAD→ön analiz→CFD→eleme→rapor zincirini artefakt kimlikleriyle takip et. Bir geçersiz geometri, bir yakınsamayan analiz ve aktif CAD değişimi enjekte et; eski sonuç kullanılmamalı. Süreç kesintisi/yeniden başlatmada aynı iş iki kez başlatılmamalı.

**Kapanış:** Seçilmiş görev ailesinde kullanıcı girdisinden rapora gerçek yeni koşu tamamlanmış; her zorunlu adımın taze çıktısı ve SHA'sı var; başarısız adayların gerekçesi korunmuş; geometri/koşul/kapsam uyumsuz aday nihai sıralamaya giremiyor. Tüm tasarım uzayı tarandı iddiası yok.

**Araştırmadan çıkarım:** Kaynak OAS ajanındaki router/coder/auditor yaklaşımı görev ayrımı için örnek alınabilir. Kaynağın çalışması bu yerel sistemin uçtan uca çalıştığının kanıtı değildir; ayrıca başka sağlayıcı/çatal bağımlılıkları taşır. [S09](https://github.com/ideas-um/openaerostruct-llm-agent), [S10](https://arxiv.org/abs/2510.21652v2), [S12](https://arxiv.org/abs/2506.19724)

### CA05 · P1 · Karmaşık kanadın VSPAERO yüzey CDi panel kabulü açık; yüzey ve iz sürüklemesi uyuşmuyor.

**Gözlenen durum:** 0/3/6°'de orta→ince yüzey CDi değişimleri %18,459/%17,850/%17,026; iz CDiw %2,179/%1,795/%1,786. İnce yüzey/iz farkı iz değerine göre %25,06/%18,81/%15,78. wake_CDiw_panel_screen_passed=true, surface_CDi_panel_screen_passed=false, overall_quality_passed=false. Yalnız kanat analize dahil; gövde/kuyruk/itki yok.

**Yerel kanıt:** [E05: run_complex_vlm.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/qualification/run_complex_vlm.py), [E06: complex_vlm_force_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/complex_vlm_force_audit.json)

**Bağımlılık:** CA02; Kurulu VSPAERO 7.2.2'nin kuvvet tanımları; Sabit analiz kümesi ve referanslar.

**Önerilen test:** Önce resmi V&V arşivinden kurulu sürümün çalıştırabildiği aynı teorik/deneysel kanat vakasını yeniden üret. Sonra yerel kırıklı kanatta kord ve açıklık panel aralıklarını ayrı değiştir; wake uzunluğu ve gevşetmesini panelden ayrı tut. Yerel yük dağılımını, CL, iki CDi kestirimini ve bağımsız LLT/VLM referansını aynı koşullarda karşılaştır. İnceleme öncesi hangi niceliğin kabul rolü olduğunu kaydet.

**Kapanış:** Önceden seçilmiş yüzey CDi kabulü gerekli panel/yük ve bağımsız kıyasla kapanmış ya da ayrı yeni yöntem sözleşmesinde bilimsel olarak gerekçelendirilmiş alternatif raporlanmış. Mevcut başarısız sözleşme geriye dönük CDiw seçilerek geçtiye çevrilmiyor; stall/sürtünme/tüm-uçak kabulü çıkarılmıyor.

**Araştırmadan çıkarım:** Geliştirici CDi ve CDiw'yi iki indüklenmiş sürükleme kestirimi olarak açıklıyor. İzdeki istikrar mevcut iki ağda daha iyi; bunun yüzey hatasının nedeni veya toplam uçak doğruluğu olduğu henüz gösterilmedi. [S04](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/python_scripts/report.md), [S05](https://groups.google.com/g/openvsp/c/7Bl7y1nGl1Q/m/J4QOlpNJBQAJ)

### CA06 · P1 · Deterministik CAD ve NIST parça başarıları keyfi yeni karmaşık parçanın doğru parametrik kurulması ve düzenlenmesine genellenemiyor.

**Gözlenen durum:** Kanat üreticisi tek elemanlı normalize Selig profil, simetrik ruled kanat/nervür ailesi ve ±15° twist kontrolüyle sınırlı. CTC01 kaynak STEP yardımlı yeniden kurma; CTC02/05 kaynak katıya yeni özellik ekleme. CTC01 FCStd tam native yeniden kurma geçmişi değil; CadQuery/JSON kaynağı düzenlenebilir. Sadece geçerli katı/hacim/prob başarısı tüm ölçü ve topolojiyi ispatlamaz.

**Yerel kanıt:** [E04: parametric_wing.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/geometry/parametric_wing.py), [E07: step_bore_measurements.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/step_bore_measurements.json), [E16: engineering_extension_quality.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/engineering_extension_quality.json), [E17: PROJECT_STATE.md](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/PROJECT_STATE.md)

**Bağımlılık:** CA02; Ayrı geometri/topoloji/parametre kabul sözleşmesi.

**Önerilen test:** Kaynak ve birimi belli, önce görülmemiş parçaları özellik sınıfına göre seç: loft/sweep, ince kabuk, kaçık çapraz delik, fillet/chamfer, çoklu gövde veya montaj. Kaynak katıdan yardım alınan ve yalnız teknik resim verilen sınamaları ayrı tut. BRepCheck, solid/shell/edge yapısı, kritik boyut/eksen, yüzey mesafesi ve STEP geri okuması yanında üç izinli parametre değişimiyle yeniden hesapla; hedef deliğin taşınması yanlışlıkla başka yüzeyi değiştirmemeli.

**Kapanış:** Önceden seçilmiş yeni parça ailesindeki kritik boyut/topoloji/yeniden düzenleme kapıları geçiyor; yanlış özellik/delik ve bozuk shell negatif kontrolleri reddediliyor. Tam imalat/bağımsız kernel doğrulaması veya görünmeyen yüzeyler için ölçülmemiş garanti verilmiyor.

**Araştırmadan çıkarım:** OCCT'nin geçerli şekil testi yapısal/topolojik sağlık denetimidir; tasarım niyetinin doğru uygulanmasını tek başına ölçmez. Text2CAD-Bench'in zorluk sınıfları yerel sınama seçimi için yararlı; uçak, montaj ve kesin tolerans yeterliliği onun kapsamını da aşıyor. [S03](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [S06](https://arxiv.org/html/2605.18430v1), [S07](https://arxiv.org/html/2604.24479v1)

### CA07 · P1 · Gerçek kanat için aeroelastik/yapısal yük, malzeme ve ağ yeterliliği açık.

**Gözlenen durum:** OAS 2.12.0/OpenMDAO 3.45.1 ile iki yayımlanmış CRM örneği ve dört toplam türev grubu sınandı; physical_design_acceptance=not evaluated. FEM 200×10×10 mm izotropik kiriş, -10 N, üç ağ ve analitik yer değiştirme karşılaştırmasıdır. Kompozit, burkulma, yorulma, bağlantı ve gerilme/dayanım kabulü yok; root gerilmesi strength iddiasından çıkarılmış.

**Yerel kanıt:** [E18: openaerostruct_examples.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/openaerostruct_examples.json), [E19: fem_results.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/fem_results.json), [E20: openaerostruct_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/openaerostruct_install.json)

**Bağımlılık:** CA01; CA02; Kaynaklı malzeme/kesit/yük/mesnet; Yüke uygun model kapsamı.

**Önerilen test:** Gerçek proje verisine geçmeden sabit geometri ve bilinen dağıtılmış yükle kiriş/kanat doğrulamasını kur. Toplam yük ve kök momentini bağımsız entegre et; yarım/tam kanat ve yük aktarımını denetle. Sonra OAS aeroelastik ağını ve yapısal ağını ayrı incelt; amaç/kısıtlar ve deformasyonla geometriyi ölç. Uyarlanmış modelde önce partial, sonra yakınsamış çözümde total türevleri birkaç tasarım noktasında/adım büyüklüğünde kontrol et. Kompozit/burkulma gerekiyorsa ayrı modele ve referansa geç.

**Kapanış:** Seçilmiş kanat/yük/malzeme için yük dengesi, deplasman ve ilgili dayanım/burkulma kabulleri; ağ duyarlılığı, bağlı yakınsama, tüm kısıtların sayısal toleransı ve türev kontrolleri birlikte geçiyor. Düşük mertebe VLM+kiriş sonucu detaylı CFD veya üretim sertifikası sayılmıyor.

**Araştırmadan çıkarım:** OAS hızlı bağlı ön tasarım için yararlı bir mevcut araçtır. Türev doğruluğu ve optimizatör başarı bayrağı fiziksel model uygunluğundan ayrı tutulmalıdır. [S02](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html), [S08](https://openmdao.org/newdocs/versions/latest/features/core_features/working_with_derivatives/check_total_derivatives.html), [S13](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/)

### CA08 · P1 · İnceleme çizimleri ile üretilebilir parça/montaj ve toleranslandırılmış teknik resim arasında açık var.

**Gözlenen durum:** SVG'ler geometri izdüşümleri; imalat/GD&T resmi değil. Kanat zarfı ve nervürler review compound içinde örtüşüyor; malzeme kütlesi ve yapısal montaj iddiası yapılmıyor. STEP delik ölçümü yalnız dört nervürde sekiz delik için yapılmış.

**Yerel kanıt:** [E04: parametric_wing.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/geometry/parametric_wing.py), [E07: step_bore_measurements.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/step_bore_measurements.json), [E17: PROJECT_STATE.md](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/PROJECT_STATE.md), [E19: fem_results.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/fem_results.json)

**Bağımlılık:** İmalat yöntemi, malzeme ve tolerans gereksinimleri; CA06; CA07.

**Önerilen test:** Tek kaynak parça için ölçülü ön/yan/üst görünüş, kesit, delik çağrısı ve revizyonu üret; bütün ölçüleri modelden geri bağla. Uygunluk toleransını malzeme ve imalat yönteminden türet. Basit iki parçalı montajda interferans, delik eşmerkezliliği, bağlantı erişimi ve parametre değişimi sonrası eşleşmeyi denetle. Görünmeyen delik veya aynı dış görünüşte farklı iç geometri negatif örneği kullan.

**Kapanış:** İlgili parça/montaj için zorunlu ölçü/tolerans/yerleşim ve proses kontrolleri imzalı kontrol tablosunda kapanmış; görünüş benzerliği veya geçerli STEP tek kabul değil. Genel imalat güvencesi ilan edilmiyor.

**Araştırmadan çıkarım:** Zero-to-CAD çalışması kendi geometrik kabulünün tam DFM kuralları uygulamadığını açıklar. Resim hakemleri de iç yapı/ölçü/montaj ilişkilerini tam değerlendiremez; bu proje için kernel ve gereksinim tabanlı kontroller gereklidir. [S06](https://arxiv.org/html/2605.18430v1), [S07](https://arxiv.org/html/2604.24479v1)

### CA09 · P2 · Fusion Compute MCP'de OAuth doğrulanmış olsa da motor, hub/lisans yetkisi ve STEP döngüsü sınanmadı.

**Gözlenen durum:** Manifest oauth_login_verified=true, fusion_engine_tested=false, available_in_current_chat=false. Öğrenci lisansı kullanıcı beyanı; bu servisteki hak başlangıç oturumuyla kontrol edilmemiş. Bu araştırmada yeniden OAuth veya motor çalışması yapılmadı.

**Yerel kanıt:** [E21: fusion_mcp_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/fusion_mcp_install.json), [E16: engineering_extension_quality.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/engineering_extension_quality.json)

**Bağımlılık:** Araçların aktif oturumda görünmesi; Autodesk hesabı/aktif lisans/Fusion Team hub hakkı; Geometri kabul sözleşmesi.

**Önerilen test:** Bağlantı görünür olduğunda sürüm/oturum/hub listesini oku ve gerçek oturumu başlat. Açık ölçülü parametrik tek parçada bir boyutu değiştir, native tasarımı kaydet, STEP dışa aktar ve FreeCAD/CadQuery ile kritik ölçü/topolojiyi geri oku. Oturum bitmeden hem native belge hem export kalıcılığını doğrula; erişim hatası veya kuyruk lisans başarısı sayılmasın.

**Kapanış:** Aynı hesapta gerçek motor oturumu, kaydet/aç/düzenle ve STEP geri ölçümü geçmiş; belge konumu ve sürüm kanıtlı. Lisans/öğrenci erişimi tahmin edilmiyor; beta limitleri koşu anında yeniden kontrol ediliyor.

**Araştırmadan çıkarım:** Resmi Compute MCP bulut Fusion oturumuna araç erişimi sağlar. Modelin doğruluğunu artıran bir CAD zekâ modeli değildir. Deterministik CAD işçisi ile MCP rakip kavramlar değildir: aynı parametrik/ölçü denetimli işlemler MCP üzerinden de yürütülebilir. [S14](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/)

### CA10 · P2 · OpenVSP Python bağlaması ve OpenVSP→OAS doğrudan yüzey köprüsü kurulu değil.

**Gözlenen durum:** OpenVSP 3.55.0 dağıtımı Python 3.11 için etiketli; mevcut ana .venv Python 3.12.14. Native exe ve AngelScript çalışıyor; Python binding kurulmadı. OAS resmi generate_vsp_surfaces yolu aynı ortamda OpenVSP Python API gerektiriyor.

**Yerel kanıt:** [E20: openaerostruct_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/openaerostruct_install.json), [E22: openvsp_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/openvsp_install.json), [E23: tool_config.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/tool_config.json)

**Bağımlılık:** Uyumlu Python ABI'si ve OpenVSP derlemesi; CA02.

**Önerilen test:** Mevcut çalışan .venv'i değiştirmeden sürümü uygun ayrı ortamda resmi API self-testini yap; .vsp3 oku, sadece izinli taşıyıcı yüzeyleri dışa aktar, yüzey/kanat referanslarını native AngelScript çıktısıyla karşılaştır. OAS köprüsünde panel sayısı/tessellation ve simetriyi raporla. Alternatif dosya köprüsü seçilirse koordinat ve kapsam manifesti zorunlu olsun.

**Kapanış:** Gerçek yerel Python import/örnek ve .vsp3→OAS yüzey koşusu geçmiş; geometri, alan, span/twist ve analiz kümesi eşleşmiş. Python sürüm uyumsuzluğu yok. Native AngelScript otomasyonu daha önce çalıştığı için bu eksik bütün OpenVSP otomasyonunu yok saydırmaz.

**Araştırmadan çıkarım:** En pratik yolun ayrı Python 3.11 ortamı mı yoksa sürümü uyumlu OpenVSP paketi mi olduğu küçük uyumluluk denemesiyle seçilmeli; sırf Python API için ağır kaynak derleme ilk tercih olmamalı. [S01](https://openvsp.org/api_docs/latest/index.html), [S02](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html)

### CA11 · P2 · Küçük metin→CAD modellerinde ölçü, kaçık delik ve çoklu delik/topoloji güvenilirliği açık.

**Gözlenen durum:** Ayrı altı basit yeni yerel parçada K-1B 0/6, data-32 4/6. Kaynak tarifine yakın örneklemede ayrı altı görevde data-32 5/6; suffix kaldırılınca 2/6. Otomatik/harici sohbet şablonları aynı kodu üretiyor; eğri çözünürlüğüyle 42 tekrar kabulü değiştirmedi. Model çıktıları elle düzeltilmedi; eğitim örtüşmesi bilinmiyor, oran genel doğruluk değil.

**Yerel kanıt:** [E24: model_usage_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/model_usage_audit.json), [E25: k_family_new_tasks.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/k_family_new_tasks.json), [E26: k_family_study.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/k_family_study.json)

**Bağımlılık:** CA06; CA03; Model/quantization/runtime/istem sürüm kaydı.

**Önerilen test:** K-1B ve data-32 için aynı ön kayıtlı yeni ölçülü parça kümesini kullan; deterministik CAD işçisi kontrol kolu olsun. Tek çıktı ve sabit küçük yeniden deneme bütçesini ayrı raporla. Her çıktıda sözdizimi, kernel/topoloji, delik sayı/eksen/çap/derinlik, bbox, hacim ve parametrik değişim kontrolü yap. Yanlış kritik ölçü render benzerliğiyle geçmesin.

**Kapanış:** Yalnız sınanan parça ailesinde ön kayıtlı kritik gereksinimler ve yanlış-kabul ölçütü sağlanırsa yardımcı role terfi. Elle düzeltilen çıktılar ayrı Codex/insan koludur. Otomatik mühendislik kabulü model başarısı varsayımıyla açılmaz.

**Araştırmadan çıkarım:** CADmium-1.5B/3B metinli sıralı CAD için ayrı araştırma adayları; farklı JSON/OCCT hattı gerekir. CAD-Coder metin→CadQuery açısından ilgili. Yerelde aynı metriklerle denenmeden hiçbiri data-32'den iyi ilan edilemez. [S06](https://arxiv.org/html/2605.18430v1), [S15](https://github.com/chandar-lab/CADmium), [S16](https://arxiv.org/abs/2505.19713v3)

### CA12 · P2 · Zero-to-CAD yerel Q6/native yolunun başarısızlığının model, dönüştürme, görsel işleme veya runtime kaynaklı olduğu ayrıştırılmadı.

**Gözlenen durum:** Özgün tek test örneğindeki sekiz 256×256 görünüş aynı sırayla verilmiş; 4096 token açgözlü üretimde eksik kod çıktı. Yerel görünüşle sözdizimi geçse bile katı oluşmadı. Q6_K + f16 görsel bağdaştırıcı yolu sınandı; özgün BF16/Transformers yolu yeniden üretilmedi. Zero-To-CAD-1m bir veri kümesidir,1m parametreli model değildir.

**Yerel kanıt:** [E27: zero_usage_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/zero_usage_audit.json), [E28: cad_model_benchmark.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/cad_model_benchmark.json)

**Bağımlılık:** Sabit özgün görüntüler/işlemci/model sürümü; Kaynak modelin bellek/disk bütçesi; CA06.

**Önerilen test:** Aynı az sayıda test görüntüsünde resmi BF16/Transformers referans yolunu, mevcut Q6/native yolla eşleştirilmiş olarak dene; işlemci/chat template, görünüş sırası, token kesilmesi, çıkan kod ve gerçek geometri ölçütleri ayrı kaydedilsin. Tam 1M veri kümesini indirme. VRAM/RAM ön denetimi geçmiyorsa yerel referans yeniden üretimi bekliyor kalsın; quantization hatası diye kesin teşhis konmasın.

**Kapanış:** Sürüm ve giriş işleme eşliği doğrulanmış referans/yerel kıyas tamamlanmış; geçerli geometri ile hedef benzerliği ayrı ölçülmüş. Aksi durumda sadece Q6/native bağlantısı doğrulanmadı ifadesi korunur. İHA mühendislik ana yolu bu yardımcı modele bağımlı kılınmaz.

**Araştırmadan çıkarım:** Zero-to-CAD sekiz temiz görünüşten tersine mühendislik içindir; yalnız serbest metinle yeni İHA tasarımının doğrudan yerine geçmez. Nokta bulutu varsa CAD-Recode 1.5B alternatif girdi türüne daha uygundur. [S07](https://arxiv.org/html/2604.24479v1), [S17](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B), [S18](https://github.com/filaPro/cad-recode)

### CA13 · P2 · EXE kullanışlı başlatıcı olarak doğrulandı; bağımsız taşınabilir mühendislik uygulaması ve baştan sona yeni ajan oturumu testi değil.

**Gözlenen durum:** Launcher.cs çalışma kökünü EXE'nin üstünden bulup projects_desk.ps1 ve .venv Python yolunu arıyor.7680 bayt EXE'nin yanında proje/araçlar gerekli. project_extension_quality.json GUI çizimi, dosya yönlendirme ve örnek araç çalışmasını kaydediyor; new_LLM_session_started_for_tests=false.

**Yerel kanıt:** [E12: project.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/project.py), [E13: projects.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/projects.py), [E14: projects_desk.ps1](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/projects_desk.ps1), [E29: Launcher.cs](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/Launcher.cs)

**Bağımlılık:** CA04; Kurulum manifestleri ve sürüm kontrolü.

**Önerilen test:** Temiz bir hedef klasörde paket geri yükleme, eksik runtime, boş/bozuk aktif CAD ve geçersiz görevle başlatma dene. Yeni gerçek ajan oturumundan görev sonuna kadar durum/kanıt dönüşünü GUI'de izle; uygulama kapatılıp açıldığında seçili proje ve devam eden gerçek süreç doğru gösterilsin. Paket boyutunu büyütmeden önce taşınabilir sanal ortam/harici çözücü yollarının taşınmasını değerlendir.

**Kapanış:** İlan edilen dağıtım modelinde sıfırdan kurulum/başlatma ve seçilmiş gerçek görev tamamlanmış; bağımlılık hataları açık; yeni oturum testi yazılım mock/dry-run diye sunulmuyor. Tek EXE zorunlu değil; kullanıcıya doğru kurulum biçimi net.

**Araştırmadan çıkarım:** UI/EXE iyileştirmesi tek başına CAD veya CFD doğruluğunu değiştirmez. Önce gerçek görev döngüsünü bağlamak, sonra paketleme kapsamını genişletmek daha ayırt edici iştir. [S10](https://arxiv.org/abs/2510.21652v2), [S12](https://arxiv.org/abs/2506.19724)

### CA14 · P3 · OpenFOAM/WSL ve ANSYS kurulu değil; ikinci hacim çözücüsüyle aynı dış-akış vakasının bağımsız kıyası da henüz yok.

**Gözlenen durum:** workflow_readiness.json OpenFOAM_installed=false, ANSYS_installed=false. Elmer kurulup laminer kanal üzerinde doğrulandı; bu türbülanslı dış akış kıyasının yerine geçmiyor. Bu araştırma bilgisayardaki WSL durumunu yeniden sorgulamadı; kurulum eksikliği kayıtlı durumdur.

**Yerel kanıt:** [E11: workflow_readiness.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/workflow_readiness.json), [E16: engineering_extension_quality.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/engineering_extension_quality.json), [E23: tool_config.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/tool_config.json)

**Bağımlılık:** Kaynak/disk/RAM ve işletim sistemi değişikliği kapsamı; Eşdeğer fizik/ağ/sınır koşulu sözleşmesi.

**Önerilen test:** Kurulum seçilirse sürümü sabit OpenFOAM dağıtımında önce resmi küçük laminer ve türbülanslı doğrulama vakalarını çalıştır; daha sonra SU2 ile aynı geometri/koşulların eşleştirme tablosunu kur. Türbülans varyantı, duvar tedavisi, referans büyüklük ve gerçek yakınsama aynı değilse farkı solver hatası diye etiketleme.

**Kapanış:** Kurulum/örnek çalışma ile kodlar-arası kıyas ayrı kapılar halinde geçmiş; deney doğrulaması ayrıca açık. Yeni çözücüye geçiş mevcut başarısız SU2/RAE/M6 kabulünü otomatik kapatmıyor.

**Araştırmadan çıkarım:** OpenFOAM Foundation'ın Windows yolu WSL'dir. İkinci çözücü faydalı bir bağımsızlık kontrolü olabilir; şu anki öncelikli iç-artık/geometri/ağ engelini yalnız kurulum yaparak çözmez. [S19](https://openfoam.org/download/windows/)

## Yeni problem diye sayılmaması gerekenler

- Kullanıcının istediği proje merkezli GUI ve EXE girişi mevcut ve önceki gerçek GUI/proje izolasyonu testleri kayıtlı; bunu yeniden eksik diye listelemiyoruz.
- Kayıtlı kanat/nervür ailesinde gerçek parametrik CAD, STEP geri ölçümü ve yanlış çap/konum reddi var; yalnız Python hesaplamasından ibaret değil.
- OpenVSP otomasyonu native exe/AngelScript ile mevcut; Python API olmaması OpenVSP'nin tümüyle kullanılamadığı anlamına gelmiyor.
- Geometri/koşul/CFD kalite kapısı açık adayın nihai kazanan olmasını engelleyen rank_candidates koruması mevcut. Kazanan null olması bu koşullarda doğru davranış.
- Model dosyaları/istem tarifi/sampling ve görsel sırası daha önce denetlendi; hiç araştırılmadı demek yanlış. Özgün BF16 referans kıyasındaki açık devam ediyor.
- Genel tasarım kabulü açıkken deney görevinin veya yayın paketinin tamamlandı olması çelişki değil; görev kapsamı ile fizik kabulü ayrılıyor.

## Kullanılabilir yöntem sentezi

### Deterministik CAD işçisi ve MCP

En uygun mevcut mimari: kaynaklı ve birimli görev şeması→izinli parametrik işlemler→gerçek CAD çekirdeği→bağımsız geometri/ölçü kabulü→analiz adaptörü. LLM plan/parametre/işlem seçebilir; çekirdek geometriyi üretir. MCP bu işçiye araç erişim arayüzü olabilir. API/MCP kullanılması yanlış parametre, yanlış yüzey veya yanlış fizik kabulünü önlemez. [S01](https://openvsp.org/api_docs/latest/index.html), [S03](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [S14](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/)

Kaynaklardan ve yerel boşluklardan çıkarılmış öneri; yeni uygulama/etki testi yapılmadı.

### MetindenCAD ve tersine mühendislik aynı görev değil

CADmium metinli sıralıCAD; CAD-Coder metin→CadQuery; CAD-Recode nokta bulutu→CadQuery; Zero-to-CAD çoklu görünüş→CadQuery. Kullanıcı girdisiyle eşleşmeyen modelin yayımlanmış skorunu yerel doğruluk veya üstünlük diye kullanmamak gerekir. Hazır doğruSTEP varsa yenidenLLMçizimi yerine içe alım+ölçü denetimi önceliklidir. [S15](https://github.com/chandar-lab/CADmium), [S16](https://arxiv.org/abs/2505.19713v3), [S17](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B), [S18](https://github.com/filaPro/cad-recode)

Araştırma kararı; alternatifler bu tur kurulmadı.

### Geçerli katı, doğru parça, üretilebilir parça ve doğru analiz ayrı kapılar

İlk kapı kod/kernel/topoloji sağlığı; ikinci kapı gereksinim ölçüsü ve yüzey/delik ilişkisi; üçüncü kapı düzenlenebilirlik/imalat/montaj; dördüncü kapı analize aktarılan temsil ve fizik. Render veya Chamfer/IoU ortalaması kritik bir delik eksenini gizleyebilir. Sayısal ölçüleri normalize geometri metriğinin yanında fiziksel birimde saklamak gerekir. [S03](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html), [S06](https://arxiv.org/html/2605.18430v1), [S07](https://arxiv.org/html/2604.24479v1)

Önerilen kabul mimarisi; mevcut dar kontroller geniş kapsama genellenmedi.

### Brute force yerine ayırt edici deneme

Önce kritik hata sınıfını seç: geometri aktarımı mı, kaynak veri mi, kernel/topoloji mi, sayısal kabul mü, ajan adım atlaması mı? Sonra tek değişkenli veya eşli kontrollü vaka kur. Modeldençokörneküretip en güzel görüntüyü seçmek yerine ölçü/topoloji doğrulayıcısıyla bütün adayları ve maliyeti kaydet; başarısız örnekler toplamdan çıkarılmasın. [S06](https://arxiv.org/html/2605.18430v1), [S10](https://arxiv.org/abs/2510.21652v2), [S12](https://arxiv.org/abs/2506.19724)

Yerel R03 ve kaynak değerlendirme tasarımlarıyla uyumlu öneri; yeni LLM iyileşme ölçümü değil.

## Şu aşamada önerilmeyen yaklaşımlar

- Zero-To-CAD 1M veri kümesini tümüyle indirmek veya model ailesini yerel eşli kabul testi olmadan art arda kurmak.
- Sadeceekran görüntüsü/görsel LLM hakemiyle kritik ölçü, iç delik, montaj veya imalat kabulü yapmak.
- Aynı benchmarkın beklenen cevaplarını prompta/belleğe yazarak kör test başarısını yükseltmek.
- CDiw daha sakin diye geçmişte seçilmiş yüzey CDi kabulünü geriye dönük geçtiye çevirmek.
- Fusion OAuth, MCP araç listesi, kurulumhealthcheck veya optimizatörsuccess flag'ini motor/geometri/fizik yeterliliği saymak.
- Mevcut .venv Python 3.12 ile Python 3.11 için derlenmiş OpenVSP bağlamasını uyumluluk kanıtı olmadan birleştirmek.
- ÖğrenciFusion lisansı veya bulutbeta hakkını giriş başarısından varsaymak; kaynak/araç lisansını projenin tümüne otomatik uygulamak.
- OpenFOAM/ANSYS kurulumunu mevcut geometri/ağ/yakınsama sorunlarının çözüldüğü anlamında sunmak.

## Kaynak kaydı ve kapsam

Kaynaklar gerçekten açıldı. Aşağıdaki özetler kısa tutuldu; hareketli doküman ile yereldeki sabit araç sürümü ayrılıyor. Araştırma ön baskıları yerel doğruluk garantisi değildir. Web içeriğinin yerel dosya SHA değeri bu kolda üretilmedi; olmayan değer yazılmadı.

### S01 · [OpenVSP API 3.55.0 resmi belgeleri](https://openvsp.org/api_docs/latest/index.html)

official_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** C++/AngelScript otomasyonu ve Python API için derlemenin Python sürümüyle eşlik gereği.

**Yerel kullanım:** Mevcut AngelScript veya gelecekteki ayrı API adaptörü.

**Sınır:** latest sayfası hareketlidir; yerel uygulama kurulu 3.55.0 ile sınanmalıdır.

### S02 · [OpenAeroStruct 2.12: OpenVSP-generated Mesh Example](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html)

official_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** generate_vsp_surfaces OpenVSP Python API ister; dahil edilen yüzeyler açık seçilir, panel ayrıklığı VSP tessellation ayarına bağlıdır.

**Yerel kullanım:** Ortak VSP geometrisinden OAS VLM oluşturma.

**Sınır:** Yerel Python köprüsü henüz çalıştırılmadı; yüzey eşdeğerliği kendiliğinden kanıtlanmaz.

### S03 · [OCCT BRepCheck_Analyzer referansı](https://www.occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html)

official_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Şeklin alt topoloji, kenar, yüzey ve kapanış kriterlerini denetler; geometrik kontroller ve exact/diskret yöntemler ayrıdır.

**Yerel kullanım:** CAD kabul katmanının sağlık testi.

**Sınır:** Açılan referans OCCT 8.0.1; yerel kernel API kullanımına aynen kopyalama yapılmadı. Tasarım gereksinimi veya DFM testi değildir.

### S04 · [OpenVSP resmi VSPAERO Verification and Validation Studies](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/python_scripts/report.md)

upstream_repository_validation_examples · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Kaynak teorik/deneysel kanatlarla geometri, analiz girdileri ve sonuç kıyasını script üzerinden kurar.

**Yerel kullanım:** Yüzey/iz CDi teşhisinden önce sürümle eşli resmi örnek.

**Sınır:** Upstream main hareketlidir; kaynak sonuçlar burada yeniden çalıştırılmadı.

### S05 · [OpenVSP geliştiricisi Rob McDonald'ın CDi/CDiw tanım açıklaması](https://groups.google.com/g/openvsp/c/7Bl7y1nGl1Q/m/J4QOlpNJBQAJ)

primary_developer_statement · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** CDi ve CDiw iki indüklenmiş sürükleme kestirimidir; CDtot = CDo + CDi, CDwtot = CDo + CDiw.

**Yerel kullanım:** Yerel kuvvet sütunlarını doğru yorumlamak.

**Sınır:** 2025 forum açıklaması tek başına kurulu sürümün sayısal doğruluk kanıtı değildir.

### S06 · [Text2CAD-Bench: A Benchmark for LLM-based Text-to-Parametric CAD Generation](https://arxiv.org/html/2605.18430v1)

original_research_preprint · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** 600 örnek; karmaşıklık ve istem biçimi ayrımı; geçerli kod ve benzerlik ayrı. Loft/sweep/shell ve karmaşık topolojide zayıflama; resim hakemi iç ölçü/montajı tam göremez.

**Yerel kullanım:** Kademeli yeni CAD holdout seçimi ve çoklu kabul ölçütü.

**Sınır:** CadQuery hedefli; montaj, sac, karmaşık parametrik aileler ve havacılık eksik. Buradaki metrikler doğrudan K/OpenSCAD üstünlüğü vermez; hakemli yayın durumu sayfadan doğrulanmadı.

### S07 · [Zero-to-CAD: Agentic Synthesis of Interpretable CAD Programs at Million-Scale Without Real Data](https://arxiv.org/html/2604.24479v1)

original_research_preprint · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Kod çalışması, geometrik/topolojik sağlık ve dışa aktarım kontrolleri ayrı; geçerli katı tam DFM kurallarını içermez.

**Yerel kullanım:** Üretici ile geometri kabulünü ayırmak.

**Sınır:** Sentetik veri ve kendi üretim/eğitim hattı; yerel Q6 başarısı veya uçak tasarımı kanıtı değildir.

### S08 · [OpenMDAO Checking Total Derivatives](https://openmdao.org/newdocs/versions/latest/features/core_features/working_with_derivatives/check_total_derivatives.html)

official_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** check_totals öncesi model yakınsamış olmalı; partial kontrolleri teşhise yardımcıdır; FD veya CS ile kıyas yapılabilir.

**Yerel kullanım:** Uyarlanmış OAS kısıt/amaç ve bağlantı türevlerini sınamak.

**Sınır:** Türev kontrolü fiziksel model ve malzeme doğrulamasının yerini tutmaz; CS uyumluluğu ayrı gereklidir.

### S09 · [ideas-um/openaerostruct-llm-agent](https://github.com/ideas-um/openaerostruct-llm-agent)

original_author_repository · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Görev sınıfı, amaç, değişken ve kısıt hazırlama, kod üretimi ve denetimi; Python 3.12 ile Gemini API veya Ollama ve host/Docker seçenekleri var.

**Yerel kullanım:** Şablondan önce açık görev sözleşmesi ve ayrı denetim rolü için yöntem örneği.

**Sınır:** Yerel eski inceleme sabit 09336bd commitindeydi; güncel upstream README başarısı yerelde yeniden üretilmedi. Gevşetme önerileri kullanıcı sert kısıtlarını değiştirme yetkisi vermez.

### S10 · [AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite](https://arxiv.org/abs/2510.21652v2)

original_research_ICLR2026 · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Kontrollü tekrar üretilebilir araç/ortam, maliyet ve araç erişimi gibi karıştırıcıların eşliği gerekir.

**Yerel kullanım:** Yerel talimat önce/sonra değerlendirme tasarımı.

**Sınır:** Bilimsel ajan genel sınaması; CAD/CFD yeterlilik skoru veya bizim ajanın ölçümü değildir.

### S11 · [Search-Time Contamination in Deep Research Agents](https://arxiv.org/abs/2606.05241v1)

original_research_preprint_under_review · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Web araması benchmark meta/veri/cevabını geri getirebilir; erişim izi ve kontrollü benchmark erişimi önemlidir.

**Yerel kullanım:** Kaynak geometri ve cevapların ayrı değerlendirme düzeni.

**Sınır:** Ön baskı; yerel sisteme performans yüzdesi aktarılmadı, güvenlik yalıtımı sağlamaz.

### S12 · [From Reproduction to Replication: Evaluating Research Agents with Progressive Code Masking](https://arxiv.org/abs/2506.19724)

original_research_preprint · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Hazır kod çalıştırma ile sıfırdan bilimsel işi kurma farklı zorluklar; tek deneme ve çoklu deneme başarısı ayrılmalı.

**Yerel kullanım:** Yerel örnek araç çalıştırmasını serbest uçtan uca ajan yetkinliğinden ayırmak.

**Sınır:** ML deneyleri ağırlıklı; yerel CAD/CFD fizik kabullerini belirlemez.

### S13 · [OpenAeroStruct 2.12.0 resmi genel belgeleri](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/)

official_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** VLM ile düğüm başına 6 serbestlikli 3B uzaysal kiriş modelini OpenMDAO optimizasyonunda bağlar.

**Yerel kullanım:** Hızlı düşük mertebe aeroelastik ön tasarım.

**Sınır:** Hacim CFD ve detaylı 3B kompozit, bağlantı veya burkulma kabulü değildir.

### S14 · [Autodesk Fusion Compute MCP: Public Beta](https://www.autodesk.com/products/fusion-360/blog/fusion-compute-mcp/)

official_vendor_announcement_and_usage_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Bulut Fusion motoruna MCP erişimi, parametrik işlemler ve export; aktif Fusion lisansı ve Team hub gerekli. Geçici oturumda kalıcı çıktılar kaydedilmeli.

**Yerel kullanım:** Motor/STEP/parametrik düzenleme kabulünün ayrı sınanması.

**Sınır:** 15 Eylül 2026 beta yazısı; kuyruk ve oturum limitleri değişebilir. Öğrenci hesabının yerel hakkı doğrulanmadı; ürün demosu doğruluk garantisi değildir.

### S15 · [chandar-lab/CADmium](https://github.com/chandar-lab/CADmium)

original_author_repository · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Metinli sıralı CAD için 1.5B/3B/7B/14B modeller; kaynak yol Python 3.11, Conda/pythonocc-core ve JSON temsili içerir.

**Yerel kullanım:** Küçük metinli CAD için ölçülü gelecekteki karşılaştırma adayı.

**Sınır:** Kurulmadı/ölçülmedi; proje CadQuery hattına doğrudan takılabilir model değildir. Model/veri lisansları ayrı incelenmeli.

### S16 · [CAD-Coder: Text-to-CAD Generation with Chain-of-Thought and Geometric Reward](https://arxiv.org/abs/2505.19713v3)

original_research_NeurIPS2025 · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Metin → CadQuery programı; geometri ve format ödülünü birleştiren eğitim yaklaşımı.

**Yerel kullanım:** Mevcut CadQuery kabul hattıyla eşli yeni model araştırması.

**Sınır:** Yayımlanmış sonuç yerel performans değildir; quantization, model boyutu, lisans ve kaynak runtime ayrıca denetlenmeli.

### S17 · [ADSKAILab/Zero-To-CAD-Qwen3-VL-2B model card](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B)

official_model_card · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** 8 temiz 256×256 görünüşten CadQuery; sentetik eğitim, 4096 token bağlam ve girdi sınırlamaları; Apache 2.0 etiketi.

**Yerel kullanım:** Yerel Q6 testinin doğru görev/girdiyle yorumlanması.

**Sınır:** Özgün model yolu yerelde sınanmadı; başka görüntü düzenleri ve karmaşık montajlar doğrulanmış değildir.

### S18 · [CAD-Recode: Reverse Engineering CAD Code from Point Clouds ve özgün repo](https://github.com/filaPro/cad-recode)

original_author_repository_and_ICCV2025_paper · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Nokta bulutundan CadQuery kodu, Qwen2-1.5B tabanlı; v1.5 inference örneği var.

**Yerel kullanım:** Hazır kaynak 3B tarama/nokta bulutu varsa tersine mühendislik araştırması.

**Sınır:** Metinden serbest tasarım modeli değildir; yerel kurulum/ölçüm yok.

[İlgili özgün makale](https://arxiv.org/abs/2412.14042v2)

### S19 · [OpenFOAM Foundation Windows kurulum yolu](https://openfoam.org/download/windows/)

official_documentation · Açıldı: 2026-10-28.

**Kaynağın desteklediği:** Windows 10/11 üzerinde Ubuntu OpenFOAM dağıtımının WSL ile çalıştırılması belgelenir.

**Yerel kullanım:** İkinci çözücü ekleme seçeneği ve kurulum kapsamı.

**Sınır:** WSL/OS özelliği değişikliği bu araştırmada yapılmadı. Kurulum fizik kabulü değildir.

## Yerel kanıt anlık kaydı

Bu SHA değerleri araştırma anında okunan dosyaları tanımlar; önceki ham deneylerin tamamının bu tur yeniden doğrulandığı anlamına gelmez. PROJECT_STATE.md gibi canlı belgeler sonraki sürümde değişebilir.

| Kimlik | Dosya | SHA256 |
|---|---|---|
| E01 | [outputs/data/project/mission.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/project/mission.json) | `1a32b070b95ceddb167817f062b6e8a03807ffb2dd0e8f7f731d8245aba916f3` |
| E02 | [outputs/data/project/mass_budget.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/project/mass_budget.json) | `4d0ed349d4fdb3e7ef12e394a1be6c3aaf3c39ba4721b5a868883baee1a23677` |
| E03 | [outputs/data/project/conceptual_steps.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/project/conceptual_steps.json) | `c8cb473b0e7aaa9167bb62a8b1b09ae07127922f6513c55db59fbe8d02173cb3` |
| E04 | [work/geometry/parametric_wing.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/geometry/parametric_wing.py) | `e652e72539f36874d313fac7f437b02946ed533d0975f9ba0973a4764a49b025` |
| E05 | [work/qualification/run_complex_vlm.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/qualification/run_complex_vlm.py) | `6392f99b060059ab2d48113eacafca42186d1d14211a31ad79d6deee4e6cd8be` |
| E06 | [outputs/reports/complex_vlm_force_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/complex_vlm_force_audit.json) | `9749345e4f8b28f8ed6da2c431bd9810151f78391eb2003a153c483707661113` |
| E07 | [outputs/reports/step_bore_measurements.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/step_bore_measurements.json) | `2163c75e8b95deda67d7df05e196cc1ff71e8d367e31eaffd0516d9d777d769f` |
| E08 | [outputs/data/agent_learning/qualification_plan_v1.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/data/agent_learning/qualification_plan_v1.json) | `23183d6e557f92184cf14259334cc825ad0b7a9a39f4b2e5e364283cdb7d56e9` |
| E09 | [.agents/skills/iha-muhendislik/references/learning_loop.md](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/.agents/skills/iha-muhendislik/references/learning_loop.md) | `31da69579d3edb14986786d00e00f374c067b2e1b8e6e4ca874c601f089897ef` |
| E10 | [work/reliability/protocol_v1.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/reliability/protocol_v1.json) | `1492ce69600d936b24099fee64e2d400c05274165dcf8db28061c3b6bf8b4771` |
| E11 | [outputs/reports/workflow_readiness.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/workflow_readiness.json) | `7301d19e4396cee07bb55db976a60d3f510b461ef632e1961501a88be7a4d3d9` |
| E12 | [work/agent/project.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/project.py) | `4dd3721d86048a7557a6e2dfaba9a302ed087c1bc6c62e6730071d7cb9709ad7` |
| E13 | [work/agent/projects.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/projects.py) | `89498ca6e7ea50f4b96c16fc6ab81f556fbe5db17f440a9f363c93603fc31f26` |
| E14 | [work/agent/projects_desk.ps1](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/projects_desk.ps1) | `ae44bf3eb959cf7a1a6b1c7bd2c042b78836a80c31d0c2196bbc61ddc6ce07b5` |
| E15 | [work/workflow/rank_candidates.py](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/workflow/rank_candidates.py) | `3ce04535cbb018265a1b43aef7a9141f498ab2142c2f281ccdde5bbb411e6b62` |
| E16 | [outputs/reports/engineering_extension_quality.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/engineering_extension_quality.json) | `51d553a5ac677b05282c71c844011d3f2f902dd9b4307899331873f573417023` |
| E17 | [PROJECT_STATE.md](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/PROJECT_STATE.md) | `2275f6785af2825304c71bee04c97ad8ea1c7be443b7fd5f1e49d1d8a3e2dddc` |
| E18 | [outputs/reports/openaerostruct_examples.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/openaerostruct_examples.json) | `340cdd2275ae2018f26513bcb50a4f9a6e7aad3799d7f21c11e21b922454f9f4` |
| E19 | [outputs/reports/fem_results.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/fem_results.json) | `f9813c1eac0db5ade4c69bcfcebcdd21f4727794ecbd035c1aa244bc078e9f61` |
| E20 | [work/setup/openaerostruct_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/openaerostruct_install.json) | `c5f389c75ae267814d04f5286a9b4757e2d0c1dee3c96973014afa9f12b27751` |
| E21 | [work/setup/fusion_mcp_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/fusion_mcp_install.json) | `2b2e0d0df4bc683c719a2e374541b962bb72b72b3336d62aaeeda583f98b6407` |
| E22 | [work/setup/openvsp_install.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/openvsp_install.json) | `e307bdf49b2974e10d8e97134bcdfaf2a5f437bcf516471d9b8efa96f7876e42` |
| E23 | [work/setup/tool_config.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/setup/tool_config.json) | `cfa0f4e28b650d8e6ba33603f5e32e6aa0513fea28b57e131bd83a5fd56c0a0f` |
| E24 | [outputs/reports/model_usage_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/model_usage_audit.json) | `4a4c7534e3db14835d55e57df10c055886dc2b1e1b69cc65a3a1b3dce77b1806` |
| E25 | [outputs/reports/k_family_new_tasks.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/k_family_new_tasks.json) | `71b309eb3b811e7382572be0cf08ca1bdd165cf3aa51606976a76fc92355d698` |
| E26 | [outputs/reports/k_family_study.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/k_family_study.json) | `304dec3bc45332ea1a5c913417a542b7cda0ed6766b664e608e1e105a2f327a9` |
| E27 | [outputs/reports/zero_usage_audit.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/zero_usage_audit.json) | `672a6ebe36bf51387d0428bc875ea366fe170fefe3a32a5f02aa66f63cef4d5f` |
| E28 | [outputs/reports/cad_model_benchmark.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/cad_model_benchmark.json) | `af5716ec69d0019d36eb0813dd7927ea505b9b47d400d769c7a0c5c3cf22aa5a` |
| E29 | [work/agent/Launcher.cs](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/agent/Launcher.cs) | `1b7644185daae6249079bd8ad0b8ba50ba49ccc28e7e4be3cdb8fcb9e3e71c3c` |
| E30 | [outputs/reports/project_extension_quality.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/reports/project_extension_quality.json) | `cd563653eb9cc4889f62ee18dee5e8f1772d35353efe7c9bdcc332a6696e30cb` |

## Araştırma sınırları

- Bu liste bu deponun kayıtlı yetenek ve açık kontrollerinin envanteridir; henüz görülmemiş bütün olası hataların eksiksiz listesi olduğu iddia edilmiyor.
- Yerel manifest/rapor/kodlar salt okunur incelendi; eski çalışma raporlarının tamamı bu tur yeniden çalıştırılmadı veya bütün ham dosyaları yeniden mühürlenmedi.
- Web kaynakları gerçekten açıldı;tam PDF/veri kümesi indirilmedi. URL ve erişim tarihi kaydedildi, web içeriğinin yerelSHA'sı alınmadığı için uydurulmadı.
- Bütün proposed_test ve closure_criterion alanları gelecekteki test tasarımıdır; çalışmış/geçmiş test değillerdir. Yeni eşik gerekiyorsa koşu ve sonuçtan önce kaynak/hata bütçesiyle dondurulmalıdır.
- Fusion öğrenci/beta hakkı, alternatif model donanım uygunluğu ve üçüncü taraf verilerin yeniden dağıtım hakları bu araştırmada hükme bağlanmadı.

Makinece okunabilir aynı envanter: [cad_agent.json](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/work/deep_research_20261027/cad_agent.json).
