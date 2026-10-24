"""Evidence-bound comparison. Unaccepted or missing CFD can never produce a final winner."""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def compare(candidates,limits,objective_key='CDwing_estimated'):
    if not all(not isinstance(v,bool) and isinstance(v,(float,int)) and math.isfinite(v) and v>0 for v in limits.values()):
        raise ValueError('Comparison limits must be positive finite values in the declared units')
    rows=[]
    for c in candidates:
        reasons=[]; unknown=[]
        for name,limit in limits.items():
            value=c.get(name)
            if value is None: unknown.append(name)
            elif value>limit: reasons.append(f'{name}: {value:.6g} > {limit:.6g}')
        cfd=c.get('CFD') or {}; cfd_ok=False
        if cfd.get('report'):
            p=(ROOT/cfd['report']).resolve()
            if not p.is_relative_to(ROOT) or not p.exists(): unknown.append('CFD kanıtı yok')
            elif sha(p)!=cfd.get('sha256'): unknown.append('CFD kanıt özeti uyuşmuyor')
            else:
                r=json.loads(p.read_text(encoding='utf-8-sig'))
                cfd_ok=bool(r.get('quality_passed') is True and r.get('geometry_sha256')==c.get('geometry_sha256')
                    and r.get('conditions_sha256')==c.get('conditions_sha256')
                    and r.get('analysis_scope')==c.get('required_CFD_scope') and c.get('required_CFD_scope')
                    and c.get('geometry_sha256') and c.get('conditions_sha256'))
                if not cfd_ok: unknown.append('CFD kabulü/geometri/koşul eşleştirmesi açık')
        else: unknown.append('Bu adaya ait kabul edilmiş CFD yok')
        score=c.get(objective_key)
        if isinstance(score,bool) or score is not None and (not isinstance(score,(int,float)) or not math.isfinite(score)):
            score=None
        if score is None: unknown.append('Karşılaştırma metriği bilinmiyor')
        rows.append({'id':c['id'],'objective':score,'requirements_status':'sağlanmadı' if reasons else ('henüz değerlendirilemedi' if unknown else 'sağlandı'),
            'rejection_reasons':reasons,'open_checks':unknown,'CFD_accepted_for_candidate':cfd_ok,
            'conditional_rank':None,'final_rank':None,'evidence':c.get('evidence',{})})
    preliminary=sorted([r for r in rows if not r['rejection_reasons'] and r['objective'] is not None],key=lambda r:r['objective'])
    for i,r in enumerate(preliminary,1): r['conditional_rank']=i
    final=sorted([r for r in preliminary if not r['open_checks']],key=lambda r:r['objective'])
    for i,r in enumerate(final,1): r['final_rank']=i
    return {'timestamp':datetime.now(timezone.utc).isoformat(),'rows':rows,
        'final_winner':final[0]['id'] if final else None,
        'status':'nihai karşılaştırma' if final else 'koşullu ön karşılaştırma; CFD kabulü bekleniyor',
        'limits':limits,'objective':objective_key,'coverage':'Only listed candidates; no exhaustive-design-space claim'}

def main():
    p=OUT/'reports/wing_study_results.json'; source=json.loads(p.read_text()); candidates=[]
    for c in source['candidates']:
        candidates.append(dict(c,id='AR'+str(c['AR']),CFD=None,
            evidence={'report':str(p.relative_to(ROOT)),'sha256':sha(p),'source_scope':'Önceki izole dikdörtgen kanat VLM/XFOIL çalışması; bu tur yeniden çözülmedi'}))
    # Explicit synthetic screening condition; no transfer into actual UAV requirements.
    result=compare(candidates,{'span_m':2.1})
    result.update(scope='Kayıtlı üç kanatla raporlama/eleme sınaması; maksimum açıklık 2.1 m test varsayımı',
        source_solver_rerun=False,unknown_aircraft_checks=['kütle','güç/enerji','CG/trim/kararlılık','yapısal yeterlilik'],
        note='Koşullu sıra yalnız tahmini izole kanat sürüklemesine dayanır; uçak uygunluğu veya CFD onaylı seçim değildir.')
    result['passed']=bool(len(result['rows'])==3 and result['final_winner'] is None)
    result['quality_passed']=False
    (OUT/'reports/candidate_comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    from html import escape
    rows=''.join('<tr>'+''.join('<td>'+escape(str(x))+'</td>' for x in [r['id'],r['conditional_rank'] or '—',r['final_rank'] or '—',r['requirements_status'],', '.join(r['rejection_reasons']+r['open_checks'])])+'</tr>' for r in result['rows'])
    html='<!doctype html><html lang="tr"><meta charset="utf-8"><title>Aday karşılaştırması</title><style>body{font:16px/1.6 Segoe UI,sans-serif;max-width:1100px;margin:40px auto;padding:20px;color:#183344}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border:1px solid #ccdce5}th{background:#eef5f8}</style><h1>Koşullu aday karşılaştırması</h1><p>Önceki üç izole kanat sonucuyla eleme/sıralama sınaması. 2,1 m maksimum açıklık test varsayımıdır. Bu tur çözücü yeniden çalıştırılmadı. Gerçek İHA seçimi değildir.</p><table><tr><th>Aday</th><th>Ön sıra</th><th>Nihai sıra</th><th>Kabul</th><th>Gerekçe / açık kontrol</th></tr>'+rows+'</table><p>Nihai kazanan yok. Sıra, VLM/XFOIL tahmini izole kanat sürüklemesine dayanır; bu adayların CFD kabulü, bütün uçak kütle/güç/kararlılık/yapı kontrolleri açık.</p><p><a href="candidate_comparison.json">Ölçümler ve kanıt özeti</a> · <a href="hafif_cfd_ve_is_akisi.html">İş akışı raporu</a></p></html>'
    (OUT/'reports/candidate_comparison.html').write_text(html,encoding='utf-8')
    print(result['status']); print('Nihai kazanan:',result['final_winner'])
if __name__=='__main__': main()
