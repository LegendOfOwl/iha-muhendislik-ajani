from prepare import ROOT,BASE,CASE,read,save,sha,now
from reduced_family import FAMILY
from audit_controls import score
from compare_utils import zones
from run import history
from scaled_restart import scales
from family_decision import decide
import numpy as np
import matplotlib.pyplot as plt

def main():
    contract=read(FAMILY/'contract.json');free=read(CASE/'contract.json')['derived_freestream'];gates=contract['unchanged_acceptance']
    results={};completion={};verified=0;work_diagnostics={}
    refs=zones(BASE/'sources/cf_convergence.dat',4)
    fig,axes=plt.subplots(1,3,figsize=(14,4));factors=scales(free)['residual']
    for role,c in contract['cases'].items():
        folder=FAMILY/role;seal=read(folder/'prediction_frozen.json')
        for p,h in seal['files_sha256'].items():assert sha(ROOT/p)==h,p;verified+=1
        assert sha(CASE/f'meshes/{role}.su2')==c['mesh_sha256']
        a=score(folder,'reduced_20261026_'+role,role,normalization=free)
        scalars=[]
        for label,values in refs:
            n=read(CASE/'contract.json')['levels'][role]['cells'];row=values[np.flatnonzero(values[:,0]==n)[0]]
            scalars.append({'source_zone':label,'same_grid_Cf':float(row[3]),'same_grid_relative_difference':abs(a['Cf_x0p97008']/row[3]-1),
               'finest_reference_Cf':float(values[0,3]),'finest_reference_relative_difference':abs(a['Cf_x0p97008']/values[0,3]-1)})
        a['scalar_reference']=scalars;results[role]=a
        m=seal['matched'];status=seal['native_status']
        completion[role]=bool(status['exit_code']==0 and status['stop_reason'] is None and m and m['field_iteration']==m['terminal_history_iteration']==c['iterations']-1)
        h=history(folder)
        windows=[]
        for start in range(0,len(h),500):
            w=h[start:start+500]
            windows.append({'first_iteration':int(w[0]['Inner_Iter']),'last_iteration':int(w[-1]['Inner_Iter']),
               'density_log10_drop':w[0]['rms[Rho]']-w[-1]['rms[Rho]'],
               'flow_Krylov_sum':int(sum(r['Linear_Solver_Iterations'] for r in w)),
               'SA_Krylov_sum':int(sum(r['LinSolIterTurb'] for r in w)),
               'flow_fraction_at40_cap':sum(r['Linear_Solver_Iterations']==40 for r in w)/len(w),
               'SA_fraction_at40_cap':sum(r['LinSolIterTurb']==40 for r in w)/len(w),
               'CFL_range':[min(r['Avg CFL'] for r in w),max(r['Avg CFL'] for r in w)]})
        work_diagnostics[role]={'history_rows':len(h),'windows':windows,
           'interpretation':'Descriptive same-run history only; correlation of CFL/capped work/residual is not a causal diagnosis or cross-grid speedup.'}
        for ax,key in zip(axes,['rms[Rho]','rms[nu]','CD']):
            shift=np.log10(factors[key]) if key in factors else 0
            ax.plot([r['Inner_Iter'] for r in h],[r[key]+shift for r in h],label=role)
            ax.set(xlabel='Restart iteration',ylabel=key+' (SI)' if key!='CD' else 'CD');ax.grid(alpha=.2);ax.legend()
    checks,changes=decide(results,completion,gates)
    axes[0].axhline(-10,color='gray',ls=':');axes[1].axhline(-11,color='gray',ls=':')
    fig.suptitle('Original source mesh family; reduced inner work, residuals converted to SI');fig.tight_layout()
    fig.savefig(ROOT/'outputs/plots/reduced_family_convergence_20261026.png',dpi=160);plt.close(fig)
    result={'reviewed_utc':now(),'contract_sha256':sha(FAMILY/'contract.json'),'results':results,'completion':completion,
       'checks':checks,'medium_fine_changes':changes,'new_file_hash_records_verified':verified,'work_diagnostics':work_diagnostics,
       'registered_2D_numerical_screens_passed':all(checks.values()),'general_physical_qualification_passed':False,'M6_qualification_passed':False,
       'GCI':None,'experiment_compared':False,'not_blind':True,
       'limits':['Fixed NASA TMR domain and one Mach/Re/SA case; not general airfoil/3D/model validation.',
                 'No automatic formal order/GCI for global leading-edge-singular drag.',
                 'Exact dimensional Sutherland constant identity across all reference codes has not been independently established.',
                 'Prior failed fields and mesh roles retained; no physical threshold changed.']}
    save(ROOT/'outputs/reports/reduced_family_review_20261026.json',result)
    print({'checks':checks,'changes':result['medium_fine_changes'],'screens_passed':result['registered_2D_numerical_screens_passed']},flush=True)

if __name__=='__main__':main()
