from common import ROOT,BASE,PROJECT,TASK,read,save,sha,now
import shutil
import sys

path=ROOT/'.agents/skills/iha-muhendislik/references/operational_lessons.json';lessons=read(path)
assert 'L11' not in {x['id'] for x in lessons['lessons']}
evidence=PROJECT/'reports/tmr_source_CAD_boundary_v2_20261025.json';audit=read(evidence)
assert audit['analytic_counterexample']['solid_interior_distance']==0
assert audit['analytic_counterexample']['boundary_distance']==.5
shutil.copyfile(path,BASE/'instruction_history/operational_lessons_after_L10.json');before=sha(path)
lessons['version']='2026-10-25.2'
lessons['lessons'].append({'id':'L11','trigger':'CAD yüzeyi ile mesh/nokta/temsil eşdeğerliği mesafesi',
    'scope':'OCC/CadQuery katı–nokta mesafe sorgusu; yüzey eşdeğerliği amaçlı denetim',
    'action':'Katıya mesafe, içerideki nokta için0 olabilir; bunu yüzeyde olma kanıtı sayma. Yüzey uzaklığını yalnız sınır yüzlerinden kurulan shell/compound üzerinde ölç. Önce birim küp merkezinin katıya0, sınıra0.5 mesafe verdiği analitik karşı örneği doğrula. Düğümlere ek olarak yüzey parçası içi ve kenar örneklerini de denetle; sonlu örneklemeyi tam Hausdorff sınırı diye sunma. Önceki geçersiz ölçümü ve hangi çıktıyı etkilediğini koru.',
    'knowledge_status':'confirmed_error_and_analytic_surface_counterexample_tested'})
save(path,lessons)
save(ROOT/'outputs/data/agent_learning/reviewer_ledger_tmr_surface_20261025.json',{
    'version':'2026-10-25.tmr2','created_utc':now(),'prior_ledger_sha256':sha(ROOT/'outputs/data/agent_learning/reviewer_ledger_tmr_20261025.json'),
    'observed_error':'First CAD checks used a solid-containing compound; interior points were classified at distance0 and surface gap understated.',
    'behavioural_cause_inference':'Treated a successful geometric distance API query as the requested surface metric without an inside-point counterexample.',
    'correction':'Use compound of source boundary faces; compare vertices, facet centers and edge midpoints; retain invalid earlier records.',
    'counterexample':audit['analytic_counterexample'],'evidence_sha256':sha(evidence),
    'native_solver_and_source_mesh_unchanged':True,'instruction_before_sha256':before,'instruction_after_sha256':sha(path),
    'lesson_id':'L11','LLM_behaviour_improvement_tested':False,'minimum_physical_qualification_passed':False,
    'reference_access_disclosure':{'event_utc':'2026-10-24T22:58:19+00:00',
        'event':'A metadata-only filter printed commented numerical CFD force rows while the fixed fine baseline was still running.',
        'not_blind_before_event':True,'subsequent_solver_configs_or_thresholds_changed':False,
        'effect':'This is development/review evidence, not a blind or unseen-agent benchmark. All new reference comparison code waits for baseline prediction seals.'}})
sys.path.insert(0,str(ROOT/'work/agent'));from learning import instruction_snapshot
t=read(TASK);t['agent_instruction_snapshot_after_surface_correction']=instruction_snapshot(ROOT)
t['applied_lesson_ids'].append('L11');save(TASK,t)
print('Scoped surface-distance lesson recorded; native fields unchanged')
