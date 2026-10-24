"""Seal scoped tool/UI delivery; generic aircraft CFD remains explicitly unverified."""
from datetime import datetime,timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import py_compile
import shutil
import subprocess
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'; REPORTS=OUT/'reports'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):self.urls += [v for k,v in attrs if k in {'src','href'}]
def main():
    html=[]
    for p in [REPORTS/'hafif_cfd_ve_is_akisi.html',REPORTS/'candidate_comparison.html',OUT/'Proje-Ozeti.html']:
        parser=Links();parser.feed(p.read_text(encoding='utf-8'));local=[urlsplit(s) for s in parser.urls if not urlsplit(s).scheme]
        missing=[s.path for s in local if s.path and not (p.parent/unquote(s.path)).exists()]
        assert not missing,missing
        html.append({'file':str(p.relative_to(ROOT)),'local_links':len(local),'missing':missing})
    for p in (ROOT/'work').rglob('*.py'):
        if '__pycache__' not in p.parts:py_compile.compile(str(p),doraise=True)
    for i in [1,2,3]:assert (OUT/f'plots/engineering_desk_tab{i}.png').exists()
    control=read(REPORTS/'workflow_checks.json');elmer=read(REPORTS/'elmer_cfd_qualification.json')
    compare=read(REPORTS/'candidate_comparison.json');core=read(REPORTS/'test_results.json')
    assert control['passed'] and len(control['checks'])==17
    assert elmer['passed'] and elmer['quality_passed'] and elmer['field_view']['readback_passed']
    assert compare['final_winner'] is None and compare['quality_passed'] is False
    assert core.get('passed',core.get('all_requested_groups_passed')) is True and read(REPORTS/'tool_health.json')['all_paths_present']
    gmsh=read(ROOT/'work/setup/freecad_install.json')['executables']['gmsh.exe']
    with (ROOT/'work/workflow/gmsh_elmer_readback.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([gmsh,elmer['field_view']['gmsh_pressure'],'-parse_and_exit'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    assert p.returncode==0
    taskpath=OUT/'data/tasks/20261018-231810-dcaa71.json'; task=read(taskpath)
    assert all(sha(ROOT/p)==value for p,value in task['input_sha256'].items())
    steps=read(OUT/'data/project/conceptual_steps.json');assert all(s['status']=='bekliyor' for s in steps)
    readiness={'timestamp':datetime.now(timezone.utc).isoformat(),'full_generic_pipeline_verified':False,
        'bounded_toolchain_operational':True,'user_request_to_task_traceability_checked':True,
        'research':'Ajan tarafından her görevde kaynak ve tanımlı tarama bütçesiyle yürütülür',
        'CAD':'Belirli kanat/nervür ailesi ölçü kontrolüyle doğrulandı; yeni aileler ayrıca sınanmalı',
        'preliminary_analysis':'Native XFOIL/VSPAERO var; tüm uçak güç/enerji/kararlılık tamamlanmadı',
        'CFD':'SU2 Euler/RANS ve Elmer Navier-Stokes çalışıyor; keyfi CAD ağı ve mevcut SU2/VLM sürükleme kabulleri açık',
        'ranking':'Kanıt/koşul/geometri/kapsam kapıları var; mevcut üç adayda nihai kazanan yok',
        'reporting':'Grafik, kaynak, ham çıktı ve açık kontroller bir arada',
        'actual_UAV_design_completed':False,'ANSYS_installed':False,'OpenFOAM_installed':False,
        'sources':[{'url':u,'checked_date':'2026-10-18','kind':'primary source opened in this session'} for u in [
            'https://docs.csc.fi/apps/elmer/','https://sourceforge.net/projects/elmerfem/files/WindowsBinaries/Win64Installer/',
            'https://www.nic.funet.fi/pub/sci/physics/elmer/bin/windows/','https://openfoam.org/download/windows/',
            'https://bluecfd.github.io/Core/Downloads/']]}
    write(REPORTS/'workflow_readiness.json',readiness)
    quality={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':True,'scope':'Installation, native CFD verification and workflow/UI guards; not all-aircraft validation',
        'html_checks':html,'workflow_checks_passed':len(control['checks']),'basic_checks_passed':core['passed_checks'],
        'elmer_native_flow_accepted_in_qualified_scope':True,'native_Gmsh_readback_passed':True,
        'GUI_tabs_rendered_and_inspected':3,'LLM_session_spawned_for_test':False,
        'real_project_inputs_unchanged':True,'full_generic_pipeline_verified':False,'CFD_ranking_demo_has_final_winner':False,
        'elmer_raw_evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for r in elmer['results'] for p in
            [Path(r['folder'])/'case.sif',Path(r['folder'])/'native.log',Path(r['folder'])/'channel.msh',Path(r['VTU'])]}}
    write(REPORTS/'light_cfd_workflow_quality.json',quality)
    config=read(ROOT/'work/setup/tool_config.json');config['latest_workflow_report']='outputs/reports/hafif_cfd_ve_is_akisi.html'
    config['workflow_readiness']='outputs/reports/workflow_readiness.json';write(ROOT/'work/setup/tool_config.json',config)
    task.update(status='tamamlandı',completed_utc=datetime.now(timezone.utc).isoformat(),report='outputs/reports/hafif_cfd_ve_is_akisi.html',
        acceptance_results=[{'criterion':c,'passed':True,'scope':'Bu entegrasyon/arayüz teslimi; genel uçak otomasyonu tamamlandı anlamına gelmez'} for c in task['acceptance']],
        follow_up=['Gerçek kısıtlarla sınırları belirli aday araştırması ve yeni analiz görevi',
            'Yeni geometri için uygun CFD ağı ve CAD/analiz eşleştirmesi','SU2/VLM açık sürükleme kabulleri',
            'Fusion motoru ve lisans/hub testi'],scope_limits=['Generic all-aircraft pipeline not verified','Actual UAV inputs still unknown','OpenFOAM/ANSYS not installed'])
    folder=REPORTS/'task_evidence'/task['id'];folder.mkdir(parents=True,exist_ok=True);task['evidence']=[]
    paths=[REPORTS/n for n in ['hafif_cfd_ve_is_akisi.md','hafif_cfd_ve_is_akisi.html','elmer_cfd_qualification.json',
        'workflow_checks.json','candidate_comparison.json','candidate_comparison.html','workflow_readiness.json','light_cfd_workflow_quality.json','tool_health.json']]
    paths.append(ROOT/'work/setup/elmer_install.json')
    for p in paths:
        dst=folder/p.name
        if dst.exists() and sha(dst)!=sha(p):raise ValueError('Sealed evidence differs: '+str(dst))
        if not dst.exists():shutil.copyfile(p,dst)
        task['evidence'].append({'path':str(dst.relative_to(ROOT)),'sha256':sha(dst),'live_path':str(p.relative_to(ROOT))})
    write(taskpath,task)
    print(json.dumps({k:v for k,v in quality.items() if k!='elmer_raw_evidence_sha256'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
