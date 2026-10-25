from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/agent'))
from project import make_task,read,write,now,digest
from learning import instruction_snapshot

def main():
    assert not (BASE/'task.json').exists()
    taskpath=make_task('NASA TMR kaynak düz plaka ağlarıyla SA-neg uygulama kontrolü: üç küçük ağ, gerçek SU2 ve kaynak Cf/profil karşılaştırması', 'qualification','qualification')
    task=read(taskpath)
    task.update(status='çalışıyor',phase='türbülans modeli sayısal doğrulama',
        acceptance=['Özgün kaynak ağ ve koşulları koru','Üç sistematik ağda native çözüm ve eşlenmiş alan/geçmiş mühürleri',
        'Referans Cf ve profil farklarını bütün noktalarla raporla; deney ve kod doğrulamasını ayır'],
        applied_lesson_ids=['L01','L02','L03','L04','L05','L06','L07','L08','L09','L10','R01','R03'],
        agent_instruction_snapshot=instruction_snapshot(ROOT))
    write(taskpath,task);write(BASE/'task.json',{'path':str(taskpath.relative_to(ROOT))})
    (BASE/'sources').mkdir(exist_ok=True)
    print(taskpath)

if __name__=='__main__':main()
