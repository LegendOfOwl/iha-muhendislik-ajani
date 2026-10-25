from incremental_export import ROOT,DEST,RUN,VERSION,PLAN,read,dump,digest,now
from pathlib import Path

def main():
    assert VERSION=='v0.12.0'
    plan=read(PLAN)
    summary='''25 Ekim2026. 11yeni native SU2 koşusu; beş tamamlanmış eşli kıyasta ön kayıtlı ortak etki geçmedi, MG2 süre sınırında eksik kaldı. Fiziksel kabul false.

- SabitCFL, otomatikCFL, yerel çok seviyeli ağ, sonlu fark Newton–Krylov ve değişken ölçekleme araştırıldı; onaylanmayan hipotezler korunur.
- Newton iki farklı on/off çiftinde gerçekten çalıştı. Ortalama akış içindir; SA ayrı çözülür, adjoint veya arXiv artık yumuşatması değildir.
- Karışık boyutlu/boyutsuz kalıntı kıyası yanlış2,719195log kazanç gösterebilirdi. Aynı SI tanımında0,0550435log kaldı; yeni denetçi bu hatayı reddeder.
- 13eşli kıyas karşı örneği,4analitik/bozuk dönüşüm kontrolü ve26temel regresyon geçti. Native tam kalıntı özdeşliği taslağı başarısız olarak korundu.
- 187yeni dosya mühürü,40ön-native kod hash'i ve230eski CFD hash'i yeniden doğrulandı. Gerçek İHA girdileri değişmedi.
- Sonraki kayıtlı maliyet deneyi henüz çalıştırılmadı. Üç yakınsamış ağ, M6/RAE ve genel CAD→CFD yeterliliği açık; LLM davranış iyileşmesi ölçülmedi.
'''
    p=DEST/'README.md';text=p.read_text(encoding='utf-8')
    text=text.replace('Güncel dağıtım **v0.11.0**','Güncel dağıtım **v0.12.0**').replace('`main` veya `v0.11.0`','`main` veya `v0.12.0`')
    text=text.replace('v0.1.0 → v0.11.0 sürüm ve kanıt notları','v0.1.0 → v0.12.0 sürüm ve kanıt notları')
    text=text.replace('[GitHub’da okunabilir güncel sonuçlar](raporlar/v0.11.0/README.md)','[GitHub’da okunabilir güncel sonuçlar](raporlar/v0.12.0/README.md)')
    text=text.replace('| [v0.11.0](surumler/v0.11.0/README.md) | Kaynak TMR M6, düz plaka, güvenilirlik politikası; gerçek artımlı sürüm |',
        '| [v0.11.0](surumler/v0.11.0/README.md) | Kaynak TMR M6, düz plaka, güvenilirlik politikası; gerçek artımlı sürüm |\n| [v0.12.0](surumler/v0.12.0/README.md) | 11 yeni CFD kontrolü, Newton–Krylov ve kalıntı birim denetimi |')
    text=text.replace('Version0.11.0 adds','Version0.12.0 adds11controlled native solver runs, finite-difference Newton–Krylov tests and residual-normalization guards. No tested method met the registered joint improvement criterion; physical qualification remains open. Version0.11.0 added')
    p.write_text(text,encoding='utf-8')
    (DEST/'VERSION').write_text(VERSION+'\n',encoding='ascii')
    changelog=DEST/'CHANGELOG.md';body=changelog.read_text(encoding='utf-8')
    body=body.replace('## v0.11.0', '## v0.12.0 —25 Ekim2026: CFD kontrol deneyleri ve birim denetimi\n\n'+summary+'\n## v0.11.0',1)
    changelog.write_text(body,encoding='utf-8')
    report=DEST/'raporlar'/VERSION;report.mkdir(parents=True)
    original=(ROOT/'outputs/reports/cfd_yakinsama_arastirmasi_20261025.md').read_text(encoding='utf-8')
    # Same report, with valid repository-relative plot links for GitHub viewing.
    original=original.replace('../plots/','../../uygulama/outputs/plots/')
    original+='\n\n[Ham kıyas JSON](../../uygulama/outputs/reports/flatplate_scaling_control_20261025.json) · [Koşu/mühür denetimi](../../uygulama/outputs/reports/flatplate_controls_integrity_20261025.json) · [Önceki M6 ve düz plaka sonuçları](../v0.11.0/README.md)\n'
    (report/'README.md').write_text(original,encoding='utf-8')
    notes='# '+VERSION+' — CFD yakınsama kontrolleri ve birim denetimi\n\n'+summary
    notes+='\n[Okunabilir sonuç raporu](../../raporlar/v0.12.0/README.md). Önceki tag ve Release varlıkları korunur. Bu sürüm artımlı yöntem/değerlendirme paketidir; sürüm sayısı uzmanlık veya fiziksel yeterlilik seviyesi değildir.\n'
    folder=DEST/'surumler'/VERSION;folder.mkdir(exist_ok=True,parents=True);(folder/'README.md').write_text(notes,encoding='utf-8')
    (RUN/'release-notes.md').write_text(notes.replace('../../raporlar/v0.12.0/README.md','https://github.com/LegendOfOwl/iha-muhendislik-ajani/blob/'+VERSION+'/raporlar/'+VERSION+'/README.md'),encoding='utf-8')
    for category in ['raporlar','cizimler','testler']:
        p=DEST/category/'README.md';text=p.read_text(encoding='utf-8');text+='\n- ['+VERSION+']('+VERSION+'/README.md)\n';p.write_text(text,encoding='utf-8')
        if category=='raporlar':continue
        child=DEST/category/VERSION;child.mkdir(exist_ok=True,parents=True)
        selected=[r for r in plan['changed'] if r['storage']=='git' and category=='testler' and any(x in r['source_path'] for x in ['control','scaling','guard'])]
        content='# '+VERSION+'\n\n'+('Bu turda CAD geometrisi değiştirilmedi. Araştırma CFD yakınsaması ve sonuç denetimi kapsamındadır.\n' if category=='cizimler' else '\n'.join('- ['+r['source_path']+'](../../'+r['repository_path']+')' for r in selected)+'\n')
        (child/'README.md').write_text(content,encoding='utf-8')
    print('v0.12.0 release documents prepared')

if __name__=='__main__':main()
