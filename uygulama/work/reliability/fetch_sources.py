"""Preserve the primary-source evidence used in this development iteration."""
from pathlib import Path
import hashlib
import json
import urllib.request
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent / 'sources'
SOURCES = [
    ('su2_v850_config.cfg', 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/config_template.cfg', 'Tagged v8.5.0 config: linear controls, CFL feedback, verification and AD options.'),
    ('su2_linear_solvers.html', 'https://su2code.github.io/docs_v7/Linear-Solvers-and-Preconditioners/', 'Linear accuracy must be balanced with nonlinear convergence and cost; central schemes may need more inner steps.'),
    ('su2_v850_CFlowCompOutput.cpp', 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/output/CFlowCompOutput.cpp', 'LinSolRes is log10 of solver-reported relative linear residual; history RMS and volume residual have distinct semantics.'),
    ('su2_v850_CSysSolve.cpp', 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/Common/src/linear_algebra/CSysSolve.cpp', 'FGMRES relative residual beta/norm0 and iteration-cap mechanics.'),
    ('nasa_iterative.html', 'https://www.grc.nasa.gov/www/wind/valid/tutorial/iterconv.html', 'Monitor both equation residuals and engineering outputs.'),
    ('nasa_adaptation_M6_20200003084.pdf', 'https://ntrs.nasa.gov/api/citations/20200003084/downloads/20200003084.pdf', 'Balan et al. 2020: Mach-Hessian anisotropic adaptation; this prototype is only an indicator, not a reproduction.'),
    ('refine_README.md', 'https://raw.githubusercontent.com/nasa/refine/master/README.md', 'Production mesh adaptation dependencies and geometry requirements; not installed by this iteration.'),
]

if __name__ == '__main__':
    BASE.mkdir(exist_ok=True)
    manifest = []
    for name, url, use in SOURCES:
        p = BASE / name
        if p.exists():
            raise FileExistsError(p)
        req = urllib.request.Request(url, headers={'User-Agent':'Engineering-source-audit/1.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        p.write_bytes(data)
        manifest.append({'file':name,'url':url,'downloaded_utc':datetime.now(timezone.utc).isoformat(),
                         'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'use':use})
    (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'sources':len(manifest),'total_bytes':sum(x['bytes'] for x in manifest)}))
