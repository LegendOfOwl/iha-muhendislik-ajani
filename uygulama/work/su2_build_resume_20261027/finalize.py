"""Close this bounded numerical experiment, without accepting physical design."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
CASE = ROOT / 'outputs/simulations/linecap_source_20261027_v1'
REPORT = ROOT / 'outputs/reports/su2_kaynak_karsilastirma_20261027.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    now = datetime.now(timezone.utc).isoformat()
    r = read(REPORT)
    assert r['new_native_CFD_runs'] == 3 and r['pristine_reproduction']['accepted'] is True
    assert type(r['cap_effect']['accepted']) is bool
    for key in ('physical_qualification_passed', 'M6_qualification_passed', 'LLM_improvement_demonstrated'):
        assert r[key] is False
    # Compare actual UAV inputs with the published v0.16 catalogue, not an assumed value.
    catalogue = read(ROOT.parent / 'iha-muhendislik-ajani/analizler/dosya_katalogu.json')
    originals = {row['source_path']: row['sha256'] for row in catalogue['files']
                 if row['source_path'].startswith('outputs/data/project/') and row['source_path'].endswith('.json')}
    assert len(originals) == 3
    for name, expected in originals.items():
        assert sha(ROOT / name) == expected, name
    evidence = []
    for path in (REPORT, REPORT.with_suffix('.md'), REPORT.with_suffix('.html'),
                 CASE / 'reproduction.json', CASE / 'effect.json', CASE / 'source_change.json',
                 ROOT / 'outputs/reports/su2_resume_checks_20261027.json'):
        evidence.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
    for path in (BASE / 'report_v1_before_visual_review/manifest.json', BASE / 'independent_review.json'):
        if path.exists():
            evidence.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
    preserved = {'checked_utc': now, 'reference': 'Published v0.16 catalogue',
                 'all_three_real_UAV_inputs_unchanged': True, 'files_sha256': originals}
    save(BASE / 'real_project_integrity.json', preserved)
    taskpath = ROOT / 'outputs/data/tasks/20261027-154600-18828f.json'
    task = read(taskpath)
    assert task['project_id'] == 'qualification'
    for name, expected in task['input_sha256'].items():
        assert sha(ROOT / name) == expected, name
    task.update(status='tamamlandı', phase='sınırlı üç-kol kaynak karşılaştırması raporlandı',
                finished_utc=now, blocked_by=[], physical_qualification_passed=False,
                M6_qualification_passed=False, LLM_improvement_demonstrated=False,
                completion_scope='Bounded experiment and report only; required physical gates remain open',
                cap_effect_accepted=r['cap_effect']['accepted'], new_native_runs=3,
                general_qualification_open=['mesh', 'farfield', 'experiment', 'RAE2822', 'M6', 'UAV'],
                next_required_step='Source-backed passive measurement of the true inner linear residual on a fixed-state diagnostic; preregister before native execution')
    existing = {entry['path'].replace('\\', '/'): entry for entry in task['evidence']}
    existing.update({entry['path']: entry for entry in evidence})
    task['evidence'] = list(existing.values())
    save(taskpath, task)
    setup = ROOT / 'work/setup/su2_source_build_install.json'
    record = read(setup)
    record.update(updated_utc=now, status='pristine_source_built_and_reproduced; cap256_control_completed',
                  reference=REPORT.relative_to(ROOT).as_posix(), report_sha256=sha(REPORT),
                  source_builds=r['source_and_recipe']['builds'], pristine_reproduction_accepted=True,
                  registered_cap_effect_accepted=r['cap_effect']['accepted'],
                  native_release_executable_replaced=False, default_solver_changed=False,
                  physical_qualification_passed=False, M6_qualification_passed=False,
                  LLM_improvement_demonstrated=False,
                  scope='Local source-build and one 2D numerical mechanism diagnostic; not a general CFD qualification')
    save(setup, record)
    statepath = ROOT / 'PROJECT_STATE.md'
    state = statepath.read_text(encoding='utf-8')
    marker = '## 27 Ekim: kaynak derlemesi yeniden üretildi ve uzun çizgi sınandı'
    if marker in state:
        print({'bounded_experiment_already_recorded': True, 'current_report_evidence_updated': True})
        return
    a, b = r['arms']['build32'], r['arms']['build256']
    m = r['cap_effect']['metrics']
    state += ('\n\n' + marker + '\n\n'
        '- Önceki başarısız derleme ve RAM reddi korundu. Kaynak baytları değişmeden yalnız hata veren çeviri birimine include yolu eklendi; 258 doğrulanmış nesne korunarak kalan32 hedef81,063s içinde derlendi. Aynı290 etkin komut tarifiyle ayrı cap256 derlemesi761,485s tamamlandı. Kurulu resmî çözücü değiştirilmedi.\n'
        '- Aynı kaynak ağ/fine3999 seed/fizikle üç yeni200-adımlık native koşu; tamamında alan/geçmiş199 eşleşti. Resmî32/kaynak32 yeniden üretimi geçti; beş SI log10 RMS eğrisindeki en büyük fark0,00175396, sonCD farkı0. Bu yalnız dar sayısal yeniden üretim kabulüdür.\n'
        f'- Yalnız MAX_LINELET_POINTS32→256: gerçek üyelik{a["native_membership_nodes"]}→{b["native_membership_nodes"]}; aynı eski sıralı-aşama RHS yoğunluk kare payı%{100*a["fixed_old_RHS_Rho_squared_share"]:.6f}→%{100*b["fixed_old_RHS_Rho_squared_share"]:.6f}. Yoğunluk kazancı{m["density_log10_gain"]:.8f}log<0,3; SA kötüleşmesi{m["SA_log10_worsening"]:.8f}log; toplamKrylov16000→16000 ve süre{a["elapsed_seconds"]:.3f}→{b["elapsed_seconds"]:.3f}s. Ortak etki kabulüfalse; bütün yoğunluk artığının kapsanması iyileşmeyi garanti etmedi.\n'
        '- Her iki kaynak kolunda flow+SA bütün200 adımda40 tavanda; Krylov≤1,5 kapısı burada ayırt edici değil, uzun çizgilerin aritmetik maliyetini temsil etmez. LinSolRes Givens tabanlı kestirimdir; bağımsız gerçek lineer artık diye sunulmadı. Tek süre çifti genel performans ölçümü değildir.\n'
        f'- {r["new_distinct_checks"]} yeni yazılım kontrolü geçti; eski70 tekrar sayılmadı. {r["old_output_integrity"]["hash_records_verified"]} eski/{r["new_output_integrity"]["hash_records_verified"]} yeni ham hash denetlendi; gerçekİHA3girdisi v0.16 ile aynı. Rapor outputs/reports/su2_kaynak_karsilastirma_20261027.html.\n'
        '- Genel fizik/RAE2822/M6/VLM/İHA kabulüfalse, GCI null. Eski fine3999 rolü korunur; bu tanısal kol üç-ağ ailesine eklenmez. LLM uzmanlığı/iyileşmesi ölçülmedi. Sonraki yöntem adayı: sabit durumda gerçek iç lineer artığın pasif ölçümü ve kestirimden ayrılması; henüz çalıştırılmadı, yeni ön kayıt gerekir. Görev20261027-154600-18828f yalnız bu sınırlı deney/rapor paketi için kapandı.\n')
    statepath.write_text(state, encoding='utf-8')
    print({'bounded_experiment_completed': True, 'cap_effect_accepted': r['cap_effect']['accepted'],
           'real_UAV_inputs_unchanged': len(originals), 'physical_qualification_passed': False})


if __name__ == '__main__':
    main()
