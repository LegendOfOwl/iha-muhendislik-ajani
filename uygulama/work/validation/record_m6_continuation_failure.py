"""Retain bounded unsuccessful continuation without substituting mismatched fields."""
import json,hashlib,sys,csv
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/validation'))
from compare_m6 import comparison,experimental
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pid=read(ROOT/'work/validation/projects.json')['cfd'];out=ROOT/'outputs/projects'/pid
    report=out/'reports/m6_rans_results.json';raw=read(report)
    initial=Path(raw['run_directory']);run=out/'simulations/m6_rans_continue_20261019_113927'
    contract=read(run/'continuation_contract.json');assert raw['conditions_sha256']==contract['conditions_sha256']
    assert raw['thresholds']==contract['thresholds']
    coarse=read(run/'results_in_progress.json')[0];groups,checks=experimental()
    coarse_comparison,_,_=comparison(coarse,groups);save(run/'coarse_experiment_comparison.json',coarse_comparison)
    source=raw['results'][1];folder=run/source['grid']
    with (folder/'history.csv').open() as f:h=[{k.strip().strip('"'):float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    assert all(np.isfinite(list(r.values())).all() for r in h);last=h[-1];tail=h[-100:]
    fine={'grid':source['grid'],'folder':str(folder),'iterations':len(h),'last_inner_iteration':int(last['Inner_Iter']),'CL':float(last['CL']),'CD':float(last['CD']),'log10_density_residual':float(last['rms[Rho]']),'CL_tail_range':float(np.ptp([r['CL'] for r in tail])),'CD_tail_range':float(np.ptp([r['CD'] for r in tail])),'runtime_passed':False,'iterative_passed':False,'timeout_seconds':900,'stop_reason':'subprocess.TimeoutExpired at 900 s; no final surface/volume output','mesh_sha256':sha(folder/'mesh.su2'),'restart_input_sha256':sha(Path(source['folder'])/'restart_flow.dat')}
    assert fine['mesh_sha256']==source['mesh']['mesh_sha256']
    assert sha(folder/'restart_flow.dat')==fine['restart_input_sha256']
    assert not (folder/'surface_flow.vtu').exists()
    diagnostic={'completed':False,'quality_passed':False,'requested_iterations_per_grid':500,'conditions_and_thresholds_unchanged':True,'run_directory':str(run),'results':[coarse,fine],'coarse_Cp_metrics':coarse_comparison,'fine_Cp_metrics':None,'experiment_report_uses':'Two completed initial 4000-iteration solutions. No final finer continuation field exists; no mismatched Cp/y+ comparison manufactured.'}
    save(run/'failure_diagnostic.json',diagnostic);save(out/'reports/m6_continuation_diagnostic.json',diagnostic)
    raw.update(previous_run_directory=str(initial),continuation_run_directory=str(run),continuation_complete=False,continuation_diagnostic_report=str(out/'reports/m6_continuation_diagnostic.json'),continuation_note='Coarse500 completed but unstable; finer timed out after900s. Main paired experiment comparison retains initial complete fields.')
    save(report,raw);print(json.dumps(diagnostic,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
