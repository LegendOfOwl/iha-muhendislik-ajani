"""Archive the installed SU2 tag's implementation used in the convergence diagnosis."""
from prepare import ROOT, BASE, read, save, sha, now
from urllib.request import urlopen

base = BASE / 'convergence_sources'
base.mkdir(exist_ok=True)
prefix = 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/'
urls = {
    'config_template.cfg': prefix + 'config_template.cfg',
    'CEulerSolver.cpp': prefix + 'SU2_CFD/src/solvers/CEulerSolver.cpp',
    'CFVMFlowSolverBase.inl': prefix + 'SU2_CFD/include/solvers/CFVMFlowSolverBase.inl',
    'CScalarSolver.inl': prefix + 'SU2_CFD/include/solvers/CScalarSolver.inl',
    'CTurbSASolver.cpp': prefix + 'SU2_CFD/src/solvers/CTurbSASolver.cpp',
    'CConfig.cpp': prefix + 'Common/src/CConfig.cpp',
    'CIntegration.cpp': prefix + 'SU2_CFD/src/integration/CIntegration.cpp',
    'CSingleGridIntegration.cpp': prefix + 'SU2_CFD/src/integration/CSingleGridIntegration.cpp',
    'CMultiGridIntegration.cpp': prefix + 'SU2_CFD/src/integration/CMultiGridIntegration.cpp',
    'CFVMFlowSolverBase.hpp': prefix + 'SU2_CFD/include/solvers/CFVMFlowSolverBase.hpp',
    'CNewtonIntegration.cpp': prefix + 'SU2_CFD/src/integration/CNewtonIntegration.cpp',
    'CNewtonIntegration.hpp': prefix + 'SU2_CFD/include/integration/CNewtonIntegration.hpp',
    'turb_ONERAM6_nk.cfg': prefix + 'TestCases/rans/oneram6/turb_ONERAM6_nk.cfg',
    'arxiv1805.03756v1.html': 'https://arxiv.org/html/1805.03756v1',
    'linear_solvers.html': 'https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/',
}
manifest = base / 'manifest.json'
rows = read(manifest) if manifest.exists() else []
for name, url in urls.items():
    p = base / name
    existing = next((r for r in rows if r['url'] == url), None)
    if existing:
        assert sha(p) == existing['sha256']
        continue
    assert not p.exists(), 'Uncatalogued source must be investigated before overwrite'
    data = urlopen(url, timeout=40).read()
    p.write_bytes(data)
    rows.append({'path': str(p.relative_to(ROOT)), 'url': url, 'downloaded_utc': now(),
                 'bytes': len(data), 'sha256': sha(p)})
    save(manifest, rows)
    print(name, len(data), flush=True)
