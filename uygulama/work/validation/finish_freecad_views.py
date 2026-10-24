"""Executed only in a dedicated native FreeCAD GUI process; save clean model views."""
import json,os
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
ROOT=Path(os.environ['UAV_VALIDATION_ROOT']);pid=json.loads((ROOT/'work/validation/projects.json').read_text())['cad'];out=ROOT/'outputs/projects'/pid
records=[];pref=App.ParamGet('User parameter:BaseApp/Preferences/Document');backups=pref.GetInt('CountBackupFiles',1);pref.SetInt('CountBackupFiles',0)
try:
    for rel,visible in [('cad/reconstructed/ctc01_reconstructed.FCStd','ReferenceSolid'),('cad/modified/ctc02_native_ports.FCStd','CutPort2'),('cad/modified/ctc05_native_grooves.FCStd','CutKeyway')]:
        path=out/rel;doc=App.openDocument(str(path))
        for o in doc.Objects:
            if o.ViewObject:
                o.ViewObject.Visibility=o.Name==visible
                if o.Name==visible:o.ViewObject.ShapeColor=(.42,.69,.78);o.ViewObject.LineColor=(.1,.2,.25);o.ViewObject.DisplayMode='Flat Lines'
        Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll();Gui.updateGui()
        Gui.activeDocument().activeView().saveImage(str(out/'plots'/(path.stem+'_native.png')),1350,900,'White')
        doc.recompute();doc.save();records.append({'file':rel,'visible_object':visible,'valid':doc.getObject(visible).Shape.isValid(),'hidden_construction_objects':[o.Name for o in doc.Objects if o.ViewObject and not o.ViewObject.Visibility]});App.closeDocument(doc.Name)
finally:pref.SetInt('CountBackupFiles',backups)
(out/'reports/native_view_checks.json').write_text(json.dumps({'passed':all(r['valid'] for r in records),'records':records},indent=2),encoding='utf-8');print('COMPLEX_GUI_VIEWS_SAVED',flush=True)
QtCore.QTimer.singleShot(300,Gui.getMainWindow().close)
