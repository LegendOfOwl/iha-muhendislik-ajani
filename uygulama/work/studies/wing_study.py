"""Reusable JSON-driven native VSPAERO + XFOIL wing comparison."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'work/native'))
from run_external import execute,read_table,history_table,json_safe
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',type=Path,default=OUT/'data/wing_study_case.json')
    parser.add_argument('--resume',type=Path)
    args=parser.parse_args()
    input_bytes=args.case.read_bytes()
    cfg=json.loads(input_bytes.decode('utf-8-sig'))
    for key in ['area_m2','velocity_m_s','density_kg_m3','dynamic_viscosity_Pa_s','speed_of_sound_m_s','comparison_CL']:
        value=cfg[key]
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<=0: raise ValueError(key+' must be positive and finite')
    if cfg['airfoil']!='NACA0012' or cfg['alpha_deg']!=[2,4,6]: raise ValueError('This validated study supports NACA0012 and [2,4,6] only; extend and verify the method before changing them.')
    if cfg['status']!='varsayım' or not cfg.get('source'): raise ValueError('Test provenance missing')
    mach=cfg['velocity_m_s']/cfg['speed_of_sound_m_s']
    if mach>=.3: raise ValueError('Study is restricted to low Mach attached-flow comparison')
    if not isinstance(cfg['aspect_ratios'],list) or not cfg['aspect_ratios']: raise ValueError('At least one aspect ratio required')
    if not 1<=cfg['XFOIL_Ncrit']<=14 or cfg['XFOIL_transition_upper_lower_xc']!=[1,1]: raise ValueError('Unsupported transition settings')
    run=args.resume.resolve() if args.resume else OUT/'simulations'/('study_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    if not run.resolve().is_relative_to(OUT/'simulations'): raise ValueError('Resume folder outside simulations')
    run.mkdir(parents=True,exist_ok=True)
    if (run/'case.json').exists():
        if json.loads((run/'case.json').read_text())!=cfg: raise ValueError('Cannot resume changed inputs')
    else: (run/'case.json').write_bytes(input_bytes)
    checks=[]; candidates=[]
    def check(name,passed,evidence,criterion):
        checks.append(dict(name=name,passed=bool(passed),evidence=json_safe(evidence),criterion=criterion))
        print(('PASS: ' if passed else 'FAIL: ')+name,flush=True)
    vsp=json.loads((ROOT/'work/setup/openvsp_install.json').read_text())
    xfoil=json.loads((ROOT/'work/setup/xfoil_install.json').read_text())
    template=(ROOT/'work/native/native_template.vspscript').read_text()
    for ar in cfg['aspect_ratios']:
        if isinstance(ar,bool) or not math.isfinite(ar) or not 4<=ar<=14: raise ValueError('Aspect ratio outside qualified range [4,14]')
        span=math.sqrt(cfg['area_m2']*ar); chord=cfg['area_m2']/span
        re=cfg['density_kg_m3']*cfg['velocity_m_s']*chord/cfg['dynamic_viscosity_Pa_s']
        folder=run/f'AR{ar}'; folder.mkdir(exist_ok=True)
        polars=[]
        for label,nu,nw,sweep in [('medium',17,49,False),('fine',33,65,True)]:
            case=folder/label; case.mkdir(exist_ok=True)
            geometry=f'string wing=MakeWing("Study_AR{ar}",{span/2:.12g},{chord:.12g},{chord:.12g},0,0,false,{nu},{nw});'
            script=template.replace('@@GEOMETRY@@',geometry).replace('@@EXPORTS@@','ExportFile("model.step",SET_ALL,EXPORT_STEP);' if sweep else '')
            for marker,value in [('WAKE_ITER',40),('XCG',chord/4),('ALPHA_START',2 if sweep else 4),('ALPHA_END',6 if sweep else 4),('ALPHA_N',3 if sweep else 1)]:
                script=script.replace('@@'+marker+'@@',str(value))
            for name,old,value in [('Sref',.5,cfg['area_m2']),('bref',2.,span),('cref',.25,chord),('Vinf',30.,cfg['velocity_m_s']),('Rho',1.225,cfg['density_kg_m3']),('MachStart',0.,mach),('MachEnd',0.,mach),('ReCref',500000.,re),('ReCrefEnd',500000.,re)]:
                needle=f'SetD( analysis, "{name}", {old} );'
                if needle not in script: raise RuntimeError('Native template changed: '+needle)
                script=script.replace(needle,f'SetD( analysis, "{name}", {value:.12g} );')
            cached=(case/'case.vspscript').exists() and (case/'case.vspscript').read_text()==script and (case/'native.log').exists() and 'NATIVE_ANALYSIS_COMPLETE' in (case/'native.log').read_text(errors='replace')
            (case/'case.vspscript').write_text(script)
            print(f'Native wing AR={ar}: {label}, Re={re:.0f}, Mach={mach:.4f}',flush=True)
            code,elapsed=(None,None) if cached else execute([vsp['executables']['vspscript.exe'],'-script',str(case/'case.vspscript')],case,'native.log',timeout=240)
            log=(case/'native.log').read_text(errors='replace')
            check(f'AR{ar} {label} native solve',(cached or code==0) and 'NATIVE_ANALYSIS_COMPLETE' in log,{'seconds':elapsed,'exit_code':code,'read_completed_case':cached},'New native exit 0 or exact completed cached case; completion marker')
            polar=read_table(case/'model.polar','Beta ')
            if not np.isfinite(polar[['AoA','CLtot','CDi','CMytot']]).all().all(): raise ValueError('Nonfinite required native coefficients')
            hist=history_table(case/'model.history')
            changes=[]
            for _,group in hist.groupby('AoA'):
                end=group.tail(2)
                changes.append([abs(float(end.CLtot.iloc[-1]-end.CLtot.iloc[-2])),abs(float(end.CDi.iloc[-1]-end.CDi.iloc[-2]))])
            check(f'AR{ar} {label} wake convergence',all(dc<5e-4 and dd<5e-5 for dc,dd in changes),changes,'Final two iteration changes CL <5e-4 and CDi <5e-5 at every angle')
            polar.to_csv(case/'polar.csv',index=False); polars.append(polar)
        middle=polars[0].iloc[0]; fine=polars[1]; point=fine.loc[np.isclose(fine.AoA,4)].iloc[0]
        change_cl=abs(float(point.CLtot/middle.CLtot-1)); change_cd=abs(float(point.CDi/middle.CDi-1))
        check(f'AR{ar} panel convergence',change_cl<.03 and change_cd<.10,{'CL_relative':change_cl,'CDi_relative':change_cd},'CL change <3%, CDi change <10%')
        k=fine.CDi/fine.CLtot**2
        variation=float(k.max()/k.min()-1)
        if not fine.CLtot.min()<cfg['comparison_CL']<fine.CLtot.max():
            raise ValueError('Requested CL outside native sweep; implicit endpoint clamping is not allowed')
        check(f'AR{ar} linear drag scaling range',variation<.08 and fine.CLtot.min()<cfg['comparison_CL']<fine.CLtot.max(),{'K_relative_range':variation,'CL_range':[float(fine.CLtot.min()),float(fine.CLtot.max())]},'CDi/CL² range <8%, comparison CL is bracketed')
        xdir=folder/'xfoil'; xdir.mkdir()
        commands=f'PLOP\nG\n\nNACA 0012\nPANE\nOPER\nVISC {re:.8f}\nMACH {mach:.8f}\nITER 200\nVPAR\nN {cfg["XFOIL_Ncrit"]}\nXTR 1 1\n\nPACC\npolar.txt\n\nASEQ -4 10 1\nPACC\n\nQUIT\n'
        (xdir/'commands.in').write_text(commands)
        code,elapsed=execute([xfoil['executable']],xdir,'xfoil.log',commands,timeout=90)
        xp=read_table(xdir/'polar.txt','alpha '); xp.to_csv(xdir/'polar.csv',index=False)
        missing=sorted(set(range(-4,11))-set(np.rint(xp.alpha).astype(int)))
        check(f'AR{ar} viscous profile polar',code==0 and np.isfinite(xp.to_numpy()).all() and (xp.CD>0).all() and len(xp)>=10,{'Re':re,'Mach':mach,'Ncrit':cfg['XFOIL_Ncrit'],'transition_xc':[1,1],'nonconverged_alpha_deg':missing},'Native XFOIL: >=10 finite converged points, positive CD; omitted angles reported')
        alpha=None; header=None; load=[]
        for line in (folder/'fine/model.lod').read_text(errors='replace').splitlines():
            fields=line.split()
            if line.startswith('AoA_'): alpha=float(fields[1])
            elif line.startswith('Iter '): header=fields
            elif header and alpha==4 and len(fields)==len(header):
                try: load.append([float(s) if 'nan' not in s.lower() else float('nan') for s in fields])
                except ValueError: pass
        ld=pd.DataFrame(load,columns=header).sort_values('Yavg')
        integrated=float((ld.Cl*ld.Chord*ld.dSpan).sum()/cfg['area_m2'])
        check(f'AR{ar} local/global lift consistency',abs(integrated/float(point.CLtot)-1)<.02,{'integrated_CL':integrated,'global_CL':float(point.CLtot)},'Span integration matches global CL within 2%')
        target_local=ld.Cl.to_numpy()*cfg['comparison_CL']/float(point.CLtot)
        attached=xp.loc[xp.alpha<=8].sort_values('CL')
        covered=target_local.min()>=attached.CL.min() and target_local.max()<=attached.CL.max()
        check(f'AR{ar} profile interpolation domain',covered,{'local_Cl_range':[float(target_local.min()),float(target_local.max())],'polar_Cl_range':[float(attached.CL.min()),float(attached.CL.max())]},'All section lift coefficients lie inside the converged attached-branch polar; no extrapolation')
        cdp=None
        if covered:
            ld['target_section_Cl']=target_local
            ld['estimated_section_Cd']=np.interp(target_local,attached.CL,attached.CD)
            cdp=float((ld.estimated_section_Cd*ld.Chord*ld.dSpan).sum()/cfg['area_m2'])
        ld.to_csv(folder/'spanload.csv',index=False)
        cdi=float(np.interp(cfg['comparison_CL'],fine.CLtot,k))*cfg['comparison_CL']**2
        result={'AR':ar,'span_m':span,'chord_m':chord,'area_m2':cfg['area_m2'],'Re':re,'Mach':mach,
                'comparison_CL':cfg['comparison_CL'],'estimated_alpha_deg':float(np.interp(cfg['comparison_CL'],fine.CLtot,fine.AoA)),
                'CDi_scaled':cdi,'CDprofile_estimated':cdp,'CDwing_estimated':cdi+cdp if cdp is not None else None,
                'nonconverged_XFOIL_alpha_deg':missing,'folder':str(folder)}
        candidates.append(result)
        shutil.copy2(folder/'fine/model.vsp3',OUT/'cad'/f'study_wing_AR{ar}.vsp3')
        shutil.copy2(folder/'fine/model.step',OUT/'cad'/f'study_wing_AR{ar}.step')
    frame=pd.DataFrame(candidates)
    frame.drop(columns=['nonconverged_XFOIL_alpha_deg','folder']).to_csv(OUT/'data/wing_comparison.csv',index=False)
    fig,ax=plt.subplots(figsize=(8,4.8)); ax.bar(frame.AR-.17,frame.CDi_scaled,width=.34,label='Induced drag, scaled to common CL')
    ax.bar(frame.AR+.17,frame.CDprofile_estimated,width=.34,label='Estimated profile drag from local 2D polar')
    ax.set(xlabel='Aspect ratio',ylabel='Drag coefficient',title=f'Isolated rectangular wings: same S, V and CL={cfg["comparison_CL"]}')
    ax.set_xticks(frame.AR); ax.legend(fontsize=8); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(OUT/'plots/wing_comparison.png',dpi=160); plt.close(fig)
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':all(a['passed'] for a in checks),
            'passed_checks':sum(a['passed'] for a in checks),'total_checks':len(checks),'checks':checks,'candidates':candidates,
            'case_sha256':hashlib.sha256(input_bytes).hexdigest(),'run_directory':str(run),
            'scope':cfg['scope'],'method':'Native VSPAERO potential flow plus XFOIL strip profile-drag estimate; approximate low-angle CL² rescaling',
            'limits':['No aircraft feasibility or optimum claim','No fuselage, interference, stall, propulsion, energy, trim or structural assessment',
                      'Section lift is rescaled using low-angle linearity; 2D to 3D viscous coupling is approximate',
                      'Panel convergence thresholds concern CL and CDi, not all possible outputs']}
    (OUT/'reports/wing_study_results.json').write_text(json.dumps(json_safe(result),indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'run':str(run)},indent=2),flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
