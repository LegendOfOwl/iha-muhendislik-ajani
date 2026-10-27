# GitHub v0.15.0 yayın makbuzu

27 Ekim 2026 · **Yayın ve uzak doğrulama tamamlandı.**

[Release](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/v0.15.0) · [GitHub'da ayrıntılı CFD raporu](https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/v0.15.0/raporlar/v0.15.0/README.md)

- Main ve yeni annotated tag aynı kaynak commitini gösteriyor: `c4cbc871cb7c8dbfddd78782dcc71d67d0d8f821`. REST ile aktarılan dosya ağacı, commit ve tag nesnelerinin kimliği yerel Git nesneleriyle bire bir eşleşti.
- Üç yeni varlığın boyutu ve GitHub sunucu SHA256 değeri yerel dosyayla aynı. Analiz arşivi 17.110.014 bayt (16,32 MiB); indirme açıklaması ve SHA listesi ayrıca var.
- Önceki 14 Release, 33 dosya ve 28 tag referansı ön-yayın anlık kaydıyla aynı. Toplam 15 Release ve 36 varlık var.
- 6307 kaynak Git blobu, 14 geri yükleme kontrolü, 16 gerçek ham hedef yolu ve 49 belge bağlantısı denetlendi. 6405 dosyanın taramasında kayıtlı gizli bilgi bulgusu yok. Temiz VM'de solver kurulumu sınanmadı.
- Yerel Git aktarımında DNS/TLS ve son API okumalarında kesintiler yaşandı. Gönderim resmî GitHub REST API'siyle, son uzaktan denetim bağlı GitHub aracının değiştirilmemiş JSON yanıtlarıyla tamamlandı. Sistem DNS/hosts, global Git veya TLS güvenlik ayarı değiştirilmedi. Yalnız süreçte denenmiş adres çözümleme/HTTP1.1 ayarları kalıcı değildir ve son doğrulamanın dayanağı değildir.
- Tam izlenen kaynak otomatik GitHub Source code ZIP'inde; ZIP'in bayt hash'i iddia edilmiyor. Commit, katalog dosya hash'leri ve ayrıca yüklenen üç varlığın sunucu hash'leri kanıttır.

Bu yayın genel CFD/M6/İHA fizik kabulü veya LLM davranış iyileşmesi değildir. Üç native koşu ve 17 yeni yazılım kontrolünün kapsamı CFD raporunda. Uzun çizgili kaynak derlemesi henüz uygulanmadı. Yayın sonrasında oluşan bu makbuz ve durum metadata'sı sonraki artımlı katalogda alınır.
