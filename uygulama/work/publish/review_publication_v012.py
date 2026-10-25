"""Repair this turn's unpublished draft only; released history is never rewritten."""
from incremental_export import ROOT,DEST,RUN,PLAN,VERSION,BASE_HEAD,read,dump,digest,now
from publish_incremental import run,api,REPO
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import shutil

def main():
    receipt=read(RUN/'commit.json');old=receipt['head']
    assert VERSION=='v0.12.0' and old=='b560a90ace497293aad1e4d489c91c36b596e8e7'
    assert run(['git','rev-parse','HEAD'])==old and not run(['git','status','--porcelain'])
    assert run(['git','ls-remote','origin','refs/heads/main']).split()[0]==BASE_HEAD
    assert not run(['git','ls-remote','origin','refs/tags/'+VERSION])
    assert all(r['tag_name']!=VERSION for r in api('repos/'+REPO+'/releases?per_page=100'))
    catalog=read(DEST/'analizler/dosya_katalogu.json');plan=read(PLAN)
    source='work/flatplate_20261025/convergence_sources/arxiv1805.03756v1.html'
    row=next(r for r in catalog['files'] if r['source_path']==source)
    assert row['storage']=='git' and digest(DEST/row['repository_path'])==row['sha256']
    row.update(storage='external_reference',source_url='https://arxiv.org/html/1805.03756v1')
    (DEST/row['repository_path']).unlink()  # One explicitly catalogued generated copy; source archive remains local.
    replacements={source:row}
    for name in ['incremental_export.py','verify_incremental.py','review_publication_v012.py']:
        src=ROOT/'work/publish'/name;rel=src.relative_to(ROOT).as_posix();out=DEST/'uygulama'/rel
        out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,out)
        prior=next((r for r in catalog['files'] if r['source_path']==rel),None)
        item=prior.copy() if prior else {'source_path':rel,'repository_path':'uygulama/'+rel,'storage':'git','version':VERSION}
        item.update(bytes=src.stat().st_size,sha256=digest(src),source_mtime_utc=datetime.fromtimestamp(src.stat().st_mtime,timezone.utc).isoformat())
        replacements[rel]=item
    catalog['files']=[replacements.pop(r['source_path'],r) for r in catalog['files']]+list(replacements.values())
    # Rebuild changed-record views from the final catalogue, retaining every historic row.
    changed={r['source_path']:r for r in catalog['files'] if r['version']==VERSION}
    plan['records']=catalog['files'];plan['changed']=list(changed.values())
    plan['summary'].update(changed=len(changed),storage=dict(Counter(r['storage'] for r in changed.values())),
       new_git_bytes=sum(r['bytes'] for r in changed.values() if r['storage']=='git'))
    catalog['summary'].update(files=len(catalog['files']),storage_counts=dict(Counter(r['storage'] for r in catalog['files'])),
       new_release_summary=plan['summary'],external_reference_policy='Full third-party papers, including HTML full text, are retained as source URL and SHA256, not republished.')
    dump(PLAN,plan);dump(DEST/'analizler/dosya_katalogu.json',catalog)
    manifest=read(DEST/'surumler'/VERSION/'manifest.json');manifest['changed_files']=list(changed.values());dump(DEST/'surumler'/VERSION/'manifest.json',manifest)
    p=DEST/'README.md';text=p.read_text(encoding='utf-8').replace('tam üçüncü taraf makale/rapor PDF’lerini','tam üçüncü taraf makale/rapor metinlerini (PDF/HTML)');p.write_text(text,encoding='utf-8')
    # Preserve all local receipts and the private draft bundle before replacing a draft ref.
    for filename in ['commit.json','assets.json','uygulama-ve-raporlar-'+VERSION+'.zip']:
        src=RUN/filename;dst=RUN/('unpublished_draft_'+filename);assert not dst.exists();src.rename(dst)
    dump(RUN/'unpublished_preflight_revision.json',{'created_utc':now(),'unpublished_head':old,'base_head':BASE_HEAD,
       'remote_head_and_absent_tag_verified':True,'reason':'Full third-party article HTML becomes external URL/SHA256. Only this turn unpublished draft refs rebuilt; all11 released tags/assets remain unchanged.'})
    run(['git','tag','-d',VERSION])
    run(['git','reset','--soft',BASE_HEAD])
    print({'unpublished_draft_preserved':old,'full_article':'external_reference','source_records':len(catalog['files'])})

if __name__=='__main__':main()
