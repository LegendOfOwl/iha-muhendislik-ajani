"""Execute one real integration check and save raw, machine-readable evidence."""
import argparse
import copy
import importlib.metadata as metadata
import json
import math
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work"))
OUT = ROOT / "outputs"
CHECKS = []


def check(name, condition, measured=None, criterion=None):
    CHECKS.append({"name": name, "passed": bool(condition),
                   "measured": measured, "criterion": criterion})


def numeric():
    import numpy as np
    import pandas as pd
    from scipy.integrate import quad
    from scipy.optimize import minimize
    integral, error = quad(np.sin, 0, np.pi)
    check("Sinüs integralinin analitik değeri", abs(integral - 2) < 1e-10,
          {"integral": integral, "error_estimate": error}, "|I-2| < 1e-10")
    result = minimize(lambda x: (x[0] - 3) ** 2, [0.5], bounds=[(0, 2)], method="L-BFGS-B")
    check("Sınır kısıtlı optimizasyon", result.success and abs(result.x[0] - 2) < 1e-6,
          {"x": float(result.x[0]), "success": bool(result.success)}, "0<=x<=2; optimum x=2, hata<1e-6")
    matrix = np.array([[3., 1.], [1., 2.]])
    rhs = np.array([9., 8.])
    solution = np.linalg.solve(matrix, rhs)
    check("Lineer denklem sistemi", np.allclose(solution, [2, 3], atol=1e-12),
          solution.tolist(), "Bilinen çözüm [2,3]")
    pd.DataFrame({"quantity": ["integral_sin_0_pi", "bounded_optimum"],
                  "value": [integral, result.x[0]]}).to_csv(OUT / "data" / "numeric_calibration.csv", index=False)


