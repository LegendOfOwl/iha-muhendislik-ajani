"""Freeze own V2 prediction before any experimental comparison. Never reads review outcomes."""
from pathlib import Path
import json,hashlib,datetime,csv,sys,shutil
import numpy as np
from postprocess import process,read_vtu,OUT,ROOT
from boundary_layer_profiles import inspect as profiles
from physical_checks import check as physical
SIM=OUT/'simulations';REP=OUT/'reports';SRC=Path(__file__).parent
CONTRACT='a3106e323f9a5671067b69fded039fa8b3d2aae607514ec114a949b501b91c69'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def load(p):return json.loads(Path(p).read_text())
def cpcompare(a,b):
    x=np.linspace(0,1,1001);errors=[];sides={}
    for side in ['upper','lower']:
        aa=a['Cp_by_side'][side];bb=b['Cp_by_side'][side];err=np.interp(x,bb['x'],bb['Cp'])-np.interp(x,aa['x'],aa['Cp']);errors.extend(err.tolist());sides[side]={'RMSE':float(np.sqrt(np.mean(err**2))),'max_absolute':float(np.max(abs(err)))}
    return {'RMSE':float(np.sqrt(np.mean(np.array(errors)**2))),'sides':sides,'grid':'1001 equally spaced x/c positions from0 to1 inclusive on EACH side, including shared LE/TE. No shock/edge points removed.'}
def comparison(a,b):return {'CL_relative_change':abs(b['CL']-a['CL'])/abs(b['CL']),'CD_relative_change':abs(b['CD']-a['CD'])/abs(b['CD']),'Cp':cpcompare(a,b),'denominator':'absolute finer/prototype value','both_iteratively_qualified':all(a['checks'].values()) and all(b['checks'].values())}
def profile_compare(base,prototype):
    aa=load(SIM/base/'boundary_layer_profile_audit.json');bb=load(SIM/prototype/'boundary_layer_profile_audit.json');rows=[];n=np.linspace(1e-6,.05,501)
    for a,b in zip(aa['profiles'],bb['profiles']):
        pa=SIM/base/f'profiles_iter{aa["field_checkpoint"]["iteration"]:06d}'/f'BL_profile_{a["side"]}_x{a["station_x_over_c"]:.2f}.csv'
        pb=SIM/prototype/f'profiles_iter{bb["field_checkpoint"]["iteration"]:06d}'/pa.name
        da=np.genfromtxt(pa,delimiter=',',names=True);db=np.genfromtxt(pb,delimiter=',',names=True)
        da=da[da['valid_probe']==1];db=db[db['valid_probe']==1]
        ua=np.interp(n,da['normal_distance_over_c'],da['Ut_over_Uinf']);ub=np.interp(n,db['normal_distance_over_c'],db['Ut_over_Uinf'])
        rows.append({'side':a['side'],'x_over_c':a['station_x_over_c'],'Ut_Uinf_relative_L2_0to0p05c':float(np.linalg.norm(ub-ua)/np.linalg.norm(ua)),'base_delta99_definitions':a['edge_definitions'],'prototype_delta99_definitions':b['edge_definitions'],'base_normal_resolution':a['normal_resolution'],'prototype_normal_resolution':b['normal_resolution']})
    return {'base_checkpoint':aa['field_checkpoint'],'prototype_checkpoint':bb['field_checkpoint'],'profiles':rows,'method':'Same physical normal stations, normalized by common freestream velocity. Uniform501 normal locations1e-6..0.05c; linear interpolation of own probed profiles only. Operational edge definitions retained separately.'}
def hotspot(name):
    sel=load(SIM/name/'checkpoint_selection.json');d,p,a=read_vtu(ROOT/sel['volume']);z=np.abs(a['Residual_Density']);ids=np.argsort(z)[-20:][::-1]
    return {'case':name,'checkpoint':sel,'highest20_absolute_nodal_density_residuals':[{'x_m':float(p[i,0]),'y_m':float(p[i,1]),'absolute_density_residual':float(z[i]),'Mach':float(a['Mach'][i]),'residual_nu_tilde':float(a['Residual_Nu_Tilde'][i])} for i in ids],'scope':'Own native point residual field for spatial diagnosis, not experiment error or a proof of the unique numerical cause.'}
