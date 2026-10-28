"""Verify saved GitHub observations; no remote mutation or inferred CFD result.

Only explicit before()/after() execution writes publication receipts. Pure map
helpers can be tested without a network, a Git command or a checkout mutation.
The v0.17 snapshot contains only its latest annotated-tag object; earlier peeled
commits therefore come from its previously verified immutable history map.
"""
from pathlib import Path
import re
import sys
from publish_incremental import ROOT, RUN, VERSION, BASE_HEAD, URL, read, dump, digest, now, run
from release_documents_v018 import validate_research_report


EXPECTED_VERSION = 'v0.18.0'
PREVIOUS = 'v0.17.0'
EXPECTED_BASE = '87c932868b14407f2892e957f3e68d02a0a8b270'
PRIOR_RELEASES = 17
PRIOR_ASSETS = 42
REPORT = 'acik_sorunlar_ve_derin_arastirma_20261028'


def _sha(value):
    assert isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value), 'Invalid Git object SHA'
    return value


def release_map(items):
    result = {}
    release_ids = set()
    asset_ids = set()
    for release in items:
        tag = release['tag_name']
        assert tag not in result and release['id'] not in release_ids, 'Duplicate release tag/id'
        release_ids.add(release['id'])
        assets, names = [], set()
        for asset in release['assets']:
            assert asset['name'] not in names and asset['id'] not in asset_ids, 'Duplicate asset name/id'
            assert type(asset['size']) is int and asset['size'] >= 0, 'Invalid asset size'
            names.add(asset['name'])
            asset_ids.add(asset['id'])
            assets.append({'id': asset['id'], 'name': asset['name'], 'bytes': asset['size'],
                           'digest': asset.get('digest')})
        result[tag] = {'id': release['id'], 'assets': sorted(assets, key=lambda a: a['name'])}
    return result


def raw_refs(refs):
    result = {}
    for ref in refs:
        name, obj = ref['ref'], ref['object']
        assert name.startswith('refs/tags/') and not name.endswith('^{}') and name not in result
        assert obj['type'] == 'tag', 'Every preserved release must use an annotated tag'
        result[name] = _sha(obj['sha'])
    return result


def prior_tag_pairs(refs, previous_pairs, latest_objects, latest_tag=PREVIOUS, latest_head=EXPECTED_BASE):
    """Reconstruct 17 immutable tag/peeled pairs without fetching old objects again."""
    observed = raw_refs(refs)
    latest_ref = 'refs/tags/' + latest_tag
    assert latest_ref in observed and latest_ref not in previous_pairs
    earlier = {k: v for k, v in observed.items() if k != latest_ref}
    expected_raw = {k: _sha(v) for k, v in previous_pairs.items() if not k.endswith('^{}')}
    assert earlier == expected_raw, 'Historical raw tag reference changed'
    assert set(previous_pairs) == set(expected_raw) | {k + '^{}' for k in expected_raw}, 'Incomplete historical tag pairs'
    for name in expected_raw:
        _sha(previous_pairs[name + '^{}'])
    obj = latest_objects[observed[latest_ref]]
    assert obj['sha'] == observed[latest_ref] and obj['tag'] == latest_tag
    assert obj['object']['type'] == 'commit' and obj['object']['sha'] == _sha(latest_head)
    pairs = dict(previous_pairs)
    pairs.update({latest_ref: observed[latest_ref], latest_ref + '^{}': latest_head})
    return pairs


def _configuration():
    assert VERSION == EXPECTED_VERSION and BASE_HEAD == EXPECTED_BASE


def before():
    _configuration()
    current = read(RUN / 'prior_cloud_snapshot.json')
    previous = read(ROOT / 'work/publish/v0.17.0/cloud_remote_snapshot.json')
    old_history = read(ROOT / 'work/publish/v0.17.0/prior_remote_history.json')
    assert current['main']['object']['sha'] == previous['main']['object']['sha'] == BASE_HEAD
    assert len(current['refs']) == PRIOR_RELEASES
    assert raw_refs(current['refs']) == raw_refs(previous['refs'])
    current_releases = release_map(current['releases'])
    assert current_releases == release_map(previous['releases'])
    assert len(current_releases) == PRIOR_RELEASES
    assert sum(len(r['assets']) for r in current_releases.values()) == PRIOR_ASSETS
    assert {k: v for k, v in current_releases.items() if k != PREVIOUS} == old_history['releases']
    pairs = prior_tag_pairs(current['refs'], old_history['tags'], previous['tag_objects'])
    assert len(pairs) == 2 * PRIOR_RELEASES
    target = RUN / 'prior_remote_history.json'
    assert not target.exists(), 'Preserve previous prepublication snapshot'
    dump(target, {'releases': current_releases, 'tags': pairs})
    print({'prior_releases': PRIOR_RELEASES, 'prior_assets': PRIOR_ASSETS,
           'prior_tag_refs': len(pairs)}, flush=True)


