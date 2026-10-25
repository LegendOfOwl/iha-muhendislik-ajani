"""Read-only audit for a literature comparison. Does not launch or modify CFD."""
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
PROJECT = ROOT / 'outputs/projects/proje-e9319baef1'
REPORTS = ROOT / 'outputs/reports'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def csv_rows(p):
    with p.open(newline='', encoding='utf-8-sig') as stream:
        return [{k.strip().strip('"'): float(v) for k,v in row.items()} for row in csv.DictReader(stream, skipinitialspace=True)]


def main():
    # Preserve the archive failures as an explicit limitation; no insecure TLS fallback.
    manifest = read(BASE / 'sources/manifest.json')
    from capture_sources import SOURCES
    by_id = {r['id']:r for r in manifest}
    for sid,title,url,name,reuse,review in SOURCES:
        p = BASE / 'sources' / name
        r = by_id.setdefault(sid, dict(id=sid,title=title,url=url,review=review))
        if p.exists():
            if name.endswith('.pdf'): assert p.read_bytes().startswith(b'%PDF')
            r.update(status='archived', path=p.relative_to(ROOT).as_posix(), sha256=sha(p), bytes=p.stat().st_size,
                     archive_checked_utc=datetime.now(timezone.utc).isoformat())
            if r.pop('error', None): r['archive_recovery']='Windows HTTPS trust store used; certificate checking retained'
            if reuse: r['reused_from']=reuse
        else:
            r['read_status']='Opened and read via web tool; direct local download unavailable'
    save(BASE/'sources/manifest.json', list(by_id.values()))
    # Read selected archive members; do not execute, compile, or extract arbitrary paths.
    inspection = BASE / 'generator_inspection'
    inspection.mkdir(exist_ok=True)
    with ZipFile(BASE/'sources/wing-release-072319.zip') as archive:
        listing = [{'name':x.filename,'bytes':x.file_size} for x in archive.infolist()]
        for name in ['readme_release.txt','hcf_wing_v5p0.f90','hcf_coarsening_v3p9.f90','om6_wing_section_sharp.dat']:
            (inspection/name).write_bytes(archive.read('wing_release_072319/'+name))
    save(inspection/'archive_listing.json', listing)
    assert b'generate_su2grid_file' in (inspection/'hcf_wing_v5p0.f90').read_bytes()
    source_driver=BASE/'sources/su2_v850_CDriver.cpp'
    source_diffusion=BASE/'sources/su2_v850_flow_diffusion.cpp'
    dl=source_driver.read_text().splitlines(); vl=source_diffusion.read_text().splitlines()
    selected=[i+1 for i,x in enumerate(dl) if 'numerics[MESH_0][FLOW_SOL][visc_term] = new CAvgGrad_Flow(nDim, nVar_Flow, true' in x]
    calls=[i+1 for i,x in enumerate(vl) if 'CorrectGradient(Mean_GradPrimVar' in x]
    assert len(selected)==1 and calls

    review_path=PROJECT/'reports/m6_cfl_feedback_20261025.json'
    review=read(review_path)
    original=read(PROJECT/'reports/m6_rans_results.json')
    results={}; evidence={}
    for name in ['fixed','adaptive']:
        run=PROJECT/'simulations/m6_cfl_feedback_20261025'/name
        seal=read(run/'prediction_frozen.json')
        problems=[]
        for rel,expected in seal['files_sha256'].items():
            if sha(ROOT/rel)!=expected: problems.append(rel)
        assert not problems, problems
        evidence[(run/'prediction_frozen.json').relative_to(ROOT).as_posix()]=sha(run/'prediction_frozen.json')
        hist=csv_rows(run/'history.csv')
        assert hist[-1]['Inner_Iter']==599
        for key in ['CL','CD','rms[Rho]']:
            assert hist[-1][key]==review['results'][name]['matched'][key]
        scores={}
        for suffix,report_key in [('', 'Cp'),('_tec_eta','alternate_eta0p96')]:
            table=PROJECT/f'data/m6_cfl_feedback_20261025/{name}/experimental_comparison{suffix}.csv'
            rows=csv_rows(table)
            assert len(rows)==271
            score=math.sqrt(sum(x['error']**2 for x in rows)/len(rows))
            assert abs(score-review['results'][name][report_key]['all_point_Cp_RMSE'])<1e-12
            scores[report_key]={'points':len(rows),'Cp_RMSE_recomputed':score,'csv_sha256':sha(table)}
            evidence[table.relative_to(ROOT).as_posix()]=sha(table)
        results[name]={
            'matched':review['results'][name]['matched'], 'scores':scores,
            'max_yplus':review['results'][name]['Cp']['yplus_max'],
            'all_surface_points_below_yplus_1':review['results'][name]['Cp']['fraction_yplus_below1']==1,
            'verified_frozen_files':len(seal['files_sha256']), 'minimum_qualification_passed':False,
        }
    cfgpath=PROJECT/'simulations/m6_cfl_feedback_20261025/adaptive/case.cfg'
    config={}
    for line in cfgpath.read_text().splitlines():
        line=line.split('%',1)[0]
        if '=' in line:
            key,value=line.split('=',1);config[key.strip()]=value.strip()
    mesh=original['results'][1]['mesh']
    re_per_m=float(config['REYNOLDS_NUMBER'])/float(config['REYNOLDS_LENGTH'])
    # Reynolds reference-length conversion, not a change to physical conditions.
    physical={'Re_per_m':re_per_m, 'Re_on_measured_root_chord':re_per_m*mesh['root_chord_m'],
              'local_temperature_K':float(config['FREESTREAM_TEMPERATURE']),
              'SU2_2014_temperature_K':273.15, 'current_TMR_temperature_K':300.0,
              'warning':'Different temperatures alone do not prove error cause; match complete nondimensional problem and viscosity law.'}
    raepath=ROOT/'outputs/projects/proje-15cce2de02/reports/review_v2_qualification.json'
    rae=read(raepath)
    for p in [review_path,raepath,cfgpath,ROOT/'work/setup/su2_install.json',ROOT/'work/reliability/protocol_v1.json']:
        evidence[p.relative_to(ROOT).as_posix()]=sha(p)
    sys.path.insert(0,str(ROOT/'work/agent'))
    from learning import instruction_snapshot
    facts={'created_utc':datetime.now(timezone.utc).isoformat(), 'scope':'Literature research and read-only evidence recomputation; no new native CFD',
           'project_id':'proje-e9319baef1', 'local_mesh':mesh, 'local_config':config, 'M6_current_results':results,
           'Reynolds_reference_conversion':physical,
           'source_code_check':{'driver_line':selected[0], 'gradient_correction_call_lines':calls,
                                'driver_sha256':sha(source_driver),'diffusion_sha256':sha(source_diffusion),
                                'conclusion':'Tagged v8.5.0 selects corrected finest-grid ideal-gas interior viscous gradient; runtime binary not instrumented. GREEN_GAUSS does not establish use of paper L00.'},
           'RAE_v2':{'minimum_qualification_passed':rae['minimum_qualification_passed'], 'grid_sensitivity':rae['grid_sensitivity'],
                     'farfield_sensitivity':rae['farfield_sensitivity'], 'critical_regional_mesh_issue_open':rae['critical_regional_mesh_issue_open']},
           'generator':{'downloaded_bytes':(BASE/'sources/wing-release-072319.zip').stat().st_size,
                        'source_and_inputs_inspected':True,'compiled':False,'mesh_generated':False,
                        'available_compilers_on_PATH':{x:shutil.which(x) for x in ['gfortran','ifort','g95']},
                        'scope':'Sharp trailing edge, normalized root chord, new benchmark definition; not the old source mesh family.'},
           'agent_instruction_snapshot':instruction_snapshot(ROOT), 'applied_lesson_ids':['L04','L05','L06','L07','L08','L09','R03'],
           'evidence_sha256':evidence, 'minimum_CFD_qualification_passed':False}
    save(REPORTS/'cfd_literatur_yerel_kiyas_20261025.json', facts)

    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    groups=review['results']['adaptive']['alternate_eta0p96']['sections']
    fig,ax=plt.subplots(figsize=(11,4.8))
    labels=[f"{r['eta']:g} / {'U' if r['side']=='u' else 'L'}" for r in groups]
    vals=[r['Cp_RMSE'] for r in groups]
    ax.bar(labels,vals,color=['#277d76' if x<.08 else '#bf6847' for x in vals])
    ax.axhline(.08,color='#414b60',ls='--',label='Existing per-section screen: 0.08')
    ax.set(xlabel='Span station eta / upper-lower surface', ylabel='Cp RMSE (dimensionless)',
           title='M6: existing adaptive run; source-corrected eta=0.96; all 271 points retained')
    ax.tick_params(axis='x',rotation=45);ax.legend();ax.grid(axis='y',alpha=.15)
    fig.tight_layout()
    fig.savefig(ROOT/'outputs/plots/m6_literatur_kesit_hatalari_20261025.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'native_CFD_runs':0,'archived_sources':sum(x['status']=='archived' for x in by_id.values()),
                      'source_records':len(by_id),'M6':results,'source_driver_line':selected[0], 'Re_root':physical['Re_on_measured_root_chord']},ensure_ascii=False))


if __name__=='__main__': main()
