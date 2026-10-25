from prepare import ROOT,BASE,CASE,read,save,sha,now
from common import run_native
from run import history
import numpy as np,struct,os,shutil
from scipy.sparse import csr_matrix

def mesh(role):
    lines=(CASE/f'meshes/{role}.su2').read_text().splitlines();j=next(i for i,s in enumerate(lines) if s.startswith('NPOIN'));n=int(lines[j].split('=')[1])
    return np.array([[float(v) for v in row.split()[:2]] for row in lines[j+1:j+1+n]])

def main():
    seedfolder=CASE/'nested_seed'
    if seedfolder.exists():assert not (seedfolder/'seed.dat').exists(),'Never overwrite an existing seed or run'
    else:seedfolder.mkdir()
    frozen=read(CASE/'medium/prediction_frozen.json');i=frozen['matched']['field_iteration'];source=CASE/f'medium/restart_flow_{i:06d}.dat'
    raw=source.read_bytes();header=list(struct.unpack('<5i',raw[:20]));assert header[0]==535532 and header[1]==7
    labels=raw[20:251];names=[labels[33*j:33*(j+1)].split(b'\0')[0].decode() for j in range(7)]
    assert names==['x','y','Density','Momentum_x','Momentum_y','Energy','Nu_Tilde']
    data=np.frombuffer(raw,offset=251,dtype='<f8').reshape(header[2],7).copy();assert struct.pack('<5i',*header)+labels+data.tobytes()==raw
    src=mesh('medium');dst=mesh('fine');assert np.array_equal(src,data[:,:2])
    ni,nj=read(CASE/'contract.json')['levels']['medium']['dimensions'];grid=src.reshape(nj,ni,2)
    nfi,nfj=read(CASE/'contract.json')['levels']['fine']['dimensions']
    fi,fj=np.meshgrid(np.arange(nfi),np.arange(nfj));fi=fi.ravel();fj=fj.ravel()
    ix=np.minimum(fi//2,ni-2);iy=np.minimum(fj//2,nj-2)
    cols=np.stack([iy*ni+ix,iy*ni+ix+1,(iy+1)*ni+ix,(iy+1)*ni+ix+1],axis=1)
    corners=src[cols];tx=(fi-2*ix)/2.;ty=(fj-2*iy)/2.
    x=grid[0,:,0];y=grid[:,0,1]
    xerr=float(np.max(abs(grid[:,:,0]-x[None,:])));yerr=float(np.max(abs(grid[:,:,1]-y[:,None])))
    assert xerr<5e-12 and yerr<5e-12
    ix=np.clip(np.searchsorted(x,dst[:,0],side='right')-1,0,ni-2);iy=np.clip(np.searchsorted(y,dst[:,1],side='right')-1,0,nj-2)
    tx=(dst[:,0]-x[ix])/(x[ix+1]-x[ix]);ty=(dst[:,1]-y[iy])/(y[iy+1]-y[iy])
    projected=np.column_stack([np.clip(dst[:,0],x[0],x[-1]),np.clip(dst[:,1],y[0],y[-1])])
    assert np.max(abs(projected-dst))<5e-12
    roundoff=int(((tx<0)|(tx>1)|(ty<0)|(ty>1)).sum());tx=np.clip(tx,0,1);ty=np.clip(ty,0,1)
    weights=np.stack([(1-tx)*(1-ty),tx*(1-ty),(1-tx)*ty,tx*ty],axis=1)
    cols=np.stack([iy*ni+ix,iy*ni+ix+1,(iy+1)*ni+ix,(iy+1)*ni+ix+1],axis=1)
    shared=(fi%2==0)&(fj%2==0);source_ids=(fj[shared]//2)*ni+fi[shared]//2
    assert np.array_equal(src[source_ids],dst[shared])
    cols[shared,0]=source_ids;weights[shared]=[1,0,0,0]
    save(seedfolder/'support_check_v4.json',{'invalid_nodes':[],'x_tensor_error_m':xerr,'y_tensor_error_m':yerr,
        'method':'Initial-state interpolation on tensor axes within5e-12m source text rounding; shared source nodes copied exactly. Native mesh untouched.',
        'coordinate_reproduction_max_tolerance_m':5e-12,'rejected_drafts':['exact tensor equality','index-parent support','VTK negative shape weights'],
        'disproven_diagnosis':'Curvilinear-grid interpretation was false; measured differences are source ASCII roundoff.',
        'native_runs_from_rejected_drafts':0})
    op=csr_matrix((weights.ravel(),cols.ravel(),np.arange(len(dst)+1)*4),shape=(len(dst),len(src)))
    assert np.max(abs(op@np.ones(len(src))-1))<1e-14 and np.max(abs(op@src-dst))<5e-12
    state=op@data[:,2:];target=np.column_stack([dst,state]);rho=target[:,2];internal=target[:,5]-.5*np.sum(target[:,3:5]**2,axis=1)/rho
    assert np.isfinite(target).all() and rho.min()>0 and internal.min()>0
    assert np.array_equal(target.reshape(nfj,nfi,7)[::2,::2,2:].reshape(-1,5),data[:,2:])
    header[2]=len(dst);seed=seedfolder/'seed.dat';seed.write_bytes(struct.pack('<5i',*header)+labels+target.astype('<f8').tobytes())
    transfer={'created_utc':now(),'source_restart_sha256':sha(source),'source_field_iteration':i,'source_iteratively_qualified':False,
        'seed_sha256':sha(seed),'nodes_from_to':[len(src),len(dst)],'weights_nonnegative':True,
        'constant_field_error_max':float(np.max(abs(op@np.ones(len(src))-1))),'coordinate_linear_field_error_m':float(np.max(abs(op@src-dst))),
        'nested_states_bitwise_preserved':True,'min_density':float(rho.min()),'min_internal_energy':float(internal.min()),'min_nu_tilde':float(target[:,6].min()),
        'clipped_physical_values':0,'weight_parameter_roundoff_clips':roundoff,
        'prevented_error':'Three drafts rejected before native. Near-tensor source rounding measured; positive tensor weights with exact common-node copy, bounded coordinate reproduction. Mesh unchanged.',
        'scope':'Positive bilinear nodal conservative-state interpolation; not global conservation or an accepted fine field.'}
    save(seedfolder/'transfer.json',transfer)
    original=(CASE/'fine/case.cfg').read_text();text=original.replace('RESTART_SOL= NO','RESTART_SOL= YES').replace('SOLUTION_FILENAME= restart_flow','SOLUTION_FILENAME= seed')
    plan={'created_utc':now(),'source_contract_sha256':sha(CASE/'contract.json'),'seed_sha256':sha(seed),'only_treatment':'initialization from medium state; native restart mechanics enabled',
        'physical_and_mesh_unchanged':True,'same_convection_gradient_CFL_and_linear_policy':True,'common_iteration':400,'minimum_density_log10_gain':.3,
        'budgets':{'smoke_s':60,'full_s':300,'full_iterations':2000},'not_blind':True,'reference_scores_not_accessed':True,
        'role_policy':'Uniform fine remains registered baseline. Nested fine is a separately reported diagnostic; no promotion by reference score.'}
    save(seedfolder/'contract.json',plan)
    for name,steps,budget in [('nested_smoke',20,60),('fine_nested',2000,300)]:
        f=CASE/name;f.mkdir();(f/'case.cfg').write_text(text.replace('ITER= 8000','ITER= '+str(steps)),encoding='utf-8');shutil.copyfile(seed,f/'seed.dat')
        save(f/'registered_inputs.json',{'cfg_sha256':sha(f/'case.cfg'),'seed_sha256':sha(f/'seed.dat'),'mesh_sha256':sha(CASE/'meshes/fine.su2'),'contract_sha256':sha(seedfolder/'contract.json')})
        exe=read(ROOT/'work/setup/su2_install.json')['executable'];env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE')
        status=run_native([exe,'case.cfg','-t','4'],f,'solver',budget,env,memory_cap_gib=1)
        h=history(f);fields=[]
        for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('restart_flow','dat')]:fields.append({int(p.stem.rsplit('_',1)[-1]) for p in f.glob(f'{prefix}_*.{ext}') if p.stem.rsplit('_',1)[-1].isdigit()})
        matched=None;common=set.intersection(*fields)&{int(r['Inner_Iter']) for r in h}
        if common:
            k=max(common);row=next(r for r in h if r['Inner_Iter']==k);tail=[r for r in h if k-99<=r['Inner_Iter']<=k]
            matched={'field_iteration':k,'terminal_history_iteration':int(h[-1]['Inner_Iter']),**{key:row[key] for key in ['CL','CD','rms[Rho]','rms[nu]']},
                'last100_samples':len(tail),'CD_last100_range':max(r['CD'] for r in tail)-min(r['CD'] for r in tail)}
        seal={'created_utc':now(),'native_status':status,'matched':matched,'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in f.iterdir() if p.is_file()},'not_blind':True}
        save(f/'prediction_frozen.json',seal);print(name,matched,status,flush=True)
        if name=='nested_smoke':assert status['exit_code']==0 and matched is not None

if __name__=='__main__':main()
