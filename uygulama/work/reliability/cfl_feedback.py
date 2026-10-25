"""A second, conditional discrimination stage: bounded SU2 CFL feedback on/off."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
from linear_pair import ROOT, PROJECT, RUN as FIRST, REPORT as FIRST_REPORT, cfg, sha, read, save, history, now
from advisor import verify_evidence, iterative_gate

RUN=PROJECT/'simulations/m6_cfl_feedback_20261025'
REPORT=PROJECT/'reports/m6_cfl_feedback_20261025.json'


def prepare():
    prior=read(FIRST_REPORT)
    assert prior['pair']['comparable'] and not prior['pair']['effect_passed'], 'Conditional next-stage trigger not met'
    assert not RUN.exists(), 'Do not overwrite a trial'
    seedfolder=FIRST/'lin40';sealpath=seedfolder/'prediction_frozen.json';seal=read(sealpath)
    assert not verify_evidence(ROOT,seal['files_sha256'])
    assert seal['matched']['field_iteration']==999
    source=cfg(seedfolder/'case.cfg')
    assert source['CFL_ADAPT']=='NO' and source['CFL_NUMBER']=='4' and source['LINEAR_SOLVER_ITER']=='40'
    RUN.mkdir(parents=True)
    for name,enabled in [('fixed','NO'),('adaptive','YES')]:
        folder=RUN/name;folder.mkdir()
        shutil.copyfile(seedfolder/'mesh.su2',folder/'mesh.su2')
        shutil.copyfile(seedfolder/'restart_flow_000999.dat',folder/'seed.dat')
        d=dict(source)
        d.update(ITER='600',CONV_STARTITER='601',CFL_ADAPT=enabled,
                 CFL_ADAPT_PARAM='( 0.5, 1.2, 4.0, 40.0, 0.001, 25 )',
                 HISTORY_OUTPUT='( ITER, RMS_RES, MAX_RES, AERO_COEFF, LINSOL, CFL_NUMBER )')
        (folder/'case.cfg').write_text('\n'.join(f'{k}= {v}' for k,v in d.items())+'\n',encoding='ascii')
    configs=[cfg(RUN/n/'case.cfg') for n in ['fixed','adaptive']]
    diff=[k for k in configs[0].keys()|configs[1].keys() if configs[0].get(k)!=configs[1].get(k)]
    assert diff==['CFL_ADAPT']
    executable=Path(read(ROOT/'work/setup/su2_install.json')['executable'])
    save(RUN/'contract.json',{'created_utc':now(),'version':1,'project_id':'proje-e9319baef1',
        'conditional_trigger':'Stage1 cap control failed the preregistered0.3-log effect; nonlinear flow remains slowly converging at fixedCFL4.',
        'trigger_report_sha256':sha(FIRST_REPORT),'source_seal_sha256':sha(sealpath),
        'source_checkpoint':str((seedfolder/'restart_flow_000999.dat').relative_to(ROOT)),
        'executable':str(executable.relative_to(ROOT)),'executable_sha256':sha(executable),
        'only_pair_difference':diff,'order':['fixed','adaptive'],'iterations_each':600,'max_seconds_each':1200,'threads':4,
        'rationale':'Test pseudo-time acceleration with bounded feedback instead of more cap values or global mesh growth. SU2 built-in feedback; not a new integration scheme.',
        'policy':'CFL min4/max40; down0.5/up1.2; acceptable relative linear residual0.001; activate after25 iterations. Both configs carry the same parameters.',
        'source':'https://github.com/su2code/SU2/blob/v8.5.0/config_template.cfg#L1449-L1455',
        'common_stopping_metadata':'Disable automatic stop before600 only to compare equal batches; acceptance thresholds remain unchanged.',
        'common_changes_from_seed_case':{k:{'old':source.get(k),'new':v} for k,v in configs[0].items() if source.get(k)!=v},
        'thresholds_unchanged':read(FIRST/'contract.json')['thresholds_unchanged'],
        'diagnostic_effect_log10_min':.3,'preselected_candidate':'adaptive',
        'stop_policy':'One pair only; timeout/failure is retained. No subsequent CFL sweep authorized by this batch.',
        'scope':'One fixed M6 mesh and existing physical conditions; numerical diagnostic, not blind/mesh/experimental qualification.',
        'cases':{n:{p.name:sha(p) for p in (RUN/n).iterdir()} for n in ['fixed','adaptive']},'code_sha256':sha(__file__)})
    print('CFL_FEEDBACK_PAIR_PREPARED',flush=True)


def run(resume=False):
    contract=read(RUN/'contract.json');exe=ROOT/contract['executable'];assert sha(exe)==contract['executable_sha256']
    for name in contract['order']:
        folder=RUN/name
        if resume and (folder/'process.json').exists():
            if not (folder/'run_status.json').exists():
                adopt(folder,contract)
            continue
        assert not (folder/'process.json').exists()
        assert all(sha(folder/f)==h for f,h in contract['cases'][name].items())
        start=time.monotonic();stamp=now()
        with (folder/'solver.log').open('w',encoding='utf-8') as log:
            p=subprocess.Popen([str(exe),'case.cfg','-t','4'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),creationflags=subprocess.CREATE_NO_WINDOW)
            save(folder/'process.json',{'pid':p.pid,'started_utc':stamp,'budget_seconds':contract['max_seconds_each']})
            print(json.dumps({'started':name,'pid':p.pid}),flush=True)
            try:code=p.wait(timeout=contract['max_seconds_each']);status='exited'
            except subprocess.TimeoutExpired:p.kill();p.wait();code=None;status='timeout_partial_preserved'
        save(folder/'run_status.json',{'status':status,'exit_code':code,'started_utc':stamp,'ended_utc':now(),'seconds':time.monotonic()-start})
        print(json.dumps({'ended':name,'status':status,'exit_code':code}),flush=True)


def adopt(folder,contract):
    """Recover the running child after a wrapper-only logging error; never relaunch it."""
    import ctypes
    from ctypes import wintypes
    from datetime import datetime,timezone
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    k.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    k.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT]
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    record=read(folder/'process.json');handle=k.OpenProcess(0x100000|0x1000|0x0001,False,record['pid'])
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        size=wintypes.DWORD(32768);buffer=ctypes.create_unicode_buffer(size.value)
        if not k.QueryFullProcessImageNameW(handle,0,buffer,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
        assert Path(buffer.value).resolve()==(ROOT/contract['executable']).resolve(),'PID points at a different executable'
        c,e,kernel,user=[wintypes.FILETIME() for _ in range(4)]
        assert k.GetProcessTimes(handle,*map(ctypes.byref,[c,e,kernel,user]))
        created=((c.dwHighDateTime<<32)|c.dwLowDateTime)/1e7-11644473600
        started=datetime.fromisoformat(record['started_utc']).timestamp()
        assert 0<=created-started<10,'PID creation time does not match the recorded launch'
        elapsed=time.time()-started;remaining=max(0,contract['max_seconds_each']-elapsed)
        save(folder/'wrapper_recovery.json',{'recovered_utc':now(),'pid':record['pid'],'executable_checked':buffer.value,
             'creation_time_matches':True,'reason':'Python wrapper lacked json import after Popen; native child continued with unchanged config. Reattached by OS handle.',
             'failed_wrapper':'work/reliability/cfl_feedback_v1_wrapper_error.py','failed_sha256':contract['code_sha256'],
             'recovery_code_sha256':sha(__file__),'native_rerun':False})
        print(json.dumps({'adopted':folder.name,'pid':record['pid']}),flush=True)
        waited=k.WaitForSingleObject(handle,int(remaining*1000))
        if waited==258:
            assert k.TerminateProcess(handle,1);k.WaitForSingleObject(handle,30000)
            status,code='timeout_partial_preserved',None
        elif waited==0:
            value=wintypes.DWORD();assert k.GetExitCodeProcess(handle,ctypes.byref(value));code=value.value;status='exited'
        else:raise ctypes.WinError(ctypes.get_last_error())
        save(folder/'run_status.json',{'status':status,'exit_code':code,'started_utc':record['started_utc'],
             'ended_utc':now(),'seconds':time.time()-started,'wrapper_recovered_without_native_restart':True})
        print(json.dumps({'ended':folder.name,'status':status,'exit_code':code}),flush=True)
    finally:k.CloseHandle(handle)


def freeze():
    contract=read(RUN/'contract.json')
    for name in contract['order']:
        folder=RUN/name;assert (folder/'run_status.json').exists();assert not (folder/'prediction_frozen.json').exists()
        rows=history(folder/'history.csv') if (folder/'history.csv').exists() else []
        common=None
        for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')]:
            iters={int(p.stem.rsplit('_',1)[-1]) for p in folder.glob(f'{prefix}_*.{ext}') if p.stem.rsplit('_',1)[-1].isdigit()}
            common=iters if common is None else common&iters
        common &= {int(r['Inner_Iter']) for r in rows}
        selected=max(common) if common else None
        gate=iterative_gate(rows,selected,contract['thresholds_unchanged'])
        row=next((r for r in rows if r['Inner_Iter']==selected),None)
        save(folder/'prediction_frozen.json',{'frozen_utc':now(),'contract_sha256':sha(RUN/'contract.json'),
             'matched':{'field_iteration':selected,'terminal_history_iteration':rows[-1]['Inner_Iter'],
                        'CL':row['CL'],'CD':row['CD'],'rms[Rho]':row['rms[Rho]'],'iteration_checks':gate.get('checks',{})} if row else None,
             'iterative_gate':gate,'no_new_experimental_score_yet':True,'not_blind':True,
             'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()}})
    print('CFL_FEEDBACK_PAIR_FROZEN')


if __name__=='__main__':
    {'prepare':prepare,'run':run,'resume':lambda:run(True),'freeze':freeze}[sys.argv[1]]()
