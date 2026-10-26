# Kalan CFD artığını konumlandırma ve kontrollü yöntem kıyası

26 Ekim 2026 · Dört yeni native SU2 koşusu · Genel fizik/M6/İHA kabulü **false**.

Bu turda yeni bir yakınsama çözümü doğrulanmadı. Buna karşılık, çözücünün gerçek doğrusal olmayan artığını nerede ürettiğini gösteren ölçüm yöntemi doğrulandı. Bu, son denemelerden daha fazla ayar taramadan bilgi çıkarabilmemizi sağlıyor. Sabit kaynak benchmarkıdır; keyfi CAD için genel analiz hizmeti değildir.

## Önceden kayıtlı40→80 kontrolü

İki taze kol aynı ince kaynak ağı, aynı ND restart baytları, aynı fizik ve aynı adaptive CFL politikasıyla200 adım çalıştı. Yalnız LINEAR_SOLVER_ITER değişti; bu ortak ayar akış ve SA iç çözücüsünü etkiler. Sonraki CFL yörüngeleri aynı olmaya zorlanmadı; gözlenen etki bu geri beslemeyi de içerir. Eski3999-adımlı koşunun kesintisiz devamı sayılmaz.

| Tek config değişimi | SI yoğunluk kazancı,log10 | SI SA kötüleşmesi,log10 | Krylov işi oranı | Ortak etki |
|---|---|---|---|---|
| İç tavan40→80 | +0.09148072 | -0.09553239 | 1.50447718 | Geçmedi |
| LU_SGS→LINELET | -0.03230637 | +0.05537677 | 2.31080300 | Geçmedi |

Geçme şartı yoğunlukta en az0,3log ek düşüş, SA'da en fazla0,1log kötüleşme ve toplam Krylov iterasyonu oranı≤1,5 idi.40→80 oranı1,50447718 olduğu için **1,5'e yuvarlayıp kabul etmedik**. Yoğunluk kazancı0,09148072 ile0,3'ün altında kaldı. Bu vaka için yalnız daha yüksek iç tavanı çözüm olarak seçmedik. Başka tavan değerlerini otomatik taramadık.

Gerçek süre/RAM gözlemleri: LU_SGS40 **40,578s/0,285GiB**; LU_SGS80 **79,563s/0,442GiB**; LINELET40 **55,594s/0,292GiB**. Bunlar tek yerel koşunun gözlemleridir. FGMRES alt uzayı büyüdükçe ortogonalizasyon ve bellek maliyeti değişir; toplam iterasyon sayısı gerçek FLOP veya genel hızlanma değildir.

![Aynı başlangıçla üç sayısal kol](../plots/inner_cap_linelet_20261026.png)

## Doğru artığı dışarı almak

SU2'nin implicit çözümünde VTU Residual_Density çalışma vektöründen yazılır; iç doğrusal çözüm onu değiştirebilir. History'deki cached RMS ile aynı olduğu varsayılmadı. Kurulu8.5.0 kaynaklarında explicit Euler akış ve SA adımlarının bu vektörü okuyup çözüm artışını ayrı tuttuğu incelendi. Aynı özgün fine3999 restartından **tek adım**, CFL1e-6, MG0 ve explicit akış+SA ile yeni gözlem yapıldı. Bu yaklaşık1s sürdü; yakınsama deneyi veya fiziksel iyileştirme değildir.

Kabul sözleşmesi ölçümden önce kaydedildi: beş denklemin hem RMS hem MAX farkı≤1e-6log;52689 sahip olunan noktanın bire bir koordinat eşlemesi≤2e-7m; native double restartta dört konservatif alanın her birinin bağılL2 drift'i≤2e-6; sonlu değerler ve pozitif yoğunluk/basınç. Duvar ve sınır noktaları normdan çıkarılmadı. Norm hacim ağırlıksız sqrt(ΣR²/N) biçimindedir; MPI halo yoktur.

| Denklem | Native RMS,log10 ND | İhraç RMS farkı,log10 | İhraç MAX farkı,log10 |
|---|---|---|---|
| Rho | -12.38121851 | 9.76e-10 | 1.14e-08 |
| RhoU | -12.78760240 | 3.19e-09 | 1.05e-08 |
| RhoV | -14.40020272 | 2.57e-09 | 4.99e-09 |
| RhoE | -13.45077818 | 4.49e-09 | 9.43e-09 |
| nu | -17.27642012 | 1.16e-09 | 4.12e-09 |

**Beş RMS/MAX birlikte geçti.** En büyük log farkı1,14e-8; koordinat eşleme en büyüğü6,51e-8m. Konservatif native alan drift'i en çok4,67e-12; ν̃ drift'i3,65e-16 ayrı gözlem olarak saklandı. Float32 VTU yuvarlaması native double drift'in yerine kullanılmadı. Her52689 düğüm ve geçerlilik bilgisi CSV'de korunuyor.

Akış artığı akış güncellemesinden önce, SA artığı bu küçük akış güncellemesinden sonra ve SA güncellemesinden önce hesaplanır. Harita bu **sıralı aşamaların artığıdır**; son çıktı alanının yeniden hesaplanmış artığı diye sunulmaz. Sabit SI çarpanı aynı denklem içindeki kare paylarını değiştirmez; farklı denklemlerin payları tek bir fiziksel hata bütçesi olarak toplanmaz.

## Artık nerede yoğunlaşıyor?

Yoğunluk artığının kare toplamının **%99,626'sı** x=0,5–2m/y=0–0,05m arka sınır tabakası bölgesinde; **%99,972'si** y≤0,02m duvar yakınında. En yüksek düğüm(x,y)=(1,9785208m,0m). Tüm kare toplamının%90'ını3964 düğüm (%7,523) taşıyor. Başlangıç kenarındaki ön tanımlı bölgenin payı yalnız%0,055924; önceki Cf kaynak farkı ile baskın yakınsama artığı aynı gözlem değildir.

