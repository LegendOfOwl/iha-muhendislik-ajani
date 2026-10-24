"""Acquire published geometry unchanged, separating analysis inputs and reviewer data."""
from pathlib import Path
import sys,json,hashlib,urllib.request
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/agent'))
import projects,project
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    store=ROOT/'work/blind_validation';store.mkdir(exist_ok=True)
    idfile=store/'project.json'
    if not idfile.exists():
        p=projects.create('Kaynak geometriden kör CFD sınaması','qualification');t=project.make_task('Yayımlanmış kaynak geometriyi değiştirmeden, hedef deney sonuçlarını analiz ajanına vermeden yerel ağ ve gerçek CFD üret; sonuçları önceden kayıtlı ölçütlerle karşılaştır','qualification',p['id'])
        task=project.read(t);task.update(status='çalışıyor',phase='araç doğrulama',acceptance=['Özgün internet geometrisi; geometri ve fiziksel koşullar kayıtlı, hedef sonuç analize verilmez','Konuma bağlı yeni viskoz ağlar; duvar/LE/TE/iz/şok, geometri/ağ/iteratif/uzak alan kontrolleri','Tahminler değerlendirmeden önce hash ile dondurulur; kaynak deneyle tüm hatalar ve açık kabul raporlanır']);project.write(t,task)
        projects.write(idfile,{'project_id':p['id'],'output_root':p['artifact_root'],'task':str(t.relative_to(ROOT))})
    info=projects.read(idfile);out=ROOT/info['output_root'];inp=store/'analysis_input';ref=store/'reviewer_only';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True)
    base='https://www.grc.nasa.gov/www/wind/valid/raetaf/'
    sources=[(inp/'geom.txt',base+'geom.txt'),(inp/'geom.f90',base+'geom.f90'),(inp/'yl.pts',base+'yl.pts'),(inp/'yu.pts',base+'yu.pts'),(ref/'cp.exp.gen',base+'raetaf04/cp.exp.gen'),(ref/'cfpost.cp.com',base+'raetaf04/cfpost.cp.com'),(ref/'cp.wind.gen',base+'raetaf04/cp.wind.gen'),(ref/'forces.lis',base+'raetaf04/forces.lis'),(ref/'case.html',base+'raetaf.html'),(ref/'study4.html',base+'raetaf04/raetaf04.html')]
    records=[]
    for p,url in sources:
        if not p.exists():
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Engineering-validation'}),timeout=40) as r:p.write_bytes(r.read())
        records.append({'file':str(p.relative_to(ROOT)),'url':url,'bytes':p.stat().st_size,'sha256':sha(p)});print(p.name,p.stat().st_size,flush=True)
    projects.write(store/'sources.json',{'timestamp':datetime.now(timezone.utc).isoformat(),'sources':records})
    conditions={'geometry':'geom.txt with signed coordinates in yl.pts / yu.pts; source geom.f90 specifies lower-column sign','length_unit':'m','chord_m':1.0,'Mach':.729,'alpha_deg':2.31,'Re_chord':6.5e6,'T_K':460*5/9,'model':'2D compressible turbulent RANS, adiabatic no-slip, fully turbulent SA baseline','conditions_source':'NASA validation Study4 corrected computational conditions; temperature is source computational assumption. No angle/pressure fitting allowed.'}
    projects.write(inp/'conditions.json',conditions)
    projects.write(store/'contract.json',{'frozen_before_analysis':datetime.now(timezone.utc).isoformat(),'geometry_sha256':{p.name:sha(p) for p in inp.glob('*') if p.is_file()},'scope':'2D RAE2822 Case6 corrected computational-condition benchmark; no 3D M6 or UAV acceptance','minimum_numerical':{'density_log10_max':-8,'force_window_iterations':200,'CL_tail_range_max':5e-5,'CD_tail_range_max':2e-6,'max_wall_yplus':1.0,'CL_finest_grid_relative_change_max':.005,'CD_finest_grid_relative_change_max':.02,'Cp_finest_grid_RMSE_max':.01,'CL_farfield_relative_change_max':.0025,'CD_farfield_relative_change_max':.01},'experimental_Cp':{'pointwise_RMSE_max':.03,'per_side_RMSE_max':.04,'p95_absolute_error_max':.06,'max_absolute_error_max':.15,'shock_location_abs_error_chords_max':.02},'note':'Local strict qualification contract, not NASA-prescribed universal thresholds. No loosening after seeing errors. Shared filesystem restrictions are procedural, not security isolation; memorization cannot be excluded.'})
    (out/'data/source_geometry').mkdir(exist_ok=True)
    import shutil
    for p in inp.glob('*'):shutil.copy2(p,out/'data/source_geometry'/p.name)
    projects.write(out/'data/blind_contract.json',projects.read(store/'contract.json'))
    print(json.dumps(info,ensure_ascii=False));print(str(inp))
if __name__=='__main__':main()
