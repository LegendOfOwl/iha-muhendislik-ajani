"""Prepare v0.16 publication documents only when explicitly executed.

Scientific summaries come verbatim from the completed parent report JSON. No
build, solver run, acceptance, patch execution or test count is inferred here.
Importing this module does not mutate the checkout; main() is deliberately not
idempotent and refuses to overwrite existing version documentation.
"""
from pathlib import PurePosixPath
from incremental_export import ROOT, DEST, RUN, VERSION, BASE_HEAD, PLAN, read
from release_documents_v015 import links
import re


PREVIOUS = 'v0.15.0'
REPORT = 'su2_kaynak_kontrolu_20261027'
TITLE = 'Kaynak derleme altyapısı ve karşılaştırma kontrolleri'


def _summary(value, key):
    text = value.get(key)
    assert isinstance(text, str) and text.strip(), 'Missing actual report summary: ' + key
    return text.strip() + '\n'


def assert_distribution_scope(plan):
    """Do not describe downloaded sources/generated tool binaries as excluded if selected."""
    binary_or_archive = {'.exe', '.dll', '.pdb', '.o', '.obj', '.a', '.lib',
                         '.zip', '.gz', '.tgz', '.tar', '.partial', '.whl'}
    for row in plan['changed']:
        name = row['source_path'].replace('\\', '/')
        assert not name.startswith('tools/'), 'External tools entered publication plan: ' + name
        if name.startswith('work/su2_build_20261027/'):
            suffix = PurePosixPath(name).suffix.lower()
            assert suffix not in binary_or_archive, 'Exclude generated tool/source archive: ' + name


