"""Finite, preregistered three-grid qualification of the accepted lower-work recipe."""
from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder
from scaled_restart import convert
import os,sys,shutil

FAMILY=CASE/'reduced_family_20261026_v1'
SOURCES={'coarse':('coarse',400),'medium':('medium',3600),'fine':('fine',2000)}
COUNTS={'coarse':200,'medium':4000,'fine':4000}
BUDGETS={'coarse':120,'medium':360,'fine':900}

def prepare():
    assert not FAMILY.exists()
    effect=read(ROOT/'outputs/reports/flatplate_linear_work_20261026.json');assert effect['effect_passed']
    original=read(CASE/'contract.json');free=original['derived_freestream']
    template=(CASE/'linear_work_20261026_v1/reduced/case.cfg').read_text()
    cases={};FAMILY.mkdir()
    for role,(parent,iteration) in SOURCES.items():
        old=CASE/parent;seal=read(old/'prediction_frozen.json');source=old/f'restart_flow_{iteration:06d}.dat'
        assert sha(source)==seal['files_sha256'][str(source.relative_to(ROOT))]
        mesh=CASE/f'meshes/{role}.su2';assert sha(mesh)==original['levels'][role]['mesh_sha256']
        f=FAMILY/role;f.mkdir();data,check=convert(source.read_bytes(),free);(f/'seed.dat').write_bytes(data)
        text=template.replace('ITER= 200\n',f'ITER= {COUNTS[role]}\n')
        text=text.replace('CONV_STARTITER= 1000','CONV_STARTITER= 100000').replace('../../meshes/medium.su2',f'../../meshes/{role}.su2')
        (f/'case.cfg').write_text(text,encoding='utf-8');save(f/'seed_conversion.json',check)
        code=f/'runner_code';code.mkdir();paths=[BASE/n for n in ['reduced_family.py','prepare.py','run.py','cfl_control.py','scaled_restart.py']]+[ROOT/'work/tmr_m6_20261025/common.py']
        for p in paths:shutil.copyfile(p,code/p.name)
        save(f/'code_before_native.json',{'created_utc':now(),'files_sha256':{str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in paths}})
        cases[role]={'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_iteration':iteration,
            'seed_sha256':sha(f/'seed.dat'),'config_sha256':sha(f/'case.cfg'),'mesh_sha256':sha(mesh),
            'iterations':COUNTS[role],'seconds':BUDGETS[role]}
    save(FAMILY/'contract.json',{'created_utc':now(),'not_blind':True,'scope':'Fixed NASA TMR2DZP SA-neg three-source-grid implementation comparison; no experimental or M6 qualification',
       'accepted_work_control_report_sha256':sha(ROOT/'outputs/reports/flatplate_linear_work_20261026.json'),
       'physical_source_contract_sha256':sha(CASE/'contract.json'),'physical_source_contract':str((CASE/'contract.json').relative_to(ROOT)),
       'unchanged_acceptance':original['gates_registered_before_flow'],'cases':cases,'threads':4,
       'numerical_policy':'Same Roe2/MUSCL-flow, SA1, WLS, FGMRES/LUSGS40, noMG; source adaptiveCFL100..1e5; ND scaling; inner tolerance1e-3.',
       'stopping':'Fixed registered iterations with budgets; CONV_STARTITER100000 prevents premature common ND residual threshold from stopping before SI gates. No automatic retry/extension.',
       'field_selection':'Each mesh uses its final complete registered iteration; an incomplete run cannot pass the family.',
       'fine_role':'Original uniform-initialized fine checkpoint2000, not the reference-better diagnostic nested seed.',
       'mesh_family':'Exact original source coordinates/connectivity, common physical domain; different evolved seed states are numerical initial conditions only.',
       'GCI':'Not automatically inferred; global leading-edge drag singularity and iterative/asymptotic requirements retained.',
       'physical_changes':None,'general_CFD_qualification_claimed':False})
    taskpath=ROOT/read(CASE/'linear_work_20261026_v1/task.json')['path'];task=read(taskpath)
    task['phase']='aynı fizik ve üç kaynak ağda kabul denetimi';task['family_contract']=str((FAMILY/'contract.json').relative_to(ROOT));task['family_contract_sha256']=sha(FAMILY/'contract.json');save(taskpath,task)
    print({'registered_family':cases,'resources':memory()},flush=True)

def run(role):
    c=read(FAMILY/'contract.json');case=c['cases'][role];folder=FAMILY/role
    assert not (folder/'solver.process.json').exists()
    if role!='coarse':assert read(FAMILY/'coarse/prediction_frozen.json')['native_status']['exit_code']==0
    assert sha(folder/'case.cfg')==case['config_sha256'] and sha(folder/'seed.dat')==case['seed_sha256']
    assert sha(CASE/f'meshes/{role}.su2')==case['mesh_sha256'] and sha(CASE/'contract.json')==c['physical_source_contract_sha256']
    for p,h in read(folder/'code_before_native.json')['files_sha256'].items():assert sha(ROOT/p)==h
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];print('START',role,memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',case['seconds'],
       dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),memory_cap_gib=2.5)
    frozen=freeze_folder(folder,FAMILY/'contract.json',CASE/f'meshes/{role}.su2');print('FROZEN',role,status,frozen['matched'],flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run(sys.argv[2])
    else:raise ValueError(sys.argv[1])
