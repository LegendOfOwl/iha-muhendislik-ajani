# Kaynaklı teşhis ve güvenilirlik geliştirmesi — 24–25 Ekim 2026

Bu ek, yeni bir fizik modeli veya uzmanlık belgesi değildir. Mevcut M6 benchmarkındaki belirsizliği azaltan bir geliştirme turudur.

## Uygulanan yöntem

1. Temsil/girdi, çözücü iterasyonu, konumsal ağ çözünürlüğü, uzak alan ve fiziksel model hatalarını ayrı izle.
2. Aynı başlangıçla bir nedeni ayırt eden eşli denemeyi önceden kaydet. Burada yalnız `LINEAR_SOLVER_ITER=10/40` değişiyor. Fizik, ağ, seed, doğrusal tolerans ve CFL aynı.
3. Önce ham çıktıları dondur; sonra bütün deney noktalarıyla değerlendir. Başarısızlık da dondurulur.
4. Önceden seçilmiş 0,3 ek log10 düşüş yoksa bu ayarın daha fazla değerini tarama. Bu etki ölçütü mühendislik kabulünü değiştirmez, istatistiksel güven düzeyi değildir.
5. Sonraki işi açık bağımlılıklara göre seç. Kanıt bozuksa sonucu yorumlama; iterasyon açıkken ağ farkını saf ayrıklaştırma hatası sayma. Bu seçim açık bir sezgisel politikadır; matematiksel optimumluğu kanıtlanmadı.

## Konumsal gösterge

Gerçek hacim alanının Mach değerinden beyazlatılmış yerel ikinci derece en küçük kareler Hessian'ı çıkarılır. Aynı tetrahedronun köşe koordinatlarıyla boyutsuz eğrilik göstergesi ve baskın yön hesaplanır. Kötü koşullu/dejenere şablonlar maskelenir. Analitik doğrusal, ikinci derece ve dönmüş ince şablonlarla sınanır; m/mm dönüşümü ayrıca kontrol edilir.

Bu, NASA'nın tam çok ölçekli Lp metriği değildir. Tam alanlı anizotropik yeniden ağ üretimi, metrik karmaşıklık normalizasyonu, gradation kontrolü, geometrik sınır projeksiyonu, sınır tabakası prizma uyarlaması ve adjoint ağırlıkları uygulanmadı. Şokta düzgünlük varsayımı bozulur. Gösterge bir inceleme önceliğidir; CL/CD hata bandı değildir.

## Kaynaklardan alınanlar

- [SU2 doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/): iç çözüm doğruluğu, iterasyon sınırı, CFL ve toplam maliyet birlikte değerlendirilir. Çok sıkı iç tolerans otomatik olarak daha doğru son akış demek değildir. Sürüm7 dokümanı, kurulu v8.5.0 etiketli koduyla birlikte okundu.
- [SU2 v8.5.0 config](https://github.com/su2code/SU2/blob/v8.5.0/config_template.cfg): doğrusal sınırlar, yerel CFL geribeslemesi ve otomatik türev seçenekleri. Kurulu pakette `_AD` executable yok; Python adjoint betiğinin bulunması çalışan ayrık adjoint çözümü kanıtlamaz.
- [NASA NPARC](https://www.grc.nasa.gov/www/wind/valid/tutorial/iterconv.html): artık ile mühendislik niceliğinin yakınsaması birlikte denetlenir.
- [Balan vd., 2020, M6 anizotropik uyarlama](https://ntrs.nasa.gov/citations/20200003084): Mach'ın ikinci türevlerinden yönlü metrik çıkarılıp sınırlı mesh karmaşıklığıyla uyarlama yapılır. Makaledeki geometri/ölçek/çözücüler bizim kaynak meshimizle birebir değildir. Yayımlanan katsayılar bu koşuya aktarılmadı.
- [NASA refine](https://github.com/nasa/refine): tam uyarlama için aday açık araç. Bu turda derlenmedi/kurulmadı. Gerekli geometri, format, metrik ve sınır koruma köprüsü henüz doğrulanmadı.

Kendi ekimiz: dondurulmuş kanıt, tek değişkenli neden sınaması, önceden kayıtlı bırakma ölçütü ve bağımlılık sırasına göre deney seçimini tek denetçide birleştirmek. Bunun LLM davranışına veya görülmemiş CFD vakalarındaki doğruluğa katkısı henüz ölçülmedi.

## Kullanım

- `linear_pair.py prepare|run|freeze`: tek kayıtlı ve sınırlı native test; aynı klasörde ikinci kez koşmaya izin vermez.
- `review_pair.py`: iki mühürden sonra deney kıyası, bağımsız kuvvet integrasyonu, maliyet ve teşhis.
- `curvature.py`: seçilmiş lin10 alanından CSV/VTU ve konumsal harita.
- `curvature_v2.py`: ilk prototipin uygunsuz yerel kullanımlarını konveks şablon desteği, fit koşulu/hatası ve40/80 komşuluk ölçeğiyle süzer. Maskeli bölgeler düşük hatalı sayılmaz. İlk prototip/alan/haritalar korunur; yeni CFD koşusu değildir.
- `cfl_feedback.py prepare|run|freeze`: ilk çift etki ölçütünü geçmezse ayrı sözleşmeyle sabit/geribeslemeli CFL için iki600-adım koşusu. `resume` yalnız kayıtlı süreç yolu ve oluşturma zamanı doğrulanırsa aynı native işi izler. İlk sarmalayıcıdaki hata ve kurtarma kaydı saklanır.
- `test_methods.py`: bozuk/eksik kanıt ve bağımsız analitik karşı örnekler.
- `check_agent_guards_20261025.py` (.venv-cad): eski39 denetimin yalnız çıktı tarihi değiştirilmiş kopyası. Özgün24 Ekim raporu v0.10.0 SHA256 değeriyle geri korunmuştur; yeni sonuç25 Ekim dosyasındadır. `agent_guard_report_preservation_20261025.json` ayrımı kaydeder.
- `project.py run reliability --project proje-e9319baef1`: kayıtlı mühürleri ve ham geçmişi yeniden denetler. GUI'de aynı proje altında “Kayıtlı sonuçların güvenilirliğini yeniden denetle”. Yeni CFD çalıştırmaz.

Kaynakların URL/zaman/SHA256 kayıtları `sources/manifest.json` içindedir. Eski M6/RAE denemeleri değiştirilemez; yeni raporlar ayrı adlarla tutulur.
