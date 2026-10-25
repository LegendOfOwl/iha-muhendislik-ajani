"""Use the original coarsener's nodal interpolation as an initial guess, not a solution."""
from common import ROOT,BASE,CASE,PROJECT,read,save,sha,now,run_native
from run_flow import rows
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix,save_npz
import os
import re
import shutil
import struct
import sys


def build_maps():
    source=CASE/'mesh_family_budget_v3';folder=CASE/'prolongation_operators';assert not folder.exists();folder.mkdir()
    for p in source.iterdir():
        if p.suffix in ['.ugrid','.k','.mapbc'] or '.lines_' in p.name:shutil.copyfile(p,folder/p.name)
    text=(source/'input_coarsen.nml').read_text().replace('generate_nc_prolong_file = F','generate_nc_prolong_file = T')
    text=text.replace(' check_non_planarity = T',' prolong_file_unformatted = F\n check_non_planarity = T')
    (folder/'input_coarsen.nml').write_text(text,encoding='utf-8')
    install=read(ROOT/'work/setup/tmr_m6_install.json');env=dict(os.environ)
    env['PATH']=install['process_PATH_prefix']+os.pathsep+env.get('PATH','')
    result=run_native([install['executables']['hcf_coarsening.exe']],folder,'coarsener',180,env,memory_cap_gib=1.)
    assert result['exit_code']==0,result
    maps=[]
    for fine_level in [1,2]:
        p=folder/f'wing_strct.{fine_level}.prolong_nc';indices=[];weights=[];indptr=[0]
        with p.open() as f:
            n=int(f.readline())
            for expected in range(1,n+1):
                i,count=map(int,f.readline().split());assert i==expected and 1<=count<=64
                for _ in range(count):
                    index,weight=f.readline().split();indices.append(int(index)-1);weights.append(float(weight))
                indptr.append(len(indices))
        coarse_count=read(PROJECT/f'reports/tmr_mesh_L{fine_level+1}_20261025.json')['nodes']
        fine_count=read(PROJECT/f'reports/tmr_mesh_L{fine_level}_20261025.json')['nodes']
        assert n==fine_count and min(indices)>=0 and max(indices)<coarse_count
        matrix=csr_matrix((weights,indices,indptr),shape=(n,coarse_count))
        sums=np.asarray(matrix.sum(axis=1)).ravel();error=float(np.max(abs(sums-1)))
        assert error<1e-10 and np.all(np.isfinite(weights)) and min(weights)>=0
        save_npz(folder/f'L{fine_level+1}_to_L{fine_level}.npz',matrix)
        maps.append({'source_map':p.name,'sha256':sha(p),'shape':list(matrix.shape),'nonzero_coefficients':len(weights),
                     'minimum_weight':min(weights),'max_constant_reproduction_error':error,
                     'single_coarse_node_rows':int(np.sum(np.diff(indptr)==1))})
    save(PROJECT/'reports/tmr_prolongation_operators_20261025.json',{'created_utc':now(),'runtime':result,'maps':maps,
         'meaning':'Source-defined convex nodal initial-state interpolation; integrated mass/momentum conservation is not guaranteed.',
         'source_mesh_files_unchanged':all(sha(p)==sha(folder/p.name) for p in source.glob('*.su2'))})
    print(maps,flush=True)


def read_restart(path):
    raw=path.read_bytes();header=list(struct.unpack('<5i',raw[:20]));assert header[0]==535532
    nf,npnt=header[1:3];labels=raw[20:20+33*nf]
    names=[labels[33*i:33*(i+1)].split(b'\0')[0].decode() for i in range(nf)]
    assert names==['x','y','z','Density','Momentum_x','Momentum_y','Momentum_z','Energy','Nu_Tilde'],names
    stop=20+33*nf+8*nf*npnt;assert len(raw)==stop,'Unknown restart metadata must be handled explicitly'
    data=np.frombuffer(raw,offset=20+33*nf,dtype='<f8').reshape(npnt,nf).copy()
    roundtrip=struct.pack('<5i',*header)+labels+data.astype('<f8').tobytes()
    assert roundtrip==raw,'Native binary restart roundtrip differs'
    return header,labels,data


