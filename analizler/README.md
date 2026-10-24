# Analizler ve ham alan arşivleri

Çözücü ayarları, küçük veriler, raporlar ve görseller `uygulama/outputs` içinde özgün bağıl yollarıyla bulunur. Büyük ağ/alan/restart dosyaları GitHub Releases içindeki `analiz-arsivi-*.zip` paketlerindedir. Hiçbir ham dosyanın içeriği değiştirilmez; SHA256 ve geri yüklenecek yol dosya kataloğunda bulunur.

- [Dosya kataloğu ve arşiv URL'leri](dosya_katalogu.json)
- [RAE2822 sonuçları](../uygulama/outputs/projects/proje-15cce2de02/reports/)
- [ONERA M6 sonuçları](../uygulama/outputs/projects/proje-e9319baef1/reports/)
- [Örnek CFD, FEM ve model çalışmaları](../uygulama/outputs/simulations/)

Arşivleri depo köküne çıkarmak özgün `uygulama/...` yollarını tamamlar. Otomatik ve hash kontrollü geri yükleme için `kurulum/analizleri_geri_yukle.py` kullanılır. Ham alan isteyen rapor bağlantıları arşiv geri yüklenene kadar yerel diskte bulunmaz. Bu depodaki sayısal/deney kabulleri kendi kapsamlarıyla sınırlıdır; genel RAE/M6 fizik yeterliliği geçmedi.
