"""Sourced single-element DAT -> new Gmsh domain -> native 2D Euler CFD.
This closes a mesh/input integration gap only; viscous/stall/3D qualification is separate.
"""
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ.get('UAV_OUTPUT_ROOT',str(ROOT/'outputs')))
sys.path.insert(0,str(ROOT/'work/geometry'))
from parametric_wing import profile
import gmsh
import numpy as np
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def replace(text,key,value):
    pattern=r'^\s*'+re.escape(key)+r'\s*=.*$'
    return re.sub(pattern,key+'= '+str(value),text,flags=re.M) if re.search(pattern,text,re.M) else text+'\n'+key+'= '+str(value)+'\n'
def mesh(xy,le,folder,h):
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('profile');g=gmsh.model.geo
        nodes=[g.addPoint(float(x),float(y),0,h) for x,y in xy]
        edges=[g.addSpline(nodes[:le+1]),g.addSpline(nodes[le:])]
        if np.linalg.norm(xy[-1]-xy[0])>1e-9:edges.append(g.addLine(nodes[-1],nodes[0]))
        inner=g.addCurveLoop(edges)
        box=[g.addPoint(x,y,0,2) for x,y in [(-20,-20),(20,-20),(20,20),(-20,20)]]
        outer=[g.addLine(a,b) for a,b in zip(box,box[1:]+box[:1])]
        surface=g.addPlaneSurface([g.addCurveLoop(outer),inner]);g.synchronize()
        gmsh.model.addPhysicalGroup(2,[surface],1)
        gmsh.model.addPhysicalGroup(1,edges,2);gmsh.model.setPhysicalName(1,2,'airfoil')
        gmsh.model.addPhysicalGroup(1,outer,3);gmsh.model.setPhysicalName(1,3,'farfield')
        fields=gmsh.model.mesh.field
        d=fields.add('Distance');fields.setNumbers(d,'CurvesList',edges);fields.setNumber(d,'Sampling',400)
        f=fields.add('Threshold');fields.setNumber(f,'InField',d);fields.setNumber(f,'SizeMin',h);fields.setNumber(f,'SizeMax',2)
        fields.setNumber(f,'DistMin',.06);fields.setNumber(f,'DistMax',3);fields.setAsBackgroundMesh(f)
        gmsh.option.setNumber('Mesh.Algorithm',6);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0)
        gmsh.model.mesh.generate(2);gmsh.write(str(folder/'mesh.msh'))
        tags,coords,_=gmsh.model.mesh.getNodes();positions={int(t):c[:2] for t,c in zip(tags,np.asarray(coords).reshape(-1,3))}
        types,_,blocks=gmsh.model.mesh.getElements(2)
        if list(types)!=[2]:raise ValueError('Only linear triangular meshes qualified')
        triangles=np.asarray(blocks[0],dtype=int).reshape(-1,3)
        cross=lambda a,b:float(a[0]*b[1]-a[1]*b[0])
        areas=np.array([cross(positions[b]-positions[a],positions[c]-positions[a])/2 for a,b,c in triangles])
        if areas.min()<=0:raise ValueError('Nonpositive cell area')
        adjacency={}
        for tri in triangles:
            center=np.mean([positions[int(t)] for t in tri],axis=0)
            for a,b in zip(tri,np.roll(tri,-1)):adjacency.setdefault(tuple(sorted([int(a),int(b)])),[]).append(center)
        boundary={}
        for label,curves in [('airfoil',edges),('farfield',outer)]:
            lines=[]
            for c in curves:
                ts,_,bs=gmsh.model.mesh.getElements(1,c)
                if list(ts)!=[1]:raise ValueError('Unexpected boundary element')
                for a,b in np.asarray(bs[0]).reshape(-1,2):
                    a=int(a);b=int(b);neighbor=adjacency[tuple(sorted([a,b]))]
                    if len(neighbor)!=1:raise ValueError('Boundary does not have exactly one fluid cell')
                    if cross(positions[b]-positions[a],neighbor[0]-positions[a])<0:a,b=b,a
                    lines.append([a,b])
            boundary[label]=lines
        used=sorted(set(int(t) for t in triangles.reshape(-1)));index={t:i for i,t in enumerate(used)}
        with (folder/'mesh.su2').open('w',encoding='ascii') as f:
            f.write('NDIME= 2\nNELEM= '+str(len(triangles))+'\n')
            for i,tri in enumerate(triangles):f.write('5 '+' '.join(str(index[int(t)]) for t in tri)+' '+str(i)+'\n')
            f.write('NPOIN= '+str(len(used))+'\n')
            for t in used:f.write(f'{positions[t][0]:.16g} {positions[t][1]:.16g} {index[t]}\n')
            f.write('NMARK= 2\n')
            for name,lines in boundary.items():
                f.write('MARKER_TAG= '+name+'\nMARKER_ELEMS= '+str(len(lines))+'\n')
                for a,b in lines:f.write(f'3 {index[a]} {index[b]}\n')
        gmsh.write(str(folder/'geometry.geo_unrolled'))
        return {'cells':len(triangles),'nodes':len(used),'min_cell_area_m2':float(areas.min()),
            'boundary_segments':{name:len(lines) for name,lines in boundary.items()},'h_near_m':h,
            'boundary_one_fluid_neighbor':True,'unused_nodes_removed':True,'mesh_sha256':sha(folder/'mesh.su2')}
    finally:gmsh.finalize()
