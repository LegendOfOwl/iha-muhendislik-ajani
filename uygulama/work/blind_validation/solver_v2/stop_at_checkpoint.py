from pathlib import Path
import time,os,json,sys
from solve import SIM,sha
name=sys.argv[1];iteration=int(sys.argv[2]);folder=SIM/name;deadline=time.monotonic()+180
needed=[folder/f'{prefix}_{iteration:06d}.{ext}' for prefix,ext in [('flow','vtu'),('surface_flow','vtu'),('surface_flow','csv'),('restart_flow','dat')]]
while not all(p.exists() and p.stat().st_size>100 for p in needed):
    if time.monotonic()>deadline:raise TimeoutError('Checkpoint not reached; native solver left running')
    time.sleep(.5)
time.sleep(2)
meta=json.loads((folder/'process.json').read_text());os.kill(meta['pid'],9)
(folder/'bounded_stop_reason.json').write_text(json.dumps({'reason':'Density residual floor and force oscillation persisted in the own fine run; stop at a complete checkpoint before a single-policy low-CFL trial, rather than spend the full long budget. No physical condition or acceptance threshold changed.','requested_checkpoint':iteration,'native_pid':meta['pid'],'preserved_checkpoint_sha256':{p.name:sha(p) for p in needed}},indent=2))
print('Stopped',name,'after complete checkpoint',iteration)
