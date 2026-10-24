# İHA mühendislik çalışma alanı

## Ortam ve kapsam
- Proje kökü bu dosyanın bulunduğu klasördür. Yolları buraya göre çöz.
- Sayısal hesaplar: `.venv/Scripts/python.exe`.
- CAD: `.venv-cad/Scripts/python.exe`; yalnız kurulup doğrulandığında kullan.
- Mevcut araçların gerçek yolları ve durumları `work/setup/tool_config.json` içindedir.
- Test komutu: `.venv/Scripts/python.exe work/tests/run_checks.py`.
- Kaldırma ön hesabında `work/engineering/evaluate_inputs.py` ve onun girdi kontrollerini kullan; bu araç bütün uçak fizibilitesini değerlendirmez.
- OpenVSP/VSPAERO: `work/setup/openvsp_install.json`; XFOIL: `work/setup/xfoil_install.json`. Yerel programlar kurulup gerçek analizlerle doğrulandı. OpenVSP Python bağlaması kurulmadı; AngelScript ve yerel .exe dosyaları kullanılıyor.
- Harici analiz + CAD + çizim komutu: `.venv/Scripts/python.exe work/native/run_all.py`. Ölçümler: `outputs/reports/external_tools_report.md`.
- Tek giriş: `outputs/Muhendislik-Merkezi.cmd`; birleşik durum/rapor: `outputs/Proje-Ozeti.html`.
- Proje iş akışı becerisi: `.agents/skills/iha-muhendislik/SKILL.md`. Mühendislik görevi için bu beceriyi oku.
- Güncel gerçek proje girdileri: `outputs/data/project/`; görev kayıtları: `outputs/data/tasks/`. Kavramsal adım durumlarını `conceptual_steps.json` içinde kanıtlarıyla tut.
- Tek komut girişi: `.venv/Scripts/python.exe -X utf8 work/agent/project.py`; `status`, `doctor`, `task`, `run core|native|fem|models|study` kullanılabilir. `doctor` yalnız yol varlığını, testler gerçek çalışmayı kontrol eder.
- FreeCAD 1.1.4 / CalculiX 2.22 / Gmsh SDK 4.15.2 kuruldu ve gerçek CAD->ağ->FE çözümüyle doğrulandı. Manifest: `work/setup/freecad_install.json`; test: `work/fem/run_fem.py` (.venv-cad). FreeCAD profilini `work/freecad/` altında tut; Windows geneli ayarlarını değiştirme.
- Parametreli üç kanat karşılaştırması: `work/studies/wing_study.py`; düzenlenebilir test girdisi `outputs/data/wing_study_case.json`. VSPAERO/XFOIL eşleştirmesi düşük açıdaki yaklaşık bir yöntemdir; tüm uçak sonucu değildir.
- K-1B Q8_0 / OpenSCAD ve Zero-to-CAD 2B Q6_K kuruldu. Manifestler `k_model_install.json` ve `cad_model_install.json`; değerlendirme `outputs/reports/cad_model_benchmark.json`. İki model de deneysel yardımcıdır: yerel üretim çalıştı, özgün çıktılar geometri kabulünü geçmedi. Otomatik mühendislik kabulü yapma. Codex'in sonradan düzelttiği çıktıyı küçük modelin başarısı sayma.
- Bu çalışma araç entegrasyonu ve proje iş akışıdır. Test modelini gerçek İHA tasarımı olarak sunma. ANSYS sonraki ağır kurulum/lisans aşamasındadır.

