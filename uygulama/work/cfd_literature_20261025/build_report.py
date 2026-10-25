"""Render and check the research artifact and finish its scoped task record."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote
import hashlib
import html
import json
import re

ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/'outputs/reports'
MD=REPORTS/'cfd_dogrulugu_literatur_20261025.md'
HTML=MD.with_suffix('.html')
TASK=ROOT/'outputs/data/tasks/20261025-005212-dd782d.json'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def inline(text):
    text=html.escape(text)
    text=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',r'<img alt="\1" src="\2" loading="lazy">',text)
    text=re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    return re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)


def render(text):
    result=[];paragraph=[];table=False;listing=False;nav=[];heading_count=0
    def flush():
        if paragraph:
            result.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
    for line in text.splitlines()+['']:
        if not line.strip():
            flush()
            if table: result.append('</tbody></table></div>');table=False
            if listing: result.append('</ul>');listing=False
        elif line.startswith('|'):
            flush()
            cells=[x.strip() for x in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?',x) for x in cells): continue
            if not table:
                result.append('<div class="table"><table><thead><tr>'+''.join('<th>'+inline(x)+'</th>' for x in cells)+'</tr></thead><tbody>');table=True
            else: result.append('<tr>'+''.join('<td>'+inline(x)+'</td>' for x in cells)+'</tr>')
        elif line.startswith('#'):
            flush();level=len(line)-len(line.lstrip('#'));title=line[level:].strip();heading_count+=1;anchor='s'+str(heading_count)
            if level==2: nav.append((anchor,title))
            result.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
        elif line.startswith('- '):
            flush()
            if not listing:result.append('<ul>');listing=True
            result.append('<li>'+inline(line[2:])+'</li>')
        else: paragraph.append(line.strip())
    return '\n'.join(result),nav


def main():
    text=MD.read_text(encoding='utf-8')
    body,nav=render(text)
    nav_html=''.join(f'<a href="#{anchor}">{html.escape(title)}</a>' for anchor,title in nav)
    style='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f1f4f6;color:#243449;font:16px/1.7 "Segoe UI",sans-serif}main{max-width:1180px;margin:30px auto;padding:42px 54px;background:white;border:1px solid #d8e1e9;border-radius:14px}h1{font-size:32px;line-height:1.25;color:#173d54}h2{font-size:23px;color:#1a5c68;padding-top:28px;border-top:1px solid #dce6ec;scroll-margin-top:15px}h3{color:#1a5c68}p{max-width:100ch}a{color:#006c8e;overflow-wrap:anywhere}code{background:#edf3f6;padding:2px 5px;border-radius:4px}.table{overflow-x:auto;margin:22px 0}table{border-collapse:collapse;min-width:700px;width:100%;font-size:14px;line-height:1.55}th,td{text-align:left;padding:13px 15px;border-bottom:1px solid #dbe4ea;vertical-align:top}th{background:#e8f1f4;color:#173d54}tr:nth-child(even){background:#f8fafb}img{max-width:100%;height:auto;border:1px solid #dce6ec;border-radius:8px}nav{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0}nav a{font-size:13px;text-decoration:none;border:1px solid #d8e4e8;border-radius:6px;padding:5px 9px;background:#f6fafb}.scope{background:#eaf4f2;padding:13px 18px;border-left:4px solid #287f75;border-radius:4px}@media(max-width:700px){main{margin:0;padding:20px;border-radius:0}h1{font-size:27px}table{font-size:13px}}'''
    HTML.write_text('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD doğruluğu ve literatür — 25 Ekim 2026</title><style>'+style+'</style></head><body><main><div class="scope">Araştırma tamamlandı · yeni CFD koşusu yok · genel fizik yeterliliği açık</div><nav>'+nav_html+'</nav>'+body+'</main></body></html>',encoding='utf-8')
    document=HTML.read_text(encoding='utf-8')
    anchors=re.findall(r'id="([^"]+)"',document)
    assert len(anchors)==len(set(anchors))
    assert all(anchor in anchors for anchor,title in nav)

    links=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)
    local=[]
    for link in links:
        if urlparse(link).scheme or link.startswith('#'):continue
        target=(REPORTS/unquote(link.split('#')[0])).resolve()
        assert target.is_file(),str(target)
        local.append({'href':link,'sha256':sha(target)})
    facts=read(REPORTS/'cfd_literatur_yerel_kiyas_20261025.json')
    assert facts['minimum_CFD_qualification_passed'] is False
    manifest=read(ROOT/'work/cfd_literature_20261025/sources/manifest.json')
    for row in manifest:
        if row['status']=='archived':assert sha(ROOT/row['path'])==row['sha256']
    assert sum(x['Cp_RMSE']<.08 for x in read(ROOT/'outputs/projects/proje-e9319baef1/reports/m6_cfl_feedback_20261025.json')['results']['adaptive']['alternate_eta0p96']['sections'])==5

    task=read(TASK)
    for rel,expected in task['input_sha256'].items():assert sha(ROOT/rel)==expected
    task.update(status='tamamlandı',phase='kaynaklı yöntem araştırması',
                acceptance=['Birincil kaynaklar ve arXiv metinlerinin yöntem/başarı tanımlarıyla araştırılması',
                            'Yerel M6/RAE ile koşul, geometri, yöntem ve doğrulama derinliği karşılaştırması',
                            'Mevcut ham geçmiş/271 nokta CSV ve dosya mühürleriyle yerel iddiaların yeniden denetimi',
                            'Sınanmamış öneriler ve genel fizik kabulü ayrılarak uygulanabilir öncelik raporu'],
                completed_utc=datetime.now(timezone.utc).isoformat(),
                scope='Araştırma ve mevcut kanıt denetimi tamamlandı; yeni CFD, ağ üretimi veya model kurulumu yapılmadı.',
                blocked_by=[],
                engineering_open_items=['Genel M6/RAE fizik kabulü false; bölgesel ağ, yakınsama, sistematik aile, uzak alan ve deney kapıları açık.',
                                        'Resmî Fortran üreteci yalnız indirildi/incelendi; derlenmedi ve ağ üretilmedi.',
                                        'Makalelerdeki ajan sonuçları yerelde yeniden üretilmedi.'],
                agent_instruction_snapshot=facts['agent_instruction_snapshot'],applied_lesson_ids=facts['applied_lesson_ids'])
    paths=[MD,HTML,REPORTS/'cfd_literatur_yerel_kiyas_20261025.json',ROOT/'work/cfd_literature_20261025/sources/manifest.json',ROOT/'outputs/plots/m6_literatur_kesit_hatalari_20261025.png']
    task['evidence']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths]
    save(TASK,task)
    # The task was linked above before completion; it now has its final hash.
    for x in local:
        if x['href'].endswith(TASK.name):x['sha256']=sha(TASK)
    quality={'checked_utc':datetime.now(timezone.utc).isoformat(),'local_links_checked':len(local),'missing_links':[],
             'source_records':len(manifest),'archived_sources':sum(x['status']=='archived' for x in manifest),
             'archive_failure_visible':True,'native_CFD_runs_this_task':0,'local_evidence_audit_passed':True,
             'minimum_CFD_qualification_passed':False,'sources_and_report_evidence':task['evidence'],'links':local}
    save(REPORTS/'cfd_literatur_rapor_kontrolu_20261025.json',quality)
    print(json.dumps({k:v for k,v in quality.items() if k not in ['links','sources_and_report_evidence']},ensure_ascii=False))


if __name__=='__main__':main()
