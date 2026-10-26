from incremental_export import ROOT,DEST,RUN,VERSION,PLAN,read,dump,now
import re

def main():
    assert VERSION=='v0.13.0';plan=read(PLAN)
    r=read(ROOT/'outputs/reports/reduced_family_review_20261026.json')
    passed=r['registered_2D_numerical_screens_passed']
    outcome='Kayıtlı2B sayısal şartların tamamı geçti.' if passed else 'Kayıtlı2B sayısal şartların tamamı geçmedi; açık kapılar raporlandı.'
    summary='26 Ekim2026. Aynı seed/ağda iç doğrusal tolerans1e-6→1e-3 testi toplam Krylov iterasyonunu%42,1123 azalttı; SI kalıntı/CD farkları ön kayıtlı sınırlar içinde kaldı. Üç kaynak ağda ayrı ve sonlu bütçeli native devam koşuları yapıldı. '+outcome+' Genel fizik/M6/İHA kabulü false; GCI null.\n\n8 maliyet ve12 aile karar kontrolü geçti. Yeni/önceki mühürler, gerçekİHA girdileri ve ön-native kodlar denetlendi. Son işlem çıktı adı gölgelenmesi düzeltildi; ham alanlar korunur. Bu kontrollü kod kıyası deney veya LLM uzmanlığı doğrulaması değildir.\n'
    p=DEST/'README.md';text=p.read_text(encoding='utf-8')
    text=text.replace('Güncel dağıtım **v0.12.0**','Güncel dağıtım **v0.13.0**').replace('`main` veya `v0.12.0`','`main` veya `v0.13.0`')
    text=text.replace('v0.1.0 → v0.12.0 sürüm ve kanıt notları','v0.1.0 → v0.13.0 sürüm ve kanıt notları')
    section='## Güncel sürüm —26 Ekim2026\n\n[**v0.13.0 sonuçları: GitHub’da okunabilir rapor**](raporlar/v0.13.0/README.md) · [Release dosyaları](https://github.com/LegendOfOwl/iha-muhendislik-ajani/releases/tag/v0.13.0) · [Sürümleme politikası](SURUMLEME.md).\n\n'+summary+'\n'
    text,n=re.subn(r'## Güncel sürüm .*?(?=## Nereden başlanır)',lambda m:section,text,flags=re.S);assert n==1
    old='| [v0.12.0](surumler/v0.12.0/README.md) | 11 yeni CFD kontrolü, Newton–Krylov ve kalıntı birim denetimi |'
    assert old in text;text=text.replace(old,old+'\n| [v0.13.0](surumler/v0.13.0/README.md) | İç çözümde%42 daha az Krylov iterasyonu ve üç kaynak ağda kabul denetimi |')
    text=text.replace('[GitHub’da okunabilir güncel sonuçlar](raporlar/v0.12.0/README.md)','[GitHub’da okunabilir güncel sonuçlar](raporlar/v0.13.0/README.md)')
    eng='## English summary\n\nA Windows CAD/aerodynamic/CFD workflow with frozen outputs and source provenance. Version0.13.0 reduced total flow+SA Krylov iterations by42.1123% in one preregistered same-seed200-step tolerance control, while keeping residual/CD differences within registered limits. A separate bounded three-source-grid flat-plate follow-up is fully reported, including failed or incomplete gates. General physical/M6/UAV qualification remains false; no universal speedup, GCI or LLM expertise is claimed. Earlier tags through0.10.0 are retrospective evidence groups;0.11.0 onward are genuine incremental releases. Code and reports were developed with substantial Codex assistance.\n\n'
    text,n=re.subn(r'## English summary.*?(?=## EXE ve lisans)',lambda m:eng,text,flags=re.S);assert n==1
    p.write_text(text,encoding='utf-8');(DEST/'VERSION').write_text(VERSION+'\n',encoding='ascii')
    p=DEST/'CHANGELOG.md';body=p.read_text(encoding='utf-8');assert '## v0.13.0' not in body
    body=body.replace('## v0.12.0','## v0.13.0 —26 Ekim2026: CFD iç çözüm işi ve üç ağ\n\n'+summary+'\n## v0.12.0',1);p.write_text(body,encoding='utf-8')
    report=DEST/'raporlar'/VERSION;report.mkdir(parents=True)
    md=(ROOT/'outputs/reports/cfd_ic_cozum_ve_uc_ag_20261026.md').read_text(encoding='utf-8')
    md=md.replace('../plots/','../../uygulama/outputs/plots/')
    for name in ['reduced_family_review_20261026.json','flatplate_linear_work_20261026.json','reduced_family_integrity_20261026.json']:
        md=md.replace(']('+name+')','](../../uygulama/outputs/reports/'+name+')')
    md+='\n\n[Önceki kontrollü deneyler](../v0.12.0/README.md) · [Önceki kaynak M6 ve düz plaka](../v0.11.0/README.md)\n'
    (report/'README.md').write_text(md,encoding='utf-8')
    folder=DEST/'surumler'/VERSION;folder.mkdir(parents=True,exist_ok=True)
    notes='# '+VERSION+' — CFD iç çözüm maliyeti ve üç kaynak ağ\n\n'+summary+'\n[Okunabilir ayrıntılı rapor](../../raporlar/v0.13.0/README.md). Önceki tag/Release varlıkları korunur. Sürüm numarası fiziksel yeterlilik puanı değildir.\n'
    (folder/'README.md').write_text(notes,encoding='utf-8')
    (RUN/'release-notes.md').write_text(notes.replace('../../raporlar/v0.13.0/README.md','https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/v0.13.0/raporlar/v0.13.0/README.md'),encoding='utf-8')
    for category in ['raporlar','cizimler','testler']:
        p=DEST/category/'README.md';p.write_text(p.read_text(encoding='utf-8')+'\n- ['+VERSION+']('+VERSION+'/README.md)\n',encoding='utf-8')
        if category=='raporlar':continue
        d=DEST/category/VERSION;d.mkdir(parents=True,exist_ok=True)
        content='Bu sürümde CAD geometrisi değiştirilmedi; CFD maliyet ve kabul denetimi yapıldı.\n' if category=='cizimler' else '\n'.join('- ['+x['source_path']+'](../../'+x['repository_path']+')' for x in plan['changed'] if x['storage']=='git' and any(s in x['source_path'] for s in ['test_family_decision','test_linear_work_control','guards_20261026','reduced_family_review']))+'\n'
        (d/'README.md').write_text('# '+VERSION+'\n\n'+content,encoding='utf-8')
    print('v0.13.0 release documents prepared')

if __name__=='__main__':main()
