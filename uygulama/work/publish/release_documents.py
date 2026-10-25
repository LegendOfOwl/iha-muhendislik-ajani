from incremental_export import ROOT,DEST,RUN,VERSION,PLAN,read,dump,digest,now
from pathlib import Path

def main():
    plan=read(PLAN);m6root=ROOT/'outputs/projects/proje-e9319baef1'
    m6=read(m6root/'reports/tmr_source_case_review_20261025.json')
    plate=read(ROOT/'outputs/reports/flatplate_comparison_20261025.json')
    p=DEST/'README.md';text=p.read_text(encoding='utf-8')
    text=text.replace('Güncel dağıtım **v0.10.0**','Güncel dağıtım **v0.11.0**')
    text=text.replace('v0.1.0 → v0.10.0 kilometre taşı notları','v0.1.0 → v0.11.0 sürüm ve kanıt notları')
    text=text.replace('Tam güncel içerik için `main` veya `v0.10.0` kullanın.','v0.1.0–v0.10.0 bu geriye dönük içe aktarımdır. **v0.11.0 ve sonrası gerçek artımlı Git değişiklikleridir.** Tam güncel içerik için `main` veya `v0.11.0` kullanın.')
    text=text.replace('| [v0.10.0](surumler/v0.10.0/README.md) | Düzenlenmiş GitHub dağıtımı |','| [v0.10.0](surumler/v0.10.0/README.md) | Düzenlenmiş GitHub dağıtımı |\n| [v0.11.0](surumler/v0.11.0/README.md) | Kaynak TMR M6, düz plaka, güvenilirlik politikası; gerçek artımlı sürüm |')
    text=text.replace('[Güncel proje özeti](uygulama/outputs/Proje-Ozeti.html) · [Ajan dersleri](uygulama/outputs/reports/ajan_talimat_gelisimi_20261024.html) · [M6 sonuçları](uygulama/outputs/reports/onera_m6_24_ekim.html)', '[GitHub’da okunabilir güncel sonuçlar](raporlar/v0.11.0/README.md) · [Yerel HTML proje özeti](uygulama/outputs/Proje-Ozeti.html) · [Ajan dersleri](uygulama/outputs/reports/ajan_talimat_gelisimi_20261024.html) · [M6 sonuçları](raporlar/v0.11.0/README.md#onera-m6)')
    intro='''
## Güncel sürüm —25 Ekim2026

[**v0.11.0 sonuçları: GitHub’da doğrudan okunabilir Markdown**](raporlar/v0.11.0/README.md) · [Release dosyaları](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/v0.11.0) · [Sürümleme politikası](SURUMLEME.md).

NASA TMR kaynak M6 üreteci ve üç ağ ailesi, SA-neg düz plaka kod karşılaştırması ve kayıtlı kanıt denetçisi eklendi. Yakınsama ve fizik kapıları açık kalıyor; yayın sürümü numarası mühendislik olgunluk puanı değildir. HTML raporları GitHub kaynak görünümünde açılır; görsel HTML görünümü için dağıtımı indirip yerelde açın. Yeni ana sonuçların eşdeğer Markdown özeti ve grafikler yukarıdadır.
'''
    text=text.replace('## Nereden başlanır?',intro+'\n## Nereden başlanır?')
    text+='''
## Yazarlık ve otomasyonun rolü

Proje sahibi hedefleri, kısıtları, araç tercihlerini ve ilerleme sırasını belirledi. Kod, araç bağlantıları, test yürütme, araştırma ve raporların önemli bölümü Codex yardımıyla üretildi. Kayıtlardaki çözümler gerçek yerel program çıktılarıdır; bu durum proje sahibinin bütün programları bağımsız kullanma deneyimi veya ajanın uzmanlığı olarak sunulmaz.

## English summary

A Windows project workflow integrating CAD, aerodynamic/CFD and structural tools with source provenance, raw solver outputs, frozen predictions and acceptance gates. Version0.11.0 adds source-generated NASA TMR ONERA M6 meshes, a three-grid compressible SA-neg flat-plate comparison, and scoped reliability checks. Some local code-comparison screens pass; required iterative convergence and general M6 qualification remain open. Earlier tags are retrospective evidence groups; releases from0.11.0 are genuine incremental updates. Code and reports were developed with substantial Codex assistance. This is neither a flight-ready UAV design nor independently demonstrated expert-agent capability.

## EXE ve lisans durumu

EXE küçük bir Windows başlatıcısıdır. [Kaynak, derleme tarifi ve SHA256](kurulum/EXE_KAYNAK_VE_HASH.md) yayımlanır; paket taşınabilir solver/Python ortamı içermez. Proje sahibi henüz genel bir açık kaynak lisansı seçmedi; üçüncü taraf lisansları [kendi bildirimleriyle](THIRD_PARTY_NOTICES.md) korunur.
'''
    p.write_text(text,encoding='utf-8')
    policy='''# Sürümleme ve yayın politikası

- v0.1.0–v0.10.0 ilk geriye dönük kanıt gruplarıdır. Eski tag, release veya başarısız sonuçlar yeniden yazılmaz.
- v0.11.0 ilk gerçek artımlı güncellemedir. Bundan sonra her anlamlı tamamlanmış değişiklik Git commit’iyle izlenir.
- Yeni yöntem/entegrasyon veya değerlendirme paketi:0.x.0 minor; uyumlu hata/belge düzeltmesi:0.x.y patch. Bu numaralar fiziksel yeterlilik seviyesi değildir.
- Sürüm sorumluluğu bu çalışma için Codex’e verildi. Her yayın VERSION, CHANGELOG, değişen dosya manifesti, sonuçların kapsamı ve bilinen açık kapıları taşır.
- Kaynak/rapor/çizim/küçük loglar Git’e; büyük ham ağ/alan/restartlar hash kontrollü Release ZIP’lerine gider. Kimlik bilgileri, kurulu araçlar, model ağırlıkları ve derleyici paketleri yayımlanmaz.
- Yeni arşivlerde aynı içeriğin tek ZIP üyesini birden çok hedef dosya kullanabilir. Katalog her özgün hedef yolunu/SHA256’yı korur; geri yükleyici bu eşlemeyi denetler. Eski arşiv biçimi de desteklenir.
- Önce katalog, arşivler, gizli bilgi taraması, geri yükleme ve dosya hash’leri denetlenir; sonra normal fast-forward push, değişmez tag ve Release yayımlanır. Zorlayarak push yapılmaz.
- Yazılım/paket testi ile sayısal/deneysel doğrulama ayrı açıklanır. Geçmeyen CFD kapısı, yeni sürüm yayımlanınca geçmiş sayılmaz.
- Bir sonraki yayın: aynı geliştirme klasöründe work/publish altındaki güncel yardımcıları kullan; önceki yayının HEAD ve katalog hash’lerini doğrula. Yerel yayın durumunu GitHub’daki güncel dal/tag/asset durumuyla yeniden karşılaştır.
'''
    (DEST/'SURUMLEME.md').write_text(policy,encoding='utf-8')
    (DEST/'VERSION').write_text(VERSION+'\n',encoding='ascii')
    ch=DEST/'CHANGELOG.md';old=ch.read_text(encoding='utf-8').replace('Geriye dönük gruplandırılmış içe aktarım; gerçek eski Git tarihçesi değildir.','v0.1.0–v0.10.0 geriye dönük içe aktarım; v0.11.0 ve sonrası gerçek artımlı Git değişiklikleridir.')
    entry='''
## v0.11.0 —25 Ekim2026: kaynak CFD teşhisi ve sürümlü güvenilirlik

- Kaynak TMR M6 üreteci/coarsener yerel derleme kayıtları;258048/32256/4032hücreli sistematik aile ve10dondurulmuş native deneme. Minimum fizik kabulü false.
- NASA kaynak düz plaka SA-neg:3264/13056/52224hücre,8native deneme, kaynak Cf/hız/μt kıyası. Kaba yakınsadı; orta/ince iteratif kapılar açık.
- Kontrollü MG, başlangıç aktarımı, LINELET ve ILU denemeleri; desteklenmeyen hipotezler ve son işlem hataları korunur.
- R01–R03 güvenilirlik politikası, L10/L11 kapsamlı hata dersleri ve hash/alan eşlemesi kontrolleri. Yeni LLM davranış iyileşmesi gösterilmedi.
- GitHub’da okunabilir sonuç özeti, EXE kaynak/hash bilgisi, İngilizce özet, yazarlık ve sürümleme politikası.
- Eski tag/yayınlar değişmedi. Yeni büyük dosyalar içerik bazında tekilleştirilmiş, her hedef yola geri yüklenebilir Release arşivlerinde.

'''
    pos=old.index('## v0.1.0');ch.write_text(old[:pos]+entry+old[pos:],encoding='utf-8')
    (DEST/'surumler'/VERSION/'README.md').write_text(f'''# {VERSION} —Kaynak CFD ve güvenilirlik

25Ekim2026 tarihli gerçek artımlı güncelleme; v0.10.0 üstüne eklenir. Bu sürüm fiziksel yeterlilik ilan etmez.

- [GitHub’da okunabilir sonuçlar](../../raporlar/v0.11.0/README.md)
- [Değişen dosyalar ve arşiv manifesti](manifest.json)
- [Tam güncel katalog](../../analizler/dosya_katalogu.json)
- [Sürümleme politikası](../../SURUMLEME.md)
- [Release ve SHA256 dosyaları]({URL_RELEASE})

Kaynak araç/solver kurulumları ve temiz Windows makinede uçtan uca yeniden üretim sınanmış değildir. Yeni geri yükleme kontrolleri yalnız paket/veri bütünlüğü kapsamındadır. Fizik, eşik veya fine rolü sonuçları tutturmak için değiştirilmedi.
'''.replace('{URL_RELEASE}','https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/'+VERSION),encoding='utf-8')
    out=DEST/'raporlar'/VERSION;out.mkdir(parents=True,exist_ok=True)
    lines=['# 25Ekim2026 —CFD ve güvenilirlik sonuçları','','**Genel M6/CFD yeterliliği false.** Yerel testler ve yayın sürümü fiziksel yeterlilikten ayrıdır. Bu özet GitHub’da doğrudan okunur; ayrıntılı HTML, JSON ve CSV özgün uygulama yollarındadır.','',
      '## ONERA M6','','TMR’nin özgün Fortran üreteciyle kaynak keskin firar kenarlı normalize M6 ailesi üretildi. Eski küt firar kenarlı vaka ile geometri/Re/T/SA varyantı aynı değildir; nedensel iyileşme gibi kıyaslanmaz. Kaynak koşullar M0,84/alfa3,06°/Re_root14,6M/T300K; standart SA-neg.','',
      '| Ağ | Hücre | Alan / son geçmiş | log yoğunluk | Cp RMSE,271 nokta | Birleşik kabul |','|---|---:|---:|---:|---:|---|']
    for role,count in [('coarse',4032),('medium',32256),('fine',258048)]:
        r=m6['results'][role];a=r['matched'];lines.append(f"| {role} | {count} | {a['field_iteration']} / {a['terminal_history_iteration']} | {a['rms[Rho]']:.6f} | {r['Cp_RMSE']:.6f} | Geçmedi |")
    lines+=['','İnce çözüm yakınsamadı; GCI=null. MG2 ve kaba→orta ilk tahmin aktarımı dar artık düşüşü ekranını geçti; LINELET geçmedi. Bunlar doğruluk veya süre hızlanması kanıtı değildir. Katıya uzaklık/yüzeye uzaklık karışıklığı analitik küp karşı örneğiyle düzeltildi; önceki hatalı ölçümler korundu.','',
      '![M6 gerçek kaynak ağ](../../uygulama/outputs/projects/proje-e9319baef1/plots/tmr_source_mesh_regions_20261025.png)','',
      '[Tam HTML rapor](../../uygulama/outputs/reports/tmr_m6_kaynak_ve_yontem_20261025.html) · [JSON karşılaştırma](../../uygulama/outputs/projects/proje-e9319baef1/reports/tmr_source_case_review_20261025.json)','',
      '## Düz plaka SA-neg uygulama teşhisi','','NASA TMR kaynak ağları SU2 biçimine koordinatları bit düzeyinde koruyarak çevrildi. M0,2/Re_per_m5M/T300K;2m adyabatik duvar. Kaynak CFD kodları CFL3D/FUN3D’dir; deneysel kıyas değildir.','',
      '| Deneme | Hücre | Alan / son geçmiş | log yoğunluk | Yerel Cf farkı: CFL3D / FUN3D | İteratif kapı |','|---|---:|---:|---:|---:|---|']
    for role,count in [('coarse',3264),('medium',13056),('fine',52224),('fine_nested',52224)]:
        r=plate['results'][role];a=r['field_audit']['matched'];errs=' / '.join(f"%{s['Cf_relative_difference_same_grid']*100:.4f}" for s in r['same_grid_reference'])
        lines.append(f"| {role} | {count} | {a['field_iteration']} / {a['terminal_history_iteration']} | {a['rms[Rho]']:.6f} | {errs} | {'Geçti' if r['field_audit']['iterative_gate'] else 'Geçmedi'} |")
    lines+=['','Yerel Cf aynı kaynak hücre sayısıyla kıyaslandı. Kaynak en ince ağın Cf eğrisi, iki hız ve μt profili ekranları yakın olsa da orta/ince yakınsaması yok. Kaba ağın geçmesi aile kabulü değildir. Boyutlu gaz/Sutherland sabitlerinin bütün kaynak kodlarla tam özdeşliği ayrıca kurulmuş değildir.','',
      '![Düz plaka kaynak kıyası](../../uygulama/outputs/plots/flatplate_reference_comparison_20261025.png)','',
      'ILU aynı checkpointle yalnız0,055log ek düşüş sağladı, önceden kayıtlı0,3eşiğini geçmedi. Orta→ince pozitif başlangıç aktarımı400adımda2,57747log ek yoğunluk düşüşü verdi; son iteratif kabul yine geçmedi. Daha iyi referans uyumu nedeniyle ana fine rolü değiştirilmedi.','',
      'Hız örneklemev2, iki native sütun arasında tam istenen x’de interpolasyon yapar; en yakın sütunla eski48son işlem dosyası korunur. Kaynak metnindeki2e−12m yuvarlamanın eğrilik olduğu teşhisi çürütülüp kayıtta tutuldu. Üç hatalı aktarım taslağı native öncesi reddedildi.','',
      '[Tam HTML rapor](../../uygulama/outputs/reports/cfd_duz_plaka_ve_m6_20261025.html) · [Tüm sayısal farklar](../../uygulama/outputs/reports/flatplate_comparison_20261025.json) · [230 hash kaydı denetimi](../../uygulama/outputs/reports/flatplate_integrity_20261025.json)','',
      '## Güvenilirlik ve ajan kapsamı','','- R01: sarmalayıcı hatasında aynı native işi ikinci kez başlatmadan PID/yol/oluşturma zamanı ve gerçek çıkış koduyla kurtarma.','- R02: yerel Hessian prototipinde hücre/şablon desteği, koşul ve iki ölçek tutarlılığı. Tam anizotropik remesher/adjoint/hata bandı değildir.','- R03: tek değişkenli neden sınaması; önceden seçilen etki yoksa gerekçesiz değer taraması yapmama.','- L10: standart SA-neg config bağımlılığı. L11: katıya uzaklığı yüzey eşdeğerliği saymama.8/8 araç ve39/39 kayıt kontrolleri; yeni LLM davranışı/uzmanlık kanıtı değildir.','',
      '[Güvenilirlik kaynak ve yöntem açıklaması](../../uygulama/work/reliability/README.md) · [Literatür araştırması](../../uygulama/outputs/reports/cfd_dogrulugu_literatur_20261025.html)','',
      '## Sıradaki kayıtlı iş','','Aynı ince başlangıçla adaptasyon kapalı sabitCFL100/10 karşılaştırması hazır, **henüz çalıştırılmadı**.400adım/240s sınırı, yoğunlukta≥0,3log kazanç ve SA kötüleşmeme ölçütü korunur. [Sözleşme](../../uygulama/outputs/simulations/flatplate_SAneg_20261025_v1/next_numerical_control_not_run.json).','',
      '## Kaynaklar','','[NASA TMR M6 ağları](https://tmbwg.github.io/turbmodels/onerawingnumerics_grids.html) · [TMR SA-neg kıyası](https://tmbwg.github.io/turbmodels/onerawingnumerics_val_sa.html) · [TMR düz plaka](https://tmbwg.github.io/turbmodels/flatplate.html) · [TMR düz plaka SA sonuçları](https://tmbwg.github.io/turbmodels/flatplate_sa.html)','']
    (out/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    for category in ['raporlar','testler','cizimler']:
        p=DEST/category/'README.md';content=p.read_text(encoding='utf-8')
        if category=='raporlar':content+='\n- [v0.11.0 —GitHub’da okunabilir güncel CFD ve güvenilirlik sonuçları](v0.11.0/README.md)\n'
        else:
            subset=[r for r in plan['changed'] if r['storage']=='git' and ((category=='testler' and any(v in r['source_path'] for v in ['audit','guard','qualification','protocol','test_'])) or (category=='cizimler' and r['source_path'].lower().endswith(('.step','.stp','.svg','.fcstd'))))]
            d=DEST/category/VERSION;d.mkdir(exist_ok=True,parents=True)
            (d/'README.md').write_text('# '+VERSION+'\n\n'+ '\n'.join(f"- [{r['source_path']}](../../{r['repository_path']})" for r in subset)+'\n',encoding='utf-8')
            content+='\n- [v0.11.0](v0.11.0/README.md)\n'
        p.write_text(content,encoding='utf-8')
    exe=ROOT/'outputs/Muhendislik-Merkezi.exe';build=ROOT/'work/setup/build_launcher.ps1'
    (DEST/'kurulum/EXE_KAYNAK_VE_HASH.md').write_text(f'''# EXE kaynak ve hash

- Kaynak: [Launcher.cs](../uygulama/work/agent/Launcher.cs)
- Derleme tarifi: [build_launcher.ps1](../uygulama/work/setup/build_launcher.ps1)
- EXE: [Muhendislik-Merkezi.exe](../uygulama/outputs/Muhendislik-Merkezi.exe),{exe.stat().st_size}bayt
- SHA256: `{digest(exe)}`
- Kaynak SHA256: `{digest(ROOT/'work/agent/Launcher.cs')}`

Bu sürümde mevcut başlatıcı yeniden derlenmedi; kaynak ve mevcut ikili dosyanın hash’i belgelenmiştir. Kod imzası/kimlik doğrulaması iddiası yoktur. Hash bütünlük kontrolüdür. Python ve solver/CAD ortamları ayrıca gerekir. Mevcut derleme betiği geliştirme ortamındaki Windows .NET Framework C# derleyicisini kullanır; sistem genelinde ayar değiştirmez.
''',encoding='utf-8')
    p=DEST/'AGENTS.md';text=p.read_text(encoding='utf-8').replace('`surumler/` geriye dönük kanıt gruplarıdır','`surumler/v0.1.0`–`v0.10.0` geriye dönük kanıt gruplarıdır; v0.11.0 ve sonrası gerçek artımlı sürümlerdir')
    text+='\nYayın güncellemelerinde SURUMLEME.md politikasını uygula. Kullanıcı sürüm seçimini Codex’e devretti; olağan sürüm numarası için tekrar soru sorma. Eski tag/Release varlıklarını değiştirme; yeni dosya/sonuçları güncel manifest ve ayrı sürümle yayımla.\n';p.write_text(text,encoding='utf-8')
    notes='''# v0.11.0 —Kaynak CFD teşhisi ve güvenilirlik

25Ekim2026. İlk gerçek artımlı sürüm; önceki0.1–0.10etiketleri korunmuştur.

- Kaynak TMR M6 üreteci, üç ağ ve10native deneme; fizik kabulü açık.
- NASA kaynak düz plaka SA-neg, üç ağ ve8native deneme; yerel kod uyumu iyi, orta/ince yakınsaması açık.
- Kapsamlı güvenilirlik politikası ve hata dersleri; LLM uzmanlık/iyileşmesi gösterilmedi.
- GitHub’da okunabilir Markdown sonuçlar, grafikler, yazarlık/İngilizce özet ve EXE kaynak/hash bilgisi.
- SHA256 kontrollü ham analiz arşivleri; aynı içerik birden çok özgün hedef yola katalogla geri yüklenir. Eski arşivler desteklenir.

Temiz makinede solver kurulumu veya yeni CFD yeniden üretimi bu yayın testinin kapsamı değildir. Başarısız denemeler korunur; eşikler gevşetilmez.
'''
    (RUN/'release-notes.md').write_text(notes,encoding='utf-8')
    print('Release documents and GitHub-readable numerical summary prepared')

if __name__=='__main__':
    URL_RELEASE='https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/'+VERSION
    main()
