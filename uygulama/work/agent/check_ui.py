"""Check the offline report's local assets and prepare Windows-compatible UI source."""
from datetime import datetime,timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import py_compile
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[2]
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in {'href','src'}: self.links.append(value)
parser=Links(); parser.feed((ROOT/'outputs/Proje-Ozeti.html').read_text(encoding='utf-8'))
missing=[]
for link in parser.links:
    url=urlsplit(link)
    if not url.scheme and url.path and not (ROOT/'outputs'/unquote(url.path)).exists(): missing.append(link)
assert not missing, missing
for path in (ROOT/'work').rglob('*.py'):
    if '__pycache__' not in path.parts: py_compile.compile(str(path),doraise=True)
p=ROOT/'work/agent/hub.ps1'
p.write_text(p.read_text(encoding='utf-8-sig'),encoding='utf-8-sig')
result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':True,'local_report_links_checked':len(parser.links),
        'missing':missing,'python_sources_compile':True,'gui_render':'outputs/plots/engineering_hub.png',
        'limits':'GUI render visually inspected; new LLM conversation not automatically started.'}
(ROOT/'outputs/reports/ui_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
