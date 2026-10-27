"""One registered release/pristine/cap comparison; never promote old mesh roles."""
from pathlib import Path
import sys,os,shutil
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/flatplate_20261025'))
from prepare import read,save,sha,now
from common import run_native,memory
from cfl_control import freeze_folder
from scaled_restart import scales
sys.path.insert(0,str(BASE))
from decisions import reproducibility_gate,linecap_effect_gate
CASE=ROOT/'outputs/simulations/linecap_source_20261027_v1'
HOME=ROOT/'tools/su2-build/v8.5.0/controls'
IDENTITY=('source_tree_sha256','compiler_manifest_sha256','runtime_manifest_sha256')

def build(label):
    from build_su2 import tree_files,verify_copy,fingerprint,inside
    folder=HOME/label;s=read(folder/'status.json');c=read(folder/'contract.json')
    assert s['succeeded'] is True and s['contract_sha256']==sha(folder/'contract.json')
    for k in (*IDENTITY,'cap','source_commit','source_patch_sha256'):assert s[k]==c[k]
    assert fingerprint(c['prepared_files'])==c['source_tree_sha256']
    assert sha(inside(Path(s['exe']),folder/'build'))==s['exe_sha256']
    assert sha(folder/'source.patch')==c['source_patch_sha256']
    for path,h in c['runtime_DLL_sha256'].items():assert sha(ROOT/path)==h,path
    assert fingerprint(c['compiler_manifest'])==c['compiler_manifest_sha256']
    assert fingerprint(c['runtime_manifest'])==c['runtime_manifest_sha256']
    for path,h in c['compiler_manifest']['binaries'].items():assert sha(ROOT/path)==h,path
    verify_copy(c['prepared_files'],tree_files(folder/'source',ignore=('su2preconfig.timestamp',)))
    return s,c

