"""Show measured native histories for every tested grid and numerical attempt."""
import csv,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def history(folder):
    with (folder/'history.csv').open() as f:
        reader=csv.DictReader(f)
        rows=[{k.strip().strip('"'):float(v) for k,v in r.items()} for r in reader]
    return {k:np.array([r[k] for r in rows]) for k in ['CL','CD','rms[Rho]']}

def main():
    pid=json.loads((ROOT/'work/validation/projects.json').read_text())['cfd']
    out=ROOT/'outputs/projects'/pid
    result=json.loads((out/'reports/m6_rans_results.json').read_text())
    first=Path(result['previous_run_directory'])
    fig,axs=plt.subplots(3,2,figsize=(14,9),sharex='col')
    for j,r in enumerate(result['results']):
        a=history(first/r['grid']);b=history(Path(result['continuation_run_directory'])/r['grid'])
        for i,key in enumerate(['CL','CD','rms[Rho]']):
            ax=axs[i,j]
            ax.plot(np.arange(1,len(a[key])+1),a[key],color='#667b8b',lw=.8,label='First run')
            ax.plot(np.arange(len(a[key])+1,len(a[key])+len(b[key])+1),b[key],color='#cf7322',lw=.9,label='Fixed-CFL continuation')
            ax.axvline(len(a[key]),ls='--',color='#263d51',lw=.7)
            ax.grid(alpha=.2);ax.set_ylabel('log10 density residual' if i==2 else key)
            if i==0:ax.set_title(r['grid']);ax.legend(fontsize=8)
            if i==2:ax.axhline(-7,color='#bc4b49',ls=':',lw=.8);ax.set_xlabel('Native iteration (first + continuation)')
    fig.suptitle('ONERA M6: native convergence histories; both attempts retained')
    fig.tight_layout();fig.savefig(out/'plots/m6_force_history.png',dpi=150);plt.close(fig)
    print('Native histories plotted for both grids and both attempts.')
if __name__=='__main__':main()
