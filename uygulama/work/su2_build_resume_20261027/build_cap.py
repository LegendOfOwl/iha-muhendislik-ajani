"""Gated, fresh, offline cap-256 build using the recovered pristine recipe.

Importing this module has no filesystem mutations or native execution. ``check``
is read-only. ``build`` requires the real registered pristine reproduction to
pass, recomputes that decision, then changes only the cap in a fresh source copy.
It neither runs CFD nor changes the installed release or existing build controls.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import difflib
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OLD_BASE = ROOT / 'work/su2_build_20261027'
sys.path.insert(0, str(OLD_BASE))
from build_su2 import (PIN, CAP_FILE, NO_DOWNLOAD, inside, tree_files, verify_copy,
                       fingerprint, patch_cap, target_from_intro, sha)
from decisions import reproducibility_gate
from build_runner import run_build
from ninja_recipe import (EXTRA_ARG, FINAL_TARGET, derive_manifest, command_map,
                          verify_command_delta, digest)

REFERENCE_LABEL = 'p32r'
LABEL = 'p256r'
TOTAL_BUDGET_SECONDS = 1800.0
EXPECTED_RESOURCES = {'parallel_jobs': 1, 'seconds_each_build_budget': 1800,
                     'process_tree_working_set_sum_GiB_max': 3., 'system_free_GiB_min': 1.}
PER_TU = {'SU2_CFD/src/interfaces/fsi/CFlowTractionInterface.cpp': [EXTRA_ARG]}
NO_FETCH = ['--no-' + item for item in ('codi', 'medi', 'opdi', 'mpp', 'coolprop',
                                        'mel', 'fado', 'mlpcpp', 'eigen')]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


def option_value(value):
    return str(value).lower() if isinstance(value, bool) else str(value)


def verify_options(rows, expected):
    """Compare effective values to the historical reference, never global OPTIONS."""
    require(isinstance(expected, dict) and expected and 'cpp_args' not in expected,
            'Original reference options without global cpp_args required')
    actual = {row['name']: row['value'] for row in rows}
    require(len(actual) == len(rows), 'Duplicate effective Meson option')
    for key, value in expected.items():
        require(key in actual and type(actual[key]) is type(value) and actual[key] == value,
                'Effective reference option mismatch: ' + key)
    for key in ('cpp_args', 'cpp_link_args', 'c_args', 'c_link_args'):
        require(actual.get(key) == [], 'Unexpected global compilation/link injection: ' + key)
    require(actual.get('backend') == 'ninja', 'Ninja backend required')
    return {key: actual[key] for key in expected}


def verify_common_recipe(reference_text, candidate_text):
    """All effective compile/archive/link commands must match, independent of order."""
    reference, candidate = command_map(reference_text), command_map(candidate_text)
    require(set(reference) == set(candidate), 'Common recipe output set differs')
    for output in reference:
        require(reference[output]['command'] == candidate[output]['command'],
                'Common effective command differs: ' + output)
    require(len(reference) == 290, 'Unexpected registered SU2_CFD command count')
    return {'passed': True, 'matched_commands': len(reference),
            'recipe_includes_per_TU_override': True,
            'source_bytes_are_checked_separately': True}


def verify_reproduction_records(native_contract, release_record, pristine_record, saved_decision):
    """Recompute and bind the real decision; truthy or stale acceptance is rejected."""
    require(native_contract.get('pristine_build') == REFERENCE_LABEL,
            'Registered native control must use the recovered pristine build')
    require(release_record.get('accepted_for_decision') is True and
            pristine_record.get('accepted_for_decision') is True,
            'Both real native payloads must be accepted for the decision')
    contract = native_contract['decision_contract']
    decision = reproducibility_gate(release_record['payload'], pristine_record['payload'], contract)
    require(saved_decision.get('accepted') is True and decision.get('accepted') is True,
            'Pristine numerical reproduction has not passed')
    require(saved_decision == decision, 'Saved reproduction is stale or differs from recomputation')
    return decision


def modified_files(pristine_files, original_cap_bytes):
    """Calculate the sole allowed source-tree difference without writing source."""
    changed = patch_cap(original_cap_bytes)
    require(CAP_FILE in pristine_files and pristine_files[CAP_FILE] ==
            {'sha256': hashlib.sha256(original_cap_bytes).hexdigest(), 'bytes': len(original_cap_bytes)},
            'Cap bytes differ from the authenticated pristine source manifest')
    expected = copy.deepcopy(pristine_files)
    expected[CAP_FILE] = {'sha256': hashlib.sha256(changed).hexdigest(), 'bytes': len(changed)}
    require([key for key in expected if expected[key] != pristine_files[key]] == [CAP_FILE],
            'Only the registered cap file may differ')
    return changed, expected


def environment(reference):
    compiler = ROOT / reference['compiler']['path']
    env = dict(os.environ)
    for key in ('CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'CPATH', 'C_INCLUDE_PATH',
                'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH', 'COMPILER_PATH', 'GCC_EXEC_PREFIX',
                'CL', '_CL_', 'LINK', 'PYTHONPATH', 'PYTHONHOME', 'CCACHE_PREFIX'):
        env.pop(key, None)
    env.update(CC=str(compiler.parent / 'gcc.exe'), CXX=str(compiler),
               PATH=str(compiler.parent) + os.pathsep + str(ROOT / '.venv/Scripts') +
                    os.pathsep + env.get('PATH', ''),
               NINJA=str(ROOT / '.venv/Scripts/ninja.exe'), OMP_NUM_THREADS='4',
               OMP_WAIT_POLICY='PASSIVE', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    return env


def check_reference():
    """Authenticate the completed source snapshot, executable, tools and recipe."""
    folder = ROOT / 'tools/su2-build/v8.5.0/controls' / REFERENCE_LABEL
    contract, status = read(folder / 'contract.json'), read(folder / 'status.json')
    require(status.get('succeeded') is True and status['contract_sha256'] == sha(folder / 'contract.json'),
            'Completed authenticated pristine build is required')
    require(contract['variant'] == 'pristine32' and contract['cap'] == 32 and contract['source_commit'] == PIN,
            'Wrong pristine source identity')
    for key in ('cap', 'source_commit', 'source_tree_sha256', 'compiler_manifest_sha256',
                'runtime_manifest_sha256', 'source_patch_sha256', 'dependency_tree_sha256',
                'pristine_archive_tree_sha256'):
        require(status[key] == contract[key], 'Reference contract/status mismatch: ' + key)
    require(fingerprint(contract['prepared_files']) == contract['source_tree_sha256'],
            'Pristine prepared-file identity mismatch')
    verify_copy(contract['prepared_files'], tree_files(folder / 'source', ignore=('su2preconfig.timestamp',)))
    require(sha(folder / 'source.patch') == contract['source_patch_sha256'] and
            (folder / 'source.patch').read_bytes() == b'', 'Pristine source patch must be empty')
    require(sha(inside(Path(status['exe']), folder / 'build')) == status['exe_sha256'],
            'Pristine archived executable changed')
    cm = contract['compiler_manifest']
    require(fingerprint(cm) == contract['compiler_manifest_sha256'] and
            cm['meson_options'] == contract['options'] and 'cpp_args' not in contract['options'] and
            cm.get('per_translation_unit_extra_cpp_args') == PER_TU,
            'Wrong common reference compiler recipe')
    for name, version in cm['packages'].items():
        require(importlib.metadata.version(name) == version, 'Build package changed: ' + name)
    require(Path(sys.executable).resolve() == (ROOT / '.venv/Scripts/python.exe').resolve(),
            'Use the project .venv Python')
    for path, expected in cm['binaries'].items():
        require(sha(inside(ROOT / path, ROOT)) == expected, 'Compiler/archive/link tool changed: ' + path)
    for name in ('gcc-ar.exe', 'collect2.exe'):
        require(any(Path(path).name == name for path in cm['binaries']), 'Missing pinned binary: ' + name)
    require(contract['runtime_manifest'] == contract['runtime_DLL_sha256'] and
            fingerprint(contract['runtime_manifest']) == contract['runtime_manifest_sha256'],
            'Runtime manifest identity mismatch')
    for path, expected in contract['runtime_manifest'].items():
        require(sha(inside(ROOT / path, ROOT / 'tools')) == expected, 'Runtime DLL changed: ' + path)
    audit_folder = BASE / 'recipe_audit_v1'
    audit = read(audit_folder / 'audit.json')
    require(sha(audit_folder / 'audit.json') == contract['recipe_audit_sha256'],
            'Reference per-TU recipe audit changed')
    recipe_text = (audit_folder / 'after.stdout.txt').read_text(encoding='utf-8')
    require(digest(recipe_text.encode()) == audit['command_delta']['after_commands_sha256'],
            'Reference effective commands changed')
    require(contract['build_resources'] == EXPECTED_RESOURCES and NO_DOWNLOAD == NO_FETCH,
            'Build resources or offline dependency policy changed')
    proof = {'label': REFERENCE_LABEL, 'status_sha256': sha(folder / 'status.json'),
             'contract_sha256': sha(folder / 'contract.json'), 'exe_sha256': status['exe_sha256']}
    return folder, contract, status, proof, recipe_text


def prerequisites():
    reference = check_reference()
    # This authenticates the registered case, design and frozen/live reader code.
    from native_control import check_contract, CASE
    native_contract = check_contract()
    release, pristine, saved = [read(CASE / name) for name in
                               ('release32_payload.json', 'build32_payload.json', 'reproduction.json')]
    decision = verify_reproduction_records(native_contract, release, pristine, saved)
    _, contract, status, proof, _ = reference
    require(native_contract['pristine_build_status_sha256'] == proof['status_sha256'] and
            native_contract['decision_contract']['pristine_source_tree_sha256'] == contract['source_tree_sha256'] and
            pristine['payload']['identity']['source_tree_sha256'] == contract['source_tree_sha256'] and
            pristine['payload']['identity']['compiler_manifest_sha256'] == contract['compiler_manifest_sha256'] and
            pristine['payload']['identity']['runtime_manifest_sha256'] == contract['runtime_manifest_sha256'],
            'Reproduction is not bound to this exact reference build')
    sealed_paths = [CASE / name for name in ('contract.json', 'release32_payload.json',
                    'build32_payload.json', 'reproduction.json')]
    seal = {'paths_sha256': {str(path.relative_to(ROOT)): sha(path) for path in sealed_paths},
            'accepted': True, 'decision_recomputed': True,
            'build32_run_fingerprint': decision['build32_run_fingerprint'],
            'decision_contract_fingerprint': decision['contract_fingerprint']}
    return reference, seal


def commands(source, build, options, manifest):
    python, ninja = ROOT / '.venv/Scripts/python.exe', ROOT / '.venv/Scripts/ninja.exe'
    require('cpp_args' not in options, 'Global include fix is forbidden')
    configure_options = ['-D' + key + '=' + option_value(value) for key, value in options.items()]
    return {'preconfigure': [str(python), '-B', str(source / 'preconfigure.py'), *NO_FETCH],
            'configure': [str(python), '-I', '-m', 'mesonbuild.mesonmain', 'setup',
                          str(build), str(source), '--backend=ninja', *configure_options],
            'commands-before': [str(ninja), '-C', str(build), '-t', 'commands', FINAL_TARGET],
            'commands-after': [str(ninja), '-C', str(build), '-f', str(manifest),
                               '-t', 'commands', FINAL_TARGET],
            'compile': [str(ninja), '-C', str(build), '-f', str(manifest), '-j', '1', FINAL_TARGET]}


def build():
    reference, reproduction = prerequisites()  # MUST precede copying or patching any source.
    ref_folder, ref, ref_status, proof, reference_recipe = reference
    home = ROOT / 'tools/su2-build/v8.5.0/controls'
    control = inside(home / LABEL, home)
    require(not control.exists(), 'Fresh cap control required; no overwrite, resume or retry')
    phases = ('preconfigure', 'configure', 'commands-before', 'commands-after', 'compile')
    for phase in phases:
        require(not any((OLD_BASE / (LABEL + '-' + phase + suffix)).exists()
                        for suffix in ('.log', '.process.json', '.status.json')),
                'Existing runner evidence: ' + phase)
    original_cap = (ref_folder / 'source' / CAP_FILE).read_bytes()
    changed_cap, expected = modified_files(ref['prepared_files'], original_cap)
    source, build_dir = control / 'source', control / 'build'
    manifest = control / 'effective-recipe.ninja'
    cmds = commands(source, build_dir, ref['options'], manifest)
    started = time.monotonic()
    control.mkdir()
    for rel in ref['prepared_files']:
        target = inside(source / rel, control)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ref_folder / 'source' / rel, target)
    (source / CAP_FILE).write_bytes(changed_cap)
    verify_copy(expected, tree_files(source))
    patch = ''.join(difflib.unified_diff(original_cap.decode().splitlines(True),
                   changed_cap.decode().splitlines(True), fromfile='a/' + CAP_FILE, tofile='b/' + CAP_FILE))
    (control / 'source.patch').write_text(patch, encoding='utf-8', newline='')
    identity = {key: copy.deepcopy(ref[key]) for key in ('source_commit', 'pristine_archive_tree_sha256',
                'dependency_tree_sha256', 'compiler_manifest_sha256', 'runtime_manifest_sha256', 'source_hash_definition')}
    identity.update(source_tree_sha256=fingerprint(expected), cap=256)
    contract = {'label': LABEL, 'variant': 'cap256', **identity,
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'prepared_files': expected, 'prepared_tree_sha256': fingerprint(expected),
                'source_patch_sha256': sha(control / 'source.patch'), 'patch_changed_files': [CAP_FILE],
                'options': copy.deepcopy(ref['options']), 'commands': cmds,
                'build_resources': EXPECTED_RESOURCES,
                'compiler_manifest': copy.deepcopy(ref['compiler_manifest']),
                'runtime_manifest': copy.deepcopy(ref['runtime_manifest']),
                'runtime_DLL_sha256': copy.deepcopy(ref['runtime_DLL_sha256']),
                'compiler': copy.deepcopy(ref['compiler']), 'reference_control': proof,
                'reproduction_before_source_change': reproduction,
                'driver_sha256': sha(Path(__file__)), 'runner_sha256': sha(OLD_BASE / 'build_runner.py'),
                'code_sha256': {str(path.relative_to(ROOT)): sha(path) for path in
                               (Path(__file__), BASE / 'ninja_recipe.py', OLD_BASE / 'build_su2.py',
                                OLD_BASE / 'decisions.py', OLD_BASE / 'native_control.py')},
                'reference_effective_commands_sha256': digest(reference_recipe.encode()),
                'effective_recipe_path': str(manifest.relative_to(ROOT)),
                'auto_download': False, 'cached_objects_reused': 0,
                'physical_qualification_passed': False,
                'scope': 'Gated native source build only; neither a CFD run nor physical acceptance'}
    save_new(control / 'contract.json', contract)
    status = {'label': LABEL, 'variant': 'cap256', **identity, 'succeeded': False, 'phases': [],
              'source_patch_sha256': contract['source_patch_sha256'],
              'contract_sha256': sha(control / 'contract.json'), 'physical_qualification_passed': False}
    env = environment(ref)
    try:
        for phase in phases:
            # Also recheck the passed reproduction and reference identities between native phases.
            current_reference, current_reproduction = prerequisites()
            require(current_reference[3] == proof and current_reproduction == reproduction,
                    'Reference or reproduction changed during the build')
            for path, value in contract['code_sha256'].items():
                require(sha(ROOT / path) == value, 'Build helper code changed: ' + path)
            verify_copy(expected, tree_files(source, ignore=('su2preconfig.timestamp',)))
            if phase != 'preconfigure':
                require((source / 'su2preconfig.timestamp').is_file(), 'Missing offline preconfigure marker')
            if phase == 'commands-before':
                actual_options = read(build_dir / 'meson-info/intro-buildoptions.json')
                verify_options(actual_options, ref['options'])
                require(target_from_intro(read(build_dir / 'meson-info/intro-targets.json'), build_dir) == FINAL_TARGET,
                        'Unexpected native target')
                original_manifest = (build_dir / 'build.ninja').read_bytes()
                (control / 'original-generated.ninja').write_bytes(original_manifest)
                manifest.write_bytes(derive_manifest(original_manifest))
            if phase == 'compile':
                before_text = (OLD_BASE / (LABEL + '-commands-before.log')).read_text(encoding='utf-8')
                after_text = (OLD_BASE / (LABEL + '-commands-after.log')).read_text(encoding='utf-8')
                delta = verify_command_delta(before_text, after_text)
                common = verify_common_recipe(reference_recipe, after_text)
                # A new directory must not silently import cached objects or a stale executable.
                require(not list(build_dir.rglob('*.obj')) and not (build_dir / FINAL_TARGET).exists(),
                        'Fresh cap build unexpectedly contains compiler outputs')
                require(derive_manifest((build_dir / 'build.ninja').read_bytes()) == manifest.read_bytes(),
                        'Effective Ninja recipe changed after inspection')
                save_new(control / 'effective_build.json', {
                    'target': FINAL_TARGET, 'command_delta': delta, 'common_recipe': common,
                    'original_generated_ninja_sha256': sha(build_dir / 'build.ninja'),
                    'effective_recipe_sha256': sha(manifest),
                    'effective_options_sha256': sha(build_dir / 'meson-info/intro-buildoptions.json'),
                    'commands_before_sha256': sha(OLD_BASE / (LABEL + '-commands-before.log')),
                    'commands_after_sha256': sha(OLD_BASE / (LABEL + '-commands-after.log'))})
            remaining = TOTAL_BUDGET_SECONDS - (time.monotonic() - started)
            require(remaining > 0, 'Total 1800-second fresh build budget exhausted')
            result = run_build(cmds[phase], source, LABEL + '-' + phase, remaining, env,
                               max_tree_gib=3., min_available_gib=1.)
            status['phases'].append(result)
            require(result['succeeded'] is True, 'Native build phase failed: ' + phase)
        verify_copy(expected, tree_files(source, ignore=('su2preconfig.timestamp',)))
        current_reference, current_reproduction = prerequisites()
        require(current_reference[3] == proof and current_reproduction == reproduction,
                'Reference changed before final executable seal')
        for path, value in contract['code_sha256'].items():
            require(sha(ROOT / path) == value, 'Build helper changed during compilation: ' + path)
        require(sha(control / 'contract.json') == status['contract_sha256'] and
                sha(control / 'source.patch') == contract['source_patch_sha256'],
                'Build contract or source patch changed during compilation')
        effective = read(control / 'effective_build.json')
        require(sha(build_dir / 'build.ninja') == effective['original_generated_ninja_sha256'] and
                sha(manifest) == effective['effective_recipe_sha256'],
                'An inspected Ninja manifest changed during compilation')
        executable = inside(build_dir / FINAL_TARGET, build_dir)
        require(executable.is_file(), 'Native cap executable absent')
        require(derive_manifest((build_dir / 'build.ninja').read_bytes()) == manifest.read_bytes(),
                'Recipe changed during compilation')
        status.update(succeeded=True, exe=str(executable), exe_sha256=sha(executable),
                      executable=str(executable.relative_to(ROOT)), executable_sha256=sha(executable),
                      bytes=executable.stat().st_size)
    except Exception as error:
        status['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        status['seconds'] = time.monotonic() - started
        save_new(control / 'status.json', status)
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'build'))
    args = parser.parse_args()
    try:
        if args.action == 'check':
            _, seal = prerequisites()
            print(json.dumps({'ready': True, 'source_not_modified': True, 'no_build_started': True,
                              'reproduction': seal}, indent=2))
        else:
            result = build()
            print(json.dumps({'succeeded': result['succeeded'], 'exe': result.get('exe'),
                              'error': result.get('error'), 'physical_qualification_passed': False}, indent=2))
            raise SystemExit(0 if result['succeeded'] else 1)
    except (ValueError, AssertionError, KeyError, FileNotFoundError) as error:
        print(json.dumps({'ready': False, 'error': str(error), 'physical_qualification_passed': False}), file=sys.stderr)
        raise SystemExit(2)
