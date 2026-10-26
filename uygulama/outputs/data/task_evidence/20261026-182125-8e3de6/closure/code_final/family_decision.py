"""Fail closed on missing/nonfinite benchmark evidence; no physical acceptance claim."""
import math

ROLES={'coarse','medium','fine'}

def finite(x):
    return isinstance(x,(int,float)) and math.isfinite(x)

def reference_gate(rows,limit):
    return len(rows)==2 and all(r.get('points',0)>0 and r.get('invalid_points')==0 and
        finite(r.get('relative_L2')) and 0<=r['relative_L2']<limit for r in rows)

def decide(results,completion,gates):
    f=results.get('fine',{});m=results.get('medium',{});err=f.get('reference_errors',{})
    def change(key):
        a=f.get(key) if key=='Cf_x0p97008' else f.get('matched',{}).get(key)
        b=m.get(key) if key=='Cf_x0p97008' else m.get('matched',{}).get(key)
        return abs(a/b-1) if finite(a) and finite(b) and a>0 and b>0 else None
    cf=change('Cf_x0p97008');cd=change('CD');scalars=f.get('scalar_reference',[]);yp=f.get('max_yplus')
    checks={'all_registered_runs_completed':set(completion)==ROLES and all(completion.values()),
      'all_three_iterative_gates':set(results)==ROLES and all(a.get('iterative_gate') is True for a in results.values()),
      'fine_max_yplus':finite(yp) and 0<=yp<gates['fine_max_yplus'],
      'fine_Cf_scalar_both_codes':len(scalars)==2 and all(finite(r.get('finest_reference_relative_difference')) and
          0<=r['finest_reference_relative_difference']<gates['fine_Cf_x0p97008_relative_difference_each_code_max'] for r in scalars),
      'fine_Cf_curve_both_codes':reference_gate(err.get('Cf_curve',[]),gates['fine_Cf_curve_relative_RMS_each_code_max']),
      'fine_velocity_both_stations':reference_gate(err.get('velocity',[]),gates['velocity_profile_relative_L2_max']),
      'fine_mut_both_codes':reference_gate(err.get('eddy_viscosity',[]),gates['mut_profile_relative_L2_max']),
      'medium_fine_Cf':cf is not None and cf<gates['medium_fine_Cf_change_max'],
      'medium_fine_CD':cd is not None and cd<gates['medium_fine_CD_change_max']}
    return checks,{'Cf':cf,'CD':cd}
