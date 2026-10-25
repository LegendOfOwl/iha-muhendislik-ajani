"""Separate the new run from an old checker's hardcoded historical report path."""
from linear_pair import ROOT, TASK, read, save, sha
import shutil

src=ROOT/'outputs/reports/agent_learning_checks_20261024.json'
new=ROOT/'outputs/reports/agent_learning_checks_20261025.json'
assert not new.exists()
shutil.copyfile(src,new)
old=ROOT.parent/'iha-muhendislik-ajani/uygulama/outputs/reports/agent_learning_checks_20261024.json'
catalog=read(ROOT.parent/'iha-muhendislik-ajani/analizler/dosya_katalogu.json')
expected=next(a['sha256'] for a in catalog['files'] if a['source_path']=='outputs/reports/agent_learning_checks_20261024.json')
assert sha(old)==expected
shutil.copyfile(old,src)
assert sha(src)==expected
original=ROOT/'work/agent_learning/check_guards.py'
body=original.read_text(encoding='utf-8')
needle="'outputs/reports/agent_learning_checks_20261024.json'"
assert body.count(needle)==1
target=ROOT/'work/reliability/check_agent_guards_20261025.py'
target.write_text(body.replace(needle,"'outputs/reports/agent_learning_checks_20261025.json'"),encoding='utf-8')
record={'old_report_restored_to_publication_sha256':expected,
        'new_report':str(new.relative_to(ROOT)),'new_report_sha256':sha(new),
        'reason':'Historical checker writes a fixed dated filename. New result saved separately; old report restored byte-for-byte. New checker copy changes only output filename.',
        'original_checker_sha256':sha(original),'current_checker_sha256':sha(target)}
recordpath=ROOT/'outputs/reports/agent_guard_report_preservation_20261025.json';save(recordpath,record)
task=read(TASK)
task['evidence'] += [{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [new,recordpath]]
save(TASK,task)
print(__import__('json').dumps(record,indent=2))
