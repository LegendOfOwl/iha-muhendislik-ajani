from prepare import ROOT,BASE,read,save,sha,now
from pathlib import Path
import shutil
def main():
    taskpath=ROOT/read(BASE/'task.json')['path'];task=read(taskpath);archive=ROOT/'outputs/data/task_evidence'/task['id']/'code';archive.mkdir()
    files=list(BASE.glob('*.py'))+list(BASE.glob('*.ps1'))+[ROOT/'work/tmr_m6_20261025/common.py'];records=[]
    for p in files:
        dest=archive/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        records.append({'source':str(p.relative_to(ROOT)),'archive':str(dest.relative_to(ROOT)),'sha256':sha(dest)})
    manifest=ROOT/'outputs/reports/flatplate_code_snapshot_20261025.json'
    save(manifest,{'created_utc':now(),'files':records,'native_executable_sha256':sha(Path(read(ROOT/'work/setup/su2_install.json')['executable'])),
        'note':'Actual input cfg, mesh and restart sealed separately. Historical rejected/postprocessing scripts preserved; code snapshots are not physical qualification.'})
    dest=archive.parent/manifest.name;shutil.copyfile(manifest,dest);task['evidence'].append({'path':str(manifest.relative_to(ROOT)),'sha256':sha(manifest),'archived':str(dest.relative_to(ROOT))});save(taskpath,task)
    for taskname in [taskpath,ROOT/'outputs/data/tasks/20261025-011533-2114a3.json']:
        t=read(taskname)
        for e in t['evidence']:assert sha(ROOT/e['path'])==e['sha256']==sha(ROOT/e['archived'])
    print({'code_files_archived':len(records),'task_evidence_archives_verified':2})
if __name__=='__main__':main()