def main():
    assert VERSION == 'v0.16.0'
    plan = read(PLAN)
    assert plan['version'] == VERSION and plan['base_head'] == BASE_HEAD
    assert_distribution_scope(plan)
    result = read(ROOT / 'outputs/reports' / (REPORT + '.json'))
    for key in ('physical_qualification_passed', 'M6_qualification_passed',
                'LLM_improvement_demonstrated'):
        assert result.get(key) is False, 'Missing or changed qualification flag: ' + key
    summary = _summary(result, 'summary_tr')
    summary_en = _summary(result, 'summary_en')
    source_report = ROOT / 'outputs/reports' / (REPORT + '.md')
    assert source_report.is_file(), 'Completed main Markdown report is required'
    markdown = links(source_report.read_text(encoding='utf-8'))
    download = (
        'Tam izlenen uygulama/kaynak ağacı otomatik **Source code (zip)** tag arşivinde; '
        'ayrı büyük analiz dosyaları sürümün `analiz-arsivi-*.zip` varlıklarından katalog '
        've geri yükleme aracıyla özgün yollarına getirilir. `KAYNAK_INDIRME.md` ve '
        '`SHA256SUMS.txt` indirme ve dosya mühürlerini açıklar. Kurulu araçlar, üretilen '
        'harici programlar ve üçüncü taraf kaynak arşivleri dağıtıma dahil edilmez; '
        'kaynak kimliği, mevcut yama/lisans manifestleri ve derleme kayıtları korunur. '
        'Önceki sürümlerin varlıkları değiştirilmez.\n'
    )
    readme_path = DEST / 'README.md'
    text = readme_path.read_text(encoding='utf-8')
    for anchor in ('Güncel dağıtım **' + PREVIOUS + '**',
                   '`main` veya `' + PREVIOUS + '`',
                   'v0.1.0 → ' + PREVIOUS + ' sürüm ve kanıt notları'):
        assert anchor in text, 'Missing previous-version README anchor: ' + anchor
    oldrow = '| [v0.15.0](surumler/v0.15.0/README.md) | Gerçek LINELET kapsamı ve tek bölge LU-SGS kontrolü |'
    assert oldrow in text
    assert '| [' + VERSION + ']' not in text
    changelog_path = DEST / 'CHANGELOG.md'
    changelog = changelog_path.read_text(encoding='utf-8')
    assert '## ' + VERSION not in changelog and '## ' + PREVIOUS in changelog
    reportdir, versiondir = DEST / 'raporlar' / VERSION, DEST / 'surumler' / VERSION
    assert not reportdir.exists() and not (versiondir / 'README.md').exists()
    category_rows = {}
    for category in ('raporlar', 'cizimler', 'testler'):
        path = DEST / category / 'README.md'
        body = path.read_text(encoding='utf-8')
        link = '- [' + VERSION + '](' + VERSION + '/README.md)'
        assert link not in body
        category_rows[path] = body.rstrip() + '\n\n' + link + '\n'
        if category != 'raporlar':
            assert not (DEST / category / VERSION / 'README.md').exists()
    test_rows = [row for row in plan['changed'] if row['storage'] == 'git'
                 and (row['source_path'].startswith('work/su2_build_20261027/')
                      or any(term in row['source_path'] for term in
                             ('su2_source_software_checks_20261027', REPORT)))]
    assert test_rows, 'No source-build test/record artifacts selected'
    # Prepare all content and validate all anchors before the first write.
    text = text.replace('Güncel dağıtım **' + PREVIOUS + '**', 'Güncel dağıtım **' + VERSION + '**')
    text = text.replace('`main` veya `' + PREVIOUS + '`', '`main` veya `' + VERSION + '`')
    text = text.replace('v0.1.0 → ' + PREVIOUS + ' sürüm ve kanıt notları',
                        'v0.1.0 → ' + VERSION + ' sürüm ve kanıt notları')
    section = (
        '## Güncel sürüm — 27 Ekim 2026\n\n'
        '[**' + VERSION + ' sonuçları: GitHub’da okunabilir rapor**](raporlar/' + VERSION + '/README.md) · '
        '[Release dosyaları](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/' + VERSION + ') · '
        '[Sürümleme politikası](SURUMLEME.md).\n\n' + summary + '\n' + download + '\n'
    )
    text, count = re.subn(r'## Güncel sürüm .*?(?=## Nereden başlanır)', lambda _: section, text, flags=re.S)
    assert count == 1
    text = text.replace(oldrow, oldrow + '\n| [' + VERSION + '](surumler/' + VERSION + '/README.md) | ' + TITLE + ' |')
    text = text.replace('[GitHub’da okunabilir güncel sonuçlar](raporlar/' + PREVIOUS + '/README.md)',
                        '[GitHub’da okunabilir güncel sonuçlar](raporlar/' + VERSION + '/README.md)')
    english = (
        '## English summary\n\n'
        'A Windows CAD/aerodynamic/CFD workflow with frozen evidence.\n\n' + summary_en + '\n'
        'GitHub’s automatic Source code (zip) tag archive provides tracked sources; '
        'separate raw analysis assets use the catalogue and hash-checking restore tool. '
        'Downloaded third-party source archives and generated external programs are excluded; '
        'source identities, available patch/license manifests and build records are retained. '
        'Earlier release assets remain available. Tags through 0.10.0 are retrospective '
        'evidence groups; 0.11.0 onward are incremental releases. Code and reports were '
        'developed with substantial Codex assistance.\n\n'
    )
    text, count = re.subn(r'## English summary.*?(?=## EXE ve lisans)', lambda _: english, text, flags=re.S)
    assert count == 1
    report_text = markdown + '\n\n[Önceki gerçek LINELET kapsamı](../v0.15.0/README.md) · [Önceki artık tanısı](../v0.14.0/README.md)\n'
    notes = ('# ' + VERSION + ' — ' + TITLE + '\n\n' + summary + '\n' + download + '\n'
             '[Ayrıntılı rapor](../../raporlar/' + VERSION + '/README.md) · [Dosya manifesti](manifest.json). '
             'Sürüm numarası fiziksel yeterlilik puanı değildir.\n')
    release_notes = notes.replace('../../raporlar/' + VERSION + '/README.md',
        'https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/raporlar/' + VERSION + '/README.md')
    release_notes = release_notes.replace('](manifest.json)',
        '](https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/surumler/' + VERSION + '/manifest.json)')
    changelog = changelog.replace('## ' + PREVIOUS,
        '## ' + VERSION + ' — 27 Ekim 2026: kaynak derlemesi ve LINELET kontrolü\n\n' + summary + '\n## ' + PREVIOUS, 1)
    test_text = '# ' + VERSION + '\n\n' + '\n'.join(
        '- [' + row['source_path'] + '](../../' + row['repository_path'] + ')' for row in test_rows) + '\n'
    # Existing historical version folders are read only throughout this routine.
    reportdir.mkdir(parents=True)
    versiondir.mkdir(parents=True, exist_ok=True)
    (reportdir / 'README.md').write_text(report_text, encoding='utf-8')
    (versiondir / 'README.md').write_text(notes, encoding='utf-8')
    (RUN / 'release-notes.md').write_text(release_notes, encoding='utf-8')
    readme_path.write_text(text, encoding='utf-8')
    (DEST / 'VERSION').write_text(VERSION + '\n', encoding='ascii')
    changelog_path.write_text(changelog, encoding='utf-8')
    for path, body in category_rows.items():
        path.write_text(body, encoding='utf-8')
    for category, body in (
        ('cizimler', '# ' + VERSION + '\n\nBu sürümde yeni CAD geometrisi üretilmedi; sabit kaynak CFD ağı ve kaynak derleme kayıtları kullanıldı.\n'),
        ('testler', test_text),
    ):
        folder = DEST / category / VERSION
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'README.md').write_text(body, encoding='utf-8')
    print(VERSION + ' documents prepared from actual report summaries; review before commit')


if __name__ == '__main__':
    main()
