"""Native Elmer incompressible Navier-Stokes; three-mesh exact Poiseuille verification."""
from datetime import datetime,timezone
import json
import os
import re
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import gmsh
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def write(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def execute(command,folder,log,env):
    start=time.perf_counter()
    with (folder/log).open('w',encoding='utf-8') as f:
        p=subprocess.run(command,cwd=folder,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
            timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode: raise RuntimeError(f'{Path(command[0]).name}: exit {p.returncode}; {folder/log}')
    return time.perf_counter()-start

def mesh(folder,n):
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0); gmsh.model.add('channel')
        g=gmsh.model.geo
        a=g.addPoint(0,0,0); b=g.addPoint(4,0,0); c=g.addPoint(4,1,0); d=g.addPoint(0,1,0)
        lines=[g.addLine(a,b),g.addLine(b,c),g.addLine(c,d),g.addLine(d,a)]
        s=g.addPlaneSurface([g.addCurveLoop(lines)]); g.synchronize()
        for l in [lines[0],lines[2]]: gmsh.model.mesh.setTransfiniteCurve(l,4*n+1)
        for l in [lines[1],lines[3]]: gmsh.model.mesh.setTransfiniteCurve(l,n+1)
        gmsh.model.mesh.setTransfiniteSurface(s)
        for tag,edges in [(1,[lines[3]]),(2,[lines[1]]),(3,[lines[0],lines[2]])]: gmsh.model.addPhysicalGroup(1,edges,tag)
        gmsh.model.addPhysicalGroup(2,[s],1)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2); gmsh.model.mesh.generate(2); gmsh.write(str(folder/'channel.msh'))
    finally: gmsh.finalize()

SIF='''Header
  CHECK KEYWORDS Warn
  Mesh DB "." "mesh"
  Include Path ""
  Results Directory ""
End
Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals = 1
  Max Output Level = 4
End
Body 1
  Target Bodies(1) = 1
  Equation = 1
  Material = 1
End
Equation 1
  Active Solvers(2) = 1 2
End
Material 1
  Density = 1.0
  Viscosity = 0.01
End
Solver 1
  Equation = Navier-Stokes
  Procedure = "FlowSolve" "FlowSolver"
  Variable = Flow Solution[Velocity:2 Pressure:1]
  Variable DOFs = 3
  Flow Model = Navier-Stokes
  Stabilize = True
  Nonlinear System Convergence Tolerance = 1.0e-10
  Nonlinear System Max Iterations = 40
  Nonlinear System Newton After Iterations = 3
  Nonlinear System Newton After Tolerance = 1.0e-3
  Nonlinear System Relaxation Factor = 1.0
  Linear System Solver = Direct
  Linear System Direct Method = UMFPACK
  Steady State Convergence Tolerance = 1.0e-10
End
Solver 2
  Exec Solver = After Simulation
  Equation = ResultOutput
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "flow"
  Vtu Format = True
  Binary Output = False
  Save Geometry Ids = True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Velocity 1 = Variable Coordinate 2
    Real MATC "6*tx*(1-tx)"
  Velocity 2 = 0.0
End
Boundary Condition 2
  Target Boundaries(1) = 2
  Pressure = 0.0
  Velocity 2 = 0.0
End
Boundary Condition 3
  Target Boundaries(1) = 3
  Velocity 1 = 0.0
  Velocity 2 = 0.0
End
'''

