"""Dimensioned modifications to a 664-face reference housing, checked analytically."""
import json,os,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
PID=json.loads((ROOT/'work/validation/projects.json').read_text())['cad'];OUT=ROOT/'outputs/projects'/PID
SOURCE=next((ROOT/'work/validation/sources/nist_ctc_definitions').rglob('nist_ctc_02_asme1_rc.stp'))
def main():
    original=cq.importers.importStep(str(SOURCE)).solids().val();s=original
    previous=OUT/'reports/ctc02_modification.json'
    if previous.exists() and not json.loads(previous.read_text())['passed']:
        failed=ROOT/'work/validation/rejected';failed.mkdir(exist_ok=True);(failed/'ctc02_initial_measurement.json').write_bytes(previous.read_bytes())
    # NIST side walls have 2-degree draft and 40 mm NORMAL thickness, not x-direction thickness.
    axis_thickness=80/math.cos(math.radians(2))
    spec={'units':'mm','kind':'Explicit test modification; not part of NIST original specification','source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'axes':[{'origin':[-500,y,-180],'direction':[1,0,0],'diameter':16,'length':1000} for y in [600,650]],'wall_normal_thickness_mm':40,'wall_draft_deg':2,'expected_parallel_wall_thickness_along_axis_mm':axis_thickness,'analytic_removed_volume_mm3':2*math.pi*8**2*axis_thickness}
    for h in spec['axes']:
        tool=cq.Solid.makeCylinder(h['diameter']/2,h['length'],cq.Vector(h['origin']),cq.Vector(h['direction']));s=s.cut(tool).clean()
    dest=OUT/'cad/modified';dest.mkdir(exist_ok=True);path=dest/'ctc02_four_wall_ports.step';cq.exporters.export(s,str(path));delivered=cq.importers.importStep(str(path)).solids().val()
    bores=[]
    for f in delivered.Faces():
        if f.geomType()=='CYLINDER':
            c=BRepAdaptor_Surface(f.wrapped,True).Cylinder();d=c.Axis().Direction();p=c.Location()
            if abs(d.X())>.999999 and abs(c.Radius()-8)<1e-5 and abs(p.Z()+180)<1e-5:bores.append({'diameter_mm':2*c.Radius(),'axis':[d.X(),d.Y(),d.Z()],'origin_mm':[p.X(),p.Y(),p.Z()]})
    control=ROOT/'work/validation/ctc02_roundtrip_control.step';cq.exporters.export(original,str(control));baseline=cq.importers.importStep(str(control)).solids().val()
    rough=original.Volume()-delivered.Volume();raw=original.Volume(1e-9)-delivered.Volume(1e-9)
    removed=baseline.Volume(1e-9)-delivered.Volume(1e-9);err=abs(removed/spec['analytic_removed_volume_mm3']-1)
    displacement=max(cq.Vertex.makeVertex(*v.Center().toTuple()).distance(baseline) for v in original.Vertices())
    extra=sum(v.Volume() for v in delivered.cut(original,tol=1e-6).Solids())
    row={'source_faces':len(original.Faces()),'delivered_faces':len(delivered.Faces()),'valid':delivered.isValid(),'solids':len(delivered.Solids()),'bores':bores,'measured_removed_volume_mm3':removed,'raw_import_to_delivered_volume_change_mm3':raw,'default_integration_volume_difference_mm3':rough,'mass_integration_relative_tolerance':1e-9,'roundtrip_control_volume_change_mm3':original.Volume(1e-9)-baseline.Volume(1e-9),'roundtrip_control_max_vertex_displacement_mm':displacement,'volume_comparison_method':'Matched no-op STEP export/reimport baseline; raw difference also retained','analytic_removed_volume_mm3':spec['analytic_removed_volume_mm3'],'removed_volume_relative_error':err,'unrequested_added_material_mm3':extra,'passed':delivered.isValid() and len(delivered.Solids())==1 and len(bores)==4 and err<1e-4 and extra<1e-4 and displacement<1e-4,'acceptance_limits':{'diameter_axis_coordinate_mm':1e-5,'removed_volume_relative':1e-4,'unrequested_added_material_mm3':1e-4,'roundtrip_max_vertex_displacement_mm':1e-4},'scope':'Source housing imported and explicitly modified; original housing was not redrawn from a PDF. Only the physical solid is measured; loose source construction geometry is excluded.','initial_failed_measurement':'Retained. Corrected normal/axis thickness and controlled STEP roundtrip integration shift; geometry/acceptance thresholds were not loosened.'}
    (OUT/'data/ctc02_port_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(OUT/'reports/ctc02_modification.json').write_text(json.dumps(row,indent=2),encoding='utf-8');print(json.dumps(row,indent=2))
if __name__=='__main__':main()
