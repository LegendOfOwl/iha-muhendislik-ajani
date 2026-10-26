# v0.14.0 — İç çözüm sınırı ve kalıntı konumu

26 Ekim 2026. Aynı ince ağ ve başlangıç alanında iç doğrusal çözüm sınırı 40→80 olarak değiştirildi. 200 adımlık eşli kontrolde yoğunluk kalıntısındaki kazanç 0.09148072 log10, SA kalıntısındaki değişim -0.09553239 log10 ve toplam Krylov işi oranı 1.50447718 oldu. Önceden belirlenen ortak etki kabulü geçmedi; başarısız deneme ve ham çıktılar korundu.

Kalan kalıntının yerini araştırmak için kaynak koduna dayalı, bir adımlık açık RHS ölçümü çalıştırıldı. Akış ve SA aşamalarının sıralı hesaplandığı bu tanıda beş RMS/MAX eşlemesi geçti: en büyük fark 1.14e-08 log10, native konservatif alan drift’i 4.67e-12. Haritanın yönlendirdiği LINELET kontrolü gerçekten etkinleşti; yoğunluk kazancı -0.03230637 log10, SA kötüleşmesi 0.05537677 log10 ve Krylov işi oranı 2.31080300 ile ortak etkiyi geçemedi. Norm ve konum bulguları ile sınırlamalar ayrıntılı raporda gösterilir. Bu çalışma yeni bir yakınsamış çözüm, deney doğrulaması veya genel CFD yeterliliği değildir. 37 yeni yazılım kontrolü geçti. Genel fizik, RAE2822, ONERA M6 ve gerçek İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

Tam izlenen uygulama/kaynak ağacı Release sayfasındaki otomatik **Source code (zip)** tag arşivinden indirilir. Yeni büyük CFD alanları `analiz-arsivi-*.zip` varlığındadır; dosya kataloğu ve geri yükleme aracı özgün yolları ve SHA256 değerlerini denetler. `KAYNAK_INDIRME.md` indirme açıklamasını, `SHA256SUMS.txt` bu sürümün yüklenen varlık mühürlerini taşır. Önceki sürümlerin varlıkları korunur.

[Okunabilir ayrıntılı rapor](../../raporlar/v0.14.0/README.md) · [Değişen dosyaların manifesti](manifest.json). Önceki tag ve Release varlıkları korunur. Sürüm numarası fiziksel yeterlilik puanı değildir.
