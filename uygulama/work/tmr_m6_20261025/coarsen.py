from common import ROOT,CASE,read,save,sha,run_native
import os

folder=CASE/'mesh_family_budget_v3'
assert not (folder/'coarsener.status.json').exists()
config='''&input_parameters
 debug_mode = F
 project = 'wing_strct'
 tet2prism = F
 ugrid_file_unformatted = T
 k_file_unformatted = F
 generate_su2grid_file = T
 generate_tec_file_b = T
 generate_tec_file_vol = F
 generate_ntrl_partition_files = F
 generate_heff_vol_report = T
 generate_nc_prolong_file = F
 generate_rmp_file = F
 generate_cc_prolong_file = F
 check_negative_elm_vol = T
 check_non_planarity = T
/
'''
(folder/'input_coarsen.nml').write_text(config,encoding='utf-8')
install=read(ROOT/'work/setup/tmr_m6_install.json')
env=dict(os.environ);env['PATH']=install['process_PATH_prefix']+os.pathsep+env.get('PATH','')
r=run_native([install['executables']['hcf_coarsening.exe']],folder,'coarsener',180,env=env,memory_cap_gib=2.)
files=sorted(folder.glob('wing_strct.*.su2'))
save(folder/'coarsening.json',{'runtime':r,'input_sha256':sha(folder/'input_coarsen.nml'),
                              'mesh_files':[{'file':p.name,'sha256':sha(p)} for p in files]})
assert r['exit_code']==0,r
assert len(files)>=3,'Coarsener exited without three levels'
print([(p.name,p.stat().st_size) for p in files])
