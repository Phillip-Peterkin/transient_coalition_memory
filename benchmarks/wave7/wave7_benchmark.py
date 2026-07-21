import os, sys, json, math, csv, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import World, Majority, StaticBayes, DynamicBayes, EWMA, ProvGraph, score, ece, EPS, sigmoid

class EnergeticCellular:
    name='energetic_cellular'
    def __init__(self, lr=.18, fast_decay=.90, slow_decay=.995, source_decay=.992,
                 claim_fast=1.0, claim_slow=.22, source=.18, direct=.16,
                 theta=.62, min_k=1, max_k=12, contradiction_gain=.75,
                 uncertainty_cost=.22, anchor=.45, temp=.85):
        self.lr=lr; self.fd=fast_decay; self.sd=slow_decay; self.srd=source_decay
        self.wf=claim_fast; self.ws=claim_slow; self.wsrc=source; self.direct=direct
        self.theta=theta; self.min_k=min_k; self.max_k=max_k; self.cg=contradiction_gain
        self.uc=uncertainty_cost; self.anchor=anchor; self.temp=temp
        self.cf=defaultdict(float); self.cs=defaultdict(float); self.src=defaultdict(float)
        self.ops=0; self.up=0
    def _evidence(self,key,reports):
        rows=[]
        for s,c,y in reports:
            sg=1 if y else -1
            ck=(key,y)
            strength=self.direct+self.wf*self.cf[ck]+self.ws*self.cs[ck]+self.wsrc*self.src[(s,c)]
            v=sg*strength
            rows.append((abs(v),v,s,c,y,ck))
            self.ops+=4
        rows.sort(key=lambda x:x[0], reverse=True)
        return rows
    def predict(self,key,reports,t):
        rows=self._evidence(key,reports)
        active=[]; z=0.0; pos=neg=0.0
        last_margin=0.0
        for row in rows[:self.max_k]:
            active.append(row); z+=row[1]
            if row[1]>=0: pos+=abs(row[1])
            else: neg+=abs(row[1])
            contradiction=min(pos,neg)/(max(pos,neg)+EPS)
            effective=abs(z)*(1-self.cg*contradiction)
            # precision-adaptive threshold: contradiction raises the activation energy required
            threshold=self.theta + self.uc*contradiction
            last_margin=effective
            self.ops+=2
            if len(active)>=self.min_k and effective>=threshold:
                break
        contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        z=z*(1-self.cg*contradiction)/max(self.temp,EPS)
        p=sigmoid(z)
        trace={'key':key,'p':p,'active':[(s,c,y,ck,abs(v)) for _,v,s,c,y,ck in active],
               'used':len(active),'contradiction':contradiction,'margin':last_margin}
        return p,trace
    def feedback(self,e):
        tr=e['trace']; truth=e['truth']; err=float(truth)-tr['p']
        active=tr['active']; den=sum(a[-1] for a in active)+EPS
        # temporary eligibility trace only: no permanent path state
        for s,c,y,ck,strength in active:
            correct=1.0 if y==truth else -1.0
            elig=strength/den
            delta=self.lr*correct*elig*(.35+abs(err))
            self.cf[ck]=self.fd*self.cf[ck]+delta
            self.cs[ck]=self.sd*self.cs[ck]+.10*delta
            sk=(s,c); self.src[sk]=self.srd*self.src[sk]+.16*delta
            self.up+=3
        # direct environmental anchor dominates reputation and rapidly flips stale claims
        tk=(e['key'],truth); fk=(e['key'],1-truth)
        a=self.lr*self.anchor*(.25+abs(err))
        self.cf[tk]=self.fd*self.cf[tk]+a; self.cf[fk]=self.fd*self.cf[fk]-a
        self.cs[tk]=self.sd*self.cs[tk]+.08*a; self.cs[fk]=self.sd*self.cs[fk]-.08*a
        self.up+=4
    def stats(self):
        return {'memory_states':len(self.cf)+len(self.cs)+len(self.src),'updates':self.up,'active_ops':self.ops}

class FixedKCellular(EnergeticCellular):
    name='fixedk_cellular'
    def __init__(self,k=4,**kw): super().__init__(min_k=k,max_k=k,theta=1e9,**kw)

METHODS={
'dynamic_bayes':(DynamicBayes,{'forget':[.94,.97,.985,.995]}),
'ewma_evidence':(EWMA,{'lr':[.04,.08,.15],'decay':[.90,.96,.99]}),
'provenance_graph':(ProvGraph,{'lr':[.06,.12,.2],'decay':[.94,.98,.995],'claim':[.2,.5,.9]}),
'energetic_cellular':(EnergeticCellular,{}),
}

