"""Typed user constraints and a bounded engineering workflow shared by GUI and agent."""
from datetime import datetime,timezone
import math
FIELDS={
 'target_speed_kmh':('target_speed','m/s',1/3.6,False),
 'endurance_min':('endurance','s',60,False),
 'payload_kg':('payload_mass','kg',1,True),
 'altitude_m':('altitude','m',1,True),
 'max_span_m':('maximum_span','m',1,False),
 'max_mass_kg':('maximum_total_mass','kg',1,False),
 'max_stall_kmh':('maximum_stall_speed','m/s',1/3.6,False),
 'budget_try':('maximum_budget','TRY',1,False),
}
ACCEPTANCE=[
 'Gereksinimleri, birimleri, kaynakları ve eksik kritik girdileri kaydet; gerçek İHA aşamalarını kanıt olmadan tamamlama',
 'Açılan birincil kaynaklarla aday araştırması yap; taranan tasarım alanını, bütçeyi ve dışarıda kalan seçenekleri belirt',
 'Aday CAD dosyaları ile geometri/birim/ölçü kontrollerini kaydet; analizde kullanılan geometriyi eşleştir',
 'Re/Mach ve yönteme uygun native ön analizleri çalıştır; kapsam, referanslar ve yakınsamayan koşulları raporla',
 'CFD uygulanabilen adayları aynı koşullarla çöz; ağ, duvar çözünürlüğü, artık ve kuvvet kararlılığı kontrollerini yap; uygun olmayan/eksik CFD sonucunu kullanma',
 'Her gereksinime sağlandı/sağlanmadı/henüz değerlendirilemedi ve kanıt ekle; yalnız karşılaştırılabilir sonuçları sırala, açık CFD onayını başarı sayma',
 'Adaylar, elenme sebepleri, çizimler, ham analiz çıktıları, belirsizlikler ve kaynaklarla tek karşılaştırma raporu teslim et',
]

def number(value):
    if value is None or isinstance(value,str) and not value.strip(): return None
    if isinstance(value,bool): raise ValueError('Sayısal alana evet/hayır girilemez')
    if isinstance(value,str):
        value=value.strip()
        if ',' in value and '.' in value: raise ValueError('Binlik ayırıcı kullanmadan sayı gir: ör. 2,5')
        value=value.replace(',','.')
    try: result=float(value)
    except (ValueError,TypeError) as exc: raise ValueError('Sayısal alana birimsiz sayı gir: ör. 2,5') from exc
    if not math.isfinite(result): raise ValueError('Sonlu bir sayı gerekli')
    return result

def normalize(payload):
    title=payload.get('request','')
    if not isinstance(title,str) or len(title.strip())<5: raise ValueError('Görevini kısa bir cümleyle yaz')
    unknown=set(payload.get('constraints',{}))-set(FIELDS)
    if unknown: raise ValueError('Tanımsız kısıt alanları: '+', '.join(sorted(unknown)))
    inputs={}
    for key,(name,unit,scale,zero_ok) in FIELDS.items():
        raw=payload.get('constraints',{}).get(key); value=number(raw)
        if value is not None and (value<0 or value==0 and not zero_ok): raise ValueError(key+': geçersiz sınır')
        inputs[name]={'value':None if value is None else value*scale,'unit':unit,
            'status':'bilinmiyor' if value is None else 'kullanıcı gereksinimi',
            'source':None if value is None else 'Kullanıcının Mühendislik Merkezi formu',
            'raw_field':key,'raw_value':raw}
    options=payload.get('options',{}); n=number(options.get('candidate_limit',6)); m=number(options.get('cfd_candidate_limit',3))
    if n is None or m is None or n!=int(n) or m!=int(m) or not 1<=n<=30 or not 1<=m<=n:
        raise ValueError('Aday sayısı 1–30; CFD aday sayısı 1 ile aday sayısı arasında olmalı')
    return {'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),'request':title.strip(),
        'project_id':payload.get('project_id'),
        'kind':'engineering','inputs':inputs,'notes':str(payload.get('notes','')),
        'pipeline':['gereksinim','kaynaklı araştırma','aday CAD','ön analiz','uygun adaylarda CFD','kanıtlı eleme/sıralama','rapor'],
        'candidate_limit':int(n),'cfd_candidate_limit':int(m),
        'search_coverage':'Tanımlı tasarım alanında ve kaydedilen arama bütçesinde aday taraması; tüm olasılıkları tüketme iddiası yok',
        'acceptance':ACCEPTANCE,
        'comparison_policy':'Aynı koşullar, birimler ve kabul edilen yöntem; eksik veya başarısız CFD nihai sıralamayı engeller. Ön analiz sıralaması açıkça koşullu etiketlenir.'}
