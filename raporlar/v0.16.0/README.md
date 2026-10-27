# SU2 kaynak derlemesi ve güvenilir karşılaştırma hazırlığı

27 Ekim 2026 · Yeni CFD koşusu: **0** · Genel fizik kabulü: **false**.

Sabit SU2 v8.5.0, Eigen ve MEL kaynakları indirildi; 4357 kaynak dosyası arşivlerle birebir doğrulandı. C++17/Haswell/OpenMP dört iş parçacığı derleyici denemesi geçti. İlk gerçek SU2 derlemesi 259. hedefte başlık arama yolu hatasıyla durdu; kaynak baytlarını koruyan ortak arama yolu düzeltmesi kaydedildi. İkinci deneme kullanılabilir RAM 1 GiB sınırının altındayken native süreci başlatmadan reddedildi. 70 yeni yazılım kontrolü geçti; önceki 14 süreç kontrolünün kanıtı ayrıca denetlendi. Yeni CFD çalıştırılmadı; pristine32 yeniden üretimi ve cap256 etki/maliyet sınaması bekliyor. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

## Neden bu yöntem?

Önceki native ölçümde çizgi birliği 52689 noktanın 7200’ünü ve ayrı doğrulanmış eski aşama RHS yoğunluk kare toplamının %53,8965’ini kapsıyordu. Kaynaktaki 32 nokta sınırını 256’ya çıkarmak bir mekanizma hipotezidir; isotropi/yön/komşuluk durdurmalarını veya çizgi dışı Jacobi bağlaşımını kaldırmaz. Bu turda sınır henüz değiştirilip çözülmedi.

## Gerçekte kurulan ve çalıştırılanlar

Meson 1.8.2, Ninja 1.13.0 ve psutil 7.1.0 proje Python ortamında; 311245 baytlık sabit libgomp paketi taşınabilir GNU araç klasöründe. İlk OpenMP derlemesi eksik `-lgomp` ile başarısızdı; bu kayıt korundu. Ek bileşenden sonra gerçek program dört iş parçacığı, 8 bayt double ve OpenMP 202111 bildirdi. Sistem PATH/DNS/TLS ayarı değişmedi.

SU2 commit `12eb826f049ef7f67df974dfcb44cf36ee07c0f8`, Eigen `d71c30c47858effcbd39967097a2d99ee48db464`, MEL `46205ab019e5224559091375a6d71aabae6bc5b9`. Arşivler sırasıyla 18876892/2719400/13894 bayt; gzip sonu, güvenli yollar ve tüm dosya baytları denetlendi. İndirilen kaynaklar/derleyici paketleri public dağıtıma eklenmez; URL/SHA256 ve yama/derleme kayıtları korunur.

## İki gerçek derleme girişiminin sonucu

| Kayıt | Başarı | Son native çıkış | Son aşama süresi,s | Durdurma sebebi |
|---|---|---|---|---|
| p32a | False | 1 | 555.171 | build_root_nonzero_exit |
| p32b | False | None | 0.000 | system_available_memory_below_minimum_before_launch |

`p32a`, 259/290 Ninja hedefinde `CFlowTractionInterface.cpp:34` için eksik başlık hatası verdi. Bu satırın göreli yolu, bulunduğu `interfaces/fsi` klasöründen hedefe ulaşmıyor. Ortak `cpp_args=['-I../source/SU2_CFD/src/interfaces']` seçeneği gerçek `Common/include/interface_interpolation/CInterpolator.hpp` dosyasına çözülüyor. Bu geometrinin/denklemin yaması değildir; aynı seçenek pristine32 ve ileride cap256 için kullanılacak. Henüz başarılı tam derleme kanıtı değildir. `p32b` öncesi kullanılabilir RAM 0,804 GiB olduğundan 1 GiB alt sınırı native süreci başlatmadı; çıkış kodu **null**, program başarısızlığı/CFD sonucu atanmadı. Başka uygulamalar kapatılmadı.

Derleme: tek iş, toplam 1800 s, süreç ağacının örneklenen çalışma kümesi≤3 GiB, boşRAM≥1 GiB. İlk gerçek derleme yaklaşık 1,65 GiB tepe kullandı; sonraki başlangıç için en az 2,7 GiB kullanılabilir bellek öneriliyor. WindowsJobObject yalnız kendi derleyici alt süreçlerini sınırlar; 0,1 s örnekleme geçici tepeyi kesin yakalama garantisi değildir. Yerel GNU 16/UCRT, resmî binary’de görülen GNU 13/win 32 işaretinden farklıdır.

## CFD başlamadan dondurulan kapılar

