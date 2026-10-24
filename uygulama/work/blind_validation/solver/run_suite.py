from pathlib import Path
import time,json
from solve import run,OUT
from postprocess import process
# The initial coarse process is already active; only independent mesh generation overlapped it.
if __name__=='__main__':
    while not (OUT/'simulations/coarse/run_status.json').exists():time.sleep(2)
    process('coarse')
    for name,budget in [('medium',1200),('fine',1600),('medium_far',1200)]:
        run(name,6000,budget,False,6.)
        process(name)
        (OUT/'reports/prediction_progress.json').write_text(json.dumps({'latest_completed_run':name,'remaining':[x for x in ['medium','fine','medium_far'] if not (OUT/'simulations'/x/'run_status.json').exists()]},indent=2))
