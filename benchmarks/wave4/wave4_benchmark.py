import argparse, json, math, os, time
from collections import defaultdict, deque
import numpy as np

EPS=1e-9

def sigmoid(x):
    return 1/(1+math.exp(-max(-40,min(40,x))))

def logit(p):
    p=min(1-EPS,max(EPS,p)); return math.log(p/(1-p))

class World:
    def __init__(self, seed, T=420, n_items=48, n_sources=12, n_contexts=3):
        self.rng=np.random.default_rng(seed); self.T=T; self.I=n_items; self.S=n_sources; self.C=n_contexts
        self.context=self.rng.integers(0,n_contexts,size=(T,n_items))
        base=self.rng.integers(0,2,size=(n_items,n_contexts))
        self.truth=np.zeros((T,n_items),dtype=np.int8); self.change_t=T//2
        late=base.copy(); flip=self.rng.random((n_items,n_contexts))<0.32; late[flip]=1-late[flip]
        for t in range(T):
            cur=base if t<self.change_t else late
            self.truth[t]=cur[np.arange(n_items),self.context[t]]
        # source reliability is context-specific and reverses for 1/3 of sources
        early=self.rng.uniform(.58,.91,size=(n_sources,n_contexts)); late_rel=early.copy()
        rev=self.rng.choice(n_sources,size=n_sources//3,replace=False)
        late_rel[rev]=np.clip(1.46-early[rev],.51,.90)
        # specialists: strong one context, middling elsewhere
        for s in range(n_sources//3):
            c=s%n_contexts; early[s,:]=.58; early[s,c]=.92; late_rel[s,:]=.58; late_rel[s,c]=.92
        self.rel_early=early; self.rel_late=late_rel; self.rev=set(map(int,rev))
        self.delays=self.rng.integers(4,19,size=(T,n_items))
        self.feedback_mask=self.rng.random((T,n_items))<.58
    def reports(self,t,i):
        c=int(self.context[t,i]); truth=int(self.truth[t,i]); rel=self.rel_early if t<self.change_t else self.rel_late
        out=[]
        old_truth=int(self.truth[self.change_t-1,i])
        changed=(t>=self.change_t and truth!=old_truth)
        for s in range(self.S):
            # adversarial stale persistence after change for reversed sources
            if changed and s in self.rev and self.rng.random()<.68:
                y=old_truth
            else:
                y=truth if self.rng.random()<rel[s,c] else 1-truth
            out.append((s,c,int(y)))
        return out

class Method:
    name='base'
    def predict(self,key,reports,t): raise NotImplementedError
    def feedback(self,event): pass
    def stats(self): return {'memory_states':0,'updates':0,'active_ops':0}

class Majority(Method):
    name='majority'
    def __init__(self,window=3): self.window=window; self.hist=defaultdict(lambda:deque(maxlen=window)); self.ops=0
    def predict(self,key,reports,t):
        vals=[y for _,_,y in reports]; self.hist[key].append(sum(vals)/len(vals)); self.ops+=len(vals)
        p=float(np.mean(self.hist[key])); return p, {'used':len(vals)}
    def stats(self): return {'memory_states':sum(len(v) for v in self.hist.values()),'updates':0,'active_ops':self.ops}

class StaticBayes(Method):
    name='bayes_source'
    def __init__(self,alpha=2.0): self.a=defaultdict(lambda:alpha); self.b=defaultdict(lambda:alpha); self.ops=0; self.up=0
    def predict(self,key,reports,t):
        z=0
        for s,c,y in reports:
            r=self.a[(s,c)]/(self.a[(s,c)]+self.b[(s,c)])
            z+=(1 if y else -1)*logit(max(.501,r)); self.ops+=1
        return sigmoid(z), {'contributors':[(s,c,y) for s,c,y in reports]}
    def feedback(self,e):
        for s,c,y in e['reports']:
            if y==e['truth']: self.a[(s,c)]+=1
            else:self.b[(s,c)]+=1
            self.up+=1
    def stats(self): return {'memory_states':2*len(self.a),'updates':self.up,'active_ops':self.ops}

class DynamicBayes(Method):
    name='dynamic_bayes'
    def __init__(self,forget=.985,alpha=2.0): self.f=forget; self.a=defaultdict(lambda:alpha); self.b=defaultdict(lambda:alpha); self.ops=0; self.up=0
    def predict(self,key,reports,t):
        z=0
        for s,c,y in reports:
            r=self.a[(s,c)]/(self.a[(s,c)]+self.b[(s,c)])
            z+=(1 if y else -1)*logit(max(.501,r)); self.ops+=1
        return sigmoid(z), {'contributors':reports}
    def feedback(self,e):
        touched={(s,c) for s,c,_ in e['reports']}
        for k in touched: self.a[k]=2+(self.a[k]-2)*self.f; self.b[k]=2+(self.b[k]-2)*self.f
        for s,c,y in e['reports']:
            if y==e['truth']: self.a[(s,c)]+=1
            else:self.b[(s,c)]+=1
            self.up+=1
    def stats(self): return {'memory_states':2*len(self.a),'updates':self.up,'active_ops':self.ops}

class EWMA(Method):
    name='ewma_evidence'
    def __init__(self,lr=.08,decay=.96): self.lr=lr; self.decay=decay; self.w=defaultdict(float); self.ops=0; self.up=0
    def predict(self,key,reports,t):
        z=0
        for s,c,y in reports: z+=(1 if y else -1)*self.w[(s,c)]; self.ops+=1
        return sigmoid(z), {'contributors':reports}
    def feedback(self,e):
        target=1 if e['truth'] else -1
        for s,c,y in e['reports']:
            k=(s,c); self.w[k]*=self.decay; self.w[k]+=self.lr*target*(1 if y else -1); self.up+=1
    def stats(self): return {'memory_states':len(self.w),'updates':self.up,'active_ops':self.ops}

class ProvGraph(Method):
    name='provenance_graph'
    def __init__(self,lr=.12,decay=.985,claim=.35): self.lr=lr; self.decay=decay; self.claim=claim; self.sw=defaultdict(float); self.cw=defaultdict(float); self.ops=0; self.up=0
    def predict(self,key,reports,t):
        z=self.claim*self.cw[key]
        for s,c,y in reports: z+=(1 if y else -1)*self.sw[(s,c)]; self.ops+=2
        return sigmoid(z), {'contributors':reports,'key':key}
    def feedback(self,e):
        target=1 if e['truth'] else -1; k=e['key']; self.cw[k]=self.decay*self.cw[k]+self.lr*target
        for s,c,y in e['reports']:
            sk=(s,c); self.sw[sk]=self.decay*self.sw[sk]+self.lr*target*(1 if y else -1); self.up+=1
    def stats(self): return {'memory_states':len(self.sw)+len(self.cw),'updates':self.up,'active_ops':self.ops}

class Cellular(Method):
    name='cellular_causal'
    def __init__(self,lr=.16,decay=.94,topk=5,path=.65,claim=.55,source=.22,context_split=True):
        self.lr=lr;self.decay=decay;self.topk=topk;self.path=path;self.claim=claim;self.source=source;self.context_split=context_split
        self.src=defaultdict(float); self.clm=defaultdict(float); self.pathw=defaultdict(float); self.fast=defaultdict(float)
        self.ops=0;self.up=0;self.trace_id=0
    def predict(self,key,reports,t):
        # Local cells form candidate coalitions. Select only strongest contributors.
        scores=[]
        for s,c,y in reports:
            ck=(key,y); pk=(s,c,key,y)
            val=(1 if y else -1)*(self.source*self.src[(s,c)] + self.claim*self.clm[ck] + self.path*self.pathw[pk])
            # unlearned cells still contribute weak direct evidence
            val += (1 if y else -1)*0.12
            scores.append((abs(val),val,s,c,y,pk,ck))
        scores.sort(reverse=True); active=scores[:self.topk]
        z=sum(v for _,v,*_ in active)
        # contradiction pressure lowers certainty rather than forcing erasure
        pos=sum(abs(v) for _,v,*_ in active if v>0); neg=sum(abs(v) for _,v,*_ in active if v<0)
        contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        z*=max(.35,1-.55*contradiction)
        self.ops+=len(reports)+len(active)*3
        trace={'active':[(s,c,y,pk,ck,abs(v)) for _,v,s,c,y,pk,ck in active], 'key':key,'contradiction':contradiction}
        return sigmoid(z),trace
    def feedback(self,e):
        target=1 if e['truth'] else -1
        active=e['trace']['active']; norm=sum(a[-1] for a in active)+EPS
        # exact causal credit through eligibility strength
        for s,c,y,pk,ck,strength in active:
            sign=1 if y==e['truth'] else -1; elig=strength/norm
            self.pathw[pk]=self.decay*self.pathw[pk]+self.lr*sign*elig
            self.clm[ck]=self.decay*self.clm[ck]+self.lr*sign*elig
            self.src[(s,c)]=.995*self.src[(s,c)]+self.lr*.22*sign*elig
            self.up+=3
        # direct claim outcome dominates source reputation
        true_ck=(e['key'],e['truth']); false_ck=(e['key'],1-e['truth'])
        self.clm[true_ck]+=self.lr*.45; self.clm[false_ck]-=self.lr*.45
        self.up+=2
    def stats(self): return {'memory_states':len(self.src)+len(self.clm)+len(self.pathw),'updates':self.up,'active_ops':self.ops}

METHODS={
'majority':(Majority,{'window':[1,3,7]}),
'bayes_source':(StaticBayes,{'alpha':[1.5,2.0,4.0]}),
'dynamic_bayes':(DynamicBayes,{'forget':[.94,.97,.985,.995]}),
'ewma_evidence':(EWMA,{'lr':[.04,.08,.15],'decay':[.90,.96,.99]}),
'provenance_graph':(ProvGraph,{'lr':[.06,.12,.2],'decay':[.94,.98,.995],'claim':[.2,.5,.9]}),
'cellular_causal':(Cellular,{'lr':[.08,.16,.25],'decay':[.90,.95,.98],'topk':[3,5,8],'path':[.4,.7,1.0],'claim':[.35,.65],'source':[.1,.25]})}

def combos(grid):
    import itertools
    keys=list(grid)
    for vals in itertools.product(*[grid[k] for k in keys]): yield dict(zip(keys,vals))

def ece(probs,ys,bins=10):
    probs=np.asarray(probs); ys=np.asarray(ys); out=0
    for lo in np.linspace(0,1,bins,endpoint=False):
        hi=lo+1/bins; m=(probs>=lo)&(probs<(hi if hi<1 else 1.0001))
        if m.any(): out+=m.mean()*abs(probs[m].mean()-ys[m].mean())
    return float(out)

def run(seed, cls, params):
    w=World(seed); m=cls(**params); queue=defaultdict(list); P=[];Y=[];changed=[];post=[];falsecertain=[]
    for t in range(w.T):
        for ev in queue.pop(t,[]): m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]); key=(i,c); reps=w.reports(t,i); p,tr=m.predict(key,reps,t); y=int(w.truth[t,i])
            P.append(p);Y.append(y); post.append(t>=w.change_t); changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i])
            falsecertain.append((p>.9 and y==0) or (p<.1 and y==1))
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i]);
                if due<w.T: queue[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr})
    P=np.array(P);Y=np.array(Y); changed=np.array(changed);post=np.array(post)
    pred=(P>=.5).astype(int); acc=(pred==Y)
    st=m.stats();
    return {'accuracy':float(acc.mean()),'post_change_accuracy':float(acc[post].mean()),'changed_fact_accuracy':float(acc[changed].mean()),
            'brier':float(np.mean((P-Y)**2)),'ece':ece(P,Y),'false_certainty':float(np.mean(falsecertain)),
            'memory_states':st['memory_states'],'updates':st['updates'],'active_ops':st['active_ops'],
            'ops_per_correct':float(st['active_ops']/max(1,acc.sum()))}

