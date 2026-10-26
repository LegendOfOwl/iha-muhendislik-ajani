from incremental_export import ROOT,DEST,RUN,VERSION,read,dump,digest,now,BASE_HEAD,URL
from pathlib import Path
import os,subprocess,json,zipfile
REPO='LegendOfOwl/iha-muhendislik-ajani'
TITLE='CFD iç tavan kontrolü ve doğrulanmış konumsal artık ölçümü'
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
    # Local application ignores exclude run logs during development. The public
    # catalogue explicitly selects reviewed logs; stage only that exact list.
    catalog=read(DEST/'analizler/dosya_katalogu.json')
    pathfile=RUN/'catalogued-git-paths.bin'
    pathfile.write_bytes(b'\0'.join(r['repository_path'].encode('utf-8') for r in catalog['files'] if r['storage']=='git')+b'\0')
    run(['git','add','--force','--pathspec-from-file='+str(pathfile),'--pathspec-file-nul'])
    from verify_incremental import verify_blobs
    count=verify_blobs(catalog,'',env=ENV)
    staged=run(['git','diff','--cached','--stat']);print(staged[-2500:],flush=True)
    run(['git','commit','-m',VERSION+': '+TITLE])
    head=run(['git','rev-parse','HEAD']);assert run(['git','rev-parse','HEAD^'])==BASE_HEAD
    assert not run(['git','status','--porcelain'])
    run(['git','tag','-a',VERSION,'-m',VERSION+' — '+TITLE+'; fizik kabulü açık'])
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

def package_sources():
    # GitHub already generates full tracked-source ZIP/tarball links for tags.
    # Avoid uploading the same historical source snapshot on every new release.
    receipt=read(RUN/'commit.json');assert run(['git','rev-parse','HEAD'])==receipt['head']
    assert not run(['git','status','--porcelain'])
    note=RUN/'KAYNAK_INDIRME.md';assert not note.exists()
    source_url=URL+'/archive/refs/tags/'+VERSION+'.zip'
    body='# '+VERSION+' kaynak ve analiz indirme\n\n'
    body+='Tam takipli uygulama/kaynak/rapor ağacı için Release sayfasındaki **Source code (zip)** veya [bu arşivi]('+source_url+') kullanın. Aynı Git etiketi: `'+receipt['head']+'`. Önceki sürümleri içeren kopya bir uygulama ZIP\'i bu sürümde tekrar yüklenmedi.\n\n'
    body+='Büyük CFD alanları Release analiz arşivlerindedir; kaynak arşivindeki `kurulum/analizleri_geri_yukle.py` ve `analizler/dosya_katalogu.json` ile özgün yollara geri yüklenir. Python/solver ortamları ve model ağırlıkları ayrıca kurulur; kurulum belgelerini okuyun.\n\n'
    body+='GitHub tarafından üretilen ZIP\'in byte düzeyi SHA\'sını iddia etmiyoruz. Etiket/commit kimliği ve katalogdaki dosya SHA256 değerleri içerik kanıtıdır. Eklenen analiz ZIP\'inin SHA256 listesi ayrıca verilir.\n\n'
    body+='[GitHub resmî Release açıklaması](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases). Eski Release varlıkları değiştirilmedi.\n'
    note.write_text(body,encoding='utf-8')
    assets=read(RUN/'build.json')['archives']+[{'name':note.name,'tag':VERSION,'local_path':str(note),'bytes':note.stat().st_size,'sha256':digest(note)}]
    sums=RUN/'SHA256SUMS.txt';assert not sums.exists()
    sums.write_text(''.join(a['sha256']+'  '+a['name']+'\n' for a in assets),encoding='ascii')
    assets.append({'name':sums.name,'tag':VERSION,'local_path':str(sums),'bytes':sums.stat().st_size,'sha256':digest(sums)})
    dump(RUN/'assets.json',assets)
    dump(RUN/'package_layout.json',{'created_utc':now(),'full_tracked_source_url':source_url,'source_commit':receipt['head'],
       'GitHub_generated_source_zip_byte_hash_claimed':False,'new_raw_assets_and_SHA256_verified_separately':True})
    print({'assets':len(assets),'total_MiB':round(sum(a['bytes'] for a in assets)/2**20,1),'full_sources':'GitHub generated Source code(zip)'},flush=True)

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
        run([GH,'release','create',VERSION,'--repo',REPO,'--verify-tag','--title',VERSION+' — '+TITLE,'--notes-file',RUN/'release-notes.md','--latest'])
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
    releases=api('repos/'+REPO+'/releases?per_page=100');assert {f'v0.{i}.0' for i in range(1,int(VERSION.split('.')[1]))}.issubset({r['tag_name'] for r in releases})
    state.update(status='published_verified',finished_utc=now(),release_url=URL+'/releases/tag/'+VERSION,remote_head_matches=True,old_release_count_retained=len([r for r in releases if r['tag_name']!=VERSION]))
    if (RUN/'package_layout.json').exists():
        layout=read(RUN/'package_layout.json');release=api('repos/'+REPO+'/releases/tags/'+VERSION)
        assert release.get('zipball_url','').endswith('/zipball/'+VERSION)
        state.update(full_source_archive_url=layout['full_tracked_source_url'],source_commit=head,
          source_delivery='GitHub automatically generated Source code ZIP',source_zip_endpoint_verified=True,
          source_archive_byte_hash_verified=False)
    dump(statepath,state);dump(ROOT/('outputs/reports/github_publication_'+VERSION+'.json'),state)
    print({'published':state['release_url'],'head':head,'verified_assets':len(state['uploaded'])},flush=True)

if __name__=='__main__':
    import sys
    {'commit':commit,'package':package,'package-sources':package_sources,'publish':publish}[sys.argv[1]]()
