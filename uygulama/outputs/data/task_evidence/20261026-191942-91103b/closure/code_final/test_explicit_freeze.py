import unittest
from copy import deepcopy
from freeze_residual_probe import explicit_matched

class ExplicitFreezeGuards(unittest.TestCase):
    def setUp(self):
        self.c={'iterations':1,'not_a_convergence_control':True}
        self.text='TIME_DISCRE_FLOW= EULER_EXPLICIT\nTIME_DISCRE_TURB= EULER_EXPLICIT\nMGLEVEL= 0\n'
        self.row={f'{kind}[{k}]':-12. for kind in ['rms','max'] for k in ['Rho','RhoU','RhoV','RhoE','nu']}
        self.row.update(Inner_Iter=0,CD=.003,CL=0,Linear_Solver_Iterations=0,LinSolIterTurb=0,LinSolRes=float('-inf'))
        self.status={'exit_code':0,'stop_reason':None}
    def test_explicit_undefined_auxiliary_is_not_nonlinear_failure(self):
        m=explicit_matched(self.c,self.text,self.row,self.status);self.assertIsNone(m['LinSolRes']);self.assertEqual(m['last100_samples'],1)
    def test_implicit_may_not_use_explicit_exception(self):
        with self.assertRaises(AssertionError):explicit_matched(self.c,self.text.replace('EULER_EXPLICIT','EULER_IMPLICIT'),self.row,self.status)
    def test_nonfinite_required_residual_is_rejected(self):
        self.row['rms[Rho]']=float('-inf')
        with self.assertRaises(AssertionError):explicit_matched(self.c,self.text,self.row,self.status)
    def test_failed_native_is_rejected(self):
        self.status['exit_code']=1
        with self.assertRaises(AssertionError):explicit_matched(self.c,self.text,self.row,self.status)
    def test_missing_component_is_rejected(self):
        del self.row['max[nu]']
        with self.assertRaises(AssertionError):explicit_matched(self.c,self.text,self.row,self.status)

if __name__=='__main__':unittest.main(verbosity=2)
