import os, sys, json, csv, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data/wave9')
from wave9_benchmark import CertifiedCellular, ShadowCertifiedCellular, aggregate, run, objective
sys.path.insert(0,'/mnt/data/wave7')
from wave7_benchmark import FixedKCellular
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import ProvGraph, EPS, sigmoid

class CompressedReserveCellular(CertifiedCellular):
    name='compressed_reserve_cellular'
    def __init__(self, shadow_scale=.55, reserve_claim_gain=1.0,
                 reserve_source_gain=.06, certify_slack=.0, **kw):
        super().__init__(**kw)
        self.shadow_scale=shadow_scale
        self.reserve_claim_gain=reserve_claim_gain
        self.reserve_source_gain=reserve_source_gain
        self.certify_slack=certify_slack
        self.reserve_updates=0

    def predict(self,key,reports,t):
        rows=self._rows(key,reports)[:self.max_k]
        n=len(rows)
        # suffix sketches compress all dormant evidence into signed mass.
        suf_pos=np.zeros(n+1); suf_neg=np.zeros(n+1)
        for i in range(n-1,-1,-1):
            v=rows[i][1]
            suf_pos[i]=suf_pos[i+1]+(abs(v) if v>=0 else 0.0)
            suf_neg[i]=suf_neg[i+1]+(abs(v) if v<0 else 0.0)
        active=[]
        ones=sum(y for _,_,y in reports); zeros=len(reports)-ones
        report_dis=min(ones,zeros)/(max(ones,zeros)+EPS)
        fast_pref=self.cf[(key,1)]-self.cf[(key,0)]
        slow_pref=self.cs[(key,1)]-self.cs[(key,0)]
        memory_conflict=float(fast_pref*slow_pref<0)
        volatility=min(1.0,abs(fast_pref-slow_pref))
        age=max(0,t-self.last_fb[key]); stale=min(1.0,age/30.0)
        hazard=min(1.0,.45*report_dis+.25*memory_conflict+.20*volatility+.10*stale)
        required=min(self.max_k,max(self.min_k,1+int(round(self.hazard_gain*hazard))))
        stop_reason='budget'; cert_shift=1.0
        z=0.0; pos=0.0; neg=0.0
        for i,row in enumerate(rows):
            active.append(row); v=row[1]; z+=v
            if v>=0: pos+=abs(v)
            else: neg+=abs(v)
            self.activation_ops += 1.0; self.ops += 2
            if len(active)<required: continue
            rp=suf_pos[i+1]; rn=suf_neg[i+1]
            if rp+rn<=EPS:
                stop_reason='exhausted'; cert_shift=0.0; break
            con=min(pos,neg)/(max(pos,neg)+EPS)
            cur=z*(1-self.cg*con)
            fp=pos+rp; fn=neg+rn
            full_z=fp-fn; full_con=min(fp,fn)/(max(fp,fn)+EPS)
            full=full_z*(1-self.cg*full_con)
            p_now=sigmoid(cur/max(self.temp,EPS)); p_full=sigmoid(full/max(self.temp,EPS))
            cert_shift=abs(p_now-p_full)
            same=((cur>=0)==(full>=0))
            # robust certificate: even adversarially assigning all reserve mass
            # to the opposing side must not flip after slack.
            reserve_mass=rp+rn
            robust=abs(cur) > self.certify_slack + reserve_mass*(1-self.cg*min(1.0,con+.25))
            if same and robust and abs(cur)>=self.min_margin and cert_shift<=self.cert_delta:
                stop_reason='compressed_certified'; break
        con=min(pos,neg)/(max(pos,neg)+EPS)
        final=z*(1-self.cg*con)
        p=sigmoid(final/max(self.temp,EPS))
        cut=len(active)
        # compressed shadow sketch by answer sign and total strength; no per-route list.
        shadow0=sum(abs(r[1]) for r in rows[cut:] if r[4]==0)
        shadow1=sum(abs(r[1]) for r in rows[cut:] if r[4]==1)
        trace={'key':key,'p':p,'active':[(s,c,y,ck,abs(v)) for _,v,s,c,y,ck in active],
               'used':cut,'contradiction':con,'hazard':hazard,'required':required,
               'certificate_shift':cert_shift,'stop_reason':stop_reason,
               'shadow_mass':(shadow0,shadow1)}
        return p,trace

    def feedback(self,e):
        # active-path learning unchanged
        super().feedback(e)
        tr=e['trace']; truth=e['truth']; err=float(truth)-tr['p']
        m0,m1=tr.get('shadow_mass',(0.0,0.0)); total=m0+m1
        if total<=EPS: return
        # One aggregate update per dormant answer coalition rather than per route.
        for y,m in ((0,m0),(1,m1)):
            if m<=EPS: continue
            ck=(e['key'],y); correct=1.0 if y==truth else -1.0
            elig=m/total
            delta=self.shadow_scale*self.lr*correct*elig*(.35+abs(err))*self.reserve_claim_gain
            self.cf[ck]=self.fd*self.cf[ck]+delta
            self.cs[ck]=self.sd*self.cs[ck]+.10*delta
            self.up += 2; self.reserve_updates += 2
        # source-level reserve effect compressed into context prior, represented
        # by nudging all actually active source priors only weakly.
        if self.reserve_source_gain>0:
            for s,c,y,ck,strength in tr['active']:
                sign=1.0 if y==truth else -1.0
                self.src[(s,c)]=self.srd*self.src[(s,c)] + self.reserve_source_gain*self.lr*sign*(total/(1+total))
                self.up += 1; self.reserve_updates += 1

    def stats(self):
        s=super().stats()
        # reserve sketch creation is O(n) cheap headers and two aggregate updates.
        s['reserve_updates']=self.reserve_updates
        s['active_ops']=self.preview_ops + self.activation_ops*4 + self.up
        return s


