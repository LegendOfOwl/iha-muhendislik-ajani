"""Fixed, offline, fresh-directory SU2 8.5.0 build controls.

inspect/plan never compile. build creates one isolated source copy, runs the
upstream offline preconfigure, configures Meson, verifies its effective options,
then asks Ninja for the single introspected SU2_CFD executable target. No fetch,
installation, release replacement, solver run, or engineering acceptance occurs.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import difflib
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import stat
import sys
import tarfile
import time
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
PIN = '12eb826f049ef7f67df974dfcb44cf36ee07c0f8'
EIGEN = 'd71c30c47858effcbd39967097a2d99ee48db464'
MEL = '46205ab019e5224559091375a6d71aabae6bc5b9'
CAP_FILE = 'Common/include/geometry/CGeometry.hpp'
OPTIONS = {'cpu-arch': 'haswell', 'with-omp': True, 'with-mpi': 'disabled',
           'custom-mpi': False, 'enable-normal': True, 'extra-deps': '',
           'buildtype': 'release', 'b_ndebug': 'true', 'c_std': 'c99',
           'cpp_std': 'c++17', 'warning_level': '0', 'wrap_mode': 'nodownload',
           'cpp_args': ['-I../source/SU2_CFD/src/interfaces']}
OPTIONS.update({key: False for key in (
    'enable-tecio', 'enable-cgns', 'enable-autodiff', 'enable-directdiff',
    'enable-pywrapper', 'enable-mkl', 'enable-openblas', 'enable-cuda',
    'enable-pastix', 'enable-tests', 'enable-mixedprec', 'enable-mpp',
    'install-mpp', 'enable-coolprop', 'enable-mlpcpp', 'enable-gprof',
    'enable-librom', 'tracy_enable')})
NO_DOWNLOAD = ['--no-' + x for x in
               ('codi', 'medi', 'opdi', 'mpp', 'coolprop', 'mel', 'fado', 'mlpcpp', 'eigen')]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def inside(path, parent):
    """Resolve containment and reject symlinks/junctions, including ancestors."""
    path, parent = Path(path).absolute(), Path(parent).resolve()
    require(path.resolve().is_relative_to(parent) and path.resolve() != parent,
            'Path escapes intended parent or equals it: ' + str(path))
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            attr = item.lstat()
            require(not stat.S_ISLNK(attr.st_mode) and
                    not (getattr(attr, 'st_file_attributes', 0) & 0x400),
                    'Reparse point/symlink forbidden: ' + str(item))
        if item == parent:
            break
    return path.resolve()


def tree_files(folder, ignore=()):
    folder = Path(folder).resolve()
    require(folder.is_dir(), 'Missing source directory: ' + str(folder))
    result, folded = {}, set()
    for current, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            item = inside(Path(current) / name, folder)
            rel = item.relative_to(folder).as_posix()
            require(rel.casefold() not in folded, 'Case-colliding source path')
            folded.add(rel.casefold())
            if name in files and rel not in ignore:
                require(item.is_file(), 'Non-regular source file')
                result[rel] = {'sha256': sha(item), 'bytes': item.stat().st_size}
    return dict(sorted(result.items()))


def fingerprint(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def archive_files(archive):
    """Hash every archive file without extracting; reject aliases and unsafe types."""
    result, roots, seen, expanded = {}, set(), set(), 0
    def member(name, size, stream, regular=True, directory=False):
        nonlocal expanded
        p = PurePosixPath(name)
        require(not p.is_absolute() and p.as_posix() == name.rstrip('/') and '\\' not in name and
                all(x not in ('.', '..', '') and ':' not in x for x in p.parts),
                'Unsafe archive member')
        require(p.parts and p.parts[0].casefold() not in ('con', 'nul'), 'Unsafe archive root')
        roots.add(p.parts[0])
        require(name.rstrip('/').casefold() not in seen, 'Duplicate/case-colliding archive member')
        seen.add(name.rstrip('/').casefold())
        require(regular or directory, 'Archive link/special member forbidden')
        if directory:
            return
        require(len(p.parts) > 1, 'File at archive root without containing directory')
        expanded += size
        require(expanded <= 700 * 1024**2, 'Expanded archive cap exceeded')
        h, actual = hashlib.sha256(), 0
        while block := stream.read(1024 * 1024):
            actual += len(block)
            require(actual <= size, 'Archive member length overflow')
            h.update(block)
        require(actual == size, 'Archive member truncated')
        result[PurePosixPath(*p.parts[1:]).as_posix()] = {'sha256': h.hexdigest(), 'bytes': actual}
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            for m in z.infolist():
                mode = (m.external_attr >> 16) & 0o170000
                require(mode not in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO),
                        'Unsafe ZIP member type')
                if m.is_dir():
                    member(m.filename, 0, None, directory=True)
                else:
                    with z.open(m) as stream:
                        member(m.filename, m.file_size, stream)
    else:
        with tarfile.open(archive, 'r:gz') as t:
            for m in t:
                if m.isdir():
                    member(m.name, 0, None, directory=True)
                else:
                    require(m.isfile(), 'TAR links/special members forbidden')
                    with t.extractfile(m) as stream:
                        member(m.name, m.size, stream)
    require(len(roots) == 1 and result, 'Archive needs one nonempty containing directory')
    return dict(sorted(result.items()))


def allowed_urls(kind, pin):
    if kind == 'eigen':
        return {f'https://gitlab.com/libeigen/eigen/-/archive/{pin}/eigen-{pin}.{ext}'
                for ext in ('zip', 'tar.gz')}
    repo = 'su2code/SU2' if kind == 'source' else 'pcarruscag/MEL'
    return {f'https://codeload.github.com/{repo}/{fmt}/{pin}' for fmt in ('zip', 'tar.gz')} | {
        f'https://github.com/{repo}/archive/{pin}.{ext}' for ext in ('zip', 'tar.gz')} | {
        f'https://api.github.com/repos/{repo}/zipball/{pin}',
        f'https://api.github.com/repos/{repo}/tarball/{pin}'}


def verify_extracted(root, folder, kind, pin):
    home = root / 'tools/su2-build/v8.5.0'
    folder = inside(folder, home)
    origin = read(folder / 'archive_origin.json')
    require(origin.get('commit', pin) == pin and origin.get('url') in allowed_urls(kind, pin),
            'Missing fixed official commit provenance: ' + kind)
    require(origin.get('destination') and (root / origin['destination']).resolve() == folder,
            'Archive destination mismatch')
    archive = inside(root / origin['path'], home)
    require(archive.is_file() and archive.stat().st_size <= 250 * 1024**2,
            'Missing/oversize retained archive')
    require(archive.stat().st_size == origin['bytes'] and sha(archive) == origin['sha256'],
            'Retained archive bytes/SHA mismatch')
    expected = archive_files(archive)
    actual = tree_files(folder, ignore=('archive_origin.json',))
    require(actual == expected, 'Extracted tree differs from retained pinned archive: ' + kind)
    return {'origin': origin, 'origin_sha256': sha(folder / 'archive_origin.json'),
            'files': actual, 'tree_sha256': fingerprint(actual)}


def patch_cap(original):
    declaration = rb'(enum\s*:\s*unsigned\s+long\s*\{\s*MAX_LINELET_POINTS\s*=\s*)(\d+)(\s*\}\s*;)'
    matches = list(re.finditer(declaration, original))
    require(len(matches) == 1 and len(re.findall(rb'\bMAX_LINELET_POINTS\s*=', original)) == 1,
            'Expected exactly one cap declaration')
    match = matches[0]
    require(match.group(2) == b'32', 'Pristine cap must be exactly 32')
    return original[:match.start(2)] + b'256' + original[match.end(2):]


def verify_copy(expected, actual):
    require(expected == actual, 'Unintended source change, missing file, or added file')


def option_value(value):
    return str(value).lower() if isinstance(value, bool) else str(value)


def verify_options(rows):
    actual = {row['name']: row['value'] for row in rows}
    require(len(actual) == len(rows), 'Duplicate Meson option name')
    for key, expected in OPTIONS.items():
        require(key in actual and option_value(actual[key]) == option_value(expected),
                'Effective Meson option mismatch: ' + key)
    require(actual.get('backend') == 'ninja', 'Ninja backend required')


def target_from_intro(rows, build):
    targets = [r for r in rows if r.get('name') == 'SU2_CFD' and r.get('type') == 'executable']
    require(len(targets) == 1 and len(targets[0].get('filename', [])) == 1,
            'Exactly one native SU2_CFD executable target required')
    output = inside(Path(targets[0]['filename'][0]), build)
    require(output.name == 'SU2_CFD.exe', 'Unexpected executable output')
    return output.relative_to(Path(build).resolve()).as_posix()


def commands(root, source, build, target='SU2_CFD/src/SU2_CFD.exe'):
    python, ninja = root / '.venv/Scripts/python.exe', root / '.venv/Scripts/ninja.exe'
    options = ['-D' + key + '=' + option_value(value) for key, value in OPTIONS.items()]
    return {'preconfigure': [str(python), '-B', str(source / 'preconfigure.py'), *NO_DOWNLOAD],
            'configure': [str(python), '-I', '-m', 'mesonbuild.mesonmain', 'setup',
                          str(build), str(source), '--backend=ninja', *options],
            'compile': [str(ninja), '-C', str(build), '-j', '1', target]}


def prepared_identity(root, plan, inputs, preflight, variant):
    """Identity before compilation, independently reproducible from pinned inputs."""
    require(variant in ('pristine32', 'cap256'), 'Unknown variant')
    files = dict(inputs['source']['files'])
    for dependency in ('eigen', 'mel'):
        files.update({'externals/' + dependency + '/' + rel: value
                      for rel, value in inputs[dependency]['files'].items()})
    original = (root / 'tools/su2-build/v8.5.0/source' / CAP_FILE).read_bytes()
    changed = patch_cap(original)
    data = changed if variant == 'cap256' else original
    files[CAP_FILE] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    compiler = Path(plan['compiler'])
    paths = [compiler, compiler.parent / 'gcc.exe', compiler.parent / 'ar.exe',
             compiler.parent / 'as.exe', compiler.parent / 'ld.exe',
             root / preflight['compiler']['cc1plus_path'],
             root / '.venv/Scripts/python.exe', root / '.venv/Scripts/ninja.exe']
    compiler_manifest = {'binaries': {str(inside(p, root).relative_to(root)): sha(p) for p in paths},
                         'preflight_compiler': preflight['compiler'],
                         'packages': preflight['installed_packages'], 'meson_options': OPTIONS,
                         'coverage_note': 'Compiler/linker/tool binaries and declared options; not a full OS/SDK image'}
    runtime_manifest = dict(preflight['runtime_DLL_sha256'])
    identity = {'source_commit': PIN, 'cap': 256 if variant == 'cap256' else 32,
                'source_tree_sha256': fingerprint(files),
                'pristine_archive_tree_sha256': inputs['source']['tree_sha256'],
                'dependency_tree_sha256': {k: inputs[k]['tree_sha256'] for k in ('eigen', 'mel')},
                'compiler_manifest_sha256': fingerprint(compiler_manifest),
                'runtime_manifest_sha256': fingerprint(runtime_manifest),
                'source_hash_definition': 'All copied upstream files plus exact Eigen/MEL files, byte hashes and sizes; '
                                          'archive_origin.json and generated su2preconfig.timestamp excluded',
                'physical_qualification_passed': False}
    return files, identity, compiler_manifest, runtime_manifest


def verify_reference(root, home, label, identity):
    from build_runner import validated_label
    require(label is not None, 'cap256 requires --reference-control with a completed pristine32 build')
    validated_label(label)
    control = inside(home / 'controls' / label, home)
    contract, status = read(control / 'contract.json'), read(control / 'status.json')
    require(contract['variant'] == 'pristine32' and status['succeeded'] is True and status['cap'] == 32,
            'Reference must be a successful pristine32 build')
    for key in ('source_commit', 'pristine_archive_tree_sha256', 'dependency_tree_sha256',
                'compiler_manifest_sha256', 'runtime_manifest_sha256'):
        require(contract[key] == identity[key] == status[key], 'Reference build identity mismatch: ' + key)
    verify_copy(contract['prepared_files'], tree_files(control / 'source', ignore=('su2preconfig.timestamp',)))
    require(sha(inside(Path(status['exe']), control / 'build')) == status['exe_sha256'],
            'Reference executable changed')
    return {'label': label, 'contract_sha256': sha(control / 'contract.json'),
            'status_sha256': sha(control / 'status.json'), 'exe_sha256': status['exe_sha256']}


def inspect_inputs(root=ROOT):
    root = Path(root).resolve()
    home, base = root / 'tools/su2-build/v8.5.0', root / 'work/su2_build_20261027'
    plan = read(base / 'setup_plan.json')
    require(plan['source_commit'] == PIN, 'Wrong source pin')
    require(plan['build_resources'] == {'parallel_jobs': 1, 'seconds_each_build_budget': 1800,
            'process_tree_working_set_sum_GiB_max': 3., 'system_free_GiB_min': 1.},
            'Build resource contract changed')
    inputs = {kind: verify_extracted(root, home / folder, kind, pin) for kind, folder, pin in (
        ('source', 'source', PIN), ('eigen', 'eigen-pinned', EIGEN), ('mel', 'mel-pinned', MEL))}
    patch_cap((home / 'source' / CAP_FILE).read_bytes())
    for dependency in ('eigen', 'mel'):
        require(not any(k.startswith('externals/' + dependency + '/') for k in inputs['source']['files']),
                'Pristine upstream tree unexpectedly contains populated dependency')
    preflight = read(root / 'outputs/reports/su2_build_preflight_20261027.json')
    require(preflight['passed'] is True and preflight['OpenMP_probe']['threads'] == 4 and
            preflight['OpenMP_probe']['double_bytes'] == 8, 'Missing successful compiler/OpenMP preflight')
    for name, version in {'meson': '1.8.2', 'ninja': '1.13.0', 'psutil': '7.1.0'}.items():
        require(importlib.metadata.version(name) == version, 'Wrong installed package version: ' + name)
    require(Path(sys.executable).resolve() == (root / '.venv/Scripts/python.exe').resolve(),
            'Run driver with project .venv Python')
    compiler = inside(Path(plan['compiler']), root / 'tools')
    require(sha(compiler) == plan['compiler_sha256'] == preflight['compiler']['sha256'], 'Compiler changed')
    for rel, expected in preflight['runtime_DLL_sha256'].items():
        require(sha(inside(root / rel, root / 'tools')) == expected, 'Runtime DLL changed')
    require(sha(root / preflight['compiler']['cc1plus_path']) == preflight['compiler']['cc1plus_sha256'],
            'cc1plus changed')
    for executable in (compiler.parent / 'gcc.exe', root / '.venv/Scripts/ninja.exe'):
        require(executable.is_file(), 'Missing build executable: ' + str(executable))
    return plan, inputs, preflight


def run_fixed_build(label, variant, root=ROOT, reference_control=None):
    from build_runner import run_build, validated_label
    require(variant in ('pristine32', 'cap256'), 'Unknown variant')
    validated_label(label)
    require(len(label) <= 55, 'Label too long for phase suffixes')
    root = Path(root).resolve()
    plan, inputs, preflight = inspect_inputs(root)
    home, base = root / 'tools/su2-build/v8.5.0', root / 'work/su2_build_20261027'
    expected, identity, compiler_manifest, runtime_manifest = prepared_identity(root, plan, inputs, preflight, variant)
    reference = verify_reference(root, home, reference_control, identity) if variant == 'cap256' else None
    control = inside(home / 'controls' / label, home)
    require(not control.exists(), 'Fresh label/directory required; no stale build reuse')
    for phase in ('preconfigure', 'configure', 'compile'):
        require(not any((base / (label + '-' + phase + suffix)).exists()
                        for suffix in ('.log', '.process.json', '.status.json')), 'Existing runner phase evidence')
    control.mkdir(parents=True)
    source, build = control / 'source', control / 'build'
    original = (home / 'source' / CAP_FILE).read_bytes()
    # Copy only verified files; archive metadata is kept in the receipt, not source.
    for kind, prefix in (('source', ''), ('eigen', 'externals/eigen/'), ('mel', 'externals/mel/')):
        folder = home / {'source': 'source', 'eigen': 'eigen-pinned', 'mel': 'mel-pinned'}[kind]
        for rel, values in inputs[kind]['files'].items():
            dest = inside(source / (prefix + rel), control)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(folder / rel, dest)
    patched = patch_cap(original) if variant == 'cap256' else original
    (source / CAP_FILE).write_bytes(patched)
    verify_copy(expected, tree_files(source))
    patch = ''.join(difflib.unified_diff(original.decode().splitlines(True), patched.decode().splitlines(True),
                                       fromfile='a/' + CAP_FILE, tofile='b/' + CAP_FILE))
    (control / 'source.patch').write_text(patch, encoding='utf-8', newline='')
    env = dict(os.environ)
    # Explicit child-only toolchain; ignore inherited compilation injection knobs.
    for key in ('CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'CPATH', 'C_INCLUDE_PATH',
                'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH', 'COMPILER_PATH', 'GCC_EXEC_PREFIX',
                'CL', '_CL_', 'LINK', 'PYTHONPATH', 'PYTHONHOME', 'CCACHE_PREFIX'):
        env.pop(key, None)
    compiler = Path(plan['compiler'])
    env.update(CC=str(compiler.parent / 'gcc.exe'), CXX=str(compiler),
               PATH=str(compiler.parent) + os.pathsep + str(root / '.venv/Scripts') + os.pathsep + env.get('PATH', ''),
               NINJA=str(root / '.venv/Scripts/ninja.exe'), OMP_NUM_THREADS='4', OMP_WAIT_POLICY='PASSIVE',
               PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    cmds = commands(root, source, build)
    receipt = {'label': label, 'variant': variant, **identity, 'created_utc': datetime.now(timezone.utc).isoformat(),
               'inputs': inputs, 'prepared_files': expected, 'prepared_tree_sha256': fingerprint(expected),
               'source_patch_sha256': sha(control / 'source.patch'), 'patch_changed_files': [CAP_FILE] if patch else [],
               'options': OPTIONS, 'commands': cmds, 'build_resources': plan['build_resources'],
               'preflight_sha256': sha(root / 'outputs/reports/su2_build_preflight_20261027.json'),
               'driver_sha256': sha(Path(__file__)), 'runner_sha256': sha(BASE / 'build_runner.py'),
               'compiler': preflight['compiler'], 'runtime_DLL_sha256': preflight['runtime_DLL_sha256'],
               'compiler_manifest': compiler_manifest, 'runtime_manifest': runtime_manifest,
               'reference_control': reference,
               'auto_download': False, 'scope': 'Local build control; release equivalence and physical qualification not established',
               'physical_qualification_passed': False}
    save_new(control / 'contract.json', receipt)
    status = {'label': label, 'variant': variant, **identity, 'succeeded': False, 'phases': [],
              'source_patch_sha256': receipt['source_patch_sha256'],
              'contract_sha256': sha(control / 'contract.json')}
    started = time.monotonic()
    try:
        for phase in ('preconfigure', 'configure', 'compile'):
            if phase != 'preconfigure':
                verify_copy(expected, tree_files(source, ignore=('su2preconfig.timestamp',)))
                require((source / 'su2preconfig.timestamp').is_file(), 'Missing native preconfigure marker')
            if phase == 'compile':
                verify_options(read(build / 'meson-info/intro-buildoptions.json'))
                target = target_from_intro(read(build / 'meson-info/intro-targets.json'), build)
                cmds['compile'] = commands(root, source, build, target)['compile']
                save_new(control / 'effective_build.json', {'target': target, 'command': cmds['compile'],
                         'options_sha256': sha(build / 'meson-info/intro-buildoptions.json'),
                         'targets_sha256': sha(build / 'meson-info/intro-targets.json'),
                         'compile_commands_sha256': sha(build / 'compile_commands.json')})
            remaining = 1800 - (time.monotonic() - started)
            require(remaining > 0, 'Total 1800 second build budget exhausted')
            result = run_build(cmds[phase], source, label + '-' + phase, remaining, env,
                               max_tree_gib=3, min_available_gib=1)
            status['phases'].append(result)
            require(result['succeeded'], 'Native phase failed: ' + phase)
        verify_copy(expected, tree_files(source, ignore=('su2preconfig.timestamp',)))
        executable = inside(build / target, build)
        require(executable.is_file(), 'Compiled executable absent')
        status.update(succeeded=True, executable=str(executable.relative_to(root)),
                      executable_sha256=sha(executable), exe=str(executable),
                      exe_sha256=sha(executable), bytes=executable.stat().st_size)
    except Exception as error:
        status['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        status['seconds'] = time.monotonic() - started
        save_new(control / 'status.json', status)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'plan', 'build'))
    parser.add_argument('label', nargs='?')
    parser.add_argument('--variant', choices=('pristine32', 'cap256'), default='pristine32')
    parser.add_argument('--reference-control', help='Completed pristine32 build label, mandatory for cap256')
    args = parser.parse_args()
    if args.action == 'inspect':
        plan, inputs, preflight = inspect_inputs()
        _, identity, _, _ = prepared_identity(ROOT, plan, inputs, preflight, args.variant)
        print(json.dumps({'ready': True, **identity, 'tree_sha256': {k: v['tree_sha256'] for k, v in inputs.items()},
                          'compiled': False, 'physical_qualification_passed': False}))
        return 0
    require(args.label is not None, 'label is required')
    if args.action == 'plan':
        from build_runner import validated_label
        validated_label(args.label)
        control = inside(ROOT / 'tools/su2-build/v8.5.0/controls' / args.label,
                         ROOT / 'tools/su2-build/v8.5.0')
        print(json.dumps({'commands': commands(ROOT, control / 'source', control / 'build'),
                          'variant': args.variant, 'inputs_checked': False, 'compiled': False}, indent=2))
        return 0
    result = run_fixed_build(args.label, args.variant, reference_control=args.reference_control)
    print(json.dumps({'succeeded': result['succeeded'], 'error': result.get('error'),
                      'executable': result.get('executable'), 'physical_qualification_passed': False}))
    return 0 if result['succeeded'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, KeyError) as error:
        print(json.dumps({'ready': False, 'error': str(error), 'compiled': False}), file=sys.stderr)
        raise SystemExit(2)
