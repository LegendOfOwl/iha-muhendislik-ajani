# OpenAeroStruct'tan ajan çalışma yöntemine

19 Ekim 2026 · Kaynak sürümü `09336bd12e5816cd212ad5b83d35c560599ea803`

OpenAeroStruct, VLM ile uzaysal kiriş modelini OpenMDAO içinde bağlar. Kanat ön tasarımında şekil, yük ve esneme ilişkisini incelemek için kullanılabilir. Hacim CFD'si, ayrılmalı akış veya ayrıntılı üç boyutlu yapı çözümü sayılmaz. [Resmî kapsam](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/).

## Ajan konusunda bulunan kaynak

Michigan Üniversitesi IDEAS/MDO laboratuvarlarının [OpenAeroStruct LLM Agent](https://github.com/ideas-um/openaerostruct-llm-agent/blob/09336bd12e5816cd212ad5b83d35c560599ea803/README.md) deposu doğrudan ilgili. Yönlendirme, şablondan kod üretimi, değişiklik denetimi ve başarısızlık teşhisi aşamaları var. Yerelde 11 ilgili dosya sabit commit ve SHA256 ile saklandı; bu kaynağın ayrı LLM sistemi çalıştırılmadı, yayımlanan başarı sonuçları yeniden üretilmedi.

## Ajan talimatlarına alınan yaklaşım

- [Router](https://github.com/ideas-um/openaerostruct-llm-agent/blob/09336bd12e5816cd212ad5b83d35c560599ea803/src/llm/router.md): sabit geometri analizi, polar taraması, tek/çok koşullu optimizasyon ve aeroelastik problemi ayır. Şablondaki varsayılan tasarım değişkenini kullanıcının isteği sayma; eksik fiziksel veriyi uydurma.
- [Coder](https://github.com/ideas-um/openaerostruct-llm-agent/blob/09336bd12e5816cd212ad5b83d35c560599ea803/src/llm/coder.md): kurulu sürümde çalışan kaynaktan başla. Değişen fiziksel sayı ve formülü kaynağına bağla; kullanıcı bir sınırı değiştirdi diye bütün modeli yeniden varsayma.
- [Auditor](https://github.com/ideas-um/openaerostruct-llm-agent/blob/09336bd12e5816cd212ad5b83d35c560599ea803/src/llm/auditor.md): geometriyi, ağ ayarını, fiziksel gereksinimi ve sayısal ölçeklemeyi ayır. Amaç/değişken/kısıt değişikliklerini tek tek denetle. Kullanıcı sert sınırı başarı elde etmek için kaldırılmaz.
- [Relakser](https://github.com/ideas-um/openaerostruct-llm-agent/blob/09336bd12e5816cd212ad5b83d35c560599ea803/src/llm/relaxer.md): teşhisi gerçek son kısıt, değişken, sınır ve yakınsama verisine dayandır. Olası sebebi gözlenmiş ihlal gibi sunma.

Bu aşamalar yerel AGENTS.md'ye uyarlandı. Kaynak uygulamanın bütün onay kuralları kopyalanmadı: kullanıcının verdiği doğrulama kapsamında rutin ağ inceltme ve sayısal yakınsama araştırması gerekçesiyle kaydedilerek yürütülür. Eksik kritik girdi yalnız bağlı işi bekletir. Talimatlar fiziksel doğruluk veya hiç adım atlamama garantisi değildir; kabul kanıtı ayrıca gerekir.

## Birebir kopyalamanın sorunları

Kaynakta coder trim için alfa eklenmesine izin verirken router/auditor daha dar değişken yetkisi kullanıyor. Burada trim serbestliği ile şekil tasarım değişkeni ayrı kaydedilecek. Ayrıca [bağımlılıklar](https://github.com/ideas-um/openaerostruct-llm-agent/blob/09336bd12e5816cd212ad5b83d35c560599ea803/pyproject.toml), resmî paket yerine özel auto-plot-save çatalına işaret ediyor; Gemini/Ollama ve ayrı arayüz bekliyor. Bunları mevcut Codex'e bağlanmış veya test edilmiş saymıyoruz. Kaynak ajan bir araştırma prototipidir; tüm uçak tasarımı ve halüsinasyonsuzluk kanıtı değildir.

## Gerçek yerel çalışma

Resmî OpenAeroStruct 2.12.0 ve OpenMDAO 3.45.1 proje ortamına kuruldu; yaklaşık 17MB paket, mevcut NumPy/SciPy değişmedi. Bağımlılık kontrolü geçti. [İki resmî örnek](openaerostruct_examples.json) gerçekten optimize edildi. Aerodinamik örnekte CL=0,5 hedefi sağlandı. Tüp-kiriş örneğinde normalize L=W artığı 1.63e-11; hasar kısıtı 1.01e-10, belirlenmiş toleransla geçti. Alfa/kalınlık için yakıt ve denge toplam türevlerinin dört grubunda en büyük norm farkı %0.0319; eşik %0,5 idi. Bu dört grup tüm türevleri kapsamaz.

Bunlar kaba CRM eğitim örnekleridir. OAS ağ duyarlılığı, bağımsız fiziksel referans ve gerçek kanadın malzeme/yük kabulü henüz yapılmadı. [Resmî hata ayıklama rehberi](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/user_reference/debugging_tips.html), optimizasyon sonunda kısıtların ve geometrinin yeniden kontrolünü destekler.

## OAS'a özgü kontroller

Tam/yarım açıklık ve yük çarpanı, kontrol noktalarının uçtan köke sırası, chord_cp ölçeği, re biriminin 1/m olması; CL0/CD0 ekleri ve viskoz korelasyon kapsamı kaydedilecek. Örnek yakıt/malzeme verileri gerçek İHA'ya taşınmayacak. [Değişken sözlüğü](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/user_reference/mesh_surface_dict.html). [OpenVSP ağ örneği](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html) Python API ister; burada bu bağlama kurulmadı.

Sonraki ölçülebilir adım gerçek kanadın malzeme, kesit, yük ve görev verilerini kaynaklarıyla tanımlamak. Ayrı bir LLM sistemi kurmak bu verilerin yerini tutmaz.
