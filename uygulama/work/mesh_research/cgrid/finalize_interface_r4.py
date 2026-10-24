"""Freeze the mesh-only R4 evidence, with native mesh and real regional views."""
from pathlib import Path
import os,json,hashlib,datetime,csv
ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).parent;OUT=ROOT/'outputs/projects/proje-15cce2de02'
os.environ['MPLCONFIGDIR']=str(WORK/'mpl_cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
import vtk,gmsh
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from audit_interface_r4 import parse,quality,sha,stat
from interface_distance_r4 import InterfaceSizing

def draw(ax,p,q,t,k,lim,title):
    for co,off in [(q,0),(t,len(q))]:
        v=p[co];sel=(v[:,:,0].max(1)>lim[0])&(v[:,:,0].min(1)<lim[1])&(v[:,:,1].max(1)>lim[2])&(v[:,:,1].min(1)<lim[3])
        coll=PolyCollection(v[sel],array=k['skew'][off:off+len(co)][sel],cmap='viridis',norm=Normalize(0,1),edgecolors='#777777',linewidths=.3);ax.add_collection(coll)
    ax.set(xlim=lim[:2],ylim=lim[2:],aspect='equal',xlabel='x/c',ylabel='y/c');ax.set_title(title,fontsize=10)
    return coll

def mesh_artifacts(folder,p,q,t,m,k):
    ug=vtk.vtkUnstructuredGrid();pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.c_[p,np.zeros(len(p))],deep=True));ug.SetPoints(pts)
    sizes=np.r_[np.full(len(q),4),np.full(len(t),3)];offsets=np.r_[0,np.cumsum(sizes)].astype(np.int64);conn=np.r_[q.ravel(),t.ravel()].astype(np.int64)
    ca=vtk.vtkCellArray();ca.SetData(numpy_to_vtkIdTypeArray(offsets,deep=True),numpy_to_vtkIdTypeArray(conn,deep=True));ug.SetCells(numpy_to_vtk(np.r_[np.full(len(q),9,np.uint8),np.full(len(t),5,np.uint8)],deep=True),ca)
    for key,arr in [('Signed_Area_m2',k['area']),('Min_Corner_Jacobian_m2',k['jac']),('Equiangle_Skew',k['skew'])]:
        da=numpy_to_vtk(arr,deep=True);da.SetName(key);ug.GetCellData().AddArray(da)
    path=folder/'mesh_geometry_only.vtu';wr=vtk.vtkXMLUnstructuredGridWriter();wr.SetFileName(str(path));wr.SetInputData(ug);wr.SetDataModeToAppended();wr.EncodeAppendedDataOff();assert wr.Write()==1
    vr=vtk.vtkXMLUnstructuredGridReader();vr.SetFileName(str(path));vr.Update();back=vr.GetOutput();vcheck={'nodes':back.GetNumberOfPoints(),'fluid_cells':back.GetNumberOfCells(),'coordinates_bitwise_equal':bool(np.array_equal(vtk_to_numpy(back.GetPoints().GetData())[:,:2],p)),'area_array_bitwise_equal':bool(np.array_equal(vtk_to_numpy(back.GetCellData().GetArray('Signed_Area_m2')),k['area']))}
    assert vcheck['nodes']==len(p) and vcheck['fluid_cells']==len(q)+len(t) and vcheck['coordinates_bitwise_equal'] and vcheck['area_array_bitwise_equal']
    # Discrete display/export entities only; source curve and fluid nodes do not move.
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add(folder.name);gmsh.model.addDiscreteEntity(2,1)
    gmsh.model.mesh.addNodes(2,1,np.arange(1,len(p)+1),np.c_[p,np.zeros(len(p))].ravel())
    gmsh.model.mesh.addElementsByType(1,3,np.arange(1,len(q)+1),(q+1).ravel());gmsh.model.mesh.addElementsByType(1,2,np.arange(len(q)+1,len(q)+len(t)+1),(t+1).ravel())
    gmsh.model.addPhysicalGroup(2,[1],3);gmsh.model.setPhysicalName(2,3,'FLUID');count=len(q)+len(t)
    for tag,(name,e) in enumerate(m.items(),1):
        gmsh.model.addDiscreteEntity(1,tag);gmsh.model.mesh.addElementsByType(tag,1,np.arange(count+1,count+len(e)+1),(e+1).ravel());gmsh.model.addPhysicalGroup(1,[tag],tag);gmsh.model.setPhysicalName(1,tag,name);count+=len(e)
    gmsh.option.setNumber('Mesh.Binary',1);gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.write(str(folder/'mesh_geometry_only.msh'));gmsh.finalize()
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(folder/'mesh_geometry_only.msh'));tags,co,_=gmsh.model.mesh.getNodes();order=np.argsort(tags);backp=np.asarray(co).reshape(-1,3)[order,:2];ty,et,ns=gmsh.model.mesh.getElements(2)
    gcheck={'nodes':len(tags),'fluid_cells':sum(len(a) for a in et),'coordinates_bitwise_equal':bool(np.array_equal(backp,p)),'boundary_names':sorted(gmsh.model.getPhysicalName(d,t) for d,t in gmsh.model.getPhysicalGroups(1))};gmsh.finalize()
    assert gcheck['nodes']==len(p) and gcheck['fluid_cells']==len(q)+len(t) and gcheck['coordinates_bitwise_equal'] and gcheck['boundary_names']==['AIRFOIL','FARFIELD']
    return {'VTU':vcheck,'MSH4_binary':gcheck,'scope':'Geometry and mesh-quality fields only, no flow solution.'}

