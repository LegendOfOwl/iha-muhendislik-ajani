"""Reassess both native induced-force columns; never substitute a passing column silently."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('UAV_OUTPUT_ROOT',str(ROOT/'outputs')))

def audit(obj=None):
    report=OUT/'reports/complex_vlm_qualification.json'
    obj=obj or json.loads(report.read_text(encoding='utf-8'))
    rows=[]; histories=[]; evidence={}
    for result in obj['results']:
        folder=Path(result['folder'])
        for name in ['model.polar','model.history','case.vspscript','native.log']:
            p=folder/name
            if p.exists(): evidence[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        if not result.get('runtime_passed'): continue
        import sys
        sys.path.insert(0,str(ROOT/'work/native'))
        from run_external import history_table
        h=history_table(folder/'model.history')
        for _,group in h.groupby('AoA'):
            t=group.tail(2)
            histories.append({'level':result['level'],'alpha_deg':float(t.AoA.iloc[-1]),
                'delta_CLiw_last2':abs(float(t.CLiw.iloc[-1]-t.CLiw.iloc[-2])),
                'delta_CDiw_last2':abs(float(t.CDiw.iloc[-1]-t.CDiw.iloc[-2]))})
    if len(obj['results'])==2 and all(r.get('runtime_passed') for r in obj['results']):
        for med,fine in zip(obj['results'][0]['polar'],obj['results'][1]['polar']):
            rows.append({'alpha_deg':fine['AoA'],'medium_CL':med['CLtot'],'fine_CL':fine['CLtot'],
                'medium_surface_CDi':med['CDi'],'fine_surface_CDi':fine['CDi'],
                'medium_wake_CDiw':med['CDiw'],'fine_wake_CDiw':fine['CDiw'],
                'surface_CDi_relative_change':abs(fine['CDi']/med['CDi']-1),
                'wake_CDiw_relative_change':abs(fine['CDiw']/med['CDiw']-1),
                'fine_surface_wake_disagreement_relative_to_wake':abs(fine['CDi']/fine['CDiw']-1)})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'rows':rows,'wake_tail_checks':histories,
        'wake_CDiw_panel_screen_passed':bool(rows) and all(r['wake_CDiw_relative_change']<.10 for r in rows),
        'surface_CDi_panel_screen_passed':bool(rows) and all(r['surface_CDi_relative_change']<.10 for r in rows),
        'wake_tail_screen_passed':bool(histories) and all(r['delta_CLiw_last2']<5e-4 and r['delta_CDiw_last2']<5e-5 for r in histories),
        'overall_quality_passed':obj['quality_passed'],
        'interpretation':'CDi and CDiw are separate surface and wake induced-force estimates. Wake estimates are more stable in this run. The predeclared surface gate remains failed; neither result is a validated total aircraft drag.',
        'source':'https://github.com/OpenVSP/OpenVSP/blob/OpenVSP_3.55.0/src/vsp_aero/Solver/VSP_Solver.C',
        'developer_clarification':'https://groups.google.com/g/openvsp/c/7Bl7y1nGl1Q/m/J4QOlpNJBQAJ',
        'evidence_sha256':evidence}
    (OUT/'reports/complex_vlm_force_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['evidence_sha256','wake_tail_checks']},ensure_ascii=False,indent=2))
    return result

if __name__=='__main__': audit()
