"""Actual FreeCAD -> STEP -> Gmsh C3D10 -> CalculiX, mesh and theory checks."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
os.environ['OMP_NUM_THREADS']='2'
import gmsh
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=ROOT/'outputs'
run=OUT/'simulations'/('fem_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
run.mkdir(parents=True)
install=json.loads((ROOT/'work/setup/freecad_install.json').read_text())
checks=[]
def check(name,passed,evidence,criterion):
    checks.append(dict(name=name,passed=bool(passed),evidence=evidence,criterion=criterion))
    print(('PASS: ' if passed else 'FAIL: ')+name,flush=True)
def execute(cmd,folder,log,environment):
    start=time.perf_counter()
    with (folder/log).open('w',encoding='utf-8') as stream:
        p=subprocess.run(list(map(str,cmd)),cwd=folder,env=environment,input='',text=True,
             stdout=stream,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    return p.returncode,round(time.perf_counter()-start,3)
environment=dict(os.environ)
for variable,rel in [('FREECAD_USER_HOME','work/freecad/home'),('FREECAD_USER_DATA','work/freecad/data'),('FREECAD_USER_TEMP','work/freecad/temp')]:
    p=ROOT/rel; p.mkdir(parents=True,exist_ok=True); environment[variable]=str(p)
environment['UAV_FEM_RUN']=str(run)
code,seconds=execute([install['executables']['FreeCADCmd.exe'],ROOT/'work/fem/freecad_beam.py'],run,'freecad.log',environment)
log=(run/'freecad.log').read_text(errors='replace')
check('FreeCAD native CAD and saved document reopen',code==0 and 'FREECAD_CAD_COMPLETE' in log,{'exit_code':code,'seconds':seconds},'Native process exits 0 and completion marker exists')
if not (run/'freecad_result.json').exists(): raise RuntimeError('See '+str(run/'freecad.log'))
cad=json.loads((run/'freecad_result.json').read_text())
check('FreeCAD STEP units and solid topology',cad['solid_count']==1 and np.allclose(cad['bbox_mm'],[200,10,10],rtol=1e-8) and abs(cad['volume_mm3']/20000-1)<1e-8,cad,'One valid 200 x 10 x 10 mm solid; volume 20000 mm3')

def make_mesh(h,folder):
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.NumThreads',2)
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.logger.start()
        gmsh.model.add('cantilever')
        gmsh.model.occ.importShapes(str(run/'cantilever.step'))
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber('Mesh.MeshSizeMin',h)
        gmsh.option.setNumber('Mesh.MeshSizeMax',h)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.setOrder(2)
        gmsh.write(str(folder/'mesh.msh'))
        tags,coordinates,_=gmsh.model.mesh.getNodes()
        nodes={int(n):xyz for n,xyz in zip(tags,np.asarray(coordinates).reshape(-1,3))}
        types,_,blocks=gmsh.model.mesh.getElements(3)
        assert list(types)==[11],f'Expected quadratic tetrahedra, got {types}'
        # Gmsh's final two midside nodes differ from Abaqus/CalculiX C3D10.
        tets=np.asarray(blocks[0]).reshape(-1,10)[:,[0,1,2,3,4,5,6,7,9,8]]
        edge_pairs=[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
        max_error=max(float(np.linalg.norm(nodes[int(tet[4+i])]-(nodes[int(tet[a])]+nodes[int(tet[b])])/2))
                      for tet in tets for i,(a,b) in enumerate(edge_pairs))
        determinants=[float(np.linalg.det(np.stack([nodes[int(tet[i])]-nodes[int(tet[0])] for i in [1,2,3]],axis=1))) for tet in tets]
        check('C3D10 connectivity '+folder.name,max_error<1e-7 and min(determinants)>0,
              {'max_midside_error_mm':max_error,'min_corner_determinant_mm3':min(determinants)},
              'All CalculiX edge nodes match physical midpoints and corner Jacobians are positive')
        root=[n for n,xyz in nodes.items() if abs(xyz[0])<1e-6]
        tip=[n for n,xyz in nodes.items() if abs(xyz[0]-200)<1e-6]
        loads={n:0.0 for n in tip}
        area_total=0.0
        for _,face in gmsh.model.getEntities(2):
            bbox=gmsh.model.getBoundingBox(2,face)
            if abs(bbox[0]-200)<1e-5 and abs(bbox[3]-200)<1e-5:
                ts,_,bs=gmsh.model.mesh.getElements(2,face)
                assert list(ts)==[9]
                for tri in np.asarray(bs[0]).reshape(-1,6):
                    p0,p1,p2=[nodes[int(n)] for n in tri[:3]]
                    area=float(np.linalg.norm(np.cross(p1-p0,p2-p0))/2)
                    area_total+=area
                    for n in tri[3:]: loads[int(n)]+=-10/100*area/3
        assert abs(area_total-100)<1e-5 and abs(sum(loads.values())+10)<1e-7
        lines=['** Units: mm, N, MPa; isotropic synthetic qualification specimen','*NODE']
        lines += [f'{n}, {xyz[0]:.12g}, {xyz[1]:.12g}, {xyz[2]:.12g}' for n,xyz in nodes.items()]
        lines += ['*ELEMENT,TYPE=C3D10,ELSET=EALL']
        lines += [str(i+1)+', '+', '.join(str(int(n)) for n in tet) for i,tet in enumerate(tets)]
        for name,ns in [('ROOT',root),('TIP',tip)]:
            lines += ['*NSET,NSET='+name]
            lines += [', '.join(map(str,ns[i:i+12])) for i in range(0,len(ns),12)]
        lines += ['*MATERIAL,NAME=TEST_ISOTROPIC','*ELASTIC','70000., 0.3',
                  '*SOLID SECTION,ELSET=EALL,MATERIAL=TEST_ISOTROPIC','*BOUNDARY','ROOT,1,3',
                  '*STEP','*STATIC','*CLOAD']
        lines += [f'{n},3,{load:.12g}' for n,load in loads.items() if load]
        lines += ['*NODE PRINT,NSET=TIP','U','*NODE PRINT,NSET=ROOT','RF','*NODE FILE','U,RF',
                  '*EL FILE','S','*END STEP']
        (folder/'beam.inp').write_text('\n'.join(lines)+'\n')
        (folder/'gmsh.log').write_text('\n'.join(gmsh.logger.get()))
        return {'size_mm':h,'nodes':len(nodes),'elements':len(tets),'root_nodes':len(root),'tip_nodes':len(tip),
                'applied_force_N':sum(loads.values()),'nodes_xyz':nodes}
    finally: gmsh.finalize()

def dat_values(path,heading):
    found=False; rows=[]
    for line in path.read_text().splitlines():
        if heading in line.lower(): found=True; continue
        fields=line.split()
        if found and len(fields)==4:
            try: rows.append([int(fields[0])]+[float(s.replace('D','E')) for s in fields[1:]])
            except ValueError:
                if rows: break
        elif found and rows and line.strip(): break
    if not rows: raise ValueError('Missing native result '+heading)
    return np.asarray(rows)

rows=[]
for label,h in [('coarse',6.0),('medium',4.0),('fine',2.5)]:
    folder=run/label; folder.mkdir()
    print('Meshing and solving',label,flush=True)
    info=make_mesh(h,folder)
    code,seconds=execute([install['executables']['ccx.exe'],'-i','beam'],folder,'calculix.log',environment)
    log=(folder/'calculix.log').read_text(errors='replace')
    check('CalculiX '+label+' native solve',code==0 and 'Job finished' in log and '*ERROR' not in log,{'exit_code':code,'seconds':seconds},'Exit 0, Job finished, no *ERROR')
    displacements=dat_values(folder/'beam.dat','displacements')
    reactions=dat_values(folder/'beam.dat','forces')
    uz=-float(np.mean(displacements[:,3]))
    rz=float(np.sum(reactions[:,3]))
    check('Load balance '+label,abs(rz-10)/10<1e-5,{'applied_N':info['applied_force_N'],'reaction_N':rz},'Reaction equals applied total force within 0.001%')
    info.pop('nodes_xyz')
    rows.append(dict(info,tip_displacement_mm=uz,root_reaction_N=rz,seconds=seconds))

# Independent physics calculation in SI; convert only the comparison output to mm.
length_m=.2; width_m=.01; height_m=.01; elastic_modulus_Pa=70e9; force_N=10.; nu=.3
area_m2=width_m*height_m; inertia_m4=width_m*height_m**3/12
eb=force_N*length_m**3/(3*elastic_modulus_Pa*inertia_m4)*1000
timoshenko=eb+force_N*length_m/((5/6)*(elastic_modulus_Pa/(2*(1+nu)))*area_m2)*1000
rel=abs(rows[-1]['tip_displacement_mm']/eb-1)
change=abs(rows[-1]['tip_displacement_mm']/rows[-2]['tip_displacement_mm']-1)
check('Independent beam theory comparison',rel<.03,{'Euler_Bernoulli_mm':eb,'Timoshenko_mm':timoshenko,'fine_FEM_mm':rows[-1]['tip_displacement_mm'],'relative_difference':rel},'Fine solid FE tip displacement within 3% of slender beam theory')
check('Mesh convergence medium to fine',change<.015,{'relative_change':change,'levels':rows},'Mean loaded-end displacement change <1.5%; this quantity only')
check('Linear small-displacement range',rows[-1]['tip_displacement_mm']/200<.01,{'displacement_over_length':rows[-1]['tip_displacement_mm']/200},'Displacement/length <1% for this test')
fig,ax=plt.subplots(figsize=(8,4.5)); ax.plot([r['elements'] for r in rows],[r['tip_displacement_mm'] for r in rows],'o-',label='CalculiX C3D10')
ax.axhline(eb,color='k',linestyle='--',label='Euler-Bernoulli'); ax.axhline(timoshenko,color='tab:green',linestyle=':',label='Timoshenko')
ax.set(xlabel='Element count',ylabel='Mean tip deflection [mm]',title='CAD to FEM: mesh convergence, synthetic cantilever')
ax.legend(); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(OUT/'plots/fem_convergence.png',dpi=160); plt.close(fig)
for suffix in ['FCStd','step']: shutil.copy2(run/('cantilever.'+suffix),OUT/'cad'/('cantilever_qualification.'+suffix))
result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),
        'passed_checks':sum(c['passed'] for c in checks),'total_checks':len(checks),'checks':checks,'levels':rows,
        'run_directory':str(run),'freecad':cad,'calculix_version':'2.22 (bundled native binary)',
        'gmsh_version':gmsh.__version__,'units':'mm, N, MPa','geometry_status':'assumption; synthetic qualification specimen',
        'unit_conversion':'Analytical calculation: m, N, Pa. Native CAD/FE input: mm, N, MPa (1 m=1000 mm; 1 MPa=1e6 Pa).',
        'material_status':'assumption; isotropic E=70000 MPa nu=0.3, no material strength assumed',
        'limitations':['Not an aircraft structural model','No composite, buckling, fatigue, joints or failure validation',
                       'Displacement convergence does not prove stress convergence; root stresses excluded from strength claims']}
(OUT/'reports/fem_results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
install.update(verified=result['passed'],last_test_utc=result['timestamp'],test_report='outputs/reports/fem_results.json')
(ROOT/'work/setup/freecad_install.json').write_text(json.dumps(install,indent=2),encoding='utf-8')
print(json.dumps({'passed':result['passed'],'checks':len(checks),'run':str(run)},indent=2),flush=True)
raise SystemExit(0 if result['passed'] else 1)
