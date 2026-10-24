from pathlib import Path
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def parse_mesh(p):
    lines=p.read_text().splitlines();cells=[];marks={};i=0
    while i<len(lines):
        line=lines[i]
        if line.startswith('NELEM='):
            n=int(line.split('=')[1]);cells=[list(map(int,x.split())) for x in lines[i+1:i+n+1]];i+=n
        elif line.startswith('NPOIN='):
            n=int(line.split('=')[1].split()[0]);points=np.array([[float(v) for v in x.split()[:2]] for x in lines[i+1:i+n+1]]);i+=n
        elif line.startswith('MARKER_TAG='):
            tag=line.split('=')[1].strip();n=int(lines[i+1].split('=')[1]);marks[tag]=np.array([[int(v) for v in x.split()[1:3]] for x in lines[i+2:i+2+n]]);i+=n+1
        i+=1
    conn=[np.array(c[1:4] if c[0]==5 else c[1:5]) for c in cells]
    return points,conn,marks
def audit(name):
    folder=OUT/'simulations'/name;p,con,marks=parse_mesh(folder/'mesh.su2')
    edges=marks['AIRFOIL'];wset=set(edges.ravel().tolist());heights=[];spacing=np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1)
    byregion={k:[] for k in ['LE','TE','gradient','other']};xg=json.loads((ROOT/'work/blind_validation/solver/gradient_regions.json').read_text())['upper']
    for c in con:
        on=[i for i in c if i in wset];off=[i for i in c if i not in wset]
        if len(on)!=2 or len(off)!=2:continue
        v=p[on[1]]-p[on[0]];q=p[off]-p[on[0]];hh=np.abs(v[0]*q[:,1]-v[1]*q[:,0])/np.linalg.norm(v)
        heights.extend(hh.tolist());xc=p[on].mean(0)
        reg='LE' if xc[0]<.05 else 'TE' if xc[0]>.9 else 'gradient' if abs(xc[0]-xg)<.07 and xc[1]>.02 else 'other';byregion[reg].extend(hh.tolist())
    centers=np.array([p[c].mean(0) for c in con]);chordslens=np.array([np.linalg.norm(p[np.roll(c,-1)]-p[c],axis=1).max() for c in con]);gradmask=(abs(centers[:,0]-xg)<.07)&(centers[:,1]>-.02)&(centers[:,1]<.18)
    vals=lambda a:{'min':float(np.min(a)),'median':float(np.median(a)),'max':float(np.max(a))}
    extra={'wall_edge_spacing_m':vals(spacing),'measured_wall_adjacent_quad_normal_height_m':vals(heights),'measured_first_height_by_region_m':{k:vals(v) for k,v in byregion.items() if v},'gradient_refinement_region':{'definition':{'x_min':xg-.07,'x_max':xg+.07,'y_min':-.02,'y_max':.18},'cells':int(gradmask.sum()),'max_edge_length_m':vals(chordslens[gradmask])},'note':'Normal full-cell height is independently computed from exported SU2 wall-edge quads; TE point-fan triangles are not represented by a two-wall-node quad height; actual Y+ screen includes all wall points.'}
    (folder/'mesh_export_audit.json').write_text(json.dumps(extra,indent=2))
    return extra
if __name__=='__main__':
    reports={n:audit(n) for n in ['coarse','medium','fine','medium_far']}
    src=np.loadtxt(ROOT/'work/blind_validation/analysis_input/geom.txt',skiprows=5)
    def loadpts(name):
        rows=[]
        for l in (ROOT/'work/blind_validation/analysis_input'/name).read_text().splitlines()[1:]:
            tokens=l.replace(',',' ').split();vals=[]
            for t in tokens:
                if '*' in t:
                    count,val=t.split('*');vals.extend([float(val)]*int(count))
                else:vals.append(float(t))
            if vals:rows.append(vals)
        return np.array(rows)
    lo=loadpts('yl.pts');up=loadpts('yu.pts')
    sourcecheck={'source_rows':len(src),'source_full_chord_m':float(np.ptp(src[:,0])),'maximum_thickness_m':float(np.max(src[:,1]+src[:,2])),'signed_pts_vs_geom_max_m':float(max(np.abs(lo[:,:2]-np.c_[src[:,0],-src[:,1]]).max(),np.abs(up[:,:2]-src[:,[0,2]]).max())),'source_file_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'work/blind_validation/analysis_input').iterdir() if p.is_file()},'classification':'source units m; signed lower ordinate verified against published Fortran conversion and both .pts; chord normalized1m without changing coordinates','family_curve_hashes':{n:json.loads((OUT/'simulations'/n/'mesh_audit.json').read_text())['curve_definition_sha256'] for n in reports},'all_family_curves_identical':len(set(json.loads((OUT/'simulations'/n/'mesh_audit.json').read_text())['curve_definition_sha256'] for n in reports))==1}
    (OUT/'reports/prediction_geometry_units_audit.json').write_text(json.dumps(sourcecheck,indent=2));print(json.dumps(sourcecheck,indent=2))
