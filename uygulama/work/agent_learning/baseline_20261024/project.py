"""Project entry point: trace tasks, run real tools, preserve evidence, launch Codex."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'
DATA=OUT/'data/project'
PHASES=['Gereksinimler ve kabul ölçütleri','Girdi, kaynak ve belirsizlik kaydı',
        'Bileşen kütle bütçesi','Kanat ve düşük hız taraması','Sürükleme, güç, enerji ve süre',
        'Yerleşim, CG, trim, kararlılık ve yapı','Tutarlılık, duyarlılık ve belirsizlik',
        'Aday karşılaştırması ve gereksinim kanıtları']
SUITES={
    'core':('.venv','work/tests/run_checks.py','outputs/reports/test_results.json'),
    'native':('.venv','work/native/run_all.py','outputs/reports/external_test_summary.json'),
    'fem':('.venv-cad','work/fem/run_fem.py','outputs/reports/fem_results.json'),
    'models':('.venv-cad','work/models/benchmark.py','outputs/reports/cad_model_benchmark.json'),
    'study':('.venv','work/studies/wing_study.py','outputs/reports/wing_study_results.json'),
    'k-family':('.venv-cad','work/models/k_family_study.py','outputs/reports/k_family_study.json'),
    'cad-parts':('.venv-cad','work/models/k_family_transfer.py','outputs/reports/k_family_new_tasks.json'),
    'model-usage':('.venv-cad','work/models/audit_usage.py','outputs/reports/model_usage_audit.json'),
    'geometry':('.venv-cad','work/geometry/parametric_wing.py','outputs/reports/parametric_cad_qualification.json'),
    'complex-vlm':('.venv','work/qualification/run_complex_vlm.py','outputs/reports/complex_vlm_qualification.json'),
    'cfd':('.venv','work/qualification/run_cfd_with_outputs.py','outputs/reports/cfd_qualification.json'),
    'elmer-cfd':('.venv-cad','work/qualification/run_elmer_cfd.py','outputs/reports/elmer_cfd_qualification.json'),
    'comparison':('.venv','work/workflow/rank_candidates.py','outputs/reports/candidate_comparison.json'),
    'profile-cfd':('.venv-cad','work/qualification/profile_cfd.py','outputs/reports/profile_cfd_results.json'),
    'aerostruct':('.venv','work/openaerostruct/run_examples.py','outputs/reports/openaerostruct_examples.json'),
}
def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    tmp.replace(path)
def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def inputs(): return {str(p.relative_to(ROOT)):digest(p) for p in sorted(DATA.glob('*.json'))}
def make_task(title,kind='engineering',project_id=None):
    task={'id':datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6],
          'request':title,'kind':kind,'created_utc':now(),'status':'bekliyor',
          'phase':'kavramsal' if kind=='engineering' else 'araç entegrasyonu',
          'acceptance':[],'blocked_by':[],'evidence':[],'input_sha256':inputs()}
    if project_id is not None:
        import projects
        project=projects.get(project_id);task.update(project_id=project_id,project_manifest=str((projects.STORE/(project_id+'.json')).relative_to(ROOT)),
            project_data_root=project['data_root'],project_output_root=project['artifact_root'])
        task['input_sha256']={str(p.relative_to(ROOT)):digest(p) for p in sorted(projects.resolve(project['data_root']).glob('*.json'))}
        task['project_snapshot']=project
        task['input_sha256'][task['project_manifest']]=digest(ROOT/task['project_manifest'])
        active=project.get('active_cad')
        if active:
            model=projects.checked_file(project_id,active['path']);task['input_sha256'][active['path']]=digest(model)
            task['active_cad_changed_since_selection']=digest(model)!=active['sha256']
    path=OUT/'data/tasks'/(task['id']+'.json'); write(path,task)
    return path
def doctor():
    cfg=read(ROOT/'work/setup/tool_config.json')
    entries={k:cfg.get(k) for k in ['numeric_python','cad_python','codex_cli','node','git']}
    for name in ['openvsp','xfoil','freecad','cad_model','k_model','cadmonkey32','su2','elmer']:
        p=ROOT/'work/setup'/(name+'_install.json')
        if p.exists():
            meta=read(p)
            candidates=meta.get('executables',{})
            if meta.get('executable'): candidates[name]=meta['executable']
            if name=='cad_model': candidates['runtime']=str(Path(meta['runtime_directory'])/'llama-cli.exe')
            if name=='cadmonkey32': candidates['model']=meta['model_path']
            for key,value in candidates.items(): entries[name+':'+key]=value
    result={'timestamp':now(),'project_root':str(ROOT),'tools':[
        {'tool':key,'path':value,'exists':bool(value) and Path(value).exists()} for key,value in entries.items()],
        'note':'Dosya varlığı çalışma veya fiziksel doğrulama değildir; test raporları ayrıca izlenir.'}
    result['all_paths_present']=all(a['exists'] for a in result['tools'])
    write(OUT/'reports/tool_health.json',result)
    return result
def status():
    mission=read(DATA/'mission.json')
    missing=[key for key,a in mission['inputs'].items() if a.get('value') is None]
    budget=read(DATA/'mass_budget.json')
    unknown_mass=[a['component'] for a in budget['components'] if a.get('mass_kg') is None]
    results=[]
    for name,(_,_,report) in SUITES.items():
        if (ROOT/report).exists():
            obj=read(ROOT/report)
            results.append({'suite':name,'report':report,'passed':obj.get('passed',obj.get('all_requested_groups_passed')),
                            'quality_passed':obj.get('quality_passed'),
                            'timestamp':obj.get('timestamp',obj.get('generated_utc',obj.get('started_local')))})
        else: results.append({'suite':name,'report':report,'passed':None})
    tasks=[read(p) for p in sorted((OUT/'data/tasks').glob('*.json'))]
    for task in tasks:
        for step in task.get('pipeline_steps',[]):
            if step['status'] not in ['bekliyor','çalışıyor','tamamlandı','uygulanmıyor','engelli']:
                raise ValueError('Geçersiz görev adımı durumu: '+str(step))
            if step['status']=='tamamlandı' and not step.get('evidence'):
                raise ValueError('Tamamlanan görev adımı için kanıt gerekli: '+step['name'])
            if step['status']=='uygulanmıyor' and not step.get('reason'):
                raise ValueError('Atlanan görev adımı için gerekçe gerekli: '+step['name'])
    phase_file=DATA/'conceptual_steps.json'
    if not phase_file.exists():
        write(phase_file,[{'step':i+1,'title':title,'status':'bekliyor',
            'reason':'Güncel proje verisi ve bu adıma ait kanıt henüz kaydedilmedi.','evidence':[]} for i,title in enumerate(PHASES)])
    phases=read(phase_file)
    for phase in phases:
        if phase['status'] not in ['bekliyor','tamamlandı','uygulanmıyor']: raise ValueError('Geçersiz aşama durumu')
        if phase['status']=='tamamlandı' and not phase['evidence']: raise ValueError('Tamamlanan aşamanın kanıtı olmalı')
        if phase['status']=='uygulanmıyor' and not phase.get('reason'): raise ValueError('Uygulanmıyor gerekçesi eksik')
    result={'timestamp':now(),'scope':'Mühendislik araçları ve iş akışı; gerçek İHA aşamaları aşağıda ayrı izlenir.',
            'aircraft_feasibility':'henüz değerlendirilemedi','missing_mission_inputs':missing,
            'unknown_component_masses':unknown_mass,
            'conceptual_steps':phases,
            'tool_tests':results,'tasks':tasks}
    write(OUT/'reports/project_status.json',result)
    lines=['# İHA mühendislik projesi — durum', '',result['scope'],'',
           '**Uçak fizibilitesi: henüz değerlendirilemedi.**','',
           'Görev vermek için `Muhendislik-Merkezi.exe` aç ve projeni seç. Bu sohbetten de aynı klasörde çalışabiliriz.','',
           '## Gerçek proje verisi','',
           'Eksik görev girdileri: '+', '.join(missing),
           'Kütlesi bilinmeyen bileşenler: '+', '.join(unknown_mass),'',
           '## Kavramsal aşama','',
           '| Adım | Durum |','|---|---|']
    lines += [f'| {a["step"]}. {a["title"]} | {a["status"]} |' for a in phases]
    lines += ['', '## Araçların son test kayıtları','','| Grup | Sonuç | Rapor |','|---|---|---|']
    for a in results:
        label='geçti' if a['passed'] is True else ('başarısız' if a['passed'] is False else 'kayıt bekleniyor')
        if a.get('quality_passed') is False: label='çalışıyor; tüm kabul ölçütleri sağlanmadı'
        lines.append(f'| {a["suite"]} | {label} | [{Path(a["report"]).name}]({Path(a["report"]).name}) |')
    lines += ['','## Görevler','']
    lines += [f'- {a["id"]}: {a["request"]} — {a["status"]}' for a in tasks] or ['Henüz görev kaydı yok.']
    (OUT/'reports/proje_durumu.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    from report import render
    render(result)
    return result
def run_suite(name,project_id='qualification'):
    import projects
    projects.bootstrap();plan=projects.run_plan(project_id,name)
    if not plan['ready']:
        print('Bu proje için hazır değil: '+plan['reason'],file=sys.stderr);return 2
    output_root=Path(plan['output_root'])
    env,script,report=SUITES[name]
    report_path=ROOT/report if project_id=='qualification' else output_root/'reports'/Path(report).name
    folder=ROOT/'work/agent/runs'/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+name+'-'+uuid.uuid4().hex[:4])
    folder.mkdir(parents=True)
    manifest={'suite':name,'project_id':project_id,'output_root':str(output_root),'started_utc':now(),'inputs':inputs() if project_id=='qualification' else {},
              'script':script,'script_sha256':digest(ROOT/script),'log':str(folder/'run.log')}
    if name=='study': manifest['inputs']['outputs/data/wing_study_case.json']=digest(OUT/'data/wing_study_case.json')
    if name in ['geometry','complex-vlm']:
        case=output_root/'data/parametric_wing_case.json';cfg=read(case)
        for path in [case,ROOT/cfg['airfoil']]: manifest['inputs'][str(path.relative_to(ROOT))]=digest(path)
    if name=='profile-cfd':
        case=output_root/'data/profile_cfd_case.json';cfg=read(case)
        for path in [case,ROOT/cfg['airfoil']]:manifest['inputs'][str(path.relative_to(ROOT))]=digest(path)
    if name=='cfd': manifest['inputs']['source_manifest']=digest(ROOT/'work/qualification/sources/source_manifest.json')
    if name=='aerostruct':manifest['inputs']['source_manifest']=digest(ROOT/'work/openaerostruct/sources/manifest.json')
    write(folder/'manifest.json',manifest)
    environment=dict(os.environ);environment.update(UAV_OUTPUT_ROOT=str(output_root),UAV_PROJECT_ID=project_id)
    with (folder/'run.log').open('w',encoding='utf-8') as log:
        proc=subprocess.Popen([str(ROOT/env/'Scripts/python.exe'),'-X','utf8',str(ROOT/script)],cwd=ROOT,
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',
             creationflags=subprocess.CREATE_NO_WINDOW,env=environment)
        for line in proc.stdout:
            print(line,end='',flush=True); log.write(line); log.flush()
        code=proc.wait()
    result=read(report_path) if report_path.exists() else {}
    # Require a report produced by this run, not an older passing report.
    fresh=report_path.exists() and report_path.stat().st_mtime >= (folder/'manifest.json').stat().st_mtime-1
    manifest.update(finished_utc=now(),exit_code=code,report=str(report_path.relative_to(ROOT)),
        report_sha256=digest(report_path) if fresh else None,
        passed=code==0 and fresh and result.get('passed',result.get('all_requested_groups_passed')) is True,
        quality_passed=result.get('quality_passed') if fresh else None)
    if fresh:
        frozen=folder/'report.json'; shutil.copyfile(report_path,frozen)
        manifest['report_archive']=str(frozen.relative_to(ROOT))
    write(folder/'manifest.json',manifest)
    status()
    if manifest['passed'] and manifest['quality_passed'] is False:
        print('Araç çalışması tamamlandı; tüm kalite kabul ölçütleri sağlanmadı. Açık kontrolleri rapordan incele.',flush=True)
    elif manifest['passed']: print('Araç çalışması ve bu raporun kontrolleri tamamlandı. Kapsam sınırları raporda.',flush=True)
    return 0 if manifest['passed'] else 1
def launch(task_path,dry=False):
    path=Path(task_path).resolve()
    if not path.is_relative_to(OUT/'data/tasks'): raise ValueError('Görev dosyası outputs/data/tasks altında olmalı.')
    task=read(path)
    cfg=read(ROOT/'work/setup/tool_config.json')
    cli=Path(cfg['codex_cli'])
    if not cli.exists():
        candidates=list(Path(os.environ.get('LOCALAPPDATA','')) .glob('OpenAI/Codex/bin/*/codex.exe'))
        if not candidates: raise FileNotFoundError('Codex uygulaması bulunamadı; sağlık raporunu kontrol et.')
        cli=max(candidates,key=lambda p:p.stat().st_mtime)
    prompt=('AGENTS.md, PROJECT_STATE.md ve .agents/skills/iha-muhendislik/SKILL.md dosyalarını oku. '
            f'Görev kaydı: {path.relative_to(ROOT)}. Bu kayıttaki isteği araçları gerçekten çalıştırarak tamamla. '
            'Eksik kritik veriyi uydurma; bağımsız işleri sürdür. Girdi, ham çıktı, kontrol, sınırlama ve raporu kaydet. '
            'Görev durumunu ve kanıt bağlantılarını güncelle. Kullanıcı isteği: '+task['request'])
    if task.get('structured_request'):
        prompt+=(' Yapılandırılmış kullanıcı kısıtları ve araştırma/CAD/ön analiz/CFD/eleme/rapor kabul sözleşmesi '
            +task['structured_request']+' dosyasındadır. Dosyayı oku; bilinmeyeni sıfır sayma. '
            'Önce tanımlı tasarım alanını ve aday bütçesini kur; tüm ihtimallerin tüketildiğini iddia etme. '
            'Geometri ve koşulları uyuşmayan eski CFD sonucunu yeni adaya aktarma. Kalite kabulü açık adayları nihai kazanan diye sunma.')
        prompt+=' Görev kaydındaki pipeline_steps durumlarını ve her tamamlanan adımın kanıtını güncelle; uygulanmayan adımın gerekçesini yaz.'
    if task.get('project_manifest'):
        prompt+=(' Seçili mühendislik projesinin manifesti: '+task['project_manifest']+'. Önce bunu oku. '
            'Bu görevin gerçek girdileri '+task['project_data_root']+'; CAD, analiz ve raporları '+task['project_output_root']+' altına yaz. '
            'Diğer projelerin veya araç yeterlilik örneklerinin sonuçlarını bu projeye aitmiş gibi kullanma. '
            'Hazır destekli analizler için work/agent/project.py run GRUP --project '+task['project_id']+' kullan; hazırlanmış girdi yoksa kullanıcıya ait varsayımlar üretme.')
    command=[str(cli),'--cd',str(ROOT),'--search','--sandbox','workspace-write','--ask-for-approval','on-request',prompt]
    if dry: return {'executable':str(cli),'cwd':str(ROOT),'task':str(path),'prompt':prompt}
    task['status']='çalışıyor'; write(path,task)
    subprocess.Popen(command,cwd=ROOT,creationflags=subprocess.CREATE_NEW_CONSOLE)
    return {'launched':True,'task':task['id']}
def main():
    p=argparse.ArgumentParser(description='İHA mühendislik projesi')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('status'); sub.add_parser('doctor')
    r=sub.add_parser('run'); r.add_argument('suite',choices=SUITES);r.add_argument('--project',default='qualification')
    t=sub.add_parser('task'); t.add_argument('title'); t.add_argument('--kind',default='engineering');t.add_argument('--project')
    a=sub.add_parser('agent'); a.add_argument('task_file'); a.add_argument('--dry-run',action='store_true')
    s=sub.add_parser('submit'); s.add_argument('request_file'); s.add_argument('--dry-run',action='store_true')
    s.add_argument('--save-only',action='store_true')
    args=p.parse_args()
    if args.command=='run': return run_suite(args.suite,args.project)
    if args.command=='status': obj=status(); print('Kavramsal aşama: güncel girdiler ve bileşen kütleleri bekleniyor.'); print(OUT/'reports/proje_durumu.md'); return 0
    if args.command=='doctor': obj=doctor()
    if args.command=='task': obj={'task_file':str(make_task(args.title,args.kind,args.project))}
    if args.command=='agent': obj=launch(args.task_file,args.dry_run)
    if args.command=='submit':
        request=read(args.request_file)
        project_id=request.get('project_id','iha')
        import projects
        projects.bootstrap();projects.get(project_id)
        if not isinstance(request.get('request'),str) or not request['request'].strip(): raise ValueError('Görev boş olamaz.')
        if 'constraints' in request:
            from intake import normalize
            try: request=normalize(request)
            except (ValueError,TypeError) as exc:
                print('Girdi düzeltilmeli: '+str(exc),file=sys.stderr); return 2
        path=make_task(request['request'].strip(),request.get('kind','engineering'),project_id)
        if request.get('schema_version')==1:
            rp=OUT/'data/requests'/(path.stem+'.json'); write(rp,request)
            task=read(path); task.update(structured_request=str(rp.relative_to(ROOT)),
                structured_request_sha256=digest(rp),acceptance=request['acceptance'],
                requested_pipeline=request['pipeline'],candidate_limit=request['candidate_limit'],cfd_candidate_limit=request['cfd_candidate_limit'],
                pipeline_steps=[{'name':name,'status':'bekliyor','evidence':[],'reason':None} for name in request['pipeline']])
            write(path,task)
        obj={'task_file':str(path),'saved':True} if args.save_only else launch(path,args.dry_run)
        status()
    print(json.dumps(obj,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': sys.exit(main())
