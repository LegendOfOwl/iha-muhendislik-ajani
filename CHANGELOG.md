# Değişiklik günlüğü

v0.1.0–v0.10.0 geriye dönük içe aktarım; v0.11.0 ve sonrası gerçek artımlı Git değişiklikleridir.


## v0.17.0 — 27 Ekim 2026: SU2 kaynak derlemesi ve kontrollü karşılaştırma

SU2 kaynak32 derlemesi, korunmuş başarısız denemeden 258 doğrulanmış nesneyi kullanarak kalan 32 hedefi 81.063 saniyede tamamladı. Üç yeni native CFD koşusu aynı kaynak ağ ve başlangıçla 200 adım çalıştı. Resmî release32–kaynak32 yeniden üretimi geçti: beş SI log10 RMS eğrisindeki en büyük fark 0.00175396, son CD mutlak farkı 0. Yalnız MAX_LINELET_POINTS=32→256 değiştirildi. Yoğunluk kazancı -0.00938603 log10, SA kötüleşmesi -0.00099585 log10, Krylov sayımı oranı 1.00000000, bu çiftte gözlenen süre oranı 1.28308938; ön kayıtlı ortak etki/maliyet kabulü geçmedi. 40 yeni yazılım kontrolü geçti; eski70 kontrol yeni sayılmadı. Krylov sayımı işlem maliyetinin vekilidir; daha uzun çizgilerin eşit aritmetik maliyeti olduğu veya tek çiftin evrensel hız kıyası olduğu iddia edilmez. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

## v0.16.0 — 27 Ekim 2026: kaynak derlemesi ve LINELET kontrolü

Sabit SU2 v8.5.0, Eigen ve MEL kaynakları indirildi; 4357 kaynak dosyası arşivlerle birebir doğrulandı. C++17/Haswell/OpenMP dört iş parçacığı derleyici denemesi geçti. İlk gerçek SU2 derlemesi 259. hedefte başlık arama yolu hatasıyla durdu; kaynak baytlarını koruyan ortak arama yolu düzeltmesi kaydedildi. İkinci deneme kullanılabilir RAM 1 GiB sınırının altındayken native süreci başlatmadan reddedildi. 70 yeni yazılım kontrolü geçti; önceki 14 süreç kontrolünün kanıtı ayrıca denetlendi. Yeni CFD çalıştırılmadı; pristine32 yeniden üretimi ve cap256 etki/maliyet sınaması bekliyor. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

## v0.15.0 — 27 Ekim 2026: çizgi kapsamı ve bölünme kontrolü

27 Ekim 2026. Üç yeni native SU2 koşusu tamamlandı. Gerçek LINELET alanında 52689 düğümün 7200 tanesi çizgilerde; önceki doğrulanmış aşama artığının yoğunluk kare toplamının %53.8965’i bu birliğin içinde. Bu konumsal kapsam ölçümüdür; yeni alanın yeniden hesaplanan artığı, nedensellik veya ağ hata bandı değildir.

Aynı kaynak ağ ve başlangıç dosyasıyla, toplam dört iş parçacığı korunarak yalnız LU-SGS önkoşullayıcısının bölünmesi 0→1 değiştirildi. 200 adımlık çiftte yoğunluk kazancı 0.14072006 log10, toplam Krylov işi oranı 1.54404968, gözlenen süre oranı 3.62357987 oldu. Ön kayıtlı ortak etki ve maliyet kabulü geçmedi. 17 yeni yazılım kontrolü geçti; başarısız denemeler ve ham çıktılar korundu. Uzun çizgili kaynak derlemesi sonraki yöntem adayıdır; henüz derlenmedi veya çalıştırılmadı. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

## v0.14.0 — 26 Ekim 2026: iç çözüm sınırı ve kalıntı tanısı

26 Ekim 2026. Aynı ince ağ ve başlangıç alanında iç doğrusal çözüm sınırı 40→80 olarak değiştirildi. 200 adımlık eşli kontrolde yoğunluk kalıntısındaki kazanç 0.09148072 log10, SA kalıntısındaki değişim -0.09553239 log10 ve toplam Krylov işi oranı 1.50447718 oldu. Önceden belirlenen ortak etki kabulü geçmedi; başarısız deneme ve ham çıktılar korundu.

Kalan kalıntının yerini araştırmak için kaynak koduna dayalı, bir adımlık açık RHS ölçümü çalıştırıldı. Akış ve SA aşamalarının sıralı hesaplandığı bu tanıda beş RMS/MAX eşlemesi geçti: en büyük fark 1.14e-08 log10, native konservatif alan drift’i 4.67e-12. Haritanın yönlendirdiği LINELET kontrolü gerçekten etkinleşti; yoğunluk kazancı -0.03230637 log10, SA kötüleşmesi 0.05537677 log10 ve Krylov işi oranı 2.31080300 ile ortak etkiyi geçemedi. Norm ve konum bulguları ile sınırlamalar ayrıntılı raporda gösterilir. Bu çalışma yeni bir yakınsamış çözüm, deney doğrulaması veya genel CFD yeterliliği değildir. 37 yeni yazılım kontrolü geçti. Genel fizik, RAE2822, ONERA M6 ve gerçek İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

## v0.13.0 —26 Ekim2026: CFD iç çözüm işi ve üç ağ

