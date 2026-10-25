"""Version the operational instructions used by the existing GUI/CLI launcher."""
import hashlib
import json
from pathlib import Path


def instruction_snapshot(root):
    root = Path(root).resolve()
    base = Path('.agents/skills/iha-muhendislik')
    paths = [Path('AGENTS.md'), base / 'SKILL.md',
             base / 'references/learning_loop.md',
             base / 'references/operational_lessons.json']
    lessons = json.loads((root / paths[-1]).read_text(encoding='utf-8'))
    policy=Path('work/reliability/protocol_v1.json')
    if (root/policy).exists():paths.append(policy)
    snapshot = {
        'version': lessons['version'],
        'files': {p.as_posix(): hashlib.sha256((root / p).read_bytes()).hexdigest()
                  for p in paths},
        'expert_qualification': 'not_established',
        'blind_analysis_safe': False,
    }
    if (root/policy).exists():
        snapshot['reliability_policy_version']=json.loads((root/policy).read_text(encoding='utf-8'))['version']
    return snapshot
