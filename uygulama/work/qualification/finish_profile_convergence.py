"""Continue the identical fine mesh/conditions from a saved native restart, retaining both runs."""
from copy import deepcopy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
from profile_cfd import ROOT,OUT,sha,save,replace,execute,history
def main():
    report=OUT/'reports/profile_cfd_results.json';old=json.loads(report.read_text());case=OUT/'data/profile_cfd_case.json';cfg=json.loads(case.read_text())
    if old['input_case_sha256']!=sha(case) or old['geometry_sha256']!=sha(ROOT/cfg['airfoil']):raise ValueError('Changed inputs cannot reuse restart')
    row=old['results'][-1];src=Path(row['folder'])
    run=OUT/'simulations'/('profile_cfd_continue_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir();folder=run/'fine';folder.mkdir()
    for name in ['mesh.su2','mesh.msh','restart_flow.dat','case.cfg']:shutil.copy2(src/name,folder/name)
    if sha(folder/'mesh.su2')!=row['mesh']['mesh_sha256']:raise ValueError('Restart mesh changed')
    text=(folder/'case.cfg').read_text()
    for key,value in {'RESTART_SOL':'YES','SOLUTION_FILENAME':'restart_flow.dat','CONV_RESIDUAL_MINVAL':-10,'ITER':6000}.items():text=replace(text,key,value)
    (folder/'case.cfg').write_text(text)
    binary=json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'];command=[binary,'case.cfg','-t','2'];save(folder/'command.json',command)
    seconds=execute(command,folder,'native.log',timeout=480);hist=history(folder/'history.csv');last=hist[-1];tail=hist[-100:]
    fresh=deepcopy(row);dcl=max(r['CL'] for r in tail)-min(r['CL'] for r in tail);dcd=max(r['CD'] for r in tail)-min(r['CD'] for r in tail)
    fresh.update(folder=str(folder),seconds=seconds,CL=last['CL'],CD_numerical_inviscid=last['CD'],log10_density_residual=last['rms[Rho]'],CL_tail_range=dcl,CD_tail_range=dcd,
        iterative_passed=last['rms[Rho]']<-7 and dcl<2e-4 and dcd<2e-5,restart_from=str(src),restart_input_sha256=sha(src/'restart_flow.dat'))
    result=deepcopy(old);result['results'][-1]=fresh;result['timestamp']=datetime.now(timezone.utc).isoformat()
    result['CL_grid_relative_change']=abs(fresh['CL']/result['results'][0]['CL']-1)
    result['CL_reference_relative_difference']=abs(fresh['CL']/result['reference']['CL']-1)
    result['quality_passed']=all(r['iterative_passed'] for r in result['results']) and result['CL_grid_relative_change']<.03 and result['CL_reference_relative_difference']<.05 and abs(fresh['CD_numerical_inviscid'])<.003
    result.update(run_directory=str(run),previous_run_directory=old['run_directory'],continuation_note='Same mesh/conditions; saved native restart continued to check force stability. Original failed acceptance is retained.')
    save(run/'results.json',result);save(report,result);print(json.dumps({'fine':fresh,'quality_passed':result['quality_passed'],'grid_CL':result['CL_grid_relative_change'],'reference_CL':result['CL_reference_relative_difference']},indent=2))
if __name__=='__main__':main()
