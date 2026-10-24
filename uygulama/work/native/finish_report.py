"""Summarize measured native-tool results and inspect native span loads."""
import json
import os
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def main():
    native=json.loads((OUT/'reports/external_solver_results.json').read_text(encoding='utf-8'))
    cad=json.loads((OUT/'reports/external_cad_results.json').read_text(encoding='utf-8'))
    source=Path(native['native_cases'][2]['folder'])/'model.lod'
    alpha=None;header=None;rows=[]
    for line in source.read_text(encoding='utf-8',errors='replace').splitlines():
        fields=line.split()
        if line.startswith('AoA_'):
            alpha=float(fields[1])
        elif line.startswith('Iter '):
            header=fields
        elif header and len(fields)==len(header) and alpha is not None and abs(alpha-4)<1e-9:
            try:
                rows.append([float(value) if 'nan' not in value.lower() else float('nan') for value in fields])
            except ValueError:
                pass
    load=pd.DataFrame(rows,columns=header)
    required=['Yavg','Cl','Cdi','Chord','dSpan','dArea']
    if load.empty or not np.isfinite(load[required].to_numpy()).all():
        raise RuntimeError('No finite native span load data at alpha=4')
    load=load.sort_values('Yavg')
    load[required].to_csv(OUT/'data/native_spanload_alpha4.csv',index=False)
    cl_integrated=float((load.Cl*load.Chord*load.dSpan).sum()/.5)
    polar=pd.DataFrame(native['native_cases'][2]['polar'])
    global_cl=float(polar.loc[np.isclose(polar.AoA,4),'CLtot'].iloc[0])
    difference=abs(cl_integrated/global_cl-1)
    load_check={'name':'VSPAERO açıklık yükü / toplam kaldırma tutarlılığı',
                'passed':bool(difference<.02),'criterion':'Yerel Cl*c*dy integralinden CL, toplam CL ile <%2 fark',
                'evidence':{'integrated_CL':cl_integrated,'global_CL':global_cl,'relative_difference':difference,'stations':len(load)}}
    assembly=pd.DataFrame(native['native_cases'][-1]['polar'])
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    axes[0].plot(polar.AoA,polar.CLtot,'o-',label='VSPAERO: isolated wing')
    axes[0].plot(assembly.AoA,assembly.CLtot,'s-',label='VSPAERO: wing + tails')
    axes[0].set(xlabel='Angle of attack [deg]',ylabel='CL',title='Native 3D lifting-surface analyses')
    axes[0].legend(fontsize=8)
    axes[1].plot(polar.CDi,polar.CLtot,'o-')
    axes[1].set(xlabel='Induced drag coefficient CDi',ylabel='CL',title='Wing induced-drag polar')
    axes[1].xaxis.set_major_locator(MaxNLocator(4))
    axes[1].ticklabel_format(axis='x',style='sci',scilimits=(-3,-3))
    for item in native['xfoil_cases']:
        frame=pd.DataFrame(item['polar'])
        axes[2].plot(frame.alpha,frame.CL,'o-',label='NACA '+item['airfoil'])
    axes[2].set(xlabel='Angle of attack [deg]',ylabel='2D CL',title='Native XFOIL: Re=500,000; Ncrit=9')
    axes[2].legend(fontsize=8)
    for ax in axes: ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(OUT/'plots/native_aerodynamics.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].plot(load.Yavg,load.Cl,'o-',markersize=3)
    axes[0].set(xlabel='Span coordinate y [m]',ylabel='Section Cl',title='Native VSPAERO span load at 4 deg')
    axes[1].plot(assembly.AoA,assembly.CMytot,'s-')
    axes[1].set(xlabel='Angle of attack [deg]',ylabel='CMy at the specified reference point',title='Wing + tails: moment curve')
    for ax in axes: ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(OUT/'plots/native_loads_moments.png',dpi=160);plt.close(fig)
    checks=native['checks']+cad['checks']+[load_check]
    passed=sum(item['passed'] for item in checks)
    all_ok=all(item['passed'] for item in checks)
    now=datetime.now(ZoneInfo('Europe/Istanbul'))
    result={'timestamp':now.isoformat(),'passed':all_ok,'passed_checks':passed,'total_checks':len(checks),
            'checks':checks,'source_run':native['run_directory'],
            'actual_aircraft_feasibility':'not_assessed','synthetic_demonstrator':True}
    (OUT/'reports/external_test_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    fine=native['native_cases'][2]
    four=next(row for row in fine['polar'] if abs(row['AoA']-4)<1e-9)
    lines=['# OpenVSP, VSPAERO, XFOIL ve CAD — gerçek araç testleri','',
           f"Tarih: {now.strftime('%d.%m.%Y %H:%M')} (Europe/Istanbul)",'',
           f"**Sonuç: {passed}/{len(checks)} kontrol geçti. {'Bu aşamanın kontrolleri tamamlandı.' if all_ok else 'Açık kontroller aşağıda belirtilmiştir.'}**",'',
           'OpenVSP 3.55.0 ve onun yerel VSPAERO 7.2.2 çözücüsü ile XFOIL 6.99 doğrudan çalıştırıldı. Python bu programları başlatıp dosyalarını okuyor; 3D/2D çözümler bu harici programlardan geliyor.','',
           '## Model ve analiz kapsamı','',
           '**Bu bir entegrasyon örneğidir; gerçek İHA için seçilmiş veya optimize edilmiş tasarım değildir.** Boyutların tümü test varsayımıdır.','',
           '| Özellik | Test değeri |','|---|---|',
           '| Referans kanat | 2 m açıklık, 0,25 m veter, 0,50 m² alan, AR=8, NACA 0012 |',
           '| Akış | 30 m/s, 1,225 kg/m³, referans Re=500.000, sıkıştırılamaz yaklaşım |',
           '| Açı taraması | −4, −2, 0, 2, 4, 6, 8 derece |',
           '| 3D araç | Yerel VSPAERO, ince taşıyıcı yüzeyler |',
           '| 2D araç | Yerel XFOIL, NACA 0012 ve NACA 2412; Ncrit=9 |',
           '| Örnek uçak geometrisi | Kanat, yatay/dikey kuyruk ve gövde; gerçek STEP sınır kutusu: '+', '.join(f'{v:.1f}' for v in cad['bbox_mm'])+' mm |','',
           'Gövde modelde çizildi ve CAD dosyasına aktarıldı; aerodinamik analiz kümesinden açıkça çıkarıldı. Kanat–kuyruk sonuçları bu taşıyıcı yüzeyler içindir. VSPAERO CD0 kestirimi doğrulanmış tüm uçak sürüklemesi olarak kullanılmadı.','',
           '## Ölçülen başlıca sonuçlar','',
           f"- Referans kanatta 4° için VSPAERO CL = **{four['CLtot']:.6f}**, CDi = **{four['CDi']:.6f}**.",
           f"- Orta -> ince ağ CL değişimi: **%{100*native['mesh_relative_CL_change']:.3f}**; CDi değişimi: **%{100*native['mesh_relative_CDi_change']:.3f}**.",
           f"- Aynı kanatta AeroSandbox VLM ile CL farkı: **%{100*native['cross_solver_CL_relative_difference']:.3f}**. Bu bir ayrı çözücü tutarlılık kontrolüdür; deneysel doğrulama değildir.",
           f"- Açıklık yüklerinin integralinden CL = **{cl_integrated:.6f}**; toplam CL ile fark **%{100*difference:.3f}**.",
           '- XFOIL iki profil için yedişer viskoz polar noktası üretti. Geçerli noktalar, ham program çıktısından alındı.',
           '- OpenVSP metre birimiyle STEP dışa aktardı; CAD içe aktarımında 2000 mm açıklık ve 250 mm veter doğrulandı.',
           '- Kapalı NACA kanat zarfı ayrıca üretildi; analitik kesit integrali ve STEP tekrar okuma kontrolleri geçti. Bu zarfın hacmi yapısal malzeme/kütle hesabı değildir.','',
           '## Görseller','',
           f"![Gerçek OpenVSP CAD geometrisi]({(OUT/'plots/aircraft_geometry.png').as_posix()})",'',
           f"![Yerel programlardan aerodinamik sonuçlar]({(OUT/'plots/native_aerodynamics.png').as_posix()})",'',
           f"![Açıklık yükü ve moment]({(OUT/'plots/native_loads_moments.png').as_posix()})",'',
           '## Açılabilir dosyalar','',
           '- [OpenVSP modelini aç](../OpenVSP-Modelini-Ac.cmd)',
           '- [Harici testleri yeniden çalıştır](../Harici-Testleri-Calistir.cmd)',
           '- [Düzenlenebilir OpenVSP modeli](../cad/aircraft_demo.vsp3)',
           '- [STEP yüzey modeli](../cad/aircraft_demo.step)',
           '- [Kapalı referans kanat STEP](../cad/reference_wing_solid.step)',
           '- [A3 üç görünüş çizimi — SVG](../cad/aircraft_three_view.svg)',
           '- [Üst DXF](../cad/aircraft_top.dxf), [yan DXF](../cad/aircraft_side.dxf), [ön DXF](../cad/aircraft_front.dxf)',
           '- [Açı taraması CSV](../data/native_wing_polar.csv), [açıklık yükü CSV](../data/native_spanload_alpha4.csv)',
           '- [XFOIL NACA 0012](../data/xfoil_naca0012_polar.csv), [XFOIL NACA 2412](../data/xfoil_naca2412_polar.csv)','',
           f"Bütün girdiler, .vspgeom, .vspaero, .polar, .history, .lod, .adb ve program logları: `{native['run_directory']}`.",'',
           '## Başarısız denemeler ve düzeltilen durumlar','',
           '- İlk çoklu ağ (NRef=1) denemesinde çözücü boş yüzey okuyup başarısız oldu. O çıktı kullanılmadı. Doğrulanan akış tek ağ (NRef=0) üretip geometri ayarlarını ayrı çalıştırmalarda inceltiyor. Görselleştirme dışa aktarımı çözümden sonra yapılıyor.',
           '- Sıfır kaldırmada verim katsayısı native dosyada `-nan(ind)` oldu. Gerekli CL/CDi verileri korunarak yalnız tanımsız yardımcı katsayılar JSON içinde null saklandı.',
           '- Kanat–kuyruk modelinde 20 iterasyonda 8° CDi değişimi seçilen sınırı sağlamadı. İlk çalışma geçerli sonuç diye sunulmadı; 40 iterasyondaki son kuvvet değişimleri kabul ölçütlerini sağladı. Eski loglar saklandı.',
           '- İlk DXF aktarımında boş çizgi çıktısı yakalandı; gerçek projeksiyon kenarlarının düzlem üzerinde aktarılması düzeltildi ve her DXF yeniden açılıp içerdiği elemanlar sayıldı.','',
           '## Sınırlar ve sonraki mühendislik işi','',
           '- XFLR5 birebir eşdeğerliği iddia edilmiyor. 2D viskoz profil, 3D taşıyıcı yüzey, polar, yük dağılımı ve moment eğrisi araç bağlantıları test edildi.',
           '- 2D XFOIL poları otomatik olarak bütün kanadın stall hızını veya 3D ayrılmasını doğrulamaz. Düşük açılı potansiyel akış sonucu da stall doğrulaması değildir.',
           '- Tüm uçak için sürükleme, motor/pervane, sürekli güç, enerji, kütle, trim, dinamik kararlılık ve yapı uygunluğu henüz değerlendirilmedi.',
           '- Ağ yakınsaması referans kanatta sınandı. Kanat-kuyruk modelinin ayrıca tüm geometriyi içeren ağ yakınsama çalışması henüz yapılmadı; onun moment/kaldırma eğrileri entegrasyon sonucudur.',
           '- CAD aktarımı yüzey modelidir; imalata hazır çok parçalı montaj veya iç yapısal tasarım değildir.',
           '- Gerçek tasarıma geçişte güncel görev/gereksinimler ve bileşen kütle bütçesi bu ortama aktarılmalı. Test boyutları gereksinim yerine kullanılmamalı.',
           '- Güncel FreeCAD/CalculiX ve yerel CAD modeli durumu için birleşik engineering_toolchain_report.md raporunu oku. ANSYS sona bırakıldı.','',
           '## Kontrol listesi','', '| Kontrol | Sonuç |', '|---|---|']
    for item in checks:
        lines.append(f"| {item['name']} | {'Geçti' if item['passed'] else 'BAŞARISIZ'} |")
    lines.extend(['','Ayrıntılı ölçümler ve eşikler: [external_test_summary.json](external_test_summary.json).','',
                  '## Resmi kaynaklar','',
                  '- [OpenVSP indirmeleri](https://openvsp.org/download.php)',
                  '- [NASA VSPAERO temelleri](https://www.nasa.gov/reference/openvsp-vspaero-basics/)',
                  '- [XFOIL — yazarın MIT sayfası](https://web.mit.edu/drela/Public/web/xfoil/)',
                  '- [OpenVSP resmi analiz betiği](https://github.com/OpenVSP/OpenVSP/blob/main/examples/scripts/TestAnalysisVSPAERO.vspscript)',''])
    (OUT/'reports/external_tools_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'FINAL EXTERNAL REPORT: {passed}/{len(checks)}',flush=True)
    return 0 if all_ok else 1


if __name__=='__main__':
    sys.exit(main())
