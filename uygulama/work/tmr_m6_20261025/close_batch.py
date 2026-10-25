"""Close the finite source-mesh study without closing physical qualification."""
from common import ROOT,BASE,PROJECT,CASE,TASK,read,save,sha,now
from pathlib import Path
import hashlib,html,os,re,shutil

def streamsha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def href(p):return os.path.relpath(p,ROOT/'outputs/reports').replace('\\','/')
def link(p,label):return f'<a href="{html.escape(href(p))}">{html.escape(label)}</a>'
def table(headers,rows):return '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def num(x,n=5):return f'{x:.{n}g}'

def main():
    dest=ROOT/'outputs/reports/tmr_m6_kaynak_ve_yontem_20261025.html'
    assert not (PROJECT/'reports/tmr_source_batch_closed_20261025.json').exists()
    review=read(PROJECT/'reports/tmr_source_case_review_20261025.json');mesh=read(PROJECT/'reports/tmr_mesh_family_20261025.json')
    cad=read(PROJECT/'reports/tmr_source_CAD_boundary_v2_20261025.json')
    mg=read(PROJECT/'reports/tmr_MG_control_20261025.json');nested=read(PROJECT/'reports/tmr_nested_initialization_20261025.json');line=read(PROJECT/'reports/tmr_linelet_control_20261025.json')
    audits=[]
    for p in sorted(CASE.rglob('prediction_frozen.json')):
        seal=read(p);files=seal['files_sha256'];bad=[rel for rel,h in files.items() if not (ROOT/rel).is_file() or streamsha(ROOT/rel)!=h]
        assert not bad,(p,bad)
        audits.append({'seal':str(p.relative_to(ROOT)),'seal_sha256':sha(p),'checked_files':len(files),'mismatches':bad})
    task=read(TASK);unchanged={p:sha(ROOT/p)==h for p,h in task['input_sha256'].items()};assert all(unchanged.values())
    integrity={'created_utc':now(),'prediction_seals':audits,'checked_file_records':sum(x['checked_files'] for x in audits),
       'registered_project_inputs_unchanged':unchanged,'all_passed':True,'physical_qualification_passed':False,
       'script_sha256':{str(p.relative_to(ROOT)):sha(p) for p in BASE.glob('*.py')}}
    save(PROJECT/'reports/tmr_integrity_20261025.json',integrity)
    manifest=[]
    for p in sorted((BASE/'sources').iterdir()):
        if p.is_file():manifest.append({'file':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
    save(BASE/'sources_current_inventory.json',{'created_utc':now(),'files':manifest,'original_URL_records':'sources/case_sources_manifest.json; earlier research and compiler manifests retain retrieval provenance'})
    rows=[]
    for role,label,level in [('coarse','Kaba',3),('medium','Orta',2),('fine','İnce',1)]:
        r=review['results'][role];m=r['matched'];me=next(x for x in mesh['levels'] if x['level']==level)
        rows.append([label,f"{me['cells']:,}",f"{m['field_iteration']} / {m['terminal_history_iteration']}",num(m['CL']),num(m['CD']),num(m['rms[Rho]']),num(m['CL_last100_range']),num(m['CD_last100_range']),num(r['max_yplus']),num(r['Cp_RMSE']),f"{r['section_screens_passed']}/14",'Geçmedi'])
    sections=[f'<h1>TMR M6: kaynak ağ ve yöntem sınaması</h1><p class="date">25 Ekim 2026 · gerçek native SU2 8.5.0 · kaynak geometri</p>',
      '<p class="callout">Kaynak üreteç, üç ağ ve kontrollü yöntemler çalıştırıldı. Asgari fizik kabulü <b>false</b>. İnce çözüm yakınsamadı; doğruluk iyileşmesi veya güvenilir CFD hata bandı gösterilmedi.</p>',
      '<h2>Bu paket neyi değiştirdi?</h2><p>NASA/TMR’nin özgün Fortran üreteci değiştirilmeden yerel derlendi. Kaynak keskin firar kenarlı M6 geometrisiyle aynı 100c dış sınırda iç içe üç ağ üretildi. Bu ayrı vaka önceki küt firar kenarlı M6’nın devamı değildir: geometri, Reynolds tanımı, sıcaklık ve SA varyantı farklıdır. Eski ve yeni deney hatalarını tek ayarın etkisi gibi kıyaslamıyoruz.</p>',
      '<p>Taşınabilir GNU Fortran 16.2.0: 84,3 MiB indirme, yaklaşık 525 MiB kurulum. Paket SHA256 değerleri resmî MSYS2 veri tabanıyla eşleşti. Global PATH değiştirilmedi. Üreteç ve coarsener gerçekten çalıştırıldı; bu bir CAD çizimi veya genel yeni CAD ağ hizmeti değildir.</p>',
      '<h2>Fizik ve önceden kayıtlı kabul</h2><p>M=0,84; alfa=3,06°; Re/kök veter=14,6 milyon; normalize kök veter=1 m; T=300 K. Standart SA-neg: NEGATIVE, WITHFT2; ν̃∞=3ν∞. Kaynak yarım kanat alanı 1,153150841 m², MAC 0,801672959 m. Adyabatik duvar, kök simetri, sıkıştırılabilir 3B RANS. TMR sayısal vaka M=0,84 ile ham deney başlığındaki 0,8395 ayrımı korunur.</p>',
      '<p>Kabul: yoğunluk log artık &lt;−7; son100 CL aralığı &lt;10⁻⁴, CD aralığı &lt;10⁻⁵; max y+&lt;1; 14 kesit/yüzey grubunun tamamında Cp RMSE&lt;0,08; üç yakınsamış sistematik ağ, bölgesel BL/TE/uç/iz, ayrı uzak alan ve bağımsız kuvvet kontrolü. Koşul veya eşik sonuçlara göre gevşetilmedi.</p>',
      '<h2>Gerçek sonuçlar</h2>'+table(['Ağ','Hücre','Alan / son geçmiş adımı','CL','CD','log yoğunluk artığı','ΔCL son100','ΔCD son100','max y+','Cp RMSE','Kesit ekranı','Birleşik kabul'],rows),
      '<p>Kaba 4000 adımı tamamladı. Orta 600 s, ince 1500 s bütçesinde durduruldu. İnce geçmişin 663. satırı alan600 ile; orta2539 satırı alan2400 ile karıştırılmadı. Tabloda alanın gerçek iterasyonu kullanılır. İncenin deney hatası daha büyük: yakınsamamış çözümden ağ yakınsaması/GCI çıkarılamaz. Önceden seçilmiş ince rol, daha iyi görünen orta ile değiştirilmedi.</p>',
      f'<img src="{href(PROJECT/"plots/tmr_Cp_comparison_20261025.png")}" alt="Yedi kesitte kaynak deney, CFL3D ve native Cp sonuçları"><p class="caption">271 ONERA deney noktası korundu. CFL3D ayrı sayısal referanstır. Grafikteki ±0,02 çubuklar görsel karşılaştırma bandıdır; burada ölçüm belirsizliği olarak doğrulanmış değildir. Alt/üst bütün noktalar CSV’de tutulur.</p>',
      '<h2>Üç ayırt edici yöntem deneyi</h2>'+table(['Deney','Sabit tutulanlar / değişen','Önceden belirlenen etki','Gözlenen','Yorum'],[
        ['MGLEVEL 0→2','Kaba ağ, fizik ve uniform başlangıç; multigrid paketi açıldı','1000 adımda ≥0,3 ek log artık düşüşü',num(mg['additional_log10_reduction']),'Dar sayısal etki geçti; hızlanma/doğruluk değil'],
        ['Kaba→orta başlangıç aktarımı','Kaynak coarsener NC ağırlıklarıyla pozitif konservatif durum interpolasyonu','1000 adımda ≥0,3 ek log düşüş',num(nested['additional_density_log10_reduction']),'Dar etki geçti; toplam korunumlu transfer veya yakınsama kanıtı değil'],
        ['LU_SGS→LINELET','Aynı orta checkpoint2400; 200 adım; yalnız önkoşullayıcı','≥0,3 log kazanç / Krylov oranı≤0,8',f"{num(line['additional_density_log10_reduction'])} log; Krylov×{num(line['Krylov_iteration_ratio'])}",'İki etki de geçmedi; daha çok değer taranmadı']]),
      '<p>NC operatörlerinde pozitif ağırlık, sabit alanı koruma ve ortak düğümlerin bit eşleşmesi sınandı; density/iç enerji pozitif kaldı. Aynı anda yürüyen denemeler nedeniyle sürelerden hız kazancı iddiası yok. MG, iç kaba-akı ve smoother politikasını da açar; bunu yalnız tek skaler fizik değişikliği diye sunmuyoruz.</p>',
      '<h2>Ağ yalnız hücre sayısı değildir</h2><p>258048 / 32256 / 4032 hücre; kaba düğümler incenin tam altkümesi. Pozitif örneklenmiş hex Jacobianları, exact minimum referans prizma Jacobianı, sınırın tek akış komşusuyla tam eşleşmesi denetlendi. Hex kontrolü 27 noktadır; tüm hücre içinde analitik pozitiflik kanıtı değildir. Kesit ve hücum/firar/uç görünümleri gerçek hacim ağındandır.</p>',
      f'<img src="{href(PROJECT/"plots/tmr_source_mesh_regions_20261025.png")}" alt="Gerçek kaynak ağın bölgesel kesitleri">',
      '<p>Kaynak “BL” etiketi ince/orta/kabada58/29/14 katmandır; gerçek δ99 değildir. İlk y+ düşük olsa da BL/iz/uç çözünürlüğü kabulü açık. Bölgesel ilk aralıklar, büyüme ve katman uzunlukları ayrıntılı JSON’dadır. Kaynak üretecin ilk32-radyal hücreli denemesi dosya üretmediği halde exit0 verdi; dosya kontrolü yakaladı. İlk393216 hücreli aile kaynak bütçesini aştı, korundu ve CFD’ye verilmedi.</p>',
      '<h2>CAD eşdeğerliği ve yakalanan ölçüm hatası</h2><p>İlk mesafe denetiminde katıya uzaklık kullanıldı. İçerideki noktanın uzaklığının sıfır olması yüzeyde bulunduğunu göstermez. Eski iki rapor yüzey metriği için geçersiz olarak saklandı. Birim küp merkezinin katıya0 / yüzey sınırına0,5 uzaklığıyla karşı örnek sınandı; düzeltilen ölçüm yalnız CAD sınır yüzlerine yapılır. CFD alanı veya kaynak ağ değişmedi.</p>'+table(['Ağ','Sınır örnekleri: maksimum uzaklık / kök veter'],[[{3:'Kaba',2:'Orta',1:'İnce'}[r['level']],num(r['all_samples']['max'])] for r in cad['levels']]),
      '<p>Düğüm, yüz merkezi ve kenar ortası örneklenir; bu sonlu örnekleme tam Hausdorff sınırı değildir. Kaynak analitik ağ ile sağlanan STEP’in tam yüzey eşdeğerliği kanıtlandı diye sunulmaz.</p>',
      '<h2>Alan ve kuvvet denetimleri</h2><p>Üç kuvvet integrasyonu korunur: eski üçgene bölme, bilineer Gauss ve düğüm-dual normal yöntemi. Dörtgen nodal basıncını köşegene bölmek farklı ağırlık verdiği için eski yöntem yanlıydı; analitik dörtgen testi bunu yakaladı. İnce bilineer yöntemde CL/CD farkı %0,1558/%0,0348; native-benzeri düğüm-dual yöntemde %0,2560/%0,1129. Yakın integrasyon, yakınsamayı veya deney doğruluğunu kanıtlamaz.</p>',
      '<p>Her ağda16 doğrudan native düğüm hız/türbülans profili, geçerli örnek maskeleri ve üç Ue dış penceresi CSV’ye yazıldı. İstenen ve gerçekleşen eta/x konumları ayrı kaydedilir; kaba ağda eta0,2 isteği kökte örneklenebilir. Bu profili eta0,2’de çözülmüş kabul etmeyin. Radial s/c ve operasyonel δ99 tam3B sınır tabakası kabulü değildir. VTU Residual_* alanı da PDE/history artığıyla özdeş varsayılmadı.</p>',
      '<h2>Talimat, erişim ve kanıt durumu</h2><p>L10: standart SA-neg için WITHFT2 zorunluluğu, native reddedilmiş ve başarılı iki config ile sınandı. L11: katı/yüzey mesafe farkı analitik karşı örnekle eklendi. 8/8 yeni araç kontrolü ve39/39 mevcut ajan kayıt kontrolü geçti. Bunlar yeni LLM davranışında iyileşme veya uzmanlık kanıtı değildir.</p>',
      '<p>Bu geliştirme kör deney değildir. Önceki M6 sonuçları biliniyordu.24Ekim22:58:19UTC’de yalnız metadata amaçlı bir filtre yorum satırındaki sayısal CFD kuvvetlerini yanlışlıkla gösterdi; ince sabit-config koşusu sürüyordu. Sonrasında çözücü ayarı/eşik değiştirilmedi. Ayrıntılı erişim açıklaması değerlendirme defterindedir.</p>',
      f'<p>{len(audits)} tahmin mühründeki {integrity["checked_file_records"]} dosya kaydı yeniden SHA256 ile doğrulandı. Kayıtlı proje girdileri aynı kaldı. Tamamlanan, bu sınırlı araştırma ve deneme paketidir; fiziksel yeterlilik değildir.</p>',
      '<h2>Dosyalar</h2><ul>']
    files=[PROJECT/'reports/tmr_source_case_review_20261025.json',PROJECT/'reports/tmr_mesh_family_20261025.json',PROJECT/'reports/tmr_source_CAD_boundary_v2_20261025.json',PROJECT/'reports/tmr_integrity_20261025.json',PROJECT/'reports/tmr_MG_control_20261025.json',PROJECT/'reports/tmr_nested_initialization_20261025.json',PROJECT/'reports/tmr_linelet_control_20261025.json',CASE/'contract.json',ROOT/'work/setup/tmr_m6_install.json',BASE/'sources_current_inventory.json',ROOT/'outputs/data/agent_learning/reviewer_ledger_tmr_surface_20261025.json']
    for role in ['coarse','medium','fine']:
        files.extend([PROJECT/f'reports/tmr_{role}_field_checks_v3_20261025.json',PROJECT/f'data/tmr_sharp_20261025_v1/{role}/experiment_comparison.csv',CASE/f'flow_v2_{role}/prediction_frozen.json'])
    sections.extend('<li>'+link(p,p.name)+'</li>' for p in files);sections.append('</ul>')
    sections.append('<h2>Kaynaklar ve sonraki teşhis</h2><p><a href="https://tmbwg.github.io/turbmodels/onerawingnumerics_grids.html">TMR özgün ağ üreteci</a> · <a href="https://tmbwg.github.io/turbmodels/onerawingnumerics_val_sa.html">TMR SA-neg sayısal karşılaştırması</a> · <a href="https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/">SU2 doğrusal yöntemler</a>.</p><p>Sonraki sınırlı iş: NASA TMR düz plakada aynı SA-neg uygulamasını kaynak ağlar ve bağımsız Cf/profillerle kontrol etmek. Amaç şok/3B etkisinden bağımsız duvar-türbülans yolunu sınamak. Düz plaka başarısı M6’yı tamamlamaz; başarısızlığı da kanıt olmadan tek nedene bağlanmaz.</p>')
    css='body{font:16px/1.65 Segoe UI,sans-serif;margin:40px auto;max-width:1250px;color:#233044;padding:0 22px}h1,h2{line-height:1.25}h2{margin-top:38px}.date,.caption{color:#637386}.callout{background:#fff1dc;border-left:5px solid #d18422;padding:18px}table{border-collapse:collapse;font-size:13px;display:block;overflow:auto}td,th{border:1px solid #d8e1e8;padding:9px;text-align:left}th{background:#edf3f6}img{max-width:100%;border:1px solid #dde5eb}a{color:#116c93}'
    body=''.join(sections);dest.write_text('<!doctype html><html lang="tr"><meta charset="utf-8"><title>TMR M6 kaynak sınaması</title><style>'+css+'</style>'+body+'</html>',encoding='utf-8')
    links=[]
    for rel in re.findall(r'(?:href|src)="([^"#]+)"',body):
        if '://' not in rel:
            p=(dest.parent/rel).resolve();assert p.exists(),p;links.append(str(p.relative_to(ROOT)))
    md=ROOT/'outputs/reports/tmr_m6_kaynak_ve_yontem_20261025.md'
    md.write_text('# TMR M6 kaynak ve yöntem sınaması —25 Ekim\n\nAsgari fizik kabulü false. Ayrıntılı tablolar, grafikler, başarısız denemeler ve kanıtlar: [HTML](tmr_m6_kaynak_ve_yontem_20261025.html).\n\n'+ '\n'.join(f'- {r[0]}: {r[1]} hücre, alan/son geçmiş {r[2]}, CpRMSE {r[9]}; birleşik kabul geçmedi.' for r in rows)+'\n\nMG ve kaba→orta başlangıç yalnız dar artık düşüşünü iyileştirdi; LINELET etkisi geçmedi. İnce çözüm yakınsamadığı için GCI ve fiziksel doğruluk iyileşmesi iddiası yok.\n',encoding='utf-8')
    state=ROOT/'PROJECT_STATE.md'
    with state.open('a',encoding='utf-8') as f:
        f.write('\n\n## 25 Ekim: TMR kaynak M6 ağları ve üç kontrollü yöntem\n\n- Görev20261025-011533-2114a3 sınırlı kaynak/deneme/rapor kapsamıyla kapandı; minimum fizik kabulü false. Rapor outputs/reports/tmr_m6_kaynak_ve_yontem_20261025.html. Özgün Fortran5.0 üreteci/coarsener3.9 taşınabilir GNU Fortran16.2 ile değiştirilmeden derlendi. Kaynak sharp-TE normalize M6:258048/32256/4032hücre; aynı100c dış sınır. Eski blunt M6 ile aynı fizik vakası değildir.\n- Gerçek native SA-neg standardı NEGATIVE,WITHFT2;M0,84/alfa3,06/Re_root14,6M/T300K. Kaba4000adım tamamlandı; orta600s/ince1500s süre bütçesinde durdu. Son tam alan/son geçmiş2400/2539 ve600/663 ayrı tutuldu. Tüm271 noktada CpRMSE kaba0,28988/orta0,15348/ince0,31158. Hiçbir iteratif kapı geçmedi, GCI null; fine rolü daha iyi görünen orta ile değiştirilmedi.\n- MG2 kaba1000adımda+0,42699log, kaynak NC interpolasyonuyla kaba→orta başlangıç+0,81136log ek yoğunluk düşüşü verdi. Aynı orta seedle200adım LINELET testi−0,15301log ve Krylov×1,5442 ile iki etkiyi geçmedi. Bunlar yakınsama/doğruluk veya süre hızlanması kanıtı değildir.\n- Katıya mesafe ile yüzeye mesafe karıştırılan ilk CAD denetimleri geçersiz olarak korundu. Birim küp karşı örneği ve boundary-face compound ile v2 düzeltildi; max örnek uzaklığı/c kaba0,0052693/orta0,0022519/ince0,0009781. Sonlu örnekleme tam Hausdorff sınırı değildir; kaynak ağ/alan değişmedi. L10 SA-neg native config ve L11 yüzey-mesafe dersleri operasyonel talimata eklendi;8/8 ve39/39 kod kontrolleri geçti, yeni LLM davranış iyileşmesi ölçülmedi.\n-10tahmin mührü yeniden doğrulandı. Eski/başarısız denemeler, üç kuvvet integrasyonu ve konumları gerçek kaydedilmiş16normal profil/ağ korundu. Kaynak sayısal kuvvetler deney değildir; bu geliştirme kör değildir. Sıradaki ayrı teşhis NASA TMR düz plaka SA-neg kontrolüdür. Önceki M6/RAE/VLM açık kapıları kapanmaz.\n')
    closure={'closed_utc':now(),'status':'bounded_test_batch_complete','minimum_physical_qualification_passed':False,
        'report':str(dest.relative_to(ROOT)),'report_sha256':sha(dest),'integrity_sha256':sha(PROJECT/'reports/tmr_integrity_20261025.json'),
        'local_links_checked':len(links),'open_gates':review['open_gates'],'next_case':'NASA TMR flatplate SA-neg verification'}
    save(PROJECT/'reports/tmr_source_batch_closed_20261025.json',closure)
    evidence=files+[dest,md,PROJECT/'reports/tmr_source_batch_closed_20261025.json']
    archive=ROOT/'outputs/data/task_evidence'/task['id'];archive.mkdir(exist_ok=True,parents=True)
    records=[]
    for k,p in enumerate(evidence):
        out=archive/(f'{k:02d}_'+p.name);shutil.copyfile(p,out);records.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'archived':str(out.relative_to(ROOT))})
    task.update(status='tamamlandı',phase='sınırlı kaynak ve yöntem denemesi kapandı',completed_utc=now(),evidence=records,
        result_scope='Bounded integration and diagnostic batch; physical qualification false',minimum_physical_qualification_passed=False,open_engineering_checks=review['open_gates'])
    save(TASK,task)
    print({'report':str(dest),'prediction_seals':len(audits),'file_records':integrity['checked_file_records'],'links':len(links)})

if __name__=='__main__':main()
