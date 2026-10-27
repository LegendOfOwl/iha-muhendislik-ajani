"""Close this bounded preparation batch, leaving unrun CFD explicitly pending."""
from pathlib import Path
import sys,shutil,html,json,re
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/tmr_m6_20261025'))
from common import read,save,sha,now,memory

def render(text):
    def inline(value):
        value=html.escape(value)
        value=re.sub(r'`([^`]+)`',r'<code>\1</code>',value)
        value=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',value)
        return re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',value)
    out=[];table=False;listing=False
    for line in text.splitlines():
        if table and not line.startswith('|'):out.append('</tbody></table>');table=False
        if listing and not line.startswith('- '):out.append('</ul>');listing=False
        if line.startswith('|'):
            cells=[x.strip() for x in line.strip('|').split('|')]
            if all(re.fullmatch(r'[: -]+',x) for x in cells):continue
            tag='td' if table else 'th'
            if not table:out.append('<table><tbody>');table=True
            out.append('<tr>'+''.join('<'+tag+'>'+inline(x)+'</'+tag+'>' for x in cells)+'</tr>')
        elif line.startswith('# '):out.append('<h1>'+inline(line[2:])+'</h1>')
        elif line.startswith('## '):out.append('<h2>'+inline(line[3:])+'</h2>')
        elif line.startswith('- '):
            if not listing:out.append('<ul>');listing=True
            out.append('<li>'+inline(line[2:])+'</li>')
        elif line.strip():out.append('<p>'+inline(line)+'</p>')
    if table:out.append('</tbody></table>')
    if listing:out.append('</ul>')
    return '\n'.join(out)

