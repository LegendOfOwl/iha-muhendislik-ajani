"""Native FreeCAD documents and editable Boolean features, executed in FreeCADCmd."""
import json,math,os
from pathlib import Path
import FreeCAD as App
import Part
ROOT=Path(os.environ['UAV_VALIDATION_ROOT']);ids=json.loads((ROOT/'work/validation/projects.json').read_text());OUT=ROOT/'outputs/projects'/ids['cad']
def source(name):
    p=next((ROOT/'work/validation/sources/nist_ctc_definitions').rglob(name+'.stp'));s=Part.Shape();s.read(str(p));return s.Solids[0]
def body(doc,shape):o=doc.addObject('Part::Feature','ReferenceSolid');o.Label='NIST source physical solid - credited reference';o.Shape=shape;return o
def cylinder(doc,name,radius,height,point,axis=App.Vector(0,0,1)):
    o=doc.addObject('Part::Cylinder',name);o.Radius=radius;o.Height=height;o.Placement=App.Placement(App.Vector(*point),App.Rotation(App.Vector(0,0,1),axis));return o
def cut(doc,name,base,tool):
    o=doc.addObject('Part::Cut',name);o.Base=base;o.Tool=tool;return o
def record(shape):return {'valid':shape.isValid(),'solids':len(shape.Solids),'faces':len(shape.Faces),'volume_mm3':shape.Volume,'bbox_mm':[shape.BoundBox.XMin,shape.BoundBox.YMin,shape.BoundBox.ZMin,shape.BoundBox.XMax,shape.BoundBox.YMax,shape.BoundBox.ZMax]}
def main():
    results=[]
    # Reopen the independently reconstructed STEP as a real native document.
    d=App.newDocument('CTC01_Reconstructed');s=Part.Shape();s.read(str(OUT/'cad/reconstructed/ctc01_reconstructed.step'));o=body(d,s.Solids[0]);o.Label='CTC01 rebuilt from measured sketches and explicit features';o.addProperty('App::PropertyString','ParameterFile');o.ParameterFile=str(OUT/'data/ctc01_rebuild_parameters.json');d.recompute();p=OUT/'cad/reconstructed/ctc01_reconstructed.FCStd';d.saveAs(str(p));results.append({'case':'CTC01 nominal native readback',**record(o.Shape)});App.closeDocument(d.Name)
    d=App.openDocument(str(p));assert d.getObject('ReferenceSolid').Shape.isValid();App.closeDocument(d.Name)
    # Housing: full native editable cylinders and Cut features, not only a frozen STEP.
    d=App.newDocument('CTC02_Ports');b=body(d,source('nist_ctc_02_asme1_rc'));current=b;tools=[]
    for i,y in enumerate([600,650],1):
        tool=cylinder(d,'PortAxis'+str(i),8,1000,[-500,y,-180],App.Vector(1,0,0));current=cut(d,'CutPort'+str(i),current,tool);tools.append(tool)
    d.recompute();nominal=record(current.Shape);before=current.Shape.Volume
    tools[0].Radius=9;d.recompute();changed=current.Shape.Volume;expected=math.pi*(9**2-8**2)*80/math.cos(math.radians(2));parameter_error=abs((before-changed)/expected-1)
    tools[0].Radius=8;d.recompute();path=OUT/'cad/modified/ctc02_native_ports.FCStd';d.saveAs(str(path));Part.export([current],str(OUT/'cad/modified/ctc02_native_ports.step'))
    results.append({'case':'CTC02 native parametric ports',**nominal,'radius_change_8_to_9_removed_mm3':before-changed,'analytic_expected_mm3':expected,'radius_change_relative_error':parameter_error,'parameter_recompute_passed':parameter_error<1e-4,'native_feature_types':[o.TypeId for o in d.Objects]});App.closeDocument(d.Name)
    d=App.openDocument(str(path));assert d.getObject('CutPort2').Shape.isValid() and abs(d.getObject('PortAxis1').Radius.Value-8)<1e-9;App.closeDocument(d.Name)
    d=App.newDocument('CTC05_Grooves');current=body(d,source('nist_ctc_05_asme1_rd'));inners=[]
    for i,(z,width,depth) in enumerate([(360,8,2),(410,12,3)],1):
        outer=cylinder(d,'GrooveOuter'+str(i),36.75,width,[0,0,z]);inner=cylinder(d,'GrooveRoot'+str(i),31.75-depth,width,[0,0,z]);ring=cut(d,'GrooveTool'+str(i),outer,inner);current=cut(d,'CutGroove'+str(i),current,ring);inners.append(inner)
    key=d.addObject('Part::Box','KeywayTool');key.Length=12;key.Width=6;key.Height=30;key.Placement.Base=App.Vector(28.75,-3,430);current=cut(d,'CutKeyway',current,key);d.recompute();nominal=record(current.Shape);before=current.Shape.Volume
    inners[0].Radius=29.25;d.recompute();changed=current.Shape.Volume;expected=math.pi*(29.75**2-29.25**2)*8;error=abs((before-changed)/expected-1)
    inners[0].Radius=29.75;d.recompute();path=OUT/'cad/modified/ctc05_native_grooves.FCStd';d.saveAs(str(path));Part.export([current],str(OUT/'cad/modified/ctc05_native_grooves.step'))
    results.append({'case':'CTC05 native grooves and keyway',**nominal,'groove_radius_change_removed_mm3':before-changed,'analytic_expected_mm3':expected,'radius_change_relative_error':error,'parameter_recompute_passed':error<1e-4,'native_feature_types':[o.TypeId for o in d.Objects]});App.closeDocument(d.Name)
    d=App.openDocument(str(path));assert d.getObject('CutKeyway').Shape.isValid();App.closeDocument(d.Name)
    result={'version':App.Version(),'results':results,'passed':all(r['valid'] and r['solids']==1 and r.get('parameter_recompute_passed',True) for r in results),'scope':'Native CAD geometry and parameter propagation; not GD&T/manufacturing or structural acceptance'}
    (OUT/'reports/freecad_complex_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2));print('COMPLEX_NATIVE_CAD_COMPLETE',flush=True)
main()
