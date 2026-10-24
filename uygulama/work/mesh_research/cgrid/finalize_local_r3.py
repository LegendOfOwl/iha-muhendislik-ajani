"""Mesh-only deliverables and hashes; preserve original and tail-r2 sources."""
from pathlib import Path
import os,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent;OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
from scipy.interpolate import BSpline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from audit_local_r3 import parse,quality,js,sha,stat,distance_end

family=json.loads((OUT/'reports/prediction_v3_cgrid_localr3_family.json').read_text());reports=[];counts=[]
fig,axs=plt.subplots(2,3,figsize=(14,8))
for col,level in enumerate(['coarse','medium','fine']):
    name='v3_cgrid_localr3_'+level;folder=OUT/'simulations'/name;r=json.loads((folder/'local_revision_audit.json').read_text());reports.append(r)
    p,q,t,m=parse(folder/'mesh.su2');k=quality(p,q,t);p0,q0,t0,_=parse(ROOT/r['baseline']['path']);k0=quality(p0,q0,t0)
    c=np.array(r['after']['worst_global'][0]['center_m']);radius=.025
    for row,(pp,qq,tt,kk,label) in enumerate([(p0,q0,t0,k0,'tail-r2 comparator'),(p,q,t,k,'local-r3')]):
        ax=axs[row,col]
        for co,off in [(qq,0),(tt,len(qq))]:
            v=pp[co];sel=(v[:,:,0].max(1)>c[0]-radius)&(v[:,:,0].min(1)<c[0]+radius)&(v[:,:,1].max(1)>c[1]-radius)&(v[:,:,1].min(1)<c[1]+radius)
            coll=PolyCollection(v[sel],array=kk['skew'][off:off+len(co)][sel],cmap='viridis',norm=Normalize(0,1),edgecolors='#777777',linewidths=.4);ax.add_collection(coll)
        ax.set(xlim=(c[0]-radius,c[0]+radius),ylim=(c[1]-radius,c[1]+radius),aspect='equal',xlabel='x/c',ylabel='y/c',title=level+' '+label+'\nnew global-worst location')
        if row==1:
            poly=np.array(r['after']['worst_global'][0]['vertices_m']);ax.plot(*np.r_[poly,poly[:1]].T,color='red',lw=1.3)
    # Independent visualization artifact only: no fluid solution variables.
    ug=vtk.vtkUnstructuredGrid();pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.c_[p,np.zeros(len(p))],deep=True));ug.SetPoints(pts)
    sizes=np.r_[np.full(len(q),4),np.full(len(t),3)];offsets=np.r_[0,np.cumsum(sizes)].astype(np.int64);conn=np.r_[q.ravel(),t.ravel()].astype(np.int64)
    ca=vtk.vtkCellArray();ca.SetData(numpy_to_vtkIdTypeArray(offsets,deep=True),numpy_to_vtkIdTypeArray(conn,deep=True));ug.SetCells(numpy_to_vtk(np.r_[np.full(len(q),9,np.uint8),np.full(len(t),5,np.uint8)],deep=True),ca)
    for key,arr in [('Signed_Area_m2',k['area']),('Min_Corner_Jacobian_m2',k['jac']),('Equiangle_Skew',k['skew'])]:
        da=numpy_to_vtk(arr,deep=True);da.SetName(key);ug.GetCellData().AddArray(da)
    wr=vtk.vtkXMLUnstructuredGridWriter();wr.SetFileName(str(folder/'mesh_geometry_only.vtu'));wr.SetInputData(ug);wr.SetDataModeToAppended();wr.EncodeAppendedDataOff();assert wr.Write()==1
    vr=vtk.vtkXMLUnstructuredGridReader();vr.SetFileName(str(folder/'mesh_geometry_only.vtu'));vr.Update();back=vr.GetOutput()
    roundtrip={'nodes':back.GetNumberOfPoints(),'cells':back.GetNumberOfCells(),'coordinates_bitwise_equal':bool(np.array_equal(vtk_to_numpy(back.GetPoints().GetData())[:,:2],p)),'area_array_bitwise_equal':bool(np.array_equal(vtk_to_numpy(back.GetCellData().GetArray('Signed_Area_m2')),k['area'])),'contains_flow_solution':False}
    assert roundtrip['nodes']==len(p) and roundtrip['cells']==len(q)+len(t) and roundtrip['coordinates_bitwise_equal'] and roundtrip['area_array_bitwise_equal']
    # Check the callback's actual influence on the OLD exterior cell centers.
    cen=k0['center'][len(q0):];distance=distance_end(cen);h_end=r['sizing']['h_end_m'];scale={'coarse':2/3,'medium':1,'fine':1.5}[level]
    x,y=cen.T;near=np.hypot(np.maximum.reduce([-x,x-1,np.zeros(len(x))]),np.maximum(abs(y)-.1,0));hwake=np.where((x>1)&(x<10),.035+.15*abs(y-np.tan(np.deg2rad(2.31))*(x-1)),1e9)
    h_old=np.minimum.reduce([.012+.24*near,hwake,3.+.12*np.maximum.reduce([abs(x)-20,abs(y)-20,np.zeros(len(x))])])/scale;htail=h_end+.25*distance;changed=htail<h_old
    influence={'sampling':'old tail-r2 exterior triangle centroids; target-size effect, distinct from Gmsh retriangulation footprint','old_exterior_cells':len(cen),'target_reduced_at_cells':int(changed.sum()),'distance_to_end_where_reduced_m':stat(distance[changed]),'h_new_over_old_where_reduced':stat(htail[changed]/h_old[changed]),'retessellation_note':'All exterior triangles are regenerated. Regions with unchanged target sizes can still change connectivity/shape; near explicit quads are bitwise preserved.'}
    des=json.loads((folder/'near_design.json').read_text());near=np.load(folder/'near_arrays.npz');gg=near['grid'];nw=des['wake_segments_each_side'];nl=des['wall_lower_segments'];nu=des['wall_upper_segments'];normalchecks={}
    for side,pay,ts,cols in [('upper',des['geometry_payload'][0],des['wall_parameter_upper'],np.arange(nw+nl,nw+nl+nu+1)),('lower',des['geometry_payload'][1],des['wall_parameter_lower'],np.arange(nw,nw+nl+1)[::-1])]:
        b=BSpline(pay['knots'],pay['coefficients_m'],3);tan=b(ts,1);norm=np.c_[-tan[:,1],tan[:,0]];norm/=np.linalg.norm(norm,axis=1)[:,None]
        first=(gg[1,cols]-gg[0,cols]);extent=(gg[-1,cols]-gg[0,cols]);normalchecks[side]={'actual_first_edge_length_m':stat(np.linalg.norm(first,axis=1)),'actual_first_normal_projection_m':stat(np.sum(first*norm,axis=1)),'actual_outer_block_wall_normal_projection_m':stat(np.sum(extent*norm,axis=1)),'note':'Exact r2 B-spline normal evaluated at actual wall parameter; sharp TE separately has finite one-sided normal.'}
    counts.append({'case':name,'before':r['before']['cells'],'after':r['after']['cells'],'increase_percent':100*(r['after']['cells']/r['before']['cells']-1),'h_end_m':h_end,'normal_layers':des['normal']['layers'],'wall_first_m':des['normal']['first_m'],'normal_cap_m':des['normal']['cap_m'],'normal_thickness_m':des['normal']['thickness_m'],'growth':des['normal']['growth_design'],'actual_normal_measurements':normalchecks,'local_skew_before':r['before']['tail_local']['skew']['max'],'local_skew_after':r['after']['tail_local']['skew']['max'],'min_angle_before_deg':r['before']['tail_local']['angle_min_deg']['min'],'min_angle_after_deg':r['after']['tail_local']['angle_min_deg']['min'],'global_skew_before':r['before']['equiangle_skew']['max'],'global_skew_after':r['after']['equiangle_skew']['max'],'global_worst_center_m':c.tolist(),'target_influence':influence})
    counts[-1]['VTU_roundtrip']=roundtrip
