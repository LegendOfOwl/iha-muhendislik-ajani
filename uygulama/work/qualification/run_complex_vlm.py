"""Native VSPAERO on a sourced cambered profile and a kinked swept/twisted wing."""
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(os.environ.get('UAV_OUTPUT_ROOT',str(ROOT/'outputs')))
sys.path.insert(0,str(ROOT/'work/native'))
from run_external import execute,read_table,history_table,json_safe
def save(p,o): p.write_text(json.dumps(json_safe(o),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
    cfg=json.loads((OUT/'data/parametric_wing_case.json').read_text(encoding='utf-8')); stations=cfg['stations']
    if cfg.get('units')!={'length':'m','angle':'deg'} or len(stations)!=3:
        raise ValueError('This native adapter is qualified for exactly three SI/degree stations')
    values=np.array([[s[k] for k in ['y','x_le','z_le','chord','twist_deg']] for s in stations])
    if not np.isfinite(values).all() or values[0,0]!=0 or not np.all(np.diff(values[:,0])>0) or np.min(values[:,3])<=0:
        raise ValueError('Finite ordered stations and positive chords required')
    manifest=json.loads((ROOT/'work/setup/openvsp_install.json').read_text()); template=(ROOT/'work/native/native_template.vspscript').read_text()
    run=OUT/'simulations'/('complex_vlm_'+datetime.now().strftime('%Y%m%d_%H%M%S')); run.mkdir()
    records=[]
    sref=2*sum((b['y']-a['y'])*(a['chord']+b['chord'])/2 for a,b in zip(stations,stations[1:]))
    bref=2*stations[-1]['y']; cref=2*sum((b['y']-a['y'])*(a['chord']**2+a['chord']*b['chord']+b['chord']**2)/3 for a,b in zip(stations,stations[1:]))/sref
    for label,nu,nw in [('medium',17,49),('fine',33,65)]:
        folder=run/label; folder.mkdir()
        lines=[f'string wing=MakeWing("Kinked_NACA2412",0.9,0.32,0.14,0,0,false,{nu},{nw});',
            'InsertXSec(wing,1,XS_FOUR_SERIES);',
            'SetParmVal(wing,"RelativeDihedralFlag","WingGeom",0);',
            'SetParmVal(wing,"RelativeTwistFlag","WingGeom",0);',
            'SetParmVal(wing,"RotateAirfoilMatchDideralFlag","WingGeom",0);',
            'SetParmVal(wing,"TwistAllInXZPlaneFlag","WingGeom",1);',
            'string xs=GetXSecSurf(wing,0);']
        for i in range(3):
            lines += [f'ChangeXSecShape(xs,{i},XS_FILE_AIRFOIL);',f'ReadFileAirfoil(GetXSec(xs,{i}),"{(ROOT/cfg["airfoil"]).as_posix()}");']
        lines += ['Update();']
        for i,(a,b) in enumerate(zip(stations,stations[1:]),1):
            dy=b['y']-a['y']; dihedral=math.degrees(math.atan2(b['z_le']-a['z_le'],dy)); sweep=math.degrees(math.atan2(b['x_le']-a['x_le'],dy))
            lines += [f'SetDriverGroup(wing,{i},SPAN_WSECT_DRIVER,ROOTC_WSECT_DRIVER,TIPC_WSECT_DRIVER);']
            for name,value in [('Span',dy),('Root_Chord',a['chord']),('Tip_Chord',b['chord']),('Sweep_Location',0),('Sweep',sweep),('Dihedral',dihedral),('Twist',b['twist_deg']),('Twist_Location',.25),('SectTess_U',nu)]:
                lines += [f'SetParmVal(wing,"{name}","XSec_{i}",{value:.12g});']
        lines += [f'SetParmVal(wing,"Twist","XSec_0",{stations[0]["twist_deg"]});','Update();',
                  'Print("COMPUTED_SREF"); Print(GetParmVal(wing,"TotalArea","WingGeom"));',
                  'Print("COMPUTED_SPAN"); Print(GetParmVal(wing,"TotalSpan","WingGeom"));',
                  'Print("COMPUTED_PROJECTED_SPAN"); Print(GetParmVal(wing,"TotalProjectedSpan","WingGeom"));',
                  'if(GetNumTotalErrors()>0) { while(GetNumTotalErrors()>0) { ErrorObj e=PopLastError(); Print(e.GetErrorString()); } return 1; }',
                  'if(GetNumXSec(xs)!=3) { Print("GEOMETRY_SECTION_COUNT_REJECTED"); return 2; }',
                  f'if(abs(GetParmVal(wing,"TotalArea","WingGeom")-{sref:.12g})>1e-5) {{ Print("GEOMETRY_SREF_REJECTED"); return 3; }}']
        script=template.replace('@@GEOMETRY@@','\n'.join(lines)).replace('@@EXPORTS@@','ExportFile("model.step",SET_ALL,EXPORT_STEP);')
        for marker,value in [('WAKE_ITER',60),('XCG',.08),('ALPHA_START',0),('ALPHA_END',6),('ALPHA_N',3)]: script=script.replace('@@'+marker+'@@',str(value))
        for key,old,value in [('Sref',.5,sref),('bref',2.,bref),('cref',.25,cref),('MachStart',0.,.08816),('MachEnd',0.,.08816)]:
            script=script.replace(f'SetD( analysis, "{key}", {old} );',f'SetD( analysis, "{key}", {value:.12g} );')
        (folder/'case.vspscript').write_text(script)
        row={'level':label,'folder':str(folder),'reference':{'Sref_m2':sref,'bref_m':bref,'cref_m':cref,'moment_reference_m':[.08,0,0]},
             'analysis_set':'3: this wing only; no fuselage, tail, ribs or propulsion','profile':cfg['airfoil']}
        try:
            print('RUN complex native VSPAERO',label,flush=True)
            code,seconds=execute([manifest['executables']['vspscript.exe'],'-script',str(folder/'case.vspscript')],folder,'native.log',timeout=480)
            row.update(exit_code=code,seconds=seconds)
            log=(folder/'native.log').read_text(errors='replace')
            if code or 'NATIVE_ANALYSIS_COMPLETE' not in log: raise ValueError('Native analysis/configuration error')
            p=read_table(folder/'model.polar','Beta '); p.to_csv(folder/'polar.csv',index=False)
            h=history_table(folder/'model.history'); changes=[]
            for _,group in h.groupby('AoA'):
                t=group.tail(2); changes.append({'alpha':float(t.AoA.iloc[-1]),'delta_CL':abs(float(t.CLtot.iloc[-1]-t.CLtot.iloc[-2])),'delta_CDi':abs(float(t.CDi.iloc[-1]-t.CDi.iloc[-2]))})
            row.update(runtime_passed=bool(len(p)==3 and np.isfinite(p[['CLtot','CDi','CMytot']]).all().all()),polar=p.to_dict('records'),wake_changes=changes,
                       wake_converged=all(c['delta_CL']<5e-4 and c['delta_CDi']<5e-5 for c in changes))
        except Exception as e:
            row.update(runtime_passed=False,wake_converged=False,error=f'{type(e).__name__}: {e}'); print(row['error'],flush=True)
        records.append(row); save(run/'results_in_progress.json',records)
        if not row['runtime_passed']: break
    panel=None
    if len(records)==2 and all(r['runtime_passed'] for r in records):
        panel=[]
        for a,b in zip(records[0]['polar'],records[1]['polar']):
            panel.append({'alpha_deg':b['AoA'],'CL_relative_change':abs(b['CLtot']/a['CLtot']-1),'CDi_relative_change':abs(b['CDi']/a['CDi']-1)})
        shutil=__import__('shutil')
        for name in ['model.vsp3','model.step']:
            shutil.copy2(run/'fine'/name,OUT/'cad'/('complex_native_wing'+Path(name).suffix))
    passed=len(records)==2 and all(r['runtime_passed'] for r in records)
    quality=passed and all(r['wake_converged'] for r in records) and all(p['CL_relative_change']<.03 and p['CDi_relative_change']<.10 for p in panel)
    obj={'timestamp':datetime.now(timezone.utc).isoformat(),'passed':passed,'quality_passed':quality,'results':records,'panel_comparison':panel,'run_directory':str(run),
         'scope':'New cambered-profile multi-section wing native VLM qualification; no viscous/stall/aircraft acceptance',
         'operating_conditions':{'classification':'varsayım; tool qualification only','Vinf_m_s':30,'rho_kg_m3':1.225,'Mach':.08816,'ReCref':500000,'mu_implied_Pa_s':1.225*30*cref/500000},
         'limits':['CAD ruled-envelope and OpenVSP section interpolation are separate representations; full surface equivalence has not been established','Refs are explicit planform quantities; section dihedral affects projected geometry','No LLT implementation is claimed']}
    save(run/'results.json',obj); save(OUT/'reports/complex_vlm_qualification.json',obj)
    from audit_vlm import audit
    audit(obj)
    print(json.dumps({'runtime_passed':passed,'quality_passed':quality,'panel':panel},indent=2),flush=True)
    return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
