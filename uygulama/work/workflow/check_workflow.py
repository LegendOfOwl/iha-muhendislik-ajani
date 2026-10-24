"""Meaningful negative controls for unit conversion, missing inputs and invalid CFD reuse."""
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
sys.path[:0]=[str(ROOT/'work/agent'),str(ROOT/'work/workflow')]
from intake import normalize
from rank_candidates import compare
import project

def main():
    checks=[]
    def check(name,passed): checks.append({'name':name,'passed':bool(passed)})
    p={'request':'İki kanat adayını karşılaştır','constraints':{'target_speed_kmh':'108','endurance_min':'12,5','payload_kg':'0'}}
    n=normalize(p)
    check('km/h and minute SI conversion',n['inputs']['target_speed']['value']==30 and n['inputs']['endurance']['value']==750)
    check('Explicit zero payload retained; empty altitude unknown',n['inputs']['payload_mass']['value']==0 and n['inputs']['altitude']['value'] is None)
    for key,value in [('target_speed_kmh','NaN'),('max_span_m','-2'),('max_mass_kg',False),('altitude_m','1.000,5')]:
        b=copy.deepcopy(p); b['constraints'][key]=value
        try: normalize(b); ok=False
        except (ValueError,TypeError): ok=True
        check('Reject invalid field '+key,ok)
    with TemporaryDirectory(dir=ROOT/'work/workflow') as td:
        folder=Path(td); data=folder/'data/project'; data.mkdir(parents=True)
        assert folder.resolve().is_relative_to((ROOT/'work/workflow').resolve())
        (folder/'data/tasks').mkdir()
        (data/'mission.json').write_text('{"no_user_data_changed":true}')
        with patch.object(project,'OUT',folder),patch.object(project,'DATA',data):
            taskfile=project.make_task(n['request'])
            saved=json.loads(taskfile.read_text()); check('Task captures input digest',bool(saved['input_sha256']))
            saved['structured_request']='outputs/data/requests/test.json';project.write(taskfile,saved)
            cmd=project.launch(taskfile,dry=True)
            check('Agent dry-run carries workflow file and CFD mismatch rule','test.json' in cmd['prompt'] and 'CFD' in cmd['prompt'])
        proof=folder/'synthetic_CFD_contract.json'
        report_data={'quality_passed':True,'geometry_sha256':'g1','conditions_sha256':'c1','analysis_scope':'3D wing'}
        proof.write_text(json.dumps(report_data))
        candidate={'id':'contract_control','CDwing_estimated':.01,'geometry_sha256':'g1','conditions_sha256':'c1','required_CFD_scope':'3D wing',
            'CFD':{'report':str(proof.relative_to(ROOT)),'sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}}
        check('Matching synthetic contract is accepted',compare([candidate],{})['final_winner']=='contract_control')
        bad=copy.deepcopy(candidate);bad['conditions_sha256']='c2'
        check('Different conditions cannot reuse CFD',compare([bad],{})['final_winner'] is None)
        bad=copy.deepcopy(candidate);bad['required_CFD_scope']='3D whole aircraft'
        check('Wing CFD cannot validate whole aircraft',compare([bad],{})['final_winner'] is None)
        report_data['quality_passed']=False;proof.write_text(json.dumps(report_data))
        candidate['CFD']['sha256']=hashlib.sha256(proof.read_bytes()).hexdigest()
        check('Failed CFD gate blocks final ranking',compare([candidate],{})['final_winner'] is None)
    check('Missing CFD cannot create a final winner',compare([{'id':'A','CDwing_estimated':.01}],{})['final_winner'] is None)
    # A passing unrelated file is still not valid evidence for this candidate.
    report=OUT/'reports/test_results.json'
    base={'id':'A','span_m':1,'CDwing_estimated':.01,'geometry_sha256':'new-wing','conditions_sha256':'new-conditions','required_CFD_scope':'3D viscous aircraft',
          'CFD':{'report':str(report.relative_to(ROOT)),'sha256':hashlib.sha256(report.read_bytes()).hexdigest()}}
    check('Unrelated solver evidence rejected',compare([base],{})['final_winner'] is None)
    base['CFD']['sha256']='wrong'
    check('Changed evidence hash rejected',compare([base],{})['final_winner'] is None)
    result=compare([{'id':'long','span_m':2.3,'CDwing_estimated':.001},{'id':'short','span_m':1.8,'CDwing_estimated':.02}],{'span_m':2.1})
    check('Hard constraint excludes attractive low-drag candidate',result['rows'][0]['requirements_status']=='sağlanmadı' and result['rows'][0]['conditional_rank'] is None and result['rows'][1]['conditional_rank']==1)
    check('Unknown objective is not ranked',compare([{'id':'unknown','CDwing_estimated':None}],{})['rows'][0]['conditional_rank'] is None)
    r={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,
        'scope':'Input/traceability/ranking guard verification; no new LLM session started and no actual UAV input changed'}
    (OUT/'reports/workflow_checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
