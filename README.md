# İHA mühendislik ajanı

Windows üzerinde proje merkezli CAD, aerodinamik/CFD, yapısal ön analiz ve kanıtlı rapor iş akışı. Güncel dağıtım **v0.15.0**. Üniversite düzeyindeki çalışmalar için geliştirilen ve sınanan bir araç bütünüdür; genel mühendislik/CFD yeterliliği tamamlanmış veya uçuşa hazır tasarım değildir.


## Güncel sürüm — 27 Ekim 2026

[**v0.15.0 sonuçları: GitHub’da okunabilir rapor**](raporlar/v0.15.0/README.md) · [Release dosyaları](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/v0.15.0) · [Sürümleme politikası](SURUMLEME.md).

27 Ekim 2026. Üç yeni native SU2 koşusu tamamlandı. Gerçek LINELET alanında 52689 düğümün 7200 tanesi çizgilerde; önceki doğrulanmış aşama artığının yoğunluk kare toplamının %53.8965’i bu birliğin içinde. Bu konumsal kapsam ölçümüdür; yeni alanın yeniden hesaplanan artığı, nedensellik veya ağ hata bandı değildir.

Aynı kaynak ağ ve başlangıç dosyasıyla, toplam dört iş parçacığı korunarak yalnız LU-SGS önkoşullayıcısının bölünmesi 0→1 değiştirildi. 200 adımlık çiftte yoğunluk kazancı 0.14072006 log10, toplam Krylov işi oranı 1.54404968, gözlenen süre oranı 3.62357987 oldu. Ön kayıtlı ortak etki ve maliyet kabulü geçmedi. 17 yeni yazılım kontrolü geçti; başarısız denemeler ve ham çıktılar korundu. Uzun çizgili kaynak derlemesi sonraki yöntem adayıdır; henüz derlenmedi veya çalıştırılmadı. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

Tam izlenen uygulama/kaynak ağacı otomatik **Source code (zip)** tag arşivinde; yeni büyük alanlar `analiz-arsivi-*.zip` dosyasındadır. `KAYNAK_INDIRME.md`, `SHA256SUMS.txt`, dosya kataloğu ve geri yükleme aracı özgün yolları ve dosya mühürlerini açıklar. Önceki sürümlerin varlıkları korunur.

## Nereden başlanır?

| Klasör | İçerik |
|---|---|
| [uygulama](uygulama/) | EXE/GUI başlatıcısı, Python/PowerShell kaynakları, ajan talimatları ve özgün proje yolları |
| [raporlar](raporlar/) | Sürüme göre araştırma, sonuç ve doğrulama raporlarına erişim |
| [cizimler](cizimler/) | STEP, FreeCAD, OpenVSP, DXF ve SVG dosyalarına erişim |
| [analizler](analizler/) | CFD/FEM/model çalışma kayıtları, büyük alan arşivleri ve tam SHA256 kataloğu |
| [testler](testler/) | Test kodları, kabul ölçütleri, başarısızlık ve doğrulama kayıtları |
| [kurulum](kurulum/) | Ortam hazırlığı, mevcut yerel araçlara bağlanma ve arşiv geri yükleme |
| [surumler](surumler/) | v0.1.0 → v0.15.0 sürüm ve kanıt notları ve dosya manifestleri |

Hazır Windows ortamında [BASLAT.cmd](BASLAT.cmd), `uygulama/outputs/Muhendislik-Merkezi.exe` açar. EXE başlatıcıdır; Python ortamları ve haricî araçlar yanında gerekir. [Kurulum açıklaması](kurulum/README.md) önce okunmalıdır. Mevcut çalışma klasörünü değiştirmeden ona yerel junction'larla bağlanmak mümkündür.

## Sürüm geçmişinin anlamı

Bu projede önceden Git geçmişi yoktu. Sürümler, elde kalan kaynak dosyaları, tarihli çıktılar ve korunmuş başarısız denemelerden **geriye dönük gruplandırılarak** oluşturuldu. Eski tag'ler özgün tarihteki tam çalışan uygulama kopyası değildir. v0.1.0–v0.10.0 bu geriye dönük içe aktarımdır. **v0.11.0 ve sonrası gerçek artımlı Git değişiklikleridir.** Tam güncel içerik için `main` veya `v0.15.0` kullanın. Git commit/yayın tarihleri bugün oluşturulan arşivin tarihidir; kaynak dosyaların gözlenen değiştirme tarihleri ayrıca katalogdadır.

| Sürüm | Kanıt grubu |
|---|---|
| [v0.1.0](surumler/v0.1.0/README.md) | Temel hesap ve girdi kontrolleri |
| [v0.2.0](surumler/v0.2.0/README.md) | Yerel CAD ve aerodinamik araçlar |
| [v0.3.0](surumler/v0.3.0/README.md) | CAD modelleri ve kullanım denetimi |
| [v0.4.0](surumler/v0.4.0/README.md) | Deterministik geometri ve hafif CFD |
| [v0.5.0](surumler/v0.5.0/README.md) | Proje merkezli arayüz ve aeroelastisite |
| [v0.6.0](surumler/v0.6.0/README.md) | Karmaşık CAD ve ilk ONERA M6 |
| [v0.7.0](surumler/v0.7.0/README.md) | Kaynak geometri ve ayrı analiz sınaması |
| [v0.8.0](surumler/v0.8.0/README.md) | C-grid araştırması ve M6 devamı |
| [v0.9.0](surumler/v0.9.0/README.md) | Hata dersleri ve ajan talimatı |
| [v0.10.0](surumler/v0.10.0/README.md) | Düzenlenmiş GitHub dağıtımı |
| [v0.11.0](surumler/v0.11.0/README.md) | Kaynak TMR M6, düz plaka, güvenilirlik politikası; gerçek artımlı sürüm |
| [v0.12.0](surumler/v0.12.0/README.md) | 11 yeni CFD kontrolü, Newton–Krylov ve kalıntı birim denetimi |
| [v0.13.0](surumler/v0.13.0/README.md) | İç çözümde%42 daha az Krylov iterasyonu ve üç kaynak ağda kabul denetimi |
| [v0.14.0](surumler/v0.14.0/README.md) | İç çözüm sınırı kıyası ve kaynak koduna dayalı kalıntı konum tanısı |
| [v0.15.0](surumler/v0.15.0/README.md) | Gerçek LINELET kapsamı ve tek bölge LU-SGS kontrolü |

