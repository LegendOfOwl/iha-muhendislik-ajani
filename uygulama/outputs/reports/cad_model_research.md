# CAD modelleri — araştırma ve bu bilgisayardaki sonuç

**Güncelleme:** Bu dosya ilk K-1B/Zero denemelerini kaydeder. Daha yeni Cadmonkey data-32'nin kurulması, daha geniş karşılaştırmalar ve doğru kullanım denetimi [güncel toplu raporda](proje_durum_ve_k1b_arastirma.html) bulunur. Eski K-1B sonucunu bütün aileye genelleme.

18 Ekim 2026. **Bu projede ana yöntem: Codex'in görevi planlaması, CAD/çözücü araçlarını çalıştırması ve sonucu bağımsız kontrollerle değerlendirmesi. Küçük CAD modeli yardımcı taslak üreticisidir.**

## Verdiğin iki bağlantı

[Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) bir veri kümesidir: “1m”, yaklaşık bir milyon örneği anlatır. Bir milyon parametreli model değildir. İlgili [Zero-To-CAD-Qwen3-VL-2B](https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B), sekiz temiz 256×256 görünüşten CadQuery programı üretir. Metinden bütün uçağı tasarlamak veya mühendislik hesabını doğrulamak amacıyla sunulmamıştır. Veri kümesinin tamamını indirmedim.

Reddit'teki [geliştirici paylaşımı](https://www.reddit.com/r/LocalLLaMA/comments/1oavxt8/i_built_a_1b_cad_generator_model/) ise [MakeMe / K-1B](https://github.com/ThomasVuNguyen/MakeMe) hakkındadır. Gemma tabanlı küçük bir modelle metinden OpenSCAD, ardından STL/OBJ üretir. “Talimat ver, hızlıca çizsin” diye hatırladığın kullanım buna daha yakındır. Model dosyaları geliştiricinin [Hugging Face deposundadır](https://huggingface.co/ThomasTheMaker/k-1b-gguf).

## Yerel ölçüm

RTX 4080 Laptop üzerinde Windows için yerel llama.cpp b11719 kullanıldı. Dosya sürümleri, gerçek komutlar, istemler, kodlar ve çıktılar saklandı. Ağırlıklar upstream SHA256 değerleriyle doğrulandı. İnternet bağlantısı model çalıştırmak için gerekmez; mevcut Codex hesabı ise bulut modelini kullanır.

| Deneme | Kurulan sürüm | Gerçek sonuç |
|---|---|---|
| K-1B: 40×30×8 mm kutu | Q8_0, 1,069 GB | Boyut ve hacim doğru; istenen merkezleme yanlış. Kabul edilmedi. |
| K-1B: aynı plakada Ø10 delik | Aynı | Delik çıkarma işlemi yok; tanımsız değişkenler var. Açılan STL, doğru parça değildi. |
| K-1B: Ø20/Ø6, 12 mm ara parça | Aynı | Çapları yarıçap gibi kullandı; geometri yanlış. |
| Zero-to-CAD: delikli plakanın 8 görünüşü | Üçüncü taraf Q6_K + f16 görsel bağdaştırıcı | İki yerel denemede tekrarlayan ve tamamlanmayan kod. Son 4096 token denemesi geçerli katı üretmedi. |

K-1B'nin üç kısa denemesinde çalıştırıcının bildirdiği üretim hızı 210,7–219,0 token/s, yükleme dahil süre 1,89–2,02 saniyeydi. Soğuk başlangıç veya önbellek kontrollü performans ölçümü yapılmadı. Bu hız, doğruluk değildir. Kutu yalnız merkezleme gereksiniminde kaldı; diğer iki parçada boyut/delik sorunları da vardı. Üç istemin bütün kabul ölçütlerini sağlayan özgün K çıktısı **0/3**.

Zero-to-CAD son denemesi 25,94 saniye sürdü ve kod kesildi. Bu, Q6 dönüşümü ve burada kullanılan yerel giriş/çalıştırıcı yolunun sonucudur; özgün BF16 modelin yayımlanmış başarısını çürüttüğü iddia edilmiyor. Özgün BF16 ve geliştiricinin tam benchmark kümesi burada denenmedi.

