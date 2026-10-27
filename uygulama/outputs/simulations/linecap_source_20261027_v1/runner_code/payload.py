"""Read-only payload extraction for the registered 2-D SA LINELET build test.

extract_payload(case_dir, *, contract, mesh_path, seed_path, rhs_csv,
                rhs_sha256, residual_si_factors, native_contract_path,
                share_sum_tolerance, identities=None, field_reader=None,
                workspace_root=ROOT)

Returns {payload, accepted_for_decision, checks, errors, evidence}. No output is
written and no program is launched. ``residual_si_factors`` maps the five bare
component names to positive ND->SI integrated-flux multipliers; no Mach, gas or
normalization value is inferred from an old benchmark. ``identities`` optionally
supplies opaque source_tree_sha256/compiler_manifest_sha256/runtime_manifest_sha256
values authenticated by the caller's actual build manifests. Missing identities
are not invented. Their provenance and build authenticity are outside this reader.

The existing benchmark binary decoder and bijective coordinate mapper are loaded
by explicit file path. VTK is imported lazily only in read_vtu(), which requires
.venv-cad. Numerical/unit tests use an injected field_reader(path)->(xyz, arrays).
Missing fields never fall back to another iteration, the old one-step membership
measurement, primitive reconstruction, or a mask filled with zeros.

Canonical comparison config keeps EVERY explicit option except the values of
six input/output filename options, replaced by role tokens. Input bytes are
hashed separately; executable identity is recorded separately. The conservative
``physics_sha256`` hashes the full explicit canonical config, mesh and SI factors;
it is a strict superset of physical settings, not proof of unrecorded defaults.
"""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import math
import re
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ('Rho', 'RhoU', 'RhoV', 'RhoE', 'nu')
_PATH_ROLES = {
    'MESH_FILENAME': '@MESH', 'SOLUTION_FILENAME': '@SEED',
    'CONV_FILENAME': '@HISTORY', 'RESTART_FILENAME': '@RESTART',
    'VOLUME_FILENAME': '@VOLUME', 'SURFACE_FILENAME': '@SURFACE',
}
_SCALARS = ('Density', 'Pressure', 'Energy', 'Nu_Tilde', 'Temperature',
            'Mach', 'Laminar_Viscosity', 'Eddy_Viscosity')
_VECTORS = ('Momentum', 'Velocity')
_HELPERS = {}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode('utf-8')).hexdigest()


