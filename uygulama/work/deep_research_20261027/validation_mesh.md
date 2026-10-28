# CFD ağ ve fiziksel doğrulama açıkları — 28 Ekim 2026

Bu alt araştırma, 27 Ekim v0.17.0 dahil yerel kanıtları ve 28 Ekim'de açılan birincil kaynakları değerlendirir. Yeni CFD, kurulum veya ağ üretilmedi. Aşağıdaki sıra, bütün proje için ana listenin CFD ağ/fizik bölümü önerisidir. P0 güvenilir sonuç üretimini engeller; P1 fiziksel kapsamı kapatmayı engeller; P2 verimlilik ve otomasyon geliştirmesidir. Mevcut başarısız eşikler değiştirilmez. Bir önerinin yazılması o yöntemin çalıştığını göstermez.

En büyük açık, ağ sayısı veya yazılım eksikliği tek başına değildir. İnce ağda sayısal yakınsama kapanmadan ağ hatası, deney uyumu ve yeni uyarlama yöntemleri güvenilir biçimde ayrıştırılamıyor. Kaynak32 SU2 yeniden üretiminin geçmesi bu belirsizliklerden birini daralttı; cap256 denemesinin başarısızlığı çizgi kapsamı artışının tek başına çözüm olmadığını gösterdi. [Son yerel rapor](../../outputs/reports/su2_kaynak_karsilastirma_20261027.html)

| Önerilen sıra | Açık problem | Önemi | Bir sonraki ayrıştırıcı iş |
|---|---|---|---|
| 1 / P0 | Üç ağ ailesinin ince çözümü hâlâ yakınsamıyor | Yakınsamamış ince sonuçtan ağ hatası çıkarılamaz | Gerçek iç artığın ölçümünü tamamla; sonra aynı geometri/ailede kayıtlı dış kapıyı geçir |
| 2 / P0 | BL normal çözünürlüğü ve LE/TE/iz geçişi | y+<1, bütün sınır tabakasının çözülmesi değildir | Sabit kaynakta yalnız normal dağılım/geçiş değişen bir kontrol; δ99, hız ve μt profilleriyle ölç |
| 3 / P0 | Geometri temsili ve yüzey eşdeğerliği | Sayısal fark geometri değişiminden kaynaklanabilir | Kaynak üretici ve bağımsız CAD'i ayrı kimliklerle tut; sınır-yüzeyi mesafesi ve teğet/normal farkını denetle |
| 4 / P1 | Üç yakınsamış sistematik ağ ve geçerli GCI yok | Küçük orta–ince fark tek başına hata bandı değildir | Aynı kaynak/ağ ailesi, tutarlı yönsel oranlar, bütün seviyelerde yakınsama ve asimptotik davranış |
| 5 / P1 | Uzak alan duyarlılığı kapanmadı | Sınır etkisi ağ etkisine karışabilir | Yakın bölgeyi koruyarak yalnız dış sınırın değiştiği ön kayıtlı çift |
| 6 / P1 | RAE/M6 deney kabulü geçmedi | Çözülen RANS problemi, deneydeki fizik ile tam aynı olmayabilir | Önce sayısal kapılar, sonra koşul/trip/geometri/örnekleme belirsizliği ve bütün deney noktaları |
| 7 / P1 | Bağımsız çözücüyle eşdeğer denklem karşılaştırması eksik | Kendi postprocessor'ıyla uyum model doğrulaması değildir | Önce TMR'nin mevcut CFL3D/FUN3D sonuçlarını tam model ve BC karşılığıyla yeniden kıyasla |
| 8 / P1 | Duvar mesafesi bağımsız denetimi yok | Anizotropik ağlarda SA kaynakları etkilenebilir | Akış çalıştırmadan LE/TE/uç dahil gerçek nokta–yüzey mesafesini doğrula; hata varsa tek değişkenli çift |
| 9 / P2 | Tam anizotropik remeshing/adjoint zinciri kurulmadı | Hessian haritası üretim ağı veya kuvvet hata bandı değildir | Önce analitik metrik/ağ-metriğe uyum; sonra küçük 2B kapalı solve→metric→remesh→transfer döngüsü |

## 1. En yeni yerel durum: tarihsel başarıları yeni genel kabul saymamak

### Düz plaka / SA-neg üç ağ ailesi