def score(r):
    return r['changed_fact_accuracy'] + .35*r['post_change_accuracy'] + .2*r['accuracy'] - .35*r['brier'] - .2*r['false_certainty']

def tune(name,seeds,max_configs=None):
    cls,grid=METHODS[name]; cs=list(combos(grid));
    # deterministic thinning for large cellular grid
    if max_configs and len(cs)>max_configs:
        rng=np.random.default_rng(123); cs=[cs[i] for i in rng.choice(len(cs),max_configs,replace=False)]
    best=None
    for j,p in enumerate(cs):
        rs=[run(s,cls,p) for s in seeds]; avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]}
        sc=score(avg)
        if best is None or sc>best[0]: best=(sc,p,avg)
    return best

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='/mnt/data/wave4');ap.add_argument('--dev',type=int,default=4);ap.add_argument('--test',type=int,default=8)
    a=ap.parse_args();os.makedirs(a.out,exist_ok=True)
    devseeds=list(range(1100,1100+a.dev)); testseeds=list(range(3100,3100+a.test))
    tuned={}; results={}
    for name in METHODS:
        mx=36 if name=='cellular_causal' else (24 if name=='provenance_graph' else None)
        b=tune(name,devseeds,mx); tuned[name]={'score':b[0],'params':b[1],'dev':b[2]}; print('tuned',name,b[1],round(b[0],4),flush=True)
    for name,(cls,_) in METHODS.items():
        rs=[run(s,cls,tuned[name]['params']) for s in testseeds]
        avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]}; sd={k:float(np.std([r[k] for r in rs],ddof=1)) for k in rs[0]}
        results[name]={'mean':avg,'sd':sd,'runs':rs,'params':tuned[name]['params']}; print('test',name,round(avg['accuracy'],3),round(avg['changed_fact_accuracy'],3),round(avg['brier'],3),flush=True)
    payload={'design':{'dev_seeds':devseeds,'test_seeds':testseeds,'T':420,'items':48,'sources':12,'contexts':3,'feedback_rate':.58,'change_fraction':.32},'tuning':tuned,'results':results}
    with open(os.path.join(a.out,'results.json'),'w') as f:json.dump(payload,f,indent=2)
    # csv
    import csv
    fields=['method','accuracy','post_change_accuracy','changed_fact_accuracy','brier','ece','false_certainty','memory_states','updates','active_ops','ops_per_correct']
    with open(os.path.join(a.out,'summary.csv'),'w',newline='') as f:
        wri=csv.DictWriter(f,fieldnames=fields);wri.writeheader()
        for n,v in results.items(): wri.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    print(os.path.join(a.out,'results.json'))