fig.suptitle('Actual exterior mesh at each NEW global worst cell; red = worst triangle. Same 0..1 skew scale.')
fig.tight_layout(rect=(0,0,.94,.95));cbax=fig.add_axes([.95,.18,.012,.6]);fig.colorbar(coll,cax=cbax,label='equiangle skew')
fig.savefig(OUT/'plots/prediction_v3_cgrid_localr3_remaining_global_worst.png',dpi=170);plt.close(fig)
table='|Ağ|Hücre önce→sonra|Artış|Uç max skew önce→sonra|Uç min açı önce→sonra|Genel max skew|\n|---|---:|---:|---:|---:|---:|\n'
for r in counts:table+=f"|{r['case'].split('_')[-1]}|{r['before']:,}→{r['after']:,}|%{r['increase_percent']:.2f}|{r['local_skew_before']:.5f}→{r['local_skew_after']:.5f}|{r['min_angle_before_deg']:.2f}°→{r['min_angle_after_deg']:.2f}°|{r['global_skew_after']:.5f}|\n"
note='''# C-grid local-r3: iz ucu dış ağ düzeltmesi

Üç yeni ağda x/c8 ucundaki dış üçgen kalitesi iyileşti. Kaynak r2 eğrisi, duvar düğümleri, bütün yakın dörtgen blok ve normal dağılımı tail-r2 ile bit düzeyinde aynı;200c kare dış sınır aynı. Pozitif alan, tüm köşe Jacobian'ları, tek bağlı akış bölgesi, ters iç kenar/işaretsiz sınır/çok-komşulu kenar kontrolleri üç seviyede geçti. Bu, geometri/ağ denetimidir; CFD yakınsaması veya akış doğruluğu kabulü değildir.

'''+table+'''
“Uç” dış üçgen merkezinin kapalı x=8 / y=tan(2,31°)×7±0,3c dikey parçasına uzaklığının0,25c'den küçük olduğu bölgedir. Önce ve sonra aynı tanım kullanıldı; hiçbir hücre açı/çarpıklık sonucu küçülsün diye çıkarılmadı. Genel en kötü hücreler ayrıca korunuyor.

Her seviyede h_end, gerçek arayüzün x=8 üzerindeki en küçük pozitif Δy'sinden ölçüldü: kaba0,00352941m, orta ve ince değerler makine okunur raporda. Yeni dış hedef boyut `min(eski_h, h_end+0,25×parçaya_uzaklık)`; h_end zaten gerçek seviyenin mesafesidir, tekrar ölçeklenmedi. Eski global boyut fonksiyonu değişmedi. Gmsh tüm dış üçgen bölgesini yeniden ağladığından hedef fonksiyonu değişmeyen yerlerde bile bağlantı/çarpıklık değişebilir. Sadece açık yakın bloklar birebir korunma güvencesi taşır.

Sınırsız doğrusal uzaklık fonksiyonunun boyut hedefi üzerindeki etkisi geometrik olarak kompakt değildir: eski dış üçgen merkezleriyle örneklenince en uzak azaltma kaba32,159c, orta11,950c, ince7,859c mesafededir. En güçlü azaltma uçta bulunur; toplam hücre artışları tabloda sınırlıdır. Bu sürüm önerilen doğrusal kuralı aynen uygular; dıştaki etkiyi sessizce sıfırlayan bir cutoff eklenmedi. Sadece1c içinde etkili kompakt bir düzeltme ayrı sürüm ve denetim gerektirir.

Kaba genel max skew0,95389'dan0,95910'a biraz yükseldi; yeni en kötü hücre(-0,059005;−0,023367)m'de LE dış-blok geçişindedir. Orta en kötü(-0,063310;−0,002506)m, ince(1,001477;0,060658)m'dedir. Bunlar gizlenmedi veya yeni bir açı eşiğiyle geçer sayılmadı. Dar uç düzeltmesi başarılıdır; genel ağın her bölgesi iyileşti denmez.

Kaba önce ağı mevcut tail-r2 SU2 dosyasıdır. Orta/ince tail-r2 karşılaştırıcıları aynı değiştirilmemiş kaynak fonksiyonlardan bu denetim için work/ altında gerçekten üretildi; bunların CFD koşusu yoktur. Her üç seviyede source/normal/body/wake fonksiyonları AST karşılaştırmasında aynı; yeniden hesaplanan yakın düğüm/quads/grid/duvar ve actual SU2 ihracı birebir eşleşti. Özgün build_cgrid.py ve tail-r2 dosyaları değiştirilmedi.

Kaynak geometrinin65 noktası aynı r2 B-spline'a makine duyarlığında oturuyor; duvar düğüm/eğri ve lineer panel sapmaları her case local_revision_audit.json dosyasında. Geometri payload SHA050ee43ead96df3cbc2a34649cf06c0839ed6fe47ae8aaf4955744d19f49cf5a. Veter1m; fizik girdileri yalnız provenans hash'iyle korundu, bu aşamada akış çözülmedi. Yakın blok0,06c, ilk yükseklik/büyüme/normal cap ve katman sayıları summary tablosunda kayıtlı. Tüm seviyeler aynı kaynak eğriyi ve dış alanı kullanır.

Yöntem, [Gmsh4.15.2](https://gmsh.info/doc/texinfo/#Structured-grids) ile açık yakın blok + dış üçgen ağı yaklaşımının yerel boyut revizyonudur. Bu çalışmada yeni bir şok/deney hedefi aranmadı. Gerçek uç önce/sonra görselleri ve kalan global en kötü hücre görseli incelendi; mesh_geometry_only.vtu yalnız ağ/kalite verisi içerir. y+, Cp, kuvvet, kalıntı ve uzak alan akış duyarlılığı bu revizyonda değerlendirilmedi. İlk şok sıcaklığından uzaktaki bu düzeltmenin CFD sorununu çözdüğü iddia edilmiyor. Parent'ın ayrı çözücü tanıları bu ağ kabulüne dahil edilmedi.

CFD başlatılmadı. Reviewer modülü veya beklenen deney/harici CFD sonuçları okunmadı; `audit_cgrid.py` metnindeki reviewer import'u fark edilip çalıştırılmadı, bu sürüm için bağımsız SU2 denetleyicisi yazıldı. Güncellenmiş global AGENTS/PROJECT_STATE ve kullanıcı raporları açılmadı.
'''
(OUT/'reports/prediction_v3_cgrid_localr3_report.md').write_text(note,encoding='utf-8')
savepath=OUT/'reports/prediction_v3_cgrid_localr3_summary.json';savepath.write_text(json.dumps({'scope':'Geometry-only local revision; CFD not run','levels':counts,'geometry_topology_checks_passed':family['all_geometry_topology_checks_passed'],'all_same_farfield':family['all_same_farfield_bounds'],'all_same_exact_geometry':family['all_same_geometry_payload_sha256']},indent=2))
files=[]
for level in ['coarse','medium','fine']:
    folder=OUT/'simulations'/('v3_cgrid_localr3_'+level);files.extend(x for x in folder.iterdir() if x.is_file())
