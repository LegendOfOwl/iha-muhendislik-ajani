"""Check delivered links, recorded artifact hashes and the policy snapshot."""
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
from linear_pair import ROOT, PROJECT, TASK, read, save, sha, now


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ['href','src'] and value:self.links.append(value)


def main():
    reports=[ROOT/'outputs/reports/guvenilirlik_gelistirme_20261025.html',PROJECT/'reports/guvenilirlik_gelistirme_20261025.html']
    missing=[];count=0
    for report in reports:
        parser=Links();parser.feed(report.read_text(encoding='utf-8'))
        for value in parser.links:
            parsed=urlparse(value)
            if parsed.scheme or value.startswith('#'):continue
            count+=1
            if not (report.parent/unquote(parsed.path)).exists():missing.append({'report':str(report),'link':value})
    task=read(TASK)
    bad=[e['path'] for e in task['evidence'] if sha(ROOT/e['path'])!=e['sha256']]
    import sys;sys.path.insert(0,str(ROOT/'work/agent'));from learning import instruction_snapshot
    snapshot=instruction_snapshot(ROOT)
    assert snapshot==task['updated_agent_instruction_snapshot']
    assert snapshot['reliability_policy_version']=='2026-10-25.1'
    for name in ['m6_curvature_20261024.json','m6_curvature_v2_20261025.json']:
        data=read(PROJECT/'reports'/name)
        bad += [p for p,h in data['artifacts'].items() if sha(ROOT/p)!=h]
    result={'checked_utc':now(),'passed':not missing and not bad,'local_links':count,
            'missing':missing,'changed_evidence':bad,'task_status':task['status'],
            'new_policy_in_launch_snapshot':True,'physical_qualification':False}
    save(ROOT/'outputs/reports/reliability_delivery_checks_20261025.json',result)
    print(__import__('json').dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
