"""One controlled numerical diagnostic; not the blinded RAE experiment or a new M6 mesh."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,shutil,subprocess,time,os,csv,re,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'work/validation'));sys.path.insert(0,str(ROOT/'work/agent'))
import project
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def replace(text,key,value):
    pattern=r'^\s*'+re.escape(key)+r'\s*=.*$'
    return re.sub(pattern,key+'= '+str(value),text,flags=re.M) if re.search(pattern,text,re.M) else text+'\n'+key+'= '+str(value)+'\n'
def main():
    pid='proje-e9319baef1';out=ROOT/'outputs/projects'/pid;first=out/'simulations/m6_rans_20261019_110436'
    initial=json.loads((first/'results.json').read_text());row=initial['results'][1];source=Path(row['folder'])
    folder=out/'simulations'/('m6_bounded_cfl_'+datetime.now().strftime('%Y%m%d_%H%M%S'));folder.mkdir()
    task_path=project.make_task('M6 aynı kaynak ağ/koşulunda yalnız CFL uyarlamasını kapatarak kayıtlı çözümden kontrollü sayısal deneme; mevcut duvar/ağ kabulü açık kalır','qualification',pid)
    task=project.read(task_path);task.update(status='çalışıyor',phase='araç doğrulama',acceptance=['Aynı geometri/ağ ve fiziksel koşullar; değişikliklerin kaydı','Gerçek native yeniden başlatma, kalıntı/kuvvet/alan kanıtı','İyileşse de yeni ağ/duvar/deney kabulü sağlanmadan M6 doğrulaması verme']);project.write(task_path,task)
    for name in ['case.cfg','mesh.su2','restart_flow.dat']:shutil.copy2(source/name,folder/name)
    assert sha(folder/'mesh.su2')==row['mesh']['mesh_sha256']
    cfg=(folder/'case.cfg').read_text();changes={'CFL_ADAPT':'NO','ITER':1000,'OUTPUT_WRT_FREQ':200,'RESTART_SOL':'YES','SOLUTION_FILENAME':'restart_flow.dat'}
    for k,v in changes.items():cfg=replace(cfg,k,v)
    (folder/'case.cfg').write_text(cfg)
    save(folder/'diagnostic_contract.json',{'source_run':str(source),'source_mesh_sha256':sha(source/'mesh.su2'),'restart_input_sha256':sha(source/'restart_flow.dat'),'physical_conditions':initial['conditions'],'changes':changes,'single_numerical_treatment':'CFL remains4; adaptive schedule disabled. Other changes only run length/checkpoint/restart output controls. No limiter/linear solver/physics change.','acceptance_unchanged':initial['thresholds'],'not_blind':True,'scope':'M6 iterative diagnostic only; no new region-refined mesh, no grid independence or overall M6 quality acceptance'})
    command=[json.loads((ROOT/'work/setup/su2_install.json').read_text())['executable'],'case.cfg','-t','4'];save(folder/'command.json',command)
    start=time.perf_counter();status='completed';code=None
    with (folder/'native.log').open('w') as log:
        p=subprocess.Popen(command,cwd=folder,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=p.wait(timeout=1200)
        except subprocess.TimeoutExpired:p.kill();p.wait();status='timeout_partial_preserved'
    with (folder/'history.csv').open() as f:h=[{k.strip().strip('"'):float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    tail=h[-100:];last=h[-1]
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'task':str(task_path.relative_to(ROOT)),'folder':str(folder),'status':status,'exit_code':code,'wall_seconds':time.perf_counter()-start,'iterations':len(h),'CL':last['CL'],'CD':last['CD'],'density_log10':last['rms[Rho]'],'CL_last100_range':float(np.ptp([r['CL'] for r in tail])),'CD_last100_range':float(np.ptp([r['CD'] for r in tail])),'initial_CL':row['CL'],'initial_CD':row['CD'],'initial_density_log10':row['log10_density_residual'],'primary_geometry_scope':'Unchanged published M6 finer source grid','quality_passed':False,'note':'Runtime/numerical diagnostic. Prior wall and source-grid sensitivity gaps remain. No replacement of sealed previous report.'}
    result['iterative_passed']=status=='completed' and code==0 and result['density_log10']<-7 and result['CL_last100_range']<2e-4 and result['CD_last100_range']<2e-5
    if status=='completed' and code==0:
        from compare_m6 import comparison,experimental
        sample=dict(row,folder=str(folder));result['pressure_comparison'],_,_=comparison(sample,experimental()[0])
    else:result['pressure_comparison']=None
    save(folder/'results.json',result);save(ROOT/'work/blind_validation/reviewer/m6_diagnostic_result.json',result)
    task.update(status='tamamlandı',completed_utc=datetime.now(timezone.utc).isoformat(),completion_scope='Controlled numerical diagnostic completed/reported; M6 physical qualification remains open',open_engineering_acceptances=['M6 wall resolution/source-grid sensitivity/experiment acceptance remains open'],evidence=[{'path':str((folder/'results.json').relative_to(ROOT)),'sha256':sha(folder/'results.json')}]);project.write(task_path,task)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