def main():
    meta=json.loads((ROOT/'work/setup/elmer_install.json').read_text()); binary=Path(meta['executables']['ElmerSolver.exe'])
    prefix=binary.parent.parent; env=dict(os.environ)
    env.update(ELMER_HOME=str(prefix),ELMER_LIB=str(prefix/'share/elmersolver/lib'),ELMERGUI_HOME=str(prefix/'share/ElmerGUI'),OMP_NUM_THREADS='2')
    env['PATH']=str(binary.parent)+os.pathsep+str(prefix/'lib')+os.pathsep+env['PATH']
    run=OUT/'simulations'/('elmer_cfd_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    rows=[]
    for n in [5,10,20]:
        folder=run/f'n{n}'; folder.mkdir(); mesh(folder,n)
        print('ELMER native Navier-Stokes mesh',n,flush=True)
        try:
            eg=[meta['executables']['ElmerGrid.exe'],'14','2','channel.msh','-out','mesh','-autoclean']
            execute(eg,folder,'mesh_conversion.log',env)
            (folder/'case.sif').write_text(SIF,encoding='ascii')
            write(folder/'commands.json',{'mesh':eg,'solver':[str(binary),'case.sif']})
            sec=execute([str(binary),'case.sif'],folder,'native.log',env)
            log=(folder/'native.log').read_text(errors='replace')
            changes=re.findall(r'Relative Change\s*:\s*([0-9.EeDd+\-]+)',log)
            final_change=float(changes[-1].replace('D','E')) if changes else None
            files=list(folder.glob('*.vtu'))+list(folder.glob('*/*.vtu'))
            if not files: raise ValueError('Native solver produced no VTU field')
            reader=vtk.vtkXMLUnstructuredGridReader(); reader.SetFileName(str(files[-1])); reader.Update(); grid=reader.GetOutput()
            pd=grid.GetPointData(); names=[pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
            velocity=next((name for name in names if name.lower()=='velocity'),None)
            pressure=next((name for name in names if name.lower()=='pressure'),None)
            if not velocity or not pressure: raise ValueError('VTU arrays: '+str(names))
            xyz=vtk_to_numpy(grid.GetPoints().GetData()); vel=vtk_to_numpy(pd.GetArray(velocity)); p=vtk_to_numpy(pd.GetArray(pressure))
            u=6*xyz[:,1]*(1-xyz[:,1]); exactp=.12*(4-xyz[:,0]); interior=(xyz[:,0]>.2)&(xyz[:,0]<3.8)
            relu=float(np.linalg.norm(vel[interior,0]-u[interior])/np.linalg.norm(u[interior]))
            relp=float(np.linalg.norm(p[interior]-exactp[interior])/np.linalg.norm(exactp[interior]))
            flux=[]
            for x in [0,2,4]:
                mask=np.isclose(xyz[:,0],x); y=xyz[mask,1]; v=vel[mask,0]; idx=np.argsort(y)
                flux.append(float(np.trapezoid(v[idx],y[idx])))
            row={'mesh_n':n,'nodes':grid.GetNumberOfPoints(),'cells':grid.GetNumberOfCells(),'fluid_cells':sum(grid.GetCell(i).GetCellDimension()==2 for i in range(grid.GetNumberOfCells())),'seconds':sec,
                'final_nonlinear_relative_change':final_change,'native_nonlinear_convergence_passed':final_change is not None and final_change<1e-9,
                'VTU':str(files[-1]),'velocity_relative_L2_error':relu,'pressure_relative_L2_error':relp,
                'max_transverse_velocity':float(np.max(np.abs(vel[:,1]))),'volume_flux_m2_s':flux,
                'relative_in_out_imbalance':abs(flux[0]-flux[2])/abs(flux[0]),'runtime_passed':True,'folder':str(folder)}
            print(json.dumps(row),flush=True); rows.append(row)
        except Exception as exc:
            rows.append({'mesh_n':n,'runtime_passed':False,'error':str(exc),'folder':str(folder)}); print(str(exc),flush=True); break
        write(run/'in_progress.json',rows)
    runtime=len(rows)==3 and all(r['runtime_passed'] for r in rows)
    quality=runtime and all(r['native_nonlinear_convergence_passed'] for r in rows) and rows[-1]['velocity_relative_L2_error']<.02 and rows[-1]['pressure_relative_L2_error']<.05 and rows[-1]['relative_in_out_imbalance']<.002
    if runtime: quality=quality and all(b['velocity_relative_L2_error']<a['velocity_relative_L2_error'] and b['pressure_relative_L2_error']<a['pressure_relative_L2_error'] for a,b in zip(rows,rows[1:]))
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':runtime,'quality_passed':quality,'results':rows,
        'run_directory':str(run),'scope':'2D laminar incompressible channel; Re_H=100, H=1m, L=4m, rho=1 kg/m3, mu=.01 Pa.s, Umean=1m/s; synthetic verification',
        'exact_solution':'u=6*y*(1-y), v=0, p=0.12*(4-x); SI units',
        'limits':['Exact-solution solver verification, not aircraft or turbulent external-flow validation','RANS/transition/3D aircraft not qualified in Elmer by this test']}
    write(run/'results.json',result); write(OUT/'reports/elmer_cfd_qualification.json',result)
    if runtime:
        from view_elmer_fields import main as show_fields
        show_fields()
    print(json.dumps({'runtime_passed':runtime,'quality_passed':quality},indent=2),flush=True)
    return 0 if runtime else 1
if __name__=='__main__': raise SystemExit(main())
