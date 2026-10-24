# OpenVSP, VSPAERO, XFOIL ve CAD — gerçek araç testleri

Tarih: 18.10.2026 17:03 (Europe/Istanbul)

**Sonuç: 26/26 kontrol geçti. Bu aşamanın kontrolleri tamamlandı.**

OpenVSP 3.55.0 ve onun yerel VSPAERO 7.2.2 çözücüsü ile XFOIL 6.99 doğrudan çalıştırıldı. Python bu programları başlatıp dosyalarını okuyor; 3D/2D çözümler bu harici programlardan geliyor.

## Model ve analiz kapsamı

**Bu bir entegrasyon örneğidir; gerçek İHA için seçilmiş veya optimize edilmiş tasarım değildir.** Boyutların tümü test varsayımıdır.

| Özellik | Test değeri |
|---|---|
| Referans kanat | 2 m açıklık, 0,25 m veter, 0,50 m² alan, AR=8, NACA 0012 |
| Akış | 30 m/s, 1,225 kg/m³, referans Re=500.000, sıkıştırılamaz yaklaşım |
| Açı taraması | −4, −2, 0, 2, 4, 6, 8 derece |
| 3D araç | Yerel VSPAERO, ince taşıyıcı yüzeyler |
| 2D araç | Yerel XFOIL, NACA 0012 ve NACA 2412; Ncrit=9 |
| Örnek uçak geometrisi | Kanat, yatay/dikey kuyruk ve gövde; gerçek STEP sınır kutusu: 1200.0, 2000.0, 300.0 mm |

Gövde modelde çizildi ve CAD dosyasına aktarıldı; aerodinamik analiz kümesinden açıkça çıkarıldı. Kanat–kuyruk sonuçları bu taşıyıcı yüzeyler içindir. VSPAERO CD0 kestirimi doğrulanmış tüm uçak sürüklemesi olarak kullanılmadı.

## Ölçülen başlıca sonuçlar

- Referans kanatta 4° için VSPAERO CL = **0.319842**, CDi = **0.004437**.
- Orta -> ince ağ CL değişimi: **%0.787**; CDi değişimi: **%5.615**.
- Aynı kanatta AeroSandbox VLM ile CL farkı: **%0.899**. Bu bir ayrı çözücü tutarlılık kontrolüdür; deneysel doğrulama değildir.
- Açıklık yüklerinin integralinden CL = **0.319842**; toplam CL ile fark **%0.000**.
- XFOIL iki profil için yedişer viskoz polar noktası üretti. Geçerli noktalar, ham program çıktısından alındı.
- OpenVSP metre birimiyle STEP dışa aktardı; CAD içe aktarımında 2000 mm açıklık ve 250 mm veter doğrulandı.
- Kapalı NACA kanat zarfı ayrıca üretildi; analitik kesit integrali ve STEP tekrar okuma kontrolleri geçti. Bu zarfın hacmi yapısal malzeme/kütle hesabı değildir.

## Görseller

![Gerçek OpenVSP CAD geometrisi](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/plots/aircraft_geometry.png)

![Yerel programlardan aerodinamik sonuçlar](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/plots/native_aerodynamics.png)

![Açıklık yükü ve moment](C:/Users/Urungu/Documents/Codex/2026-10-18/bu/outputs/plots/native_loads_moments.png)

## Açılabilir dosyalar

- [OpenVSP modelini aç](../OpenVSP-Modelini-Ac.cmd)
- [Harici testleri yeniden çalıştır](../Harici-Testleri-Calistir.cmd)
- [Düzenlenebilir OpenVSP modeli](../cad/aircraft_demo.vsp3)
- [STEP yüzey modeli](../cad/aircraft_demo.step)
- [Kapalı referans kanat STEP](../cad/reference_wing_solid.step)
- [A3 üç görünüş çizimi — SVG](../cad/aircraft_three_view.svg)
- [Üst DXF](../cad/aircraft_top.dxf), [yan DXF](../cad/aircraft_side.dxf), [ön DXF](../cad/aircraft_front.dxf)
- [Açı taraması CSV](../data/native_wing_polar.csv), [açıklık yükü CSV](../data/native_spanload_alpha4.csv)
- [XFOIL NACA 0012](../data/xfoil_naca0012_polar.csv), [XFOIL NACA 2412](../data/xfoil_naca2412_polar.csv)

Bütün girdiler, .vspgeom, .vspaero, .polar, .history, .lod, .adb ve program logları: `C:\Users\Urungu\Documents\Codex\2026-10-18\bu\outputs\simulations\external_20261018_164605`.

## Başarısız denemeler ve düzeltilen durumlar

