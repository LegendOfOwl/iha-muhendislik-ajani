"""Report the bounded work-control/family results, including any failed gate."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from reduced_family import FAMILY
import html,shutil

def main():
    review=read(ROOT/'outputs/reports/reduced_family_review_20261026.json')
    effect=read(ROOT/'outputs/reports/flatplate_linear_work_20261026.json')
    contract=read(FAMILY/'contract.json')
    taskpath=ROOT/read(CASE/'linear_work_20261026_v1/task.json')['path'];task=read(taskpath)
    assert task['status']!='tamamlandı'
    native=[];newhash=oldhash=codehash=0
    newfolders=[CASE/'linear_work_20261026_v1/reduced']+[FAMILY/r for r in contract['cases']]
    for sealpath in CASE.rglob('prediction_frozen.json'):
        s=read(sealpath);new=sealpath.parent in newfolders
        for p,h in s['files_sha256'].items():
            assert sha(ROOT/p)==h,p
            if new:newhash+=1
            else:oldhash+=1
        if new:
            for p,h in read(sealpath.parent/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/p)==h,p;codehash+=1
            native.append({'folder':str(sealpath.parent.relative_to(ROOT)),'seal_sha256':sha(sealpath),
                'status':s['native_status'],'matched':s['matched']})
    assert len(native)==4
    real={}
    for p in (ROOT/'outputs/data/project').glob('*.json'):
        assert sha(p)==sha(ROOT.parent/'iha-muhendislik-ajani/uygulama/outputs/data/project'/p.name)
        real[str(p.relative_to(ROOT))]=sha(p)
    integrity={'checked_utc':now(),'new_runs':native,'new_hash_records_verified':newhash,
       'old_hash_records_reverified':oldhash,'pre_native_code_hashes_verified':codehash,
       'actual_UAV_inputs_unchanged_vs_v0_12':real,'scope':'File integrity and frozen result pairing, not independent physical validation.'}
    save(ROOT/'outputs/reports/reduced_family_integrity_20261026.json',integrity)
    passed=review['registered_2D_numerical_screens_passed'];fine=review['results']['fine']
    nextplan={'created_utc':now(),'status':'registered_not_run','scope':'Fine-grid inner cap diagnosis, not another physical fit or automatic extension',
       'source':'https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/',
       'observation':{'final_flow_Krylov_iterations':40,'final_flow_linear_log_residual':fine['matched']['LinSolRes'],
          'inner_tolerance':.001,'final500_fraction_at40_cap':review['work_diagnostics']['fine']['windows'][-1]['flow_fraction_at40_cap']},
       'hypothesis':'A binding inner cap can restrict adaptive nonlinear progress; one endpoint and cap frequency do not establish causality.',
       'seed':str((FAMILY/'fine/restart_flow_003999.dat').relative_to(ROOT)),
       'seed_sha256':sha(FAMILY/'fine/restart_flow_003999.dat'),'seed_normalization':'FREESTREAM_VEL_EQ_MACH',
       'mesh_sha256':contract['cases']['fine']['mesh_sha256'],
       'only_config_change':'LINEAR_SOLVER_ITER40→80; both fresh arms use the identical final ND restart and all other options',
       'per_arm_iterations':200,'per_arm_seconds':180,'threads':4,
       'effect':{'SI_density_log10_gain_min':.3,'SI_SA_log10_worsening_max':.1,'total_Krylov_work_ratio_max':1.5},
       'physical_gates_unchanged':True,'no_automatic_sweep_extension_or_acceptance':True,
       'rejected_old_hypotheses_retained':True}
    save(CASE/'next_inner_cap_control_not_run_20261026.json',nextplan)
    def pct(x):return f'{100*x:.4f}%'
    def yn(x):return 'Geçti' if x else 'Geçmedi'
    names={'all_registered_runs_completed':'Üç kayıtlı koşunun bütçe içinde tamamlanması','all_three_iterative_gates':'Üç ağda SI kalıntıları ve son100 CD kararlılığı',
       'fine_max_yplus':'İnce ağ max y+ <1','fine_Cf_scalar_both_codes':'Cf(x=0,97008 m), iki kodun en ince referansına fark <%2',
       'fine_Cf_curve_both_codes':'Cf eğrisi iki kodla bağıl L2 <%3','fine_velocity_both_stations':'İki istasyonda hız profili bağıl L2 <%3',
       'fine_mut_both_codes':'İki kodla türbülans viskozitesi bağıl L2 <%5','medium_fine_Cf':'Orta–ince Cf değişimi <%1','medium_fine_CD':'Orta–ince CD değişimi <%2'}
    rows=[]
    for role,a in review['results'].items():
        m=a['matched'];s=a['native_status']
        rows.append([role,str(contract['cases'][role]['iterations']),f"{m['field_iteration']}/{m['terminal_history_iteration']}",
             f"{s['seconds']:.1f}",f"{m['rms[Rho]']:.7f}",f"{m['rms[nu]']:.7f}",f"{a['max_yplus']:.6f}",f"{m['CD']:.10f}",yn(a['iterative_gate'])])
    def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows)
    runs_table=table(['Ağ','Kayıtlı adım','Alan/son geçmiş','Süre,s','SI logρ','SI logν̃','maxy+','CD','İteratif şart'],rows)
    checks_table=table(['Önceden kayıtlı şart','Sonuç'],[[names[k],yn(v)] for k,v in review['checks'].items()])
    errors=[]
    for k,rs in fine['reference_errors'].items():
        for r in rs:errors.append([k,r['source_zone'],str(r['points']),str(r['invalid_points']),pct(r['relative_L2']) if r['relative_L2'] is not None else 'hesaplanamadı',pct(r['relative_L2_all_points']) if r['relative_L2_all_points'] is not None else 'hesaplanamadı'])
    errors_table=table(['Nicelik','Kaynak bölgesi','Nokta','Geçersiz','Kayıtlı pencere L2','Tüm noktalarda L2'],errors)
    batch={'closed_utc':now(),'new_native_runs':4,'registered_work_effect_passed':effect['effect_passed'],
       'registered_2D_numerical_screens_passed':passed,'checks':review['checks'],'general_physical_qualification_passed':False,
       'M6_qualification_passed':False,'LLM_behaviour_improvement_measured':False,'no_automatic_continuation':True,
       'review_sha256':sha(ROOT/'outputs/reports/reduced_family_review_20261026.json')}
    save(FAMILY/'batch_closed.json',batch)
    event={'created_utc':now(),'instruction_snapshot':task['agent_instruction_snapshot'],
       'events':[{'type':'accepted_scoped_cost_effect','evidence':'outputs/reports/flatplate_linear_work_20261026.json',
          'scope':'This medium source grid, same evolved seed,200steps and installed native solver only'},
         {'type':'bounded_family_evaluation','checks':review['checks'],'general_physical_acceptance':False},
         {'type':'postprocessing_output_name_bug','observation':'Station legend variable shadowed the output label; unique labels now survive both profile stations.',
          'scope':'File naming and plot title only; raw fields, numerical values and historical seals untouched.'}],
       'new_prompt_version':False,'LLM_behaviour_evaluation':False,'not_blind':True,
       'lessons':'Existing L04/L05/L08/L09/L10 and R01/R03 cover the numerical controls; no duplicate rule or experiment answers added to analyst memory.'}
    save(ROOT/'outputs/data/agent_learning/reviewer_ledger_reduced_family_20261026.json',event)
    outcome='Bütün kayıtlı2B sayısal şartlar geçti.' if passed else 'Kayıtlı2B sayısal şartların tamamı geçmedi; aile kabulü false.'
    md=f'''# Daha az iç çözüm işi ve üç ağda CFD denetimi

26 Ekim2026 · Dört yeni native SU2v8.5.0 koşusu · {outcome} Genel fizik/M6/İHA kabulü **false**.

## Bulunan yöntem

İç doğrusal çözücü toleransı1e-6 yerine1e-3 kullanıldığında200 ortak adımın toplam akış+SA Krylov iterasyon sayısı **11144→6451** oldu: **%{100*(1-effect['work_ratio']):.4f} azalma**. Bu sayı matris-vektör işlemlerinin veya duvar süresinin tam maliyeti değildir. Akış6500→3952, SA4644→2499.

Aynı ağ, aynı seed baytları, aynı fizik, dış çözüm yöntemi ve boyutsuzlaştırma korundu; eşli deneyde yalnız bu tek config satırı değişti. SI yoğunluk kalıntısı{effect['density_log10_worsening']:.8f}log ve SA{effect['SA_log10_worsening']:.8f}log kötüleşti; ikisi de ön kayıtlı0,05log sınırı içinde. |ΔCD|={effect['absolute_CD_difference']:.4g}<1e-7. İş oranı{effect['work_ratio']:.8f}<0,7; kayıtlı maliyet hipotezi geçti. Önceki20,032s ve yeni10,563s gözlemi genel iki kat hızlanma kanıtı olarak kullanılmadı.

[SU2 doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/) aşırı sıkı iç çözüm yerine toplam doğrusal olmayan ilerlemeyi izlemeyi önerir. Rehberden seçilen ayar bu vakada gerçekten sınandı; evrensel en iyi tolerans ilan edilmedi. Yalnız ölçekleme deneyinin önceki başarısız sonucu değişmedi.

## Aynı kaynak ailede gerçek devam çözümleri

NASA TMR düz plaka:3264/13056/52224hücre, M0,2, Re/m5e6, T300K; aynı geometri, dış sınır ve SA-neg fizik. ND FREESTREAM_VEL_EQ_MACH; Roe/MUSCL akış, birinci mertebe SA, FGMRES/LUSGS40, MG0 ve özgün adaptifCFL politikası korundu.1e-3 toleransla üç ayrı kaynak restartı fiziksel SI→ND dönüşümüyle kullanıldı. Bu devamlar soğuk başlangıçtan toplam maliyet kıyası değildir.

Kaba200/120s, orta4000/360s ve ince4000/900s sınırları çözümden önce sabitlendi. Ortak hamND artık−13 durdurucusunun eskiSI SA eşiğinden önce kesmemesi için CONV_STARTITER100000 önceden kaydedildi; fiziksel kabul eşiği değiştirilmedi. Sonuçlar aynı SI artık tanımında değerlendirilir. İnce rolü özgün ince checkpoint2000'den gelir; referansa daha yakın görünen tanısal aktarımlı seed seçilmedi.

{runs_table}

Alan/son geçmiş adımları eşleşmiyorsa son tam alanın kalıntısı kullanılır; daha sonraki CSV satırı alana atanmaz. Zaman aşımı veya eksik kayıtlı adım bütün aile kabulünü engeller. `solver.status.json` gerçek OS çıkışını ve kaynak sınırını korur.

{checks_table}

Orta–ince Cf değişimi{pct(review['medium_fine_changes']['Cf'])}; CD değişimi{pct(review['medium_fine_changes']['CD'])}. Bunlar tek başına ağ bağımsızlığı ya da hata bandı değildir. Global ön-kenar sürüklemesinin tekilliği ve asimptotik şartlar nedeniyle GCI/Richardson hata bandı **null** kaldı.

![Üç kaynak ağda aynı SI artıklar ve CD](../plots/reduced_family_convergence_20261026.png)

## İnce alanın kaynak kod kıyası

{errors_table}

**Pencere ile tam eğriyi ayırmak gerekir:** Cf penceresinde farklar yaklaşık%0,20/%0,23 iken, başlangıç kenarı dahil bütün447 noktada L2 **%17,84/%9,62**. Özellikle x=0,001m noktasının native karşılığı kenar aralığında interpolasyondur ve kaynaklara belirgin uzak kalır. Bu noktalar çıkarılmadı; ön kayıtlı pencerenin geçmesini bütün plaka boyunca aynı doğruluk diye sunmuyoruz.

Cf eğrisinin önceden belirlenmiş0,1–1,9m penceresi ve pencere dışındaki bütün noktalar CSV'de tutulur. Hız istasyonları0,97008/1,90334m; iki native sütun arasında pozitif interpolasyon ve çift geçerlilik maskesi kullanıldı. Sıfır yer tutucular fiziksel örnek sayılmadı. Sütun uyuşma uzaklıkları ve geçersiz örnek sayıları JSON'da saklandı. Cf tek nokta kıyası hem aynı kaynak ağ sayısıyla hem her kodun en ince referansıyla ayrı verilir; ikisi karıştırılmaz.

İnce alan duvar Cf integrali CD={fine['CD_independent_trapezoid']:.10f}; native CD'ye bağıl fark{pct(fine['CD_integration_relative_difference'])}. Bu farklı ayrıklaştırma/integrasyonun kontrolüdür; yeni bir deneysel kuvvet değildir. Referanslar CFL3D/FUN3D sayısal çözümleridir; rüzgâr tüneli ölçümü değildir. Boyutlu Sutherland sabitlerinin bütün referans kodlarında tam özdeşliği ayrıca kurulmadı.

![İnce ağda hız ve türbülans profilleri](../plots/flatplate_reduced_20261026_fine_profiles_20261025.png)

![Cf kaynak kıyası: başlangıç kenarı ve ön kayıtlı pencere](../plots/reduced_family_Cf_reference_20261026.png)

## Güvenilirlik ve sonraki ayrım

- Yeni mühürlerde{newhash}, ön-native kod arşivlerinde{codehash}, eski dondurulmuş kayıtlarda{oldhash} hash yeniden doğrulandı. GerçekİHA'nın{len(real)} girdi dosyası v0.12 ile aynı.
- Yeni maliyet kararı8/8, eksik referans/NaN/geçersiz prob/başarısız süreç gibi aile kararları12/12 kontrolü geçti. Bunlar yazılım kabul kontrolleridir; fizik veya LLM uzmanlığı kanıtı değildir.
- Son işlemde istasyonun grafik etiketi çıktı adını eziyordu. Etiketler ayrıldı; yeni grafik/JSON farklı koşu adlarını korur. Eski ham alanlar ve mühürler değiştirilmedi.
- Bu oturum referansları biliyor; kör LLM deneyi değil. Ajan promptu için yeni başarı iddiası veya hedef katsayı içeren ders eklenmedi.
- Bu reçete yalnız bu kaynak düz plaka ve koşul için sınandı. RAE2822, şok/ayrılma,3B M6, keyfiCAD→ağ, uçuşa elverişlilik ve genelCFD yeterliliği kapanmadı. Açık kapıyı yalnız iterasyon sayısı artırarak geçmiş saymayacağız.
- İnce koşunun son500 adımında akış iç çözümü%6,6 oranında40 iterasyon sınırına dayandı; son iç artık−2,0377, istenen log10(1e-3)=−3'e ulaşmadı. Bu bütün yavaşlığın sebebini kanıtlamaz. Rehberin iç çözüme yeterli iterasyon verilmesi önerisiyle, aynı son restartta yalnız40→80 tavanı için iki200-adımlık/180s kollu ayrı kontrol ön kaydedildi; **çalıştırılmadı**. Ortak yoğunluk kazancı≥0,3log, SA kötüleşmesi≤0,1log ve toplam Krylov işi oranı≤1,5 gerekecek. Otomatik tarama veya başarısız aileye ek adım yok. M6'ya doğrudan ayar taşımadan önce onun kendi kontrolü gerekir; bu turda yeniM6 koşusu yapılmadı.

[Makinece okunabilir tüm şartlar](reduced_family_review_20261026.json) · [Maliyet kıyası](flatplate_linear_work_20261026.json) · [Dosya/koşu denetimi](reduced_family_integrity_20261026.json) · [NASA kaynak vaka](https://tmbwg.github.io/turbmodels/flatplate_sa.html)
'''
    report=ROOT/'outputs/reports/cfd_ic_cozum_ve_uc_ag_20261026.md';report.write_text(md,encoding='utf-8')
    def html_table(headers,rs):
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rs)+'</tbody></table></div>'
    body='<h1>İç çözüm işi ve üç ağda CFD denetimi</h1><p class="lead">Krylov iterasyonu %42,11 azaldı. '+outcome+'</p>'
    body+='<p>Genel fizik/M6/İHA kabulü false. NASA TMR SA-neg düz plaka, tek Mach/Re koşulu; deneysel doğrulama değil.</p>'
    body+='<h2>Gerçek native sonuçlar</h2>'+html_table(['Ağ','Kayıtlı adım','Alan/geçmiş','Süre,s','SI logρ','SI logν̃','maxy+','CD','İteratif'],rows)
    body+='<h2>Ön kayıtlı şartlar</h2>'+html_table(['Şart','Sonuç'],[[names[k],yn(v)] for k,v in review['checks'].items()])
    body+='<img src="../plots/reduced_family_convergence_20261026.png" alt="Üç kaynak ağda SI artıklar ve CD">'
    body+='<h2>Kaynakla kıyas</h2>'+html_table(['Nicelik','Kaynak','Nokta','Geçersiz','Pencere L2','Tüm L2'],errors)
    body+='<p>Cf penceresinde%0,20/%0,23; başlangıç kenarı dahil447 noktada%17,84/%9,62. Pencere dışı farklar saklanır ve genel doğruluk iddiası kurulmaz.</p>'
    body+='<img src="../plots/reduced_family_Cf_reference_20261026.png" alt="Başlangıç kenarı dahil Cf kıyası">'
    body+='<img src="../plots/flatplate_reduced_20261026_fine_profiles_20261025.png" alt="İnce ağ profilleri">'
    body+='<h2>Kapsam ve kanıt</h2><p>Tek-değişken kontrolde11144→6451 Krylov iterasyonu; SI kalıntı farkları0,05log içinde. Tek zamanlama genel hızlanma iddiası değildir. Fizik ve eşikler korunur; bütün noktalar ve geçersizlik maskeleri saklanır. GCI null. M6/RAE/İHA açık kalır.</p>'
    body+='<p>'+str(newhash)+' yeni ham dosya, '+str(codehash)+' ön-native kod ve '+str(oldhash)+' eski hash doğrulandı.8 maliyet+12 aile kontrolü geçti. GerçekİHA girdileri aynı. LLM davranış iyileşmesi ölçülmedi.</p>'
    body+='<p><a href="cfd_ic_cozum_ve_uc_ag_20261026.md">Ayrıntılı Markdown raporu</a> · <a href="reduced_family_review_20261026.json">Sayısal JSON</a> · <a href="reduced_family_integrity_20261026.json">Mühür/koşu denetimi</a></p>'
    page='<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD üç ağ denetimi</title><style>body{font:16px/1.6 Segoe UI,sans-serif;background:#edf2f5;color:#20313d;max-width:1180px;margin:24px auto;padding:20px}article{background:white;padding:28px;border-radius:12px}h1{line-height:1.2}h2{margin-top:32px}.lead{font-size:21px}img{width:100%}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border:1px solid #dbe3e8;text-align:left}th{background:#e9f1f4}a{color:#006976}</style><article>'+body+'</article></html>'
    report.with_suffix('.html').write_text(page,encoding='utf-8')
    evidence=[report,report.with_suffix('.html'),FAMILY/'batch_closed.json',CASE/'next_inner_cap_control_not_run_20261026.json']+[ROOT/'outputs/reports'/n for n in [
        'flatplate_linear_work_20261026.json','linear_work_guards_20261026.json','reduced_family_review_20261026.json','reduced_family_guards_20261026.json','reduced_family_integrity_20261026.json']]
    evidence+=[ROOT/'outputs/data/agent_learning/reviewer_ledger_reduced_family_20261026.json']
    archive=ROOT/'outputs/data/task_evidence'/task['id']/'closure';archive.mkdir(parents=True)
    for i,p in enumerate(evidence):
        dst=archive/f'{i:02d}_{p.name}';shutil.copyfile(p,dst)
        task['evidence'].append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'archived':str(dst.relative_to(ROOT))})
    code=archive/'code_final';code.mkdir();codefiles=[BASE/n for n in ['linear_work_control.py','reduced_family.py','review_reduced_family.py','close_reduced_family.py','field_audit.py','audit_controls.py','family_decision.py','test_family_decision.py','test_linear_work_control.py','scaled_restart.py']]
    for p in codefiles:shutil.copyfile(p,code/p.name)
    save(archive/'code_snapshot.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in codefiles}})
    task.update(status='tamamlandı',phase='sınırlı iç-iş ve üç-ağ paketi kapandı',completed_utc=now(),
       registered_cost_effect_passed=effect['effect_passed'],registered_2D_numerical_screens_passed=passed,physical_qualification_passed=False)
    save(taskpath,task)
    state=f'\n\n## 26 Ekim: daha az iç çözüm işi ve üç kaynak ağ\n\n- Dört yeni native SU2 koşusu kapandı; rapor outputs/reports/cfd_ic_cozum_ve_uc_ag_20261026.html. Aynı orta seed/ağda yalnız tolerans1e-6→1e-3: toplam Krylov11144→6451 (%42,1123 azalma); SI yoğunluk/SA kötüleşmesi0,00143916/0,00121123log, |CD farkı|2,3e-11. Kayıtlı maliyet etkisi geçti; tek süre gözleminden genel hızlanma çıkarılmadı.\n- Kaynak üç ağda yeni sonlu bütçe/seed/sayısal reçete ön kaydedildi.2B sayısal şartların tümü={passed}; tek-tek sonuçlar reduced_family_review_20261026.json. İnce rolü özgün fine2000den korunur. HamND kalıntılar eskiSI eşikleriyle karıştırılmadı; alan/terminal adımları ve OS çıkışı ayrı.\n- {newhash} yeni ham hash, {codehash} ön-native kod ve {oldhash} eski hash doğrulandı.8 maliyet+12 aile karar kontrolü geçti. Son işlem çıktı adı gölgelenmesi düzeltildi; ham alan/mühürler aynı. GerçekİHA {len(real)}girdisi v0.12 ile aynı.\n- Genel fizik/M6/RAE/VLM/İHA kabulleri false, GCI null; referanslar sayısal kod sonuçlarıdır. Yeni körLLM/prompt uzmanlığı ölçülmedi. Kayıtlı bütçe dışında otomatik uzatma yapılmadı. Görev {task["id"]} sınırlı test/rapor paketi olarak kapandı.\n'
    with (ROOT/'PROJECT_STATE.md').open('a',encoding='utf-8') as f:f.write(state)
    print({'report':str(report),'screens_passed':passed,'new_hashes':newhash,'old_hashes':oldhash,'code_hashes':codehash})

if __name__=='__main__':main()
