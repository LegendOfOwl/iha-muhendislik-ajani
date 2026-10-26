from copy import deepcopy
from prepare import ROOT,CASE,read,save,now
from family_decision import decide

def main():
    gates=read(CASE/'contract.json')['gates_registered_before_flow']
    row={'points':10,'invalid_points':0,'relative_L2':.001}
    a={'iterative_gate':True,'max_yplus':.3,'Cf_x0p97008':.003,'matched':{'CD':.003},
       'scalar_reference':[{'finest_reference_relative_difference':.001} for _ in range(2)],
       'reference_errors':{k:[deepcopy(row),deepcopy(row)] for k in ['Cf_curve','velocity','eddy_viscosity']}}
    results={r:deepcopy(a) for r in ['coarse','medium','fine']};done=dict.fromkeys(results,True)
    assert all(decide(results,done,gates)[0].values());checks=['valid_narrow_screens']
    def bad(name,modify):
        r=deepcopy(results);d=done.copy();modify(r,d)
        assert not all(decide(r,d,gates)[0].values()),name;checks.append(name)
    bad('incomplete_native_run',lambda r,d:d.update(fine=False))
    bad('missing_grid',lambda r,d:r.pop('coarse'))
    bad('iterative_failure',lambda r,d:r['medium'].update(iterative_gate=False))
    bad('empty_reference',lambda r,d:r['fine']['reference_errors'].update(Cf_curve=[]))
    bad('missing_reference_code',lambda r,d:r['fine']['scalar_reference'].pop())
    bad('invalid_probe',lambda r,d:r['fine']['reference_errors']['velocity'][0].update(invalid_points=1))
    bad('nan_metric',lambda r,d:r['fine']['reference_errors']['eddy_viscosity'][0].update(relative_L2=float('nan')))
    bad('yplus_at_strict_limit',lambda r,d:r['fine'].update(max_yplus=1.))
    bad('reference_at_strict_limit',lambda r,d:r['fine']['reference_errors']['Cf_curve'][0].update(relative_L2=.03))
    bad('zero_drag',lambda r,d:r['medium']['matched'].update(CD=0.))
    bad('mesh_change_too_large',lambda r,d:r['fine'].update(Cf_x0p97008=.0031))
    out={'checked_utc':now(),'passed':len(checks),'checks':checks,'general_physical_qualification':False}
    save(ROOT/'outputs/reports/reduced_family_guards_20261026.json',out);print(out)

if __name__=='__main__':main()
