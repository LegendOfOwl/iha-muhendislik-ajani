"""Close this finite research batch, including negative results and source limits."""
from prepare import ROOT, BASE, CASE, read, save, sha, now
from run import history
import sys
import shutil
import html
import json
from datetime import datetime,timezone


def main():
    folders=[CASE/r for r in ['fixed_cfl_pair_v1/cfl100','fixed_cfl_pair_v1/cfl10','mg_control_v1/smoke',
         'mg_control_v1/mg2','adaptive_toggle_v1/adaptive','newton_control_v1/seed','newton_control_v1/quasi',
         'newton_control_v1/newton','warm_scaling_pair_v1/scaled','newton_warm_control_v1/quasi','newton_warm_control_v1/newton']]
    runs=[];verified=code_verified=0
    for folder in folders:
        seal=read(folder/'prediction_frozen.json')
        for p,h in seal['files_sha256'].items():assert sha(ROOT/p)==h,p;verified+=1
        code=folder/'runner_code_before_native.json'
        if code.exists():
            for p,h in read(code)['files_sha256'].items():assert sha(ROOT/p)==h,p;code_verified+=1
        m=seal['matched'];status=seal['native_status']
        runs.append({'path':str(folder.relative_to(ROOT)),'seal_sha256':sha(folder/'prediction_frozen.json'),
           'exit_code':status['exit_code'],'stop_reason':status['stop_reason'],'seconds':status['seconds'],
           'sampled_peak_working_set_GiB':status['peak_working_set_GiB'],
           'field_iteration':m['field_iteration'] if m else None,'terminal_history_iteration':m['terminal_history_iteration'] if m else None})
    # Reverify prior frozen CFD, not the evolving working copies of scripts/reports.
    old_verified=0
    for role in ['smoke','coarse','medium','fine','nested_smoke','fine_nested','ilu_pair/lusgs','ilu_pair/ilu']:
        for p,h in read(CASE/role/'prediction_frozen.json')['files_sha256'].items():assert sha(ROOT/p)==h,p;old_verified+=1
    taskpath=ROOT/read(CASE/'fixed_cfl_pair_v1/task.json')['path'];task=read(taskpath)
    real=task.setdefault('real_project_inputs_at_close',{})
    # Compare actual project data with the last published snapshot, not an invented prior hash.
    published=ROOT.parent/'iha-muhendislik-ajani/uygulama/outputs/data/project'
    for p in sorted((ROOT/'outputs/data/project').glob('*.json')):
        if (published/p.name).exists():
            assert sha(p)==sha(published/p.name);real[str(p.relative_to(ROOT))]=sha(p)
    pairs={
      'CFL100→10':read(ROOT/'outputs/reports/flatplate_fixed_cfl_control_20261025.json'),
      'MG0→2':read(ROOT/'outputs/reports/flatplate_multigrid_control_20261025.json'),
      'Otomatik→sabit CFL':read(ROOT/'outputs/reports/flatplate_adaptive_toggle_20261025.json'),
      'Newton / soğuk başlangıç':read(ROOT/'outputs/reports/flatplate_newton_control_20261025.json'),
      'Yalnız değişken ölçekleme':read(ROOT/'outputs/reports/flatplate_scaling_control_20261025.json'),
      'Newton / gelişmiş alan':read(ROOT/'outputs/reports/flatplate_newton_warm_control_20261025.json')}
    rows=[]
    for label,r in pairs.items():
        d=r.get('comparison_decision',r)
        rows.append({'method':label,'comparable':d['comparable'],'density_gain':d['density_log10_gain'],
                     'SA_worsening':d['SA_log10_worsening'],'effect_passed':d['effect_passed']})
    integrity={'checked_utc':now(),'new_runs':runs,'new_native_runs':len(runs),'new_hash_records_verified':verified,
       'pre_native_code_archive_hash_records_verified':code_verified,'old_hash_records_reverified':old_verified,
       'actual_project_inputs_unchanged_vs_v0_11':real,'physical_qualification_passed':False,
       'scope':'All new top-level files in seals; nested code archives verified through sealed manifests. Not a fresh-machine reproduction.'}
    save(ROOT/'outputs/reports/flatplate_controls_integrity_20261025.json',integrity)
    scaling=pairs['Yalnız değişken ölçekleme']
    sys.path.insert(0,str(ROOT/'work/reliability'))
    from test_paired_control import main as check_pairs
    pair_checks=check_pairs()
    save(ROOT/'outputs/reports/flatplate_pair_guards_20261025.json',{'checked_utc':now(),'passed':len(pair_checks),'checks':pair_checks,'physical_qualification':False})
    events=[{'type':'hypothesis_not_supported' if row['comparable'] else 'not_evaluated_at_registered_checkpoint',
       'scope':'Only this seed, mesh, installed solver and registered budget','result':row} for row in rows]
    events += [
      {'type':'prevented_failure','id':'mixed_residual_normalization','evidence':'outputs/reports/flatplate_scaling_control_20261025.json',
       'observation':f"Unconverted mixed-unit gain{scaling['spurious_unconverted_density_gain']:.9g}log; SI-normalized gain{scaling['density_log10_gain']:.9g}log. Mixed-unit comparator now refuses the input.",
       'related_existing_rule':'L08 source semantics/normalization; no duplicate prompt lesson added'},
      {'type':'source_policy_clarification','id':'native_MG_CFL','evidence':str((CASE/'mg_control_v1/native_policy_note.json').relative_to(ROOT)),
       'observation':'CFL_ADAPT=NO does not imply constant native coarse-grid CFL or damping.'},
      {'type':'rejected_test_design','evidence':'outputs/reports/flatplate_scaling_guards_20261025.json',
       'observation':'All-component exact native residual identity threshold failed. Original draft preserved; native observation has no replacement relaxed acceptance threshold.'}]
    save(ROOT/'outputs/data/agent_learning/reviewer_ledger_flatplate_controls_20261025.json',
         {'created_utc':now(),'instruction_snapshot':task['agent_instruction_snapshot'],'events':events,
          'new_prompt_version':False,'new_LLM_behaviour_evaluation':False,'not_blind':True})
    nextplan={'created_utc':now(),'status':'registered_not_run','scope':'Inner linear oversolving / work reduction, not another CFL sweep or physical-model fit',
       'sources':['https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/'],
       'baseline':str((CASE/'warm_scaling_pair_v1/scaled').relative_to(ROOT)),
       'baseline_seal_sha256':sha(CASE/'warm_scaling_pair_v1/scaled/prediction_frozen.json'),
       'seed_sha256':sha(CASE/'warm_scaling_pair_v1/scaled/seed.dat'),'mesh_sha256':sha(CASE/'meshes/medium.su2'),
       'only_config_change':'LINEAR_SOLVER_ERROR1e-6→1e-3','iterations':200,'seconds':120,'threads':4,'comparison_iteration':199,
       'effect':{'total_flow_plus_SA_Krylov_iterations_ratio_max':.7,'density_and_SA_SI_log10_worsening_max':.05,'absolute_CD_difference_max':1e-7},
       'no_speedup_claim_from_single_timing':True,'no_automatic_extension_or_sweep':True,'physical_thresholds_unchanged':True}
    save(CASE/'next_linear_work_control_not_run.json',nextplan)
    complete={'closed_utc':now(),'scope':'Finite convergence research/control batch complete; all physical qualification gates remain open',
       'rows':rows,'integrity_report_sha256':sha(ROOT/'outputs/reports/flatplate_controls_integrity_20261025.json'),
       'new_native_runs':len(runs),'new_numerical_effects_accepted':0,'next_registered_not_run':str((CASE/'next_linear_work_control_not_run.json').relative_to(ROOT)),
       'physical_qualification_passed':False,'M6_qualification_passed':False,'expert_agent_claimed':False}
    save(CASE/'controls_batch_closed.json',complete)
    def fmt(x):return '—' if x is None else f'{x:+.6f}'
    table='\n'.join(f"| {r['method']} | {fmt(r['density_gain'])} | {fmt(r['SA_worsening'])} | {'Ölçülemedi: alan200, geçmiş390' if not r['comparable'] else 'Geçmedi'} |" for r in rows)
    md=f'''# CFD yakınsama araştırması: kontrollü yöntemler ve birim denetimi

25 Ekim 2026 · {len(runs)} yeni native SU2 koşusu · Genel fizik kabulü **false**.

Bu turda bir yakınsama çözümü bulunmadı. Küçük CFD kod kıyaslarında yerel uyum, yakınsama eksikliğiyle birlikte raporlandı. M6, RAE2822 ve gerçek İHA kabulleri kapanmadı.

## Gerçekte sınananlar

| Kontrollü değişiklik | Yoğunluk kazancı, log10 | SA kötüleşmesi, log10 | Ön kayıtlı etki |
|---|---:|---:|---|
{table}

Kazanç pozitifse ikinci yöntemin yoğunluk kalıntısı daha düşüktür; SA kötüleşmesi pozitifse türbülans kalıntısı daha yüksektir. Eşikler yoğunlukta en az0,3log iyileşme ve SA'da en fazla0,1log kötüleşmeydi. Bu etki testi fiziksel yeterlilik değildir. Her kıyasın koşulları ayrı sözleşmede sabitlendi; yöntemlerin farklı başlangıçlarını birbirine karşı başarı sıralaması yapmadık.

MG2 koşusu240s sınırında390. geçmiş satırında durdu. Son tam alan200. adımdadır; bu alana390/399 kalıntısı atanmadı ve399 etkisi hesaplanmadı. MG'nin çalışması süre bütçesinde tamamlanamadı; bu tek başına yöntemin işe yaramadığını kanıtlamaz.

## En önemli güvenilirlik düzeltmesi

Yalnız boyutsuzlaştırma kıyasında ham sayıları karıştırsaydık yoğunlukta **{scaling['spurious_unconverted_density_gain']:.6f}log** kazanç görünecekti. Aynı SI kalıntı tanımına çevrilince gerçek fark **{scaling['density_log10_gain']:.6f}log** kaldı ve0,3log eşiğini geçmedi. Yeni denetçi birimlendirme kanıtı eksik veya farklıysa karşılaştırmayı reddeder.

Restart dönüşümü kaynak koordinatlarını bit düzeyinde korudu; yoğunluk/hız/basınç SI geri dönüş farkı en çok2,55e-16 bağıl mertebesindeydi. Kaynak binary ve dönüştürülmüş binary ayrı SHA256 ile tutulur; aynı fiziksel başlangıç farklı byte dizisi olarak açıkça kaydedildi. Bu dönüşüm yalnız bu7-alanlı2B ideal gaz/SA biçimi ve1m referans uzunluğu için sınandı.

Analitik dönüşüm ve bozuk girdi için4 kontrol, eşli karşılaştırma için13 karşı örnek geçti. Gerçek native beş kalıntının tam özdeşliği için ilk taslakta kullanılan gerekçesiz1e-5log sınırı zayıf düşey momentumda2,31e-5log farkla geçmedi. Taslak korundu; yerine gevşetilmiş bir geçme sınırı konmadı. Bu gözlem fiziksel kabulü değiştirmedi.

## Yeni yöntem gerçekten kullanıldı mı?

SU2v8.5.0'ın resmî örneğindeki `NEWTON_KRYLOV` anahtarı iki ayrı on/off çiftinde kullanıldı. Kaynak kodu, Jacobian-vektör çarpımının sonlu farkla hesaplandığını gösteriyor; ek `_AD` programı gerekmedi. Bu uygulama ortalama akış denklemleri içindir; SA ayrı çözülür. Tam bağlı akış+SA, adjoint veya makaledeki artık yumuşatmalı Newton uygulaması değildir.

Soğuk çiftte iki kolun ilk20 geçmiş kaydı aynıydı. Newton'a özgü200 başlangıç adımı resmî örnekten korundu. Gelişmiş alan çiftinde başlangıç gecikmesi iki kolda da0 olarak kaydedildi. Bu iki çiftin farkını yalnız başlangıcın nedensel etkisi saymadık. Her iki on/off çiftinde kayıtlı ortak etki geçmedi; Newton yöntemini genel olarak başarısız ilan etmiyoruz.

Kaynak kodunda ayrıca kaba MG seviyelerinin CFL ve sönüm katsayılarını kendiliğinden değiştirdiği görüldü. Ana `CFL_ADAPT=NO` seçeneği bütün MG seviyelerini sabitlemiyor. Ön sözleşmedeki0,5 sönüm değerleri başlangıç değerleridir; sonradan bulunan açıklama ayrı kayda eklendi, özgün sözleşme değiştirilmedi.

## Alan ve kaynak sonuçları

Kaynak Cf eğrisi, iki hız profili ve türbülans viskozitesi profilleri bütün noktaları ve geçerlilik maskeleriyle CSV'ye çıkarıldı. Yeni olgun başlangıçlı kontrol alanları yerel kod kıyası ekranlarını geçti; bütün yeni alanlarda iteratif kabul açık kaldı. Soğuk Newton alanında Cf/hız/viskozite ekranları da geçmedi. Çözüme uysun diye kaynak nokta, fizik, ağ veya kabul eşiği değiştirilmedi.

Gelişmiş orta ağ Newton alanının SI yoğunluk kalıntısı−9,9730285:−10 eşiğini **geçmez**.−10'a yuvarlayarak kabul etmedik. Son100CD aralığı8,66e-10 ve maxy+0,482214 olması bu eksikliği kapatmıyor. Bu yerel kod kıyası deney doğrulaması veya3B kanat yeterliliği değildir.

![Aynı ince ağ ve başlangıç alanıyla kontrollü yakınsama](../plots/flatplate_convergence_controls_20261025.png)

## Kaynak araştırmasından seçilen sonraki iş

[SU2 doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/), iç doğrusal çözümü aşırı sıkı çözmenin toplam ilerlemeyi yavaşlatabileceğini açıklıyor. Sıradaki tek deney, aynı gelişmiş orta ağ alanında yalnız iç toleransı1e-6→1e-3 değiştirecek. Ön kayıt:200adım/120s, toplam akış+SA Krylov işinde en az%30 azalma; aynı SI kalıntıları en fazla0,05log kötüleşme;CD farkı<1e-7. **Henüz çalıştırılmadı.** Bu bir maliyet hipotezidir; otomatik fiziksel kabul veya sınırsız ayar taraması değildir.

[Mavriplis, arXiv1805.03756v1](https://arxiv.org/html/1805.03756v1), Newton devamında yerel artık yumuşatmasını inceliyor. Bu, ileri uygulama adayı olarak ayrıldı; hazır anahtarın o makaleyi uyguladığını iddia etmedik. [SU2v8.5.0 resmî Newton örneği](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/TestCases/rans/oneram6/turb_ONERAM6_nk.cfg) ve [uygulama kodu](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/integration/CNewtonIntegration.cpp) açılıp arşivlendi. [NASA TMR](https://tmbwg.github.io/turbmodels/flatplate_sa.html) kıyası iki bağımsız kodun sayısal referanslarıdır.

## Kanıt ve sınırlar

- Yeni mühürlerde{verified} dosya kaydı, ön-native kod arşivlerinde{code_verified} hash ve önceki düz plaka kayıtlarında{old_verified} hash yeniden doğrulandı.
- Temel regresyon26/26 geçti; geçen yazılım testleri fizik doğrulaması sayılmadı.
- Gerçek İHA girdileri önceki yayınla aynı kaldı. Yeni küçük model/prompt başarı yüzdesi veya LLM davranış iyileşmesi ölçülmedi.
- Bu normal geliştirme oturumu referansları biliyor; kör deney değil. Kodun başlangıçtan önce arşivlenmesi son sayısal çiftlerde eklendi; ilk kontrol kolları için son kaynak kodun anlık kaydı, o gün çalışan Python sürümünün bağımsız yürütme tasdiki değildir.
- Genel/keyfi CAD→otomatik güvenilir CFD hazır değil. Üç yakınsamış ağ, kapsamına uygun uzak alan ve deney/model sınırları ayrı kapılar olarak korunuyor.
'''
    path=ROOT/'outputs/reports/cfd_yakinsama_arastirmasi_20261025.md';path.write_text(md,encoding='utf-8')
    # Markdown source is escaped; scientific plot stays a standard standalone PNG.
    body=''.join('<p>'+html.escape(p).replace('\n','<br>')+'</p>' for p in md.split('\n\n') if not p.startswith('!['))
    page='''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD yakınsama araştırması</title><style>body{font:17px/1.65 Segoe UI,sans-serif;color:#20313d;background:#f4f7f8;max-width:1080px;margin:35px auto;padding:25px}article{background:white;padding:35px;border-radius:14px}p{overflow-wrap:anywhere}img{width:100%;background:white}a{color:#007d86}</style><article><h1>CFD yakınsama araştırması</h1><p>11 gerçek koşu · Fiziksel kabul açık</p>'''+body+'''<img src="../plots/flatplate_convergence_controls_20261025.png" alt="Kontrollü yakınsama grafikleri"><p><a href="cfd_yakinsama_arastirmasi_20261025.md">Markdown raporu</a> · <a href="flatplate_controls_integrity_20261025.json">Dosya ve koşu denetimi</a></p></article></html>'''
    (ROOT/'outputs/reports/cfd_yakinsama_arastirmasi_20261025.html').write_text(page,encoding='utf-8')
    evidence=[path,ROOT/'outputs/reports/cfd_yakinsama_arastirmasi_20261025.html',ROOT/'outputs/reports/flatplate_controls_integrity_20261025.json',
              ROOT/'outputs/reports/flatplate_pair_guards_20261025.json',ROOT/'outputs/reports/flatplate_scaling_guards_20261025.json',
              ROOT/'outputs/data/agent_learning/reviewer_ledger_flatplate_controls_20261025.json',CASE/'controls_batch_closed.json',CASE/'next_linear_work_control_not_run.json']
    evidence += [ROOT/'outputs/reports'/name for name in ['flatplate_fixed_cfl_control_20261025.json','flatplate_multigrid_control_20261025.json',
                 'flatplate_adaptive_toggle_20261025.json','flatplate_newton_control_20261025.json','flatplate_scaling_control_20261025.json',
                 'flatplate_newton_warm_control_20261025.json','flatplate_control_fields_20261025.json','flatplate_scaled_control_fields_20261025.json']]
    archive=ROOT/'outputs/data/task_evidence'/task['id'];archive.mkdir(exist_ok=True,parents=True)
    for n,p in enumerate(evidence):
        dst=archive/f'{n:02d}_{p.name}';shutil.copyfile(p,dst)
        task['evidence'].append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'archived':str(dst.relative_to(ROOT))})
    codefiles=list(BASE.glob('*.py'))+[ROOT/'work/reliability/paired_control.py',ROOT/'work/reliability/test_paired_control.py']
    codefolder=archive/'code_final';codefolder.mkdir()
    codehash={}
    for p in codefiles:
        dst=codefolder/p.name;shutil.copyfile(p,dst);codehash[str(dst.relative_to(ROOT))]=sha(dst)
    save(archive/'code_snapshot.json',{'created_utc':now(),'scope':'Final source snapshot; historical pre-native snapshots remain separately preserved','files_sha256':codehash})
    task.update(status='tamamlandı',phase='sınırlı kontrollü araştırma paketi kapandı',physical_qualification_passed=False,completed_utc=now())
    save(taskpath,task)
    print({'new_runs':len(runs),'new_hashes':verified,'old_hashes':old_verified,'code_hashes':code_verified,'report':str(path)},flush=True)

if __name__=='__main__':main()
