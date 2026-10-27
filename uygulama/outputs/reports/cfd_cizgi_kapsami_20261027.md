# Gerçek LINELET kapsamı ve önkoşullayıcı bölünmesi

27 Ekim 2026 · Üç gerçek native SU2 koşusu · Yeni genel fizik/M6/İHA kabulü **false**.

Bu tur, önceki başarısız LINELET denemesinin gerçekten hangi bölgeyi içerdiğini ölçtü. Ardından kaynak kodundaki LU-SGS bölünmesini kaldıran tek kontrollü yöntem sınandı. **Kapsam ölçümü geçti; yeni çözüm ayarı etki/maliyet kabulünü geçmedi.** Bu sabit 2B SA-neg kaynak benchmarkıdır; yeni bir uçak analizi veya kör LLM değerlendirmesi değildir.

## Kaynak sabiti yerine gerçek kapsam

Kurulu SU2 v8.5.0'ın CFVMOutput uygulaması, LINELET seçiliyken native `Linelet` alanını dışarı yazabiliyor. Kaynak geometrinin `lineletColor` dizisi kullanılır:0 çizgi dışı, pozitif tamsayılar komşuluk renklendirmesidir. Aynı rengi paylaşan noktalar tek bir çizgi sayılmadı.

Ön kayıttan sonra aynı özgün fine3999 ND başlangıç dosyasıyla **tek implicit adım** çalıştırıldı. Fizik/ağ aynı; 200→1 adım, yazma sıklığı 1 ve ek LINELET çıktısı ölçüm değişiklikleridir. Native exit0; 1,563 s, yaklaşık 0,294 GiB örneklenmiş tepe çalışma kümesi. Alan/yüzey/restart/geçmiş 0 eşleşip mühürlendi. Bu adımın amacı yakınsama değildir.

- 52689 düğümün **7200'ü (%13,6651)** gerçek LINELET birliğinde.
- Birliğin y aralığı 0–**5. 3065788069e-05m**, yaklaşık 53,1 µm.
- Önceki doğrulanmış aşama RHS haritasının yoğunluk kare toplamının **%53. 89653**'i bu birlik içinde; **%46. 10347**'i dışında.
- SA kare toplamının yalnız **%0. 014798**'i içinde. Yoğunluk ve SA farklı denklemlerdir; bu paylar tek fiziksel hata bütçesi olarak toplanmaz.
- 52689 nokta bire bir eşlendi, en büyük koordinat farkı 6,51e-8 m; ön kayıtlı sınır 2e-7 m. Bütün düğümler CSV'de kaldı. Bağımsız tablo denetimi işaret/renk/tamsayı/üyelik ve normalize negatif olmayan kare paylarını yeniden kontrol etti.

![Gerçek native çizgi birliği ve ayrı aşama RHS](../plots/linelet_coverage_20261027.png)

Bu, yeni implicit alanın yeniden hesaplanmış artığı değildir. Geometriye bağlı statik üyelik, **önceki ayrı explicit gözlemin sıralı akış/SA aşama RHS** değerleriyle eşlendi. Artık payı ağ hata bandı veya başarısızlığın kesin nedeni değildir. 32 nokta sınırı kaynakta sabittir; uzunluğun artırılması da izotropi/yön/komşuluk durdurmalarını kaldırmaz. Native alanın renkleri benzersiz çizgi kimliklerini vermez.

## Kaynakla gerekçeli tek değişken

CSysMatrix, `LINEAR_SOLVER_PREC_THREADS=0` iken maksimum OpenMP iş parçacığı sayısını bölge sayısı olarak kullanıyor. LU-SGS alt/üst üçgensel çarpımları her bölgenin başlangıç/bitiş satırıyla sınırlanıyor; kaynak, thread-halo olmadığına açıkça işaret ediyor. `=1` tek üçgensel bölge seçer. Bu, sınır ötesi üçgensel bağlaşımı geri getirebilir hipoteziyle sınandı; varsayılan ayarın kesin hata olduğu kabul edilmedi.