[26 Ekim kayıtlı aile incelemesi](../../outputs/reports/reduced_family_review_20261026.json): kaba/orta/ince üçü de gerçekten tamamlanmış; kaba ve orta iteratif kapıyı geçiyor, önceden seçilmiş ince alan3999 geçmiyor. Aynı SI tanımındaki ince yoğunluk −9,71543318 ve son100 CD aralığı 2,8770e−9. İnce max y+0,25822335; iki kaynak koduna Cf, hız ve μt ekranları geçiyor. Orta→ince CD değişimi %0,0618543, Cf değişimi %0,1664201. Buna rağmen aile kabulü false ve GCI null. Cf tam eğrisinin LE yakınındaki bütün-nokta normu ile kabul penceresi normu ayrı; pencere dışında kalan veriler saklanmış. Bu sayısal kod karşılaştırması deney doğrulaması değildir. Tam boyutlu Sutherland sabitlerinin bütün referans kodlarda özdeşliği ayrıca kanıtlanmış değil.

27 Ekim source32/cap256 kolları yeni yakınsamış ince aile rolü yerine konmadı. Üç yeni 200-adım kol yalnız kaynak yeniden üretimi ve bir kaynak sabiti mekanizması içindir. Yoğunluk kazancı −0,00938603 log10; ön kayıtlı etki geçmedi. Eski fine3999 rolü korunuyor. Dolayısıyla 'yeni derleme çalıştı, üç ağ tamam' sonucu çıkarılamaz.

### RAE2822

[24 Ekim v3 paket kapanışı](../../outputs/projects/proje-15cce2de02/reports/v3_test_batch_closed.json) en yeni RAE görev kapanışıdır: 14 native denemenin kayıtları mevcut; yakınsamış üç ağ, tam BL/normal hassasiyet, 200c/400c uzak alan ve önceden seçilmiş ince deney kapısı açık. R4 ağları 92.412/196.741/424.826 hücre olarak gerçekten üretildi. Bu mesh üretim başarısı yüksek doğruluklu üç çözüm başarısı değildir.

v2'nin başarılı dar üç-ağ ekranı tarihsel ve kendi temsil/fizik kapsamındadır: CL %0,2138, CD %1,4119 ve Cp ağ farkı0,002808. Aynı yakınsamış orta çözümlerde 0,01c→0,02c normal blok CL %3,9766 ve CD %4,6762 değiştirdi; bu bağımsız bölgesel açık kapanmadı. v2 önceden seçilmiş fine3400'ün kaynak tablo düzeltmeli 103-nokta CpRMSE'si0,06702898>0,03; v3/JST ve Roe tanıları da genel kabulü geçmedi. RAE v2 fine değerini v3'ün güncel sonucu diye etiketleme.

### ONERA M6

[25 Ekim TMR kaynak vaka incelemesi](../../outputs/projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json), eski blunt kaynak M6'dan ayrı sharp-TE geometri/fizik vakasıdır. Kaynak Fortran üreteci/coarsener gerçekten derlenmiş ve 4.032/32.256/258.048 hücrelik aynı 100c dış alan ailesi üretilmiştir. 'Üçüncü ağ henüz yok' eski bilgi olur; açık olan üç ağın birlikte yakınsaması ve fizik kabulüdür.

| TMR sharp rolü | Tam alan / terminal geçmiş | Yoğunluk log10 | Tüm271 noktada CpRMSE |
|---|---:|---:|---:|
| kaba |3999 /3999 |−6,08121 |0,289875 |
| orta |2400 /2539 |−5,11608 |0,153477 |
| ince |600 /663 |−1,75401 |0,311580 |

Hiçbir iteratif kapı geçmedi. İnce rolünü daha iyi görünen orta ile değiştirmek yasak; GCI null. Sözleşmenin mevcut yoğunluk<−7, son100 CL aralığı<1e−4, CD<1e−5, max y+<1 ve bütün14 kesit/yüzey CpRMSE<0,08 kapıları sürüyor. BL/TE/uç/iz, ayrı uzak alan ve bağımsız kuvvet integrali de birlikte gerekli.

Eski blunt ağdaki normal dağıtım max y+'yı yaklaşık1,458→0,830'a indirdi, fakat bu yeni TMRsharp ailesinin başarılı çözümü değildir. Yalnız y+ başarı kaydı bütün 3B fizik kapılarını kapatmaz.

## 2. Araştırmanın önerdiği somut düzeltmeler

### Normal çözünürlük ve geçiş: toplam hücreyi artırmaktan önce yönü ve yeri ölç

