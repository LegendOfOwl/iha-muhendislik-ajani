# C-grid local-r3: iz ucu dış ağ düzeltmesi

Üç yeni ağda x/c8 ucundaki dış üçgen kalitesi iyileşti. Kaynak r2 eğrisi, duvar düğümleri, bütün yakın dörtgen blok ve normal dağılımı tail-r2 ile bit düzeyinde aynı;200c kare dış sınır aynı. Pozitif alan, tüm köşe Jacobian'ları, tek bağlı akış bölgesi, ters iç kenar/işaretsiz sınır/çok-komşulu kenar kontrolleri üç seviyede geçti. Bu, geometri/ağ denetimidir; CFD yakınsaması veya akış doğruluğu kabulü değildir.

|Ağ|Hücre önce→sonra|Artış|Uç max skew önce→sonra|Uç min açı önce→sonra|Genel max skew|
|---|---:|---:|---:|---:|---:|
|coarse|84,404→86,780|%2.82|0.93643→0.68131|3.81°→19.12°|0.95910|
|medium|185,987→189,117|%1.68|0.95038→0.68681|2.98°→18.79°|0.91700|
|fine|409,982→414,194|%1.03|0.90861→0.67854|5.48°→19.29°|0.93809|

“Uç” dış üçgen merkezinin kapalı x=8 / y=tan(2,31°)×7±0,3c dikey parçasına uzaklığının0,25c'den küçük olduğu bölgedir. Önce ve sonra aynı tanım kullanıldı; hiçbir hücre açı/çarpıklık sonucu küçülsün diye çıkarılmadı. Genel en kötü hücreler ayrıca korunuyor.

Her seviyede h_end, gerçek arayüzün x=8 üzerindeki en küçük pozitif Δy'sinden ölçüldü: kaba0,00352941m, orta ve ince değerler makine okunur raporda. Yeni dış hedef boyut `min(eski_h, h_end+0,25×parçaya_uzaklık)`; h_end zaten gerçek seviyenin mesafesidir, tekrar ölçeklenmedi. Eski global boyut fonksiyonu değişmedi. Gmsh tüm dış üçgen bölgesini yeniden ağladığından hedef fonksiyonu değişmeyen yerlerde bile bağlantı/çarpıklık değişebilir. Sadece açık yakın bloklar birebir korunma güvencesi taşır.

Sınırsız doğrusal uzaklık fonksiyonunun boyut hedefi üzerindeki etkisi geometrik olarak kompakt değildir: eski dış üçgen merkezleriyle örneklenince en uzak azaltma kaba32,159c, orta11,950c, ince7,859c mesafededir. En güçlü azaltma uçta bulunur; toplam hücre artışları tabloda sınırlıdır. Bu sürüm önerilen doğrusal kuralı aynen uygular; dıştaki etkiyi sessizce sıfırlayan bir cutoff eklenmedi. Sadece1c içinde etkili kompakt bir düzeltme ayrı sürüm ve denetim gerektirir.

Kaba genel max skew0,95389'dan0,95910'a biraz yükseldi; yeni en kötü hücre(-0,059005;−0,023367)m'de LE dış-blok geçişindedir. Orta en kötü(-0,063310;−0,002506)m, ince(1,001477;0,060658)m'dedir. Bunlar gizlenmedi veya yeni bir açı eşiğiyle geçer sayılmadı. Dar uç düzeltmesi başarılıdır; genel ağın her bölgesi iyileşti denmez.

Kaba önce ağı mevcut tail-r2 SU2 dosyasıdır. Orta/ince tail-r2 karşılaştırıcıları aynı değiştirilmemiş kaynak fonksiyonlardan bu denetim için work/ altında gerçekten üretildi; bunların CFD koşusu yoktur. Her üç seviyede source/normal/body/wake fonksiyonları AST karşılaştırmasında aynı; yeniden hesaplanan yakın düğüm/quads/grid/duvar ve actual SU2 ihracı birebir eşleşti. Özgün build_cgrid.py ve tail-r2 dosyaları değiştirilmedi.

Kaynak geometrinin65 noktası aynı r2 B-spline'a makine duyarlığında oturuyor; duvar düğüm/eğri ve lineer panel sapmaları her case local_revision_audit.json dosyasında. Geometri payload SHA050ee43ead96df3cbc2a34649cf06c0839ed6fe47ae8aaf4955744d19f49cf5a. Veter1m; fizik girdileri yalnız provenans hash'iyle korundu, bu aşamada akış çözülmedi. Yakın blok0,06c, ilk yükseklik/büyüme/normal cap ve katman sayıları summary tablosunda kayıtlı. Tüm seviyeler aynı kaynak eğriyi ve dış alanı kullanır.

Yöntem, [Gmsh4.15.2](https://gmsh.info/doc/texinfo/#Structured-grids) ile açık yakın blok + dış üçgen ağı yaklaşımının yerel boyut revizyonudur. Bu çalışmada yeni bir şok/deney hedefi aranmadı. Gerçek uç önce/sonra görselleri ve kalan global en kötü hücre görseli incelendi; mesh_geometry_only.vtu yalnız ağ/kalite verisi içerir. y+, Cp, kuvvet, kalıntı ve uzak alan akış duyarlılığı bu revizyonda değerlendirilmedi. İlk şok sıcaklığından uzaktaki bu düzeltmenin CFD sorununu çözdüğü iddia edilmiyor. Parent'ın ayrı çözücü tanıları bu ağ kabulüne dahil edilmedi.

CFD başlatılmadı. Reviewer modülü veya beklenen deney/harici CFD sonuçları okunmadı; `audit_cgrid.py` metnindeki reviewer import'u fark edilip çalıştırılmadı, bu sürüm için bağımsız SU2 denetleyicisi yazıldı. Güncellenmiş global AGENTS/PROJECT_STATE ve kullanıcı raporları açılmadı.