İki kolun toplam native iş parçacığı sayısı **dört** kaldı. Configler yalnız PREC_THREADS 0/1 satırında farklı. Aynı özgün fine3999 seed baytları,52224 hücre/52689 nokta kaynak ağı, LU_SGS/FGMRES 40 ve iç tolerans0,001 kullanıldı. Her kolda 200 adım/240 s üst bütçe,2,5 GiB bellek sınırı; fizik ve kabul eşikleri değiştirilmedi. Aynı adaptive CFL politikası korundu, gerçekleşen CFL yörüngeleri eşitlenmedi. Bu fark politika geri beslemesini de içerir. Native bölge dizisi doğrudan dışarı yazılmadı; 0→4/1 yorumu kabul edilen config ve eşleşen8.5.0 kaynak semantiğine dayanır.

| Kol | Yoğunluk, SI log10 | SA, SI log10 | Krylov toplamı | Gözlenen süre, s | CD |
|---|---|---|---|---|---|
| Varsayılan bölünme 0→4 | -9. 793985228 | -12. 299814785 | 6924 | 65. 047 | 0. 002848053098 |
| Tek önkoşullayıcı bölgesi 1 | -9. 934705288 | -12. 480820155 | 10691 | 235. 703 | 0. 002848045076 |

Her iki native exit0 ve alan/geçmiş 199 eşleşti; son100 örnek mevcut. Yoğunluk kazancı **0. 14072006 log10**, gereken ≥0,3'ün altında. SA kötüleşmesi **-0. 18100537 log10**; negatif değer iyileşmedir ve ≤0,1 şartını geçer. Toplam akış+SA Krylov oranı **1. 54404968**, kayıtlı ≤1,5'i geçmedi. Süre oranı **3. 62357987**, önceden kayıtlı ≤1,5'i geçmedi. **Ortak etki false.** Tek süre çifti evrensel hız ölçümü değildir; donanım/işletim sistemi yükü etkisini ayıran performans çalışması yapılmadı. Bu sınırlama, başarısız yoğunluk/Krylov sonuçlarını değiştirmez.

![Aynı başlangıçtan iki bölünme kolu](../plots/prec_partition_20261027.png)

Tek bölge yoğunluk SI≈−9,934705 ile **−10 eşiğini geçmez**. Yakın görünmesi kabul değildir. Bu200adımlık tanı eski üç-ağ ailesindeki fine3999 rolünün yerine konmadı; aile ve genel fizik kabulleri kapatılmadı. Süreyi/iterasyonu otomatik uzatmadık,2/3 bölge değerlerini taramadık.

## Literatürden çıkan uygulanabilir ayrımlar

