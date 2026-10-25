from prepare import ROOT,CASE,read,save,now
from audit_controls import score

def main():
    free=read(CASE/'contract.json')['derived_freestream']
    folders={'scaling':'warm_scaling_pair_v1/scaled','cold_quasi':'newton_control_v1/quasi',
             'cold_newton':'newton_control_v1/newton','warm_quasi':'newton_warm_control_v1/quasi',
             'warm_newton':'newton_warm_control_v1/newton'}
    results={name:score(CASE/rel,'control_'+name,'medium',normalization=free) for name,rel in folders.items()}
    save(ROOT/'outputs/reports/flatplate_scaled_control_fields_20261025.json',
         {'created_utc':now(),'cases':results,'physical_qualification_passed':False,
          'scaling':'Same source freestream SI reference, length1m; force/Cf/yplus unchanged, primitive fields and residuals converted.',
          'limits':['One medium mesh only; no general three-grid qualification.','Cold-start reference errors are diagnostic; they are not accepted converged predictions.']})

if __name__=='__main__':main()
