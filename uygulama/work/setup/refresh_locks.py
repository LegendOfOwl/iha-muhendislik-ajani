"""Merge newly installed wheel hashes into the existing reproducible environment locks."""
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[2]
def normalized(s): return re.sub(r'[-_.]+','-',s).lower()
for env,lock,reports in [('.venv','requirements-core.txt',['core-install-report.json','agent-pip-report.json']),
                         ('.venv-cad','requirements-cad.txt',['cad-install-report.json','extension-pip-report.json'])]:
    known={}
    for line in (ROOT/'work/setup'/lock).read_text().splitlines():
        m=re.match(r'([^= ]+)==([^ ]+)\s+--hash=sha256:([a-f0-9]+)',line)
        if m: known[(normalized(m[1]),m[2])]=(m[1],m[3])
    for report in reports:
        data=json.loads((ROOT/'work/setup'/report).read_text())
        for row in data['install']:
            name=row['metadata']['name']; version=row['metadata']['version']
            sha=row['download_info']['archive_info']['hashes']['sha256']
            known[(normalized(name),version)]=(name,sha)
    packages=json.loads(subprocess.check_output([str(ROOT/env/'Scripts/python.exe'),'-m','pip','list','--format=json'],text=True))
    lines=['# Windows x64 / Python 3.12; exact wheel hashes from actual pip installation reports.']
    for row in sorted(packages,key=lambda a:normalized(a['name'])):
        if normalized(row['name']) in {'pip','setuptools','wheel'}: continue
        key=(normalized(row['name']),row['version'])
        if key not in known: raise RuntimeError('Missing actual installed-wheel provenance: '+str(key))
        name,sha=known[key]; lines.append(f'{name}=={row["version"]} --hash=sha256:{sha}')
    text='\n'.join(lines)+'\n'
    for p in [ROOT/'work/setup'/lock,ROOT/'outputs/reports'/lock]: p.write_text(text,encoding='utf-8')
    print(env,len(lines)-1,'packages pinned with SHA256')