def freeze():
    names=['v2_diag_jst','v2_diag_mat','v2_r2_coarse','v2_r2_medium','v2_r2_fine','v2_r2_fine_cfl1','v2_r3_medium']
    for name in names:
        if not (SIM/name/'run_status.json').exists():raise RuntimeError('Run still active: '+name)
    met={n:process(n) for n in names}
    for n in ['v2_r2_coarse','v2_r2_medium','v2_r2_fine','v2_r2_fine_cfl1','v2_r3_medium']:
        profiles(n);physical(n)
    cases=[]
    for role,n in [('coarse','v2_r2_coarse'),('medium','v2_r2_medium'),('fine','v2_r2_fine_cfl1')]:
        f=SIM/n;sel=load(f/'checkpoint_selection.json');cases.append({'level':role,'case_name':n,'folder':rel(f),'config':rel(f/'case.cfg'),'mesh':rel(f/'mesh.su2'),'surface':sel['surface'].replace('\\','/'),'volume':sel['volume'].replace('\\','/'),'restart':sel['restart'].replace('\\','/'),'history':rel(f/'history.csv'),'field_checkpoint_iteration':sel['iteration'],'history_terminal_iteration':met[n]['history_terminal']['Inner_Iter'],'iterative_and_yplus_checks':met[n]['checks'],'metrics_file':rel(f/'prediction_metrics.json'),'boundary_layer_profile_file':rel(f/'boundary_layer_profile_audit.json'),'mesh_metadata_source':rel((SIM/'v2_r2_fine/mesh_audit.json') if role=='fine' else f/'mesh_audit.json'),'continuation_from':{'case':'v2_r2_fine','checkpoint':800} if role=='fine' else None})
    far=SIM/'v2_r2_medium_far';far_status=load(far/'run_status.json');farrec={'level':'farfield_sensitivity','case_name':'v2_r2_medium_far','folder':rel(far),'mesh':rel(far/'mesh.su2'),'config':None,'surface':None,'volume':None,'restart':None,'history':None,'CL':None,'CD':None,'Cp':None,'max_wall_yplus':None,'status':far_status,'mesh_stitch_provenance':rel(far/'mesh_stitch_provenance.json')}
    for case in cases:
        case['sha256']={key:sha(ROOT/case[key]) for key in ['config','mesh','surface','volume','restart','history']}
        audit=load(ROOT/case['mesh_metadata_source']);case['cells']=audit['cells'];case['farfield_bounds_m']=audit['farfield_bounds_m'];case['geometry_curve_sha256']=audit['curve_definition_sha256'];case['condition_sha256']=sha(ROOT/'work/blind_validation/analysis_input/conditions.json')
    farrec['mesh_sha256']=sha(far/'mesh.su2')
    farrec['cells']=load(far/'mesh_audit.json')['cells']
    manifest={'family_id':'r2_C1_source65_200c_BL0p01_JST_MAT','chosen_before_experiment_comparison':True,'selection_reason':'Predeclared same-geometry/same200c-domain3-level numerical family. Fine fixed-CFL1 continuation uses identical spatial mesh/physics/flux discretization after original fine residual floor. No best-match-to-experiment selection. BL0.02 medium is a diagnostic, not substituted into the family.','main_cases':cases,'farfield_case':farrec}
    (REP/'prediction_v2_selected_cases.json').write_text(json.dumps(manifest,indent=2))
    grid=comparison(met['v2_r2_medium'],met['v2_r2_fine_cfl1']);thick=comparison(met['v2_r2_medium'],met['v2_r3_medium']);method=comparison(met['v2_diag_jst'],met['v2_diag_mat'])
    grid['screens']={'CL_change_below_0p5pct':grid['CL_relative_change']<.005,'CD_change_below2pct':grid['CD_relative_change']<.02,'Cp_RMSE_below0p01':grid['Cp']['RMSE']<.01}
    grid['valid_for_grid_error_estimate']=grid['both_iteratively_qualified'];grid['GCI_or_Richardson_error_band']=None
    bl=profile_compare('v2_r2_medium','v2_r3_medium');(REP/'prediction_v2_normal_resolution_comparison.json').write_text(json.dumps(bl,indent=2))
    # Large sensitivity or incomplete iterative qualification leaves the normal-resolution check OPEN.
    normal_closed=thick['both_iteratively_qualified'] and thick['CL_relative_change']<.005 and thick['CD_relative_change']<.02 and thick['Cp']['RMSE']<.01
    summary={'analysis_scope':'Native SU2v8.5.0 2D compressible steady RANS/SA baseline, original published65-point geometry, fixed Mach0.729/alpha2.31deg/Re6.5e6/T255.5555556K/chord1m, adiabatic no-slip, fully turbulent. No optimization/lift trim; not3D aircraft/stall/design verification.','strict_screens':{'density_log10_lt':-8,'CL_final200_range_lt':5e-5,'CD_final200_range_lt':2e-6,'max_yplus_lt':1.,'last2grid_CL_relative_lt':.005,'last2grid_CD_relative_lt':.02,'last2grid_Cp_RMSE_lt':.01,'farfield_CL_relative_lt':.0025,'farfield_CD_relative_lt':.01},'main_case_metrics':{n:{k:met[n][k] for k in ['field_checkpoint_iteration','density_log10_residual','CL','CD','CL_final200_range','CD_final200_range','max_wall_yplus','checks','independent_surface_force']} for n in ['v2_r2_coarse','v2_r2_medium','v2_r2_fine_cfl1']},'last2_grid_comparison':grid,'BL0p01_to0p02_medium_diagnostic':thick,'normal_resolution_check_closed':normal_closed,'normal_resolution_interpretation':'Quad block coverage is not alone the criterion. Actual normal velocity/eddy-viscosity profiles, exact cell cuts and the same-physics BL-thickness trial are retained. A large or unqualified trial leaves this check open.','scalar_to_matrix_method_diagnostic_old_geometry':method,'farfield_comparison':{'status':'not_evaluated','CL_relative_change':None,'CD_relative_change':None,'reason':far_status['reason']},'geometry':load(REP/'prediction_v2_geometry_revision.json'),'geometry_units_and_shared_near_mesh':load(REP/'prediction_v2_geometry_units_audit.json'),'physics_limitations':['Fully turbulent smooth-wall SA baseline does not explicitly impose the parent-sourced experimental trip atx/c0.03 with0.254mm roughness. Temperature is the source computational assumption, not claimed measured tunnel temperature.','SA nu_tilde freestream factor3 is the unchangedv8.5 default; TURB2LAMVISCRATIO10 is not that SA initialization factor.','Normal-profile Ue is operational and pressure-gradient dependent; two outer windows are retained.','Farfield physical flux trapezoid is a diagnostic, not the exact SU2 boundary numerical flux. Any imbalance remains visible in physical_units_force_balance.json.','Procedural blinding on shared disk does not prove security/training-memory isolation.'],'all_required_numeric_screens_passed':False,'all_required_gates_passed':False,'experiment_validation':'Not evaluated or accessed by the analyst. Reviewer will compare only after this freeze.','next_concrete_mesh_step':'Use an explicit body-fitted aft normal block/C-grid with capped normal step beyond0.01c, continuing through at least0.04c where appropriate; preserve exact source spline and C1 LE, use a controlled TE/wake transition instead of globally extending the self-intersecting Gmsh BoundaryLayer envelope. Verify x/c0.4/0.8/0.95 cut counts and profile convergence, then repeat a same-domain3-grid family before farfield and experiment acceptance.'}
    (REP/'prediction_v2_numerical_summary.json').write_text(json.dumps(summary,indent=2))
    (REP/'prediction_v2_stagnation_diagnostic.json').write_text(json.dumps({'original_fine':hotspot('v2_r2_fine'),'low_CFL_continuation':hotspot('v2_r2_fine_cfl1')},indent=2))
    shutil.copy2(SRC/'access_log_v2.json',REP/'prediction_v2_access_log.json')
    # A concise human-readable analyst report; evaluator-owned user reports remain untouched.
    lines=['# Kör analiz: ikinci sayısal revizyon','', 'Genel sayısal kabul: **geçmedi**. Deney sonuçları analist tarafından açılmadı.','', '|Seviye|Alan adımı|CL|CD|log yoğunluk artığı|max y+|','|---|---:|---:|---:|---:|---:|']
    for role,n in [('Kaba','v2_r2_coarse'),('Orta','v2_r2_medium'),('İnce, CFL1 devamı','v2_r2_fine_cfl1')]:
        m=met[n];lines.append(f'|{role}|{m["field_checkpoint_iteration"]}|{m["CL"]:.9f}|{m["CD"]:.9f}|{m["density_log10_residual"]:.4f}|{m["max_wall_yplus"]:.4f}|')
    lines+=['',f'Orta–ince değişim: CL%{100*grid["CL_relative_change"]:.4f}, CD%{100*grid["CD_relative_change"]:.4f}; yüzey Cp RMSE{grid["Cp"]["RMSE"]:.6f}. İnce iteratif kabulü kapanmadan bu farklar güvenilir ağ hatası değildir.', '',f'0,01→0,02c orta normal-katman tanısı: CL%{100*thick["CL_relative_change"]:.4f}, CD%{100*thick["CD_relative_change"]:.4f}, CpRMSE{thick["Cp"]["RMSE"]:.6f}. Alan/profil/kesit çözünürlüğü kayıtlıdır; yalnız y+ geçişiyle yeterlilik verilmedi.','', '0,03/0,04c global katman prototipleri kesişme yüzünden reddedildi. Büyük uzak alan koşusu kritik normal-ağ/iterasyon denetimi açıkken başlatılmadı; sonuçları null kaldı. Hazır400c ağın20c iç50.469 hücresi200c orta ağla birebirdir.','', '65 kaynak nokta korunarak C1 hücum kenarı sağlandı;305 nokta yalnız bağımsız şekil denetiminde kullanıldı. Firar kenarı yuvarlatılmadı. İlk taşmalı interpolasyon adayı ve tüm başarısız/durdurulan sayısal denemeler korundu.','', 'Tam türbülanslı SA çözümü, deneyin x/c0,03 trip düzenini açıkça uygulamaz. Bu çalışma2D sayısal analizdir; genel profil/3D uçak/deney doğrulaması değildir.','', 'Sonraki somut adım: kaynak eğriyi koruyan, aft bölgede normal adımı sınırlayan açık C-grid/normal blok ve kontrollü firar-izi geçişi; sonra aynı alan altında üç ağ ve ayrı uzak alan kabulü.']
    (REP/'prediction_v2_analyst_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    casesha={rel(p):sha(p) for f in SIM.glob('v2_*') if f.is_dir() for p in f.rglob('*') if p.is_file()}
    scripts={rel(p):sha(p) for p in SRC.glob('*.py')}
    inputs=[ROOT/'work/blind_validation/analysis_input'/f for f in ['geom.txt','geom.f90','yl.pts','yu.pts','conditions.json']]+[ROOT/'work/blind_validation/geometry_reference_v2'/f for f in ['source_surface_305.csv','manifest.json','initial_source_metadata.json']]+[ROOT/'work/blind_validation/reviewer/leading_edge_tangent_audit.json',ROOT/'work/setup/su2_install.json']
    insh={rel(p):sha(p) for p in inputs if p.is_file()}
    repsha={rel(p):sha(p) for p in REP.glob('prediction_v2_*') if p.is_file() and 'frozen' not in p.name}
    freeze={'schema':'blind_prediction_v2','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_by':'Delegated analysis agent, after its own numerical audits and before reviewer comparison','contract_sha256':CONTRACT,'contract_hash_provenance':'Parent supplied immutable hash metadata; contract file not opened','input_sha256':insh,'source_script_sha256':scripts,'case_files_sha256':casesha,'prediction_report_sha256':repsha,'selected_case_manifest':manifest,'numerical_summary':{k:summary[k] for k in ['strict_screens','main_case_metrics','last2_grid_comparison','BL0p01_to0p02_medium_diagnostic','normal_resolution_check_closed','farfield_comparison','all_required_numeric_screens_passed','all_required_gates_passed','analysis_scope']},'all_attempt_folders':[rel(f) for f in SIM.glob('v2_*') if f.is_dir()],'access_log':load(SRC/'access_log_v2.json'),'physics_limitations':summary['physics_limitations'],'next_concrete_mesh_step':summary['next_concrete_mesh_step'],'no_experimental_target_used_for_case_selection':True}
    freeze['work_log_sha256']={rel(p):sha(p) for p in SRC.glob('*.log') if 'finaliz' not in p.name}
    freeze['v1_preservation_baseline_sha256']=sha(SRC/'v1_preservation_hashes.json')
    freeze['v1_files_written_by_v2']=[]
    path=REP/'prediction_v2_frozen.json'
    if path.exists():raise RuntimeError('A frozen revision already exists; do not replace it')
    path.write_text(json.dumps(freeze,indent=2),encoding='utf-8');(REP/'prediction_v2_frozen.sha256').write_text(sha(path)+'  prediction_v2_frozen.json\n')
    print('FROZEN',rel(path),sha(path),flush=True)
if __name__=='__main__':freeze()
