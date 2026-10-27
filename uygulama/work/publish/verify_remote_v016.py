"""Verify raw connected-GitHub observations and preserve all prior releases."""
from pathlib import Path
import sys
from publish_incremental import ROOT,RUN,VERSION,BASE_HEAD,DEST,URL,read,dump,digest,now,run

def release_map(items):
    return {r['tag_name']:{'id':r['id'],'assets':sorted([
        {'id':a['id'],'name':a['name'],'bytes':a['size'],'digest':a.get('digest')}
        for a in r['assets']],key=lambda a:a['name'])} for r in items}

def before():
    assert VERSION=='v0.16.0' and BASE_HEAD=='c4cbc871cb7c8dbfddd78782dcc71d67d0d8f821'
    current=read(RUN/'prior_cloud_snapshot.json');previous=read(ROOT/'work/publish/v0.15.0/cloud_remote_snapshot.json')
    assert current['main']['object']['sha']==BASE_HEAD and len(current['refs'])==15
    a={r['ref']:r['object']['sha'] for r in current['refs']}
    assert a=={r['ref']:r['object']['sha'] for r in previous['refs']}
    assert release_map(current['releases'])==release_map(previous['releases'])
    assert len(current['releases'])==15 and sum(len(r['assets']) for r in current['releases'])==36
    tags={}
    for ref in current['refs']:
        obj=ref['object'];assert obj['type']=='tag'
        old=previous['tag_objects'][obj['sha']];assert old['sha']==obj['sha'] and old['object']['type']=='commit'
        tags[ref['ref']]=obj['sha'];tags[ref['ref']+'^{}']=old['object']['sha']
    value={'releases':release_map(current['releases']),'tags':tags}
    target=RUN/'prior_remote_history.json';assert not target.exists();dump(target,value)
    print({'prior_releases':15,'prior_assets':36,'prior_tag_refs':30},flush=True)

