"""Resolve a local portable MSYS2 UCRT Fortran toolchain from its official database."""
from pathlib import Path
from datetime import datetime, timezone
import ctypes
import hashlib
import io
import json
import re
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).parent


def decompress(raw):
    lib=ctypes.CDLL(str(ROOT/'tools/elmer/ElmerFEM-gui-nompi-Windows-AMD64/bin/libzstd.dll'))
    lib.ZSTD_getFrameContentSize.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    lib.ZSTD_getFrameContentSize.restype=ctypes.c_ulonglong
    lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
    lib.ZSTD_decompress.restype=ctypes.c_size_t
    lib.ZSTD_isError.argtypes=[ctypes.c_size_t];lib.ZSTD_isError.restype=ctypes.c_uint
    lib.ZSTD_getErrorName.argtypes=[ctypes.c_size_t];lib.ZSTD_getErrorName.restype=ctypes.c_char_p
    source=ctypes.create_string_buffer(raw)
    expected=lib.ZSTD_getFrameContentSize(source,len(raw))
    sizes=[expected] if expected<512*1024**2 else [2**x for x in range(22,30)]
    for size in sizes:
        dest=ctypes.create_string_buffer(size)
        result=lib.ZSTD_decompress(dest,size,source,len(raw))
        if not lib.ZSTD_isError(result):return dest.raw[:result]
        error=lib.ZSTD_getErrorName(result).decode()
        if 'Destination buffer is too small' not in error:raise RuntimeError(error)
    raise RuntimeError('Decompressed package exceeds scoped 512 MiB cap')


def main():
    db=BASE/'sources/ucrt64.db'
    packages={}
    with tarfile.open(fileobj=io.BytesIO(decompress(db.read_bytes()))) as archive:
        for member in archive:
            if member.isfile() and member.name.endswith('/desc'):
                data=archive.extractfile(member).read().decode()
                fields={m.group(1):m.group(2).strip().splitlines() for m in re.finditer(r'%([^%\n]+)%\n(.*?)(?=\n%|\Z)',data,re.S)}
                packages[fields['NAME'][0]]=fields
    root='mingw-w64-ucrt-x86_64-gcc-fortran'
    todo=[root];selected={}
    while todo:
        name=todo.pop()
        if name in selected:continue
        assert name.startswith('mingw-w64-ucrt-x86_64-'),name
        f=packages[name]
        selected[name]={k:f[k][0] for k in ['NAME','VERSION','FILENAME','CSIZE','ISIZE','SHA256SUM']}
        selected[name]['depends']=f.get('DEPENDS',[])
        selected[name]['url']='https://mirror.msys2.org/mingw/ucrt64/'+f['FILENAME'][0]
        for dep in f.get('DEPENDS',[]):
            d=re.split(r'[<>=]',dep)[0]
            if d not in packages:raise KeyError('Unresolved dependency '+dep)
            todo.append(d)
    download=sum(int(x['CSIZE']) for x in selected.values())
    expanded=sum(int(x['ISIZE']) for x in selected.values())
    plan={'created_utc':datetime.now(timezone.utc).isoformat(),'root_package':root,
          'source_url':'https://mirror.msys2.org/mingw/ucrt64/ucrt64.db','db_sha256':hashlib.sha256(db.read_bytes()).hexdigest(),
          'compressed_bytes':download,'installed_bytes':expanded,'packages':list(selected.values()),
          'install_root':'tools/fortran_msys2','system_path_changed':False,'budget_download_bytes':180*1024**2}
    assert download<plan['budget_download_bytes'],download
    (BASE/'compiler_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(json.dumps({'packages':len(selected),'download_MiB':download/1024**2,'installed_MiB':expanded/1024**2,'versions':{k:x['VERSION'] for k,x in selected.items()}},indent=2))


if __name__=='__main__':main()
