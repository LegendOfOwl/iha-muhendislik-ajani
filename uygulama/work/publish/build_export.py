"""Prepare an honest chronological Git import and complete project asset export."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib
import json
import os
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT.parent / 'iha-muhendislik-ajani'
STATE = ROOT / 'work/publish'
ASSETS = STATE / 'assets'
URL = 'https://github.com/LegendOfOwl/iha-muhendislik-ajani'
STAGES = [
    ('v0.1.0', 'Temel hesap ve girdi kontrolleri', 'Birim, girdi ve sayısal kontroller; ilk araç hazırlığı.'),
    ('v0.2.0', 'Yerel CAD ve aerodinamik araçlar', 'OpenVSP/VSPAERO, XFOIL, FreeCAD, CalculiX ve kanat karşılaştırmaları.'),
    ('v0.3.0', 'CAD modelleri ve kullanım denetimi', 'K-1B, Cadmonkey ve Zero-to-CAD deneyleri; özgün başarısızlıklar ve istem denetimleri.'),
    ('v0.4.0', 'Deterministik geometri ve hafif CFD', 'Parametrik kanat, karmaşık VLM, SU2 ve Elmer araç sınamaları.'),
    ('v0.5.0', 'Proje merkezli arayüz ve aeroelastisite', 'EXE başlatıcı, proje kayıtları, profile CFD ve OpenAeroStruct örnekleri.'),
    ('v0.6.0', 'Karmaşık CAD ve ilk ONERA M6', 'NIST kaynak parçaları ve ONERA deney verisiyle ilk 3B RANS kıyası.'),
    ('v0.7.0', 'Kaynak geometri ve ayrı analiz sınaması', 'RAE2822 v1/v2 geometri aktarımı, dondurulmuş tahminler ve deney değerlendirmesi.'),
    ('v0.8.0', 'C-grid araştırması ve M6 devamı', 'Konumsal ağ düzeltmeleri, başarısız sayısal kontroller ve 24 Ekim M6 koşuları.'),
    ('v0.9.0', 'Hata dersleri ve ajan talimatı', 'Kanıtlı hata defteri, operasyonel bellek, 39 kontrol ve başlatıcı talimat sürümü.'),
    ('v0.10.0', 'Düzenlenmiş GitHub dağıtımı', 'Kategori dizinleri, tam dosya kataloğu, sürüm notları ve hash kontrollü analiz arşivleri.'),
]


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def stage_for(p):
    q = p.lower()
    if q.startswith('work/publish/'): return 'v0.10.0'
    if q in ['work/agent/project.py', 'work/agent/report.py']: return 'v0.10.0'
    if q.startswith(('.agents/', 'work/agent_learning/')) or q in ['agents.md', 'project_state.md', 'work/agent/learning.py']: return 'v0.9.0'
    if any(s in q for s in ['agent_learning', 'ajan_talimat', 'ajan_hafiza', '20261024-164603']): return 'v0.9.0'
    if q.startswith(('work/m6_followup/', 'work/mesh_research/')): return 'v0.8.0'
    if 'proje-15cce2de02' in q:
        return 'v0.8.0' if any(s in q for s in ['/v3', 'prediction_v3', 'v3_', 'research']) else 'v0.7.0'
    if 'proje-e9319baef1' in q:
        return 'v0.8.0' if any(s in q for s in ['20261024', '24_ekim']) else 'v0.6.0'
    if q.startswith('work/blind_validation/') or any(s in q for s in ['blind_cfd', 'source_geometry', 'kaynak_geometri', 'review_v2']): return 'v0.7.0'
    if any(s in q for s in ['m6_followup', 'onera_m6_24', 'kaynakli_cfd', 'mesh_research']): return 'v0.8.0'
    if q.startswith('work/validation/') or any(s in q for s in ['proje-e8fe92444f', 'nist_nasa', 'karmasik_cad', 'validation_benchmark']): return 'v0.6.0'
    if q.startswith(('work/agent/', 'work/openaerostruct/', 'work/workflow/')) or any(s in q for s in ['aerostruct', 'proje-0314dcd012', 'profile_cfd', 'hafif_cfd', 'muhendislik-merkezi', 'projects/']): return 'v0.5.0'
    if q.startswith(('work/models/', 'work/research/')) or any(s in q for s in ['k_family', 'cad_model', 'cadmonkey', 'k_model', 'zero_', 'usage_audit', 'model_usage', 'checked_parts']): return 'v0.3.0'
    if q.startswith(('work/geometry/', 'work/qualification/')) or any(s in q for s in ['parametric', 'complex_vlm', 'complex-vlm', 'elmer', 'su2', '/cfd_', 'cfd_qualification', 'cfd_reference', 'muhendislik_seviyesi']): return 'v0.4.0'
    if q.startswith(('work/native/', 'work/fem/', 'work/studies/')) or any(s in q for s in ['freecad', 'xfoil', 'openvsp', 'vspaero', 'wing_study', 'external_', 'fem_', '/cad/', '/plots/']): return 'v0.2.0'
    if q.startswith(('outputs/data/projects/', 'outputs/data/tasks/', 'outputs/data/requests/')): return 'v0.5.0'
    return 'v0.1.0'


SECRET = {
    'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'openai_key': re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}\b'),
    'aws_key': re.compile(rb'\bAKIA[0-9A-Z]{16}\b'),
    'literal_secret': re.compile(rb'''(?i)["']?(?:access_token|refresh_token|client_secret|password|api_key)["']?\s*[:=]\s*["']([A-Za-z0-9_./+\-=]{24,})["']'''),
}
TEXT = {'.py', '.ps1', '.cs', '.json', '.toml', '.yaml', '.yml', '.xml', '.cfg', '.ini', '.log', '.txt', '.md', '.html', '.htm', '.cmd', '.bat', '.csv', '.vspscript', '.scad'}


def secret_findings(path):
    if path.suffix.lower() not in TEXT: return []
    matches = set(); overlap = b''
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            current = overlap + chunk
            for label, expression in SECRET.items():
                for found in expression.finditer(current):
                    value = found.group(1) if label == 'literal_secret' else found.group()
                    if label == 'literal_secret' and any(word in value.lower() for word in [b'placeholder', b'example', b'redacted', b'os.environ', b'getenv']): continue
                    matches.add(label)
            overlap = current[-512:]
    return sorted(matches)


def excluded(rel):
    parts = rel.parts; q = rel.as_posix(); top = parts[0]
    if top in {'.venv', '.venv-cad', 'tools'}: return 'external_runtime_or_model'
    if top == '.codex': return 'local_connector_configuration'
    if '__pycache__' in parts or rel.suffix.lower() == '.pyc': return 'generated_python_cache'
    if q.startswith(('work/setup/downloads/', 'work/cache/', 'work/freecad/')): return 'download_or_application_cache'
    if q.startswith('work/publish/') and rel.suffix != '.py': return 'local_publication_state_or_auth'
    if any(p.lower() in {'auth', 'credentials', '.ssh'} for p in parts): return 'authentication_material'
    if rel.name.lower() in {'.env', 'hosts.yml', 'credentials.json', 'auth.json', 'token.json'}: return 'authentication_material'
    return None


def is_bulk(rel, size):
    q = rel.as_posix()
    if size < 1024 * 1024: return False
    # Keep report media and finished CAD directly inspectable in the repository.
    if size < 20 * 1024 * 1024 and (rel.suffix.lower() in {'.png', '.jpg', '.jpeg', '.svg', '.step', '.stp', '.fcstd', '.dxf', '.vsp3'} or '/reports/' in q): return False
    return True


def write_category(folder, title, records, predicate):
    selected = [r for r in records if r['storage'] == 'git' and predicate(r['source_path'])]
    lines = [f'# {title}', '', 'Asıl dosyalar uygulamanın bağıl yolları korunarak `uygulama/` içinde saklanır. Bu dizin sürümlere göre erişim sağlar.', '']
    for version, name, _ in STAGES:
        subset = [r for r in selected if r['version'] == version]
        if not subset: continue
        child = DEST / folder / version; child.mkdir(parents=True, exist_ok=True)
        content = [f'# {version} — {name}', '', f'{len(subset)} dosya. Bu bir geriye dönük kanıt grubudur; eksiksiz eski uygulama imajı değildir.', '']
        for row in subset:
            target = '../../' + row['repository_path']
            content.append(f'- [{row["source_path"]}]({target})')
        (child / 'README.md').write_text('\n'.join(content) + '\n', encoding='utf-8')
        lines.append(f'- [{version} — {name}]({version}/README.md): {len(subset)} dosya')
    (DEST / folder / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    assert not DEST.exists(), 'Do not overwrite an existing checkout'
    DEST.mkdir(); ASSETS.mkdir(exist_ok=True)
    candidates = []; omitted = []; findings = []
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not excluded((Path(folder) / d).relative_to(ROOT))]
        for name in names:
            path = Path(folder) / name; rel = path.relative_to(ROOT); reason = excluded(rel)
            if reason:
                omitted.append({'path': rel.as_posix(), 'reason': reason}); continue
            if path.is_symlink():
                omitted.append({'path': rel.as_posix(), 'reason': 'symbolic_link'}); continue
            labels = secret_findings(path)
            if labels:
                findings.append({'path': rel.as_posix(), 'types': labels}); continue
            candidates.append((rel, path.stat().st_size))
    dump(STATE / 'secret_scan.json', {'findings': findings, 'scanned_files': len(candidates) + len(findings), 'values_printed': False})
    assert not findings, 'Possible secrets found; inspect metadata report before publishing'
    records = []; bulk = defaultdict(list); versions = defaultdict(list)
    for rel, size in sorted(candidates):
        version = stage_for(rel.as_posix()); hashed = digest(ROOT / rel)
        row = {'source_path': rel.as_posix(), 'repository_path': 'uygulama/' + rel.as_posix(),
               'bytes': size, 'sha256': hashed, 'version': version,
               'source_mtime_utc': datetime.fromtimestamp((ROOT / rel).stat().st_mtime, timezone.utc).isoformat()}
        if is_bulk(rel, size):
            row['storage'] = 'release_asset'; bulk[version].append(row)
        else:
            row['storage'] = 'git'; target = DEST / row['repository_path']; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target); assert digest(target) == hashed
            versions[version].append(row['repository_path'])
        records.append(row)
    archives = []
    for version, group in sorted(bulk.items()):
        packs = [[]]; total = 0
        for row in group:
            if total + row['bytes'] > 600 * 1024 * 1024 and packs[-1]:
                packs.append([]); total = 0
            packs[-1].append(row); total += row['bytes']
        for index, pack in enumerate(packs, 1):
            name = f'analiz-arsivi-{version}-part{index:02d}.zip'; path = ASSETS / name
            with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as zipped:
                for row in pack:
                    assert digest(ROOT / row['source_path']) == row['sha256'], row['source_path']
                    zipped.write(ROOT / row['source_path'], row['repository_path'])
                    row.update(asset=name, release_tag=version)
            assert path.stat().st_size < 2 * 1024**3
            archives.append({'name': name, 'tag': version, 'bytes': path.stat().st_size,
                             'sha256': digest(path), 'files': len(pack), 'local_path': str(path),
                             'download_url': URL + '/releases/download/' + version + '/' + name})
            print(json.dumps({'archive': name, 'MiB': round(path.stat().st_size / 2**20, 1), 'files': len(pack)}), flush=True)
    counts = Counter(r['storage'] for r in records)
    summary = {'created_utc': datetime.now(timezone.utc).isoformat(), 'version': 'v0.10.0', 'repository_url': URL,
               'history_kind': 'retrospective_grouped_import_not_original_git_history',
               'source_root': str(ROOT), 'files': len(records), 'storage_counts': dict(counts),
               'git_bytes': sum(r['bytes'] for r in records if r['storage'] == 'git'),
               'asset_source_bytes': sum(r['bytes'] for r in records if r['storage'] == 'release_asset'),
               'excluded_roots': ['.venv', '.venv-cad', 'tools', '.codex', 'work/setup/downloads', 'work/cache', 'work/freecad'],
               'excluded_reason': 'Third-party installed runtimes/model weights, caches and local auth; installer code and version/source manifests are retained.',
               'expert_or_physical_qualification_claimed': False}
    catalog = {'summary': summary, 'files': records, 'archives': [{k:v for k,v in a.items() if k != 'local_path'} for a in archives]}
    dump(DEST / 'analizler/dosya_katalogu.json', catalog)
    dump(STATE / 'export_plan.json', {'destination': str(DEST), 'versions': dict(versions), 'archives': archives, 'summary': summary})
    dump(DEST / 'kurulum/yayin_kapsami.json', {**summary, 'excluded_files': omitted, 'secret_scan_findings': [], 'secret_scan_values_printed': False})
    for version, name, detail in STAGES:
        folder = DEST / 'surumler' / version; folder.mkdir(parents=True)
        subset = [r for r in records if r['version'] == version]
        assets = [a for a in archives if a['tag'] == version]
        doc = f'''# {version} — {name}

{detail}

Bu sürüm, mevcut dosyaların ve korunmuş denemelerin **geriye dönük gruplandırılmış içe aktarımıdır**. Önceden Git geçmişi bulunmadığı için özgün tarihteki eksiksiz çalışan uygulama kopyası veya gerçek eski commit olarak sunulmaz. Commit ve yayın tarihi bu GitHub hazırlığının tarihidir; dosyaların gözlenen değiştirme tarihleri katalogda ayrıca saklanır.

- Bu grupta {len(subset)} özgün dosya var.
- Büyük analiz alanları {len(assets)} ayrı ZIP varlığıyla bu sürümün Releases bölümünde saklanır.
- Başarısız denemeler korunmuştur. Yazılım testi, fiziksel tasarım veya genel CFD doğrulaması değildir.
- [Tam dosya kataloğu](../../analizler/dosya_katalogu.json)

Geçmiş aşamaları incelemek için sürüm dizinlerini ve tag'leri; bütün güncel kaynaklar için `main` veya `v0.10.0` kullanın.
'''
        (folder / 'README.md').write_text(doc, encoding='utf-8')
        dump(folder / 'manifest.json', {'version': version, 'name': name, 'history_kind': summary['history_kind'], 'files': subset,
                                       'assets': [{k:v for k,v in a.items() if k != 'local_path'} for a in assets]})
        notes = f'{version} — {name}\n\n{detail}\n\nGeriye dönük kanıt grubu; özgün eski Git geçmişi veya eksiksiz eski çalışan sürüm iddiası yoktur. Ham alanlar için bu sürümün analiz-arsivi ZIP dosyalarını indirin. Başarısız fizik kabulleri açık kalır.\n'
        (STATE / (version + '-release-notes.md')).write_text(notes, encoding='utf-8')
    for folder, title, predicate in [
        ('raporlar', 'Raporlar', lambda p: '/reports/' in p or p == 'outputs/Proje-Ozeti.html'),
        ('cizimler', 'Çizimler ve CAD', lambda p: p.endswith(('.step', '.stp', '.FCStd', '.vsp3', '.dxf', '.scad', '.svg'))),
        ('testler', 'Testler ve doğrulama kayıtları', lambda p: p.startswith(('work/tests/', 'work/agent_learning/')) or any(s in p for s in ['qualification', 'audit', 'test_results', 'validation_quality']))]:
        (DEST / folder).mkdir(exist_ok=True)
        write_category(folder, title, records, predicate)
    (DEST / 'analizler/README.md').write_text('''# Analizler ve ham alan arşivleri

Çözücü ayarları, küçük veriler, raporlar ve görseller `uygulama/outputs` içinde özgün bağıl yollarıyla bulunur. Büyük ağ/alan/restart dosyaları GitHub Releases içindeki `analiz-arsivi-*.zip` paketlerindedir. Hiçbir ham dosyanın içeriği değiştirilmez; SHA256 ve geri yüklenecek yol dosya kataloğunda bulunur.

- [Dosya kataloğu ve arşiv URL'leri](dosya_katalogu.json)
- [RAE2822 sonuçları](../uygulama/outputs/projects/proje-15cce2de02/reports/)
- [ONERA M6 sonuçları](../uygulama/outputs/projects/proje-e9319baef1/reports/)
- [Örnek CFD, FEM ve model çalışmaları](../uygulama/outputs/simulations/)

Arşivleri depo köküne çıkarmak özgün `uygulama/...` yollarını tamamlar. Otomatik ve hash kontrollü geri yükleme için `kurulum/analizleri_geri_yukle.py` kullanılır. Ham alan isteyen rapor bağlantıları arşiv geri yüklenene kadar yerel diskte bulunmaz. Bu depodaki sayısal/deney kabulleri kendi kapsamlarıyla sınırlıdır; genel RAE/M6 fizik yeterliliği geçmedi.
''', encoding='utf-8')
    (DEST / 'kurulum/README.md').write_text('''# Kurulum ve mevcut yerel ortam

Windows x64 ve Python 3.12 gerekir. Uygulamanın proje kökü `uygulama/` klasörüdür; bütün kaynak ve raporların özgün bağıl düzeni burada korunur.

1. Kilitli Python bağımlılıkları: `uygulama/work/setup/requirements-core.txt` ve `requirements-cad.txt`. Mevcut hazırlama betiği: `uygulama/work/setup/rebuild_light.ps1 -PythonBase TAM_PYTHON_EXE_YOLU`.
2. Yerel solver/CAD/model kurulum betikleri ve kaynak/sürüm kayıtları `uygulama/work/setup` içindedir. Üçüncü taraf programların kurulu dizinleri ve model ağırlıkları depoya kopyalanmaz. Fusion OAuth, hesap erişimi ve lisanslar aktarılmaz. ANSYS ve OpenFOAM bu projede kurulmuş sayılmaz.
3. `tool_config.json` ve `*_install.json` özgün makine yollarını belgeliyor. Başka kurulumda bu yolları yeni araç konumlarına göre hazırlayıp `doctor` ve ilgili gerçek testlerle denetleyin. Bu yayın tek başına bütün ağır araçları otomatik kurduğu iddiasında değildir.
4. Aynı bilgisayardaki mevcut çalışma ortamına bağlanmak için `Yerel-Ortami-Bagla.ps1 -MevcutProje TAM_KAYNAK_KLASORU` kullanılır; yalnız bu depoda `.venv`, `.venv-cad` ve `tools` junction'ları oluşturur, global ayar değiştirmez.
5. Büyük analizleri geri yüklemek için `analizleri_geri_yukle.py` çalıştırın. İnternet ve birkaç GB disk alanı gerekir; indirme/çıkarma SHA256 ile denetlenir.
6. Hazır ortamda kökteki `BASLAT.cmd`, `uygulama/outputs/Muhendislik-Merkezi.exe` açar. EXE başlatıcıdır; klasörleri ve Python ortamları yanında kalmalıdır.

Yayınlama için kullanılan GitHub oturumu, auth dosyaları, yerel bağlantı ayarları ve tarayıcı ekran görüntüleri bu depoda bulunmaz. Teknik envanter ve kapsam `yayin_kapsami.json` dosyasındadır.
''', encoding='utf-8')
    (DEST / 'THIRD_PARTY_NOTICES.md').write_text('''# Üçüncü taraf kaynakları ve lisanslar

Kurulu Python paketleri, CAD/CFD programları ve model ağırlıkları yeniden dağıtılmadı. Kurulum manifestleri resmî indirme adresi, sürüm ve mümkün olduğunda hash içerir. Kaynak çalışma örnekleri ve NASA/ONERA/NIST verileri kendi kaynak/atıf ve kullanım koşullarıyla saklanır; kamuya açık olmak bütün içerik için tek lisans olduğu anlamına gelmez. Kaynak manifestlerini `uygulama/work/validation/sources`, `qualification/sources`, `openaerostruct/sources` ve ilgili proje `data/reference` klasörlerinde inceleyin.

Proje sahibi genel bir açık kaynak lisansı seçmedi; bu yayınla kendiliğinden MIT/GPL veya başka lisans atanmadı. Bağımsız üçüncü taraf dosyalarının mevcut bildirimleri geçerlidir.
''', encoding='utf-8')
    (DEST / '.gitignore').write_text('**/__pycache__/\n**/*.pyc\n**/.venv/\n**/.venv-cad/\n**/tools/\n**/.codex/\n**/.env\n**/auth/\n**/hosts.yml\n*.part\n', encoding='utf-8')
    (DEST / '.gitattributes').write_text('* -text\n*.md text eol=lf\n*.cmd text eol=crlf\n*.ps1 -text\n', encoding='utf-8')
    (DEST / 'BASLAT.cmd').write_text('@echo off\nstart "" "%~dp0uygulama\\outputs\\Muhendislik-Merkezi.exe"\n', encoding='ascii')
    (DEST / 'AGENTS.md').write_text('# Depo çalışma yönlendirmesi\n\nMühendislik proje kökü `uygulama/` klasörüdür. Önce `uygulama/AGENTS.md`, `uygulama/PROJECT_STATE.md` ve `uygulama/.agents/skills/iha-muhendislik/SKILL.md` okuyun. `surumler/` geriye dönük kanıt gruplarıdır; dondurulmuş eski çıktıları değiştirmeyin. Büyük dosyalar `analizler/dosya_katalogu.json` ile sürüm arşivlerinde izlenir.\n', encoding='utf-8')
    dump(STATE / 'export_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
