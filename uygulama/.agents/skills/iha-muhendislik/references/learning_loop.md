# Kanıtlı talimat iyileştirmesi — sürüm 1

Bu protokol araç ve süreç hatalarının tekrarını azaltmayı amaçlar. Model ağırlıklarını eğitmez. Talimatın yüklenmesi, kod kontrollerinin geçmesi ve bağımsız mühendislik yeterliliği ayrı iddialardır.

## Bir hata görüldüğünde

1. Önce özgün config, kaynak girdi, yazılım sürümü, ham log, alan ve seçilmiş alan iterasyonunu koru. Dondurulmuş denemeyi değiştirme. Sonuç, geometri ve koşul hash'lerini eşleştir; alan yoksa alan niceliği üretme.
2. Gözlemi yorumsuz yaz: beklenen sözleşme, gerçekleşen olay, kanıt yolu/SHA256. `confirmed_error`, `prevented_failure`, `hypothesis` ve `disproven_diagnosis` ayrımını kullan. Muhtemel ajan davranışını çıkarım diye etiketle; başarısız Cp kıyasını tek başına prompt hatası veya bir ayarın nedensel kanıtı sayma.
3. Bir düzeltme öner: tetikleyici, araç/sürüm/kapsam, yapılacak işlem, başarısızsa duracak bağlı adım. Fiziksel girdiyi, deney noktasını, toleransı veya seçilmiş aday/ağ rolünü sonuç tutturmak için değiştirme. Mevcut kurala link ver; aynı kuralı farklı cümlelerle çoğaltma.
4. Bir değişiklikle sınanabilen en küçük karşı örneği çalıştır. Dış dosya biçimi için sıra dışı fakat geçerli kayıt ve bozuk kayıt; sayısal kabul için eşik yanı, eksik kapı ve yanlış alan/geçmiş eşlemesi kullan. Sadece metinde kuralın bulunduğunu test etme. Çözücü politikası değişirse kurulu sürümle küçük native deneme yap; geçmişte yapılan denemeyi yeni çalışmış gibi sayma.
5. Gerçek vakada başarısızlık düzeltildiyse yalnız o hata sınıfına dar önleme kuralı ekle. Nedeni henüz bilinmeyen fiziksel uyuşmazlık `hypothesis` olarak kalsın. Çürüyen teşhisin eski kaydı ve onu çürüten kanıt birlikte tutulsun. Kod kontrolü geçen kuralın LLM tarafından uygulandığı ayrıca sınanmamış olabilir.
6. Aynı görev yetkisi içinde bir sonraki denemede ilgili operasyonel dersleri uygula; başarısızlıktan sonra bu döngüyü tekrar et. Yeni bir fiziksel hipotez için önce değişken, sabitler, sayısal bütçe, durma koşulu ve geçme ölçütünü kaydet. İlerleme yoksa aynı denemeyi gerekçesiz tekrarlama; teşhisi ve sıradaki ayırt edici testi bırak.

## İki ayrı kayıt

- Analizciye uygun kısa bellek: `operational_lessons.json`. Beklenen Cp/CL/CD, şok konumu, deney cevabı ve o değerlere götüren rapor yollarını içermez. Bu dosya yalnız işlemsel düzeltmeleri taşır.
- Değerlendirici defteri: `outputs/data/agent_learning/reviewer_ledger_v1.json`. Olay, kanıt SHA256, davranış çıkarımı, karşı örnek, sınanmamış hipotez, reddedilmiş teşhis ve revizyon geçmişi burada tutulur. Tahmin dondurulduktan sonra değerlendirmede kullanılır; normal proje incelemesiyle kör sınama karıştırılmaz.

Normal GUI görevi AGENTS.md ve PROJECT_STATE.md'nin tümünü okur; bunlar geçmiş deney sonuçlarını içerir. Bu yol üzerinden açılmış oturumu kör analiz diye sunma. Kör değerlendirmede ayrı geçmişe yalnız yetkili geometri/koşul/sayısal sözleşme ve hedef içermeyen ders paketi ver; erişim veya cevap sızıntısı olduysa bildir. Paylaşılan dosya sistemi ve bu talimat güvenlik yalıtımı değildir.

## Sürüm ve kabul

Görev başında uygulanan ders kimliklerini, talimat sürümünü ve ilgili dosyaların SHA256 anlık kaydını tut. GUI başlatıcısı bunu `agent_instruction_snapshot` alanına yazar. Mevcut sohbet geçmişi yeni başlatılmış bağımsız oturum değildir.

Her sürümde eski başarısız olaylar ve yeni karşı örnekler tekrar kontrol edilir. Yeni geometri/koşullarda LLM davranışını ölçmek için çalışma öncesinde kapsam, süre/aday bütçesi ve kabul tablosu belirle; önceki sürümle aynı araç/girdi/bütçede karşılaştır. Örnek sayısı, tüm başarısızlıklar, tekrarlar, maliyet ve cevap sızıntısı raporlansın. Geliştirmede kullanılan vaka artık görülmemiş test sayılmaz; sonraki sürüm için yeni vaka ayır. Tek başarı genel doğruluk oranı veya uzmanlık değildir.

İleri yeterlilik tablosunda en az kaynak geometri/karmaşık CAD geri ölçümü, içe aktarma/topoloji, çözücü uygunluğu, bölgesel ağ/alan kontrolleri, iteratif yakınsama, sistematik ağ/uzak alan, bağımsız kuvvet integrasyonu, deney kıyası ve belirsizlik/sınırlama raporu ayrı izlenir. Vakaya uymayan madde gerekçeli uygulanmıyor olabilir; eksik zorunlu madde kabulü kapatır. 2B, 3B, düşük mertebe aeroelastik ve detaylı yapı ayrı yetkinliklerdir. Gözlenmiş mühendislik başarısı olmadan `uzman` statüsü verilmez.

Global Codex hafızası bu defterin kopyası değildir. Kullanıcının hafıza yazma yetkisi içinde kısa, kapsamı belirli yönlendirme notu ekle; hipotezi gerçek diye, benchmark cevabını analizci dersi diye kaydetme. Buradaki döngü yetkili görevler çalışırken uygulanır; arka planda sınırsız çalışma başlatmaz.
