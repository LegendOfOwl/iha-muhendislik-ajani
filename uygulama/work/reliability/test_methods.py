"""Adversarial evidence cases and analytic checks independent of CFD answers."""
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
import numpy as np
from advisor import sha, verify_evidence, iterative_gate, choose_next, audit_registered
from curvature import reconstruct, indicator


class EvidenceTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform=='win32','Windows native process recovery')
    def test_wrapper_recovery_preserves_nonzero_exit(self):
        from cfl_feedback import adopt, save, now
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name);stamp=now()
            p=subprocess.Popen([sys._base_executable,'-c','import time;time.sleep(0.7);raise SystemExit(7)'],
                               creationflags=subprocess.CREATE_NO_WINDOW)
            save(folder/'process.json',{'pid':p.pid,'started_utc':stamp})
            adopt(folder,{'executable':sys._base_executable,'max_seconds_each':10,'code_sha256':'fixture'})
            self.assertEqual(json.loads((folder/'run_status.json').read_text())['exit_code'],7)
            self.assertFalse(json.loads((folder/'wrapper_recovery.json').read_text())['native_rerun'])
            p.wait()

    def test_raw_audit_overrides_saved_pass_and_rejects_corrupt_field(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);folder=root/'case';folder.mkdir()
            contract={'project_id':'demo','iterations_each':100,
                      'thresholds_unchanged':{'density_log10_max':-7,'CL_last100_range_max':.0002,'CD_last100_range_max':.00002}}
            (root/'contract.json').write_text(json.dumps(contract))
            (folder/'history.csv').write_text('Inner_Iter,CL,CD,rms[Rho]\n'+''.join(f'{i},.3,.02,-6.9\n' for i in range(100)))
            for filename in ['flow_000099.vtu','surface_flow_000099.vtu','restart_flow_000099.dat']:
                (folder/filename).write_bytes(b'unchanged dummy field for provenance test')
            (folder/'run_status.json').write_text(json.dumps({'exit_code':0}))
            seal={'matched':{'field_iteration':99},'contract_sha256':sha(root/'contract.json'),
                  'files_sha256':{str(p.relative_to(root)):sha(p) for p in folder.iterdir()}}
            (folder/'prediction_frozen.json').write_text(json.dumps(seal))
            spec={'project_id':'demo','contract':'contract.json','preselected_case':'case',
                  'cases':[{'name':'case','folder':'case'}],
                  'evidence_sha256':{str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()},
                  'state':{'checkpoint_complete':True,'iteration_passed':True,'remaining_native_runs':0}}
            audit=audit_registered(root,spec,'demo')
            self.assertTrue(audit['passed'])
            self.assertFalse(audit['raw_recomputed']['case']['iterative_gate']['passed'])
            self.assertFalse(audit['quality_passed'])
            self.assertEqual(audit['recommendation']['action'],'diagnose_iteration')
            self.assertTrue(audit_registered(root,spec,'another-project')['evidence_errors'])
            (folder/'flow_000099.vtu').write_bytes(b'changed')
            self.assertEqual(audit_registered(root,spec,'demo')['recommendation']['action'],'repair_evidence')

    def test_changed_missing_and_outside(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);p=root/'field.dat';p.write_bytes(b'first')
            entries={'field.dat':sha(p)}
            self.assertEqual(verify_evidence(root,entries),[])
            p.write_bytes(b'changed')
            self.assertTrue(verify_evidence(root,entries))
            self.assertTrue(verify_evidence(root,{'absent':'0'*64}))
            self.assertTrue(verify_evidence(root,{'../outside':'0'*64}))
            self.assertTrue(verify_evidence(root,{}))

    def test_raw_threshold_and_contiguous_window(self):
        limits={'density_log10_max':-7,'CL_last100_range_max':.0002,'CD_last100_range_max':.00002}
        rows=[{'Inner_Iter':i,'CL':.3,'CD':.02,'rms[Rho]':-7.1} for i in range(100)]
        self.assertTrue(iterative_gate(rows,99,limits)['passed'])
        rows[-1]['rms[Rho]']=-6.999999999
        self.assertFalse(iterative_gate(rows,99,limits)['passed'])
        rows[-1]['rms[Rho]']=-7
        self.assertFalse(iterative_gate(rows,99,limits)['passed'])
        rows[-1]['rms[Rho]']=-7.1
        self.assertFalse(iterative_gate(rows[1:],99,limits)['passed'])
        self.assertFalse(iterative_gate(rows+[rows[-1]],99,limits)['passed'])
        rows[2]['CL']=float('nan')
        self.assertFalse(iterative_gate(rows,99,limits)['passed'])
        self.assertFalse(iterative_gate(rows,None,limits)['passed'])

    def test_precedence_and_no_repeat_sweep(self):
        state={'checkpoint_complete':True,'iteration_passed':False,'linear_cap_saturated':True,
               'remaining_native_runs':2,'regional_mesh_passed':False}
        self.assertEqual(choose_next(state)['action'],'controlled_linear_pair')
        state['linear_pair']={'comparable':True,'effect_passed':False}
        self.assertEqual(choose_next(state)['action'],'localize_nonlinear_stall')
        state['evidence_errors']=['changed seed']
        self.assertEqual(choose_next(state)['action'],'repair_evidence')
        state['evidence_errors']=[];state['iteration_passed']=True
        self.assertEqual(choose_next(state)['action'],'regional_mesh_control')
        state['remaining_native_runs']=0
        self.assertTrue(choose_next(state)['native_action_budget_blocked'])
        self.assertFalse(choose_next(state)['new_physical_acceptance'])
        state['checkpoint_complete']=False
        self.assertEqual(choose_next(state)['action'],'recover_checkpoint')


