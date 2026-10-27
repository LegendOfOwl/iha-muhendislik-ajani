"""Independent checks on the exported native-membership table, without new CFD."""
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'work/flatplate_20261025'))
from prepare import read, save, sha, now


def measure(colors, rho_share, nu_share):
    arrays = [np.asarray(v, dtype=float) for v in (colors, rho_share, nu_share)]
    color, rho, nu = arrays
    if any(a.ndim != 1 or a.shape != color.shape or a.size == 0 for a in arrays):
        raise ValueError('Equal, nonempty one-dimensional arrays required')
    if not all(np.isfinite(a).all() for a in arrays):
        raise ValueError('Nonfinite membership or residual share')
    if (color < 0).any() or (color != np.round(color)).any():
        raise ValueError('Native graph colors must be nonnegative integers')
    for share in (rho, nu):
        if (share < 0).any() or not np.isclose(share.sum(), 1.0, rtol=0, atol=1e-12):
            raise ValueError('Residual squared shares must be nonnegative and normalized')
    inside = color > 0
    if not inside.any() or inside.all():
        raise ValueError('Both covered and uncovered nodes required for this comparison')
    return {
        'nodes': int(color.size), 'linelet_nodes': int(inside.sum()),
        'covered_Rho_squared_share': float(rho[inside].sum()),
        'covered_nu_squared_share': float(nu[inside].sum()),
    }


def audit():
    path = ROOT / 'outputs/reports/linelet_coverage_20261027.json'
    source = read(path)
    csv = ROOT / source['data_csv']
    assert sha(csv) == source['data_csv_sha256']
    data = np.genfromtxt(csv, delimiter=',', names=True)
    n = len(data)
    assert np.array_equal(data['mesh_node'], np.arange(n))
    assert np.isfinite(data['x_m']).all() and np.isfinite(data['y_m']).all()
    assert np.array_equal(data['native_linelet_member'], (data['linelet_graph_color'] > 0).astype(int))
    result = measure(data['linelet_graph_color'], data['Rho_squared_share'], data['nu_squared_share'])
    for key, value in result.items():
        assert abs(source[key] - value) <= 1e-14, key
    save(ROOT / 'outputs/reports/linelet_coverage_audit_20261027.json', {
        'checked_utc': now(), 'table_sha256': sha(csv), 'source_report_sha256': sha(path),
        'measurements': result, 'passed': True, 'physical_qualification_passed': False,
        'scope': 'Independent table/sign/normalization check; native field and original analysis unchanged',
    })
    print(result)


if __name__ == '__main__':
    audit()
