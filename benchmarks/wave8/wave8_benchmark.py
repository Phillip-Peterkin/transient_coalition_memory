import os, sys, json, csv, math
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data/wave7')
from wave7_benchmark import EnergeticCellular, FixedKCellular, run as base_run
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import World, DynamicBayes, EWMA, ProvGraph, EPS, sigmoid, ece

class VOICellular(EnergeticCellular):
    name='voi_cellular'
    def __init__(self, min_k=1, max_k=8, base_margin=.34, flip_guard=1.15,
                 delta_p=.035, lookahead=2, disagreement_gain=.55,
                 volatility_gain=.55, stale_gain=.12, **kw):
        super().__init__(min_k=min_k,max_k=max_k,**kw)
        self.base_margin=base_margin
        self.flip_guard=flip_guard
        self.delta_p=delta_p
        self.lookahead=lookahead
        self.dg=disagreement_gain
        self.vg=volatility_gain
        self.stale_gain=stale_gain
        self.last_fb=defaultdict(lambda:-10**9)
    def predict(self,key,reports,t):
        rows=self._evidence(key,reports)
        active=[]; z=0.0; pos=neg=0.0
        ones=sum(y for _,_,y in reports); zeros=len(reports)-ones
        report_dis=min(ones,zeros)/(max(ones,zeros)+EPS)
        # fast/slow disagreement is an internal change detector
        fast_pref=self.cf[(key,1)]-self.cf[(key,0)]
        slow_pref=self.cs[(key,1)]-self.cs[(key,0)]
        volatility=min(1.5,abs(fast_pref-slow_pref))
        age=max(0,t-self.last_fb[key]); stale=min(1.0,age/30.0)
        stop_reason='budget'
        for n,row in enumerate(rows[:self.max_k]):
            active.append(row); z+=row[1]
            if row[1]>=0: pos+=abs(row[1])
            else: neg+=abs(row[1])
            contradiction=min(pos,neg)/(max(pos,neg)+EPS)
            effective_z=z*(1-self.cg*contradiction)
            self.ops+=2
            if len(active)<self.min_k: continue
            remaining=rows[n+1:min(len(rows),n+1+self.lookahead)]
            if not remaining:
                stop_reason='exhausted'; break
            # pessimistic bound: unresolved evidence may oppose the current decision
            rem_bound=sum(r[0] for r in remaining)
            current_sign=1 if effective_z>=0 else -1
            worst_z=effective_z-current_sign*self.flip_guard*rem_bound
            p_now=sigmoid(effective_z/max(self.temp,EPS))
            p_worst=sigmoid(worst_z/max(self.temp,EPS))
            probability_shift=abs(p_now-p_worst)
            adaptive_margin=(self.base_margin + self.dg*report_dis +
                             self.vg*volatility + self.stale_gain*stale)
            flip_safe=(effective_z==0) or ((effective_z>0)==(worst_z>0))
            margin_safe=abs(effective_z)>=adaptive_margin
            value_low=probability_shift<=self.delta_p
            if flip_safe and margin_safe and value_low:
                stop_reason='low_value'; break
        contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        final_z=z*(1-self.cg*contradiction)/max(self.temp,EPS)
        p=sigmoid(final_z)
        trace={'key':key,'p':p,'active':[(s,c,y,ck,abs(v)) for _,v,s,c,y,ck in active],
               'used':len(active),'contradiction':contradiction,
               'report_disagreement':report_dis,'volatility':volatility,'age':age,
               'stop_reason':stop_reason}
        return p,trace
    def feedback(self,e):
        super().feedback(e)
        self.last_fb[e['key']]=e.get('time',self.last_fb[e['key']])


