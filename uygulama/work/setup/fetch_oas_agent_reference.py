"""Read-only upstream prompt/blueprint research at a recorded commit; never execute it."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[2]
def main():
    tree=json.loads((ROOT/'work/openaerostruct/agent_source_tree.json').read_text());commit=tree['sha']
    dest=ROOT/'work/openaerostruct/agent_reference';dest.mkdir(exist_ok=True)
    paths=['README.md','LICENSE','pyproject.toml','src/agent_logic.py','src/llm/router.md','src/llm/coder.md','src/llm/auditor.md','src/llm/relaxer.md','src/blueprints/aero_opt.py','src/blueprints/aerostruct_tube.py','tests/test_router_contract.py']
    records=[]
    for path in paths:
        url=f'https://raw.githubusercontent.com/ideas-um/openaerostruct-llm-agent/{commit}/{path}'
        raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Engineering-research'}),timeout=30).read()
        local=dest/path;local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(raw)
        records.append({'upstream':path,'url':url,'local_path':str(local.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest()})
    (dest/'manifest.json').write_text(json.dumps({'retrieved_utc':datetime.now(timezone.utc).isoformat(),'commit':commit,'policy':'Reference only; upstream LLM framework was not executed or installed','files':records},indent=2),encoding='utf-8')
    print(commit, len(records),'reference files saved')
if __name__=='__main__':main()
