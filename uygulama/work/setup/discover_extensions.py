"""Fetch primary-source metadata, without downloading large datasets or weights."""
from pathlib import Path
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'work/research'
DEST.mkdir(parents=True, exist_ok=True)
sources = {
    'freecad_release': 'https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest',
    'zero_model': 'https://huggingface.co/api/models/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B?blobs=true',
    'zero_quantizations': 'https://huggingface.co/api/models?search=Zero-To-CAD&limit=30',
    'zero_dataset': 'https://huggingface.co/api/datasets/ADSKAILab/Zero-To-CAD-1m',
    'cadmium_readme': 'https://raw.githubusercontent.com/chandar-lab/CADmium/main/README.md',
    'cad_recode_readme': 'https://raw.githubusercontent.com/filaPro/cad-recode/main/README.md',
    'projects_doc': 'https://learn.chatgpt.com/docs/projects.md',
}
for name, url in sources.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'UAV-engineering-workspace/1.0'})
        data = urllib.request.urlopen(req, timeout=45).read()
        (DEST / (name + ('.json' if data.startswith((b'{', b'[')) else '.md'))).write_bytes(data)
        obj = json.loads(data) if data.startswith((b'{', b'[')) else None
        if name == 'freecad_release':
            print(name, obj['tag_name'], [(a['name'], a['size'], a['browser_download_url']) for a in obj['assets'] if 'Windows' in a['name']], flush=True)
        elif name == 'zero_model':
            print(name, obj['sha'], [(a['rfilename'], a.get('size')) for a in obj['siblings']], flush=True)
        elif isinstance(obj, list):
            print(name, [a.get('id') for a in obj], flush=True)
        else:
            print(name, len(data), 'bytes saved', flush=True)
    except Exception as exc:
        print(name, type(exc).__name__, str(exc), flush=True)