NASA TMR'nin ilk-duvar-noktası incelemesi, aynı 225×97 ağ boyutunda yalnız minimum normal aralık ve büyüme değiştirilerek yapılmıştır. SA ile omega tabanlı modeller aynı hassasiyeti göstermemiştir. Bu yüzden tek bir y+ eşiği bütün yöntemlere taşınamaz; ilk nokta denetimi ayrı, normal profil ve katman dışı geçiş ayrı olmalı. [TMR y+ çalışması](https://tmbwg.github.io/turbmodels/flatplate_val_ypluseffect.html)

RAE R4'te [gerçek dış/iç normal yükseklik oranları](../../outputs/projects/proje-15cce2de02/reports/prediction_v3_cgrid_interfacer4_summary.json) kaydedilmiş; bazı gövde/iz arayüzlerinde sıçrama sürüyor. TMR M6'da58/29/14 kaynak radial katman var, fakat radial çizgi uzunluğu gerçek normal kalınlık veya δ99 değil. Mevcut profil çıkarımı 16 konum ve dış örnekleme penceresi duyarlılığını kaydediyor; seçili fine600 alanı yakınsamadığı için sonuç fizik kanıtı değil.

Önerilen kontrol: tek kaynak temsil, tek dış alan ve aynı fizik ile yalnız aft normal dağılımını/geçişini değiştiren bir çift. Kaynak duvar koordinatları ve teğetsel aralıklar korunmalı. Ue operasyonel tanımı ile 0,03–0,06c, 0,04–0,08c ve 0,06–0,12c gibi mevcut dış pencerelerin sonuç duyarlılığı görünmeli; geçersiz maskeler bütün integrallere uygulanmalı. Yeni δ99 değerini en uygun pencere seçerek kabul ettirmemeli. Kapanış, yalnız y+ değil yakınsamış sonuçta normal profil ve kuvvetin kontrollü normal çözünürlüğe duyarsızlığıdır. Eşikler çalışmadan önce ayrı sözleşmede belirlenir; mevcut başarısız kapılar gevşetilmez.

### Kaynak geometri ve CAD yüzeyi: önce hangi geometrinin çözüldüğünü kesinleştir

