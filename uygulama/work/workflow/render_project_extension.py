"""User-facing usage, measured results and sourced agent-workflow changes."""
from datetime import datetime,timezone
import importlib.metadata as meta
import importlib.util
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';REPORTS=OUT/'reports'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def markdown(text):
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text);chunks=[]
    for p in text.strip().split('\n\n'):
        if p.startswith('# '):chunks.append('<h1>'+p[2:]+'</h1>')
        elif p.startswith('## '):chunks.append('<h2>'+p[3:]+'</h2>')
        elif p.startswith('- '):chunks.append('<ul>'+''.join('<li>'+s[2:]+'</li>' for s in p.splitlines())+'</ul>')
        else:chunks.append('<p>'+p+'</p>')
    return '\n'.join(chunks)
def page(title,body):return f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>body{{font:16px/1.65 'Segoe UI',sans-serif;background:#eef3f6;color:#173246;margin:0}}main{{max-width:1080px;margin:auto;padding:35px 24px}}section{{background:white;border:1px solid #d7e2ea;border-radius:12px;padding:26px;margin:20px 0}}h1{{line-height:1.2;font-size:32px}}h2{{font-size:23px}}a{{color:#087f89}}img{{width:100%}}li{{margin:8px 0}}</style><main>{body}</main></html>'''
def deliver(name,text,extra=''):
    for old,new in [('OpenAeroStruct2','OpenAeroStruct 2'),('OpenMDAO3','OpenMDAO 3'),('yaklaşık17','yaklaşık 17'),('EXE6.144',f"EXE {(OUT/'Muhendislik-Merkezi.exe').stat().st_size:,}".replace(',','.')),(')15/15',') 15/15'),('kontroller26','kontroller 26'),('akışı17','akışı 17'),('ağ13','ağ 13'),('hedef−10','hedef −10'),('Bu2D','Bu 2D'),('ve3D','ve 3D'),('RANS%','RANS %'),('doğrulanmış3D','doğrulanmış 3D'),('biriminin1','biriminin 1')]:text=text.replace(old,new)
    (REPORTS/(name+'.md')).write_text(text,encoding='utf-8')
    (REPORTS/(name+'.html')).write_text(page(text.splitlines()[0][2:],'<section>'+markdown(text)+'</section>'+extra),encoding='utf-8')
def main():
    pid='proje-0314dcd012';cfd=read(OUT/f'projects/{pid}/reports/profile_cfd_results.json');oas=read(REPORTS/'openaerostruct_examples.json');tube=oas['results'][1]
    commit=read(ROOT/'work/openaerostruct/agent_reference/manifest.json')['commit'];base=f'https://github.com/ideas-um/openaerostruct-llm-agent/blob/{commit}'
    manifest={'installed_utc':datetime.now(timezone.utc).isoformat(),'version':meta.version('openaerostruct'),'openmdao_version':meta.version('openmdao'),'python':str(ROOT/'.venv/Scripts/python.exe'),'module':importlib.util.find_spec('openaerostruct').origin,'pip_report':'work/setup/openaerostruct_pip_report.json','source_manifest':'work/openaerostruct/sources/manifest.json','reference_agent_commit':commit,'reference_agent_executed':False,'runtime_verified':oas['passed'],'physical_design_accepted':False,'test_report':'outputs/reports/openaerostruct_examples.json','runner':'work/openaerostruct/run_examples.py','limits':['Published coarse CRM examples and four total derivative groups checked','No OAS mesh independence, experimental validation or UAV-specific aeroelastic design','No OpenVSP Python API bridge','Upstream Gemini/Ollama agent and its auto-plot-save fork not installed']}
    save(ROOT/'work/setup/openaerostruct_install.json',manifest)
    cfg=read(ROOT/'work/setup/tool_config.json');cfg.update(workflow_interface='work/agent/projects_desk.ps1',workflow_executable='outputs/Muhendislik-Merkezi.exe',projects_registry='outputs/data/projects',latest_workflow_report='outputs/reports/projeler_exe_ve_profil_cfd.html',latest_engineering_report='outputs/reports/projeler_exe_ve_profil_cfd.html',openaerostruct=manifest)
    cfg['profile_cfd']={'runner':'work/qualification/profile_cfd.py','project_id':pid,'runtime_verified':cfd['passed'],'quality_passed':cfd['quality_passed'],'verified_scope':cfd['analysis_scope'],'report':f'outputs/projects/{pid}/reports/profile_cfd_results.json','limits':cfd['limits']};save(ROOT/'work/setup/tool_config.json',cfg)
    guide=f'''# OpenAeroStruct'tan ajan çalışma yöntemine

19 Ekim 2026 · Kaynak sürümü `{commit}`

OpenAeroStruct, VLM ile uzaysal kiriş modelini OpenMDAO içinde bağlar. Kanat ön tasarımında şekil, yük ve esneme ilişkisini incelemek için kullanılabilir. Hacim CFD'si, ayrılmalı akış veya ayrıntılı üç boyutlu yapı çözümü sayılmaz. [Resmî kapsam](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/).

## Ajan konusunda bulunan kaynak

Michigan Üniversitesi IDEAS/MDO laboratuvarlarının [OpenAeroStruct LLM Agent]({base}/README.md) deposu doğrudan ilgili. Yönlendirme, şablondan kod üretimi, değişiklik denetimi ve başarısızlık teşhisi aşamaları var. Yerelde 11 ilgili dosya sabit commit ve SHA256 ile saklandı; bu kaynağın ayrı LLM sistemi çalıştırılmadı, yayımlanan başarı sonuçları yeniden üretilmedi.

## Ajan talimatlarına alınan yaklaşım

- [Router]({base}/src/llm/router.md): sabit geometri analizi, polar taraması, tek/çok koşullu optimizasyon ve aeroelastik problemi ayır. Şablondaki varsayılan tasarım değişkenini kullanıcının isteği sayma; eksik fiziksel veriyi uydurma.
- [Coder]({base}/src/llm/coder.md): kurulu sürümde çalışan kaynaktan başla. Değişen fiziksel sayı ve formülü kaynağına bağla; kullanıcı bir sınırı değiştirdi diye bütün modeli yeniden varsayma.
- [Auditor]({base}/src/llm/auditor.md): geometriyi, ağ ayarını, fiziksel gereksinimi ve sayısal ölçeklemeyi ayır. Amaç/değişken/kısıt değişikliklerini tek tek denetle. Kullanıcı sert sınırı başarı elde etmek için kaldırılmaz.
- [Relakser]({base}/src/llm/relaxer.md): teşhisi gerçek son kısıt, değişken, sınır ve yakınsama verisine dayandır. Olası sebebi gözlenmiş ihlal gibi sunma.

Bu aşamalar yerel AGENTS.md'ye uyarlandı. Kaynak uygulamanın bütün onay kuralları kopyalanmadı: kullanıcının verdiği doğrulama kapsamında rutin ağ inceltme ve sayısal yakınsama araştırması gerekçesiyle kaydedilerek yürütülür. Eksik kritik girdi yalnız bağlı işi bekletir. Talimatlar fiziksel doğruluk veya hiç adım atlamama garantisi değildir; kabul kanıtı ayrıca gerekir.

## Birebir kopyalamanın sorunları

Kaynakta coder trim için alfa eklenmesine izin verirken router/auditor daha dar değişken yetkisi kullanıyor. Burada trim serbestliği ile şekil tasarım değişkeni ayrı kaydedilecek. Ayrıca [bağımlılıklar]({base}/pyproject.toml), resmî paket yerine özel auto-plot-save çatalına işaret ediyor; Gemini/Ollama ve ayrı arayüz bekliyor. Bunları mevcut Codex'e bağlanmış veya test edilmiş saymıyoruz. Kaynak ajan bir araştırma prototipidir; tüm uçak tasarımı ve halüsinasyonsuzluk kanıtı değildir.

## Gerçek yerel çalışma

Resmî OpenAeroStruct2.12.0 ve OpenMDAO3.45.1 proje ortamına kuruldu; yaklaşık17MB paket, mevcut NumPy/SciPy değişmedi. Bağımlılık kontrolü geçti. [İki resmî örnek](openaerostruct_examples.json) gerçekten optimize edildi. Aerodinamik örnekte CL=0,5 hedefi sağlandı. Tüp-kiriş örneğinde normalize L=W artığı {tube['L_equals_W']:.3g}; hasar kısıtı {tube['failure_max']:.3g}, belirlenmiş toleransla geçti. Alfa/kalınlık için yakıt ve denge toplam türevlerinin dört grubunda en büyük norm farkı %{100*max(r['relative_norm_error_with_unit_floor'] for r in tube['derivatives']):.4f}; eşik %0,5 idi. Bu dört grup tüm türevleri kapsamaz.

Bunlar kaba CRM eğitim örnekleridir. OAS ağ duyarlılığı, bağımsız fiziksel referans ve gerçek kanadın malzeme/yük kabulü henüz yapılmadı. [Resmî hata ayıklama rehberi](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/user_reference/debugging_tips.html), optimizasyon sonunda kısıtların ve geometrinin yeniden kontrolünü destekler.

## OAS'a özgü kontroller

Tam/yarım açıklık ve yük çarpanı, kontrol noktalarının uçtan köke sırası, chord_cp ölçeği, re biriminin1/m olması; CL0/CD0 ekleri ve viskoz korelasyon kapsamı kaydedilecek. Örnek yakıt/malzeme verileri gerçek İHA'ya taşınmayacak. [Değişken sözlüğü](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/user_reference/mesh_surface_dict.html). [OpenVSP ağ örneği](https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/advanced_features/openvsp_mesh_example.html) Python API ister; burada bu bağlama kurulmadı.

Sonraki ölçülebilir adım gerçek kanadın malzeme, kesit, yük ve görev verilerini kaynaklarıyla tanımlamak. Ayrı bir LLM sistemi kurmak bu verilerin yerini tutmaz.
'''
    deliver('openaerostruct_ajan_yaklasimi',guide,'<section><img src="../plots/openaerostruct_deformation.png"><p>Resmî CRM örneğinin hesaplanmış bağlı ağ değişimi.</p></section>')
    report=f'''# Proje merkezli Mühendislik Merkezi

19 Ekim 2026 · [EXE'yi aç](../Muhendislik-Merkezi.exe)

Sol taraftan projeyi seç; görev, CAD, alanlar ve raporlar o proje içinde kalır. Yeni proje oluşturabilir, dosya ekleyebilir, aktif model seçebilir, FreeCAD/OpenVSP tercihini projeye kaydedebilirsin. Görev taslağı proje değiştirince korunur. İlk gerçek İHA verileri yerinde kaldı; eski araç örnekleri ayrı projeye bağlandı.

## Kullanım ve EXE

Proje özeti içinde CAD programını seç. Uyumlu aktif dosya varsa onunla açılır; yoksa program boş açılır. Proje dosyalarından model ekle ve aktif seç. Görev ve kısıtlar bölümünde bilinen verileri gir. Yalnız kaydet isteği dosyaya yazar; bu sohbetten kaydedilen göreve devam edilebilir. Kaydet ve ajanla başlat ayrı Codex terminal penceresini seçili proje/görevle açar; bu sohbete otomatik mesaj göndermez.

EXE6.144 baytlık Windows başlatıcısıdır; mevcut Python ve mühendislik araçlarını kullanır. Bütün proje klasörleri yanında kalmalı; yalnız EXE'yi taşımak yetmez. Aynı dosya/komut işlevleri korunur, görünür CMD penceresi gerekmez. CMD aynı yeni arayüzün yedeğidir.

## Denetimler

[Yeni proje/aktif CAD/dosya/taslak/yol ve görev aktarımı](project_interface_checks.json)15/15 geçti; ayrı çıktı klasöründe gerçek CAD üretimi ve özgün CAD'in korunması dahil. Temel kontroller26/26, önceki görev akışı17/17. EXE yolu, arayüzün açılıp çıkması, dört sekmenin çizimi ve gezinme düğmeleri denetlendi. Testte yeni LLM oturumu başlatılmadı.

## Yeni geometride ağ ve CFD

Profil ağı ve CFD doğrulaması projesinde kaynak DAT → yeni Gmsh akış ağı → native SU2 Euler → kuvvet/alan → bağımsız XFOIL kontrolü baştan çalıştı. Orta/ince ağ13.914/41.768 hücre; ince CL={cfd['results'][-1]['CL']:.6f}; CL ağ farkı %{100*cfd['CL_grid_relative_change']:.2f}; XFOIL inviscid farkı %{100*cfd['CL_reference_relative_difference']:.2f}. Önceden belirlenmiş bu koşula ait sayısal ön kabul geçti. İlk başarısız kuvvet kararlılığı çalışmaları saklandı; ince hedef−10 ile tekrar çözüldü. [Ağ/alan/kuvvet raporu](../projects/{pid}/reports/profile_cfd.html).

Bu2D sürtünmesiz profil sonucudur. Negatif sayısal CD gerçek sürükleme/itki değildir. Sınır tabakası, geçiş, stall, uzak alan duyarlılığı ve3D uçak CFD kabulü açık kalır. Önceki RANS%22,84 sürükleme ağ farkı ve karmaşık VLM yüzey CDi kabulü kapanmadı.

## OpenAeroStruct ve ajan talimatları

Üniversite kaynaklı OpenAeroStruct LLM Agent'ın isteği yapılandırma, uygun şablon, değişiklik denetimi ve başarısızlık teşhisi yaklaşımı incelendi; yerel kurallara uyarlandı. Kaynak projenin ayrı LLM sistemi kurulmadı. Resmî OpenAeroStruct/OpenMDAO kuruldu; iki örnek, kısıtlar ve dört türev grubu gerçek çalışmada geçti. Aeroelastik araç testidir; yeni İHA tasarımı veya CFD değildir. [İnceleme, kaynaklar ve yerel test](openaerostruct_ajan_yaklasimi.html).

## Açık kalanlar

Fusion OAuth tamam; bu sohbetin araç listesinde motor yok, lisans/parametrik parça/STEP döngüsü test edilmedi. Keyfi içe aktarılmış CAD'i tek tıkla ağlayıp doğrulanmış3D CFD yapan genel servis henüz yok. Hazır olmayan projenin düğmesi eski örneği sessizce çalıştırmaz. Araştırma ve aday taraması yeni görev için kapsam/bütçe tanımlanarak yürütülür. Gerçek İHA'nın sekiz kavramsal adımı güncel veri bekliyor; ANSYS sona bırakıldı.

Ölçülebilir sonraki adım gerçek görevin koşullarını, bileşen kütlelerini ve kanat malzeme/kesit/yük verisini kaydedip eksik girdi tablosunu kapatmak.
'''
    deliver('projeler_exe_ve_profil_cfd',report,f'<section><img src="../plots/projects_iha_0.png"></section><section><img src="../projects/{pid}/plots/profile_field_mesh.png"><p>Gerçek Euler basınç alanı ve yeni ağ.</p></section>')
    start='''# Mühendislik Merkezi — buradan başla

**[Muhendislik-Merkezi.exe](Muhendislik-Merkezi.exe) dosyasını çift tıkla, soldan projeni seç.** Aynı projenin görevleri, CAD dosyaları, analiz alanları ve raporları bu pencerenin içinde listelenir. [Güncel rapor ve kullanım](reports/projeler_exe_ve_profil_cfd.html).

- İHA projem gerçek girdiler içindir. Araç doğrulama örnekleri önceki kurulum testleridir. Profil ağı ve CFD doğrulaması yeni kaynak profilden ağ/CFD deneyidir. Yeni proje kendi boş girdilerini ve klasörlerini oluşturur.
- Proje özetinden CAD programını seç. FreeCAD/OpenVSP tercihi projeye kaydedilir. Uyumlu aktif model varsa onunla, yoksa boş açılır. Yeni dosyayı projenin CAD klasörüne kaydet. Proje dosyalarından dışarıdaki modeli kopyalayabilir ve aktif seçebilirsin.
- Görev ve kısıtlar bölümünde isteği/bildiğin değerleri yaz. Boş alan bilinmiyor kalır. Taslak proje değiştirince korunur; henüz görev kaydı oluşturulmamış olabilir.
- Yalnız bu projeye kaydet isteği dosyaya yazar. Bu sohbette kaydedilen görevi incelememi söyleyebilirsin. Kaydet ve ajanla başlat seçili proje bilgileriyle ayrı Codex terminal penceresi açar; bu sohbete otomatik mesaj göndermez.
- Görevler ve çalışmalar bölümünde hazırlanmış analizleri seç. Girdi tanımı yoksa düğme kapalıdır; eski örnek bu projenin sonucu yerine kullanılmaz. CAD eklemek tek başına uygun CFD ağı ve sınır koşulu hazırlamaz.
- Proje dosyaları filtresinden rapor/grafik/alan aç. STEP/FCStd FreeCAD'de, VSP3 OpenVSP'de, MSH/POS Gmsh'de açılır. VTU ham alandır; ParaView kurulu sayılmaz.

EXE küçük başlatıcıdır; mevcut Python/araçlar ve bütün proje klasörleri birlikte kalmalı. CMD aynı yeni arayüzün yedeğidir. Ajanın dosya ve komut girişleri korunur.

Projeler data/projects/, yeni sonuçlar projects/<kimlik>/ altında. İlk İHA'nın eski data/project/ girdileri yerinde korundu. Görevler data/tasks/ içinde proje kimliğiyle tutulur. Aktif CAD değişirse eski analizle eşleşmesi yeniden gerekir. STEP özellik geçmişini kendiliğinden taşımaz.

İleri kullanım: .venv/Scripts/python.exe -X utf8 work/agent/project.py run GRUP --project KIMLIK. geometry, complex-vlm ve profile-cfd hazırlanmış proje tanımı ister. Diğer eski gruplar qualification araç örnekleridir; aerostruct resmî OpenAeroStruct örneklerini çalıştırır. doctor yalnız yol varlığını, gerçek testler çalışmayı denetler.

[OpenAeroStruct ve ajan kuralları](reports/openaerostruct_ajan_yaklasimi.html), [önceki CAD/VLM/SU2 raporu](reports/muhendislik_seviyesi_ve_cfd.html), [eski hafif CFD iş akışı](reports/hafif_cfd_ve_is_akisi.html), [CAD modeli araştırması](reports/proje_durum_ve_k1b_arastirma.html).

Fusion girişi tamamlandı; bu sohbette motor, lisans/hub ve parametrik model/STEP testi bekliyor. Küçük CAD modelleri deneysel yardımcıdır. Euler profil kabulü eski RANS veya3D uçak kabulünü kapatmaz. Gerçek uçak için güncel görev/bileşen verileri ayrıca gerekir. Kurulum testleri uçuşa elverişlilik garantisi değildir. ANSYS sona bırakıldı.
'''
    (OUT/'Baslangic.md').write_text(start,encoding='utf-8');print('PROJECT_EXTENSION_REPORTS_OK')
if __name__=='__main__':main()