def execute(cmd,folder,log,inputs=None,timeout=300):
    start=time.perf_counter()
    with (folder/log).open('w',encoding='utf-8') as f:
        p=subprocess.run(cmd,cwd=folder,input=inputs,text=True,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise ValueError('Native process failed; see '+str(folder/log))
    return time.perf_counter()-start
def history(path):
    import csv
    with path.open() as f:raw=list(csv.DictReader(f))
    return [{k.strip().strip('"'):float(v) for k,v in row.items()} for row in raw]
def main():
    case=OUT/'data/profile_cfd_case.json';cfg=json.loads(case.read_text());source=(ROOT/cfg['airfoil']).resolve()
    if not source.is_relative_to(ROOT) or cfg.get('mode')!='euler2d' or cfg.get('units')!={'length':'m','angle':'deg'}:raise ValueError('Qualified normalized single-profile Euler2D input required')
    mach=cfg['Mach'];alpha=cfg['alpha_deg']
    if isinstance(mach,bool) or not .1<=mach<=.3 or not math.isfinite(alpha) or not -5<=alpha<=5:raise ValueError('Qualified input screen: Mach [0.1,0.3], alpha [-5,5] deg')
    xy,le,_=profile(source);run=OUT/'simulations'/('profile_cfd_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    (run/'case.json').write_bytes(case.read_bytes());(run/'airfoil.dat').write_bytes(source.read_bytes())
    conditions={'solver':'EULER','Mach':mach,'alpha_deg':alpha,'P_Pa':101325,'T_K':273.15,'reference_area_m2':1,'reference_length_m':1,'farfield_extent_chords':20}
    condition_sha=hashlib.sha256(json.dumps(conditions,sort_keys=True).encode()).hexdigest()
    binary=json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'];rows=[]
    for name,h in [('medium',.006),('fine',.003)]:
        folder=run/name;folder.mkdir();print('PROFILE MESH AND NATIVE CFD',name,flush=True)
        try:
            metrics=mesh(xy,le,folder,h)
            text=(ROOT/'work/qualification/sources/inv_NACA0012.cfg').read_text()
            for key,value in {'MACH_NUMBER':mach,'AOA':alpha,'MESH_FILENAME':'mesh.su2','ITER':6000,'MGLEVEL':0,'CFL_NUMBER':30,'CFL_ADAPT':'NO','LINEAR_SOLVER_ITER':20,
                'CONV_RESIDUAL_MINVAL':(-10 if name=='fine' else -8),'OUTPUT_FILES':'(RESTART, PARAVIEW, SURFACE_CSV)','OUTPUT_WRT_FREQ':6000,
                'HISTORY_OUTPUT':'(ITER, RMS_RES, AERO_COEFF)'}.items():text=replace(text,key,value)
            (folder/'case.cfg').write_text(text);save(folder/'command.json',[binary,'case.cfg','-t','2'])
            seconds=execute([binary,'case.cfg','-t','2'],folder,'native.log',timeout=600)
            hist=history(folder/'history.csv');last=hist[-1];tail=hist[-100:]
            cl=last['CL'];cd=last['CD'];res=last['rms[Rho]']
            dcl=max(r['CL'] for r in tail)-min(r['CL'] for r in tail);dcd=max(r['CD'] for r in tail)-min(r['CD'] for r in tail)
            row={'level':name,'folder':str(folder),'mesh':metrics,'seconds':seconds,'CL':cl,'CD_numerical_inviscid':cd,
                'log10_density_residual':res,'CL_tail_range':dcl,'CD_tail_range':dcd,'runtime_passed':True,
                'iterative_passed':res<-7 and dcl<2e-4 and dcd<2e-5}
            print(json.dumps(row),flush=True);rows.append(row)
        except Exception as exc:rows.append({'level':name,'runtime_passed':False,'error':str(exc),'folder':str(folder)});print(str(exc),flush=True);break
    reference=None
    try:
        xdir=run/'xfoil_inviscid';xdir.mkdir();(xdir/'airfoil.dat').write_bytes(source.read_bytes())
        xbin=json.loads((ROOT/'work/setup/xfoil_install.json').read_text())['executable']
        commands=f'PLOP\nG\n\nLOAD airfoil.dat\nPANE\nOPER\nMACH {mach}\nPACC\npolar.txt\n\nALFA {alpha}\nPACC\n\nQUIT\n'
        (xdir/'commands.in').write_text(commands);execute([xbin],xdir,'native.log',commands,timeout=45)
        numbers=[]
        for line in (xdir/'polar.txt').read_text().splitlines():
            try:v=[float(x) for x in line.split()]
            except ValueError:continue
            if len(v)>=5:numbers.append(v)
        if not numbers:raise ValueError('No inviscid XFOIL polar')
        reference={'solver':'XFOIL inviscid','CL':numbers[-1][1],'Mach':mach,'alpha_deg':alpha,'note':'Same source DAT, independent panel method; not experimental validation or identical spline representation'}
    except Exception as exc:reference={'error':str(exc)}
    runtime=len(rows)==2 and all(r['runtime_passed'] for r in rows)
    grid=abs(rows[1]['CL']/rows[0]['CL']-1) if runtime and abs(rows[0]['CL'])>1e-4 else None
    referror=abs(rows[-1]['CL']/reference['CL']-1) if runtime and reference.get('CL') and abs(reference['CL'])>1e-4 else None
    quality=bool(runtime and all(r['iterative_passed'] for r in rows) and grid is not None and grid<.03 and referror is not None and referror<.05 and abs(rows[-1]['CD_numerical_inviscid'])<.003)
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':runtime,'quality_passed':quality,'results':rows,'reference':reference,
        'CL_grid_relative_change':grid,'CL_reference_relative_difference':referror,'geometry_sha256':sha(source),'conditions_sha256':condition_sha,
        'analysis_scope':'2D inviscid profile','conditions':conditions,'input_case_sha256':sha(case),'run_directory':str(run),
        'acceptance_thresholds':{'density_residual_log10_max':-7,'CL_last100_range_max':2e-4,'CD_last100_range_max':2e-5,'CL_grid_relative_change_max':.03,'CL_XFOIL_relative_difference_max':.05,'absolute_inviscid_numerical_CD_max':.003},
        'scope':'New source DAT -> Gmsh fluid domain -> native 2D Euler; not viscous drag or 3D wing CFD',
        'limits':['No boundary-layer mesh/RANS/transition qualification','Inviscid numerical CD is not physical profile drag','No stall or whole-aircraft acceptance','20-chord farfield sensitivity not independently established']}
    save(run/'results.json',result);save(OUT/'reports/profile_cfd_results.json',result)
    if runtime:
        from profile_cfd_views import render
        render(OUT)
    print(json.dumps({'runtime_passed':runtime,'quality_passed':quality,'grid_CL':grid,'XFOIL_CL_difference':referror}),flush=True)
    return 0 if runtime else 1
if __name__=='__main__':raise SystemExit(main())
