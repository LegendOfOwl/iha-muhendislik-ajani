from incremental_export import DEST

def main():
    path=DEST/'kurulum/analizleri_geri_yukle.py';text=path.read_text(encoding='utf-8')
    old="""        expected = {r['repository_path']: r for r in records}
        with zipfile.ZipFile(archive) as zipped:
            if set(zipped.namelist()) != set(expected) or len(zipped.namelist()) != len(expected):
                raise ValueError('Arşiv dosya listesi katalogla eşleşmiyor.')
            for name, rec in expected.items():
"""
    new="""        # Older assets use one member per destination. New assets may share
        # immutable content; every destination still has its own expected hash.
        expected = {r['repository_path']: r for r in records}
        if len(expected) != len(records):
            raise ValueError('Katalogda yinelenen hedef yolu.')
        members = {}
        for rec in records:
            member = rec.get('archive_member', rec['repository_path'])
            if not member.startswith('uygulama/') or '..' in Path(member).parts:
                raise ValueError('Güvenli olmayan arşiv üyesi.')
            if member in members and members[member] != rec['sha256']:
                raise ValueError('Aynı arşiv üyesi için farklı hash bekleniyor.')
            members[member] = rec['sha256']
        with zipfile.ZipFile(archive) as zipped:
            if set(zipped.namelist()) != set(members) or len(zipped.namelist()) != len(members):
                raise ValueError('Arşiv dosya listesi katalogla eşleşmiyor.')
            for name, rec in expected.items():
"""
    assert old in text
    text=text.replace(old,new).replace('with zipped.open(name) as source, partial.open(\'xb\') as stream:',"with zipped.open(rec.get('archive_member', name)) as source, partial.open('xb') as stream:")
    compile(text,str(path),'exec');path.write_text(text,encoding='utf-8');print('Backwards-compatible shared-member restore prepared')

if __name__=='__main__':main()
