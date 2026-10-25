"""Archive the primary sources opened for this research; never run a CFD solver."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / 'sources'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = [
    ('S01', 'SU2 AIAA 2014 V&V', 'https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf', 'su2_2014.pdf', 'work/mesh_research/sources/SU2_AIAA2014_0243.pdf', 'published conference paper; M6 and RAE sections read'),
    ('S02', 'TMR M6 numerical validation', 'https://tmbwg.github.io/turbmodels/onerawingnumerics_val.html', 'tmr_m6.html', None, 'official current case page; geometry and section correction read'),
    ('S03', 'TMR M6 grid generator', 'https://tmbwg.github.io/turbmodels/onerawingnumerics_grids.html', 'tmr_grids.html', None, 'official grid page read'),
    ('S04', 'TMR ONERA M6 case specification', 'https://tmbwg.github.io/turbmodels/Onerawingnumerics_val/ONERA_M6_Test_Case_TMR.pdf', 'tmr_m6_spec.pdf', None, 'official 9-page specification; geometry read'),
    ('S05', 'Numerical Aspects of Gradient Reconstruction Schemes Applied to Complex Geometries', 'https://arxiv.org/pdf/2601.15522v1', 'arxiv_2601_15522v1.pdf', None, 'arXiv preprint v1; full PDF numerical methods and M6 read'),
    ('S06', 'NASA LAVA M6 tutorial', 'https://nas.nasa.gov/LAVA/unst_docs/tutorials/onera_M6/onera_M6/', 'lava_m6.html', None, 'official tutorial read'),
    ('S07', 'SU2 v8.5.0 driver', 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/drivers/CDriver.cpp', 'su2_v850_CDriver.cpp', None, 'tagged source; finest interior corrected gradient selection read'),
    ('S08', 'SU2 v8.5.0 viscous gradient operator', 'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/numerics/flow/flow_diffusion.cpp', 'su2_v850_flow_diffusion.cpp', None, 'tagged source; CorrectGradient and call read; binary branch not instrumented'),
    ('S09', 'Cross-code anisotropic adaptation on M6', 'https://ntrs.nasa.gov/api/citations/20200003084/downloads/20200003084.pdf', 'nasa_20200003084.pdf', 'work/reliability/sources/nasa_adaptation_M6_20200003084.pdf', 'NASA author paper; comparison and method read'),
    ('S10', 'DLR geometry-adapted refinement with cell stacks', 'https://elib.dlr.de/216488/1/AMR25_AlgoGeoAdaptedMeshRef_2025-09-02_pub.pdf', 'dlr_amr25.pdf', None, 'public 2025 research presentation; M6 failure slides read'),
    ('S11', 'Foam-Agent', 'https://arxiv.org/html/2509.18178v1', 'foam_agent_2509_18178v1.html', None, 'arXiv preprint; benchmark method and tables read'),
    ('S12', 'Preliminary Assessment of Coding Agents for CFD', 'https://arxiv.org/html/2602.11689v1', 'coding_agents_2602_11689v1.html', None, 'arXiv preprint; benchmark scope, success criterion and exception read'),
    ('S13', 'CFD Forge', 'https://arxiv.org/html/2610.14104v1', 'cfd_forge_2610_14104v1.html', None, 'arXiv preprint; contracts, fault benchmark and limitations read'),
    ('S14', 'AI CFD Scientist', 'https://arxiv.org/html/2605.06607v1', 'cfd_scientist_2605_06607v1.html', None, 'arXiv preprint; tasks, mesh screen and limitations read'),
    ('S15', 'NASA RAE2822 Study 1', 'https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf01/raetaf01.html', 'nasa_rae_study1.html', 'work/mesh_research/sources/NASA_RAE_Study1.html', 'official study; grid and setup read'),
    ('S16', 'NASA RAE2822 Study 4', 'https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html', 'nasa_rae_study4.html', 'work/mesh_research/sources/NASA_RAE_Study4.html', 'official study; corrected conditions and Cp read'),
    ('S17', 'TMR wing Fortran generator release', 'https://www.nasa.gov/wp-content/uploads/2026/04/wing-release-072319.zip', 'wing-release-072319.zip', None, 'download and inspect only; not compiled or used for CFD'),
    ('S18', 'TMR structured grid input', 'https://tmbwg.github.io/turbmodels/Onerawingnumerics_grids/input.nml_wing_strct_stt', 'input.nml_wing_strct_stt', None, 'generator input inspection only'),
    ('S19', 'TMR structured grid input with lower LE/TE stretching', 'https://tmbwg.github.io/turbmodels/Onerawingnumerics_grids/input.nml_wing_strct_2_stt', 'input.nml_wing_strct_2_stt', None, 'generator input inspection only'),
    ('S20', 'NASA spatial grid convergence guidance', 'https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html', 'nasa_grid_convergence.html', None, 'official verification guidance read'),
    ('S21', 'TMR flat plate model verification', 'https://tmbwg.github.io/turbmodels/flatplate.html', 'tmr_flatplate.html', None, 'official model-verification scope and grid family read'),
]


def capture(row):
    sid, title, url, name, reuse, review = row
    record = dict(id=sid, title=title, url=url, review=review)
    target = OUT / name
    try:
        if target.exists():
            raw = target.read_bytes()
            record['action'] = 'existing research archive rehashed'
        elif reuse and (ROOT / reuse).exists():
            raw = (ROOT / reuse).read_bytes()
            target.write_bytes(raw)
            record.update(action='copied prior preserved download; no new remote fetch', reused_from=reuse)
        else:
            req = urllib.request.Request(url, headers={'User-Agent': 'CFD-literature-research/1.0'})
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read(22_000_001)
                record['resolved_url'] = response.url
                record['content_type'] = response.headers.get('Content-Type')
            if len(raw) > 22_000_000:
                raise ValueError('research source exceeded 22 MB cap')
            if name.endswith('.pdf') and not raw.startswith(b'%PDF'):
                raise ValueError('expected PDF signature absent')
            if name.endswith('.zip') and not raw.startswith(b'PK'):
                raise ValueError('expected ZIP signature absent')
            target.write_bytes(raw)
            record['action'] = 'downloaded'
        record.update(status='archived', path=target.relative_to(ROOT).as_posix(), bytes=len(raw),
                      sha256=hashlib.sha256(raw).hexdigest(), checked_utc=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        record.update(status='archive_failed', error=str(exc))
    return record


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(capture, SOURCES))
    (OUT / 'manifest.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: r.get(k) for k in ('id','status','bytes','error')} for r in results], ensure_ascii=False))
