# İHA mühendislik projesi — durum

Mühendislik araçları ve iş akışı; gerçek İHA aşamaları aşağıda ayrı izlenir.

**Uçak fizibilitesi: henüz değerlendirilemedi.**

Görev vermek için `Muhendislik-Merkezi.exe` aç ve projeni seç. Bu sohbetten de aynı klasörde çalışabiliriz.

## Gerçek proje verisi

Eksik görev girdileri: mission, target_speed, endurance, payload_mass, altitude, takeoff_landing, size_constraint
Kütlesi bilinmeyen bileşenler: yapı, motor_ve_pervane, enerji_sistemi, aviyonik_ve_servo, faydali_yuk, baglanti_kablo_diger

## Kavramsal aşama

| Adım | Durum |
|---|---|
| 1. Gereksinimler ve kabul ölçütleri | bekliyor |
| 2. Girdi, kaynak ve belirsizlik kaydı | bekliyor |
| 3. Bileşen kütle bütçesi | bekliyor |
| 4. Kanat ve düşük hız taraması | bekliyor |
| 5. Sürükleme, güç, enerji ve süre | bekliyor |
| 6. Yerleşim, CG, trim, kararlılık ve yapı | bekliyor |
| 7. Tutarlılık, duyarlılık ve belirsizlik | bekliyor |
| 8. Aday karşılaştırması ve gereksinim kanıtları | bekliyor |

## Araçların son test kayıtları

| Grup | Sonuç | Rapor |
|---|---|---|
| core | geçti | [test_results.json](test_results.json) |
| native | geçti | [external_test_summary.json](external_test_summary.json) |
| fem | geçti | [fem_results.json](fem_results.json) |
| models | çalışıyor; tüm kabul ölçütleri sağlanmadı | [cad_model_benchmark.json](cad_model_benchmark.json) |
| study | geçti | [wing_study_results.json](wing_study_results.json) |
| k-family | çalışıyor; tüm kabul ölçütleri sağlanmadı | [k_family_study.json](k_family_study.json) |
| cad-parts | çalışıyor; tüm kabul ölçütleri sağlanmadı | [k_family_new_tasks.json](k_family_new_tasks.json) |
| model-usage | çalışıyor; tüm kabul ölçütleri sağlanmadı | [model_usage_audit.json](model_usage_audit.json) |
| geometry | geçti | [parametric_cad_qualification.json](parametric_cad_qualification.json) |
| complex-vlm | çalışıyor; tüm kabul ölçütleri sağlanmadı | [complex_vlm_qualification.json](complex_vlm_qualification.json) |
| cfd | çalışıyor; tüm kabul ölçütleri sağlanmadı | [cfd_qualification.json](cfd_qualification.json) |
| elmer-cfd | geçti | [elmer_cfd_qualification.json](elmer_cfd_qualification.json) |
| comparison | çalışıyor; tüm kabul ölçütleri sağlanmadı | [candidate_comparison.json](candidate_comparison.json) |
| profile-cfd | kayıt bekleniyor | [profile_cfd_results.json](profile_cfd_results.json) |
| aerostruct | geçti | [openaerostruct_examples.json](openaerostruct_examples.json) |
| reliability | kayıt bekleniyor | [reliability_audit.json](reliability_audit.json) |

## Görevler

- 20261018-174944-24ba6b: Yerel mühendislik çalışma alanını proje düzeninde birleştir; CAD modellerini araştır, küçük araçları kur ve gerçek testlerle değerlendir. — tamamlandı
- 20261018-203719-a2da02: K-1B/MakeMe ailesini derin araştır; yeni sürüm ve istem ayarlarını ölçü kontrolleriyle değerlendir; projenin bugünkü yeteneklerini ve sınırlarını raporla. — tamamlandı
- 20261018-212129-8ffed7: Mühendislik seviyesini yükselt: deterministik parametrik CAD, Fusion/MCP araştırması, karmaşık profil/kanat doğrulaması ve gerçek CFD çıktısı — tamamlandı
- 20261018-231810-dcaa71: ANSYS öncesi hafif native CFD araçlarını kur ve doğrula; basit arayüz ve kısıttan araştırma/CAD/analiz/CFD/eleme/rapora iş akışı oluştur; hazır ve eksik kapsamı kanıtla — tamamlandı
- 20261019-100440-8e781b: Proje merkezli arayüz ve EXE başlatıcı: proje/görev/CAD/analiz/rapor bağlamlarını ayır; hazırlanan yeni profil için gerçek ağ-CFD bağlantısını ilerlet ve sınırları ölç — tamamlandı
- 20261019-110206-b6bbf3: NASA arşivli ONERA M6 Test2308 koşullarında iki kaynak ağda gerçek SU2 RANS çalıştır; yedi kesitte deney Cp verisiyle karşılaştır — tamamlandı
- 20261019-110206-eaf969: NIST kaynak teknik resim/modelinden karmaşık parçaları yeniden oluştur; referans STEP ile ölçü/topoloji/katı farkını ve FreeCAD geri okumasını denetle — tamamlandı
- 20261019-122134-162b99: Yayımlanmış kaynak geometriyi değiştirmeden, hedef deney sonuçlarını analiz ajanına vermeden yerel ağ ve gerçek CFD üret; sonuçları önceden kayıtlı ölçütlerle karşılaştır — tamamlandı
- 20261019-123823-5d7902: M6 aynı kaynak ağ/koşulunda yalnız CFL uyarlamasını kapatarak kayıtlı çözümden kontrollü sayısal deneme; mevcut duvar/ağ kabulü açık kalır — tamamlandı
- 20261019-201609-ab8031: Kaynak araştırmasıyla RAE2822 bölgesel ağ duyarlılığını teşhis et; kaynak geometriyi koruyan C-grid/blok çözümünü gerçek CFD ile ve değişmeyen kabul eşikleriyle sına — tamamlandı
- 20261024-153804-27f425: RAE2822 testlerini kapattıktan sonra ONERA M6 Test2308 için kaynaklı kontrollü gerçek3B RANS ve271 deney noktası karşılaştırması yap — tamamlandı
- 20261024-164603-4764e5: Kanıtlı hata derslerini ve hipotezleri ayır; ajan talimatı ve kalıcı hafızayı güncelle; karşı örneklerle sınayıp uzmanlık iddiasını ayrı tut — tamamlandı
- 20261024-170508-83546a: Tüm proje çalışmalarını sürümlü, kategorilere ayrılmış ve hassas bilgi taraması yapılmış yeni public iha-muhendislik-ajani GitHub deposuna yayımla — tamamlandı
- 20261024-235336-d874a2: Kaynak araştırması ve kanıt odaklı yöntemle güvenilirlik geliştirme: M6 aynı restart doğrusal çözücü kontrolü, otomatik teşhis ve bölgesel hata göstergesi — tamamlandı
- 20261025-005212-dd782d: CFD doğruluğu literatür araştırması: arXiv, hazır ONERA M6/RAE doğrulamaları ve yerel kurulum farklarının kaynaklı ayrıntılı karşılaştırması — tamamlandı
- 20261025-011533-2114a3: Resmî TMR ONERA M6 üreteci: taşınabilir derleme, kaynak geometri ve üç sistematik ağ kontrolü; bütçeli native SU2 kaynak vaka sınaması — tamamlandı
- 20261025-215442-4b9487: NASA TMR kaynak düz plaka ağlarıyla SA-neg uygulama kontrolü: üç küçük ağ, gerçek SU2 ve kaynak Cf/profil karşılaştırması — tamamlandı
