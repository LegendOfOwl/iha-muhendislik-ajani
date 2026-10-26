"""Record and compare all prior remote release assets and tag object identities."""
from publish_incremental import api,run,REPO,RUN,VERSION,BASE_HEAD,ROOT
from incremental_export import read,dump,now,digest
import sys

def snapshot():
    releases=api('repos/'+REPO+'/releases?per_page=100')
    data={r['tag_name']:{'id':r['id'],'assets':sorted([{'id':a['id'],'name':a['name'],'bytes':a['size'],'digest':a.get('digest')} for a in r['assets']],key=lambda a:a['name'])} for r in releases if r['tag_name']!=VERSION}
    tags={s.split()[1]:s.split()[0] for s in run(['git','ls-remote','origin','refs/tags/*']).splitlines() if not s.split()[1].endswith('/'+VERSION) and not s.split()[1].endswith('/'+VERSION+'^{}')}
    return {'releases':data,'tags':tags}

def main(mode):
    p=RUN/'prior_remote_history.json'
    if mode=='before':
        assert not p.exists();assert run(['git','rev-parse','HEAD'])==BASE_HEAD
        assert not run(['git','status','--porcelain'])
        assert run(['git','ls-remote','origin','refs/heads/main']).split()[0]==BASE_HEAD
        s=snapshot();assert len(s['releases'])==12;dump(p,s)
        print({'prior_releases':len(s['releases']),'prior_assets':sum(len(r['assets']) for r in s['releases'].values()),'prior_tag_refs':len(s['tags'])})
    elif mode=='after':
        old=read(p);assert snapshot()==old
        publication=read(RUN/'publication_state.json');assert publication['status']=='published_verified'
        oldstate=ROOT/'work/publish/github_publication_state.json';prior=read(oldstate)
        backup=ROOT/'work/publish/github_publication_state_v0.12.0.json'
        if not backup.exists():dump(backup,prior)
        prior.update(current_version=VERSION,updated_utc=now(),status='published_verified',remote_head_matches=True,remote_tags=13,remote_releases=13,
          remote_assets=sum(len(r['assets']) for r in old['releases'].values())+len(publication['uploaded']),
          latest_incremental_publication_state=str((RUN/'publication_state.json').relative_to(ROOT)),
          uploaded_assets=[dict(tag=VERSION,name=a['name'],size=a['bytes'],sha256=a['sha256'],server_digest_matches=True,url=a['url']) for a in publication['uploaded']])
        dump(oldstate,prior)
        out={'checked_utc':now(),'prior_releases_unchanged':12,'prior_assets_unchanged':sum(len(r['assets']) for r in old['releases'].values()),'prior_tag_refs_unchanged':len(old['tags']),'remote_snapshot_sha256':digest(p),'current_head':publication['head'],'all_verified':True}
        dump(ROOT/'outputs/reports/github_history_v0.13.0.json',out);print(out)
    else:raise ValueError(mode)

if __name__=='__main__':main(sys.argv[1])
