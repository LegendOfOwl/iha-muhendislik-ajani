# Ek kayıt03: yöntem paketinin etkin değişimleri ve rekonstrüksiyon ayrımı

R4/JST'nin 4.000 tam alanında yoğunluk artığı -6,5746, son200CL/CD
aralığı6,7436e-4/5,7350e-5 idi; maxy+0,48554 uygundu. Sonraki terminal4173
bu alanla karıştırılmadı. Deneme kabul edilmedi; daha fazla iterasyonun
kesinlikle işe yaramayacağı sonucu da çıkarılmadı. Bütçeli tanı saklandı.

R4/Roe aynı mesh ve başlangıçla gerçekten çalıştı. Native başlık ikinci
mertebe flow ve birinci mertebe turbulence politikasını doğruladı. Ancak
300–1.600 arasında yoğunluk yaklaşık-5,4 çevresinde kaldı. Bir sonraki ayrım
aynı Roe yönteminde yalnız `MUSCL_FLOW=YES -> NO` olacaktır. Amaç mean-flow
rekonstrüksiyonunu devreden çıkarınca iterasyonun düzelip düzelmediğini
sınamaktır. Birinci mertebe deneme yüksek doğruluk veya genel kabul yerine
geçmez; önceden seçilmiş fine rolü değişmez. Fizik/ağ/seed/CFL/MG/SA ve
doğrusal çözücü aynı kalır. Geçen birinci mertebe alan yalnız başlangıç
üretme veya sorunu daraltma amacıyla kullanılabilir; ikinci mertebe
yakınsamasını kanıtlamaz.

Kaynaklar:

- [SU2 resmî limiter açıklaması](https://su2code.github.io/docs_v7/Slope-Limiters-and-Shock-Resolution/):
  limiter yalnız MUSCL etkinse kullanılır; K katsayısı ölçeğe duyarlıdır.
  Mertebe/limiter adını fiziksel doğruluk kanıtı saymıyoruz.
- [v8.5.0 SIMD factory,38–79](https://github.com/su2code/SU2/blob/v8.5.0/SU2_CFD/include/numerics_simd/CNumericsSIMD.cpp#L38-L79):
  JST_MAT'te kaba MG akısı LAX, Roe'da Roe'dur.
- [v8.5.0 upwind,63–70](https://github.com/su2code/SU2/blob/v8.5.0/SU2_CFD/include/numerics_simd/flow/convection/upwind.hpp#L63-L70):
  MUSCL yalnız en ince MG seviyesinde etkin. MGLEVEL=3 sabit tutulsa da
  JST→Roe paketi kaba akıyı LAX→birinci-mertebe Roe olarak değiştirir.
  Bu, tek finest-flux katsayısının testi değildir.
- [Açık PR2959](https://github.com/su2code/SU2/pull/2959),19Ekim'de incelendi:
  NishikawaR4, wall-distance/sharp-edge ve NEMO adlarıyla ilgili. Burada
  Venkatakrishnan kullanıldığı için başlığı görüp bizim nedenimiz saymadık.
- [Açık PR2956](https://github.com/su2code/SU2/pull/2956),19Ekim'de incelendi:
  scalar MUSCL limiter/pozitiflik/diğer seçenek düzeltmeleri. Mevcut ana
  denemelerde MUSCL_TURB=NO, LIMITER_ITER=999999 ve edge limiter yok;
  bu başlık kendi başına mevcut hatayı açıklamaz. v8.5 yerine geliştirme
  sürümü kurulup kanıtsız bir çözücü değişikliği yapılmadı.

VTU `Residual_Density` dışa yazılmış LinSysRes çalışma vektörüdür; geçmişin
ayrı kayıtlı `GetRes_RMS` değeriyle sayısal olarak eşleşmiyor. Konumsal
görsellerde çalışma vektörü diye raporlanır; history yakınsama eşiği yerine
geçmez. Bu ayrım ham akış/kuvvet alanlarını veya deney puanlarını değiştirmez.