if __name__=='__main__':main()

class CellularAdaptive(Method):
    name='cellular_adaptive'
    def __init__(self,lr=.2,fast_decay=.88,slow_decay=.995,min_k=4,margin=1.2,path=.35,claim_fast=.9,claim_slow=.25,source=.18):
        self.lr=lr;self.fd=fast_decay;self.sd=slow_decay;self.min_k=min_k;self.margin=margin
        self.path=path;self.cf=claim_fast;self.cs=claim_slow;self.source=source
        self.src=defaultdict(float);self.fast=defaultdict(float);self.slow=defaultdict(float);self.pathw=defaultdict(float)
        self.ops=0;self.up=0
    def predict(self,key,reports,t):
        contrib=[]
        for s,c,y in reports:
            sign=1 if y else -1; ck=(key,y); pk=(s,c,key,y)
            v=sign*(.28 + self.source*self.src[(s,c)] + self.cf*self.fast[ck] + self.cs*self.slow[ck] + self.path*self.pathw[pk])
            contrib.append((abs(v),v,s,c,y,pk,ck))
        contrib.sort(reverse=True)
        active=[]; z=0.0
        for row in contrib:
            active.append(row);z+=row[1]
            pos=sum(abs(r[1]) for r in active if r[1]>0);neg=sum(abs(r[1]) for r in active if r[1]<0)
            if len(active)>=self.min_k and abs(pos-neg)>=self.margin: break
        pos=sum(abs(r[1]) for r in active if r[1]>0);neg=sum(abs(r[1]) for r in active if r[1]<0)
        contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        z*=max(.45,1-.4*contradiction)
        self.ops+=len(reports)+len(active)*2
        return sigmoid(z),{'active':[(s,c,y,pk,ck,abs(v)) for _,v,s,c,y,pk,ck in active],'key':key}
    def feedback(self,e):
        truth=e['truth']; active=e['trace']['active']; norm=sum(x[-1] for x in active)+EPS
        # Claim-specific outcome is strongest and has two time scales.
        tck=(e['key'],truth); fck=(e['key'],1-truth)
        for ck in [tck,fck]:
            self.fast[ck]*=self.fd; self.slow[ck]*=self.sd
        self.fast[tck]+=self.lr;self.fast[fck]-=self.lr
        self.slow[tck]+=self.lr*.15;self.slow[fck]-=self.lr*.15;self.up+=4
        for s,c,y,pk,ck,strength in active:
            good=1 if y==truth else -1; elig=strength/norm
            self.pathw[pk]=self.fd*self.pathw[pk]+self.lr*.55*good*elig
            self.src[(s,c)]=self.sd*self.src[(s,c)]+self.lr*.12*good*elig
            self.up+=2
    def stats(self):return {'memory_states':len(self.src)+len(self.fast)+len(self.slow)+len(self.pathw),'updates':self.up,'active_ops':self.ops}
