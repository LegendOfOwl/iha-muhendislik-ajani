"""Views of the native solution, retaining its actual fluid-cell connectivity."""
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

def render(out):
    out=Path(out); result=json.loads((out/'reports/profile_cfd_results.json').read_text())
    case=json.loads((out/'data/profile_cfd_case.json').read_text()); source=ROOT/case['airfoil']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=result['geometry_sha256']:raise ValueError('Source geometry changed')
    plots=out/'plots';plots.mkdir(exist_ok=True)
    import sys
    sys.path.insert(0,str(ROOT/'work/geometry'))
    from parametric_wing import profile
    xy,le,_=profile(source)
    def camber(x):
        upper=xy[:le+1][::-1];lower=xy[le:]
        return .5*(np.interp(x,upper[:,0],upper[:,1])+np.interp(x,lower[:,0],lower[:,1]))
    fig,ax=plt.subplots(figsize=(9,5));grids={};checks=[]
    for row,color in zip(result['results'],['#a46820','#087e8b']):
        folder=Path(row['folder']);reader=vtk.vtkXMLUnstructuredGridReader();reader.SetFileName(str(folder/'flow.vtu'));reader.Update();grid=reader.GetOutput()
        if grid.GetNumberOfCells()!=row['mesh']['cells']:raise ValueError('Volume mesh cell count differs')
        locator=vtk.vtkStaticPointLocator();locator.SetDataSet(grid);locator.BuildLocator()
        with (folder/'surface_flow.csv').open() as f:wall=list(csv.DictReader(f))
        points=np.array([[float(r['x']),float(r['y']),0] for r in wall]);ids=[locator.FindClosestPoint(p) for p in points]
        distance=max(np.linalg.norm(np.array(grid.GetPoint(i))-p) for i,p in zip(ids,points))
        if distance>1e-7:raise ValueError('Wall/volume mapping failed')
        cp=vtk_to_numpy(grid.GetPointData().GetArray('Pressure_Coefficient'))
        if not np.all(np.isfinite(cp)):raise ValueError('Nonfinite native Cp')
        table=np.column_stack([points[:,:2],cp[ids]])
        np.savetxt(folder/'wall_cp.csv',table,delimiter=',',header='x_m,y_m,Cp',comments='')
        upper=table[:,1]>=camber(table[:,0])
        for mask,style,label in [(upper,'-','upper'),(~upper,'--','lower')]:
            t=table[mask];t=t[np.argsort(t[:,0])];ax.plot(t[:,0],t[:,2],style,color=color,label=row['level']+' '+label)
        checks.append({'level':row['level'],'volume_cells':grid.GetNumberOfCells(),'wall_mapping_max_error_m':float(distance),'field_finite':True})
        grids[row['level']]=grid
    ax.invert_yaxis();ax.set(xlabel='x/c',ylabel='Cp',title='NACA2412: native SU2 Euler, Mach 0.15, alpha 2 deg');ax.grid(alpha=.2);ax.legend(fontsize=9);fig.tight_layout();fig.savefig(plots/'profile_cp.png',dpi=150);plt.close(fig)
    g=grids['fine'];geometry=vtk.vtkGeometryFilter();geometry.SetInputData(g);geometry.Update();tri=vtk.vtkTriangleFilter();tri.SetInputConnection(geometry.GetOutputPort());tri.Update();poly=tri.GetOutput()
    pts=vtk_to_numpy(poly.GetPoints().GetData());cells=vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1,4)[:,1:]
    cp=vtk_to_numpy(poly.GetPointData().GetArray('Pressure_Coefficient'));centers=pts[cells].mean(axis=1)
    cells=cells[(centers[:,0]>-.3)&(centers[:,0]<1.3)&(np.abs(centers[:,1])<.4)]
    triangulation=mtri.Triangulation(pts[:,0],pts[:,1],triangles=cells)
    pos=Path(result['results'][-1]['folder'])/'pressure_nearfield.pos'
    with pos.open('w',encoding='ascii') as f:
        f.write('View "SU2 Euler Cp, actual fluid cells" {\n')
        for ids in cells:f.write('ST('+','.join(f'{v:.10g}' for v in pts[ids].reshape(-1))+'){'+','.join(f'{v:.10g}' for v in cp[ids])+'};\n')
        f.write('};\n')
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(pos));tags=gmsh.view.getTags()
        readback=len(tags)==1 and list(gmsh.view.getListData(tags[0])[1])==[len(cells)]
        if not readback:raise ValueError('Gmsh view readback failed')
    finally:gmsh.finalize()
    fig,axs=plt.subplots(2,1,figsize=(10,7),sharex=True)
    image=axs[0].tricontourf(triangulation,cp,levels=np.linspace(-1.8,1.1,45),cmap='coolwarm',extend='both');fig.colorbar(image,ax=axs[0],label='Cp')
    axs[1].triplot(triangulation,color='#395166',linewidth=.24)
    for ax in axs:ax.set(xlim=(-.2,1.2),ylim=(-.26,.3),aspect='equal',ylabel='y/c')
    axs[0].set_title('Computed inviscid pressure field');axs[1].set(xlabel='x/c',title='Actual new fluid mesh; airfoil interior excluded');fig.tight_layout();fig.savefig(plots/'profile_field_mesh.png',dpi=150);plt.close(fig)
    # Source-coordinate drawing is separate from the mesher's interpolation.
    cad=out/'cad';cad.mkdir(exist_ok=True)
    polyline=' '.join(f'{70+950*x:.4f},{190-950*y:.4f}' for x,y in xy)
    (cad/'source_profile.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 320"><rect width="1100" height="320" fill="white"/><text x="55" y="45" font-family="sans-serif" font-size="22">NACA2412 source coordinates — normalized x/c, y/c</text><line x1="70" y1="190" x2="1020" y2="190" stroke="#bbb"/><polygon points="'+polyline+'" fill="#e3f1f4" stroke="#126778" stroke-width="2"/><text x="55" y="285" font-family="sans-serif" font-size="16">Source polyline drawing; CFD boundary uses Gmsh splines. This is not a 3D CAD solid.</text></svg>',encoding='utf-8')
    view={'timestamp':datetime.now(timezone.utc).isoformat(),'source_geometry_sha256':result['geometry_sha256'],'conditions_sha256':result['conditions_sha256'],'checks':checks,'gmsh_pressure_view':str(pos),'gmsh_triangles':len(cells),'gmsh_readback_passed':readback,'scope':result['analysis_scope']}
    (out/'reports/profile_field_checks.json').write_text(json.dumps(view,indent=2),encoding='utf-8')
    rows=''.join(f"<tr><td>{r['level']}</td><td>{r['mesh']['cells']:,}</td><td>{r['CL']:.6f}</td><td>{r['CD_numerical_inviscid']:.6f}</td><td>{r['CL_tail_range']:.3g}</td></tr>" for r in result['results'])
    relative_pos=os.path.relpath(pos,out/'reports').replace('\\','/')
    html=f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Yeni profil ağı ve CFD</title><style>body{{font:16px/1.6 Segoe UI,sans-serif;background:#eef3f6;color:#183043;max-width:1060px;margin:35px auto;padding:20px}}section{{background:white;padding:25px;border-radius:12px;margin:20px 0}}img{{width:100%}}td,th{{padding:10px;border-bottom:1px solid #ccd8e0;text-align:left}}a{{color:#087f88}}</style><h1>Kaynak profilden yeni ağ ve gerçek CFD</h1><p>Profil ağı ve CFD doğrulaması · 19 Ekim 2026</p>
<section><p>UIUC NACA2412 koordinatlarından Gmsh ile yeni akış ağı oluşturuldu; SU2 8.5.0 yerel Euler çözücüsü gerçekten çalıştırıldı. Koşullar araç yeterliliği için varsayımdır: Mach 0,15, alfa 2°, veter 1 m, uzak alan ±20 veter. Gerçek İHA gereksinimi değildir.</p><p><strong>Bu koşula ait sayısal ön kabul: {'geçti' if result['quality_passed'] else 'açık'}.</strong> İki ağdaki CL değişimi %{100*result['CL_grid_relative_change']:.2f}; aynı DAT ve koşullarla bağımsız XFOIL inviscid CL={result['reference']['CL']:.4f}, ince ağ farkı %{100*result['CL_reference_relative_difference']:.2f}. Bu iki yöntem arasında uyum deneysel doğrulama değildir.</p><table><tr><th>Ağ</th><th>Hücre</th><th>CL</th><th>Sayısal CD</th><th>Son 100 CL aralığı</th></tr>{rows}</table><p>Önceden belirlenen eşikler: CL ağ değişimi &lt;%3; XFOIL farkı &lt;%5; son 100 CL aralığı &lt;0,0002; CD aralığı &lt;0,00002; yoğunluk kalıntısı log10 &lt;−7; ince |sayısal CD| &lt;0,003. Bunlar sınırlı bir yeterlilik ekranıdır; iki ağ evrensel ağ bağımsızlığı kanıtı değildir.</p></section>
<section><img src="../plots/profile_field_mesh.png"><p>Görsel gerçek hücre bağlantıları ve çözülen basınç alanından üretildi. Profilin içi akış hücreleriyle doldurulmadı. Gmsh görünümü {len(cells):,} gösterim üçgeniyle geri okundu.</p><img src="../plots/profile_cp.png"></section>
<section><h2>Sınırlar</h2><p>Euler modeli sürtünme, sınır tabakası ve ayrılmayı çözmez. Negatif sayısal CD fiziksel itki veya gerçek profil sürüklemesi değildir; burada sayısal hata göstergesi olarak raporlanır. Geçiş/türbülans, stall, uzak alan duyarlılığı ve üç boyutlu kanat/uçak CFD kabulü açık kalır. Eski RANS çalışmasının %22,84 sürükleme ağ değişimi ve y+ kabulü bu sonuçla kapanmadı.</p><p>İlk −8 kalıntı hedefinde kuvvet kararlılığı kabul edilmedi; eski çalışma saklandı. Aynı ağ ve koşullarda −10 hedefli devam çözümü kabulü geçti. Yeniden çalıştırma ince ağda doğrudan −10 hedefini kullanır.</p><p><a href="profile_cfd_results.json">Ham kuvvet ve kabul kaydı</a> · <a href="profile_field_checks.json">Alan eşleme ve Gmsh kontrolü</a> · <a href="{escape(relative_pos)}">Gmsh basınç alanı</a> · <a href="../cad/source_profile.svg">Kaynak profil çizimi</a> · <a href="../data/profile_cfd_case.json">Koşullar ve kaynak</a></p><p>Yöntem kaynakları: <a href="https://m-selig.ae.illinois.edu/ads/coord/naca2412.dat">UIUC profil koordinatları</a>, <a href="https://gmsh.info/doc/texinfo/#t10">Gmsh ağ boyutu alanları</a>, <a href="https://su2code.github.io/docs_v7/Quick-Start/">SU2 resmi örnek yöntemi</a>.</p></section></html>'''
    (out/'reports/profile_cfd.html').write_text(html,encoding='utf-8')
    return view

if __name__=='__main__':
    print(json.dumps(render(Path(os.environ['UAV_OUTPUT_ROOT'])),indent=2))
