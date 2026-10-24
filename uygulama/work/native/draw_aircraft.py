"""Import real OpenVSP STEP geometry, produce CAD drawings and a valid wing solid."""
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "work/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "work/cache"))
import cadquery as cq
from cadquery.occ_impl.exporters.svg import getSVG
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

checks = []


def check(name, passed, evidence, criterion):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence, "criterion": criterion})
    print(('PASS: ' if passed else 'FAIL: ') + name, flush=True)


def projection(shape, direction, horizontal=(1,0,0)):
    from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
    from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    from OCP.HLRAlgo import HLRAlgo_Projector
    from OCP.BRepLib import BRepLib
    algorithm = HLRBRep_Algo()
    algorithm.Add(shape.wrapped)
    algorithm.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(), gp_Dir(*direction),gp_Dir(*horizontal))))
    algorithm.Update(); algorithm.Hide()
    result = HLRBRep_HLRToShape(algorithm)
    parts = []
    for raw in [result.VCompound(), result.Rg1LineVCompound(), result.OutLineVCompound()]:
        if not raw.IsNull():
            BRepLib.BuildCurves3d_s(raw, 1e-7)
            parts.append(cq.Shape.cast(raw))
    return cq.Compound.makeCompound(parts)


def wing_solid():
    # An aerodynamic envelope, not a structural solid or mass model.
    x = (1 - np.cos(np.linspace(0, np.pi, 121))) / 2
    yt = 5 * .12 * (.2969 * np.sqrt(x) - .126 * x - .3516 * x**2 + .2843 * x**3 - .1036 * x**4)
    yt[0] = yt[-1] = 0
    def section(y):
        upper = [cq.Vector(float(250*a), y, float(250*b)) for a,b in zip(x,yt)]
        lower = [cq.Vector(float(250*a), y, float(-250*b)) for a,b in zip(x[::-1],yt[::-1])]
        return cq.Wire.assembleEdges([cq.Edge.makeSpline(upper), cq.Edge.makeSpline(lower)])
    solid = cq.Solid.makeLoft([section(-1000), section(1000)], ruled=True)
    analytic_area_ratio = 10 * .12 * (.2969 * 2/3 - .126/2 - .3516/3 + .2843/4 - .1036/5)
    expected_volume = analytic_area_ratio * 250**2 * 2000
    check("CadQuery gerçek NACA kanat katısı", solid.isValid() and abs(solid.Volume()/expected_volume - 1) < .01,
          {"solid_valid":solid.isValid(),"volume_mm3":solid.Volume(),"analytic_envelope_volume_mm3":expected_volume},
          "Geçerli kapalı kanat zarfı; analitik NACA kesit integraline göre hacim farkı<%1")
    cq.exporters.export(solid,str(OUT/'cad/reference_wing_solid.step'))
    cq.exporters.export(solid,str(OUT/'cad/reference_wing_solid.stl'))
    imported = cq.importers.importStep(str(OUT/'cad/reference_wing_solid.step')).val()
    check("Kanat katısının STEP turu", imported.isValid() and abs(imported.Volume()/solid.Volume()-1) < 1e-6,
          {"volume_relative_change":abs(imported.Volume()/solid.Volume()-1)},"STEP tekrar okuma hacim değişimi<1e-6")


