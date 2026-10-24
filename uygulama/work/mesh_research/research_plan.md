# RAE2822: kaynaklı teşhis ve kontrollü ağ araştırması, v3

Bu bir araç doğrulama çalışmasıdır. Gerçek İHA girdileri değiştirilmez. V1/v2
çözümleri, deney değerlendirmeleri ve mühürleri korunur. Önceki minimum kabul
sözleşmesi değişmez (`work/blind_validation/contract.json`).

## Okunan birincil kaynaklardan çıkarılan eylemler

1. [Diskin ve Thomas, NIA Report 2008-12 / NASA NTRS 20090007493](https://ntrs.nasa.gov/api/citations/20090007493/downloads/20090007493.pdf),
   §2, §4 ve §6: yüksek en-boy oranı, eğrilik ve stencil düzeni birlikte gradyan
   doğruluğunu etkileyebilir. Tek bir hücre sayısı veya en-boy oranı bunu çözmez.
   Bu vaka için neden kanıtı değildir. Eylem: aynı geometriye açık, düzenli
   duvar-normal sütunları; ilk katman, büyüme ve dış geçişi yerinde ölçme.
   Ayrı analitik alan testi düşünülür; Python kopyası native SU2 doğrulaması
   diye adlandırılmaz. GG'nin otomatik daha doğru olduğu çıkarılmaz.
2. [Gmsh 4.15.2 kılavuzu, transfinite / boundary layer](https://www.gmsh.info/doc/texinfo/gmsh.html#Structured-grids):
   BoundaryLayer alanı 2D ağ kısıtıdır; açık topolojik blok değildir. Normal
   ekstrüzyonda da köşe/fanların kendiliğinden çözüldüğü varsayılamaz.
   Eylem: kaynak B-spline üzerinde açık C-blok, ortak iç iz kesiti; dış
   üçgenler Gmsh ile ve her arayüz kenarı iki akış hücresine komşu olacak.
   Kullanılan kod Gmsh transfinite yüzey komutuyla kurulmuş bir blok değildir;
   açık Python koordinat haritalaması ve sabitlenmiş arayüzdür.
3. [NASA RAE Study 1: kaynak C-grid ve sınırlar](https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf01/raetaf01.html):
   yayımlanmış 369×65 C-grid, J1'de eşlenmiş iz kesiti içerir. Eylem: indirilmiş
   özgün PLOT3D koordinatlarını hareket ettirmeden SU2'ye dönüştürmek; tam
   çakışan kesit düğümlerini kaynak/bağlantı denetimiyle birleştirmek.
4. [NASA RAE Study 4](https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html):
   SA/SST seçenekleri, kuvvet yakınsaması ve sınır tabakası incelemesi var.
   Sayfanın kaynak ağı için ortalama y+<2 ifadesi bizim max y+<1 kapımızı
   karşılamaz. Duyarlılık çalışması yapılmadığını sayfa açıkça belirtir.
5. [SU2 v8.5.0 gradyan kaynak kodu](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/gradients/computeGradientsLeastSquares.hpp),
   özellikle 217–254. satırlar: düğüm kenar komşuları; uzaklığın karesinin
   tersi normal denklem ağırlığı. Çağrı yolu
   [CFVMFlowSolverBase.inl](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/solvers/CFVMFlowSolverBase.inl).
   WLS adı hakkında bellekten varsayım yapılmadı. Kaynak kodu incelemesi
   gerçek çalıştırılmış native gradyan hata ölçümü değildir.

## Deney matrisi ve sonuçtan bağımsız roller

| Kol | Değişen | Sabit kalan / yorum sınırı |
|---|---|---|
| `v3_reference_sourcegrid` | NASA yayımlanmış 369×65 ağ; kaynak 305 düğümlü çokgen | V2 RANS/SA-noft2, M/Re/alfa/T, WLS/JST_MAT ve sayısal yöntem. Bu ana ajanın referans ağ tanısıdır, kör sınama değildir. |
| `v3_cgrid_coarse/medium/fine` | Aynı r2 eğrisi, aynı 200c dış sınır; teğetsel/normal/yakın-dış ağ ölçekleri 2/3, 1, 1.5 | Aynı fizik ve tek yöntem. 0.06c açık yakın blok; ilk uzaklık 0.8µm/ölçek, büyüme 1+0.14/ölçek, dış normal aralık tavanı 0.00075c/ölçek. Her seviye ayrı denetlenir. |
| Sonraki normal duyarlılık | Gerekirse yalnız normal dağılım / blok kapsamı | Tamamlanıp yakınsamadan kapalı sayılmaz. Eski 0.01c ve yeni 0.06c farkı salt hücre sayısı etkisi değildir. |
| Sonraki uzak alan | Aynı iç ağ ve 200c→400c | Önceki 400c çalışılmamış ağ sonuç sayılmaz. |

Kaynak ağ kontrolü saf ağ inceltme değildir: geometrinin temsil sürümü ve uzak
sınır da V2'den farklıdır. Bütün dış kenarlarda mevcut SU2 FARFIELD kullanılır;
WIND'in ayrı basınç çıkışı bire bir yeniden üretilmez. Bu karışan değişkenler
raporlanmadan fark yalnız C-grid'e atfedilemez.

Ana ailede deney kıyas rolü en ince önceden tanımlı seviyedir. Daha düşük Cp
hatası veren ağ/ayar seçilip ona doğrulandı denmez. Üç seviye, iteratif yakınsama,
y+, normal/uzak alan ve tüm deney kapıları tamamlanmadan `minimum=false`.
Yeni C-blok taslağı ayrı analiz geçmişinde hedef sonuç verilmeden üretildi.
O analizci devam edemediğinde ana ajan denetim ve gerçek çözüm işini devraldı;
ana ajan eski deney değerlendirmesini biliyor. Bu devam çalışması yeni bağımsız
kör deney diye sunulamaz. Beklenen katsayılar native çözücüye verilmez.

## Dondurma ve kayıt

Her yeni deneme yeni klasördür; hazır config/ağ/alan üzerine çözüm yazılmaz.
200 adımda immutable restart/yüzey/hacim çıktısı; yalnız aynı iterasyonun tam
üçlüsü ve o satırın geçmişi kullanılır. Süre aşımı terminal satırı ayrı tutulur.
Config, geometri, ağ, kaynak kodu ve çözüm SHA256 kayıtları tutulur.
V3'ün tahmin çıktıları deney puanı hesaplanmadan ayrı mühürlenir; bu prosedür
ana ajanın önceki sonuç bilgisini ortadan kaldırmaz.