family=json.loads((OUT/'reports/prediction_v3_cgrid_interfacer4_family.json').read_text());assert family['all_three_levels_completed'];rows=[];reports=[];gfig,gaxs=plt.subplots(2,3,figsize=(14,8))
for col,level in enumerate(['coarse','medium','fine']):
    name='v3_cgrid_interfacer4_'+level;folder=OUT/'simulations'/name;r=json.loads((folder/'interface_revision_audit.json').read_text());reports.append(r);p,q,t,m=parse(folder/'mesh.su2');k=quality(p,q,t);p0,q0,t0,m0=parse(ROOT/r['baseline']['path']);k0=quality(p0,q0,t0)
    exported=mesh_artifacts(folder,p,q,t,m,k)
    fig,axs=plt.subplots(2,3,figsize=(14,8));cy=np.tan(np.deg2rad(2.31))*7;views=[('LE interface',(-.085,.025,-.065,.065)),('TE upper interface',(.96,1.04,.04,.085)),('upper end corner',(7.9,8.09,cy+.21,cy+.39))]
    for row,(pp,qq,tt,kk,label) in enumerate([(p0,q0,t0,k0,'tail-r2 before'),(p,q,t,k,'interface-r4 after')]):
        for ax,(label2,lim) in zip(axs[row],views):coll=draw(ax,pp,qq,tt,kk,lim,label+' / '+label2)
    fig.suptitle(name+' actual exported mesh; common equiangle-skew color scale 0..1');fig.tight_layout(rect=(0,0,.94,.95));cax=fig.add_axes([.95,.2,.012,.6]);fig.colorbar(coll,cax=cax);fig.savefig(OUT/'plots'/f'prediction_{name}_LE_TE_end.png',dpi=170);plt.close(fig)
    worst=r['after']['worst_global'][0];c=np.array(worst['center_m']);radius=.12
    for row,(pp,qq,tt,kk,label) in enumerate([(p0,q0,t0,k0,'tail-r2 before'),(p,q,t,k,'interface-r4 after')]):
        coll=draw(gaxs[row,col],pp,qq,tt,kk,(c[0]-radius,c[0]+radius,c[1]-radius,c[1]+radius),level+' '+label+'\nnew global worst position')
        if row==1:
            v=np.asarray(worst['vertices_m']);gaxs[row,col].plot(*np.r_[v,v[:1]].T,'r-',lw=1.3)
    # Independent shape-matching/normal preservation is already in the audit;
    # provide a compact table for its interpretation, without flow acceptance.
    tr0=r['interface_normal_transition_before']['regions'];tr=r['interface_normal_transition_after']['regions']
    rows.append({'case':name,'cells':r['after']['cells'],'baseline_cells':r['before']['cells'],'increase_percent':100*(r['after']['cells']/r['before']['cells']-1),'max_skew_before':r['before']['equiangle_skew']['max'],'max_skew_after':r['after']['equiangle_skew']['max'],'p99_skew_before':r['before']['equiangle_skew']['p99'],'p99_skew_after':r['after']['equiangle_skew']['p99'],'global_worst':worst,'tail_min_angle_before_deg':r['before']['tail_local']['angle_min_deg']['min'],'tail_min_angle_after_deg':r['after']['tail_local']['angle_min_deg']['min'],'LE_height_ratio_max_before_after':[tr0['LE_interface']['outside_over_inside_height_ratio']['max'],tr['LE_interface']['outside_over_inside_height_ratio']['max']],'TE_height_ratio_max_before_after':[tr0['TE_interface']['outside_over_inside_height_ratio']['max'],tr['TE_interface']['outside_over_inside_height_ratio']['max']],'normal_transition':r['interface_normal_transition_after'],'exact_distance_check':r['sizing']['distance_audit'],'near_block_preserved':all(r['tailr2_near_block_equality'].values()),'geometric_checks_passed':r['checks_passed'],'artifact_roundtrip':exported,'geometry':r['geometry']})
    rows[-1]['all_cell_angle_min_deg']=float(k['angle'][:,0].min())
    rows[-1]['farfield_boundary_coordinate_set_bitwise_equal_tailr2']=bool(np.array_equal(np.unique(p[m['FARFIELD'].ravel()],axis=0),np.unique(p0[m0['FARFIELD'].ravel()],axis=0)))