## Mühendislik kuralları
- İlgili proje verilerini ve `PROJECT_STATE.md` dosyasını oku. Eski sohbet varsayımlarını yeni gereksinim sayma.
- Kavramsal -> ön -> detay -> üretim -> test/doğrulama sırasını koru. Her aşamanın kendi hesap kontrollerini o aşamada yap.
- Her girdiyi `ölçülmüş`, `kaynaklı`, `kullanıcı gereksinimi`, `varsayım` veya `bilinmiyor` olarak işaretle.
- Her sayının birimini, kaynağını veya hesap yolunu, geçerli koşullarını ve mümkünse belirsizliğini kaydet.
- Hesaplarda SI kullan. CAD'in mm birimini açıkça dönüştür. AeroSandbox alpha/beta açıları derecedir.
- Eksik kritik girdiye varsayılan fiziksel değer atama. Gerekçelendirilmiş varsayım/aralıkla yalnız koşullu sonuç üret; veri yoksa bağlı sonucu `henüz değerlendirilemedi` olarak bırak.
- Eksik girdiler bağımsız işleri durdurmasın. Tamamlanamayan kontrolü ve sebebini görünür tut.
- Kaynakları gerçekten aç ve iddiayı desteklediğini kontrol et; kaynak, deney veya çözücü sonucu uydurma.
- Araçları gerçekten çalıştır; betik, girdiler, sürümler, ham çıktılar ve hata kayıtlarını sakla.
- Yöntemin Reynolds/Mach sayısı, geometri ve akış rejimi bakımından uygunluğunu denetle. Model dışı koşulları ekstrapolasyon diye işaretle.
- VLM sonuçlarını sürtünme/ayrılma/stall doğrulaması olarak kullanma. NeuralFoil bir kestirim modelidir; deneysel doğrulama sayma.
- XFOIL analizlerinde Re, Mach, Ncrit, geçiş koşulları ve yakınsamayan açıları raporla. 2D profilden tüm kanadın CLmax değerini otomatik türetme.
- VSPAERO'da Sref/bref/cref ve moment referansı aynı geometri/birimlere dayanmalı. Analiz kümesine hangi parçaların dahil olduğunu açıkça kaydet; çizilmiş gövdeyi kendiliğinden analiz edilmiş sayma.
- Yerel dosyalardaki tanımsız yardımcı katsayılar (ör. sıfır kaldırmada verim) nedeniyle geçerli CL/CDi satırlarını atma. Gerekli katsayılar sonlu olmalı; tanımsız yardımcı değerler null ve açıklamayla saklanmalı.
- Birim, büyüklük mertebesi, bağımsız referans ve gerektiğinde ağ/panel yakınsaması kontrollerini yap.
- Geçen yazılım testi fiziksel tasarımın doğrulandığı anlamına gelmez. Halüsinasyonsuzluk veya uçuşa elverişlilik garantisi verme.

## Kavramsal tasarım görevleri
1. Görev, hedefler, kısıtlar ve kabul ölçütlerini çıkar; çelişkileri kaydet.
2. Girdi/kaynak/belirsizlik tablosunu kur.
3. Bileşen bazında kütle bütçesi oluştur; bilinmeyenleri sıfır sayma.
4. Kanat yüklemesi, geometri ve düşük hız koşullarını birlikte tara.
5. Hıza bağlı sürükleme, gerekli/mevcut sürekli güç, enerji ve süreyi değerlendir.
6. Yerleşim, ağırlık merkezi, trim, kararlılık ve yapısal ön gereksinimleri kapsamına uygun değerlendir.
7. Birbirine bağlı hesapları tutarlı hale getir; duyarlılık ve belirsizlikleri incele.
8. Adayları aynı kısıtlarla karşılaştır. Her gereksinime `sağlandı`, `sağlanmadı` veya `henüz değerlendirilemedi` ve kanıt ekle.
- Her madde için tamamlandı/bekliyor/uygulanmıyor durumu tut. Uygulanmıyorsa gerekçe yaz.
- Kaldırma/stall hesabını hedef hızın, sürekli gücün, dayanımın veya kararlılığın kanıtı sayma.
- Kritik kontroller açıkken `tasarım tamamlandı` veya `uygun uçak` sonucu verme.

## Çıktı ve çalışma biçimi
- Kullanıcıya Türkçe, açık ve kısa yaz. Sonuçları varsayımlarından ayrı sun.
- Kullanıcı çıktıları: `outputs/reports`, `outputs/data`, `outputs/plots`, `outputs/cad`, `outputs/simulations`.
- Çalışma betikleri, ara veriler ve loglar: `work/`.
- Kalıcı kurulumların ve testlerin durumunu `PROJECT_STATE.md` içinde güncelle.
- Kullanıcının verdiği kapsam içinde ilerle; rutin, geri alınabilir işlemlerde tekrar izin isteme.
- Silme, sistem ayarı değiştirme ve fiziksel donanım kontrolünde mevcut yetkiyi ve riski ayrıca değerlendir.
