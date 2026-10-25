from common import ROOT,BASE,CASE,PROJECT,TASK,read,save,sha,now
import shutil
import sys

lessons=ROOT/'.agents/skills/iha-muhendislik/references/operational_lessons.json'
old=read(lessons);assert 'L10' not in {x['id'] for x in old['lessons']}
checks=read(PROJECT/'reports/tmr_mesh_guards_20261025.json');assert checks['passed']
bad=CASE/'flow_smoke';good=CASE/'flow_v2_smoke'
assert read(bad/'prediction_frozen.json')['native_status']['exit_code']!=0
assert read(good/'prediction_frozen.json')['native_status']['exit_code']==0
history=BASE/'instruction_history';history.mkdir(exist_ok=True)
shutil.copyfile(lessons,history/'operational_lessons_before.json')
before=sha(lessons)
old['version']='2026-10-25.1'
old['lessons'].append({'id':'L10','trigger':'SU2 SA varyantını başka kaynak modeline eşleme',
    'scope':'SU2v8.5.0 standart SA-neg; diğer SA varyantlarına genelleme yok',
    'action':'Model adını tek anahtarla eşleşmiş sayma. Bu sürümde standart SA-neg için SA_OPTIONS=NEGATIVE,WITHFT2 gerekir; NEGATIVE tek başına native parser tarafından standart dışı sayılır. Kaynakta standart model isteniyorsa EXPERIMENTAL ile hatayı bypass etme. Kurulu sürüm dokümanı/koduyla terimleri ve FREESTREAM_NU_FACTOR anlamını kontrol et; pahalı koşudan önce küçük native ön kontrol yap.',
    'knowledge_status':'confirmed_error_and_native_counterexample_tested'})
save(lessons,old)
ledger={'version':'2026-10-25.tmr1','created_utc':now(),'scope':'One configuration mapping defect and postprocessing distinctions; no expert or unseen LLM improvement claim',
        'previous_ledger':'outputs/data/agent_learning/reviewer_ledger_v2_20261025.json',
        'observed_error':'Intended standard SA-neg configured as NEGATIVE alone; native parser refused before any flow field.',
        'behavioural_cause_inference':'Mapped model name to one option without checking the coupled ft2 requirement before the first parser test.',
        'correction':'Official variant definition matched with NEGATIVE,WITHFT2; no EXPERIMENTAL override; rejected config and seal retained.',
        'counterexample':'Same20step mesh/physics/config except SA_OPTIONS; old rejected, corrected native run exited0 and produced matched field19.',
        'evidence':{str(p.relative_to(ROOT)):sha(p) for p in [bad/'prediction_frozen.json',good/'prediction_frozen.json',PROJECT/'reports/tmr_mesh_guards_20261025.json',BASE/'sources/SU2_physical_definition.html']},
        'lesson_id':'L10','instructions_before_sha256':before,'instructions_after_sha256':sha(lessons),
        'additional_records':[{'type':'visualization','observed':'Default VTK cutter introduced triangle diagonals in a hex cut view. Original figure retained; polygon cuts selected and unit-cube4vs5edge counterexample passed.'},
                              {'type':'force_postprocessing','observed':'Quad face diagonal integration and bilinear interpolation define different surface quadrature; all estimates retained. No native field changed.'},
                              {'type':'wrapper','observed':'Coarsener succeeded; summary expected an uncopied fine SU2 file. Finalization recovered from completed outputs without rerunning native coarsening.'}],
        'physical_root_cause_identified':False,'LLM_behaviour_improvement_tested':False,'expert_status':False}
save(ROOT/'outputs/data/agent_learning/reviewer_ledger_tmr_20261025.json',ledger)
sys.path.insert(0,str(ROOT/'work/agent'))
from learning import instruction_snapshot
task=read(TASK);task['agent_instruction_snapshot_after_correction']=instruction_snapshot(ROOT)
task['applied_lesson_ids'].append('L10');save(TASK,task)
print('Scoped standard SA-neg lesson recorded; no physical qualification claim')
