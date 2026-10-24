"""Independent post-freeze experimental comparison; never supplies target values to analyst."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,math,csv
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'work/blind_validation'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def reference(name):
    lines=(BASE/'reviewer_only'/name).read_text().splitlines();data=[]
    for line in lines:
        try:a=[float(v) for v in line.split()]
        except ValueError:continue
        if len(a)==2:data.append(a)
    a=np.array(data);assert a.shape[1]==2 and np.isfinite(a).all()
    ile=int(np.argmin(a[:,0]));assert 0<ile<len(a)-1
    # Published CFPOST script applies Cp scale -1; retain every source sample.
    a[:,1]*=-1
    return a,np.arange(len(a))<=ile

def surface(path):
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(path));r.Update();g=r.GetOutput()
    xy=vtk_to_numpy(g.GetPoints().GetData())[:,:2];pd=g.GetPointData()
    names=[pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
    cp=vtk_to_numpy(pd.GetArray('Pressure_Coefficient'));assert np.isfinite(cp).all()
    adjacency={}
    for i in range(g.GetNumberOfCells()):
        ids=g.GetCell(i).GetPointIds()
        if ids.GetNumberOfIds()!=2:raise ValueError('Expected 2D wall line elements')
        a,b=ids.GetId(0),ids.GetId(1)
        adjacency.setdefault(a,[]).append(b);adjacency.setdefault(b,[]).append(a)
    assert all(len(v)==2 for v in adjacency.values())
    first=min(adjacency);order=[first];previous=None;now=first
    while True:
        nxt=next(v for v in adjacency[now] if v!=previous)
        if nxt==first:break
        if nxt in order:raise ValueError('Wall contains multiple/non-simple loops')
        order.append(nxt);previous,now=now,nxt
    assert len(order)==len(adjacency)
    q=xy[order];signed=.5*np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))
    if signed<0:order=order[::-1];q=xy[order]
    ile=int(np.argmin(q[:,0]));ite=int(np.argmax(q[:,0]));n=len(order)
    def chain(step):
        ids=[];j=ile
        while True:
            ids.append(order[j])
            if j==ite:break
            j=(j+step)%n
        ids=np.array(ids);sort=np.argsort(xy[ids,0]);return ids[sort]
    a,b=chain(1),chain(-1)
    upper,lower=(a,b) if xy[a,1].mean()>xy[b,1].mean() else (b,a)
    branches={side:np.column_stack([xy[ids],cp[ids]]) for side,ids in [('upper',upper),('lower',lower)]}
    closed=np.array(order+[order[0]]);d=np.diff(xy[closed],axis=0);avg=(cp[closed[:-1]]+cp[closed[1:]])/2
    pressure_force=np.array([-np.sum(avg*d[:,1]),np.sum(avg*d[:,0])])
    wall_yplus=vtk_to_numpy(pd.GetArray('Y_Plus')) if 'Y_Plus' in names else None
    return branches,{'points':len(order),'array_names':names,'signed_enclosed_area_m2':float(abs(signed)),'pressure_CFx_independent':float(pressure_force[0]),'pressure_CFy_independent':float(pressure_force[1]),'max_wall_yplus':float(np.max(wall_yplus)) if wall_yplus is not None else None,'classification':'Closed wall topology split at LE and TE; branch mean ordinate identifies upper/lower. No y>=0 classification.'}

def metrics(pred,truth):
    err=np.array(pred)-np.array(truth)
    return {'points':len(err),'RMSE':float(np.sqrt(np.mean(err**2))),'mean_bias':float(err.mean()),'p95_abs_error':float(np.percentile(abs(err),95)),'max_abs_error':float(abs(err).max()),'fraction_within_source_uncertainty_0p0026':float(np.mean(abs(err)<=.0026))}

def farfield_mass_diagnostic(folder):
    """Independent nodal trapezoid estimate, not the solver's exact discrete flux."""
    from scipy.spatial import cKDTree
    lines=(folder/'mesh.su2').read_text().splitlines();i=next(i for i,s in enumerate(lines) if s.startswith('NPOIN'))
    n=int(lines[i].split('=')[1].split()[0]);xy=np.array([[float(v) for v in s.split()[:2]] for s in lines[i+1:i+1+n]])
    i=next(i for i,s in enumerate(lines) if 'MARKER_TAG' in s and 'FARFIELD' in s);count=int(lines[i+1].split('=')[1]);edges=np.array([[int(v) for v in s.split()[1:3]] for s in lines[i+2:i+2+count]])
    r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(folder/'flow.vtu'));r.Update();g=r.GetOutput();positions=vtk_to_numpy(g.GetPoints().GetData())[:,:2]
    rho=vtk_to_numpy(g.GetPointData().GetArray('Density'));velocity=vtk_to_numpy(g.GetPointData().GetArray('Velocity'))[:,:2]
    distance,ids=cKDTree(positions).query(xy[np.unique(edges)])
    if distance.max()>1e-5:raise ValueError('Volume/farfield mesh readback mismatch')
    mapping=dict(zip(np.unique(edges),ids));index=np.array([[mapping[a],mapping[b]] for a,b in edges]);p=xy[edges];delta=p[:,1]-p[:,0]
    normal=np.c_[delta[:,1],-delta[:,0]];center=(xy.min(0)+xy.max(0))/2
    flip=np.sum(normal*(p.mean(1)-center),axis=1)<0;normal[flip]*=-1
    momentum=(rho[:,None]*velocity)[index].mean(1);flux=np.sum(momentum*normal,axis=1)
    return {'normalized_net_mass_imbalance':float(abs(flux.sum())/(.5*np.abs(flux).sum())),'net_mass_flux_in_output_units':float(flux.sum()),'max_coordinate_match_error_m':float(distance.max()),'method':'Nodal rho*u trapezoid on square outer boundary, positive outward normal. A diagnostic with quadrature error, not the native Riemann flux or a new acceptance threshold.'}

