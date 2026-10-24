"""Re-run installed engineering tools and rebuild the evidence report."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
LABELS = {"numeric": "Sayısal hesaplama", "guards": "Eksik veri ve birim kontrolleri",
          "aero": "Aerodinamik ve optimizasyon", "cad": "Parametrik CAD ve STEP"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", nargs="+", choices=list(LABELS), default=list(LABELS))
    args = parser.parse_args()
    started = datetime.now(ZoneInfo("Europe/Istanbul"))
    run_id = started.strftime("%Y%m%d-%H%M%S")
    logs = ROOT / "work" / "tests" / "logs" / run_id
    results_dir = ROOT / "work" / "tests" / "results"
    logs.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    for name in ["reports", "data", "plots", "cad"]:
        (OUT / name).mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                       MPLCONFIGDIR=str(ROOT / "work" / "matplotlib"),
                       XDG_CACHE_HOME=str(ROOT / "work" / "cache"),
                       OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")
    groups = []
    for group in args.groups:
        executable = ROOT / (".venv-cad" if group == "cad" else ".venv") / "Scripts" / "python.exe"
        if not executable.exists():
            groups.append({"group": group, "passed": False, "checks": [], "versions": {},
                           "error": "Python environment not installed", "status": "not_installed"})
            print(f"{group}: NOT INSTALLED", flush=True)
            continue
        result_path = results_dir / f"{group}.json"
        # Delete only this known stale result; never accept evidence from an earlier run.
        result_path.unlink(missing_ok=True)
        begin = time.perf_counter()
        print(f"{group}: running...", flush=True)
        try:
            process = subprocess.run([str(executable), "-X", "utf8",
                                      str(ROOT / "work" / "tests" / "check_worker.py"), group],
                                     cwd=ROOT, env=environment, capture_output=True,
                                     text=True, encoding="utf-8", errors="replace", timeout=300)
            (logs / f"{group}.stdout.txt").write_text(process.stdout, encoding="utf-8")
            (logs / f"{group}.stderr.txt").write_text(process.stderr, encoding="utf-8")
            result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {
                "group": group, "passed": False, "checks": [], "versions": {},
                "error": "Worker produced no JSON result; see logs."}
            result["exit_code"] = process.returncode
            result["passed"] = bool(result.get("passed")) and process.returncode == 0
        except subprocess.TimeoutExpired:
            result = {"group": group, "passed": False, "checks": [], "versions": {},
                      "error": "300 second timeout"}
        result["elapsed_seconds"] = round(time.perf_counter() - begin, 3)
        groups.append(result)
        print(f"{group}: {'PASS' if result['passed'] else 'FAIL'} ({result['elapsed_seconds']} s)", flush=True)
    dependency_checks = {}
    for env_name in [".venv", ".venv-cad"]:
        executable = ROOT / env_name / "Scripts" / "python.exe"
        if executable.exists():
            process = subprocess.run([str(executable), "-m", "pip", "check"], cwd=ROOT,
                                     capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            dependency_checks[env_name] = {"passed": process.returncode == 0,
                                           "output": process.stdout + process.stderr}
    all_ok = all(g["passed"] for g in groups) and all(v["passed"] for v in dependency_checks.values())
    passed = sum(c["passed"] for g in groups for c in g["checks"])
    count = sum(len(g["checks"]) for g in groups)
    summary = {"run_id": run_id, "started_local": started.isoformat(), "project_root": str(ROOT),
               "synthetic_test_only": True, "all_requested_groups_passed": all_ok,
               "passed_checks": passed, "total_checks": count, "groups": groups,
               "dependency_checks": dependency_checks, "logs_directory": str(logs),
               "deferred": ["FreeCAD/CalculiX", "ANSYS"],
               "does_not_prove": ["LLM hallucination-free behavior", "actual UAV feasibility",
                                   "experimental aerodynamic validation", "structural FEM validation"]}
    (OUT / "reports" / "test_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    (logs / "test_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Hafif mühendislik ortamı — kurulum ve test raporu", "",
             f"Test zamanı: {started.strftime('%d.%m.%Y %H:%M:%S')} (Europe/Istanbul)", "",
             f"**Sonuç: {'İSTENEN GRUPLAR GEÇTİ' if all_ok else 'AÇIK KONTROLLER VAR'} — {passed}/{count} kontrol geçti.**", "",
             "Bu rapor gerçek yerel çalıştırmalardan üretilmiştir. Bütün örnekler sentetik kurulum testidir; İHA projesinin tasarım değerleri değildir.", "",
             "| Grup | Durum | Kontrol sayısı | Süre |", "|---|---|---:|---:|"]
    for group in groups:
        status = "Geçti" if group["passed"] else "Kurulu değil" if group.get("status") == "not_installed" else "Başarısız"
        lines.append(f"| {LABELS[group['group']]} | {status} | {len(group['checks'])} | {group.get('elapsed_seconds', 0):.2f} s |")
    lines.extend(["", "## Sürümler ve ortamlar", "", f"Proje: `{ROOT}`", "",
                  "Python ortamları, masaüstü uygulamasının mevcut Python 3.12 tabanından oluşturulmuştur. Sistem genelinde Python/PATH ayarı değiştirilmemiştir. Bu taban ileride kaldırılırsa ortamlar yeniden kurulmalıdır.", ""])
    for group in groups:
        if group.get("versions"):
            lines.append(f"- {LABELS[group['group']]}: " + ", ".join(f"{name} {version}" for name, version in group["versions"].items()))
    for name, item in dependency_checks.items():
        lines.append(f"- {name}: bağımlılık kontrolü {'geçti' if item['passed'] else 'BAŞARISIZ'}; {item['output'].strip()}")
    lines.extend(["", "## Ölçümler ve kabul ölçütleri", ""])
    for group in groups:
        lines.extend([f"### {LABELS[group['group']]}", ""])
        for item in group["checks"]:
            lines.append(f"- **{'GEÇTİ' if item['passed'] else 'BAŞARISIZ'} — {item['name']}**: {item.get('criterion', '')}")
            lines.append("  Ölçüm: `" + json.dumps(item.get("measured"), ensure_ascii=False) + "`")
        if group.get("error"):
            lines.extend(["", "Çalıştırma hatası:", "```text", group["error"], "```"])
        lines.append("")
    lines.extend(["## Oluşturulan çıktılar", ""])
    artifacts = ["plots/naca2412.png", "plots/vlm_convergence.png", "plots/cad_coupon.png",
                 "cad/calibration_coupon.step", "cad/calibration_coupon.stl",
                 "data/input_guard_examples.json", "data/neuralfoil_naca0012.csv",
                 "data/vlm_panel_convergence.csv", "data/numeric_calibration.csv"]
    for artifact in artifacts:
        if (OUT / artifact).exists():
            lines.append(f"- [{artifact}](../{artifact})")
    lines.extend(["", "## Kapsam ve sınırlar", "",
                  "- Girdi testleri belirli eksik/yanlış verileri yakalar. Bunlar ajan modelinin her hatasını veya halüsinasyonunu engellediğini kanıtlamaz.",
                  "- NACA grafiği geometri testidir. NeuralFoil kontrolleri kestirim modelinin entegrasyon ve fiziksel simetri kontrolleridir; deneysel doğrulama değildir.",
                  "- VLM küçük hücum açısında potansiyel akış testidir; hesaplanan sürükleme indüklenmiş bileşendir. Viskoz sürükleme, ayrılma ve stall burada doğrulanmadı.",
                  "- Yaklaşık kaldırma çizgisi referansı kaba bir tutarlılık kontrolüdür. Panel yakınsaması bu örneğe aittir, tüm geometriler için yeterlilik kanıtı değildir.",
                  "- CAD kuponu tek bir katı ve STEP aktarım testidir. Gerilme/deformasyon veya FEM çözümü yapılmadı.",
                  "- OpenVSP/VSPAERO ve XFOIL sonradan kurulup ayrı harici araç testleriyle doğrulandı. Bu komut temel Python/CAD kontrolleridir; harici analizler için Harici-Testleri-Calistir.cmd ve external_tools_report.md kullanılır.",
                  "- FreeCAD/CalculiX ve ANSYS kurulmadı. ANSYS ağır kurulum ve lisans aşamasına bırakıldı.",
                  "- Gerçek İHA gereksinimleri henüz bu klasörde doğrulanmadı. Güç, kararlılık, yapı, uçuş süresi ve hedef hız uygunluğu değerlendirilmedi.", "",
                  "## Yeniden çalıştırma", "",
                  "Üst klasördeki **Testleri-Calistir.cmd** dosyasını aç. Her çalıştırma araçları tekrar çalıştırır ve bu raporu günceller. Rapor, canlı internet erişimi gerektirmez.", "",
                  f"Ham loglar: `{logs}`", "",
                  "## Yöntem ve kurulum kaynakları", "",
                  "- [Codex proje talimatları](https://learn.chatgpt.com/docs/agent-configuration/agents-md)",
                  "- [AeroSandbox](https://github.com/peterdsharpe/AeroSandbox)",
                  "- [VortexLatticeMethod](https://aerosandbox.readthedocs.io/en/master/autoapi/aerosandbox/aerodynamics/aero_3D/vortex_lattice_method/)",
                  "- [CadQuery kurulumu](https://cadquery.readthedocs.io/en/latest/installation.html)",
                  "- [NASA kaldırma denklemi](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/)", ""])
    (OUT / "reports" / "setup_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Result: {passed}/{count}; report: outputs/reports/setup_report.md", flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
