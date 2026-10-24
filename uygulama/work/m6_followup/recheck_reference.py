"""Download the public reference separately; never replace original data."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'work/m6_followup/reference_recheck';folder.mkdir(exist_ok=True)
target=folder/'ONERAb114.tec';assert not target.exists()
url='https://www.grc.nasa.gov/www/wind/valid/m6wing/ONERAb114.tec'
data=urllib.request.urlopen(url,timeout=30).read();target.write_bytes(data)
old=ROOT/'work/validation/sources/ONERAb114.tec';a={'verified_download_utc':datetime.now(timezone.utc).isoformat(),
    'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'matches_preserved_original_bytes':data==old.read_bytes(),
    'original_file_unchanged':True,'provenance_note':'Fresh24Oct public-source download verified; original19Oct download time for this supplemental file was not in the first manifest.'}
assert a['matches_preserved_original_bytes'],'Reference changed: preserve both and require a separately versioned review'
(ROOT/'outputs/projects/proje-e9319baef1/reports/m6_reference_recheck_20261024.json').write_text(json.dumps(a,indent=2))
print(json.dumps(a,indent=2))