Üç taze kolun aynı ağ, özgün fine 3999 NDseed, fizik, tüm açık sayısal/output ayarları ve dört native iş parçacığıyla 200 adım çalışması planlandı. Tümünde `LINELET` alanı istenir; eski 200 adımın eksik alanı başka 1 adımlık dosyadan doldurulmaz. Her kol 240 s/2,5 GiB üst bütçede ve alan/yüzey/restart/geçmiş 199 birlikte mühürlenmek zorunda.

Önce release 32–pristine32: beş SI log10 RMS eğrisinin bütün 200 adımında en büyük fark≤0,03; son |ΔCD|≤1e-8; toplam akış+SA Krylov farkı≤%5; 52689 noktada koordinat eşleme≤2e-7 m ve tam aynı boolean üyelik.0,03 yerel işletim ekranıdır, evrensel kayan nokta/fizik hata bandı değildir. Son 100 CD aralığı<1e-7, sonlu alanlar ve pozitif yoğunluk/basınç ayrıca gerekir.

Bu kapı geçerse yalnız tek cap 32→256 deklarasyonu değişebilir. Aynı derleyici/runtime ve tüm diğer kaynak baytları doğrulanır; yoğunluk kazancı≥0,3 log, SA kötüleşmesi≤0,1 log, toplam Krylov ve gözlenen süre oranları≤1,5 gerekir. Native üye sayısı ve **aynı eski RHS** kapsama payı artmalıdır. Graph renkleri çizgiID değildir; bu yeni alanın artığı veya ağ hata bandı değildir. Eşikler sonuçlara göre gevşetilmeyecek; tarama/otomatik uzatma yapılmayacak.

## Güvenilirlik kontrolünün sınırı

31 karar +20 veri çıkarma +9 derleme koruması +10 yürütücü karşı örneği geçti. Arama yolu seçeneği değişince ilgili 9 derleme testi ayrıca tekrarlandı; bunu 9 yeni test saymadık. Önceki 14 süreç kontrolü yeniden çalıştırılmadan mevcut 5 gerçek Windows senaryosunun 15 kayıt dosyası denetlendi. Kontrollü sahte dosyalar kullanan testler CFD çalıştırmaz. Gerçek eski 200 adımlık alanla veri okuyucu sınandı:200 SI geçmiş satırı ve 199 eşzamanlı dosyalar okundu, eksikLinelet nedeniyle kabul reddedildi.

Eski CFD mühürlerinin **738 hash kaydı** yeniden eşleşti. Gerçek İHA’nın üç girdisi v0.15 kataloğu/depo kopyalarıyla aynı. Bu kaynak benchmarkına ait geliştirmeler keyfiCAD→CFD hizmeti veya LLM uzmanlığı kanıtı değildir; eski fine 3999/üç-ağ/RAE/M6/VLM kabulleri kapanmadı.

## Kanıt ve sonraki iş

- [Ham sonuç ve kimlikler](../../uygulama/outputs/reports/su2_kaynak_kontrolu_20261027.json)
- [Derleyici gerçek OpenMP denemesi](../../uygulama/outputs/reports/su2_build_preflight_20261027.json)
- [60 yazılım kontrolü ve eski süreç kanıtı](../../uygulama/outputs/reports/su2_source_software_checks_20261027.json)
- [10 yürütücü karşı örneği](../../uygulama/outputs/reports/su2_native_controller_checks_20261027.json)
- [Sabit yöntem sözleşmesi](../../uygulama/work/su2_build_20261027/method_design.json)
- [Başlık yolu teşhisi](../../uygulama/work/su2_build_20261027/include_path_diagnosis.json)

Sonraki iş: yeterli RAM’de yeni pristine32 derlemesi; başarılıysa fresh release 32/pristine32 yeniden üretimi. Cap 256 ancak bundan sonra. ANSYS kurulmadı; başka büyük geliştirme paketi eklenmedi.

Kaynaklar: [sabit SU2 kaynağı](https://github.com/su2code/SU2/tree/12eb826f049ef7f67df974dfcb44cf36ee07c0f8), [sabit Eigen](https://gitlab.com/libeigen/eigen/-/tree/d71c30c47858effcbd39967097a2d99ee48db464), [sabit MEL](https://github.com/pcarruscag/MEL/tree/46205ab019e5224559091375a6d71aabae6bc5b9). İddialar yerel hash’i doğrulanmış kaynak/arşiv, native kayıt ve testlere dayanır.


[Önceki gerçek LINELET kapsamı](../v0.15.0/README.md) · [Önceki artık tanısı](../v0.14.0/README.md)
