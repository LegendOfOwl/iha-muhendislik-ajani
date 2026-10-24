"""Small, explicit lift-screening gate. This is not an aircraft design solver."""
import math

G = 9.80665
REQUIRED = {
    "mass": "kg",
    "wing_area": "m2",
    "density": "kg/m3",
    "cl_max": "1",
}
ALLOWED_STATUS = {"measured", "sourced", "requirement", "assumption"}


def lift_screening(inputs):
    if not isinstance(inputs, dict):
        return {"status": "blocked", "issues": [{"code": "INPUTS_MUST_BE_OBJECT"}],
                "results": None, "aircraft_feasibility": "not_assessed"}
    issues = []
    values = {}
    for name, unit in REQUIRED.items():
        entry = inputs.get(name)
        if not isinstance(entry, dict) or entry.get("value") is None:
            issues.append({"input": name, "code": "MISSING_VALUE"})
            continue
        value = entry["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            issues.append({"input": name, "code": "INVALID_POSITIVE_FINITE_VALUE"})
        elif entry.get("unit") != unit:
            issues.append({"input": name, "code": "WRONG_OR_MISSING_UNIT", "expected": unit})
        elif not isinstance(entry.get("status"), str) or entry["status"] not in ALLOWED_STATUS or not isinstance(entry.get("source"), str) or not entry["source"].strip():
            issues.append({"input": name, "code": "MISSING_PROVENANCE"})
        else:
            values[name] = value
    if issues:
        return {"status": "blocked", "issues": issues, "results": None,
                "aircraft_feasibility": "not_assessed"}
    try:
        speed = math.sqrt(2 * values["mass"] * G /
                          (values["density"] * values["wing_area"] * values["cl_max"]))
        if not math.isfinite(speed) or speed <= 0 or not math.isfinite(3.6 * speed):
            raise ValueError("Non-finite or zero derived speed")
    except (OverflowError, ZeroDivisionError, ValueError):
        return {"status": "blocked", "issues": [{"code": "NUMERIC_RANGE_ERROR"}],
                "results": None, "aircraft_feasibility": "not_assessed"}
    return {
        "status": "conditional_lift_screening",
        "inputs": inputs,
        "results": {"stall_speed_m_s": speed, "stall_speed_km_h": 3.6 * speed},
        "method": "1g, steady level flight: mg = 0.5*rho*V^2*S*CLmax",
        "source": "https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/",
        "limitations": ["Requires applicable whole-wing CLmax; not inferred here.",
                        "No power, drag, structure, stability or endurance assessment."],
        "aircraft_feasibility": "not_assessed",
    }
