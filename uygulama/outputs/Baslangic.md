# Mühendislik Merkezi — buradan başla

**[Muhendislik-Merkezi.exe](Muhendislik-Merkezi.exe) dosyasını çift tıkla, soldan projeni seç.** Aynı projenin görevleri, CAD dosyaları, analiz alanları ve raporları bu pencerenin içinde listelenir. [Güncel rapor ve kullanım](reports/projeler_exe_ve_profil_cfd.html).

- İHA projem gerçek girdiler içindir. Araç doğrulama örnekleri önceki kurulum testleridir. Profil ağı ve CFD doğrulaması yeni kaynak profilden ağ/CFD deneyidir. Yeni proje kendi boş girdilerini ve klasörlerini oluşturur.
- Proje özetinden CAD programını seç. FreeCAD/OpenVSP tercihi projeye kaydedilir. Uyumlu aktif model varsa onunla, yoksa boş açılır. Yeni dosyayı projenin CAD klasörüne kaydet. Proje dosyalarından dışarıdaki modeli kopyalayabilir ve aktif seçebilirsin.
- Görev ve kısıtlar bölümünde isteği/bildiğin değerleri yaz. Boş alan bilinmiyor kalır. Taslak proje değiştirince korunur; henüz görev kaydı oluşturulmamış olabilir.
- Yalnız bu projeye kaydet isteği dosyaya yazar. Bu sohbette kaydedilen görevi incelememi söyleyebilirsin. Kaydet ve ajanla başlat seçili proje bilgileriyle ayrı Codex terminal penceresi açar; bu sohbete otomatik mesaj göndermez.
- Görevler ve çalışmalar bölümünde hazırlanmış analizleri seç. Girdi tanımı yoksa düğme kapalıdır; eski örnek bu projenin sonucu yerine kullanılmaz. CAD eklemek tek başına uygun CFD ağı ve sınır koşulu hazırlamaz.
- Proje dosyaları filtresinden rapor/grafik/alan aç. STEP/FCStd FreeCAD'de, VSP3 OpenVSP'de, MSH/POS Gmsh'de açılır. VTU ham alandır; ParaView kurulu sayılmaz.

EXE küçük başlatıcıdır; mevcut Python/araçlar ve bütün proje klasörleri birlikte kalmalı. CMD aynı yeni arayüzün yedeğidir. Ajanın dosya ve komut girişleri korunur.

Projeler data/projects/, yeni sonuçlar projects/<kimlik>/ altında. İlk İHA'nın eski data/project/ girdileri yerinde korundu. Görevler data/tasks/ içinde proje kimliğiyle tutulur. Aktif CAD değişirse eski analizle eşleşmesi yeniden gerekir. STEP özellik geçmişini kendiliğinden taşımaz.

İleri kullanım: .venv/Scripts/python.exe -X utf8 work/agent/project.py run GRUP --project KIMLIK. geometry, complex-vlm ve profile-cfd hazırlanmış proje tanımı ister. Diğer eski gruplar qualification araç örnekleridir; aerostruct resmî OpenAeroStruct örneklerini çalıştırır. doctor yalnız yol varlığını, gerçek testler çalışmayı denetler.

[OpenAeroStruct ve ajan kuralları](reports/openaerostruct_ajan_yaklasimi.html), [önceki CAD/VLM/SU2 raporu](reports/muhendislik_seviyesi_ve_cfd.html), [eski hafif CFD iş akışı](reports/hafif_cfd_ve_is_akisi.html), [CAD modeli araştırması](reports/proje_durum_ve_k1b_arastirma.html).

Fusion girişi tamamlandı; bu sohbette motor, lisans/hub ve parametrik model/STEP testi bekliyor. Küçük CAD modelleri deneysel yardımcıdır. Euler profil kabulü eski RANS veya3D uçak kabulünü kapatmaz. Gerçek uçak için güncel görev/bileşen verileri ayrıca gerekir. Kurulum testleri uçuşa elverişlilik garantisi değildir. ANSYS sona bırakıldı.
