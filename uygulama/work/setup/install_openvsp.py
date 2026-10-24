"""Install the official portable OpenVSP distribution inside this workspace."""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2]
downloads = ROOT / "work/setup/downloads"
downloads.mkdir(parents=True, exist_ok=True)
with urlopen(Request("https://openvsp.org/download.php", headers={"User-Agent": "UAV-engineering-setup/1.0"}), timeout=45) as response:
    page = response.read().decode("utf-8")
candidates = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', page, re.S | re.I)
matches = [(html.unescape(href), re.sub("<[^>]+>", "", label).strip())
           for href, label in candidates if "64-bit Python 3.11" in re.sub("<[^>]+>", "", label)]
if len(matches) != 1:
    raise RuntimeError(f"Expected one Windows Python3.11 link, found {matches}")
download_url = urljoin("https://openvsp.org/", matches[0][0])
if urlparse(download_url).hostname not in {"openvsp.org", "www.openvsp.org"}:
    raise RuntimeError("Unexpected download host")
archive_path = downloads / Path(urlparse(download_url).path).name
print("Official distribution:", matches[0][1], download_url, flush=True)
if not archive_path.exists():
    request = Request(download_url, headers={"User-Agent": "UAV-engineering-setup/1.0"})
    with urlopen(request, timeout=90) as response, archive_path.open("wb") as output:
        amount = 0
        while block := response.read(1024 * 1024):
            output.write(block)
            amount += len(block)
            if amount % (8 * 1024 * 1024) < len(block):
                print(f"Downloaded {amount / 2**20:.1f} MiB", flush=True)
sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
target = (ROOT / "tools/openvsp").resolve()
target.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive_path) as archive:
    bad = archive.testzip()
    if bad:
        raise RuntimeError(f"ZIP CRC failure: {bad}")
    for entry in archive.infolist():
        resolved = (target / entry.filename).resolve()
        if not resolved.is_relative_to(target):
            raise RuntimeError("Unsafe ZIP member path")
    archive.extractall(target)
vsp = list(target.rglob("vsp.exe"))
if len(vsp) != 1:
    raise RuntimeError(f"Expected one vsp.exe, got {vsp}")
install = vsp[0].parent
manifest = {
    "installed_utc": datetime.now(timezone.utc).isoformat(),
    "source_page": "https://openvsp.org/download.php", "source_url": download_url,
    "label": matches[0][1], "archive_sha256": sha256,
    "archive_bytes": archive_path.stat().st_size,
    "install_directory": str(install),
    "executables": {p.name: str(p) for p in install.glob("*.exe")},
    "integration": "Native executables and AngelScript. Python binding is not installed.",
}
(ROOT / "work/setup/openvsp_install.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2), flush=True)
