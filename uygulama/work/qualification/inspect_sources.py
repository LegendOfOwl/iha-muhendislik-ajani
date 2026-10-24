import json
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[2]; DEST=ROOT/'work/qualification'
urls={'su2_quickstart.json':'https://api.github.com/repos/su2code/SU2/contents/QuickStart?ref=v8.5.0',
      'su2_rans_case.json':'https://api.github.com/repos/su2code/TestCases/contents/rans/naca0012',
      'su2_tutorial_rans.json':'https://api.github.com/repos/su2code/Tutorials/contents/incompressible_flow/Inc_Turbulent_NACA0012'}
for name,url in urls.items():
    try:
        data=urlopen(Request(url,headers={'User-Agent':'Engineering-qualification/1.0'}),timeout=40).read()
        (DEST/name).write_bytes(data); obj=json.loads(data)
        print(name,[(x['name'],x.get('size'),x.get('download_url')) for x in obj],flush=True)
    except Exception as e: print(name,type(e).__name__,str(e),flush=True)
