"""Separate runtime success from geometric acceptance for specialized CAD models."""
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
import vtk

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'
def response(raw):
    if '\n> ' in raw: raw=raw.split('\n> ',1)[1].split('\n',1)[1]
    raw=raw.split('[ Prompt:',1)[0].strip()
    fences=re.findall(r'```(?:python|scad|openscad)?\s*\n(.*?)```',raw,re.S)
    if fences: return fences[0].strip()
    if raw.startswith('```'): raw=raw.split('\n',1)[1]
    return raw.strip()
def mesh_metrics(path,case):
    reader=vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    mesh=reader.GetOutput()
    if mesh.GetNumberOfPoints()==0: raise ValueError('Empty STL')
    bounds=np.array(mesh.GetBounds()).reshape(3,2)
    bbox=bounds[:,1]-bounds[:,0]; center=bounds.mean(axis=1)
    mass=vtk.vtkMassProperties(); mass.SetInputData(mesh); mass.Update()
    edges=vtk.vtkFeatureEdges(); edges.SetInputData(mesh); edges.FeatureEdgesOff(); edges.ManifoldEdgesOff(); edges.BoundaryEdgesOn(); edges.NonManifoldEdgesOn(); edges.Update()
    expected=np.asarray(case['bbox_mm']); bbox_error=float(np.max(np.abs(bbox/expected-1)))
    volume=float(mass.GetVolume()); volume_error=abs(volume/case['volume_mm3']-1)
    centering=True
    if case.get('center_at_origin',case['id'] in ['box','hole_plate']): centering=bool(np.max(np.abs(center))<1e-3)
    query=[]; expected_inside=[]
    z=float(center[2])
    if case['id']=='hole_plate': query=[(0,0,z),(4.5,0,z),(5.5,0,z),(15,0,z)]; expected_inside=[False,False,True,True]
    if case['id']=='spacer': query=[(0,0,z),(2.7,0,z),(3.3,0,z),(9.5,0,z),(10.5,0,z)]; expected_inside=[False,False,True,True,False]
    if 'probes_mm' in case:
        query=case['probes_mm']; expected_inside=case['expected_inside']
    interior=[]
    if query:
        pts=vtk.vtkPoints()
        for xyz in query: pts.InsertNextPoint(xyz)
        cloud=vtk.vtkPolyData(); cloud.SetPoints(pts)
        enclosed=vtk.vtkSelectEnclosedPoints(); enclosed.SetInputData(cloud); enclosed.SetSurfaceData(mesh); enclosed.SetTolerance(1e-6); enclosed.Update()
        interior=[bool(enclosed.IsInside(i)) for i in range(len(query))]
    accepted=bbox_error<.01 and volume_error<.01 and centering and interior==expected_inside and edges.GetOutput().GetNumberOfCells()==0
    return {'bbox_mm':bbox.tolist(),'bbox_center_mm':center.tolist(),'volume_mm3':volume,
            'max_relative_bbox_error':bbox_error,'relative_volume_error':volume_error,'required_centering_met':centering,
            'hole_probe_expected_inside':expected_inside,'hole_probe_actual_inside':interior,
            'open_or_nonmanifold_edges':edges.GetOutput().GetNumberOfCells(),'geometry_accepted':bool(accepted)}
