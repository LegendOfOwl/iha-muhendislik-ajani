"""Project separation, task transfer, file routing and compiled launcher checks."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'work/agent')]
import projects
import project
checks=[]
def check(name,ok):checks.append({'name':name,'passed':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def main():
    folder=ROOT/'work/workflow/project_tests';folder.mkdir(exist_ok=True)
    original=projects.sha(ROOT/'outputs/cad/parametric_wing/envelope.step')
    with TemporaryDirectory(dir=folder) as td:
        temp=Path(td).resolve();assert temp.is_relative_to(folder.resolve())
        base=temp/'outputs/data/project';base.mkdir(parents=True)
        for name in ['mission.json','mass_budget.json','conceptual_steps.json']:shutil.copy2(ROOT/'outputs/data/project'/name,base/name)
        with patch.object(projects,'ROOT',temp),patch.object(projects,'STORE',temp/'outputs/data/projects'):
            projects.bootstrap();a=projects.create('Deneme A — ölçülü kanat');b=projects.create('Deneme B')
            source=ROOT/'outputs/cad/parametric_wing/envelope.step'
            imported=projects.import_file(a['id'],source);projects.active_cad(a['id'],imported['path'])
            check('CAD belongs only to importing project',any(x['group']=='CAD' for x in projects.files(a['id'])) and not any(x['group']=='CAD' for x in projects.files(b['id'])))
            check('Active CAD selection is per project',projects.get(a['id'])['active_cad'] is not None and projects.get(b['id'])['active_cad'] is None)
            projects.cad_tool(a['id'],'openvsp');projects.cad_tool(b['id'],'freecad')
            check('CAD program choice persists per project',projects.get(a['id'])['cad_tool']=='openvsp' and projects.get(b['id'])['cad_tool']=='freecad')
            try:projects.checked_file(b['id'],imported['path']);rejected=False
            except ValueError:rejected=True
            check('Other project file rejected',rejected)
            projects.save_draft(a['id'],{'project_id':a['id'],'request':'A projesinin taslağı'})
            projects.save_draft(b['id'],{'project_id':b['id'],'request':'B projesinin taslağı'})
            check('Drafts survive project switching',projects.draft(a['id'])['request']=='A projesinin taslağı' and projects.draft(b['id'])['request']=='B projesinin taslağı')
            imported_path=projects.resolve(imported['path']);imported_path.write_bytes(imported_path.read_bytes()+b'\n')
            check('Modified active CAD is flagged',projects.summary(a['id'])['active_cad_changed'])
            check('Unprepared CFD cannot run a demo in real project',not projects.run_plan(a['id'],'cfd')['ready'])
            try:projects.get('../../outside');rejected=False
            except ValueError:rejected=True
            check('Project traversal rejected',rejected)
            # Run the actual submit command against an isolated copy of the workspace code.
            agent=temp/'work/agent';agent.mkdir(parents=True,exist_ok=True)
            for name in ['project.py','projects.py','intake.py','report.py']:shutil.copy2(ROOT/'work/agent'/name,agent/name)
            payload={'project_id':a['id'],'request':'Bu projenin kanat adaylarını araştır ve karşılaştır','constraints':{'target_speed_kmh':'108'}}
            inbox=temp/'request.json';projects.write(inbox,payload)
            result=subprocess.run([sys.executable,'-X','utf8',str(agent/'project.py'),'submit',str(inbox),'--save-only'],cwd=temp,capture_output=True,text=True,encoding='utf-8')
            (folder/'isolated_submit.log').write_text(result.stdout+result.stderr,encoding='utf-8')
            tasks=list((temp/'outputs/data/tasks').glob('*.json'));saved=projects.read(tasks[0]) if tasks else {}
            check('Actual submit saves under selected project context',result.returncode==0 and saved.get('project_id')==a['id'] and saved.get('project_output_root')==a['artifact_root'])
            check('Task snapshots active CAD and detects changed file',saved.get('project_snapshot',{}).get('active_cad',{}).get('path')==imported['path'] and saved.get('active_cad_changed_since_selection') is True and saved.get('input_sha256',{}).get(imported['path'])==projects.sha(imported_path))
            normalized=projects.read(temp/saved['structured_request']) if saved else {}
            check('Saved SI constraints and seven tracked steps',normalized.get('inputs',{}).get('target_speed',{}).get('value')==30 and len(saved.get('pipeline_steps',[]))==7)
            with patch.object(project,'ROOT',temp),patch.object(project,'OUT',temp/'outputs'):
                setup=temp/'work/setup';setup.mkdir();projects.write(setup/'tool_config.json',{'codex_cli':str(ROOT/'work/setup/tool_config.json')})
                # No process is started; inspect what would be sent to the agent.
                launch=project.launch(tasks[0],dry=True)
                check('Agent receives selected project folders',a['artifact_root'] in launch['prompt'] and a['id'] in launch['prompt'])
            # Exercise the native CAD builder with a separate output root.
            cadout=temp/'scoped_cad'
            for name in ['cad','data','reports','simulations','plots']:(cadout/name).mkdir(parents=True)
            shutil.copy2(ROOT/'outputs/data/parametric_wing_case.json',cadout/'data/parametric_wing_case.json')
            env=dict(os.environ,UAV_OUTPUT_ROOT=str(cadout))
            with (folder/'scoped_cad.log').open('w') as log:
                p=subprocess.run([str(ROOT/'.venv-cad/Scripts/python.exe'),'-X','utf8',str(ROOT/'work/geometry/parametric_wing.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
            report=projects.read(cadout/'reports/parametric_cad_qualification.json') if (cadout/'reports/parametric_cad_qualification.json').exists() else {}
            check('Actual CAD generation respects scoped output root',p.returncode==0 and report.get('passed') and (cadout/'cad/parametric_wing/envelope.step').exists())
    check('Original CAD evidence untouched',projects.sha(ROOT/'outputs/cad/parametric_wing/envelope.step')==original)
    exe=ROOT/'outputs/Muhendislik-Merkezi.exe'
    p=subprocess.run([str(exe),'--probe'],cwd=ROOT,timeout=15)
    check('Native EXE locates project dependencies',p.returncode==0 and projects.read(ROOT/'outputs/reports/exe_launcher_probe.json')['passed'])
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,
        'scope':'Real project isolation and routing checks, actual CAD run in temporary scope; agent invocation inspected without starting an LLM session'}
    projects.write(ROOT/'outputs/reports/project_interface_checks.json',result);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
