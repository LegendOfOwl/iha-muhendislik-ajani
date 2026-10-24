# Araştırma ek kaydı 01 — sayısal teşhis, kabul eşiği değişikliği yok

Başlangıç: özgün v3 C-grid/coarse, native çözüm 1103. satıra kadar yazdı;
`Residual > 10^20` nedeniyle çözücü kendisi hata ile çıktı. Ana ajan onu
durdurmaya karar vermişti fakat Stop-Process işlemine ulaşmadan süreç bitmişti;
bu nedenle ilk deneme elle durdurulmuş diye etiketlenmez. Son tam alan1000.

Önceki plan mührü korunur. Aşağıdaki dallar aynı coarse mesh ve aynı1000
restartından başlar. Fiziksel sayılar ve deney eşikleri sabittir.

| Dal | Karşılaştırma | Tek değişen sayısal politika | Teşhis |
|---|---|---|---|
| coarse_cfl1 | özgün coarse1000 sonrası | adaptif1..6 → sabit1 CFL | V2'de işe yarayan zaman adımı denetiminin bu yeni ağda işe yarayıp yaramadığını sınar; beklenen Cp kullanılmaz. |
| coarse_cfl1_mg0 | coarse_cfl1 | MGLEVEL3 →0 | Aynı başlangıçla multigrid etkisini ayırır. |
| coarse_entropy0p2 | coarse_cfl1 | ENTROPY_FIX_COEFF0.05 →0.2 | Yalnız minimum özdeğer yayınımı; yeni CFL/MG değişimi birlikte yapılmaz. |
| reference_sourcegrid_sa2 | yakınsamış reference_sourcegrid5752 | MUSCL_TURB NO → YES | Türbülans taşınımı uzaysal mertebesini aynı ağ ve fizik üzerinde ayırır. |

Yeni kaynaklar gerçekten açıldı:

- [SU2 v8.5.0 RAE2822 test config](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/TestCases/rans/rae2822/turb_SA_RAE2822.cfg):
  WLS/MG3/W-cycle ve birinci mertebe türbülans mevcut örnekte bulunuyor.
  Eski ayarlar API uydurması değil; örnek dosya doğruluk kanıtı da değil.
- [SU2 bakımcısının 2022 RAE2822 ağ/kararlılık cevabı](https://github.com/su2code/SU2/discussions/1522):
  aşırı uzamış iz hücrelerinin multigrid ve yakınsamayı bozabileceği yönündeki
  vaka önerisi MG0 hipotezini destekler. Eski yazılım hatasını bizimv8.5.0
  çalışmamızın nedeni diye göstermiyoruz.
- [SU2 resmî akı şemaları kılavuzu](https://su2code.github.io/docs_v7/Convective-Schemes/):
  JST_MAT minimum özdeğer eşiği için0.05–0.2 aralığı, arttıkça daha çok yayınım;
  örtük Jacobian katsayısı da ayrı bir sayısal ayardır. İlk test yalnız
  ENTROPY_FIX'i değiştirir, Jacobian katsayısı4 kalır.
- [Palacios ve diğerleri, AIAA2014-0243](https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf),
  baskı sayfa23/33: RAE2822 için ikinci mertebe scalar upwind türbülans ve
  GMRES doğrusal toleransı1e-6 kullanılmış. Bunlar bizim kod örneğinin
  sayısal ayarlarından farklıdır; SA2 denemesinde yalnız taşınım mertebesi
  değişir, doğrusal tolerans ayrıca sabit kalır. Makaledeki T273.15K'yi
  NASA'dan önceden seçilmiş255.5556K yerine kopyalamayız.
- [NASA/TMBWG SA tanımı](https://tmbwg.github.io/turbmodels/spalart.html):
  SA-noft2 ve uygun3ν∞ girişinin çoğu pratik yüksekRe durumda SA'ya yakın
  sonuç vermesi beklenir; farkı kanıtsız tek hata nedeni yapmıyoruz. Fiziksel
  trip ve model değişikliği bu sayısal ayar çalışmasına karıştırılmaz.

Kaynaklı yeni hipotezler, aynı disk/model geçmişindeki ana ajan tarafından
değerlendirilir. Bu yeni bir bağımsız kör deney değildir.

Orta ağ için kendi V2 fine3400 alanından yalnız başlangıç tahmini aktarıldı.
Bu test henüz çalışmadı. Interpolasyonun165 geçersiz VTK noktası ayrı kaydedildi;
sıfır yer tutucuları kullanılmadı, yalnız başlangıç için yakın kaynak düğümü
değeri kondu. Native çözümün tekrar yakınsaması zorunludur. Kaynak/katı geometrisi
değişmedi. İlk plandaki uniform başlangıçtan bu değişiklik hız içindir;
çıktıyı kabul edilmiş analiz yapmaz. Yakınsama problemi çözülmeden pahalı
orta/ince çözümleri başlatmıyoruz; eksik kapılar açık kalır.