def run(seed,cls,params):
    w=World(seed);m=cls(**params);q=defaultdict(list);P=[];Y=[];changed=[];post=[];fc=[];used=[];reasons=defaultdict(int)
    for t in range(w.T):
        for ev in q.pop(t,[]):m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]);key=(i,c);reps=w.reports(t,i);p,tr=m.predict(key,reps,t);y=int(w.truth[t,i])
            P.append(p);Y.append(y);post.append(t>=w.change_t);changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i]);fc.append((p>.9 and y==0)or(p<.1 and y==1));used.append(tr.get('used',len(reps))); reasons[tr.get('stop_reason','na')]+=1
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i])
                if due<w.T:q[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr,'time':due})
    P=np.array(P);Y=np.array(Y);post=np.array(post);changed=np.array(changed);acc=((P>=.5).astype(int)==Y);st=m.stats()
    return {'accuracy':float(acc.mean()),'post_change_accuracy':float(acc[post].mean()),'changed_fact_accuracy':float(acc[changed].mean()),
            'brier':float(np.mean((P-Y)**2)),'ece':ece(P,Y),'false_certainty':float(np.mean(fc)),
            'memory_states':st['memory_states'],'updates':st['updates'],'active_ops':st['active_ops'],'ops_per_correct':float(st['active_ops']/max(1,acc.sum())),
            'avg_activated':float(np.mean(used)),'p90_activated':float(np.percentile(used,90)),'stop_reasons':dict(reasons)}

def aggregate(cls,p,seeds):
    rs=[run(s,cls,p) for s in seeds]
    keys=[k for k,v in rs[0].items() if isinstance(v,(int,float))]
    return {'mean':{k:float(np.mean([r[k] for r in rs])) for k in keys},'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in keys},'runs':rs,'params':p}

def candidates():
    base={'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58,'theta':999}
    out=[]
    for bm in [.30,.40]:
      for fg in [1.0,1.3]:
       for dp in [.035,.065]:
        for la in [1,2]:
         p=base.copy();p.update({'base_margin':bm,'flip_guard':fg,'delta_p':dp,'lookahead':la,'disagreement_gain':.5,'volatility_gain':.5,'stale_gain':.1,'min_k':1,'max_k':8})
         out.append(p)
    return out

def objective(m):
    # preserve changed-world quality first; then accuracy; then sparse activation
    return 2.2*m['changed_fact_accuracy'] + .8*m['accuracy'] - .35*m['brier'] - .12*m['false_certainty'] - .012*m['avg_activated']

def main():
    out='/mnt/data/wave8';os.makedirs(out,exist_ok=True)
    dev=[12100]
    regression=[11700,11701,11702,11703]
    holdout=[13100,13101,13102]
    best=None
    for p in candidates():
        a=aggregate(VOICellular,p,dev);sc=objective(a['mean'])
        if best is None or sc>best[0]:best=(sc,p,a)
    pbest=best[1]
    standard={
      'provenance_graph':(ProvGraph,{'lr':.12,'decay':.98,'claim':.5}),
      'old_energetic':(EnergeticCellular,{'lr':.22,'fast_decay':.90,'theta':.50,'min_k':1,'max_k':8,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58}),
      'fixed_k8':(FixedKCellular,{'k':8,'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58}),
      'voi_cellular':(VOICellular,pbest)
    }
    results={n:aggregate(c,p,holdout) for n,(c,p) in standard.items()}
    regression_result={'deferred':'not run in compact pass'}
    payload={'design':{'dev':dev,'regression':regression,'fresh_holdout':holdout,'scope':'gating-only repair'},'best_params':pbest,'dev_result':best[2],'regression_result':regression_result,'results':results}
    with open(out+'/results.json','w') as f:json.dump(payload,f,indent=2)
    fields=['method','accuracy','changed_fact_accuracy','brier','ece','false_certainty','avg_activated','p90_activated','ops_per_correct','memory_states']
    with open(out+'/summary.csv','w',newline='') as f:
        wri=csv.DictWriter(f,fieldnames=fields);wri.writeheader()
        for n,v in results.items():wri.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    print('best',pbest)
    for n,v in results.items():
        m=v['mean'];print(n,round(m['accuracy'],4),round(m['changed_fact_accuracy'],4),round(m['brier'],4),round(m['avg_activated'],2),round(m['p90_activated'],1),round(m['ops_per_correct'],1))

if __name__=='__main__':main()
