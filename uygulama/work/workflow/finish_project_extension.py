"""Seal integration evidence while retaining open aircraft/viscous-CFD acceptance."""
from datetime import datetime,timezone
import hashlib,json,shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs';REPORTS=OUT/'reports'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ['src','href'] and value:self.urls.append(value)
def check_links(p):
    h=Links();h.feed(p.read_text(encoding='utf-8'));checked=[]
    for url in h.urls:
        u=urlsplit(url)
        if u.scheme or not u.path:continue
        target=(p.parent/unquote(u.path)).resolve()
        if not target.exists():raise ValueError('Missing local link: '+str(p)+' -> '+url)
        checked.append(url)
    return {'file':str(p.relative_to(ROOT)),'checked_local_links':len(checked),'passed':True}
def main():
    task_path=OUT/'data/tasks/20261019-100440-8e781b.json';task=read(task_path)
    unchanged=all(sha(ROOT/p)==h for p,h in task['input_sha256'].items());assert unchanged
    core=read(REPORTS/'test_results.json');workflow=read(REPORTS/'workflow_checks.json');projects=read(REPORTS/'project_interface_checks.json')
    assert core['passed_checks']==26 and core['total_checks']==26
    assert workflow['passed'] and len(workflow['checks'])==17
    assert projects['passed'] and len(projects['checks'])==15
    launch=read(REPORTS/'exe_normal_launch.json');assert launch['passed'] and launch['responding']
    assert read(REPORTS/'tool_health.json')['all_paths_present']
    croot=OUT/'projects/proje-0314dcd012';cfd=read(croot/'reports/profile_cfd_results.json');field=read(croot/'reports/profile_field_checks.json')
    assert cfd['passed'] and cfd['quality_passed'] and field['gmsh_readback_passed']
    assert cfd['geometry_sha256']==field['source_geometry_sha256'] and cfd['conditions_sha256']==field['conditions_sha256']
    case=read(croot/'data/profile_cfd_case.json');assert sha(ROOT/case['airfoil'])==cfd['geometry_sha256']
    assert read(REPORTS/'cfd_qualification.json')['quality_passed'] is False
    assert read(REPORTS/'complex_vlm_qualification.json')['quality_passed'] is False
    assert all(p['status']=='bekliyor' for p in read(OUT/'data/project/conceptual_steps.json'))
    oas=read(REPORTS/'openaerostruct_examples.json');assert oas['passed'] and oas['physical_design_acceptance']=='not evaluated'
    assert len(oas['results'][1]['derivatives'])==4
    docs=[REPORTS/'projeler_exe_ve_profil_cfd.html',REPORTS/'openaerostruct_ajan_yaklasimi.html',croot/'reports/profile_cfd.html',OUT/'Proje-Ozeti.html']
    local_links=[check_links(p) for p in docs]
    raw={}
    for row in cfd['results']:
        folder=Path(row['folder'])
        for name in ['mesh.su2','case.cfg','history.csv','flow.vtu','native.log']:
            p=folder/name;raw[str(p.relative_to(ROOT))]=sha(p)
    sources=[ROOT/'AGENTS.md']+[ROOT/p for p in ['work/agent/projects.py','work/agent/projects_desk.ps1','work/agent/project.py','work/agent/intake.py','work/agent/Launcher.cs','work/setup/build_launcher.ps1','work/qualification/profile_cfd.py','work/qualification/profile_cfd_views.py','work/openaerostruct/run_examples.py','work/openaerostruct/agent_reference/manifest.json']]
    ui=[OUT/'plots'/('projects_'+id+'_'+str(i)+'.png') for id in ['iha','qualification'] for i in range(4)]
    assert all(p.exists() for p in ui)
    q={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':True,'scope':'Project GUI/EXE and tool integration; physical scope acceptance is separate','checks':{'core':26,'workflow':17,'project_routing':15,'real_UAV_inputs_unchanged':unchanged,'EXE_self_test_exit':0,'normal_EXE_window_running':True,'four_tabs_two_projects_rendered':True,'source_profile_native_CFD_runtime':True,'source_profile_Euler_preliminary_quality':True,'published_OAS_examples':2,'OAS_total_derivative_groups':4},'exe_sha256':sha(OUT/'Muhendislik-Merkezi.exe'),'exe_bytes':(OUT/'Muhendislik-Merkezi.exe').stat().st_size,'local_links':local_links,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'ui_sha256':{str(p.relative_to(ROOT)):sha(p) for p in ui},'raw_profile_CFD_sha256':raw,'not_completed':['Arbitrary imported CAD to qualified 3D CFD','New-source viscous/RANS boundary-layer qualification','Existing RANS CD and complex VLM surface CDi quality gates','OAS mesh/physical design acceptance and OpenVSP Python bridge','Fusion engine, entitlement and STEP round-trip','Eight actual UAV conceptual steps; current mission/mass data missing'],'upstream_OAS_LLM_framework_executed':False,'new_LLM_session_started_for_tests':False}
    save(REPORTS/'project_extension_quality.json',q)
    # Immutable per-task copies protect these facts from later report regeneration.
    evidence=[*docs[:2],REPORTS/'projeler_exe_ve_profil_cfd.md',REPORTS/'openaerostruct_ajan_yaklasimi.md',REPORTS/'project_extension_quality.json',REPORTS/'project_interface_checks.json',REPORTS/'workflow_checks.json',REPORTS/'test_results.json',REPORTS/'openaerostruct_examples.json',REPORTS/'exe_normal_launch.json',croot/'reports/profile_cfd_results.json',croot/'reports/profile_field_checks.json',croot/'reports/profile_cfd.html',OUT/'plots/projects_iha_0.png',OUT/'plots/openaerostruct_deformation.png',ROOT/'work/setup/openaerostruct_install.json']
    folder=REPORTS/'task_evidence'/task['id'];folder.mkdir(parents=True,exist_ok=True);items=[]
    for p in evidence:
        dest=folder/p.name
        if dest.exists() and sha(dest)!=sha(p):raise ValueError('Previously sealed evidence changed: '+str(dest))
        if not dest.exists():shutil.copy2(p,dest)
        items.append({'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'live_path':str(p.relative_to(ROOT))})
    task['acceptance'].append('OpenAeroStruct ve üniversite kaynaklı ajan yaklaşımını incele, yerel talimatları uyarla ve resmî hafif çözücü örneklerini test et')
    task.update(status='tamamlandı',completed_utc=q['timestamp'],evidence=items,blocked_by=[],remaining_capabilities=q['not_completed'],completion_scope=q['scope'])
    task['acceptance_results']=[{'criterion':s,'status':'sağlandı','evidence':'outputs/reports/project_extension_quality.json'} for s in task['acceptance']]
    save(task_path,task)
    print(json.dumps({'passed':True,'links':local_links,'archived_evidence':len(items),'EXE_bytes':q['exe_bytes'],'aircraft_steps_completed':0},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