def _number(value, minimum=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
        return False
    try:
        return math.isfinite(float(value)) and (minimum is None or value >= minimum)
    except (TypeError, ValueError, OverflowError):
        return False


def _integer(value, minimum=0):
    return _number(value, minimum) and float(value).is_integer()


def _valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def _helper(name):
    if name not in _HELPERS:
        path = ROOT / 'work/flatplate_20261025' / (name + '.py')
        spec = importlib.util.spec_from_file_location('_linecap_payload_' + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _HELPERS[name] = module
    return _HELPERS[name]


def parse_config(text):
    result = {}
    for raw in text.splitlines():
        line = raw.split('%', 1)[0].strip()
        if not line:
            continue
        if '=' not in line:
            raise ValueError('Unparsed SU2 config line: ' + line)
        key, value = (part.strip() for part in line.split('=', 1))
        if not key or not value or key in result:
            raise ValueError('Empty or duplicate SU2 config key: ' + key)
        result[key] = value
    return result


def canonical_config(config):
    return {key: _PATH_ROLES.get(key, re.sub(r'\s+', '', value))
            for key, value in sorted(config.items())}


def _configured_path(folder, value, extension=None):
    value = value.strip().strip('"\'')
    path = Path(value)
    if extension and path.suffix == '':
        path = path.with_suffix(extension)
    return path if path.is_absolute() else folder / path


def _mesh_points(path, expected):
    lines = Path(path).read_text(encoding='utf-8-sig').splitlines()
    dimension = [line for line in lines if line.strip().startswith('NDIME=')]
    if len(dimension) != 1 or int(dimension[0].split('=', 1)[1]) != 2:
        raise ValueError('Only the registered 2D SU2 mesh is supported')
    headers = [i for i, line in enumerate(lines) if line.strip().startswith('NPOIN=')]
    if len(headers) != 1:
        raise ValueError('Missing or duplicate mesh point header')
    index = headers[0]
    counts = [int(value) for value in lines[index].split('=', 1)[1].split()]
    if counts[0] != expected or (len(counts) > 1 and counts[1] != expected):
        raise ValueError('Mesh/owned node count differs from the registered all-owned grid')
    points = []
    for node, line in enumerate(lines[index + 1:index + 1 + expected]):
        values = line.split()
        if len(values) not in (2, 3) or (len(values) == 3 and int(values[2]) != node):
            raise ValueError('Unexpected mesh point layout or point ordering')
        points.append([float(values[0]), float(values[1])])
    a = np.asarray(points, dtype=float)
    if a.shape != (expected, 2) or not np.isfinite(a).all():
        raise ValueError('Missing or nonfinite mesh coordinates')
    return a


def read_history(path, factors, iterations):
    """Return required raw columns plus exact integer Krylov counts; no filtering."""
    if (set(factors) != set(COMPONENTS)
            or not all(_number(value, 0) and value > 0 for value in factors.values())):
        raise ValueError('All five explicit positive finite SI factors are required')
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.reader(stream, skipinitialspace=True)
        columns = [label.strip().strip('"') for label in next(reader)]
        if len(columns) != len(set(columns)):
            raise ValueError('Duplicate normalized history column')
        required = ['Inner_Iter', 'CD', 'Linear_Solver_Iterations', 'LinSolIterTurb']
        required += ['rms[' + key + ']' for key in COMPONENTS]
        if any(key not in columns for key in required):
            raise ValueError('Missing required flow/SA history column')
        raw_rows, rows, auxiliary = [], [], set()
        for index, values in enumerate(reader):
            if len(values) != len(columns):
                raise ValueError('Ragged or empty history row')
            raw = {key: float(value) for key, value in zip(columns, values)}
            if (not all(_number(raw[key]) for key in required)
                    or not _integer(raw['Inner_Iter']) or int(raw['Inner_Iter']) != index
                    or not _integer(raw['Linear_Solver_Iterations'])
                    or not _integer(raw['LinSolIterTurb'])):
                raise ValueError('Nonfinite, fractional, missing or repeated required history value')
            auxiliary.update(key for key, value in raw.items() if key not in required and not math.isfinite(value))
            si = {key: raw['rms[' + key + ']'] + math.log10(float(factors[key])) for key in COMPONENTS}
            if not all(math.isfinite(value) for value in si.values()):
                raise ValueError('Nonfinite SI residual conversion')
            rows.append(dict(iteration=index, rms=si, CD=raw['CD'],
                             flow_iterations=int(raw['Linear_Solver_Iterations']),
                             SA_iterations=int(raw['LinSolIterTurb'])))
            raw_rows.append(raw)
    if len(rows) != iterations:
        raise ValueError('History is not the exact registered sequence; no truncation')
    return rows, raw_rows, sorted(auxiliary)


def read_vtu(path):
    """The only VTK dependency; call using .venv-cad."""
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path)); reader.Update()
    grid = reader.GetOutput()
    if grid.GetNumberOfPoints() <= 0 or grid.GetPoints() is None:
        raise ValueError('Empty or unreadable selected native VTU')
    names = [grid.GetPointData().GetArrayName(i) for i in range(grid.GetPointData().GetNumberOfArrays())]
    if None in names or len(names) != len(set(names)):
        raise ValueError('Missing or duplicate native point array name')
    return (vtk_to_numpy(grid.GetPoints().GetData()).astype(float),
            {name: vtk_to_numpy(grid.GetPointData().GetArray(i)).astype(float)
             for i, name in enumerate(names)})


def _rhs(path, expected, tolerance):
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        required = {'mesh_node', 'x_m', 'y_m', 'Rho_residual_ND', 'Rho_finite', 'Rho_squared_share'}
        if (not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames))
                or not required.issubset(reader.fieldnames)):
            raise ValueError('Missing fixed old RHS columns')
        rows = list(reader)
    if len(rows) != expected:
        raise ValueError('Fixed old RHS does not retain every registered node')
    xy, residuals, shares = [], [], []
    for index, row in enumerate(rows):
        node, valid = float(row['mesh_node']), float(row['Rho_finite'])
        values = [float(row[key]) for key in ('x_m', 'y_m', 'Rho_residual_ND', 'Rho_squared_share')]
        if (not _integer(node) or int(node) != index or valid != 1
                or not all(_number(value) for value in values) or not 0 <= values[3] <= 1):
            raise ValueError('Invalid fixed RHS coordinate/order/validity/share; no rows removed')
        xy.append(values[:2]); residuals.append(values[2]); shares.append(values[3])
    residuals, shares = np.asarray(residuals), np.asarray(shares)
    maximum = float(np.max(np.abs(residuals)))
    if maximum <= 0:
        raise ValueError('Zero fixed RHS cannot define a normalized squared-residual map')
    squared = (residuals / maximum) ** 2
    recomputed = squared / squared.sum()
    if abs(float(shares.sum()) - 1) > tolerance or np.max(np.abs(recomputed - shares)) > tolerance:
        raise ValueError('Fixed RHS shares fail normalization or raw-residual recomputation')
    return np.asarray(xy), shares


