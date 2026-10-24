"""Use the documented official Fusion Compute endpoint; credentials remain with Codex OAuth."""
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
cfg=json.loads((ROOT/'work/setup/tool_config.json').read_text())
command=[cfg['codex_cli'],'-c','mcp_servers.fusion_compute.url="https://developer.api.autodesk.com/da/v3/mcp/fusion"',
         'mcp','login','fusion_compute']
print('Autodesk Fusion Compute: official browser sign-in. No model API key or password is read by this script.',flush=True)
raise SystemExit(subprocess.call(command,cwd=ROOT))
