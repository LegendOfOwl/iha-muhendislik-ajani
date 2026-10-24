"""Render eight clean orthographic views of a known CadQuery test part."""
from pathlib import Path
import itertools
import json
import cadquery as cq
import vtk

def render(folder):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    part=cq.Workplane('XY').box(1,.75,.2).faces('>Z').workplane().hole(.25).val()
    cq.exporters.export(part,str(folder/'reference.step'))
    vertices,triangles=part.tessellate(.002,.15)
    points=vtk.vtkPoints()
    for v in vertices: points.InsertNextPoint(v.x,v.y,v.z)
    cells=vtk.vtkCellArray()
    for tri in triangles:
        cells.InsertNextCell(3)
        for index in tri: cells.InsertCellPoint(index)
    mesh=vtk.vtkPolyData(); mesh.SetPoints(points); mesh.SetPolys(cells)
    mapper=vtk.vtkPolyDataMapper(); mapper.SetInputData(mesh)
    actor=vtk.vtkActor(); actor.SetMapper(mapper); actor.GetProperty().SetColor(.64,.68,.74)
    renderer=vtk.vtkRenderer(); renderer.SetBackground(1,1,1); renderer.AddActor(actor)
    window=vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(256,256); window.AddRenderer(renderer)
    directions=list(itertools.product([1,-1],[1,-1],[1,-1]))
    for i,(x,y,z) in enumerate(directions):
        camera=renderer.GetActiveCamera(); camera.SetPosition(3*x,3*y,3*z); camera.SetFocalPoint(0,0,0)
        camera.SetViewUp(0,0,1); camera.ParallelProjectionOn(); camera.SetParallelScale(.72)
        renderer.ResetCameraClippingRange(); window.Render()
        capture=vtk.vtkWindowToImageFilter(); capture.SetInput(window); capture.ReadFrontBufferOff(); capture.Update()
        writer=vtk.vtkPNGWriter(); writer.SetFileName(str(folder/f'view_{i}.png')); writer.SetInputConnection(capture.GetOutputPort()); writer.Write()
    window.Finalize()
    (folder/'reference.json').write_text(json.dumps({'geometry':'rectangular plate with through hole',
        'dimensions':[1,.75,.2],'hole_diameter':.25,'units':'normalized; images cannot determine absolute scale',
        'camera_directions':directions,'render_size_px':[256,256]},indent=2))
    print('Eight CAD views rendered',flush=True)
    return folder
if __name__=='__main__':
    import sys
    render(sys.argv[1])
