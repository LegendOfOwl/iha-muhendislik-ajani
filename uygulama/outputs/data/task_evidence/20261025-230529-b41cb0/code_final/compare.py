from prepare import ROOT,BASE,CASE,read,save,sha,now
from compare_utils import zones,relative_l2,interpolate,check
from run import history
import numpy as np,os,re
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    roles=['coarse','medium','fine','fine_nested'];sealed={}
    for role in roles:
        p=CASE/role/'prediction_frozen.json';s=read(p)
        for rel,h in s['files_sha256'].items():assert sha(ROOT/rel)==h
        sealed[role]=s
    refs={name:zones(BASE/'sources'/name,nc) for name,nc in [('cf_plate.dat',2),('cf_convergence.dat',4),('drag_convergence.dat',4),('mut_0.97.dat',3),('flatplate_u.dat',2)]}
    assert len(refs['cf_plate.dat'])==len(refs['mut_0.97.dat'])==len(refs['flatplate_u.dat'])==2
    fig,axes=plt.subplots(1,3,figsize=(15,5));colors={'coarse':'#a77a2c','medium':'#25858d','fine':'#a44a5f','fine_nested':'#4456a8'}
    for label,a in refs['cf_plate.dat']:axes[0].plot(a[:,0],a[:,1],':',label=label.split('=')[-1].strip('"'),lw=1.2)
    for label,a in refs['flatplate_u.dat']:
        axes[1].plot(a[:,0],a[:,1],'k:' if '0.97008' in label else 'k--',lw=1,label='CFL3D '+('x0.97' if '0.97008' in label else 'x1.90'))
    for label,a in refs['mut_0.97.dat']:axes[2].plot(a[:,2],a[:,1],':',lw=1.2,label=label.split('=')[-1].strip('"'))
    results={}
    for role in roles:
        audit=read(ROOT/f'outputs/reports/flatplate_{role}_field_audit_20261025.json');meshrole='fine' if role=='fine_nested' else role
        count=read(CASE/'contract.json')['levels'][meshrole]['cells'];data=ROOT/f'outputs/data/qualification/flatplate_SAneg_20261025_v1/{role}'
        wall=np.genfromtxt(data/'wall.csv',delimiter=',',names=True);x=wall['x_m'];cf=wall['Cfx'];curve=[];scalars=[]
        for label,a in refs['cf_plate.dat']:
            pred,valid=interpolate(x,cf,a[:,0]);mask=(a[:,0]>=.1)&(a[:,0]<=1.9)
            score=relative_l2(pred[mask],a[:,1][mask],valid[mask]);allscore=relative_l2(pred,a[:,1],valid)
            code='CFL3D' if 'CFL3D' in label else 'FUN3D'
            out=data/f'Cf_vs_{code}.csv';np.savetxt(out,np.column_stack([a[:,0],a[:,1],pred,pred-a[:,1],valid.astype(int),mask.astype(int)]),delimiter=',',header='x_m,Cf_reference,Cf_native,error,valid_sample,registered_scoring_window',comments='')
            curve.append({'code':code,'points':len(a),'invalid_points':int((~valid).sum()),'window_points':int(mask.sum()),'relative_L2_window':score,'relative_L2_all_points':allscore,
                'max_absolute_error_all_valid':float(abs(pred[valid]-a[:,1][valid]).max()),'csv':str(out.relative_to(ROOT))})
        for label,a in refs['cf_convergence.dat']:
            row=a[np.flatnonzero(a[:,0]==count)[0]];code='CFL3D' if 'CFL3D' in label else 'FUN3D'
            drag=next(a for l,a in refs['drag_convergence.dat'] if code in l);drow=drag[np.flatnonzero(drag[:,0]==count)[0]]
            scalars.append({'code':code,'same_grid_cells':count,'Cf_reference_same_grid':float(row[3]),'Cf_relative_difference_same_grid':abs(audit['Cf_x0p97008']/row[3]-1),
                'CD_reference_same_grid':float(drow[3]),'CD_relative_difference_same_grid':abs(audit['matched']['CD']/drow[3]-1),
                'Cf_relative_difference_finest_reference':abs(audit['Cf_x0p97008']/a[0,3]-1)})
        velocities=[];viscosities=[]
        for profile,(label,a) in zip(audit['profiles'],refs['flatplate_u.dat']):
            p=np.genfromtxt(ROOT/profile['csv'],delimiter=',',names=True);pred,valid=interpolate(p['y_m'],p['u_over_Uinf'],a[:,1]);valid &= p['valid_sample'].all()
            score=relative_l2(pred,a[:,0],valid)
            name='velocity_'+str(profile['requested_x_m'])+'.csv';np.savetxt(data/name,np.column_stack([a[:,1],a[:,0],pred,pred-a[:,0],valid.astype(int)]),delimiter=',',header='y_m,reference_u_over_Uinf,native_u_over_Uinf,error,valid_sample',comments='')
            velocities.append({'requested_x_m':profile['requested_x_m'],'actual_x_m':profile['actual_x_m'],'points':len(a),'invalid_points':int((~valid).sum()),'relative_L2':score})
            axes[1].plot(p['u_over_Uinf'],p['y_m'],'-' if profile['requested_x_m']<1 else '--',color=colors[role],lw=.9,label=role if profile['requested_x_m']<1 else None)
        p=np.genfromtxt(ROOT/audit['profiles'][0]['csv'],delimiter=',',names=True)
        for label,a in refs['mut_0.97.dat']:
            pred,valid=interpolate(p['y_m'],p['mut_over_muinf'],a[:,1]);score=relative_l2(pred,a[:,2],valid);code='CFL3D' if 'CFL3D' in label else 'FUN3D'
            np.savetxt(data/f'mut_vs_{code}.csv',np.column_stack([a[:,1],a[:,2],pred,pred-a[:,2],valid.astype(int)]),delimiter=',',header='y_m,reference_mut_over_muinf,native_mut_over_muinf,error,valid_sample',comments='')
            viscosities.append({'code':code,'reference_x_m':float(a[0,0]),'native_x_m':audit['profiles'][0]['actual_x_m'],'points':len(a),'invalid_points':int((~valid).sum()),'relative_L2':score})
        axes[0].plot(x,cf,color=colors[role],lw=1,label=role);axes[2].plot(p['mut_over_muinf'],p['y_m'],color=colors[role],lw=1,label=role)
        def below(value,limit):return value is not None and value<limit
        screens={'iteration':audit['iterative_gate'],'max_yplus':audit['max_yplus']<1,
            'Cf_scalar_both_finest_codes':all(below(s['Cf_relative_difference_finest_reference'],.02) for s in scalars),
            'Cf_curve_both_codes':all(below(s['relative_L2_window'],.03) for s in curve),
            'velocity_both_stations':all(below(s['relative_L2'],.03) for s in velocities),
            'mut_both_codes':all(below(s['relative_L2'],.05) for s in viscosities)}
        results[role]={'field_audit':audit,'curve_errors':curve,'same_grid_reference':scalars,'velocity_errors':velocities,'eddy_viscosity_errors':viscosities,'screens':screens,
            'role_gate_passed':all(screens.values())}
    for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=7)
    axes[0].set(xlim=(0,2),ylim=(0,.006),xlabel='x [m]',ylabel='Cfx',title='CFD code comparison; full CSV retains endpoints')
    axes[1].set(xlim=(0,1.1),ylim=(0,.06),xlabel='u/Uinf',ylabel='y [m]',title='Velocity: x≈0.97 and1.90m')
    axes[2].set(xlim=(0,250),ylim=(0,.06),xlabel='mu_t/mu_inf',ylabel='y [m]',title='Eddy viscosity: x≈0.97m')
    fig.suptitle('Source SA references vs native SA-neg; unconverged fields retained');fig.tight_layout();fig.savefig(ROOT/'outputs/plots/flatplate_reference_comparison_20261025.png',dpi=160);plt.close(fig)
    h0=history(CASE/'fine');h1=history(CASE/'fine_nested');r0=next((r for r in h0 if r['Inner_Iter']==400),None);r1=next((r for r in h1 if r['Inner_Iter']==400),None)
    gain=r0['rms[Rho]']-r1['rms[Rho]'] if r0 and r1 else None
    medium=results['medium']['field_audit'];fine=results['fine']['field_audit']
    sensitivity={'Cf_change':abs(fine['Cf_x0p97008']/medium['Cf_x0p97008']-1),'CD_change':abs(fine['matched']['CD']/medium['matched']['CD']-1),
        'valid_discretization_error_estimate':False,'reason':'Medium and fine iterative gates failed. Small differences cannot close convergence.'}
    result={'reviewed_utc':now(),'contract_sha256':sha(CASE/'contract.json'),'results':results,'mesh_sensitivity':sensitivity,
        'nested_initialization_effect':{'common_iteration':400,'density_log10_gain':gain,'effect_passed':gain is not None and gain>=.3,'physical_qualification_passed':False},
        'comparison_definitions':{'relative_L2':'unweighted norm(pred-reference)/norm(reference), all invalid samples retained; any invalid sample prevents score',
           'source_velocity_normalization':'Reference variable u interpreted as u/Uinf: nominal outer u≈1; native SI speed divided by registered freestream. This interpretation is explicit, not a measured velocity in m/s.',
           'source_mut_normalization':'TMR page explicitly specifies eddy viscosity normalized by freestream laminar viscosity',
           'curve':'Source finest545x385 Cf curves vs each native mesh; scalar same-grid values separately reported',
           'profile_positions':'Native actual coordinate and CFL3D/FUN3D reference x positions recorded; near0.97 is not exact identical x.'},
        'reference_sha256':{name:sha(BASE/'sources'/name) for name in refs},'guard_checks':check(),'GCI':None,
        'not_blind':True,'experiment_compared':False,'scoped_implementation_qualification_passed':False,'M6_qualification_passed':False,
        'conclusion':'Some local code-agreement screens pass, but not all required iterative/profile gates. No proof that M6 discrepancy is solely mesh/numerics or solely SA implementation.'}
    save(ROOT/'outputs/reports/flatplate_comparison_20261025.json',result)
    for role,r in results.items():print(role,{'screens':r['screens'],'Cf_same_grid_percent':{s['code']:100*s['Cf_relative_difference_same_grid'] for s in r['same_grid_reference']},'velocity':r['velocity_errors'],'mut':r['eddy_viscosity_errors']},flush=True)
    print('nested effect',result['nested_initialization_effect'])

if __name__=='__main__':main()
