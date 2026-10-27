"""Seal the three-run diagnostic batch; no promotion into the frozen CFD family."""
from pathlib import Path
import sys, os, io, unittest, shutil, html
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'work/flatplate_20261025'))
from prepare import CASE as OLD, read, save, sha, now
from run import history
from scaled_restart import scales


def main():
    taskpath = ROOT / read(BASE / 'task.json')['path']
    task = read(taskpath)
    assert task['status'] != 'tamamlandı'
    case = ROOT / 'outputs/simulations/flatplate_20261027_v1'
    coverage = read(ROOT / 'outputs/reports/linelet_coverage_20261027.json')
    audit = read(ROOT / 'outputs/reports/linelet_coverage_audit_20261027.json')
    partition = read(ROOT / 'outputs/reports/prec_partition_control_20261027.json')
    assert coverage['native_membership_accepted'] and audit['passed']
    assert partition['quality']['comparable'] and not partition['effect_passed']
    assert sha(ROOT / coverage['data_csv']) == coverage['data_csv_sha256']
    assert sha(case / 'linelet_coverage/contract.json') == task['coverage_contract_sha256']
    assert sha(case / 'prec_partition/contract.json') == task['partition_contract_sha256']
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(BASE), pattern='test_coverage_partition.py')
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (BASE / 'guard_results.txt').write_text(log.getvalue(), encoding='utf-8')
    guards = {'checked_utc': now(), 'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'passed': result.wasSuccessful(),
              'log_sha256': sha(BASE / 'guard_results.txt'), 'physical_qualification_passed': False}
    save(ROOT / 'outputs/reports/coverage_partition_guards_20261027.json', guards)
    assert result.testsRun == 17 and result.wasSuccessful()
    newhash = oldhash = codehash = 0
    runs = []
    for p in OLD.rglob('prediction_frozen.json'):
        for f, h in read(p)['files_sha256'].items():
            assert sha(ROOT / f) == h, f
            oldhash += 1
    for p in sorted(case.rglob('prediction_frozen.json')):
        s = read(p)
        for f, h in s['files_sha256'].items():
            assert sha(ROOT / f) == h, f
            newhash += 1
        for f, h in read(p.parent / 'code_before_native.json')['files_sha256'].items():
            assert sha(ROOT / f) == h, f
            codehash += 1
        assert s['native_status']['exit_code'] == 0
        assert s['matched']['field_iteration'] == s['matched']['terminal_history_iteration']
        runs.append({'folder': str(p.parent.relative_to(ROOT)), 'seal_sha256': sha(p),
                     'native_status': s['native_status'], 'matched': s['matched']})
    assert len(runs) == 3
    real = {}
    for p in (ROOT / 'outputs/data/project').glob('*.json'):
        assert sha(p) == sha(ROOT.parent / 'iha-muhendislik-ajani/uygulama/outputs/data/project' / p.name)
        real[str(p.relative_to(ROOT))] = sha(p)
    for row in read(BASE / 'sources/manifest.json'):
        assert sha(ROOT / row['path']) == row['sha256']
    integrity = {'checked_utc': now(), 'new_native_runs': runs,
                 'new_raw_hash_records_verified': newhash, 'old_raw_hash_records_verified': oldhash,
                 'pre_native_code_hash_records_verified': codehash,
                 'real_UAV_inputs_unchanged_vs_v0_14': real, 'source_manifest_sha256': sha(BASE / 'sources/manifest.json')}
    save(ROOT / 'outputs/reports/coverage_partition_integrity_20261027.json', integrity)
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'work/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    factors = scales(read(OLD / 'contract.json')['derived_freestream'])['residual']
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    for name, label in [('auto4', 'Default partitions (0 -> 4)'), ('single', 'One preconditioner partition')]:
        h = history(case / 'prec_partition' / name)
        x = [r['Inner_Iter'] for r in h]
        axes[0, 0].plot(x, [r['rms[Rho]'] + np.log10(factors['rms[Rho]']) for r in h], label=label)
        axes[0, 1].plot(x, [r['rms[nu]'] + np.log10(factors['rms[nu]']) for r in h], label=label)
        axes[1, 0].plot(x, np.cumsum([r['Linear_Solver_Iterations'] + r['LinSolIterTurb'] for r in h]), label=label)
        axes[1, 1].plot(x, [r['Avg CFL'] for r in h], label=label)
    for ax, label in zip(axes.flat, ['SI log10 density residual', 'SI log10 SA residual',
                                   'Cumulative flow+SA Krylov iterations', 'Reported average CFL']):
        ax.set(xlabel='Fresh-restart iteration', ylabel=label)
        ax.grid(alpha=.2)
        ax.legend()
    axes[0, 0].axhline(-10, ls=':', color='gray')
    fig.suptitle('Same native total four threads; same adaptive policy, not identical CFL trajectories')
    fig.tight_layout()
    fig.savefig(ROOT / 'outputs/plots/prec_partition_20261027.png', dpi=160)
    plt.close(fig)
    nextplan = {
        'created_utc': now(), 'status': 'proposed_not_built_not_run',
        'basis': ['Measured native linelet coverage leaves46.1% density squared RHS outside',
                  'A single LU_SGS partition failed registered benefit and cost gates',
                  'Longer lines retain line-implicit Jacobi semantics; no proof they fix missing transverse coupling'],
        'next_method': 'Controlled source-build feasibility, then one length-cap mechanism test; no parameter sweep',
        'required_order': [
            'Pin pristineSU2v8.5.0 source/compiler/dependencies/build options; retain LGPL notice and source hashes',
            'Reproduce unchanged32-point binary result on the same source grid and original fine3999 seed before attributing any modified-binary difference to the cap',
            'Register reproducibility limits, activation checks, matched200-step comparison and both timing/Krylov budgets before native runs',
            'If the build-control passes, modify only MAX_LINELET_POINTS32->256;193 normal nodes on this grid do not imply the algorithm follows a full normal column',
            'Export native LINELET union again; require increased actual coverage, not a claim from the constant alone',
            'Freeze all successful/failed predictions; compare density/SA effect and observed elapsed cost; never promote into old three-grid family'],
        'not_implemented': ['No modifiedSU2binary', 'No full-line/SGS hybrid', 'No arXiv residual-smoothing source term'],
        'physical_qualification_passed': False,
        'sources': ['https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/include/geometry/CGeometry.hpp',
                    'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/geometry/CGeometry.cpp',
                    'https://web.stanford.edu/group/ctr/ResBriefs/2011/26_palacios.pdf',
                    'https://arxiv.org/abs/1805.03756'],
    }
    save(BASE / 'next_method_plan_not_run.json', nextplan)
    q = partition['quality']
    outcomes = {'created_utc': now(), 'scope': 'Three-native-run membership and one-partition diagnostic; not blind',
                'native_membership_accepted': True, 'partition_effect_passed': False,
                'physical_qualification_passed': False, 'M6_qualification_passed': False,
                'LLM_behaviour_improvement_measured': False, 'new_native_runs': 3, 'new_software_tests': 17,
                'next_method_plan': str((BASE / 'next_method_plan_not_run.json').relative_to(ROOT))}
    save(case / 'batch_closed.json', outcomes)
    ledger = {'created_utc': now(), 'instruction_snapshot': task['agent_instruction_snapshot'],
              'observations': ['Native graph colors are not individual line IDs',
                               'Measured union7200 of52689 nodes, separate-stage squared residual shares retained',
                               'Default-to-single LU_SGS partition failed preregistered residual/work/time gates'],
              'behavioral_risks': ['Confusing source length cap with observed spatial coverage',
                                  'Calling fewer additive domains unconditionally stronger or faster',
                                  'Treating Euler/M6 paper results as validation of SA-neg flatplate',
                                  'Selecting near-threshold diagnostic output as replacement fine-family role'],
              'physical_hypotheses': [{'name': 'Length cap contributes to incomplete coupling', 'status': 'unproven'},
                                      {'name': 'One LU_SGS domain is sufficient at acceptable cost', 'status': 'not_supported_in_this_pair'}],
              'lessons': 'ExistingL04/L05/L08/L09/R01/R03 cover these risks; no duplicate prompt rule and no benchmark targets copied to analyst memory',
              'process_error': {'kind': 'generic_test_module_name_import_collision',
                                'retained_failure_log': 'work/flatplate_20261027/guard_results_v1_import_collision.txt',
                                'correction': 'Use unique test_coverage_partition module name',
                                'native_outputs_affected': False},
              'new_prompt_version': False, 'new_blind_LLM_test': False}
    save(ROOT / 'outputs/data/agent_learning/reviewer_ledger_coverage_partition_20261027.json', ledger)
    def table(headers, rows):
        return '| ' + ' | '.join(headers) + ' |\n|' + '|'.join(['---'] * len(headers)) + '|\n' + '\n'.join('| ' + ' | '.join(map(str, r)) + ' |' for r in rows)
    rows = []
    for i, label in enumerate(['Varsayılan bölünme0→4', 'Tek önkoşullayıcı bölgesi1']):
        m = partition['SI'][i]['matched']
        raw = partition['raw'][i]
        rows.append([label, f"{m['rms[Rho]']:.9f}", f"{m['rms[nu]']:.9f}",
                     partition['work_counts'][i]['total'], f"{raw['native_status']['seconds']:.3f}", f"{m['CD']:.12f}"])
    results_table = table(['Kol', 'Yoğunluk,SI log10', 'SA,SI log10', 'Krylov toplamı', 'Gözlenen süre,s', 'CD'], rows)
    md = f'''# Gerçek LINELET kapsamı ve önkoşullayıcı bölünmesi

27 Ekim 2026 · Üç gerçek native SU2 koşusu · Yeni genel fizik/M6/İHA kabulü **false**.

Bu tur, önceki başarısız LINELET denemesinin gerçekten hangi bölgeyi içerdiğini ölçtü. Ardından kaynak kodundaki LU-SGS bölünmesini kaldıran tek kontrollü yöntem sınandı. **Kapsam ölçümü geçti; yeni çözüm ayarı etki/maliyet kabulünü geçmedi.** Bu sabit2B SA-neg kaynak benchmarkıdır; yeni bir uçak analizi veya körLLM değerlendirmesi değildir.

## Kaynak sabiti yerine gerçek kapsam

KuruluSU2v8.5.0'ın CFVMOutput uygulaması, LINELET seçiliyken native `Linelet` alanını dışarı yazabiliyor. Kaynak geometrinin `lineletColor` dizisi kullanılır:0 çizgi dışı, pozitif tamsayılar komşuluk renklendirmesidir. Aynı rengi paylaşan noktalar tek bir çizgi sayılmadı.

Ön kayıttan sonra aynı özgünfine3999 ND başlangıç dosyasıyla **tek implicit adım** çalıştırıldı. Fizik/ağ aynı;200→1adım, yazma sıklığı1 ve ekLINELET çıktısı ölçüm değişiklikleridir. Nativeexit0;1,563s, yaklaşık0,294GiB örneklenmiş tepe çalışma kümesi. Alan/yüzey/restart/geçmiş0 eşleşip mühürlendi. Bu adımın amacı yakınsama değildir.

-52689 düğümün **7200'ü (%13,6651)** gerçek LINELET birliğinde.
- Birliğin y aralığı0–**{coverage['covered_y_extent_m'][1]:.11g}m**, yaklaşık53,1µm.
- Önceki doğrulanmış aşamaRHS haritasının yoğunluk kare toplamının **%{100*coverage['covered_Rho_squared_share']:.5f}**'i bu birlik içinde; **%{100*coverage['uncovered_Rho_squared_share']:.5f}**'i dışında.
- SA kare toplamının yalnız **%{100*coverage['covered_nu_squared_share']:.6f}**'i içinde. Yoğunluk ve SA farklı denklemlerdir; bu paylar tek fiziksel hata bütçesi olarak toplanmaz.
-52689 nokta bire bir eşlendi, en büyük koordinat farkı6,51e-8m; ön kayıtlı sınır2e-7m. Bütün düğümler CSV'de kaldı. Bağımsız tablo denetimi işaret/renk/tamsayı/üyelik ve normalize negatif olmayan kare paylarını yeniden kontrol etti.

![Gerçek native çizgi birliği ve ayrı aşamaRHS](../plots/linelet_coverage_20261027.png)

Bu, yeni implicit alanın yeniden hesaplanmış artığı değildir. Geometriye bağlı statik üyelik, **önceki ayrı explicit gözlemin sıralı akış/SA aşamaRHS** değerleriyle eşlendi. Artık payı ağ hata bandı veya başarısızlığın kesin nedeni değildir.32nokta sınırı kaynakta sabittir; uzunluğun artırılması da izotropi/yön/komşuluk durdurmalarını kaldırmaz. Native alanın renkleri benzersiz çizgi kimliklerini vermez.

## Kaynakla gerekçeli tek değişken

CSysMatrix, `LINEAR_SOLVER_PREC_THREADS=0` iken maksimumOpenMP iş parçacığı sayısını bölge sayısı olarak kullanıyor. LU-SGS alt/üst üçgensel çarpımları her bölgenin başlangıç/bitiş satırıyla sınırlanıyor; kaynak, thread-halo olmadığına açıkça işaret ediyor. `=1` tek üçgensel bölge seçer. Bu, sınır ötesi üçgensel bağlaşımı geri getirebilir hipoteziyle sınandı; varsayılan ayarın kesin hata olduğu kabul edilmedi.

İki kolun toplam native iş parçacığı sayısı **dört** kaldı. Configler yalnızPREC_THREADS0/1 satırında farklı. Aynı özgünfine3999 seed baytları,52224hücre/52689nokta kaynak ağı,LU_SGS/FGMRES40 ve iç tolerans0,001 kullanıldı. Her kolda200adım/240s üst bütçe,2,5GiB bellek sınırı; fizik ve kabul eşikleri değiştirilmedi. Aynı adaptiveCFL politikası korundu, gerçekleşen CFL yörüngeleri eşitlenmedi. Bu fark politika geri beslemesini de içerir. Native bölge dizisi doğrudan dışarı yazılmadı;0→4/1 yorumu kabul edilen config ve eşleşen8.5.0 kaynak semantiğine dayanır.

{results_table}

Her iki nativeexit0 ve alan/geçmiş199 eşleşti; son100örnek mevcut. Yoğunluk kazancı **{q['density_log10_gain']:.8f}log10**, gereken≥0,3'ün altında. SA kötüleşmesi **{q['SA_log10_worsening']:+.8f}log10**; negatif değer iyileşmedir ve≤0,1 şartını geçer. Toplam akış+SA Krylov oranı **{partition['work_ratio']:.8f}**, kayıtlı≤1,5'i geçmedi. Süre oranı **{partition['observed_time_ratio']:.8f}**, önceden kayıtlı≤1,5'i geçmedi. **Ortak etki false.** Tek süre çifti evrensel hız ölçümü değildir; donanım/işletim sistemi yükü etkisini ayıran performans çalışması yapılmadı. Bu sınırlama, başarısız yoğunluk/Krylov sonuçlarını değiştirmez.

![Aynı başlangıçtan iki bölünme kolu](../plots/prec_partition_20261027.png)

Tek bölge yoğunlukSI≈−9,934705 ile **−10 eşiğini geçmez**. Yakın görünmesi kabul değildir. Bu200adımlık tanı eski üç-ağ ailesindekifine3999 rolünün yerine konmadı; aile ve genel fizik kabulleri kapatılmadı. Süreyi/iterasyonu otomatik uzatmadık,2/3bölge değerlerini taramadık.

## Literatürden çıkan uygulanabilir ayrımlar

[Palacios ve Alonso,2011](https://web.stanford.edu/group/ctr/ResBriefs/2011/26_palacios.pdf), gerilmiş ağlarda çizgi normalindeki bağlantıları blok üç köşegen çözüme alan LINELET'i ve çizgi dışında Jacobi kullanımını anlatır. Gösterilen kıyasın Jacobi'ye karşı olması, bizimLU-SGS ayarımızdan daha iyi olacağını kanıtlamaz. Çizgileri uzatmak başka yönlerdeki bağlaşımı kendiliğinden güçlendirmez.

[Chiew ve Aftosmis,ICCFD12,2024](https://iccfd.org/iccfd12/assets/pdf/papers/ICCFD12_Paper_10-A-04.pdf), matrix-free implicit önkoşullama ve Krylov uzayı maliyetini incelemiş. Daha büyük uzayların daha güçlü artık düşüşüyle birlikte daha fazla iş getirebildiği için toplam süreyi ayrıca ölçüyorlar. **Bu makalenin testleriEuler/Cart3D**; girişindeRANS tartışılması bizimSA-negRANS'ın doğrulandığı anlamına gelmez. Buraya aktarılan ilke, artık ile maliyeti ayrı kabul etmektir.

[Mavriplis,arXiv1805.03756](https://arxiv.org/abs/1805.03756), Newton devamını yumuşatan ek artık kaynak terimi önerir. Buradaki nativeNEWTON_KRYLOV veyaLINELET bu kaynak teriminin uygulanması değildir. Yöntemi yalnız config ismini değiştirerek kurmuş sayamayız. Önceki soğuk/sıcakNewton çiftlerinin sonuçları da korunuyor.

## Sonraki yöntem ve gereken kontrol

Art arda yeni sayı denemek yerine, **uzun çizgili kaynak derlemesini** ayrı yöntem adayı olarak kaydettik. Henüz yeni binary derlenmedi ve bu aday çalıştırılmadı. Önce değişmemişv8.5.0 kaynak derlemesi aynı başlangıç/konfigürasyonda mevcut32noktalı sonucu yeniden üretmeli; derleyici/binary farkı ayar etkisiyle karıştırılmamalı. Ancak bu kontrol geçerse tek sabit32→256 değişimiyle gerçek native kapsam yeniden ölçülebilir.256, bu kaynak ağdaki193normal düğümden büyük bir tavan adayıdır; algoritmanın bütün normal sütunu izlediği veya bütün sınır tabakasını çözdüğü iddia edilmez.

Maliyet ve karşılaştırma eşikleri yeni native çalışmalardan önce kaydedilmeli; aynı-binary kontrolü geçmeden değiştirilmişbinary'den nedensel sonuç çıkarılmamalı. Hibrit çizgi+SGS, arXiv yumuşatması ve genel keyfiCAD ağı **uygulanmış değil**. [Sonraki yöntem kaydı](../../work/flatplate_20261027/next_method_plan_not_run.json).

## Kayıt, test ve kapsam

17yeni karşı örnek/yazılım testi geçti: negatif/eksik/sonlu olmayan paylar, renklerin çizgi kimliği sanılması, yanlış şekilli veri ve süre/iş kabulünde yanıltıcı sonuçlar reddediliyor. İlk kayıtçı genel test_guards adı nedeniyle eski başka klasörün test modülünü yükledi ve durdu; hata logu korundu, benzersiz test_coverage_partition adıyla düzeltildi. Yeni CFD koşusu gerekmedi; ham native çıktılar değişmedi. Bu testlerCFD fiziğini veyaLLM uzmanlığını doğrulamaz.

{newhash} yeni ham hash, {codehash} ön-native kod hash'i ve {oldhash} önceki dondurulmuş CFD hash'i yeniden doğrulandı. GerçekİHA'nın{len(real)} girdisi v0.14 ile aynı. Kaynak URL/zaman/SHA kayıtları ve SU2 lisansının özgün kopyası korunuyor. Ders defterinde gözlem/olası davranışsal risk/fizik hipotezi ayrı; mevcut dersler yeterli olduğundan hedef benchmark değerleri analizci hafızasına taşınmadı. Yeni prompt sürümü veya körLLM iyileşme ölçümü yok. GenelM6/RAE/VLM/İHA kabulleri **false**,GCI **null**.

[Kapsam ölçümü](linelet_coverage_20261027.json) · [Bağımsız tablo denetimi](linelet_coverage_audit_20261027.json) · [Bölünme sonucu ve tüm kapılar](prec_partition_control_20261027.json) · [17yazılım testi](coverage_partition_guards_20261027.json) · [Ham/eskisonuç mühür denetimi](coverage_partition_integrity_20261027.json)

Birincil uygulama kaynakları: [nativeLINELET çıktısı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/output/CFVMOutput.cpp), [LU-SGS bölünmesi](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/linear_algebra/CSysMatrix.cpp), [kurulu seçenek kaydı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/CConfig.cpp), [LINELET sınırı](https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/include/geometry/CGeometry.hpp), [resmî doğrusal çözücü rehberi](https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/).
'''
    # Normalize list markers without changing source numbers or paths.
    md = md.replace('\n+-', '\n- ').replace('\n-52689', '\n- 52689')
    report = ROOT / 'outputs/reports/cfd_cizgi_kapsami_20261027.md'
    report.write_text(md, encoding='utf-8')
    htmlrows = ''.join('<tr>' + ''.join('<td>' + html.escape(str(x)) + '</td>' for x in r) + '</tr>' for r in rows)
    body = f'''<h1>CFD çizgi kapsamı ve bölünme testi</h1><p class="lead">Gerçek kapsama ölçüldü; yeni çözüm ayarı ortak etkiyi geçmedi.</p>
<p>27 Ekim2026 · Üç native koşu · Genel fizik/M6/İHA kabulü <strong>false</strong>.</p>
<h2>LINELET nerede çalışıyor?</h2><p>52689 düğümün7200'ü çizgilerde. Önceki doğrulanmış aşama artığının yoğunluk kare toplamının%53,8965'i içeride,%46,1035'i dışarıda. Bu yerel kapsam ölçümüdür; neden veya ağ hata bandı değildir.</p>
<img src="../plots/linelet_coverage_20261027.png" alt="Native üyelik ve ayrı aşama artığı">
<h2>Tek bölge testi</h2><p>Toplam dört iş parçacığı korunarak yalnız önkoşullayıcı bölünmesi kaldırıldı. Yoğunluk kazancı0,14072log; gereken0,3. Krylov oranı1,54405 ve gözlenen süre oranı3,62358; iki maliyet sınırı1,5. Ortak kabul geçmedi.</p>
<div class="scroll"><table><tr><th>Kol</th><th>Yoğunluk,SI log</th><th>SA,SI log</th><th>Krylov</th><th>Süre,s</th><th>CD</th></tr>{htmlrows}</table></div>
<img src="../plots/prec_partition_20261027.png" alt="İki kolun SI artık, iş ve CFL geçmişi">
<h2>Sonraki yöntem</h2><p>Uzun çizgili kaynak derlemesi aday olarak kaydedildi; henüz kurulmadı/çalışmadı. Önce değiştirilmemiş derleme mevcut32noktalı sonucu yeniden üretmeli. Makaledeki artık yumuşatmasını native seçeneğimizin uyguladığını iddia etmiyoruz.</p>
<p>17yazılım kontrolü geçti; eski üç-ağfine3999 sonucu ve fizik kabulleri korundu. YeniLLM davranış iyileşmesi ölçülmedi.</p>
<p><a href="cfd_cizgi_kapsami_20261027.md">Ayrıntılı rapor, kaynaklar ve sonraki yöntem</a> · <a href="prec_partition_control_20261027.json">Tüm sonuçlar</a> · <a href="coverage_partition_integrity_20261027.json">Mühür denetimi</a></p>'''
    report.with_suffix('.html').write_text('<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD çizgi kapsamı</title><style>body{font:16px/1.65 Segoe UI,sans-serif;background:#edf3f6;color:#20313d;max-width:1180px;margin:25px auto;padding:20px}article{padding:28px;background:white;border-radius:12px}h1{line-height:1.2}.lead{font-size:21px}img{width:100%}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dbe3e8;padding:9px;text-align:left}th{background:#e9f1f4}h2{margin-top:30px}a{color:#006976}</style><article>' + body + '</article></html>', encoding='utf-8')
    evidence = [report, report.with_suffix('.html'), case / 'batch_closed.json', BASE / 'next_method_plan_not_run.json',
                ROOT / 'outputs/data/agent_learning/reviewer_ledger_coverage_partition_20261027.json']
    evidence += [ROOT / 'outputs/reports' / n for n in ['linelet_coverage_20261027.json', 'linelet_coverage_audit_20261027.json',
                 'prec_partition_control_20261027.json', 'coverage_partition_guards_20261027.json', 'coverage_partition_integrity_20261027.json']]
    archive = ROOT / 'outputs/data/task_evidence' / task['id'] / 'closure'
    archive.mkdir(parents=True)
    for i, p in enumerate(evidence):
        target = archive / f'{i:02d}_{p.name}'
        shutil.copyfile(p, target)
        task['evidence'].append({'path': str(p.relative_to(ROOT)), 'sha256': sha(p), 'archived': str(target.relative_to(ROOT))})
    code = archive / 'code_final'
    code.mkdir()
    for p in BASE.glob('*.py'):
        shutil.copyfile(p, code / p.name)
    save(archive / 'code_snapshot.json', {'created_utc': now(), 'files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in code.glob('*.py')}})
    task.update(status='tamamlandı', phase='üç koşuluk kapsam ve bölünme paketi kapandı', completed_utc=now(),
                physical_qualification_passed=False, native_membership_accepted=True, partition_effect_passed=False,
                next_method_implemented=False)
    save(taskpath, task)
    with (ROOT / 'PROJECT_STATE.md').open('a', encoding='utf-8') as f:
        f.write(f'\n\n## 27 Ekim: gerçek LINELET kapsamı ve tek bölge kontrolü\n\n- Görev{task["id"]}:3yeni nativeSU2 koşusu. NativeLINELET alanı ile7200/52689düğüm (%13,6651),ymax53,1µm ölçüldü. Eski doğrulanmış sıralı aşamaRHS yoğunluk kare payının%53,8965\'i kapsandı; SA%0,014798. Renkler çizgiID değil, yeniimplicit alanın yeniden hesaplanan artığı değil; nedensellik/ağ hata bandı yok.\n- Kaynakla gerekçeli PREC_THREADS0→1 tek değişkeni, toplam-t4 korunarak200adım/240s iki taze kolda sınandı. Yoğunluk kazancı0,14072006log<0,3; SA kötüleşmesi−0,18100537log; Krylov6924→10691,oran1,54404968>1,5; gözlenen süre65,047→235,703s,oran3,62357987>1,5. Ortak etki false, genel hızlanma iddiası yok.\n- İki alan/geçmiş199 eşleşti. Tek bölge SIyoğunluk−9,93470529,−10 hedefini geçmez. Eski fine3999 rolü/fizik/M6/RAE/VLM/İHA kabulleri false,GCI null.17yeni kod karşı örneği geçti;{newhash} yeni ham/{codehash} ön-nativekod/{oldhash} eski hash ve gerçekİHA{len(real)}girdi doğrulandı.\n- Rapor outputs/reports/cfd_cizgi_kapsami_20261027.html. Literatür Euler/Cart3D ile SA-negRANS kapsamını ayırır; arXiv artık yumuşatması nativeNK diye sunulmadı. Uzun çizgili kaynak derlemesi sonraki aday, önce değişmemişbinarykontrolü gerekli; henüz derlenmedi/çalışmadı. Yeni körLLM/promptuzmanlığı ölçülmedi.\n')
    print({'report': str(report), 'native_runs': 3, 'new_raw': newhash, 'old_raw': oldhash, 'pre_native_code': codehash, 'tests': 17})


if __name__ == '__main__':
    main()
