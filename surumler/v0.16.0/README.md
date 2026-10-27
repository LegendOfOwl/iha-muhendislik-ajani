# v0.16.0 — Kaynak derleme altyapısı ve karşılaştırma kontrolleri

Sabit SU2 v8.5.0, Eigen ve MEL kaynakları indirildi; 4357 kaynak dosyası arşivlerle birebir doğrulandı. C++17/Haswell/OpenMP dört iş parçacığı derleyici denemesi geçti. İlk gerçek SU2 derlemesi 259. hedefte başlık arama yolu hatasıyla durdu; kaynak baytlarını koruyan ortak arama yolu düzeltmesi kaydedildi. İkinci deneme kullanılabilir RAM 1 GiB sınırının altındayken native süreci başlatmadan reddedildi. 70 yeni yazılım kontrolü geçti; önceki 14 süreç kontrolünün kanıtı ayrıca denetlendi. Yeni CFD çalıştırılmadı; pristine32 yeniden üretimi ve cap256 etki/maliyet sınaması bekliyor. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

Tam izlenen uygulama/kaynak ağacı otomatik **Source code (zip)** tag arşivinde; ayrı büyük analiz dosyaları sürümün `analiz-arsivi-*.zip` varlıklarından katalog ve geri yükleme aracıyla özgün yollarına getirilir. `KAYNAK_INDIRME.md` ve `SHA256SUMS.txt` indirme ve dosya mühürlerini açıklar. Kurulu araçlar, üretilen harici programlar ve üçüncü taraf kaynak arşivleri dağıtıma dahil edilmez; kaynak kimliği, mevcut yama/lisans manifestleri ve derleme kayıtları korunur. Önceki sürümlerin varlıkları değiştirilmez.

[Ayrıntılı rapor](../../raporlar/v0.16.0/README.md) · [Dosya manifesti](manifest.json). Sürüm numarası fiziksel yeterlilik puanı değildir.
