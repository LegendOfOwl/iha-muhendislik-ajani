# Mühendislik araçları ve proje düzeni — sonuç

18 Ekim 2026. Yerel araç zinciri ve projeye bağlı görev düzeni kuruldu. Yerel CAD modellerinin çalışması ve ölçülere uygunluğu ayrı sonuçlar olarak izlendi.

## Kurulu araçlar

| İş | Araç ve sürüm | Durum |
|---|---|---|
| Parametrik uçak geometrisi / 3D potansiyel akış | OpenVSP 3.55.0 / VSPAERO 7.2.2 | Önceki native testler ve yeni kanat karşılaştırması geçti |
| 2D viskoz profil | XFOIL 6.99 | Reynolds/Mach/Ncrit/geçiş ve eksik açılar kaydedildi |
| Düzenlenebilir CAD | FreeCAD 1.1.4, CadQuery 2.8.0 | Native belge, STEP tekrar açma ve geometri kontrolleri geçti |
| Ağ / yapısal çözüm | Gmsh SDK 4.15.2 / CalculiX 2.22 | Gerçek 3D çözüm, üç ağ ve analitik karşılaştırma geçti |
| Metinden şekil | OpenSCAD 2021.01 / K-1B Q8_0 | Yerel üretim çalıştı; özgün 3 parça bütün kabul ölçütlerini geçemedi |
| Görünüşlerden CAD | Zero-to-CAD 2B Q6_K + f16 görsel bağdaştırıcı | Yerel üretim çalıştı; geçerli katı üretilemedi |

FreeCAD içindeki FEM arayüzü için de CalculiX ve paketlenmiş Gmsh 4.15.0 yolları proje profiline yazıldı; yeni FreeCAD sürecinde okunabildi. Bu, Gmsh 4.15.2 SDK ile yaptığımız sayısal ağ testinden ayrı bir yapılandırma kontrolüdür. Genel sistem PATH veya kalıcı Windows çalıştırma ilkesi değiştirilmedi. Merkez başlatıcısındaki PowerShell seçeneği yalnız o sürece uygulanır.

## Gerçek yapısal çözüm

Sentetik test: 200×10×10 mm ankastre kiriş; E=70 GPa, nu=0,3 ve uç yüzde toplam 10 N yük test varsayımıdır. Analitik hesap SI tabanında yapıldı; native CAD/FE girdisinde mm–N–MPa dönüşümü açıkça kaydedildi.

- İnce ağ: 13208 düğüm, 7261 adet C3D10 eleman.
- Uç sehim: 0.456204 mm; Euler–Bernoulli: 0.457143 mm.
- Bağımsız hesap farkı: %0.205; orta–ince ağ değişimi: %0.036.
- Üç ağda kuvvet dengesi ve eleman bağlantıları kontrol edildi. 14/14 kontrol geçti.
- İlk ağ aktarımındaki C3D10 kenar düğümü sıralama sorunu yakalandı; CalculiX sırasına dönüşüm ve tüm kenar orta noktalarının kontrolü eklendi. Başarısız ham çalışma saklandı.
- Bu kiriş bir İHA kanadı değildir. Kompozit, burkulma, yorulma, bağlantılar veya dayanım marjı değerlendirilmedi. Sehim yakınsaması gerilme yakınsaması sayılmadı.

## Parametreli aerodinamik karşılaştırma

Tek dosyadan üç AR adayı oluşturuldu; referans alan/açıklık/veter ve moment noktası geometriyle birlikte değişti. Hız/dinamik viskozite/yoğunlukla Re, ses hızıyla Mach hesaplandı. Her adayda iki panel düzeyi ve wake değişimi kontrol edildi. VSPAERO yerel yükleriyle global kaldırma karşılaştırıldı; yerel Cl değerleri XFOIL polarının içinde eşleştirildi.

**27/27 yöntem kontrolü geçti.** AR=8 polarda +2°, AR=10 polarda −2° yakınsamadı; bu açılar gizlenmedi. Mevcut yakınsamış noktalarda, karşılaştırma aralığını kapsayan polar üzerinden doğrusal enterpolasyon yapıldı. Bu nedenle profil sürüklemesi yaklaşık kestirimdir. 2D/3D bu bağlantı stall veya deneysel doğrulama sayılmaz.

| AR | Açıklık m | Veter m | Re | Ortak CL=0,35 için CDi | Tahmini profil CD |
|---|---|---|---|---|---|
| 6 | 1.732 | 0.289 | 592870 | 0.00722 | 0.00765 |
| 8 | 2.000 | 0.250 | 513440 | 0.00531 | 0.00798 |
| 10 | 2.236 | 0.224 | 459235 | 0.00428 | 0.00823 |

Bu karşılaştırma test varsayımları altındaki izole kanatları kapsar. Gerçek uçak için en iyi kanat, toplam sürükleme, sürekli güç, enerji veya uçuşa uygunluk sonucu değildir.

## Ajanın çalışma düzeni

- Tek giriş: `outputs/Muhendislik-Merkezi.cmd`; burada doğal dille görev verilir ve gerçek araçlar açılır.
- Görevler `outputs/data/tasks`, güncel proje girdileri `outputs/data/project` altında tutulur.
- Proje becerisi `.agents/skills/iha-muhendislik/SKILL.md`; üst kurallar AGENTS.md içinde korunur.
- Test/çalışma komutları tek girişte toplanır. Yeni çalışmalarda girdi ve rapor SHA256 değerleri ile ham loglar saklanır; eski rapor yeni çalışmanın sonucu sayılmaz.
- Gerçek İHA kavramsal adımları ayrı izlenir. Eksik kütleler sıfır kabul edilmedi; uçak fizibilitesi değerlendirilmedi.
- Mühendislik Merkezi arayüzü oluşturulup görseli kontrol edildi. Başlatıcı komut oluşturma yolu yeni bir ajan başlatmadan sınandı. Bu çalışmanın kendisi gerçek araçlarla yürütüldü; ayrıca ikinci bir LLM seansı otomatik başlatılmadı.

## Kayıtlar ve yeniden kurma

[Birleşik kanıt kaydı](verification_summary.json), [model araştırması](cad_model_research.md), [yerel model ölçümleri](cad_model_benchmark.json), [FEM](fem_results.json), [kanat karşılaştırması](wing_study_results.json).

Yeni büyük dosyaların toplam indirmesi yaklaşık 4.10 GiB; küçük Python paketleri buna dahil değil. Veri kümesinin bir milyon örneği indirilmedi. Kaynak arşivleri ve checksum kayıtları çalışma klasöründe tutuluyor.
İki Python ortamının wheel sürümleri ve gerçek indirme SHA256 değerleri kilit dosyalarında güncellendi; bağımlılık kontrolü geçti. `work/setup/rebuild_light.ps1` Python ortamlarını geri kurma yoludur; bu turda sıfırdan bütün ortamların yeniden kurulması denenmedi. Native araçlar için kurulum betikleri ve sürümlü manifestler `work/setup` içindedir.
ANSYS ağır/lisanslı aşama olarak sona bırakıldı. Diğer araştırma modelleri karşılaştırma raporunda kurulu/denenmemiş olarak açıkça ayrıldı.

## Birincil kaynaklar

- [Resmi FreeCAD 1.1.4 paketi](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4)
- [Gmsh SDK ve belgeleri](https://gmsh.info/)
- [CalculiX geliştirici sitesi](https://www.calculix.de/)
- [OpenSCAD indirmeleri](https://openscad.org/downloads.html)
- [OpenAI: yerel klasörler ve projeler](https://learn.chatgpt.com/docs/projects)
