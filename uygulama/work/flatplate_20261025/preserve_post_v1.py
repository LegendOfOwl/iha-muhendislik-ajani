from prepare import ROOT,BASE,read,save,sha,now
from pathlib import Path
import shutil
def main():
    target=BASE/'postprocessing_v1_nearest';assert not target.exists();target.mkdir()
    files=[BASE/'field_audit.py',BASE/'compare.py',ROOT/'outputs/reports/flatplate_comparison_20261025.json',ROOT/'outputs/plots/flatplate_reference_comparison_20261025.png']
    for role in ['coarse','medium','fine','fine_nested']:
        files.extend([ROOT/f'outputs/reports/flatplate_{role}_field_audit_20261025.json',ROOT/f'outputs/plots/flatplate_{role}_profiles_20261025.png'])
        files.extend((ROOT/f'outputs/data/qualification/flatplate_SAneg_20261025_v1/{role}').glob('*.csv'))
    records=[]
    for p in files:
        out=target/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
        records.append({'original_path':str(p.relative_to(ROOT)),'preserved_path':str(out.relative_to(ROOT)),'sha256':sha(out)})
    save(target/'manifest.json',{'created_utc':now(),'reason':'Nearest-column x1.90334 profile actually sampled at1.91408 or1.89260m. Replace with explicit two-column interpolation to requested x. Raw CFD unchanged. Old records retain their original relative paths, mapped here to archived copies.','files':records})
    print('Preserved',len(files),'v1 postprocessing records')
if __name__=='__main__':main()
