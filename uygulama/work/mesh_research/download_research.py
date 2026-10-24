from pathlib import Path
from datetime import datetime,timezone
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'work/mesh_research/sources';DEST.mkdir(parents=True,exist_ok=True)
ITEMS=[
('Diskin_Thomas_2008_gradient_accuracy.pdf','https://ntrs.nasa.gov/api/citations/20090007493/downloads/20090007493.pdf'),
('gmsh_4_15_2_manual.html','https://www.gmsh.info/doc/texinfo/gmsh.html'),
('SU2_v8_5_0_computeGradientsLeastSquares.hpp','https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/gradients/computeGradientsLeastSquares.hpp'),
('SU2_v8_5_0_CFVMFlowSolverBase.inl','https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/solvers/CFVMFlowSolverBase.inl'),
('NASA_RAE_Study1.html','https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf01/raetaf01.html'),
('NASA_RAE_Study4.html','https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf04.html'),
]
def main():
    manifest=[]
    for name,url in ITEMS:
        target=DEST/name
        if not target.exists():
            request=urllib.request.Request(url,headers={'User-Agent':'EngineeringValidation/1.0'})
            with urllib.request.urlopen(request,timeout=45) as response:body=response.read()
            target.write_bytes(body)
        data=target.read_bytes()
        manifest.append({'url':url,'path':str(target.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'verified_or_downloaded_utc':datetime.now(timezone.utc).isoformat()})
        print(name,len(data),flush=True)
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
