"""Bounded worker for reviewed CadQuery-only model output; not a security sandbox."""
import ast
import json
import math
from pathlib import Path
import sys
import cadquery as cq

def checked_tree(code):
    tree=ast.parse(code)
    forbidden={'open','exec','eval','compile','getattr','setattr','delattr','globals','locals','vars','input','help',
               '__import__','export','exporters','importers','read','write','save','load','load_module','system','popen'}
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            if not isinstance(node,ast.Import) or any(a.name not in {'cadquery','math'} for a in node.names): raise ValueError('Only cadquery/math imports allowed')
        if isinstance(node,ast.Attribute) and (node.attr.startswith('_') or node.attr in forbidden): raise ValueError('Disallowed attribute '+node.attr)
        if isinstance(node,ast.Name) and (node.id.startswith('__') or node.id in forbidden): raise ValueError('Disallowed name '+node.id)
        if isinstance(node,(ast.While,ast.With,ast.AsyncFunctionDef,ast.ClassDef,ast.Delete,ast.Global,ast.Nonlocal)): raise ValueError('Unsupported CAD program structure')
    return tree
def main():
    folder=Path(sys.argv[1])
    code=(folder/'generated.py').read_text(encoding='utf-8')
    tree=checked_tree(code)
    tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
    ast.fix_missing_locations(tree)
    safe={'range':range,'len':len,'float':float,'int':int,'list':list,'tuple':tuple,'abs':abs,'min':min,'max':max,'sum':sum,'enumerate':enumerate,'zip':zip,'print':print}
    namespace={'__builtins__':safe,'cq':cq,'cadquery':cq,'math':math}
    exec(compile(tree,'reviewed_cad_model','exec'),namespace)
    result=namespace.get('result')
    if isinstance(result,cq.Workplane): result=result.val()
    if not isinstance(result,cq.Shape) or not result.isValid() or len(result.Solids())!=1: raise ValueError('Expected one valid solid in result')
    cq.exporters.export(result,str(folder/'generated.step'))
    bbox=result.BoundingBox()
    (folder/'cad_metrics.json').write_text(json.dumps({'valid_solid':True,'solid_count':1,'volume':result.Volume(),
        'bbox':[bbox.xlen,bbox.ylen,bbox.zlen]},indent=2))
if __name__=='__main__': main()
