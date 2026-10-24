"""Close the interrupted session honestly and prepare a bounded continuation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    src=OUT/'simulations/v3_r4roe_coarse_firstorder_control';dst=OUT/'simulations/v3_r4roe_firstorder_cont4200'
    assert not dst.exists(),'Preserve prepared trials'
    pid=json.loads((src/'process.json').read_text())['pid']
    probe=subprocess.run(['powershell','-NoProfile','-Command',f"Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName"],capture_output=True,text=True)
    assert probe.stdout.strip()!='SU2_CFD','Previous owned CFD still running'
    seal=json.loads((OUT/'reports/v3_firstorder_control_preseal.json').read_text())
    assert sha(src/'mesh.su2')==seal['mesh_sha256'] and sha(src/'case.cfg')==seal['config_sha256']
    now=datetime.now(timezone.utc).isoformat()
    if not (src/'run_status.json').exists():
        status={'name':src.name,'status':'interrupted_between_sessions','exit_code':None,'seconds':None,
                'observed_utc':now,'last_history_iteration':4302,'process_absent_verified':True,
                'note':'No solver completion/status file survived; do not infer successful exit or continuous elapsed runtime',
                'threads':4,'config_sha256':sha(src/'case.cfg'),'mesh_sha256':sha(src/'mesh.su2')}
        (src/'run_status.json').write_text(json.dumps(status,indent=2))
    checkpoint=src/'restart_flow_004200.dat';assert checkpoint.exists()
    for f in ['flow_004200.vtu','surface_flow_004200.vtu']:assert (src/f).exists()
    dst.mkdir();shutil.copy2(src/'mesh.su2',dst/'mesh.su2')
    parser=load('existing_cfg',ROOT/'work/blind_validation/solver_v2/solve.py')
    settings=parser.readcfg(src/'case.cfg');settings['ITER']='3000'
    helper=load('run_helper',ROOT/'work/mesh_research/run_case.py')
    helper.prepare(dst.name,checkpoint,settings)
    note={'created_utc':now,'source_case':src.name,'source_checkpoint':4200,'initial_restart_sha256':sha(checkpoint),
          'only_run_length_restart_changed':True,'same_mesh':sha(dst/'mesh.su2')==sha(src/'mesh.su2'),
          'numerical_policy':'First-order Roe, fixedCFL1/MG3; same physical case',
          'scope':'Bounded numerical diagnostic, cannot qualify high-order flow or replace preselected fine',
          'request_order':'Finish these tests and their review before new ONERA M6 native runs',
          'minimum_qualification_passed':False}
    (dst/'controlled_trial.json').write_text(json.dumps(note,indent=2))
    (OUT/'reports/v3_firstorder_continuation_preseal.json').write_text(json.dumps(note,indent=2))
    print(json.dumps(note,indent=2))
if __name__=='__main__':main()
