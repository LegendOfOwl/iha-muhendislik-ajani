# Proje durumu

Tarih: 2026-10-18 (Europe/Istanbul)

## Onaylı mevcut iş
Hafif kurulum tamamlandı. Kullanıcı şimdi OpenVSP/VSPAERO gibi harici programlarla gerçek modelleme ve aerodinamik analiz, daha anlamlı CAD çizimi ve çizime özel model araştırmasını istedi. Bu ikinci aşama onaylıdır. ANSYS sona bırakılacak.

## Gerçek İHA girdileri
Bu klasöre aktarılmış ve güncel olduğu doğrulanmış bir görev/gereksinim dosyası henüz yoktur. Kurulum testlerinin bütün sayıları sentetik test verisidir.

## Kurulum sırası
1. Ayrı Python ortamı, NumPy/SciPy/Matplotlib/pandas.
2. AeroSandbox/NeuralFoil ve optimizasyon doğrulaması.
3. Ayrı CAD ortamı, CadQuery ve STEP aktarım testi.
4. Gerektiğinde OpenVSP/VSPAERO, FreeCAD/CalculiX.
5. ANSYS: en son, kurulum ve lisans koşulları belirlendiğinde.

## Durum
- Hafif kurulum tamamlandı. Python 3.12.14 tabanlı iki ayrı ortam oluşturuldu; sistem PATH ayarı değiştirilmedi.
- Sayısal ortam: NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2, pandas 3.0.6, AeroSandbox 4.2.10, NeuralFoil 0.3.3, CasADi 3.8.1.
- CAD ortamı: CadQuery 2.8.0, OpenCascade Python paketi 7.9.3.1.1.
- Gerçek çalıştırmada 26/26 kontrol geçti. İki ortamın bağımlılık kontrolleri de geçti. Ayrıntılar `outputs/reports/setup_report.md` ve `test_results.json` içinde.
- Profil koordinatları, NeuralFoil değerleri, VLM panel yakınsaması, STEP/STL ve CAD önizlemesi üretildi.
- Boş girdi şablonu gerçek çalıştırmada eksikleri bildirdi; sayısal sonuç üretmedi (beklenen çıkış kodu 2).
- Mevcut Codex CLI 0.162.0-alpha.17.2: ChatGPT ile giriş durumu doğrulandı. Ek API anahtarı yapılandırılmadı.
- Paket sürümleri ve SHA-256 doğrulamaları sabitlendi. Ortam yolları `work/setup/tool_config.json`; yeniden kurma betiği `work/setup/rebuild_light.ps1`.
- Araç kurulum testi, LLM'nin her görevi hatasız yapacağını veya gerçek İHA'nın uygunluğunu kanıtlamaz.
- İkinci aşama: OpenVSP 3.55.0 / yerel VSPAERO 7.2.2 ve MIT yazar dağıtımından XFOIL 6.99 kuruldu. Kurulumlar proje içindeki `tools/` klasöründedir.
- Harici analiz/CAD kontrolleri: 26/26 geçti. Referans kanatta üç ağ; ince kanat ve kanat-kuyruk modeli için yedişer açı; iki profil için yedişer XFOIL viskoz noktası çalıştırıldı.
- Orta->ince kanat ağında CL değişimi %0,787; AeroSandbox ile aynı kanatta CL farkı %0,899. Bunlar deneysel doğrulama değildir.
- Uçak görünümlü parametreli OpenVSP örneği, native STEP/STL, üç görünüş SVG ve üç DXF üretildi. Gerçek OpenVSP STEP dosyası CAD çekirdeğinde tekrar açıldı; açıklık 2000 mm doğrulandı.
- Örnek gövde yalnız çizim/CAD içindir; VSPAERO taşıyıcı-yüzey kümesinden çıkarılmıştır. Kanat-kuyruk modelinin tüm geometri için ayrı ağ yakınsama çalışması bu aşamada yapılmadı; referans kanat ağ çalışması onun yerine sayılmamalıdır.
- İlk başarısız geometri, yakınsamayan 20-iterasyonlu 8 derece ve boş DXF denemeleri yakalandı; son raporda düzeltmeler ve sınırlar var. Eski ham loglar saklandı.
- Çizime özel modelin kimliği kesinleştirilemedi. Zero-to-CAD 1M veri kümesi, 2B görselden CAD modeli ve CADmium-1.5B araştırıldı; özel yerel CAD modeli kurulmadı.
- FreeCAD/CalculiX ve ANSYS kurulmadı. ANSYS ağır kurulum/lisans aşamasına bırakıldı.

## Sonraki gerçek görev
İHA'nın güncel görev ve gereksinimlerini kaynağıyla bu çalışma alanına aktar; ardından kavramsal tasarım girdileri ve bileşen kütle bütçesiyle ilerle. Eski test sayılarını gerçek proje verisi sayma.