def validate(run):
    records=json.loads((run/'generations.json').read_text(encoding='utf-8'))
    checks=[]; results=[]
    kmeta=json.loads((ROOT/'work/setup/k_model_install.json').read_text())
    for record in records:
        folder=Path(record['folder'])
        raw=(folder/'stdout.txt').read_text(encoding='utf-8',errors='replace')
        code=response(raw)
        perf=re.search(r'Generation:\s*([\d.]+) t/s',raw)
        record['reported_generation_tok_s']=float(perf[1]) if perf else None
        record['inference_completed']=record['exit_code']==0
        checks.append({'name':record['model']+' '+record.get('id','views')+' native inference','passed':record['exit_code']==0})
        try:
            if record['model']=='k':
                record['expected_bbox_mm']=list(record['bbox_mm'])
                record['expected_volume_mm3']=record['volume_mm3']
                (folder/'generated.scad').write_text(code,encoding='utf-8')
                if re.search(r'\b(import|surface|include|use)\b',re.sub(r'//[^\n]*','',code)): raise ValueError('External-file OpenSCAD operation rejected')
                with (folder/'openscad.log').open('w',encoding='utf-8') as log:
                    p=subprocess.run([kmeta['executable'],'-o',str(folder/'generated.stl'),str(folder/'generated.scad')],
                        cwd=folder,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
                record['openscad_exit_code']=p.returncode
                record['openscad_warnings']=[line for line in (folder/'openscad.log').read_text(errors='replace').splitlines() if 'WARNING' in line or 'ERROR' in line]
                if p.returncode or not (folder/'generated.stl').exists(): raise ValueError('Native OpenSCAD export failed')
                record.update(mesh_metrics(folder/'generated.stl',record))
                record['cad_created']=True
            else:
                from cad_worker import checked_tree
                (folder/'generated.py').write_text(code,encoding='utf-8')
                checked_tree(code)
                with (folder/'cad_worker.log').open('w',encoding='utf-8') as log:
                    p=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'work/models/cad_worker.py'),str(folder)],
                       cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
                if p.returncode: raise ValueError('CadQuery execution failed: see cad_worker.log')
                record.update(json.loads((folder/'cad_metrics.json').read_text()))
                record.update(cad_created=True,geometry_accepted=False,acceptance_note='Valid shape still requires normalized geometry comparison; absolute scale cannot come from images alone.')
        except Exception as exc:
            record.update(cad_created=False,geometry_accepted=False,geometry_error=f'{type(exc).__name__}: {exc}')
        results.append(record)
        print(f'{record["model"]} {record.get("id","views")}: inference={record["inference_completed"]}, CAD={record["cad_created"]}, requested geometry={record["geometry_accepted"]}',flush=True)
    report_path=OUT/'reports/cad_model_benchmark.json'
    previous=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    by_id={(r['model'],r.get('id','views')):r for r in previous.get('results',[])}
    by_id.update({(r['model'],r.get('id','views')):r for r in results})
    merged=list(by_id.values())
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(r['inference_completed'] for r in merged),
            'installation_inference_passed':all(r['inference_completed'] for r in merged),
            'quality_passed':all(r['geometry_accepted'] for r in merged),
            'accepted_cases':sum(r['geometry_accepted'] for r in merged),'total_cases':len(merged),
            'results':merged,'checks':[{'name':r['model']+' '+r.get('id','views')+' inference','passed':r['inference_completed']} for r in merged],
            'hardware':'NVIDIA RTX 4080 Laptop, 12282 MiB; native Windows',
            'scope':'Small local quantized-model probe; not vendor benchmark reproduction or broad model ranking',
            'acceptance':'K: bbox and volume within 1%, required centering, bore probes and closed STL. Zero: executable valid solid plus shape comparison required.',
            'limits':['Q6_K Zero-to-CAD is a third-party conversion; this does not establish original BF16 quality',
                      'K-1B Q8_0 was not corrected by the agent; generated code preserved verbatim',
                      'Reported tok/s is the runtime generation metric, excluding loading; end-to-end seconds recorded separately',
                      'Short local runs; cold-start and cache-controlled performance were not benchmarked',
                      'Specialized-model output is an unverified draft and must pass task-specific checks']}
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    for name,meta_path in [('k','k_model_install.json'),('zero','cad_model_install.json')]:
        p=ROOT/'work/setup'/meta_path; meta=json.loads(p.read_text())
        subset=[r for r in merged if r['model']==name]
        if subset:
            meta.update(verified_inference=all(r['inference_completed'] for r in subset),
                        geometry_accepted_cases=sum(r['geometry_accepted'] for r in subset),
                        engineering_auto_use=False,test_report='outputs/reports/cad_model_benchmark.json')
            p.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return 0 if result['installation_inference_passed'] else 1