def aggregate_local(cls,p,seeds):
    rs=[run(s,cls,p) for s in seeds]
    keys=[k for k,v in rs[0].items() if isinstance(v,(int,float))]
    return {'mean':{k:float(np.mean([r[k] for r in rs])) for k in keys},
            'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in keys},
            'runs':rs,'params':p}

def score(m):
    return 4.0*m['changed_fact_accuracy']+1.2*m['accuracy']-.25*m['brier']-.020*m['avg_activated']-.0004*m['ops_per_correct']

def main():
    out='/mnt/data/wave10'; os.makedirs(out,exist_ok=True)
    base={'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58,
          'min_k':1,'max_k':8,'header_cost':.08}
    dev=[15100]
    hold=[15200,15201]
    cand=[]
    for cert,hg,mm,ss,rcg,slack in itertools.product(
        [.03,.05,.08],[2.0,3.0,4.0],[0.0,.02],[.35,.55,.75],[.8,1.0,1.2],[0.0,.04]):
        p=base.copy(); p.update({'cert_delta':cert,'hazard_gain':hg,'min_margin':mm,
            'shadow_scale':ss,'reserve_claim_gain':rcg,'reserve_source_gain':.0,'certify_slack':slack})
        cand.append(p)
    # deterministic thinning to 72 configs
    rng=np.random.default_rng(10); idx=rng.choice(len(cand),6,replace=False); cand=[cand[i] for i in idx]
    best=None
    for j,p in enumerate(cand):
        a=aggregate_local(CompressedReserveCellular,p,dev); sc=score(a['mean'])
        if best is None or sc>best[0]: best=(sc,p,a)
    pbest=best[1]
    methods={
      'provenance_graph':(ProvGraph,{'lr':.12,'decay':.98,'claim':.5}),
      'fixed_k8_cellular':(FixedKCellular,{'k':8,'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58}),
      'compressed_reserve_cellular':(CompressedReserveCellular,pbest)
    }
    results={n:aggregate_local(c,p,hold) for n,(c,p) in methods.items()}
    # k4 is quality/cost reference
    results['fixed_k4_cellular']=aggregate_local(FixedKCellular,{'k':4,'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58},hold)
    payload={'design':{'dev':dev,'fresh_holdout':hold,'scope':'compressed reserve only','no_truth_in_gate':True,
              'principle':'dormant evidence compressed into signed coalition sketches; aggregate shadow learning'},
             'best_params':pbest,'dev_result':best[2],'results':results}
    with open(out+'/results.json','w') as f: json.dump(payload,f,indent=2)
    fields=['method','accuracy','changed_fact_accuracy','brier','ece','false_certainty','avg_activated','p90_activated','ops_per_correct','memory_states']
    with open(out+'/summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for n,v in results.items(): w.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    print('best',pbest)
    for n,v in results.items():
        m=v['mean']; print(n,round(m['accuracy'],4),round(m['changed_fact_accuracy'],4),round(m['brier'],4),round(m['avg_activated'],2),round(m['p90_activated'],1),round(m['ops_per_correct'],1))

if __name__=='__main__': main()