## Dosyalar ve yeniden üretim

Bütün özgün proje dosyaları `uygulama/work` ve `uygulama/outputs` düzeninde kalır; üstteki kategoriler yolları bozmadan erişim sağlar. Kaynak kod, rapor, çizim, küçük veri ve ham loglar Git'tedir. Büyük ağ/alan/restart dosyaları sürüm Releases varlıklarındaki ZIP paketlerindedir. [Katalog](analizler/dosya_katalogu.json) her dosyanın yolunu, boyutunu, SHA256 değerini ve hangi arşivden geri yükleneceğini içerir.

`python kurulum/analizleri_geri_yukle.py` büyük alanları indirip özgün konumlarına çıkarır ve hash'lerini doğrular. `--references` tam üçüncü taraf makale/rapor PDF'lerini kaynak adreslerinden ayrıca getirir. Ortamlar, kurulu solver/CAD programları, indirilen kurucular, model ağırlıkları ve hesap/OAuth bilgileri depoya kopyalanmaz; kurulum betikleri ve kaynak/sürüm manifestleri tutulur.

## Mevcut sonuçların sınırı

- OpenVSP/XFOIL, FreeCAD/CalculiX, SU2, Elmer ve OpenAeroStruct ile gerçek yerel çalışmalar yapıldı; kapsamları raporlarında belirtilir.
- Küçük CAD modellerinin özgün başarı ve başarısızlıkları korunur; Codex düzeltmeleri modelin başarısı sayılmaz.
- Son ajan dersleri için 39/39 kod/dosya kontrolü ve temel yazılım için 26/26 kontrol kayıtlıdır. Görülmemiş mühendislik görevinde önce/sonra LLM iyileşmesi henüz ölçülmedi.
- RAE2822 ve ONERA M6 genel fizik kabulleri geçmedi. y+ veya kuvvet ekranının tek başına geçmesi bütün CFD doğrulamasını kapatmaz.
- Gerçek İHA girdileri ile araç yeterlilik örnekleri ayrı tutulur. ANSYS ve OpenFOAM kurulmuş değildir; Fusion yalnız OAuth aşamasında doğrulanmıştır.

[GitHub’da okunabilir güncel sonuçlar](raporlar/v0.15.0/README.md) · [Yerel HTML proje özeti](uygulama/outputs/Proje-Ozeti.html) · [Ajan dersleri](uygulama/outputs/reports/ajan_talimat_gelisimi_20261024.html) · [M6 sonuçları](raporlar/v0.11.0/README.md#onera-m6) · [Üçüncü taraf kaynakları](THIRD_PARTY_NOTICES.md)

Dosya/arşiv dağıtım sınırları için [GitHub büyük dosya belgeleri](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) ve [Releases belgeleri](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) esas alındı. Başarısız sonuçlar gizlenmedi; eşikler yayın için değiştirilmedi.

## Yazarlık ve otomasyonun rolü

Proje sahibi hedefleri, kısıtları, araç tercihlerini ve ilerleme sırasını belirledi. Kod, araç bağlantıları, test yürütme, araştırma ve raporların önemli bölümü Codex yardımıyla üretildi. Kayıtlardaki çözümler gerçek yerel program çıktılarıdır; bu durum proje sahibinin bütün programları bağımsız kullanma deneyimi veya ajanın uzmanlığı olarak sunulmaz.

## English summary

A Windows CAD/aerodynamic/CFD workflow with frozen evidence. Version 0.15.0 measures native LINELET membership: 7,200 of 52,689 nodes, covering 53.8965% of a separately verified sequential-stage density squared residual. This is static membership against a prior RHS snapshot, not a recomputed residual or causal error estimate. A single-domain LU-SGS control with four total threads achieved 0.14072006 log10 density gain at 1.54404968 times the Krylov work and 3.62357987 times the observed elapsed time. The preregistered joint effect/cost gate failed. All 17 new software checks passed. A longer-line source build is proposed but has not been built or run. Physical/RAE/M6/UAV gates remain open; improved LLM behaviour has not been demonstrated. GitHub’s automatic tag archive provides tracked sources; separate raw assets use the hash-checking restore tool. Tags through 0.10.0 are retrospective evidence groups; 0.11.0 onward are incremental releases. Code and reports were developed with substantial Codex assistance.

## EXE ve lisans durumu

EXE küçük bir Windows başlatıcısıdır. [Kaynak, derleme tarifi ve SHA256](kurulum/EXE_KAYNAK_VE_HASH.md) yayımlanır; paket taşınabilir solver/Python ortamı içermez. Proje sahibi henüz genel bir açık kaynak lisansı seçmedi; üçüncü taraf lisansları [kendi bildirimleriyle](THIRD_PARTY_NOTICES.md) korunur.