Ham kanıt ve ölçüler: [cad_model_benchmark.json](cad_model_benchmark.json). Kabul ölçütleri: boyut/hacimde %1, istenen merkezleme, delik iç/dış nokta sorguları ve kapalı ağ. Kodun çalışması ayrı, bu ölçütlerin geçmesi ayrı izlenir.

## Hata düzeltme döngüsü

Başarısız üç K taslağını **bu Codex çalışması** açık ölçülerle düzeltti; K-1B kendi kendine düzeltmiş gibi gösterilmedi. Düzeltilen OpenSCAD'ler gerçek OpenSCAD'de STL'ye çevrildi; ölçü/hacim/delik/merkezleme kontrolleri tekrar yapıldı. Aynı parçalar CadQuery'de ayrı oluşturulup STEP'e aktarıldı ve tekrar açıldı: **3/3 geçti**. [Düzeltme kanıtı](checked_parts_results.json), [kontrollü parçalar](../cad/checked_parts/).

Bu örnek, ajanın bir çıktıyı reddedip gerekçeli olarak düzeltmesini gösterir. İHA dayanımı veya üretim uygunluğu testi değildir.

## Daha uygun alternatifler

“En iyi” modeli bütün görevler için söylemek doğru olmaz; girdiler ve ölçütler farklıdır.

| Aday | Girdi / çıktı | Projeye uygun rol ve durum |
|---|---|---|
| [CADmium 1.5B / 3B / 7B / 14B](https://github.com/chandar-lab/CADmium) | Metin → sıralı CAD/JSON | Metinle boyutlu parça oluşturma için ilgili araştırma adayı. Resmi yol Conda/pythonocc-core içeriyor. Burada kurulmadı veya ölçülmedi; K ile yerel üstünlük iddiası yok. |
| [CAD-Recode v1.5](https://github.com/filaPro/cad-recode) | Nokta bulutu → CadQuery; Qwen2-1.5B tabanı | Taranmış parçanın tersine mühendisliği için daha uygun girdi türü. Serbest metinden İHA tasarımının yerine geçmez; kurulmadı. |
| [Text2CAD](https://sadilkhan.github.io/text2cad-project/) | Metin → parametrik işlem dizisi | Küçük, araştırma odaklı ayrı bir temsil ve dönüştürme hattı. Burada kurulmadı; mevcut CadQuery hattına doğrudan model değişimi değildir. |
| [CAD-Coder, Guan ve arkadaşları](https://github.com/gudo7208/CAD-Coder) | Metin → CadQuery | Metinle CAD için daha doğrudan aday; ayrı model ve sürüm uyarlaması gerekir. Burada denenmedi. Aynı adı taşıyan görsel modellerle karıştırılmamalı. |
| [Pointer-CAD v2](https://github.com/Snitro/Pointer-CAD-v2) | Boyut planlama → parametrik yapım | Ölçü doğruluğunu doğrudan ele alan yeni araştırma. İncelenen resmi depoda hâlâ “Code coming soon”; kurulu veya kullanılabilir diye gösterilmiyor. [Makale](https://arxiv.org/abs/2606.29301). |

## Kullanım kararı

K-1B hızlı bir şekil taslağı için kullanılabilir; ölçüleri doğru sayılmadan kontrol edilmelidir. Zero-to-CAD'in bu Q6 bağlantısı deneysel durumda bırakıldı. İki yardımcı model de otomatik mühendislik kabulü için etkinleştirilmedi.

Bugün kullanılabilir ana yol: görev → kaynaklı/etiketli parametreler → CadQuery/FreeCAD/OpenVSP → gerçek analiz → geometri ve fizik kontrolleri → rapor. Yeni bir modelin daha iyi olduğunu söylemek için aynı ölçülü görevleri ve aynı kabul ölçütlerini kullanarak ayrıca ölçmek gerekir.
