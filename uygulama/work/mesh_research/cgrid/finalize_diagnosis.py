"""Document own numerical diagnosis. Does not run or alter any solver case."""
from pathlib import Path
import json,os,hashlib,datetime
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent;OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from scipy.spatial import cKDTree
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=json.loads((OUT/'reports/prediction_v3_cgrid_shock_diagnosis_v2.json').read_text())
base=OUT/'simulations/v3_cgrid_coarse';m=np.load(base/'mesh_arrays.npz');p=m['points'];quads=m['quads'];tris=m['triangles']
fig,axs=plt.subplots(2,2,figsize=(12,8))
for ax,f in zip(axs.ravel(),a['fields']):
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(ROOT/f['field']));r.Update();g=r.GetOutput();vp=vtk_to_numpy(g.GetPoints().GetData())[:,:2];_,mp=cKDTree(vp).query(p)
    residual=np.abs(vtk_to_numpy(g.GetPointData().GetArray('Residual_Density')))[mp]
    for co in [quads,tris]:
        cen=p[co].mean(1);keep=(cen[:,0]>-.1)&(cen[:,0]<1.15)&(cen[:,1]>-.15)&(cen[:,1]<.6)
        coll=PolyCollection(p[co[keep]],array=np.log10(np.maximum(residual[co[keep]].mean(1),1e-12)),cmap='magma',clim=(-8,-2),edgecolors='none');ax.add_collection(coll)
    for h in f['global_maxima'][:3]:ax.plot(*h['xy_m'],'cx',ms=6)
    for e in m['wall']:ax.plot(p[e,0],p[e,1],'k-',lw=.5)
    ax.set(xlim=(-.05,1.1),ylim=(-.12,.55),aspect='equal',xlabel='x/c',ylabel='y/c');ax.set_title(f['case']+'\nlocal checkpoint '+str(f['checkpoint_iteration_local']),fontsize=10)
cbax=fig.add_axes([.91,.15,.018,.68]);fig.colorbar(coll,cax=cbax,label='log10 nodal |density residual|, cell mean')
fig.suptitle('Own fields only; cyan marks = three global maxima; common color scale')
fig.subplots_adjust(left=.06,right=.87,bottom=.07,top=.9,hspace=.32,wspace=.18)
fig.savefig(OUT/'plots/prediction_v3_cgrid_global_residual_diagnosis.png',dpi=170);plt.close(fig)

# Document a real minor generator weakness without claiming it caused the shock:
# last wake point is overwritten by L, which can enlarge the last streamwise cell.
wake=[]
for level in ['coarse','medium','fine']:
    f=OUT/'simulations'/('v3_cgrid_'+level)/'near_design.json';b=json.loads(f.read_text());x=np.array(b['wake_distribution_x_m']);scale={'coarse':2/3,'medium':1,'fine':1.5}[level]
    wake.append({'case':'v3_cgrid_'+level,'last_dx_m':float(x[-1]-x[-2]),'penultimate_dx_m':float(x[-2]-x[-3]),'nominal_cap_dx_m':.05/scale,'last_to_cap_ratio':float((x[-1]-x[-2])/(.05/scale)),'near_design_sha256':sha(f)})

