"""Verify the narrow instruction update, preserving old evidence and physics status."""
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs'
sys.path.insert(0, str(ROOT / 'work/agent'))
from learning import instruction_snapshot


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    with Path(p).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in ('href', 'src') and v)


def verify_pairs(pairs):
    return {'records': len(pairs), 'mismatches': [p for p, h in pairs if sha(ROOT / p) != h]}


def main():
    ledger = read(OUT / 'data/agent_learning/reviewer_ledger_v1.json')
    checks = read(OUT / 'reports/agent_learning_checks_20261024.json')
    snapshot = instruction_snapshot(ROOT)
    assert snapshot == checks['instruction_snapshot'] == ledger['instruction_snapshot']
    lesson_audit = verify_pairs([(r['path'], r['sha256']) for l in ledger['lessons'] for r in l['evidence']])
    preserved = []
    for ident in ['20261019-201609-ab8031', '20261024-153804-27f425']:
        task = read(OUT / 'data/tasks' / (ident + '.json'))
        pairs = [(r['path'], r['sha256']) for r in task['evidence']]
        pairs += list(task.get('reproduction_code_sha256', {}).items()) + list(task.get('input_sha256', {}).items())
        preserved.append({'task_id': ident, **verify_pairs(pairs)})
    frozen = []
    for name in ['m6_jst_prediction_frozen_20261024_v2.json', 'm6_wallnormal_prediction_frozen_20261024_v3.json']:
        data = read(OUT / 'projects/proje-e9319baef1/reports' / name)
        frozen.append({'manifest': name, **verify_pairs(list(data['files_sha256'].items()))})
    source = OUT / 'reports/ajan_hafiza_notu_20261024.md'
    target = Path('C:/Users/Urungu/.codex/memories/extensions/ad_hoc/notes/2026-10-24T140500-engineering-agent-learning-loop.md')
    memory_ok = target.is_file() and sha(source) == sha(target)
    save(OUT / 'data/agent_learning/memory_installation_20261024.json', {
        'verified_utc': datetime.now(timezone.utc).isoformat(), 'source_copy': str(source.relative_to(ROOT)),
        'installed_path': str(target), 'sha256': sha(source), 'installed_copy_matches': memory_ok,
        'registry_directly_modified': False})
    link_audits = []
    for path in [OUT / 'reports/ajan_talimat_gelisimi_20261024.html', OUT / 'Proje-Ozeti.html']:
        parser = Links(); parser.feed(path.read_text(encoding='utf-8'))
        refs = [r for r in parser.links if not urlsplit(r).scheme and not urlsplit(r).netloc and urlsplit(r).path]
        missing = [r for r in refs if not (path.parent / unquote(urlsplit(r).path)).resolve().exists()]
        link_audits.append({'path': str(path.relative_to(ROOT)), 'local_links': len(refs), 'missing': missing})
    scripts = list((ROOT / 'work/agent_learning').glob('*.py'))
    scripts += [ROOT / 'work/agent/learning.py', ROOT / 'work/agent/project.py', ROOT / 'work/agent/report.py']
    for script in scripts:
        py_compile.compile(str(script), doraise=True)
    core = read(OUT / 'reports/test_results.json')
    passed = (checks['passed'] and core['all_requested_groups_passed'] and memory_ok
              and not lesson_audit['mismatches'] and all(not x['mismatches'] for x in preserved + frozen)
              and all(not x['missing'] for x in link_audits))
    result = {'verified_utc': datetime.now(timezone.utc).isoformat(), 'passed': passed,
              'lesson_evidence': lesson_audit, 'old_task_evidence_and_code': preserved,
              'M6_frozen_predictions': frozen, 'memory_installation_matches': memory_ok,
              'HTML_links': link_audits, 'compiled_scripts': len(scripts),
              'guard_checks': checks['total'], 'core_checks': core['total_checks'],
              'instruction_snapshot': snapshot, 'expert_qualification_passed': False,
              'minimum_physical_qualification_passed': False,
              'scope': 'Evidence, instructions, launcher and software checks; no new LLM/CFD engineering validation'}
    save(OUT / 'reports/agent_learning_integrity_20261024.json', result)
    assert passed, result
    path = OUT / 'data/tasks/20261024-164603-4764e5.json'; task = read(path)
    evidence = ['outputs/reports/ajan_talimat_gelisimi_20261024.html',
                'outputs/data/agent_learning/reviewer_ledger_v1.json',
                'outputs/data/agent_learning/qualification_plan_v1.json',
                'outputs/data/agent_learning/memory_installation_20261024.json',
                'outputs/reports/ajan_hafiza_notu_20261024.md',
                'outputs/reports/agent_learning_checks_20261024.json',
                'outputs/reports/agent_learning_integrity_20261024.json',
                'outputs/reports/test_results.json']
    task.update(status='tamamlandı', phase='talimat ve araç süreci doğrulaması',
        completed_utc=datetime.now(timezone.utc).isoformat(),
        acceptance=['Hata/risk/hipotez ayrımı ve çürüyen teşhislerin korunması',
                    'Sürümlü operasyonel dersler ve mevcut başlatıcı bağlantısı',
                    'Karşı örnekler ve kalıcı hafıza kopyasının doğrulanması',
                    'Eski kanıtların ve açık uzmanlık/fizik kabullerinin korunması'],
        applied_lesson_ids=[r['id'] for r in ledger['lessons']], agent_instruction_snapshot=snapshot,
        completion_scope='İlk talimat/hafıza güncellemesi ve kod karşı örnekleri; görülmemiş LLM mühendislik kıyası yapılmadı',
        expert_qualification_passed=False, minimum_physical_qualification_passed=False,
        engineering_work_remaining=['Görülmemiş görevlerde önce/sonra LLM davranış kıyası', 'Açık RAE/M6 sayısal, ağ ve deney kapıları'],
        evidence=[{'path': p, 'sha256': sha(ROOT / p)} for p in evidence], blocked_by=[])
    save(path, task)
    print(json.dumps({'passed': passed, 'lesson_evidence': lesson_audit,
                      'preserved_tasks': preserved, 'frozen_records': sum(x['records'] for x in frozen),
                      'memory_matches': memory_ok, 'HTML_links': link_audits}, ensure_ascii=False))


if __name__ == '__main__':
    main()