def shock(x,cp):
    # Generic interior recovery locator, fixed before prediction review; not tuned to a target location.
    sort=np.argsort(x);x=np.array(x)[sort];cp=np.array(cp)[sort]
    mid=(x[:-1]+x[1:])/2;gradient=np.diff(cp)/np.maximum(np.diff(x),1e-15)
    mask=(mid>=.15)&(mid<=.9);ids=np.flatnonzero(mask);i=ids[np.argmax(gradient[mask])]
    return {'location_x_over_c':float(mid[i]),'bracket_x_over_c':[float(x[i]),float(x[i+1])],'Cp_recovery_gradient':float(gradient[i]),'method':'max positive upper-surface secant dCp/dx, interior 0.15..0.9; bracket/tap spacing retained'}

def evaluate_one(path):
    ref,upper=reference('cp.exp.gen');assert len(ref)==103
    assert 'Cp scale -1' in (BASE/'reviewer_only/cfpost.cp.com').read_text()
    branches,geometry=surface(path);prediction=np.empty(len(ref));source_side=np.where(upper,'upper','lower')
    for side in ['upper','lower']:
        mask=source_side==side;b=branches[side]
        if ref[mask,0].min()<b[:,0].min()-1e-7 or ref[mask,0].max()>b[:,0].max()+1e-7:raise ValueError('Reference would require unreported extrapolation')
        prediction[mask]=np.interp(ref[mask,0],b[:,0],b[:,2])
    result={'all':metrics(prediction,ref[:,1]),'upper':metrics(prediction[upper],ref[upper,1]),'lower':metrics(prediction[~upper],ref[~upper,1]),'wall':geometry,'source_pressure_uncertainty':.0026,'source_pressure_uncertainty_scope':'Reported pressure measurement error, not total CFD modeling uncertainty or universal pass criterion','regions':{}}
    for name,mask in [('LE',ref[:,0]<=.05),('mid', (ref[:,0]>.05)&(ref[:,0]<.9)),('TE',ref[:,0]>=.9)]:result['regions'][name]=metrics(prediction[mask],ref[mask,1])
    b=branches['upper'];result['predicted_shock']=shock(b[:,0],b[:,2]);result['experimental_shock']=shock(ref[upper,0],ref[upper,1])
    result['shock_location_abs_error_chords']=abs(result['predicted_shock']['location_x_over_c']-result['experimental_shock']['location_x_over_c'])
    contract=read(BASE/'contract.json')['experimental_Cp'];result['checks']={'all_RMSE':result['all']['RMSE']<=contract['pointwise_RMSE_max'],'upper_RMSE':result['upper']['RMSE']<=contract['per_side_RMSE_max'],'lower_RMSE':result['lower']['RMSE']<=contract['per_side_RMSE_max'],'p95_error':result['all']['p95_abs_error']<=contract['p95_absolute_error_max'],'max_error':result['all']['max_abs_error']<=contract['max_absolute_error_max'],'shock_location':result['shock_location_abs_error_chords']<=contract['shock_location_abs_error_chords_max']}
    result['experimental_passed']=all(result['checks'].values())
    result['negative_control_wrong_Cp_sign_RMSE']=metrics(-prediction,ref[:,1])['RMSE']
    assert result['negative_control_wrong_Cp_sign_RMSE']>contract['pointwise_RMSE_max']
    return result,ref,source_side,prediction,branches

