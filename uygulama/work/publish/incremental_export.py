"""Append a genuine versioned release without rewriting the historical import."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import os,json,hashlib,zipfile,shutil,subprocess
from build_export import ROOT,DEST,STATE,ASSETS,URL,digest,dump,excluded,is_bulk,secret_findings

VERSION='v0.12.0'
RUN=STATE/VERSION
PLAN=RUN/'plan.json'
BASE_HEAD='f06d1524c390646e0659d2e72327f30d8bd59dff'
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def reference_urls():
    result={r['source_path']:r['source_url'] for r in read(DEST/'analizler/dosya_katalogu.json')['files'] if r['storage']=='external_reference'}
    for manifest in [ROOT/'work/cfd_literature_20261025/sources/manifest.json',ROOT/'work/reliability/sources/manifest.json',ROOT/'work/flatplate_20261025/convergence_sources/manifest.json']:
        for item in read(manifest):
            if item.get('path'):p=ROOT/item['path']
            elif item.get('file'):p=manifest.parent/item['file']
            else:continue
            if (p.suffix.lower()=='.pdf' or p.name=='arxiv1805.03756v1.html') and item.get('url'):result[p.relative_to(ROOT).as_posix()]=item['url']
    return result

def plan():
    assert subprocess.check_output(['git','-C',str(DEST),'rev-parse','HEAD'],text=True).strip()==BASE_HEAD
    assert not subprocess.check_output(['git','-C',str(DEST),'status','--porcelain'],text=True).strip(),'Preserve unexpected user changes'
    base=read(DEST/'analizler/dosya_katalogu.json');old={r['source_path']:r for r in base['files']};urls=reference_urls()
    records=[];changed=[];omitted=[];findings=[];seen=set()
    for folder,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','.venv-cad','tools','.codex','__pycache__','compiler_packages'}]
        for name in files:
            path=Path(folder)/name;relative=path.relative_to(ROOT);rel=relative.as_posix();reason=excluded(relative)
            if rel.startswith('work/publish/') and relative.suffix not in {'.py'}:reason='local_publication_state_assets_or_auth'
            if rel.startswith('work/publish/restore-fixtures/') or (len(relative.parts)>2 and relative.parts[:2]==('work','publish') and relative.parts[2].startswith('v0.')):reason='publication_fixture_or_self_output'
            if 'compiler_packages' in relative.parts or rel.endswith('.pkg.tar.zst'):reason='external_compiler_binary_package'
            if path.is_symlink():reason='symbolic_link'
            if reason:omitted.append({'path':rel,'reason':reason});continue
            labels=secret_findings(path)
            if labels:findings.append({'path':rel,'types':labels});continue
            seen.add(rel);h=digest(path);prior=old.get(rel)
            if prior and h==prior['sha256']:
                records.append(prior.copy());continue
            row={'source_path':rel,'repository_path':'uygulama/'+rel,'bytes':path.stat().st_size,'sha256':h,'version':VERSION,
                 'source_mtime_utc':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()}
            if prior:row.update(previous_sha256=prior['sha256'],previous_version=prior['version'])
            if relative.suffix.lower()=='.pdf' or relative.name=='arxiv1805.03756v1.html':
                if rel not in urls:
                    omitted.append({'path':rel,'reason':'full_third_party_PDF_no_verified_restore_URL'});continue
                row.update(storage='external_reference',source_url=urls[rel])
            else:row['storage']='release_asset' if is_bulk(relative,row['bytes']) else 'git'
            records.append(row);changed.append(row)
    retained=[]
    for rel,row in old.items():
        if rel not in seen:
            historical=row.copy();historical['retained_historical_source_missing']=True;records.append(historical);retained.append(rel)
    assert not findings,findings
    unique={r['sha256']:r for r in changed if r['storage']=='release_asset'}
    result={'created_utc':now(),'version':VERSION,'base_head':BASE_HEAD,'history_kind':'incremental_after_retrospective_import',
      'records':records,'changed':changed,'omitted':omitted,'retained_historical':retained,'secret_scan_findings':findings,
      'summary':{'changed':len(changed),'storage':dict(Counter(r['storage'] for r in changed)),
        'new_git_bytes':sum(r['bytes'] for r in changed if r['storage']=='git'),'raw_bytes':sum(r['bytes'] for r in changed if r['storage']=='release_asset'),
        'unique_raw_bytes':sum(r['bytes'] for r in unique.values()),'unique_raw_files':len(unique)},
      'old_archives':base['archives']}
    dump(PLAN,result);print(json.dumps(result['summary'],ensure_ascii=False),flush=True)

def build():
    p=read(PLAN);assert p['base_head']==BASE_HEAD;RUN.mkdir(exist_ok=True,parents=True)
    records=p['records'];new=p['changed'];archives=[]
    # New release only: identical bytes get one member; catalogue keeps every path.
    bulk=[r for r in new if r['storage']=='release_asset'];bysha={}
    for r in bulk:bysha.setdefault(r['sha256'],[]).append(r)
    packs=[[]];size=0
    for h,aliases in bysha.items():
        r=aliases[0]
        if packs[-1] and size+r['bytes']>600*2**20:packs.append([]);size=0
        packs[-1].append((r,aliases));size+=r['bytes']
    for index,pack in enumerate(packs,1):
        if not pack:continue
        name=f'analiz-arsivi-{VERSION}-part{index:02d}.zip';target=RUN/name;assert not target.exists()
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
            for canonical,aliases in pack:
                src=ROOT/canonical['source_path'];assert digest(src)==canonical['sha256'];member=canonical['repository_path'];z.write(src,member)
                for row in aliases:row.update(asset=name,release_tag=VERSION,archive_member=member)
        asset={'name':name,'tag':VERSION,'bytes':target.stat().st_size,'sha256':digest(target),'files':sum(len(a) for _,a in pack),
           'unique_members':len(pack),'local_path':str(target),'download_url':URL+'/releases/download/'+VERSION+'/'+name}
        archives.append(asset);print({'archive':name,'MiB':round(asset['bytes']/2**20,1),'paths':asset['files'],'unique_members':len(pack)},flush=True)
    updated={r['source_path']:r for r in new}
    records=[updated.get(r['source_path'],r) for r in records]
    copied=0
    for r in new:
        if r['storage']=='git':
            src=ROOT/r['source_path'];assert digest(src)==r['sha256'];out=DEST/r['repository_path'];out.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,out);assert digest(out)==r['sha256'];copied+=1
    summary={'created_utc':now(),'version':VERSION,'repository_url':URL,'history_kind':'v0.1-v0.10 retrospective; v0.11 genuine incremental release',
       'files':len(records),'storage_counts':dict(Counter(r['storage'] for r in records)),
       'expert_or_physical_qualification_claimed':False,'new_release_summary':p['summary'],
       'external_reference_policy':'Full third-party papers retained as source URL and SHA256, not republished.'}
    catalog={'summary':summary,'files':records,'archives':p['old_archives']+[{k:v for k,v in a.items() if k!='local_path'} for a in archives]}
    dump(DEST/'analizler/dosya_katalogu.json',catalog)
    folder=DEST/'surumler'/VERSION;folder.mkdir(parents=True,exist_ok=True)
    dump(folder/'manifest.json',{'version':VERSION,'created_utc':now(),'base_commit':BASE_HEAD,'history_kind':'genuine_incremental',
       'changed_files':new,'new_archives':[{k:v for k,v in a.items() if k!='local_path'} for a in archives]})
    dump(RUN/'build.json',{'created_utc':now(),'archives':archives,'copied_git_files':copied,'catalog_sha256':digest(DEST/'analizler/dosya_katalogu.json')})
    dump(DEST/('kurulum/yayin_kapsami_'+VERSION+'.json'),{'version':VERSION,'base_commit':BASE_HEAD,'omitted_files':p['omitted'],'secret_scan_findings':[],
        'compiler_distribution':'Portable GNU/MSYS2 installed binaries and compiler packages excluded; source/build/hash records retained.',
        'clean_machine_solver_reproduction_tested':False,'expert_or_physical_qualification_claimed':False})
    print({'copied':copied,'archives':len(archives),'catalog_records':len(records)},flush=True)

if __name__=='__main__':
    import sys
    {'plan':plan,'build':build}[sys.argv[1]]()
