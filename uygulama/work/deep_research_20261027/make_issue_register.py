"""Join the researched gaps without confusing missing evidence with known bugs."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent


def main():
    rows = []
    def add(priority, domain, kind, title, observed, impact, next_test, closure, mapped, sources, depends=()):
        rows.append(dict(id='U%02d' % (len(rows)+1), rank=len(rows)+1, priority=priority, domain=domain,
            kind=kind, title=title, observed=observed, impact=impact, next_test=next_test,
            closure=closure, specialist_issue_ids=mapped, source_ids=sources,
            depends_on=list(depends), status='open', proposal_executed=False))

    add('P0','CFD','acceptance_failed','İnce ağın sayısal yakınsaması ve gerçek iç artık ölçümü',
        'Düz plaka ailesinde ince rolün yoğunluk kapısı açık; RAE ve TMRsharp M6 da genel kabulü geçmedi. v17 üç tanı kolunda tüm200 flow/SA çözümü40 tavanda. LinSolRes, bağımsız b−Aδ normu değil.',
        'İterasyon hatası sınırlanmadan ağ ve deney farkının ne kadarının fiziksel olduğu ayrılamaz.',
        'Assembled FGMRES çağrısında gerçek A,b,x0,δ,norm0 kimliğini kaydet; scratch vektörle mutlak/bağıl/bileşen gerçek artığını pasif ölç. Analitik matris kontrolleri ve değişmeyen kaynak32 yeniden üretiminden sonra aynı ilk-adım A,b ile kısa32/256 kıyası yap.',
        'Ölçüm doğruluğu ve çözümü değiştirmediği ayrı geçmeli; sonra önceden seçilmiş fine ve bütün zorunlu dış kapılar aynı vaka/ailede geçmeli. Yeni ölçüm veya tek bileşen iyileşmesi fizik kabulü değildir.',
        ['N01','N02','VM01'],['NS01','NS04','NS06'])
    add('P0','CFD','resolution_unverified','Konuma göre BL/LE/TE/iz/uç çözünürlüğü ve bütün Cf eğrisi',
        'y+ bazı kollarda geçti; RAE normal blok değişimi kuvvetleri yaklaşık%4 etkiledi. Düz plaka kabul penceresi Cf normu ile bütün447 noktanın normu farklı. M6 uç/iz ve katman geçişi birlikte kapanmadı.',
        'Toplam hücre veya ilk y+ iyi olsa da gerekli akış gradyanı çözülmemiş olabilir.',
        'Gerçek normal/teğetsel aralık, son segment büyümesi, toplam katman ve hız/μt profillerini çıkar; yalnız bir bölgesel dağılım/geçişi değiştiren eş kontrol kur. LE dahil bütün kaynak noktalarını koru.',
        'Yakınsamış eş çözümlerde ön kayıtlı profil/kuvvet duyarlılığı ve bölgesel mesh kapıları birlikte geçmeli; kötü noktalar puandan çıkarılmamalı.',
        ['VM02','N05'],['NS03','VS01'],['U01'])
    add('P0','Geometri','equivalence_unverified','Kaynak CAD, mesh, VLM ve OAS temsil eşdeğerliği',
        'Aynı parametreler farklı interpolasyonlar üretiyor. TMR M6 sınır-yüzeyi örneklerinin max uzaklığı yaklaşık9,78e−4 kök veter; bu tam Hausdorff değil. Önceki solid mesafe denetimi superseded.',
        'Farklı geometriyi tek aday veya tek sistematik ağ ailesi saymak karşılaştırmayı bozabilir.',
        'Birim/eksen/TE/LE/twist eksenini ve hangi yüzeyin solid/camber/deforme yüzey olduğunu tanımla; iki yönlü boundary mesafesi, normal ve ara istasyon kontrolleriyle ortak aday kimliğine bağla.',
        'İlan edilmiş hata bütçesi bütün zorunlu örneklerde geçmeli; kasıtlı ölçek/twist sapması reddedilmeli. Yeni geometri yeni temsil sürümü olmalı.',
        ['VM03','CA02'],['CS01','CS02','CS03','VS02'])
    add('P0','CFD','acceptance_failed','Üç yakınsamış sistematik ağ ve geçerli GCI',
        'Birden fazla gerçek üç-ağ ailesi var; fakat gerekli iteratif/asimptotik şartlar birlikte sağlanmadı. Özellikle TMRsharp M6 üç ağı zaten üretildi, eksik olan üç başarılı çözüm. GCI null.',
        'Sadece üç sonuç veya küçük orta–ince fark güvenilir ayrıklaştırma hata bandı vermez.',
        'Aynı geometri/dış sınır/fizikte yönsel inceltme oranlarını kaydet; her seviyeyi aynı QoI ve iterasyon kapılarıyla değerlendir. LE/şok tekilliklerini ayrı ele al.',
        'Kayıtlı ağ ailesi için iteratif belirsizlik sınırlı ve gözlenen mertebe/asimptotik davranış uygun olmalı; uygunsuz nicelikte GCI açıklamalı null kalmalı.',
        ['VM04'],['VS04','PS01'],['U01','U02','U03'])
    add('P0','CFD','sensitivity_missing','Uzak alan ve sınır etkisinin bağımsız ölçülmesi',
        'RAE400c ağı hazırlanmış fakat kabul edilmiş çözümü yok; TMR M6 kaynak100c olması tek başına duyarlılık deneyi değil. Eski farklı dış alanlar salt mesh yakınsaması sayılmadı.',
        'Dış sınır etkisi ağ ve model hatasıyla karışabilir.',
        'Kaynak gövde ve yakın ağı koruyup yalnız dış bölgeyi değiştiren eş çift çalıştır; aynı matched alan/geçmiş ve kuvvet pencerelerini kullan.',
        'İki çözüm de kendi sayısal kapısını geçmeli ve ön kayıtlı QoI sınır duyarlılığı kapanmalı; alanı olmayan hazır ağın sonuçları null kalmalı.',
        ['VM05'],['VS04','PS01'],['U01','U03'])
    add('P0','Doğrulama','acceptance_failed','RAE2822/M6 deney kıyası ve fiziksel koşul eşlemesi',
        'RAE v2 fine CpRMSE≈0,067>0,03; v3 genel kabulü false. Daha yeni TMRsharp M6 kaynak ailesinin hiçbir iteratif kapısı geçmedi. Eski blunt M6 iyileşmeleri ayrı vaka. Model/BC/ölçek ve Sutherland özdeşliği her kodda tam kanıtlanmış değil.',
        'Denklemlerin çözülmesi, deneydeki geometri/akış/modelin doğru temsilini kendiliğinden göstermez.',
        'Sharp/blunt, root/MAC Reynolds, nominal/düzeltilmiş koşul, trip, SA varyantı, viskozite yasası ve Cp işaretini kaynak matrisiyle eşleştir. Sonra bütün deney noktaları/grupları ve bağımsız kuvvet zinciriyle değerlendir.',
        'Vakaya önceden bağlanmış sayısal, geometri, deney ve kapsam kapıları birlikte geçmeli. Koşul/puan/eşik sonuç tutturmak için değiştirilmemeli.',
        ['VM06'],['VS02','VS05','NS03','PS01'],['U01','U02','U03','U04','U05'])
    add('P0','Gerçek İHA','input_missing','Gerçek görev, kütle ve kabul girdileri',
        'Kalıcı gerçek İHA mission kaydında7 girdi null; altı bileşen kütlesi bilinmiyor;8 kavramsal adım bekliyor. Bunlar yazılım hatası değildir.',
        'Gerçek uçağın güç/enerji/CG/trim veya uygunluğu hesaplanamaz. Bu eksik benchmark araştırmasını engellemez.',
        'Kullanıcı gereksinimlerini ve kaynaklı bileşen verilerini değer/aralık, SI birim, kaynak ve geçerlilikle kaydet; çelişki/eksik için kabul matrisi kur.',
        'Bağlı hesaplar için kritik girdiler onaylı olmalı; bilinmeyenler sıfır olmamalı. Her aşama kendi kanıtıyla kapanmalı.',
        ['CA01'],['CS09','PS02'])
    add('P1','CFD','capability_unproven','Keyfi kullanıcı CAD’inden kaliteli hacim ağı',
        'Kaynak benchmark ve tanımlı profil/kanat aileleri için betikler var; keyfi yeni parçaya genel RANS ağı ve bütün bölgesel kontroller doğrulanmadı.',
        'Hazır örneği çalıştırmak yeni kullanıcı geometrisine ait sonuç üretmez.',
        'Önce sınırlı bir yeni geometri ailesi seç; watertight CAD/duvar/sınır etiketleri, bölgesel mesh sözleşmesi, kalite retleri ve aynı geometriyle üç seviye üretimini sınayacak vaka kur.',
        'Yeni geometri kendi kimliğiyle CAD→mesh→solver→kabul zincirini geçmeli; destek dışı geometri doğru biçimde reddedilmeli.',
        ['CA04'],['PS03','CS03','VS03'],['U02','U03','U04'])
    add('P1','Gerçek İHA','capability_unproven','Bütün uçak performansı, trim, kararlılık ve3B kapsam',
        '2B profil, ayrı kanat VLM/OAS ve M6 testleri var; gerçek gövde/kuyruk/itki etkileşimi ile sürekli güç, enerji, CG ve trim birlikte doğrulanmadı.',
        'Bir profil/kanat sonucu bütün uçağın görev gereksinimlerini kapatamaz.',
        'Aynı gerçek adayda bileşen kütleleri, güç/enerji modeli, CG/trim ve uygun aero/yapı yöntemini bağla; dahil edilmeyen parçaları ve model rejimini kaydet.',
        'Gereksinimlerin her biri sağlandı/sağlanmadı/henüz değerlendirilemedi ve kanıt taşımalı; bileşen sonucu uçak sonucu diye aktarılmamalı.',
        ['CA01','CA07'],['CS09','CS13','PS02'],['U07','U03'])
    add('P1','Ajan','capability_unproven','Yeni projede araştırmadan sıralamaya uçtan uca ajan',
        'full_generic_pipeline_verified=false. GUI/EXE ve görev kaydı çalışıyor; yeni ayrı CLI oturumu açılması, yeni projede bütün aşamaların özerk tamamlandığını kanıtlamıyor.',
        'Kullanıcının istediği tek görevde araştırma→CAD→analiz→CFD→sıralama→rapor zinciri henüz gösterilmedi.',
        'Görülmemiş sınırlı bir proje, aday bütçesi ve kabul sözleşmesiyle gerçekten yeni oturum başlat; eksik veri, araç hatası ve destek dışı CAD dallarını da izle.',
        'Aynı project/candidate/geometry/condition kimliği bütün aşamalarda eşleşmeli; final sıra yalnız bütün gerekli kapıları geçen adaylarla ve taranmayan alan açıklamasıyla oluşmalı.',
        ['CA04'],['CS10','CS12','CS09'],['U03','U08','U11'])
    add('P1','Ajan','behaviour_unvalidated','Talimat/hafıza iyileşmesinin görülmemiş görevlerde ölçülmesi',
        'Talimat sürümleri, yanlış-kabul korumaları ve kod karşı örnekleri var; aynı bütçe/araçlarla bağımsız önce/sonra görülmemiş mühendislik değerlendirmesi yok.',
        'Kod kontrolü veya aynı benchmarkın tekrar düzeltilmesi uzman ajan davranışı kanıtı değildir.',
        'Yeni geometri/koşulları geliştirme vakalarından ayır; sabit araç/model/bütçede iki talimat sürümünü karşılaştır. Bağımsız sayısal/ölçü hakemi, tüm başarısızlıklar ve kaynak-cevap sızıntısı kaydı olsun.',
        'Görev düzeyinde doğruluk, yanlış kabul, maliyet ve tekrarlar raporlanmalı; ortak diskteki rol ayrımı güvenli körlük diye sunulmamalı. Tek başarı genel oran değildir.',
        ['CA03'],['CS10','CS11','CS12'])
    add('P1','Karar','uncertainty_missing','Belirsizlik bütçesi ve savunulabilir aday sıralaması',
        'Kanıt/koşul eşleştirmesi ve başarısız CFD’de kazananı engelleme çalışıyor. Kayıtlı adaylarda final_winner=null; sayısal/model/girdi belirsizliğiyle birleşik gerçek tasarım sıralaması yok.',
        'İki küçük fark belirsizlik içindeyse tek kazananı savunmak mümkün olmayabilir.',
        'Önce tek QoI için girdi, geometri, iterasyon, mesh, BC/model ve deney belirsizliklerini ayrı kur; bağımlılıkları belirt. Sonra aynı sert kısıtlarda duyarlılık/robustlukla adayları kıyasla.',
        'Belirsizlik kullanım amacına göre yeterli olmalı; eksik model hatası sıfır sayılmamalı. Sıralama ayrışmıyorsa sonuç eşdeğer/koşullu kalmalı.',
        [],['PS01','PS02','PS03'],['U04','U05','U06','U07'])
    add('P1','Aerodinamik','acceptance_failed','Karmaşık kanatta VLM sürükleme panel kabulü',
        'Yüzey CDi panel farkı yaklaşık%17–18,46 ile kayıtlı kapı açık. İz CDiw daha kararlı; iki nicelik farklı kestirimlerdir ve uygun sütunu seçerek eski kabul kapatılamaz.',
        'CL’nin daha kararlı olması toplam sürükleme ve aday L/D sıralamasını doğrulamaz.',
        'Sref/bref/cref, analiz kümesi ve aynı kanat temsiliyle yüzey/iz kuvvetlerini ayrı izleyen panel/iz aileleri kur; kaynak tanımı ve bağımsız uygun referansı kaydet.',
        'Başlangıçta seçilmiş nicelikler kendi kapılarını geçmeli; sürtünme/stall/ayrılma gibi model dışı fizik için VLM kabulü kullanılmamalı.',
        ['CA05'],['CS04','CS05'],['U03'])
    add('P1','CAD','capability_unproven','Yeni karmaşık CAD ailelerinde ölçü ve topoloji güvencesi',
        'Tanımlı kanat/nervür ve3 NIST kaynak parçada ölçülü işlemler geçti. Bunlar her yeni loft/sweep/shell/çoklu delik veya kaynak çizimden yeniden kurma görevinin kabulü değildir.',
        'Çalışan program ve geçerli katı, tasarım niyetinin veya bütün ölçülerin doğru olduğunu göstermeyebilir.',
        'Karmaşıklık basamaklı yeni kaynak parçalarda feature/parametre değişimi ve STEP geri okuması; eksen/merkez/bağlantı/topoloji/kalınlık kontrolleriyle negatif örnekler çalıştır.',
        'Göreve özgü bütün ölçü/topoloji kuralları ve düzenleme sonrası aynı kurallar geçmeli. Hacim/bbox/probe tek başına tam şekil kanıtı olmamalı.',
        ['CA06'],['CS03','CS06'],['U03'])
    add('P1','CAD','capability_unproven','Ölçülü teknik resim, montaj ve üretime aktarım kapsamı',
        'Kaynak PDF/CAD işlemleri ve bazı dışa aktarımlar var; keyfi montajda bağlantılar, çakışma, tam ölçü zinciri ve üretim toleranslarıyla genel teknik resim zinciri gösterilmedi.',
        'Güzel3B görüntü imalat veya montaj uygunluğu yerine geçmez.',
        'Bir gerçek montaj ailesinde parça/eklem/çakışma kontrolleri ve gerekli ölçüleri taşıyan resim üret; CAD parametre değişince resmin güncellendiğini geri ölç.',
        'Önceden tanımlanmış montaj/ölçü ve çıktı sözleşmesi geçmeli; resim bütün gerekli iç özellikleri ve birimleri göstermeli.',
        ['CA08'],['CS06','CS14'],['U14'])
    add('P1','Yapı','capability_unproven','Gerçek kanada özel FEM ve aeroelastik optimizasyon',
        'CAD→Gmsh→CalculiX örneği ve iki OAS kaynak optimizasyonu/türev kontrolü geçti. Gerçek İHA malzeme, yük, bağlantı/mesh, kompozit ve aeroelastik tasarımı doğrulanmadı.',
        'Kaynak CRM malzemesi/yakıtı/yükleri gerçek kanada aktarılamaz; optimizatör başarı bayrağı dayanım kanıtı değildir.',
        'Göreve özgü yük/malzeme/sınır koşulu ve tasarım değişkenlerini kur; boyutlu denge, izinli sınırlar, bağlı yakınsama, mesh ve türev kontrolleriyle uygula.',
        'Gerçek modelin bütün sert kısıtları ve bağımsız fizik kontrolleri geçmeli; VLM+kiriş sonucu detaylı yapı veya hacim CFD sayılmamalı.',
        ['CA07'],['CS08','CS09','CS13'],['U07','U03'])
    add('P1','CFD','measurement_missing','Güncel iç sistemle eşleşen artık konum haritası',
        '%99,979 kapsam, yeni implicit alanın yeniden hesaplanan artığı değil aynı eski explicit-aşama RHS’sinin üyelik kesişimi. Anlamı düzeltildi; güncel b ve gerçek rL haritası henüz yok.',
        'Eski kapsamanın artması bugünkü düzeltme yönünün doğru olduğunu göstermez.',
        'U01 çağrısının aynı b ve b−Aδ vektörlerini bütün sahip olunan düğümlerle çıkar; native norm yeniden toplamını doğrula ve flow/SA bölgelerini ayrı raporla.',
        'Durum/iterasyon/normalizasyon/düğüm eşleşmesi ve yeniden toplam uyuşmalı; konum haritası nedensel hata veya mesh hata bandı diye adlandırılmamalı.',
        ['N03'],['NS01','NS05'],['U01'])
    add('P1','Maliyet','measurement_limit','Doygun Krylov sayımı ve tek çift süre ölçüsü',
        'Üç v17kolunda16000 zaten200×(40+40) tavanıdır. Eşit sayım uzun çizgilerin eşit aritmetik maliyetini göstermez; gerçek süre74,125→95,109s tek gözlemdir.',
        'Bir yöntemin gerçek doğruluk/maliyet kazancı yalnız bu vekilden çıkarılamaz.',
        'Yeni sözleşmede flow/SA ayrı, A×v ve preconditioner build/apply sayaçları, gerçek süre ve RAM ile gerçek hata azalımını birlikte izle.',
        'Eski kapı/karar korunmalı; yeni ölçüt native öncesi yazılmalı. Tek çalıştırma çiftinden evrensel hız iddiası çıkarılmamalı.',
        ['N04'],['NS02','NS06'],['U01'])
    add('P1','CFD','untested_hypothesis','Duvar mesafesi hesabının bağımsız denetimi',
        'Yerelde yanlış wall-distance kanıtı yok. NASA2018M6 çalışması anizotropik ağda böyle bir hata sınıfını göstermiş; bu yeni düşük maliyetli denetim adayı.',
        'SA kaynakları için kullanılan geometrik mesafe yanlışsa mesh/y+ görseli sorunu gizleyebilir.',
        'Önce gerçek wall marker ve source kod yolunu incele. LE/TE/uç/kök/aft noktalarında native mesafeyi bağımsız global nokta–segment/üçgen/CAD-boundary hesabıyla kıyasla; uygun düz plaka yerlerinde analitik mesafeyi kullan.',
        'Geometriye bağlı bağımsız mesafe uyuşuyorsa bu hipotezi kapat. Sapma varsa yerini/etkisini kaydet ve yalnız o hesabı değişen ayrı kontrollü test tasarla; yerel kök neden henüz yok.',
        ['VM08'],['VS03'],['U03'])
    add('P2','CFD','prototype_only','Hessian’dan tam anizotropik/adjoint ağ döngüsüne geçiş',
        'Yerel türev/öncelik prototipinde maskeli ve yönü kararsız bölgeler var; üretim remesher, adjoint veya CL/CD hata bandı değil.',
        'Bir renk haritası önerilen metrikte geçerli yeni ağ ve daha doğru QoI üretildiğini göstermez.',
        'Analitik metrikte CAD sınır ve eleman-metrik uyumunu sınayan küçük2B solve→metric→remesh→transfer→solve döngüsü kur; korunumluluk ve pozitiflik ölç.',
        'Bütün döngü ve sabit ağ kıyası doğrulanmalı; maskeler saklanmalı. Adjointin denklemi ve türevleri ayrı kontrol edilmeli; yeni makale yerel kurulum sayılmamalı.',
        ['VM09','N06'],['VS03','VS09','VS10','NS05'],['U01','U02','U03'])
    add('P2','Entegrasyon','engine_untested','Fusion motoru, hub ve lisans yetkisi',
        '18EkimOAuth doğrulandı; motorun gerçek oturumu, yetki/hub, ölçülü model ve STEP geri ölçümü yapılmadı. Beta erişimi öğrenci masaüstü lisansından çıkarılamaz.',
        'Kimlik doğrulama başarılı olsa da CAD işlemlerinin çalışacağı kanıtlanmış değil.',
        'Mevcut bağlantıyı güncel araç listesinde doğrula; sürüm/session/hub/entitlement kontrolünden sonra ölçülü basit parça ve parametre değişimi, STEP geri ölçümü yap.',
        'Gerçek motor çıktısı ve ölçü kontrolleri geçmeli. Bulut/servis erişimi koşulları ayrıca kanıtlanmalı.',
        ['CA09'],['CS14'])
    add('P2','Entegrasyon','bridge_missing','OpenVSP Python→OAS köprüsü',
        'AngelScript/native OpenVSP çalışıyor. Kurulu paket Python3.11, sayısal ortam3.12; OAS resmî VSP mesh örneğinin istediği Python API köprüsü kurulup doğrulanmadı.',
        'Ayrı üretilmiş OAS yüzeyi native VSP3 adayına otomatik bağlanmış sayılamaz.',
        'Uyumlu ayrı API ortamı veya kontrollü dosya adaptörü seç; sürüm/birim/simetri/mesh ve referans alanı geri ölçerek tek aday üzerinde doğrula.',
        'Köprü gerçek native geometriyi doğru istasyon/analiz yüzeyine taşımalı; yanlış sürüm/ölçek negatif kontrolü reddedilmeli.',
        ['CA10'],['CS01','CS02'],['U03'])
    add('P2','Model','topology_failures','Küçük CAD modellerinin geometri/topoloji güvenilirliği',
        'Cadmonkeydata32 yeni altı basit parçada4/6 geçti; kaçık/çift delik gibi redler var. Başka kullanım denemesindeki5/6 farklı protokol; genel doğruluk oranı değil.',
        'Modelin kod üretmesi veya görüntü benzerliği katı/ölçü/topoloji doğruluğunu garanti etmez.',
        'Loft/sweep/shell/çoklu boşluk gibi yeni ailelerde özgün değişmemiş çıktıyı sabit bütçe ve görev bazlı kernel/ölçü hakemiyle değerlendir.',
        'Bütün zorunlu kontroller geçmeden taslak kabul edilmemeli; insan/Codex düzeltmesi küçük model başarısı sayılmamalı. Genel oran için bağımsız temsil edici test gerekir.',
        ['CA11'],['CS06','CS15','CS16'])
    add('P2','Model','reference_runtime_unreproduced','Zero-to-CAD özgün çalışma yolunun ayrıştırılması',
        '2 milyar parametreli Zero-to-CAD modelinin yerel Q6/native köprü testleri geçerli katı üretmedi; özgünBF16/Transformers çalışma yolu yeniden üretilmedi.1m veri ölçeği,1m parametreli model demek değil.',
        'Başarısızlık kesin olarak checkpoint kalitesine veya bütün aileye yüklenemez.',
        'Özgün modelcard sürümü, sekiz görünüş, processor/template/token bütçesi ve kod temizleme semantiğini yerel köprüyle fark tablosuna bağla; kaynak bütçesi uygunsa ayrı kontrollü referans denemesi tasarla.',
        'Referans yol ile native yolun farkı gerçek çıktılarla ayrılmalı; ağır çalışma bütçeye sığmıyorsa doğrulanmadı olarak kalmalı. Tasarım kabulü ayrıca yapılmalı.',
        ['CA12'],['CS07','CS17'])
    add('P2','Ürün','portability_unproven','EXE dağıtımı ve yeni ortamda gerçek görev kullanımı',
        'EXE çalışır başlatıcı; kurulu Python/araçlar ve proje klasörleri yanında gerekir. Temiz makine solver kurulumu ve GUI’den görülmemiş uçtan uca görev doğrulanmadı.',
        'Mevcut PC’de arayüzün açılması bağımsız taşınabilir uygulama ve görev başarı kanıtı değildir.',
        'İzole kullanıcı/VM ya da temiz kopyada yollar/bağımlılık/kimlik doğrulama/eksik araç hatası ve bir yeni projenin gerçek oturumunu sınayacak kurulum kabulü yap.',
        'Gerekli bileşenler kaydedilmeli; eksik araç anlaşılır hata vermeli; başka proje girdisi kullanılmamalı ve kullanıcı çıktıyı tek projede izleyebilmeli.',
        ['CA13'],['CS10'],['U10'])
    add('P3','Entegrasyon','optional_deferred','İkinci yerel RANS çözücüsü / OpenFOAM kurulumu',
        'SU2 ve dar laminer Elmer doğrulamaları mevcut. OpenFOAM için doğrulanmış yerel kurulum/aynı3BRANSvaka tekrarı yok; TMR CFL3D/FUN3D kıyasları ayrı mevcut kanıt.',
        'Bağımsız yöntem farkı yararlı olabilir; yeni program kurmak tek başına doğruluğu artırmaz.',
        'Önce mevcut TMR referanslarıyla tam denklem/BC/model eşlemesini bitir. Sonra read-only ortam/RAM/WSL değerlendirmesi ve küçük eşdeğer vaka ile ikinci çözümü ele al.',
        'Sürüm, SA varyantı, sıkıştırılabilirlik, geometri ve koşullar eşleşmeden fark çözücü hatası sayılmamalı. WSL/servis kurulumu ve kaynak bütçesi ayrıca ele alınmalı.',
        ['CA14','VM07'],['CS19','VS06','PS04'],['U01','U06'])
    assert len(rows) == 26
    n = json.loads((BASE/'numerics.json').read_text(encoding='utf-8'))
    c = json.loads((BASE/'cad_agent.json').read_text(encoding='utf-8'))
    v = json.loads((BASE/'validation_mesh.json').read_text(encoding='utf-8'))
    required = {x['id'] for x in n['problems']} | {x['id'] for x in c['issues']} | {x['id'] for x in v['problems']}
    mapped = {x for row in rows for x in row['specialist_issue_ids']}
    assert required == mapped, (required-mapped, mapped-required)
    assert all(dep in {r['id'] for r in rows} for r in rows for dep in r['depends_on'])
    (BASE/'issue_register.json').write_text(json.dumps({'issues': rows,
        'specialist_issues_mapped': len(required), 'all_specialist_issues_mapped': True,
        'priority_basis': 'Consequences for valid engineering use, then enabling dependencies and information gain/cost; no invented numerical risk score.'},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print({'consolidated_issues': len(rows), 'specialist_issues_mapped': len(required)})


if __name__ == '__main__':
    main()
