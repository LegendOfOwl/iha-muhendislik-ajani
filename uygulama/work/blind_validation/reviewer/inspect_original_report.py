from pathlib import Path
import pypdfium2 as pdfium,json
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'work/blind_validation/reviewer/additional_sources'
doc=pdfium.PdfDocument(BASE/'agard_ar138.pdf')
rows=[]
for i in range(175,min(210,len(doc))):
 page=doc[i]; text=page.get_textpage().get_text_range()
 (BASE/f'page_{i+1:03}.txt').write_text(text,encoding='utf-8')
 rows.append({'pdf_page':i+1,'text':text[:280]})
 if 'CASE 6' in text.upper() or 'TABLE 6.7' in text.upper():
  page.render(scale=2).to_pil().save(BASE/f'page_{i+1:03}.png')
print(json.dumps({'pages':len(doc),'probes':rows},ensure_ascii=False))
