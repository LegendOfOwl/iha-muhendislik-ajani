"""Close a bounded source-backed diagnostic batch; preserve failed hypotheses."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from run import history
from scaled_restart import scales
import os,shutil,html
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    cap=read(ROOT/'outputs/reports/flatplate_inner_cap_20261026.json');line=read(ROOT/'outputs/reports/flatplate_linelet_20261026.json')
    probe=read(ROOT/'outputs/reports/residual_probe_20261026.json');guards=read(ROOT/'outputs/reports/residual_probe_guards_20261026.json')
    assert guards['passed'] and guards['tests_run']==28
    assert read(ROOT/'outputs/reports/inner_cap_guards_20261026.json')['passed']==9
    taskpath=ROOT/read(CASE/'inner_cap_20261026_v1/task.json')['path'];task=read(taskpath);assert task['status']!='tamamlandı'
    folders=[CASE/p for p in ['inner_cap_20261026_v1/cap40','inner_cap_20261026_v1/cap80','residual_probe_20261026_v1/explicit','linelet_20261026_v1/linelet']]
    runs=[];newhash=oldhash=codehash=0
    for p in CASE.rglob('prediction_frozen.json'):
        s=read(p);new=p.parent in folders
        for f,h in s['files_sha256'].items():
            assert sha(ROOT/f)==h,f
            if new:newhash+=1
            else:oldhash+=1
        if new:
            for f,h in read(p.parent/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/f)==h;codehash+=1
            runs.append({'folder':str(p.parent.relative_to(ROOT)),'seal_sha256':sha(p),'native_status':s['native_status'],'matched':s['matched']})
    assert len(runs)==4
    real={}
    for p in (ROOT/'outputs/data/project').glob('*.json'):
        assert sha(p)==sha(ROOT.parent/'iha-muhendislik-ajani/uygulama/outputs/data/project'/p.name);real[str(p.relative_to(ROOT))]=sha(p)
    integrity={'checked_utc':now(),'new_native_runs':runs,'new_raw_hash_records_verified':newhash,'old_raw_hash_records_verified':oldhash,
       'pre_native_code_hash_records_verified':codehash,'real_UAV_inputs_unchanged_vs_v0_13':real,'no_native_retry_after_probe_wrapper_error':True}
    save(ROOT/'outputs/reports/residual_diagnostics_integrity_20261026.json',integrity)
    fig,axes=plt.subplots(2,2,figsize=(12,7));factors=scales(read(CASE/'contract.json')['derived_freestream'])['residual']
    for label,folder in [('LU_SGS40',folders[0]),('LU_SGS80',folders[1]),('LINELET40',folders[3])]:
        h=history(folder);x=[r['Inner_Iter'] for r in h]
        axes[0,0].plot(x,[r['rms[Rho]']+np.log10(factors['rms[Rho]']) for r in h],label=label)
        axes[0,1].plot(x,[r['rms[nu]']+np.log10(factors['rms[nu]']) for r in h],label=label)
        axes[1,0].plot(x,np.cumsum([r['Linear_Solver_Iterations']+r['LinSolIterTurb'] for r in h]),label=label)
        axes[1,1].plot(x,[r['Avg CFL'] for r in h],label=label)
    for a,y in zip(axes.flat,['SI log10 density residual','SI log10 SA residual','Cumulative flow+SA Krylov count','Reported average CFL']):
        a.set(xlabel='Fresh-restart iteration',ylabel=y);a.grid(alpha=.2);a.legend()
    axes[0,0].axhline(-10,color='gray',ls=':');axes[0,1].axhline(-11,color='gray',ls=':')
    fig.suptitle('Same seed and source grid; same adaptive policy, different resulting trajectories');fig.tight_layout()
    fig.savefig(ROOT/'outputs/plots/inner_cap_linelet_20261026.png',dpi=150);plt.close(fig)
    def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
    comparisons=[]
    for label,r in [('İç tavan40→80',cap),('LU_SGS→LINELET',line)]:
        q=r['quality'];comparisons.append([label,f"{q['density_log10_gain']:+.8f}",f"{q['SA_log10_worsening']:+.8f}",f"{r['work_ratio']:.8f}",'Geçti' if r['effect_passed'] else 'Geçmedi'])
    comp_table=table(['Tek config değişimi','SI yoğunluk kazancı,log10','SI SA kötüleşmesi,log10','Krylov işi oranı','Ortak etki'],comparisons)
    norms=table(['Denklem','Native RMS,log10 ND','İhraç RMS farkı,log10','İhraç MAX farkı,log10'],[[k,f"{v['native_log10_RMS']:.8f}",f"{v['RMS_log10_error']:.3g}",f"{v['MAX_log10_error']:.3g}"] for k,v in probe['components'].items()])
    spatial=probe.get('spatial',{});rho=spatial.get('Rho',{});nu=spatial.get('nu',{})
    regionrows=[[x['name'],x['nodes'],f"{100*x['squared_residual_share']:.7f}%"] for x in rho.get('regions',[])]
    regiontable=table(['Ön tanımlı bölge','Düğüm','Yoğunluk artığı kare toplamındaki pay'],regionrows)
    outcomes={'created_utc':now(),'scope':'Bounded4-native diagnostic batch; no replacement of frozen fine role',
       'inner_cap_effect_passed':cap['effect_passed'],'linelet_effect_passed':line['effect_passed'],
       'verified_RHS_measurement_accepted':probe['measurement_accepted'],'new_native_runs':4,'new_software_guard_checks':37,
       'physical_qualification_passed':False,'M6_qualification_passed':False,'LLM_behaviour_improvement_measured':False,
       'hypotheses':[{'name':'Inner cap is sufficient to improve at registered cost','status':'not_supported_in_this_pair'},
          {'name':'Normal-line preconditioner improves at registered cost','status':'not_supported_in_this_pair'},
          {'name':'LE Cf error is the same issue as the dominant density residual','status':'not_established; spatial observations differ'},
          {'name':'Localized residual proves local mesh error','status':'not_established'}]}
    save(CASE/'residual_probe_20261026_v1/batch_closed.json',outcomes)
    ledger={'created_utc':now(),'instruction_snapshot':task['agent_instruction_snapshot'],'events':outcomes['hypotheses'],
       'confirmed_process_errors':[{'kind':'explicit_auxiliary_semantics','evidence':'wrapper_freeze_failure.json','resolved_without_new_native_run':True},
           {'kind':'guard_recorder_Path_type','preserved_source':'work/flatplate_20261026/failed_guard_recorder_v1.py','native_outputs_affected':False}],
       'new_prompt_version':False,'new_blind_LLM_test':False,'not_blind':True,'operational_lessons':'Existing L04/L05/L08/L09/R01/R03 cover these events; benchmark values not copied into analyst lessons.'}
    save(ROOT/'outputs/data/agent_learning/reviewer_ledger_residual_diagnostics_20261026.json',ledger)
    md=f'''# Kalan CFD artığını konumlandırma ve kontrollü yöntem kıyası

26 Ekim 2026 · Dört yeni native SU2 koşusu · Genel fizik/M6/İHA kabulü **false**.

Bu turda yeni bir yakınsama çözümü doğrulanmadı. Buna karşılık, çözücünün gerçek doğrusal olmayan artığını nerede ürettiğini gösteren ölçüm yöntemi doğrulandı. Bu, son denemelerden daha fazla ayar taramadan bilgi çıkarabilmemizi sağlıyor. Sabit kaynak benchmarkıdır; keyfi CAD için genel analiz hizmeti değildir.

## Önceden kayıtlı40→80 kontrolü

İki taze kol aynı ince kaynak ağı, aynı ND restart baytları, aynı fizik ve aynı adaptive CFL politikasıyla200 adım çalıştı. Yalnız LINEAR_SOLVER_ITER değişti; bu ortak ayar akış ve SA iç çözücüsünü etkiler. Sonraki CFL yörüngeleri aynı olmaya zorlanmadı; gözlenen etki bu geri beslemeyi de içerir. Eski3999-adımlı koşunun kesintisiz devamı sayılmaz.

{comp_table}

Geçme şartı yoğunlukta en az0,3log ek düşüş, SA'da en fazla0,1log kötüleşme ve toplam Krylov iterasyonu oranı≤1,5 idi.40→80 oranı1,50447718 olduğu için **1,5'e yuvarlayıp kabul etmedik**. Yoğunluk kazancı0,09148072 ile0,3'ün altında kaldı. Bu vaka için yalnız daha yüksek iç tavanı çözüm olarak seçmedik. Başka tavan değerlerini otomatik taramadık.

Gerçek süre/RAM gözlemleri: LU_SGS40 **40,578s/0,285GiB**; LU_SGS80 **79,563s/0,442GiB**; LINELET40 **55,594s/0,292GiB**. Bunlar tek yerel koşunun gözlemleridir. FGMRES alt uzayı büyüdükçe ortogonalizasyon ve bellek maliyeti değişir; toplam iterasyon sayısı gerçek FLOP veya genel hızlanma değildir.

![Aynı başlangıçla üç sayısal kol](../plots/inner_cap_linelet_20261026.png)

## Doğru artığı dışarı almak

SU2'nin implicit çözümünde VTU Residual_Density çalışma vektöründen yazılır; iç doğrusal çözüm onu değiştirebilir. History'deki cached RMS ile aynı olduğu varsayılmadı. Kurulu8.5.0 kaynaklarında explicit Euler akış ve SA adımlarının bu vektörü okuyup çözüm artışını ayrı tuttuğu incelendi. Aynı özgün fine3999 restartından **tek adım**, CFL1e-6, MG0 ve explicit akış+SA ile yeni gözlem yapıldı. Bu yaklaşık1s sürdü; yakınsama deneyi veya fiziksel iyileştirme değildir.

Kabul sözleşmesi ölçümden önce kaydedildi: beş denklemin hem RMS hem MAX farkı≤1e-6log;52689 sahip olunan noktanın bire bir koordinat eşlemesi≤2e-7m; native double restartta dört konservatif alanın her birinin bağılL2 drift'i≤2e-6; sonlu değerler ve pozitif yoğunluk/basınç. Duvar ve sınır noktaları normdan çıkarılmadı. Norm hacim ağırlıksız sqrt(ΣR²/N) biçimindedir; MPI halo yoktur.

{norms}

**Beş RMS/MAX birlikte geçti.** En büyük log farkı1,14e-8; koordinat eşleme en büyüğü6,51e-8m. Konservatif native alan drift'i en çok4,67e-12; ν̃ drift'i3,65e-16 ayrı gözlem olarak saklandı. Float32 VTU yuvarlaması native double drift'in yerine kullanılmadı. Her52689 düğüm ve geçerlilik bilgisi CSV'de korunuyor.

Akış artığı akış güncellemesinden önce, SA artığı bu küçük akış güncellemesinden sonra ve SA güncellemesinden önce hesaplanır. Harita bu **sıralı aşamaların artığıdır**; son çıktı alanının yeniden hesaplanmış artığı diye sunulmaz. Sabit SI çarpanı aynı denklem içindeki kare paylarını değiştirmez; farklı denklemlerin payları tek bir fiziksel hata bütçesi olarak toplanmaz.

## Artık nerede yoğunlaşıyor?

Yoğunluk artığının kare toplamının **%99,626'sı** x=0,5–2m/y=0–0,05m arka sınır tabakası bölgesinde; **%99,972'si** y≤0,02m duvar yakınında. En yüksek düğüm(x,y)=(1,9785208m,0m). Tüm kare toplamının%90'ını3964 düğüm (%7,523) taşıyor. Başlangıç kenarındaki ön tanımlı bölgenin payı yalnız%0,055924; önceki Cf kaynak farkı ile baskın yakınsama artığı aynı gözlem değildir.

{regiontable}

Bölgeler önceden tanımlı ve örtüşür; payları bir bölümleme gibi toplamayın. SA artığının dağılımı farklıdır: upstream bölgede yaklaşık%72,00; en yüksek düğüm x≈−0,002001m/y≈1,000465e-6m. Bu, türbülans denkleminin dominant yoğunluk artığıyla aynı yerde olması gerektiği anlamına gelmez. Lokal artık bir kestirme ağ hata bandı, deney hatası veya kesin nedensel teşhis değildir.

![Doğrulanmış sıralı aşama artıklarının kare payı](../plots/residual_probe_20261026.png)

## Haritanın yönlendirdiği tek aday: LINELET

Duvar yakınındaki artık ve kaynak ağın çok gerilmiş normal hücreleri, normal bağlaşımı birlikte çözen LINELET'i bir kez sınamayı gerekçelendirdi. Bugünkü LU_SGS40 kolu aynı seed/ağ/config kontrolleriyle yeniden kullanıldı; yeni200-adımlık kolda yalnız LU_SGS→LINELET değişti. Kaynak rehber ve8.5.0 uygulaması arşivlendi. Eşikler önceki kıyasla aynı kaydedildi; fizik değiştirilmedi.

Native log, **Using a linelet preconditioning.** ve **Computed linelet structure,32 points in each line (average).** mesajlarıyla yöntemin gerçekten çalıştığını gösterdi. Kaynak algoritmada çizgi başına en fazla32 nokta var; tüm193 normal düğümün veya bütün sınır tabakasının birlikte çözüldüğü söylenemez. Çizgilerde blok tridiagonal, çizgi dışında blok Jacobi kullanılır; LU_SGS'nin diğer bağlantılarını zayıflatabilir.

Bu kol yoğunlukta0,03230637log **daha kötü** kaldı; SA0,05537677log kötüleşti, Krylov oranı2,31080300 oldu. Kayıtlı ortak etki geçmedi. Tavanı artırma ve LINELET, bu eşleşmiş vakalarda yeterli çözüm olarak desteklenmedi; bütün akışlarda işe yaramaz ilan edilmedi. Kalan artığın kesin nedeni henüz bilinmiyor. Sonraki araştırma, gerçek çizgi kapsamı ve akış/normal yönlerdeki bağlaşımın ayrılması olmalı; yeni parametre taraması yapılmadı.

## Hatalar, kayıt ve sınırlar

- Explicit gözlem exit0 ile bir kez tamamlandı. Genel implicit mühürleyici, çözülmeyen doğrusal sistemin LinSolRes=−inf yardımcı sütununu zorunlu saydığı için hata verdi. Ham log ve başarısızlık korundu; yalnız bu explicit kapsam için yardımcı değer null/açıklamalı yapıldı. Beş RMS/MAX zorunluluğu korunarak yeni mühür alındı; CFD yeniden çalıştırılmadı. Bu istisnanın implicit/başarısız koşuya taşınmasını önleyen beş test eklendi.
- Dokuz maliyet/etki ve28 norm/konum/drift/explicit-mühür kontrolü geçti. Test kayıtçısının Path tür hatası ayrı taslak ve logla korundu, düzeltildi; native alan etkilenmedi. Bunlar37 yazılım kontrolüdür, LLM uzmanlığı kanıtı değildir.
- Yeni mühürlerde{newhash} ham hash, ön-native kod arşivlerinde{codehash}, önceki dondurulmuş sonuçlarda{oldhash} hash doğrulandı. GerçekİHA'nın{len(real)} girdi dosyası v0.13 ile aynı.
- Eski üç-ağ fine rolü3999 ve onun başarısız yoğunluk kapısı değiştirilmedi. Yeni200-adımlık kolları aileye sonradan geçirip kabul kapatmadık. M6/RAE/VLM/İHA ve genel CFD kabulleri açık; GCI null. Bu oturum kör LLM değerlendirmesi değildir; benchmark cevapları operasyonel analizci derslerine eklenmedi.

[40/80 tüm sonuçlar](flatplate_inner_cap_20261026.json) · [LINELET sonucu](flatplate_linelet_20261026.json) · [RHS ölçüm ve konum kanıtı](residual_probe_20261026.json) · [Mühür/koşu denetimi](residual_diagnostics_integrity_20261026.json) · [Yazılım kontrolleri](residual_probe_guards_20261026.json)

## Birincil kaynaklar

[SU2 doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/), [explicit akış uygulaması](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/solvers/CFVMFlowSolverBase.hpp), [SA explicit adımı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/solvers/CScalarSolver.inl), [RMS/MAX hesapları](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/solvers/CSolver.cpp), [çıktı semantiği](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/output/CFlowCompOutput.cpp), [linelet sınırı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/include/geometry/CGeometry.hpp), [çizgi üretimi](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/geometry/CGeometry.cpp), [matris işlemleri](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/linear_algebra/CSysMatrix.cpp). Yerel kaynak URL/zaman/SHA256 manifestleri ayrıca tutulur.
'''
    report=ROOT/'outputs/reports/cfd_kalan_artik_20261026.md';report.write_text(md,encoding='utf-8')
    def ht(headers,rows):return '<div class="scroll"><table><tr>'+''.join('<th>'+html.escape(str(h))+'</th>' for h in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r)+'</tr>' for r in rows)+'</table></div>'
    body='<h1>Kalan CFD artığını konumlandırma</h1><p class="lead">Yeni yakınsama ayarı kabul edilmedi; yerel artık ölçümünün doğruluğu doğrulandı.</p><p>Genel fizik/M6/İHA kabulü false. Kaynak2B SA-neg düz plaka; deneysel doğrulama değil.</p>'
    body+='<h2>İki kontrollü yöntem kıyası</h2>'+ht(['Değişim','Yoğunluk kazancı,log','SA kötüleşmesi,log','İş oranı','Etki'],comparisons)
    body+='<img src="../plots/inner_cap_linelet_20261026.png" alt="Üç aynı-seed yöntem kolu">'
    body+='<h2>Yerel artık gerçekten cached RMS ile aynı mı?</h2>'+ht(['Denklem','Native RMS,logND','RMS logfarkı','MAX logfarkı'],[[k,f"{v['native_log10_RMS']:.8f}",f"{v['RMS_log10_error']:.3g}",f"{v['MAX_log10_error']:.3g}"] for k,v in probe['components'].items()])
    body+='<p>Beş denklemde eşleşme geçti.52689 noktanın tamamı korunur. Native konservatif drift max4,67e-12. Bu tek explicit adımın sıralı aşama artığıdır; son alanın yeniden hesaplanan artığı değildir.</p>'
    body+='<h2>Yoğunluk artığının konumu</h2><p>Kare toplamının%99,626’sı arka sınır tabakası bölgesinde. Bu yerel artık ölçümüdür; ağ hata bandı veya kesin neden değildir.</p>'+ht(['Bölge','Düğüm','Kare artık payı'],regionrows)
    body+='<img src="../plots/residual_probe_20261026.png" alt="Yerel artık kare payları">'
    body+='<p>LINELET gerçekten devreye girdi; ortalama32 noktalı çizgilerle beklenen etkiyi sağlamadı.37 yazılım kontrolü geçti. Eski üç ağ/M6/RAE kabulleri açık; genel uzmanlık iddiası yok.</p>'
    body+='<p><a href="cfd_kalan_artik_20261026.md">Ayrıntılı Markdown raporu ve kaynaklar</a> · <a href="residual_probe_20261026.json">Ölçüm JSON</a> · <a href="residual_diagnostics_integrity_20261026.json">Mühür denetimi</a></p>'
    report.with_suffix('.html').write_text('<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD kalan artık tanısı</title><style>body{font:16px/1.65 Segoe UI,sans-serif;background:#edf3f6;color:#20313d;max-width:1180px;margin:25px auto;padding:20px}article{padding:28px;background:white;border-radius:12px}h1{line-height:1.2}.lead{font-size:21px}img{width:100%}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dbe3e8;padding:9px;text-align:left}th{background:#e9f1f4}h2{margin-top:30px}a{color:#006976}</style><article>'+body+'</article></html>',encoding='utf-8')
    evidence=[report,report.with_suffix('.html'),ROOT/'outputs/data/agent_learning/reviewer_ledger_residual_diagnostics_20261026.json',CASE/'residual_probe_20261026_v1/batch_closed.json']
    evidence += [ROOT/'outputs/reports'/name for name in ['flatplate_inner_cap_20261026.json','inner_cap_guards_20261026.json','residual_probe_20261026.json','residual_probe_guards_20261026.json','flatplate_linelet_20261026.json','residual_diagnostics_integrity_20261026.json']]
    archive=ROOT/'outputs/data/task_evidence'/task['id']/'closure';archive.mkdir(parents=True)
    for i,p in enumerate(evidence):
        dst=archive/f'{i:02d}_{p.name}';shutil.copyfile(p,dst);task['evidence'].append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'archived':str(dst.relative_to(ROOT))})
    code=archive/'code_final';code.mkdir();names=['inner_cap_control.py','test_inner_cap_control.py','prepare_residual_probe.py','freeze_residual_probe.py','probe_residual_analysis.py','test_probe_residual_analysis.py','test_explicit_freeze.py','record_probe_guards.py','linelet_control.py','close_residual_diagnostics.py']
    for n in names:shutil.copyfile(BASE/n,code/n)
    save(archive/'code_snapshot.json',{'created_utc':now(),'files_sha256':{str((code/n).relative_to(ROOT)):sha(code/n) for n in names}})
    task.update(status='tamamlandı',phase='sınırlı kontrol ve residual ölçüm paketi kapandı',completed_utc=now(),
       physical_qualification_passed=False,cap_effect_passed=cap['effect_passed'],linelet_effect_passed=line['effect_passed'],RHS_measurement_accepted=probe['measurement_accepted']);save(taskpath,task)
    with (ROOT/'PROJECT_STATE.md').open('a',encoding='utf-8') as f:f.write(f'\n\n## 26 Ekim: konumsal artık gözlemi ve iki kontrollü hipotez\n\n- Görev {task["id"]}:4 yeni native koşu.40→80 ortak tavan kıyası yoğunluk kazancı0,09148072log/Krylov1,50447718 ile ön kayıtlı0,3/1,5 şartını geçmedi. Yalnız40→80 ayarı akış+SA ve adaptiveCFL geri beslemesini etkiler.\n- Kaynakla gerekçeli tek explicit adımda exported RHS5RMS/MAX ile≤1,14e-8log uyuştu.52689 nokta bijektif; native konservatif driftmax4,67e-12. Rho kareartıkpayı aftBL%99,626,leadingedge%0,055924; bu konum ölçümüdür, ağ hata bandı veya neden kanıtı değildir. Sıralı flow/SA aşaması artığı; finalfieldin yeniden hesaplanan artığı değil.\n- Konuma dayalı tekLINELET kolu nativeortalama32 noktalı lineletlerle gerçekten çalıştı; gain−0,03230637log/Krylov2,310803 ile başarısız. Kaynak32noktalı sınır tüm193normalnoktayı kapsamaz. Eski3Dsonucu genellenmedi. Yeni tarama/otomatik uzatma yok.\n- ExplicitLinSolRes−inf yardımcı sütunu genel mühürleyicide hata verdi; özgün kayıt korundu, aynı completednativeişi yeniden koşmadan explicit null-semantiğiyle mühürlendi. Testkayıtçısının Pathhatası da korundu/düzeltildi.9+28=37yazılım kontrolü geçti. {newhash} yeni ham/{codehash} ön-nativekod/{oldhash} eskihash doğrulandı; gerçekİHA{len(real)}girdisi v0.13 ile aynı.\n- Rapor outputs/reports/cfd_kalan_artik_20261026.html. Eski fine3999 rolü/üç-ağ minimum ve genelM6/RAE/VLM/İHA kabulü false,GCI null. Yeni körLLM/promptuzmanlığı ölçülmedi.\n')
    print({'report':str(report),'native_runs':4,'new_hashes':newhash,'old_hashes':oldhash,'code_hashes':codehash,'software_checks':37})

if __name__=='__main__':main()
