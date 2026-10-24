"""Compare native wing surface pressures against NASA-hosted tunnel measurements."""
from datetime import datetime,timezone
import argparse,json,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
PID=json.loads((ROOT/'work/validation/projects.json').read_text())['cfd'];OUT=ROOT/'outputs/projects'/PID;SOURCE=ROOT/'work/validation/sources'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def experimental():
    groups=[];values=[]
    for line in (SOURCE/'ONERAb114.tec').read_text().splitlines():
        if line.lstrip().startswith('ZONE'):
            if values:groups.append(np.array(values));values=[]
        else:
            try:v=[float(x) for x in line.split()]
            except ValueError:continue
            if len(v)==5:values.append(v)
    if values:groups.append(np.array(values))
    assert len(groups)==7
    checks=[]
    for i,table in enumerate(groups,1):
        for side in ['u','l']:
            a=np.loadtxt(SOURCE/f'cp{i}{side}.ex')
            index=[np.argmin(abs(table[:,1]-x)) for x in a[:,0]]
            error=float(np.max(np.abs(-a[:,1]-table[index,4])))
            if error>2e-5:raise ValueError('NASA -Cp/Cp sign or coordinate mapping differs')
            checks.append({'section':i,'side':side,'max_sign_normalization_error':error,'points':len(a)})
    return groups,checks
def surface_grid(folder):
    path=folder/'surface_flow.vtu';r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(path));r.Update();g=r.GetOutput()
    if not g.GetNumberOfPoints():raise ValueError('No native wing surface points')
    assert g.GetPointData().GetArray('Pressure_Coefficient') is not None
    return g
def comparison(row,groups,use_tec_eta=False):
    folder=Path(row['folder']);g=surface_grid(folder);points=vtk_to_numpy(g.GetPoints().GetData());cp=vtk_to_numpy(g.GetPointData().GetArray('Pressure_Coefficient'))
    yp=vtk_to_numpy(g.GetPointData().GetArray('Y_Plus'));metrics=[];tables=[];curves=[]
    for i,ex in enumerate(groups,1):
        source_eta=float(ex[0,2]);eta=source_eta if use_tec_eta else [.2,.44,.65,.8,.9,.95,.99][i-1]
        plane=vtk.vtkPlane();plane.SetOrigin(0,eta*1.1963,0);plane.SetNormal(0,1,0)
        cutter=vtk.vtkCutter();cutter.SetCutFunction(plane);cutter.SetInputData(g);cutter.Update();cut=cutter.GetOutput()
        pts=vtk_to_numpy(cut.GetPoints().GetData());vals=vtk_to_numpy(cut.GetPointData().GetArray('Pressure_Coefficient'))
        edges=vtk_to_numpy(cut.GetLines().GetConnectivityArray()).reshape(-1,2)
        leading=float(pts[:,0].min());chord=float(np.ptp(pts[:,0]));norm=np.column_stack([(pts[:,0]-leading)/chord,pts[:,2]/chord])
        a=norm[edges[:,0]];b=norm[edges[:,1]];v=b-a;length2=(v*v).sum(axis=1)
        predicted=[];distance=[]
        for exp in ex:
            target=exp[[1,3]];t=np.clip(((target-a)*v).sum(axis=1)/np.maximum(length2,1e-20),0,1)
            projection=a+t[:,None]*v;dist=np.linalg.norm(projection-target,axis=1);j=np.argmin(dist)
            predicted.append(float(vals[edges[j,0]]*(1-t[j])+vals[edges[j,1]]*t[j]));distance.append(float(dist[j]))
        predicted=np.array(predicted);delta=predicted-ex[:,4];geommax=max(distance)
        # Source upper/lower assignment is by the published .ex lists, not a Cp sign guess.
        for side in ['u','l']:
            raw=np.loadtxt(SOURCE/f'cp{i}{side}.ex');idx=np.array([np.argmin(abs(ex[:,1]-x)) for x in raw[:,0]])
            d=delta[idx];metrics.append({'section':i,'eta':eta,'eta_in_tec_file':source_eta,'side':side,'points':len(idx),'Cp_RMSE':float(np.sqrt(np.mean(d*d))),'Cp_max_abs_error':float(np.max(np.abs(d))),'fraction_within_measurement_0p02':float(np.mean(abs(d)<=.02)),'max_geometry_distance_over_chord':float(np.max(np.array(distance)[idx]))})
        for j,exp in enumerate(ex):tables.append([i,eta,exp[1],exp[3],exp[4],predicted[j],delta[j],distance[j]])
        curves.append((eta,norm,vals,ex))
    table=np.array(tables);np.savetxt(folder/('experimental_comparison_tec_eta.csv' if use_tec_eta else 'experimental_comparison.csv'),table,delimiter=',',header='section,eta,x_over_c,z_over_c,Cp_experiment,Cp_CFD,error,geometry_distance_over_chord',comments='')
    return {'grid':row['grid'],'surface_points':g.GetNumberOfPoints(),'yplus_max':float(np.max(yp)),'yplus_p95':float(np.percentile(yp,95)),'fraction_yplus_below1':float(np.mean(yp<1)),'all_point_Cp_RMSE':float(np.sqrt(np.mean(table[:,6]**2))),'fraction_within_NASA_measurement_uncertainty':float(np.mean(abs(table[:,6])<=.02)),'all_points_within_NASA_uncertainty':bool(np.all(abs(table[:,6])<=.02)),'geometry_distance_max_over_chord':float(table[:,7].max()),'sections':metrics},curves,g
