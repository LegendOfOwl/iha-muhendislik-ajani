"""Agent correction of failed local-model drafts, independently rechecked in two CAD tools."""
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/models'))
from benchmark import K_CASES
from validate_geometry import mesh_metrics
import cadquery as cq

OUT=ROOT/'outputs'
folder=OUT/'cad/checked_parts'; folder.mkdir(parents=True,exist_ok=True)
install=json.loads((ROOT/'work/setup/k_model_install.json').read_text())
programs={
 'box':'cube([40,30,8],center=true);',
 'hole_plate':'difference(){ cube([40,30,8],center=true); cylinder(d=10,h=10,center=true,$fn=128); }',
 'spacer':'difference(){ cylinder(d=20,h=12,center=true,$fn=128); cylinder(d=6,h=14,center=true,$fn=128); }',
}
checks=[]
for case in K_CASES:
    name=case['id']; source=folder/(name+'.scad'); source.write_text('// Codex correction; all lengths are mm. Synthetic test requirement.\n'+programs[name]+'\n')
    with (ROOT/'work/cad'/(name+'_openscad.log')).open('w') as log:
        p=subprocess.run([install['executable'],'-o',str(folder/(name+'.stl')),str(source)],stdout=log,stderr=subprocess.STDOUT,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
    metric=mesh_metrics(folder/(name+'.stl'),case)
    if name=='box': part=cq.Workplane('XY').box(40,30,8)
    elif name=='hole_plate': part=cq.Workplane('XY').box(40,30,8).faces('>Z').workplane().hole(10)
    else: part=cq.Workplane('XY').circle(10).circle(3).extrude(12).translate((0,0,-6))
    cq.exporters.export(part,str(folder/(name+'.step')))
    reopened=cq.importers.importStep(str(folder/(name+'.step'))).val()
    step_ok=reopened.isValid() and len(reopened.Solids())==1 and abs(reopened.Volume()/case['volume_mm3']-1)<1e-7
    metric.update(part=name,native_OpenSCAD_exit_code=p.returncode,STEP_valid=step_ok,expected_volume_mm3=case['volume_mm3'],
                  source='Agent-authored correction, not specialized-model self-repair')
    checks.append({'name':name+' corrected OpenSCAD + independent CadQuery/STEP','passed':p.returncode==0 and metric['geometry_accepted'] and step_ok,'evidence':metric})
    print(('PASS: ' if checks[-1]['passed'] else 'FAIL: ')+name+' corrected part',flush=True)
report={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(a['passed'] for a in checks),'checks':checks,
        'scope':'Closed-loop correction example: model draft -> dimensional rejection -> explicit agent correction -> native export -> geometry recheck',
        'limits':['All dimensions are synthetic test requirements','Not a UAV component or strength assessment','Not a claim that the 1B model corrected itself']}
(OUT/'reports/checked_parts_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
