# C-grid sayısal teşhisi — kör kayıt

Üretilmiş ağ veya jeneratörde yerel bağlantı/haritalama hatası saptanmadı. Mevcut başarısız yakınsamanın nedeni kesin belirlenmedi. Şok çevresinde katmanlar arası dalgalanma ölçüldü; bunu yalnız “carbuncle” diye adlandırmak için kanıt yeterli değil. Bu kayıt deney karşılaştırması içermez ve hiçbir kabul eşiğini kapatmaz.

## Gerçek ağdan kontroller

Özgün `build_cgrid.py` SHA256 hâlâ `9d385936e598c2371179f8a5a4fe44e44964b2ccc1c5a6d674b1f62912a48637`. SU2 dosyasındaki yakın blok düğümleri ve dörtgen bağlantıları `near_arrays.npz` ile tam eşleşiyor. Bağımsız median-dual yeniden kurulumunda en küçük alt-poligon alanı5,80858e−11m², dual hacim1,22402e−10m²; tüm dual-yüz/primal-kenar iç çarpımları pozitif. İç düğümlerin sabit akış vektör kapanışı ençok3,55271e−15m. Bu, SU2'nin gerçek kaba multigrid aglomerasyonunu denetlemez.

Kendi1000 alanından seçilen x/c0,50–0,54 / y/c0,095–0,125 kutusundaki357 dörtgende köşe Jacobian'ı≥2,21688e−6m², açılar87,509–92,491°, kenar en-boy oranı1,790–3,114. Kutunun üstü dış üçgen arayüzüne kadar ulaşır; asıl en büyük nokta(0,51827748355;0,10376227848)m ise arayüzden0,01781067m içeridedir, tam dört komşusu vardır. Burada negatif hücre, tekil dual hacim, kopuk dikiş veya ani normal aralık sıçraması görülmedi. Normal aralık0,00111317m'dir. Bu geometrik sonuç çözüm doğruluğunun kanıtı değildir.

## Kendi alanındaki ölçüm

İlk1000 alanında x/c0,518277 sütunundaki18 normal düğümde Mach1,21946–1,31586; ardışık eğim9 kez işaret değiştiriyor. Yerel doğrusal eğilimi çıkaran ikinci-fark RMS0,0227699, en büyük0,0532709. Bu, çözümün normal yönde pürüzsüz olmadığını gösteriyor. Noktalar çözücünün kendi düğümleridir; beklenen şok konumundan örnek seçilmedi.

Sonraki dalları tek eski kutuyla açıklamak doğru değil. SabitCFL1 dalının1000 yerel alanında global en büyük kalıntı(0,7219463;0,0828609)m'de0,00226707; MG0 dalının1200 yerel alanında(0,4995433;0,2532513)m'de5,02574e−5 ve dış üçgen bölgededir. Entropy0,2 dalının1200 yerel alanında global en büyük(0,6859110;0,0702130)m'de0,00290824. Her dal aynı ana1000 başlangıcından ilerlediği için bu yerel iterasyonlar tek kesintisiz zaman çizgisi değildir. Alan sürüm/hash'leri JSON'dadır. Farklı bitiş alanları tek başına kontrollü nedensellik kıyası sayılmaz.

Basınç farklarının i/j yönündeki birbirini götürme oranı ilk sütunda tekil olarak0,031'e düşüyor, medyan1. Bu sınırlı ölçüm yaygın sensör iptalini desteklemiyor; gerçek SU2 sensörünün sınır/komşuluk ayrıntılarının yerini almaz. Eski koşulda gerçek doğrusal çözücü artık geçmişi yok; doğrusal tolerans/iterasyon sınırına takıldığı iddia edilmedi.

## Kaynakla doğrulanan sayısal ayrım

