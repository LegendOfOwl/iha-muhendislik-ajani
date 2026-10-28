"""Check the generated artifact and immutable evidence, without a browser."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
REPORT=ROOT/'outputs/reports/acik_sorunlar_ve_derin_arastirma_20261028'


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.cards=[]; self.current=None; self.scripting=False
        self.scripts=[]; self.script=''; self.links=[]; self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a['href'])
        if tag=='details' and a.get('class')=='issue':
            assert self.current is None
            self.current={'priority':a['data-priority'],'domain':a['data-domain'],'text':''}
        if tag=='script':self.scripting=True;self.script='';assert 'src' not in a
    def handle_endtag(self,tag):
        if tag=='details' and self.current is not None:self.cards.append(self.current);self.current=None
        if tag=='script':self.scripts.append(self.script);self.scripting=False
    def handle_data(self,data):
        if self.scripting:self.script+=data
        elif self.current is not None:self.current['text']+=data


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    r=json.loads(REPORT.with_suffix('.json').read_text(encoding='utf-8'))
    parser=Parser();parser.feed(REPORT.with_suffix('.html').read_text(encoding='utf-8'));parser.close()
    assert len(parser.cards)==r['issue_count']==26 and len(parser.scripts)==1
    assert len(parser.ids)==len(set(parser.ids))==5
    local=[];external=set()
    for target in parser.links:
        u=urlsplit(target)
        if u.scheme:
            assert u.scheme=='https' and u.netloc
            external.add(target)
        elif u.path:
            p=(REPORT.parent/unquote(u.path)).resolve()
            assert p.is_relative_to(ROOT) and p.is_file(),target
            local.append(p.relative_to(ROOT).as_posix())
    verified=0
    snapshots=r['evidence_integrity'].get('mutable_baseline_snapshots',{})
    for name,h in r['evidence_integrity']['files_sha256'].items():
        path=ROOT/snapshots[name]['path'] if name in snapshots else ROOT/name
        if name in snapshots:assert snapshots[name]['sha256']==h
        assert sha(path)==h,name
        verified+=1
    for stem,entry in r['specialist_modules'].items():assert sha(BASE/stem)==entry['sha256'],stem
    codes={'U%02d'%i for i in range(1,27)}
    assert codes=={x['id'] for x in r['issues']}
    assert all(x['proposal_executed'] is False and x['status']=='open' for x in r['issues'])
    for x in ('physical_qualification_passed','M6_qualification_passed','LLM_improvement_demonstrated'):assert r[x] is False
    assert type(r['new_native_CFD_runs']) is int and r['new_native_CFD_runs']==r['new_builds']==r['new_installations']==0
    fixture=BASE/'report_ui_fixture.json'
    fixture.write_text(json.dumps({'cards':parser.cards,'script':parser.scripts[0]},ensure_ascii=False),encoding='utf-8')
    cfg=json.loads((ROOT/'work/setup/tool_config.json').read_text(encoding='utf-8'))
    p=subprocess.run([cfg['node'],str(BASE/'check_report_filters.js'),str(fixture)],text=True,capture_output=True,encoding='utf-8',timeout=10)
    assert p.returncode==0,p.stderr or p.stdout
    ui=json.loads(p.stdout)
    checks=json.loads((BASE/'v018_publication_checks.json').read_text(encoding='utf-8'))
    assert checks['passed'] is True and checks['tests_run']==28
    for name,h in checks['code_sha256_after'].items():assert sha(ROOT/name)==h
    result={'checked_utc':datetime.now(timezone.utc).isoformat(),'passed':True,
        'report_files_sha256':{str(REPORT.with_suffix(e).relative_to(ROOT)):sha(REPORT.with_suffix(e)) for e in ('.json','.md','.html')},
        'local_link_occurrences':len(local),'unique_local_links':len(set(local)),
        'primary_source_addresses':r['distinct_primary_source_addresses'], 'unique_external_link_addresses':len(external),
        'unique_local_evidence_hashes_rechecked':verified,'all_specialist_module_hashes_matched':True,
        'mutable_baseline_snapshots_used':snapshots,
        'check_code_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in (Path(__file__),BASE/'check_report_filters.js')},
        'functional_report_checks':ui,'publication_guard_checks':28,'new_native_CFD_runs':0,'new_builds':0,
        'browser_visual_verification':False,'browser_limitation':'CUA file URL opening was blocked by browser protocol policy; no workaround or alternate browser surface attempted.',
        'alternative':'Static HTML/local-link checks and report JavaScript executed against inert DOM fixtures only.',
        'physical_qualification_passed':False,'LLM_improvement_demonstrated':False}
    target=ROOT/'outputs/reports/deep_research_checks_20261028.json'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print({'passed':True,'issues':26,'sources':r['distinct_primary_source_addresses'],'local_links':len(set(local)),
           'filter_checks':len(ui['checks']),'browser_visual_verification':False})


if __name__=='__main__':main()
