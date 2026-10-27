"""Bounded Windows build process tree, with a suspended launch and a private job.

Only processes in the job created by this invocation are sampled or terminated.
No global environment, process policy, or unrelated process is changed. Working
set ceilings are sampled (0.1 s); kill-on-close is the orphan-prevention mechanism.
"""
from pathlib import Path
from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
GIB = 1024**3
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
CREATE_UNICODE_ENVIRONMENT = 0x00000400
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
ERROR_MORE_DATA = 234
SIZE_T = ctypes.c_size_t
ULONG_PTR = ctypes.c_size_t


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value, *, new=False):
    with Path(path).open('x' if new else 'w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def valid_number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def resource_stop_reason(elapsed, working_set_gib, available_gib, seconds, max_tree_gib, min_available_gib):
    """Fail closed on invalid samples. A value exactly at a WS/free bound is valid."""
    values = (elapsed, working_set_gib, available_gib, seconds, max_tree_gib, min_available_gib)
    if not all(valid_number(value) and value >= 0 for value in values) or seconds <= 0 or max_tree_gib <= 0:
        return 'invalid_resource_sample_or_budget'
    if elapsed >= seconds:
        return 'time_budget_exceeded'
    if working_set_gib > max_tree_gib:
        return 'process_tree_working_set_exceeded'
    if available_gib < min_available_gib:
        return 'system_available_memory_below_minimum'
    return None


def validated_label(label):
    if not isinstance(label, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', label):
        raise ValueError('Label must be a short filename token, not a path')
    if label.endswith('.') or label.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1, 10)), *('LPT'+str(i) for i in range(1, 10))}:
        raise ValueError('Reserved Windows filename label')
    return label


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR), ('lpDesktop', wintypes.LPWSTR),
                ('lpTitle', wintypes.LPWSTR), ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD), ('dwXCountChars', wintypes.DWORD),
                ('dwYCountChars', wintypes.DWORD), ('dwFillAttribute', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD), ('wShowWindow', wintypes.WORD),
                ('cbReserved2', wintypes.WORD), ('lpReserved2', ctypes.POINTER(ctypes.c_ubyte)),
                ('hStdInput', wintypes.HANDLE), ('hStdOutput', wintypes.HANDLE), ('hStdError', wintypes.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong), ('PerJobUserTimeLimit', ctypes.c_longlong),
                ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', SIZE_T),
                ('MaximumWorkingSetSize', SIZE_T), ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ULONG_PTR), ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ('ReadOperationCount', 'WriteOperationCount',
                'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION), ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', SIZE_T), ('JobMemoryLimit', SIZE_T),
                ('PeakProcessMemoryUsed', SIZE_T), ('PeakJobMemoryUsed', SIZE_T)]


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, SIZE_T) for name in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
        'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


def windows_api():
    if os.name != 'nt':
        raise RuntimeError('This process-tree runner requires Windows job objects')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    api.CreateJobObjectW.restype = wintypes.HANDLE
    api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    api.SetInformationJobObject.restype = wintypes.BOOL
    api.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    api.QueryInformationJobObject.restype = wintypes.BOOL
    api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    api.AssignProcessToJobObject.restype = wintypes.BOOL
    api.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    api.IsProcessInJob.restype = wintypes.BOOL
    api.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    api.TerminateJobObject.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    api.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
        wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)]
    api.CreateProcessW.restype = wintypes.BOOL
    api.ResumeThread.argtypes = [wintypes.HANDLE]
    api.ResumeThread.restype = wintypes.DWORD
    api.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    api.TerminateProcess.restype = wintypes.BOOL
    api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    api.WaitForSingleObject.restype = wintypes.DWORD
    api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    api.GetExitCodeProcess.restype = wintypes.BOOL
    api.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    api.GetProcessTimes.restype = wintypes.BOOL
    api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    return api, psapi


def checked(value, operation):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error(), operation)
    return value


def creation_identity(api, handle, pid):
    created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
    checked(api.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)), 'GetProcessTimes')
    ticks = (created.dwHighDateTime << 32) | created.dwLowDateTime
    timestamp = ticks / 1e7 - 11644473600
    return {'pid': int(pid), 'creation_filetime_100ns': ticks, 'creation_time_unix': timestamp,
            'creation_time_utc': datetime.fromtimestamp(timestamp, timezone.utc).isoformat()}


def exited(api, handle):
    value = api.WaitForSingleObject(handle, 0)
    if value not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
        raise ctypes.WinError(ctypes.get_last_error(), 'WaitForSingleObject')
    return value == WAIT_OBJECT_0


def exit_code(api, handle):
    if not exited(api, handle):
        return None
    code = wintypes.DWORD()
    checked(api.GetExitCodeProcess(handle, ctypes.byref(code)), 'GetExitCodeProcess')
    return int(code.value)