| Ön tanımlı bölge | Düğüm | Yoğunluk artığı kare toplamındaki pay |
|---|---|---|
| leading_edge | 4719 | 0.0559241% |
| near_wall | 28740 | 99.9723599% |
| upstream | 9386 | 0.0171877% |
| inlet_strip | 193 | 0.0103361% |
| outlet_strip | 193 | 0.9417695% |
| top_strip | 273 | 0.0058136% |
| aft_boundary_layer | 12298 | 99.6263502% |
| outer_core | 10958 | 0.0002850% |

Bölgeler önceden tanımlı ve örtüşür; payları bir bölümleme gibi toplamayın. SA artığının dağılımı farklıdır: upstream bölgede yaklaşık%72,00; en yüksek düğüm x≈−0,002001m/y≈1,000465e-6m. Bu, türbülans denkleminin dominant yoğunluk artığıyla aynı yerde olması gerektiği anlamına gelmez. Lokal artık bir kestirme ağ hata bandı, deney hatası veya kesin nedensel teşhis değildir.

![Doğrulanmış sıralı aşama artıklarının kare payı](../plots/residual_probe_20261026.png)

## Haritanın yönlendirdiği tek aday: LINELET

Duvar yakınındaki artık ve kaynak ağın çok gerilmiş normal hücreleri, normal bağlaşımı birlikte çözen LINELET'i bir kez sınamayı gerekçelendirdi. Bugünkü LU_SGS40 kolu aynı seed/ağ/config kontrolleriyle yeniden kullanıldı; yeni200-adımlık kolda yalnız LU_SGS→LINELET değişti. Kaynak rehber ve8.5.0 uygulaması arşivlendi. Eşikler önceki kıyasla aynı kaydedildi; fizik değiştirilmedi.

Native log, **Using a linelet preconditioning.** ve **Computed linelet structure,32 points in each line (average).** mesajlarıyla yöntemin gerçekten çalıştığını gösterdi. Kaynak algoritmada çizgi başına en fazla32 nokta var; tüm193 normal düğümün veya bütün sınır tabakasının birlikte çözüldüğü söylenemez. Çizgilerde blok tridiagonal, çizgi dışında blok Jacobi kullanılır; LU_SGS'nin diğer bağlantılarını zayıflatabilir.

Bu kol yoğunlukta0,03230637log **daha kötü** kaldı; SA0,05537677log kötüleşti, Krylov oranı2,31080300 oldu. Kayıtlı ortak etki geçmedi. Tavanı artırma ve LINELET, bu eşleşmiş vakalarda yeterli çözüm olarak desteklenmedi; bütün akışlarda işe yaramaz ilan edilmedi. Kalan artığın kesin nedeni henüz bilinmiyor. Sonraki araştırma, gerçek çizgi kapsamı ve akış/normal yönlerdeki bağlaşımın ayrılması olmalı; yeni parametre taraması yapılmadı.

## Hatalar, kayıt ve sınırlar

- Explicit gözlem exit0 ile bir kez tamamlandı. Genel implicit mühürleyici, çözülmeyen doğrusal sistemin LinSolRes=−inf yardımcı sütununu zorunlu saydığı için hata verdi. Ham log ve başarısızlık korundu; yalnız bu explicit kapsam için yardımcı değer null/açıklamalı yapıldı. Beş RMS/MAX zorunluluğu korunarak yeni mühür alındı; CFD yeniden çalıştırılmadı. Bu istisnanın implicit/başarısız koşuya taşınmasını önleyen beş test eklendi.
- Dokuz maliyet/etki ve28 norm/konum/drift/explicit-mühür kontrolü geçti. Test kayıtçısının Path tür hatası ayrı taslak ve logla korundu, düzeltildi; native alan etkilenmedi. Bunlar37 yazılım kontrolüdür, LLM uzmanlığı kanıtı değildir.
- Yeni mühürlerde61 ham hash, ön-native kod arşivlerinde31, önceki dondurulmuş sonuçlarda632 hash doğrulandı. GerçekİHA'nın3 girdi dosyası v0.13 ile aynı.
- Eski üç-ağ fine rolü3999 ve onun başarısız yoğunluk kapısı değiştirilmedi. Yeni200-adımlık kolları aileye sonradan geçirip kabul kapatmadık. M6/RAE/VLM/İHA ve genel CFD kabulleri açık; GCI null. Bu oturum kör LLM değerlendirmesi değildir; benchmark cevapları operasyonel analizci derslerine eklenmedi.

[40/80 tüm sonuçlar](flatplate_inner_cap_20261026.json) · [LINELET sonucu](flatplate_linelet_20261026.json) · [RHS ölçüm ve konum kanıtı](residual_probe_20261026.json) · [Mühür/koşu denetimi](residual_diagnostics_integrity_20261026.json) · [Yazılım kontrolleri](residual_probe_guards_20261026.json)

## Birincil kaynaklar

[SU2 doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/), [explicit akış uygulaması](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/solvers/CFVMFlowSolverBase.hpp), [SA explicit adımı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/solvers/CScalarSolver.inl), [RMS/MAX hesapları](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/solvers/CSolver.cpp), [çıktı semantiği](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/output/CFlowCompOutput.cpp), [linelet sınırı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/include/geometry/CGeometry.hpp), [çizgi üretimi](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/geometry/CGeometry.cpp), [matris işlemleri](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/linear_algebra/CSysMatrix.cpp). Yerel kaynak URL/zaman/SHA256 manifestleri ayrıca tutulur.
