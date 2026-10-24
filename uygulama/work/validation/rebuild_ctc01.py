"""Reference-assisted, feature-based reconstruction of NIST CTC01.
Measured analytic sketches are serialized first; imported faces/solids are never exported as reconstruction.
"""
import json,os,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
PID=json.loads((ROOT/'work/validation/projects.json').read_text())['cad'];OUT=ROOT/'outputs/projects'/PID
SOURCE=next((ROOT/'work/validation/sources/nist_ctc_definitions').rglob('nist_ctc_01_asme1_rd.stp'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def xyz(v):return [v.X(),v.Y(),v.Z()]
def sketch(w):
    edges=[]
    for e in w.Edges():
        t=e.geomType();a=e.positionAt(0).toTuple();b=e.positionAt(1).toTuple()
        if t=='LINE':edges.append({'type':'line','start':a,'end':b})
        elif t=='CIRCLE':
            if cq.Vector(a).sub(cq.Vector(b)).Length<1e-7:
                c=BRepAdaptor_Curve(e.wrapped).Circle();edges.append({'type':'circle','radius':c.Radius(),'center':xyz(c.Location()),'normal':xyz(c.Axis().Direction())})
            else:edges.append({'type':'arc','start':a,'middle':e.positionAt(.5).toTuple(),'end':b})
        else:raise ValueError('Unqualified sketch curve '+t)
    return edges
def wire(data):
    edges=[]
    for e in data:
        if e['type']=='line':edges.append(cq.Edge.makeLine(cq.Vector(e['start']),cq.Vector(e['end'])))
        elif e['type']=='arc':edges.append(cq.Edge.makeThreePointArc(cq.Vector(e['start']),cq.Vector(e['middle']),cq.Vector(e['end'])))
        else:edges.append(cq.Edge.makeCircle(e['radius'],cq.Vector(e['center']),cq.Vector(e['normal'])))
    return cq.Wire.assembleEdges(edges)
def face_data(f,exclude_center=False):
    inner=f.innerWires()
    if exclude_center:inner=[w for w in inner if abs(w.Center().x)>100 or abs(w.Center().y)>100]
    return {'outer':sketch(f.outerWire()),'inner':[sketch(w) for w in inner]}
def prism(d,vector):return cq.Solid.extrudeLinear(wire(d['outer']),[wire(w) for w in d['inner']],cq.Vector(vector))
def extract():
    s=cq.importers.importStep(str(SOURCE)).val();planes=[f for f in s.Faces() if f.geomType()=='PLANE']
    top=next(f for f in planes if f.Area()>200000 and abs(f.Center().z)<1e-5)
    feet=[f for f in planes if abs(f.Center().z+100)<1e-5 and f.Area()>10000]
    engrave=[f for f in planes if abs(f.Center().x-398)<1e-5 and f.normalAt().x>.99]
    parameters={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'units':'mm','method':'Analytic sketch coordinates measured from published reference; independent new edges/prisms/booleans. This is not blind drawing inference.',
        'plate_thickness':50,'feet_height':50,'root_fillet':10,'boss_across_flats':100,'boss_height':50,'boss_top_chamfer':5,'boss_base_fillet':5,'blind_holes':{'x':[-30,30],'start_y':-125,'end_y':-80,'z':-25,'diameter':20,'drill_half_angle_rad':1.0297442575},'plate_sketch':face_data(top,True),'feet_sketches':[face_data(f) for f in feet],'engraving_sketches':[face_data(f) for f in engrave]}
    save(OUT/'data/ctc01_rebuild_parameters.json',parameters);return parameters
def build(p,boss_height=None):
    steps=[];s=prism(p['plate_sketch'],[0,0,-p['plate_thickness']]);steps.append(('Plate_from_analytic_sketch',s))
    for d in p['feet_sketches']:s=s.fuse(prism(d,[0,0,p['feet_height']])).clean()
    steps.append(('Four_feet',s))
    edges=[]
    for e in s.Edges():
        c=e.Center();b=e.BoundingBox()
        if e.geomType()=='LINE' and abs(c.z+50)<1e-5 and b.zlen<1e-5:
            if (abs(abs(c.y)-125)<1e-5 and 240<abs(c.x)<401) or (abs(abs(c.x)-250)<1e-5 and 115<abs(c.y)<151):edges.append(e)
    print('FOOT_JOIN_EDGES',[(e.Center().toTuple(),e.Length()) for e in edges],flush=True)
    if len(edges)!=8:raise ValueError('Expected 8 concave foot joins')
    s=s.fillet(p['root_fillet'],edges).clean();steps.append(('Foot_root_fillets',s))
    radius=p['boss_across_flats']/math.sqrt(3);pts=[(radius*math.cos(math.radians(30+60*i)),radius*math.sin(math.radians(30+60*i))) for i in range(6)]
    height=boss_height or p['boss_height'];boss=cq.Workplane('XY').polyline(pts).close().extrude(height).edges('>Z').chamfer(p['boss_top_chamfer']).val()
    s=s.fuse(boss).clean();root_edges=[e for e in s.Edges() if e.geomType()=='LINE' and abs(e.Center().z)<1e-5 and abs(e.Center().x)<70 and abs(e.Center().y)<70]
    if len(root_edges)!=6:raise ValueError('Expected six boss root edges')
    s=s.fillet(p['boss_base_fillet'],root_edges).clean();steps.append(('Chamfered_hex_boss_and_root_fillet',s))
    h=p['blind_holes'];r=h['diameter']/2;depth=h['end_y']-h['start_y'];tip=r/math.tan(h['drill_half_angle_rad'])
    for x in h['x']:
        bore=cq.Solid.makeCylinder(r,depth,cq.Vector(x,h['start_y'],h['z']),cq.Vector(0,1,0));cone=cq.Solid.makeCone(r,0,tip,cq.Vector(x,h['end_y'],h['z']),cq.Vector(0,1,0));s=s.cut(bore.fuse(cone)).clean()
    steps.append(('Two_blind_cross_drilled_holes',s))
    for d in p['engraving_sketches']:s=s.cut(prism(d,[2.1,0,0])).clean()
    steps.append(('Measured_NIST_marking_pockets',s))
    return s,steps
def main():
    dest=OUT/'cad/reconstructed';dest.mkdir(parents=True,exist_ok=True);case=OUT/'data/ctc01_rebuild_parameters.json';p=json.loads(case.read_text()) if case.exists() else extract();s,steps=build(p)
    for name,shape in steps:print(name,shape.isValid(),len(shape.Solids()),shape.Volume(),flush=True)
    cq.exporters.export(s,str(dest/'ctc01_reconstructed.step'))
    # Compare the delivered STEP solids; mixed Compound tolerances can make coincident cuts fail.
    ref=cq.importers.importStep(str(SOURCE)).solids().val();s=cq.importers.importStep(str(dest/'ctc01_reconstructed.step')).solids().val()
    missing=sum(v.Volume() for v in ref.cut(s,tol=1e-6).Solids());extra=sum(v.Volume() for v in s.cut(ref,tol=1e-6).Solids());ratio=(missing+extra)/ref.Volume()
    distances=[cq.Vertex.makeVertex(*v.Center().toTuple()).distance(ref) for v in s.Vertices()]
    distances += [cq.Vertex.makeVertex(*v.Center().toTuple()).distance(s) for v in ref.Vertices()]
    result={'source':str(SOURCE.relative_to(ROOT)),'nominal_valid':s.isValid(),'solid_count':len(s.Solids()),'reference_volume_mm3':ref.Volume(),'reconstructed_volume_mm3':s.Volume(),'volume_relative_error':abs(s.Volume()/ref.Volume()-1),'missing_mm3':missing,'extra_mm3':extra,'symmetric_difference_relative':ratio,'boolean_fuzzy_tolerance_mm':1e-6,'bidirectional_vertex_surface_max_distance_mm':max(distances),'vertex_samples':len(distances),'shape_match_passed':ratio<1e-6 and abs(s.Volume()/ref.Volume()-1)<1e-6 and max(distances)<1e-4,'source_assistance':'CAD-referenced measured sketches and explicit features; not a blind drawing-to-CAD benchmark','steps':[{'name':n,'valid':a.isValid(),'solids':len(a.Solids()),'volume_mm3':a.Volume()} for n,a in steps]}
    changed,_=build(p,55);cq.exporters.export(changed,str(dest/'ctc01_boss_height55.step'))
    expected_delta=math.sqrt(3)/2*p['boss_across_flats']**2*5
    box=changed.BoundingBox();result['parameter_variant']={'boss_height_mm':55,'max_z_mm':box.zmax,'delta_volume_mm3':changed.Volume()-s.Volume(),'expected_delta_volume_mm3':expected_delta,'passed':changed.isValid() and abs(box.zmax-55)<1e-6 and abs((changed.Volume()-s.Volume())/expected_delta-1)<1e-6}
    save(OUT/'reports/ctc01_reconstruction.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