def main(partial=False):
    runs=sorted((OUT/'simulations').glob('m6_rans_*'),key=lambda p:p.stat().st_mtime)
    run=runs[-1] if partial else Path(json.loads((OUT/'reports/m6_rans_results.json').read_text())['run_directory'])
    result=json.loads((run/('results_in_progress.json' if partial else 'results.json')).read_text());rows=result if partial else result['results']
    if not partial:
        current=json.loads((OUT/'reports/m6_rans_results.json').read_text())
        for key in ['previous_run_directory','continuation_run_directory','continuation_complete','continuation_diagnostic_report','continuation_note']:
            if key in current:result[key]=current[key]
    groups,signs=experimental();analyses=[];fields={};sensitivity=[]
    fig,axs=plt.subplots(2,4,figsize=(16,8));axs=axs.ravel()
    for row,color in zip(rows,['#bc842c','#087e8b']):
        if not row['runtime_passed']:continue
        metrics,curves,g=comparison(row,groups);analyses.append(metrics);fields[row['grid']]=g
        alternative,_,_=comparison(row,groups,True)
        sensitivity.append({'grid':row['grid'],'main_eta_0p95_RMSE':metrics['all_point_Cp_RMSE'],'alternative_eta_0p96_RMSE':alternative['all_point_Cp_RMSE'],'section6_alternative':[s for s in alternative['sections'] if s['section']==6]})
        for i,(eta,points,cp,exp) in enumerate(curves):
            for upper,style in [(True,'-'),(False,'--')]:
                mask=(points[:,1]>=0) if upper else (points[:,1]<0);order=np.argsort(points[mask,0]);axs[i].plot(points[mask,0][order],cp[mask][order],style,color=color,label=row['grid'] if upper else None)
            if len(analyses)==1:
                axs[i].errorbar(exp[:,1],exp[:,4],yerr=.02,fmt='none',ecolor='#192d42',alpha=.5,lw=.7)
                axs[i].scatter(exp[:,1],exp[:,4],s=20,facecolor='white',edgecolor='#192d42',label='Tunnel, NASA archive')
            axs[i].set(title=f'y/b = {eta:g}',xlabel='x/c',ylabel='Cp');axs[i].grid(alpha=.18)
    for ax in axs[:7]:ax.invert_yaxis()
    axs[0].legend(fontsize=8);axs[7].axis('off');axs[7].text(.05,.8,'ONERA M6, Test 2308\nM=0.8395; alpha=3.06 deg\nRe=11.72M; c_ref=0.64607 m\n3-D RANS / Spalart-Allmaras\nAll source experimental points retained\nError bars: NASA uncertainty +/-0.02\nSource grids differ in farfield geometry\nIterative acceptance: '+('passed' if all(r['iterative_passed'] for r in rows) else 'NOT PASSED'),va='top',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'plots'/('m6_Cp_partial.png' if partial else 'm6_Cp_comparison.png'),dpi=150);plt.close(fig)
    assessment={'timestamp':datetime.now(timezone.utc).isoformat(),'native_report':str(run/'results.json'),'experiment_source':'https://www.grc.nasa.gov/www/wind/valid/m6wing/m6wing.html','experiment':'Schmitt & Charpin 1979, Test2308; NASA-hosted data, not a NASA-conducted tunnel test','experiment_points':sum(len(g) for g in groups),'sign_checks':signs,'results':analyses,'source_eta_discrepancy':'NASA main table and Study1 Fig13 specify section6 eta=0.95; its Tecplot file encodes 0.96. Main comparison follows the table; both interpretations are retained as postprocessing sensitivity, without fitting flow conditions.','eta_sensitivity':sensitivity,'normalization':'At y=eta*NASA nominal semispan 1.1963 m; local cut leading/trailing x define x/c, z/c uses the same chord. Cp interpolated on nearest cut segment to measured (x/c,z/c); geometry mismatch recorded. No flow angle or pressure fitted to experiment.','mesh_geometry_note':'Rounded source-grid tips extend beyond NASA nominal semispan; grid families differ slightly in surface geometry and substantially in farfield domain (coarse x -6.45/+5.64 m, finer +/-59.90 m). This is source-grid sensitivity and experiment comparison, not formal grid independence.'}
    if not partial:
        assessment['all_native_iterative_passed']=all(r['iterative_passed'] for r in rows)
        assessment['strict_wall_yplus_passed']=all(r['yplus_max']<1 for r in analyses)
        assessment['experimental_RMSE_screen_passed']=len(analyses)==2 and all(s['Cp_RMSE']<.08 for s in analyses[-1]['sections'])
        assessment['grid_CL_change']=abs(rows[-1]['CL']/rows[0]['CL']-1);assessment['grid_CD_change']=abs(rows[-1]['CD']/rows[0]['CD']-1)
        assessment['grid_force_screen_passed']=assessment['grid_CL_change']<.03 and assessment['grid_CD_change']<.1
        assessment['quality_passed']=assessment['all_native_iterative_passed'] and assessment['strict_wall_yplus_passed'] and assessment['experimental_RMSE_screen_passed'] and assessment['grid_force_screen_passed']
        result.update(quality_passed=assessment['quality_passed'],experimental_comparison_status='completed; all errors retained',comparison_report=str(OUT/'reports/m6_experiment_comparison.json'));save(OUT/'reports/m6_rans_results.json',result)
        from render_m6_field import render
        assessment['field_view']=render(fields[rows[-1]['grid']],OUT,Path(rows[-1]['folder']))
    dest=OUT/'reports'/('m6_partial_comparison.json' if partial else 'm6_experiment_comparison.json');save(dest,assessment)
    print(json.dumps({k:v for k,v in assessment.items() if k not in ['results','sign_checks']},indent=2));print([(r['grid'],r['all_point_Cp_RMSE'],r['fraction_within_NASA_measurement_uncertainty'],r['yplus_max']) for r in analyses])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');args=p.parse_args();main(args.partial)
