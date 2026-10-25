from prepare import ROOT,BASE,CASE,read,save
from run import history
from nested_control import mesh
import os
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    ni,nj=read(CASE/'contract.json')['levels']['fine']['dimensions'];g=mesh('fine').reshape(nj,ni,2)
    fig,axes=plt.subplots(2,2,figsize=(13,8))
    for ax in axes.flat[:2]:
        for row in g:ax.plot(row[:,0],row[:,1],color='#538998',lw=.4)
        for col in g.transpose(1,0,2):ax.plot(col[:,0],col[:,1],color='#538998',lw=.4)
        ax.set(xlabel='x [m]',ylabel='y [m]');ax.grid(alpha=.1)
    axes[0,0].set(xlim=(-.1,.3),ylim=(0,.004),title='Actual NASA fine mesh: leading-edge region')
    axes[0,1].set(xlim=(.85,1.1),ylim=(0,.06),title='Wall-normal distribution near x=0.97')
    for role,label,color in [('coarse','coarse','#a77a2c'),('medium','medium','#25858d'),('fine','fine uniform','#a44a5f'),('fine_nested','fine nested','#4456a8')]:
        p=CASE/role/'prediction_frozen.json'
        if not p.exists():continue
        h=history(p.parent);x=np.array([r['Inner_Iter'] for r in h]);rho=np.array([r['rms[Rho]'] for r in h]);cd=np.array([r['CD'] for r in h])
        axes[1,0].plot(x,rho,label=label,color=color,lw=1);axes[1,1].plot(x,cd,label=label,color=color,lw=1)
    axes[1,0].axhline(-10,ls='--',color='#8b969f',lw=.7);axes[1,0].set(xlabel='Native iteration (each run starts at0)',ylabel='log10 density residual',title='Iteration and restart histories')
    axes[1,1].set(xlabel='Native iteration',ylabel='CD (Sref=2m2)',ylim=(.0027,.006),title='Stable force alone does not prove convergence')
    for ax in axes[1]:ax.grid(alpha=.2);ax.legend()
    fig.suptitle('NASA flat-plate SA-neg: source mesh and actual native histories');fig.tight_layout();fig.savefig(ROOT/'outputs/plots/flatplate_mesh_and_convergence_20261025.png',dpi=160);plt.close(fig)
    print('Mesh/convergence figure written')

if __name__=='__main__':main()
