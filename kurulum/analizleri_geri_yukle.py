"""Download public release archives and restore only catalogued, hashed files."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def restore(catalog, version=None, verify_only=False):
    assets = [a for a in catalog['archives'] if version is None or a['tag'] == version]
    if version and not assets:
        raise ValueError('Bu sürüm için büyük analiz arşivi yok: ' + version)
    cache = ROOT / 'arsiv-indirmeleri'
    if not verify_only:
        cache.mkdir(exist_ok=True)
    for asset in assets:
        records = [r for r in catalog['files'] if r.get('asset') == asset['name']]
        if verify_only:
            missing = [r['repository_path'] for r in records if not (ROOT / r['repository_path']).is_file()]
            wrong = [r['repository_path'] for r in records if (ROOT / r['repository_path']).is_file() and sha(ROOT / r['repository_path']) != r['sha256']]
            if missing or wrong:
                raise ValueError(json.dumps({'asset': asset['name'], 'missing': missing, 'changed': wrong}, ensure_ascii=False))
            print('Dosyalar doğrulandı:', asset['name']); continue
        archive = cache / asset['name']
        if not archive.exists():
            partial = archive.with_suffix('.zip.part')
            req = urllib.request.Request(asset['download_url'], headers={'User-Agent': 'iha-muhendislik-restore'})
            print('İndiriliyor:', asset['name'], flush=True)
            with urllib.request.urlopen(req, timeout=180) as response, partial.open('wb') as stream:
                shutil.copyfileobj(response, stream, length=1024 * 1024)
            if sha(partial) != asset['sha256']:
                raise ValueError('Arşiv SHA256 uyuşmadı; dosyalar çıkarılmadı.')
            partial.replace(archive)
        if sha(archive) != asset['sha256']:
            raise ValueError('Yerel arşiv SHA256 uyuşmadı.')
        # Older assets use one member per destination. New assets may share
        # immutable content; every destination still has its own expected hash.
        expected = {r['repository_path']: r for r in records}
        if len(expected) != len(records):
            raise ValueError('Katalogda yinelenen hedef yolu.')
        members = {}
        for rec in records:
            member = rec.get('archive_member', rec['repository_path'])
            if not member.startswith('uygulama/') or '..' in Path(member).parts:
                raise ValueError('Güvenli olmayan arşiv üyesi.')
            if member in members and members[member] != rec['sha256']:
                raise ValueError('Aynı arşiv üyesi için farklı hash bekleniyor.')
            members[member] = rec['sha256']
        with zipfile.ZipFile(archive) as zipped:
            if set(zipped.namelist()) != set(members) or len(zipped.namelist()) != len(members):
                raise ValueError('Arşiv dosya listesi katalogla eşleşmiyor.')
            for name, rec in expected.items():
                dest = (ROOT / name).resolve()
                if not dest.is_relative_to(ROOT) or not name.startswith('uygulama/'):
                    raise ValueError('Güvenli olmayan arşiv yolu.')
                if dest.exists():
                    if dest.is_file() and sha(dest) == rec['sha256']:
                        continue
                    raise ValueError('Mevcut farklı dosyanın üzerine yazılmadı: ' + name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                partial = dest.with_name(dest.name + '.part')
                with zipped.open(rec.get('archive_member', name)) as source, partial.open('xb') as stream:
                    shutil.copyfileobj(source, stream, length=1024 * 1024)
                if sha(partial) != rec['sha256']:
                    raise ValueError('Çıkarılan dosya SHA256 uyuşmadı: ' + name)
                partial.replace(dest)
        print('Geri yüklendi ve doğrulandı:', asset['name'], flush=True)


def restore_references(catalog, verify_only=False):
    records = [r for r in catalog['files'] if r['storage'] == 'external_reference']
    cache = ROOT / 'arsiv-indirmeleri/kaynaklar'
    if not verify_only:
        cache.mkdir(parents=True, exist_ok=True)
    for rec in records:
        target = (ROOT / rec['repository_path']).resolve()
        if not target.is_relative_to(ROOT) or not rec['repository_path'].startswith('uygulama/'):
            raise ValueError('Güvenli olmayan kaynak yolu')
        if target.exists():
            if target.is_file() and sha(target) == rec['sha256']:
                continue
            raise ValueError('Mevcut kaynak dosyası değiştirilmedi: ' + rec['repository_path'])
        if verify_only:
            raise ValueError('Kaynak henüz indirilmemiş: ' + rec['repository_path'])
        downloaded = cache / (rec['sha256'] + '.pdf')
        if not downloaded.exists():
            if not rec['source_url'].startswith('https://'):
                raise ValueError('Kaynak adresi HTTPS olmalı')
            req = urllib.request.Request(rec['source_url'], headers={'User-Agent': 'Mozilla/5.0 iha-muhendislik-restore'})
            temporary = downloaded.with_suffix('.part')
            with urllib.request.urlopen(req, timeout=180) as response, temporary.open('wb') as stream:
                shutil.copyfileobj(response, stream)
            if sha(temporary) != rec['sha256']:
                raise ValueError('Kaynak içeriği özgün SHA256 ile eşleşmedi; özgün dosya yerine atanmadı.')
            temporary.replace(downloaded)
        if sha(downloaded) != rec['sha256']:
            raise ValueError('Önbellekteki kaynak SHA256 uyuşmuyor')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(downloaded, target)
        print('Kaynak indirildi ve doğrulandı:', rec['repository_path'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Büyük analiz alanlarını yayımlanmış sürüm arşivlerinden geri yükle')
    parser.add_argument('--version', help='Örnek: v0.8.0. Belirtilmezse bütün arşivler.')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--references', action='store_true', help='Büyük alanlar yerine üçüncü taraf PDF kaynaklarını ayrı indir')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'analizler/dosya_katalogu.json').read_text(encoding='utf-8'))
    if args.references:
        restore_references(catalog, args.verify_only)
    else:
        restore(catalog, args.version, args.verify_only)
