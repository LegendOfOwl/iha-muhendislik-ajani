# v0.15.0 — LINELET kapsamı ve LU-SGS bölünmesi

27 Ekim 2026. Üç yeni native SU2 koşusu tamamlandı. Gerçek LINELET alanında 52689 düğümün 7200 tanesi çizgilerde; önceki doğrulanmış aşama artığının yoğunluk kare toplamının %53.8965’i bu birliğin içinde. Bu konumsal kapsam ölçümüdür; yeni alanın yeniden hesaplanan artığı, nedensellik veya ağ hata bandı değildir.

Aynı kaynak ağ ve başlangıç dosyasıyla, toplam dört iş parçacığı korunarak yalnız LU-SGS önkoşullayıcısının bölünmesi 0→1 değiştirildi. 200 adımlık çiftte yoğunluk kazancı 0.14072006 log10, toplam Krylov işi oranı 1.54404968, gözlenen süre oranı 3.62357987 oldu. Ön kayıtlı ortak etki ve maliyet kabulü geçmedi. 17 yeni yazılım kontrolü geçti; başarısız denemeler ve ham çıktılar korundu. Uzun çizgili kaynak derlemesi sonraki yöntem adayıdır; henüz derlenmedi veya çalıştırılmadı. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

Tam izlenen uygulama/kaynak ağacı otomatik **Source code (zip)** tag arşivinde; yeni büyük alanlar `analiz-arsivi-*.zip` dosyasındadır. `KAYNAK_INDIRME.md`, `SHA256SUMS.txt`, dosya kataloğu ve geri yükleme aracı özgün yolları ve dosya mühürlerini açıklar. Önceki sürümlerin varlıkları korunur.

[Ayrıntılı rapor](../../raporlar/v0.15.0/README.md) · [Dosya manifesti](manifest.json). Sürüm numarası fiziksel yeterlilik puanı değildir.
