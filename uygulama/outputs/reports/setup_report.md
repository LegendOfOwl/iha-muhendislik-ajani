# Hafif mühendislik ortamı — kurulum ve test raporu

Test zamanı: 24.10.2026 16:55:26 (Europe/Istanbul)

**Sonuç: İSTENEN GRUPLAR GEÇTİ — 26/26 kontrol geçti.**

Bu rapor gerçek yerel çalıştırmalardan üretilmiştir. Bütün örnekler sentetik kurulum testidir; İHA projesinin tasarım değerleri değildir.

| Grup | Durum | Kontrol sayısı | Süre |
|---|---|---:|---:|
| Sayısal hesaplama | Geçti | 3 | 1.52 s |
| Eksik veri ve birim kontrolleri | Geçti | 13 | 0.14 s |
| Aerodinamik ve optimizasyon | Geçti | 7 | 2.15 s |
| Parametrik CAD ve STEP | Geçti | 3 | 3.20 s |

## Sürümler ve ortamlar

Proje: `C:\Users\Urungu\Documents\Codex\2026-10-18\bu`

Python ortamları, masaüstü uygulamasının mevcut Python 3.12 tabanından oluşturulmuştur. Sistem genelinde Python/PATH ayarı değiştirilmemiştir. Bu taban ileride kaldırılırsa ortamlar yeniden kurulmalıdır.

- Sayısal hesaplama: numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2, pandas 3.0.6
- Aerodinamik ve optimizasyon: aerosandbox 4.2.10, neuralfoil 0.3.3, casadi 3.8.1
- Parametrik CAD ve STEP: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- .venv: bağımlılık kontrolü geçti; No broken requirements found.
- .venv-cad: bağımlılık kontrolü geçti; No broken requirements found.

## Ölçümler ve kabul ölçütleri

### Sayısal hesaplama

- **GEÇTİ — Sinüs integralinin analitik değeri**: |I-2| < 1e-10
  Ölçüm: `{"integral": 2.0, "error_estimate": 2.220446049250313e-14}`
- **GEÇTİ — Sınır kısıtlı optimizasyon**: 0<=x<=2; optimum x=2, hata<1e-6
  Ölçüm: `{"x": 2.0, "success": true}`
- **GEÇTİ — Lineer denklem sistemi**: Bilinen çözüm [2,3]
  Ölçüm: `[2.0, 3.0]`

### Eksik veri ve birim kontrolleri

- **GEÇTİ — Tam girdide koşullu sonuç**: Yalnız kaldırma ön hesabı
  Ölçüm: `"conditional_lift_screening"`
- **GEÇTİ — Kütle ölçekleme kontrolü**: Kütle x4 => hız x2
  Ölçüm: `2.0`
- **GEÇTİ — Eksik CLmax sonucu engeller**: Sayı üretmeden blocked
  Ölçüm: `{"status": "blocked", "issues": [{"input": "cl_max", "code": "MISSING_VALUE"}], "results": null, "aircraft_feasibility": "not_assessed"}`
- **GEÇTİ — Geçersiz girdi yapısı**: JSON nesnesi gerekli
  Ölçüm: `[{"code": "INPUTS_MUST_BE_OBJECT"}]`
- **GEÇTİ — Yanlış kütle birimi**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "mass", "code": "WRONG_OR_MISSING_UNIT", "expected": "kg"}]`
- **GEÇTİ — Sıfır kanat alanı**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "wing_area", "code": "INVALID_POSITIVE_FINITE_VALUE"}]`
- **GEÇTİ — Negatif yoğunluk**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "density", "code": "INVALID_POSITIVE_FINITE_VALUE"}]`
- **GEÇTİ — NaN kaldırma katsayısı**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "cl_max", "code": "INVALID_POSITIVE_FINITE_VALUE"}]`
- **GEÇTİ — Kaynağı olmayan girdi**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "mass", "code": "MISSING_PROVENANCE"}]`
- **GEÇTİ — Bilinmiyor durumunda sayı**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "mass", "code": "MISSING_PROVENANCE"}]`
- **GEÇTİ — Mantıksal değer sayı sayılmaz**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "mass", "code": "INVALID_POSITIVE_FINITE_VALUE"}]`
- **GEÇTİ — Boşluk içeren kaynak**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"input": "mass", "code": "MISSING_PROVENANCE"}]`
- **GEÇTİ — Taşma üreten sayısal değer**: Geçersiz girdide sonuç yok
  Ölçüm: `[{"code": "NUMERIC_RANGE_ERROR"}]`

### Aerodinamik ve optimizasyon

- **GEÇTİ — NACA koordinat üretimi**: Sonlu koordinatlar, >50 nokta; yalnız geometri testi
  Ölçüm: `{"points": 399}`
- **GEÇTİ — NeuralFoil simetrik profil kontrolü**: CL(0) mutlak<.02; işaret ve simetri hatası<.03
  Ölçüm: `{"alpha_deg": [-4.0, 0.0, 4.0], "CL": [-0.43490445245539744, -5.204189192568436e-16, 0.4349044524553979]}`
- **GEÇTİ — NeuralFoil sürükleme ve model güveni**: CD>0; model confidence>.8, deneysel doğrulama değildir
  Ölçüm: `{"CD": [0.007422911640258723, 0.005351412095536144, 0.007422911640258723], "model_confidence": [0.9597443641608387, 0.9581492416231159, 0.9597443641608403]}`
