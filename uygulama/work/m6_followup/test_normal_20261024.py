"""A source-backed, one-policy M6 native test after closure of the RAE batch."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/projects/proje-e9319baef1'
CASE=OUT/'simulations/m6_jst_wallnormal_20261024_v3'
BASE=OUT/'simulations/m6_bounded_cfl_20261019_123823'
REP=OUT/'reports';DATA=OUT/'data/m6_jst_wallnormal_20261024_v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,a):p.write_text(json.dumps(a,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def cfg(p):
    d={}
    for line in p.read_text().splitlines():
        s=line.split('%',1)[0].strip()
        if '=' in s:k,v=s.split('=',1);d[k.strip()]=v.strip()
    return d
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def history(p):
    with p.open(newline='') as f:
        r=csv.DictReader(f);return [{k.strip().strip('"'):float(v) for k,v in row.items()} for row in r]
def prepare():
    dep=ROOT/'outputs/projects/proje-15cce2de02/reports/v3_test_batch_closed.json'
    closed=json.loads(dep.read_text());assert closed['bounded_test_and_review_completed']
    assert not CASE.exists(),'Never overwrite a trial';CASE.mkdir(parents=True);DATA.mkdir(parents=True)
    old=cfg(BASE/'case.cfg');assert old['CONV_NUM_METHOD_FLOW']=='ROE' and old['CFL_ADAPT']=='NO'
    assert sha(BASE/'mesh.su2')=='d20855c5a7b97cf6c32713f4f406b9b5b158b937a97ba583855dc58afe87e9f4'
    generated=OUT/'simulations/m6_wallnormal_mesh_20261024_v3'
    audit=json.loads((generated/'normal_mesh_audit.json').read_text());assert audit['primal_geometry_check_passed']
    shutil.copy2(generated/'mesh.su2',CASE/'mesh.su2');shutil.copy2(BASE/'restart_flow.dat',CASE/'seed.dat')
    new=dict(old);new.update(CONV_NUM_METHOD_FLOW='JST',MUSCL_FLOW='NO',ITER='3000',SOLUTION_FILENAME='seed',READ_BINARY_RESTART='YES',
        OUTPUT_WRT_FREQ='( 200, 200, 200, 200 )',WRT_RESTART_OVERWRITE='NO',WRT_SURFACE_OVERWRITE='NO',WRT_VOLUME_OVERWRITE='NO',
        VOLUME_OUTPUT='( COORDINATES, SOLUTION, PRIMITIVE, RESIDUAL )',HISTORY_OUTPUT='( ITER, RMS_RES, MAX_RES, AERO_COEFF, LINSOL )')
    physical=['SOLVER','KIND_TURB_MODEL','MACH_NUMBER','AOA','SIDESLIP_ANGLE','REYNOLDS_NUMBER','REYNOLDS_LENGTH',
              'FREESTREAM_TEMPERATURE','REF_AREA','REF_LENGTH','MARKER_HEATFLUX','MARKER_SYM','MARKER_FAR','VISCOSITY_MODEL']
    assert all(new[k]==old[k] for k in physical)
    (CASE/'case.cfg').write_text('\n'.join(f'{k}= {v}' for k,v in new.items())+'\n')
    original=json.loads((BASE/'diagnostic_contract.json').read_text())
    contract={'created_utc':now(),'project_id':'proje-e9319baef1','RAE_batch_closed':str(dep.relative_to(ROOT)),
        'RAE_closure_sha256':sha(dep),'source_case':str(BASE.relative_to(ROOT)),
        'source_checkpoint_note':'Previously completed M6 bounded1000 run, history terminal999; matching last field/restart preserved',
        'source_inputs_sha256':{str((BASE/f).relative_to(ROOT)):sha(BASE/f) for f in ['case.cfg','mesh.su2','restart_flow.dat','surface_flow.vtu','history.csv']},
        'conditions':original['physical_conditions'],'thresholds':original['acceptance_unchanged'],
        'physical_fields_unchanged':physical,'overrides':{k:{'old':old.get(k),'new':v} for k,v in new.items() if old.get(k)!=v},
        'single_numerical_policy':'Compared with m6_jst_control_20261024_v2: same JST config, same initial seed by point-ID; only interior prism normal coordinates differ. Reused field is an initial guess at shifted points and must reconverge.',
        'source_mesh_design':str(generated.relative_to(ROOT)),
        'source_mesh_design_sha256':{str((generated/f).relative_to(ROOT)):sha(generated/f) for f in ['normal_design_preseal.json','normal_mesh_audit.json','mesh.su2']},
        'source_mesh_code_sha256':sha(ROOT/'work/m6_followup/wallnormal_mesh.py'),
        'source_rationale':{'paper':'https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf','page':'25/33',
            'paper_sha256':sha(ROOT/'work/mesh_research/sources/SU2_AIAA2014_0243.pdf'),
            'claim':'Published M6 validation uses JST mean flow with first-order SA/SST transport. This trial keeps its own prior conditions and is not a full reproduction of that mesh/T/method.',
            'experiment':'https://www.grc.nasa.gov/www/wind/valid/m6wing/m6wing.html'},
        'scope':'Same source wall/farfield and connectivity, local wall-normal coordinate redistribution driven by own previous Yplus; not systematic mesh convergence or blind validation',
        'required_unclosed_gates':['systematic same-geometry three-grid family','regional boundary-layer sensitivity','controlled farfield sensitivity'],
        'minimum_qualification_passed':False}
    save(CASE/'contract.json',contract);save(REP/'m6_wallnormal_preseal_20261024_v3.json',contract)
    task=ROOT/'outputs/data/tasks/20261024-153804-27f425.json';a=json.loads(task.read_text());a.update(status='çalışıyor',phase='araç doğrulama',
        acceptance=['RAE test ve kanıt kaydı kapandıktan sonra başlat','Aynı kaynak M6 ağı/koşullarla native3B RANS ve eşlenmiş checkpoint','271 deney noktasının tamamı, y+, kuvvet/kalıntı ve açık kalite kapılarıyla rapor'])
    save(task,a);print(json.dumps({'case':str(CASE.relative_to(ROOT)),'prepared':True,'one_policy':contract['single_numerical_policy']},ensure_ascii=False))
def run():
    assert (CASE/'contract.json').exists() and not (CASE/'process.json').exists()
    contract=json.loads((CASE/'contract.json').read_text());dep=ROOT/contract['RAE_batch_closed'];assert sha(dep)==contract['RAE_closure_sha256']
    exe=Path(json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'])
    start=time.monotonic();stamp=now()
    with (CASE/'solver.log').open('w',encoding='utf-8') as log:
        p=subprocess.Popen([str(exe),'case.cfg','-t','4'],cwd=CASE,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),creationflags=subprocess.CREATE_NO_WINDOW)
        save(CASE/'process.json',{'pid':p.pid,'started_utc':stamp,'budget_seconds':1800,'threads':4})
        try:code=p.wait(timeout=1800);status='exited'
        except subprocess.TimeoutExpired:p.kill();p.wait();code=None;status='timeout_partial_preserved'
    record={'status':status,'exit_code':code,'started_utc':stamp,'ended_utc':now(),'seconds':time.monotonic()-start,
            'config_sha256':sha(CASE/'case.cfg'),'mesh_sha256':sha(CASE/'mesh.su2'),'executable_sha256':sha(exe),'threads':4}
    save(CASE/'run_status.json',record);print(json.dumps(record,indent=2))
def review():
    import numpy as np
    assert (CASE/'run_status.json').exists(),'Native attempt must have ended'
    frozen=REP/'m6_wallnormal_prediction_frozen_20261024_v3.json';assert not frozen.exists()
    contracts=json.loads((CASE/'contract.json').read_text());h=history(CASE/'history.csv')
    def suffix(prefix,ext):return {int(p.stem.rsplit('_',1)[-1]) for p in CASE.glob(prefix+'_*.'+ext) if p.stem.rsplit('_',1)[-1].isdigit()}
    available=suffix('flow','vtu')&suffix('surface_flow','vtu')&suffix('restart_flow','dat')
    iterations={int(a['Inner_Iter']):a for a in h};available&=iterations.keys();assert available,'No matched complete checkpoint'
    selected=max(available);row=iterations[selected];tail=[a for a in h if selected-99<=a['Inner_Iter']<=selected];assert len(tail)==100
    limits=contracts['thresholds'];metrics={'field_iteration':selected,'terminal_history_iteration':h[-1]['Inner_Iter'],'CL':row['CL'],'CD':row['CD'],
        'density_log10':row['rms[Rho]'],'turbulence_log10':row['rms[nu]'],'CL_last100_range':max(a['CL'] for a in tail)-min(a['CL'] for a in tail),
        'CD_last100_range':max(a['CD'] for a in tail)-min(a['CD'] for a in tail),
        'linear_iterations_max':max(a.get('Linear_Solver_Iterations',0) for a in tail),'linear_residual_log10_range':[min(a.get('LinSolRes',0) for a in tail),max(a.get('LinSolRes',0) for a in tail)]}
    metrics['iteration_checks']={'density':metrics['density_log10']<limits['density_log10_max'],'CL_window':metrics['CL_last100_range']<limits['CL_last100_range_max'],'CD_window':metrics['CD_last100_range']<limits['CD_last100_range_max']}
    save(CASE/'matched_checkpoint.json',metrics)
    files={str(p.relative_to(ROOT)):sha(p) for p in CASE.rglob('*') if p.is_file()}
    save(frozen,{'frozen_utc':now(),'files_sha256':files,'code_sha256':{str(Path(__file__).relative_to(ROOT)):sha(__file__)},
        'selection':metrics,'no_experimental_score_yet':True,'not_blind':True,'scope':contracts['scope']})
    assert all(sha(ROOT/p)==v for p,v in files.items())
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    compare=module('original_source_comparator',ROOT/'work/validation/compare_m6.py');groups,signs=compare.experimental()
    reviewdir=DATA/'prediction';reviewdir.mkdir();shutil.copy2(CASE/f'surface_flow_{selected:06d}.vtu',reviewdir/'surface_flow.vtu')
    assessment,curves,g=compare.comparison({'folder':str(reviewdir),'grid':'JST wall-normal redistributed mesh'},groups)
    alternate,_,_=compare.comparison({'folder':str(reviewdir),'grid':'JST wall-normal redistributed mesh'},groups,True)
    base_review=DATA/'baseline';base_review.mkdir();shutil.copy2(BASE/'surface_flow.vtu',base_review/'surface_flow.vtu')
    baseline,basecurves,_=compare.comparison({'folder':str(base_review),'grid':'Prior Roe CFL4 same source mesh'},groups)
    fig,axs=plt.subplots(2,4,figsize=(16,8));axs=axs.ravel()
    for i,((eta,xy,cp,exp),(_,bxy,bcp,_)) in enumerate(zip(curves,basecurves)):
        for values,pts,color,label in [(cp,xy,'#147d92','JST'),(bcp,bxy,'#b07b2c','Prior Roe')]:
            for upper,style in [(True,'-'),(False,'--')]:
                mask=pts[:,1]>=0 if upper else pts[:,1]<0;order=np.argsort(pts[mask,0]);axs[i].plot(pts[mask,0][order],values[mask][order],style,color=color,label=label if upper else None,lw=1)
        axs[i].errorbar(exp[:,1],exp[:,4],yerr=.02,fmt='o',ms=2,color='#172d42',lw=.5,label='ONERA experiment');axs[i].invert_yaxis();axs[i].grid(alpha=.2);axs[i].set(title=f'eta={eta:g}',xlabel='x/c',ylabel='Cp')
    axs[0].legend(fontsize=7);axs[7].axis('off');axs[7].text(0,.9,f'3D RANS/SA; M0.8395, alpha3.06\nSame258,969 cells; normal redistribution\nSource wall/farfield kept fixed\nMatched native field {selected}\nAll271 experimental points retained\nNO general M6 qualification',va='top')
    fig.tight_layout();fig.savefig(OUT/'plots/m6_wallnormal_Cp_20261024_v3.png',dpi=155);plt.close(fig)
    experiment_checks={f'section{a["section"]}{a["side"]}':a['Cp_RMSE']<limits['per_section_Cp_RMSE_max'] for a in assessment['sections']}
    result={'reviewed_utc':now(),'project_id':'proje-e9319baef1','native_run':json.loads((CASE/'run_status.json').read_text()),'matched':metrics,
        'experiment_points':sum(len(a) for a in groups),'sign_checks':signs,'Cp':assessment,'baseline_Cp':baseline,
        'alternate_eta0p96':alternate,'iteration_passed':all(metrics['iteration_checks'].values()),'wall_passed':assessment['yplus_max']<limits['strict_max_yplus'],
        'experimental_checks':experiment_checks,'experiment_passed':all(experiment_checks.values()),'minimum_qualification_passed':False,
        'missing_full_qualification':contracts['required_unclosed_gates'],'frozen_prediction_sha256':sha(frozen),'scope':contracts['scope'],
        'force_reference':'Same half-wing projected reference area0.7613155538973486m2, cref0.64607m; no force rescaling to match experiment',
        'geometry_note':'Published rounded-tip source surface extends past nominal NASA1.1963m semispan; unchanged source approximation. Section6 main eta.95 and alternative.96 both retained.'}
    save(REP/'m6_wallnormal_results_20261024_v3.json',result)
    print(json.dumps({k:result[k] for k in ['matched','iteration_passed','wall_passed','experiment_passed','minimum_qualification_passed']},indent=2))
if __name__=='__main__':{'prepare':prepare,'run':run,'review':review}[sys.argv[1]]()
