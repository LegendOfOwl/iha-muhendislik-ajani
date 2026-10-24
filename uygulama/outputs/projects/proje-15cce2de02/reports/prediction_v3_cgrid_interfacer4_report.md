# C-grid interface-r4 — gerçek ağ denetimi

Arayüz teğetsel boyutunu dışa taşımak üç seviyede genel en kötü çarpıklığı düşürdü; tüm yakın blok, duvar, r2 kaynak eğrisi ve200c dış alan korunuyor. Bu geometri/ağ sonucu CFD yakınsaması veya fiziksel doğrulama değildir.

|Ağ|Hücre önce→sonra|Artış|Genel max skew önce→sonra|LE dış/iç normal yükseklik max önce→sonra|
|---|---:|---:|---:|---:|
|coarse|84,404→92,412|%9.49|0.95389→0.83320|22.06→3.00|
|medium|185,987→196,741|%5.78|0.95038→0.79497|10.97→2.92|
|fine|409,982→424,826|%3.62|0.93809→0.91748|11.12→3.19|

Eski dış boyut callback'i `MeshSizeExtendFromBoundary=0` altında arayüzün küçük teğetsel kenarlarının boyutunu dışa taşımıyordu. Bu bizim callback/boyut geçişi eksikliğimizdir; Gmsh BoundaryLayer algoritmasının arızası diye yorumlanmadı. [Gmsh mesh-size dokümanı ve t10](https://gmsh.info/doc/texinfo/#t10) uzaklık tabanlı Distance/Threshold boyutlandırmayı, callback ve sınır boyutlarının uzatılma seçeneğini açıklar. Burada gerçek ihrac edilmiş arayüz parçalarına tam uzaklık kullanıldı; kaynak profil yeniden çizilmedi.

Her arayüz düğümünde h=min(önceki,sonraki gerçek kenar uzunluğu). En yakın kapalı parça üzerindeki izdüşümde h doğrusal enterpole edilir. d≤0,25c için hedef min(eski_h,h_interface+0,25d);0,25–1c arası kübik smoothstep ile eski_h'ye dönülür. d≥1c'de eski callback değeri bit düzeyinde aynen döner. En yakın-parça hızlandırması midpoint cKDTree'dir; global en büyük yarı-kenar uzunluğu aday yarıçapını muhafazakâr yapar. Her seviyede sabit tohumlu1200 rastgele noktada bütün gerçek parçalara brute-force mesafe/izdüşüm kıyası yapıldı: en büyük uzaklık ve h enterpolasyon farkı0m; yanlış d<1 atlaması0. R3'ün32c'ye kadar uzayan sınırsız boyut etkisi bu sürümde yoktur. Bütün dış üçgenler yeniden üretildiği için bağlantı değişimi, boyut fonksiyonunun kompakt desteğinin dışına yayılabilir.

Actual SU2 dosyasından pozitif alan ve tüm köşe Jacobian'ı, tek bağlı akış bileşeni, kapalı AIRFOIL/FARFIELD, sıfır işaretsiz/çok-komşulu/ters yönlü iç kenar ve sıfır çakışık düğüm kontrolleri üç seviyede geçti. Tail-r2 kaynak fonksiyonları AST ile aynı; yeniden hesaplanan ve gerçek SU2'ye yazılan yakıncoords/quads/grid/body/wall bit düzeyinde aynı. Kaynak65 noktaya ve aynı r2 eğrisine sapmalar denetim JSON'larında; geometri payload SHA050ee43ead96df3cbc2a34649cf06c0839ed6fe47ae8aaf4955744d19f49cf5a. Orta/ince karşılaştırıcılar R3 sırasında üretilmiş geometry-only tail-r2 dosyalarıdır; tekrar yazılmadılar.

Normal geçiş gerçek arayüz kenarındaki komşu quad/triangle üzerinden ölçüldü: dış üçgen h=2A/kenar, iç quad h=karşı iki tepenin kenara dik uzaklık ortalaması. LE, TE, aft gövde, yatay iz ve dikey uç ayrı raporlandı. İnce TE kısa kenarları ile dikey iz ucunda dış/iç normal yükseklik oranı1'e yakın değildir; uçtaki çok uzun iz quad'ının yanındaki küçük dış üçgen oranı ayrıca korunur. Bu oran tek başına hatalı hücre veya çözülmüş sınır tabakası kanıtı değildir; açı/Jacobian ve gelecek akış duyarlılığıyla birlikte değerlendirilmeli.

Yeni global en kötü konumlar kaba(9,459155;0,350182)m, orta(9,394876;0,455634)m, ince(9,896578;0,194787)m: LE/TE arayüzlerinden dış iz bölgesine taşındı. Global min açılar sırasıyla10,01°/12,30°/4,95°; ince en kötü çarpıklık0,91748 hâlâ açıktır. Bu noktalar1c kompakt desteğin dışındadır ve eski dış boyut callback'i aynen korunmuştur. Eski hwake'nin x<10 dalındaki geçiş ile ilgili olasılık bu aşamada nedensel olarak sınanmadı. Hiçbir sonradan açı/skew cutoff'u eklenmedi ve kötü hücreler çıkarılmadı.

Gerçek LE/TE/uç önce-sonra görselleri ve global en kötü üçgen görseli üretildi. mesh_geometry_only.vtu ve native MSH4 binary dosyaları yalnız ağ/kalite verisi içerir; geri okumada düğüm/hücre/koordinat ve sınır adları doğrulandı. Kaynak kodu, girdiler, meshler ve raporlar SHA256 manifestinde kayıtlı. Özgün, tail-r2 ve R3 dosyaları değiştirilmedi.

Bu aşamada CFD başlatılmadı; y+, Cp, kuvvet, kalıntı/ağ/uzak-alan akış kabulü değerlendirilmedi. Parent'ın ayrı başlangıç/çözücü tanıları bu ağ kalitesi sonucuna dahil edilmedi. Reviewer/hedef deney/harici CFD sonuçlarına veya güncellenmiş AGENTS/PROJECT_STATE/kullanıcı raporlarına erişilmedi. Bu, kaynak yöntemle gerekçelendirilmiş sabit geometri ağ prototipidir; keyfî CAD hizmeti veya genel CFD yeterliliği değildir.
