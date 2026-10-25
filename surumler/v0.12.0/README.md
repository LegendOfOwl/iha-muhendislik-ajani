# v0.12.0 — CFD yakınsama kontrolleri ve birim denetimi

25 Ekim2026. 11yeni native SU2 koşusu; beş tamamlanmış eşli kıyasta ön kayıtlı ortak etki geçmedi, MG2 süre sınırında eksik kaldı. Fiziksel kabul false.

- SabitCFL, otomatikCFL, yerel çok seviyeli ağ, sonlu fark Newton–Krylov ve değişken ölçekleme araştırıldı; onaylanmayan hipotezler korunur.
- Newton iki farklı on/off çiftinde gerçekten çalıştı. Ortalama akış içindir; SA ayrı çözülür, adjoint veya arXiv artık yumuşatması değildir.
- Karışık boyutlu/boyutsuz kalıntı kıyası yanlış2,719195log kazanç gösterebilirdi. Aynı SI tanımında0,0550435log kaldı; yeni denetçi bu hatayı reddeder.
- 13eşli kıyas karşı örneği,4analitik/bozuk dönüşüm kontrolü ve26temel regresyon geçti. Native tam kalıntı özdeşliği taslağı başarısız olarak korundu.
- 187yeni dosya mühürü,40ön-native kod hash'i ve230eski CFD hash'i yeniden doğrulandı. Gerçek İHA girdileri değişmedi.
- Sonraki kayıtlı maliyet deneyi henüz çalıştırılmadı. Üç yakınsamış ağ, M6/RAE ve genel CAD→CFD yeterliliği açık; LLM davranış iyileşmesi ölçülmedi.

[Okunabilir sonuç raporu](../../raporlar/v0.12.0/README.md). Önceki tag ve Release varlıkları korunur. Bu sürüm artımlı yöntem/değerlendirme paketidir; sürüm sayısı uzmanlık veya fiziksel yeterlilik seviyesi değildir.
