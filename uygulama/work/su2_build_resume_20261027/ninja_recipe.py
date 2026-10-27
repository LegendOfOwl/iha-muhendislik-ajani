"""One-edge, source-preserving recovery graph for the frozen p32a build.

The pure helpers accept no shell syntax and never mutate input bytes. The audit
entry point writes a separate manifest/evidence directory and invokes only Ninja
inspection tools and a dry run. It does not compile, reconfigure, install or run
SU2. Original Meson options are historical metadata; the effective recipe is the
original graph plus this explicitly recorded translation-unit-specific option.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess

TARGET = 'SU2_CFD/src/libSU2core.a.p/interfaces_fsi_CFlowTractionInterface.cpp.obj'
SOURCE = '../source/SU2_CFD/src/interfaces/fsi/CFlowTractionInterface.cpp'
EXTRA_ARG = '-I../source/SU2_CFD/src/interfaces'
FINAL_TARGET = 'SU2_CFD/src/SU2_CFD.exe'
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalized_output(value):
    value = value.replace('\\', '/')
    p = PurePosixPath(value)
    require(value == p.as_posix() and not p.is_absolute() and
            all(x not in ('', '.', '..') and ':' not in x for x in p.parts),
            'Unsafe or noncanonical output path')
    return value


def derive_manifest(original):
    """Append the quoted -I to exactly one expected edge; preserve all other bytes."""
    require(isinstance(original, bytes) and original, 'Nonempty bytes required')
    original.decode('utf-8', errors='strict')
    lines = original.splitlines(keepends=True)
    relevant = []
    for i, raw in enumerate(lines):
        line = raw.rstrip(b'\r\n')
        if line.startswith(b'build ') and b'CFlowTractionInterface.cpp' in line:
            # The archive edge also lists this output among its many inputs.
            outputs = line[6:].split(b': ', 1)[0]
            if b'CFlowTractionInterface.cpp' in outputs:
                relevant.append(i)
    require(len(relevant) == 1, 'Exactly one unambiguous traction-object edge required')
    start = relevant[0]
    expected = f'build {TARGET}: cpp_COMPILER {SOURCE}'.encode()
    require(lines[start].rstrip(b'\r\n') == expected, 'Unexpected/deceptive target or source declaration')
    stop = start + 1
    while stop < len(lines) and lines[stop].strip():
        require(lines[stop].startswith(b' '), 'Unexpected target block syntax')
        stop += 1
    bindings = lines[start + 1:stop]
    keys = [line.lstrip().split(b' = ', 1)[0] for line in bindings]
    require(keys == [b'DEPFILE', b'DEPFILE_UNQUOTED', b'ARGS'],
            'Unexpected, duplicate, or missing edge binding')
    require(EXTRA_ARG.encode() not in original and b'-iquote' not in b''.join(bindings),
            'Existing include override is not a pristine recipe')
    index = start + 3
    require(lines[index].startswith(b' ARGS = ') and b'$' not in lines[index],
            'Direct ARGS binding required; expansions are not permitted')
    old_line = lines[index]
    body = old_line.rstrip(b'\r\n')
    ending = old_line[len(body):]
    require(ending in (b'\n', b'\r\n'), 'Terminated ARGS line required')
    lines[index] = body + b' "' + EXTRA_ARG.encode() + b'"' + ending
    result = b''.join(lines)
    require(result.replace(lines[index], old_line, 1) == original,
            'Unintended manifest mutation')
    return result


def windows_arguments(command):
    """Parse Windows C-runtime quote/backslash rules without invoking a shell."""
    require(isinstance(command, str) and '\n' not in command and '\r' not in command,
            'One native command line required')
    args, i, n = [], 0, len(command)
    while i < n:
        while i < n and command[i] in ' \t':
            i += 1
        if i == n:
            break
        chars, quoted = [], False
        while i < n and (quoted or command[i] not in ' \t'):
            if command[i] == '\\':
                start = i
                while i < n and command[i] == '\\':
                    i += 1
                count = i - start
                if i < n and command[i] == '"':
                    chars.extend('\\' * (count // 2))
                    if count % 2:
                        chars.append('"')
                    else:
                        quoted = not quoted
                    i += 1
                else:
                    chars.extend('\\' * count)
            elif command[i] == '"':
                quoted = not quoted
                i += 1
            else:
                chars.append(command[i])
                i += 1
        require(not quoted, 'Unclosed native command quote')
        args.append(''.join(chars))
    require(args, 'Empty native command')
    return args


def command_map(text):
    """Index Ninja -t commands output, allowing the three pinned SU2 edge kinds."""
    require(isinstance(text, str) and text.strip(), 'Nonempty command output required')
    result = {}
    for command in text.splitlines():
        require(command.strip() == command and command, 'Blank/indented command record')
        args = windows_arguments(command)
        executable = args[0].replace('\\', '/').rsplit('/', 1)[-1].lower()
        if executable in ('g++.exe', 'g++'):
            require(args.count('-o') == 1, 'Compiler/link output is ambiguous')
            oi = args.index('-o')
            require(oi + 1 < len(args), 'Missing compiler/link output')
            output = normalized_output(args[oi + 1])
            kind = 'compile' if '-c' in args else 'link'
            if kind == 'compile':
                require(args.count('-c') == 1 and args[-2] == '-c',
                        'Unexpected compilation source syntax')
        elif executable in ('gcc-ar', 'gcc-ar.exe'):
            require(len(args) >= 4 and args[1] == 'csrDT', 'Unexpected archive command')
            output, kind = normalized_output(args[2]), 'archive'
        else:
            raise ValueError('Unexpected command executable: ' + executable)
        require(output.casefold() not in {x.casefold() for x in result},
                'Duplicate/case-colliding command output')
        result[output] = {'command': command, 'arguments': args, 'kind': kind,
                          'command_sha256': digest(command.encode())}
    return result


def verify_command_delta(before_text, after_text):
    before, after = command_map(before_text), command_map(after_text)
    require(list(before) == list(after), 'Build graph command outputs/order changed')
    changed = [key for key in before if before[key]['command'] != after[key]['command']]
    require(changed == [TARGET], 'Exactly the traction-object command may change')
    b, a = before[TARGET], after[TARGET]
    require(b['kind'] == a['kind'] == 'compile' and b['arguments'][-1] == SOURCE,
            'Expected compilation translation unit required')
    require(b['command'].count(' -MD -MQ ') == 1, 'Missing unique dependency flag boundary')
    expected = b['command'].replace(' -MD -MQ ', ' "' + EXTRA_ARG + '" -MD -MQ ', 1)
    require(a['command'] == expected, 'Unintended compilation flag/quoting change')
    require(EXTRA_ARG not in b['arguments'] and a['arguments'].count(EXTRA_ARG) == 1,
            'Unexpected include-argument multiplicity')
    return {'command_count': len(before), 'changed_outputs': changed,
            'unchanged_command_count': len(before) - 1,
            'before_commands_sha256': digest(before_text.encode()),
            'after_commands_sha256': digest(after_text.encode()),
            'changed_before_sha256': b['command_sha256'],
            'changed_after_sha256': a['command_sha256']}


def inventory(commands, existing_outputs, logged_outputs):
    """Classify existing verified cache versus missing targets; no filesystem I/O."""
    existing_outputs, logged_outputs = set(existing_outputs), set(logged_outputs)
    require(existing_outputs <= set(commands) and logged_outputs == existing_outputs,
            'Cache files and successful Ninja log outputs disagree')
    require(TARGET not in existing_outputs, 'Recovery edge unexpectedly already compiled')
    remaining = [key for key in commands if key not in existing_outputs]
    return {'total': len(commands), 'existing': len(existing_outputs),
            'remaining': remaining,
            'remaining_by_kind': {kind: sum(commands[x]['kind'] == kind for x in remaining)
                                  for kind in ('compile', 'archive', 'link')}}


def dry_run_map(text):
    commands, sequence = [], []
    for line in text.splitlines():
        match = re.fullmatch(r'\[(\d+)/(\d+)\] (.+)', line)
        if match:
            sequence.append((int(match[1]), int(match[2])))
            commands.append(match[3])
        else:
            require(line.startswith('ninja: Entering directory ') or not line,
                    'Unexpected non-command dry-run output')
    require(sequence and sequence == [(i, len(sequence)) for i in range(1, len(sequence) + 1)],
            'Incomplete or inconsistent dry-run sequence')
    return command_map('\n'.join(commands))


def verify_dry_run(commands, info, dry_text):
    dry = dry_run_map(dry_text)
    require(set(dry) == set(info['remaining']), 'Dry run would rebuild cached or unexpected outputs')
    for key in dry:
        require(dry[key]['command'] == commands[key]['command'],
                'Dry-run command differs from inspected recipe')
    return {'passed': True, 'planned_targets': len(dry),
            'cached_targets_rebuilt': 0,
            'by_kind': info['remaining_by_kind']}


def snapshot(folder):
    """Preserve bytes and write times; access times are intentionally excluded."""
    return {p.relative_to(folder).as_posix():
            {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size,
             'mtime_ns': p.stat().st_mtime_ns}
            for p in sorted(folder.rglob('*')) if p.is_file()}


def audit(directory, root=ROOT):
    directory = Path(directory).resolve()
    require(directory.is_relative_to(BASE.resolve()) and directory != BASE.resolve(),
            'Fresh audit directory must stay below resume work folder')
    require(not directory.exists(), 'Fresh audit directory required')
    directory.mkdir()
    build = Path(root) / 'tools/su2-build/v8.5.0/controls/p32a/build'
    ninja = Path(root) / '.venv/Scripts/ninja.exe'
    old_snapshot = snapshot(build)
    original = (build / 'build.ninja').read_bytes()
    modified = derive_manifest(original)
    manifest = directory / 'recovery.ninja'
    manifest.write_bytes(modified)
    (directory / 'original.ninja').write_bytes(original)
    for name in ('.ninja_log', '.ninja_deps'):
        (directory / ('original' + name)).write_bytes((build / name).read_bytes())
    outputs = {}
    for name, extra in (('before', []), ('after', ['-f', str(manifest)]),
                        ('dry_run', ['-f', str(manifest), '-n', '-v'])):
        command = [str(ninja), '-C', str(build), *extra]
        command += [FINAL_TARGET] if name == 'dry_run' else ['-t', 'commands', FINAL_TARGET]
        native = subprocess.run(command, capture_output=True, text=True, timeout=30)
        (directory / (name + '.stdout.txt')).write_text(native.stdout, encoding='utf-8', newline='')
        (directory / (name + '.stderr.txt')).write_text(native.stderr, encoding='utf-8', newline='')
        require(native.returncode == 0, 'Ninja inspection failed: ' + name)
        outputs[name] = native.stdout
    delta = verify_command_delta(outputs['before'], outputs['after'])
    commands = command_map(outputs['after'])
    logged = []
    for line in (build / '.ninja_log').read_text().splitlines():
        if line.startswith('# ninja log v'):
            continue
        fields = line.split('\t')
        require(len(fields) == 5, 'Unexpected Ninja log record')
        logged.append(normalized_output(fields[3]))
    existing = [key for key in commands if (build / key).is_file()]
    info = inventory(commands, existing, logged)
    require(info['total'] == 290 and info['existing'] == 258 and len(info['remaining']) == 32 and
            info['remaining_by_kind'] == {'compile': 29, 'archive': 2, 'link': 1},
            'p32a no longer matches the frozen expected recovery stage')
    dry = verify_dry_run(commands, info, outputs['dry_run'])
    require(snapshot(build) == old_snapshot, 'Inspection mutated the original build directory')
    record = {'audit_only': True, 'actual_build_run': False, 'physical_qualification_passed': False,
              'source_modified': False, 'original_build_directory_unchanged': True,
              'original_manifest_sha256': digest(original), 'recovery_manifest_sha256': digest(modified),
              'override': {'target': TARGET, 'source': SOURCE, 'extra_argument': EXTRA_ARG},
              'command_delta': delta, 'inventory': info, 'dry_run': dry,
              'original_build_files': old_snapshot,
              'effective_recipe_note': 'Original p32a options plus exactly one translation-unit include argument; '
                                       'the global cpp_args recipe from p32b is not used.'}
    (directory / 'audit.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audit_directory')
    args = parser.parse_args()
    result = audit(args.audit_directory)
    print(json.dumps({key: result[key] for key in ('audit_only', 'source_modified',
                     'original_build_directory_unchanged', 'command_delta', 'dry_run')}, indent=2))