def job_pids(api, job):
    count = 64
    for _ in range(10):
        buffer = ctypes.create_string_buffer(8 + count * ctypes.sizeof(ULONG_PTR))
        written = wintypes.DWORD()
        success = api.QueryInformationJobObject(job, 3, buffer, len(buffer), ctypes.byref(written))
        assigned = wintypes.DWORD.from_buffer(buffer, 0).value
        listed = wintypes.DWORD.from_buffer(buffer, 4).value
        if success:
            if listed > count:
                raise RuntimeError('Invalid job PID-list length')
            values = (ULONG_PTR * listed).from_buffer(buffer, 8)
            return [int(pid) for pid in values]
        if ctypes.get_last_error() != ERROR_MORE_DATA:
            raise ctypes.WinError(ctypes.get_last_error(), 'QueryInformationJobObject PID list')
        count = max(count * 2, assigned + 8)
    raise RuntimeError('Job PID list kept growing beyond the bounded query')


def assign_process(api, job, handle):
    """Separate hook lets the failure guard verify that no process was resumed."""
    checked(api.AssignProcessToJobObject(job, handle), 'AssignProcessToJobObject')


def run_build(command, cwd, label, seconds, env=None, max_tree_gib=3, min_available_gib=1):
    import psutil
    label = validated_label(label)
    if not isinstance(command, (list, tuple)) or not command or not all(isinstance(x, (str, os.PathLike)) for x in command):
        raise ValueError('Command must be a nonempty argv list; no shell command strings')
    if resource_stop_reason(0, 0, min_available_gib, seconds, max_tree_gib, min_available_gib) is not None:
        raise ValueError('Invalid build resource budget')
    cwd = Path(cwd).resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError('Build cwd is not a directory')
    environment = dict(os.environ if env is None else env)
    if not all(isinstance(k, str) and isinstance(v, str) and '\0' not in k+v and '=' not in k for k, v in environment.items()):
        raise ValueError('Invalid Windows environment block')
    argv = [str(x) for x in command]
    if any('\0' in value for value in argv):
        raise ValueError('Embedded NUL in argv')
    requested = Path(argv[0])
    relative_candidate = cwd / requested if not requested.is_absolute() else requested
    executable = str(relative_candidate) if (('\\' in argv[0] or '/' in argv[0]) and relative_candidate.is_file()) else shutil.which(argv[0], path=environment.get('PATH'))
    if executable is None and Path(argv[0]).is_absolute() and Path(argv[0]).is_file():
        executable = argv[0]
    if executable is None:
        raise FileNotFoundError(argv[0])
    argv[0] = str(Path(executable).resolve(strict=True))
    process_path, status_path, log_path = (BASE / (label + suffix) for suffix in ('.process.json', '.status.json', '.log'))
    if any(path.exists() for path in (process_path, status_path, log_path)):
        raise FileExistsError('A build label must never reuse existing process/status/log files: ' + label)
    BASE.mkdir(parents=True, exist_ok=True)
    started = now()
    begin = time.monotonic()
    metadata = {'label': label, 'prepared_utc': started, 'command': argv, 'cwd': str(cwd),
        'environment_sha256': hashlib.sha256(json.dumps(sorted(environment.items()), ensure_ascii=False).encode()).hexdigest(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'created_suspended': False, 'assigned_to_private_job': False, 'resumed': False,
        'job_policy': 'JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; job handle is not inherited',
        'resource_policy': {'seconds': seconds, 'max_tree_working_set_GiB': max_tree_gib,
                            'min_system_available_GiB': min_available_gib, 'sampling_seconds': .1},
        'observed_processes': [], 'unobserved_exited_before_open': 0}
    # Exclusive reservation prevents a concurrent invocation from reusing this label.
    write_json(process_path, metadata, new=True)
    api = psapi = None
    job = None
    process = PROCESS_INFORMATION()
    handles = {}
    reason = failure = None
    peak = 0
    minimum_available = None
    samples = 0
    final_active = None
    job_termination_requested = False
    terminated_code = None
    cleanup_errors = []
    actual_root_exit = None
    log = stdin = None
    try:
        api, psapi = windows_api()
        available = float(psutil.virtual_memory().available / GIB)
        minimum_available = available
        if available < min_available_gib:
            reason = 'system_available_memory_below_minimum_before_launch'
        else:
            job = checked(api.CreateJobObjectW(None, None), 'CreateJobObjectW')
            limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            checked(api.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)), 'SetInformationJobObject kill-on-close')
            import msvcrt
            log = log_path.open('xb', buffering=0)
            stdin = open(os.devnull, 'rb')
            output_handle, input_handle = msvcrt.get_osfhandle(log.fileno()), msvcrt.get_osfhandle(stdin.fileno())
            os.set_handle_inheritable(output_handle, True)
            os.set_handle_inheritable(input_handle, True)
            startup = STARTUPINFOW()
            startup.cb = ctypes.sizeof(startup)
            startup.dwFlags = 0x00000100 | 0x00000001  # USESTDHANDLES | USESHOWWINDOW
            startup.wShowWindow = 0  # hidden
            startup.hStdInput, startup.hStdOutput, startup.hStdError = input_handle, output_handle, output_handle
            env_block = ctypes.create_unicode_buffer('\0'.join(k + '=' + v for k, v in sorted(environment.items(), key=lambda kv: kv[0].upper())) + '\0\0')
            command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
            try:
                checked(api.CreateProcessW(argv[0], command_line, None, None, True,
                    CREATE_SUSPENDED | CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
                    ctypes.cast(env_block, ctypes.c_void_p), str(cwd), ctypes.byref(startup), ctypes.byref(process)), 'CreateProcessW suspended')
            finally:
                os.set_handle_inheritable(output_handle, False)
                os.set_handle_inheritable(input_handle, False)
            metadata['created_suspended'] = True
            root = creation_identity(api, process.hProcess, process.dwProcessId)
            root.update(role='root', first_observed_utc=now(), sampled_peak_working_set_bytes=0, exit_code=None)
            handles[int(process.dwProcessId)] = (process.hProcess, root)
            metadata['root_identity'] = dict(root)
            write_json(process_path, metadata)
            # The process cannot execute user code or create children before assignment.
            assign_process(api, job, process.hProcess)
            metadata['assigned_to_private_job'] = True
            resumed = api.ResumeThread(process.hThread)
            if resumed == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error(), 'ResumeThread')
            metadata['resumed'] = True
            metadata['resumed_utc'] = now()
            write_json(process_path, metadata)
            api.CloseHandle(process.hThread)
            process.hThread = None
            while True:
                pids = job_pids(api, job)
                total = 0
                for pid in pids:
                    if pid not in handles:
                        # A job PID query establishes ownership. All subsequent reads use
                        # a retained process handle, so PID reuse cannot redirect sampling.
                        handle = api.OpenProcess(0x00100000 | 0x00001000 | 0x00000010, False, pid)
                        if not handle:
                            error = ctypes.get_last_error()
                            if error in (87, 1168):  # process exited before it could be opened
                                metadata['unobserved_exited_before_open'] += 1
                                continue
                            raise ctypes.WinError(error, 'OpenProcess owned job child')
                        belongs = wintypes.BOOL()
                        try:
                            checked(api.IsProcessInJob(handle, job, ctypes.byref(belongs)), 'IsProcessInJob owned child')
                            if not belongs.value:
                                # The queried PID may have exited and been reused before
                                # OpenProcess; never sample an unrelated replacement.
                                api.CloseHandle(handle)
                                metadata['unobserved_exited_before_open'] += 1
                                continue
                        except BaseException:
                            api.CloseHandle(handle)
                            raise
                        try:
                            identity = creation_identity(api, handle, pid)
                        except BaseException:
                            api.CloseHandle(handle)
                            raise
                        identity.update(role='descendant', first_observed_utc=now(), sampled_peak_working_set_bytes=0, exit_code=None)
                        handles[pid] = (handle, identity)
                    handle, identity = handles[pid]
                    if exited(api, handle):
                        continue
                    counters = PROCESS_MEMORY_COUNTERS()
                    counters.cb = ctypes.sizeof(counters)
                    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), ctypes.sizeof(counters)):
                        if exited(api, handle):
                            continue
                        raise ctypes.WinError(ctypes.get_last_error(), 'GetProcessMemoryInfo owned process')
                    total += int(counters.WorkingSetSize)
                    identity['sampled_peak_working_set_bytes'] = max(identity['sampled_peak_working_set_bytes'], int(counters.WorkingSetSize))
                peak = max(peak, total)
                available = float(psutil.virtual_memory().available / GIB)
                minimum_available = min(minimum_available, available)
                samples += 1
                reason = resource_stop_reason(time.monotonic() - begin, total / GIB, available, seconds, max_tree_gib, min_available_gib)
                if reason:
                    break
                if exited(api, process.hProcess):
                    actual_root_exit = exit_code(api, process.hProcess)
                    remaining = [pid for pid in job_pids(api, job) if pid != int(process.dwProcessId)]
                    if remaining:
                        reason = 'root_exited_with_live_job_children'
                    elif actual_root_exit != 0:
                        reason = 'build_root_nonzero_exit'
                    break
                time.sleep(.1)
    except BaseException as error:
        failure = {'type': type(error).__name__, 'message': str(error), 'recorded_utc': now()}
        if not metadata['assigned_to_private_job'] and metadata['created_suspended']:
            reason = 'job_assignment_or_suspended_setup_failed'
        elif not metadata['resumed']:
            reason = 'build_not_started_setup_failed'
        else:
            reason = 'process_monitor_or_runner_failed'
    finally:
        if api is not None:
            if process.hProcess and not metadata['assigned_to_private_job']:
                # This is only our still-suspended process, never an arbitrary PID.
                if not exited(api, process.hProcess):
                    if not api.TerminateProcess(process.hProcess, 125):
                        cleanup_errors.append('TerminateProcess suspended root: ' + str(ctypes.get_last_error()))
            if job is not None:
                try:
                    active = job_pids(api, job)
                    if active:
                        terminated_code = 124 if reason == 'time_budget_exceeded' else 137 if reason in ('process_tree_working_set_exceeded', 'system_available_memory_below_minimum') else 125
                        job_termination_requested = True
                        if not api.TerminateJobObject(job, terminated_code):
                            cleanup_errors.append('TerminateJobObject: ' + str(ctypes.get_last_error()))
                    cleanup_begin = time.monotonic()
                    while job_pids(api, job) and time.monotonic() - cleanup_begin < 5:
                        time.sleep(.025)
                    final_active = job_pids(api, job)
                    if final_active:
                        cleanup_errors.append('Job still had active processes before final kill-on-close')
                except BaseException as error:
                    cleanup_errors.append('Job cleanup query: ' + str(error))
                # Final kernel-enforced cleanup, including any late child creation.
                api.CloseHandle(job)
                job = None
            if process.hProcess:
                api.WaitForSingleObject(process.hProcess, 5000)
                try:
                    actual_root_exit = exit_code(api, process.hProcess)
                except BaseException as error:
                    cleanup_errors.append('Root exit code: ' + str(error))
            # A job can report zero active members before every process object
            # becomes signalled. Confirm exit on each retained identity handle,
            # with one shared cleanup deadline (not five seconds per child).
            identity_deadline = time.monotonic() + 5
            for pid, (handle, identity) in handles.items():
                try:
                    wait_ms = max(0, int((identity_deadline - time.monotonic()) * 1000))
                    api.WaitForSingleObject(handle, wait_ms)
                    identity['exit_code'] = exit_code(api, handle)
                    identity['confirmed_exited'] = exited(api, handle)
                except BaseException as error:
                    identity['exit_observation_error'] = str(error)
                    identity['confirmed_exited'] = False
                api.CloseHandle(handle)
            if process.hProcess and int(process.dwProcessId) not in handles:
                api.CloseHandle(process.hProcess)
            if process.hThread:
                api.CloseHandle(process.hThread)
        if stdin is not None:
            stdin.close()
        if log is not None:
            log.close()
    metadata['observed_processes'] = [identity for handle, identity in handles.values()]
    metadata['finished_utc'] = now()
    write_json(process_path, metadata)
    confirmed = all(identity.get('confirmed_exited', False) for handle, identity in handles.values())
    clean = confirmed and not cleanup_errors and (final_active == [] or not metadata['assigned_to_private_job'])
    status = {'label': label, 'prepared_utc': started, 'ended_utc': now(), 'command': argv, 'cwd': str(cwd),
        'build_started': metadata['resumed'], 'assigned_to_private_job': metadata['assigned_to_private_job'],
        'exit_code': actual_root_exit, 'stop_reason': reason, 'runner_error': failure,
        'seconds': time.monotonic() - begin, 'budget_s': seconds,
        'peak_process_tree_working_set_GiB': peak / GIB, 'minimum_system_available_GiB': minimum_available,
        'sample_count': samples, 'sampling_seconds': .1, 'observed_process_count': len(handles),
        'job_termination_requested': job_termination_requested, 'requested_termination_exit_code': terminated_code,
        'job_active_pids_before_final_close': final_active, 'all_observed_processes_confirmed_exited': confirmed,
        'cleanup_confirmed': clean, 'cleanup_errors': cleanup_errors,
        'succeeded': bool(metadata['resumed'] and actual_root_exit == 0 and reason is None and failure is None and clean),
        'working_set_policy': 'Sum of current working sets of all job-member processes sampled every0.1s; shared pages may count in multiple processes; transient peaks between samples are not guaranteed observed.',
        'physical_qualification_passed': False}
    write_json(status_path, status, new=True)
    return status


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 3 or argv[1] != '--':
        raise SystemExit('Usage: python build_runner.py LABEL -- COMMAND ARGS')
    plan = json.loads((BASE / 'setup_plan.json').read_text(encoding='utf-8-sig'))
    limits = plan['build_resources']
    result = run_build(argv[2:], Path.cwd(), argv[0], limits['seconds_each_build_budget'],
        dict(os.environ), max_tree_gib=limits['process_tree_working_set_sum_GiB_max'],
        min_available_gib=limits['system_free_GiB_min'])
    print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    return 0 if result['succeeded'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
