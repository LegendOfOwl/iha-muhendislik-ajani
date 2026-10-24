from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'work/blind_validation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=BASE/'pre_analysis_seal.json'
if seal.exists():raise ValueError('Input seal already exists; do not overwrite')
contract=json.loads((BASE/'contract.json').read_text())
for name,digest in contract['geometry_sha256'].items():assert sha(BASE/'analysis_input'/name)==digest
seal.write_text(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'contract_sha256':sha(BASE/'contract.json'),'input_sha256':contract['geometry_sha256'],'reference_manifest_sha256':sha(BASE/'sources.json'),'blinding':'Separate no-history analyst receives geometry, conditions and numerical controls; expected result files retained by reviewer. Procedural shared-filesystem boundary.'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Pre-analysis contract and source inputs sealed.')
