"""Independent SU2 primal-mesh connectivity and geometric audit (no flow targets)."""
from pathlib import Path
import sys,json
from collections import Counter,defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'outputs/projects/proje-15cce2de02'
def audit(name):
 p=OUT/'simulations'/name/'mesh.su2';lines=p.read_text().splitlines();i=0;cells=[];markers={}
 while i<len(lines):
  s=lines[i].strip()
  if s.startswith('NELEM'):
   count=int(s.split('=')[1]);raw=[list(map(int,row.split())) for row in lines[i+1:i+1+count]]
   assert all(row[0] in (5,9) for row in raw)
   cells=[np.array(row[1:4] if row[0]==5 else row[1:5]) for row in raw];i+=count
  elif s.startswith('NPOIN'):
   count=int(s.split('=')[1].split()[0]);points=np.array([[float(v) for v in row.split()[:2]] for row in lines[i+1:i+1+count]]);i+=count
  elif s.startswith('MARKER_TAG'):
   tag=s.split('=')[1].strip();count=int(lines[i+1].split('=')[1]);markers[tag]=[tuple(sorted(map(int,row.split()[1:3]))) for row in lines[i+2:i+2+count]];i+=count+1
  i+=1
 edges=Counter();owners=defaultdict(list);area=[];skew=[];centers=[]
 for ci,c in enumerate(cells):
  q=points[c];d=np.roll(q,-1,axis=0)-q;area.append(.5*np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1)));centers.append(q.mean(0))
  previous=points[np.roll(c,1)]-q;angle=np.degrees(np.arccos(np.clip(np.sum(previous*d,axis=1)/(np.linalg.norm(previous,axis=1)*np.linalg.norm(d,axis=1)),-1,1)))
  ideal=60 if len(c)==3 else 90;skew.append(max((angle.max()-ideal)/(180-ideal),(ideal-angle.min())/ideal))
  for a,b in zip(c,np.roll(c,-1)):
   edge=tuple(sorted((int(a),int(b))));edges[edge]+=1;owners[edge].append(ci)
 boundary={edge for edge,n in edges.items() if n==1};tagged=set(e for es in markers.values() for e in es)
 unmatched=boundary-tagged;unexpected=tagged-boundary;badneighbors=[e for e,n in edges.items() if n not in (1,2)]
 degree={}
 for tag,es in markers.items():
  counts=Counter(n for e in es for n in e);degree[tag]={'edges':len(es),'nodes':len(counts),'all_node_degrees_2':all(n==2 for n in counts.values()),'min_degree':min(counts.values()),'max_degree':max(counts.values())}
 adjacency=[[] for _ in cells]
 for es in owners.values():
  if len(es)==2:adjacency[es[0]].append(es[1]);adjacency[es[1]].append(es[0])
 seen=set();components=[]
 for k in range(len(cells)):
  if k in seen:continue
  todo=[k];seen.add(k);size=0
  while todo:
   u=todo.pop();size+=1
   for v in adjacency[u]:
    if v not in seen:seen.add(v);todo.append(v)
  components.append(size)
 area=np.array(area);skew=np.array(skew);centers=np.array(centers);idx=int(skew.argmax())
 result={'case':name,'nodes':len(points),'cells':len(cells),'all_positive_signed_areas':bool(np.all(area>0)),'minimum_signed_area_m2':float(area.min()),'exact_duplicate_node_coordinates':int(len(points)-len(np.unique(points,axis=0))),'unmarked_boundary_edges':len(unmatched),'tagged_edges_not_single_fluid_neighbor':len(unexpected),'nonmanifold_edges':len(badneighbors),'fluid_connected_components_cell_counts':components,'marker_closed_loops':degree,'max_equiangle_skewness':float(skew[idx]),'worst_skew_cell_center_m':centers[idx].tolist(),'worst_skew_cell_node_ids':cells[idx].tolist(),'method_scope':'Independent primal SU2 geometry/edge audit. High wall aspect ratio is not a failure by itself. This does not directly audit SU2 node-centered dual-volume orthogonality; no after-result skew cutoff was introduced.'}
 result['topology_and_positive_area_checks_passed']=result['all_positive_signed_areas'] and len(components)==1 and not (unmatched or unexpected or badneighbors) and all(d['all_node_degrees_2'] for d in degree.values())
 return result
if __name__=='__main__':
 names=sys.argv[1:] or ['coarse','medium','fine','medium_far'];results={n:audit(n) for n in names}
 dest=OUT/'reports'/('review_v2_topology.json' if names[0].startswith('v2') else 'review_v1_topology.json')
 dest.write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps({k:{'passed':v['topology_and_positive_area_checks_passed'],'skew':v['max_equiangle_skewness'],'worst_location':v['worst_skew_cell_center_m']} for k,v in results.items()},indent=2))
