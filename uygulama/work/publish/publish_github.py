"""Publish only the verified, explicitly authorized public repository and assets."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import subprocess
import threading
import time
import zipfile

from build_export import ROOT, DEST, STATE, ASSETS, STAGES, URL, digest, dump

REPO = 'LegendOfOwl/iha-muhendislik-ajani'
ENV = dict(os.environ)
ENV.update(GH_CONFIG_DIR=str(ROOT / 'tools/github-cli/auth'), GIT_TERMINAL_PROMPT='0', GH_PROMPT_DISABLED='1')
# This verified checkout was created by the sandbox SID; trust only this exact
# path in this process tree when the authenticated Windows account uploads it.
config_index = int(ENV.get('GIT_CONFIG_COUNT', '0'))
ENV.update({f'GIT_CONFIG_KEY_{config_index}': 'safe.directory',
            f'GIT_CONFIG_VALUE_{config_index}': str(DEST), 'GIT_CONFIG_COUNT': str(config_index + 1)})
GH = json.loads((STATE / 'github_cli_install.json').read_text(encoding='utf-8'))['executable']
LOCK = threading.Lock()
PROGRESS = {'repository': REPO, 'url': URL, 'visibility': 'public', 'status': 'preparing', 'uploaded_assets': []}
if (STATE / 'github_publication_state.json').exists():
    prior = json.loads((STATE / 'github_publication_state.json').read_text(encoding='utf-8'))
    assert prior['repository'] == REPO and prior['url'] == URL
    PROGRESS = prior


def run(command, timeout=1800, check=True):
    result = subprocess.run(command, cwd=DEST, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def gh(*args):
    return run([GH, *args]).stdout.strip()


def api(path):
    return json.loads(gh('api', path))


def save_progress():
    PROGRESS['updated_utc'] = datetime.now(timezone.utc).isoformat()
    dump(STATE / 'github_publication_state.json', PROGRESS)
    dump(ROOT / 'outputs/data/github_publication_20261024.json', PROGRESS)


def main():
    verified = json.loads((STATE / 'local_verification.json').read_text(encoding='utf-8'))
    assert verified['passed'] and verified['commits'] == 10
    assert gh('api', 'user', '--jq', '.login') == 'LegendOfOwl'
    plan = json.loads((STATE / 'export_plan.json').read_text(encoding='utf-8'))
    current = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
    assert run(['git', 'status', '--porcelain']).stdout == ''
    # A convenient current package supplements GitHub's automatically generated source archives.
    bundle = ASSETS / 'uygulama-ve-raporlar-v0.10.0.zip'
    files = [p for p in run(['git', 'ls-files', '-z']).stdout.split('\0') if p]
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as zipped:
        for name in files: zipped.write(DEST / name, name)
    with zipfile.ZipFile(bundle) as zipped:
        assert zipped.testzip() is None and set(zipped.namelist()) == set(files)
    extras = [{'name': bundle.name, 'tag': 'v0.10.0', 'local_path': str(bundle), 'bytes': bundle.stat().st_size,
               'sha256': digest(bundle), 'kind': 'application_sources_reports_no_external_runtimes'}]
    all_assets = plan['archives'] + extras
    sums = ASSETS / 'SHA256SUMS.txt'
    sums.write_text('\n'.join(a['sha256'] + '  ' + a['name'] for a in all_assets) + '\n', encoding='ascii')
    all_assets.append({'name': sums.name, 'tag': 'v0.10.0', 'local_path': str(sums), 'bytes': sums.stat().st_size,
                       'sha256': digest(sums), 'kind': 'checksums'})
    PROGRESS.update(status='local_package_verified', head=current,
                    original_files=plan['summary']['files'], git_original_files=verified['git_original_file_hashes'],
                    archived_original_files=verified['archived_original_file_hashes'], external_reference_files=4,
                    expected_assets=[{k:v for k,v in a.items() if k != 'local_path'} for a in all_assets],
                    total_upload_bytes=sum(a['bytes'] for a in all_assets), versions=[v for v,_,_ in STAGES])
    save_progress()
    existing = run([GH, 'api', 'repos/' + REPO], check=False)
    if existing.returncode == 0:
        known = json.loads(existing.stdout)
        if PROGRESS.get('repository_id') != known['id']:
            raise RuntimeError('Repository name already exists without this task creation receipt; no changes made')
    elif '404' not in existing.stderr:
        raise RuntimeError(existing.stderr)
    else:
        print('CREATE_PUBLIC_REPOSITORY', REPO, flush=True)
        gh('repo', 'create', REPO, '--public', '--source', str(DEST), '--remote', 'origin',
           '--description', 'Windows İHA mühendislik ajanı: proje arayüzü, CAD/CFD/FEM araçları, sürümlü kanıtlar ve raporlar.')
    repo = api('repos/' + REPO)
    assert repo['private'] is False and repo['full_name'] == REPO
    PROGRESS.update(status='pushing_history', repository_id=repo['id']); save_progress()
    print('PUSH_MAIN_AND_10_TAGS', flush=True)
    pushed = run(['git', 'push', '-u', 'origin', 'main', '--tags'])
    print(pushed.stderr[-1500:], flush=True)
    for index, (version, name, _) in enumerate(STAGES):
        present = run([GH, 'api', 'repos/' + REPO + '/releases/tags/' + version], check=False)
        if present.returncode == 0:
            assert json.loads(present.stdout)['tag_name'] == version
            continue
        if '404' not in present.stderr: raise RuntimeError(present.stderr)
        args = ['release', 'create', version, '--repo', REPO, '--verify-tag', '--title', version + ' — ' + name,
                '--notes-file', str(STATE / (version + '-release-notes.md'))]
        args += ['--latest'] if index == len(STAGES)-1 else ['--prerelease']
        gh(*args)
        print('RELEASE_CREATED', version, flush=True)
    PROGRESS['status'] = 'uploading_assets'; save_progress()

    def upload(asset):
        print(json.dumps({'upload_start': asset['name'], 'MiB': round(asset['bytes'] / 2**20, 1)}), flush=True)
        failures = []
        for attempt in range(2):
            remote = api('repos/' + REPO + '/releases/tags/' + asset['tag'])
            match = next((a for a in remote['assets'] if a['name'] == asset['name']), None)
            if match:
                assert match.get('digest') == 'sha256:' + asset['sha256'] and match['size'] == asset['bytes']
                break
            result = run([GH, 'release', 'upload', asset['tag'], asset['local_path'], '--repo', REPO], check=False)
            if result.returncode == 0: break
            failures.append(result.stderr)
            # Never overwrite an existing asset; accept only an exact server-side hash match.
            remote = api('repos/' + REPO + '/releases/tags/' + asset['tag'])
            match = next((a for a in remote['assets'] if a['name'] == asset['name']), None)
            if match and match.get('digest') == 'sha256:' + asset['sha256'] and match['size'] == asset['bytes']:
                break
            if attempt == 1: raise RuntimeError(asset['name'] + ': ' + result.stderr)
            time.sleep(2)
        remote = api('repos/' + REPO + '/releases/tags/' + asset['tag'])
        match = next(a for a in remote['assets'] if a['name'] == asset['name'])
        assert match['size'] == asset['bytes']
        assert match.get('digest') == 'sha256:' + asset['sha256'], 'Remote digest missing/mismatched: ' + asset['name']
        item = {'name': asset['name'], 'tag': asset['tag'], 'size': match['size'], 'sha256': asset['sha256'],
                'server_digest_matches': True, 'url': match['browser_download_url'], 'attempt_failures': failures}
        with LOCK:
            PROGRESS['uploaded_assets'] = [a for a in PROGRESS['uploaded_assets'] if a['name'] != item['name']]
            PROGRESS['uploaded_assets'].append(item); save_progress()
            print(json.dumps({'upload_verified': asset['name'], 'completed': len(PROGRESS['uploaded_assets']), 'total': len(all_assets)}), flush=True)
        return item

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(upload, a) for a in sorted(all_assets, key=lambda a: a['bytes'], reverse=True)]
        for future in as_completed(futures): future.result()
    # Verify remote state independently of the commands' success messages.
    remotes = dict(line.split()[::-1] for line in run(['git', 'ls-remote', 'origin']).stdout.splitlines())
    assert remotes['refs/heads/main'] == current
    for version, _, _ in STAGES:
        assert remotes['refs/tags/' + version] == run(['git', 'rev-parse', version]).stdout.strip()
    repo = api('repos/' + REPO)
    tags = api('repos/' + REPO + '/tags?per_page=100')
    releases = api('repos/' + REPO + '/releases?per_page=100')
    assert len(tags) == 10 and len(releases) == 10 and repo['private'] is False
    assert {r['tag_name'] for r in releases} == {v for v,_,_ in STAGES}
    assert all(not r['draft'] for r in releases)
    assert len(PROGRESS['uploaded_assets']) == len(all_assets)
    PROGRESS.update(status='published_verified', published_utc=datetime.now(timezone.utc).isoformat(),
                    remote_head_matches=True, public_verified=True, remote_tags=10, remote_releases=10,
                    remote_assets=len(all_assets), local_repository=str(DEST))
    save_progress()
    print(json.dumps({'status': PROGRESS['status'], 'url': URL, 'tags': 10, 'releases': 10, 'assets': len(all_assets)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
