"""Run inside FreeCADCmd; create a dimensioned, editable benchmark solid."""
import json
import os
from pathlib import Path
import FreeCAD as App
import Part

out=Path(os.environ['UAV_FEM_RUN'])
doc=App.newDocument('Cantilever_qualification')
beam=doc.addObject('Part::Box','Beam')
beam.Label='Qualification only - 200 x 10 x 10 mm'
beam.Length=200; beam.Width=10; beam.Height=10
doc.recompute()
assert beam.Shape.isValid() and len(beam.Shape.Solids)==1
doc.saveAs(str(out/'cantilever.FCStd'))
Part.export([beam],str(out/'cantilever.step'))
shape=Part.Shape(); shape.read(str(out/'cantilever.step'))
assert shape.isValid() and len(shape.Solids)==1
data={'freecad_version':App.Version(),'valid_solid':shape.isValid(),'solid_count':len(shape.Solids),
      'volume_mm3':shape.Volume,'bbox_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength]}
(out/'freecad_result.json').write_text(json.dumps(data,indent=2))
App.closeDocument(doc.Name)
reopened=App.openDocument(str(out/'cantilever.FCStd'))
assert reopened.getObject('Beam').Shape.isValid()
print('FREECAD_CAD_COMPLETE',flush=True)
App.closeDocument(reopened.Name)