[Palacios ve Alonso,2011](https://web.stanford.edu/group/ctr/ResBriefs/2011/26_palacios.pdf), gerilmiş ağlarda çizgi normalindeki bağlantıları blok üç köşegen çözüme alan LINELET'i ve çizgi dışında Jacobi kullanımını anlatır. Gösterilen kıyasın Jacobi'ye karşı olması, bizim LU-SGS ayarımızdan daha iyi olacağını kanıtlamaz. Çizgileri uzatmak başka yönlerdeki bağlaşımı kendiliğinden güçlendirmez.

[Chiew ve Aftosmis, ICCFD12,2024](https://iccfd.org/iccfd12/assets/pdf/papers/ICCFD12_Paper_10-A-04.pdf), matrix-free implicit önkoşullama ve Krylov uzayı maliyetini incelemiş. Daha büyük uzayların daha güçlü artık düşüşüyle birlikte daha fazla iş getirebildiği için toplam süreyi ayrıca ölçüyorlar. **Bu makalenin testleri Euler/Cart3D**; girişinde RANS tartışılması bizim SA-neg RANS'ın doğrulandığı anlamına gelmez. Buraya aktarılan ilke, artık ile maliyeti ayrı kabul etmektir.

[Mavriplis, arXiv1805. 03756](https://arxiv.org/abs/1805.03756), Newton devamını yumuşatan ek artık kaynak terimi önerir. Buradaki native NEWTON_KRYLOV veya LINELET bu kaynak teriminin uygulanması değildir. Yöntemi yalnız config ismini değiştirerek kurmuş sayamayız. Önceki soğuk/sıcak Newton çiftlerinin sonuçları da korunuyor.

## Sonraki yöntem ve gereken kontrol

Art arda yeni sayı denemek yerine, **uzun çizgili kaynak derlemesini** ayrı yöntem adayı olarak kaydettik. Henüz yeni binary derlenmedi ve bu aday çalıştırılmadı. Önce değişmemiş v8.5.0 kaynak derlemesi aynı başlangıç/konfigürasyonda mevcut32noktalı sonucu yeniden üretmeli; derleyici/binary farkı ayar etkisiyle karıştırılmamalı. Ancak bu kontrol geçerse tek sabit32→256 değişimiyle gerçek native kapsam yeniden ölçülebilir. 256, bu kaynak ağdaki193 normal düğümden büyük bir tavan adayıdır; algoritmanın bütün normal sütunu izlediği veya bütün sınır tabakasını çözdüğü iddia edilmez.

Maliyet ve karşılaştırma eşikleri yeni native çalışmalardan önce kaydedilmeli; aynı-binary kontrolü geçmeden değiştirilmişbinary'den nedensel sonuç çıkarılmamalı. Hibrit çizgi + SGS, arXiv yumuşatması ve genel keyfi CAD ağı **uygulanmış değil**. [Sonraki yöntem kaydı](../../work/flatplate_20261027/next_method_plan_not_run.json).

## Kayıt, test ve kapsam

17 yeni karşı örnek/yazılım testi geçti: negatif/eksik/sonlu olmayan paylar, renklerin çizgi kimliği sanılması, yanlış şekilli veri ve süre/iş kabulünde yanıltıcı sonuçlar reddediliyor. İlk kayıtçı genel test_guards adı nedeniyle eski başka klasörün test modülünü yükledi ve durdu; hata logu korundu, benzersiz test_coverage_partition adıyla düzeltildi. Yeni CFD koşusu gerekmedi; ham native çıktılar değişmedi. Bu testler CFD fiziğini veya LLM uzmanlığını doğrulamaz.

45 yeni ham hash, 21 ön-native kod hash'i ve 693 önceki dondurulmuş CFD hash'i yeniden doğrulandı. Gerçek İHA'nın3 girdisi v0. 14 ile aynı. Kaynak URL/zaman/SHA kayıtları ve SU2 lisansının özgün kopyası korunuyor. Ders defterinde gözlem/olası davranışsal risk/fizik hipotezi ayrı; mevcut dersler yeterli olduğundan hedef benchmark değerleri analizci hafızasına taşınmadı. Yeni prompt sürümü veya kör LLM iyileşme ölçümü yok. Genel M6/RAE/VLM/İHA kabulleri **false**, GCI **null**.

[Kapsam ölçümü](linelet_coverage_20261027.json) · [Bağımsız tablo denetimi](linelet_coverage_audit_20261027.json) · [Bölünme sonucu ve tüm kapılar](prec_partition_control_20261027.json) · [17 yazılım testi](coverage_partition_guards_20261027.json) · [Ham/eskisonuç mühür denetimi](coverage_partition_integrity_20261027.json)

Birincil uygulama kaynakları: [nativeLINELET çıktısı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/output/CFVMOutput.cpp), [LU-SGS bölünmesi](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/linear_algebra/CSysMatrix.cpp), [kurulu seçenek kaydı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/CConfig.cpp), [LINELET sınırı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/include/geometry/CGeometry.hpp), [resmî doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/).
