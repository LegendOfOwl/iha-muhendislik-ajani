from pathlib import Path
from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).parent
PROJECT=ROOT/'outputs/projects/proje-e9319baef1'
CASE=PROJECT/'simulations/tmr_sharp_20261025_v1'
TASK=ROOT/'outputs/data/tasks/20261025-011533-2114a3.json'


def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(n,ctypes.c_ulonglong) for n in
        ['total_phys','avail_phys','total_page','avail_page','total_virtual','avail_virtual','avail_extended']]


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in
        ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
         'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage']]


def memory():
    state=MEMORYSTATUSEX();state.length=ctypes.sizeof(state)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state))
    return {'total_GiB':state.total_phys/2**30,'available_GiB':state.avail_phys/2**30}


def run_native(command,cwd,logname,seconds,env=None,memory_cap_gib=8):
    cwd=Path(cwd);status_path=cwd/(logname+'.status.json')
    assert not status_path.exists(),status_path
    start=time.monotonic();startutc=now();peak=0.0
    with (cwd/(logname+'.log')).open('w',encoding='utf-8') as log:
        process=subprocess.Popen([str(x) for x in command],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD]
        handle=wintypes.HANDLE(int(process._handle))
        created=wintypes.FILETIME();exited=wintypes.FILETIME();kernel=wintypes.FILETIME();user=wintypes.FILETIME()
        assert ctypes.windll.kernel32.GetProcessTimes(handle,ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel),ctypes.byref(user))
        ticks=(created.dwHighDateTime<<32)+created.dwLowDateTime
        save(cwd/(logname+'.process.json'),{'pid':process.pid,'executable':str(command[0]),'created_filetime':ticks,
                                           'started_utc':startutc,'budget_s':seconds,'command':[str(x) for x in command]})
        reason=None
        while process.poll() is None:
            counter=PROCESS_MEMORY_COUNTERS();counter.cb=ctypes.sizeof(counter)
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counter),counter.cb):
                peak=max(peak,counter.WorkingSetSize/2**30)
            if time.monotonic()-start>seconds:reason='time_budget_exceeded'
            elif peak>memory_cap_gib:reason='working_set_budget_exceeded'
            elif memory()['available_GiB']<1.0:reason='system_available_RAM_below_1GiB'
            if reason:
                process.kill();break
            time.sleep(.5)
        exit_code=process.wait()
    status={'started_utc':startutc,'ended_utc':now(),'exit_code':exit_code,'seconds':time.monotonic()-start,
            'stop_reason':reason,'peak_working_set_GiB':peak,'budget_s':seconds,'command':[str(x) for x in command]}
    save(status_path,status)
    return status


if __name__=='__main__':print(json.dumps(memory()))