def guards():
    from engineering.conceptual import lift_screening
    base = {name: {"value": value, "unit": unit, "status": "assumption",
                   "source": "Synthetic integration-test fixture, not project data."}
            for name, value, unit in [("mass", 3., "kg"), ("wing_area", .4, "m2"),
                                      ("density", 1.225, "kg/m3"), ("cl_max", 1.1, "1")]}
    result = lift_screening(base)
    check("Tam girdide koşullu sonuç", result["status"] == "conditional_lift_screening"
          and result["aircraft_feasibility"] == "not_assessed", result["status"], "Yalnız kaldırma ön hesabı")
    mass4 = copy.deepcopy(base)
    mass4["mass"]["value"] *= 4
    ratio = lift_screening(mass4)["results"]["stall_speed_m_s"] / result["results"]["stall_speed_m_s"]
    check("Kütle ölçekleme kontrolü", abs(ratio - 2) < 1e-12, ratio, "Kütle x4 => hız x2")
    missing = copy.deepcopy(base)
    del missing["cl_max"]
    missing_result = lift_screening(missing)
    check("Eksik CLmax sonucu engeller", missing_result["status"] == "blocked"
          and missing_result["results"] is None, missing_result, "Sayı üretmeden blocked")
    examples = {"complete_synthetic_case": result, "missing_clmax": missing_result}
    malformed = lift_screening([])
    check("Geçersiz girdi yapısı", malformed["status"] == "blocked", malformed["issues"], "JSON nesnesi gerekli")
    for label, field, update in [
        ("Yanlış kütle birimi", "mass", {"unit": "g"}),
        ("Sıfır kanat alanı", "wing_area", {"value": 0}),
        ("Negatif yoğunluk", "density", {"value": -1}),
        ("NaN kaldırma katsayısı", "cl_max", {"value": float("nan")}),
        ("Kaynağı olmayan girdi", "mass", {"source": ""}),
        ("Bilinmiyor durumunda sayı", "mass", {"status": "unknown"}),
        ("Mantıksal değer sayı sayılmaz", "mass", {"value": True}),
        ("Boşluk içeren kaynak", "mass", {"source": "   "}),
        ("Taşma üreten sayısal değer", "mass", {"value": 1e308}),
    ]:
        case = copy.deepcopy(base)
        case[field].update(update)
        response = lift_screening(case)
        check(label, response["status"] == "blocked" and response["results"] is None,
              response["issues"], "Geçersiz girdide sonuç yok")
    (OUT / "data" / "input_guard_examples.json").write_text(
        json.dumps(examples, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def aero():
    import aerosandbox as asb
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    airfoil = asb.Airfoil("naca2412")
    coordinates = np.asarray(airfoil.coordinates)
    pd.DataFrame(coordinates, columns=["x_over_c", "z_over_c"]).to_csv(
        OUT / "data" / "naca2412_coordinates.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(coordinates[:, 0], coordinates[:, 1], color="#126e82", lw=2)
    ax.set(xlabel="x/c", ylabel="z/c", title="NACA 2412 — geometry integration test")
    ax.axis("equal")
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(OUT / "plots" / "naca2412.png", dpi=160)
    plt.close(fig)
    check("NACA koordinat üretimi", np.isfinite(coordinates).all() and coordinates.shape[0] > 50,
          {"points": len(coordinates)}, "Sonlu koordinatlar, >50 nokta; yalnız geometri testi")
    foil = asb.Airfoil("naca0012")
    alpha = np.array([-4., 0., 4.])
    prediction = foil.get_aero_from_neuralfoil(alpha=alpha, Re=1e6, mach=0.05, model_size="large")
    cl = np.asarray(prediction["CL"]).reshape(-1)
    cd = np.asarray(prediction["CD"]).reshape(-1)
    confidence = np.asarray(prediction["analysis_confidence"]).reshape(-1)
    check("NeuralFoil simetrik profil kontrolü", np.isfinite(cl).all() and abs(cl[1]) < .02
          and cl[0] < 0 < cl[2] and abs(cl[0] + cl[2]) < .03,
          {"alpha_deg": alpha.tolist(), "CL": cl.tolist()}, "CL(0) mutlak<.02; işaret ve simetri hatası<.03")
    check("NeuralFoil sürükleme ve model güveni", np.isfinite(cd).all() and (cd > 0).all()
          and np.isfinite(confidence).all() and (confidence > .8).all(),
          {"CD": cd.tolist(), "model_confidence": confidence.tolist()}, "CD>0; model confidence>.8, deneysel doğrulama değildir")
    pd.DataFrame({"alpha_deg": alpha, "CL": cl, "CD": cd, "model_confidence": confidence}).to_csv(
        OUT / "data" / "neuralfoil_naca0012.csv", index=False)
    wing = asb.Wing(name="Synthetic rectangular wing", symmetric=True, xsecs=[
        asb.WingXSec(xyz_le=[0, 0, 0], chord=.25, airfoil=foil),
        asb.WingXSec(xyz_le=[0, 1., 0], chord=.25, airfoil=foil)])
    plane = asb.Airplane(name="Calibration only", wings=[wing], s_ref=.5, b_ref=2., c_ref=.25)
    rows = []
    # Thresholds selected before execution: 20% approximate theory, 4% panel change.
    for resolution in [6, 12, 24]:
        response = asb.VortexLatticeMethod(airplane=plane,
            op_point=asb.OperatingPoint(velocity=30, alpha=4),
            spanwise_resolution=resolution, chordwise_resolution=6).run()
        rows.append({"spanwise_resolution": resolution,
                     "CL": float(response["CL"]), "CDi": float(response["CD"])})
    theoretical_cl = (2 * np.pi * 8 / (8 + 2)) * np.deg2rad(4)
    relative_error = abs(rows[-1]["CL"] / theoretical_cl - 1)
    panel_change = abs(rows[-1]["CL"] / rows[-2]["CL"] - 1)
    check("VLM sonlu kanat referansı", relative_error < .2 and rows[-1]["CDi"] > 0,
          {"CL": rows[-1]["CL"], "approximate_theory_CL": float(theoretical_cl), "relative_error": relative_error},
          "Yaklaşık kaldırma çizgisi referansından sapma<%20; CDi>0, deneysel doğrulama değildir")
    check("VLM panel yakınsaması", panel_change < .04, {"rows": rows, "last_change": panel_change},
          "12->24 açıklık panelinde CL değişimi<%4")
    zero = asb.VortexLatticeMethod(airplane=plane,
        op_point=asb.OperatingPoint(velocity=30, alpha=0),
        spanwise_resolution=12, chordwise_resolution=6).run()
    check("VLM sıfır hücum açısı", abs(float(zero["CL"])) < .005,
          {"CL_at_zero": float(zero["CL"])}, "Simetrik düz kanat için |CL|<.005")
    pd.DataFrame(rows).to_csv(OUT / "data" / "vlm_panel_convergence.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([row["spanwise_resolution"] for row in rows], [row["CL"] for row in rows], "o-", label="VLM")
    ax.axhline(theoretical_cl, ls="--", color="#666", label="Approximate lifting-line reference")
    ax.set(xlabel="Spanwise resolution per half-wing", ylabel="CL", title="Synthetic wing — panel convergence")
    ax.legend()
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(OUT / "plots" / "vlm_convergence.png", dpi=160)
    plt.close(fig)
    optimization = asb.Opti()
    x = optimization.variable(init_guess=1)
    optimization.subject_to([x >= 0, x <= 2])
    optimization.minimize((x - 3) ** 2)
    solution = optimization.solve(verbose=False)
    optimum = float(solution(x))
    check("AeroSandbox/CasADi/IPOPT kısıtlı optimizasyon", abs(optimum - 2) < 1e-5,
          {"x": optimum}, "Bilinen sınır optimumu x=2; hata<1e-5")


def cad():
    import cadquery as cq
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    # CAD uses mm. This coupon is a test fixture, not a proposed aircraft part.
    dimensions_mm = [200., 20., 10.]
    body = cq.Workplane("XY").box(*dimensions_mm)
    shape = body.val()
    expected = math.prod(dimensions_mm)
    check("CAD katı ve analitik hacim", shape.isValid() and len(body.solids().vals()) == 1
          and abs(shape.Volume() / expected - 1) < 1e-9,
          {"volume_mm3": shape.Volume(), "expected_mm3": expected}, "Tek geçerli katı; hacim bağıl hata<1e-9")
    step = OUT / "cad" / "calibration_coupon.step"
    stl = OUT / "cad" / "calibration_coupon.stl"
    cq.exporters.export(body, str(step))
    cq.exporters.export(body, str(stl))
    imported = cq.importers.importStep(str(step)).val()
    bbox = imported.BoundingBox()
    lengths = [bbox.xlen, bbox.ylen, bbox.zlen]
    check("STEP dışa/içe aktarımı", imported.isValid() and abs(imported.Volume() / expected - 1) < 1e-7
          and np.allclose(lengths, dimensions_mm, atol=1e-6, rtol=0),
          {"reimported_volume_mm3": imported.Volume(), "bounding_box_mm": lengths},
          "Hacim bağıl hata<1e-7; boyut hatası<1e-6 mm")
    volume_m3 = imported.Volume() * 1e-9
    check("CAD mm3 -> SI m3 dönüşümü", abs(volume_m3 - .2 * .02 * .01) < 1e-12,
          {"volume_m3": volume_m3}, "Analitik SI hacmiyle mutlak hata<1e-12 m3")
    vertices, triangles = shape.tessellate(.1)
    points = np.array([[v.x, v.y, v.z] for v in vertices])
    faces = [points[list(face)] for face in triangles]
    fig = plt.figure(figsize=(9, 4.5))
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(faces, facecolor="#167d9a", edgecolor="#163346", alpha=.85))
    ax.set(xlim=(-110, 110), ylim=(-12, 12), zlim=(-6, 6), xlabel="x [mm]", ylabel="y [mm]", zlabel="z [mm]")
    ax.set_box_aspect((10, 1.5, 1))
    ax.set_axis_off()
    ax.set_title("STEP calibration coupon — 200 x 20 x 10 mm")
    fig.tight_layout()
    fig.savefig(OUT / "plots" / "cad_coupon.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=["numeric", "guards", "aero", "cad"])
    args = parser.parse_args()
    for folder in ["reports", "data", "plots", "cad"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    result = {"group": args.group, "synthetic_test_only": True, "python": sys.version,
              "python_executable": sys.executable, "checks": CHECKS}
    try:
        globals()[args.group]()
    except Exception:
        result["error"] = traceback.format_exc()
        check("Çalıştırma hatası", False, result["error"], "Hatasız çalışma")
    names = {"numeric": ["numpy", "scipy", "matplotlib", "pandas"],
             "guards": [], "aero": ["aerosandbox", "neuralfoil", "casadi"],
             "cad": ["cadquery", "cadquery-ocp"]}[args.group]
    result["versions"] = {}
    for name in names:
        try:
            result["versions"][name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result["versions"][name] = "not_installed"
    result["passed"] = bool(CHECKS) and all(item["passed"] for item in CHECKS)
    dest = ROOT / "work" / "tests" / "results"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{args.group}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"group": args.group, "passed": result["passed"], "checks": len(CHECKS),
                      "failures": [c["name"] for c in CHECKS if not c["passed"]]}, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