def check_contract():
    c=read(CASE/'contract.json');anchor=read(BASE/'native_contract_anchor.json')
    assert sha(CASE/'contract.json')==anchor['contract_sha256']
    assert sha(BASE/'method_design.json')==c['design_sha256']==anchor['design_sha256']
    design=read(BASE/'method_design.json')
    expected=dict(design['decision_contract_limits'],pristine_source_tree_sha256=c['decision_contract']['pristine_source_tree_sha256'])
    assert c['decision_contract']==expected
    for p,h in c['live_code_before_native_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in c['code_before_native_sha256'].items():assert sha(ROOT/p)==h,p
    return c

def checked_change(label,c):
    from build_su2 import CAP_FILE,patch_cap,fingerprint
    import hashlib
    s,bc=build(label);old,oc=build(c['pristine_build'])
    ref=bc['reference_control']
    assert ref['label']==c['pristine_build'] and ref['status_sha256']==c['pristine_build_status_sha256']
    assert ref['contract_sha256']==sha(HOME/c['pristine_build']/'contract.json') and ref['exe_sha256']==old['exe_sha256']
    for k in ('source_commit','pristine_archive_tree_sha256','dependency_tree_sha256',*IDENTITY[1:]):assert s[k]==old[k]
    assert old['source_tree_sha256']==c['decision_contract']['pristine_source_tree_sha256']
    assert old['cap']==32 and s['cap']==256 and bc['patch_changed_files']==[CAP_FILE]
    expected=dict(oc['prepared_files'])
    modified=patch_cap((HOME/c['pristine_build']/'source'/CAP_FILE).read_bytes())
    expected[CAP_FILE]={'sha256':hashlib.sha256(modified).hexdigest(),'bytes':len(modified)}
    assert expected==bc['prepared_files'] and fingerprint(expected)==s['source_tree_sha256']
    return s,{'verified':True,'only_change':'MAX_LINELET_POINTS','reference_cap':32,'candidate_cap':256,
      'pristine_source_sha256':old['source_tree_sha256'],'modified_source_sha256':s['source_tree_sha256'],
      'patch_sha256':bc['source_patch_sha256']}

def prepare(label='p32a'):
    assert not CASE.exists(),'Do not replace registered cases'
    design=read(BASE/'method_design.json');s,c=build(label)
    assert s['cap']==32
    for p,h in design['inputs'].items():assert sha(ROOT/p)==h,p
    contract=dict(design['decision_contract_limits'],pristine_source_tree_sha256=s['source_tree_sha256'])
    mesh,seed,parent=[ROOT/design[k] for k in ('mesh','seed','parent_config')]
    CASE.mkdir(parents=True);cases={}
    original=parent.read_text(encoding='utf-8')
    for arm in ('release32','build32','build256'):
        f=CASE/arm;f.mkdir()
        aliases={'MESH_FILENAME= ../../meshes/fine.su2':'MESH_FILENAME= '+os.path.relpath(mesh,f).replace('\\','/'),
                 'VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE)':'VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE,LINELET)'}
        text=original
        for a,b in aliases.items():assert text.splitlines().count(a)==1;text=text.replace(a+'\n',b+'\n')
        (f/'case.cfg').write_text(text,encoding='utf-8');shutil.copyfile(seed,f/'seed.dat')
        cases[arm]={'config_sha256':sha(f/'case.cfg'),'seed_sha256':sha(f/'seed.dat')}
    assert len({r['config_sha256'] for r in cases.values()})==1
    release=Path(read(ROOT/'work/setup/su2_install.json')['executable'])
    free=read(ROOT/'outputs/simulations/flatplate_SAneg_20261025_v1/contract.json')['derived_freestream']
    factors={k[4:-1]:float(v) for k,v in scales(free)['residual'].items()}
    assert set(factors)=={'Rho','RhoU','RhoV','RhoE','nu'}
    record={'created_utc':now(),'design_sha256':sha(BASE/'method_design.json'),'decision_contract':contract,
            'share_sum_tolerance':1e-12,'mesh':str(mesh.relative_to(ROOT)),'mesh_sha256':sha(mesh),
            'fixed_RHS_csv':design['fixed_RHS_csv'],'fixed_RHS_sha256':sha(ROOT/design['fixed_RHS_csv']),
            'residual_ND_to_SI_factors':factors,'pristine_build':label,
            'pristine_build_status_sha256':sha(HOME/label/'status.json'),
            'release_executable':str(release),'release_executable_sha256':sha(release),
            'native_resources':design['native_resources'],'cases':cases,'not_blind':True,
            'no_automatic_extension':True,'physical_qualification_passed':False,'old_fine3999_role_preserved':True}
    code=CASE/'runner_code';code.mkdir()
    files=[BASE/n for n in ['native_control.py','decisions.py','payload.py','build_su2.py','compiler_smoke.py']]
    files += [ROOT/'work/flatplate_20261025'/n for n in ['cfl_control.py','run.py','prepare.py','scaled_restart.py','probe_residual_analysis.py','field_audit.py']]
    files += [ROOT/'work/tmr_m6_20261025/common.py',ROOT/'work/reliability/paired_control.py']
    for p in files:shutil.copyfile(p,code/p.name)
    record['code_before_native_sha256']={str((code/p.name).relative_to(ROOT)):sha(code/p.name) for p in files}
    record['live_code_before_native_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    save(CASE/'contract.json',record)
    assert not (BASE/'native_contract_anchor.json').exists()
    save(BASE/'native_contract_anchor.json',{'created_utc':now(),'contract_sha256':sha(CASE/'contract.json'),
                                          'design_sha256':sha(BASE/'method_design.json')})
    print({'prepared':str(CASE),'contract_sha256':sha(CASE/'contract.json')},flush=True)

def run(arm,label=None):
    c=check_contract();f=CASE/arm;assert arm in c['cases']
    assert not (f/'solver.process.json').exists()
    assert sha(BASE/'method_design.json')==c['design_sha256']
    for p,h in c['code_before_native_sha256'].items():assert sha(ROOT/p)==h,p
    assert sha(f/'case.cfg')==c['cases'][arm]['config_sha256'] and sha(f/'seed.dat')==c['cases'][arm]['seed_sha256']
    assert sha(ROOT/c['mesh'])==c['mesh_sha256']
    if arm=='release32':
        exe=c['release_executable'];assert sha(Path(exe))==c['release_executable_sha256'];identity={}
    else:
        if arm=='build256':
            reproduction=read(CASE/'reproduction.json');assert reproduction['accepted'] is True
            assert sha(HOME/c['pristine_build']/'status.json')==c['pristine_build_status_sha256']
        if arm=='build256':s,_=checked_change(label,c)
        else:s,_=build(label or c['pristine_build'])
        assert s['cap']==(256 if arm=='build256' else 32)
        if arm=='build32':assert sha(HOME/(label or c['pristine_build'])/'status.json')==c['pristine_build_status_sha256']
        exe=s['exe'];identity={k:s[k] for k in IDENTITY}
        assert identity['source_tree_sha256']==c['decision_contract']['pristine_source_tree_sha256'] or arm=='build256'
    save(f/'executable_before_native.json',{'exe':exe,'exe_sha256':sha(Path(exe)),'build_identities':identity,
        'build_label':label or (c['pristine_build'] if arm!='release32' else None)})
    from compiler_smoke import environment
    print('START',arm,memory(),flush=True)
    status=run_native([exe,'case.cfg','-t','4'],f,'solver',c['native_resources']['seconds_each'],environment(),memory_cap_gib=2.5)
    seal=freeze_folder(f,CASE/'contract.json',ROOT/c['mesh'])
    print('FROZEN',arm,status,seal['matched'],flush=True)

def extract(arm):
    from payload import extract_payload
    c=check_contract();f=CASE/arm;e=read(f/'executable_before_native.json')
    assert sha(Path(e['exe']))==e['exe_sha256']
    result=extract_payload(f,contract=c['decision_contract'],mesh_path=ROOT/c['mesh'],seed_path=f/'seed.dat',
            rhs_csv=ROOT/c['fixed_RHS_csv'],rhs_sha256=c['fixed_RHS_sha256'],
            residual_si_factors=c['residual_ND_to_SI_factors'],native_contract_path=CASE/'contract.json',
            share_sum_tolerance=c['share_sum_tolerance'],identities=e['build_identities'])
    save(CASE/(arm+'_payload.json'),result)
    print({'arm':arm,'extraction_accepted':result['accepted_for_decision'],'errors':result['errors']},flush=True)

def compare():
    c=check_contract();records=[read(CASE/(arm+'_payload.json')) for arm in ('release32','build32')]
    assert all(r['accepted_for_decision'] is True for r in records)
    a,b=[r['payload'] for r in records]
    result=reproducibility_gate(a,b,c['decision_contract']);target=CASE/'reproduction.json'
    assert not target.exists();save(target,result);print(result,flush=True)

def effect(label):
    c=check_contract();s,source_change=checked_change(label,c)
    records=[read(CASE/(arm+'_payload.json')) for arm in ('build32','build256')]
    assert all(r['accepted_for_decision'] is True for r in records)
    a,b=[r['payload'] for r in records]
    result=linecap_effect_gate(a,b,c['decision_contract'],read(CASE/'reproduction.json'),source_change)
    target=CASE/'effect.json';assert not target.exists();save(target,result);save(CASE/'source_change.json',source_change)
    print(result,flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':prepare(*sys.argv[2:])
    elif action=='run':run(*sys.argv[2:])
    elif action=='extract':extract(sys.argv[2])
    elif action=='compare':compare()
    elif action=='effect':effect(sys.argv[2])
    else:raise ValueError(action)
