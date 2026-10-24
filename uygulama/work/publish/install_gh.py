"""Fetch portable GitHub CLI from its official signed-release asset metadata."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'iha-muhendislik-publication'})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def main():
    release = json.loads(get('https://api.github.com/repos/cli/cli/releases/latest'))
    asset = next(a for a in release['assets'] if a['name'].endswith('windows_amd64.zip'))
    checks = next(a for a in release['assets'] if a['name'].endswith('checksums.txt'))
    checksum_text = get(checks['browser_download_url']).decode()
    expected = next(line.split()[0] for line in checksum_text.splitlines() if line.split()[-1] == asset['name'])
    content = get(asset['browser_download_url']); actual = hashlib.sha256(content).hexdigest()
    assert actual == expected
    if asset.get('digest'):
        assert asset['digest'] == 'sha256:' + actual
    dest = ROOT / 'tools/github-cli' / release['tag_name']; dest.mkdir(parents=True, exist_ok=True)
    archive = dest / asset['name']; archive.write_bytes(content)
    with zipfile.ZipFile(archive) as zipped:
        for entry in zipped.infolist():
            assert (dest / entry.filename).resolve().is_relative_to(dest.resolve())
        zipped.extractall(dest)
    exe = next(dest.rglob('gh.exe'))
    manifest = {'installed_utc': datetime.now(timezone.utc).isoformat(), 'version': release['tag_name'],
                'url': asset['browser_download_url'], 'sha256': actual, 'executable': str(exe),
                'scope': 'portable task-local; no system PATH change'}
    (ROOT / 'work/publish/github_cli_install.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