def after():
    cloudpath=RUN/'cloud_remote_snapshot.json';cloud=read(cloudpath);prior=read(RUN/'prior_remote_history.json')
    commit=read(RUN/'commit.json');head=commit['head'];tagsha=commit['tag_object']
    assert cloud['main']['object']['sha']==head and len(cloud['refs'])==16
    newrefs={r['ref']:r['object']['sha'] for r in cloud['refs']}
    assert newrefs.pop('refs/tags/'+VERSION)==tagsha
    assert newrefs=={k:v for k,v in prior['tags'].items() if not k.endswith('^{}')}
    tag=cloud['tag_objects'][tagsha];assert tag['sha']==tagsha and tag['object']=={'sha':head,'type':'commit','url':tag['object']['url']}
    oldreleases=[r for r in cloud['releases'] if r['tag_name']!=VERSION]
    assert release_map(oldreleases)==prior['releases'] and len(oldreleases)==15
    release=next(r for r in cloud['releases'] if r['tag_name']==VERSION)
    expected=read(RUN/'assets.json');assert len(release['assets'])==len(expected)
    verified=[]
    for asset in expected:
        actual=next(a for a in release['assets'] if a['name']==asset['name'])
        assert digest(Path(asset['local_path']))==asset['sha256']
        assert actual['size']==asset['bytes'] and actual['digest']=='sha256:'+asset['sha256']
        verified.append({'name':asset['name'],'bytes':asset['bytes'],'sha256':asset['sha256'],
                         'server_digest_matches':True,'url':actual['browser_download_url']})
    assert release['zipball_url'].endswith('/zipball/'+VERSION)
    assert run(['git','rev-parse','HEAD'])==head and not run(['git','status','--porcelain'])
    layout=read(RUN/'package_layout.json');statepath=RUN/'publication_state.json'
    state=read(statepath) if statepath.exists() else {'version':VERSION,'head':head}
    state.update(status='published_verified',uploaded=verified,finished_utc=now(),release_url=release['html_url'],
       remote_head_matches=True,old_release_count_retained=15,full_source_archive_url=layout['full_tracked_source_url'],
       source_commit=head,source_delivery='GitHub automatically generated Source code ZIP',source_zip_endpoint_verified=True,
       source_archive_byte_hash_verified=False,official_remote_snapshot_sha256=digest(cloudpath),
       final_verification_transport='Connected GitHub direct REST JSON',operating_system_DNS_or_TLS_policy_changed=False)
    dump(statepath,state);dump(ROOT/('outputs/reports/github_publication_'+VERSION+'.json'),state)
    globalpath=ROOT/'work/publish/github_publication_state.json';old=read(globalpath)
    backup=ROOT/'work/publish/github_publication_state_v0.15.0.json'
    if not backup.exists():assert old['current_version']=='v0.15.0';dump(backup,old)
    assert old['current_version'] in ('v0.15.0',VERSION)
    old.update(current_version=VERSION,head=head,published_utc=state['finished_utc'],updated_utc=now(),
       versions=sorted(set(old['versions'])|{VERSION},key=lambda x:tuple(map(int,x.lstrip('v').split('.')))),
       status='published_verified',remote_head_matches=True,remote_tags=16,remote_releases=16,remote_assets=36+len(expected),
       latest_incremental_publication_state=str(statepath.relative_to(ROOT)),
       uploaded_assets=[dict(tag=VERSION,name=a['name'],size=a['bytes'],sha256=a['sha256'],server_digest_matches=True,url=a['url']) for a in verified])
    dump(globalpath,old)
    audit={'checked_utc':now(),'prior_releases_unchanged':15,'prior_assets_unchanged':36,'prior_tag_refs_unchanged':30,
       'remote_snapshot_sha256':digest(cloudpath),'prerelease_snapshot_sha256':digest(RUN/'prior_remote_history.json'),
       'current_head':head,'all_verified':True,'verification_transport':state['final_verification_transport']}
    dump(ROOT/('outputs/reports/github_history_'+VERSION+'.json'),audit)
    tracking=run(['git','rev-parse','refs/remotes/origin/main']);assert tracking in (BASE_HEAD,head)
    if tracking!=head:run(['git','update-ref','refs/remotes/origin/main',head,tracking])
    checks=read(RUN/'verification.json')
    md=f'''# GitHub {VERSION} yayın makbuzu

[Release]({release['html_url']}) · [Okunabilir rapor]({URL}/blob/{VERSION}/raporlar/{VERSION}/README.md)

Main ve yeni annotated tag `{head}` commitini gösteriyor. {len(expected)} yeni varlığın boyutu ve sunucu SHA256 değeri yerel dosyayla aynı. Önceki15 Release,36 varlık ve30 tag referansı değişmedi.

{commit['git_source_blobs_verified']} kaynak blobu;{len(checks['restore_tests'])} geri yükleme kontrolü;{checks['actual_data_restore']['restored_original_paths']} gerçek ham hedef yolu;{checks['new_document_links_checked']} belge bağlantısı doğrulandı. {checks['secret_scan_files']} dosya taramasında kayıtlı gizli bilgi bulgusu yok. Tam izlenen kaynak otomatik tag ZIP'inde; bu ZIP'in bayt hash'i iddia edilmiyor. Kurulu derleyici/solver ve indirilen üçüncü taraf arşivler dağıtılmaz.

Bu sürümde yeni CFD koşusu yok;70 yeni yazılım kontrolü, kaynak/derleme hazırlığı ve korunmuş başarısızlıklar var. Pristine32 yeniden üretimi ve cap256 etkisi henüz ölçülmedi. Genel fizik/M6/İHA/LLM yeterliliği false kalır. Yayın sonrası bu makbuz sonraki artımlı kataloğa taşınır.
'''
    (ROOT/('outputs/reports/github_yayini_'+VERSION+'.md')).write_text(md,encoding='utf-8')
    path=ROOT/'PROJECT_STATE.md';text=path.read_text(encoding='utf-8');marker='## 27 Ekim: v0.16.0 yayın doğrulandı'
    if marker not in text:
        path.write_text(text+f'\n\n{marker}\n\n- Public main/tag {head};16 sürüm/{36+len(expected)} varlık. Yeni varlıkların sunucu SHA256/boyutu ve önceki15 sürüm/36 varlık/30 tag referansı doğrulandı. {commit["git_source_blobs_verified"]} kaynak blobu, {len(checks["restore_tests"])} restore kontrolü ve {checks["actual_data_restore"]["restored_original_paths"]} gerçek ham yol denetlendi. Genel fizik/CFD/LLM kabulü değişmedi; makbuz github_yayini_v0.16.0.md.\n',encoding='utf-8')
    print({'published':release['html_url'],'head':head,'assets_verified':len(verified),'prior_releases_unchanged':15},flush=True)

if __name__=='__main__':{'before':before,'after':after}[sys.argv[1]]()