access={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read own v3 mesh/config/selected checkpoint data; immutable generator and original source geometry. No solver launched and no frozen case modified.','initial_delegation_and_parent_messages_read':True,'files_read_for_this_diagnosis':[str(x.relative_to(ROOT)) for x in [WORK/'build_cgrid.py',WORK/'diagnose_shock.py',base/'build_metadata.json',base/'independent_cgrid_audit.json',base/'own_residual_hotspots.json',base/'checkpoint_selection.json',base/'mesh.su2',base/'near_arrays.npz',base/'mesh_arrays.npz',base/'near_design.json']],'per_case_read_patterns':['v3_cgrid_coarse*/case.cfg','v3_cgrid_coarse*/history.csv (header or last rows only; no expected results)','v3_cgrid_coarse*/checkpoint_selection.json','selected flow_*.vtu listed in numerical report'],'own_geometry_records_read_before_diagnosis':['work/blind_validation/solver_v2/geometry_revision.py','work/blind_validation/solver_v2/mesh.py','work/blind_validation/solver_v2/audit_mesh_family.py','work/blind_validation/solver_v2/quality_and_views.py','work/blind_validation/solver_v2/gradient_regions.json','outputs/projects/proje-15cce2de02/simulations/v2_r2_medium/mesh_audit.json','work/blind_validation/analysis_input/conditions.json','work/setup/freecad_install.json','.agents/skills/iha-muhendislik/SKILL.md'],'forbidden_updated_PROJECT_STATE_AGENTS_reviewer_reference_reports_read':False,'accidental_reference_exposure_this_diagnosis':None,'network_scope':'Only SU2 official documentation/source, Gmsh official docs/tutorial mirror, Diskin–Thomas method PDF. No case target outcome search. Some guessed source paths returned404/cachemiss; GitHub source directory names used only to locate actual centered implementation. Python network request to GitHub tree failed socket permission; no data obtained.'}
(WORK/'access_log_v3_diagnosis.json').write_text(json.dumps(access,indent=2),encoding='utf-8')

note='''# C-grid sayısal teşhisi — kör kayıt

Üretilmiş ağ veya jeneratörde yerel bağlantı/haritalama hatası saptanmadı. Mevcut başarısız yakınsamanın nedeni kesin belirlenmedi. Şok çevresinde katmanlar arası dalgalanma ölçüldü; bunu yalnız “carbuncle” diye adlandırmak için kanıt yeterli değil. Bu kayıt deney karşılaştırması içermez ve hiçbir kabul eşiğini kapatmaz.

## Gerçek ağdan kontroller

Özgün `build_cgrid.py` SHA256 hâlâ `9d385936e598c2371179f8a5a4fe44e44964b2ccc1c5a6d674b1f62912a48637`. SU2 dosyasındaki yakın blok düğümleri ve dörtgen bağlantıları `near_arrays.npz` ile tam eşleşiyor. Bağımsız median-dual yeniden kurulumunda en küçük alt-poligon alanı5,80858e−11m², dual hacim1,22402e−10m²; tüm dual-yüz/primal-kenar iç çarpımları pozitif. İç düğümlerin sabit akış vektör kapanışı ençok3,55271e−15m. Bu, SU2'nin gerçek kaba multigrid aglomerasyonunu denetlemez.

Kendi1000 alanından seçilen x/c0,50–0,54 / y/c0,095–0,125 kutusundaki357 dörtgende köşe Jacobian'ı≥2,21688e−6m², açılar87,509–92,491°, kenar en-boy oranı1,790–3,114. Kutunun üstü dış üçgen arayüzüne kadar ulaşır; asıl en büyük nokta(0,51827748355;0,10376227848)m ise arayüzden0,01781067m içeridedir, tam dört komşusu vardır. Burada negatif hücre, tekil dual hacim, kopuk dikiş veya ani normal aralık sıçraması görülmedi. Normal aralık0,00111317m'dir. Bu geometrik sonuç çözüm doğruluğunun kanıtı değildir.

## Kendi alanındaki ölçüm

İlk1000 alanında x/c0,518277 sütunundaki18 normal düğümde Mach1,21946–1,31586; ardışık eğim9 kez işaret değiştiriyor. Yerel doğrusal eğilimi çıkaran ikinci-fark RMS0,0227699, en büyük0,0532709. Bu, çözümün normal yönde pürüzsüz olmadığını gösteriyor. Noktalar çözücünün kendi düğümleridir; beklenen şok konumundan örnek seçilmedi.

Sonraki dalları tek eski kutuyla açıklamak doğru değil. SabitCFL1 dalının1000 yerel alanında global en büyük kalıntı(0,7219463;0,0828609)m'de0,00226707; MG0 dalının1200 yerel alanında(0,4995433;0,2532513)m'de5,02574e−5 ve dış üçgen bölgededir. Entropy0,2 dalının1200 yerel alanında global en büyük(0,6859110;0,0702130)m'de0,00290824. Her dal aynı ana1000 başlangıcından ilerlediği için bu yerel iterasyonlar tek kesintisiz zaman çizgisi değildir. Alan sürüm/hash'leri JSON'dadır. Farklı bitiş alanları tek başına kontrollü nedensellik kıyası sayılmaz.

Basınç farklarının i/j yönündeki birbirini götürme oranı ilk sütunda tekil olarak0,031'e düşüyor, medyan1. Bu sınırlı ölçüm yaygın sensör iptalini desteklemiyor; gerçek SU2 sensörünün sınır/komşuluk ayrıntılarının yerini almaz. Eski koşulda gerçek doğrusal çözücü artık geçmişi yok; doğrusal tolerans/iterasyon sınırına takıldığı iddia edilmedi.

## Kaynakla doğrulanan sayısal ayrım

Resmî [SU2 convective schemes](https://su2code.github.io/docs_v7/Convective-Schemes/) sayfası JST_MAT için entropy0,05–0,2 ve Jacobian katsayısı yaklaşık8 öneriyor; merkezî yöntemlerde MUSCL akış sınırlayıcısı etkin değil. Dolayısıyla bu koşuda `LIMITER_ITER` değiştirmek doğrudan merkezî şok yakalamayı sınamaz. Entropy artışı sönümü de değiştirir.

Gerçek sürümün [SIMD centered.hpp](https://github.com/su2code/SU2/blob/v8.5.0/SU2_CFD/include/numerics_simd/flow/convection/centered.hpp#L291) uygulamasında `fixFactor` yalnız örtük Jacobian'a girer(310–314); artık akısına girmez(305–307,349–356). Eigenvalue tabanı entropy ile değişir(325–337). ScalarJST dalı ise stretching düzeltmesi çağırır(215–216); MAT dalı çağırmaz. Bu nedenle JST/MAT kıyası aynı ayrık denklem değildir; farkı yalnız eigenvalue ölçeklemesine indirgeyemeyiz. [Factory](https://github.com/su2code/SU2/blob/v8.5.0/SU2_CFD/include/numerics_simd/CNumericsSIMD.cpp#L65) ayrıca merkezî yöntemlerin kaba multigrid seviyesindeLAX kullandığını gösterir.

İlk kontrollü ayrım: aynı ana1000 restartı, aynı ağ/fizik, sabitCFL1, MG3, entropy0,05 ve tüm diğer ayarlar; yalnız `CENTRAL_JACOBIAN_FIX_FACTOR=8`. Parent bu dalı kendi kuyruğunda yönetiyor. Aynı artık denklemi daha iyi yakınsarsa örtük iterasyon koşullanması açıklaması güçlenir; yakınsamazsa elenmez ama tek başına çözüm değildir. `LINSOL`, `CFL_NUMBER`, `MAX_RES` grupları yalnız gözlem kaydı olarak eklenebilir. Sonraki hazır scalarJST dalı sayısal sönüm/method ayrımıdır; yakınsarsa bile kuvvet, y+, ağ ve uzak alan ekranları tekrar gerekir.

## Kapsam ve açık ağ zayıflığı

Normal kılavuzun ilk0,003c'de yumuşak dönmesi açıları değiştiren kayıtlı bir haritalama tercihidir; orada bulunan kötü gradyan olasılığı bu denetimle bütünüyle dışlanmış değildir. Sıcak ilk nokta bu dönüşün çok dışındadır. Dış üçgen geçişinde ve iz bloğunun x/c8 sonundaki kötü açılar ayrıca açık kalır; tüm ağın geometrik kontrolleri geçmiş olsa da bu bölgelerin çözüm etkisi kanıtlanmış değildir.

Kod incelemesinde küçük, gerçek bir dağıtım açığı bulundu: `wake_distribution` son mevcut x noktasını8c ile değiştiriyor; bu, son iz hücresini ilan edilen adım tavanının üstüne çıkarabiliyor. Sayısal ölçüler ekJSON'dadır. Bu uç, ilk şok sıcaklığından çok uzaktadır; çöküş nedeni diye sunulmadı. Sonraki ağ revizyonunda kalan uzunluğu son sabit-adımlı kuyruğa eşit dağıtmak gerekir. Özgün jeneratör/ağ değiştirilmedi; mevcut karşı dallar aynı ağla sürmelidir.

Yüksek en-boy oranına tek başına hata atfedilmedi: [Diskin–Thomas](https://ntrs.nasa.gov/api/citations/20090007493/downloads/20090007493.pdf) eğrilik, stencil ve çözüm yönünün birlikte etkisini inceler. Burada doğrudan ölçülen sıcak hücrelerin oranı yaklaşık2–3'tür; raporun yüksek-anizotropi sonuçları tek başına bu çöküşün teşhisi değildir.

Hiçbir çözücü başlatılmadı; frozenv1/v2 veya mevcutv3 ağ/config/alan değiştirilmedi. GüncellenmişAGENTS/PROJECT_STATE, reviewer ve deney/harici CFD sonuçları okunmadı. Genel sayısal kabul hâlâ açık.
'''
(OUT/'reports/prediction_v3_cgrid_diagnostic_note.md').write_text(note,encoding='utf-8')
extra={'wake_tail_spacing_audit':wake,'suggested_next_revision_only':'Redistribute remaining L-x tail length over ceil(remaining/cap) equal intervals; do not replace the last already accepted x point. Not applied to frozen meshes.','controlled_next_test':{'owner':'parent','only_arithmetic_change':'CENTRAL_JACOBIAN_FIX_FACTOR4->8','same_spatial_residual':True,'seed':'v3_cgrid_coarse/restart_flow_001000.dat','CFL':1,'CFL_ADAPT':'NO','MGLEVEL':3,'ENTROPY_FIX_COEFF':.05},'sources':[{'url':'https://su2code.github.io/docs_v7/Convective-Schemes/','accessed':'web tool, this turn'},{'url':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/numerics_simd/flow/convection/centered.hpp','relevant_lines':[215,216,291,359]},{'url':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/numerics_simd/CNumericsSIMD.cpp','relevant_lines':[65,79]},{'url':'https://raw.githubusercontent.com/su2code/SU2/v8.5.0/SU2_CFD/include/numerics_simd/flow/convection/common.hpp','relevant_lines':[468,484]}],'files_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [WORK/'diagnose_shock.py',WORK/'finalize_diagnosis.py',WORK/'access_log_v3_diagnosis.json',OUT/'reports/prediction_v3_cgrid_shock_diagnosis_v2.json',OUT/'reports/prediction_v3_cgrid_diagnostic_note.md',OUT/'plots/prediction_v3_cgrid_shock_diagnosis_v2.png',OUT/'plots/prediction_v3_cgrid_global_residual_diagnosis.png']}}
(OUT/'reports/prediction_v3_cgrid_diagnostic_manifest.json').write_text(json.dumps(extra,indent=2),encoding='utf-8')
for f in [WORK/'wake_tail_revision_proposal.py',OUT/'reports/prediction_v3_cgrid_unapplied_tail_proposal.json']:
    if f.exists():extra['files_sha256'][str(f.relative_to(ROOT))]=sha(f)
(OUT/'reports/prediction_v3_cgrid_diagnostic_manifest.json').write_text(json.dumps(extra,indent=2),encoding='utf-8')
print(json.dumps(wake,indent=2));print('Report and diagnostic manifest saved. No solver started.')
