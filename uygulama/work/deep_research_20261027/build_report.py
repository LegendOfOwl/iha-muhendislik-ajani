"""Build a traceable, filterable research report; no engineering solver runs."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import html
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
STEM = 'acik_sorunlar_ve_derin_arastirma_20261028'
OUT = ROOT / 'outputs/reports'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def link_from_report(path):
    import os
    path=Path(path).as_posix()
    if path=='PROJECT_STATE.md':path='work/deep_research_20261027/baseline_PROJECT_STATE.md'
    if path=='.agents/skills/iha-muhendislik/references/learning_loop.md':path='work/deep_research_20261027/baseline_learning_loop.md'
    return Path(os.path.relpath(ROOT/path, OUT)).as_posix()


def render(markdown):
    def inline(text):
        text = html.escape(text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        return re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    rows, table, listing = [], False, False
    for line in markdown.splitlines():
        if table and not line.startswith('|'): rows.append('</tbody></table>'); table=False
        if listing and not re.match(r'^[-\d]', line): rows.append('</ul>'); listing=False
        if line.startswith('|'):
            cells=[x.strip() for x in line.strip('|').split('|')]
            if all(re.fullmatch(r'[-: ]+', x) for x in cells): continue
            tag='td' if table else 'th'
            if not table: rows.append('<table><tbody>'); table=True
            rows.append('<tr>'+''.join('<'+tag+'>'+inline(x)+'</'+tag+'>' for x in cells)+'</tr>')
        elif line.startswith('### '): rows.append('<h3>'+inline(line[4:])+'</h3>')
        elif line.startswith('## '): rows.append('<h2>'+inline(line[3:])+'</h2>')
        elif line.startswith('# '): rows.append('<h1>'+inline(line[2:])+'</h1>')
        elif line.startswith('- '):
            if not listing: rows.append('<ul>'); listing=True
            rows.append('<li>'+inline(line[2:])+'</li>')
        elif line.strip(): rows.append('<p>'+inline(line)+'</p>')
    if table: rows.append('</tbody></table>')
    if listing: rows.append('</ul>')
    return '\n'.join(rows)


def main():
    n,c,v=[read(BASE/(name+'.json')) for name in ('numerics','cad_agent','validation_mesh')]
    issues=read(BASE/'issue_register.json')['issues']
    initial=read(BASE/'initial_evidence.json')
    sources, source_map, by_url = [], {}, {}
    def source(sid, title, url, raw, module):
        assert url.startswith('https://')
        if url not in by_url:
            row={'id':sid,'aliases':[],'title':title,'url':url,'consulted_date':'2026-10-28',
                 'records':[], 'not_reproduced_locally':True}
            by_url[url]=row; sources.append(row)
        row=by_url[url]; row['aliases'].append(sid)
        row['records'].append({'module':module,'original_record':raw}); source_map[sid]=row
    parents=[
        ('PS01','NASA NPARC CFD verification/validation overview','https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html','HTML opened; verification, validation and intended-use distinction'),
        ('PS02','NASA-STD-7009B, 2024','https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf','Full PDF opened; consulted acceptance/credibility/problem-tracking sections, not claimed fully reproduced'),
        ('PS03','CFD Vision2030 Study, NASA/CR-2014-218178','https://ntrs.nasa.gov/api/citations/20140003093/downloads/20140003093.pdf','Full PDF opened; sections on workflow automation, geometry/grid and uncertainty; historical2014 diagnosis'),
        ('PS04','OpenFOAM Foundation Windows documentation','https://openfoam.org/download/windows/','Official current page opened; WSL2 route, no installation attempted')]
    for sid,title,url,depth in parents: source(sid,title,url,{'reading_depth':depth},'parent')
    for item in n['core_sources']: source('N'+item['id'],item['title'],item['url'],item,'numerics')
    for item in c['sources']: source('C'+item['id'],item['title'],item['url'],item,'cad_agent')
    for item in v['sources']: source('VS'+item['id'][1:],item['title'],item['url'],item,'validation_mesh')
    for row in issues:
        assert all(s in source_map for s in row['source_ids']), row['id']
        row['source_links']=[{'id':sid,'title':source_map[sid]['title'],'url':source_map[sid]['url']} for sid in row['source_ids']]
        paths=set()
        for issue in c['issues']:
            if issue['id'] in row['specialist_issue_ids']:
                paths.update(item['path'] for item in c['evidence'] if item['id'] in issue['local_evidence'])
        if any(s.startswith('N') for s in row['specialist_issue_ids']): paths.update(item['path'] for item in n['local_evidence'])
        if any(s.startswith('VM') for s in row['specialist_issue_ids']): paths.update(v['local_evidence_sha256'])
        if row['id']=='U12': paths.update(['outputs/reports/candidate_comparison.json','work/workflow/rank_candidates.py'])
        row['local_evidence_links']=[{'path':name,'sha256':sha(ROOT/name)} for name in sorted(paths)]
    expected=dict(initial['files_sha256'])
    records=[{'path':k,'sha256':val} for k,val in expected.items()]
    records += n['local_evidence'] + n['verified_native_source_files'] + c['evidence']
    records += [{'path':k,'sha256':val} for k,val in v['local_evidence_sha256'].items()]
    known={item['path'] for item in records}
    records += [item for row in issues for item in row['local_evidence_links'] if item['path'] not in known and not known.add(item['path'])]
    baseline=BASE/'baseline_PROJECT_STATE.md'
    if not baseline.exists():shutil.copyfile(ROOT/'PROJECT_STATE.md',baseline)
    for item in records:
        checked=baseline if item['path']=='PROJECT_STATE.md' else ROOT/item['path']
        assert sha(checked)==item['sha256'],item['path']
        expected.setdefault(item['path'],item['sha256'])
        assert expected[item['path']]==item['sha256']
    assert sha(baseline)==expected['PROJECT_STATE.md']
    lesson='.agents/skills/iha-muhendislik/references/learning_loop.md'
    lesson_copy=BASE/'baseline_learning_loop.md'
    if not lesson_copy.exists():shutil.copyfile(ROOT/lesson,lesson_copy)
    assert sha(lesson_copy)==expected[lesson]
    modules={name:{'sha256':sha(BASE/name),'bytes':(BASE/name).stat().st_size}
             for name in ('numerics.md','numerics.json','validation_mesh.md','validation_mesh.json','cad_agent.md','cad_agent.json','issue_register.json')}
    counts=dict(Counter(row['priority'] for row in issues))
    assert counts=={'P0':7,'P1':12,'P2':6,'P3':1}
    summary=(f'28 Ekim2026:29 uzmanlık-alt başlığı, yinelenmeler birleştirilerek26 açık başlıkta önceliklendirildi '
        f'(P0=7,P1=12,P2=6,P3=1). {len(sources)} farklı birincil kaynak adresi; {len(expected)} benzersiz yerel kanıt dosyasının SHA256 değeri yeniden kontrol edildi. '
        'En kritik sıra gerçek iç artık/dış yakınsama, bölgesel ağ, geometri eşdeğerliği, sistematik ağ/uzak alan ve deney kabulüdür. '
        'Gerçek İHA girdileri eksik; genel uçtan uca ajan ve görülmemiş görevlerde iyileşme kanıtı yok. '
        'Araştırmadan pasif b−Aδ ölçümü ve bağımsız wall-distance denetimi somut adaylar olarak çıktı; bunlar henüz uygulanmadı. '
        'Yeni CFD, kaynak derlemesi veya kurulum yapılmadı; mevcut fizik/RAE/M6/İHA/LLM kabulü değişmedi.')
    summary_en=(f'On28 October2026,29 specialist gaps were consolidated into26 prioritized open items '
        f'(7P0,12P1,6P2,1P3), supported by{len(sources)} distinct primary-source addresses and{len(expected)} rehashed unique local evidence files. '
        'True inner residual/outer convergence, regional meshing, geometry equivalence, systematic-grid/farfield and experimental gates remain critical. '
        'Real UAV inputs, generic end-to-end autonomy and unseen-task improvement remain unestablished. '
        'Passive true-linear-residual instrumentation and independent wall-distance auditing are proposed, not executed. '
        'No new CFD, source build or installation was run; physical/M6/UAV qualification and LLM-improvement status did not change.')
    findings=[
        ('İç artık: ölçülecek nicelik eksik',
         'Jadoui vd. M6 adjoint örneklerinde gerçek ve least-squares artıklarını ayrı izliyor. Bizim primal, ayrık flow/SA sistemimiz aynı sistem değil. Yerel veri, raporlanan iç akış oranının yaklaşık45kat iyileşmesini dış yoğunluk ilerlemesine bağlayamıyor; ilk öneri yeni çözücü değil bağımsız b−Aδ ölçümü.', ['NS06','NS01']),
        ('Duvar mesafesi: ucuz ve ayrı bir kontrol adayı',
         'Park vd.2018, anizotropik M6 ağında yanlış mesafe varsayımının akışı etkileyebildiğini gösteriyor. Bu, SU2’mizde kanıtlanmış neden değil. Önce akış çalıştırmadan geometriye bağlı bağımsız mesafe karşılaştırması yapmak anlamlı.', ['VS03']),
        ('Önceden var olan düzeltmeyi tekrar eklememek',
         'Derlenen v8.5.0 kaynağı zaten iki geçişli Classical Gram–Schmidt kullanıyor. Fonksiyon adından eski Modified Gram–Schmidt uygulaması varsaymak yanlış öneri üretebilirdi. Önbellekli web raw görünümü yerine hashli yerel kaynak ve pinned GitHub API teyidi kullanıldı.', ['NS01','NS06']),
        ('CAD ve ajan: görünüş başarısı ile görev kabulü ayrı',
         'Text2CAD-Bench daha karmaşık işlem/topoloji değerlendirmesini; AstaBench araç ve bütçe denetimli ajan değerlendirmesini ele alıyor. Bizim için çıkarım, daha uzun talimattan önce görev bazlı ölçü/topoloji hakemi, ayrı yeni görevler ve aynı koşullu önce/sonra deneyidir.', ['CS06','CS10','CS11']),
        ('Uyarlama ve yeni modeller: daha sonra, kanıtlı ihtiyaçla',
         'Hessian prototipi tam solve–remesh döngüsü değildir. Yeni immersed-boundary veya surrogate–Newton çalışmaları farklı altyapı gerektiriyor. Yakınsamaya yakın mevcut seed için yeni bir sinir ağı başlangıcı, terminal yakınsama sorununu kendiliğinden çözmez; bu yerel kapsam çıkarımıdır.', ['VS09','VS10','NS07']),
        ('Kurulum sayısı başarı ölçütü değil',
         'NASA’nın tarihsel Vision2030 çalışması geometri/ağ ve belirsizlik yönetimini darboğaz olarak ele alıyor. Bizde öncelik aynı adayın kaynak–geometri–mesh–çözüm–kabul zincirini bağlamak. OpenFOAM farklı yöntem kıyası sunabilir; resmî Windows yolu WSL2 ve ayrıca kaynak bütçesi ister.', ['PS03','PS04'])]
    steps=[
        ('A','Ölçümü önce doğrula','U01', 'Küçük bilinen lineer sistemler, sıfır RHS ve zaten çözülmüş başlangıç; sonra pasif ölçüm patch’inin kaynak32 yeniden üretimi. Matris, b, δ ve fizik durumunun değişmediği kanıtlanmalı.'),
        ('B','Geometriyi paralel denetle','U03,U19','Gerçek wall marker ve kaynak yolu üzerinden nokta–segment/üçgen/sınır mesafesi. Yanlışlık yoksa hipotez kapanır; sonuç kötü diye mesafe değiştirilmez.'),
        ('C','Tek gerçek iç sistemde tanı','U01,U17,U18','Aynı ilk durum ve A,b kimlikleriyle32/256; gerçek artık, kestirim, δ ve uygulanan ΔU, yerel relaxation/CFL, operatör maliyetleri. Farklı A,b sabit-sistem kıyası sayılmaz.'),
        ('D','Sonuca göre tek mekanizma seç','U01','Gerçek iç artık yeterliyse dış güncelleme/bağlaşım araştırılır; yetersizse önkoşullandırıcı/operatör tutarlılığı incelenir. Gerçek/kestirim farkı yokken ortogonalleştirme eklenmez. Her kol önceden bütçelenir; otomatik tarama yok.'),
        ('E','Önce kaynak düz plaka ailesi','U02,U04,U05','Korunan fine rolüyle bütün sayısal kapılar; model/BC/viskozite eşleşmesi; bütün kaynak noktaları ve GCI uygunluğu. Bir tanı kolu eski üç-ağ ailesine sessizce eklenmez.'),
        ('F','RAE, ardından M6','U06','RAE’de aynı C1 temsil, normal/TE/iz ve ayrı uzak alan; M6’da TMRsharp sayısal aile ile eski blunt/deney geometrisi ayrımı. Her kapsam kendi koşul ve deney sözleşmesiyle kapanır.'),
        ('G','Görülmemiş yeni proje','U08,U10,U11','Aynı izlenebilir adayda yeni CAD/mesh/çözüm/karar zinciri; ayrı görevlerde sabit araç/model/bütçeyle davranış ölçümü. Geliştirmede görülen vaka yeni kör test sayılmaz.'),
        ('H','Gerçek İHA kararı','U07,U09,U12,U16','Kullanıcının güncel gereksinim/kütle girdileriyle güç, enerji, CG, trim, yapı ve görev uygunluğu. Kritik kabul açıkken nihai kazanan veya uygun uçak sonucu yok.')]
    resolved=[
        'SU2 kaynak derlemesi ve bu200-adımlık vakada resmî/kaynak32 yeniden üretimi geçti; bunu bekleyen kurulum diye tekrar listelemedim.',
        'Native OpenVSP/VSPAERO/XFOIL, tanımlı CAD/FEM ve Elmer laminer kanal çalışmaları kendi dar kapsamlarında mevcut; yeni araç gerekliliğiyle karıştırılmadı.',
        'Proje merkezli GUI/EXE başlatıcı, girdi/birim ve yanlış-CFD-aktarımı/sıralama korumaları çalışıyor; genel uçtan uca başarı ayrıca açık.',
        'Geçersiz prob maskesi, alan/geçmiş eşlemesi ve katı-içi mesafeyi yüzey mesafesi sanma gibi bilinen olaylarda düzeltme/kanıt var. Bunlar çözümsüz aynı hata olarak yeniden sayılmadı.',
        'cap32→256 denemesinin kayıtlı dış yoğunluk etki kabulü başarısız kaldı. Sonuç bütün LINELET ailesinin işe yaramadığı veya bütün model hatasının bulunduğu anlamına gelmez.' ]
    result={'schema':'open_issue_deep_research_v1','created_utc':datetime.now(timezone.utc).isoformat(),
        'research_date_local':'2026-10-28','timezone':'Europe/Istanbul','evidence_cutoff':'v0.17.0 / 27 October2026; literature consulted28 October2026',
        'summary_tr':summary,'summary_en':summary_en,'issue_count':len(issues),'specialist_issue_count':29,
        'priority_counts':counts,'distinct_primary_source_addresses':len(sources),'issues':issues,'sources':sources,
        'findings':[dict(title=t,text=body,source_ids=ids) for t,body,ids in findings],
        'execution_sequence':[dict(step=a,title=b,issue_ids=c,method=d) for a,b,c,d in steps],
        'priority_is_expert_judgment_not_measured_risk_score':True,
        'priority_vs_dependency':'Importance and execution order differ; missing real UAV data blocks that design, not independent benchmark research.',
        'already_resolved_or_scope_qualified':resolved,
        'deliberate_deferral':{'ANSYS':'User deferred heavy installation/license stage; not the first solution to current accuracy gaps'},
        'evidence_integrity':{'hash_records_rechecked':len(records),'unique_files_rechecked':len(expected),'all_matched':True,
                              'files_sha256':expected,'snapshot_before_research_state_update':True,
                              'mutable_baseline_snapshots':{'PROJECT_STATE.md':{'path':str(baseline.relative_to(ROOT)), 'sha256':sha(baseline)}}},
        'specialist_modules':modules,'new_native_CFD_runs':0,'new_builds':0,'new_installations':0,
        'supporting_source_copies':{lesson:{'path':lesson_copy.relative_to(ROOT).as_posix(),'sha256':sha(lesson_copy)}},
        'physical_qualification_passed':False,'M6_qualification_passed':False,'LLM_improvement_demonstrated':False,
        'thresholds_changed':False,'research_not_a_blind_prediction':True,
        'limitations':['This is an evidence inventory of the recorded project, not proof of finding every possible future failure.',
            'Source reading depths and restricted abstracts are retained per source; no claim that every full text or reported experiment was reproduced.',
            'Proposed test methods require a separate native preregistration; literature thresholds are not copied into the old acceptance contract.']}
    text='# Açık sorunlar, önem sırası ve derin araştırma\n\n28 Ekim2026 · Son deney kanıtı:v0.17.0 · Yeni CFD/derleme/kurulum:0.\n\n'+summary+'\n\n'
    text+='## Önceliklerin anlamı\n\nP0, ilgili kapsamda mühendislik kabulünü veya gerçek tasarımın başlamasını engeller. P1, güvenilir genel iş akışını tamamlamak için gereklidir. P2, kapsam/entegrasyon ve yöntem geliştirmesidir. P3, ikincil kurulum seçeneğidir. Sıra bir risk olasılığı hesabı değildir; karar etkisi, bağımlılık ve bilgi kazanımı/maliyet değerlendirmesidir. U07’nin verileri gerçek İHA’yı bekletir; diğer bağımsız araştırmaları durdurmaz. Hipotez ve eksik yetenek, kanıtlanmış yazılım hatası diye etiketlenmedi.\n\n'
    text+='## Kayıtlardaki bütün açık başlıklar\n\n| Sıra | Öncelik | Başlık | Tür |\n|---|---|---|---|\n'
    kinds={'acceptance_failed':'Kabul açık','resolution_unverified':'Çözünürlük açık','equivalence_unverified':'Eşdeğerlik açık',
        'sensitivity_missing':'Duyarlılık eksik','input_missing':'Girdi eksik','capability_unproven':'Yetenek sınanmadı',
        'behaviour_unvalidated':'Davranış ölçülmedi','uncertainty_missing':'Belirsizlik eksik','measurement_missing':'Ölçüm eksik',
        'measurement_limit':'Ölçüt sınırlı','untested_hypothesis':'Sınanmamış hipotez','prototype_only':'Prototip',
        'engine_untested':'Motor sınanmadı','bridge_missing':'Köprü eksik','topology_failures':'Geometri redleri',
        'reference_runtime_unreproduced':'Referans yol sınanmadı','portability_unproven':'Taşınabilirlik sınanmadı','optional_deferred':'İkincil seçenek'}
    for row in issues: text+=f'| {row["rank"]} / {row["id"]} | {row["priority"]} | {row["title"]} | {kinds[row["kind"]]} |\n'
    text+='\n## Araştırmanın somut katkıları\n\n'
    for title,body,ids in findings:
        text+='### '+title+'\n\n'+body+' '+', '.join('['+source_map[sid]['title']+']('+source_map[sid]['url']+')' for sid in ids)+'.\n\n'
    text+='## Hangi sonucu hangi vaka için kullanıyoruz?\n\nDüz plakada26Ekim kaynak ailesi ve korunmuş fine3999 rolü esastır; v17 kaynak-sabiti kolları ayrı tanıdır. RAE’de en yeni v3 kapanışı genel kabulü geçmedi; v2’nin dar başarılı ekranları geçmiş kanıttır. M6’da25Ekim TMRsharp üç-ağ ailesi zaten üretildi, üçü de gerekli iteratif kapıyı geçmedi. Eski blunt M6’nın y+ ve Cp iyileşmesi bu yeni aileye taşınmadı. Kaynak CFD kıyası deneysel doğrulama sayılmadı. Ayrıntılar ve dosya mühürleri alt raporlardadır.\n\n'
    text+='## Sorunları kapatmak için yürütme sırası\n\n'
    for a,b,cids,d in steps: text+=f'- **{a} — {b} ({cids}):** {d}\n'
    text+='\nBu sıra yeni koşu yetkilendirmesinin veya native sözleşmenin yerine geçmez. Önerilen sayısal tolerans/bütçe, yöntem seçildiğinde çalışmadan önce kaydedilir; mevcut başarısız eşikler korunur.\n\n'
    text+='## Her başlık için kanıt, test ve kapanış\n\n'
    for row in issues:
        text+=f'### {row["id"]} · {row["priority"]} · {row["title"]}\n\n'
        for label,key in [('Gözlem','observed'),('Etkisi','impact'),('Bir sonraki test','next_test'),('Kapanış','closure')]: text+=f'**{label}:** {row[key]}\n\n'
        text+='**Bağımlı olduğu işler:** '+(', '.join(row['depends_on']) or 'Bağımsız hazırlanabilir')+'. '
        text+='**Ayrıntılı yerel kayıt:** '+(', '.join(row['specialist_issue_ids']) or 'Ana karar/iş akışı kayıtları')+'.\n\n'
        text+='**Kaynak:** '+', '.join('['+s['title']+']('+s['url']+')' for s in row['source_links'])+'.\n\n'
        text+='**Yerel kanıt:** '+', '.join('['+Path(e['path']).name+']('+link_from_report(e['path'])+')' for e in row['local_evidence_links'])+'.\n\n'
    text+='## Çözülmüş veya dar kapsamında geçen işler\n\n'+'\n'.join('- '+x for x in resolved)+'\n\n'
    text+='ANSYS kullanıcı isteğiyle ağır/lisans aşamasına ertelendi; mevcut yakınsama sorunlarının ilk çözümü sayılmadı. OpenFOAM ise U26’da doğrulanmamış ikinci yerel çözücü seçeneği olarak ayrı kaydedildi.\n\n'
    text+='## Araştırma dosyaları ve kaynak kaydı\n\n'
    for name,label in [('numerics.md','Sayısal yöntemler ve ölçüm tasarımı'),('validation_mesh.md','Ağ, geometri, RAE ve M6 doğrulaması'),('cad_agent.md','CAD, modeller, gerçek proje ve ajan iş akışı')]:
        text+='- ['+label+']('+link_from_report('work/deep_research_20261027/'+name)+')\n'
    text+=f'- [Bütün26 başlık, kaynak ve SHA256 kaydı]({STEM}.json)\n- [Son gerçek CFD karşılaştırması](su2_kaynak_karsilastirma_20261027.html)\n\n'
    text+='Açılan kaynakların yayın tarihi, okuma derinliği, erişim kısıtı ve uygulanabilirliği alt JSON kayıtlarında korunur. Abstract/publisher özeti ile tam metin ayrıldı; kapalı/başarısız erişim tam okunmuş sayılmadı. Kaynakların tam metni yeniden yayımlanmadı.\n\n'
    for row in sources: text+='- **'+('/'.join(row['aliases']))+'** ['+row['title']+']('+row['url']+')\n'
    text+=f'\nYerel kanıt kontrolü:{len(records)} hash kaydı/{len(expected)} benzersiz dosya eşleşti. Bu araştırma hata envanteridir; yeni doğruluk, kör LLM değerlendirmesi, CFD yeterliliği veya uçuşa uygunluk kabulü üretmedi.\n'
    paths=[OUT/(STEM+suffix) for suffix in ('.json','.md','.html')]
    assert not any(p.exists() for p in paths),'Preserve the previous research report; create a revision'
    OUT.mkdir(parents=True,exist_ok=True)
    paths[0].write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    paths[1].write_text(text,encoding='utf-8')
    options=''.join('<option>'+html.escape(x)+'</option>' for x in sorted({r['domain'] for r in issues}))
    cards=[]
    for row in issues:
        content=''.join('<p><strong>'+label+':</strong> '+html.escape(row[key])+'</p>' for label,key in [('Gözlem','observed'),('Etkisi','impact'),('Sonraki test','next_test'),('Kapanış','closure')])
        content+='<p>Bağımlılık: '+html.escape(', '.join(row['depends_on']) or 'Bağımsız hazırlanabilir')+'</p>'
        content+='<p>'+', '.join('<a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['title'])+'</a>' for s in row['source_links'])+'</p>'
        content+='<p>Yerel kanıt: '+', '.join('<a href="'+html.escape(link_from_report(e['path']),quote=True)+'">'+html.escape(Path(e['path']).name)+'</a>' for e in row['local_evidence_links'])+'</p>'
        cards.append('<details class="issue" data-priority="'+row['priority']+'" data-domain="'+html.escape(row['domain'],quote=True)+'"><summary><span class="pill '+row['priority']+'">'+row['priority']+'</span> '+str(row['rank'])+'. '+html.escape(row['title'])+'</summary>'+content+'</details>')
    page='''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Açık sorunlar ve derin araştırma</title>
<style>body{font:16px/1.65 system-ui;color:#182d3c;background:#f4f7fb;max-width:1200px;margin:28px auto;padding:0 22px}h1,h2,h3{line-height:1.3}a{color:#006f94;overflow-wrap:anywhere}table{border-collapse:collapse;display:block;overflow-x:auto;background:white}th,td{padding:8px;border:1px solid #ccd7e0}code{overflow-wrap:anywhere}section{margin:22px 0}.issue{background:white;border:1px solid #cdd8e2;border-radius:10px;padding:12px 16px;margin:10px 0}.issue summary{cursor:pointer;font-weight:650}.pill{border-radius:5px;padding:3px 8px;color:white;font-size:13px}.P0{background:#a52b3a}.P1{background:#a96512}.P2{background:#26758a}.P3{background:#627486}input,select,button{font:inherit;padding:9px;max-width:100%}.controls{display:flex;gap:10px;flex-wrap:wrap;background:#e6eef5;padding:14px;border-radius:10px}.note{background:#e2edf3;border-left:5px solid #26758a;padding:14px}.issue[hidden]{display:none}button{cursor:pointer}</style>
<h1>Açık sorunlar ve derin araştırma</h1><p>28 Ekim2026 · v0.17.0 kanıt tabanı · Yeni CFD/derleme/kurulum:0</p>'''
    page+='<p class="note">'+html.escape(summary)+'</p><h2>Öncelik listesi</h2><p>Başlıkları açarak kanıtı, önerilen testi ve kapanış ölçütünü görebilirsin. Filtre yalnız görünümü değiştirir; kayıtlar JSON’da korunur.</p>'
    page+='<div class="controls"><input id="q" placeholder="Sorun veya yöntem ara" aria-label="Ara"><select id="priority" aria-label="Öncelik"><option value="">Bütün öncelikler</option><option>P0</option><option>P1</option><option>P2</option><option>P3</option></select><select id="domain" aria-label="Alan"><option value="">Bütün alanlar</option>'+options+'</select><button id="expand">Görünenleri aç/kapat</button><span id="count"></span></div><section>'+''.join(cards)+'</section>'
    # The complete linear report remains available even with JavaScript disabled.
    page+='<details><summary>Doğrusal rapor, yöntem bulguları ve bütün kaynaklar</summary>'+render(text)+'</details>'
    page+='''<script>const cards=[...document.querySelectorAll('.issue')],q=document.querySelector('#q'),p=document.querySelector('#priority'),d=document.querySelector('#domain');function filter(){const term=q.value.toLocaleLowerCase('tr');let n=0;for(const c of cards){c.hidden=!!((p.value&&c.dataset.priority!==p.value)||(d.value&&c.dataset.domain!==d.value)||!c.textContent.toLocaleLowerCase('tr').includes(term));if(!c.hidden)n++;}document.querySelector('#count').textContent=n+' / '+cards.length+' başlık';}for(const e of [q,p,d])e.addEventListener('input',filter);document.querySelector('#expand').addEventListener('click',()=>{const visible=cards.filter(c=>!c.hidden),open=visible.some(c=>!c.open);for(const c of visible)c.open=open;});filter();</script></html>'''
    paths[2].write_text(page,encoding='utf-8')
    print({'issues':len(issues),'sources':len(sources),'local_hash_records':len(records),'unique_local_files':len(expected),
           'report':str(paths[2].relative_to(ROOT)),'new_CFD':0})


if __name__ == '__main__':
    main()
