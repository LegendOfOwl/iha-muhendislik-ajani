from incremental_export import ROOT,DEST,RUN,VERSION,read,dump,digest,now
import importlib.util,tempfile,zipfile,shutil,hashlib,re,subprocess,os
from build_export import secret_findings

def module():
    spec=importlib.util.spec_from_file_location('restore_incremental',DEST/'kurulum/analizleri_geri_yukle.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def restore_tests():
    # The previous ten counterexamples are rerun against the modified helper.
    from verify_export import restores_test
    results=restores_test();m=module()
    for case in ['shared-content','shared-conflicting-hash','duplicate-zip-member','shared-unsafe-member']:
        with tempfile.TemporaryDirectory(prefix='restore_',dir=RUN) as tmp:
            root=__import__('pathlib').Path(tmp);m.ROOT=root;cache=root/'arsiv-indirmeleri';cache.mkdir();zpath=cache/'fixture.zip';payload=b'two original paths, one immutable member'
            member='uygulama/outputs/simulations/field.dat'
            if case=='shared-unsafe-member':member='uygulama/../outside.dat'
            with zipfile.ZipFile(zpath,'w') as z:
                z.writestr(member,payload)
                if case=='duplicate-zip-member':z.writestr(member,payload)
            files=[{'repository_path':name,'archive_member':member,'asset':'fixture.zip','storage':'release_asset','sha256':hashlib.sha256(payload).hexdigest()}
                   for name in ['uygulama/a/field.dat','uygulama/b/seed.dat']]
            if case=='shared-conflicting-hash':files[1]['sha256']='0'*64
            catalog={'files':files,'archives':[{'name':'fixture.zip','tag':VERSION,'sha256':digest(zpath),'download_url':'https://invalid.example/not-used'}]}
            try:
                m.restore(catalog)
                assert case=='shared-content','Invalid archive/catalog was accepted'
                assert all((root/r['repository_path']).read_bytes()==payload for r in files)
                m.restore(catalog,verify_only=True)
            except ValueError:
                assert case!='shared-content'
            results.append({'case':case,'passed':True})
    return results

def full_restore(catalog):
    # Actual v0.11 assets, not synthetic fields, in a new empty destination.
    target=RUN/'fresh_data_restore';assert not target.exists();target.mkdir()
    cache=target/'arsiv-indirmeleri';cache.mkdir();build=read(RUN/'build.json')
    for asset in build['archives']:shutil.copyfile(asset['local_path'],cache/asset['name'])
    m=module();m.ROOT=target;m.restore(catalog,version=VERSION);m.restore(catalog,version=VERSION,verify_only=True)
    rows=[r for r in catalog['files'] if r['storage']=='release_asset' and r.get('release_tag')==VERSION]
    assert all(digest(target/r['repository_path'])==r['sha256'] for r in rows)
    return {'scope':'Actual new release raw-data restore in empty directory on this Windows machine; not VM/clean solver installation or new CFD run',
        'restored_original_paths':len(rows),'all_sha256_passed':True}

def verify_blobs(catalog,ref):
    rows=[r for r in catalog['files'] if r['storage']=='git'];p=subprocess.Popen(['git','-C',str(DEST),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for r in rows:
        p.stdin.write((ref+':'+r['repository_path']+'\n').encode());p.stdin.flush();header=p.stdout.readline().decode().split();assert len(header)==3 and header[1]=='blob',r['repository_path']
        n=int(header[2]);h=hashlib.sha256()
        while n:
            data=p.stdout.read(min(n,2**20));assert data;n-=len(data);h.update(data)
        assert p.stdout.read(1)==b'\n';assert h.hexdigest()==r['sha256'],r['repository_path']
    p.stdin.close();assert p.wait()==0;return len(rows)

def main(mode):
    catalog=read(DEST/'analizler/dosya_katalogu.json')
    if mode=='blobs':
        print({'git_source_blobs_verified':verify_blobs(catalog,'HEAD')});return
    for r in catalog['files']:
        if r['storage']=='git':assert digest(DEST/r['repository_path'])==r['sha256'],r['repository_path']
    archivechecks=[]
    for asset in read(RUN/'build.json')['archives']:
        assert digest(__import__('pathlib').Path(asset['local_path']))==asset['sha256']
        rows=[r for r in catalog['files'] if r.get('asset')==asset['name']];members={r.get('archive_member',r['repository_path']):r for r in rows}
        with zipfile.ZipFile(asset['local_path']) as z:
            assert len(z.namelist())==len(members) and set(z.namelist())==set(members)
            for member,r in members.items():
                with z.open(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['sha256']
        archivechecks.append({'name':asset['name'],'paths':len(rows),'unique_members':len(members),'passed':True})
    tests=restore_tests();restored=full_restore(catalog)
    docs=[DEST/'README.md',DEST/'SURUMLEME.md',DEST/'surumler/v0.11.0/README.md',DEST/'raporlar/v0.11.0/README.md',DEST/'kurulum/EXE_KAYNAK_VE_HASH.md']
    links=[]
    for doc in docs:
        for match in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if '://' in match or match.startswith('#'):continue
            p=(doc.parent/match.split('#',1)[0]).resolve();assert p.exists(),(doc,p);links.append(str(p.relative_to(DEST)))
    # Inspect generated publication files as well as copied source candidates.
    findings=[];scanned=0
    for p in DEST.rglob('*'):
        if not p.is_file() or '.git' in p.parts:continue
        labels=secret_findings(p);scanned+=1
        if labels:findings.append({'path':p.relative_to(DEST).as_posix(),'types':labels})
    assert not findings,findings
    result={'checked_utc':now(),'version':VERSION,'passed':True,'archives':archivechecks,'restore_tests':tests,'actual_data_restore':restored,
        'new_document_links_checked':len(links),'secret_scan_files':scanned,'secret_scan_findings':findings,
        'physical_qualification':False,'LLM_improvement_measured':False,'clean_machine_solver_installation_tested':False}
    dump(RUN/'verification.json',result);dump(DEST/'surumler/v0.11.0/publication_checks.json',result)
    print({'passed':True,'restore_tests':len(tests),'actual_raw_paths_restored':restored['restored_original_paths'],'links':len(links),'secret_scan_files':scanned})

if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else 'local')
