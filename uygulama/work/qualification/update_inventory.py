"""Persist measured qualification status without upgrading incomplete acceptance."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=ROOT/'work/qualification/sources'; manifest=read(source/'source_manifest.json')
    for entry in manifest:
        if entry['file'].endswith('nasa_naca0012_validation.html'):
            entry.update(usable_as_validation_source=False,note='Legacy URL redirected to a generic NASA page; not used as airfoil evidence')
    for name in ['CP_Gregory_expdata.dat','CLCD_Ladson_expdata.dat','n0012clcd_cfl3d_sa.dat','n0012cp_cfl3d_sa.dat']:
        p=source/name
        if not any(e['file']==str(p.relative_to(ROOT)) for e in manifest):
            manifest.append({'file':str(p.relative_to(ROOT)),'url':'https://tmbwg.github.io/turbmodels/NACA0012_validation/'+name,
                'bytes':p.stat().st_size,'sha256':sha(p),'usable_as_validation_source':True})
    write(source/'source_manifest.json',manifest)
    cfd=read(OUT/'reports/cfd_qualification.json'); compare=read(OUT/'reports/cfd_reference_comparison.json')
    meta=read(ROOT/'work/setup/su2_install.json')
    meta.update(status='installed and native Euler/RANS run verified; full CFD acceptance incomplete',
        runtime_verified=cfd['passed'],quality_passed=cfd['quality_passed'] and compare['grid_acceptance_passed'],
        last_test_utc=cfd['timestamp'],test_report='outputs/reports/cfd_qualification.json',
        reference_report='outputs/reports/cfd_reference_comparison.json',
        limits=['One 2D RANS angle; no automatic arbitrary airfoil meshing service',
                'Medium/fine drag changes 22.84%; mesh independence not established',
                'Fine max y+ 1.744 does not meet strict max y+ <1'])
    write(ROOT/'work/setup/su2_install.json',meta)
    cfg=read(ROOT/'work/setup/tool_config.json'); cfg['su2']=meta
    # PowerShell object parsing rejects keys that differ only by case.
    freecad_path=ROOT/'work/setup/freecad_install.json'; freecad=read(freecad_path)
    for alias in ['freecad.exe','freecadcmd.exe']:
        freecad['executables'].pop(alias,None)
    write(freecad_path,freecad); cfg['freecad']=freecad
    cfg['fusion_compute']=read(ROOT/'work/setup/fusion_mcp_install.json')
    cfg['deterministic_cad']={'runner':'work/geometry/parametric_wing.py','input':'outputs/data/parametric_wing_case.json',
        'geometry_checks_passed':True,'report':'outputs/reports/parametric_cad_qualification.json',
        'scope':'Single-element normalized Selig airfoil; symmetric ruled wing and ribs; not arbitrary CAD'}
    cfg['complex_native_vlm']={'runner':'work/qualification/run_complex_vlm.py','report':'outputs/reports/complex_vlm_qualification.json',
        'runtime_verified':True,'quality_passed':False,'force_audit':'outputs/reports/complex_vlm_force_audit.json'}
    cfg['latest_engineering_report']='outputs/reports/muhendislik_seviyesi_ve_cfd.html'
    cfg['last_engineering_extension_utc']=datetime.now(timezone.utc).isoformat()
    write(ROOT/'work/setup/tool_config.json',cfg)
    # This supplement records actual test settings; solver-run evidence is left unchanged.
    vlm=read(OUT/'reports/complex_vlm_qualification.json'); cref=vlm['results'][0]['reference']['cref_m']
    evidence={'timestamp':datetime.now(timezone.utc).isoformat(),
        'classification':{'CAD_profile':'kaynaklı; UIUC','CAD_dimensions':'varsayım; synthetic qualification',
            'VSPAERO_conditions':'varsayım; tool qualification','CFD_conditions':'kaynaklı; SU2 tutorial',
            'solver_outputs':'ölçülmüş; native solver output, not physical experiment','actual_UAV_inputs':'bilinmiyor'},
        'VSPAERO_conditions':{'Vinf_m_s':30,'rho_kg_m3':1.225,'Mach':.08816,'ReCref':500000,
            'mu_implied_Pa_s':1.225*30*cref/500000,'note':'Explicit qualification assumptions; native CDo heuristic is not accepted total drag'},
        'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [OUT/'data/parametric_wing_case.json',OUT/'data/airfoils/naca2412.dat',source/'source_manifest.json']},
        'solver_run_evidence_preserved':True,'Fusion_engine_tested':False,
        'further_validation':['Fine-grid RANS drag convergence and y+','Native VLM surface/wake force disagreement',
            'Full CAD/OpenVSP surface equivalence','Custom airfoil mesh generation and operating envelope','Fusion engine round trip after MCP reload']}
    write(OUT/'reports/engineering_extension_evidence.json',evidence)
    print('Measured inventory and source hashes updated; incomplete acceptance retained.')
if __name__=='__main__': main()
