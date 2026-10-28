"""Prepare v0.18 publication documents only when explicitly executed.

Scientific summaries come verbatim from the completed parent report JSON. No
build, solver run, acceptance, patch execution or test count is inferred here.
Importing this module does not mutate the checkout; main() is deliberately not
idempotent and refuses to overwrite existing version documentation.
"""
from pathlib import PurePosixPath
from incremental_export import ROOT, DEST, RUN, VERSION, BASE_HEAD, PLAN, read
from release_documents_v015 import links
import re


PREVIOUS = 'v0.17.0'
REPORT = 'acik_sorunlar_ve_derin_arastirma_20261028'
TITLE = 'Açık problemler, öncelikler ve derin araştırma'
REQUIRED_RESEARCH = frozenset(
    'work/deep_research_20261027/' + stem + suffix
    for stem in ('numerics', 'validation_mesh', 'cad_agent')
    for suffix in ('.md', '.json')
) | frozenset({
    'work/deep_research_20261027/research_control.py',
    'outputs/reports/' + REPORT + '.md',
    'outputs/reports/' + REPORT + '.json',
    'outputs/reports/' + REPORT + '.html',
})


def _summary(value, key):
    text = value.get(key)
    assert isinstance(text, str) and text.strip(), 'Missing actual report summary: ' + key
    return text.strip() + '\n'


def validate_research_report(value):
    """A literature release must never inherit old solver/build success claims."""
    for key in ('physical_qualification_passed', 'M6_qualification_passed',
                'LLM_improvement_demonstrated'):
        assert value.get(key) is False, 'Missing or changed qualification flag: ' + key
    for key in ('new_native_CFD_runs', 'new_builds'):
        assert type(value.get(key)) is int and value[key] == 0, 'Research-only zero count required: ' + key
    return _summary(value, 'summary_tr'), _summary(value, 'summary_en')


def assert_research_payloads(plan):
    selected = {row['source_path'].replace('\\', '/') for row in plan['changed']
                if row['storage'] == 'git'}
    missing = sorted(REQUIRED_RESEARCH - selected)
    assert not missing, 'Missing reviewed research payloads: ' + ', '.join(missing)


def assert_distribution_scope(plan):
    """Do not describe downloaded sources/generated tool binaries as excluded if selected."""
    binary_or_archive = {'.exe', '.dll', '.pdb', '.o', '.obj', '.a', '.lib',
                         '.zip', '.gz', '.tgz', '.tar', '.partial', '.whl'}
    for row in plan['changed']:
        name = row['source_path'].replace('\\', '/')
        parts = PurePosixPath(name).parts
        assert parts and not PurePosixPath(name).is_absolute() and '..' not in parts and ':' not in parts[0], 'Unsafe source path: ' + name
        assert not name.startswith('tools/'), 'External tools entered publication plan: ' + name
        if name.startswith(('work/su2_build_20261027/', 'work/su2_build_resume_20261027/')):
            suffix = PurePosixPath(name).suffix.lower()
            assert suffix not in binary_or_archive, 'Exclude generated tool/source archive: ' + name


def main():
    assert VERSION == 'v0.18.0'
    assert BASE_HEAD == '87c932868b14407f2892e957f3e68d02a0a8b270'
    plan = read(PLAN)
    assert plan['version'] == VERSION and plan['base_head'] == BASE_HEAD
    assert_distribution_scope(plan)
    assert_research_payloads(plan)
    result = read(ROOT / 'outputs/reports' / (REPORT + '.json'))
    summary, summary_en = validate_research_report(result)
    source_report = ROOT / 'outputs/reports' / (REPORT + '.md')
    assert source_report.is_file(), 'Completed main Markdown report is required'
    markdown = links(source_report.read_text(encoding='utf-8'))
    # Large linked data live in release ZIPs; do not publish a nonexistent Git path.
    catalogue = read(DEST / 'analizler/dosya_katalogu.json')
    archives = {asset['name']: asset['download_url'] for asset in catalogue['archives']}
    for row in catalogue['files']:
        if row['storage'] == 'release_asset':
            target = '../../' + row['repository_path']
            markdown = markdown.replace('](' + target + ')', '](' + archives[row['asset']] + ')')
    markdown += '\n\nBu sürümün araştırma kayıtları Markdown/JSON ve ana HTML raporundadır. Önceki büyük dosyaların özgün yolu ve SHA256 değeri katalogda korunur; ilgili arşivler geri yükleme aracıyla açılır.\n'
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
    oldrow = '| [v0.17.0](surumler/v0.17.0/README.md) | SU2 kaynak derlemesi ve kontrollü karşılaştırma |'
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
                 and (row['source_path'].replace('\\', '/').startswith('work/deep_research_20261027/')
                      or REPORT in row['source_path']
                      or any(term in row['source_path'] for term in
                             ('test_v018_', 'verify_remote_v018', 'release_documents_v018', 'deep_research_checks_20261028')))]
    assert test_rows, 'No research or publication guard artifacts selected'
    # Prepare all content and validate all anchors before the first write.
    text = text.replace('Güncel dağıtım **' + PREVIOUS + '**', 'Güncel dağıtım **' + VERSION + '**')
    text = text.replace('`main` veya `' + PREVIOUS + '`', '`main` veya `' + VERSION + '`')
    text = text.replace('v0.1.0 → ' + PREVIOUS + ' sürüm ve kanıt notları',
                        'v0.1.0 → ' + VERSION + ' sürüm ve kanıt notları')
    section = (
        '## Güncel sürüm — 28 Ekim 2026\n\n'
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
    report_text = markdown + '\n\n[Önceki kontrollü SU2 kaynak karşılaştırması](../v0.17.0/README.md)\n'
    notes = ('# ' + VERSION + ' — ' + TITLE + '\n\n' + summary + '\n' + download + '\n'
             '[Ayrıntılı rapor](../../raporlar/' + VERSION + '/README.md) · [Dosya manifesti](manifest.json). '
             'Sürüm numarası fiziksel yeterlilik puanı değildir.\n')
    release_notes = notes.replace('../../raporlar/' + VERSION + '/README.md',
        'https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/raporlar/' + VERSION + '/README.md')
    release_notes = release_notes.replace('](manifest.json)',
        '](https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/surumler/' + VERSION + '/manifest.json)')
    changelog = changelog.replace('## ' + PREVIOUS,
        '## ' + VERSION + ' — 28 Ekim 2026: Açık problemler, öncelikler ve derin araştırma\n\n' + summary + '\n## ' + PREVIOUS, 1)
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
        ('cizimler', '# ' + VERSION + '\n\nBu sürüm kaynak araştırması ve açık problem önceliklendirmesidir. Yeni CAD geometrisi, native CFD veya çözücü derlemesi üretilmedi.\n'),
        ('testler', test_text),
    ):
        folder = DEST / category / VERSION
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'README.md').write_text(body, encoding='utf-8')
    print(VERSION + ' documents prepared from actual report summaries; review before commit')


if __name__ == '__main__':
    main()
