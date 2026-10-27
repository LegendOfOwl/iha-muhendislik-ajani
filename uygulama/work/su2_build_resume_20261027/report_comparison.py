"""Report only a completed, authenticated three-arm source comparison.

No solver/build is launched here. Importing is read only. Missing cap data,
unaccepted payload extraction or stale decisions stop main() before outputs.
Old scientific files, task/state/install records and publication are untouched.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import html
import json
import math
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
OLD_BASE = ROOT / 'work/su2_build_20261027'
CASE = ROOT / 'outputs/simulations/linecap_source_20261027_v1'
HOME = ROOT / 'tools/su2-build/v8.5.0/controls'
STEM = 'su2_kaynak_karsilastirma_20261027'
ARMS = ('release32', 'build32', 'build256')
LABELS = {'release32': 'Resmî release32', 'build32': 'Kaynak32', 'build256': 'Kaynak256'}
COLORS = {'release32': '#425466', 'build32': '#087f8c', 'build256': '#bf5b17'}
COMPONENTS = ('Rho', 'RhoU', 'RhoV', 'RhoE', 'nu')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def finite(value):
    value = float(value)
    assert math.isfinite(value)
    return value


def render(markdown):
    """Small stdlib renderer, matching the earlier report with image support."""
    def inline(value):
        value = html.escape(value)
        value = re.sub(r'!\[([^]]*)\]\(([^)]+)\)', r'<img alt="\1" src="\2">', value)
        value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
        value = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)
        return re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', value)
    output, table, listing = [], False, False
    for line in markdown.splitlines():
        if table and not line.startswith('|'):
            output.append('</tbody></table>'); table = False
        if listing and not line.startswith('- '):
            output.append('</ul>'); listing = False
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if all(re.fullmatch(r'[: -]+', cell) for cell in cells):
                continue
            tag = 'td' if table else 'th'
            if not table:
                output.append('<table><tbody>'); table = True
            output.append('<tr>' + ''.join('<' + tag + '>' + inline(cell) + '</' + tag + '>' for cell in cells) + '</tr>')
        elif line.startswith('## '): output.append('<h2>' + inline(line[3:]) + '</h2>')
        elif line.startswith('# '): output.append('<h1>' + inline(line[2:]) + '</h1>')
        elif line.startswith('- '):
            if not listing:
                output.append('<ul>'); listing = True
            output.append('<li>' + inline(line[2:]) + '</li>')
        elif line.strip(): output.append('<p>' + inline(line) + '</p>')
    if table: output.append('</tbody></table>')
    if listing: output.append('</ul>')
    return '\n'.join(output)


def verify_seals(folders):
    records, paths, seal_records = 0, {}, []
    for folder in folders:
        sealpath = folder / 'prediction_frozen.json'
        seal = read(sealpath)
        assert seal['files_sha256'], 'Empty raw prediction seal: ' + rel(sealpath)
        for name, expected in seal['files_sha256'].items():
            path = ROOT / name
            assert sha(path) == expected, 'Frozen raw file changed: ' + name
            normalized = rel(path)
            assert normalized not in paths or paths[normalized] == expected
            paths[normalized] = expected
            records += 1
        seal_records.append({'path': rel(sealpath), 'sha256': sha(sealpath),
                             'raw_hash_records': len(seal['files_sha256'])})
    return {'hash_records_verified': records, 'unique_paths_verified': len(paths),
            'seals': seal_records, 'all_matched': True}


def raw_linear_summary(arm, payload, limit):
    with (CASE / arm / 'history.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = [{key.strip(): value.strip() for key, value in row.items()}
                for row in csv.DictReader(stream, skipinitialspace=True)]
    assert len(rows) == len(payload['history'])
    flow, turbulence = [], []
    for raw, item in zip(rows, payload['history']):
        assert finite(raw['Inner_Iter']) == item['iteration']
        a, b = finite(raw['Linear_Solver_Iterations']), finite(raw['LinSolIterTurb'])
        assert a == int(a) == item['flow_iterations'] and b == int(b) == item['SA_iterations']
        flow.append(int(a)); turbulence.append(int(b))
        finite(raw['LinSolRes']); finite(raw['LinSolResTurb'])
    return {'rows': len(rows), 'iteration_limit': limit,
            'flow_iterations': sum(flow), 'SA_iterations': sum(turbulence),
            'combined_Krylov_count_proxy': sum(flow) + sum(turbulence),
            'flow_limit_hit_count': sum(value == limit for value in flow),
            'SA_limit_hit_count': sum(value == limit for value in turbulence),
            'final_LinSolRes_log10_raw': finite(rows[-1]['LinSolRes']),
            'final_LinSolResTurb_log10_raw': finite(rows[-1]['LinSolResTurb']),
            'new_posthoc_acceptance_gate': False}


def raw_linelet_summary(arm):
    """Read the one exact native summary; a mean is not a line distribution."""
    logpath = CASE / arm / 'solver.log'
    pattern = re.compile(r'Computed linelet structure, ([0-9]+(?:\.[0-9]+)?) points in each line \(average\)\.')
    matches = [(line, pattern.fullmatch(line)) for line in logpath.read_text(encoding='utf-8', errors='strict').splitlines()]
    matches = [(line, match) for line, match in matches if match is not None]
    assert len(matches) == 1, 'Expected one exact native LINELET summary: ' + rel(logpath)
    line, match = matches[0]
    value = finite(match[1])
    assert value > 0
    return {'reported_average_points_per_linelet': value, 'raw_line': line,
            'log_path': rel(logpath), 'log_sha256': sha(logpath),
            'interpretation': 'Native formatted average only; not individual line lengths, a full distribution or proof that every line reaches the cap.',
            'new_posthoc_acceptance_gate': False}


def source_and_recipe(c, checked_change):
    """Use the native controller's read-only source/tool/one-change authentication."""
    changed_status, source_change = checked_change('p256r', c)
    assert source_change == read(CASE / 'source_change.json')
    reference = read(HOME / c['pristine_build'] / 'contract.json')
    pristine_status = read(HOME / c['pristine_build'] / 'status.json')
    candidate = read(HOME / 'p256r/contract.json')
    assert candidate['cached_objects_reused'] == 0
    effective = read(HOME / 'p256r/effective_build.json')
    assert effective['common_recipe']['passed'] is True
    assert sha(HOME / 'p256r' / 'effective-recipe.ninja') == effective['effective_recipe_sha256']
    assert sha(HOME / 'p256r/build/build.ninja') == effective['original_generated_ninja_sha256']
    for key in ('compiler_manifest_sha256', 'runtime_manifest_sha256'):
        assert reference[key] == candidate[key]
    auditpath = BASE / 'recipe_audit_v1/audit.json'
    audit = read(auditpath)
    assert sha(auditpath) == reference['recipe_audit_sha256']
    assert sha(BASE / 'recovery.ninja') == reference['recovery_ninja_sha256']
    assert sha(BASE / 'cache_before.json') == reference['recovery_cache_before_sha256']
    cache = read(BASE / 'cache_before.json')['objects']
    for name, item in cache.items():
        assert sha(HOME / 'p32a/build' / name) == item['sha256'], name
    old_status_path = HOME / 'p32a/status.json'
    assert sha(old_status_path) == reference['original_failure_status_sha256']
    assert read(old_status_path)['succeeded'] is False
    safe_refusal = read(HOME / 'p32b/status.json')
    assert safe_refusal['succeeded'] is False
    observation = read(BASE / 'operator_observations_v1.json')
    assert observation['solver_output_changed_by_postcheck'] is False
    for name, expected in reference['recovery_code_sha256'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in candidate['code_sha256'].items():
        assert sha(ROOT / name) == expected, name
    summaries = {}
    for label, contract, status in ((c['pristine_build'], reference, pristine_status),
                                    ('p256r', candidate, changed_status)):
        summaries[label] = {key: status[key] for key in (
            'succeeded', 'source_tree_sha256', 'compiler_manifest_sha256',
            'runtime_manifest_sha256', 'exe_sha256', 'bytes', 'seconds')}
        summaries[label].update(contract_sha256=sha(HOME / label / 'contract.json'),
            status_sha256=sha(HOME / label / 'status.json'),
            source_patch_sha256=contract['source_patch_sha256'],
            source_commit=contract['source_commit'])
    return {'source_change': source_change, 'builds': summaries,
            'recovery_seconds': pristine_status['seconds'],
            'previous_failed_build_seconds': reference['previous_build_seconds'],
            'cumulative_pristine_build_seconds': pristine_status['cumulative_native_build_seconds'],
            'cumulative_time_scope': 'Recorded previous driver wall time plus native recovery; not pure compiler CPU time or only native phase durations.',
            'cached_objects_reused_and_reverified': len(cache),
            'remaining_build_targets': audit['dry_run']['planned_targets'],
            'unchanged_effective_commands': audit['command_delta']['unchanged_command_count'],
            'inspected_effective_commands': audit['command_delta']['command_count'],
            'common_cap_build_commands': effective['common_recipe']['matched_commands'],
            'recipe_audit_path': rel(auditpath), 'recipe_audit_sha256': sha(auditpath),
            'old_failed_status_preserved': True, 'old_resource_refusal_preserved': True,
            'operator_observation_path': rel(BASE / 'operator_observations_v1.json'),
            'operator_observation_sha256': sha(BASE / 'operator_observations_v1.json'),
            'operator_observation': observation,
            'scope': 'Declared tools/runtime/recipe and source bytes; not a complete OS/SDK image or independent clean-room build.'}


def fixed_membership_data(c, payloads):
    path = ROOT / c['fixed_RHS_csv']
    assert sha(path) == c['fixed_RHS_sha256']
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    rows.sort(key=lambda row: int(row['mesh_node']))
    count = c['decision_contract']['membership_expected_nodes']
    assert len(rows) == count and [int(row['mesh_node']) for row in rows] == list(range(count))
    records = []
    for index, row in enumerate(rows):
        item = {'mesh_node': index, 'x_m': finite(row['x_m']), 'y_m': finite(row['y_m']),
                'fixed_old_RHS_Rho_squared_share': finite(row['Rho_squared_share'])}
        for arm in ARMS:
            mask = payloads[arm]['membership']['mask']
            assert len(mask) == count and type(mask[index]) is bool
            item[arm + '_member'] = int(mask[index])
        records.append(item)
    total = math.fsum(row['fixed_old_RHS_Rho_squared_share'] for row in records)
    assert abs(total - 1.) <= c['share_sum_tolerance']
    for arm in ARMS:
        share = math.fsum(row['fixed_old_RHS_Rho_squared_share'] for row in records if row[arm + '_member'])
        assert abs(share - payloads[arm]['membership']['Rho_squared_share']) <= c['share_sum_tolerance']
    return records


def make_plots(payloads, records, history_paths, coverage_paths):
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'tools/matplotlib-cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    figure, axes = plt.subplots(3, 2, figsize=(12, 11), constrained_layout=True)
    for component, axis in zip((*COMPONENTS, 'CD'), axes.flat):
        for arm in ARMS:
            history = payloads[arm]['history']
            values = [row['CD'] if component == 'CD' else row['rms'][component] for row in history]
            axis.plot([row['iteration'] for row in history], values, label=LABELS[arm],
                      color=COLORS[arm], lw=1.25, alpha=.88,
                      linestyle='--' if arm == 'release32' else '-')
        axis.set_title(component)
        axis.set_xlabel('Yeni koşu iterasyonu; aynı fine3999 başlangıcı')
        axis.set_ylabel('CD' if component == 'CD' else 'log10 RMS; kayıtlı SI2D dönüşümü')
        axis.grid(alpha=.25)
        if component == 'CD': axis.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useOffset=False)
    axes.flat[0].legend(fontsize=9)
    figure.suptitle('Sabit ağ/başlangıç/fizik: beş geçmiş artığı ve CD\nSayısal kontrol; fiziksel doğrulama değildir', fontsize=13)
    for path in history_paths: figure.savefig(path, dpi=170)
    plt.close(figure)
    x = np.array([row['x_m'] for row in records]); y = np.array([row['y_m'] for row in records])
    reference = np.array([row['build32_member'] for row in records], dtype=bool)
    candidate = np.array([row['build256_member'] for row in records], dtype=bool)
    union = reference | candidate
    ymax = float(y[union].max()) if union.any() else float(y.max())
    # Explicit wall view; a native line at the outflow can reach the domain top.
    zoom_y = .002
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    visibility = {}
    for column, (arm, mask) in enumerate((('build32', reference), ('build256', candidate))):
        for rownum, axis in enumerate(axes[:, column]):
            axis.scatter(x, y, s=1, color='#d8dfe4', rasterized=True)
            axis.scatter(x[mask], y[mask], s=2.2, color=COLORS[arm], rasterized=True)
            axis.set_xlabel('x,m'); axis.set_ylabel('y,m'); axis.grid(alpha=.15)
            if rownum == 0:
                axis.set_title(LABELS[arm] + ': bütün alan / bütün düğümler')
                axis.set_xlim(float(x.min()), float(x.max())); axis.set_ylim(float(y.min()), float(y.max()))
            else:
                axis.set_xlim(float(x.min()), float(x.max())); axis.set_ylim(0., zoom_y)
                outside = int(np.count_nonzero((y < 0.) | (y > zoom_y)))
                visibility[arm] = {'all_nodes': len(records), 'zoom_y_max_m': zoom_y,
                                   'outside_zoom_nodes_preserved': outside,
                                   'membership_nodes': int(mask.sum())}
                axis.set_title(f'Yakın görünüm: {outside} alan dışı düğüm CSV’de korunur')
    figure.suptitle('Native boolean LINELET üyeliği; renk/çizgi numarası kullanılmadı\nKapsam aynı eski RHS ile ölçülür; yeni alan artığı veya ağ hata bandı değildir', fontsize=12)
    for path in coverage_paths: figure.savefig(path, dpi=170)
    plt.close(figure)
    return visibility