def make_seed():
    from scipy.sparse import load_npz
    # Importing this parser brings VTK into this short preparation only.
    from mesh_audit import load_mesh
    folder=CASE/'nested_medium_seed';assert not folder.exists();folder.mkdir()
    source=CASE/'flow_v2_coarse';seal=read(source/'prediction_frozen.json');i=seal['matched']['field_iteration']
    seed=source/f'restart_flow_{i:06d}.dat';header,labels,data=read_restart(seed)
    matrix=load_npz(CASE/'prolongation_operators/L3_to_L2.npz')
    xyz,_,_=load_mesh(CASE/'mesh_family_budget_v3/wing_strct.2.su2')
    sourcexyz,_,_=load_mesh(CASE/'mesh_family_budget_v3/wing_strct.3.su2')
    assert np.max(abs(data[:,:3]-sourcexyz))<1e-12
    target=np.column_stack([xyz,matrix@data[:,3:]])
    rho=target[:,3];internal=target[:,7]-.5*np.sum(target[:,4:7]**2,axis=1)/rho
    assert np.all(np.isfinite(target)) and rho.min()>0 and internal.min()>0
    one=np.flatnonzero(np.diff(matrix.indptr)==1)
    idx=matrix.indices[matrix.indptr[one]]
    assert len(one)==len(sourcexyz)
    assert np.max(abs(xyz[one]-sourcexyz[idx]))<1e-12
    assert np.array_equal(target[one,3:],data[idx,3:])
    header[2]=len(xyz);dest=folder/'seed.dat'
    dest.write_bytes(struct.pack('<5i',*header)+labels+target.astype('<f8').tobytes())
    h,l,back=read_restart(dest);assert np.array_equal(back,target)
    save(folder/'transfer.json',{'created_utc':now(),'source_restart_sha256':sha(seed),'source_field_iteration':i,
        'source_iteratively_qualified':False,'seed_sha256':sha(dest),'source_points':len(data),'target_points':len(target),
        'constant_field_check_passed':True,'native_binary_roundtrip_bitwise':True,'nested_nodes_state_bitwise_preserved':True,
        'min_density':float(rho.min()),'min_conservative_internal_energy':float(internal.min()),'min_SA_variable':float(target[:,8].min()),
        'clipped_values':0,'scope':'Initial guess only; not a converged medium-grid field or conservative global transfer.'})
    print('Native-format nested seed validated',len(data),'->',len(target),flush=True)


def run_warm(smoke):
    name='nested_medium_smoke' if smoke else 'nested_medium_control';folder=CASE/name
    assert not folder.exists();folder.mkdir()
    baseline=CASE/'flow_v2_medium';text=(baseline/'case.cfg').read_text()
    text=text.replace('RESTART_SOL= NO','RESTART_SOL= YES').replace('SOLUTION_FILENAME= restart_flow','SOLUTION_FILENAME= seed')
    if smoke:text=text.replace('ITER= 4000','ITER= 20')
    (folder/'case.cfg').write_text(text,encoding='utf-8');shutil.copyfile(CASE/'nested_medium_seed/seed.dat',folder/'seed.dat')
    if not smoke:
        s=read(CASE/'nested_medium_smoke/prediction_frozen.json');assert s['native_status']['exit_code']==0 and s['terminal_history']['Inner_Iter']==19
    budget=60 if smoke else 600
    save(folder/'contract.json',{'created_utc':now(),'baseline_seal_sha256':sha(baseline/'prediction_frozen.json'),
          'seed_sha256':sha(folder/'seed.dat'),'cfg_sha256':sha(folder/'case.cfg'),'source_contract_sha256':sha(CASE/'contract.json'),
          'treatment':'Only initialization differs: source coarsener interpolates coarse conservative state; same medium mesh, physics and numerical policy.',
          'smoke':smoke,'budget_s':budget,'common_iteration':1000,'effect_log10_min':.3,
          'timing_not_controlled':'Fine baseline runs concurrently; no wall-time speedup claim.',
          'physical_acceptance_unchanged':True})
    exe=read(ROOT/'work/setup/su2_install.json')['executable'];env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
    print('START',name,flush=True)
    status=run_native([exe,'case.cfg','-t','4'],folder,'solver',budget,env,memory_cap_gib=.5)
    h=rows(folder/'history.csv') if (folder/'history.csv').exists() else []
    current=next((x for x in h if x['Inner_Iter']==1000),None)
    b=next(x for x in rows(baseline/'history.csv') if x['Inner_Iter']==1000)
    gain=b['rms[Rho]']-current['rms[Rho]'] if current else None
    common=[]
    for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')]:
        common.append({int(p.stem.rsplit('_',1)[1]) for p in folder.glob(f'{prefix}_*.{ext}') if p.stem.rsplit('_',1)[1].isdigit()})
    matched=set.intersection(*common)&{int(x['Inner_Iter']) for x in h}
    i=max(matched) if matched else None
    seal={'frozen_utc':now(),'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in folder.iterdir() if p.is_file()},
          'native_status':status,'terminal_history':h[-1] if h else None,'matched_iteration':i,
          'matched_history':next((x for x in h if x['Inner_Iter']==i),None),'not_blind':True,'new_reference_score_read':False,
          'registered_common_iteration':1000,'additional_density_log10_reduction':gain,'effect_passed':bool(gain is not None and gain>=.3),
          'physical_qualification_passed':False}
    save(folder/'prediction_frozen.json',seal)
    if smoke:assert status['exit_code']==0 and i==19,'Seed import rejected; no full warm run'
    else:save(PROJECT/'reports/tmr_nested_initialization_20261025.json',seal)
    print('END',name,status,'effect',gain,flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='maps':build_maps()
    elif mode=='seed':make_seed()
    elif mode=='smoke':run_warm(True)
    elif mode=='run':run_warm(False)
    else:raise ValueError(mode)