files.extend([OUT/'reports/prediction_v3_cgrid_localr3_family.json',OUT/'reports/prediction_v3_cgrid_localr3_report.md',savepath,OUT/'plots/prediction_v3_cgrid_localr3_remaining_global_worst.png'])
files.extend(OUT/'plots'/f'prediction_v3_cgrid_localr3_{level}_tail_before_after.png' for level in ['coarse','medium','fine'])
manifest={'scope':'Only three local-r3 geometry meshes and independent topology/quality checks. No solver fields or numerical acceptance claimed.','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_script_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [WORK/'build_cgrid.py',WORK/'build_cgrid_tail_r2.py',WORK/'build_cgrid_local_r3.py',WORK/'audit_local_r3.py',WORK/'finalize_local_r3.py']},'input_sha256':family['input_sha256'],'contract_sha256':'a3106e323f9a5671067b69fded039fa8b3d2aae607514ec114a949b501b91c69','contract_hash_source':'Parent supplied; contract was not opened. Flow acceptance not evaluated.','case_files_sha256':{str(f.relative_to(ROOT)):sha(f) for f in files},'input_access_log':str((WORK/'access_log_local_r3.json').relative_to(ROOT)),'input_access_log_sha256':sha(WORK/'access_log_local_r3.json'),'CFD_launched':False,'future_flow_numerical_acceptance':None}
(OUT/'reports/prediction_v3_cgrid_localr3_mesh_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(counts,indent=2));print('Manifest saved:',len(files),'deliverable hashes')
