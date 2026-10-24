"""Run OpenVSP/VSPAERO and XFOIL native programs; preserve all solver files."""
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "work/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "work/cache"))
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHECKS = []


def check(name, passed, evidence, criterion):
    CHECKS.append({"name": name, "passed": bool(passed), "evidence": evidence, "criterion": criterion})
    print(f"{'PASS' if passed else 'FAIL'}: {name}", flush=True)


def read_table(path, header_start):
    header = None
    rows = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if line.strip().startswith(header_start):
            header = fields
            continue
        if header and len(fields) == len(header):
            try:
                values = []
                for item in fields:
                    # MSVC writes undefined zero-lift efficiency as -nan(ind).
                    values.append(float('nan') if 'nan' in item.lower() else float(item))
                rows.append(values)
            except ValueError:
                pass
    if not rows:
        raise RuntimeError(f"No numeric solver rows in {path}")
    return pd.DataFrame(rows, columns=header)


def json_safe(value):
    if isinstance(value, dict):
        return {key:json_safe(item) for key,item in value.items()}
    if isinstance(value, (list,tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (float,np.floating)) and not np.isfinite(value):
        return None
    return value


def history_table(path):
    # Two-word names in the native history file are explicit columns, not split tokens.
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    text = text.replace("L2 Residual", "L2_Residual").replace("Max Residual", "Max_Residual")
    replacement = path.with_suffix(".history.normalized.txt")
    replacement.write_text(text, encoding="utf-8")
    return read_table(replacement, "Iter ")


def execute(command, folder, log_name, input_text=None, timeout=360):
    begin = time.perf_counter()
    environment = dict(os.environ)
    environment.update(OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")
    with (folder / log_name).open("w", encoding="utf-8") as log:
        process = subprocess.run(command, cwd=folder, env=environment,
                                 input=input_text, text=True, stdout=log, stderr=subprocess.STDOUT,
                                 timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    return process.returncode, round(time.perf_counter() - begin, 3)


def native_case(run, label, nu, nw, assembly=False, sweep=True, export=False):
    folder = run / label
    folder.mkdir(parents=True, exist_ok=True)
    geometry = f'string wing = MakeWing("Main_wing_NACA0012", 1.0, 0.25, 0.25, {0.28 if assembly else 0.0}, 0.0, false, {nu}, {nw});'
    if assembly:
        geometry += f'''\n    string horizontal = MakeWing("Horizontal_tail", 0.275, 0.13, 0.13, 1.0, 0.0, false, {max(7, nu//2)}, {nw});
    string vertical = MakeWing("Vertical_tail", 0.2, 0.18, 0.09, 0.98, 0.0, true, {max(7, nu//2)}, {nw});
    string body = AddGeom("POD", "");
    SetGeomName(body, "Fuselage_visualization_only");
    SetParmVal(body, "Length", "Design", 1.2);
    SetParmVal(body, "FineRatio", "Design", 12.0);
    SetSetFlag(body, 3, false);'''
    exports = ''
    if export:
        exports = 'ExportFile("model.step", SET_ALL, EXPORT_STEP);\n    ExportFile("model.stl", SET_ALL, EXPORT_STL);'
    template = (ROOT / "work/native/native_template.vspscript").read_text(encoding="utf-8")
    script = template.replace("@@GEOMETRY@@", geometry).replace("@@EXPORTS@@", exports)
    script = script.replace("@@WAKE_ITER@@", "40" if assembly else "20")
    script = script.replace("@@XCG@@", "0.3425" if assembly else "0.0625")
    for marker, value in [("ALPHA_START", -4 if sweep else 4), ("ALPHA_END", 8 if sweep else 4), ("ALPHA_N", 7 if sweep else 1)]:
        script = script.replace(f"@@{marker}@@", str(value))
    script_path = folder / "case.vspscript"
    install = json.loads((ROOT / "work/setup/openvsp_install.json").read_text())
    cached = script_path.exists() and script_path.read_text(encoding='utf-8') == script and (folder/'native.log').exists() and 'NATIVE_ANALYSIS_COMPLETE' in (folder/'native.log').read_text(encoding='utf-8',errors='replace')
    if script_path.exists() and not cached:
        raise RuntimeError(f'Existing case is incomplete or changed. Start a new run: {folder}')
    if cached:
        print(f"Reading completed native run: {label}",flush=True)
        code, elapsed = None, None
    else:
        script_path.write_text(script, encoding="utf-8")
        print(f"Native VSPAERO: {label}", flush=True)
        code, elapsed = execute([install["executables"]["vspscript.exe"], "-script", str(script_path)], folder, "native.log")
    log = (folder / "native.log").read_text(encoding="utf-8", errors="replace")
    completed = (cached or code == 0) and "NATIVE_ANALYSIS_COMPLETE" in log and (folder / "model.polar").exists()
    check(f"VSPAERO {label}: gerçek çözücü çalışması", completed,
          {"exit_code": code, "seconds": elapsed, "read_completed_case":cached,"log": str(folder / "native.log")}, "Yeni çalıştırmada çıkış 0; tümünde API hatası yok, polar ve tamamlanma işareti var")
    if not completed:
        raise RuntimeError(f"Native analysis failed: {folder / 'native.log'}\n{log[-2000:]}")
    polar = read_table(folder / "model.polar", "Beta ")
    check(f"VSPAERO {label}: gerekli katsayılar", len(polar)==(7 if sweep else 1) and np.isfinite(polar[['AoA','CLtot','CDi','CMytot']].to_numpy()).all(),
          {'rows':len(polar)},'İstenen tüm açılar ve sonlu CL, CDi, Cm. Sıfır kaldırmada tanımsız verim null olarak saklanır.')
    polar.to_csv(folder / "polar.csv", index=False)
    history = history_table(folder / "model.history")
    changes = []
    for alpha, group in history.groupby("AoA"):
        if len(group) >= 2:
            last = group.iloc[-1]
            previous = group.iloc[-2]
            changes.append({"alpha_deg": float(alpha), "CL_change": abs(float(last.CLtot - previous.CLtot)),
                            "CDi_change": abs(float(last.CDi - previous.CDi)),
                            "L2_Residual_native": float(last.L2_Residual),
                            "Max_Residual_native": float(last.Max_Residual)})
    force_ok = bool(changes) and max(item["CL_change"] for item in changes) < 5e-4 and max(item["CDi_change"] for item in changes) < 5e-5
    check(f"VSPAERO {label}: son iterasyon kuvvet değişimi", force_ok, changes,
          "Son iki iterasyonda |delta CL|<5e-4 ve |delta CDi|<5e-5; ağ yakınsaması ayrıca incelenir")
    return {"label": label, "folder": str(folder), "nu": nu, "nw": nw, "elapsed_seconds": elapsed,
            "polar": json_safe(polar.to_dict("records")), "history_last_changes": json_safe(changes)}


def xfoil_case(run, airfoil):
    folder = run / f"xfoil_naca{airfoil}"
    folder.mkdir(exist_ok=True)
    commands = f"PLOP\nG\n\nNACA {airfoil}\nPANE\nOPER\nVISC 500000\nMACH 0\nITER 200\nVPAR\nN 9\n\nPACC\npolar.txt\n\nASEQ -4 8 2\nPACC\n\nQUIT\n"
    install = json.loads((ROOT / "work/setup/xfoil_install.json").read_text())
    cached = (folder/'commands.in').exists() and (folder/'commands.in').read_text()==commands and (folder/'polar.txt').exists() and (folder/'xfoil.log').exists()
    if cached:
        print(f'Reading completed XFOIL polar: NACA {airfoil}',flush=True)
        code,elapsed=None,None
    else:
        (folder / "commands.in").write_text(commands, encoding="ascii")
        print(f"Native XFOIL: NACA {airfoil}", flush=True)
        code, elapsed = execute([install["executable"]], folder, "xfoil.log", commands, timeout=90)
    polar = read_table(folder / "polar.txt", "alpha ")
    polar.to_csv(folder / "polar.csv", index=False)
    expected = np.arange(-4, 10, 2)
    complete = (cached or code == 0) and len(polar) == len(expected) and np.allclose(polar.alpha, expected)
    check(f"XFOIL NACA {airfoil}: viskoz açı taraması", complete and (polar.CD > 0).all()
          and np.isfinite(polar.to_numpy()).all(),
          {"exit_code": code, "rows": len(polar), "seconds": elapsed,"read_completed_case":cached}, "Re=500000, Mach=0, Ncrit=9; -4..8 derece 7 yakınsamış nokta; sonlu değerler ve CD>0")
    return {"airfoil": airfoil, "folder": str(folder), "elapsed_seconds": elapsed, "polar": polar.to_dict("records")}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume',type=Path)
    args=parser.parse_args()
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    run = args.resume.resolve() if args.resume else OUT / "simulations" / ("external_" + now.strftime("%Y%m%d_%H%M%S"))
    if not run.resolve().is_relative_to((OUT/'simulations').resolve()):
        raise RuntimeError('Resume path must stay within outputs/simulations')
    run.mkdir(parents=True,exist_ok=True)
    conditions = {
        "status": "synthetic_integration_demonstrator_not_aircraft_recommendation",
        "units": "m, kg, s; OpenVSP STEP export explicitly metres; CAD imports millimetres",
        "reference_wing": {"span_m": 2., "chord_m": .25, "area_m2": .5, "airfoil": "NACA0012", "aspect_ratio": 8.},
        "assembly": {"fuselage_length_m": 1.2, "fuselage_fineness": 12., "wing_le_x_m": .28,
                     "horizontal_tail_span_m": .55, "horizontal_tail_chord_m": .13, "horizontal_tail_le_x_m": 1.,
                     "vertical_tail_height_m": .2, "vertical_tail_root_m": .18, "vertical_tail_tip_m": .09,
                     "vertical_tail_le_x_m": .98, "moment_reference_x_m": .3425},
        "flow": {"velocity_m_s": 30., "density_kg_m3": 1.225, "Re_ref": 500000., "Mach_requested": 0.,
                 "alpha_deg": [-4,-2,0,2,4,6,8], "XFOIL_Ncrit": 9},
        "analysis_scope": "3D thin lifting surfaces. Fuselage is drawn/exported but excluded from aerodynamic set. Native VSPAERO CD0 estimate is not a validated total aircraft drag.",
        "real_project_requirements": "not inferred from previous chats or these test parameters",
    }
    (run / "conditions.json").write_text(json.dumps(conditions, indent=2), encoding="utf-8")
    cases = []
    for label, nu, nw in [("wing_coarse", 9, 33), ("wing_medium", 17, 49), ("wing_fine", 33, 65)]:
        cases.append(native_case(run, label, nu, nw, sweep=label == "wing_fine", export=label == "wing_fine"))
    fine = pd.DataFrame(cases[-1]["polar"])
    rows = []
    for case in cases:
        frame = pd.DataFrame(case["polar"])
        row = frame.loc[np.isclose(frame.AoA, 4)].iloc[0]
        rows.append({"case": case["label"], "spanwise_setting": case["nu"], "chordwise_setting": case["nw"],
                     "CLtot": float(row.CLtot), "CDi": float(row.CDi)})
    delta_cl = abs(rows[-1]["CLtot"] / rows[-2]["CLtot"] - 1)
    delta_cdi = abs(rows[-1]["CDi"] / rows[-2]["CDi"] - 1)
    check("VSPAERO bağımsız ağ inceltme", delta_cl < .03 and delta_cdi < .10,
          {"rows": rows, "relative_CL_change": delta_cl, "relative_CDi_change": delta_cdi}, "Orta->ince ağda CL değişimi<%3; indüklenmiş sürükleme değişimi<%10")
    pd.DataFrame(rows).to_csv(OUT / "data" / "native_mesh_convergence.csv", index=False)
    import aerosandbox as asb
    foil = asb.Airfoil("naca0012")
    wing = asb.Wing(symmetric=True, xsecs=[asb.WingXSec(xyz_le=[0,0,0], chord=.25, airfoil=foil),
                                         asb.WingXSec(xyz_le=[0,1,0], chord=.25, airfoil=foil)])
    plane = asb.Airplane(wings=[wing], s_ref=.5, b_ref=2., c_ref=.25)
    response = asb.VortexLatticeMethod(airplane=plane, op_point=asb.OperatingPoint(velocity=30, alpha=4),
                                     spanwise_resolution=32, chordwise_resolution=12).run()
    independent_cl = float(response["CL"])
    difference = abs(rows[-1]["CLtot"] / independent_cl - 1)
    check("VSPAERO / AeroSandbox ayrı çözücü karşılaştırması", difference < .10,
          {"VSPAERO_CL": rows[-1]["CLtot"], "AeroSandbox_CL": independent_cl, "relative_difference": difference},
          "Aynı AR=8 kanat, alfa=4 derece, incompressible model: CL farkı<%10; deneysel doğrulama değildir")
    zero = fine.loc[np.isclose(fine.AoA, 0)].iloc[0]
    pos = fine.loc[np.isclose(fine.AoA, 4)].iloc[0]
    neg = fine.loc[np.isclose(fine.AoA, -4)].iloc[0]
    check("VSPAERO simetrik kanat fiziksel kontrolü", abs(zero.CLtot) < .005 and pos.CLtot > 0 and neg.CLtot < 0
          and abs(pos.CLtot + neg.CLtot) < .01, {"CL_zero": zero.CLtot, "CL_plus4": pos.CLtot, "CL_minus4": neg.CLtot},
          "Sıfır açıda |CL|<.005; +/-4 derecede zıt işaret ve simetri hatası<.01")
    cases.append(native_case(run, "aircraft_lifting_surfaces_refined_wake", 25, 49, assembly=True, sweep=True, export=True))
    xfoil = [xfoil_case(run, name) for name in ["0012", "2412"]]
    profile = pd.DataFrame(xfoil[0]["polar"])
    check("XFOIL simetrik profil kontrolü", abs(float(profile.loc[np.isclose(profile.alpha,0),"CL"].iloc[0])) < .01
          and abs(float(profile.loc[np.isclose(profile.alpha,4),"CL"].iloc[0] + profile.loc[np.isclose(profile.alpha,-4),"CL"].iloc[0])) < .01,
          {"CL_at_zero": float(profile.loc[np.isclose(profile.alpha,0),"CL"].iloc[0])}, "NACA0012 sıfır açı ve +/-4 derece simetrisi")
    assembly = pd.DataFrame(cases[-1]["polar"])
    model_folder = Path(cases[-1]["folder"])
    for suffix in ["vsp3", "step", "stl"]:
        shutil.copyfile(model_folder / f"model.{suffix}", OUT / "cad" / f"aircraft_demo.{suffix}")
    for suffix in ["vsp3", "step", "stl"]:
        shutil.copyfile(Path(cases[2]["folder"]) / f"model.{suffix}", OUT / "cad" / f"reference_wing.{suffix}")
    fine.to_csv(OUT / "data/native_wing_polar.csv", index=False)
    assembly.to_csv(OUT / "data/native_aircraft_lifting_surface_polar.csv", index=False)
    for item in xfoil:
        pd.DataFrame(item["polar"]).to_csv(OUT / f"data/xfoil_naca{item['airfoil']}_polar.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(14,4))
    axes[0].plot(fine.AoA, fine.CLtot, 'o-', label='VSPAERO: isolated wing')
    axes[0].plot(assembly.AoA, assembly.CLtot, 's-', label='VSPAERO: wing + tails')
    axes[0].set(xlabel='Angle of attack [deg]', ylabel='CL', title='Native 3D lifting-surface analyses')
    axes[0].legend(fontsize=8)
    axes[1].plot(fine.CDi, fine.CLtot,'o-')
    axes[1].set(xlabel='Induced drag coefficient CDi', ylabel='CL', title='Wing induced-drag polar')
    for item in xfoil:
        frame=pd.DataFrame(item['polar'])
        axes[2].plot(frame.alpha,frame.CL,'o-',label='NACA '+item['airfoil'])
    axes[2].set(xlabel='Angle of attack [deg]',ylabel='2D CL',title='Native XFOIL: Re=500,000; Ncrit=9')
    axes[2].legend(fontsize=8)
    for ax in axes: ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(OUT/'plots/native_aerodynamics.png',dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7,4))
    ax.plot([r['spanwise_setting'] for r in rows],[r['CLtot'] for r in rows],'o-')
    ax.set(xlabel='Spanwise tessellation setting (chord grid also refined)',ylabel='CL at 4 deg',title='VSPAERO independent mesh refinement')
    ax.grid(alpha=.25);fig.tight_layout();fig.savefig(OUT/'plots/native_mesh_convergence.png',dpi=160);plt.close(fig)
    summary = {"timestamp": now.isoformat(), "run_directory": str(run), "conditions": conditions,
               "native_cases": cases, "xfoil_cases": xfoil, "checks": CHECKS,
               "passed": all(c["passed"] for c in CHECKS),
               "cross_solver_CL_relative_difference": difference,
               "mesh_relative_CL_change": delta_cl, "mesh_relative_CDi_change": delta_cdi,
               "experimental_validation": False, "actual_aircraft_feasibility": "not_assessed"}
    summary=json_safe(summary)
    (OUT/'reports/external_solver_results.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    (run/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print('EXTERNAL SOLVERS FINISHED:',len(CHECKS),'checks; passed=',summary['passed'],flush=True)
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