gfig.suptitle('R4 remaining global worst triangles (red); all lie outside 1c interface-distance support')
gfig.tight_layout(rect=(0,0,.94,.95));cax=gfig.add_axes([.95,.2,.012,.6]);gfig.colorbar(coll,cax=cax);gfig.savefig(OUT/'plots/prediction_v3_cgrid_interfacer4_global_worst.png',dpi=170);plt.close(gfig)
table='|Ağ|Hücre önce→sonra|Artış|Genel max skew önce→sonra|LE dış/iç normal yükseklik max önce→sonra|\n|---|---:|---:|---:|---:|\n'
for r in rows:table+=f"|{r['case'].split('_')[-1]}|{r['baseline_cells']:,}→{r['cells']:,}|%{r['increase_percent']:.2f}|{r['max_skew_before']:.5f}→{r['max_skew_after']:.5f}|{r['LE_height_ratio_max_before_after'][0]:.2f}→{r['LE_height_ratio_max_before_after'][1]:.2f}|\n"
note='''# C-grid interface-r4 — gerçek ağ denetimi

Arayüz teğetsel boyutunu dışa taşımak üç seviyede genel en kötü çarpıklığı düşürdü; tüm yakın blok, duvar, r2 kaynak eğrisi ve200c dış alan korunuyor. Bu geometri/ağ sonucu CFD yakınsaması veya fiziksel doğrulama değildir.

'''+table+'''
Eski dış boyut callback'i `MeshSizeExtendFromBoundary=0` altında arayüzün küçük teğetsel kenarlarının boyutunu dışa taşımıyordu. Bu bizim callback/boyut geçişi eksikliğimizdir; Gmsh BoundaryLayer algoritmasının arızası diye yorumlanmadı. [Gmsh mesh-size dokümanı ve t10](https://gmsh.info/doc/texinfo/#t10) uzaklık tabanlı Distance/Threshold boyutlandırmayı, callback ve sınır boyutlarının uzatılma seçeneğini açıklar. Burada gerçek ihrac edilmiş arayüz parçalarına tam uzaklık kullanıldı; kaynak profil yeniden çizilmedi.

Her arayüz düğümünde h=min(önceki,sonraki gerçek kenar uzunluğu). En yakın kapalı parça üzerindeki izdüşümde h doğrusal enterpole edilir. d≤0,25c için hedef min(eski_h,h_interface+0,25d);0,25–1c arası kübik smoothstep ile eski_h'ye dönülür. d≥1c'de eski callback değeri bit düzeyinde aynen döner. En yakın-parça hızlandırması midpoint cKDTree'dir; global en büyük yarı-kenar uzunluğu aday yarıçapını muhafazakâr yapar. Her seviyede sabit tohumlu1200 rastgele noktada bütün gerçek parçalara brute-force mesafe/izdüşüm kıyası yapıldı: en büyük uzaklık ve h enterpolasyon farkı0m; yanlış d<1 atlaması0. R3'ün32c'ye kadar uzayan sınırsız boyut etkisi bu sürümde yoktur. Bütün dış üçgenler yeniden üretildiği için bağlantı değişimi, boyut fonksiyonunun kompakt desteğinin dışına yayılabilir.

Actual SU2 dosyasından pozitif alan ve tüm köşe Jacobian'ı, tek bağlı akış bileşeni, kapalı AIRFOIL/FARFIELD, sıfır işaretsiz/çok-komşulu/ters yönlü iç kenar ve sıfır çakışık düğüm kontrolleri üç seviyede geçti. Tail-r2 kaynak fonksiyonları AST ile aynı; yeniden hesaplanan ve gerçek SU2'ye yazılan yakıncoords/quads/grid/body/wall bit düzeyinde aynı. Kaynak65 noktaya ve aynı r2 eğrisine sapmalar denetim JSON'larında; geometri payload SHA050ee43ead96df3cbc2a34649cf06c0839ed6fe47ae8aaf4955744d19f49cf5a. Orta/ince karşılaştırıcılar R3 sırasında üretilmiş geometry-only tail-r2 dosyalarıdır; tekrar yazılmadılar.

Normal geçiş gerçek arayüz kenarındaki komşu quad/triangle üzerinden ölçüldü: dış üçgen h=2A/kenar, iç quad h=karşı iki tepenin kenara dik uzaklık ortalaması. LE, TE, aft gövde, yatay iz ve dikey uç ayrı raporlandı. İnce TE kısa kenarları ile dikey iz ucunda dış/iç normal yükseklik oranı1'e yakın değildir; uçtaki çok uzun iz quad'ının yanındaki küçük dış üçgen oranı ayrıca korunur. Bu oran tek başına hatalı hücre veya çözülmüş sınır tabakası kanıtı değildir; açı/Jacobian ve gelecek akış duyarlılığıyla birlikte değerlendirilmeli.

Yeni global en kötü konumlar kaba(9,459155;0,350182)m, orta(9,394876;0,455634)m, ince(9,896578;0,194787)m: LE/TE arayüzlerinden dış iz bölgesine taşındı. Global min açılar sırasıyla10,01°/12,30°/4,95°; ince en kötü çarpıklık0,91748 hâlâ açıktır. Bu noktalar1c kompakt desteğin dışındadır ve eski dış boyut callback'i aynen korunmuştur. Eski hwake'nin x<10 dalındaki geçiş ile ilgili olasılık bu aşamada nedensel olarak sınanmadı. Hiçbir sonradan açı/skew cutoff'u eklenmedi ve kötü hücreler çıkarılmadı.

Gerçek LE/TE/uç önce-sonra görselleri ve global en kötü üçgen görseli üretildi. mesh_geometry_only.vtu ve native MSH4 binary dosyaları yalnız ağ/kalite verisi içerir; geri okumada düğüm/hücre/koordinat ve sınır adları doğrulandı. Kaynak kodu, girdiler, meshler ve raporlar SHA256 manifestinde kayıtlı. Özgün, tail-r2 ve R3 dosyaları değiştirilmedi.

Bu aşamada CFD başlatılmadı; y+, Cp, kuvvet, kalıntı/ağ/uzak-alan akış kabulü değerlendirilmedi. Parent'ın ayrı başlangıç/çözücü tanıları bu ağ kalitesi sonucuna dahil edilmedi. Reviewer/hedef deney/harici CFD sonuçlarına veya güncellenmiş AGENTS/PROJECT_STATE/kullanıcı raporlarına erişilmedi. Bu, kaynak yöntemle gerekçelendirilmiş sabit geometri ağ prototipidir; keyfî CAD hizmeti veya genel CFD yeterliliği değildir.
'''
(OUT/'reports/prediction_v3_cgrid_interfacer4_report.md').write_text(note,encoding='utf-8')
(OUT/'reports/prediction_v3_cgrid_interfacer4_summary.json').write_text(json.dumps({'scope':'Mesh-only R4; no CFD launched; no flow acceptance','all_three_levels_complete':True,'geometry_topology_checks_passed':all(r['geometric_checks_passed'] for r in rows),'levels':rows},indent=2))
files=[]
for l in ['coarse','medium','fine']:files.extend(x for x in (OUT/'simulations'/('v3_cgrid_interfacer4_'+l)).iterdir() if x.is_file())
files.extend(OUT/'plots'/f'prediction_v3_cgrid_interfacer4_{l}_LE_TE_end.png' for l in ['coarse','medium','fine']);files.append(OUT/'plots/prediction_v3_cgrid_interfacer4_global_worst.png')
files.extend(OUT/'reports'/f'prediction_v3_cgrid_interfacer4_{n}' for n in ['report.md','summary.json','family.json'])
alpath=WORK/'access_log_interface_r4.json';al=json.loads(alpath.read_text());al['finalize_reads_and_hashed_files']=sorted({str(f.relative_to(ROOT)) for f in files}|set(family['input_sha256'])|{r['baseline']['path'] for r in reports});al['method_sources_browsed']=['https://gmsh.info/doc/texinfo/#t10','https://gmsh.info/doc/texinfo/#Structured-grids'];al['additional_sources_read']=['work/mesh_research/cgrid/interface_distance_r4.py','work/mesh_research/cgrid/finalize_interface_r4.py'];al['expected_reference_exposure']=None;alpath.write_text(json.dumps(al,indent=2))
manifest={'scope':'Three real interface-r4 meshes; geometric checks only. No CFD prediction.','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_files_sha256':{str(f.relative_to(ROOT)):sha(f) for f in files},'source_script_sha256':{str((WORK/f).relative_to(ROOT)):sha(WORK/f) for f in ['build_cgrid.py','build_cgrid_tail_r2.py','build_cgrid_interface_r4.py','interface_distance_r4.py','audit_interface_r4.py','finalize_interface_r4.py']},'input_sha256':family['input_sha256'],'contract_sha256':'a3106e323f9a5671067b69fded039fa8b3d2aae607514ec114a949b501b91c69','contract_source':'Parent supplied hash only; contract not read. All flow acceptances remain unevaluated.','CFD_launched':False,'flow_numerical_acceptance':None,'access_log':str((WORK/'access_log_interface_r4.json').relative_to(ROOT)),'access_log_sha256':sha(WORK/'access_log_interface_r4.json')}
manifest['runtime_versions']={'Gmsh':gmsh.__version__,'VTK':vtk.vtkVersion.GetVTKVersion(),'numpy':np.__version__}
(OUT/'reports/prediction_v3_cgrid_interfacer4_mesh_manifest.json').write_text(json.dumps(manifest,indent=2))
print([(r['case'],r['cells'],r['max_skew_after'],r['global_worst']['center_m']) for r in rows]);print('Recorded deliverable hashes',len(files))
