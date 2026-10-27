"""Improve spacing in new report prose without changing code, URLs or numbers."""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now
from finalize_batch import render

def prose(text):
    parts=re.split(r'(`[^`]*`|\]\([^)]*\)|[+-]?\d+(?:\.\d+)?[eE][+-]?\d+)',text)
    for i in range(0,len(parts),2):
        s=parts[i]
        s=re.sub(r'(?<=[A-UW-Za-uw-zÇĞİÖŞÜçğıöşü])(?=\d)',' ',s)
        s=re.sub(r'(?<=\d)(?=[A-Za-zÇĞİÖŞÜçğıöşü])',' ',s)
        s=re.sub(r'(?<!\d),(?=\d)',', ',s)
        s=re.sub(r'(?<=[;])(?=\w)',' ',s)
        s=re.sub(r'(?<=\w)(?=%)',' ',s)
        s=re.sub(r'(\d) e([+-]\d+)',r'\1e\2',s)
        for a,b in [('p 32 a','p32a'),('p 32 b','p32b'),('2 B','2B'),('3 B','3B'),('SU 2','SU2'),('SHA 256','SHA256'),('log 10','log10'),('RAE 2822','RAE2822'),('M 6','M6'),('pristine 32','pristine32'),('cap 256','cap256')]:s=s.replace(a,b)
        parts[i]=s
    return ''.join(parts)

def main():
    stem=ROOT/'outputs/reports/su2_kaynak_kontrolu_20261027'
    path=stem.with_suffix('.md');md=prose(path.read_text(encoding='utf-8'));path.write_text(md,encoding='utf-8')
    htmlpath=stem.with_suffix('.html');old=htmlpath.read_text(encoding='utf-8')
    header=old.split('</style>',1)[0]+'</style>'
    htmlpath.write_text(header+render(md)+'</html>',encoding='utf-8')
    data=read(stem.with_suffix('.json'))
    for key in ('summary_tr','summary_en'):data[key]=prose(data[key])
    data['editorial_note']='Spacing only; source, numerical values and native/build records unchanged.'
    save(stem.with_suffix('.json'),data)
    taskpath=ROOT/read(BASE/'task.json')['path'];task=read(taskpath)
    paths=[x if isinstance(x,str) else x['path'] for x in task['evidence']]
    task['evidence']=[{'path':p,'sha256':sha(ROOT/p)} for p in dict.fromkeys(paths)]
    task['editorial_updated_utc']=now();save(taskpath,task)
    print({'report_spacing_updated':True,'numerical_results_changed':False},flush=True)

if __name__=='__main__':main()
