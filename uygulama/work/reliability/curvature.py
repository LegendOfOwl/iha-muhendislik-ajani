"""Solution-only quadratic curvature indicator. NOT an adjoint/error bound."""
import os
for _key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[_key] = '1'
from pathlib import Path
import argparse
import csv
import json
import numpy as np
from scipy.spatial import cKDTree


def reconstruct(cloud, scalar, centers, neighbors=40):
    """Whitened quadratic LS. Masks degenerate/ill-conditioned stencils."""
    cloud, scalar, centers = [np.asarray(a, dtype=float) for a in [cloud, scalar, centers]]
    if cloud.ndim != 2 or cloud.shape[1] != 3 or scalar.shape != (len(cloud),):
        raise ValueError('Need Nx3 cloud and N scalar values')
    if not all(np.isfinite(a).all() for a in [cloud, scalar, centers]):
        raise ValueError('Non-finite input')
    if len(cloud) < neighbors or neighbors < 12:
        raise ValueError('Insufficient stencil')
    _, ids = cKDTree(cloud).query(centers, k=neighbors, workers=1)
    delta = cloud[ids] - centers[:, None, :]
    _, s, vh = np.linalg.svd(delta, full_matrices=False)
    valid = (s[:, -1] > 1e-8 * s[:, 0]) & (s[:, 0] > 0)
    safe_s = np.where(s > 0, s, 1)
    transform = vh.transpose(0, 2, 1) * (np.sqrt(neighbors) / safe_s)[:, None, :]
    u = np.einsum('nki,nij->nkj', delta, transform)
    x, y, z = [u[:, :, i] for i in range(3)]
    a = np.stack([np.ones_like(x), x, y, z, .5*x*x, x*y, x*z, .5*y*y, y*z, .5*z*z], axis=-1)
    left, singular, right = np.linalg.svd(a, full_matrices=False)
    condition = np.divide(singular[:, 0], singular[:, -1], out=np.full(len(singular), np.inf),
                          where=singular[:, -1] > np.finfo(float).eps * singular[:, 0])
    valid &= condition < 1e6
    f = scalar[ids]
    offset = f.mean(axis=1)
    target = f - offset[:, None]
    inv = np.divide(1., singular, out=np.zeros_like(singular), where=singular > 1e-12*singular[:, :1])
    coeff = np.einsum('nji,nj->ni', right, inv * np.einsum('nki,nk->ni', left, target))
    predicted = np.einsum('nki,ni->nk', a, coeff)
    rmse = np.sqrt(np.mean((predicted - target)**2, axis=1))
    relative_rmse = rmse / np.maximum(np.ptp(f, axis=1), 1e-12)
    h = np.empty((len(centers), 3, 3))
    h[:, 0, 0], h[:, 1, 1], h[:, 2, 2] = coeff[:, 4], coeff[:, 7], coeff[:, 9]
    h[:, 0, 1] = h[:, 1, 0] = coeff[:, 5]
    h[:, 0, 2] = h[:, 2, 0] = coeff[:, 6]
    h[:, 1, 2] = h[:, 2, 1] = coeff[:, 8]
    hworld = transform @ h @ transform.transpose(0, 2, 1)
    valid &= np.isfinite(hworld).all(axis=(1, 2))
    hworld[~valid] = np.nan
    return hworld, valid, condition, relative_rmse


def indicator(hessians, vertices):
    """Absolute-Hessian barycentric quadratic indicator, dimensionless for Mach."""
    eigenvalues, vectors = np.linalg.eigh(hessians)
    absolute = (vectors * np.abs(eigenvalues)[:, None, :]) @ vectors.transpose(0, 2, 1)
    delta = vertices - vertices.mean(axis=1)[:, None, :]
    value = .5 * np.einsum('nki,nij,nkj->nk', delta, absolute, delta).mean(axis=1)
    largest = np.argmax(np.abs(eigenvalues), axis=1)
    direction = vectors[np.arange(len(vectors)), :, largest]
    return value, direction