def main():
    builds=[]
    for label in ('p32a','p32b','p32c','p256a'):
        folder=ROOT/'tools/su2-build/v8.5.0/controls'/label
        if not folder.exists():continue
        assert (folder/'status.json').exists(),'Do not report while build is running'
        out=BASE/'build_evidence'/label;out.mkdir(parents=True,exist_ok=True)
        for name in ('contract.json','status.json','source.patch','effective_build.json'):
            p=folder/name
            if p.exists():
                target=out/name
                if target.exists():assert sha(target)==sha(p)
                else:shutil.copy2(p,target)
        s=read(folder/'status.json');builds.append(dict(label=label,status=s,records=str(out.relative_to(ROOT))))
    checks=read(ROOT/'outputs/reports/su2_source_software_checks_20261027.json')
    controller=read(ROOT/'outputs/reports/su2_native_controller_checks_20261027.json')
    assert checks['passed'] and controller['passed']
    verified=0;seen={}
    for family in ('flatplate_SAneg_20261025_v1','flatplate_20261027_v1'):
        for seal in (ROOT/'outputs/simulations'/family).rglob('prediction_frozen.json'):
            for p,h in read(seal)['files_sha256'].items():
                path=ROOT/p;assert sha(path)==h,p
                seen[p]=h;verified+=1
    old_integrity={'verified_utc':now(),'old_raw_hash_records_verified':verified,'unique_paths':len(seen),
                   'all_matched':True,'no_old_solution_promoted':True}
    save(BASE/'old_output_integrity.json',old_integrity)
    nativecase=ROOT/'outputs/simulations/linecap_source_20261027_v1'
    native_runs=[str(p.parent.relative_to(ROOT)) for p in nativecase.glob('*/prediction_frozen.json')]
    repro=read(nativecase/'reproduction.json') if (nativecase/'reproduction.json').exists() else None
    effect=read(nativecase/'effect.json') if (nativecase/'effect.json').exists() else None
    assert not native_runs,'This bounded report template is for preparation only; report actual CFD explicitly if run.'
    summary=('Sabit SU2 v8.5.0, Eigen ve MEL kaynakları indirildi; 4357 kaynak dosyası arşivlerle birebir doğrulandı. '
       'C++17/Haswell/OpenMP dört iş parçacığı derleyici denemesi geçti. İlk gerçek SU2 derlemesi 259. hedefte '
       'başlık arama yolu hatasıyla durdu; kaynak baytlarını koruyan ortak arama yolu düzeltmesi kaydedildi. '
       'İkinci deneme kullanılabilir RAM 1 GiB sınırının altındayken native süreci başlatmadan reddedildi. '
       '70 yeni yazılım kontrolü geçti; önceki 14 süreç kontrolünün kanıtı ayrıca denetlendi. '
       'Yeni CFD çalıştırılmadı; pristine32 yeniden üretimi ve cap256 etki/maliyet sınaması bekliyor. '
       'Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.')
    summary_en=('Pinned SU2 8.5.0, Eigen and MEL archives were acquired and all 4,357 source files matched their archives. '
       'A native C++17/Haswell/OpenMP four-thread compiler probe passed. The first actual solver build stopped at '
       'target259 on a missing relative include; a common source-preserving include-search option was registered. '
       'A second attempt was refused before native launch because available RAM was below the1 GiB safety floor. '
       'All70 new software checks passed; evidence from14 earlier process checks was audited separately. '
       'No new CFD run or cap effect has been demonstrated. Pristine reproduction remains mandatory. '
       'Physical/RAE/M6/UAV qualification and LLM improvement remain unestablished.')
    result={'created_utc':now(),'scope':'Bounded source-build and comparison infrastructure batch; dependent CFD pending',
      'summary_tr':summary,'summary_en':summary_en,'sources':read(BASE/'accepted_archives.json'),
      'builds':builds,'compiler_preflight':read(ROOT/'outputs/reports/su2_build_preflight_20261027.json'),
      'software_checks_report':'outputs/reports/su2_source_software_checks_20261027.json',
      'controller_checks_report':'outputs/reports/su2_native_controller_checks_20261027.json',
      'new_distinct_checks':70,'build_recipe_checks_rerun_after_option_change':9,
      'prior_process_checks_audited':14,'old_output_integrity':old_integrity,
      'new_native_CFD_runs':0,'pristine_reproduction':repro,'cap_effect':effect,
      'memory_at_report':memory(),'minimum_advisable_available_GiB_before_next_compile':2.7,
      'next_step':'New pristine32 build with common include option when RAM permits; then fresh release32/build32 CFD, cap256 only after reproduction.',
      'method_design_sha256':sha(BASE/'method_design.json'),'old_fine3999_role_preserved':True,
      'physical_qualification_passed':False,'M6_qualification_passed':False,'LLM_improvement_demonstrated':False}
    report=ROOT/'outputs/reports/su2_kaynak_kontrolu_20261027'
    save(report.with_suffix('.json'),result)
    rows=[]
    for item in builds:
        s=item['status'];last=s['phases'][-1]
        rows.append('| '+item['label']+' | '+str(s['succeeded'])+' | '+str(last['exit_code'])+' | '+
                    format(last['seconds'],'.3f')+' | '+str(last['stop_reason'])+' |')
    md='# SU2 kaynak derlemesi ve güvenilir karşılaştırma hazırlığı\n\n27 Ekim2026 · Yeni CFD koşusu: **0** · Genel fizik kabulü: **false**.\n\n'+summary+'\n\n'
    md+='## Neden bu yöntem?\n\nÖnceki native ölçümde çizgi birliği52689 noktanın7200’ünü ve ayrı doğrulanmış eski aşama RHS yoğunluk kare toplamının%53,8965’ini kapsıyordu. Kaynaktaki32 nokta sınırını256’ya çıkarmak bir mekanizma hipotezidir; isotropi/yön/komşuluk durdurmalarını veya çizgi dışı Jacobi bağlaşımını kaldırmaz. Bu turda sınır henüz değiştirilip çözülmedi.\n\n'
    md+='## Gerçekte kurulan ve çalıştırılanlar\n\nMeson1.8.2, Ninja1.13.0 ve psutil7.1.0 proje Python ortamında;311245 baytlık sabit libgomp paketi taşınabilir GNU araç klasöründe. İlk OpenMP derlemesi eksik `-lgomp` ile başarısızdı; bu kayıt korundu. Ek bileşenden sonra gerçek program dört iş parçacığı,8bayt double ve OpenMP202111 bildirdi. Sistem PATH/DNS/TLS ayarı değişmedi.\n\n'
    md+='SU2 commit `12eb826f049ef7f67df974dfcb44cf36ee07c0f8`, Eigen `d71c30c47858effcbd39967097a2d99ee48db464`, MEL `46205ab019e5224559091375a6d71aabae6bc5b9`. Arşivler sırasıyla18876892/2719400/13894bayt;gzip sonu, güvenli yollar ve tüm dosya baytları denetlendi. İndirilen kaynaklar/derleyici paketleri public dağıtıma eklenmez; URL/SHA256 ve yama/derleme kayıtları korunur.\n\n'
    md+='## İki gerçek derleme girişiminin sonucu\n\n| Kayıt | Başarı | Son native çıkış | Son aşama süresi,s | Durdurma sebebi |\n|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\n'
    md+='`p32a`,259/290 Ninja hedefinde `CFlowTractionInterface.cpp:34` için eksik başlık hatası verdi. Bu satırın göreli yolu, bulunduğu `interfaces/fsi` klasöründen hedefe ulaşmıyor. Ortak `cpp_args=[\'-I../source/SU2_CFD/src/interfaces\']` seçeneği gerçek `Common/include/interface_interpolation/CInterpolator.hpp` dosyasına çözülüyor. Bu geometrinin/denklemin yaması değildir; aynı seçenek pristine32 ve ileride cap256 için kullanılacak. Henüz başarılı tam derleme kanıtı değildir. `p32b` öncesi kullanılabilir RAM0,804GiB olduğundan1GiB alt sınırı native süreci başlatmadı; çıkış kodu **null**, program başarısızlığı/CFD sonucu atanmadı. Başka uygulamalar kapatılmadı.\n\n'
    md+='Derleme: tek iş, toplam1800s, süreç ağacının örneklenen çalışma kümesi≤3GiB, boşRAM≥1GiB. İlk gerçek derleme yaklaşık1,65GiB tepe kullandı; sonraki başlangıç için en az2,7GiB kullanılabilir bellek öneriliyor. WindowsJobObject yalnız kendi derleyici alt süreçlerini sınırlar;0,1s örnekleme geçici tepeyi kesin yakalama garantisi değildir. Yerel GNU16/UCRT, resmî binary’de görülen GNU13/win32 işaretinden farklıdır.\n\n'
    md+='## CFD başlamadan dondurulan kapılar\n\nÜç taze kolun aynı ağ, özgün fine3999 NDseed, fizik, tüm açık sayısal/output ayarları ve dört native iş parçacığıyla200adım çalışması planlandı. Tümünde `LINELET` alanı istenir; eski200adımın eksik alanı başka1adımlık dosyadan doldurulmaz. Her kol240s/2,5GiB üst bütçede ve alan/yüzey/restart/geçmiş199 birlikte mühürlenmek zorunda.\n\n'
    md+='Önce release32–pristine32: beş SI log10RMS eğrisinin bütün200adımında en büyük fark≤0,03; son |ΔCD|≤1e-8; toplam akış+SA Krylov farkı≤%5;52689 noktada koordinat eşleme≤2e-7m ve tam aynı boolean üyelik.0,03 yerel işletim ekranıdır, evrensel kayan nokta/fizik hata bandı değildir. Son100CD aralığı<1e-7, sonlu alanlar ve pozitif yoğunluk/basınç ayrıca gerekir.\n\n'
    md+='Bu kapı geçerse yalnız tek cap32→256 deklarasyonu değişebilir. Aynı derleyici/runtime ve tüm diğer kaynak baytları doğrulanır; yoğunluk kazancı≥0,3log, SA kötüleşmesi≤0,1log, toplam Krylov ve gözlenen süre oranları≤1,5 gerekir. Native üye sayısı ve **aynı eski RHS** kapsama payı artmalıdır. Graph renkleri çizgiID değildir; bu yeni alanın artığı veya ağ hata bandı değildir. Eşikler sonuçlara göre gevşetilmeyecek; tarama/otomatik uzatma yapılmayacak.\n\n'
    md+='## Güvenilirlik kontrolünün sınırı\n\n31 karar +20 veri çıkarma +9 derleme koruması +10 yürütücü karşı örneği geçti. Arama yolu seçeneği değişince ilgili9 derleme testi ayrıca tekrarlandı; bunu9yeni test saymadık. Önceki14 süreç kontrolü yeniden çalıştırılmadan mevcut5 gerçek Windows senaryosunun15 kayıt dosyası denetlendi. Kontrollü sahte dosyalar kullanan testler CFD çalıştırmaz. Gerçek eski200adımlık alanla veri okuyucu sınandı:200SI geçmiş satırı ve199eşzamanlı dosyalar okundu, eksikLinelet nedeniyle kabul reddedildi.\n\n'
    md+=f'Eski CFD mühürlerinin **{verified} hash kaydı** yeniden eşleşti. Gerçek İHA’nın üç girdisi v0.15 kataloğu/depo kopyalarıyla aynı. Bu kaynak benchmarkına ait geliştirmeler keyfiCAD→CFD hizmeti veya LLM uzmanlığı kanıtı değildir; eski fine3999/üç-ağ/RAE/M6/VLM kabulleri kapanmadı.\n\n'
    md+='## Kanıt ve sonraki iş\n\n- [Ham sonuç ve kimlikler](su2_kaynak_kontrolu_20261027.json)\n- [Derleyici gerçek OpenMP denemesi](su2_build_preflight_20261027.json)\n- [60 yazılım kontrolü ve eski süreç kanıtı](su2_source_software_checks_20261027.json)\n- [10 yürütücü karşı örneği](su2_native_controller_checks_20261027.json)\n- [Sabit yöntem sözleşmesi](../../work/su2_build_20261027/method_design.json)\n- [Başlık yolu teşhisi](../../work/su2_build_20261027/include_path_diagnosis.json)\n\n'
    md+='Sonraki iş: yeterli RAM’de yeni pristine32 derlemesi; başarılıysa fresh release32/pristine32 yeniden üretimi. Cap256 ancak bundan sonra. ANSYS kurulmadı; başka büyük geliştirme paketi eklenmedi.\n\n'
    md+='Kaynaklar: [sabit SU2 kaynağı](https://github.com/su2code/SU2/tree/12eb826f049ef7f67df974dfcb44cf36ee07c0f8), [sabit Eigen](https://gitlab.com/libeigen/eigen/-/tree/d71c30c47858effcbd39967097a2d99ee48db464), [sabit MEL](https://github.com/pcarruscag/MEL/tree/46205ab019e5224559091375a6d71aabae6bc5b9). İddialar yerel hash’i doğrulanmış kaynak/arşiv, native kayıt ve testlere dayanır.\n'
    report.with_suffix('.md').write_text(md,encoding='utf-8')
    body=render(md)
    page='<!doctype html><html lang="tr"><meta charset="utf-8"><title>SU2 kaynak kontrolü</title><style>body{font:16px/1.65 system-ui;max-width:1100px;margin:40px auto;padding:0 22px;color:#172733;background:#f5f8fb}h1,h2{line-height:1.25}table{border-collapse:collapse;background:white}td,th{border:1px solid #ccd7df;padding:8px}code{overflow-wrap:anywhere}a{color:#006d91}</style>'+body+'</html>'
    report.with_suffix('.html').write_text(page,encoding='utf-8')
    taskpath=ROOT/read(BASE/'task.json')['path'];t=read(taskpath)
    t.update(status='bekliyor',phase='sınırlı derleme/hazırlık paketi kapandı; RAM ve pristine yeniden üretimi bekliyor',
      blocked_by=['Successful pristine source build and release reproduction not established; last resource gate refused launch.'],
      evidence=t.get('evidence',[])+[str(report.with_suffix('.json').relative_to(ROOT)),str(report.with_suffix('.html').relative_to(ROOT))],
      physical_qualification_passed=False)
    save(taskpath,t)
    state=ROOT/'PROJECT_STATE.md';text=state.read_text(encoding='utf-8')
    marker='## 27 Ekim: sabit kaynak derlemesi ve karşılaştırma korumaları'
    assert marker not in text
    text+='\n\n'+marker+'\n\n- '+summary+'\n- Rapor outputs/reports/su2_kaynak_kontrolu_20261027.html. Kaynak/ağaç kimlikleri, eski başarısız derleme ve RAM reddi korundu. Yöntem limitleri method_design.json içinde native öncesi donduruldu; hiçbir yeni CFD sonucu yok. Sonraki derleme ortak ek include yoluyla ve kaynak baytları korunarak yapılmalı.\n'
    state.write_text(text,encoding='utf-8')
    print({'report':str(report.relative_to(ROOT)),'old_hash_records':verified,'new_CFD_runs':0,'task':'bekliyor'},flush=True)

if __name__=='__main__':main()
