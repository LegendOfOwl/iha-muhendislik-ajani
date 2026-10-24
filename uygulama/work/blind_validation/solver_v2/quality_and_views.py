from pathlib import Path
import numpy as np,json,os,sys
from audit_mesh_family import parse_mesh,OUT
os.environ['MPLCONFIGDIR']=str(Path(__file__).parent/'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
def inspect(name):
    folder=OUT/'simulations'/name;p,c,marks=parse_mesh(folder/'mesh.su2');records=[]
    for nv in [3,4]:
        ids=np.array([i for i,co in enumerate(c) if len(co)==nv]);co=np.array([c[i] for i in ids]);v=p[np.roll(co,-1,axis=1)]-p[co];prev=np.roll(v,1,axis=1)
        angles=np.rad2deg(np.arccos(np.clip(np.sum(-prev*v,axis=2)/(np.linalg.norm(prev,axis=2)*np.linalg.norm(v,axis=2)),-1,1)));ideal=60. if nv==3 else 90.
        skew=np.maximum(np.max((angles-ideal)/(180-ideal),1),np.max((ideal-angles)/ideal,1))
        center=p[co].mean(1);mid=(p[co]+p[np.roll(co,-1,axis=1)])/2;delta=mid-center[:,None,:];normal=np.stack([v[:,:,1],-v[:,:,0]],axis=2)
        nonorth=np.max(np.rad2deg(np.arccos(np.clip(np.abs(np.sum(delta*normal,2))/(np.linalg.norm(delta,axis=2)*np.linalg.norm(normal,axis=2)),0,1))),1)
        for i,sk,no,cen in zip(ids,skew,nonorth,center):records.append((int(i),float(sk),float(no),cen))
    records.sort(key=lambda a:a[1],reverse=True);allsk=np.array([r[1] for r in records]);allno=np.array([r[2] for r in records]);report={'run':name,'equiangle_skewness':{'max':float(allsk.max()),'p99':float(np.quantile(allsk,.99)),'p95':float(np.quantile(allsk,.95))},'center_face_nonorthogonality_degrees':{'max':float(allno.max()),'p99':float(np.quantile(allno,.99)),'p95':float(np.quantile(allno,.95))},'worst10_by_skew':[{'cell_id':r[0],'skewness':r[1],'nonorthogonality_deg':r[2],'center_m':r[3].tolist(),'vertices_m':p[c[r[0]]].tolist()} for r in records[:10]],'interpretation':'Reported geometric quality measures have no newly invented pass cutoff; long thin boundary-layer cells are not rejected solely by aspect ratio. Positive signed areas/Jacobians and connectivity are separate audits.'}
    (folder/'mesh_quality_locations.json').write_text(json.dumps(report,indent=2))
    centers=np.array([p[co].mean(0) for co in c]);fig,axs=plt.subplots(2,3,figsize=(16,8));R=float(np.max(abs(p)))
    views=[('whole domain',(-R,R,-R,R)),('near body',(-.1,1.3,-.25,.3)),('LE',(-.025,.055,-.045,.045)),('normal-layer transition',(.37,.44,.05,.09)),('TE',(.9,1.06,-.025,.04)),('wake',(.9,3,-.13,.22))]
    for ax,(label,lims) in zip(axs.ravel(),views):
        mask=(centers[:,0]>lims[0]-.05)&(centers[:,0]<lims[1]+.05)&(centers[:,1]>lims[2]-.05)&(centers[:,1]<lims[3]+.05)
        ax.add_collection(PolyCollection([p[co] for co,m in zip(c,mask) if m],facecolors='none',edgecolors='#24495e',linewidths=.25));ax.set(xlim=lims[:2],ylim=lims[2:],aspect='equal',title=label)
        for e in marks['AIRFOIL']:ax.plot(p[e,0],p[e,1],color='#bb2525',lw=.5)
    fig.suptitle(f'{name}: actual selected solver mesh, {len(c):,} cells');fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_v2_actual_mesh_{name}.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6));mask=(centers[:,0]>-.03)&(centers[:,0]<.05)&(abs(centers[:,1])<.05);sk_by_id=np.zeros(len(c))
    for r in records:sk_by_id[r[0]]=r[1]
    coll=PolyCollection([p[co] for co,m in zip(c,mask) if m],array=sk_by_id[mask],cmap='viridis',edgecolors='gray',linewidths=.12);ax.add_collection(coll);ax.set(xlim=(-.025,.04),ylim=(-.04,.04),aspect='equal',title=name+' LE cell skewness');fig.colorbar(coll,ax=ax);fig.tight_layout();fig.savefig(OUT/'plots'/f'prediction_v2_LE_quality_{name}.png',dpi=160);plt.close(fig)
    print(name,report['equiangle_skewness'],report['worst10_by_skew'][0]['center_m']);return report
if __name__=='__main__':
    for n in ['v2_r2_coarse','v2_r2_medium','v2_r2_fine','v2_r2_medium_far']:inspect(n)
