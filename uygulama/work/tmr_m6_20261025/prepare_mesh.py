"""Pre-register a distinct normalized sharp-TE source case and generate nested grids."""
from common import ROOT,BASE,PROJECT,CASE,TASK,read,save,sha,now,memory,run_native
import os
import re
import shutil
import sys


def input_for(base,changes):
    text=base
    for key,value in changes.items():
        text,count=re.subn(r'(?m)^(\s*'+re.escape(key)+r'\s*=)[^!\n]+',lambda m:m.group(1)+' '+str(value)+' ',text)
        assert count==1,(key,count)
    return text


def prepare():
    assert not (CASE/'contract.json').exists()
    CASE.mkdir(parents=True,exist_ok=True)
    physical={'Mach':.84,'alpha_deg':3.06,'beta_deg':0,'Re_root':14.6e6,'Reynolds_length_m':1.,'T_K':300.,
              'source_root_chord_original_mm':810.491484086,'normalized_root_chord_m':1.,
              'nominal_semispan_m':1.47601797621980,'S_ref_half_wing_m2':1.15315084119231,'MAC_m':.801672958512342,
              'moment_center_m':[0.,0.,0.],'SA_variant':'SA-neg','nu_tilde_inf_over_nu':3.,
              'Pr_lam':.72,'Pr_turb':.9,'mu_ref':1.716e-5,'T_mu_ref_K':491.6*5/9,'Sutherland_K':198.6*5/9,
              'boundary':'No-slip adiabatic wing; root symmetry; characteristic farfield',
              'origin':'TMR sharp-TE numerical comparison definition, NOT original blunt tunnel geometry'}
    source=ROOT/'tools/tmr_m6/source'
    contract={'version':'tmr_sharp_20261025_v1','created_utc':now(),'project_id':'proje-e9319baef1',
              'scope':'Source generator + nested family + budgeted SU2 source-case diagnostic; independent agent blindness and general CFD acceptance not claimed',
              'not_blind':True,'physical':physical,'source_sha256':{p.name:sha(p) for p in source.iterdir() if p.is_file()},
              'source_urls':['https://tmbwg.github.io/turbmodels/onerawingnumerics_val.html',
                             'https://tmbwg.github.io/turbmodels/onerawingnumerics_val_sa.html',
                             'https://tmbwg.github.io/turbmodels/onerawingnumerics_grids.html'],
              'planned_fine_mesh':{'nnodes_cylinder_input':32,'nr_gs':16,'nre':64,'R_outer':100,'target_y_plus':.125,
                                   'stretching_tanh_towards_lete':1.0,'igrid_type':5},
              'family':'Generate one fine HC mesh, use original coarsener twice; same analytical source geometry and outer radius. Discrete surface facets change systematically.',
              'geometry_screens':{'root_chord_abs_error_max':1e-9,'boundary_node_single_fluid_neighbour_required':True,
                                  'positive_element_volume_required':True,'positive_sampled_Jacobian_required':True,
                                  'same_source_points_and_normalized_scale_required':True},
              'mesh_resource_budget':{'fine_max_nodes':320000,'fine_max_cells':320000,'generator_seconds':180,'coarsener_seconds':180},
              'native_budget':{'full_runs_max':3,'iterations_per_run_max':4000,'seconds_by_role':{'coarse':300,'medium':600,'fine':1500},
                               'working_set_GiB_max':2.5,'minimum_available_system_GiB':1.},
              'physical_acceptance_gates':{'density_log10_below':-7.,'CL_last100_absolute_range_below':1e-4,
                  'CD_last100_absolute_range_below':1e-5,'strict_max_yplus_below':1.,
                  'all_14_section_Cp_RMSE_below':.08,'all_experiment_points_retained':True,
                  'three_iteratively_converged_systematic_meshes_required':True,'regional_BL_TE_tip_wake_required':True,
                  'separate_farfield_sensitivity_required':True,'independent_force_integral_required':True},
              'native_numerical_policy':{'baseline':'Installed SU2 v8.5 native M6 source config syntax; JST, MUSCL_FLOW=NO, first-order SA transport',
                  'gradient':'GREEN_GAUSS; corrected interior viscous flux per tagged code',
                  'linear_solver':'FGMRES/LU_SGS; tol1e-5 cap40','CFL':'5 adaptive(0.5,1.2,5,100,0.001,50)',
                  'multigrid_levels':0,'reason':'Single mesh nonlinear baseline; no simultaneous method sweep or feedback to experiment'},
              'comparison_policy':'Freeze each failed or successful prediction before opening new reference tables; numerical-source forces are not experiment.',
              'memory_at_registration':memory(),'minimum_physical_qualification_passed':False}
    save(CASE/'contract.json',contract)
    sys.path.insert(0,str(ROOT/'work/agent'))
    from learning import instruction_snapshot
    task=read(TASK);task.update(status='çalışıyor',phase='kaynak ağ ve çözücü doğrulaması',
        acceptance=['Özgün kaynak programların yerel derlenmesi ve gerçek çalışması','Üç sistematik kaynak ağının topoloji/geometri/bölgesel ölçüleri',
                    'Bütçeli native çözümler ve dondurulmuş ham çıktılar','Kaynak koşullarına bağlı karşılaştırma ve açık kabullerle rapor'],
        applied_lesson_ids=['L01','L02','L03','L04','L05','L06','L07','L08','L09','R01','R03'],
        agent_instruction_snapshot=instruction_snapshot(ROOT),contract=str((CASE/'contract.json').relative_to(ROOT)),contract_sha256=sha(CASE/'contract.json'))
    save(TASK,task)


def generate(name,changes):
    folder=CASE/name;folder.mkdir()
    install=read(ROOT/'work/setup/tmr_m6_install.json')
    source=ROOT/'tools/tmr_m6/source'
    base=(source/'input.nml_strct').read_text(encoding='utf-8')
    mesh=read(CASE/'contract.json')['planned_fine_mesh']
    updates={'target_y_plus':mesh['target_y_plus'],'nnodes_cylinder_input':mesh['nnodes_cylinder_input'],
             'nr_gs':mesh['nr_gs'],'nre':mesh['nre'],'stretching_tanh_towards_lete':1.,
             'generate_p3d_ufmt_file':'F','generate_su2grid_file':'T','generate_tec_file_b':'T','generate_tec_file_v':'F'}
    updates.update(changes)
    (folder/'input.nml').write_text(input_for(base,updates),encoding='utf-8')
    shutil.copyfile(source/'om6_wing_section_sharp.dat',folder/'om6_wing_section_sharp.dat')
    env=dict(os.environ);env['PATH']=install['process_PATH_prefix']+os.pathsep+env.get('PATH','')
    result=run_native([install['executables']['hcf_wing.exe']],folder,'generator',180,env=env,memory_cap_gib=2.)
    assert result['exit_code']==0,result
    assert list(folder.glob('*.su2')),'Source generator exited without a SU2 mesh'
    save(folder/'generation.json',{'input_sha256':sha(folder/'input.nml'),'runtime':result,'source_modified':False,
                                  'meshes':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in folder.glob('*.su2')]})
    print(name,[(p.name,p.stat().st_size) for p in folder.glob('*.su2')],flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='smoke':generate('generator_smoke',{'nnodes_cylinder_input':16,'nr_gs':4,'nre':32})
    elif mode=='smoke-v2':generate('generator_smoke_v2',{'nnodes_cylinder_input':16,'nr_gs':4,'nre':128})
    elif mode=='family':generate('mesh_family',{})
    elif mode=='family-v3':generate('mesh_family_budget_v3',{})
    else:raise ValueError(mode)
