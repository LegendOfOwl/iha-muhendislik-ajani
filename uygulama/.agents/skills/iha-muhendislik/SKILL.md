---
name: iha-muhendislik
description: "Bu İHA çalışma alanında mühendislik görevi yürüt: kaynaklı gereksinimler, parametrik CAD, aerodinamik veya yapısal analiz ve kanıtlı rapor. Genel sohbet ya da sırf görsel resim üretimi için kullanma."
---

# İHA mühendislik görevini yürüt

Proje kökü, bu SKILL.md dosyasının bulunduğu klasörden `../../..` konumudur. Önce kökteki AGENTS.md ve PROJECT_STATE.md dosyalarını oku; mühendislik kurallarının tek kaynağı AGENTS.md'dir.

## Göreve başla

`outputs/data/project/` gerçek proje girdilerini içerir. `outputs/data/tasks/` içindeki ilgili görev kaydını oku; yoksa `.venv/Scripts/python.exe work/agent/project.py task "kullanıcının görevi"` ile oluştur. İsteği, kabul ölçütünü ve mevcut aşamayı kayda geçir. Eski test geometresini gerçek uçak sayma.

`work/setup/tool_config.json` ile ilgili `*_install.json` dosyalarını kullan. Araç yolu veya sürümünü hatırlayarak yazma. `.venv/Scripts/python.exe work/agent/project.py doctor` dosya varlığını kontrol eder; çalışabilirlik için ilgili testin gerçek sonucunu oku.

Görevin başında [operasyonel dersleri](references/operational_lessons.json) oku ve yalnız araç/sürüm/geometri kapsamına uyan ders kimliklerini görevde `applied_lesson_ids` ile kaydet. Hata, çelişkili ölçüm, yöntem değişikliği veya yeniden deneme varsa [kanıtlı iyileştirme döngüsünü](references/learning_loop.md) uygula. Hedef deney sonuçlarını içeren değerlendirme defterini kör analiz girdisine ekleme. Bu okuma, ortak disk veya model belleği bakımından yalıtım sağlamaz.

## Uygun aracı seç ve çalıştır

- Girdi kontrolü: `work/engineering/evaluate_inputs.py` yalnız kaldırma ön hesabıdır.
- Sayısal/aerodinamik hesap: `.venv`; CAD/çizim/ağ: `.venv-cad`.
- OpenVSP/VSPAERO ve XFOIL örnek entegrasyonu: `work/native/run_all.py`. Gerçek geometri için girdilerini uyarlayıp yeni bir çalışma klasöründe çalıştır; örnek sonuçları kopyalama.
- Yapısal çözüm: `work/fem/run_fem.py` içindeki doğrulanmış Gmsh/CalculiX bağlantısını kullan. Bu testin izotropik malzemesini kompozit kanada taşımadan önce yeni malzeme, sınır koşulu ve yük tanımla.
- Yerel yardımcı CAD modelleri: `work/models/benchmark.py` ve `outputs/reports/cad_model_research.md`. K-1B metinden OpenSCAD; Zero-to-CAD sekiz görünüşten CadQuery üretir. Boyut/katı/topoloji kontrolleri olmadan kabul etme.
- Parametre değişimi ile gerçek çözücü deneyi: `work/studies/wing_study.py`; durum koşullarını ve referansları girdi dosyasında açık tut.

Her göreve uygun araçları seç; bütün testleri her seferinde körlemesine çalıştırma. Yeni hesap için betiği `work/` altında yaz; girdileri, sürümleri, ham çıktıyı ve logları ayrı sakla. Mevcut komutları tek girişten çalıştırmak için `work/agent/project.py run core|native|fem|models|study` kullan; her çalıştırma giriş ve rapor SHA256 kaydı üretir.

## Sonucu kabul et

Görevin kabul ölçütünü geometri ölçümü, bağımsız hesap veya çözücü yakınsamasıyla kontrol et. Çalışan kodu tek başına tasarım doğrulaması sayma. Bir test başarısızsa kaydı sakla; düzeltmeyi yeni çalıştırmada doğrula.

`outputs/reports/` içinde kısa rapor üret. Her iddiayı gerçek çıktı, kaynak veya açık varsayıma bağla; eksik veriye bağlı sonuçları henüz değerlendirilemedi olarak bırak. Görev kaydında `acceptance`, `blocked_by`, `evidence` alanlarını ve `status` değerini güncelle. Kanıt girdilerinin ve raporların SHA256 değerlerini ekle. Tamamlanmayan mühendislik adımlarını tamamlandı işaretleme.

Son olarak PROJECT_STATE.md dosyasına kalıcı değişiklikleri yaz ve `work/agent/project.py status` çalıştır. Kullanıcıya sonucu, kanıt bağlantısını, sınırını ve sıradaki tek gerekli adımı Türkçe bildir.