def after():
    _configuration()
    cloudpath = RUN / 'cloud_remote_snapshot.json'
    cloud, prior = read(cloudpath), read(RUN / 'prior_remote_history.json')
    assert len(prior['releases']) == PRIOR_RELEASES
    assert sum(len(r['assets']) for r in prior['releases'].values()) == PRIOR_ASSETS
    assert len(prior['tags']) == 2 * PRIOR_RELEASES
    commit = read(RUN / 'commit.json')
    head, tagsha = _sha(commit['head']), _sha(commit['tag_object'])
    assert commit['base'] == BASE_HEAD and commit['tag'] == VERSION
    assert cloud['main']['object']['sha'] == head and len(cloud['refs']) == PRIOR_RELEASES + 1
    refs = raw_refs(cloud['refs'])
    assert refs.pop('refs/tags/' + VERSION) == tagsha
    assert refs == {k: v for k, v in prior['tags'].items() if not k.endswith('^{}')}
    tag = cloud['tag_objects'][tagsha]
    assert tag['sha'] == tagsha and tag['tag'] == VERSION
    assert tag['object']['sha'] == head and tag['object']['type'] == 'commit'
    all_releases = release_map(cloud['releases'])
    assert len(all_releases) == PRIOR_RELEASES + 1
    assert all_releases.pop(VERSION) and all_releases == prior['releases']
    release = next(r for r in cloud['releases'] if r['tag_name'] == VERSION)
    expected = read(RUN / 'assets.json')
    assert expected and len({a['name'] for a in expected}) == len(expected), 'Missing or duplicate planned assets'
    assert len(release['assets']) == len(expected)
    assert {a['name'] for a in release['assets']} == {a['name'] for a in expected}
    verified = []
    for asset in expected:
        actual = next(a for a in release['assets'] if a['name'] == asset['name'])
        local = Path(asset['local_path'])
        assert local.stat().st_size == asset['bytes'] and digest(local) == asset['sha256']
        assert actual['size'] == asset['bytes'] and actual['digest'] == 'sha256:' + asset['sha256']
        verified.append({'name': asset['name'], 'bytes': asset['bytes'], 'sha256': asset['sha256'],
                         'server_digest_matches': True, 'url': actual['browser_download_url']})
    assert release['zipball_url'].endswith('/zipball/' + VERSION)
    assert run(['git', 'rev-parse', 'HEAD']) == head and not run(['git', 'status', '--porcelain'])
    tracking = run(['git', 'rev-parse', 'refs/remotes/origin/main'])
    assert tracking in (BASE_HEAD, head)
    layout, checks = read(RUN / 'package_layout.json'), read(RUN / 'verification.json')
    assert layout['source_commit'] == head and checks['passed'] is True and checks['version'] == VERSION
    result = read(ROOT / 'outputs/reports' / (REPORT + '.json'))
    summary, _ = validate_research_report(result)
    statepath = RUN / 'publication_state.json'
    state = read(statepath) if statepath.exists() else {'version': VERSION, 'head': head}
    assert state['version'] == VERSION and state['head'] == head
    globalpath = ROOT / 'work/publish/github_publication_state.json'
    old = read(globalpath)
    assert old['current_version'] in (PREVIOUS, VERSION)
    backup = ROOT / 'work/publish/github_publication_state_v0.17.0.json'
    if not backup.exists():
        assert old['current_version'] == PREVIOUS, 'Cannot reconstruct missing previous-version state'
    else:
        prior_state = read(backup)
        assert prior_state['current_version'] == PREVIOUS and prior_state['head'] == BASE_HEAD
    # All data/identity checks above precede the first receipt or state write.
    finished = now()
    state.update(status='published_verified', uploaded=verified, finished_utc=finished,
        release_url=release['html_url'], remote_head_matches=True,
        old_release_count_retained=PRIOR_RELEASES, full_source_archive_url=layout['full_tracked_source_url'],
        source_commit=head, source_delivery='GitHub automatically generated Source code ZIP',
        source_zip_endpoint_verified=True, source_archive_byte_hash_verified=False,
        official_remote_snapshot_sha256=digest(cloudpath),
        final_verification_transport='Connected GitHub direct REST JSON',
        operating_system_DNS_or_TLS_policy_changed=False,
        new_native_CFD_runs=result['new_native_CFD_runs'], new_builds=result['new_builds'],
        research_report_sha256=digest(ROOT / 'outputs/reports' / (REPORT + '.json')),
        physical_qualification_passed=False, M6_qualification_passed=False, LLM_improvement_demonstrated=False)
    if not backup.exists():
        dump(backup, old)
    dump(statepath, state)
    dump(ROOT / ('outputs/reports/github_publication_' + VERSION + '.json'), state)
    old.update(current_version=VERSION, head=head, published_utc=finished, updated_utc=now(),
        versions=sorted(set(old['versions']) | {VERSION}, key=lambda x: tuple(map(int, x.lstrip('v').split('.')))),
        status='published_verified', remote_head_matches=True, remote_tags=PRIOR_RELEASES + 1,
        remote_releases=PRIOR_RELEASES + 1, remote_assets=PRIOR_ASSETS + len(expected),
        latest_incremental_publication_state=str(statepath.relative_to(ROOT)),
        uploaded_assets=[dict(tag=VERSION, name=a['name'], size=a['bytes'], sha256=a['sha256'],
                              server_digest_matches=True, url=a['url']) for a in verified])
    dump(globalpath, old)
    audit = {'checked_utc': now(), 'prior_releases_unchanged': PRIOR_RELEASES,
        'prior_assets_unchanged': PRIOR_ASSETS, 'prior_tag_refs_unchanged': 2 * PRIOR_RELEASES,
        'remote_snapshot_sha256': digest(cloudpath),
        'prerelease_snapshot_sha256': digest(RUN / 'prior_remote_history.json'),
        'current_head': head, 'all_verified': True, 'verification_transport': state['final_verification_transport']}
    dump(ROOT / ('outputs/reports/github_history_' + VERSION + '.json'), audit)
    if tracking != head:
        run(['git', 'update-ref', 'refs/remotes/origin/main', head, tracking])
    md = f'''# GitHub {VERSION} yayın makbuzu

[Release]({release['html_url']}) · [Okunabilir rapor]({URL}/blob/{VERSION}/raporlar/{VERSION}/README.md)

Main ve yeni annotated tag `{head}` commitini gösteriyor. {len(expected)} yeni varlığın boyutu ve sunucu SHA256 değeri yerel dosyayla aynı. Önceki {PRIOR_RELEASES} Release, {PRIOR_ASSETS} varlık ve {2 * PRIOR_RELEASES} tag referansı değişmedi.

{commit['git_source_blobs_verified']} kaynak blobu; {len(checks['restore_tests'])} geri yükleme kontrolü; {checks['actual_data_restore']['restored_original_paths']} gerçek ham hedef yolu; {checks['new_document_links_checked']} belge bağlantısı doğrulandı. {checks['secret_scan_files']} dosya taramasında kayıtlı gizli bilgi bulgusu yok. Tam izlenen kaynak otomatik tag ZIP'inde; bu ZIP'in bayt hash'i iddia edilmiyor. Kurulu derleyici/solver ve indirilen üçüncü taraf arşivler dağıtılmaz.

{summary.strip()}

Bu yayın doğrulaması fiziksel CFD/M6/İHA yeterliliği veya LLM iyileşmesi kanıtı değildir. Yayın sonrası bu makbuz sonraki artımlı kataloğa taşınır.
'''
    (ROOT / ('outputs/reports/github_yayini_' + VERSION + '.md')).write_text(md, encoding='utf-8')
    path = ROOT / 'PROJECT_STATE.md'
    text = path.read_text(encoding='utf-8')
    marker = '## 28 Ekim: ' + VERSION + ' yayın doğrulandı'
    if marker not in text:
        text += (f'\n\n{marker}\n\n- Public main/tag {head}; {PRIOR_RELEASES + 1} sürüm/'
            f'{PRIOR_ASSETS + len(expected)} varlık. Yeni varlıkların sunucu SHA256/boyutu ve önceki '
            f'{PRIOR_RELEASES} sürüm/{PRIOR_ASSETS} varlık/{2 * PRIOR_RELEASES} tag referansı doğrulandı. '
            f'{commit["git_source_blobs_verified"]} kaynak blobu, {len(checks["restore_tests"])} restore kontrolü '
            f've {checks["actual_data_restore"]["restored_original_paths"]} gerçek ham yol denetlendi. '
            f'Genel fizik/CFD/LLM kabulü değişmedi; makbuz github_yayini_{VERSION}.md.\n')
        path.write_text(text, encoding='utf-8')
    print({'published': release['html_url'], 'head': head, 'assets_verified': len(verified),
           'prior_releases_unchanged': PRIOR_RELEASES}, flush=True)


if __name__ == '__main__':
    {'before': before, 'after': after}[sys.argv[1]]()