- İlk çoklu ağ (NRef=1) denemesinde çözücü boş yüzey okuyup başarısız oldu. O çıktı kullanılmadı. Doğrulanan akış tek ağ (NRef=0) üretip geometri ayarlarını ayrı çalıştırmalarda inceltiyor. Görselleştirme dışa aktarımı çözümden sonra yapılıyor.
- Sıfır kaldırmada verim katsayısı native dosyada `-nan(ind)` oldu. Gerekli CL/CDi verileri korunarak yalnız tanımsız yardımcı katsayılar JSON içinde null saklandı.
- Kanat–kuyruk modelinde 20 iterasyonda 8° CDi değişimi seçilen sınırı sağlamadı. İlk çalışma geçerli sonuç diye sunulmadı; 40 iterasyondaki son kuvvet değişimleri kabul ölçütlerini sağladı. Eski loglar saklandı.
- İlk DXF aktarımında boş çizgi çıktısı yakalandı; gerçek projeksiyon kenarlarının düzlem üzerinde aktarılması düzeltildi ve her DXF yeniden açılıp içerdiği elemanlar sayıldı.

## Sınırlar ve sonraki mühendislik işi

- XFLR5 birebir eşdeğerliği iddia edilmiyor. 2D viskoz profil, 3D taşıyıcı yüzey, polar, yük dağılımı ve moment eğrisi araç bağlantıları test edildi.
- 2D XFOIL poları otomatik olarak bütün kanadın stall hızını veya 3D ayrılmasını doğrulamaz. Düşük açılı potansiyel akış sonucu da stall doğrulaması değildir.
- Tüm uçak için sürükleme, motor/pervane, sürekli güç, enerji, kütle, trim, dinamik kararlılık ve yapı uygunluğu henüz değerlendirilmedi.
- Ağ yakınsaması referans kanatta sınandı. Kanat-kuyruk modelinin ayrıca tüm geometriyi içeren ağ yakınsama çalışması henüz yapılmadı; onun moment/kaldırma eğrileri entegrasyon sonucudur.
- CAD aktarımı yüzey modelidir; imalata hazır çok parçalı montaj veya iç yapısal tasarım değildir.
- Gerçek tasarıma geçişte güncel görev/gereksinimler ve bileşen kütle bütçesi bu ortama aktarılmalı. Test boyutları gereksinim yerine kullanılmamalı.
- Güncel FreeCAD/CalculiX ve yerel CAD modeli durumu için [birleşik araç raporunu](engineering_toolchain_report.md) oku. ANSYS sona bırakıldı.

## Kontrol listesi

| Kontrol | Sonuç |
|---|---|
| VSPAERO wing_coarse: gerçek çözücü çalışması | Geçti |
| VSPAERO wing_coarse: gerekli katsayılar | Geçti |
| VSPAERO wing_coarse: son iterasyon kuvvet değişimi | Geçti |
| VSPAERO wing_medium: gerçek çözücü çalışması | Geçti |
| VSPAERO wing_medium: gerekli katsayılar | Geçti |
| VSPAERO wing_medium: son iterasyon kuvvet değişimi | Geçti |
| VSPAERO wing_fine: gerçek çözücü çalışması | Geçti |
| VSPAERO wing_fine: gerekli katsayılar | Geçti |
| VSPAERO wing_fine: son iterasyon kuvvet değişimi | Geçti |
| VSPAERO bağımsız ağ inceltme | Geçti |
| VSPAERO / AeroSandbox ayrı çözücü karşılaştırması | Geçti |
| VSPAERO simetrik kanat fiziksel kontrolü | Geçti |
| VSPAERO aircraft_lifting_surfaces_refined_wake: gerçek çözücü çalışması | Geçti |
| VSPAERO aircraft_lifting_surfaces_refined_wake: gerekli katsayılar | Geçti |
| VSPAERO aircraft_lifting_surfaces_refined_wake: son iterasyon kuvvet değişimi | Geçti |
| XFOIL NACA 0012: viskoz açı taraması | Geçti |
| XFOIL NACA 2412: viskoz açı taraması | Geçti |
| XFOIL simetrik profil kontrolü | Geçti |
| OpenVSP -> CAD referans birim kontrolü | Geçti |
| OpenVSP uçak yüzeylerinin CAD aktarımı | Geçti |
| CadQuery gerçek NACA kanat katısı | Geçti |
| Kanat katısının STEP turu | Geçti |
| TOP / Z: gerçek CAD çizgi projeksiyonu | Geçti |
| SIDE / -Y: gerçek CAD çizgi projeksiyonu | Geçti |
| FRONT / X: gerçek CAD çizgi projeksiyonu | Geçti |
| VSPAERO açıklık yükü / toplam kaldırma tutarlılığı | Geçti |

Ayrıntılı ölçümler ve eşikler: [external_test_summary.json](external_test_summary.json).

## Resmi kaynaklar

- [OpenVSP indirmeleri](https://openvsp.org/download.php)
- [NASA VSPAERO temelleri](https://www.nasa.gov/reference/openvsp-vspaero-basics/)
- [XFOIL — yazarın MIT sayfası](https://web.mit.edu/drela/Public/web/xfoil/)
- [OpenVSP resmi analiz betiği](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/TestAnalysisVSPAERO.vspscript)
