"""Check delivered evidence and seal this integration task without accepting failed physics gates."""
from datetime import datetime,timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'; REPORTS=OUT/'reports'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs): self.links += [v for k,v in attrs if k in {'href','src'}]

def main():
    links=[]
    for p in [OUT/'Proje-Ozeti.html',REPORTS/'muhendislik_seviyesi_ve_cfd.html']:
        parser=Links(); parser.feed(p.read_text(encoding='utf-8'))
        local=[urlsplit(s) for s in parser.links if not urlsplit(s).scheme]
        missing=[s.path for s in local if s.path and not (p.parent/unquote(s.path)).exists()]
        assert not missing,missing
        links.append({'path':str(p.relative_to(ROOT)),'local_links':len(local),'missing':missing})
    cad=read(REPORTS/'parametric_cad_qualification.json'); cfd=read(REPORTS/'cfd_qualification.json')
    ref=read(REPORTS/'cfd_reference_comparison.json'); vlm=read(REPORTS/'complex_vlm_qualification.json')
    fusion=read(ROOT/'work/setup/fusion_mcp_install.json'); controls=read(REPORTS/'input_rejection_checks.json')
    bores=read(REPORTS/'step_bore_measurements.json'); shortcuts=read(REPORTS/'native_shortcut_checks.json')
    assert cad['passed'] and cad['passed_checks']==9 and all(r['STEP_bore_readback']['passed'] for r in cad['ribs'])
    assert controls['passed'] and bores['passed'] and shortcuts['passed']
    assert cfd['passed'] and cfd['quality_passed'] is False and ref['grid_acceptance_passed'] is False
    assert vlm['passed'] and vlm['quality_passed'] is False
    assert fusion['oauth_login_verified'] and fusion['fusion_engine_tested'] is False
    assert ref['gmsh_readback']['passed']
    source=read(ROOT/'work/qualification/sources/source_manifest.json')
    assert all(sha(ROOT/s['file'])==s['sha256'] for s in source)
    taskpath=OUT/'data/tasks/20261018-212129-8ffed7.json'; task=read(taskpath)
    assert all(sha(ROOT/p)==h for p,h in task['input_sha256'].items())
    steps=read(OUT/'data/project/conceptual_steps.json')
    assert len(steps)==8 and all(s['status']=='bekliyor' for s in steps)
    raw={}
    for case in cfd['results']:
        folder=Path(case['folder'])
        for name in ['case.cfg','command.json','inputs.json','native.log','history.csv','flow.vtu','surface_flow.csv']:
            p=folder/name; assert p.exists(); raw[str(p.relative_to(ROOT))]=sha(p)
    q={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':True,'scope':'Integration, traceability and delivery checks, not acceptance of all physical results',
       'html_links':links,'source_hashes_match':True,'real_project_inputs_unchanged':True,
       'CAD_checks_passed':cad['passed_checks'],'invalid_inputs_rejected':len(controls['checks']),
       'exported_STEP_bores_passed':bores['passed'],'native_Gmsh_readback_passed':True,
       'CFD_runtime_passed':True,'CFD_full_quality_accepted':False,'VLM_runtime_passed':True,'VLM_full_quality_accepted':False,
       'Fusion_OAuth_verified':True,'Fusion_engine_tested':False,'real_UAV_conceptual_steps_completed':0,
       'raw_CFD_evidence_sha256':raw,
       'visually_inspected':['outputs/plots/engineering_hub.png','outputs/plots/parametric_wing_cad.png',
            'outputs/plots/cfd_pressure_and_mesh.png','outputs/plots/cfd_cp_validation.png']}
    write(REPORTS/'engineering_extension_quality.json',q)
    task.update(status='tamamlandı',completed_utc=datetime.now(timezone.utc).isoformat(),
        report='outputs/reports/muhendislik_seviyesi_ve_cfd.html',
        acceptance_results=[{'criterion':c,'passed':True,'interpretation':'Kurulum/deney ve raporlama kabulü; bütün fiziksel sonuçların kabul edildiği anlamına gelmez'} for c in task['acceptance']],
        follow_up=[{'item':'Fusion motoru ve lisans/hub doğrulaması','status':'bekliyor','requires':'MCP bağlantı araçlarının bu sohbete yüklenmesi'},
                   {'item':'CFD sürükleme ve duvar ağı yakınsaması','status':'bekliyor'},
                   {'item':'Karmaşık kanatta yüzey/iz kuvvet farkı ve tam geometri eşleştirmesi','status':'bekliyor'}],
        scope_limits=['Fusion OAuth completed; no Fusion modeling session invoked',
            'CFD and native complex VLM have open quality gates',
            'No general arbitrary-airfoil mesh service or arbitrary-CAD guarantee',
            'Actual UAV design inputs remain unknown; ANSYS deferred'])
    paths=[REPORTS/n for n in ['muhendislik_seviyesi_ve_cfd.md','muhendislik_seviyesi_ve_cfd.html',
        'parametric_cad_qualification.json','step_bore_measurements.json','input_rejection_checks.json',
        'complex_vlm_qualification.json','complex_vlm_force_audit.json','cfd_qualification.json','cfd_reference_comparison.json',
        'engineering_extension_evidence.json','engineering_extension_quality.json','native_shortcut_checks.json','ui_check.json','tool_health.json']]
    paths += [ROOT/'work/setup'/n for n in ['su2_install.json','fusion_mcp_install.json','fusion_connection_check.json','freecad_install.json']]
    folder=REPORTS/'task_evidence'/task['id']; folder.mkdir(parents=True,exist_ok=True); task['evidence']=[]
    for p in paths:
        dst=folder/p.name
        if dst.exists() and sha(dst)!=sha(p): raise ValueError('Sealed evidence differs: '+str(dst))
        if not dst.exists(): shutil.copyfile(p,dst)
        task['evidence'].append({'path':str(dst.relative_to(ROOT)),'sha256':sha(dst),'live_path':str(p.relative_to(ROOT))})
    write(taskpath,task)
    print(json.dumps({k:v for k,v in q.items() if k!='raw_CFD_evidence_sha256'},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
