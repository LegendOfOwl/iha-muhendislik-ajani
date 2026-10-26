"""Prepare v0.14.0 documentation after the incremental export has been built.

This script changes the publication checkout only when explicitly executed. It
does not run a solver, commit files, create a tag, or call a remote service.
"""
from incremental_export import ROOT, DEST, RUN, VERSION, PLAN, read
import math
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit


PREVIOUS = 'v0.13.0'
REPORT = 'cfd_kalan_artik_20261026'


def finite_number(value):
    assert not isinstance(value, bool) and isinstance(value, (int, float))
    assert math.isfinite(value)
    return value


def github_report_links(markdown):
    """Resolve report-relative artifact links at raporlar/v0.14.0/README.md."""
    pattern = re.compile(r'(?P<open>!?\[[^\]\n]*\]\()(?P<target>[^\s)]+)(?P<close>\))')

    def replace(match):
        target = match['target']
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith('/'):
            return match.group(0)
        path = posixpath.normpath(posixpath.join('outputs/reports', parts.path))
        # Report links may refer to plots, data, raw simulations or neighbouring
        # reports. Preserve an unexpected outside path for explicit review.
        assert path.startswith('outputs/'), ('Outside report artifact link', target)
        rewritten = '../../uygulama/' + path
        return match['open'] + urlunsplit(('', '', rewritten, parts.query, parts.fragment)) + match['close']

    return pattern.sub(replace, markdown)


def append_category_link(path):
    body = path.read_text(encoding='utf-8')
    link = '- [' + VERSION + '](' + VERSION + '/README.md)'
    assert link not in body, ('Version already listed', str(path))
    path.write_text(body.rstrip() + '\n\n' + link + '\n', encoding='utf-8')