def run(seed,cls,params):
    w=World(seed);m=cls(**params);q=defaultdict(list);P=[];Y=[];changed=[];post=[];fc=[];used=[]
    for t in range(w.T):
        for ev in q.pop(t,[]):m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]);key=(i,c);reps=w.reports(t,i);p,tr=m.predict(key,reps,t);y=int(w.truth[t,i])
            P.append(p);Y.append(y);post.append(t>=w.change_t);changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i]);fc.append((p>.9 and y==0)or(p<.1 and y==1));used.append(tr.get('used',len(reps)))
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i])
                if due<w.T:q[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr})
    P=np.array(P);Y=np.array(Y);post=np.array(post);changed=np.array(changed);acc=((P>=.5).astype(int)==Y);st=m.stats()
    return {'accuracy':float(acc.mean()),'post_change_accuracy':float(acc[post].mean()),'changed_fact_accuracy':float(acc[changed].mean()),
            'brier':float(np.mean((P-Y)**2)),'ece':ece(P,Y),'false_certainty':float(np.mean(fc)),
            'memory_states':st['memory_states'],'updates':st['updates'],'active_ops':st['active_ops'],'ops_per_correct':float(st['active_ops']/max(1,acc.sum())),
            'avg_activated':float(np.mean(used))}

def combos(grid):
    ks=list(grid)
    for vals in itertools.product(*[grid[k] for k in ks]):yield dict(zip(ks,vals))

def tune_baseline(name,seeds):
    cls,grid=METHODS[name];best=None
    for p in combos(grid):
        rs=[run(s,cls,p) for s in seeds];avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]};sc=score(avg)
        if best is None or sc>best[0]:best=(sc,p,avg)
    return best

def cellular_candidates():
    return [
      {'lr':.18,'fast_decay':.88,'theta':.42,'min_k':1,'max_k':12,'contradiction_gain':.72,'uncertainty_cost':.22,'temp':.82,'anchor':.55},
      {'lr':.18,'fast_decay':.92,'theta':.62,'min_k':1,'max_k':12,'contradiction_gain':.72,'uncertainty_cost':.28,'temp':.88,'anchor':.50},
      {'lr':.24,'fast_decay':.88,'theta':.58,'min_k':2,'max_k':12,'contradiction_gain':.80,'uncertainty_cost':.34,'temp':.90,'anchor':.60},
      {'lr':.16,'fast_decay':.95,'theta':.78,'min_k':2,'max_k':10,'contradiction_gain':.65,'uncertainty_cost':.18,'temp':.78,'anchor':.42},
      {'lr':.22,'fast_decay':.90,'theta':.50,'min_k':1,'max_k':8,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58},
    ]

def tune_cell(seeds):
    best=None
    for p in cellular_candidates():
        rs=[run(s,EnergeticCellular,p) for s in seeds];avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]}
        sc=score(avg)-0.002*avg['avg_activated']
        if best is None or sc>best[0]:best=(sc,p,avg)
    return best

def aggregate(cls,p,seeds):
    rs=[run(s,cls,p) for s in seeds]
    return {'mean':{k:float(np.mean([r[k] for r in rs])) for k in rs[0]},'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in rs[0]},'runs':rs,'params':p}

def main():
    out='/mnt/data/wave7';os.makedirs(out,exist_ok=True)
    test=list(range(11700,11704))
    tuned={
      'dynamic_bayes':{'params':{'forget':.985}},
      'ewma_evidence':{'params':{'lr':.08,'decay':.96}},
      'provenance_graph':{'params':{'lr':.12,'decay':.98,'claim':.5}},
      'energetic_cellular':{'params':{'lr':.22,'fast_decay':.90,'theta':.50,'min_k':1,'max_k':8,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58}}
    }
    results={}
    results['dynamic_bayes']=aggregate(DynamicBayes,tuned['dynamic_bayes']['params'],test)
    results['ewma_evidence']=aggregate(EWMA,tuned['ewma_evidence']['params'],test)
    results['provenance_graph']=aggregate(ProvGraph,tuned['provenance_graph']['params'],test)
    results['energetic_cellular']=aggregate(EnergeticCellular,tuned['energetic_cellular']['params'],test)
    base=tuned['energetic_cellular']['params'].copy(); fixed={}
    for k in [1,2,4,8]:
        p={x:v for x,v in base.items() if x not in ('theta','min_k','max_k')};p['k']=k
        fixed[str(k)]=aggregate(FixedKCellular,p,test)
    payload={'design':{'fresh_holdout':test,'principles':['temporary eligibility only','fast/slow claim memory','source prior','energetic confidence stopping','contradiction raises threshold']},'tuning':tuned,'results':results,'fixed_k_ablation':fixed}
    with open(out+'/results.json','w') as f:json.dump(payload,f,indent=2)
    fields=['method','accuracy','changed_fact_accuracy','brier','ece','false_certainty','avg_activated','ops_per_correct','memory_states']
    with open(out+'/summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for n,v in results.items():w.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    for n,v in results.items():
        m=v['mean'];print(n,round(m['accuracy'],4),round(m['changed_fact_accuracy'],4),round(m['brier'],4),round(m['avg_activated'],2),round(m['ops_per_correct'],1))
    print('fixed-k')
    for k,v in fixed.items():
        m=v['mean'];print(k,round(m['accuracy'],4),round(m['changed_fact_accuracy'],4),round(m['avg_activated'],2),round(m['ops_per_correct'],1))

if __name__=='__main__':main()
