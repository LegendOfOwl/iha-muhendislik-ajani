"""Verify every committed source byte and every archived raw field before upload."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import zipfile

from build_export import ROOT, DEST, STATE, digest, dump


def restores_test():
    spec = importlib.util.spec_from_file_location('restore_export', DEST / 'kurulum/analizleri_geri_yukle.py')
    restore = importlib.util.module_from_spec(spec); spec.loader.exec_module(restore)
    results = []
    fixture_base = STATE / 'restore-fixtures'; fixture_base.mkdir(exist_ok=True)
    cases = ['valid', 'verify-only', 'archive-hash', 'member-list', 'traversal', 'field-hash', 'existing-changed', 'missing-field', 'reference-existing', 'reference-changed']
    for case in cases:
        with tempfile.TemporaryDirectory(prefix='case_', dir=fixture_base) as folder:
            base = Path(folder).resolve(); assert base.is_relative_to(fixture_base.resolve())
            restore.ROOT = base; cache = base / 'arsiv-indirmeleri'; cache.mkdir()
            name = 'uygulama/outputs/simulations/fixture/field.bin'
            if case == 'traversal': name = 'uygulama/../../outside.bin'
            payload = b'publication test fixture, not a CFD field'
            archive = cache / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as zipped:
                zipped.writestr(name, payload)
                if case == 'member-list': zipped.writestr('unknown.bin', b'not listed')
            record = {'repository_path': name, 'storage': 'release_asset', 'asset': archive.name,
                      'sha256': hashlib.sha256(payload).hexdigest()}
            asset = {'name': archive.name, 'tag': 'test', 'sha256': digest(archive),
                     'download_url': 'https://invalid.example/never-used'}
            catalog = {'archives': [asset], 'files': [record]}
            if case == 'archive-hash': asset['sha256'] = '0' * 64
            if case == 'field-hash': record['sha256'] = '0' * 64
            target = base / name
            if case in ['existing-changed', 'verify-only', 'reference-existing', 'reference-changed']:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload if case in ['verify-only', 'reference-existing'] else b'user modified file')
            expected_rejection = case not in ['valid', 'verify-only', 'reference-existing']
            try:
                if case.startswith('reference-'):
                    record.update(storage='external_reference', source_url='https://invalid.example/never-used')
                    restore.restore_references(catalog, verify_only=True)
                else:
                    restore.restore(catalog, verify_only=case in ['verify-only', 'missing-field'])
                assert not expected_rejection, 'Bad input was accepted'
                assert target.read_bytes() == payload
                results.append({'case': case, 'passed': True})
            except ValueError:
                assert expected_rejection, case
                if case in ['existing-changed', 'reference-changed']:
                    assert target.read_bytes() == b'user modified file'
                assert not (base.parent / 'outside.bin').exists()
                results.append({'case': case, 'passed': True})
    return results


def main():
    catalog = json.loads((DEST / 'analizler/dosya_katalogu.json').read_text(encoding='utf-8'))
    plan = json.loads((STATE / 'export_plan.json').read_text(encoding='utf-8'))
    source_rows = [r for r in catalog['files'] if r['storage'] == 'git']
    errors = []; repo_checks = 0
    for row in source_rows:
        if digest(DEST / row['repository_path']) != row['sha256']:
            errors.append('Working copy changed: ' + row['repository_path'])
    # Read actual Git blobs so newline normalization cannot silently alter evidence.
    process = subprocess.Popen(['git', '-C', str(DEST), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for row in source_rows:
        process.stdin.write(('HEAD:' + row['repository_path'] + '\n').encode('utf-8')); process.stdin.flush()
        header = process.stdout.readline().decode().strip().split()
        if len(header) != 3 or header[1] != 'blob':
            errors.append('Missing Git blob: ' + row['repository_path']); continue
        size = int(header[2]); hashed = hashlib.sha256()
        while size:
            block = process.stdout.read(min(size, 1024 * 1024)); assert block
            size -= len(block); hashed.update(block)
        assert process.stdout.read(1) == b'\n'
        if hashed.hexdigest() != row['sha256']:
            errors.append('Git blob differs from source: ' + row['repository_path'])
        repo_checks += 1
    process.stdin.close(); assert process.wait() == 0
    archived = []
    for asset in plan['archives']:
        path = Path(asset['local_path']); assert digest(path) == asset['sha256']
        expected = {r['repository_path']: r for r in catalog['files'] if r.get('asset') == asset['name']}
        with zipfile.ZipFile(path) as zipped:
            assert len(zipped.namelist()) == len(expected) and set(zipped.namelist()) == set(expected)
            for member, row in expected.items():
                hashed = hashlib.sha256()
                with zipped.open(member) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''): hashed.update(block)
                assert hashed.hexdigest() == row['sha256'], member
        archived.append({'asset': asset['name'], 'files': len(expected), 'sha256': asset['sha256'], 'passed': True})
        print(json.dumps({'archive_verified': asset['name'], 'files': len(expected)}), flush=True)
    results = restores_test()
    for file in ['kurulum/analizleri_geri_yukle.py']:
        compile((DEST / file).read_bytes(), file, 'exec')
    tracked = subprocess.check_output(['git', '-C', str(DEST), 'ls-files', '-z']).decode('utf-8').split('\0')
    forbidden = [p for p in tracked if p and any(s in '/' + p + '/' for s in ['/auth/', '/.codex/', '/.venv/', '/.venv-cad/', '/tools/', '/github_authorization.png/'])]
    assert not forbidden, forbidden
    status = subprocess.check_output(['git', '-C', str(DEST), 'status', '--porcelain']).decode()
    assert not status, status
    refs = subprocess.check_output(['git', '-C', str(DEST), 'tag', '--list']).decode().splitlines()
    assert len(refs) == 10
    commits = subprocess.check_output(['git', '-C', str(DEST), 'rev-list', '--count', 'HEAD']).decode().strip()
    assert commits == '10'
    report = {'verified_utc': datetime.now(timezone.utc).isoformat(), 'passed': not errors,
              'git_original_file_hashes': repo_checks, 'archives': archived,
              'archived_original_file_hashes': sum(a['files'] for a in archived),
              'external_references': len([r for r in catalog['files'] if r['storage'] == 'external_reference']),
              'restore_adversarial_tests': results, 'tags': refs, 'commits': int(commits),
              'forbidden_files': forbidden, 'errors': errors, 'tracked_files': len([p for p in tracked if p]),
              'scope': 'Publication/integrity checks, not new CAD/CFD or LLM physical validation'}
    dump(STATE / 'local_verification.json', report)
    dump(ROOT / 'outputs/reports/github_local_verification_20261024.json', report)
    assert not errors, errors
    print(json.dumps({k:v for k,v in report.items() if k not in ['archives', 'restore_adversarial_tests']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
