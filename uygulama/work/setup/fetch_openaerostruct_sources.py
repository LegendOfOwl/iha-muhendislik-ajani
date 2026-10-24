"""Retain the official example as published, with URL/hash and Apache license."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'work/openaerostruct/sources';DEST.mkdir(parents=True,exist_ok=True)
class Code(HTMLParser):
    def __init__(self):super().__init__();self.inside=False;self.current='';self.blocks=[]
    def handle_starttag(self,tag,attrs):
        if tag=='pre':self.inside=True;self.current=''
    def handle_endtag(self,tag):
        if tag=='pre':self.inside=False;self.blocks.append(self.current)
    def handle_data(self,data):
        if self.inside:self.current+=data
def main():
    records=[]
    for name,url in [('tube','https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/aerostructural_tube_walkthrough.html'),('quick','https://mdolab-openaerostruct.readthedocs-hosted.com/en/latest/quick_example.html'),('license','https://raw.githubusercontent.com/mdolab/OpenAeroStruct/main/LICENSE.md')]:
        req=urllib.request.Request(url,headers={'User-Agent':'Engineering-tool-qualification'})
        raw=urllib.request.urlopen(req,timeout=45).read();path=DEST/(name+('.txt' if name=='license' else '.html'));path.write_bytes(raw)
        record={'url':url,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest()}
        if name!='license':
            parser=Code();parser.feed(raw.decode('utf-8'));code=max(parser.blocks,key=len)
            if 'prob.run_driver()' not in code:raise ValueError('Full published example not found')
            script=DEST/(name+'_official.py');script.write_text(code,encoding='utf-8');record['example']=str(script.relative_to(ROOT));record['example_sha256']=hashlib.sha256(script.read_bytes()).hexdigest()
        records.append(record)
    (DEST/'manifest.json').write_text(json.dumps({'retrieved_utc':datetime.now(timezone.utc).isoformat(),'records':records},indent=2),encoding='utf-8')
    print(json.dumps(records,indent=2))
if __name__=='__main__':main()