class CurvatureTests(unittest.TestCase):
    def test_cell_outside_fit_support_is_rejected(self):
        from curvature_v2 import support_covered
        cube=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]],dtype=float)
        inside=np.array([[0,0,0],[.1,0,0],[0,.1,0],[0,0,.1]])
        self.assertTrue(support_covered(cube,inside))
        outside=inside.copy();outside[0,0]=1.001
        self.assertFalse(support_covered(cube,outside))
        # A point inside the componentwise box can still be outside a tetrahedron.
        tetra=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],dtype=float)
        self.assertFalse(support_covered(tetra,np.array([[.6,.6,.6]])))
    @classmethod
    def setUpClass(cls):
        cls.points=np.random.default_rng(4720).uniform(-1,1,(250,3))
        cls.centers=np.array([[0,0,0],[.2,-.1,.1]])

    def test_affine_zero_curvature(self):
        f=3+self.points@np.array([2,-1,.5])
        h,valid,*_=reconstruct(self.points,f,self.centers)
        self.assertTrue(valid.all())
        np.testing.assert_allclose(h,0,atol=3e-13)

    def test_quadratic_rotated_anisotropic(self):
        theta=.7
        rotation=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1]])
        points=(self.points*np.array([1,.02,.0001]))@rotation.T
        expected=np.array([[2,.4,-.2],[.4,4,.1],[-.2,.1,6]])
        f=.5*np.einsum('ni,ij,nj->n',points,expected,points)+points@np.array([.5,-1,.1])+7
        h,valid,*_=reconstruct(points,f,np.zeros((1,3)))
        self.assertTrue(valid.all())
        np.testing.assert_allclose(h[0],expected,atol=2e-6)

    def test_barycentric_quadratic_identity(self):
        vertices=np.array([[[0,0,0],[1,0,0],[0,1,0],[0,0,1]]],dtype=float)
        h=np.diag([2.,4.,6.])[None]
        value,direction=indicator(h,vertices)
        def exact(p):return .5*np.einsum('...i,ij,...j->...',p,h[0],p)
        error=exact(vertices[0]).mean()-exact(vertices[0].mean(0))
        self.assertAlmostEqual(value[0],error,places=13)
        self.assertAlmostEqual(abs(direction[0,2]),1)
        # Same physical field, lengths in mm: H_mm = H_m / 1e6.
        converted,_=indicator(h/1e6,vertices*1000)
        np.testing.assert_allclose(value,converted,atol=1e-13)

    def test_degenerate_and_nonfinite(self):
        cloud=self.points.copy();cloud[:,2]=0
        h,valid,*_=reconstruct(cloud,np.sum(cloud**2,axis=1),self.centers)
        self.assertFalse(valid.any());self.assertTrue(np.isnan(h).all())
        bad=self.points.copy();bad[0,0]=np.nan
        with self.assertRaises(ValueError):reconstruct(bad,np.ones(len(bad)),self.centers)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=Path(__file__).resolve().parents[2]/'outputs/reports/reliability_method_tests.json'
    report.write_text(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),
                                 'failures':len(result.failures),'errors':len(result.errors),
                                 'scope':'Adversarial evidence and analytic reconstruction; no new CFD qualification.'},indent=2),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
