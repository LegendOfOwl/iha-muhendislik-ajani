"""Two circumferential grooves and a keyway on the source NIST flanged shaft."""
import json,os,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
PID=json.loads((ROOT/'work/validation/projects.json').read_text())['cad'];OUT=ROOT/'outputs/projects'/PID
SOURCE=next((ROOT/'work/validation/sources/nist_ctc_definitions').rglob('nist_ctc_05_asme1_rd.stp'))
def features(shape):
    found=[];key=False
    for f in shape.Faces():
        if f.geomType()=='CYLINDER':
            c=BRepAdaptor_Surface(f.wrapped,True).Cylinder();d=c.Axis().Direction();p=c.Location();b=f.BoundingBox()
            if abs(d.Z())>.999999 and abs(p.X())<1e-6 and abs(p.Y())<1e-6 and (abs(c.Radius()-29.75)<1e-6 or abs(c.Radius()-28.75)<1e-6):found.append({'radius_mm':c.Radius(),'z_range_mm':[b.zmin,b.zmax]})
        if f.geomType()=='PLANE' and abs(f.Center().x-28.75)<1e-5 and abs(f.Center().z-445)<1e-5 and abs(f.normalAt().x)>.999999:key=True
    return found,key
def main():
    original=cq.importers.importStep(str(SOURCE)).solids().val();s=original;R=31.75
    spec={'source':str(SOURCE.relative_to(ROOT)),'kind':'New dimensioned modification; not in original NIST definition','units':'mm','shaft_radius':R,'grooves':[{'z':360,'width':8,'depth':2},{'z':410,'width':12,'depth':3}],'keyway':{'z':430,'length':30,'width':6,'depth':3,'side':'+X'}}
    expected=0
    for g in spec['grooves']:
        outer=cq.Solid.makeCylinder(R+5,g['width'],cq.Vector(0,0,g['z']));inner=cq.Solid.makeCylinder(R-g['depth'],g['width'],cq.Vector(0,0,g['z']))
        s=s.cut(outer.cut(inner)).clean();expected+=math.pi*(R**2-(R-g['depth'])**2)*g['width']
    k=spec['keyway'];tool=cq.Workplane('XY').box(12,k['width'],k['length'],centered=False).translate((R-k['depth'],-k['width']/2,k['z'])).val();s=s.cut(tool).clean()
    a=k['width']/2;expected+=k['length']*(a*math.sqrt(R**2-a*a)+R**2*math.asin(a/R)-k['width']*(R-k['depth']))
    dest=OUT/'cad/modified';dest.mkdir(exist_ok=True);p=dest/'ctc05_grooves_and_keyway.step';cq.exporters.export(s,str(p));delivered=cq.importers.importStep(str(p)).solids().val()
    control=ROOT/'work/validation/ctc05_roundtrip_control.step';cq.exporters.export(original,str(control));baseline=cq.importers.importStep(str(control)).solids().val()
    removed=baseline.Volume(1e-9)-delivered.Volume(1e-9);error=abs(removed/expected-1);grooves,key=features(delivered);negative_grooves,negative_key=features(original)
    row={'source_faces':len(original.Faces()),'delivered_faces':len(delivered.Faces()),'valid':delivered.isValid(),'solids':len(delivered.Solids()),'groove_surfaces':grooves,'keyway_floor_found':key,'analytic_removed_volume_mm3':expected,'roundtrip_baseline_removed_volume_mm3':removed,'removed_volume_relative_error':error,'unmodified_source_rejected':len(negative_grooves)==0 and not negative_key,'passed':delivered.isValid() and len(delivered.Solids())==1 and len(grooves)>=2 and key and error<1e-4 and not negative_key,'acceptance_limits':{'coordinate_radius_mm':1e-5,'removed_volume_relative':1e-4},'scope':'Source flanged shaft modified with explicit new dimensions; source geometry is credited, not claimed as redrawn from scratch.'}
    (OUT/'data/ctc05_groove_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(OUT/'reports/ctc05_modification.json').write_text(json.dumps(row,indent=2),encoding='utf-8');print(json.dumps(row,indent=2))
if __name__=='__main__':main()
