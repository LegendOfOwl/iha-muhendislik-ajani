"""Reviewable v0.15 documents; no commit, solver or remote mutation."""
from incremental_export import ROOT, DEST, RUN, VERSION, PLAN, read
from release_documents_v014 import append_category_link, finite_number
import re, posixpath
from urllib.parse import urlsplit, urlunsplit

PREVIOUS = 'v0.14.0'


def links(markdown):
    def replace(m):
        p = urlsplit(m[2])
        if p.scheme or p.netloc or not p.path or p.path.startswith('/'): return m[0]
        path = posixpath.normpath(posixpath.join('outputs/reports', p.path))
        assert path.startswith(('outputs/', 'work/'))
        return m[1] + urlunsplit(('', '', '../../uygulama/' + path, p.query, p.fragment)) + ')'
    return re.sub(r'(!?\[[^\]\n]*\]\()([^\s)]+)\)', replace, markdown)


def main():
    assert VERSION == 'v0.15.0'
    plan = read(PLAN)
    assert plan['version'] == VERSION
    c = read(ROOT / 'outputs/reports/linelet_coverage_20261027.json')
    r = read(ROOT / 'outputs/reports/prec_partition_control_20261027.json')
    g = read(ROOT / 'outputs/reports/coverage_partition_guards_20261027.json')
    assert c['native_membership_accepted'] and r['quality']['comparable']
    assert r['effect_passed'] is False and r['physical_qualification_passed'] is False
    assert g['passed'] and g['tests_run'] == 17 and g['failures'] == g['errors'] == 0
    gain = finite_number(r['quality']['density_log10_gain'])
    work = finite_number(r['work_ratio'])
    seconds = finite_number(r['observed_time_ratio'])
    summary = (
        '27 Ekim 2026. Üç yeni native SU2 koşusu tamamlandı. Gerçek LINELET alanında '
        f'{c["nodes"]} düğümün {c["linelet_nodes"]} tanesi çizgilerde; önceki doğrulanmış '
        f'aşama artığının yoğunluk kare toplamının %{100*c["covered_Rho_squared_share"]:.4f}’i '
        'bu birliğin içinde. Bu konumsal kapsam ölçümüdür; yeni alanın yeniden hesaplanan '
        'artığı, nedensellik veya ağ hata bandı değildir.\n\n'
        'Aynı kaynak ağ ve başlangıç dosyasıyla, toplam dört iş parçacığı korunarak yalnız '
        'LU-SGS önkoşullayıcısının bölünmesi 0→1 değiştirildi. 200 adımlık çiftte yoğunluk '
        f'kazancı {gain:.8f} log10, toplam Krylov işi oranı {work:.8f}, gözlenen süre oranı '
        f'{seconds:.8f} oldu. Ön kayıtlı ortak etki ve maliyet kabulü geçmedi. 17 yeni '
        'yazılım kontrolü geçti; başarısız denemeler ve ham çıktılar korundu. Uzun çizgili '
        'kaynak derlemesi sonraki yöntem adayıdır; henüz derlenmedi veya çalıştırılmadı. '
        'Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.\n'
    )
    download = (
        'Tam izlenen uygulama/kaynak ağacı otomatik **Source code (zip)** tag arşivinde; '
        'yeni büyük alanlar `analiz-arsivi-*.zip` dosyasındadır. `KAYNAK_INDIRME.md`, '
        '`SHA256SUMS.txt`, dosya kataloğu ve geri yükleme aracı özgün yolları ve dosya '
        'mühürlerini açıklar. Önceki sürümlerin varlıkları korunur.\n'
    )
    readme_path = DEST / 'README.md'
    text = readme_path.read_text(encoding='utf-8')
    assert 'Güncel dağıtım **' + PREVIOUS + '**' in text
    text = text.replace('Güncel dağıtım **' + PREVIOUS + '**', 'Güncel dağıtım **' + VERSION + '**')
    text = text.replace('`main` veya `' + PREVIOUS + '`', '`main` veya `' + VERSION + '`')
    text = text.replace('v0.1.0 → ' + PREVIOUS + ' sürüm ve kanıt notları', 'v0.1.0 → ' + VERSION + ' sürüm ve kanıt notları')
    section = ('## Güncel sürüm — 27 Ekim 2026\n\n'
               '[**' + VERSION + ' sonuçları: GitHub’da okunabilir rapor**](raporlar/' + VERSION + '/README.md) · '
               '[Release dosyaları](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/' + VERSION + ') · '
               '[Sürümleme politikası](SURUMLEME.md).\n\n' + summary + '\n' + download + '\n')
    text, n = re.subn(r'## Güncel sürüm .*?(?=## Nereden başlanır)', lambda _: section, text, flags=re.S)
    assert n == 1
    oldrow = '| [v0.14.0](surumler/v0.14.0/README.md) | İç çözüm sınırı kıyası ve kaynak koduna dayalı kalıntı konum tanısı |'
    assert oldrow in text
    text = text.replace(oldrow, oldrow + '\n| [' + VERSION + '](surumler/' + VERSION + '/README.md) | Gerçek LINELET kapsamı ve tek bölge LU-SGS kontrolü |')
    text = text.replace('[GitHub’da okunabilir güncel sonuçlar](raporlar/' + PREVIOUS + '/README.md)', '[GitHub’da okunabilir güncel sonuçlar](raporlar/' + VERSION + '/README.md)')
    english = (
        '## English summary\n\nA Windows CAD/aerodynamic/CFD workflow with frozen evidence. '
        'Version 0.15.0 measures native LINELET membership: 7,200 of 52,689 nodes, covering '
        f'{100*c["covered_Rho_squared_share"]:.4f}% of a separately verified sequential-stage '
        'density squared residual. This is static membership against a prior RHS snapshot, '
        'not a recomputed residual or causal error estimate. A single-domain LU-SGS control '
        f'with four total threads achieved {gain:.8f} log10 density gain at {work:.8f} times '
        f'the Krylov work and {seconds:.8f} times the observed elapsed time. The preregistered '
        'joint effect/cost gate failed. All 17 new software checks passed. A longer-line source '
        'build is proposed but has not been built or run. Physical/RAE/M6/UAV gates remain open; '
        'improved LLM behaviour has not been demonstrated. GitHub’s automatic tag archive '
        'provides tracked sources; separate raw assets use the hash-checking restore tool. '
        'Tags through 0.10.0 are retrospective evidence groups; 0.11.0 onward are incremental '
        'releases. Code and reports were developed with substantial Codex assistance.\n\n'
    )
    text, n = re.subn(r'## English summary.*?(?=## EXE ve lisans)', lambda _: english, text, flags=re.S)
    assert n == 1
    changelog_path = DEST / 'CHANGELOG.md'
    changelog = changelog_path.read_text(encoding='utf-8')
    assert '## ' + VERSION not in changelog and '## ' + PREVIOUS in changelog
    reportdir = DEST / 'raporlar' / VERSION
    versiondir = DEST / 'surumler' / VERSION
    assert not reportdir.exists() and not (versiondir / 'README.md').exists()
    reportdir.mkdir(parents=True)
    versiondir.mkdir(exist_ok=True)
    source = ROOT / 'outputs/reports/cfd_cizgi_kapsami_20261027.md'
    (reportdir / 'README.md').write_text(links(source.read_text(encoding='utf-8')) + '\n\n[Önceki artık tanısı](../v0.14.0/README.md) · [Üç kaynak ağ](../v0.13.0/README.md)\n', encoding='utf-8')
    notes = ('# ' + VERSION + ' — LINELET kapsamı ve LU-SGS bölünmesi\n\n' + summary + '\n' + download + '\n'
             '[Ayrıntılı rapor](../../raporlar/' + VERSION + '/README.md) · [Dosya manifesti](manifest.json). '
             'Sürüm numarası fiziksel yeterlilik puanı değildir.\n')
    (versiondir / 'README.md').write_text(notes, encoding='utf-8')
    (RUN / 'release-notes.md').write_text(notes.replace('../../raporlar/' + VERSION + '/README.md',
        'https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/raporlar/' + VERSION + '/README.md').replace(
        '](manifest.json)', '](https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/' + VERSION + '/surumler/' + VERSION + '/manifest.json)'), encoding='utf-8')
    readme_path.write_text(text, encoding='utf-8')
    (DEST / 'VERSION').write_text(VERSION + '\n', encoding='ascii')
    changelog_path.write_text(changelog.replace('## ' + PREVIOUS, '## ' + VERSION + ' — 27 Ekim 2026: çizgi kapsamı ve bölünme kontrolü\n\n' + summary + '\n## ' + PREVIOUS, 1), encoding='utf-8')
    for category in ['raporlar', 'cizimler', 'testler']:
        append_category_link(DEST / category / 'README.md')
        if category == 'raporlar': continue
        folder = DEST / category / VERSION
        folder.mkdir(parents=True, exist_ok=True)
        if category == 'cizimler':
            body = 'Bu sürümde yeni CAD geometrisi üretilmedi; mevcut kaynak CFD ağında sayısal yöntem ve kapsam ölçüldü.\n'
        else:
            rows = [x for x in plan['changed'] if x['storage'] == 'git' and any(w in x['source_path'] for w in ['20261027', 'linelet_coverage'])]
            assert rows
            body = '\n'.join('- [' + x['source_path'] + '](../../' + x['repository_path'] + ')' for x in rows) + '\n'
        (folder / 'README.md').write_text('# ' + VERSION + '\n\n' + body, encoding='utf-8')
    print('v0.15.0 documents prepared')


if __name__ == '__main__': main()
