# Ek kayıt 02: arayüz ağını düzeltme ve ayrı akı politikası denetimi

R3 yalnız iz ucundaki dış ağı inceltti. R4, kaynak r2 eğrisi ve tail-r2 yakın
blok koordinatları değişmeden bütün blok/dış ağ arayüzünün gerçek kenar
uzunluğunu dış üçgen boyutuna bağlar. Etki d<=0,25c tam, 0,25..1c arasında
yumuşak sönümlü, d>=1c eski boyut kuralıyla bit aynıdır. Böylece uzaktaki tüm
ağı sebepsiz sıklaştırma önlenir. Yine de arayüzün tüm normal boyut oranları
birörnek değildir; özellikle iz tarafındaki büyük oranlar ve fine dış iz
bölgesindeki 4,95 derece hücre açısı açık olarak saklanır. Geometri/topoloji
geçişi, genel CFD ağı yeterliliği olarak etiketlenmez.

İlk R4 coarse çözümü 2.000 adımı geçtiğinde yoğunluk artığı yaklaşık -6,13'e
geri döndü. Son200 kuvvet aralıkları da eşiklerin üzerinde. Daha düzgün
hücrelerin tek başına sorunu çözdüğü iddia edilmiyor. Bu kaydın hazırlanması
sırasında ilk R4 çözümü sürüyor; henüz R4 deney puanı hesaplanmadı.

[Palacios ve diğerleri, AIAA2014-0243](https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf),
sayfa23/33, Case6 için JST/Roe yöntemlerini karşılaştırır. Upwind akıda
primitive değişkenlerde Venkatakrishnan sınırlayıcı kullanır. Bu kaynak ayrı
Roe/MUSCL akı politikası denetimini gerekçelendirir; Roe'nun bu yeni ağda kesin
başarılı olacağını veya SA ile yapılan bu denemenin makaledeki bütün
karşılaştırmayı yeniden üreteceğini göstermez. T, türbülans modeli ve fiziksel
koşullar kaynaktan yeni baştan kopyalanmaz.

Sayfa24/33 doğrusal çözücü toleransını ayrıca araştırır; o örnekte 1e-2 en kısa
toplam çözüm süresini vermiştir. Dolayısıyla 1e-6'yı her sorunun çözümü saymıyoruz.
Mevcut gerçek LinSolRes kayıtları da istenen 0,05'e ulaşıldığını gösterir.

## Sonuçtan önce kaydedilen yeni yöntem ailesi

- `v3_r4roe_coarse_warmstart`, `v3_r4roe_medium_warmstart`,
  `v3_r4roe_fine_warmstart`: aynı R4 ağları; ince seviye deney değerlendirme
  rolü baştan sabit. Bu yeni sayısal yöntem ailesidir. Önceki R4/JST ailesinin
  eksik ince rolünü sonradan bir Roe coarse sonucuyla kapatmaz.
- İlk deneme, R4 coarse ile **aynı mesh ve aynı seed.dat** kullanır. Başlangıç
  tahmini yine kendi v2 fine3400 alanıdır, deney hedefi değildir.
- Değişen politika: `CONV_NUM_METHOD_FLOW=ROE`, `MUSCL_FLOW=YES`,
  `SLOPE_LIMITER_FLOW=VENKATAKRISHNAN`; mevcut 0,03 sınırlayıcı katsayısı bu
  yöntemde etkin olur. Bu bir akı+yeniden kurma+sınırlayıcı paketidir; yalnız
  tek katsayı değişiminin nedensel etkisi diye sunulamaz. Merkezi yöntemde
  MUSCL etkin değildi. Türbülans taşınımı bu denemede birinci mertebe kalır.
- CFL1, MG3, WLS, doğrusal çözüm ve fizik sabit. Eski başarısız alanlar,
  geometri ve sözleşme değişmez. Önce coarse yakınsama çözülür; orta/ince
  pahalı çözümler başarısız coarse'u gizlemek için çalıştırılmaz.
- Yoğunluk<=-8, aynı200 kuvvet penceresi, maxy+<1, üç ağ, bölgesel/uzak alan
  ve bütün103 deney noktası kapıları değişmez. Hiçbir yöntem ailesi sırf
  diğerinden daha iyi deney puanı verdi diye doğrulanmış sayılmaz.
