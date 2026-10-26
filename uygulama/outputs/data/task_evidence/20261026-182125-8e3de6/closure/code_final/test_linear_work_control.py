from prepare import ROOT,save,now
from linear_work_control import decision

def main():
    limits={'total_flow_plus_SA_Krylov_iterations_ratio_max':.7,'density_and_SA_SI_log10_worsening_max':.05,'absolute_CD_difference_max':1e-7}
    assert decision(True,.6,.01,.01,1e-8,limits)['effect_passed']
    cases={'incomplete_pair':(False,.6,.01,.01,1e-8),'work_above_limit':(True,.7000001,.01,.01,1e-8),
       'density_above_limit':(True,.6,.0500001,.01,1e-8),'SA_above_limit':(True,.6,.01,.0500001,1e-8),
       'CD_at_strict_limit':(True,.6,.01,.01,1e-7),'nonfinite_work':(True,float('nan'),.01,.01,1e-8),
       'missing_work':(True,None,.01,.01,1e-8)}
    for name,c in cases.items():assert not decision(*c,limits)['effect_passed'],name
    result={'checked_utc':now(),'passed':8,'checks':['valid_effect_not_physical_acceptance']+list(cases),'physical_qualification':False}
    save(ROOT/'outputs/reports/linear_work_guards_20261026.json',result);print(result)

if __name__=='__main__':main()
