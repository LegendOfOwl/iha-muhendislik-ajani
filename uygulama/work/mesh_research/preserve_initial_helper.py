from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
current=ROOT/'work/mesh_research/run_case.py'
s=current.read_text()
new="""        seed=Path(seed)
        if seed.resolve()!=(folder/'seed.dat').resolve():shutil.copy2(seed,folder/'seed.dat')
        d.update(RESTART_SOL='YES',SOLUTION_FILENAME='seed',READ_BINARY_RESTART='YES')"""
old="        seed=Path(seed);shutil.copy2(seed,folder/'seed.dat');d.update(RESTART_SOL='YES',SOLUTION_FILENAME='seed',READ_BINARY_RESTART='YES')"
assert s.count(new)==1
s=s.replace(new,old).replace("    if mode=='prepare':prepare(name,seed=OUT/'simulations'/name/'seed.dat' if '--seed-existing' in sys.argv else None)","    if mode=='prepare':prepare(name)")
data=s.encode()
expected=json.loads((ROOT/'outputs/projects/proje-15cce2de02/reports/v3_research_plan_seal.json').read_text())['sha256']['work\\mesh_research\\run_case.py']
assert hashlib.sha256(data).hexdigest()==expected
(ROOT/'work/mesh_research/run_case_plan_version.py').write_bytes(data)
print('Original plan-sealed source preserved byte-exact:',expected)
