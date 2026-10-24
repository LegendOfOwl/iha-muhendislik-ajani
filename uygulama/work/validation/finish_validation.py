"""Record source provenance, report links and task completion without accepting failed CFD."""
from datetime import datetime,timezone
import hashlib,json,shutil,sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';IDS=json.loads((ROOT/'work/validation/projects.json').read_text());CAD=OUT/'projects'/IDS['cad'];CFD=OUT/'projects'/IDS['cfd']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,t,attrs):
        for k,v in attrs:
            if k in ['src','href'] and v:self.urls.append(v)
def links(p):
    parser=Links();parser.feed(p.read_text(encoding='utf-8'));count=0
    for url in parser.urls:
        u=urlsplit(url)
        if u.scheme or not u.path:continue
        if not (p.parent/unquote(u.path)).resolve().exists():raise ValueError('Missing report link '+url)
        count+=1
    return {'path':str(p.relative_to(ROOT)),'checked_local_links':count}
def main():
    stamp=datetime.now(timezone.utc).isoformat();index=read(OUT/'reports/validation_benchmark_index.json');raw=read(CFD/'reports/m6_rans_results.json');ex=read(CFD/'reports/m6_experiment_comparison.json')
    assert index['cad']['passed'] and raw['passed'] and len(raw['results'])==2 and ex['experiment_points']==271
    assert ex['field_view']['gmsh_readback_passed'] and ex['field_view']['native_field_finite']
    assert len(ex['sign_checks'])==14 and all(r['max_sign_normalization_error']<2e-5 for r in ex['sign_checks'])
    assert read(CAD/'reports/native_view_checks.json')['passed']
    # Check actual solver config, not only prose metadata.
    cfg_sources=[];conditions={'MACH_NUMBER':.8395,'AOA':3.06,'SIDESLIP_ANGLE':0,'REYNOLDS_NUMBER':11.72e6,'REYNOLDS_LENGTH':.64607,'FREESTREAM_TEMPERATURE':288.15}
    import re
    for row in raw['results']:
        folder=Path(row['folder']);text=(folder/'case.cfg').read_text()
        for key,val in conditions.items():assert float(re.search(r'^\s*'+key+r'\s*=\s*([^%\n]+)',text,re.M)[1])==val
        assert sha(folder/'mesh.su2')==row['mesh']['mesh_sha256']
        cfg_sources += [folder/name for name in ['case.cfg','command.json','mesh.su2','history.csv','surface_flow.vtu','native.log','experimental_comparison.csv']]
    # Retain source-control and initial/continued attempts in the same audit.
    initial_run=Path(raw['previous_run_directory']);initial=read(initial_run/'results.json')
    initial_comparison=read(initial_run/'initial_experiment_comparison.json')
    for row in initial['results']:
        folder=Path(row['folder'])
        cfg_sources += [folder/name for name in ['case.cfg','command.json','mesh.su2','history.csv','surface_flow.vtu','native.log','experimental_comparison.csv']]
    continuation=Path(raw['continuation_run_directory']);diagnostic=read(CFD/'reports/m6_continuation_diagnostic.json');contract=read(continuation/'continuation_contract.json')
    cfg_sources += [initial_run/'results.json',initial_run/'initial_experiment_comparison.json',continuation/'continuation_contract.json',continuation/'failure_diagnostic.json']
    assert raw['conditions_sha256']==initial['conditions_sha256']
    assert raw['thresholds']==initial['thresholds']
    assert contract['conditions_sha256']==initial['conditions_sha256'] and contract['thresholds']==initial['thresholds']
    for first,last in zip(initial['results'],diagnostic['results']):
        folder=Path(last['folder']);assert sha(folder/'mesh.su2')==first['mesh']['mesh_sha256']
        text=(folder/'case.cfg').read_text()
        for key,val in conditions.items():assert float(re.search(r'^\s*'+key+r'\s*=\s*([^%\n]+)',text,re.M)[1])==val
        assert last['restart_input_sha256']==sha(Path(first['folder'])/'restart_flow.dat')
        cfg_sources += [folder/name for name in ['case.cfg','command.json','mesh.su2','history.csv','native.log']]
        if last['runtime_passed']:cfg_sources += [folder/'surface_flow.vtu',folder/'experimental_comparison.csv']
    assert not diagnostic['completed'] and diagnostic['fine_Cp_metrics'] is None
    assert not (continuation/'finer_hybrid/surface_flow.vtu').exists()
    source_manifest=read(ROOT/'work/validation/sources/manifest.json');source_files=[]
    for r in source_manifest['sources']:
        p=ROOT/r['file'];assert sha(p)==r['sha256'];source_files.append(p)
    source_registry=OUT/'reports/nist_nasa_sources.json'
    save(source_registry,{'verified_utc':stamp,**source_manifest,'notes':['NIST reference geometry assisted reconstruction/modification; not a blind PDF benchmark','NASA hosts ONERA tunnel data; the experiment was conducted by ONERA','Official SU2 source grids used unchanged; not generated from the new CAD parts']})
    import zipfile
    with zipfile.ZipFile(ROOT/'work/validation/sources/nist_ctc_definitions.zip') as archive:
        for number in ['01','02','05']:
            source=next((ROOT/'work/validation/sources/nist_ctc_definitions').rglob('nist_ctc_'+number+'*.stp'))
            entry=next(name for name in archive.namelist() if Path(name).name==source.name)
            assert source.read_bytes()==archive.read(entry)
            delivered=CAD/'data/sources'/source.name;shutil.copy2(source,delivered)
            source_files += [source,delivered]
    github=read(ROOT/'work/validation/su2_cases_index.json')['rans/oneram6']
    for r in github:
        if r['name'].endswith('.su2'):
            data=(ROOT/'work/validation/sources'/r['name']).read_bytes();blob=hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest();assert blob==r['sha']
    source_files += [ROOT/'work/validation/sources/ONERAb114.tec',ROOT/'work/validation/sources/turb_ONERAM6.cfg']
    record={'Mach':{'value':.8395,'unit':'dimensionless','status':'kaynaklı','source':'NASA M6 Test2308'},'alpha':{'value':3.06,'unit':'deg','status':'kaynaklı','source':'NASA M6 Test2308'},'Re':{'value':11.72e6,'unit':'dimensionless','status':'kaynaklı','source':'NASA M6 Test2308'},'reference_length':{'value':.64607,'unit':'m','status':'kaynaklı','source':'NASA M6 Test2308'},'temperature':{'value':288.15,'unit':'K','status':'kaynaklı','source':'SU2 official example; actual tunnel temperature not established from this archive'},'turbulence_model':{'value':'SA fully turbulent','unit':'model','status':'varsayım','source':'SU2 source benchmark formulation'},'NASA_Cp_uncertainty':{'value':.02,'unit':'dimensionless','status':'kaynaklı','source':'NASA archive'}}
    save(CFD/'data/benchmark_input_records.json',record)
    save(CAD/'data/input_classification.json',{'units':'mm','source_geometry':'kaynaklı — NIST published reference STEP; missing dimensions measured from model','new_port_groove_keyway_dimensions':'varsayım — explicitly declared benchmark modifications, not NIST or UAV requirements','CTC01_method':'measured analytic sketch reconstruction; not blind PDF inference','material_and_airworthiness':'bilinmiyor; not evaluated'})
    files=[CAD/'reports/cad_validation.html',CFD/'reports/m6_validation.html',OUT/'reports/karmasik_cad_ve_nasa_testleri.html']
    link_checks=[links(p) for p in files]
    prior=read(OUT/'data/tasks/20261019-100440-8e781b.json');unchanged=all(sha(ROOT/p)==h for p,h in prior['input_sha256'].items());assert unchanged
    assert all(r['status']=='bekliyor' for r in read(OUT/'data/project/conceptual_steps.json'))
    # A successful experiment comparison task can correctly produce a failed physical acceptance.
    quality={'timestamp':stamp,'completed_requested_comparisons':True,'cad_geometry_checks_passed':True,'CFD_runtime_passed':True,'CFD_quality_passed':ex['quality_passed'],'actual_UAV_inputs_unchanged':unchanged,'LLM_CAD_models_used':False,'source_framework_LLM_invocations':0,'case_budget':{'CAD_source_parts':3,'CFD_geometry':'ONERA M6 Test2308','CFD_grid_families':2,'first_run_iterations_per_grid':4000,'numerical_continuation_iterations_per_grid':500},'local_report_links':link_checks,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in source_files},'raw_CFD_evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for p in cfg_sources},'cad_artifact_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (CAD/'cad').rglob('*') if p.is_file()},'limitations':['One CAD reference-assisted reconstruction plus two source-model modifications; not three blind drawing reconstructions','Source mesh families differ in farfield/rounded-tip geometry; no formal grid convergence','CFD acceptance and experiment discrepancies explicitly remain if quality_passed=false','No actual UAV conceptual phase completed']}
    quality['case_budget']['numerical_continuation_iterations_requested_per_grid']=quality['case_budget'].pop('numerical_continuation_iterations_per_grid')
    quality['case_budget']['numerical_continuation_iterations_recorded']={r['grid']:r['iterations'] for r in diagnostic['results']}
    quality['CFD_attempts']={'initial_quality_passed':initial_comparison['quality_passed'],'continued_quality_passed':False,'continuation_completed':False,'fine_continuation_fields_used':False,'conditions_and_thresholds_unchanged':True,'restart_and_mesh_checks_passed':True,'initial_report':str((initial_run/'initial_experiment_comparison.json').relative_to(ROOT)),'continuation_diagnostic':str((CFD/'reports/m6_continuation_diagnostic.json').relative_to(ROOT))}
    save(OUT/'reports/nist_nasa_validation_quality.json',quality)
    for kind,pid in IDS.items():
        project_root=CAD if kind=='cad' else CFD;task_path=next(p for p in (OUT/'data/tasks').glob('*.json') if read(p).get('project_id')==pid);task=read(task_path)
        evidence=list((project_root/'reports').glob('*.json'))+[project_root/'reports'/('cad_validation.html' if kind=='cad' else 'm6_validation.html'),OUT/'reports/nist_nasa_validation_quality.json',source_registry]
        folder=OUT/'reports/task_evidence'/task['id'];folder.mkdir(parents=True,exist_ok=True);items=[]
        for p in evidence:
            dest=folder/p.name
            if dest.exists() and sha(dest)!=sha(p):raise ValueError('Sealed evidence differs')
            if not dest.exists():shutil.copy2(p,dest)
            items.append({'path':str(dest.relative_to(ROOT)),'live_path':str(p.relative_to(ROOT)),'sha256':sha(dest)})
        task.update(status='tamamlandı',completed_utc=stamp,evidence=items,blocked_by=[],completion_scope=('One reference-assisted reconstruction plus two source-solid modifications, geometric checks and native parameter tests completed' if kind=='cad' else 'Two completed initial tunnel comparisons; additional continuation failed/timed out and was retained, no missing fields fabricated. Physical CFD quality failed'),open_engineering_acceptances=[] if kind=='cad' else ['M6 combined CFD acceptance remains open','Previous RANS/VLM aircraft quality still open'])
        manifest=read(ROOT/task['project_manifest']);task['completion_project_snapshot']=manifest
        if manifest.get('active_cad'):
            active=ROOT/manifest['active_cad']['path'];task['completion_active_cad_sha256']=sha(active)
            assert sha(active)==manifest['active_cad']['sha256']
        task['acceptance_results']=[{'criterion':s,'status':'sağlandı','evidence':'outputs/reports/nist_nasa_validation_quality.json'} for s in task['acceptance']];save(task_path,task)
    cfg=read(ROOT/'work/setup/tool_config.json');cfg['latest_engineering_report']='outputs/reports/karmasik_cad_ve_nasa_testleri.html';cfg['validation_benchmarks']={'index':'outputs/reports/validation_benchmark_index.json','projects':IDS,'cad_geometry_verified':True,'M6_CFD_runtime_verified':True,'M6_CFD_quality_passed':ex['quality_passed']};save(ROOT/'work/setup/tool_config.json',cfg)
    print(json.dumps({'finished':True,'CAD':index['cad'],'CFD':index['cfd'],'local_links':link_checks},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
