"""Record verified GitHub publication without changing historical CFD evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json

from build_export import ROOT, DEST, STATE, STAGES, URL, dump, digest


def main():
    state = json.loads((STATE / 'github_publication_state.json').read_text(encoding='utf-8'))
    local = json.loads((STATE / 'local_verification.json').read_text(encoding='utf-8'))
    summary = json.loads((STATE / 'export_summary.json').read_text(encoding='utf-8'))
    assert state['status'] == 'published_verified' and state['public_verified'] and local['passed']
    rows = ''.join(f'<tr><td><a href="{URL}/releases/tag/{v}">{v}</a></td><td>{html.escape(n)}</td></tr>' for v,n,_ in STAGES)
    report = f'''<!doctype html><html lang="tr"><meta charset="utf-8"><title>GitHub yayını — İHA mühendislik ajanı</title>
<style>body{{font:17px/1.6 system-ui;max-width:1050px;margin:40px auto;padding:0 24px;color:#203449;background:#f8fafc}}.box{{background:white;border:1px solid #cbd5e1;border-radius:12px;padding:22px;margin:20px 0}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #cbd5e1;padding:10px;text-align:left}}a{{color:#1756a0}}code{{font-size:14px}}</style>
<h1>GitHub yayını tamamlandı</h1><p>24 Ekim 2026 · Public · Güncel sürüm v0.10.0</p>
<div class="box"><p><a href="{URL}"><b>LegendOfOwl/iha-muhendislik-ajani</b></a></p><p>10 commit, 10 sürüm etiketi ve 10 GitHub Release doğrulandı. Main commit: <code>{state['head']}</code>.</p>
<p>{local['git_original_file_hashes']} özgün dosya Git içinde, {local['archived_original_file_hashes']} büyük analiz dosyası 16 ham alan ZIP paketinde. Güncel uygulama/rapor ZIP'i ve SHA256 listesiyle toplam {state['remote_assets']} yayın varlığı yüklendi; her birinin sunucu SHA256 değeri yerel dosyayla eşleşti.</p></div>
<div class="box"><h2>Klasörler</h2><p><b>uygulama:</b> mevcut EXE/GUI, kaynaklar ve özgün proje yolları. <b>raporlar:</b> sürümlere göre rapor erişimi. <b>cizimler:</b> CAD/STEP/FreeCAD/OpenVSP/DXF/SVG erişimi. <b>analizler:</b> alan arşivleri ve dosya kataloğu. <b>testler:</b> kontroller ve kanıtlar. <b>kurulum:</b> ortam/geri yükleme yardımcıları. <b>surumler:</b> eski→yeni kilometre taşları.</p></div>
<h2>Sürümler</h2><table><tr><th>Sürüm</th><th>Aşama</th></tr>{rows}</table>
<div class="box"><h2>Geçmiş ve kapsam</h2><p>Önceden Git geçmişi bulunmadığı için eski sürümler eldeki korunmuş dosyalardan geriye dönük gruplandı. Bunlar özgün tarihteki eksiksiz eski çalışan uygulama kopyaları değildir. Tam güncel çalışma main/v0.10.0 içindedir. Kaynak dosyaların gözlenen değiştirme tarihleri ve SHA256 değerleri katalogda ayrı tutulur.</p>
<p>Katalog {summary['files']} özgün proje dosyasını izler. Dört tam üçüncü taraf araştırma PDF kopyası kaynak adresi/SHA256 ile ayrı geri yüklenir. Kurulu programlar, model ağırlıkları, ortam önbellekleri, kurucular ve hesap/OAuth bilgileri yüklenmedi; araç kurulum betikleri ve sürüm/kaynak manifestleri korundu. EXE başlatıcıdır; bütün araçları içeren bağımsız bir kurucu değildir.</p>
<p>Başarısız denemeler korunmuştur. Yeni fizik/CFD veya görülmemiş LLM doğrulaması yapılmadı; mevcut açık mühendislik kabulleri yayınla kapanmaz.</p></div>
<div class="box"><h2>Doğrulama</h2><p>4.267 Git dosyasının çalışma kopyası ve gerçek Git blob SHA256 değerleri; 866 arşiv dosyasının açılmış içeriği; 16 ZIP'in dosya listesi ve arşiv SHA256 değerleri denetlendi. Geri yüklemede 10 geçerli/geçersiz dosya ve üzerine yazmama kontrolü geçti. Kimlik bilgisi dosyaları ile yasaklanan klasörler izlenen Git dosyalarında bulunmadı.</p>
<p>Uzak main ve bütün tag commitleri yerel kayıtlarla eşleşti. Deponun public olduğu ve 10 Release'in yayımlandığı ayrıca GitHub API ile doğrulandı.</p>
<ul><li><a href="{URL}/releases/tag/v0.10.0">Güncel uygulama/rapor paketini indir</a></li><li><a href="{URL}/tree/main/surumler">Bütün sürüm klasörleri</a></li><li><a href="github_local_verification_20261024.json">Yerel bütünlük kontrolleri</a></li><li><a href="../data/github_publication_20261024.json">Uzak yayın ve sunucu hash kayıtları</a></li></ul></div></html>'''
    dest = ROOT / 'outputs/reports/github_yayini_20261024.html'; dest.write_text(report, encoding='utf-8')
    task_path = ROOT / 'outputs/data/tasks/20261024-170508-83546a.json'
    task = json.loads(task_path.read_text(encoding='utf-8'))
    evidence = ['outputs/reports/github_yayini_20261024.html', 'outputs/reports/github_local_verification_20261024.json',
                'outputs/data/github_publication_20261024.json']
    task.update(status='tamamlandı', completed_utc=datetime.now(timezone.utc).isoformat(), phase='sürümlü GitHub yayını',
                acceptance=['Yeni public repo ve kategori erişimi', 'Açık geriye dönük sürüm grupları, 10 commit/tag/release',
                            'Ham dosyalar ve kod SHA256 korunması', 'Hesap/kimlik dosyalarını dışarıda bırakma',
                            'Tüm yayın varlıklarının sunucu hashleri ve uzak commitlerin doğrulanması'],
                evidence=[{'path': p, 'sha256': digest(ROOT / p)} for p in evidence], blocked_by=[],
                repository_url=URL, repository_visibility='public', release='v0.10.0',
                local_repository=str(DEST), source_snapshot_utc=summary['created_utc'],
                historical_versions_reconstructed=True, original_git_history_available=False,
                expert_qualification_passed=False, minimum_physical_qualification_passed=False,
                completion_scope='İstenen yeni public depoda kaynak, rapor, CAD ve ham analiz arşivlerinin sürümlü yayını; mühendislik kabulleri ayrı')
    dump(task_path, task)
    path = ROOT / 'PROJECT_STATE.md'; content = path.read_text(encoding='utf-8')
    heading = '## 24 Ekim: yeni public GitHub deposu ve sürümlü dağıtım'
    assert heading not in content
    section = f'''\n{heading}

- Kullanıcının açık public tercihiyle `{URL}` oluşturuldu. Main ve10 tag/Release doğrulandı; güncel dağıtım v0.10.0, commit `{state['head']}`. Yerel kopya `{DEST}`. Kaynak çalışma klasörü taşınmadı; hesap/OAuth verileri depoya alınmadı.
- Önceden Git tarihçesi yoktu; v0.1.0→v0.10.0 aşamaları mevcut korunmuş dosyalardan geriye dönük gruplandırılmış içe aktarmadır. Eski tag'ler özgün tarihteki tam çalışan uygulama imajı diye sunulmadı. `uygulama`, `raporlar`, `cizimler`, `analizler`, `testler`, `kurulum`, `surumler` erişimi var; uygulama içi özgün bağıl yollar korunur.
- {local['git_original_file_hashes']} dosyanın Git blob SHA256 ve {local['archived_original_file_hashes']} ham dosyanın açılmış ZIP içeriği doğrulandı.16 ham alan ZIP'i, güncel uygulama/rapor ZIP'i ve SHA256 listesiyle {state['remote_assets']} varlığın sunucu hashleri eşleşti. Dört üçüncü taraf tam PDF kaynak adresi/hash ile dış referanstır. Kurulu runtime/model ağırlıkları/kurucular aktarılmadı; kurulum manifestleri ve betikleri durur.
- Geri yükleme için10 geçerli/geçersiz karşı örnek geçti. Yayın raporu `outputs/reports/github_yayini_20261024.html`, uzak makbuz `outputs/data/github_publication_20261024.json`, görev `20261024-170508-83546a`. Bu yayın yeni CFD/LLM fizik doğrulaması değildir; önceki açık kabuller korunur. Git güven istisnası yalnız yükleyici süreçte bu yeni klasöre uygulandı; global Git ayarı değiştirilmedi.
'''
    path.write_text(content + section, encoding='utf-8')
    print(json.dumps({'report': str(dest), 'repository': URL, 'status': 'complete'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