def main():
    aircraft = cq.importers.importStep(str(OUT/'cad/aircraft_demo.step')).val()
    wing = cq.importers.importStep(str(OUT/'cad/reference_wing.step')).val()
    box = aircraft.BoundingBox(); wbox=wing.BoundingBox()
    dimensions = [box.xlen,box.ylen,box.zlen]
    check("OpenVSP -> CAD referans birim kontrolü", wing.isValid() and abs(wbox.ylen-2000)<.1 and abs(wbox.xlen-250)<.1,
          {"reference_wing_bounding_box_mm":[wbox.xlen,wbox.ylen,wbox.zlen]},"OpenVSP metre -> STEP -> CAD milimetre: açıklık 2000, veter 250 mm, hata<.1mm")
    check("OpenVSP uçak yüzeylerinin CAD aktarımı", aircraft.isValid() and len(aircraft.Faces())>10 and abs(box.ylen-2000)<.1,
          {"bbox_mm":dimensions,"faces":len(aircraft.Faces()),"solids":len(aircraft.Solids()),"valid":aircraft.isValid()},
          "Geçerli CAD geometrisi; >10 yüzey ve 2000mm açıklık. Yüzey geometrisi imalata hazır katı anlamına gelmez")
    wing_solid()
    svg_ns="http://www.w3.org/2000/svg"
    ET.register_namespace('',svg_ns)
    def tag(name): return f'{{{svg_ns}}}{name}'
    sheet=ET.Element(tag('svg'),{'width':'420mm','height':'297mm','viewBox':'0 0 1680 1188'})
    ET.SubElement(sheet,tag('rect'),{'x':'0','y':'0','width':'1680','height':'1188','fill':'white'})
    def label(x,y,text,size=24,color='#142d40'):
        ET.SubElement(sheet,tag('text'),{'x':str(x),'y':str(y),'font-family':'Arial, sans-serif','font-size':str(size),'fill':color}).text=text
    label(60,55,'OPENVSP -> STEP -> CAD: THREE-VIEW DRAWING',30)
    label(60,90,'SYNTHETIC INTEGRATION DEMO — NOT AN AIRCRAFT DESIGN RECOMMENDATION',19,'#9a4c17')
    label(60,122,'Units: mm | Print A3 at 100%: nominal scale 1:10 | No manufacturing tolerances assigned',18)
    views=[('top',(0,0,1),box.xlen,60,180,'TOP / Z'),
           ('side',(0,-1,0),box.xlen,680,180,'SIDE / -Y'),
           ('front',(1,0,0),box.ylen,680,510,'FRONT / X')]
    for name,direction,projected_width,px,py,title in views:
        projected=projection(aircraft,direction,(0,1,0) if name=='front' else (1,0,0))
        svg = getSVG(projected,{'width':projected.BoundingBox().xlen*.4+40,'height':None,'marginLeft':20,'marginTop':20,
                              'projectionDir':(0,0,1),'showAxes':False,'showHidden':False,
                              'strokeColor':(20,45,64),'strokeWidth':1.3})
        view=ET.fromstring(svg)
        view.set('x',str(px));view.set('y',str(py))
        sheet.append(view);label(px,py-12,title,23)
        (OUT/f'cad/aircraft_{name}.svg').write_text(svg,encoding='utf-8')
        projected_workplane=cq.Workplane('XY').newObject(projected.Edges())
        cq.exporters.export(projected_workplane,str(OUT/f'cad/aircraft_{name}.dxf'),exportType='DXF')
        import ezdxf
        document=ezdxf.readfile(OUT/f'cad/aircraft_{name}.dxf')
        document.units=ezdxf.units.MM
        document.saveas(OUT/f'cad/aircraft_{name}.dxf')
        check(f"{title}: gerçek CAD çizgi projeksiyonu", len(document.modelspace())>0,
              {"DXF_entities":len(document.modelspace())},"OpenCascade gizli çizgi hesabından boş olmayan DXF")
    label(680,810,f'Overall length: {box.xlen:.1f} mm',23)
    label(680,850,f'Overall span: {box.ylen:.1f} mm',23)
    label(680,890,f'Overall height: {box.zlen:.1f} mm',23)
    label(680,950,'Fuselage is drawn; its aerodynamic loads are excluded.',19)
    label(680,982,'Wing + tail analysis uses native VSPAERO.',19)
    label(60,1100,'Editable geometry: aircraft_demo.vsp3 | Surface CAD: aircraft_demo.step',21)
    label(60,1142,'No propulsion, structure, trim or flight feasibility approval is implied.',19,'#9a4c17')
    ET.ElementTree(sheet).write(OUT/'cad/aircraft_three_view.svg',encoding='utf-8',xml_declaration=True)
    # Preview is tessellated directly from the imported native STEP surfaces.
    vertices,triangles=aircraft.tessellate(3.0, .15)
    points=np.array([[p.x,p.y,p.z] for p in vertices])/1000
    faces=[points[list(index)] for index in triangles]
    fig=plt.figure(figsize=(11,6.5));ax=fig.add_subplot(111,projection='3d')
    ax.add_collection3d(Poly3DCollection(faces,facecolors='#308ca3',edgecolors='none',alpha=.95))
    lower=points.min(axis=0);upper=points.max(axis=0)
    ax.set(xlim=(lower[0],upper[0]),ylim=(lower[1],upper[1]),zlim=(lower[2],upper[2]))
    ax.set_box_aspect(upper-lower,zoom=1.12);ax.view_init(elev=26,azim=-55)
    ax.set_axis_off();ax.set_title('Actual OpenVSP STEP geometry — integration demonstrator',fontsize=15)
    fig.text(.5,.05,'Synthetic dimensions; fuselage loads, propulsion and structure are not evaluated.',ha='center',fontsize=11,color='#8d4312')
    fig.tight_layout();fig.savefig(OUT/'plots/aircraft_geometry.png',dpi=160);plt.close(fig)
    result={'checks':checks,'passed':all(item['passed'] for item in checks),'bbox_mm':dimensions,
            'geometry_source':'outputs/cad/aircraft_demo.step exported by native OpenVSP',
            'model_scope':'synthetic integration test; surface CAD and separate closed wing envelope',
            'no_manufacturing_release':True}
    (OUT/'reports/external_cad_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print('CAD FINISHED',len(checks),'checks; passed=',result['passed'],flush=True)
    return 0 if result['passed'] else 1


if __name__=='__main__':
    sys.exit(main())