def main():
    assert VERSION == 'v0.14.0'
    plan = read(PLAN)
    assert plan['version'] == VERSION
    result = read(ROOT / 'outputs/reports/flatplate_inner_cap_20261026.json')
    assert result['effect_passed'] is False
    assert result['physical_qualification_passed'] is False
    quality = result['quality']
    assert quality['comparable'] is True
    gain = finite_number(quality['density_log10_gain'])
    sa_worse = finite_number(quality['SA_log10_worsening'])
    work_ratio = finite_number(result['work_ratio'])
    guards = read(ROOT / 'outputs/reports/inner_cap_guards_20261026.json')
    assert guards['passed'] == 9 and len(guards['checks']) == 9
    assert guards['physical_qualification'] is False
    probe_guards = read(ROOT / 'outputs/reports/residual_probe_guards_20261026.json')
    assert probe_guards['passed'] is True
    assert probe_guards['tests_run'] == 28
    assert probe_guards['failures'] == 0 and probe_guards['errors'] == 0
    assert probe_guards['physical_qualification'] is False
    guard_count = guards['passed'] + probe_guards['tests_run']
    probe = read(ROOT / 'outputs/reports/residual_probe_20261026.json')
    assert probe['measurement_accepted'] is True and probe['map_authorized'] is True
    assert probe['all_five_RMS_and_MAX_match'] is True
    assert probe['physical_qualification_passed'] is False
    assert probe['M6_qualification_passed'] is False
    assert probe['LLM_improvement_demonstrated'] is False
    assert set(probe['components']) == {'Rho', 'RhoU', 'RhoV', 'RhoE', 'nu'}
    assert all(component['passed'] is True for component in probe['components'].values())
    norm_error = max(finite_number(component[key])
                     for component in probe['components'].values()
                     for key in ('RMS_log10_error', 'MAX_log10_error'))
    assert probe['native_binary_drift']['passed'] is True
    drift = finite_number(probe['native_binary_drift']['maximum_conservative_relative_L2'])
    linelet = read(ROOT / 'outputs/reports/flatplate_linelet_20261026.json')
    assert linelet['effect_passed'] is False
    assert linelet['physical_qualification_passed'] is False
    assert linelet['activation_verified'] is True
    linelet_gain = finite_number(linelet['quality']['density_log10_gain'])
    linelet_sa = finite_number(linelet['quality']['SA_log10_worsening'])
    linelet_work = finite_number(linelet['work_ratio'])
    source_report = ROOT / 'outputs/reports' / (REPORT + '.md')
    assert source_report.is_file()
    summary = (
        '26 Ekim 2026. Aynı ince ağ ve başlangıç alanında iç doğrusal çözüm '
        'sınırı 40→80 olarak değiştirildi. 200 adımlık eşli kontrolde yoğunluk '
        f'kalıntısındaki kazanç {gain:.8f} log10, SA kalıntısındaki değişim '
        f'{sa_worse:.8f} log10 ve toplam Krylov işi oranı {work_ratio:.8f} oldu. '
        'Önceden belirlenen ortak etki kabulü geçmedi; başarısız deneme ve ham '
        'çıktılar korundu.\n\n'
        'Kalan kalıntının yerini araştırmak için kaynak koduna dayalı, bir adımlık '
        'açık RHS ölçümü çalıştırıldı. Akış ve SA aşamalarının sıralı hesaplandığı '
        f'bu tanıda beş RMS/MAX eşlemesi geçti: en büyük fark {norm_error:.3g} log10, '
        f'native konservatif alan drift’i {drift:.3g}. Haritanın yönlendirdiği '
        f'LINELET kontrolü gerçekten etkinleşti; yoğunluk kazancı {linelet_gain:.8f} '
        f'log10, SA kötüleşmesi {linelet_sa:.8f} log10 ve Krylov işi oranı '
        f'{linelet_work:.8f} ile ortak etkiyi geçemedi. Norm ve konum bulguları '
        'ile sınırlamalar ayrıntılı raporda gösterilir. '
        'Bu çalışma yeni bir yakınsamış çözüm, deney doğrulaması veya genel CFD '
        f'yeterliliği değildir. {guard_count} yeni yazılım kontrolü geçti. Genel fizik, '
        'RAE2822, ONERA M6 ve gerçek İHA kabulleri açık; LLM davranışında '
        'iyileşme ölçülmedi.\n'
    )
    download_note = (
        'Tam izlenen uygulama/kaynak ağacı Release sayfasındaki otomatik '
        '**Source code (zip)** tag arşivinden indirilir. Yeni büyük CFD alanları '
        '`analiz-arsivi-*.zip` varlığındadır; dosya kataloğu ve geri yükleme aracı '
        'özgün yolları ve SHA256 değerlerini denetler. `KAYNAK_INDIRME.md` '
        'indirme açıklamasını, `SHA256SUMS.txt` bu sürümün yüklenen varlık '
        'mühürlerini taşır. Önceki sürümlerin varlıkları korunur.\n'
    )
    report_dir = DEST / 'raporlar' / VERSION
    version_dir = DEST / 'surumler' / VERSION
    assert not report_dir.exists(), 'Preserve existing version documentation'
    assert not (version_dir / 'README.md').exists()
    # Read and validate every expected anchor before modifying the checkout.
    readme_path = DEST / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    assert 'Güncel dağıtım **' + PREVIOUS + '**' in readme
    assert '`main` veya `' + PREVIOUS + '`' in readme
    assert 'v0.1.0 → ' + PREVIOUS + ' sürüm ve kanıt notları' in readme
    old_row = '| [' + PREVIOUS + '](surumler/' + PREVIOUS + '/README.md) | İç çözümde%42 daha az Krylov iterasyonu ve üç kaynak ağda kabul denetimi |'
    assert old_row in readme
    changelog_path = DEST / 'CHANGELOG.md'
    changelog = changelog_path.read_text(encoding='utf-8')
    assert '## ' + VERSION not in changelog
    assert '## ' + PREVIOUS in changelog
    readme = readme.replace('Güncel dağıtım **' + PREVIOUS + '**', 'Güncel dağıtım **' + VERSION + '**')
    readme = readme.replace('`main` veya `' + PREVIOUS + '`', '`main` veya `' + VERSION + '`')
    readme = readme.replace('v0.1.0 → ' + PREVIOUS + ' sürüm ve kanıt notları', 'v0.1.0 → ' + VERSION + ' sürüm ve kanıt notları')
    section = (
        '## Güncel sürüm — 26 Ekim 2026\n\n'
        '[**' + VERSION + ' sonuçları: GitHub’da okunabilir rapor**](raporlar/' + VERSION + '/README.md) · '
        '[Release dosyaları](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/' + VERSION + ') · '
        '[Sürümleme politikası](SURUMLEME.md).\n\n' + summary + '\n' + download_note + '\n'
    )
    readme, count = re.subn(r'## Güncel sürüm .*?(?=## Nereden başlanır)', lambda _: section, readme, flags=re.S)
    assert count == 1
    readme = readme.replace(old_row, old_row + '\n| [' + VERSION + '](surumler/' + VERSION + '/README.md) | İç çözüm sınırı kıyası ve kaynak koduna dayalı kalıntı konum tanısı |')
    readme = readme.replace('[GitHub’da okunabilir güncel sonuçlar](raporlar/' + PREVIOUS + '/README.md)', '[GitHub’da okunabilir güncel sonuçlar](raporlar/' + VERSION + '/README.md)')
    english = (
        '## English summary\n\n'
        'A Windows CAD/aerodynamic/CFD workflow with frozen outputs and source provenance. '
        'Version 0.14.0 reports a preregistered 40-to-80 inner iteration-cap control: '
        f'the density residual improved by {gain:.8f} log10, while total flow+SA Krylov '
        f'work increased to {work_ratio:.8f} times the baseline. The joint effect gate failed. '
        'A source-based one-step explicit RHS probe examines residual localization; its sequential '
        f'flow and SA stages matched all five RMS/MAX norms within {norm_error:.3g} log10, '
        f'with conservative native restart drift at most {drift:.3g}. The map-guided LINELET '
        f'control was active but failed the joint effect gate at {linelet_work:.8f} times the '
        f'baseline Krylov work. All {guard_count} new software checks passed. '
        'This probe is not a new converged solution or physical qualification. General physical, '
        'RAE2822, M6 and UAV gates remain open, and improved LLM behaviour has not been measured. '
        'The complete tracked source/application tree is provided by GitHub’s automatic '
        'Source code (zip) tag archive; raw CFD assets are restored using the catalogue and '
        'hash-checking restore tool. Prior release assets remain available. '
        'Earlier tags through 0.10.0 are retrospective evidence groups; 0.11.0 onward are genuine '
        'incremental releases. Code and reports were developed with substantial Codex assistance.\n\n'
    )
    readme, count = re.subn(r'## English summary.*?(?=## EXE ve lisans)', lambda _: english, readme, flags=re.S)
    assert count == 1
    github_report = github_report_links(source_report.read_text(encoding='utf-8'))
    github_report += '\n\n[Önceki üç kaynak ağ çalışması](../v0.13.0/README.md) · [Önceki kontrollü deneyler](../v0.12.0/README.md)\n'
    notes = (
        '# ' + VERSION + ' — İç çözüm sınırı ve kalıntı konumu\n\n' + summary + '\n' + download_note + '\n'
        '[Okunabilir ayrıntılı rapor](../../raporlar/' + VERSION + '/README.md) · '
        '[Değişen dosyaların manifesti](manifest.json). '
        'Önceki tag ve Release varlıkları korunur. Sürüm numarası fiziksel yeterlilik puanı değildir.\n'
    )
    readme_path.write_text(readme, encoding='utf-8')
    (DEST / 'VERSION').write_text(VERSION + '\n', encoding='ascii')
    changelog = changelog.replace('## ' + PREVIOUS, '## ' + VERSION + ' — 26 Ekim 2026: iç çözüm sınırı ve kalıntı tanısı\n\n' + summary + '\n## ' + PREVIOUS, 1)
    changelog_path.write_text(changelog, encoding='utf-8')
    report_dir.mkdir(parents=True)
    (report_dir / 'README.md').write_text(github_report, encoding='utf-8')
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / 'README.md').write_text(notes, encoding='utf-8')
    release_notes = notes.replace('../../raporlar/' + VERSION + '/README.md', 'https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/raporlar/' + VERSION + '/README.md')
    release_notes = release_notes.replace('](manifest.json)', '](https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/surumler/' + VERSION + '/manifest.json)')
    (RUN / 'release-notes.md').write_text(release_notes, encoding='utf-8')
    for category in ['raporlar', 'cizimler', 'testler']:
        append_category_link(DEST / category / 'README.md')
        if category == 'raporlar':
            continue
        folder = DEST / category / VERSION
        folder.mkdir(parents=True, exist_ok=True)
        if category == 'cizimler':
            content = 'Bu sürümde CAD geometrisi değiştirilmedi. CFD iç çözüm ve kalıntı tanısı çalışıldı.\n'
        else:
            keywords = ('inner_cap', 'residual_probe', 'residual_probe_guards', 'kalan_artik', 'linelet', 'probe_residual')
            entries = [x for x in plan['changed'] if x['storage'] == 'git' and any(word in x['source_path'] for word in keywords)]
            assert entries, 'No changed test/evaluation artifacts selected'
            content = '\n'.join('- [' + x['source_path'] + '](../../' + x['repository_path'] + ')' for x in entries) + '\n'
        (folder / 'README.md').write_text('# ' + VERSION + '\n\n' + content, encoding='utf-8')
    print(VERSION + ' release documents prepared; inspect the probe outcome and rewritten artifact links before commit')


if __name__ == '__main__':
    main()
