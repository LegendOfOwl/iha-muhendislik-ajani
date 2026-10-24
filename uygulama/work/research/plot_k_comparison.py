"""Plot actual native STL meshes from the fixed-setting comparison."""
import json
import os
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
study=json.loads((ROOT/'outputs/reports/k_family_study.json').read_text(encoding='utf-8'))
fig=plt.figure(figsize=(13,8),facecolor='#f1f5f8')
names={'box':'40 × 30 × 8 mm kutu','hole_plate':'Ø10 delikli plaka','spacer':'Ø20 / Ø6, h12 ara parça'}
for i,model in enumerate(['k1b','cadmonkey32']):
    for j,case in enumerate(names):
        row=next(r for r in study['results'] if r['model']==model and r['mode']=='baseline' and r['case']==case)
        p=Path(row['folder'])/'generated.stl'
        raw=p.read_text(encoding='ascii')
        verts=np.array([[float(v) for v in match] for match in re.findall(r'vertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)',raw)])
        triangles=verts.reshape(-1,3,3)
        ax=fig.add_subplot(2,3,i*3+j+1,facecolor='white')
        accepted=row['geometry_accepted']; color='#199284' if accepted else '#c15d4a'
        ax.imshow(plt.imread(ROOT/'work/research/k1b_deep/views'/f'{model}_{case}.png')); ax.set_axis_off()
        label='K-1B' if model=='k1b' else 'Cadmonkey data-32'
        ax.set_title(label+' · '+names[case],fontsize=11,pad=0,color='#173b4b')
        metric='Kabul edildi' if accepted else ('Merkezleme yanlış' if case=='box' else 'Geometri yanlış')
        ax.text(.5,.01,metric,transform=ax.transAxes,ha='center',color=color,fontsize=11,weight='bold')
fig.suptitle('Aynı istemler · gerçek OpenSCAD çıktıları · model kodu değiştirilmedi',fontsize=16,color='#173b4b',y=.97)
fig.text(.5,.018,'Başlıklardaki ölçüler istenen değerlerdir; görünüşler ayrı ölçeklendi. Kabul ölçümlerle verildi; genel doğruluk oranı değildir.',ha='center',fontsize=9.5,color='#53697a')
fig.subplots_adjust(left=.02,right=.98,top=.91,bottom=.07,hspace=.08,wspace=.03)
fig.savefig(ROOT/'outputs/plots/k_family_comparison.png',dpi=160)
print(ROOT/'outputs/plots/k_family_comparison.png')
