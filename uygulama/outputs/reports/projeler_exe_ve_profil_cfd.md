# Proje merkezli Mühendislik Merkezi

19 Ekim 2026 · [EXE'yi aç](../Muhendislik-Merkezi.exe)

Sol taraftan projeyi seç; görev, CAD, alanlar ve raporlar o proje içinde kalır. Yeni proje oluşturabilir, dosya ekleyebilir, aktif model seçebilir, FreeCAD/OpenVSP tercihini projeye kaydedebilirsin. Görev taslağı proje değiştirince korunur. İlk gerçek İHA verileri yerinde kaldı; eski araç örnekleri ayrı projeye bağlandı.

## Kullanım ve EXE

Proje özeti içinde CAD programını seç. Uyumlu aktif dosya varsa onunla açılır; yoksa program boş açılır. Proje dosyalarından model ekle ve aktif seç. Görev ve kısıtlar bölümünde bilinen verileri gir. Yalnız kaydet isteği dosyaya yazar; bu sohbetten kaydedilen göreve devam edilebilir. Kaydet ve ajanla başlat ayrı Codex terminal penceresini seçili proje/görevle açar; bu sohbete otomatik mesaj göndermez.

EXE 7.680 baytlık Windows başlatıcısıdır; mevcut Python ve mühendislik araçlarını kullanır. Bütün proje klasörleri yanında kalmalı; yalnız EXE'yi taşımak yetmez. Aynı dosya/komut işlevleri korunur, görünür CMD penceresi gerekmez. CMD aynı yeni arayüzün yedeğidir.

## Denetimler

[Yeni proje/aktif CAD/dosya/taslak/yol ve görev aktarımı](project_interface_checks.json) 15/15 geçti; ayrı çıktı klasöründe gerçek CAD üretimi ve özgün CAD'in korunması dahil. Temel kontroller 26/26, önceki görev akışı 17/17. EXE yolu, arayüzün açılıp çıkması, dört sekmenin çizimi ve gezinme düğmeleri denetlendi. Testte yeni LLM oturumu başlatılmadı.

## Yeni geometride ağ ve CFD

Profil ağı ve CFD doğrulaması projesinde kaynak DAT → yeni Gmsh akış ağı → native SU2 Euler → kuvvet/alan → bağımsız XFOIL kontrolü baştan çalıştı. Orta/ince ağ 13.914/41.768 hücre; ince CL=0.491715; CL ağ farkı %2.04; XFOIL inviscid farkı %3.66. Önceden belirlenmiş bu koşula ait sayısal ön kabul geçti. İlk başarısız kuvvet kararlılığı çalışmaları saklandı; ince hedef −10 ile tekrar çözüldü. [Ağ/alan/kuvvet raporu](../projects/proje-0314dcd012/reports/profile_cfd.html).

Bu 2D sürtünmesiz profil sonucudur. Negatif sayısal CD gerçek sürükleme/itki değildir. Sınır tabakası, geçiş, stall, uzak alan duyarlılığı ve 3D uçak CFD kabulü açık kalır. Önceki RANS %22,84 sürükleme ağ farkı ve karmaşık VLM yüzey CDi kabulü kapanmadı.

## OpenAeroStruct ve ajan talimatları

Üniversite kaynaklı OpenAeroStruct LLM Agent'ın isteği yapılandırma, uygun şablon, değişiklik denetimi ve başarısızlık teşhisi yaklaşımı incelendi; yerel kurallara uyarlandı. Kaynak projenin ayrı LLM sistemi kurulmadı. Resmî OpenAeroStruct/OpenMDAO kuruldu; iki örnek, kısıtlar ve dört türev grubu gerçek çalışmada geçti. Aeroelastik araç testidir; yeni İHA tasarımı veya CFD değildir. [İnceleme, kaynaklar ve yerel test](openaerostruct_ajan_yaklasimi.html).

## Açık kalanlar

Fusion OAuth tamam; bu sohbetin araç listesinde motor yok, lisans/parametrik parça/STEP döngüsü test edilmedi. Keyfi içe aktarılmış CAD'i tek tıkla ağlayıp doğrulanmış 3D CFD yapan genel servis henüz yok. Hazır olmayan projenin düğmesi eski örneği sessizce çalıştırmaz. Araştırma ve aday taraması yeni görev için kapsam/bütçe tanımlanarak yürütülür. Gerçek İHA'nın sekiz kavramsal adımı güncel veri bekliyor; ANSYS sona bırakıldı.

Ölçülebilir sonraki adım gerçek görevin koşullarını, bileşen kütlelerini ve kanat malzeme/kesit/yük verisini kaydedip eksik girdi tablosunu kapatmak.
