from datetime import datetime,timezone
import hashlib,json,sys
from pathlib import Path
import urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/agent'))
import projects,project
DEST=ROOT/'work/validation/sources'
def main():
    ids=ROOT/'work/validation/projects.json'
    projects.bootstrap()
    if not ids.exists():
        cad=projects.create('NIST karmaşık CAD doğrulaması','qualification');cfd=projects.create('NASA ONERA M6 CFD doğrulaması','qualification')
        projects.write(ids,{'cad':cad['id'],'cfd':cfd['id']})
        for p,request,criteria in [(cad,'NIST kaynak teknik resim/modelinden karmaşık parçaları yeniden oluştur; referans STEP ile ölçü/topoloji/katı farkını ve FreeCAD geri okumasını denetle',['Kaynak PDF ve STEP, birimler ve SHA kayıtlı','Parametrik yeniden üretim; orijinali yeniden dışa aktararak üretim iddia etme','Hacim/boyut/topoloji/katı farkı, gerçek CAD dosyaları ve geometri raporu']),
            (cfd,'NASA arşivli ONERA M6 Test2308 koşullarında iki kaynak ağda gerçek SU2 RANS çalıştır; yedi kesitte deney Cp verisiyle karşılaştır',['M0.8395, alfa3.06deg, Re11.72M ve c0.64607m koşul eşleşmesi','Gerçek 3D RANS, ham alan/kuvvet/y+ ve iki ağda sayısal duyarlılık','NASA deney Cp, x/c ve y/b kesit eşlemesi; tüm hatalar ve açık kabul raporlanır'])]:
            path=project.make_task(request,'qualification',p['id']);t=project.read(path);t.update(status='çalışıyor',acceptance=criteria,phase='araç doğrulama',blocked_by=[]);project.write(path,t)
    sources=[('nist_ctc_definitions.zip','https://www.nist.gov/document/nist-ctc-test-case-definitions'),('nist_ftc_definitions.zip','https://www.nist.gov/document/nist-ftc-test-case-definitions'),('nist_ctc01.pdf','https://www.nist.gov/document/nist-cad-model-ctc-01'),('nist_ctc02.pdf','https://www.nist.gov/document/nist-cad-model-ctc-02'),('nist_ctc05.pdf','https://www.nist.gov/document/nist-cad-model-ctc-05'),('m6_nasa.html','https://www.grc.nasa.gov/www/wind/valid/m6wing/m6wing.html')]
    index=json.loads((ROOT/'work/validation/su2_cases_index.json').read_text())
    sources += [(x['name'],x['download_url']) for x in index['rans/oneram6'] if x['name'].endswith('.su2')]
    sources += [(f'cp{i}{s}.ex',f'https://www.grc.nasa.gov/www/wind/valid/m6wing/cp{i}{s}.ex') for i in range(1,8) for s in ['l','u']]
    records=[]
    for name,url in sources:
        p=DEST/name
        if not p.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'Engineering-source-validation'})
            with urllib.request.urlopen(req,timeout=60) as r:raw=r.read();final=r.url
            p.write_bytes(raw)
        else:final=url
        records.append({'file':str(p.relative_to(ROOT)),'url':url,'resolved_url':final,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        print(name,p.stat().st_size,flush=True)
        if p.suffix=='.zip':
            out=DEST/p.stem;out.mkdir(exist_ok=True)
            with zipfile.ZipFile(p) as z:
                for info in z.infolist():
                    dest=(out/info.filename).resolve()
                    if not dest.is_relative_to(out.resolve()):raise ValueError('Unsafe zip path')
                    z.extract(info,out)
    projects.write(DEST/'manifest.json',{'timestamp':datetime.now(timezone.utc).isoformat(),'sources':records})
    print(ids.read_text())
if __name__=='__main__':main()
