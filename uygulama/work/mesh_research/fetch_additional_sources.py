from pathlib import Path
from datetime import datetime,timezone
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'work/mesh_research/sources'
items=[
 ('SU2_AIAA2014_0243.pdf','https://su2code.github.io/documents/SU2_AIAA_SciTech2014.pdf'),
 ('SU2_v8_5_0_RAE2822_SA.cfg','https://raw.githubusercontent.com/su2code/SU2/v8.5.0/TestCases/rans/rae2822/turb_SA_RAE2822.cfg'),
 ('SU2_convective_schemes.html','https://su2code.github.io/docs_v7/Convective-Schemes/'),
 ('SU2_v8_5_0_CFlowCompOutput.cpp','https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/src/output/CFlowCompOutput.cpp'),
 ('TMBWG_SA_variants.html','https://tmbwg.github.io/turbmodels/spalart.html'),
 ('SU2_discussion1522.html','https://github.com/su2code/SU2/discussions/1522'),
 ('NASA_RAE_Study5.html','https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf05/raetaf05.html'),
]
def main():
    target=DEST/'additional_manifest.json'
    if target.exists():raise RuntimeError('Preserve download manifest.')
    manifest=[]
    for name,url in items:
        p=DEST/name
        if not p.exists():
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EngineeringValidation/1.0'}),timeout=45) as r:body=r.read()
            p.write_bytes(body)
        body=p.read_bytes();manifest.append({'url':url,'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'verified_or_downloaded_utc':datetime.now(timezone.utc).isoformat()})
        print(name,len(body),flush=True)
    target.write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
