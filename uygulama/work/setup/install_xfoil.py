"""Fetch the author's Windows XFOIL build and keep it portable."""
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urljoin
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2]
index = "https://web.mit.edu/drela/Public/web/xfoil/"
with urlopen(index, timeout=45) as response:
    text = response.read().decode("utf-8")
links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.I | re.S)
selected = [href for href, label in links if re.sub("<[^>]+>", "", label).strip().upper() == "XFOIL6.99.ZIP"]
if len(selected) != 1:
    raise RuntimeError("Could not identify author's Windows distribution")
url = urljoin(index, html.unescape(selected[0]))
download = ROOT / "work/setup/downloads/XFOIL6.99.zip"
if not download.exists():
    with urlopen(url, timeout=90) as response:
        download.write_bytes(response.read())
target = (ROOT / "tools/xfoil").resolve()
target.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(download) as archive:
    if archive.testzip():
        raise RuntimeError("XFOIL ZIP failed CRC check")
    for member in archive.infolist():
        if member.is_dir():
            continue
        if not (target / member.filename).resolve().is_relative_to(target):
            raise RuntimeError("Unsafe archive path")
        archive.extract(member, target)
exes = [p for p in target.rglob("*.exe") if "xfoil" in p.name.lower()]
if len(exes) != 1:
    raise RuntimeError(f"Unexpected executable list: {exes}")
manifest = {"source_page": index, "source_url": url,
            "archive_sha256": hashlib.sha256(download.read_bytes()).hexdigest(),
            "archive_bytes": download.stat().st_size,
            "executable": str(exes[0]), "license": "GPL, upstream distribution retained"}
(ROOT / "work/setup/xfoil_install.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2), flush=True)
