"""Additional source audit; never changes the pre-analysis inputs or contract."""
from pathlib import Path
import urllib.request,json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
DEST=ROOT/'work/blind_validation/reviewer/additional_sources'
DEST.mkdir(exist_ok=True)
SOURCES={
 'agard_ar138.pdf':'https://www.abbottaerospace.com/downloads/agard-r-138/?ind=1461685668841&wpdmdl=3718',
 'raetaf.x.fmt':'https://www.grc.nasa.gov/www/wind/valid/raetaf/raetaf04/raetaf.x.fmt',
}
records=[]
for name,url in SOURCES.items():
 p=DEST/name
 try:
  if not p.exists():
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=55) as r:
    data=r.read(); final=r.url
   if name.endswith('.pdf') and not data.startswith(b'%PDF'):raise ValueError('Not a PDF')
   p.write_bytes(data)
  else:final=None
  records.append({'file':str(p.relative_to(ROOT)),'url':url,'resolved_url':final,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'timestamp_utc':datetime.now(timezone.utc).isoformat()})
  print(name,p.stat().st_size,flush=True)
 except Exception as e:
  records.append({'file':name,'url':url,'error':repr(e)})
  print(name,repr(e),flush=True)
(DEST/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
