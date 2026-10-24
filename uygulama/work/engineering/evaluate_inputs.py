"""Evaluate user-edited inputs without inventing missing values."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work"))
from engineering.conceptual import lift_screening

parser = argparse.ArgumentParser()
parser.add_argument("input", nargs="?", default=str(ROOT / "outputs/data/kavramsal_girdi_sablonu.json"))
args = parser.parse_args()
try:
    inputs = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    response = lift_screening(inputs)
except (OSError, ValueError) as error:
    response = {"status": "blocked", "issues": [{"code": "INVALID_INPUT_FILE", "detail": str(error)}],
                "results": None, "aircraft_feasibility": "not_assessed"}
target = ROOT / "outputs/reports/input_check.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(response, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
print(json.dumps(response, ensure_ascii=False, indent=2, allow_nan=False))
sys.exit(2 if response["status"] == "blocked" else 0)
