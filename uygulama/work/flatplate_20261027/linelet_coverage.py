"""Read native linelet coverage; graph colors are not individual line IDs."""
from pathlib import Path
import sys,os,shutil
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/flatplate_20261025'))
from prepare import CASE as OLD,read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder
CASE=ROOT/'outputs/simulations/flatplate_20261027_v1/linelet_coverage'
REPORT=ROOT/'outputs/reports/linelet_coverage_20261027.json'

def prepare():
    assert not CASE.exists();parent=OLD/'linelet_20261026_v1/linelet';seal=read(parent/'prediction_frozen.json')
    for p,h in seal['files_sha256'].items():assert sha(ROOT/p)==h,p
    probe=read(ROOT/'outputs/reports/residual_probe_20261026.json');assert probe['map_authorized'] and probe['all_five_RMS_and_MAX_match']
    for p,h in probe['output_files_sha256'].items():assert sha(ROOT/p)==h,p
    sources=read(BASE/'sources/manifest.json')
    for x in sources:assert sha(ROOT/x['path'])==x['sha256']
    folder=CASE/'native';folder.mkdir(parents=True);mesh=OLD/'meshes/fine.su2'
    path=os.path.relpath(mesh,folder).replace('\\','/')
    text=(parent/'case.cfg').read_text();changes={'ITER= 200':'ITER= 1',
      'MESH_FILENAME= ../../meshes/fine.su2':'MESH_FILENAME= '+path,
      'OUTPUT_WRT_FREQ= (200,200,200,200)':'OUTPUT_WRT_FREQ= (1,1,1,1)',
      'VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE)':'VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE,LINELET)'}
    for a,b in changes.items():assert text.splitlines().count(a)==1;text=text.replace(a+'\n',b+'\n')
    (folder/'case.cfg').write_text(text,encoding='utf-8');shutil.copyfile(parent/'seed.dat',folder/'seed.dat')
    code=folder/'runner_code';code.mkdir();files=[Path(__file__),ROOT/'work/flatplate_20261025/cfl_control.py',ROOT/'work/flatplate_20261025/prepare.py',ROOT/'work/flatplate_20261025/run.py',ROOT/'work/tmr_m6_20261025/common.py']
    for p in files:shutil.copyfile(p,code/p.name)
    save(folder/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in files}})
    csv=ROOT/probe['all_points_csv']
    c={'created_utc':now(),'not_blind':True,'purpose':'Native static linelet membership vs separately verified sequential-stage nonlinear RHS; no convergence claim',
      'config_sha256':sha(folder/'case.cfg'),'seed_sha256':sha(folder/'seed.dat'),'mesh':str(mesh.relative_to(ROOT)),'mesh_sha256':sha(mesh),
      'sources_manifest_sha256':sha(BASE/'sources/manifest.json'),'source_probe_report_sha256':sha(ROOT/'outputs/reports/residual_probe_20261026.json'),
      'source_probe_csv':str(csv.relative_to(ROOT)),'source_probe_csv_sha256':sha(csv),'changes_from_parent':changes,
      'source_semantics':'CFVMOutput loads geometry.GetLineletInfo(config).lineletColor; zero means no linelet, positive integers are graph colors, not individual line IDs.',
      'gates':{'expected_points':52689,'coordinate_mapping_max_m':2e-7,'finite_nonnegative_integer_colors':True,'positive_membership_required':True},
      'iterations':1,'seconds':60,'threads':4,'physical_conditions_unchanged':True,'physical_qualification_passed':False}
    save(CASE/'contract.json',c)
    taskpath=ROOT/read(BASE/'task.json')['path'];t=read(taskpath);t.update(phase='nativeLINELET kapsama ölçümü',coverage_contract=str((CASE/'contract.json').relative_to(ROOT)),coverage_contract_sha256=sha(CASE/'contract.json'));save(taskpath,t)
    print({'prepared':str(CASE),'resources':memory()},flush=True)

def run():
    c=read(CASE/'contract.json');f=CASE/'native';assert not (f/'solver.process.json').exists()
    for p,h in read(f/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/p)==h
    assert sha(f/'case.cfg')==c['config_sha256'] and sha(f/'seed.dat')==c['seed_sha256'] and sha(ROOT/c['mesh'])==c['mesh_sha256']
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];print('START native linelet coverage',memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],f,'solver',c['seconds'],dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=2.5)
    s=freeze_folder(f,CASE/'contract.json',ROOT/c['mesh']);print('FROZEN',status,s['matched'],flush=True)

