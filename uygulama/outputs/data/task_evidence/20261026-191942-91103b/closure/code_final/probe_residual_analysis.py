"""Audit one explicit observation of a frozen restart; never infer CFD qualification.

The small explicit update is an observation device, not a convergence continuation.
Flow and SA residuals belong to their sequential evaluation stages. VTK is imported
only by the CLI reader so the numerical guards can be tested without VTK.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import os
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / 'outputs/simulations/flatplate_SAneg_20261025_v1'
PROBE = CASE / 'residual_probe_20261026_v1'
REPORT = ROOT / 'outputs/reports/residual_probe_20261026.json'
PLOT = ROOT / 'outputs/plots/residual_probe_20261026.png'
DATA = ROOT / 'outputs/data/qualification/flatplate_SAneg_20261025_v1/residual_probe_20261026'
COMPONENTS = ('Rho', 'RhoU', 'RhoV', 'RhoE', 'nu')
CONSERVATIVE = ('Density', 'Momentum_x', 'Momentum_y', 'Energy')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def finite_number(value):
    return not isinstance(value, (bool, np.bool_)) and isinstance(value, (int, float, np.number)) and math.isfinite(float(value))


def residual_norm_check(values, native_rms_log, native_max_log, tolerance, expected_points):
    """No point filtering: a missing, nonfinite, or zero vector fails closed."""
    result = {'passed': False, 'rejected_because': [], 'points': None,
              'computed_log10_RMS': None, 'computed_log10_MAX': None,
              'native_log10_RMS': float(native_rms_log) if finite_number(native_rms_log) else None,
              'native_log10_MAX': float(native_max_log) if finite_number(native_max_log) else None,
              'RMS_log10_error': None, 'MAX_log10_error': None}
    if values is None:
        result['rejected_because'].append('Missing exported residual component')
        return result
    a = np.asarray(values, dtype=float)
    result['points'] = int(a.size)
    if a.ndim != 1 or len(a) != expected_points:
        result['rejected_because'].append('Residual is not one scalar per registered owned node')
    if not np.isfinite(a).all():
        result['rejected_because'].append('Nonfinite exported residual; no nodes removed')
    if not finite_number(native_rms_log) or not finite_number(native_max_log):
        result['rejected_because'].append('Missing/nonfinite native RMS or MAX history value')
    if not finite_number(tolerance) or tolerance < 0:
        result['rejected_because'].append('Invalid preregistered log tolerance')
    if result['rejected_because']:
        return result
    maximum = float(np.max(np.abs(a)))
    if maximum == 0:
        result['rejected_because'].append('Zero vector has no finite log norm or residual-share map')
        return result
    scaled = a / maximum
    lrms = math.log10(maximum) + .5 * math.log10(float(np.mean(scaled * scaled)))
    lmax = math.log10(maximum)
    result.update(computed_log10_RMS=lrms, computed_log10_MAX=lmax,
                  RMS_log10_error=abs(lrms - native_rms_log), MAX_log10_error=abs(lmax - native_max_log))
    if result['RMS_log10_error'] > tolerance:
        result['rejected_because'].append('Exported RMS does not match native cached RMS')
    if result['MAX_log10_error'] > tolerance:
        result['rejected_because'].append('Exported maximum does not match native cached MAX')
    result['passed'] = not result['rejected_because']
    return result


def coordinate_mapping(reference, observed, tolerance, expected_points):
    """Return reference->observed KD-tree permutation only after a bijection check."""
    result = {'passed': False, 'rejected_because': [], 'maximum_distance_m': None,
              'reference_points': len(reference), 'observed_points': len(observed), 'unique_matches': None}
    a, b = np.asarray(reference, dtype=float), np.asarray(observed, dtype=float)
    if (a.ndim != 2 or b.ndim != 2 or a.shape[1] != 2 or b.shape[1] not in (2, 3)
            or len(a) != expected_points or len(b) != expected_points):
        result['rejected_because'].append('Wrong coordinate dimensions or registered node count')
        return result, None
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        result['rejected_because'].append('Nonfinite coordinates; no nodes removed')
        return result, None
    if not finite_number(tolerance) or tolerance < 0:
        result['rejected_because'].append('Invalid preregistered coordinate tolerance')
        return result, None
    if b.shape[1] == 3 and np.max(np.abs(b[:, 2])) > tolerance:
        result['rejected_because'].append('Nonzero out-of-plane coordinates in registered 2D case')
    if len(np.unique(a, axis=0)) != len(a) or len(np.unique(b[:, :2], axis=0)) != len(b):
        result['rejected_because'].append('Duplicate reference or observed coordinates')
    from scipy.spatial import cKDTree
    distance, order = cKDTree(b[:, :2]).query(a)
    result['maximum_distance_m'] = float(np.max(distance))
    result['unique_matches'] = int(len(np.unique(order)))
    if result['unique_matches'] != expected_points:
        result['rejected_because'].append('Nearest-coordinate mapping is not bijective')
    if result['maximum_distance_m'] > tolerance:
        result['rejected_because'].append('Coordinate mapping exceeds registered distance')
    result['passed'] = not result['rejected_because']
    return result, order if result['passed'] else None


def relative_l2(before, after):
    before, after = np.asarray(before, dtype=float), np.asarray(after, dtype=float)
    scale = float(np.max(np.abs(before)))
    if scale == 0:
        return 0.0 if np.array_equal(before, after) else None
    numerator = float(np.linalg.norm((after - before) / scale))
    denominator = float(np.linalg.norm(before / scale))
    value = numerator / denominator
    return value if math.isfinite(value) else None


def conservative_drift(before, after, limit, gamma=1.4):
    """Per conservative field, global L2 relative drift; SA is a separate observation."""
    a, b = np.asarray(before, dtype=float), np.asarray(after, dtype=float)
    result = {'passed': False, 'rejected_because': [], 'relative_L2_by_field': {},
              'Nu_Tilde_relative_L2_observation': None, 'density_min': None, 'pressure_min': None,
              'positive_density_and_pressure': False, 'maximum_conservative_relative_L2': None}
    if a.ndim != 2 or a.shape != b.shape or a.shape[1] != 5 or len(a) == 0:
        result['rejected_because'].append('Expected matching Nx5 native solution arrays')
        return result
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        result['rejected_because'].append('Nonfinite native solution; no nodes removed')
        return result
    if not finite_number(limit) or limit < 0 or not finite_number(gamma) or gamma <= 1:
        result['rejected_because'].append('Invalid registered drift bound or gamma')
        return result
    for label, values in [('seed', a), ('output', b)]:
        rho = values[:, 0]
        if np.min(rho) <= 0:
            result['rejected_because'].append(label + ': nonpositive density')
            continue
        pressure = (gamma - 1) * (values[:, 3] - .5 * np.sum(values[:, 1:3]**2, axis=1) / rho)
        if not np.isfinite(pressure).all() or np.min(pressure) <= 0:
            result['rejected_because'].append(label + ': nonpositive/nonfinite ideal-gas pressure')
        if label == 'output':
            result['density_min'] = float(np.min(rho))
            result['pressure_min'] = float(np.min(pressure)) if np.isfinite(pressure).all() else None
    result['positive_density_and_pressure'] = not result['rejected_because']
    for column, name in enumerate(CONSERVATIVE):
        value = relative_l2(a[:, column], b[:, column])
        result['relative_L2_by_field'][name] = value
        if value is None or value > limit:
            result['rejected_because'].append(name + ': native relative L2 drift exceeds bound or has zero reference norm')
    result['Nu_Tilde_relative_L2_observation'] = relative_l2(a[:, 4], b[:, 4])
    numbers = list(result['relative_L2_by_field'].values())
    if all(v is not None for v in numbers):
        result['maximum_conservative_relative_L2'] = max(numbers)
    result['passed'] = not result['rejected_because']
    return result


def analyse_arrays(mesh_xy, field_xy, residuals, row, seed_xy, seed_values,
                   output_xy, output_values, gates, gamma=1.4):
    """Pure numerical audit; no VTK, filesystem writes, or CFD execution."""
    n, ct = gates['expected_points'], gates['coordinate_mapping_max_m']
    mapping, order = coordinate_mapping(mesh_xy, field_xy, ct, n)
    sm, si = coordinate_mapping(mesh_xy, seed_xy, ct, n)
    om, oi = coordinate_mapping(mesh_xy, output_xy, ct, n)
    checks = {}
    for name in COMPONENTS:
        values = residuals.get(name)
        if values is not None and order is not None and np.asarray(values).shape == (n,):
            values = np.asarray(values)[order]
        checks[name] = residual_norm_check(values, row.get('rms[' + name + ']'),
            row.get('max[' + name + ']'), gates['residual_log10_error_max'], n)
    drift = {'passed': False, 'rejected_because': ['Native seed/output coordinate mapping failed']}
    if si is not None and oi is not None:
        drift = conservative_drift(np.asarray(seed_values)[si], np.asarray(output_values)[oi],
                                   gates['conservative_global_relative_drift_max'], gamma)
    all_norms = all(item['passed'] for item in checks.values())
    accepted = mapping['passed'] and sm['passed'] and om['passed'] and drift['passed'] and all_norms
    return {'coordinate_mapping': mapping, 'seed_coordinate_mapping': sm, 'output_coordinate_mapping': om,
            'components': checks, 'all_five_RMS_and_MAX_match': all_norms, 'native_binary_drift': drift,
            'measurement_accepted': bool(accepted), 'map_authorized': bool(accepted),
            'component_map_authorized': {name: bool(accepted and checks[name]['passed']) for name in COMPONENTS},
            'physical_qualification_passed': False}, order


def shares(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or not len(values):
        raise ValueError('A residual-share map requires every finite scalar value')
    maximum = float(np.max(np.abs(values)))
    if maximum == 0:
        raise ValueError('Zero residual has no nonzero error-share budget')
    weights = (values / maximum)**2
    return weights / np.sum(weights)


def region_mask(xy, region):
    """Inclusive SI rectangles only; unknown/empty definitions are rejected."""
    xy = np.asarray(xy, dtype=float)
    allowed = {'name', 'description', 'x_min', 'x_max', 'y_min', 'y_max', 'x', 'y',
               'x_m', 'y_m', 'x_range_m', 'y_range_m'}
    if not set(region) <= allowed:
        raise ValueError('Unsupported registered region keys: ' + repr(set(region) - allowed))
    mask = np.ones(len(xy), dtype=bool)
    used = False
    for axis, label in enumerate(('x', 'y')):
        pair = next((region[k] for k in (label, label + '_m', label + '_range_m') if k in region), None)
        bounds = (region.get(label + '_min'), region.get(label + '_max')) if pair is None else pair
        if len(bounds) != 2:
            raise ValueError('Region needs two bounds per coordinate')
        lo, hi = bounds
        for value in bounds:
            if value is not None and not finite_number(value):
                raise ValueError('Nonfinite region bound')
        if lo is not None and hi is not None and lo > hi:
            raise ValueError('Region bounds reversed')
        if lo is not None:
            mask &= xy[:, axis] >= lo
            used = True
        if hi is not None:
            mask &= xy[:, axis] <= hi
            used = True
    if not used:
        raise ValueError('Unbounded region is not a registered spatial diagnosis')
    return mask


def spatial_summary(xy, values, regions):
    xy, values = np.asarray(xy, dtype=float), np.asarray(values, dtype=float)
    weights = shares(values)
    peak = int(np.argmax(np.abs(values)))
    count90 = int(np.searchsorted(np.cumsum(np.sort(weights)[::-1]), .9) + 1)
    result = {'points': len(values), 'peak_mesh_node': peak, 'peak_coordinate_m': xy[peak].tolist(),
              'peak_signed_residual_ND': float(values[peak]), 'peak_square_share': float(weights[peak]),
              'nodes_carrying_90_percent_of_squared_residual': count90,
              'fraction_of_nodes_carrying_90_percent': count90 / len(values),
              'regions_overlap_and_must_not_be_summed_as_a_partition': True, 'regions': []}
    entries = [dict(v, name=k) for k, v in regions.items()] if isinstance(regions, dict) else regions
    for region in entries:
        if not region.get('name'):
            raise ValueError('Every registered region needs a name')
        mask = region_mask(xy, region)
        result['regions'].append({'name': region['name'], 'registered_definition': region,
            'nodes': int(mask.sum()), 'squared_residual_share': float(weights[mask].sum())})
    return result


def load_mesh(path):
    lines = Path(path).read_text().splitlines()
    j = next(i for i, line in enumerate(lines) if line.strip().startswith('NPOIN'))
    tokens = lines[j].split('=', 1)[1].split()
    n = int(tokens[0])
    if len(tokens) > 1 and int(tokens[1]) != n:
        raise ValueError('Partitioned mesh ownership is outside this single-process probe')
    xy = np.array([[float(v) for v in line.split()[:2]] for line in lines[j + 1:j + 1 + n]])
    if xy.shape != (n, 2):
        raise ValueError('Incomplete source mesh coordinates')
    return xy


def vtk_field(path):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    if grid.GetNumberOfPoints() == 0:
        raise ValueError('Empty native VTU')
    xyz = vtk_to_numpy(grid.GetPoints().GetData()).astype(float)
    data = {grid.GetPointData().GetArrayName(i): vtk_to_numpy(grid.GetPointData().GetArray(i)).astype(float)
            for i in range(grid.GetPointData().GetNumberOfArrays())}
    return xyz, data


def exported_component(data, scalar, vector=None, column=None):
    if scalar in data:
        a = np.asarray(data[scalar])
        return a[:, 0] if a.ndim == 2 and a.shape[1] == 1 else a
    if vector in data:
        a = np.asarray(data[vector])
        if a.ndim == 2 and a.shape[1] > column:
            return a[:, column]
    return None


def residual_components(data):
    return {'Rho': exported_component(data, 'Residual_Density'),
            'RhoU': exported_component(data, 'Residual_Momentum_x', 'Residual_Momentum', 0),
            'RhoV': exported_component(data, 'Residual_Momentum_y', 'Residual_Momentum', 1),
            'RhoE': exported_component(data, 'Residual_Energy'),
            'nu': exported_component(data, 'Residual_Nu_Tilde')}


def write_csv(path, columns, header):
    np.savetxt(path, np.column_stack(columns), delimiter=',', header=','.join(header), comments='', fmt='%.17g')


def render(report, xy=None, residuals=None):
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'work/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    if not report.get('map_authorized'):
        for ax in axes.flat:
            ax.axis('off')
        axes[0, 0].text(0, .9, 'RESIDUAL MAP REJECTED', weight='bold', fontsize=16)
        axes[0, 0].text(0, .7, '\n'.join(report.get('rejected_because', ['Audit gates did not all pass'])), va='top', wrap=True)
        axes[1, 0].text(0, .9, 'No residual spatial inference is authorized.\nRaw samples remain in the CSV files.\nThis is not a CFD qualification result.', va='top')
    else:
        for row, name in enumerate(('Rho', 'nu')):
            weights = shares(residuals[name])
            positive = weights[weights > 0]
            # Zero nodes remain plotted with a display-only floor, and unchanged in CSV.
            floor = max(float(positive.min()), float(weights.max()) * 1e-12)
            for col, near in enumerate((False, True)):
                ax = axes[row, col]
                art = ax.scatter(xy[:, 0], xy[:, 1], c=np.maximum(weights, floor), s=2, rasterized=True,
                                 norm=LogNorm(vmin=floor, vmax=float(weights.max())), cmap='magma')
                ax.set(xlabel='x [m]', ylabel='y [m]', title=name + ': squared residual share' + ('; wall view' if near else ''))
                if near:
                    ax.set_ylim(0, .05)
                fig.colorbar(art, ax=ax, label='R_i^2 / sum(R_j^2); zeros use display floor')
        fig.suptitle('One-step explicit observation: sequential flow / SA residual stages; not final-field residual')
    fig.tight_layout()
    PLOT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT, dpi=160)
    plt.close(fig)


def main():
    contract_path = PROBE / 'contract.json'
    contract = read(contract_path)
    gates = contract['gates']
    if gates.get('all5_RMS_and_MAX_required') is not True:
        raise ValueError('This evaluator requires the preregistered all-five RMS and MAX gate')
    folder = PROBE / contract.get('native_folder', 'explicit')
    seal_path = folder / 'prediction_frozen.json'
    if not seal_path.exists():
        raise RuntimeError('Native probe is not frozen; this script never starts or extends a solver')
    seal = read(seal_path)
    seed_path = resolve(contract['seed_path'])
    mesh_path = resolve(contract['mesh_path'])
    paths = [contract_path, seal_path, seed_path, mesh_path, folder / 'case.cfg', folder / 'history.csv',
             folder / 'flow_000000.vtu', folder / 'restart_flow_000000.dat', Path(__file__),
             Path(__file__).with_name('test_probe_residual_analysis.py')]
    paths += [resolve(p) for p in contract.get('source_files_sha256', {})]
    source_manifest = resolve(contract['source_manifest']) if 'source_manifest' in contract else None
    source_entries = read(source_manifest) if source_manifest is not None else []
    if source_manifest is not None:
        paths += [source_manifest] + [resolve(entry['path']) for entry in source_entries]
    paths += [seed_path.parent / 'prediction_frozen.json', CASE / 'contract.json']
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.exists()}
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'algorithm_version': 1,
        'gates_unchanged': gates, 'contract_sha256': sha(contract_path), 'source_files_sha256_before': before,
        'measurement_accepted': False, 'map_authorized': False, 'physical_qualification_passed': False,
        'M6_qualification_passed': False, 'LLM_improvement_demonstrated': False, 'rejected_because': [],
        'scope': 'Single source-grid one-step explicit observation of sequential flow and SA residual stages; not a residual recomputation on the final exported solution.',
        'norm_definition': 'sqrt(sum_i R_i^2 / N_owned); every registered owned node including walls and BC nodes, no volume weighting, no masks or removed points; single OpenMP process, no halo nodes.',
        'limits': ['Export/history identity is a measurement check, not convergence or physical acceptance.',
                   'Native binary restart determines drift; float32 VTU solution drift is reported separately.',
                   'Regions can overlap and their shares must not be added as a partition.',
                   'Flow and SA evaluation stages are sequential; this is not a new accepted CFD solution.']}
    try:
        if seal.get('contract_sha256') != sha(contract_path):
            raise ValueError('Probe seal does not match the registered contract')
        for p, expected in seal['files_sha256'].items():
            if sha(resolve(p)) != expected:
                raise ValueError('Frozen native file changed: ' + p)
        for key, path in [('seed_sha256', seed_path), ('mesh_sha256', mesh_path)]:
            if key in contract and sha(path) != contract[key]:
                raise ValueError('Registered input hash mismatch: ' + key)
        for key, path in [('config_sha256', folder / 'case.cfg'),
                          ('parent_seal_sha256', seed_path.parent / 'prediction_frozen.json'),
                          ('physical_contract_sha256', CASE / 'contract.json')]:
            if key in contract and sha(path) != contract[key]:
                raise ValueError('Registered provenance hash mismatch: ' + key)
        if source_manifest is not None and sha(source_manifest) != contract['source_manifest_sha256']:
            raise ValueError('Registered source manifest changed')
        for entry in source_entries:
            if sha(resolve(entry['path'])) != entry['sha256']:
                raise ValueError('Archived source file changed: ' + entry['path'])
        for p, expected in contract.get('source_files_sha256', {}).items():
            if sha(resolve(p)) != expected:
                raise ValueError('Archived source hash mismatch: ' + p)
        matched = seal.get('matched') or {}
        status = seal.get('native_status') or {}
        if status.get('exit_code') != 0 or status.get('stop_reason') is not None:
            raise ValueError('Native observation incomplete or failed')
        if matched.get('field_iteration') != 0 or matched.get('terminal_history_iteration') != 0:
            raise ValueError('Only the registered complete iteration0 tuple may be analysed')
        with (folder / 'history.csv').open() as stream:
            rows = [{k.strip(' "'): float(v) for k, v in row.items()}
                    for row in csv.DictReader(stream, skipinitialspace=True)]
        if len(rows) != 1 or rows[0].get('Inner_Iter') != 0:
            raise ValueError('Probe history must contain exactly registered iteration0')
        from scaled_restart import decode
        _, _, seed = decode(seed_path.read_bytes())
        _, _, output = decode((folder / 'restart_flow_000000.dat').read_bytes())
        xy = load_mesh(mesh_path)
        field_xy, data = vtk_field(folder / 'flow_000000.vtu')
        residuals = residual_components(data)
        numerical, order = analyse_arrays(xy, field_xy, residuals, rows[0], seed[:, :2], seed[:, 2:],
                                         output[:, :2], output[:, 2:], gates, float(contract.get('gamma', 1.4)))
        report.update(numerical, native_array_names=list(data), native_history_iteration0=rows[0])
        # Unrelated diagnostic NaNs such as Buffet/CEff are not residual samples and are kept separately.
        report['native_history_iteration0'] = {k: v if math.isfinite(v) else None for k, v in rows[0].items()}
        report['native_history_nonfinite_columns'] = [k for k, v in rows[0].items() if not math.isfinite(v)]
        report['rejected_because'] = [name + ': ' + reason for name, item in report['components'].items() for reason in item['rejected_because']]
        for key in ('coordinate_mapping', 'seed_coordinate_mapping', 'output_coordinate_mapping', 'native_binary_drift'):
            report['rejected_because'] += [key + ': ' + r for r in report[key]['rejected_because']]
        DATA.mkdir(parents=True, exist_ok=True)
        if order is not None:
            aligned = {k: np.asarray(v)[order] if v is not None and np.asarray(v).shape == (len(xy),) else None
                       for k, v in residuals.items()}
            columns = [np.arange(len(xy)), xy[:, 0], xy[:, 1]]
            header = ['mesh_node', 'x_m', 'y_m']
            for name in COMPONENTS:
                values = aligned[name]
                raw = np.full(len(xy), np.nan) if values is None else values
                valid = np.isfinite(raw)
                normalized = np.full(len(xy), np.nan)
                weight = np.full(len(xy), np.nan)
                if valid.all() and np.any(raw != 0):
                    weight = shares(raw)
                    scaled = raw / np.max(np.abs(raw))
                    normalized = scaled / np.sqrt(np.mean(scaled * scaled))
                columns += [raw, valid.astype(int), normalized, weight]
                header += [name + '_residual_ND', name + '_finite', name + '_Ri_over_export_RMS', name + '_squared_share']
            rawpath = DATA / 'all_owned_nodes.csv'
            write_csv(rawpath, columns, header)
            report['all_points_csv'] = str(rawpath.relative_to(ROOT))
            report['CSV_scope'] = 'Every owned node retained; raw diagnostic values are not an authorized map unless map_authorized=true.'
            if report['map_authorized']:
                regions = contract['regions']
                report['spatial'] = {name: spatial_summary(xy, aligned[name], regions) for name in ('Rho', 'nu')}
                for name in ('Rho', 'nu'):
                    weight = shares(aligned[name])
                    for axis, label in enumerate(('x', 'y')):
                        coords, idx = np.unique(xy[:, axis], return_inverse=True)
                        marginal = np.bincount(idx, weights=weight)
                        write_csv(DATA / (name + '_' + label + '_marginal.csv'), [coords, marginal], [label + '_m', 'squared_residual_share'])
                # VTU solution export is independent of the native-double drift gate.
                vtk_values = [exported_component(data, 'Density'),
                              exported_component(data, 'Momentum_x', 'Momentum', 0),
                              exported_component(data, 'Momentum_y', 'Momentum', 1),
                              exported_component(data, 'Energy'), exported_component(data, 'Nu_Tilde')]
                if all(v is not None and np.asarray(v).shape == (len(xy),) for v in vtk_values):
                    _, si = coordinate_mapping(xy, seed[:, :2], gates['coordinate_mapping_max_m'], gates['expected_points'])
                    report['VTU_float32_solution_drift_observation_only'] = conservative_drift(seed[si, 2:], np.column_stack(vtk_values)[order], gates['conservative_global_relative_drift_max'])
                render(report, xy, aligned)
            else:
                render(report)
        else:
            report['CSV_scope'] = 'Coordinate mapping failed; mesh-ordered CSV and residual maps are withheld.'
            render(report)
    except (ValueError, KeyError, OSError, AssertionError, RuntimeError) as error:
        report.update(measurement_accepted=False, map_authorized=False, physical_qualification_passed=False)
        report['component_map_authorized'] = {name: False for name in COMPONENTS}
        report['rejected_because'].append(type(error).__name__ + ': ' + str(error))
        render(report)
    after = {p: sha(ROOT / p) for p in before}
    report['source_files_sha256_after'] = after
    report['raw_inputs_unchanged'] = before == after
    if before != after:
        report.update(measurement_accepted=False, map_authorized=False)
        report['component_map_authorized'] = {name: False for name in COMPONENTS}
        report['rejected_because'].append('A source/native input changed during postprocessing')
        render(report)
    report['plot'] = str(PLOT.relative_to(ROOT))
    report['output_files_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in ([PLOT] + sorted(DATA.glob('*.csv'))) if p.exists()}
    save(REPORT, report)
    print({key: report.get(key) for key in ('measurement_accepted', 'map_authorized', 'all_five_RMS_and_MAX_match', 'raw_inputs_unchanged', 'rejected_because')}, flush=True)
    return report


if __name__ == '__main__':
    main()
