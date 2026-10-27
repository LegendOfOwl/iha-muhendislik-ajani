"""Preserve the 14 earlier releases, 33 assets and 28 annotated-tag refs.

Run ``before`` on the clean v0.14.0 checkout, then ``after`` only once the new
publisher has verified v0.15.0. This tool never commits or publishes anything.
"""
from publish_incremental import api, run, REPO, RUN, VERSION, BASE_HEAD, ROOT
from incremental_export import read, dump, now, digest
import sys


PREVIOUS = 'v0.14.0'
PRIOR_RELEASES = 14
PRIOR_ASSETS = 33
PRIOR_TAG_REFS = 28


def snapshot():
    releases = api('repos/' + REPO + '/releases?per_page=100')
    data = {
        release['tag_name']: {
            'id': release['id'],
            'assets': sorted([
                {'id': asset['id'], 'name': asset['name'], 'bytes': asset['size'], 'digest': asset.get('digest')}
                for asset in release['assets']
            ], key=lambda asset: asset['name']),
        }
        for release in releases if release['tag_name'] != VERSION
    }
    tags = {}
    for line in run(['git', 'ls-remote', 'origin', 'refs/tags/*']).splitlines():
        sha, ref = line.split()
        if ref not in {'refs/tags/' + VERSION, 'refs/tags/' + VERSION + '^{}'}:
            tags[ref] = sha
    return {'releases': data, 'tags': tags}


def checked_counts(state):
    assert len(state['releases']) == PRIOR_RELEASES
    assert set(state['releases']) == {f'v0.{i}.0' for i in range(1, PRIOR_RELEASES + 1)}
    assert sum(len(r['assets']) for r in state['releases'].values()) == PRIOR_ASSETS
    assert len(state['tags']) == PRIOR_TAG_REFS
    assert set(state['tags']) == {
        'refs/tags/v0.' + str(i) + '.0' + suffix
        for i in range(1, PRIOR_RELEASES + 1) for suffix in ('', '^{}')
    }
    assert state['tags']['refs/tags/' + PREVIOUS + '^{}'] == BASE_HEAD


def main(mode):
    assert VERSION == 'v0.15.0'
    assert BASE_HEAD == 'd6eb54a79d2c6eec7e4f54c977561e0f7cd14fed'
    path = RUN / 'prior_remote_history.json'
    if mode == 'before':
        assert not path.exists(), 'Preserve the prerelease remote-history snapshot'
        assert run(['git', 'rev-parse', 'HEAD']) == BASE_HEAD
        assert not run(['git', 'status', '--porcelain'])
        assert run(['git', 'ls-remote', 'origin', 'refs/heads/main']).split()[0] == BASE_HEAD
        assert not run(['git', 'ls-remote', 'origin', 'refs/tags/' + VERSION, 'refs/tags/' + VERSION + '^{}'])
        state = snapshot()
        checked_counts(state)
        dump(path, state)
        print({'prior_releases': PRIOR_RELEASES, 'prior_assets': PRIOR_ASSETS, 'prior_tag_refs': PRIOR_TAG_REFS})
    elif mode == 'after':
        previous = read(path)
        checked_counts(previous)
        assert snapshot() == previous, 'A prior release asset or tag ref changed'
        publication = read(RUN / 'publication_state.json')
        assert publication['version'] == VERSION
        assert publication['status'] == 'published_verified'
        assert publication['remote_head_matches'] is True
        assert publication['finished_utc']
        assert all(a['server_digest_matches'] is True for a in publication['uploaded'])
        assert run(['git', 'ls-remote', 'origin', 'refs/heads/main']).split()[0] == publication['head']
        assert run(['git', 'ls-remote', 'origin', 'refs/tags/' + VERSION + '^{}']).split()[0] == publication['head']
        state_path = ROOT / 'work/publish/github_publication_state.json'
        prior = read(state_path)
        backup = ROOT / 'work/publish/github_publication_state_v0.14.0.json'
        if not backup.exists():
            assert prior['current_version'] == PREVIOUS
            dump(backup, prior)
        else:
            assert read(backup)['current_version'] == PREVIOUS
            assert prior['current_version'] in {PREVIOUS, VERSION}
        versions = sorted(set(prior.get('versions', [])) | set(previous['releases']) | {VERSION},
                          key=lambda v: tuple(map(int, v.lstrip('v').split('.'))))
        prior.update(
            current_version=VERSION,
            head=publication['head'],
            published_utc=publication['finished_utc'],
            updated_utc=now(),
            versions=versions,
            status='published_verified',
            remote_head_matches=True,
            remote_tags=PRIOR_RELEASES + 1,
            remote_releases=PRIOR_RELEASES + 1,
            remote_assets=PRIOR_ASSETS + len(publication['uploaded']),
            latest_incremental_publication_state=str((RUN / 'publication_state.json').relative_to(ROOT)),
            uploaded_assets=[dict(tag=VERSION, name=a['name'], size=a['bytes'], sha256=a['sha256'],
                                  server_digest_matches=True, url=a['url']) for a in publication['uploaded']],
        )
        dump(state_path, prior)
        result = {
            'checked_utc': now(),
            'prior_releases_unchanged': PRIOR_RELEASES,
            'prior_assets_unchanged': PRIOR_ASSETS,
            'prior_tag_refs_unchanged': PRIOR_TAG_REFS,
            'remote_snapshot_sha256': digest(path),
            'current_head': publication['head'],
            'current_published_utc': publication['finished_utc'],
            'all_verified': True,
        }
        dump(ROOT / 'outputs/reports/github_history_v0.15.0.json', result)
        print(result)
    else:
        raise ValueError(mode)


if __name__ == '__main__':
    main(sys.argv[1])
