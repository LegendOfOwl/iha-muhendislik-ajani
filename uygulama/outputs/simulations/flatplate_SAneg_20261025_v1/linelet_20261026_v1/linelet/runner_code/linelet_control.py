"""One source-justified normal-line control after the verified RHS observation."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder,evaluate
from scaled_restart import dimensional_matched
from linear_work_control import work
from inner_cap_control import decide
from run import history
import os,sys,shutil,re,urllib.request

PAIR=CASE/'linelet_20261026_v1';SOURCES=ROOT/'work/flatplate_20261026/linelet_sources'
BASELINE=CASE/'inner_cap_20261026_v1/cap40'
PATHS=['Common/include/geometry/CGeometry.hpp','Common/src/geometry/CGeometry.cpp',
 'Common/include/linear_algebra/CPreconditioner.hpp','Common/src/linear_algebra/CSysMatrix.cpp']

def sources():
    assert not SOURCES.exists();SOURCES.mkdir(parents=True);manifest=[]
    for path in PATHS:
        url='https://raw.githubusercontent.com/su2code/SU2/v8.5.0/'+path
        with urllib.request.urlopen(url,timeout=40) as r:data=r.read()
        p=SOURCES/path.rsplit('/',1)[-1];p.write_bytes(data)
        manifest.append({'url':url,'fetched_utc':now(),'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':len(data)})
    save(SOURCES/'manifest.json',manifest);print({'source_files':len(manifest)})

def prepare():
    assert not PAIR.exists();probe=read(ROOT/'outputs/reports/residual_probe_20261026.json');assert probe['map_authorized']
    old=read(BASELINE/'prediction_frozen.json')
    for p,h in old['files_sha256'].items():assert sha(ROOT/p)==h
    for e in read(SOURCES/'manifest.json'):assert sha(ROOT/e['path'])==e['sha256']
    folder=PAIR/'linelet';folder.mkdir(parents=True);source=(BASELINE/'case.cfg').read_text()
    assert source.splitlines().count('LINEAR_SOLVER_PREC= LU_SGS')==1
    text=source.replace('LINEAR_SOLVER_PREC= LU_SGS\n','LINEAR_SOLVER_PREC= LINELET\n')
    assert [(a,b) for a,b in zip(source.splitlines(),text.splitlines()) if a!=b]==[('LINEAR_SOLVER_PREC= LU_SGS','LINEAR_SOLVER_PREC= LINELET')]
    (folder/'case.cfg').write_text(text,encoding='utf-8');shutil.copyfile(BASELINE/'seed.dat',folder/'seed.dat')
    code=folder/'runner_code';code.mkdir();files=[BASE/n for n in ['linelet_control.py','prepare.py','run.py','cfl_control.py','scaled_restart.py','inner_cap_control.py','linear_work_control.py']]+[ROOT/'work/reliability/paired_control.py',ROOT/'work/tmr_m6_20261025/common.py']
    for p in files:shutil.copyfile(p,code/p.name)
    save(folder/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in files}})
    c={'created_utc':now(),'not_blind':True,'baseline':str(BASELINE.relative_to(ROOT)),'baseline_seal_sha256':sha(BASELINE/'prediction_frozen.json'),
       'seed_sha256':sha(folder/'seed.dat'),'mesh_sha256':sha(CASE/'meshes/fine.su2'),'config_sha256':sha(folder/'case.cfg'),
       'source_manifest_sha256':sha(SOURCES/'manifest.json'),'probe_report_sha256':sha(ROOT/'outputs/reports/residual_probe_20261026.json'),
       'observation':'Verified density residual squared share99.626% in x.5..2,y0..0.05; stretched wall-normal cells. Localization is not mesh-error or causal proof.',
       'hypothesis':'Normal-line implicit coupling may improve the localized convergence at bounded cost; may lose beneficial off-line LU_SGS coupling.',
       'only_config_change':'LINEAR_SOLVER_PREC LU_SGS→LINELET','iterations':200,'seconds':180,'threads':4,
       'effect':{'SI_density_log10_gain_min':.3,'SI_SA_log10_worsening_max':.1,'total_Krylov_work_ratio_max':1.5},
       'activation':'Native preconditioner message plus computed mean line length>1',
       'source_algorithm_limit':'SU2v8.5 MAX_LINELET_POINTS32; not all193 wall-normal nodes and not full BL resolution.',
       'same_adaptive_policy_not_trajectory':True,'no_automatic_extension_or_parameter_sweep':True,
       'old_M6_result':'Prior3D source-M6 LINELET effect failed; not generalized to this measured2D source grid.',
       'physical_qualification_passed':False}
    save(PAIR/'contract.json',c)
    t=ROOT/read(CASE/'inner_cap_20261026_v1/task.json')['path'];task=read(t)
    task.update(phase='konumsal artığa dayalı tekLINELET kontrolü',linelet_contract=str((PAIR/'contract.json').relative_to(ROOT)),linelet_contract_sha256=sha(PAIR/'contract.json'));save(t,task)
    print({'registered':str(PAIR),'resources':memory()},flush=True)

def run():
    c=read(PAIR/'contract.json');folder=PAIR/'linelet';assert not (folder/'solver.process.json').exists()
    assert sha(BASELINE/'prediction_frozen.json')==c['baseline_seal_sha256']
    assert sha(folder/'case.cfg')==c['config_sha256'] and sha(folder/'seed.dat')==c['seed_sha256'] and sha(CASE/'meshes/fine.su2')==c['mesh_sha256']
    assert sha(SOURCES/'manifest.json')==c['source_manifest_sha256']
    for p,h in read(folder/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/p)==h
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];print('START LINELET',memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',c['seconds'],dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=2.5)
    seal=freeze_folder(folder,PAIR/'contract.json',CASE/'meshes/fine.su2');print('FROZEN',status,seal['matched'],flush=True)

def compare():
    c=read(PAIR/'contract.json');free=read(CASE/'contract.json')['derived_freestream'];folders=[BASELINE,PAIR/'linelet'];raw=[read(p/'prediction_frozen.json') for p in folders];verified=0
    for s in raw:
        for p,h in s['files_sha256'].items():assert sha(ROOT/p)==h;verified+=1
    si=[dimensional_matched(s,free) for s in raw];e=c['effect']
    quality=evaluate(*si,199,e['SI_density_log10_gain_min'],e['SI_SA_log10_worsening_max'],normalizations=('SI2D','SI2D'))
    counts=[work(history(p),199) for p in folders] if quality['comparable'] else [None,None]
    ratio=counts[1]['total']/counts[0]['total'] if quality['comparable'] else None
    log=(folders[1]/'solver.log').read_text(errors='replace')
    means=[float(v) for v in re.findall(r'Computed linelet structure,\s*([0-9.eE+-]+)\s*points in each line',log)]
    activation='Using a linelet preconditioning.' in log and bool(means) and all(v>1 for v in means)
    decision=decide(quality,ratio,e['total_Krylov_work_ratio_max']);decision['checks']['native_linelet_active']=activation;decision['effect_passed']=all(decision['checks'].values())
    result={'reviewed_utc':now(),'contract_sha256':sha(PAIR/'contract.json'),'raw':raw,'SI':si,'quality':quality,'work_counts':counts,'work_ratio':ratio,
       'activation_verified':activation,'reported_mean_line_lengths':means,'verified_file_records':verified,**decision,
       'limits':['Same200-step restart control only; cached full family unchanged.','Linelets capped at32points, off-line blockJacobi.','Krylov work is not FLOP or universal wall-time speedup.']}
    save(ROOT/'outputs/reports/flatplate_linelet_20261026.json',result);print({k:result[k] for k in ['quality','work_ratio','activation_verified','reported_mean_line_lengths','effect_passed']},flush=True)

if __name__=='__main__':{'sources':sources,'prepare':prepare,'run':run,'compare':compare}[sys.argv[1]]()
