"""Prioritize the current package while two large, disjoint field uploads run."""
import json
import argparse
import time
from publish_github import ROOT, STATE, ASSETS, REPO, GH, PROGRESS, run, api
from build_export import digest, dump


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--field-tail', action='store_true')
    parser.add_argument('--one-asset')
    args = parser.parse_args()
    state = json.loads((STATE / 'github_publication_state.json').read_text(encoding='utf-8'))
    assert api('repos/' + REPO)['id'] == state['repository_id']
    expected = state['expected_assets']
    chosen = [a for a in expected if a['tag'] == 'v0.10.0']
    chosen += [a for a in expected if a['tag'] in {'v0.1.0','v0.2.0','v0.3.0','v0.4.0','v0.5.0','v0.6.0'}]
    if args.field_tail:
        priority_names = {a['name'] for a in chosen}
        deadline = time.monotonic() + 3600
        while True:
            marker = STATE / 'priority_uploads.json'
            if marker.exists():
                done = {a['name'] for a in json.loads(marker.read_text(encoding='utf-8'))['verified']}
                if priority_names.issubset(done): break
            if time.monotonic() > deadline: raise TimeoutError('Priority queue did not finish; no extra upload started')
            time.sleep(10)
        # These assets are far behind the main uploader's active prefix, so the
        # extra stream finishes them before the main workers reach their names.
        names = ['analiz-arsivi-v0.7.0-part01.zip', 'analiz-arsivi-v0.8.0-part07.zip', 'analiz-arsivi-v0.7.0-part03.zip']
        chosen = [next(a for a in expected if a['name'] == n) for n in names]
    if args.one_asset:
        chosen = [next(a for a in expected if a['name'] == args.one_asset)]
    verified = []
    for asset in chosen:
        path = ASSETS / asset['name']; assert digest(path) == asset['sha256']
        release = api('repos/' + REPO + '/releases/tags/' + asset['tag'])
        present = next((a for a in release['assets'] if a['name'] == asset['name']), None)
        if present is None:
            print('PRIORITY_UPLOAD', asset['name'], flush=True)
            run([GH, 'release', 'upload', asset['tag'], str(path), '--repo', REPO], timeout=3600)
            release = api('repos/' + REPO + '/releases/tags/' + asset['tag'])
            present = next(a for a in release['assets'] if a['name'] == asset['name'])
        if present.get('state') != 'uploaded':
            continue
        assert present['size'] == asset['bytes'] and present.get('digest') == 'sha256:' + asset['sha256']
        verified.append({'name': asset['name'], 'sha256': asset['sha256'], 'url': present['browser_download_url']})
        marker = 'one_asset_upload.json' if args.one_asset else ('tail_uploads.json' if args.field_tail else 'priority_uploads.json')
        dump(STATE / marker, {'verified': verified})
        print('PRIORITY_VERIFIED', asset['name'], flush=True)


if __name__ == '__main__':
    main()
