from common import ROOT,PROJECT,CASE,read
import os
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mesh_audit import load_mesh


def main():
    reader=vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(PROJECT/'data/tmr_sharp_20261025_v1/source_fine_mesh.vtu'));reader.Update()
    plane=vtk.vtkPlane();eta=.2;b=1.4760179762198;y=eta*b
    plane.SetOrigin(0,y,0);plane.SetNormal(0,1,0)
    cutter=vtk.vtkCutter();cutter.GenerateTrianglesOff();cutter.SetCutFunction(plane);cutter.SetInputData(reader.GetOutput());cutter.Update()
    edges=vtk.vtkExtractEdges();edges.SetInputConnection(cutter.GetOutputPort());edges.Update();g=edges.GetOutput()
    pts=vtk_to_numpy(g.GetPoints().GetData());connect=vtk_to_numpy(g.GetLines().GetConnectivityArray()).reshape(-1,2)
    segments=pts[connect][:,:,[0,2]]
    le=np.tan(np.deg2rad(29.999))*y;c=1+(0.5625159852668158-1)*eta;te=le+c
    fig,axes=plt.subplots(2,2,figsize=(12,9))
    for ax in axes.flat[:3]:
        ax.add_collection(LineCollection(segments,colors='#477281',linewidths=.35))
        ax.set_aspect('equal');ax.set(xlabel='x / normalized root chord',ylabel='z / normalized root chord');ax.grid(alpha=.15)
    axes[0,0].set(xlim=(le-.15,te+.4),ylim=(-.2,.2),title='Actual source volume-grid cut: eta=0.20')
    axes[0,1].set(xlim=(le-.025,le+.11),ylim=(-.065,.065),title='Leading-edge spacing')
    axes[1,0].set(xlim=(te-.12,te+.20),ylim=(-.06,.06),title='Trailing edge and near wake')
    xyz,cells,markers=load_mesh(CASE/'mesh_family_budget_v3/wing_strct.1.su2')
    wallsegments=[]
    for face in markers['WING3D']:
        q=xyz[face]
        for i in range(len(face)):
            if q[:,1].max()>.9*b:wallsegments.append(q[[i,(i+1)%len(face)]][:,[0,1]])
    ax=axes[1,1];ax.add_collection(LineCollection(wallsegments,colors='#477281',linewidths=.4))
    ax.set(xlim=(.7,1.43),ylim=(.9*b,1.515),xlabel='x / root chord',ylabel='y / root chord',title='Rounded-tip surface mesh, plan view');ax.set_aspect('equal');ax.grid(alpha=.15)
    fig.suptitle('TMR source geometry: 258,048 cells; geometry/topology screens only',fontsize=14)
    fig.tight_layout();dest=PROJECT/'plots/tmr_source_mesh_regions_20261025.png'
    fig.savefig(dest,dpi=165);plt.close(fig)
    print(dest)


if __name__=='__main__':main()
