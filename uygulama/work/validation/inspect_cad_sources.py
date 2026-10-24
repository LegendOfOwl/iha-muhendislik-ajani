import collections,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'work/cache'))
import cadquery as cq
import vtk
from OCP.BRepAdaptor import BRepAdaptor_Surface
DEST=ROOT/'work/validation/cad_inspect';DEST.mkdir(exist_ok=True)
def vec(v):return [v.X(),v.Y(),v.Z()]
def main():
    records=[];paths=sorted((ROOT/'work/validation/sources/nist_ctc_definitions').rglob('*.stp'))
    for p in paths:
        shape=cq.importers.importStep(str(p)).val();box=shape.BoundingBox();faces=[]
        for f in shape.Faces():
            a=BRepAdaptor_Surface(f.wrapped,True);t=f.geomType();r={'type':t,'area':f.Area(),'center':f.Center().toTuple(),'bbox':[f.BoundingBox().xmin,f.BoundingBox().ymin,f.BoundingBox().zmin,f.BoundingBox().xmax,f.BoundingBox().ymax,f.BoundingBox().zmax]}
            if t=='CYLINDER':c=a.Cylinder();r.update(radius=c.Radius(),origin=vec(c.Location()),axis=vec(c.Axis().Direction()))
            if t=='CONE':c=a.Cone();r.update(reference_radius=c.RefRadius(),semiangle=c.SemiAngle(),origin=vec(c.Location()),axis=vec(c.Axis().Direction()))
            if t=='PLANE':r['normal']=f.normalAt().toTuple()
            faces.append(r)
        r={'name':p.stem,'source':str(p.relative_to(ROOT)),'valid':shape.isValid(),'solids':len(shape.Solids()),'volume_mm3':shape.Volume(),'bbox':[box.xmin,box.ymin,box.zmin,box.xmax,box.ymax,box.zmax],'face_types':dict(collections.Counter(f.geomType() for f in shape.Faces())),'faces':faces}
        records.append(r);(DEST/(p.stem+'.json')).write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='faces'}),flush=True)
        renderer=vtk.vtkRenderer();renderer.SetBackground(.96,.98,.99);stl=DEST/(p.stem+'.stl');cq.exporters.export(shape,str(stl));reader=vtk.vtkSTLReader();reader.SetFileName(str(stl));reader.Update();mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(reader.GetOutputPort());actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(.2,.52,.63);renderer.AddActor(actor)
        win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1100,800);win.AddRenderer(renderer);cam=renderer.GetActiveCamera();center=shape.Center();scale=max(box.xlen,box.ylen,box.zlen);cam.SetPosition(center.x+scale*1.3,center.y-scale*1.8,center.z+scale*1.4);cam.SetFocalPoint(center.x,center.y,center.z);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();renderer.ResetCamera();win.Render();capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.ReadFrontBufferOff();capture.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(DEST/(p.stem+'.png')));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
    (DEST/'summary.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='faces'} for r in records],indent=2))
if __name__=='__main__':main()