def main():
    # These prerequisites precede imports that authenticate/read the complete source tree.
    required = [CASE / name for name in ('contract.json', 'reproduction.json', 'effect.json', 'source_change.json')]
    for arm in ARMS:
        required += [CASE / (arm + '_payload.json'), CASE / arm / 'prediction_frozen.json']
    for path in required:
        assert path.is_file(), 'Completed native comparison required; absent: ' + rel(path)
    records = {arm: read(CASE / (arm + '_payload.json')) for arm in ARMS}
    assert all(row.get('accepted_for_decision') is True for row in records.values()), 'All three native payload extractions must be accepted'
    sys.path.insert(0, str(OLD_BASE))
    from native_control import check_contract, checked_change
    from decisions import reproducibility_gate, linecap_effect_gate
    c = check_contract()
    payloads = {arm: record['payload'] for arm, record in records.items()}
    reproduction = reproducibility_gate(payloads['release32'], payloads['build32'], c['decision_contract'])
    assert reproduction == read(CASE / 'reproduction.json') and reproduction['accepted'] is True
    source = source_and_recipe(c, checked_change)
    effect = linecap_effect_gate(payloads['build32'], payloads['build256'], c['decision_contract'], reproduction, source['source_change'])
    assert effect == read(CASE / 'effect.json') and type(effect['accepted']) is bool
    for result in (reproduction, effect):
        for key in ('physical_qualification_passed', 'M6_qualification_passed', 'LLM_improvement_demonstrated'):
            assert result.get(key) is False
    old_folders = [seal.parent for family in ('flatplate_SAneg_20261025_v1', 'flatplate_20261027_v1')
                   for seal in sorted((ROOT / 'outputs/simulations' / family).rglob('prediction_frozen.json'))]
    old_integrity = verify_seals(old_folders)
    assert old_integrity['hash_records_verified'] == read(OLD_BASE / 'old_output_integrity.json')['old_raw_hash_records_verified']
    new_integrity = verify_seals([CASE / arm for arm in ARMS])
    for arm in ARMS:
        sealpath = CASE / arm / 'prediction_frozen.json'
        seal = read(sealpath)
        assert records[arm]['evidence']['seal_sha256'] == sha(sealpath)
        assert seal['contract_sha256'] == sha(CASE / 'contract.json') and seal['mesh_sha256'] == c['mesh_sha256']
        assert seal['matched']['field_iteration'] == seal['matched']['terminal_history_iteration'] == c['decision_contract']['comparison_iteration']
        exe = read(CASE / arm / 'executable_before_native.json')
        assert sha(exe['exe']) == exe['exe_sha256']
        assert exe['build_identities'] == {key: value for key, value in payloads[arm]['identity'].items()
            if key in ('source_tree_sha256', 'compiler_manifest_sha256', 'runtime_manifest_sha256')}
    checks_path = ROOT / 'outputs/reports/su2_resume_checks_20261027.json'
    checks = read(checks_path)
    assert checks['passed'] is True and checks['failures'] == checks['errors'] == 0
    assert sum(checks['counts'].values()) == checks['tests_run']
    assert sha(ROOT / checks['log_path']) == checks['log_sha256']
    for name, expected in checks['code_sha256'].items(): assert sha(ROOT / name) == expected, name
    linear = {arm: raw_linear_summary(arm, payloads[arm], int(records[arm]['evidence']['canonical_config']['LINEAR_SOLVER_ITER'])) for arm in ARMS}
    linelets = {arm: raw_linelet_summary(arm) for arm in ARMS}
    source_commit = source['builds'][c['pristine_build']]['source_commit']
    linear_source = HOME / c['pristine_build'] / 'source/Common/src/linear_algebra/CSysSolve.cpp'
    linear_source_url = 'https://github.com/su2code/SU2/blob/' + source_commit + '/Common/src/linear_algebra/CSysSolve.cpp#L468-L616'
    linear_semantics = {
        'reported_quantity': 'log10(beta/norm0); beta updated from the Givens-rotated reduced right-hand side g[i+1]',
        'normalization': 'norm0 starts as ||b|| and is reset to the initial residual norm for relative tolerance',
        'independently_recomputed_Ax_minus_b_claimed': False,
        'source_recompute_scope': 'The optional mat_vec(x)-b recomputation is inside monitoring && COMM_FULL and recomputeRes; it is not the returned beta/norm0 value.',
        'source_path': rel(linear_source), 'source_sha256': sha(linear_source), 'pinned_source_url': linear_source_url,
        'source_lines': {'norm0_and_initial_beta': [468, 490], 'Givens_beta': [564, 573],
                         'monitoring_optional_recompute': [594, 613], 'returned_residual': [616, 616]}}
    membership = fixed_membership_data(c, payloads)
    output = ROOT / 'outputs/reports' / STEM
    plotbase = ROOT / 'outputs/plots' / STEM
    history_paths = [plotbase.with_name(plotbase.name + '_history').with_suffix(ext) for ext in ('.png', '.pdf')]
    coverage_paths = [plotbase.with_name(plotbase.name + '_membership').with_suffix(ext) for ext in ('.png', '.pdf')]
    csvpath = ROOT / 'outputs/data/qualification/linecap_source_20261027_v1/all_nodes_membership.csv'
    targets = [output.with_suffix(ext) for ext in ('.json', '.md', '.html')] + history_paths + coverage_paths + [csvpath]
    assert not any(path.exists() for path in targets), 'Preserve existing report/plot outputs; review before a new report revision'
    for path in targets: path.parent.mkdir(parents=True, exist_ok=True)
    visibility = make_plots(payloads, membership, history_paths, coverage_paths)
    with csvpath.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(membership[0])); writer.writeheader(); writer.writerows(membership)
    metrics, rm = effect['metrics'], reproduction['metrics']
    worst_reproduction = max(rm['max_abs_RMS_log10_difference_by_component'].values())
    passed_tr, passed_en = ('geçti', 'passed') if effect['accepted'] else ('geçmedi', 'did not pass')
    summary_tr = (f'SU2 kaynak32 derlemesi, korunmuş başarısız denemeden {source["cached_objects_reused_and_reverified"]} doğrulanmış nesneyi kullanarak '
        f'kalan {source["remaining_build_targets"]} hedefi {source["recovery_seconds"]:.3f} saniyede tamamladı. '
        f'Üç yeni native CFD koşusu aynı kaynak ağ ve başlangıçla {c["decision_contract"]["iterations"]} adım çalıştı. '
        f'Resmî release32–kaynak32 yeniden üretimi geçti: beş SI log10 RMS eğrisindeki en büyük fark {worst_reproduction:.8f}, '
        f'son CD mutlak farkı {rm["final_CD_absolute_difference"]:.10g}. Yalnız MAX_LINELET_POINTS=32→256 değiştirildi. '
        f'Yoğunluk kazancı {metrics["density_log10_gain"]:.8f} log10, SA kötüleşmesi {metrics["SA_log10_worsening"]:.8f} log10, '
        f'Krylov sayımı oranı {metrics["work_ratio"]:.8f}, bu çiftte gözlenen süre oranı {metrics["observed_elapsed_ratio"]:.8f}; '
        f'ön kayıtlı ortak etki/maliyet kabulü {passed_tr}. {checks["tests_run"]} yeni yazılım kontrolü geçti; eski70 kontrol yeni sayılmadı. '
        'Krylov sayımı işlem maliyetinin vekilidir; daha uzun çizgilerin eşit aritmetik maliyeti olduğu veya tek çiftin evrensel hız kıyası olduğu iddia edilmez. '
        'Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.')
    summary_en = (f'The pristine source32 build reused {source["cached_objects_reused_and_reverified"]} authenticated objects from the preserved failed attempt '
        f'and completed {source["remaining_build_targets"]} remaining targets in {source["recovery_seconds"]:.3f} seconds. '
        f'Three fresh native CFD arms each ran {c["decision_contract"]["iterations"]} iterations on the same mesh and seed. '
        f'Release32/source32 numerical reproduction passed: the largest five-component SI log10 RMS curve difference was {worst_reproduction:.8f}; '
        f'final absolute CD difference was {rm["final_CD_absolute_difference"]:.10g}. Only MAX_LINELET_POINTS changed from32 to256. '
        f'Density gain was {metrics["density_log10_gain"]:.8f} log10, SA worsening {metrics["SA_log10_worsening"]:.8f}, '
        f'Krylov-count ratio {metrics["work_ratio"]:.8f}, and observed elapsed-time ratio {metrics["observed_elapsed_ratio"]:.8f}; '
        f'the preregistered joint effect/cost gate {passed_en}. All {checks["tests_run"]} new software checks passed; the prior70 checks were not counted again. '
        'Krylov counts are a work proxy, not equal floating-point cost for longer linelets; one elapsed-time pair is not a universal speed benchmark. '
        'General physical/RAE2822/M6/UAV qualification and LLM improvement remain unestablished.')
    result = {'created_utc': datetime.now(timezone.utc).isoformat(), 'visualisation_algorithm_version': 2,
        'visual_review_revision': 'Common wall close-up fixed to 0-2mm; initial report/plots preserved under work/su2_build_resume_20261027/report_v1_before_visual_review. Native results and decisions unchanged.',
        'scope': 'Pinned source/native32 reproduction and one controlled cap32→256 diagnostic; not a mesh or physical qualification',
        'summary_tr': summary_tr, 'summary_en': summary_en, 'new_native_CFD_runs': len(ARMS),
        'native_contract_path': rel(CASE / 'contract.json'), 'native_contract_sha256': sha(CASE / 'contract.json'),
        'native_contract_anchor_sha256': sha(OLD_BASE / 'native_contract_anchor.json'),
        'method_design_sha256': sha(OLD_BASE / 'method_design.json'),
        'reproduction_record_sha256': sha(CASE / 'reproduction.json'),
        'effect_record_sha256': sha(CASE / 'effect.json'),
        'source_change_record_sha256': sha(CASE / 'source_change.json'),
        'source_and_recipe': source, 'pristine_reproduction': reproduction, 'cap_effect': effect,
        'linear_solver_observations': linear, 'linear_solver_residual_semantics': linear_semantics,
        'native_linelet_log_observations': linelets, 'new_distinct_checks': checks['tests_run'],
        'software_checks_report': rel(checks_path), 'software_checks_sha256': sha(checks_path),
        'old_output_integrity': old_integrity, 'new_output_integrity': new_integrity,
        'frozen_and_live_native_code_hash_records_verified': len(c['code_before_native_sha256']) + len(c['live_code_before_native_sha256']),
        'arms': {arm: {'payload_path': rel(CASE / (arm + '_payload.json')), 'payload_sha256': sha(CASE / (arm + '_payload.json')),
            'field_iteration': payloads[arm]['field_iteration'], 'elapsed_seconds': payloads[arm]['elapsed_seconds'],
            'final_SI_log10_RMS': payloads[arm]['history'][-1]['rms'], 'final_CD': payloads[arm]['history'][-1]['CD'],
            'last100_CD_range': payloads[arm]['CD_last100_range'], 'native_membership_nodes': sum(payloads[arm]['membership']['mask']),
            'reported_average_points_per_linelet': linelets[arm]['reported_average_points_per_linelet'],
            'fixed_old_RHS_Rho_squared_share': payloads[arm]['membership']['Rho_squared_share']} for arm in ARMS},
        'artifacts': {rel(path): {'sha256': sha(path), 'bytes': path.stat().st_size} for path in (*history_paths, *coverage_paths, csvpath)},
        'spatial_view_scope': visibility, 'all_owned_nodes_retained_in_CSV': len(membership),
        'fixed_RHS_scope': 'Same previously authenticated sequential-stage RHS; not recomputed residual of any new implicit field and not mesh-error evidence.',
        'old_fine3999_role_preserved': True, 'not_blind': True, 'thresholds_changed_after_results': False,
        'independent_review': {'path': rel(BASE / 'independent_review.json'), 'sha256': sha(BASE / 'independent_review.json'),
            'scope': 'Separate read-only audit of three existing runs; not an independent blind prediction'},
        'planned_next_method': {'status': 'planned_not_executed',
            'method': 'Passive true inner-linear residual measurement on the same fixed matrix/RHS, separately from the Givens estimate',
            'prerequisites': ['Preregister resource and numerical gates', 'Audit passive instrumentation against pinned source',
                'Reproduce unchanged solution path before assigning any difference to the new measurement'],
            'new_physical_conditions': False, 'parameter_sweep_authorised_by_this_record': False},
        'GCI': None, 'physical_qualification_passed': False, 'M6_qualification_passed': False, 'LLM_improvement_demonstrated': False}
    text = '# SU2 kaynak derlemesi ve kontrollü karşılaştırma\n\n27 Ekim2026 · Üç yeni native CFD koşusu · Genel fizik kabulü: **false**.\n\n' + summary_tr + '\n\n'
    text += '## Derlemede ne değişti?\n\n'
    text += (f'Önceki `p32a` başarısız kaydı başarısız kaldı; `p32b` bellek korumasının native başlamadan verdiği ret de korundu. '
        f'Yeni `p32r`, kaynak baytlarına dokunmadan yalnız sorunlu CFlowTractionInterface.cpp derleme birimine kayıtlı başlık arama argümanını ekledi. '
        f'{source["inspected_effective_commands"]} etkin komutun {source["unchanged_effective_commands"]} tanesi değişmedi; '
        f'{source["cached_objects_reused_and_reverified"]} nesnenin hash’i yeniden denetlendi ve kalan {source["remaining_build_targets"]} hedef '
        f'{source["recovery_seconds"]:.3f}s sürdü. Önceki sürücü işlemleri dahil kayıtlı toplam derleme süresi {source["cumulative_pristine_build_seconds"]:.3f}s. '
        'Daha önce önerilen global cpp_args seçeneği bu kurtarma derlemesine taşınmadı. `p32r/source` gerçek derleme yolunun bayt eşdeğer arşividir; '
        'asıl derleme p32a çalışma ağacında yapılmış, EXE sonra p32r kaydına kopyalanmıştır.\n\n')
    text += 'Kaynak256 yeni klasörde, nesne önbelleği taşınmadan derlendi. Aynı genişletilmiş derleyici/linker/archive/Python/Ninja manifesti, runtime DLL kimliği ve etkin komutlar doğrulandı; kaynakta yalnız `MAX_LINELET_POINTS=32→256` farkı var. Bu, tüm işletim sistemi/SDK ortamının veya bağımsız bir temiz oda derlemesinin eşdeğerliği değildir.\n\n'
    text += '## Kaynak32 resmî sonucu yeniden üretiyor mu?\n\n| SI log10 RMS bileşeni | Bütün200 adımda en büyük mutlak fark | Ön kayıtlı üst sınır |\n|---|---|---|\n'
    for key, value in rm['max_abs_RMS_log10_difference_by_component'].items():
        text += f'| {key} | {value:.10g} | {c["decision_contract"]["reproduction_max_abs_log10_difference"]} |\n'
    text += (f'\nYeniden üretim **{str(reproduction["accepted"]).lower()}**. Son |ΔCD|={rm["final_CD_absolute_difference"]:.10g}; '
        f'toplam akış+SA Krylov sayımı {rm["reference_Krylov"]}→{rm["build32_Krylov"]}; '
        'native boolean üyelik aynı. Bu sayısal ekran, farklı GNU/runtime derlemeleri arasında bu vaka için işlemsel eşdeğerlik kanıtıdır; fizik hata bandı değildir.\n\n')
    text += '## Tek kaynak değişikliğinin etkisi\n\n| Kayıt | Son SI yoğunluk log10 RMS | Son SI SA log10 RMS | CD | Son100 CD aralığı | Krylov sayımı | Süre,s | Native üye | Logdaki ortalama çizgi noktası | Aynı eski RHS yoğunluk kare payı |\n|---|---|---|---|---|---|---|---|---|---|\n'
    for arm in ARMS:
        a = result['arms'][arm]; linear_arm = linear[arm]
        text += f'| {LABELS[arm]} | {a["final_SI_log10_RMS"]["Rho"]:.9f} | {a["final_SI_log10_RMS"]["nu"]:.9f} | {a["final_CD"]:.12g} | {a["last100_CD_range"]:.5g} | {linear_arm["combined_Krylov_count_proxy"]} | {a["elapsed_seconds"]:.3f} | {a["native_membership_nodes"]} | {a["reported_average_points_per_linelet"]:g} | %{100*a["fixed_old_RHS_Rho_squared_share"]:.6f} |\n'
    text += '\nOrtalama çizgi noktası yalnız native logun tam `Computed linelet structure, ... points in each line (average).` satırından okunur. Yazdırılmış ortalama, tek tek çizgi boylarının dağılımı veya her çizginin cap değerine ulaştığı anlamına gelmez; yeni kabul kapısı değildir.\n'
    text += '\n| Ön kayıtlı kapı | Gerçek durum |\n|---|---|\n'
    for name, value in effect['checks'].items(): text += f'| `{name}` | {str(value).lower()} |\n'
    text += (f'\nOrtak kabul **{str(effect["accepted"]).lower()}**. Yoğunluk kazancı {metrics["density_log10_gain"]:.9f} '
        f'(hedef≥{c["decision_contract"]["density_gain_min"]}); SA kötüleşmesi {metrics["SA_log10_worsening"]:.9f} '
        f'(hedef≤{c["decision_contract"]["SA_worsening_max"]}); Krylov sayımı oranı {metrics["work_ratio"]:.9f} '
        f'(üst sınır {c["decision_contract"]["work_ratio_max"]}); gözlenen süre oranı {metrics["observed_elapsed_ratio"]:.9f} '
        f'(üst sınır {c["decision_contract"]["elapsed_ratio_max"]}). Eşikler değişmedi; bütün gerekli kapılar birlikte değerlendirildi. '
        'Krylov sayımı aritmetik işin yalnız vekilidir: çizgi boyu değişince bir iterasyonun maliyeti eşit kabul edilmez. '
        'Gerçek süre bu yüzden ayrı verildi; tek eş koşu çifti genel performans oranı değildir. '
        f'Bu vakada kaynak32 sayımı {linear["build32"]["combined_Krylov_count_proxy"]}='
        f'{linear["build32"]["rows"]}×({linear["build32"]["iteration_limit"]}+'
        f'{linear["build32"]["iteration_limit"]}) ile kayıtlı toplam tavanın tamamı olduğundan, '
        'aynı tavanlı aday için Krylov≤1,5 oran kapısı ayırt edici değildir; eşik değiştirilmedi ve gerçek süre ayrı değerlendirildi.\n\n')
    text += '## İç doğrusal çözümler: ek gözlem, yeni kabul eşiği yok\n\n| Kayıt | Akış / SA40-tavanına ulaşma | Son LinSolRes ham log10 | Son LinSolResTurb ham log10 |\n|---|---|---|---|\n'
    for arm in ARMS:
        a = linear[arm]
        text += f'| {LABELS[arm]} | {a["flow_limit_hit_count"]}/{a["rows"]} · {a["SA_limit_hit_count"]}/{a["rows"]} | {a["final_LinSolRes_log10_raw"]:.10g} | {a["final_LinSolResTurb_log10_raw"]:.10g} |\n'
    text += ('\nBu sütunlar CSV’den doğrudan okunan iç doğrusal çözücü artıklarıdır; yukarıdaki beş SI nonlinear RMS eğrisiyle aynı nicelik değildir. '
        'Bu FGMRES yolunda döndürülen değer `beta/norm0` olup beta, Givens döndürmeleri sonrası azaltılmış sistemin `g[i+1]` değerinden güncellenir. '
        'Dolayısıyla LinSolRes burada bağımsız olarak yeniden hesaplanmış `||Ax-b||` ölçümü diye sunulmaz. norm0 önce `||b||` olur; '
        'bağıl toleransta başlangıç artık normuna ayarlanır. Gerçek `mat_vec(x)-b` yeniden hesabı, kaynakta yalnız monitoring/COMM_FULL ve '
        'recomputeRes koşullu dalındadır; bu dal döndürülen `beta/norm0` değerinin yerine geçmez. '
        '[Sabit kaynak: CSysSolve.cpp468–616](' + linear_source_url + '). '
        'İterasyon sayılarının tavanı görmesi, tek başına hassasiyet veya fizik kabulü kanıtı değildir. '
        'Bu gözlem için sonuçtan sonra yeni geçme/kalma kapısı eklenmedi.\n\n')
    text += f'![Üç koşunun beş SI geçmişi ve CD](../plots/{history_paths[0].name})\n\n'
    text += '## Çizgi kapsamının konumu\n\nBoolean üyelik native Linelet alanının pozitifliğinden gelir; graph renkleri çizgiID değildir. Kapsanan pay, bütün kollarda aynı dondurulmuş eski sıralı akış/SA aşama RHS’sinin yoğunluk kare toplamıdır. Yeni implicit alanların yeniden hesaplanmış nonlinear artığı, nedensel hata haritası veya ağ hata bandı değildir.\n\n'
    text += f'![Tam alan ve yakın görünümde gerçek üyelik](../plots/{coverage_paths[0].name})\n\n'
    text += f'Bütün **{len(membership)} düğüm**, dışarıda kalanlar dahil [konum/üyelik CSV’sinde](../data/qualification/linecap_source_20261027_v1/all_nodes_membership.csv) korunur. Yakın görünüm yalnız eksen sınırını değiştirir; dışındaki düğümler silinmez.\n\n'
    text += '## Korunan kayıtlar ve sınırlar\n\n'
    text += (f'İki eski düz plaka ailesinin {old_integrity["hash_records_verified"]} ham hash kaydı ve '
        f'yeni üç kolun {new_integrity["hash_records_verified"]} kaydı eşleşti. Donmuş/canlı native kod, CASE sözleşme çapası, '
        'kaynak ağaçları, tek yama, derleyici/runtime ve EXE mühürleri yeniden denetlendi. '
        f'{checks["tests_run"]} yeni kontrolün dağılımı: {checks["counts"]["engineering_recipe_and_cap"]} derleme/yöntem ve '
        f'{checks["counts"]["publication_guards"]} yayın koruması. Eski70 kontrol bu sayıya eklenmedi.\n\n')
    text += 'Nesne-cache ek çapraz denetiminde Windows/posix yol ayracı nedeniyle KeyError görüldü; normalize edilmiş yeniden denetim geçti. Bu sırada tek mevcut derleme işi sürdü; ikinci native iş başlatılmadı. Davranış riski, bağımlı ek denetimin dönüş koduna bakmadan işi başlatmaktı; dosyadaki çıkarım ve düzeltme korunuyor. Bu bir süreç olayıdır, CFD’nin fiziksel hata nedeni veya LLM iyileşme kanıtı değildir.\n\n'
    text += 'Eski fine3999 rolü ve üç-ağ ailesi korunur; bu üç200-adımlık mekanizma kolu onların yerine seçilmez. Ağ, uzak alan, deney ve bağımsız fizik kabulleri kapanmadı; GCI üretilmedi. Bu kaynak benchmarkı keyfiCAD→CFD/İHA hizmeti, stall/3B M6 yeterliliği veya uzman LLM kanıtı değildir.\n\n'
    text += '## Sonraki yöntem adayı\n\nYalnız çizgi kapsamını büyütmek, gerekli dış yoğunluk kazancını sağlamadı. Sonraki kontrollü tanı adayı, aynı sabit lineer sistemde gerçek b−Aδ normunu pasif olarak ölçüp Givens tabanlı kestirimden ayırmaktır. Böylece iç çözücünün hatası ile dış akış güncellemesinin etkisi ayrı sorgulanabilir; mevcut veriler tek başına neden kanıtlamaz. Bu ölçüm henüz yapılmadı. Kaynak denetimi, değişmeyen çözüm yolunun yeniden üretimi ve native öncesi yeni bütçe/kabul kaydı gerekir.\n\n'
    text += '[Ayrı geçmişte mevcut çıktılar üzerinde yapılan bağımsız kod/VTK denetimi](../../work/su2_build_resume_20261027/independent_review.json) ham mühürleri, bütün geçmiş satırlarını ve üç alanın düğüm eşleşmesini yeniden kontrol etti; yeni kör CFD tahmini değildir. Görsel kontrolde ilk yakın görünümün çıkıştaki yüksek çizgi üyeleri nedeniyle tam alanla aynı olduğu görüldü. İlk rapor/grafikler korundu; yeni yakın görünüm iki kolda da açıkça y=0–0,002m olarak çizildi. Alan/kuvvet/kararlar değişmedi; bütün düğümler CSV’de bulunur.\n\n'
    text += f'- [Bütün sonuç ve dosya mühürleri]({STEM}.json)\n- [Yeni{checks["tests_run"]} yazılım kontrolü](su2_resume_checks_20261027.json)\n- [Önceki kaynak hazırlığı](su2_kaynak_kontrolu_20261027.html)\n- [Native sözleşme](../simulations/linecap_source_20261027_v1/contract.json)\n- [Kaynak değişikliği](../simulations/linecap_source_20261027_v1/source_change.json)\n- [Kayıtlı etki kararı](../simulations/linecap_source_20261027_v1/effect.json)\n'
    text += '\nKaynak kimliği: [sabit SU2 v8.5.0 commit](https://github.com/su2code/SU2/tree/12eb826f049ef7f67df974dfcb44cf36ee07c0f8). Yeni üçüncü taraf bağımlılık kurulmadı; rapor mevcut matplotlib ve standart HTML araçlarıyla üretildi.\n'
    with output.with_suffix('.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
    output.with_suffix('.md').write_text(text, encoding='utf-8')
    page = ('<!doctype html><html lang="tr"><meta charset="utf-8"><title>SU2 kaynak karşılaştırması</title>'
        '<style>body{font:16px/1.65 system-ui;max-width:1180px;margin:36px auto;padding:0 20px;color:#172733;background:#f5f8fb}'
        'h1,h2{line-height:1.25}table{border-collapse:collapse;background:white;display:block;overflow-x:auto}'
        'td,th{border:1px solid #ccd7df;padding:8px}code{overflow-wrap:anywhere}a{color:#006d91}img{max-width:100%;height:auto;background:white}</style>'
        + render(text) + '</html>')
    output.with_suffix('.html').write_text(page, encoding='utf-8')
    print({'report': rel(output.with_suffix('.html')), 'native_runs': len(ARMS),
           'reproduction_passed': reproduction['accepted'], 'cap_effect_passed': effect['accepted'],
           'old_hash_records': old_integrity['hash_records_verified'], 'new_hash_records': new_integrity['hash_records_verified'],
           'physical_qualification_passed': False}, flush=True)


if __name__ == '__main__':
    main()
