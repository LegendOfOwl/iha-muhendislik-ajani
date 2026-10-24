"""Narrow reusable checks derived from observed failures; no CFD qualification."""
import hashlib
import math
from pathlib import Path


def boundary_nodes(line, point_count, dimension=3):
    """SU2 boundary connectivity, optionally followed by a boundary element ID."""
    values = [int(v) for v in line.split('%', 1)[0].split()]
    if not values:
        raise ValueError('Empty boundary record')
    counts = {2: {3: 2}, 3: {5: 3, 9: 4}}
    count = counts.get(dimension, {}).get(values[0])
    if count is None or len(values) not in (count + 1, count + 2):
        raise ValueError('Unsupported boundary type or wrong record length')
    nodes = tuple(values[1:count + 1])
    if len(set(nodes)) != count or any(n < 0 or n >= point_count for n in nodes):
        raise ValueError('Repeated or out-of-range node')
    if len(values) == count + 2 and values[-1] < 0:
        raise ValueError('Negative boundary element ID')
    return nodes


def su2_policy(config, version):
    """Only the version/policy combination verified by our native failed run."""
    fields = {}
    for line in config.splitlines():
        line = line.split('%', 1)[0].strip()
        if '=' in line:
            key, value = (v.strip().upper() for v in line.split('=', 1))
            if key in fields:
                raise ValueError('Duplicate config key: ' + key)
            fields[key] = value
    if version != '8.5.0':
        return {'covered': False, 'reason': 'Native check required for this version'}
    if fields.get('CONV_NUM_METHOD_FLOW') in ('JST', 'JST_MAT'):
        if fields.get('MUSCL_FLOW') != 'NO':
            raise ValueError('SU2 8.5.0 centered policy requires explicit MUSCL_FLOW=NO')
        return {'covered': True}
    return {'covered': False, 'reason': 'Policy outside this narrow guard'}


def complete_checkpoint(records, history_iterations, case_identity, requested=None):
    """Select a complete validated tuple; caller must establish native field metadata.

    A record must give role, iteration, path, expected SHA256 and case identity.
    File names alone never establish iteration or geometry identity here.
    """
    required = {'surface', 'volume', 'restart'}
    grouped = {}
    for rec in records:
        if rec['role'] not in required:
            continue
        if rec['case_identity'] != case_identity:
            raise ValueError('Geometry/conditions/mesh identity mismatch')
        iteration = rec['iteration']
        if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 0:
            raise ValueError('Invalid iteration metadata')
        path = Path(rec['path'])
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError('Missing or empty checkpoint artifact')
        if hashlib.sha256(path.read_bytes()).hexdigest() != rec['sha256']:
            raise ValueError('Checkpoint artifact changed')
        group = grouped.setdefault(iteration, {})
        if rec['role'] in group:
            raise ValueError('Ambiguous artifact for the same role and iteration')
        group[rec['role']] = rec
    valid = [i for i, g in grouped.items()
             if set(g) == required and i in set(history_iterations)]
    if requested is not None:
        if requested not in valid:
            raise ValueError('Requested iteration lacks a complete matched tuple')
        return {'iteration': requested, 'artifacts': grouped[requested]}
    if not valid:
        raise ValueError('No complete matched field/history tuple')
    iteration = max(valid)
    return {'iteration': iteration, 'artifacts': grouped[iteration]}


def required_gates(required, observed):
    if not required or len(set(required)) != len(required):
        raise ValueError('An explicit nonempty unique gate contract is required')
    states = {k: observed.get(k) is True for k in required}
    return {'passed': all(states.values()), 'gates': states,
            'missing': [k for k in required if k not in observed]}


def raw_below(value, limit):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and math.isfinite(limit) and value < limit)
