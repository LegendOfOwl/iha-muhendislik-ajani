"""Measure existing native STEP cylinders; keep generation evidence unchanged."""
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'work/geometry'))
from parametric_wing import measure_bores
import cadquery as cq
def main():
    cad=json.loads((OUT/'reports/parametric_cad_qualification.json').read_text()); results=[]
    for row in cad['ribs']:
        shape=cq.importers.importStep(row['path']).val(); m=measure_bores(shape,row['probes'])
        results.append({'path':row['path'],'measurement':m})
    wrong_radius=copy.deepcopy(cad['ribs'][0]['probes']); wrong_radius[0]['diameter_mm']*=2
    wrong_offset=copy.deepcopy(cad['ribs'][0]['probes']); wrong_offset[0]['center_mm'][0]+=3
    first=cq.importers.importStep(cad['ribs'][0]['path']).val()
    controls={'wrong_diameter_rejected':not measure_bores(first,wrong_radius)['passed'],
              'wrong_position_rejected':not measure_bores(first,wrong_offset)['passed']}
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(r['measurement']['passed'] for r in results) and all(controls.values()),
         'results':results,'negative_controls':controls,'scope':'Four existing exported STEP ribs, eight cylinder diameters/axes and centerline void probes'}
    (OUT/'reports/step_bore_measurements.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':obj['passed'],'ribs':len(results),'controls':controls},ensure_ascii=False)); return 0 if obj['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