def main():
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
    from linear_pair import ROOT, RUN, PROJECT, read, save, sha, now
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['lin10'], default='lin10')
    args = parser.parse_args()
    folder = RUN / args.case
    frozen = read(folder / 'prediction_frozen.json')
    iteration = frozen['matched']['field_iteration']
    path = folder / f'flow_{iteration:06d}.vtu'
    assert sha(path) == frozen['files_sha256'][str(path.relative_to(ROOT))]
    out = PROJECT / 'data/reliability_20261024'
    out.mkdir(parents=True, exist_ok=True)
    spec = out / 'indicator_spec.json'
    assert not spec.exists(), 'Do not overwrite a prior representation/indicator'
    save(spec, {'created_utc': now(), 'source_field': str(path.relative_to(ROOT)), 'source_sha256': sha(path),
                'preselected_role': 'lin10 regardless of experimental agreement',
                'formula': '0.5 mean_i[(v_i-centroid)^T |H_Mach| (v_i-centroid)]',
                'fit': '40 nearest volume vertices; whitened quadratic LS, geometry ratio>1e-8, design condition<1e6',
                'selection': '99th percentile within tetrahedra at nondimensional nearest-wall-vertex distance<2 chords; ties retained',
                'no_experimental_targets': True, 'not_error_bound': True, 'not_adjoint': True,
                'normal_prism_layers_excluded': True,
                'limitation': 'Nearest-wall-vertex distance is only a region filter; shocks are nonsmooth and quadratic assumptions fail. No boundary-layer or wall-distance certification.',
                'code_sha256': sha(__file__)})
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path)); reader.Update(); grid = reader.GetOutput()
    points = vtk_to_numpy(grid.GetPoints().GetData()).astype(float)
    mach = vtk_to_numpy(grid.GetPointData().GetArray('Mach')).astype(float)
    conn = vtk_to_numpy(grid.GetCells().GetConnectivityArray())
    offsets = vtk_to_numpy(grid.GetCells().GetOffsetsArray())
    types = vtk_to_numpy(grid.GetCellTypes())
    tetra_ids = np.flatnonzero(types == vtk.VTK_TETRA)
    ids = conn[offsets[tetra_ids, None] + np.arange(4)[None, :]]
    vertices = points[ids]; centers = vertices.mean(axis=1)
    surface = folder / f'surface_flow_{iteration:06d}.vtu'
    sr = vtk.vtkXMLUnstructuredGridReader();sr.SetFileName(str(surface));sr.Update()
    wallpoints = vtk_to_numpy(sr.GetOutput().GetPoints().GetData()).astype(float)
    distance, _ = cKDTree(wallpoints).query(centers)
    region = distance < 2 * .64607
    candidate = np.flatnonzero(region)
    values = np.full(len(tetra_ids), np.nan)
    directions = np.full((len(tetra_ids), 3), np.nan)
    valid = np.zeros(len(tetra_ids), dtype=bool)
    fit_error = np.full(len(tetra_ids), np.nan)
    conditions = np.full(len(tetra_ids), np.nan)
    for start in range(0, len(candidate), 512):
        take = candidate[start:start+512]
        h, mask, cond, err = reconstruct(points, mach, centers[take])
        conditions[take], fit_error[take] = cond, err
        valid[take] = mask
        good = take[mask]
        if len(good):
            values[good], directions[good] = indicator(h[mask], vertices[good])
    good = np.flatnonzero(valid)
    threshold = float(np.quantile(values[good], .99))
    selected = valid & (values >= threshold)
    jump = np.ptp(mach[ids], axis=1)
    csvpath = out / 'curvature_cells.csv'
    with csvpath.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['cell_id','x_m','y_m','z_m','indicator','Mach_jump','fit_valid','fit_relative_RMSE','fit_condition','dir_x','dir_y','dir_z','selected'])
        for i in candidate:
            def nullable(x):return float(x) if np.isfinite(x) else ''
            writer.writerow([int(tetra_ids[i]), *centers[i], nullable(values[i]), jump[i], int(valid[i]),
                             nullable(fit_error[i]), nullable(conditions[i]), *[nullable(x) for x in directions[i]], int(selected[i])])
    for name, subset in [('MachCurvatureIndicator', values), ('FitValid', valid.astype(float)), ('RefinementPriority', selected.astype(float))]:
        allvalues = np.full(grid.GetNumberOfCells(), np.nan)
        allvalues[tetra_ids] = subset
        array = numpy_to_vtk(allvalues, deep=True); array.SetName(name); grid.GetCellData().AddArray(array)
    writer = vtk.vtkXMLUnstructuredGridWriter(); writer.SetFileName(str(out/'curvature_view.vtu'));writer.SetInputData(grid);assert writer.Write()
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12,5))
    # Diagnostic projection; depth overlap is explicit, no synthetic flow reconstruction.
    show = good[np.argsort(values[good])]
    sc = axes[0].scatter(centers[show,0], centers[show,1], c=np.log10(np.maximum(values[show],1e-12)), s=2, cmap='viridis', rasterized=True)
    axes[0].scatter(wallpoints[:,0],wallpoints[:,1],s=.15,c='#666',alpha=.15)
    axes[0].set(title='Volume tetrahedra: x-y projection',xlabel='x [m]',ylabel='y [m]')
    fig.colorbar(sc,ax=axes[0],label='log10 curvature indicator [Mach]')
    axes[1].scatter(centers[selected,0],centers[selected,1],c=fit_error[selected],s=12,cmap='magma')
    axes[1].set(title='Top 1%: locations for inspection',xlabel='x [m]',ylabel='y [m]')
    for ax in axes:ax.set_aspect('equal');ax.grid(alpha=.2)
    fig.suptitle('Solution-only diagnostic; excludes prism BL; NOT a CFD error bound')
    fig.tight_layout(); plot=PROJECT/'plots/m6_curvature_20261024.png';fig.savefig(plot,dpi=150);plt.close(fig)
    report = {'created_utc':now(),'source_field':str(path.relative_to(ROOT)),'source_sha256':sha(path),
              'preselected_case':args.case,'field_iteration':iteration,'tetrahedra_total':len(tetra_ids),'region_candidates':len(candidate),
              'valid_fits':int(valid.sum()),'invalid_fits':int((region & ~valid).sum()),'selected_cells':int(selected.sum()),
              'indicator_quantile99':threshold,'selected_bbox_m':{'min':centers[selected].min(axis=0).tolist(),'max':centers[selected].max(axis=0).tolist()},
              'selected_fit_relative_rmse':{'median':float(np.median(fit_error[selected])),'max':float(np.max(fit_error[selected]))},
              'iterative_prerequisite_passed':all(frozen['matched']['iteration_checks'].values()),
              'permission_to_claim_error_bound':False,'minimum_qualification_passed':False,
              'artifacts':{str(p.relative_to(ROOT)):sha(p) for p in [spec,csvpath,out/'curvature_view.vtu',plot]},
              'scope':'A location/direction indicator on a nonconverged field. Full anisotropic remeshing, adjoint weighting and BL coverage are not implemented.'}
    save(PROJECT/'reports/m6_curvature_20261024.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
