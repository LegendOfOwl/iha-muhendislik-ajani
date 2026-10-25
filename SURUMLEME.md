# Sürümleme ve yayın politikası

- v0.1.0–v0.10.0 ilk geriye dönük kanıt gruplarıdır. Eski tag, release veya başarısız sonuçlar yeniden yazılmaz.
- v0.11.0 ilk gerçek artımlı güncellemedir. Bundan sonra her anlamlı tamamlanmış değişiklik Git commit’iyle izlenir.
- Yeni yöntem/entegrasyon veya değerlendirme paketi:0.x.0 minor; uyumlu hata/belge düzeltmesi:0.x.y patch. Bu numaralar fiziksel yeterlilik seviyesi değildir.
- Sürüm sorumluluğu bu çalışma için Codex’e verildi. Her yayın VERSION, CHANGELOG, değişen dosya manifesti, sonuçların kapsamı ve bilinen açık kapıları taşır.
- Kaynak/rapor/çizim/küçük loglar Git’e; büyük ham ağ/alan/restartlar hash kontrollü Release ZIP’lerine gider. Kimlik bilgileri, kurulu araçlar, model ağırlıkları ve derleyici paketleri yayımlanmaz.
- Yeni arşivlerde aynı içeriğin tek ZIP üyesini birden çok hedef dosya kullanabilir. Katalog her özgün hedef yolunu/SHA256’yı korur; geri yükleyici bu eşlemeyi denetler. Eski arşiv biçimi de desteklenir.
- Önce katalog, arşivler, gizli bilgi taraması, geri yükleme ve dosya hash’leri denetlenir; sonra normal fast-forward push, değişmez tag ve Release yayımlanır. Zorlayarak push yapılmaz.
- Yazılım/paket testi ile sayısal/deneysel doğrulama ayrı açıklanır. Geçmeyen CFD kapısı, yeni sürüm yayımlanınca geçmiş sayılmaz.
- Bir sonraki yayın: aynı geliştirme klasöründe work/publish altındaki güncel yardımcıları kullan; önceki yayının HEAD ve katalog hash’lerini doğrula. Yerel yayın durumunu GitHub’daki güncel dal/tag/asset durumuyla yeniden karşılaştır.
