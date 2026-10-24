"""Render the saved, linked engineering report without changing solver results."""
from html import escape
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'outputs/reports/muhendislik_seviyesi_ve_cfd.md'

def inline(text):
    text=escape(text)
    text=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',r'<figure><img src="\2" alt="\1"><figcaption>\1</figcaption></figure>',text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
    return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text)

def main(report_path=None):
    path=Path(report_path) if report_path else ROOT/'outputs/reports/muhendislik_seviyesi_ve_cfd.md'
    report=path.read_text(encoding='utf-8'); lines=report.splitlines(); i=0; parts=[]
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1; continue
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#')); parts.append(f'<h{n}>{inline(line[n:].strip())}</h{n}>'); i+=1
        elif line.startswith('!['): parts.append(inline(line)); i+=1
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=lines[i].strip('|').split('|')
                if not all(re.fullmatch(r'\s*[-:]+\s*',c) for c in cells): rows.append(cells)
                i+=1
            parts.append('<div class="table"><table>'+''.join('<tr>'+''.join(f'<{"th" if j==0 else "td"}>{inline(c.strip())}</{"th" if j==0 else "td"}>' for c in row)+'</tr>' for j,row in enumerate(rows))+'</table></div>')
        elif line.startswith('- ') or re.match(r'^\d+\. ',line):
            numbered=bool(re.match(r'^\d+\. ',line)); tag='ol' if numbered else 'ul'; items=[]
            while i<len(lines) and (bool(re.match(r'^\d+\. ',lines[i])) if numbered else lines[i].startswith('- ')):
                items.append('<li>'+inline(re.sub(r'^\d+\. |^- ','',lines[i]))+'</li>'); i+=1
            parts.append(f'<{tag}>'+''.join(items)+f'</{tag}>')
        else:
            parts.append('<p>'+inline(line)+'</p>'); i+=1
    css='''body{margin:0;background:#edf2f6;color:#183344;font:16px/1.7 "Segoe UI",sans-serif}main{max-width:1060px;margin:30px auto;background:white;padding:36px 48px;border-radius:14px}h1{font-size:33px;line-height:1.3}h2{font-size:24px;border-top:2px solid #dce6ed;padding-top:24px;margin-top:40px}h3{color:#12666d}strong{color:#125b65}a{color:#087783}a:hover{text-decoration:none}.table{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px;border:1px solid #dce6ed;text-align:left;vertical-align:top}th{background:#edf5f6}tr:nth-child(even){background:#f7fafb}figure{margin:26px 0}img{width:100%;height:auto;border:1px solid #dce6ed}figcaption{font-size:13px;color:#597080}nav{font-size:14px;border-bottom:1px solid #dce6ed;padding-bottom:16px}li{margin:8px 0}@media(max-width:750px){main{margin:0;padding:20px}h1{font-size:27px}}@media print{body{background:white}main{margin:0;padding:0}figure,tr{break-inside:avoid}}'''
    title=escape(lines[0].lstrip('# '))
    html='<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+title+'</title><style>'+css+'</style></head><body><main><nav><a href="../Proje-Ozeti.html">Proje özeti</a> · <a href="'+path.name+'">Metin sürümü</a></nav>'+''.join(parts)+'</main></body></html>'
    path.with_suffix('.html').write_text(html,encoding='utf-8')
    print('Report rendered:',path.with_suffix('.html')); print('Words:',len(report.split()))
if __name__=='__main__': main()
