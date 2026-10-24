from pathlib import Path
import time,json
from solve import prepare,execute,SIM,OUT
from initialize import initialize
from postprocess import process
if __name__=='__main__':
    while not (SIM/'v2_r2_coarse/run_status.json').exists():time.sleep(2)
    process('v2_r2_coarse')
    source=SIM/'v2_r2_coarse/restart_flow.dat'
    for name,budget in [('v2_r2_medium',1800),('v2_r2_fine',3400),('v2_r2_medium_far',1900)]:
        if name.endswith('_far'):source=SIM/'v2_r2_medium/restart_flow.dat'
        seed=initialize(name,source)
        prepare(name,seed=seed,method='JST_MAT',iterations=8000,more={'FREESTREAM_NU_FACTOR':'3.0'})
        execute(name,budget)
        process(name)
        source=SIM/name/'restart_flow.dat'
        (OUT/'reports/prediction_v2_progress.json').write_text(json.dumps({'latest_completed_run':name,'remaining':[x for x in ['v2_r2_medium','v2_r2_fine','v2_r2_medium_far'] if not (SIM/x/'run_status.json').exists()]},indent=2))
