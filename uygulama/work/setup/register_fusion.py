"""Add only a project-scoped official Fusion server after completed OAuth."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
folder=ROOT/'.codex'; folder.mkdir(exist_ok=True)
p=folder/'config.toml'; text=p.read_text(encoding='utf-8') if p.exists() else ''
section='[mcp_servers.fusion_compute]'
if section not in text:
    text+='\n'+section+'\nurl = "https://developer.api.autodesk.com/da/v3/mcp/fusion"\nstartup_timeout_sec = 30\ntool_timeout_sec = 180\nenabled = true\n'
    p.write_text(text,encoding='utf-8')
manifest={'registered_utc':datetime.now(timezone.utc).isoformat(),'provider':'Official Autodesk Fusion Compute MCP (public beta)',
 'endpoint':'https://developer.api.autodesk.com/da/v3/mcp/fusion','config_scope':'project .codex/config.toml',
 'oauth_login_verified':True,'user_reported_license':'Fusion student license; entitlement not yet checked by starting a session',
 'available_in_current_chat':False,'fusion_engine_tested':False,
 'next_action':'Reload MCP/server connection in the app or reopen this project; list versions/sessions before starting Fusion',
 'roles':{'OpenVSP':'aircraft geometry and fast aerodynamics','Fusion_FreeCAD':'parametric parts, assemblies and drawings','SU2':'volume-mesh CFD'},
 'credentials':'Managed by Codex OAuth; no tokens or passwords copied into project files'}
(ROOT/'work/setup/fusion_mcp_install.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
cfg=json.loads((ROOT/'work/setup/tool_config.json').read_text())
cli=[cfg['codex_cli'],'-c','mcp_servers.fusion_compute.url="https://developer.api.autodesk.com/da/v3/mcp/fusion"','mcp','get','fusion_compute','--json']
proc=subprocess.run(cli,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
(ROOT/'work/setup/fusion_connection_check.json').write_text(json.dumps({'exit_code':proc.returncode,'metadata':json.loads(proc.stdout) if proc.returncode==0 else proc.stdout,'note':'Metadata confirms configuration; no Fusion modeling tool was invoked.'},indent=2),encoding='utf-8')
print('Project-scoped official Fusion endpoint registered; OAuth completed; engine validation still pending.')