def analyse():
    import numpy as np
    from field_audit import field
    from probe_residual_analysis import coordinate_mapping
    c=read(CASE/'contract.json');f=CASE/'native';seal=read(f/'prediction_frozen.json')
    for p,h in seal['files_sha256'].items():assert sha(ROOT/p)==h,p
    assert seal['native_status']['exit_code']==0 and seal['matched']['field_iteration']==seal['matched']['terminal_history_iteration']==0
    csv=ROOT/c['source_probe_csv'];assert sha(csv)==c['source_probe_csv_sha256']
    old=np.genfromtxt(csv,delimiter=',',names=True);xy=np.column_stack([old['x_m'],old['y_m']])
    grid,vxy,d=field(f/'flow_000000.vtu');g=c['gates']
    mapping,order=coordinate_mapping(xy,vxy,g['coordinate_mapping_max_m'],g['expected_points']);assert mapping['passed']
    color=d['Linelet'][order];assert color.shape==(len(xy),) and np.isfinite(color).all() and np.all(color>=0) and np.all(color==np.round(color))
    member=color>0;assert member.any() and (~member).any()
    rho=old['Rho_squared_share'];nu=old['nu_squared_share'];assert np.isfinite(rho).all() and np.isfinite(nu).all()
    assert abs(rho.sum()-1)<1e-12 and abs(nu.sum()-1)<1e-12
    out=ROOT/'outputs/data/qualification/flatplate_20261027/linelet_coverage';out.mkdir(parents=True,exist_ok=True)
    np.savetxt(out/'all_nodes.csv',np.column_stack([np.arange(len(xy)),xy,color,member.astype(int),rho,nu]),delimiter=',',
      header='mesh_node,x_m,y_m,linelet_graph_color,native_linelet_member,Rho_squared_share,nu_squared_share',comments='')
    info={'reviewed_utc':now(),'contract_sha256':sha(CASE/'contract.json'),'mapping':mapping,'native_membership_accepted':True,
      'nodes':len(xy),'linelet_nodes':int(member.sum()),'linelet_node_fraction':float(member.mean()),'unique_positive_graph_colors':np.unique(color[member]).astype(int).tolist(),
      'covered_y_extent_m':[float(xy[member,1].min()),float(xy[member,1].max())],
      'covered_Rho_squared_share':float(rho[member].sum()),'covered_nu_squared_share':float(nu[member].sum()),
      'uncovered_Rho_squared_share':float(rho[~member].sum()),'uncovered_nu_squared_share':float(nu[~member].sum()),
      'data_csv':str((out/'all_nodes.csv').relative_to(ROOT)),'data_csv_sha256':sha(out/'all_nodes.csv'),
      'source_RHS':'Verified explicit sequential-stage snapshot from original fine3999; not recomputed from this new implicit field.',
      'colors_are_not_individual_line_IDs':True,'coverage_is_not_causal_or_mesh_error_proof':True,'physical_qualification_passed':False}
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(13,4.4))
    ax[0].scatter(xy[~member,0],xy[~member,1],s=1,c='#c5cbd2',label='Outside native linelets',rasterized=True)
    ax[0].scatter(xy[member,0],xy[member,1],s=1,c='#007f96',label='Inside native linelets',rasterized=True)
    ax[0].set(xlabel='x [m]',ylabel='y [m]',ylim=(-.00002,.002),title='Actual native union; colors are not line IDs');ax[0].legend(markerscale=5)
    ys,idx=np.unique(xy[:,1],return_inverse=True);marg=np.bincount(idx,weights=rho)
    ax[1].semilogx(ys[ys>0],np.cumsum(marg)[ys>0],label='Cumulative density squared residual')
    ax[1].axvline(info['covered_y_extent_m'][1],color='#007f96',ls='--',label='Maximum native linelet height')
    ax[1].set(xlabel='y [m]',ylabel='Cumulative fraction',ylim=(0,1.01),title='Separate original RHS snapshot; all nodes kept');ax[1].legend()
    for a in ax:a.grid(alpha=.2)
    fig.tight_layout();plot=ROOT/'outputs/plots/linelet_coverage_20261027.png';fig.savefig(plot,dpi=160);plt.close(fig)
    info['plot']=str(plot.relative_to(ROOT));save(REPORT,info);print({k:info[k] for k in ['nodes','linelet_nodes','covered_y_extent_m','covered_Rho_squared_share','covered_nu_squared_share']},flush=True)

if __name__=='__main__':{'prepare':prepare,'run':run,'analyse':analyse}[sys.argv[1]]()
