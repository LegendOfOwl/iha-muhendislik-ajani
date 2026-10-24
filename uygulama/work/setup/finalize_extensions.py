"""Update the project inventory and build user-facing verification reports."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def save(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
cfg=load('work/setup/tool_config.json')
fem=load('outputs/reports/fem_results.json'); study=load('outputs/reports/wing_study_results.json')
models=load('outputs/reports/cad_model_benchmark.json'); repaired=load('outputs/reports/checked_parts_results.json')
native=load('outputs/reports/external_test_summary.json'); core=load('outputs/reports/test_results.json')
profile=load('outputs/reports/freecad_portable_profile.json')
cfg['freecad']=load('work/setup/freecad_install.json')
cfg['calculix']={'version':'2.22','executable':cfg['freecad']['executables']['ccx.exe'],'verified':fem['passed'],'source':'Official FreeCAD 1.1.4 portable package'}
cfg['gmsh']={'version':'4.15.2','python':cfg['cad_python'],'integration':'Official pip SDK / native gmsh-4.15.dll','verified':fem['passed'],
             'FreeCAD_GUI_binary_version':'4.15.0','FreeCAD_GUI_binary':cfg['freecad']['executables']['gmsh.exe']}
cfg['k_model']=load('work/setup/k_model_install.json'); cfg['cad_model']=load('work/setup/cad_model_install.json')
cfg['openscad']={'version':'2021.01','executable':cfg['k_model']['executable'],'verified':repaired['passed'],'source':'Official portable ZIP'}
cfg['deferred_tools']={'ANSYS':'Deferred heavy installation; license not checked'}
cfg['project_entry']='outputs/Muhendislik-Merkezi.cmd'
cfg['project_runner']='work/agent/project.py'
cfg['project_skill']='.agents/skills/iha-muhendislik/SKILL.md'
cfg['last_extension_verification']=datetime.now(timezone.utc).isoformat()
cfg['extension_download_bytes']=sum(a['bytes'] for a in cfg['cad_model']['files'])+cfg['k_model']['model']['bytes']+cfg['k_model']['openscad_archive']['bytes']+cfg['freecad']['archive_bytes']
cfg['system_path_changed']=False
cfg['freecad_profile_is_project_local']=True
cfg['model_auto_engineering_acceptance']=False
save(ROOT/'work/setup/tool_config.json',cfg)

evidence={}
for name in ['test_results.json','external_test_summary.json','fem_results.json','wing_study_results.json',
             'cad_model_benchmark.json','checked_parts_results.json','freecad_portable_profile.json']:
    p=OUT/'reports'/name
    evidence[name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
qualified=core['all_requested_groups_passed'] and native['passed'] and fem['passed'] and study['passed'] and repaired['passed'] and profile['passed']
summary={'timestamp':datetime.now(timezone.utc).isoformat(),'engineering_toolchain_passed':qualified,
         'specialized_model_inference_passed':models['installation_inference_passed'],
         'specialized_model_geometry_passed':models['quality_passed'],'aircraft_feasibility':'not_assessed',
         'evidence':evidence,'downloads_MiB_excluding_small_wheels':round(cfg['extension_download_bytes']/2**20,1)}
save(OUT/'reports/verification_summary.json',summary)

fine=fem['levels'][-1]
theory=next(c['evidence'] for c in fem['checks'] if c['name']=='Independent beam theory comparison')
change=next(c['evidence']['relative_change'] for c in fem['checks'] if c['name']=='Mesh convergence medium to fine')
lines=['# Mühendislik araçları ve proje düzeni — sonuç','',
       '18 Ekim 2026. Yerel araç zinciri ve projeye bağlı görev düzeni kuruldu. Yerel CAD modellerinin çalışması ve ölçülere uygunluğu ayrı sonuçlar olarak izlendi.','',
       '## Kurulu araçlar','',
       '| İş | Araç ve sürüm | Durum |','|---|---|---|',
       '| Parametrik uçak geometrisi / 3D potansiyel akış | OpenVSP 3.55.0 / VSPAERO 7.2.2 | Önceki native testler ve yeni kanat karşılaştırması geçti |',
       '| 2D viskoz profil | XFOIL 6.99 | Reynolds/Mach/Ncrit/geçiş ve eksik açılar kaydedildi |',
       '| Düzenlenebilir CAD | FreeCAD 1.1.4, CadQuery 2.8.0 | Native belge, STEP tekrar açma ve geometri kontrolleri geçti |',
       '| Ağ / yapısal çözüm | Gmsh SDK 4.15.2 / CalculiX 2.22 | Gerçek 3D çözüm, üç ağ ve analitik karşılaştırma geçti |',
       '| Metinden şekil | OpenSCAD 2021.01 / K-1B Q8_0 | Yerel üretim çalıştı; özgün 3 parça bütün kabul ölçütlerini geçemedi |',
       '| Görünüşlerden CAD | Zero-to-CAD 2B Q6_K + f16 görsel bağdaştırıcı | Yerel üretim çalıştı; geçerli katı üretilemedi |','',
       'FreeCAD içindeki FEM arayüzü için de CalculiX ve paketlenmiş Gmsh 4.15.0 yolları proje profiline yazıldı; yeni FreeCAD sürecinde okunabildi. Bu, Gmsh 4.15.2 SDK ile yaptığımız sayısal ağ testinden ayrı bir yapılandırma kontrolüdür. Genel sistem PATH veya kalıcı Windows çalıştırma ilkesi değiştirilmedi. Merkez başlatıcısındaki PowerShell seçeneği yalnız o sürece uygulanır.','',
       '## Gerçek yapısal çözüm','',
       'Sentetik test: 200×10×10 mm ankastre kiriş; E=70 GPa, nu=0,3 ve uç yüzde toplam 10 N yük test varsayımıdır. Analitik hesap SI tabanında yapıldı; native CAD/FE girdisinde mm–N–MPa dönüşümü açıkça kaydedildi.','',
       f'- İnce ağ: {fine["nodes"]} düğüm, {fine["elements"]} adet C3D10 eleman.',
       f'- Uç sehim: {fine["tip_displacement_mm"]:.6f} mm; Euler–Bernoulli: {theory["Euler_Bernoulli_mm"]:.6f} mm.',
       f'- Bağımsız hesap farkı: %{100*theory["relative_difference"]:.3f}; orta–ince ağ değişimi: %{100*change:.3f}.',
       '- Üç ağda kuvvet dengesi ve eleman bağlantıları kontrol edildi. 14/14 kontrol geçti.',
       '- İlk ağ aktarımındaki C3D10 kenar düğümü sıralama sorunu yakalandı; CalculiX sırasına dönüşüm ve tüm kenar orta noktalarının kontrolü eklendi. Başarısız ham çalışma saklandı.',
       '- Bu kiriş bir İHA kanadı değildir. Kompozit, burkulma, yorulma, bağlantılar veya dayanım marjı değerlendirilmedi. Sehim yakınsaması gerilme yakınsaması sayılmadı.','',
       '## Parametreli aerodinamik karşılaştırma','',
       'Tek dosyadan üç AR adayı oluşturuldu; referans alan/açıklık/veter ve moment noktası geometriyle birlikte değişti. Hız/dinamik viskozite/yoğunlukla Re, ses hızıyla Mach hesaplandı. Her adayda iki panel düzeyi ve wake değişimi kontrol edildi. VSPAERO yerel yükleriyle global kaldırma karşılaştırıldı; yerel Cl değerleri XFOIL polarının içinde eşleştirildi.','',
       '**27/27 yöntem kontrolü geçti.** AR=8 polarda +2°, AR=10 polarda −2° yakınsamadı; bu açılar gizlenmedi. Mevcut yakınsamış noktalarda, karşılaştırma aralığını kapsayan polar üzerinden doğrusal enterpolasyon yapıldı. Bu nedenle profil sürüklemesi yaklaşık kestirimdir. 2D/3D bu bağlantı stall veya deneysel doğrulama sayılmaz.','',
       '| AR | Açıklık m | Veter m | Re | Ortak CL=0,35 için CDi | Tahmini profil CD |','|---|---|---|---|---|---|']
for r in study['candidates']: lines.append(f'| {r["AR"]} | {r["span_m"]:.3f} | {r["chord_m"]:.3f} | {r["Re"]:.0f} | {r["CDi_scaled"]:.5f} | {r["CDprofile_estimated"]:.5f} |')
lines += ['', 'Bu karşılaştırma test varsayımları altındaki izole kanatları kapsar. Gerçek uçak için en iyi kanat, toplam sürükleme, sürekli güç, enerji veya uçuşa uygunluk sonucu değildir.','',
          '## Ajanın çalışma düzeni','',
          '- Tek giriş: `outputs/Muhendislik-Merkezi.cmd`; burada doğal dille görev verilir ve gerçek araçlar açılır.',
          '- Görevler `outputs/data/tasks`, güncel proje girdileri `outputs/data/project` altında tutulur.',
          '- Proje becerisi `.agents/skills/iha-muhendislik/SKILL.md`; üst kurallar AGENTS.md içinde korunur.',
          '- Test/çalışma komutları tek girişte toplanır. Yeni çalışmalarda girdi ve rapor SHA256 değerleri ile ham loglar saklanır; eski rapor yeni çalışmanın sonucu sayılmaz.',
          '- Gerçek İHA kavramsal adımları ayrı izlenir. Eksik kütleler sıfır kabul edilmedi; uçak fizibilitesi değerlendirilmedi.',
          '- Mühendislik Merkezi arayüzü oluşturulup görseli kontrol edildi. Başlatıcı komut oluşturma yolu yeni bir ajan başlatmadan sınandı. Bu çalışmanın kendisi gerçek araçlarla yürütüldü; ayrıca ikinci bir LLM seansı otomatik başlatılmadı.','',
          '## Kayıtlar ve yeniden kurma','',
          '[Birleşik kanıt kaydı](verification_summary.json), [model araştırması](cad_model_research.md), [yerel model ölçümleri](cad_model_benchmark.json), [FEM](fem_results.json), [kanat karşılaştırması](wing_study_results.json).','',
          f'Yeni büyük dosyaların toplam indirmesi yaklaşık {cfg["extension_download_bytes"]/2**30:.2f} GiB; küçük Python paketleri buna dahil değil. Veri kümesinin bir milyon örneği indirilmedi. Kaynak arşivleri ve checksum kayıtları çalışma klasöründe tutuluyor.',
          'İki Python ortamının wheel sürümleri ve gerçek indirme SHA256 değerleri kilit dosyalarında güncellendi; bağımlılık kontrolü geçti. `work/setup/rebuild_light.ps1` Python ortamlarını geri kurma yoludur; bu turda sıfırdan bütün ortamların yeniden kurulması denenmedi. Native araçlar için kurulum betikleri ve sürümlü manifestler `work/setup` içindedir.',
          'ANSYS ağır/lisanslı aşama olarak sona bırakıldı. Diğer araştırma modelleri karşılaştırma raporunda kurulu/denenmemiş olarak açıkça ayrıldı.','',
          '## Birincil kaynaklar','',
          '- [Resmi FreeCAD 1.1.4 paketi](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4)',
          '- [Gmsh SDK ve belgeleri](https://gmsh.info/)',
          '- [CalculiX geliştirici sitesi](https://www.calculix.de/)',
          '- [OpenSCAD indirmeleri](https://openscad.org/downloads.html)',
          '- [OpenAI: yerel klasörler ve projeler](https://learn.chatgpt.com/docs/projects)','']
(OUT/'reports/engineering_toolchain_report.md').write_text('\n'.join(lines),encoding='utf-8')

guide='''# İHA Mühendislik — buradan başla

**Muhendislik-Merkezi.cmd dosyasını çift tıkla.** Görevini yazıp **Ajanla çalışmaya başla** düğmesine bas. Mevcut ChatGPT hesabını kullanan Codex bu proje klasöründe açılır; dosyaları okuyabilir, CAD ve analiz araçlarını çalıştırabilir, çıkan sonucu kontrol edip raporlayabilir. Bu Codex sohbetinde de doğrudan görev verebilirsin.

## Normal sohbetten bu kullanıma geçiş

Burada ayrı bir model eğitmek veya yeni API anahtarı almak gerekmiyor. Bu kurulumda Codex modelin çalıştığı ajan ortamıdır. Proje klasörü girdileri ve araçları taşır; AGENTS.md kuralları, proje becerisi çalışma yöntemini, görev kayıtları da yapılan işi taşır. Yalnız bir ChatGPT projesine talimat yapıştırmak aynı yerel araç kurulumunu sağlamaz.

Masaüstü uygulamasında ayrıca yerel proje olarak göstermek istersen Projects bölümünden bu klasörü ekleyip birincil klasör seç: `C:\\Users\\Urungu\\Documents\\Codex\\2026-10-18\\bu`. Merkez başlatıcısı bu seçime gerek duymadan doğru klasörde çalışır. Bu çalışma uygulamanın kenar çubuğunda yeni bir proje kaydı oluşturduğunu iddia etmez. [Resmi proje/klasör açıklaması](https://learn.chatgpt.com/docs/projects).

## Görev nasıl verilir?

Görev, mevcut veriler ve istediğin kabul ölçütünü birlikte yaz. Örneğin:

> Bu proje klasöründeki görev ve kütle verilerini oku. Kavramsal tasarım için iki kanat adayını aynı kısıtlarla karşılaştır. Gerekli geometriyi oluştur, uygun yerel araçları gerçekten çalıştır, yakınsama ve bağımsız hesap kontrollerini yap. Kaynakları, varsayımları ve eksik veriye bağlı sonuçları açıkça ayır. CAD dosyaları, grafikler ve kanıt bağlantılı kısa rapor üret.

Eksik kritik veriler uydurulmaz. Tamamlanabilen işler sürer; eksik veriye bağlı karar açık bırakılır. Bir işin araya girip kaybolmaması için görev ve durum dosyaya yazılır.

## Nerede ne var?

- **Proje-Ozeti.html**: tek sayfada durum, test sonuçları, çizimler ve rapor bağlantıları.
- **data/project/**: gerçek projenin güncel görev girdileri, bileşen kütle bütçesi ve kavramsal adım durumları. Şu anda bilinmeyenler boş bırakıldı.
- **data/tasks/**: görevin metni, durumu, kabul ölçütleri, eksikleri ve kanıtları.
- **cad/**: düzenlenebilir VSP3, FreeCAD belgesi, STEP, DXF ve üç görünüş. Test örnekleri gerçek İHA olarak seçilmiş değildir.
- **simulations/**: gerçek solver dosyaları, model istemleri ve ham çıktılar.
- **reports/**: kısa raporlar ve ayrıntılı ölçümler. **work/**: çalışma betikleri, kurulum manifestleri ve loglar.

## Merkezdeki düğmeler

**Aerodinamik + CAD** OpenVSP/VSPAERO ve XFOIL bağlantısını, **CAD → yapısal analiz** FreeCAD/Gmsh/CalculiX zincirini, **Kanat karşılaştırması** dosyadan yönetilen üç adayı çalıştırır. **Yerel CAD modelleri** K-1B ve Zero-to-CAD'i tekrar dener; geometri kabulünün başarısız olabileceği raporda ayrıca gösterilir. Bu düğmeler internetten sessizce yeni model indirmez.

**OpenVSP modelini aç** ve **FreeCAD modelini aç** düzenlenebilir örnekleri gerçek programda gösterir. Gerçek proje verisini araç testi parametrelerinden ayrı tut.

İleri kullanım için tek komut girişi: `.venv/Scripts/python.exe -X utf8 work/agent/project.py`. `status`, `doctor`, `task` ve `run core|native|fem|models|study` alt komutları bulunur. Olağan kullanımda komut yazman gerekmez.

## Ne kuruldu, model ne kadar işe yaradı?

OpenVSP/VSPAERO, XFOIL, FreeCAD, CalculiX, Gmsh, CadQuery, OpenSCAD ve iki küçük yerel CAD modeli kurulu. [Kurulum/analiz raporu](reports/engineering_toolchain_report.md) ve [model karşılaştırması](reports/cad_model_research.md) gerçek sonuçları içerir.

K-1B hızlı taslak üretti; üç istemin bütün ölçü/geometri gereksinimlerini sağlayamadı. Zero-to-CAD Q6 denemesi geçerli katı üretemedi. Codex'in sonradan düzelttiği üç parça ayrı testte geçti. Bu sonuçlar küçük modellerin tek başına güvenilir mühendislik ajanı olmadığını gösteren yerel denemelerdir; bütün modeller için genel hüküm değildir.

ANSYS ağır kurulum/lisans aşaması olarak sona bırakıldı. Gerçek İHA'nın güncel gereksinimleri ve bileşen kütleleri gelince kavramsal tasarım bu dosyalar üzerinden ilerler. Kurulum testleri uçuşa elverişlilik veya halüsinasyonsuzluk garantisi değildir.
'''
(OUT/'Baslangic.md').write_text(guide,encoding='utf-8')
state_backup=ROOT/'work/setup/project_state_before_extension.md'
if not state_backup.exists(): shutil.copy2(ROOT/'PROJECT_STATE.md',state_backup)
state='''# İHA mühendislik çalışma alanı — güncel durum

Son güncelleme: 18 Ekim 2026. Kapsam: gerçek yerel araçların kurulması, nitelendirilmesi ve projeye bağlı ajan iş akışı. Gerçek İHA gereksinimleri bu klasöre aktarılmadı; test boyutları gerçek tasarım verisi değildir.

## Kullanım
- Tek giriş: outputs/Muhendislik-Merkezi.cmd; durum/rapor: outputs/Proje-Ozeti.html.
- Yerel Codex, mevcut ChatGPT hesabını kullanır. Merkez görev metnini kaydeder ve Codex'i bu klasörde açar; burada da aynı araçlarla çalışılabilir.
- Proje becerisi: .agents/skills/iha-muhendislik/SKILL.md. Girdi ve görev kayıtları outputs/data/project ve outputs/data/tasks altında.
- Tek komut düzeni: .venv/Scripts/python.exe -X utf8 work/agent/project.py status|doctor|task|run. run grupları core, native, fem, models, study. Her yeni çalışmada giriş ve rapor SHA256, çıkış durumu ve ham log saklanır.

## Kurulu ve gerçek testten geçenler
- Sayısal/aerodinamik ortam .venv; CAD/ağ ortamı .venv-cad. Windows x64 Python 3.12.14; kurulu masaüstü Python tabanına bağlıdır. İki ortamın paketleri SHA256 ile kilitli; pip bağımlılık kontrolü geçti. Global PATH değişmedi.
- AeroSandbox 4.2.10, NeuralFoil 0.3.3, CasADi 3.8.1 ve CadQuery 2.8.0. Son temel kontrol 26/26.
- OpenVSP 3.55.0 ve VSPAERO 7.2.2 native exe/AngelScript; OpenVSP Python bağlaması kurulmadı. XFOIL 6.99. Önceki harici entegrasyon 26/26 kontrol geçti.
- FreeCAD 1.1.4 taşınabilir paket; CalculiX 2.22, Gmsh SDK 4.15.2. CAD→STEP→C3D10 ağ→gerçek FE çözümünde 14/14 kontrol geçti; üç ağ, kuvvet dengesi ve bağımsız kiriş hesabı var. Native FreeCAD dosyası kaydedildi ve tekrar açıldı.
- FreeCAD GUI FEM araç yolları proje içindeki taşınabilir profile yazıldı; ayrı süreçte okuma doğrulandı. FreeCAD paketindeki Gmsh GUI ikilisi 4.15.0; sayısal ağ testinde kullanılan SDK 4.15.2'dir.
- Yeni dosyadan yönetilen üç kanat karşılaştırması: 27/27 yöntem kontrolü geçti. Geometriyle tutarlı S/b/c, Re/Mach hesabı, panel/wake kontrolü, XFOIL ve VSPAERO yerel yük eşleştirmesi kullanıldı. Yakınsamayan XFOIL açıları kayıtlı; profil sürüklemesi yaklaşık kestirimdir.
- OpenSCAD 2021.01 taşınabilir. Codex tarafından düzeltilen üç parçanın geometri ve bağımsız STEP kontrolleri 3/3 geçti.

## Yerel CAD modelleri
- Reddit'teki model ThomasTheMaker/K-1B, Gemma tabanlı metin→OpenSCAD modelidir. Q8_0 kuruldu; üç native üretim çalıştı. Bütün boyut/delik/merkezleme ölçütlerini sağlayan özgün çıktı 0/3. Çalışan STL doğru parça sayılmadı.
- ADSKAILab/Zero-To-CAD-1m model değil veri kümesidir. İlgili 2B modelin Q6_K dönüşümü ve f16 görsel bağdaştırıcısı kuruldu. Sekiz temiz görünüşle iki yerel deneme geçerli katı üretmedi. Özgün BF16 modeli ve tam benchmark burada denenmedi.
- Ağırlıklar ve native runtime dosyaları upstream SHA256 ile doğrulandı. İki model de yalnız deneysel yardımcıdır; otomatik mühendislik kabulü kapalıdır.
- CADmium, CAD-Recode, Text2CAD, CAD-Coder ve Pointer-CAD v2 araştırıldı. Kurulmuş veya yerelde ölçülmüş gibi gösterilmedi. Ayrıntı outputs/reports/cad_model_research.md.

## Sınırlar ve gerçek proje
- Gerçek uçak fizibilitesi henüz değerlendirilmedi. Kavramsal sekiz adım outputs/data/project/conceptual_steps.json içinde bekliyor; görev, kütle, güç/enerji, CG/trim/kararlılık ve yapı kanıtları yok.
- Kaldırma ön hesabı work/engineering/evaluate_inputs.py kapsamlı uçak tasarımı değildir. Boş/yanlış girdilere sonuç üretmeyen kontroller korunur.
- OpenVSP uçak görünümlü testte gövde CAD'de vardır ama taşıyıcı-yüzey analizinden çıkarılmıştır. Tüm kanat-kuyruk modelinin ayrı panel yakınsaması yapılmadı; yeni çalışma izole dikdörtgen kanatlara aittir.
- FE kiriş testi sentetik/izotropiktir. Uçak yapısı, kompozit, burkulma, yorulma, bağlantı ve gerilme yakınsaması doğrulanmadı.
- ANSYS kurulmadı; ağır/lisanslı aşama sona bırakıldı.

## Kanıt
outputs/reports/engineering_toolchain_report.md, verification_summary.json, cad_model_benchmark.json, wing_study_results.json, fem_results.json ve checked_parts_results.json. Araçların gerçek yolları work/setup/tool_config.json içindedir. Başarısız denemeler ve eski ham loglar korunur.

Sonraki gerçek mühendislik adımı: kullanıcının güncel görev/gereksinim ve bileşen verilerini kaynaklarıyla outputs/data/project içine aktar; önce kavramsal girdi ve kütle bütçesi oluştur. Eski sohbet hedeflerini otomatik yeni gereksinim sayma.
'''
(ROOT/'PROJECT_STATE.md').write_text(state,encoding='utf-8')
sys.path.insert(0,str(ROOT/'work/agent'))
from project import status,doctor
doctor(); status()
print(json.dumps(summary,ensure_ascii=False,indent=2))
