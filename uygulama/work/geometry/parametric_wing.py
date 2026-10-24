"""Deterministic Selig-profile wing/rib builder. Geometry comes from an explicit contract, not model generation."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(os.environ.get('UAV_OUTPUT_ROOT',str(ROOT/'outputs')))
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import numpy as np
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def measure_bores(shape,expected):
    """Read cylinder radii and axes from the imported STEP, independently of cutters."""
    cylinders=[]
    for face in shape.Faces():
        if face.geomType()!='CYLINDER': continue
        cylinder=BRepAdaptor_Surface(face.wrapped).Cylinder(); p=cylinder.Location(); axis=cylinder.Axis().Direction()
        cylinders.append({'diameter_mm':2*cylinder.Radius(),'axis_point_mm':[p.X(),p.Y(),p.Z()],
                          'axis_direction':[axis.X(),axis.Y(),axis.Z()]})
    measurements=[]
    for bore in expected:
        center=bore['center_mm']; diameter=bore['diameter_mm']
        candidates=[c for c in cylinders if abs(c['diameter_mm']-diameter)<.001 and
            math.hypot(c['axis_point_mm'][0]-center[0],c['axis_point_mm'][2]-center[2])<.001 and
            abs(abs(c['axis_direction'][1])-1)<1e-8]
        measurements.append({'requested_diameter_mm':diameter,'requested_center_mm':center,
            'passed':len(candidates)==1,'matching_STEP_cylinders':candidates,
            'through_depth_samples_empty_in_STEP':all(not shape.isInside(cq.Vector(*center)+cq.Vector(0,d,0),1e-5) for d in [-.4*shape.BoundingBox().ylen,0,.4*shape.BoundingBox().ylen])})
    return {'passed':len(cylinders)==len(expected) and all(m['passed'] and m['through_depth_samples_empty_in_STEP'] for m in measurements),
            'STEP_cylinder_count':len(cylinders),'diameter_and_axis_tolerance_mm':.001,'measurements':measurements}
def profile(path):
    rows=[]
    for line in path.read_text().splitlines():
        v=line.split()
        if len(v)==2:
            try: rows.append([float(x) for x in v])
            except ValueError: pass
    xy=np.asarray(rows,dtype=float)
    if xy.ndim!=2 or len(xy)<20 or not np.isfinite(xy).all(): raise ValueError('Expected finite Selig-format single airfoil with >=20 points')
    keep=np.r_[True,np.linalg.norm(np.diff(xy,axis=0),axis=1)>1e-10]; xy=xy[keep]
    if np.min(xy[:,0])<-.01 or np.max(xy[:,0])>1.01 or np.ptp(xy[:,0])<.99: raise ValueError('Only explicitly normalized unit-chord input is supported')
    le=int(np.argmin(xy[:,0]))
    if le<3 or le>len(xy)-4 or xy[0,0]<.98 or xy[-1,0]<.98: raise ValueError('Selig ordering TE-upper -> LE -> TE-lower required')
    if np.any(np.diff(xy[:le+1,0])>1e-5) or np.any(np.diff(xy[le:,0])< -1e-5): raise ValueError('Nonmonotone branch or unsupported multi-element profile')
    xs=np.linspace(.01,.99,101)
    gap=np.interp(xs,xy[:le+1,0][::-1],xy[:le+1,1][::-1])-np.interp(xs,xy[le:,0],xy[le:,1])
    if np.min(gap)<=0 or np.max(np.abs(xy[:,1]))>.5: raise ValueError('Crossed/invalid upper and lower airfoil branches')
    area=abs(float(np.dot(xy[:,0],np.roll(xy[:,1],-1))-np.dot(xy[:,1],np.roll(xy[:,0],-1))))/2
    if not .001<area<.5: raise ValueError('Implausible normalized section area')
    return xy,le,area
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--case',type=Path,default=OUT/'data/parametric_wing_case.json'); args=parser.parse_args()
    case=args.case.resolve(); cfg=json.loads(case.read_text(encoding='utf-8')); stations=cfg['stations']
    if cfg['units']!={'length':'m','angle':'deg'}: raise ValueError('Explicit m/deg units required')
    ys=np.array([s['y'] for s in stations]); numeric=np.array([[s[k] for k in ['y','x_le','z_le','chord','twist_deg']] for s in stations])
    if len(stations)<2 or not np.isfinite(numeric).all() or ys[0]!=0 or not np.all(np.diff(ys)>0): raise ValueError('Root at y=0 and strictly increasing finite stations required')
    if np.min(numeric[:,3])<=0 or np.max(np.abs(numeric[:,4]))>15: raise ValueError('Positive chord; qualified twist range +/-15 deg required')
    src=(ROOT/cfg['airfoil']).resolve(); xy,le,area=profile(src)
    folder=OUT/'simulations'/('parametric_cad_'+datetime.now().strftime('%Y%m%d_%H%M%S')); folder.mkdir()
    dest=OUT/'cad/parametric_wing'; dest.mkdir(exist_ok=True)
    shutil.copy2(case,folder/'case.json'); shutil.copy2(src,folder/'source_airfoil.dat')
    checks=[]
    def check(name,passed,measurement,criterion):
        checks.append({'name':name,'passed':bool(passed),'measurement':measurement,'criterion':criterion})
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)
    def station(y):
        return {k:float(np.interp(abs(y),ys,[s[k] for s in stations])) for k in ['x_le','z_le','chord','twist_deg']}
    def point(x,z,y):
        s=station(y); c=s['chord']; theta=math.radians(s['twist_deg']); u=c*(x-.25); v=c*z
        return cq.Vector(1000*(s['x_le']+.25*c+u*math.cos(theta)+v*math.sin(theta)),1000*y,
                         1000*(s['z_le']-u*math.sin(theta)+v*math.cos(theta)))
    def wire(y):
        vertices=[point(x,z,y) for x,z in xy]
        edges=[cq.Edge.makeSpline(vertices[:le+1]),cq.Edge.makeSpline(vertices[le:])]
        if (vertices[-1]-vertices[0]).Length>1e-7: edges.append(cq.Edge.makeLine(vertices[-1],vertices[0]))
        return cq.Wire.assembleEdges(edges)
    full_y=list(-ys[1:][::-1])+list(ys)
    wing=cq.Solid.makeLoft([wire(float(y)) for y in full_y],ruled=True)
    check('Multi-section swept/tapered/twisted envelope',wing.isValid() and len(wing.Solids())==1,{'solids':len(wing.Solids()),'volume_mm3':wing.Volume()},'One valid closed solid')
    cq.exporters.export(wing,str(dest/'envelope.step')); cq.exporters.export(wing,str(dest/'envelope.stl'))
    restored=cq.importers.importStep(str(dest/'envelope.step')).val()
    rel=abs(restored.Volume()/wing.Volume()-1)
    check('STEP volume and topology',restored.isValid() and len(restored.Solids())==1 and rel<cfg['acceptance']['step_volume_relative'],{'relative_volume_change':rel},'Valid one-solid STEP; volume relative error <1e-6')
    estimate=2*area*sum((ys[i+1]-ys[i])*(stations[i]['chord']**2+stations[i]['chord']*stations[i+1]['chord']+stations[i+1]['chord']**2)/3 for i in range(len(ys)-1))*1e9
    rel=abs(wing.Volume()/estimate-1)
    check('Volume vs independent source-polygon integration',rel<cfg['acceptance']['volume_vs_source_polygon_relative'],{'CAD_mm3':wing.Volume(),'source_polygon_estimate_mm3':estimate,'relative_difference':rel},'Source-polygon area times integral of chord squared; allows small spline/ruled-twist differences <3%')
    distances=[]
    for y in full_y:
        distances += [restored.distance(cq.Vertex.makeVertex(*point(float(x),float(z),float(y)).toTuple())) for x,z in xy[::3]]
    check('Station profile points after STEP',max(distances)<cfg['acceptance']['station_surface_distance_mm'],{'max_distance_mm':max(distances),'stations':len(full_y),'sampled_points':len(distances)},'Source-profile transformed sample points lie on exported surface within 0.03 mm; not full shape equivalence')
    b=restored.BoundingBox(); span=2*ys[-1]*1000
    check('SI-to-CAD span',abs(b.ylen-span)<.001,{'span_mm':b.ylen,'expected_span_mm':span},'Full span within 0.001 mm')
    parts=[wing]; rib_results=[]
    for index,y in enumerate(cfg['rib_y_m']):
        if not 0<y<ys[-1] or cfg['rib_thickness_m']<=0: raise ValueError('Rib station or thickness invalid')
        thickness=cfg['rib_thickness_m']*1000
        rib=cq.Solid.extrudeLinear(wire(y),[],cq.Vector(0,thickness,0)).intersect(wing)
        probes=[]
        for bore in cfg['bores']:
            x=bore['x_over_c']; d=bore['diameter_m']*1000
            if not 0.05<x<.9 or not 0<d<station(y)['chord']*1000*.1: raise ValueError('Unsupported bore position/diameter')
            z=(float(np.interp(x,xy[:le+1,0][::-1],xy[:le+1,1][::-1]))+float(np.interp(x,xy[le:,0],xy[le:,1])))/2
            center=point(x,z,y); center.y+=thickness/2
            if not rib.isInside(center,1e-5): raise ValueError('Requested bore center lies outside rib')
            cutter=cq.Solid.makeCylinder(d/2,thickness+4,center-cq.Vector(0,thickness/2+2,0),cq.Vector(0,1,0))
            rib=rib.cut(cutter)
            depths=[-thickness*.4,0,thickness*.4]
            empty=all(not rib.isInside(center+cq.Vector(0,depth,0),1e-5) for depth in depths)
            material=rib.isInside(center+cq.Vector(d/2+1,0,0),1e-5)
            probes.append({'diameter_mm':d,'center_mm':list(center.toTuple()),'through_depth_samples_empty':empty,'adjacent_material_exists':material})
        path=dest/f'rib_{index+1}.step'; cq.exporters.export(rib,str(path)); back=cq.importers.importStep(str(path)).val()
        bore_readback=measure_bores(back,probes)
        ok=back.isValid() and len(back.Solids())==1 and all(p['through_depth_samples_empty'] and p['adjacent_material_exists'] for p in probes) and bore_readback['passed']
        check(f'Rib {index+1}: clipped profile and two located bores',ok,{'volume_mm3':back.Volume(),'probes':probes,'STEP_bore_readback':bore_readback},'One valid rib; bores empty at 3 depths; imported STEP cylinder diameters and axis positions within 0.001 mm')
        parts.append(rib); rib_results.append({'station_y_m':y,'path':str(path),'volume_mm3':back.Volume(),'probes':probes,'STEP_bore_readback':bore_readback})
    assembly=cq.Compound.makeCompound(parts); cq.exporters.export(assembly,str(dest/'review_envelope_and_ribs.step'))
    # Real geometric projection, not an image-generation model.
    for label,direction in [('top',(0,0,1)),('iso',(1,-2,1)),('front',(1,0,0))]:
        cq.exporters.export(assembly,str(dest/f'{label}.svg'),exportType='SVG',opt={'projectionDir':direction,'showHidden':False,'strokeWidth':.4,'width':1200,'height':500})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'passed_checks':sum(c['passed'] for c in checks),'total_checks':len(checks),
      'checks':checks,'ribs':rib_results,'profile_file':str(src),'profile_sha256':sha(src),'case_sha256':sha(case),'run_directory':str(folder),
      'envelope_bbox_mm':[b.xlen,b.ylen,b.zlen],'envelope_volume_mm3':wing.Volume(),
      'geometry_generation':'Fixed CadQuery kernel operations from JSON and source coordinates; no local CAD-model inference',
      'coordinate_convention':'x_le/z_le are untwisted reference LE; twist is about 25% chord, positive nose-up; cross-sections in constant-y planes',
      'limits':['Qualified single-element normalized Selig profile and ruled symmetric wing family only',
                'Envelope and ribs overlap in review compound; no material mass or structural assembly claim',
                'Not a manufacturing release, strength validation or proof of arbitrary-CAD correctness']}
    save(folder/'results.json',result); save(OUT/'reports/parametric_cad_qualification.json',result)
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'bbox_mm':result['envelope_bbox_mm']},indent=2),flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
