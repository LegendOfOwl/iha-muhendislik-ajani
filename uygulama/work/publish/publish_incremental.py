from incremental_export import ROOT,DEST,RUN,VERSION,read,dump,digest,now,BASE_HEAD,URL
from pathlib import Path
import os,subprocess,json,zipfile
REPO='LegendOfOwl/iha-muhendislik-ajani'
ENV=dict(os.environ,GH_CONFIG_DIR=str(ROOT/'tools/github-cli/auth'),GH_PROMPT_DISABLED='1',GIT_TERMINAL_PROMPT='0')
n=int(ENV.get('GIT_CONFIG_COUNT','0'));ENV.update({f'GIT_CONFIG_KEY_{n}':'safe.directory',f'GIT_CONFIG_VALUE_{n}':str(DEST),'GIT_CONFIG_COUNT':str(n+1)})
GH=read(ROOT/'work/publish/github_cli_install.json')['executable']
def run(args,timeout=1800):
    r=subprocess.run([str(x) for x in args],cwd=DEST,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    return r.stdout.strip()
def api(path):return json.loads(run([GH,'api',path]))

def commit():
    assert read(RUN/'verification.json')['passed']
    assert run(['git','rev-parse','HEAD'])==BASE_HEAD
    assert not run(['git','tag','--list',VERSION])
    run(['git','add','--all'])
    staged=run(['git','diff','--cached','--stat']);print(staged[-2500:],flush=True)
    run(['git','commit','-m',VERSION+': kaynak CFD teşhisi, güvenilirlik ve okunabilir sonuç raporları'])
    head=run(['git','rev-parse','HEAD']);assert run(['git','rev-parse','HEAD^'])==BASE_HEAD
    from verify_incremental import verify_blobs
    count=verify_blobs(read(DEST/'analizler/dosya_katalogu.json'),'HEAD')
    assert not run(['git','status','--porcelain'])
    run(['git','tag','-a',VERSION,'-m',VERSION+' —25Ekim kaynak CFD ve güvenilirlik; fizik kabulü açık'])
    dump(RUN/'commit.json',{'created_utc':now(),'head':head,'base':BASE_HEAD,'git_source_blobs_verified':count,'tag':VERSION,'tag_object':run(['git','rev-parse',VERSION])})
    print({'commit':head,'git_source_blobs_verified':count},flush=True)

def package():
    receipt=read(RUN/'commit.json');assert run(['git','rev-parse','HEAD'])==receipt['head'];bundle=RUN/('uygulama-ve-raporlar-'+VERSION+'.zip');assert not bundle.exists()
    run(['git','archive','--format=zip','--output',bundle,'HEAD'])
    tracked=set(run(['git','ls-files','-z']).split('\0'));tracked.discard('')
    with zipfile.ZipFile(bundle) as z:assert z.testzip() is None and {n for n in z.namelist() if not n.endswith('/')}==tracked
    assets=read(RUN/'build.json')['archives']+[{'name':bundle.name,'tag':VERSION,'local_path':str(bundle),'bytes':bundle.stat().st_size,'sha256':digest(bundle)}]
    sums=RUN/'SHA256SUMS.txt';sums.write_text(''.join(a['sha256']+'  '+a['name']+'\n' for a in assets),encoding='ascii')
    assets.append({'name':sums.name,'tag':VERSION,'local_path':str(sums),'bytes':sums.stat().st_size,'sha256':digest(sums)})
    dump(RUN/'assets.json',assets);print({'assets':len(assets),'total_MiB':round(sum(a['bytes'] for a in assets)/2**20,1)},flush=True)

def publish():
    receipt=read(RUN/'commit.json');head=receipt['head'];assets=read(RUN/'assets.json')
    assert run(['git','rev-parse','HEAD'])==head and not run(['git','status','--porcelain'])
    repo=api('repos/'+REPO);assert repo['private'] is False and repo['id']==1432271592
    remote=run(['git','ls-remote','origin','refs/heads/main']).split()[0]
    assert remote in [BASE_HEAD,head],'Remote changed; preserve collaborator changes'
    state={'version':VERSION,'head':head,'started_utc':now(),'status':'pushing','uploaded':[]};statepath=RUN/'publication_state.json'
    if statepath.exists():state=read(statepath)
    dump(statepath,state)
    print(run(['git','push','origin','main','refs/tags/'+VERSION]),flush=True)
    releases=api('repos/'+REPO+'/releases?per_page=100');release=next((r for r in releases if r['tag_name']==VERSION),None)
    if release is None:
        run([GH,'release','create',VERSION,'--repo',REPO,'--verify-tag','--title',VERSION+' —Kaynak CFD ve güvenilirlik','--notes-file',RUN/'release-notes.md','--latest'])
    state['status']='uploading';dump(statepath,state)
    for asset in assets:
        assert digest(Path(asset['local_path']))==asset['sha256']
        release=api('repos/'+REPO+'/releases/tags/'+VERSION);known=next((a for a in release['assets'] if a['name']==asset['name']),None)
        if known is None:
            print({'upload':asset['name'],'MiB':round(asset['bytes']/2**20,1)},flush=True)
            run([GH,'release','upload',VERSION,asset['local_path'],'--repo',REPO])
        release=api('repos/'+REPO+'/releases/tags/'+VERSION);a=next(a for a in release['assets'] if a['name']==asset['name'])
        assert a['size']==asset['bytes'] and a.get('digest')=='sha256:'+asset['sha256'],asset['name']
        record={'name':a['name'],'bytes':a['size'],'sha256':asset['sha256'],'server_digest_matches':True,'url':a['browser_download_url']}
        state['uploaded']=[r for r in state['uploaded'] if r['name']!=a['name']]+[record];dump(statepath,state);print({'verified':a['name']},flush=True)
    assert run(['git','ls-remote','origin','refs/heads/main']).split()[0]==head
    assert run(['git','ls-remote','origin','refs/tags/'+VERSION+'^{}']).split()[0]==head
    releases=api('repos/'+REPO+'/releases?per_page=100');assert {f'v0.{i}.0' for i in range(1,12)}.issubset({r['tag_name'] for r in releases})
    state.update(status='published_verified',finished_utc=now(),release_url=URL+'/releases/tag/'+VERSION,remote_head_matches=True,old_release_count_retained=10)
    dump(statepath,state);dump(ROOT/'outputs/reports/github_publication_v0.11.0.json',state)
    print({'published':state['release_url'],'head':head,'verified_assets':len(state['uploaded'])},flush=True)

if __name__=='__main__':
    import sys
    {'commit':commit,'package':package,'publish':publish}[sys.argv[1]]()
