"""Record the scope of a source-backed research task; never launch a solver."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
TASK = ROOT / 'outputs/data/tasks/20261027-221814-12f67c.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    sys.path.insert(0, str(ROOT / 'work/agent'))
    from learning import instruction_snapshot
    now = datetime.now(timezone.utc).isoformat()
    task = read(TASK)
    for name, expected in task['input_sha256'].items():
        assert sha(ROOT / name) == expected
    task.update(status='çalışıyor', phase='açık problem envanteri, birincil kaynak taraması ve önceliklendirme',
        research_date_local='2026-10-28', resumed_utc=now,
        acceptance=[
            'Every known open item has current local evidence; resolved historical failures are separated',
            'Priority and execution dependency are distinguished; missing real-project inputs are explicit',
            'Opened primary literature is linked with applicability, limitations and proposed discriminating tests',
            'No claim that literature recommendations, new native tests or physical acceptance were completed',
            'Detailed report, machine-readable issue/source register and GitHub version update'],
        applied_lesson_ids=['L04','L05','L06','L07','L08','L09','L11','R02','R03'],
        agent_instruction_snapshot=instruction_snapshot(ROOT),
        physical_qualification_passed=False, LLM_improvement_demonstrated=False,
        new_native_CFD_runs=0, new_installations=0)
    save(TASK, task)
    selected = [
        'PROJECT_STATE.md', 'outputs/data/project/mission.json', 'outputs/data/project/mass_budget.json',
        'outputs/data/project/conceptual_steps.json', 'outputs/reports/su2_kaynak_karsilastirma_20261027.json',
        'outputs/reports/reduced_family_review_20261026.json', 'outputs/reports/m6_followup_index.json',
        'outputs/reports/workflow_readiness.json', 'outputs/reports/complex_vlm_qualification.json',
        'outputs/reports/parametric_cad_qualification.json', 'outputs/reports/openaerostruct_examples.json',
        'work/setup/fusion_mcp_install.json', 'work/setup/openvsp_install.json']
    save(BASE / 'initial_evidence.json', {'captured_utc': now, 'report_date_local': '2026-10-28',
        'last_published_version': 'v0.17.0', 'source_commit': '87c932868b14407f2892e957f3e68d02a0a8b270',
        'files_sha256': {name: sha(ROOT / name) for name in selected},
        'all_real_UAV_inputs_unknown': True, 'new_solver_runs': 0,
        'scope': 'Inventory and literature review; later source inspections are separately referenced'} )
    print({'task': str(TASK.relative_to(ROOT)), 'evidence_files': len(selected), 'new_CFD_runs': 0})


if __name__ == '__main__':
    main()
