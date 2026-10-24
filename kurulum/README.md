# Kurulum ve mevcut yerel ortam

Windows x64 ve Python 3.12 gerekir. Uygulamanın proje kökü `uygulama/` klasörüdür; bütün kaynak ve raporların özgün bağıl düzeni burada korunur.

1. Kilitli Python bağımlılıkları: `uygulama/work/setup/requirements-core.txt` ve `requirements-cad.txt`. Mevcut hazırlama betiği: `uygulama/work/setup/rebuild_light.ps1 -PythonBase TAM_PYTHON_EXE_YOLU`.
2. Yerel solver/CAD/model kurulum betikleri ve kaynak/sürüm kayıtları `uygulama/work/setup` içindedir. Üçüncü taraf programların kurulu dizinleri ve model ağırlıkları depoya kopyalanmaz. Fusion OAuth, hesap erişimi ve lisanslar aktarılmaz. ANSYS ve OpenFOAM bu projede kurulmuş sayılmaz.
3. `tool_config.json` ve `*_install.json` özgün makine yollarını belgeliyor. Başka kurulumda bu yolları yeni araç konumlarına göre hazırlayıp `doctor` ve ilgili gerçek testlerle denetleyin. Bu yayın tek başına bütün ağır araçları otomatik kurduğu iddiasında değildir.
4. Aynı bilgisayardaki mevcut çalışma ortamına bağlanmak için `Yerel-Ortami-Bagla.ps1 -MevcutProje TAM_KAYNAK_KLASORU` kullanılır; yalnız bu depoda `.venv`, `.venv-cad` ve `tools` junction'ları oluşturur, global ayar değiştirmez.
5. Büyük analizleri geri yüklemek için `analizleri_geri_yukle.py` çalıştırın. İnternet ve birkaç GB disk alanı gerekir; indirme/çıkarma SHA256 ile denetlenir.
6. Hazır ortamda kökteki `BASLAT.cmd`, `uygulama/outputs/Muhendislik-Merkezi.exe` açar. EXE başlatıcıdır; klasörleri ve Python ortamları yanında kalmalıdır.

Yayınlama için kullanılan GitHub oturumu, auth dosyaları, yerel bağlantı ayarları ve tarayıcı ekran görüntüleri bu depoda bulunmaz. Teknik envanter ve kapsam `yayin_kapsami.json` dosyasındadır.
