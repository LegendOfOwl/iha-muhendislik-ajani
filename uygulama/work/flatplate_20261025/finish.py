from prepare import ROOT,BASE,CASE,read,save,sha,now
from run import history
import os,html,re,hashlib,shutil

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rel(p):return os.path.relpath(p,ROOT/'outputs/reports').replace('\\','/')
def link(p,text=None):return f'<a href="{html.escape(rel(p))}">{html.escape(text or p.name)}</a>'
def table(headers,rows):return '<table><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</table>'
def pct(x):return 'null' if x is None else f'%{100*x:.4f}'

def main():
    dest=ROOT/'outputs/reports/cfd_duz_plaka_ve_m6_20261025.html';report=read(ROOT/'outputs/reports/flatplate_comparison_20261025.json');contract=read(CASE/'contract.json')
    assert not (CASE/'batch_closed.json').exists()
    taskpath=ROOT/read(BASE/'task.json')['path'];task=read(taskpath)
    integrity=[];runtime=[];matched_residuals={}
    for p in sorted(CASE.rglob('prediction_frozen.json')):
        s=read(p);bad=[r for r,h in s['files_sha256'].items() if not (ROOT/r).is_file() or digest(ROOT/r)!=h];assert not bad,(p,bad)
        integrity.append({'seal':str(p.relative_to(ROOT)),'sha256':sha(p),'files_checked':len(s['files_sha256']),'mismatches':bad})
        status=s.get('native_status',s.get('result',{}).get('native'));assert status
        runtime.append({'case':str(p.parent.relative_to(CASE)),'exit_code':status['exit_code'],'stop_reason':status['stop_reason'],'seconds':status['seconds']})
    unchanged={r:sha(ROOT/r)==h for r,h in task['input_sha256'].items()};assert all(unchanged.values())
    for role,v in report['results'].items():
        matched=v['field_audit']['matched'];row=next(r for r in history(CASE/role) if r['Inner_Iter']==matched['field_iteration'])
        matched_residuals[role]={k:v for k,v in row.items() if k.startswith('rms[')}
    quality={'checked_utc':now(),'predictions':integrity,'file_records':sum(x['files_checked'] for x in integrity),'runtime':runtime,
        'registered_project_inputs_unchanged':unchanged,'selected_all_RMS_history':matched_residuals,
        'all_integrity_checks_passed':True,'scoped_implementation_qualification_passed':False,'M6_qualification_passed':False,
        'comparison_guard_checks':report['guard_checks']}
    qpath=ROOT/'outputs/reports/flatplate_integrity_20261025.json';save(qpath,quality)
    nextplan={'created_utc':now(),'status':'prepared_not_run','scope':'Distinguish nonlinear pseudo-time step aggressiveness; not a reference-target fit',
        'source':'https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/',
        'observation':'Fine histories show repeated transient residual growth while adaptive CFL is at or above100. Correlation only; ILU matched-seed test did not meet effect.',
        'seed':str((CASE/'fine_nested/restart_flow_000800.dat').relative_to(ROOT)),'seed_sha256':sha(CASE/'fine_nested/restart_flow_000800.dat'),
        'mesh':str((CASE/'meshes/fine.su2').relative_to(ROOT)),'mesh_sha256':sha(CASE/'meshes/fine.su2'),
        'pair':{'A':'fixed CFL100, adaptation off','B':'fixed CFL10, adaptation off'},'only_paired_difference':'CFL_NUMBER100 versus10; same fixed policy, seed, numerics and physics',
        'iterations_each':400,'max_seconds_each':240,'threads_each':4,
        'preselected_comparison_iteration':399,'effect':'B density log10 at least0.3 lower than A; SA residual must not be worse by more than0.1log. No physical acceptance inferred.',
        'no_automatic_sweep_or_further_extension':True,'existing_acceptance_thresholds_unchanged':True}
    save(CASE/'next_numerical_control_not_run.json',nextplan)
    ledger={'created_utc':now(),'instruction_version':task['agent_instruction_snapshot']['version'],
        'events':[{'type':'hypothesis_not_supported','id':'flatplate_ILU','evidence':'outputs/reports/flatplate_ILU_control_20261025.json','result':'Gain0.0550645log <0.3; high-CFL linear solver explanation not established. Do not generalize ILU as bad.'},
          {'type':'prevented_failure','id':'transfer_support','evidence':str((CASE/'nested_seed/support_check_v4.json').relative_to(ROOT)),
           'observation':'Exact tensor, index-selected parent and VTK negative-weight guards rejected three drafts before native execution.',
           'disproven_diagnosis':'Source grid is curvilinear was incorrect; measured x/y differences4.76e-17/2.00e-12m are ASCII rounding.',
           'correction':'Initial-state only tensor interpolation with measured coordinate reproduction2e-12m, exact shared-node states, positive weights and no physical clipping. Native mesh unchanged.'},
          {'type':'confirmed_postprocessing_limitation','id':'nearest_profile','evidence':str((BASE/'postprocessing_v1_nearest/manifest.json').relative_to(ROOT)),
           'correction':'Preserve48v1 files; interpolate between two native columns to requested x. Both coordinate/value masks required; compare again. CFD fields and force histories unchanged.'},
          {'type':'scoped_numerical_effect','id':'nested_fine','result':report['nested_initialization_effect'],'not_physical_validation':True}],
        'new_LLM_behaviour_evaluation':False,'new_prompt_lesson_needed':'No duplicate lesson added: existing support/validity, raw-field matching and single-variable rules cover these cases.',
        'reference_manifest_sha256':sha(BASE/'sources/reference_manifest.json'),'not_blind':True}
    ledgerpath=ROOT/'outputs/data/agent_learning/reviewer_ledger_flatplate_20261025.json';save(ledgerpath,ledger)
    rows=[];profiles=[]
    for role,label in [('coarse','Kaba'),('medium','Orta'),('fine','İnce / uniform'),('fine_nested','İnce / aktarılmış başlangıç')]:
        r=report['results'][role];a=r['field_audit'];m=a['matched'];meshrole='fine' if role=='fine_nested' else role
        rows.append([label,f"{contract['levels'][meshrole]['cells']:,}",f"{m['field_iteration']} / {m['terminal_history_iteration']}",f"{m['rms[Rho]']:.6f}",f"{m['rms[nu]']:.6f}",f"{m['CD_last100_range']:.3g}",f"{a['max_yplus']:.5f}",'Geçti' if a['iterative_gate'] else 'Geçmedi'])
        profiles.append([label,' / '.join(pct(s['Cf_relative_difference_same_grid']) for s in r['same_grid_reference']),
            ' / '.join(pct(s['relative_L2_window']) for s in r['curve_errors']),
            ' / '.join(pct(s['relative_L2']) for s in r['velocity_errors']),
            ' / '.join(pct(s['relative_L2']) for s in r['eddy_viscosity_errors'])])
    mg_link=ROOT/'outputs/reports/tmr_m6_kaynak_ve_yontem_20261025.html'
    body=['<h1>CFD güvenilirliği: düz plaka ve M6 sonuçları</h1><p class="muted">25 Ekim2026 · gerçek SU2 8.5.0 çözümleri · kaynak ağlar</p>',
      '<p class="callout"><b>Yerel kaynak kıyası iyi, bütün aile kabulü açık.</b> Düz plakada sürtünme ve profiller CFL3D/FUN3D ile yakın. Kaba ağ yakınsadı; orta ve iki ince deneme zorunlu iteratif kapıları geçmedi. Genel CFD, M6 veya uçak yeterliliği <b>false</b> kalıyor.</p>',
      '<p>'+link(mg_link,'Önceki TMR M6 kaynak ağ/yöntem paketinin ayrıntılı raporu')+' kapatıldı:10 tahmin mührü ve348 dosya kaydı doğrulandı. Bu rapor onun ardından tamamlanan daha hafif SA uygulama teşhisidir.</p>',
      '<h2>Neden bu test?</h2><p><a href="https://tmbwg.github.io/turbmodels/flatplate.html">NASA TMR VERIF/2DZP</a>, türbülans modelinin uygulanışını farklı kodlarla kıyaslamak için kaynak ağ ve sonuçlar sağlar. Şok ve3B kanat etkilerini içermeyen bu akış, M6 teşhisini daraltır. Bu sayfada kullanılan sonuçlar deney değil, bağımsız CFL3D/FUN3D hesaplarıdır; fiziksel modelin deneysel doğruluğunu tek başına sınamaz.</p>',
      '<h2>Girdi ve kaynak</h2><p>Kaynak NASA arşivinden69×49 /137×97 /273×193 düğüm ağları indirildi. Kaynak koordinatlar SU2 biçimine17 basamakla çevrildi ve geri okunduğunda bit düzeyinde korundu. İnce→orta→kaba koordinat altkümeleri tam eşleşti; pozitif dörtgen köşe Jacobianları, tek akış komşusu ve sınır kenarları denetlendi. Kaynak çizim yeniden tasarlanmadı.</p>',
      '<p>2B sıkıştırılabilir RANS; M0,2; bir metreye göre Re5milyon;300K; alfa0°; duvar0–2m, alan yüksekliği1m. Adyabatik duvar, upstream simetri, total giriş/statik çıkış. Standart SA-neg NEGATIVE,WITHFT2;ν̃∞=3ν∞. Pr0,72/0,9. Referans alan2m². '+link(ROOT/'outputs/data/qualification/flatplate_SAneg_20261025_v1/input_ledger.json','Birim, kaynak, varsayım ve hesap tablosu')+'.</p>',
      '<p>SI gaz/Sutherland sabitleri açık kaydedildi; NASA’nın tüm boyutlu sabitleriyle tam özdeşlik bağımsız kurulmuş değildir. Re/M/T’ye tutarlı p∞=114454,649Pa hesaplandı; eski resmî SU2 tarifindeki yuvarlanmış115056Pa doğrudan kopyalanmadı. Bu basınç seçimi hedef Cf’ye göre yapılmadı. Kaynak tarif Roe2.mertebe/WLS, türbülans taşıması1.mertebe; kurulu8.5 sözdizimiyle gerçek native çalışma sınandı.</p>',
      '<h2>Yakınsama ve alan/geçmiş eşlemesi</h2>'+table(['Deneme','Hücre','Alan / son geçmiş','log yoğunluk','log SA','ΔCD son100','max y+','İteratif kapı'],rows),
      '<p>Önceden kayıtlı iteratif kapı: yoğunluk&lt;−10; SA&lt;−11; son100 CD aralığı&lt;10⁻⁷. Çalıştırma hedefi daha sıkı−13 idi. Orta300s, ince uniform600s ve ince başlangıç-aktarım300s bütçesinde durdu; OS çıkışı1 olarak saklandı. Eski alanı son CSV satırıyla eşleştirmedik. Yalnız ilk duvar y+ bütün BL’nin veya yakınsamanın kanıtı değildir.</p>',
      f'<img src="{rel(ROOT/"outputs/plots/flatplate_mesh_and_convergence_20261025.png")}" alt="Kaynak ağ ve gerçek yakınsama geçmişleri">',
      '<h2>Kaynakla gerçek sayısal farklar</h2>'+table(['Deneme','Cf(x≈0,97), aynı ağ: CFL3D / FUN3D','Cf eğrisi bağıl L2: CFL3D / FUN3D','Hız bağıl L2: x0,97008 /1,90334','μt profili bağıl L2: CFL3D / FUN3D'],profiles),
      '<p>Cf eğrisi için0,1≤x≤1,9m penceresi sonuçlardan önce seçildi: hücum kenarı tekilliği ve çıkış etkileşimi kaynak tarafından açıklanıyor. Pencere dışındaki noktalar da bütün farklarıyla CSV’de korunur; tam-eğri hatası ayrıca JSON’dadır. Kaynak eğriler545×385 ağındandır; tabloyun yerel Cf sütunu her native ağa karşılık gelen aynı kaynak hücre sayısıyla kıyaslanır. Bu iki kıyas sessizce karıştırılmadı.</p>',
      f'<img src="{rel(ROOT/"outputs/plots/flatplate_reference_comparison_20261025.png")}" alt="Kaynak sürtünme ve hız/türbülans profilleriyle native kıyas">',
      '<p>Bağıl L2=norm(native−referans)/norm(referans); noktalar ağırlıksızdır. Her hız profilindeki385; türbülans profillerindeki384/385 kaynak nokta korundu, geçersiz örnek sayısı0. Hızdaki kaynak “u” serbest akışa göre boyutsuz hız olarak yorumlandı; bu açık normalizasyon notudur. μt/μ∞ tanımı TMR sayfasında açık verilir. CFL3D μt kesiti x0,9701266, FUN3D x0,97; native kesit0,97008m olduğu için küçük konum farkları kayıtlıdır.</p>',
      '<p>İlk son işlemde hız1,90334 isteği en yakın sütundan1,91408 veya1,89260m’de örnekleniyordu.48 eski rapor/veri/kod/figür dosyası korundu. Yeni sürüm iki native sütun arasında pozitif interpolasyonla tam istenen x’de örnekler; her iki düğümün geçerlilik maskesi gerekir. Bu düzeltme CFD’yi yeniden çalıştırmadı; alanlar ve kuvvetler değişmedi.</p>',
      '<h2>Deneyerek taramak yerine iki mekanizma</h2><p><b>ILU:</b> <a href="https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/">SU2 yüksek CFL için ILU’yu öneriyor</a>. Aynı orta checkpoint3600 ile200’er adım, yalnız LU_SGS/ILU değişti. Önceden gereken≥0,3log ek düşüş yerine0,05506log oluştu. Etki geçmedi; başka ILU değerleri taranmadı. Bu, ILU’nun genel olarak kötü olduğunu göstermez.</p>',
      f'<p><b>Başlangıç aktarımı:</b> aynı ince ağ/konveksiyon/CFL/fizik üzerinde orta alan yalnız ilk tahmin olarak kullanıldı.400.adımda yoğunluk log artığı {report["nested_initialization_effect"]["density_log10_gain"]:.5f} daha düşük: dar sayısal etki geçti. Başlangıç hazırlama ve eşzamanlı yükler nedeniyle süre hızlanması iddiası yok. Son yakınsama yine geçmedi; aktarılan ince deneme, referansa daha yakın diye ana “fine” rolünün yerine konmadı.</p>',
      '<p>Kaynak metnindeki yaklaşık2×10⁻¹²m yuvarlama, aşırı katı eşitlik/ebeveyn hücre testlerini tetikledi. Eğri ağ teşhisi yanlıştı ve geçersiz olarak korundu. Negatif VTK ağırlıkları da reddedildi. Üç reddedilmiş taslak native çözücüye verilmedi. Kullanılan başlangıç aktarımı pozitif ağırlıklı; sabit alan hatası2,22×10⁻¹⁶; koordinat yeniden üretimi2,00×10⁻¹²m. Ortak düğüm durumları bit düzeyinde aynı; yoğunluk ve iç enerji pozitif; fiziksel değer kırpması0. Bu toplam korunumlu yeniden ağlama değildir. Native kaynak ağın koordinatları hiç değişmedi.</p>',
      '<h2>Ne öğrenildi, ne açık kaldı?</h2><p>Duvar sürtünmesi, hız ve μt’nin bu düşük Mach attached-flow vakasında bağımsız kaynakla yakın olması, SA yolunda kaba bir uygulama hatası olduğuna dair kanıt sağlamıyor. Bu bir çıkarımdır; tüm SA denklemlerini, şok/ayrılma/3B M6’yı veya keyfi kullanıcı geometrisini doğrulamaz. Kaba tek ağın bütün yerel ekranları geçmesi de üç ağ ailesinin kabulü değildir.</p>',
      '<p>Orta/ince iteratif kapılar açık. Küçük orta→ince farktan GCI çıkarılmadı; GCI=null. Normal profil örneklemesi, gerçek ham RMS bileşenleri ve bağımsız Cf integrasyonu kayıtta. Basınç olmayan düz duvarın CD’si bağımsız trapez Cf integrasyonuyla yaklaşık10⁻⁹ bağıl mertebede uyuştu; bu deney doğruluğu değildir.</p>',
      '<p>Sıradaki tek teşhis hazır, <b>çalıştırılmadı</b>: aynı ince checkpoint800 ile sabit CFL100/10; iki kolda adaptasyon kapalı, yalnız CFL değeri değişir. Amaç artık salınımlarında zaman adımının etkisini ayırmak.400adım/240s sınırı ve≥0,3log yoğunluk kazanımı+SA kötüleşmeme şartı kayıtlı; fiziksel kabul eşikleri aynı. '+link(CASE/'next_numerical_control_not_run.json','Sonraki kontrollü deney sözleşmesi')+'.</p>',
      '<h2>Kanıtlar ve kullanım sınırı</h2><p>Bu geliştirme kör deney değildir. Bütün baseline ve aktarım çıktıları yeni referanslar indirilip puanlanmadan önce mühürlendi. Yeni LLM sürümü/bağımsız ajan davranışı sınanmadı; uzmanlık kazanımı iddiası yok. Mevcut kapsam/maske/alan eşlemesi dersleri uygulandı; aynı kurallar tekrar yeni prompt kuralı olarak çoğaltılmadı.</p>',
      f'<p>{len(integrity)} native denemenin {quality["file_records"]} dosya kaydı tekrar SHA256 ile denetlendi. Kaynak arşivde yerel hash var; upstream yayınlanmış checksum doğrulaması iddia edilmez. Proje girdileri korunuyor.</p><ul>']
    files=[ROOT/'outputs/reports/flatplate_comparison_20261025.json',qpath,ROOT/'outputs/reports/flatplate_ILU_control_20261025.json',CASE/'contract.json',CASE/'nested_seed/contract.json',CASE/'nested_seed/transfer.json',CASE/'nested_seed/support_check_v4.json',BASE/'sources/input_sources_manifest.json',BASE/'sources/reference_manifest.json',BASE/'postprocessing_v1_nearest/manifest.json',ledgerpath]
    for role in ['coarse','medium','fine','fine_nested']:files.extend([ROOT/f'outputs/reports/flatplate_{role}_field_audit_20261025.json',CASE/role/'prediction_frozen.json',ROOT/f'outputs/data/qualification/flatplate_SAneg_20261025_v1/{role}/Cf_vs_CFL3D.csv',ROOT/f'outputs/data/qualification/flatplate_SAneg_20261025_v1/{role}/velocity_1.90334.csv'])
    body.extend('<li>'+link(p)+'</li>' for p in files);body.append('</ul><p><a href="https://tmbwg.github.io/turbmodels/flatplate_grids.html">TMR kaynak ağlar</a> · <a href="https://tmbwg.github.io/turbmodels/flatplate_sa.html">TMR SA referans ve sınırları</a> · <a href="https://su2code.github.io/tutorials/Turbulent_Flat_Plate/">Resmî SU2 başlangıç tarifi</a></p>')
    css='body{font:16px/1.65 Segoe UI,sans-serif;max-width:1250px;margin:40px auto;padding:0 22px;color:#243147}h1,h2{line-height:1.25}h2{margin-top:36px}.callout{background:#fff0da;padding:18px;border-left:5px solid #bd7d29}.muted{color:#6c7a88}table{border-collapse:collapse;display:block;overflow:auto;font-size:13px}td,th{border:1px solid #d5dfe5;padding:9px;text-align:left}th{background:#eaf1f6}img{max-width:100%;border:1px solid #d5dfe5}a{color:#076c92}'
    text=''.join(body);dest.write_text('<!doctype html><html lang="tr"><meta charset="utf-8"><title>CFD düz plaka ve M6</title><style>'+css+'</style>'+text+'</html>',encoding='utf-8')
    links=[]
    for path in re.findall(r'(?:href|src)="([^"#]+)"',text):
        if '://' not in path:
            p=(dest.parent/path).resolve();assert p.exists(),p;links.append(str(p.relative_to(ROOT)))
    md=dest.with_suffix('.md');md.write_text('# CFD düz plaka ve M6 —25Ekim\n\n[Ayrıntılı rapor](cfd_duz_plaka_ve_m6_20261025.html)\n\nKaynak NASA ağlarında gerçek SA-neg:3264/13056/52224hücre. Kaba iteratif kabul geçti; orta/ince ve aktarımlı ince geçmedi. Kaynak Cf/hız/μt ekranları yakın olsa da aile yeterliliği false. ILU etkisi0,055log ile geçmedi. Başlangıç aktarımı400adımda2,57747log ek yoğunluk düşüşü verdi; doğruluk/hız veya genel kabul değildir.\n\nSonraki sabitCFL100/10 deneyi yalnız hazırlandı, çalıştırılmadı.\n',encoding='utf-8')
    closure={'closed_utc':now(),'scope':'bounded source SA implementation diagnostic batch complete','scoped_qualification_passed':False,
        'native_runs':runtime,'report':str(dest.relative_to(ROOT)),'report_sha256':sha(dest),'local_links_checked':len(links),
        'integrity_report_sha256':sha(qpath),'open_checks':['medium and fine iterative convergence','three converged meshes and asymptotic comparison','dimensional constant identity limitation','general3D/M6/experiment qualification remains separate']}
    save(CASE/'batch_closed.json',closure)
    setup=ROOT/'work/setup/su2_install.json';s=read(setup);s.setdefault('additional_case_reports',{})['flatplate_20261025']={'report':str(dest.relative_to(ROOT)),'native_runs':len(runtime),'scoped_qualification_passed':False};save(setup,s)
    with (ROOT/'PROJECT_STATE.md').open('a',encoding='utf-8') as f:
        f.write('\n\n## 25 Ekim: kaynak NASA düz plakada SA-neg uygulama teşhisi\n\n- Rapor outputs/reports/cfd_duz_plaka_ve_m6_20261025.html. Ayrı qualification görevinde NASA kaynak69×49/137×97/273×193 ağları biçim çevrimiyle korundu;3264/13056/52224hücre. M0,2/Re_per_m5M/T300K, standardSA-neg NEGATIVE,WITHFT2;ν̃∞=3ν∞. Kaynak fizik/sayısal varsayım/birim/hesap defteri ayrı. Boyutlu gaz/Sutherland sabitlerinin bütün NASA kodlarıyla tam özdeşliği kurulmadı; kaynak yuvarlanmış basıncı kopyalamak yerine Re tutarlılığı kullanıldı.\n-8native koşu tamamlandı/durduruldu ve mühürlendi. Kaba400tam alan yoğunluk−13,0359/SA−15,6227 ile iteratif kapıyı geçti. Orta300s alan3600/terminal3716:yoğunluk−9,47085; ince600s alan2000/terminal2015:−8,30779. Maxy+0,95150/0,48224/0,25889. Zorunlu orta/ince yakınsaması yok; aile yeterliliği false,GCI null.\n- Aynı kaynak hücre sayısındaki Cf(x0,97008) farkları CFL3D/FUN3D: kaba%0,2511/%1,4925; orta%0,1528/%0,4863; ince%0,3815/%0,4652. Cf eğriL2, iki hız veμt kaynak profili ekranları geçti; sonuçlar sayısal CFD referanslarıdır, deney veya M6 doğrulaması değil. Bütün referans noktaları ve pencere dışı farklar CSV’de.\n- Aynı orta restartla200adımlık LU_SGS/ILU tek değişken kontrolü0,05506log ile0,3eşiğini geçmedi; daha çok ILU taraması yapılmadı. Orta→ince pozitif başlangıç aktarımı native olarak okundu;400adımda2,57747log ek yoğunluk düşüşü sağladı. Son alan800/terminal925 yoğunluk−9,36639/SA−9,76442/CDpencere3,42664e−7 ile kabul geçmedi. Fine rolü referansa daha yakın aktarımlı sonuçla değiştirilmedi; hızlanma veya doğruluk iyileşmesi iddiası yok.\n- Üç aktarım taslağı geometri/ağırlık kontrollerince native öncesi reddedildi; kaynak metindeki2e−12m farkın eğrilik olduğu teşhisi çürüdü. Kullanılan ilk-tahmin interpolasyonu koordinatı2e−12m, sabit alanı2,22e−16 ile üretiyor; ortak durumlar bit eşleşiyor,ρ/iç enerji pozitif, fizik kırpması0; CFD ağı değişmedi.\n- Son işlemv2 tamx0,97008/1,90334 için iki native sütun arasında interpolasyon ve çift maske kullanır. En yakın sütunla eski48dosya work/flatplate_20261025/postprocessing_v1_nearest altında korundu; alan/kuvvetler değişmedi.8tahminin bütün hash kayıtları ve kayıtlı proje girdileri yeniden kontrol edildi. Kör veya yeniLLM davranış sınaması değildir; öncekiM6/RAE/VLM açık kabulleri kapanmadı.\n- Sonraki ayırt edici test sözleşmesi hazır fakat çalışmadı: aynı ince checkpoint800 ile adaptasyon kapalı sabitCFL100/10,400adım/240s. Kabul eşikleri ve fizik değişmez.\n')
    archive=ROOT/'outputs/data/task_evidence'/task['id'];archive.mkdir(exist_ok=True,parents=True);evidence=[]
    for j,p in enumerate(files+[dest,md,CASE/'batch_closed.json']):
        out=archive/(f'{j:02d}_'+p.name);shutil.copyfile(p,out);evidence.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'archived':str(out.relative_to(ROOT))})
    task.update(status='tamamlandı',phase='sınırlı SA kaynak kontrolü kapandı',completed_utc=now(),evidence=evidence,
        result_scope='Source-code agreement diagnostic; family numerical qualification false, M6 false',scoped_qualification_passed=False,open_engineering_checks=closure['open_checks']);save(taskpath,task)
    print({'report':str(dest),'native_runs':len(runtime),'hash_records':quality['file_records'],'links':len(links),'qualification':False})

if __name__=='__main__':main()