Resmî [SU2 convective schemes](https://su2code.github.io/docs_v7/Convective-Schemes/) sayfası JST_MAT için entropy0,05–0,2 ve Jacobian katsayısı yaklaşık8 öneriyor; merkezî yöntemlerde MUSCL akış sınırlayıcısı etkin değil. Dolayısıyla bu koşuda `LIMITER_ITER` değiştirmek doğrudan merkezî şok yakalamayı sınamaz. Entropy artışı sönümü de değiştirir.

Gerçek sürümün [SIMD centered.hpp](https://github.com/su2code/SU2/blob/v8.5.0/SU2_CFD/include/numerics_simd/flow/convection/centered.hpp#L291) uygulamasında `fixFactor` yalnız örtük Jacobian'a girer(310–314); artık akısına girmez(305–307,349–356). Eigenvalue tabanı entropy ile değişir(325–337). ScalarJST dalı ise stretching düzeltmesi çağırır(215–216); MAT dalı çağırmaz. Bu nedenle JST/MAT kıyası aynı ayrık denklem değildir; farkı yalnız eigenvalue ölçeklemesine indirgeyemeyiz. [Factory](https://github.com/su2code/SU2/blob/v8.5.0/SU2_CFD/include/numerics_simd/CNumericsSIMD.cpp#L65) ayrıca merkezî yöntemlerin kaba multigrid seviyesindeLAX kullandığını gösterir.

İlk kontrollü ayrım: aynı ana1000 restartı, aynı ağ/fizik, sabitCFL1, MG3, entropy0,05 ve tüm diğer ayarlar; yalnız `CENTRAL_JACOBIAN_FIX_FACTOR=8`. Parent bu dalı kendi kuyruğunda yönetiyor. Aynı artık denklemi daha iyi yakınsarsa örtük iterasyon koşullanması açıklaması güçlenir; yakınsamazsa elenmez ama tek başına çözüm değildir. `LINSOL`, `CFL_NUMBER`, `MAX_RES` grupları yalnız gözlem kaydı olarak eklenebilir. Sonraki hazır scalarJST dalı sayısal sönüm/method ayrımıdır; yakınsarsa bile kuvvet, y+, ağ ve uzak alan ekranları tekrar gerekir.

## Kapsam ve açık ağ zayıflığı

Normal kılavuzun ilk0,003c'de yumuşak dönmesi açıları değiştiren kayıtlı bir haritalama tercihidir; orada bulunan kötü gradyan olasılığı bu denetimle bütünüyle dışlanmış değildir. Sıcak ilk nokta bu dönüşün çok dışındadır. Dış üçgen geçişinde ve iz bloğunun x/c8 sonundaki kötü açılar ayrıca açık kalır; tüm ağın geometrik kontrolleri geçmiş olsa da bu bölgelerin çözüm etkisi kanıtlanmış değildir.

Kod incelemesinde küçük, gerçek bir dağıtım açığı bulundu: `wake_distribution` son mevcut x noktasını8c ile değiştiriyor; bu, son iz hücresini ilan edilen adım tavanının üstüne çıkarabiliyor. Sayısal ölçüler ekJSON'dadır. Bu uç, ilk şok sıcaklığından çok uzaktadır; çöküş nedeni diye sunulmadı. Sonraki ağ revizyonunda kalan uzunluğu son sabit-adımlı kuyruğa eşit dağıtmak gerekir. Özgün jeneratör/ağ değiştirilmedi; mevcut karşı dallar aynı ağla sürmelidir.

Yüksek en-boy oranına tek başına hata atfedilmedi: [Diskin–Thomas](https://ntrs.nasa.gov/api/citations/20090007493/downloads/20090007493.pdf) eğrilik, stencil ve çözüm yönünün birlikte etkisini inceler. Burada doğrudan ölçülen sıcak hücrelerin oranı yaklaşık2–3'tür; raporun yüksek-anizotropi sonuçları tek başına bu çöküşün teşhisi değildir.

Hiçbir çözücü başlatılmadı; frozenv1/v2 veya mevcutv3 ağ/config/alan değiştirilmedi. GüncellenmişAGENTS/PROJECT_STATE, reviewer ve deney/harici CFD sonuçları okunmadı. Genel sayısal kabul hâlâ açık.
