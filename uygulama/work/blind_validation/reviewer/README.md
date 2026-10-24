# Değerlendirici alanı

Analiz girdisi `../analysis_input` içindeki yayımlanmış kaynak koordinatlar ve koşullardır. Analiz ajanı beklenen Cp/kuvvet/şok sonuçlarını almaz. `../reviewer_only` dosyaları değerlendirmeye aittir. Beklenen sonuçla kıyas, `prediction_frozen.json` ve gerçek çıktılar SHA256 ile kaydedildikten sonra yapılır. Ortak dosya sistemi üzerinde süreç ayrımıdır; güvenlik yalıtımı veya model eğitim belleği yalıtımı iddiası yoktur.

Önceki M6 incelemesindeki kanıtlı açıklar: aynı aile olmayan yüzey ve uzak alanlar, duvar y+ kabulünün geçmemesi, artıklarda taban/salınım, kuvvet geçmişindeki hareket ve devam denemesinin süre aşımında son alan üretememesi. CFL, doğrusal tolerans ve sınırlayıcı birlikte değiştirildiği için salınım artışını tek bir ayara nedensel olarak bağlamak mümkün değildir.

Bu turdaki çözüm yolu: yeni fiziksel şekil çizmek yerine özgün koordinatları kullanmak; sabit geometri/dış sınır altında bölgesel ağ ailesi; duvar normalinde katman, hücum/firar kenarı, iz ve ön çözümün gradyanından bulunan şok bölgesini ölçmek; düzenli ara kayıt; değişiklik günlüğü; deneyden önce tahmini dondurmak; sayısal ve deneysel kabulleri ayrı uygulamak.

RAE2822 Case 6 kaynak sayfasının nominal koşulları ile NASA Study 4 hesaplama koşulları farklıdır. Bu sınamada Study 4 koşulları önceden seçildi; bunlar deney basıncına göre optimize edilmez. Kaynak sıcaklık bir hesaplama varsayımıdır. Normalleştirilmiş koordinatlar 1 m veterle çözülür, Mach/Re ve referanslar korunur.

`cp.exp.gen` ve `cp.wind.gen` başlıklarında Cp yazmasına rağmen çizim konvansiyonu −Cp'dir. Kaynak `cfpost.cp.com` içindeki `Cp scale -1` ile işaret denetlenir. Deney eğrisi üst yüzey firar kenarından hücum kenarına, ardından alt yüzey firar kenarına gider. Tüm 103 nokta tutulur. `forces.lis` WIND hesaplamasıdır; deneysel CL/CD diye etiketlenemez. Basınç deneyinin belirtilen belirsizliği ±0,0026; bu sayı genel RANS doğruluk veya otomatik geçme garantisi değildir.

Üç ağ asimptotik/monoton ve iteratif kabul sağlamazsa Richardson/GCI güvenilir hata bandı olarak verilmez. Şokta yerel Richardson uygunluğu ayrıca sınırlıdır. En ince iki ağ farkının küçük olması deney doğrulaması yerine geçmez. Sıkı eşikler `../contract.json` içinde çözümden önce kaydedilmiştir; sonuçtan sonra gevşetilmez. Herhangi bir gerekli kabul açıkken asgari yeterlilik verilmez.