def main():
    info=read(BASE/'project.json');out=ROOT/info['output_root'];frozen=out/'reports/prediction_frozen.json'
    if not frozen.exists():raise ValueError('Prediction not frozen: reviewer comparison is forbidden')
    seal=read(BASE/'pre_analysis_seal.json');assert sha(BASE/'contract.json')==seal['contract_sha256']
    for name,h in seal['input_sha256'].items():assert sha(BASE/'analysis_input'/name)==h
    snapshot=read(frozen)
    (out/'data/review').mkdir(exist_ok=True)
    # Paths selected by analyst before reviewer unblinding, not by best experimental fit.
    manifest=read(BASE/'reviewer/review_manifest.json')
    cases=[];fig,axs=plt.subplots(2,2,figsize=(13,9));colors=['#b68b38','#4a8393','#b45e62','#735893']
    for i,case in enumerate(manifest['cases']):
        folder=ROOT/case['folder'];path=ROOT/case['surface_file'];assert sha(path)==case['surface_sha256']
        result,ref,sides,pred,b=evaluate_one(path);result.update(label=case['label'],surface_file=str(path.relative_to(ROOT)),surface_sha256=sha(path));cases.append(result)
        result['mass_balance_diagnostic']=farfield_mass_diagnostic(folder)
        for side,ls in [('upper','-'),('lower','--')]:axs[0,0].plot(b[side][:,0],b[side][:,2],ls,color=colors[i%4],lw=1,label=case['label'] if side=='upper' else None)
        axs[0,1].plot(ref[:,0],pred-ref[:,1],'.',color=colors[i%4],ms=3,label=case['label'])
        np.savetxt(out/'data/review'/f'{i:02d}_experimental_Cp.csv',np.column_stack([ref[:,0],(sides=='upper').astype(int),ref[:,1],pred,pred-ref[:,1]]),delimiter=',',header='x_over_c,is_upper,Cp_experiment,Cp_prediction,error',comments='')
    ref,upper=reference('cp.exp.gen');axs[0,0].errorbar(ref[:,0],ref[:,1],yerr=.0026,fmt='o',ms=3,markerfacecolor='white',color='#223a4e',lw=.5,label='Cook tunnel, NASA archive');axs[0,0].invert_yaxis();axs[0,0].set(xlabel='x/c',ylabel='Cp',title='All 103 experimental points retained');axs[0,0].legend(fontsize=7)
    axs[0,1].axhspan(-.0026,.0026,color='#b9cdc4',alpha=.5);axs[0,1].set(xlabel='x/c',ylabel='Cp prediction - experiment',title='Error by location, including LE/shock/TE');axs[0,1].legend(fontsize=7)
    axs[1,0].bar([c['label'] for c in cases],[c['all']['RMSE'] for c in cases],color=colors[:len(cases)]);axs[1,0].axhline(.03,color='#aa3e43',ls='--',label='Predeclared minimum screen');axs[1,0].set(ylabel='Cp RMSE');axs[1,0].legend(fontsize=8)
    axs[1,1].axis('off');axs[1,1].text(0,1,'RAE2822 Case6, corrected source conditions\nM=.729, alpha=2.31 deg, Re=6.5M\nT=255.556 K (source computational assumption)\nNo angle/pressure fitting to expected results\nNo use of experimental shock for mesh selection\n\nNumerical screens and experiment screens\nare assessed separately. A passed process\nis not a passed physical validation.',va='top')
    for ax in axs.ravel()[:3]:ax.grid(alpha=.18)
    fig.tight_layout();fig.savefig(out/'plots/review_Cp_comparison.png',dpi=160);plt.close(fig)
    summary={'timestamp':datetime.now(timezone.utc).isoformat(),'prediction_frozen_sha256':sha(frozen),'contract_sha256':seal['contract_sha256'],'source_files_unchanged':True,'all_experimental_points':103,'case_results':cases,'note':'Numerical acceptance must be independently audited and combined; this file alone does not assert minimum overall qualification','experimental_forces_available':False,'WIND_force_file_is':'Numerical cross-code diagnostic, not tunnel CL/CD','blinding':'Procedural separate history/files; not security or memorization isolation'}
    save(out/'reports/review_experiment_comparison.json',summary)
    print(json.dumps({c['label']:{'Cp_RMSE':c['all']['RMSE'],'experimental_passed':c['experimental_passed'],'checks':c['checks']} for c in cases},indent=2))
if __name__=='__main__':main()
