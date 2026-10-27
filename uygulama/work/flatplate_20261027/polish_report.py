"""Editorial spacing only; preserve earlier report and update its task evidence."""
from pathlib import Path
import sys, re, shutil
ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'work/flatplate_20261025'))
from prepare import read, save, sha, now


def polish(text):
    replacements = {
        'sabit2B': 'sabit 2B', 'körLLM': 'kör LLM', 'KuruluSU2v8.5.0': 'Kurulu SU2 v8.5.0',
        'özgünfine3999': 'özgün fine3999', 'nativeexit0': 'native exit0', 'Nativeexit0': 'Native exit0',
        'aşamaRHS': 'aşama RHS', 'ekLINELET': 'ek LINELET', 'maksimumOpenMP': 'maksimum OpenMP',
        'yalnızPREC_THREADS0/1': 'yalnız PREC_THREADS 0/1', 'FGMRES40': 'FGMRES 40',
        'adaptiveCFL': 'adaptive CFL', 'yoğunlukSI': 'yoğunluk SI', 'ailesindekifine3999': 'ailesindeki fine3999',
        'küçükRHS': 'küçük RHS', 'bizimLU-SGS': 'bizim LU-SGS', 'testleriEuler/Cart3D': 'testleri Euler/Cart3D',
        'girişindeRANS': 'girişinde RANS', 'bizimSA-negRANS': 'bizim SA-neg RANS',
        'nativeNEWTON_KRYLOV': 'native NEWTON_KRYLOV', 'veyaLINELET': 'veya LINELET',
        'sıcakNewton': 'sıcak Newton', 'değişmemişv8.5.0': 'değişmemiş v8.5.0',
        'Hibrit çizgi+SGS': 'Hibrit çizgi + SGS', 'keyfiCAD': 'keyfi CAD', 'testlerCFD': 'testler CFD',
        'veyaLLM': 'veya LLM', 'GerçekİHA': 'Gerçek İHA', 'GenelM6': 'Genel M6',
        'YeniLLM': 'Yeni LLM', 'üç-ağfine3999': 'üç ağ fine3999', 'NativeLINELET': 'Native LINELET',
    }
    # Protect code, link destinations, HTML tags and filenames from text edits.
    parts = re.split(r'(`[^`]*`|\]\([^)]*\)|<[^>]*>)', text)
    for i in range(0, len(parts), 2):
        s = parts[i]
        for old, new in replacements.items(): s = s.replace(old, new)
        s = re.sub(r'(\d)(hücre|nokta|adım|örnek|normal|yazılım|yeni|bölge|log10|µm|GiB)(?=\b|[A-ZÇĞİÖŞÜ])', r'\1 \2', s)
        s = re.sub(r'(\d)(s|m)(?=[,.; /]|$)', r'\1 \2', s)
        s = re.sub(r'(aralığı|yaklaşık|farkı|sınır|sıklığı|geçmiş|kolda|alanı|altında|oranı|geçmişi)(?=\d)', r'\1 ', s)
        s = re.sub(r'(?<=[,;])(?=[A-Za-zÇĞİÖŞÜçğıöşü])|(?<=;)(?=\d)', ' ', s)
        s = re.sub(r'(?<=[.!?])(?=\d{2,})', ' ', s)
        s = s.replace('gereken≥', 'gereken ≥').replace('ve≤', 've ≤').replace('kayıtlı≤', 'kayıtlı ≤')
        s = s.replace('önkoşullayıcı bölgesi1', 'önkoşullayıcı bölgesi 1').replace('bölünme0→4', 'bölünme 0→4')
        parts[i] = s
    return ''.join(parts)


def main():
    taskpath = ROOT / read(BASE / 'task.json')['path']
    task = read(taskpath)
    saved = BASE / 'editorial_v1'
    saved.mkdir(exist_ok=True)
    changes = []
    for suffix in ('.md', '.html'):
        path = ROOT / ('outputs/reports/cfd_cizgi_kapsami_20261027' + suffix)
        original = saved / path.name
        if not original.exists(): shutil.copyfile(path, original)
        before = sha(original)
        path.write_text(polish(original.read_text(encoding='utf-8')), encoding='utf-8')
        for entry in task['evidence']:
            if entry['path'] == str(path.relative_to(ROOT)):
                if not (saved / ('closure_' + path.name)).exists():
                    shutil.copyfile(ROOT / entry['archived'], saved / ('closure_' + path.name))
                shutil.copyfile(path, ROOT / entry['archived'])
                entry['previous_editorial_sha256'] = before
                entry['sha256'] = sha(path)
        changes.append({'path': str(path.relative_to(ROOT)), 'before': before, 'after': sha(path)})
    task['editorial_revision'] = {'created_utc': now(), 'changes': changes, 'native_or_numerical_results_changed': False}
    save(taskpath, task)
    closure = ROOT / 'outputs/data/task_evidence' / task['id'] / 'closure'
    shutil.copyfile(Path(__file__), closure / 'code_final/polish_report.py')
    snap = closure / 'code_snapshot.json'
    data = read(snap)
    p = closure / 'code_final/polish_report.py'
    data['files_sha256'][str(p.relative_to(ROOT))] = sha(p)
    save(snap, data)
    print({'editorial_files': len(changes), 'native_results_changed': False})


if __name__ == '__main__': main()
