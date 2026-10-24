"""Local metadata inventory for the explicitly requested GitHub export."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import json
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'work/publish'


def main():
    totals = defaultdict(lambda: [0, 0]); entries = []; errors = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != '.git']
        for name in files:
            path = Path(folder) / name
            try:
                stat = path.stat(); rel = path.relative_to(ROOT).as_posix()
                top = rel.split('/')[0]
                group = '/'.join(rel.split('/')[:2]) if '/' in rel else top
                totals[group][0] += 1; totals[group][1] += stat.st_size
                if top not in ('.venv', '.venv-cad', 'tools') and '__pycache__' not in path.parts:
                    entries.append({'path': rel, 'bytes': stat.st_size,
                                    'mtime_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()})
            except OSError as exc:
                errors.append({'path': str(path), 'error': type(exc).__name__})
    result = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'groups': {k: {'files': v[0], 'bytes': v[1]} for k, v in sorted(totals.items())},
              'project_files': entries, 'errors': errors}
    (OUT / 'inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    groups = sorted(result['groups'].items(), key=lambda kv: kv[1]['bytes'], reverse=True)
    print(json.dumps({'groups': groups[:20], 'project_files': len(entries),
                      'project_GiB': round(sum(x['bytes'] for x in entries) / 2**30, 3),
                      'largest_project_files': sorted(entries, key=lambda x: x['bytes'], reverse=True)[:6],
                      'errors': errors[:4]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