NASA TMR M6 açıkça sharp-TE sayısal egzersizini tanımlar; orijinal deney kanadı blunt-TE'dir. CAD mm, kaynak üreteci birim kök veterin normalize edildiği koordinatlardır. Deneyin Re_MAC≈11,72M sayısını normalize vaka Re_root14,6M yerine geçirmek doğru değildir. Altıncı deney kesiti güncel kaynakta eta0,96'dır. [TMR vaka tanımı](https://tmbwg.github.io/turbmodels/onerawingnumerics_val.html)

Yerelde güncel ve kullanılacak geometri kanıtı [boundary-v2 mesafe denetimidir](../../outputs/projects/proje-e9319baef1/reports/tmr_source_CAD_boundary_v2_20261025.json). Önceki solid mesafe sürümü iç noktayı sıfır sayabildiği için geçersizlenmiştir. Fine kaynak düğümlerinin CAD sınır-yüzeyine örneklenmiş max uzaklığı6,982881e−4 kök veter; düğüm/kenar/merkez bütün örneklerinde max9,781043e−4'tür. Bu sonlu örnek denetimi tam Hausdorff sınırı değildir. Kaynak üreteci ile bağımsız STEP'in yüzey eşdeğerliği henüz kabul edilmemiştir; bu tek başına Cp hatasının nedeni kanıtı da değildir.

Sonraki iş: kaynak üretecini kendi sayısal referanslarıyla kıyaslamak ve CAD eşdeğerliği iddiasını ayrı tutmak. Yeni CAD tabanlı aile istenirse, CAD'in yüz/kenar ilişkisinin mesh'e korunması, teğet/normal/LE/TE/uç konumlarının ölçülmesi ve aynı kaynaktan üç seviye gerekir. Eski ve yeni geometriler tek GCI ailesi olamaz.

### Duvar mesafesi: kör ayar taraması yerine düşük maliyetli yeni mekanizma denetimi

Park ve arkadaşlarının NASA/INRIA/Boeing/Sandia çalışmasında, anizotropik ağda en yakın yüzey düğümüne komşu üçgenin en yakın yüzey üçgeni olduğu varsayımı bozulmuş; ONERA M6 SA çözümü, BL ve şok etkilenmiştir. Aynı ağda yalnız duvar mesafesi hesabını değiştirerek fark gösterilmiş; bazı yöntemlerde bu düzeltme referansa yaklaşmayı iyileştirmiştir. Bu, bütün solverlerin aynı hataya sahip olduğu veya bizim SU2'de bu nedenin bulunduğu anlamına gelmez. [Park vd.,2018, BölümVI ve Şekil11–13](https://ntrs.nasa.gov/api/citations/20180006169/downloads/20180006169.pdf?attachment=true)

Bizim için önce yeni CFD gerektirmeyen audit uygundur: kaynak SU2 sürümündeki wall-distance yolunu incele; seçilmiş LE/TE/uç/kök/aft noktaları için native mesafeyi en yakın düğümden bağımsız global nokta–üçgen/yüzey mesafesiyle karşılaştır. Solide olan mesafeyi kullanma. Hata görülürse gerçek artığın yoğunlaştığı yerle ilişkiyi ölç ve yalnız bu hesabı değiştiren yeni ön kayıtlı karşılaştırma yap. Hata yoksa hipotezi kapat; daha çok değer deneme.

### GCI ve uzak alan: üç sayı bir hata bandı değildir

NASA'nın yönergesi aynı aileyi, duvar ve birleşim gibi kritik aralıkların sistematik oranlarını, üç seviyede gözlenen mertebe/asimptotik kontrolünü öneriyor. Şokun bulunduğu yerel bölgede Richardson varsayımı bozulur; global kuvvet için ayrıca kontrol gerekir. Mevcut üç ağın tamamı yakınsamadan p/GCI üretmek, iterasyon hatasını ağ hatası diye raporlar. [NPARC mekânsal yakınsama](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)

Uzak alanı ayrı çiftte test et: kaynak gövde ve yakın ağ aynı kalmalı; yalnız dış bölge uzatılmalı. Aynı matched checkpoint, residual tanımı ve son kuvvet penceresi kapıları her ikisinde de geçmeli. RAE400c ağı hazır, çözüm yapılmamış; hazır dosyadan Cp/y+/kuvvet çıkarılamaz. TMR M6 kaynak100c geometrisi kendi başına duyarlılık çalışması değildir.

### Deney uyumu: yanlış problemi daha hassas çözmemek

NASA WIND RAE Study4, 369×65 C-grid, SA/SST, ayrı yakınsama/kuvvet grafikleri ve M0,729/alfa2,31°/Re6,5M/T460R koşullarını kaydeder; nominal deney sayfası M0,725/alfa2,92° verir. Yerel vakada baştan seçilmiş düzeltilmiş koşullar sonuç tutturmak için tekrar değiştirilmemeli. Deney trip'i, geometri, türbülans varyantı ve tünel düzeltmesi model uyuşmazlığı olarak ayrıca kalır. [WIND Study4](https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html)

CpRMSE tek başına her şeyi açıklamaz: bütün noktaların farkları, yüzey/kesit yanlılığı, LE/TE/şok konumu ve basınç/sürtünme kuvvetleri raporlanmalı. RAE kaynak basınç ölçüm belirsizliği±0,0026 toplam CFD/model belirsizliği veya seçilebilir kabul eşiği değildir. M6 kaynak CFD kuvvetlerini deneysel CL/CD saymak da yanlış olur. Önce sayısal hatayı sınırlayıp sonra model/deney farkını tartışmak gerekir.

### Bağımsız çözücü: yeni program kurmak doğruluğu kendiliğinden artırmaz

En hafif bağımsız adım zaten indirilen TMR CFL3D/FUN3D sayısal referanslarını tam model varyantı, aynı grid, BC, sıkıştırılabilirlik, Sutherland ve referans ölçekleriyle eşleştirmektir. M0,2 düz plaka neredeyse sıkıştırılamaz olsa da kaynak açıkça sıkıştırılabilir bir doğrulama vakasıdır; incompressible çözüm yakın ama aynı limitte olmayabilir. [TMR 2DZP](https://tmbwg.github.io/turbmodels/flatplate.html)

OpenFOAM ileride farklı sayısal ayrıklaştırmayla yararlı karşılaştırma sağlayabilir. Resmî Windows yolu WSL2/Ubuntu'dur; bu yerel ortamda kurulu/çalışır veya RAM bütçesine sığar diye doğrulanmadı. Önce yalnız read-only dağıtım ve kaynak bütçesi denetlenmeli; tam wing/çok milyon hücreye atlanmamalı. Eşdeğer SA-neg/ft2, wall BC ve sıkıştırılabilir çözücü eşleştirilmeden farkı SU2 hatası diye etiketlememeli. [OpenFOAM Foundation Windows yolu](https://openfoam.org/download/windows/)

Profesyoneller de bu güçlükleri yaşıyor: Drag Prediction Workshop sonuçlarında kodlar arası dağılım yalnız ağ büyütmeyle kaybolmamış; geometri/ayrılma/ağ ailesi uyuşmazlıkları önemli olmuş. Bu, düşük doğruluk için mazeret değil; tek solver/tek mesh ve 'çok hücre' ölçütünün neden yeterli olmadığının birincil kanıtıdır. [Morrison ve Hemsch,2007](https://ntrs.nasa.gov/citations/20080002265)

### Adjoint ve yeni yöntemler: hedefe göre ağ kur, ama tüm zinciri doğrula

NASA'nın adjoint örneği akış, adjoint, metrik ve yeniden ağ üretimini ayrı bileşenler halinde kuruyor; inviscid ve türbülans adjoint türevlerini sonlu farkla sınamış. Sunulan adaptation örneklerinin inviscid M6 ve laminer NACA0012 kapsamını yerel türbülanslı M6 doğrulaması diye genişletmemeli. [Balan vd.,2019](https://ntrs.nasa.gov/citations/20200002636)

Yerel Hessian v2, 88.407 adayın53.068'ini uygun,35.339'unu maskeli bulmuş;531 öncelikli hücrenin274'ünde yön kararlı. Bu bir mesh üretici, adjoint veya CL/CD hata bandı değildir. Önce analitik metrikte beklenen eleman yönü/boyu ve CAD sınır korunumu; sonra küçük2B örnekte tam solve→metric→remesh→transfer→solve döngüsü ve sabit-grid karşılaştırması gerekir. Maskeli yerler düşük hata sayılmamalı. Kaynak aktarımı kütle/enerji/türbülans pozitifliğini ve geometriyi korumalı; her cycle yeni mesh hash'i taşır.

arXiv2607.27580, karma geometriyi sabit body-fitted kısım ve değişen immersed detay olarak ayırıp yerel adaptasyon yapıyor. Çalışmanın coarse/fine IBM örnekleri çözünürlüğün hâlâ kritik olduğunu; CODA ve ayrı penalization altyapısı gerektirdiğini gösteriyor. Bizim SU2 mesh sorununa doğrudan eklenecek hazır düzeltme değildir. Şimdilik uygulanabilir çıkarım: yalnız değişen tasarım parçasının çevresini yeniden ağlayan, sabit kısmı koruyan mimari; üretim yöntemi olarak önerilmeden bağımsız yeterlilik gerekir. [Núñez-de la Rosa vd.,2026,ön baskı](https://arxiv.org/html/2607.27580v1)

## 3. Sıralı kapanış planı

1. Kaynak32 yeniden üretimi kanıtını koru. Gerçek iç lineer artığı ölçme planı ana sayısal araştırmayla birlikte önce kapatılsın; cap256 sonucunu daha fazla otomatik tarama gerekçesi yapma.
2. Akış çalıştırmadan geometri/boundary mesafe ve wall-distance auditleri yap. Kaynak üreteci/STEP farkını, yanlış geometri veya fizik 'düzeltmesi' yapmadan görünür tut.
3. Kaynak düz plaka üç ailesinde önceden seçilmiş fine rolüyle iteratif kapıyı kapat. Bağımsız kod/viskozite/model/BC eşleşmesini belgeleyip GCI uygunluğunu değerlendir; LE singular toplam drag için otomatik mertebe çıkarma.
4. RAE'de aynı kaynak r2 temsilini kullanarak normal/TE/iz geçişini kontrollü çöz. Yeni üç ağ ve ayrı200c/400c kontrolü tamamlanmadan deney kabulünü veya genel RANS kabulünü kapatma.
5. Aynı sıralamayı TMRsharp M6'ya taşı: kaynak fizik korunarak üç yakınsamış seviye; BL/TE/uç/iz; uzak alan; bütün271 deney noktası ve14grup. Eski blunt vaka ayrı kalır.
6. Tam anizotropik/adjoint döngüsünü küçük2B'de ayrı yeterlendir. Üniversite İHA projesinin keyfi CAD→3B CFD hizmeti ancak geometri/akış kapsamı ve bu kapılar yeni projede tekrar sağlanırsa mümkün sayılır.

Bu çalışma hiç bir fizik kapısını kapatmadı. En yararlı yeni düşük maliyetli araştırma önerisi bağımsız duvar-mesafesi denetimi; en önemli mühendislik engeli ise ince ağın ve tam bölgesel çözünürlüğün birlikte yakınsamamasıdır.
