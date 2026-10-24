"""Prepare an explicitly synthetic, sourced profile project; never seed the actual UAV."""
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/agent'))
import projects
projects.bootstrap();record=ROOT/'work/setup/profile_project.json'
if record.exists():p=projects.get(json.loads(record.read_text())['project_id'])
else:
    p=projects.create('Profil ağı ve CFD doğrulaması','qualification');projects.write(record,{'project_id':p['id']})
dest=projects.resolve(p['artifact_root']);source=ROOT/'outputs/data/airfoils/naca2412.dat';shutil.copy2(source,dest/'data/naca2412.dat')
case={'mode':'euler2d','units':{'length':'m','angle':'deg'},'airfoil':str((dest/'data/naca2412.dat').relative_to(ROOT)),
    'Mach':.15,'alpha_deg':2.0,'classification':{'airfoil':'kaynaklı; UIUC NACA2412','operating_conditions':'varsayım; synthetic qualification'},
    'source_url':'https://m-selig.ae.illinois.edu/ads/coord/naca2412.dat'}
projects.write(dest/'data/profile_cfd_case.json',case);print(p['id'])
