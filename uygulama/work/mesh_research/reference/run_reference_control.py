"""Published NASA PLOT3D mesh control, separate from the geometry-only mesh test.

The original source mesh coordinates are never moved. The coincident wake cut
is welded into internal edges in SU2's unstructured format. No experimental
coefficients are supplied to the solver or used to choose numerical settings.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'outputs/projects/proje-15cce2de02'
NAME = 'v3_reference_sourcegrid'
CASE = OUT / 'simulations' / NAME
SOURCE = ROOT / 'work/blind_validation/reviewer/additional_sources/raetaf.x.fmt'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mesh():
    CASE.mkdir(parents=True, exist_ok=True)
    if (CASE / 'mesh.su2').exists():
        raise RuntimeError('Preserve an existing mesh; use a new case version.')
    values = np.fromstring(SOURCE.read_text(), sep=' ')
    ni, nj = map(int, values[:2])
    assert (ni, nj) == (369, 65) and len(values) == 2 + 2 * ni * nj
    p = values[2:].reshape(2, nj, ni).transpose(1, 2, 0)
    # NASA I33..337 (1-based) is the wall; I1..33 and I337..369
    # coincide in reverse order at J1, including both TE copies.
    assert np.array_equal(p[0, :33], p[0, -1:-34:-1])
    ids = np.empty((nj, ni), dtype=int)
    nodes, lookup = [], {}
    for j in range(nj):
        for i in range(ni):
            # Exact tuple equality: no rounding or geometric smoothing.
            key = tuple(p[j, i])
            if key not in lookup:
                lookup[key] = len(nodes)
                nodes.append(key)
            ids[j, i] = lookup[key]
    nodes = np.asarray(nodes)
    cells = []
    for j in range(nj - 1):
        for i in range(ni - 1):
            q = [ids[j, i], ids[j, i+1], ids[j+1, i+1], ids[j+1, i]]
            xy = nodes[q]
            area = .5 * np.sum(xy[:, 0] * np.roll(xy[:, 1], -1) - xy[:, 1] * np.roll(xy[:, 0], -1))
            if area < 0:
                q.reverse()
            assert area != 0 and len(set(q)) == 4
            cells.append(q)
    wall = [(ids[0, i], ids[0, i+1]) for i in range(32, 336)]
    far = [(ids[-1, i], ids[-1, i+1]) for i in range(ni-1)]
    far += [(ids[j, 0], ids[j+1, 0]) for j in range(nj-1)]
    far += [(ids[j, -1], ids[j+1, -1]) for j in range(nj-1)]
    with (CASE / 'mesh.su2').open('w') as f:
        f.write(f'NDIME= 2\nNELEM= {len(cells)}\n')
        for k, q in enumerate(cells):
            f.write('9 ' + ' '.join(map(str, q)) + f' {k}\n')
        f.write(f'NPOIN= {len(nodes)}\n')
        for k, (x, y) in enumerate(nodes):
            f.write(f'{x:.16g} {y:.16g} {k}\n')
        f.write('NMARK= 2\n')
        for tag, edges in [('AIRFOIL', wall), ('FARFIELD', far)]:
            f.write(f'MARKER_TAG= {tag}\nMARKER_ELEMS= {len(edges)}\n')
            for a, b in edges:
                f.write(f'3 {a} {b}\n')
    np.savez_compressed(CASE / 'original_structured_coordinates.npz', xy=p, node_ids=ids)
    audit_module = load_module('reference_topology_audit', ROOT / 'work/blind_validation/reviewer/audit_export_topology.py')
    audit = audit_module.audit(NAME)
    assert audit['topology_and_positive_area_checks_passed'], audit
    # Corner Jacobians detect a folded bilinear quadrangle missed by area alone.
    q = nodes[np.array(cells)]
    outgoing = np.roll(q, -1, axis=1) - q
    incoming = q - np.roll(q, 1, axis=1)
    jac = incoming[:, :, 0] * outgoing[:, :, 1] - incoming[:, :, 1] * outgoing[:, :, 0]
    audit['minimum_corner_cross_product_m2'] = float(jac.min())
    audit['all_corner_jacobians_positive'] = bool(np.all(jac > 0))
    assert audit['all_corner_jacobians_positive']
    spacing = np.linalg.norm(p[1, 32:337] - p[0, 32:337], axis=1)
    audit['first_wall_node_spacing_m'] = {'min': float(spacing.min()), 'max': float(spacing.max())}
    audit['source'] = {
        'url': 'https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf.x.fmt',
        'local_path': str(SOURCE.relative_to(ROOT)), 'sha256': sha(SOURCE),
        'published_dimensions': [ni, nj], 'source_chord_unit': 'normalized by chord',
        'solver_chord_m': 1.0, 'source_coordinates_changed': False,
        'exact_coincident_nodes_welded': ni * nj - len(nodes),
        'wake_cut': 'J1 I1..33 paired exactly with I369..337, no wake wall',
    }
    audit['scope'] = {
        'arm': 'parent reference-mesh diagnostic; not a new blind prediction or new mesher qualification',
        'not_a_pure_mesh_comparison_to_v2': [
            'Published 305-point polygon differs from the r2 interpolated source curve.',
            'Published far boundary is roughly 20-27 chords, not the v2 200c square.',
            'Outer boundary uses the existing SU2 characteristic FARFIELD on all outer edges; WIND uses FREESTREAM plus downstream pressure OUTFLOW.',
            'Wall spacing about 1e-5c is unchanged; strict max y+<1 is not assumed.',
        ],
        'purpose': 'Test native SU2 on a published structured C-grid without experimental fitting; identify whether mesh construction merits targeted investigation.',
        'gates_unchanged': True,
    }
    audit['mesh_sha256'] = sha(CASE / 'mesh.su2')
    (CASE / 'mesh_audit.json').write_text(json.dumps(audit, indent=2))
    plot_mesh(p)
    print(json.dumps({k: v for k, v in audit.items() if k not in ['source', 'scope']}, indent=2))


def plot_mesh(p):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    views = [((-.05, 1.2), (-.15, .2), 'Published C-grid near body'),
             ((-.015, .035), (-.035, .035), 'Leading edge'),
             ((.88, 1.1), (-.025, .04), 'Trailing edge and welded wake')]
    for ax, (xlim, ylim, title) in zip(axes, views):
        for line in p:
            ax.plot(line[:, 0], line[:, 1], color='#426780', lw=.25)
        for line in p.transpose(1, 0, 2):
            ax.plot(line[:, 0], line[:, 1], color='#426780', lw=.25)
        ax.set(xlim=xlim, ylim=ylim, title=title, xlabel='x/c', ylabel='y/c', aspect='equal')
    fig.tight_layout()
    fig.savefig(OUT / 'plots/v3_reference_sourcegrid_mesh.png', dpi=180)
    plt.close(fig)


def prepare():
    if (CASE / 'case.cfg').exists():
        raise RuntimeError('Never overwrite a prepared configuration.')
    helper = load_module('read_config_only', ROOT / 'work/blind_validation/solver_v2/solve.py')
    base = OUT / 'simulations/v2_r2_medium/case.cfg'
    d = helper.readcfg(base)
    original = d.copy()
    d['RESTART_SOL'] = 'NO'
    d['SOLUTION_FILENAME'] = 'solution'
    d['ITER'] = '8000'
    # All flow physics, reference values, gradients, flux, multigrid and
    # convergence settings are inherited unchanged, not chosen by Cp fit.
    (CASE / 'case.cfg').write_text('\n'.join(f'{k}= {v}' for k, v in d.items()) + '\n')
    manifest = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'case': NAME, 'base_config': str(base.relative_to(ROOT)), 'base_sha256': sha(base),
        'config_sha256': sha(CASE / 'case.cfg'), 'mesh_sha256': sha(CASE / 'mesh.su2'),
        'overrides': {k: {'base': original.get(k), 'new': v} for k, v in d.items() if original.get(k) != v},
        'contract_sha256': sha(ROOT / 'work/blind_validation/contract.json'),
        'physical_and_numerical_method_unchanged': True,
        'restart': 'uniform freestream; no interpolation from a different mesh',
        'role_preselected': 'diagnostic only; cannot replace preselected v2 fine validation',
        'time_budget_seconds': 1000, 'maximum_iterations': 8000,
    }
    (CASE / 'configuration_overrides.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


def run():
    if (CASE / 'run_status.json').exists() or (CASE / 'process.json').exists():
        raise RuntimeError('Never overwrite an executed attempt.')
    exe = Path(json.loads((ROOT / 'work/setup/su2_install.json').read_text())['executable'])
    env = os.environ.copy()
    env['OMP_NUM_THREADS'] = '4'
    env['OMP_WAIT_POLICY'] = 'PASSIVE'
    start = time.monotonic()
    epoch = time.time()
    with (CASE / 'solver.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([str(exe), 'case.cfg', '-t', '4'], cwd=CASE, env=env, stdout=log, stderr=subprocess.STDOUT)
        (CASE / 'process.json').write_text(json.dumps({'pid': proc.pid, 'start_epoch': epoch, 'budget_s': 1000}))
        try:
            code = proc.wait(timeout=1000)
            status = 'exited'
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            code = None
            status = 'timeout_partial_preserved'
    result = {'case': NAME, 'status': status, 'exit_code': code, 'wall_seconds': time.monotonic()-start,
              'threads': 4, 'config_sha256': sha(CASE / 'case.cfg'), 'mesh_sha256': sha(CASE / 'mesh.su2'),
              'executable_sha256': sha(exe), 'start_epoch': epoch, 'checkpoint_frequency': 200, 'overwrite': False}
    (CASE / 'run_status.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def post():
    # Reuse the audited matched-checkpoint selector without altering frozen code.
    helper = load_module('read_only_v2_postprocess', ROOT / 'work/blind_validation/solver_v2/postprocess.py')
    helper.process(NAME)


if __name__ == '__main__':
    {'mesh': mesh, 'prepare': prepare, 'run': run, 'post': post}[sys.argv[1]]()
