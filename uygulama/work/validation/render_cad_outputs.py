"""Render the actual delivered solids and make review drawings from their edges."""
import json,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import cadquery as cq
import vtk
PID=json.loads((ROOT/'work/validation/projects.json').read_text())['cad'];OUT=ROOT/'outputs/projects'/PID
def render(shape,path):
    stl=ROOT/'work/validation/cad_view.stl';cq.exporters.export(shape,str(stl),tolerance=.15,angularTolerance=.15)
    renderer=vtk.vtkRenderer();renderer.SetBackground(.96,.98,.99);r=vtk.vtkSTLReader();r.SetFileName(str(stl));r.Update();m=vtk.vtkPolyDataMapper();m.SetInputConnection(r.GetOutputPort());a=vtk.vtkActor();a.SetMapper(m);a.GetProperty().SetColor(.13,.47,.59);renderer.AddActor(a)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1350,900);win.AddRenderer(renderer);b=shape.BoundingBox();c=shape.Center();scale=max(b.xlen,b.ylen,b.zlen);cam=renderer.GetActiveCamera();cam.SetPosition(c.x+scale*1.3,c.y-scale*1.8,c.z+scale*1.4);cam.SetFocalPoint(c.x,c.y,c.z);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();renderer.ResetCamera();win.Render();capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.ReadFrontBufferOff();capture.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
def main():
    files=[('CTC01 reconstructed','cad/reconstructed/ctc01_reconstructed.step'),('CTC02 four ports','cad/modified/ctc02_native_ports.step'),('CTC05 grooves and keyway','cad/modified/ctc05_native_grooves.step')]
    records=[]
    for title,name in files:
        path=OUT/name;s=cq.importers.importStep(str(path)).solids().val();base=path.stem;render(s,OUT/'plots'/(base+'.png'))
        drawing=OUT/'cad/drawings';drawing.mkdir(exist_ok=True)
        for label,direction in [('top',(0,0,1)),('front',(0,-1,0)),('right',(1,0,0))]:
            svg=cq.exporters.getSVG(s,opts={'width':1200,'height':650,'marginLeft':25,'marginTop':25,'projectionDir':direction,'showAxes':False,'showHidden':True,'strokeWidth':.6,'hiddenColor':(160,170,180)})
            (drawing/(base+'_'+label+'.svg')).write_text(svg,encoding='utf-8')
        records.append({'title':title,'file':name,'valid':s.isValid(),'solids':len(s.Solids()),'faces':len(s.Faces()),'bbox_mm':[s.BoundingBox().xlen,s.BoundingBox().ylen,s.BoundingBox().zlen]})
    # Publish source PDFs beside their provenance, separate from the generated CAD.
    refs=OUT/'data/sources';refs.mkdir(exist_ok=True)
    for number in ['01','02','05']:shutil.copy2(ROOT/'work/validation/sources'/('nist_ctc'+number+'.pdf'),refs/('nist_ctc'+number+'.pdf'))
    (OUT/'reports/cad_output_readback.json').write_text(json.dumps({'files':records,'scope':'STEP readback, actual rendered geometry and orthographic review projections; not a fully dimensioned/toleranced manufacturing drawing'},indent=2),encoding='utf-8')
    print(json.dumps(records,indent=2))
if __name__=='__main__':main()
