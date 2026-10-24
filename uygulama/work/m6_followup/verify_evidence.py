"""Independent readback of frozen predictions, source geometry and all CSV rows."""
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import csv,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-e9319baef1';REP=OUT/'reports'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def freeze(p):
    a=read(p);entries={**a['files_sha256'],**a['code_sha256']}
    errors=[path for path,h in entries.items() if not (ROOT/path).exists() or sha(ROOT/path)!=h]
    return {'file':str(p.relative_to(ROOT)),'hash_records':len(entries),'mismatches':errors,'passed':not errors}
def mesh(path):
    lines=path.read_text().splitlines();n=int(lines[1].split('=')[1]);at=2+n;count=int(lines[at].split('=')[1].split()[0]);start=at+1
    xyz=np.array([[float(x) for x in row.split()[:3]] for row in lines[start:start+count]])
    i=start+count;nm=int(lines[i].split('=')[1]);i+=1;markers={}
    for _ in range(nm):
        name=lines[i].split('=')[1].strip();length=int(lines[i+1].split('=')[1]);i+=2
        rows=[[int(x) for x in row.split()] for row in lines[i:i+length]];i+=length
        markers[name]=np.unique(np.concatenate([row[1:1+{5:3,9:4}[row[0]]] for row in rows]))
    tet=np.array([[int(x) for x in row.split()][1:5] for row in lines[2:2+n] if row.split()[0]=='10'])
    return xyz,lines[:start],lines[start+count:],markers,tet
class LinkParser(HTMLParser):
    def __init__(self):super().__init__();self.refs=[]
    def handle_starttag(self,tag,attrs):self.refs.extend(v for k,v in attrs if k in ['href','src'] and v)
def links(p):
    parser=LinkParser();parser.feed(p.read_text(encoding='utf-8'));local=[]
    for ref in parser.refs:
        a=urlsplit(ref)
        if not a.scheme and not a.netloc and a.path:local.append((p.parent/unquote(a.path)).resolve())
    return {'file':str(p.relative_to(ROOT)),'local_references':len(local),'missing':[str(x) for x in local if not x.exists()]}
def main():
    output=REP/'m6_followup_integrity_20261024.json';assert not output.exists()
    folders=[OUT/'simulations/m6_jst_control_20261024_v2',OUT/'simulations/m6_jst_wallnormal_20261024_v3']
    contracts=[read(p/'contract.json') for p in folders]
    frozen=[freeze(REP/f) for f in ['m6_jst_prediction_frozen_20261024_v2.json','m6_wallnormal_prediction_frozen_20261024_v3.json']]
    a,prefix,tail,marks,tets=mesh(folders[0]/'mesh.su2');b,prefix2,tail2,marks2,_=mesh(folders[1]/'mesh.su2')
    geometry={'same_cell_topology':prefix==prefix2,'same_boundary_topology':tail==tail2,
        'same_wall_coordinates':np.array_equal(a[marks['WING']],b[marks['WING']]),
        'same_farfield_coordinates':np.array_equal(a[marks['FARFIELD']],b[marks['FARFIELD']]),
        'tetrahedra_coordinates_unchanged':np.array_equal(a[tets],b[tets]),
        'symmetry_plane_y_unchanged':np.array_equal(a[marks['SYMMETRY'],1],b[marks['SYMMETRY'],1]),
        'changed_interior_nodes':int(np.sum(np.any(a!=b,axis=1))),'node_count':len(a)}
    data=[]
    for name in ['m6_jst_control_20261024_v2','m6_jst_wallnormal_20261024_v3']:
        p=OUT/'data'/name/'prediction/experimental_comparison.csv';table=np.loadtxt(p,delimiter=',',skiprows=1)
        data.append({'file':str(p.relative_to(ROOT)),'points':len(table),'all_finite':bool(np.isfinite(table).all()),'unique_sections':len(np.unique(table[:,0])),'sha256':sha(p)})
    originals=read(ROOT/'work/validation/sources/manifest.json')['sources'];sources=[]
    for x in originals:
        p=ROOT/x['file']
        if p.name.startswith('cp') or p.name in ['ONERAb114.tec','m6_nasa.html','mesh_ONERAM6_turb_hybrid_258969.su2','turb_ONERAM6.cfg']:
            sources.append({'file':x['file'],'unchanged':sha(p)==x['sha256']})
    baseline=[]
    for c in contracts:
        baseline.append(all(sha(ROOT/p)==h for p,h in c['source_inputs_sha256'].items()))
    dep=ROOT/ contracts[0]['RAE_batch_closed'];closed=read(dep)
    dependency={'RAE_closed_before_both':all(datetime.fromisoformat(read(p/'run_status.json')['started_utc'])>=datetime.fromisoformat(closed['closed_utc']) for p in folders),
        'closure_unchanged':all(sha(dep)==c['RAE_closure_sha256'] for c in contracts),
        'RAE_report_unchanged':sha(ROOT/closed['report'])==closed['report_sha256'],
        'RAE_integrity_record_unchanged':sha(ROOT/'outputs/projects/proje-15cce2de02/reports/v3_evidence_integrity.json')==closed['evidence_integrity_sha256']}
    old=read(ROOT/'outputs/reports/source_geometry_validation_quality.json')
    uav={p:sha(ROOT/p)==h for p,h in old['actual_UAV_current_hashes'].items()}
    checks={'frozen_predictions':all(x['passed'] for x in frozen),'same_config_bytes':sha(folders[0]/'case.cfg')==sha(folders[1]/'case.cfg'),
        'same_seed_bytes':sha(folders[0]/'seed.dat')==sha(folders[1]/'seed.dat'),
        'unchanged_limits':contracts[0]['thresholds']==contracts[1]['thresholds'],
        'geometry_readback':all(v for k,v in geometry.items() if isinstance(v,bool)),
        'all_271_points':all(x['points']==271 and x['unique_sections']==7 and x['all_finite'] for x in data),
        'raw_sources_unchanged':all(x['unchanged'] for x in sources),'baseline_inputs_unchanged':all(baseline),
        'order_and_RAE_preservation':all(dependency.values()),'actual_UAV_inputs_unchanged':all(uav.values())}
    rejected=OUT/'simulations/m6_jst_control_20261024'
    rejected_check={'config_guard_rejected':read(rejected/'run_status.json')['exit_code']==1,'no_history_or_flow':not (rejected/'history.csv').exists() and not list(rejected.glob('flow*.vtu'))}
    result={'verified_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'frozen':frozen,'geometry':geometry,'source_data':sources,
        'all_point_tables':data,'dependency':dependency,'actual_UAV_inputs':uav,'initial_rejection':rejected_check,
        'evidence_checks_passed':all(checks.values()) and all(rejected_check.values()),'minimum_physical_qualification_passed':False,
        'note':'Integrity/readback checks do not turn failed residual/experiment or missing grid/BL/farfield gates into successful physics'}
    output.write_text(json.dumps(result,indent=2))
    result['report_links']=[links(REP/'m6_24_ekim.html'),links(ROOT/'outputs/reports/onera_m6_24_ekim.html')]
    result['evidence_checks_passed'] &=all(not x['missing'] for x in result['report_links'])
    output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    assert result['evidence_checks_passed'],'Do not complete a failed evidence audit'
if __name__=='__main__':main()
