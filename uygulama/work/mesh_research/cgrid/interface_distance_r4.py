"""Exact polygon-segment distance with a conservative cKDTree broad phase.

No CAD/profile approximation: this uses the actual existing near-grid interface.
"""
import numpy as np
from scipy.spatial import cKDTree

class InterfaceSizing:
    def __init__(self,points):
        self.a=np.array(points,dtype=float);self.b=np.roll(self.a,-1,axis=0);self.v=self.b-self.a
        self.length=np.linalg.norm(self.v,axis=1);assert np.min(self.length)>0
        self.hnode=np.minimum(self.length,np.roll(self.length,1))
        self.hnext=np.roll(self.hnode,-1);self.l2=self.length**2
        self.mid=(self.a+self.b)/2;self.tree=cKDTree(self.mid);self.max_half=float(self.length.max()/2)
        self.calls=0;self.skips=0;self.candidates_sum=0;self.candidates_max=0

    def distances(self,point,ids):
        # Orthogonal projection on the CLOSED segment; endpoints included.
        ids=np.asarray(ids,dtype=int);q=np.asarray(point)
        t=np.clip(np.sum((q-self.a[ids])*self.v[ids],axis=1)/self.l2[ids],0,1)
        distance=np.linalg.norm(q-(self.a[ids]+t[:,None]*self.v[ids]),axis=1)
        return distance,t

    def nearest(self,point,compact=True):
        self.calls+=1;point=np.asarray(point,dtype=float);dm,j=self.tree.query(point)
        # Any segment's distance >= distance-to-nearest-midpoint - longest half
        # segment. Thus this test cannot skip an actual point with d<1c.
        if compact and dm-self.max_half>=1.+2e-12:
            self.skips+=1;return None
        dd,_=self.distances(point,[j]);bound=dd[0]+self.max_half+2e-12
        ids=self.tree.query_ball_point(point,bound)
        # If a segment can improve dd, its midpoint is within dd+its_half_length.
        # The global max_half makes this candidate set conservatively complete.
        d,t=self.distances(point,ids);k=int(np.argmin(d));j=int(ids[k]);frac=float(t[k])
        self.candidates_sum+=len(ids);self.candidates_max=max(self.candidates_max,len(ids))
        h=(1-frac)*self.hnode[j]+frac*self.hnext[j]
        return float(d[k]),float(h),j,frac

    def size(self,point,h_old):
        hit=self.nearest(point,compact=True)
        if hit is None:return h_old
        d,h,_,_=hit
        if d>=1:return h_old
        full=min(h_old,h+.25*d)
        if d<=.25:return full
        t=(d-.25)/.75;s=t*t*(3-2*t)
        return (1-s)*full+s*h_old

    def audit(self,seed=17391,nrandom=1200):
        rng=np.random.default_rng(seed)
        # Sample both close to arbitrary segments and around the 1c cutoff.
        pick=rng.integers(0,len(self.a),nrandom);frac=rng.random(nrandom)
        center=self.a[pick]+frac[:,None]*self.v[pick]
        angle=rng.uniform(-np.pi,np.pi,nrandom)
        radii=np.r_[rng.uniform(0,.3,nrandom//3),rng.uniform(.8,1.2,nrandom//3),rng.uniform(0,3,nrandom-2*(nrandom//3))]
        pts=center+radii[:,None]*np.c_[np.cos(angle),np.sin(angle)]
        ids=np.arange(len(self.a));errors=[];herrors=[];wrongcut=0;unchanged=0
        for p in pts:
            ds,ts=self.distances(p,ids);k=int(np.argmin(ds));exact=ds[k];eh=(1-ts[k])*self.hnode[k]+ts[k]*self.hnext[k]
            hit=self.nearest(p,compact=True)
            if hit is None:
                wrongcut+=int(exact<1);continue
            errors.append(abs(hit[0]-exact));herrors.append(abs(hit[1]-eh))
            if exact>=1:
                old=.734567891234;unchanged+=int(self.size(p,old)==old)
        assert wrongcut==0 and max(errors,default=0)<1e-12
        return {'random_seed':seed,'random_samples':nrandom,'reference':'Brute-force distance/projection to EVERY real interface segment, independent of cKDTree candidate selection','max_distance_error_m':max(errors,default=0),'max_interpolated_h_error_m':max(herrors,default=0),'incorrect_d_less_than_1_skips':wrongcut,'queried_d_ge_1_size_exactly_old_count':unchanged,'broad_phase_completeness':'midpoint lower bound and candidate radius use maximum actual segment half-length, with2e-12m roundoff padding','interface_segments':len(self.a),'segment_length_m':{'min':float(self.length.min()),'median':float(np.median(self.length)),'max':float(self.length.max())},'node_h_m':{'min':float(self.hnode.min()),'median':float(np.median(self.hnode)),'max':float(self.hnode.max())}}

    def counters(self):return {'calls':self.calls,'far_cutoff_skips':self.skips,'candidate_count_max':self.candidates_max,'candidate_count_mean_for_non_skipped':self.candidates_sum/max(1,self.calls-self.skips)}
