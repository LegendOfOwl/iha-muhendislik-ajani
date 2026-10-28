"""Preserve the completed mesh research as structured provenance; no CFD."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent


def main():
    md = BASE / 'validation_mesh.md'
    text = md.read_text(encoding='utf-8')
    links = re.findall(r'\[([^\]]+)\]\(([^\s)]+)\)', text)
    urls = {}
    evidence = {}
    for title, target in links:
        if target.startswith('https://'):
            urls.setdefault(target, title)
        elif not target.startswith('#'):
            path = (BASE / target).resolve()
            assert path.is_relative_to(ROOT) and path.is_file(), target
            evidence[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = []
    for line in text.splitlines():
        if re.match(r'\| [1-9] / P', line):
            cells = [s.strip() for s in line.strip('|').split('|')]
            rows.append({'id': 'VM%02d' % (len(rows) + 1), 'priority': cells[0].split('/')[1].strip(),
                         'problem': cells[1], 'impact': cells[2], 'next_test': cells[3]})
    assert len(rows) == 9 and len(urls) == 10
    result = {'schema': 'mesh_validation_research_v1', 'research_date_local': '2026-10-28',
        'compiled_from': md.relative_to(ROOT).as_posix(), 'markdown_sha256': hashlib.sha256(md.read_bytes()).hexdigest(),
        'provenance': 'Structured by parent from the completed specialist Markdown after specialist capacity interruption; no new claim of independent CFD or source reproduction.',
        'problems': rows, 'local_evidence_sha256': evidence,
        'sources': [{'id': 'V%02d' % (i + 1), 'title': title, 'url': url,
                     'accessed_date': '2026-10-28', 'reading_scope': 'Primary-source analysis retained in validation_mesh.md; not every method reproduced',
                     'source_class': 'author paper or official documentation'} for i, (url, title) in enumerate(urls.items())],
        'new_native_runs': 0, 'new_builds': 0, 'new_installations': 0,
        'physical_qualification_passed': False, 'M6_qualification_passed': False,
        'LLM_improvement_demonstrated': False,
        'latest_case_roles': {'TMR_flatplate': 'reduced_family_review_20261026; source-cap arms are separate diagnostics',
            'RAE2822': 'v3 batch closure; v2 narrow screens remain historical',
            'M6': 'TMRsharp source three-grid case; old blunt source-grid results are separate'},
        'unexecuted_new_control': 'Independent native-wall-distance versus global surface-distance audit; not a diagnosed local bug'}
    (BASE / 'validation_mesh.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print({'mesh_problems': len(rows), 'sources': len(urls), 'local_evidence_files': len(evidence)})


if __name__ == '__main__':
    main()
