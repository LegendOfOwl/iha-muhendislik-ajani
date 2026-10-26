from prepare import ROOT,save,now
from inner_cap_control import decide

def main():
    good={'comparable':True,'effect_passed':True};limit=1.5
    assert decide(good,1.,limit)['effect_passed']
    assert decide(good,limit,limit)['effect_passed']
    cases={'above_work_limit':(good,1.50000001),'nonfinite_work':(good,float('nan')),
       'missing_work':(good,None),'bool_work':(good,False),'negative_work':(good,-1.),
       'unmatched_pair':({'comparable':False,'effect_passed':False},1.),
       'joint_residual_effect_failed':({'comparable':True,'effect_passed':False},1.)}
    for name,(quality,ratio) in cases.items():assert not decide(quality,ratio,limit)['effect_passed'],name
    result={'checked_utc':now(),'passed':2+len(cases),'checks':['valid_effect_not_physical','inclusive_work_boundary']+list(cases),
       'physical_qualification':False}
    save(ROOT/'outputs/reports/inner_cap_guards_20261026.json',result);print(result)

if __name__=='__main__':main()
