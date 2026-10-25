"""Small escaped renderer for this report's headings, tables, lists, links and plot."""
from prepare import ROOT,CASE,read,save,sha,now
import html,re,shutil

def inline(text):
    text=html.escape(text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)

def main():
    root=ROOT/'outputs/reports';source=root/'cfd_yakinsama_arastirmasi_20261025.md';target=source.with_suffix('.html')
    old=ROOT/'work/flatplate_20261025/report_layout_v1.html'
    assert not old.exists();shutil.copyfile(target,old)
    blocks=[]
    for part in source.read_text(encoding='utf-8').split('\n\n'):
        if not part.strip():continue
        lines=part.splitlines()
        if part.startswith('#'):
            m=re.match(r'^(#+) (.*)',part);blocks.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>')
        elif part.startswith('|'):
            rows=[l.strip().strip('|').split('|') for l in lines]
            head='<tr>'+''.join('<th>'+inline(v.strip())+'</th>' for v in rows[0])+'</tr>'
            body=''.join('<tr>'+''.join('<td>'+inline(v.strip())+'</td>' for v in row)+'</tr>' for row in rows[2:])
            blocks.append('<div class="scroll"><table><thead>'+head+'</thead><tbody>'+body+'</tbody></table></div>')
        elif part.startswith('- '):blocks.append('<ul>'+''.join('<li>'+inline(l[2:])+'</li>' for l in lines)+'</ul>')
        elif part.startswith('!['):
            m=re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)',part)
            blocks.append('<figure><img alt="'+html.escape(m[1])+'" src="'+html.escape(m[2])+'"><figcaption>'+html.escape(m[1])+'</figcaption></figure>')
        else:blocks.append('<p>'+inline(part.replace('\n',' '))+'</p>')
    page='''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CFD yakınsama araştırması</title><style>body{font:17px/1.65 Segoe UI,sans-serif;color:#20313d;background:#eef3f4;max-width:1120px;margin:30px auto;padding:20px}article{background:white;padding:36px;border-radius:14px}h1{font-size:30px;line-height:1.25}h2{margin-top:38px;font-size:23px;color:#006e78}p,li{overflow-wrap:anywhere}img{width:100%}figure{margin:30px 0}figcaption{font-size:13px;color:#65747c}table{border-collapse:collapse;width:100%;font-size:15px}th{background:#e4f0f1}td,th{padding:12px;border-bottom:1px solid #dce6e8;text-align:left}code{font:14px Consolas,monospace;background:#f1f4f5;padding:2px 4px}a{color:#007d86}.scroll{overflow:auto}@media(max-width:650px){body{padding:8px}article{padding:18px}}</style><article>'''+''.join(blocks)+'''<p><a href="flatplate_controls_integrity_20261025.json">Ham koşu ve dosya denetimi</a> · <a href="cfd_yakinsama_arastirmasi_20261025.md">Markdown raporu</a></p></article></html>'''
    target.write_text(page,encoding='utf-8')
    assert page.count('<table>')==page.count('</table>')==1 and page.count('<img ')==1
    for link in re.findall(r'(?:href|src)="([^"]+)"',page):
        if '://' not in link:assert (root/link).exists(),link
    taskpath=ROOT/read(CASE/'fixed_cfl_pair_v1/task.json')['path'];task=read(taskpath)
    archived=ROOT/'outputs/data/task_evidence'/task['id']/'report_layout_v2.html';shutil.copyfile(target,archived)
    task['evidence'].append({'path':str(target.relative_to(ROOT)),'sha256':sha(target),'archived':str(archived.relative_to(ROOT)),
       'revision_note':'HTML rendered as readable table/links/headings; prior escaped Markdown layout retained; no solver/data changes'})
    save(taskpath,task)
    print({'html':str(target),'validated_local_links':True})

if __name__=='__main__':main()
