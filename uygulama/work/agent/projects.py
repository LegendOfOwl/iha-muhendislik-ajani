"""Logical engineering projects; scoped files/tasks and explicit prepared analysis inputs."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid
ROOT=Path(__file__).resolve().parents[2]
STORE=ROOT/'outputs/data/projects'
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.'+uuid.uuid4().hex+'.tmp')
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');t.replace(p)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def resolve(value):
    p=(ROOT/value).resolve()
    if not p.is_relative_to(ROOT.resolve()):raise ValueError('Yol çalışma alanı dışında')
    return p
def bootstrap():
    STORE.mkdir(parents=True,exist_ok=True)
    for id,name,kind,artifact,data in [('qualification','Araç doğrulama örnekleri','qualification','outputs','outputs/data/qualification'),
            ('iha','İHA projem','engineering','outputs/projects/iha','outputs/data/project')]:
        p=STORE/(id+'.json')
        if not p.exists():
            write(p,{'id':id,'name':name,'kind':kind,'artifact_root':artifact,'data_root':data,'created_utc':now(),'active_cad':None})
        elif id=='qualification' and read(p)['data_root']=='outputs/data/project':
            current=read(p);current['data_root']=data;write(p,current)
        setup(read(p))
def setup(p):
    root=resolve(p['artifact_root'])
    for sub in ['cad','data','reports','simulations','plots']:(root/sub).mkdir(parents=True,exist_ok=True)
    resolve(p['data_root']).mkdir(parents=True,exist_ok=True)
def get(id):
    if not isinstance(id,str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',id):raise ValueError('Geçersiz proje kimliği')
    p=STORE/(id+'.json')
    if not p.exists():raise ValueError('Proje bulunamadı: '+id)
    obj=read(p);resolve(obj['artifact_root']);resolve(obj['data_root']);return obj
def create(name,kind='engineering'):
    if not isinstance(name,str) or not name.strip() or len(name.strip())>80:raise ValueError('Proje adı 1–80 karakter olmalı')
    if kind not in ['engineering','qualification']:raise ValueError('Geçersiz proje türü')
    id='proje-'+uuid.uuid4().hex[:10];root='outputs/projects/'+id
    p={'id':id,'name':name.strip(),'kind':kind,'artifact_root':root,'data_root':root+'/data/project','created_utc':now(),'active_cad':None}
    setup(p);write(STORE/(id+'.json'),p)
    # Fresh unknowns, never copy an old test case into a user's design.
    for name in ['mission.json','mass_budget.json','conceptual_steps.json']:
        src=ROOT/'outputs/data/project'/name
        if src.exists():
            blank=read(src)
            if name=='mission.json':
                for x in blank.get('inputs',{}).values():x.update(value=None,status='bilinmiyor',source=None)
                blank.update(requirements=[],conflicts=[])
            elif name=='mass_budget.json':
                for x in blank.get('components',[]):
                    x['mass_kg']=None
                    if 'status' in x:x['status']='bilinmiyor'
                    if 'source' in x:x['source']=None
                    if 'range_kg' in x:x['range_kg']=None
            else:
                for x in blank:x.update(status='bekliyor',evidence=[],reason='Bu projeye ait kanıt henüz yok.')
            write(resolve(p['data_root'])/name,blank)
    return p
def list_projects():
    return sorted([get(p.stem) for p in STORE.glob('*.json')],key=lambda p:(p['kind']=='qualification',p['created_utc']))
def draft_path(id):get(id);return ROOT/'work/agent/project_ui/drafts'/(id+'.json')
def save_draft(id,payload):
    if payload.get('project_id',id)!=id:raise ValueError('Taslak başka projeye ait')
    write(draft_path(id),payload);return {'saved':True,'project_id':id}
def draft(id):
    p=draft_path(id);return read(p) if p.exists() else {'project_id':id,'request':'','constraints':{},'options':{'candidate_limit':6,'cfd_candidate_limit':3}}
def files(id):
    p=get(id);root=resolve(p['artifact_root']);items=[]
    groups=[('CAD',root/'cad'),('Rapor',root/'reports'),('Alan / analiz',root/'simulations'),('Görsel',root/'plots'),('Girdi',resolve(p['data_root']))]
    for label,folder in groups:
        paths=folder.glob('*') if label in ['Rapor','Görsel','Girdi'] else folder.rglob('*')
        candidates=sorted([s for s in paths if s.is_file()],key=lambda s:s.stat().st_mtime,reverse=True)
        if label=='Alan / analiz':candidates=[s for s in candidates if s.suffix.lower() in ['.pos','.vtu','.su2','.msh','.sif','.cfg','.csv','.log','.json']]
        for f in candidates[:160]:
            if not f.resolve().is_relative_to(folder.resolve()):continue
            items.append({'group':label,'name':f.name,'path':str(f.relative_to(ROOT)),'full_path':str(f),'bytes':f.stat().st_size,'modified':f.stat().st_mtime})
    known={i['path'] for i in items}
    for f in sorted((root/'data').glob('*')):
        if f.is_file() and f.suffix.lower() in ['.json','.dat'] and str(f.relative_to(ROOT)) not in known:
            items.append({'group':'Girdi','name':f.name,'path':str(f.relative_to(ROOT)),'full_path':str(f),'bytes':f.stat().st_size,'modified':f.stat().st_mtime})
    return items
def checked_file(id,value):
    p=get(id);f=resolve(value)
    allowed=[resolve(p['artifact_root'])/s for s in ['cad','reports','simulations','plots','data']]+[resolve(p['data_root'])]
    if not f.is_file() or not any(f.is_relative_to(a.resolve()) for a in allowed):raise ValueError('Dosya seçili projeye ait değil')
    if id=='qualification' and f.is_relative_to((ROOT/'outputs/data/project').resolve()):raise ValueError('Bu girdi gerçek İHA projesine aittir')
    return f
def active_cad(id,value):
    p=get(id);f=checked_file(id,value)
    if not f.is_relative_to((resolve(p['artifact_root'])/'cad').resolve()):raise ValueError('Aktif CAD, projenin CAD klasöründe olmalı')
    if f.suffix.lower() not in ['.step','.stp','.fcstd','.vsp3','.brep','.stl','.iges','.igs']:raise ValueError('Aktif CAD için bir model dosyası seç')
    p['active_cad']={'path':str(f.relative_to(ROOT)),'sha256':sha(f),'selected_utc':now()};write(STORE/(id+'.json'),p);return p

def cad_tool(id,value):
    if value not in ['auto','freecad','openvsp']:raise ValueError('Bu CAD programı henüz bağlanmadı')
    p=get(id);p['cad_tool']=value;write(STORE/(id+'.json'),p);return p
def import_file(id,source):
    p=get(id);src=Path(source).resolve()
    if not src.is_file():raise ValueError('Kaynak dosya bulunamadı')
    if src.suffix.lower() not in ['.step','.stp','.fcstd','.vsp3','.stl','.brep','.iges','.igs','.dat','.json']:
        raise ValueError('Bu dosya türü CAD/girdi aktarımına uygun değil')
    category='data' if src.suffix.lower() in ['.dat','.json'] else 'cad'
    dest=resolve(p['artifact_root'])/category/src.name
    if src!=dest:
        if dest.exists():dest=dest.with_name(dest.stem+'-'+uuid.uuid4().hex[:6]+dest.suffix)
        shutil.copy2(src,dest)
    return {'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'project_id':id}
def run_plan(id,suite):
    p=get(id);root=resolve(p['artifact_root'])
    if id=='qualification' and suite!='profile-cfd':return {'ready':True,'output_root':str(root),'note':'Kayıtlı yeterlilik örneği'}
    needed={'geometry':'data/parametric_wing_case.json','complex-vlm':'data/parametric_wing_case.json','profile-cfd':'data/profile_cfd_case.json'}
    if suite not in needed:return {'ready':False,'reason':'Bu çözüm seçili projenin girdilerine henüz bağlanmadı; görev olarak hazırlanmalı.'}
    f=root/needed[suite]
    if not f.exists():return {'ready':False,'reason':'Önce bu projeye ait '+f.name+' tanımı hazırlanmalı.'}
    return {'ready':True,'output_root':str(root),'case':str(f),'note':'Seçili projenin hazırlanmış sayısal tanımı kullanılır; içe aktarılan her CAD otomatik analiz edilmez.'}
def summary(id):
    p=get(id);all_files=files(id);tasks=[]
    for path in (ROOT/'outputs/data/tasks').glob('*.json'):
        t=read(path)
        if t.get('project_id','qualification')==id:tasks.append({'id':t['id'],'request':t['request'],'status':t['status'],'path':str(path.relative_to(ROOT))})
    active=p.get('active_cad');changed=False
    if active:
        f=resolve(active['path']);changed=not f.exists() or sha(f)!=active['sha256']
    result={'project':p,'files':all_files,'tasks':sorted(tasks,key=lambda t:t['id'],reverse=True),
        'active_cad_changed':changed,'actions':{s:run_plan(id,s) for s in ['geometry','complex-vlm','profile-cfd','cfd','fem','elmer-cfd','comparison','aerostruct']},
        'scope_note':'Araç yeterlilik örnekleri; gerçek tasarım değildir.' if p['kind']=='qualification' else 'Yalnız bu projenin görevleri ve dosyaları. Eksik girdiler sonuç sayılmaz.'}
    return result
def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    c=sub.add_parser('new');c.add_argument('name')
    for name in ['summary','draft']:
        c=sub.add_parser(name);c.add_argument('id')
    for name in ['draft-save','active-cad','import','cad-tool']:
        c=sub.add_parser(name);c.add_argument('id');c.add_argument('file')
    c=sub.add_parser('check-file');c.add_argument('id');c.add_argument('file')
    a=parser.parse_args();bootstrap()
    if a.command=='list':r=list_projects()
    elif a.command=='new':r=create(a.name)
    elif a.command=='summary':r=summary(a.id)
    elif a.command=='draft':r=draft(a.id)
    elif a.command=='draft-save':r=save_draft(a.id,read(a.file))
    elif a.command=='active-cad':r=active_cad(a.id,a.file)
    elif a.command=='cad-tool':r=cad_tool(a.id,a.file)
    elif a.command=='import':r=import_file(a.id,a.file)
    elif a.command=='check-file':r={'full_path':str(checked_file(a.id,a.file))}
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except (ValueError,FileNotFoundError) as exc:parser_error=str(exc);print(json.dumps({'error':parser_error},ensure_ascii=False));raise SystemExit(2)
