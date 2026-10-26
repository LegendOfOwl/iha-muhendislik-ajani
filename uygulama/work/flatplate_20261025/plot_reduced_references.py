from prepare import ROOT,read
import os
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    r=read(ROOT/'outputs/reports/reduced_family_review_20261026.json')['results']['fine']
    fig,ax=plt.subplots(1,2,figsize=(12,4.4))
    for index,(record,color,name) in enumerate(zip(r['reference_errors']['Cf_curve'],['#007e97','#bf6c31'],['CFL3D source','FUN3D source'])):
        data=np.genfromtxt(ROOT/record['csv'],delimiter=',',names=True);assert np.all(data['valid_sample']==1)
        if index==0:
            # Draw exactly the interpolated values scored at reference x points;
            # connecting a native x=0 node on a log axis misrepresents the LE sample.
            for a in ax:a.plot(data['coordinate'],data['native'],label='SU2 field3999, at source x',color='#202c35')
        for a in ax:a.plot(data['coordinate'],data['reference'],label=name,color=color,ls='--')
    ax[0].set(xscale='log',xlim=(.0008,2),title='All reference points, including leading edge')
    ax[1].set(xlim=(.1,1.9),ylim=(.0022,.0042),title='Preregistered scoring window:0.1–1.9m')
    for a in ax:a.set(xlabel='x [m]',ylabel='Cf');a.grid(alpha=.25);a.legend()
    fig.tight_layout();fig.savefig(ROOT/'outputs/plots/reduced_family_Cf_reference_20261026.png',dpi=160);plt.close(fig)

if __name__=='__main__':main()
