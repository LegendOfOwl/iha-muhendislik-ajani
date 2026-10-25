"""Counterexamples for the new parser/Jacobian and actual native SA-neg option repair."""
from common import ROOT,BASE,CASE,PROJECT,read,save,sha,now
from mesh_audit import load_mesh,topology,hex_jacobians,SIGNS,FACES
from pathlib import Path
import tempfile
import unittest
import numpy as np


class Guards(unittest.TestCase):
    def cube(self,extra_id=False):
        xyz=(SIGNS+1)/2
        text='NDIME= 3\nNELEM= 1\n12 0 1 2 3 4 5 6 7 0\nNPOIN= 8\n'
        text+=''.join(' '.join(map(str,p))+f' {i}\n' for i,p in enumerate(xyz))
        text+='NMARK= 3\n'
        for name,faces in [('WING3D',FACES[12][:1]),('SYMMETRY',FACES[12][1:2]),('FARFIELD',FACES[12][2:])]:
            text+=f'MARKER_TAG= {name}\nMARKER_ELEMS= {len(faces)}\n'
            for face in faces:text+='9 '+' '.join(map(str,face))+(' 0' if extra_id else '')+'\n'
        return text

    def test_optional_boundary_ID_inside_valid_node_range(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            p=Path(temp)/'cube.su2';p.write_text(self.cube(True))
            xyz,cells,markers=load_mesh(p)
            self.assertTrue(all(len(f)==4 for a in markers.values() for f in a))
            self.assertTrue(topology(cells,markers)['boundary_exactly_matches_exterior'])

    def test_wrong_boundary_topology_rejected(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            p=Path(temp)/'cube.su2';p.write_text(self.cube())
            _,cells,markers=load_mesh(p)
            markers['WING3D'][0]=[0,1,2,7]
            with self.assertRaises(AssertionError):topology(cells,markers)

    def test_thin_valid_BL_cell_and_inverted_cell(self):
        cube=(SIGNS+1)/2;cube[:,2]*=1e-7
        self.assertGreater(hex_jacobians(cube[None])[0][0],0)
        cube[:,0]*=-1
        self.assertLess(hex_jacobians(cube[None])[0][0],0)

    def test_actual_native_standard_SAneg_repair(self):
        bad=CASE/'flow_smoke';good=CASE/'flow_v2_smoke'
        a=read(bad/'prediction_frozen.json');b=read(good/'prediction_frozen.json')
        self.assertNotEqual(a['native_status']['exit_code'],0)
        self.assertIsNone(a['matched'])
        self.assertIn('non-standard version of SA-neg',(bad/'solver.log').read_text())
        self.assertEqual(b['native_status']['exit_code'],0)
        self.assertEqual(b['matched']['field_iteration'],19)
        self.assertNotIn('EXPERIMENTAL',(good/'case.cfg').read_text())
        def cfg(p):return {k.strip():v.strip() for k,v in (x.split('=',1) for x in p.read_text().splitlines() if '=' in x)}
        old=cfg(bad/'case.cfg');new=cfg(good/'case.cfg')
        self.assertEqual([k for k in old if old[k]!=new[k]],['SA_OPTIONS'])

    def test_slice_triangulation_does_not_become_source_mesh_edges(self):
        from mesh_audit import vtk_grid
        import vtk
        g=vtk_grid((SIGNS+1)/2,{12:np.arange(8).reshape(1,8)})
        plane=vtk.vtkPlane();plane.SetOrigin(0,.5,0);plane.SetNormal(0,1,0)
        def edges(triangles):
            c=vtk.vtkCutter();c.SetGenerateTriangles(triangles);c.SetCutFunction(plane);c.SetInputData(g)
            e=vtk.vtkExtractEdges();e.SetInputConnection(c.GetOutputPort());e.Update()
            return e.GetOutput().GetNumberOfCells()
        self.assertEqual(edges(False),4)
        self.assertEqual(edges(True),5)

    def test_quad_bilinear_pressure_integral(self):
        from field_checks import face_quadrature
        pts=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],float)
        cp=np.array([0,0,1,0],float)
        area=sum(np.linalg.norm(av) for N,av,p in face_quadrature(pts))
        force=sum(float(N@cp)*av[2] for N,av,p in face_quadrature(pts))
        self.assertAlmostEqual(area,1)
        self.assertAlmostEqual(force,.25)
        # Diagonal triangulation integrates the same nodal values as1/3 instead.
        legacy=(cp[[0,1,2]].mean()+cp[[0,2,3]].mean())/2
        self.assertAlmostEqual(legacy,1/3)

    def test_node_dual_area_and_constant_pressure(self):
        from field_checks import dual_node_normals
        pts=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],float)
        normal=dual_node_normals(pts)
        np.testing.assert_allclose(normal[:,2],.25)
        np.testing.assert_allclose(normal.sum(0),[0,0,1])

    def test_inside_solid_is_not_zero_distance_to_surface(self):
        import cadquery as cq
        solid=cq.Solid.makeBox(1,1,1);center=cq.Vertex.makeVertex(.5,.5,.5)
        boundary=cq.Compound.makeCompound(solid.Faces())
        self.assertEqual(solid.distance(center),0)
        self.assertAlmostEqual(boundary.distance(center),.5)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Guards)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    save(PROJECT/'reports/tmr_mesh_guards_20261025.json',{'checked_utc':now(),'tests':result.testsRun,
        'passed':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),
        'native_counterexample_source':'Failed NEGATIVE-only config vs standard NEGATIVE,WITHFT2; this is not physical validation.'})
    raise SystemExit(not result.wasSuccessful())
