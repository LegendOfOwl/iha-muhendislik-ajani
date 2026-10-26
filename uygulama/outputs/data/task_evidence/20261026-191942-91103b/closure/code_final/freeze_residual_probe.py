"""Freeze an explicit observation; undefined implicit-solver auxiliary is null."""
from prepare import ROOT,read,save,sha,now
from prepare_residual_probe import PROBE
from run import history
import math

def explicit_matched(c,text,row,status):
    assert c['iterations']==1 and c['not_a_convergence_control'] is True
    for line in ['TIME_DISCRE_FLOW= EULER_EXPLICIT','TIME_DISCRE_TURB= EULER_EXPLICIT','MGLEVEL= 0']:
        assert text.splitlines().count(line)==1
    assert status['exit_code']==0 and status['stop_reason'] is None
    assert row['Inner_Iter']==0
    required=[k for k in row if k.startswith(('rms[','max['))]+['CD','CL']
    assert len([k for k in required if k.startswith('rms[')])==5 and len([k for k in required if k.startswith('max[')])==5
    assert all(math.isfinite(row[k]) for k in required)
    assert row['Linear_Solver_Iterations']==row['LinSolIterTurb']==0
    return {'field_iteration':0,'terminal_history_iteration':0,**{k:row[k] for k in required},
       'Linear_Solver_Iterations':0,'LinSolRes':None,'LinSolResTurb':None,'last100_samples':1,'CD_last100_range':0.,
       'undefined_auxiliary_reason':'No implicit linear system solved in EULER_EXPLICIT diagnostic.'}

def main():
    folder=PROBE/'explicit';target=folder/'prediction_frozen.json';assert not target.exists()
    s=read(folder/'solver.status.json');assert s['exit_code']==0 and s['stop_reason'] is None
    h=history(folder);assert len(h)==1 and h[0]['Inner_Iter']==0
    for p in ['flow_000000.vtu','surface_flow_000000.vtu','restart_flow_000000.dat']:assert (folder/p).exists()
    row=h[0];c=read(PROBE/'contract.json');assert sha(folder/'case.cfg')==c['config_sha256']
    m=explicit_matched(c,(folder/'case.cfg').read_text(),row,s)
    failure={'recorded_utc':now(),'type':'wrapper_auxiliary_semantics_error','native_exit_code':0,
       'original_wrapper':'prepare_residual_probe.py run -> cfl_control.freeze_folder assert(all matched finite)',
       'observation':'Explicit solver has no linear solve; raw history LinSolRes/LinSolResTurb=-inf. All10 required nonlinear RMS/MAX values are finite.',
       'correction':'Scoped explicit seal omits undefined implicit linear solver auxiliary from required finite measurements; raw files unchanged, no native retry.',
       'not_a_physical_gate_relaxation':True}
    save(folder/'wrapper_freeze_failure.json',failure)
    save(target,{'frozen_utc':now(),'not_blind':True,'contract_sha256':sha(PROBE/'contract.json'),'mesh_sha256':c['mesh_sha256'],
       'matched':m,'native_status':s,'freeze_recovery':failure,'not_convergence_qualification':True,
       'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in folder.iterdir() if p.is_file()}})
    print({'native_completed_once':True,'required_nonlinear_metrics':12,'implicit_auxiliary':None,'field':0})

if __name__=='__main__':main()