def extract_payload(case_dir, *, contract, mesh_path, seed_path, rhs_csv,
                    rhs_sha256, residual_si_factors, native_contract_path,
                    share_sum_tolerance, identities=None, field_reader=None,
                    workspace_root=ROOT):
    folder, mesh_path, seed_path = Path(case_dir), Path(mesh_path), Path(seed_path)
    root, rhs_csv, native_contract_path = Path(workspace_root), Path(rhs_csv), Path(native_contract_path)
    payload = dict(normalization=None, native_exit_code=None, field_iteration=None,
                   history_iteration=None, last100_samples=None, CD_last100_range=None,
                   elapsed_seconds=None, history=[], membership=None, identity={},
                   field_validity=dict(rho_positive_finite=False, pressure_positive_finite=False,
                                       required_arrays_finite=False))
    checks = dict(valid_extraction_contract=False, config_input_bytes=False,
                  frozen_files_and_native_process=False, exact_SI_history=False,
                  coeval_registered_tuple=False, fixed_old_RHS=False,
                  complete_positive_fields=False, native_membership=False)
    errors, evidence = [], {
        'scope': 'Registered all-owned 2D SA source grid; same frozen old sequential-stage RHS.',
        'opaque_identity_provenance': 'Optional caller-supplied hashes from actual pinned build manifests; not derived or authenticated here.',
        'colors_are_not_line_IDs': True, 'uses_old_one_step_membership': False,
        'physical_qualification_passed': False,
    }

    def finish():
        return dict(payload=payload, accepted_for_decision=all(checks.values()),
                    checks=checks, errors=errors, evidence=evidence)

    try:
        if (not isinstance(contract, dict) or contract.get('normalization') != 'SI2D'
                or not _integer(contract.get('iterations'), 1)
                or not _integer(contract.get('comparison_iteration'))
                or contract['comparison_iteration'] != contract['iterations'] - 1
                or not _integer(contract.get('last_window_samples'), 1)
                or contract['last_window_samples'] > contract['iterations']
                or not _integer(contract.get('membership_expected_nodes'), 1)
                or not _number(contract.get('coordinate_mapping_max_m'), 0)
                or not _valid_sha(rhs_sha256)
                or not _number(share_sum_tolerance, 0)):
            raise ValueError('Missing/invalid explicit extraction contract')
        checks['valid_extraction_contract'] = True
        n, iteration = int(contract['membership_expected_nodes']), int(contract['comparison_iteration'])
        config_path = folder / 'case.cfg'
        config = parse_config(config_path.read_text(encoding='utf-8-sig'))
        if (config.get('REF_DIMENSIONALIZATION') != 'FREESTREAM_VEL_EQ_MACH'
                or config.get('RESTART_SOL') != 'YES' or config.get('READ_BINARY_RESTART') != 'YES'
                or config.get('MESH_FORMAT') != 'SU2'
                or config.get('TIME_DISCRE_FLOW') != 'EULER_IMPLICIT'
                or config.get('TIME_DISCRE_TURB') != 'EULER_IMPLICIT'
                or int(config.get('ITER', '-1')) != contract['iterations']):
            raise ValueError('Config is not the registered ND implicit/restart/native-mesh scope')
        if (sha(_configured_path(folder, config['MESH_FILENAME'])) != sha(mesh_path)
                or sha(_configured_path(folder, config['SOLUTION_FILENAME'], '.dat')) != sha(seed_path)):
            raise ValueError('Supplied mesh/seed bytes are not those selected by native config')
        canonical = canonical_config(config)
        identity = dict(mesh_sha256=sha(mesh_path), seed_sha256=sha(seed_path),
                        comparison_config_sha256=_digest(canonical))
        # Validate factors before encoding them into the explicit physics identity.
        if (set(residual_si_factors) != set(COMPONENTS)
                or not all(_number(x, 0) and x > 0 for x in residual_si_factors.values())):
            raise ValueError('Explicit positive five-component SI factors are required')
        factors = {key: float(residual_si_factors[key]) for key in COMPONENTS}
        identity['physics_sha256'] = _digest(dict(explicit_config=canonical,
            mesh_sha256=identity['mesh_sha256'], residual_ND_to_SI_factors=factors))
        if identities is not None and not isinstance(identities, dict):
            raise ValueError('Opaque identity evidence must be a dictionary or None')
        for key in ('source_tree_sha256', 'compiler_manifest_sha256', 'runtime_manifest_sha256'):
            if identities is not None and key in identities:
                if not _valid_sha(identities[key]):
                    raise ValueError('Malformed opaque build identity: ' + key)
                identity[key] = identities[key]
        payload['identity'] = identity
        checks['config_input_bytes'] = True
        evidence.update(config_sha256=sha(config_path), canonical_config=canonical,
                        residual_ND_to_SI_factors=factors)
        mesh_xy = _mesh_points(mesh_path, n)
        seal_path = folder / 'prediction_frozen.json'
        seal, status, process = (_read(folder / name) for name in
                                ('prediction_frozen.json', 'solver.status.json', 'solver.process.json'))
        status_proven = (
            isinstance(status.get('exit_code'), int) and not isinstance(status['exit_code'], bool)
            and status['exit_code'] == 0 and status.get('stop_reason') is None
            and _number(status.get('seconds'), 0) and status['seconds'] > 0
            and seal.get('native_status') == status
            and _integer(process.get('pid'), 1) and _integer(process.get('created_filetime'), 1)
            and process.get('started_utc') == status.get('started_utc')
            and isinstance(process.get('started_utc'), str) and bool(process['started_utc'])
            and process.get('command') == status.get('command')
            and isinstance(process.get('command'), list) and bool(process['command'])
            and isinstance(process.get('executable'), str)
            and process['command'][0] == process['executable'])
        if not status_proven:
            raise ValueError('Missing/inconsistent native exit, process identity or frozen status')
        if seal.get('contract_sha256') != sha(native_contract_path) or seal.get('mesh_sha256') != sha(mesh_path):
            raise ValueError('Frozen native contract or mesh differs from registered inputs')
        records = seal.get('files_sha256')
        if not isinstance(records, dict) or not records:
            raise ValueError('No frozen raw-file records')
        verified = {}
        for name, expected in records.items():
            path = Path(name)
            path = path if path.is_absolute() else root / path
            if not _valid_sha(expected) or sha(path) != expected:
                raise ValueError('Frozen raw-file hash mismatch: ' + name)
            verified[path.resolve()] = expected
        history_path = _configured_path(folder, config['CONV_FILENAME'], '.csv')
        volume = _configured_path(folder, config['VOLUME_FILENAME'] + f'_{iteration:06d}.vtu')
        surface = _configured_path(folder, config['SURFACE_FILENAME'] + f'_{iteration:06d}.vtu')
        restart = _configured_path(folder, config['RESTART_FILENAME'] + f'_{iteration:06d}.dat')
        mandatory = [config_path, seed_path, history_path, volume, surface, restart,
                     folder / 'solver.status.json', folder / 'solver.process.json']
        if any(path.resolve() not in verified for path in mandatory):
            raise ValueError('Selected coeval files/config/seed/process were not all frozen')
        checks['frozen_files_and_native_process'] = True
        evidence.update(seal_sha256=sha(seal_path), verified_file_records=len(verified),
                        selected_files={key: str(path) for key, path in
                                        [('volume', volume), ('surface', surface), ('restart', restart)]},
                        executable=process['executable'])
        rows, raw_rows, auxiliary = read_history(history_path, factors, int(contract['iterations']))
        tail = rows[-int(contract['last_window_samples']):]
        cd_range = max(row['CD'] for row in tail) - min(row['CD'] for row in tail)
        matched = seal.get('matched')
        if (not isinstance(matched, dict)
                or not _integer(matched.get('field_iteration'))
                or not _integer(matched.get('terminal_history_iteration'))
                or matched['field_iteration'] != matched['terminal_history_iteration']
                or matched['field_iteration'] != iteration
                or matched.get('last100_samples') != len(tail)
                or matched.get('CD_last100_range') != cd_range
                or matched.get('CD') != raw_rows[-1]['CD']
                or any(matched.get('rms[' + key + ']') != raw_rows[-1]['rms[' + key + ']'] for key in COMPONENTS)):
            raise ValueError('Frozen field/history/raw-final-row tuple is not coeval at the registered iteration')
        payload.update(normalization='SI2D', native_exit_code=0, field_iteration=iteration,
                       history_iteration=rows[-1]['iteration'], last100_samples=len(tail),
                       CD_last100_range=cd_range, elapsed_seconds=float(status['seconds']), history=rows)
        checks['exact_SI_history'] = checks['coeval_registered_tuple'] = True
        evidence['nonfinite_auxiliary_history_columns'] = auxiliary
        if sha(rhs_csv) != rhs_sha256:
            raise ValueError('Fixed original RHS CSV hash differs from the preregistered hash')
        rhs_xy, shares = _rhs(rhs_csv, n, float(share_sum_tolerance))
        mapping = _helper('probe_residual_analysis').coordinate_mapping
        rhs_map, rhs_order = mapping(mesh_xy, rhs_xy, contract['coordinate_mapping_max_m'], n)
        if not rhs_map['passed'] or not np.array_equal(rhs_order, np.arange(n)):
            raise ValueError('Fixed RHS is not in canonical source-mesh node order')
        checks['fixed_old_RHS'] = True
        xyz, arrays = (field_reader or read_vtu)(volume)
        xyz, arrays = np.asarray(xyz, dtype=float), dict(arrays)
        mapped, order = mapping(rhs_xy, xyz, contract['coordinate_mapping_max_m'], n)
        if not mapped['passed']:
            raise ValueError('Selected native field mapping is not a complete bijection')
        for key in _SCALARS + _VECTORS:
            if key not in arrays:
                raise ValueError('Missing required native primitive/solution array: ' + key)
            values = np.asarray(arrays[key], dtype=float)
            shape = (n, 3) if key in _VECTORS else (n,)
            if values.shape != shape or not np.isfinite(values).all():
                raise ValueError('Invalid shape or nonfinite required native array: ' + key)
        for key, values in arrays.items():
            values = np.asarray(values, dtype=float)
            if values.ndim < 1 or values.shape[0] != n or not np.isfinite(values).all():
                raise ValueError('Nonfinite or partial native point array: ' + key)
        rho_ok = bool(np.all(np.asarray(arrays['Density']) > 0))
        pressure_ok = bool(np.all(np.asarray(arrays['Pressure']) > 0))
        _, _, binary = _helper('scaled_restart').decode(restart.read_bytes())
        binary_map, _ = mapping(rhs_xy, binary[:, :2], contract['coordinate_mapping_max_m'], n)
        gamma = float(config['GAMMA_VALUE'])
        if not binary_map['passed'] or not _number(gamma) or gamma <= 1:
            raise ValueError('Native double restart mapping/gamma is invalid')
        native_rho = binary[:, 2]
        with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
            native_p = (gamma - 1) * (binary[:, 5] - .5 * np.sum(binary[:, 3:5] ** 2, axis=1) / native_rho)
        rho_ok = rho_ok and bool(np.isfinite(native_rho).all() and np.all(native_rho > 0))
        pressure_ok = pressure_ok and bool(np.isfinite(native_p).all() and np.all(native_p > 0))
        payload['field_validity'] = dict(rho_positive_finite=rho_ok,
                                         pressure_positive_finite=pressure_ok,
                                         required_arrays_finite=True)
        checks['complete_positive_fields'] = rho_ok and pressure_ok
        evidence.update(native_arrays=sorted(arrays), native_binary_points=len(binary),
                        native_density_min=float(np.min(native_rho)),
                        native_pressure_min=float(np.min(native_p)) if np.isfinite(native_p).all() else None)
        if not checks['complete_positive_fields']:
            raise ValueError('Nonpositive/nonfinite density or pressure in VTU/native binary')
        if 'Linelet' not in arrays:
            raise ValueError('Missing native Linelet array; no old one-step/backfilled membership is allowed')
        color = np.asarray(arrays['Linelet'], dtype=float)
        if (color.shape != (n,) or not np.isfinite(color).all() or np.any(color < 0)
                or np.any(color != np.floor(color))):
            raise ValueError('Invalid native Linelet graph-color values')
        mask = color[order] > 0
        payload['membership'] = dict(node_ids=list(range(n)), mask=mask.tolist(), mapping=mapped,
                                     Rho_squared_share=float(shares[mask].sum()), fixed_RHS_sha256=rhs_sha256)
        checks['native_membership'] = True
        evidence.update(linelet_nodes=int(mask.sum()), fixed_RHS_sha256=rhs_sha256,
                        source_RHS_scope='Frozen original explicit sequential flow/SA stage snapshot; not this implicit field residual')
    except (OSError, ValueError, TypeError, KeyError, AssertionError, StopIteration, OverflowError) as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc))
    return finish()
