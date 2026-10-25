"""Finalize source-reference distribution and construct chronological import tags."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os
import subprocess
import zipfile

from build_export import ROOT, DEST, STATE, STAGES, URL, digest, dump


def git(*args, **kwargs):
    result = subprocess.run(['git', '-C', str(DEST), *args], text=True, encoding='utf-8',
                            errors='replace', stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def main():
    assert not (DEST / '.git').exists(), 'Do not rewrite an existing repository'
    plan = json.loads((STATE / 'export_plan.json').read_text(encoding='utf-8'))
    catalog_path = DEST / 'analizler/dosya_katalogu.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    external = {
        'outputs/projects/proje-15cce2de02/data/reference/AGARD-AR138-original.pdf': 'https://www.abbottaerospace.com/downloads/agard-r-138/?ind=1461685668841&wpdmdl=3718',
        'work/blind_validation/reviewer/additional_sources/agard_ar138.pdf': 'https://www.abbottaerospace.com/downloads/agard-r-138/?ind=1461685668841&wpdmdl=3718',
        'work/mesh_research/sources/Diskin_Thomas_2008_gradient_accuracy.pdf': 'https://ntrs.nasa.gov/api/citations/20090007493/downloads/20090007493.pdf',
        'work/mesh_research/sources/SU2_AIAA2014_0243.pdf': 'https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf',
    }
    remove_by_asset = {}
    for row in catalog['files']:
        if row['source_path'] not in external: continue
        if row['storage'] == 'release_asset':
            remove_by_asset.setdefault(row['asset'], set()).add(row['repository_path'])
        else:
            target = DEST / row['repository_path']; assert target.resolve().is_relative_to(DEST.resolve())
            target.unlink()
        row.update(storage='external_reference', source_url=external[row['source_path']],
                   distribution_reason='Full third-party research paper/report retained by URL and SHA256, not republished')
        row.pop('asset', None); row.pop('release_tag', None)
        plan['versions'][row['version']] = [p for p in plan['versions'][row['version']] if p != row['repository_path']]
    for asset in plan['archives']:
        dropped = remove_by_asset.get(asset['name'])
        if dropped:
            path = Path(asset['local_path']); temp = path.with_suffix('.repack.zip')
            with zipfile.ZipFile(path) as source, zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as dest:
                for rec in source.infolist():
                    if rec.filename not in dropped:
                        with source.open(rec) as src, dest.open(rec, 'w', force_zip64=True) as sink:
                            import shutil
                            shutil.copyfileobj(src, sink, length=1024 * 1024)
            temp.replace(path)
            asset.update(bytes=path.stat().st_size, sha256=digest(path), files=asset['files'] - len(dropped))
    catalog['archives'] = [{k:v for k,v in a.items() if k != 'local_path'} for a in plan['archives']]
    summary = catalog['summary']; summary['storage_counts'] = dict(Counter(r['storage'] for r in catalog['files']))
    for key, storage in [('git_bytes', 'git'), ('asset_source_bytes', 'release_asset'), ('external_reference_bytes', 'external_reference')]:
        summary[key] = sum(r['bytes'] for r in catalog['files'] if r['storage'] == storage)
    summary['external_reference_policy'] = 'Four full research report/paper copies are preserved as source URLs plus SHA256; restore helper retrieves them separately.'
    plan['summary'] = summary
    dump(catalog_path, catalog); dump(STATE / 'export_plan.json', plan); dump(STATE / 'export_summary.json', summary)
    scope_path = DEST / 'kurulum/yayin_kapsami.json'; scope = json.loads(scope_path.read_text(encoding='utf-8'))
    scope.update(summary); dump(scope_path, scope)
    (DEST / '.gitattributes').write_text('* -text\n*.zip binary\n*.png binary\n*.exe binary\n', encoding='utf-8')
    with (DEST / '.gitignore').open('a', encoding='utf-8') as sink:
        sink.write('arsiv-indirmeleri/\n')
    with (DEST / 'THIRD_PARTY_NOTICES.md').open('a', encoding='utf-8') as sink:
        sink.write('\nAGARD ve araştırma makalelerinin dört tam PDF kopyası yeniden yayımlanmadı; kaynak adresleri ve özgün SHA256 kayıtları dosya kataloğunda durur. `kurulum/analizleri_geri_yukle.py --references` ile kaynak sunucudan ayrı indirilip doğrulanabilir. NIST teknik çizimleri kendi kaynak bildirimleriyle korunur.\n')
    for version, _, _ in STAGES:
        path = DEST / 'surumler' / version / 'manifest.json'
        meta = json.loads(path.read_text(encoding='utf-8'))
        meta['files'] = [r for r in catalog['files'] if r['version'] == version]
        meta['assets'] = [a for a in catalog['archives'] if a['tag'] == version]
        dump(path, meta)
    # Root category indexes must not link to externally stored report copies.
    for path in [DEST / 'raporlar/v0.8.0/README.md']:
        if path.exists():
            lines = path.read_text(encoding='utf-8').splitlines()
            path.write_text('\n'.join(l for l in lines if not any(p in l for p in external))+'\n', encoding='utf-8')
    if not (DEST / 'kurulum/analizleri_geri_yukle.py').exists():
        raise FileNotFoundError('Restore helper missing')
    readme = '''# İHA mühendislik ajanı

Windows üzerinde proje merkezli CAD, aerodinamik/CFD, yapısal ön analiz ve kanıtlı rapor iş akışı. Güncel dağıtım **v0.10.0**. Üniversite düzeyindeki çalışmalar için geliştirilen ve sınanan bir araç bütünüdür; genel mühendislik/CFD yeterliliği tamamlanmış veya uçuşa hazır tasarım değildir.

## Nereden başlanır?

| Klasör | İçerik |
|---|---|
| [uygulama](uygulama/) | EXE/GUI başlatıcısı, Python/PowerShell kaynakları, ajan talimatları ve özgün proje yolları |
| [raporlar](raporlar/) | Sürüme göre araştırma, sonuç ve doğrulama raporlarına erişim |
| [cizimler](cizimler/) | STEP, FreeCAD, OpenVSP, DXF ve SVG dosyalarına erişim |
| [analizler](analizler/) | CFD/FEM/model çalışma kayıtları, büyük alan arşivleri ve tam SHA256 kataloğu |
| [testler](testler/) | Test kodları, kabul ölçütleri, başarısızlık ve doğrulama kayıtları |
| [kurulum](kurulum/) | Ortam hazırlığı, mevcut yerel araçlara bağlanma ve arşiv geri yükleme |
| [surumler](surumler/) | v0.1.0 → v0.10.0 kilometre taşı notları ve dosya manifestleri |

Hazır Windows ortamında [BASLAT.cmd](BASLAT.cmd), `uygulama/outputs/Muhendislik-Merkezi.exe` açar. EXE başlatıcıdır; Python ortamları ve haricî araçlar yanında gerekir. [Kurulum açıklaması](kurulum/README.md) önce okunmalıdır. Mevcut çalışma klasörünü değiştirmeden ona yerel junction'larla bağlanmak mümkündür.

## Sürüm geçmişinin anlamı

Bu projede önceden Git geçmişi yoktu. Sürümler, elde kalan kaynak dosyaları, tarihli çıktılar ve korunmuş başarısız denemelerden **geriye dönük gruplandırılarak** oluşturuldu. Eski tag'ler özgün tarihteki tam çalışan uygulama kopyası değildir. Tam güncel içerik için `main` veya `v0.10.0` kullanın. Git commit/yayın tarihleri bugün oluşturulan arşivin tarihidir; kaynak dosyaların gözlenen değiştirme tarihleri ayrıca katalogdadır.

| Sürüm | Kanıt grubu |
|---|---|
'''
    readme += '\n'.join(f'| [{v}](surumler/{v}/README.md) | {name} |' for v,name,_ in STAGES)
    readme += '''

## Dosyalar ve yeniden üretim

Bütün özgün proje dosyaları `uygulama/work` ve `uygulama/outputs` düzeninde kalır; üstteki kategoriler yolları bozmadan erişim sağlar. Kaynak kod, rapor, çizim, küçük veri ve ham loglar Git'tedir. Büyük ağ/alan/restart dosyaları sürüm Releases varlıklarındaki ZIP paketlerindedir. [Katalog](analizler/dosya_katalogu.json) her dosyanın yolunu, boyutunu, SHA256 değerini ve hangi arşivden geri yükleneceğini içerir.

`python kurulum/analizleri_geri_yukle.py` büyük alanları indirip özgün konumlarına çıkarır ve hash'lerini doğrular. `--references` tam üçüncü taraf makale/rapor PDF'lerini kaynak adreslerinden ayrıca getirir. Ortamlar, kurulu solver/CAD programları, indirilen kurucular, model ağırlıkları ve hesap/OAuth bilgileri depoya kopyalanmaz; kurulum betikleri ve kaynak/sürüm manifestleri tutulur.

## Mevcut sonuçların sınırı

- OpenVSP/XFOIL, FreeCAD/CalculiX, SU2, Elmer ve OpenAeroStruct ile gerçek yerel çalışmalar yapıldı; kapsamları raporlarında belirtilir.
- Küçük CAD modellerinin özgün başarı ve başarısızlıkları korunur; Codex düzeltmeleri modelin başarısı sayılmaz.
- Son ajan dersleri için 39/39 kod/dosya kontrolü ve temel yazılım için 26/26 kontrol kayıtlıdır. Görülmemiş mühendislik görevinde önce/sonra LLM iyileşmesi henüz ölçülmedi.
- RAE2822 ve ONERA M6 genel fizik kabulleri geçmedi. y+ veya kuvvet ekranının tek başına geçmesi bütün CFD doğrulamasını kapatmaz.
- Gerçek İHA girdileri ile araç yeterlilik örnekleri ayrı tutulur. ANSYS ve OpenFOAM kurulmuş değildir; Fusion yalnız OAuth aşamasında doğrulanmıştır.

[Güncel proje özeti](uygulama/outputs/Proje-Ozeti.html) · [Ajan dersleri](uygulama/outputs/reports/ajan_talimat_gelisimi_20261024.html) · [M6 sonuçları](uygulama/outputs/reports/onera_m6_24_ekim.html) · [Üçüncü taraf kaynakları](THIRD_PARTY_NOTICES.md)

Dosya/arşiv dağıtım sınırları için [GitHub büyük dosya belgeleri](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) ve [Releases belgeleri](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) esas alındı. Başarısız sonuçlar gizlenmedi; eşikler yayın için değiştirilmedi.
'''
    (STATE / 'README-final.md').write_text(readme, encoding='utf-8')
    git('init', '-b', 'main')
    git('config', 'user.name', 'LegendOfOwl')
    git('config', 'user.email', '80211423+LegendOfOwl@users.noreply.github.com')
    git('config', 'core.autocrlf', 'false')
    git('config', 'core.quotePath', 'false')
    # Use CLI authentication only inside this repository; do not alter global Git.
    gh = json.loads((STATE / 'github_cli_install.json').read_text(encoding='utf-8'))['executable'].replace('\\', '/')
    git('config', 'credential.helper', '')
    git('config', '--add', 'credential.helper', '!' + gh + ' auth git-credential')
    tracked = set(); commits = []
    for index, (version, name, detail) in enumerate(STAGES):
        final = index == len(STAGES) - 1
        if final:
            (DEST / 'README.md').write_text(readme, encoding='utf-8')
            files = [p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file() and '.git' not in p.relative_to(DEST).parts]
        else:
            (DEST / 'README.md').write_text(f'# İHA mühendislik ajanı — {version}\n\n{name}\n\n{detail}\n\nBu tag mevcut kanıtlardan geriye dönük oluşturulan kısmi bir içe aktarma aşamasıdır; özgün eski çalışan uygulama imajı değildir. Bütün güncel kaynaklar main/v0.10.0 içindedir.\n\n[Bu aşamanın manifesti](surumler/{version}/manifest.json)\n', encoding='utf-8')
            files = list(plan['versions'].get(version, []))
            for folder in ['surumler', 'raporlar', 'cizimler', 'testler']:
                child = DEST / folder / version
                if child.exists(): files += [p.relative_to(DEST).as_posix() for p in child.rglob('*') if p.is_file()]
        (DEST / 'VERSION').write_text(version + '\n', encoding='ascii')
        (DEST / 'CHANGELOG.md').write_text('# Değişiklik günlüğü\n\nGeriye dönük gruplandırılmış içe aktarım; gerçek eski Git tarihçesi değildir.\n\n' + '\n'.join(f'## {v} — {n}\n\n{d}\n' for v,n,d in STAGES[:index+1]), encoding='utf-8')
        files += ['README.md', 'VERSION', 'CHANGELOG.md', '.gitattributes', '.gitignore']
        files = sorted(set(files))
        listing = STATE / 'git-paths.bin'
        listing.write_bytes(b''.join((':(literal)' + p).encode('utf-8') + b'\0' for p in files))
        git('add', '-f', '--pathspec-from-file=' + str(listing), '--pathspec-file-nul')
        git('commit', '-m', f'{version}: {name} (geriye dönük kanıt grubu)')
        git('tag', '-a', version, '-m', f'{name}; retrospective evidence import, not original historical source snapshot')
        commit = git('rev-parse', 'HEAD'); commits.append({'version': version, 'commit': commit, 'name': name})
        print(json.dumps(commits[-1], ensure_ascii=False), flush=True)
    git('fsck', '--full')
    assert not git('status', '--porcelain')
    dump(STATE / 'local_repository.json', {'repository': str(DEST), 'url': URL, 'commits': commits, 'history_reconstructed': True})


if __name__ == '__main__':
    main()