26 Ekim2026. Aynı seed/ağda iç doğrusal tolerans1e-6→1e-3 testi toplam Krylov iterasyonunu%42,1123 azalttı; SI kalıntı/CD farkları ön kayıtlı sınırlar içinde kaldı. Üç kaynak ağda ayrı ve sonlu bütçeli native devam koşuları yapıldı. Kayıtlı2B sayısal şartların tamamı geçmedi; açık kapılar raporlandı. Genel fizik/M6/İHA kabulü false; GCI null.

8 maliyet ve12 aile karar kontrolü geçti. Yeni/önceki mühürler, gerçekİHA girdileri ve ön-native kodlar denetlendi. Son işlem çıktı adı gölgelenmesi düzeltildi; ham alanlar korunur. Bu kontrollü kod kıyası deney veya LLM uzmanlığı doğrulaması değildir.

## v0.12.0 —25 Ekim2026: CFD kontrol deneyleri ve birim denetimi

25 Ekim2026. 11yeni native SU2 koşusu; beş tamamlanmış eşli kıyasta ön kayıtlı ortak etki geçmedi, MG2 süre sınırında eksik kaldı. Fiziksel kabul false.

- SabitCFL, otomatikCFL, yerel çok seviyeli ağ, sonlu fark Newton–Krylov ve değişken ölçekleme araştırıldı; onaylanmayan hipotezler korunur.
- Newton iki farklı on/off çiftinde gerçekten çalıştı. Ortalama akış içindir; SA ayrı çözülür, adjoint veya arXiv artık yumuşatması değildir.
- Karışık boyutlu/boyutsuz kalıntı kıyası yanlış2,719195log kazanç gösterebilirdi. Aynı SI tanımında0,0550435log kaldı; yeni denetçi bu hatayı reddeder.
- 13eşli kıyas karşı örneği,4analitik/bozuk dönüşüm kontrolü ve26temel regresyon geçti. Native tam kalıntı özdeşliği taslağı başarısız olarak korundu.
- 187yeni dosya mühürü,40ön-native kod hash'i ve230eski CFD hash'i yeniden doğrulandı. Gerçek İHA girdileri değişmedi.
- Sonraki kayıtlı maliyet deneyi henüz çalıştırılmadı. Üç yakınsamış ağ, M6/RAE ve genel CAD→CFD yeterliliği açık; LLM davranış iyileşmesi ölçülmedi.

## v0.11.0 —25 Ekim2026: kaynak CFD teşhisi ve sürümlü güvenilirlik

- Kaynak TMR M6 üreteci/coarsener yerel derleme kayıtları;258048/32256/4032hücreli sistematik aile ve10dondurulmuş native deneme. Minimum fizik kabulü false.
- NASA kaynak düz plaka SA-neg:3264/13056/52224hücre,8native deneme, kaynak Cf/hız/μt kıyası. Kaba yakınsadı; orta/ince iteratif kapılar açık.
- Kontrollü MG, başlangıç aktarımı, LINELET ve ILU denemeleri; desteklenmeyen hipotezler ve son işlem hataları korunur.
- R01–R03 güvenilirlik politikası, L10/L11 kapsamlı hata dersleri ve hash/alan eşlemesi kontrolleri. Yeni LLM davranış iyileşmesi gösterilmedi.
- GitHub’da okunabilir sonuç özeti, EXE kaynak/hash bilgisi, İngilizce özet, yazarlık ve sürümleme politikası.
- Eski tag/yayınlar değişmedi. Yeni büyük dosyalar içerik bazında tekilleştirilmiş, her hedef yola geri yüklenebilir Release arşivlerinde.

## v0.1.0 — Temel hesap ve girdi kontrolleri

Birim, girdi ve sayısal kontroller; ilk araç hazırlığı.

## v0.2.0 — Yerel CAD ve aerodinamik araçlar

OpenVSP/VSPAERO, XFOIL, FreeCAD, CalculiX ve kanat karşılaştırmaları.

## v0.3.0 — CAD modelleri ve kullanım denetimi

K-1B, Cadmonkey ve Zero-to-CAD deneyleri; özgün başarısızlıklar ve istem denetimleri.

## v0.4.0 — Deterministik geometri ve hafif CFD

Parametrik kanat, karmaşık VLM, SU2 ve Elmer araç sınamaları.

## v0.5.0 — Proje merkezli arayüz ve aeroelastisite

EXE başlatıcı, proje kayıtları, profile CFD ve OpenAeroStruct örnekleri.

## v0.6.0 — Karmaşık CAD ve ilk ONERA M6

NIST kaynak parçaları ve ONERA deney verisiyle ilk 3B RANS kıyası.

## v0.7.0 — Kaynak geometri ve ayrı analiz sınaması

RAE2822 v1/v2 geometri aktarımı, dondurulmuş tahminler ve deney değerlendirmesi.

## v0.8.0 — C-grid araştırması ve M6 devamı

Konumsal ağ düzeltmeleri, başarısız sayısal kontroller ve 24 Ekim M6 koşuları.

## v0.9.0 — Hata dersleri ve ajan talimatı

Kanıtlı hata defteri, operasyonel bellek, 39 kontrol ve başlatıcı talimat sürümü.

## v0.10.0 — Düzenlenmiş GitHub dağıtımı

Kategori dizinleri, tam dosya kataloğu, sürüm notları ve hash kontrollü analiz arşivleri.
