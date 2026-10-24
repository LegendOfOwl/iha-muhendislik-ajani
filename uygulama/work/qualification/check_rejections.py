"""Negative controls: malformed profile/units/geometry must stop before CAD output."""
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'work/geometry'))
from parametric_wing import profile

def main():
    folder=ROOT/'work/qualification/negative_controls'; folder.mkdir(exist_ok=True)
    base=json.loads((OUT/'data/parametric_wing_case.json').read_text())
    checks=[]
    for name,change,expected in [
        ('mm_units',lambda c:c['units'].update(length='mm'),'Explicit m/deg'),
        ('zero_chord',lambda c:c['stations'][1].update(chord=0),'Positive chord'),
        ('station_reversal',lambda c:c['stations'][1].update(y=-.1),'strictly increasing'),
        ('nonfinite_station',lambda c:c['stations'][1].update(x_le=float('nan')),'finite stations')]:
        cfg=copy.deepcopy(base); change(cfg); p=folder/(name+'.json'); p.write_text(json.dumps(cfg))
        run=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'work/geometry/parametric_wing.py'),'--case',str(p)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        (folder/(name+'.log')).write_text(run.stdout+run.stderr,encoding='utf-8')
        checks.append({'name':name,'passed':run.returncode!=0 and expected in run.stderr,'exit_code':run.returncode})
    src=OUT/'data/airfoils/naca2412.dat'; xy,_,_=profile(src)
    for name,data in [('reversed_surface',xy[::-1]),('unnormalized_profile',xy*1000)]:
        p=folder/(name+'.dat'); p.write_text('Invalid control\n'+'\n'.join(f'{x} {y}' for x,y in data))
        try: profile(p); passed=False; error=None
        except ValueError as exc: passed=True; error=str(exc)
        checks.append({'name':name,'passed':passed,'error':error})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,
            'scope':'Six deliberately invalid inputs. Does not prove rejection of every possible malformed CAD/airfoil.'}
    (OUT/'reports/input_rejection_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