- **GEÇTİ — VLM sonlu kanat referansı**: Yaklaşık kaldırma çizgisi referansından sapma<%20; CDi>0, deneysel doğrulama değildir
  Ölçüm: `{"CL": 0.3237105372488659, "approximate_theory_CL": 0.35091926759428826, "relative_error": 0.0775355839875953}`
- **GEÇTİ — VLM panel yakınsaması**: 12->24 açıklık panelinde CL değişimi<%4
  Ölçüm: `{"rows": [{"spanwise_resolution": 6, "CL": 0.33436629258487627, "CDi": 0.004192978390647586}, {"spanwise_resolution": 12, "CL": 0.3275893459615998, "CDi": 0.0042058931380660495}, {"spanwise_resolution": 24, "CL": 0.3237105372488659, "CDi": 0.004197094709875997}], "last_change": 0.011840460505051276}`
- **GEÇTİ — VLM sıfır hücum açısı**: Simetrik düz kanat için |CL|<.005
  Ölçüm: `{"CL_at_zero": 5.756331947300034e-16}`
- **GEÇTİ — AeroSandbox/CasADi/IPOPT kısıtlı optimizasyon**: Bilinen sınır optimumu x=2; hata<1e-5
  Ölçüm: `{"x": 2.000000019995}`

### Parametrik CAD ve STEP

- **GEÇTİ — CAD katı ve analitik hacim**: Tek geçerli katı; hacim bağıl hata<1e-9
  Ölçüm: `{"volume_mm3": 39999.99999999999, "expected_mm3": 40000.0}`
- **GEÇTİ — STEP dışa/içe aktarımı**: Hacim bağıl hata<1e-7; boyut hatası<1e-6 mm
  Ölçüm: `{"reimported_volume_mm3": 39999.99999999999, "bounding_box_mm": [200.0, 20.0, 10.0]}`
- **GEÇTİ — CAD mm3 -> SI m3 dönüşümü**: Analitik SI hacmiyle mutlak hata<1e-12 m3
  Ölçüm: `{"volume_m3": 3.9999999999999996e-05}`

## Oluşturulan çıktılar

- [plots/naca2412.png](../plots/naca2412.png)
- [plots/vlm_convergence.png](../plots/vlm_convergence.png)
- [plots/cad_coupon.png](../plots/cad_coupon.png)
- [cad/calibration_coupon.step](../cad/calibration_coupon.step)
- [cad/calibration_coupon.stl](../cad/calibration_coupon.stl)
- [data/input_guard_examples.json](../data/input_guard_examples.json)
- [data/neuralfoil_naca0012.csv](../data/neuralfoil_naca0012.csv)
- [data/vlm_panel_convergence.csv](../data/vlm_panel_convergence.csv)
- [data/numeric_calibration.csv](../data/numeric_calibration.csv)

## Kapsam ve sınırlar

- Girdi testleri belirli eksik/yanlış verileri yakalar. Bunlar ajan modelinin her hatasını veya halüsinasyonunu engellediğini kanıtlamaz.
- NACA grafiği geometri testidir. NeuralFoil kontrolleri kestirim modelinin entegrasyon ve fiziksel simetri kontrolleridir; deneysel doğrulama değildir.
- VLM küçük hücum açısında potansiyel akış testidir; hesaplanan sürükleme indüklenmiş bileşendir. Viskoz sürükleme, ayrılma ve stall burada doğrulanmadı.
- Yaklaşık kaldırma çizgisi referansı kaba bir tutarlılık kontrolüdür. Panel yakınsaması bu örneğe aittir, tüm geometriler için yeterlilik kanıtı değildir.
- CAD kuponu tek bir katı ve STEP aktarım testidir. Gerilme/deformasyon veya FEM çözümü yapılmadı.
- OpenVSP/VSPAERO ve XFOIL sonradan kurulup ayrı harici araç testleriyle doğrulandı. Bu komut temel Python/CAD kontrolleridir; harici analizler için Harici-Testleri-Calistir.cmd ve external_tools_report.md kullanılır.
- FreeCAD/CalculiX ve ANSYS kurulmadı. ANSYS ağır kurulum ve lisans aşamasına bırakıldı.
- Gerçek İHA gereksinimleri henüz bu klasörde doğrulanmadı. Güç, kararlılık, yapı, uçuş süresi ve hedef hız uygunluğu değerlendirilmedi.

## Yeniden çalıştırma

Üst klasördeki **Testleri-Calistir.cmd** dosyasını aç. Her çalıştırma araçları tekrar çalıştırır ve bu raporu günceller. Rapor, canlı internet erişimi gerektirmez.

Ham loglar: `C:\Users\Urungu\Documents\Codex\2026-10-18\bu\work\tests\logs\20261024-165526`

## Yöntem ve kurulum kaynakları

- [Codex proje talimatları](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [AeroSandbox](https://github.com/peterdsharpe/AeroSandbox)
- [VortexLatticeMethod](https://aerosandbox.readthedocs.io/en/master/autoapi/aerosandbox/aerodynamics/aero_3D/vortex_lattice_method/)
- [CadQuery kurulumu](https://cadquery.readthedocs.io/en/latest/installation.html)
- [NASA kaldırma denklemi](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/)
