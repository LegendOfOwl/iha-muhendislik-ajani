"""Render the real STL comparison with a depth buffer."""
import json
from pathlib import Path
import vtk
ROOT=Path(__file__).resolve().parents[2]
study=json.loads((ROOT/'outputs/reports/k_family_study.json').read_text(encoding='utf-8'))
dest=ROOT/'work/research/k1b_deep/views'; dest.mkdir(exist_ok=True)
for row in study['results']:
    if row['mode']!='baseline': continue
    reader=vtk.vtkSTLReader(); reader.SetFileName(str(Path(row['folder'])/'generated.stl')); reader.Update()
    mapper=vtk.vtkPolyDataMapper(); mapper.SetInputConnection(reader.GetOutputPort())
    actor=vtk.vtkActor(); actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*((.07,.55,.48) if row['geometry_accepted'] else (.74,.30,.22)))
    renderer=vtk.vtkRenderer(); renderer.SetBackground(1,1,1); renderer.AddActor(actor)
    window=vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(650,440); window.SetMultiSamples(4); window.AddRenderer(renderer)
    b=reader.GetOutput().GetBounds(); mid=[(b[i]+b[i+1])/2 for i in [0,2,4]]; span=max(b[i+1]-b[i] for i in [0,2,4])
    camera=renderer.GetActiveCamera(); camera.SetPosition(mid[0]+3*span,mid[1]-4*span,mid[2]+4*span); camera.SetFocalPoint(*mid); camera.SetViewUp(0,0,1)
    camera.ParallelProjectionOn(); camera.SetParallelScale(span*.62)
    renderer.ResetCameraClippingRange(); window.Render()
    capture=vtk.vtkWindowToImageFilter(); capture.SetInput(window); capture.ReadFrontBufferOff(); capture.Update()
    writer=vtk.vtkPNGWriter(); writer.SetFileName(str(dest/f'{row["model"]}_{row["case"]}.png')); writer.SetInputConnection(capture.GetOutputPort()); writer.Write(); window.Finalize()
print('Six real STL views rendered')
