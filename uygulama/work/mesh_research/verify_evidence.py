"""Read-only checks of old and new frozen evidence and local report links."""
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02';REP=OUT/'reports'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(path,groups=None):
    a=json.loads(path.read_text());records={}
    for k,v in a.items():
        if isinstance(v,dict) and (groups is None or k in groups) and (k.endswith('sha256') or k=='sha256'):
            records.update({str(p):h for p,h in v.items() if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h)})
    if isinstance(a.get('access_log'),str) and a.get('access_log_sha256'):records[a['access_log']]=a['access_log_sha256']
    errors=[]
    for p,h in records.items():
        target=ROOT/p
        if not target.exists():errors.append({'file':p,'error':'missing'})
        elif sha(target)!=h:errors.append({'file':p,'error':'hash mismatch'})
    return {'manifest':str(path.relative_to(ROOT)),'records':len(records),'errors':errors,'passed':not errors}
class Links(HTMLParser):
    def __init__(self):super().__init__();self.items=[]
    def handle_starttag(self,tag,attrs):
        self.items.extend(v for k,v in attrs if k in ['src','href'] and v)
def links(path):
    a=Links();a.feed(path.read_text(encoding='utf-8'));local=[]
    for s in a.items:
        parsed=urlsplit(s)
        if parsed.scheme or parsed.netloc or not parsed.path:continue
        p=(path.parent/unquote(parsed.path)).resolve();local.append(p)
    return {'file':str(path.relative_to(ROOT)),'local_references':len(local),'missing':[str(p) for p in local if not p.exists()]}
def main():
    reports=[verify(REP/'prediction_frozen.json',{'source_script_sha256','case_files_sha256'}),verify(REP/'prediction_v2_frozen.json')]
    for p in sorted(REP.glob('v3_diagnostic_freeze_*.json')):reports.append(verify(p))
    for p in [REP/'prediction_v3_cgrid_diagnostic_manifest.json',REP/'prediction_v3_cgrid_localr3_mesh_manifest.json',REP/'prediction_v3_cgrid_interfacer4_mesh_manifest.json']:
        reports.append(verify(p))
    for p in REP.glob('v3_firstorder*prediction_frozen.json'):reports.append(verify(p))
    old=json.loads((ROOT/'outputs/reports/source_geometry_validation_quality.json').read_text())
    uav={p:sha(ROOT/p)==h for p,h in old['actual_UAV_current_hashes'].items()}
    plan=json.loads((REP/'v3_research_plan_seal.json').read_text())
    oldhelper=sha(ROOT/'work/mesh_research/run_case_plan_version.py')==plan['sha256']['work\\mesh_research\\run_case.py']
    contract=sha(ROOT/'work/blind_validation/contract.json')=='a3106e323f9a5671067b69fded039fa8b3d2aae607514ec114a949b501b91c69'
    htmlchecks=[links(p) for p in [REP/'v3_research_diagnosis.html',ROOT/'outputs/reports/kaynakli_cfd_teshisi.html'] if p.exists()]
    result={'verified_utc':datetime.now(timezone.utc).isoformat(),'manifests':reports,'actual_UAV_inputs_unchanged':uav,
            'original_plan_helper_preserved_with_matching_hash':oldhelper,'contract_unchanged':contract,'HTML_links':htmlchecks,
            'evidence_checks_passed':all(r['passed'] for r in reports) and all(uav.values()) and oldhelper and contract and all(not a['missing'] for a in htmlchecks),
            'minimum_physical_qualification_passed':False,'scope':'Evidence integrity/software checks only; failed CFD gates stay failed'}
    (REP/'v3_evidence_integrity.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
