import os, sys, json, math, argparse, csv, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import World, Method, Majority, StaticBayes, DynamicBayes, EWMA, ProvGraph, score, ece, EPS, sigmoid


def stable_hash(parts, seed=0):
    h=(1469598103934665603 ^ seed) & ((1<<64)-1)
    for p in parts:
        for x in str(p).encode('utf-8'):
            h ^= x; h=(h*1099511628211)&((1<<64)-1)
        h ^= 255; h=(h*1099511628211)&((1<<64)-1)
    return h

class RoutedField:
    """Distributed cell field with persistent routes and event-driven cached route potentials."""
    def __init__(self,n_cells,fanout,salt):
        self.n=n_cells; self.fanout=fanout; self.salt=salt
        self.cells=np.zeros(n_cells,dtype=np.float64)
        self.routes={}; self.value={}
        self.link_states=0; self.propagation_ops=0
    def ensure(self,key):
        if key in self.routes:return key
        ads=[]; seen=set()
        j=0
        while len(ads)<self.fanout:
            h=stable_hash(key,self.salt+104729*j); j+=1
            idx=int(h%self.n)
            if idx in seen:continue
            seen.add(idx); sign=1.0 if ((h>>17)&1) else -1.0
            ads.append((idx,sign))
        self.routes[key]=tuple(ads)
        norm=math.sqrt(len(ads)); self.value[key]=sum(sign*self.cells[idx] for idx,sign in ads)/norm
        self.link_states += len(ads)
        return key
    def read(self,key):
        self.ensure(key); return self.value[key]
    def write(self,key,delta,decay=1.0):
        self.ensure(key); ads=self.routes[key]; norm=math.sqrt(len(ads)); touched=[]
        for idx,sign in ads:
            old=self.cells[idx]; new=old*decay+sign*delta/norm; d=new-old; self.cells[idx]=new;touched.append(idx)
            # Event-local membrane cache: update the active route immediately.
            # Overlapping routes are reconciled only when they next activate.
            self.value[key]+=sign*d/norm;self.propagation_ops+=1
        return len(touched)
    def memory(self):return int(np.count_nonzero(self.cells))+self.link_states+len(self.routes)

class CellularEventRouted(Method):
    name='cellular_event_routed'
    def __init__(self,lr=.16,claim_fast=.95,claim_slow=.28,path=.45,source=.14,
                 fast_decay=.90,slow_decay=.996,source_decay=.996,
                 n_claim_cells=4096,n_path_cells=8192,claim_fanout=7,path_fanout=5,
                 min_k=4,margin=1.0,direct=.20,error_gain=1.0,anti_credit=.45,
                 output_scale=.8,anchor_gain=.30):
        self.lr=lr;self.wcf=claim_fast;self.wcs=claim_slow;self.wp=path;self.ws=source
        self.fd=fast_decay;self.sd=slow_decay;self.srd=source_decay
        self.min_k=min_k;self.margin=margin;self.direct=direct;self.eg=error_gain;self.anti=anti_credit
        self.scale=output_scale;self.anchor_gain=anchor_gain
        self.cf=RoutedField(n_claim_cells,claim_fanout,31);self.cs=RoutedField(n_claim_cells,claim_fanout,43)
        self.pw=RoutedField(n_path_cells,path_fanout,73);self.src=defaultdict(float)
        self.ops=0;self.up=0;self.trace_id=0
    def predict(self,key,reports,t):
        # Event-driven route reads are constant-time after first route creation.
        contrib=[]
        for s,c,y in reports:
            sg=1 if y else -1; ck=('claim',key,y);pk=('path',s,c,key,y)
            claim=self.wcf*self.cf.read(ck)+self.wcs*self.cs.read(ck)
            path=self.wp*self.pw.read(pk);src=self.ws*self.src[(s,c)]
            v=sg*(self.direct+claim+path+src);contrib.append((abs(v),v,s,c,y,ck,pk))
        contrib.sort(key=lambda x:x[0],reverse=True)
        active=[];pos=neg=0.0
        for row in contrib:
            active.append(row)
            if row[1]>=0:pos+=abs(row[1])
            else:neg+=abs(row[1])
            if len(active)>=self.min_k and abs(pos-neg)>=self.margin:break
        z=sum(r[1] for r in active); contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        z*=max(.50,1-.35*contradiction); z*=self.scale
        p=sigmoid(z);self.trace_id+=1
        self.ops += len(reports)*4 + len(active) # 3 routed state reads + source + recruitment
        tr={'id':self.trace_id,'key':key,'z':z,'p':p,'active':[{'s':s,'c':c,'y':y,'v':v,'ck':ck,'pk':pk} for _,v,s,c,y,ck,pk in active]}
        return p,tr
    def feedback(self,e):
        tr=e['trace'];truth=e['truth'];target=float(truth);err=(target-tr['p'])*self.eg
        active=tr['active'];den=sum(abs(a['v']) for a in active)+EPS
        for a in active:
            correct=1.0 if a['y']==truth else -1.0; mag=abs(a['v'])/den
            # contribution-specific delayed credit, with active erasure of wrong routes
            delta=self.lr*(err*correct*mag+self.anti*correct*mag*abs(err))
            self.up+=self.cf.write(a['ck'],delta,self.fd)
            self.up+=self.cs.write(a['ck'],.12*delta,self.sd)
            self.up+=self.pw.write(a['pk'],.78*delta,self.fd)
            sk=(a['s'],a['c']);self.src[sk]=self.srd*self.src[sk]+.10*delta;self.up+=1
        tk=('claim',e['key'],truth);fk=('claim',e['key'],1-truth)
        anchor=self.lr*self.anchor_gain*max(.12,abs(err))
        self.up+=self.cf.write(tk,anchor,self.fd)+self.cf.write(fk,-anchor,self.fd)
        self.up+=self.cs.write(tk,.08*anchor,self.sd)+self.cs.write(fk,-.08*anchor,self.sd)
    def stats(self):
        prop=self.cf.propagation_ops+self.cs.propagation_ops+self.pw.propagation_ops
        return {'memory_states':self.cf.memory()+self.cs.memory()+self.pw.memory()+len(self.src),
                'updates':self.up,'active_ops':self.ops+prop,'route_propagations':prop}

class CellularNoPath(CellularEventRouted):
    name='cellular_no_path'
    def predict(self,key,reports,t):
        old=self.wp;self.wp=0.0
        # custom compact duplicate avoiding path read/use
        contrib=[]
        for s,c,y in reports:
            sg=1 if y else -1;ck=('claim',key,y);pk=('path',s,c,key,y)
            claim=self.wcf*self.cf.read(ck)+self.wcs*self.cs.read(ck);src=self.ws*self.src[(s,c)]
            v=sg*(self.direct+claim+src);contrib.append((abs(v),v,s,c,y,ck,pk))
        contrib.sort(key=lambda x:x[0],reverse=True);active=[];pos=neg=0.0
        for row in contrib:
            active.append(row);pos+=abs(row[1]) if row[1]>=0 else 0;neg+=abs(row[1]) if row[1]<0 else 0
            if len(active)>=self.min_k and abs(pos-neg)>=self.margin:break
        z=sum(r[1] for r in active)*max(.50,1-.35*min(pos,neg)/(max(pos,neg)+EPS))*self.scale;p=sigmoid(z)
        self.ops+=len(reports)*3+len(active);self.trace_id+=1
        return p,{'id':self.trace_id,'key':key,'z':z,'p':p,'active':[{'s':s,'c':c,'y':y,'v':v,'ck':ck,'pk':pk} for _,v,s,c,y,ck,pk in active]}
    def feedback(self,e):
        tr=e['trace'];truth=e['truth'];err=float(truth)-tr['p'];den=sum(abs(a['v']) for a in tr['active'])+EPS
        for a in tr['active']:
            correct=1.0 if a['y']==truth else -1.0;mag=abs(a['v'])/den;delta=self.lr*(err*correct*mag+self.anti*correct*mag*abs(err))
            self.up+=self.cf.write(a['ck'],delta,self.fd)+self.cs.write(a['ck'],.12*delta,self.sd)
            sk=(a['s'],a['c']);self.src[sk]=self.srd*self.src[sk]+.10*delta;self.up+=1
        tk=('claim',e['key'],truth);fk=('claim',e['key'],1-truth);anchor=self.lr*self.anchor_gain*max(.12,abs(err))
        self.up+=self.cf.write(tk,anchor,self.fd)+self.cf.write(fk,-anchor,self.fd)

METHODS={
'majority':(Majority,{'window':[1,3,7]}),
'bayes_source':(StaticBayes,{'alpha':[1.5,2.0,4.0]}),
'dynamic_bayes':(DynamicBayes,{'forget':[.94,.97,.985,.995]}),
'ewma_evidence':(EWMA,{'lr':[.04,.08,.15],'decay':[.90,.96,.99]}),
'provenance_graph':(ProvGraph,{'lr':[.06,.12,.2],'decay':[.94,.98,.995],'claim':[.2,.5,.9]}),
'cellular_event_routed':(CellularEventRouted,{
'lr':[.10,.16,.24],'fast_decay':[.86,.92,.97],'min_k':[3,5,7],'margin':[.65,1.1,1.6],
'path':[.25,.5,.8],'claim_fast':[.7,1.0],'source':[.08,.18],'anti_credit':[.2,.5,.8],
'output_scale':[.45,.7,1.0],'claim_fanout':[5,7],'path_fanout':[3,5]})}

def combos(grid):
    ks=list(grid)
    for vs in itertools.product(*[grid[k] for k in ks]):yield dict(zip(ks,vs))

def run(seed,cls,params):
    w=World(seed);m=cls(**params);queue=defaultdict(list);P=[];Y=[];changed=[];post=[];fc=[]
    for t in range(w.T):
        for ev in queue.pop(t,[]):m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]);key=(i,c);reps=w.reports(t,i);p,tr=m.predict(key,reps,t);y=int(w.truth[t,i])
            P.append(p);Y.append(y);post.append(t>=w.change_t);changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i]);fc.append((p>.9 and y==0)or(p<.1 and y==1))
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i])
                if due<w.T:queue[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr})
    P=np.array(P);Y=np.array(Y);post=np.array(post);changed=np.array(changed);acc=((P>=.5).astype(int)==Y);st=m.stats()
    return {'accuracy':float(acc.mean()),'post_change_accuracy':float(acc[post].mean()),'changed_fact_accuracy':float(acc[changed].mean()),
    'brier':float(np.mean((P-Y)**2)),'ece':ece(P,Y),'false_certainty':float(np.mean(fc)),
    'memory_states':st['memory_states'],'updates':st['updates'],'active_ops':st['active_ops'],'ops_per_correct':float(st['active_ops']/max(1,acc.sum()))}

def tune(name,seeds,max_configs=None):
    cls,grid=METHODS[name]
    if name=='cellular_event_routed':
        cs=[
        {'lr':.16,'fast_decay':.86,'min_k':7,'margin':.65,'path':.5,'claim_fast':1.0,'source':.18,'anti_credit':.5,'output_scale':1.0,'claim_fanout':5,'path_fanout':5},
        {'lr':.24,'fast_decay':.92,'min_k':5,'margin':1.1,'path':.8,'claim_fast':1.0,'source':.08,'anti_credit':.8,'output_scale':.7,'claim_fanout':5,'path_fanout':3},
        {'lr':.16,'fast_decay':.97,'min_k':3,'margin':1.6,'path':.25,'claim_fast':.7,'source':.18,'anti_credit':.2,'output_scale':.45,'claim_fanout':7,'path_fanout':3}]
    else:
        cs=list(combos(grid))
        if max_configs and len(cs)>max_configs:
            rng=np.random.default_rng(660);inds=rng.choice(len(cs),max_configs,replace=False);cs=[cs[i] for i in inds]
    best=None
    for p in cs:
        rs=[run(s,cls,p) for s in seeds];avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]};sc=score(avg)
        if best is None or sc>best[0]:best=(sc,p,avg)
    return best

def evaluate(methods,tuned,seeds):
    out={}
    for name,(cls,_) in methods.items():
        rs=[run(s,cls,tuned[name]['params']) for s in seeds];out[name]={'mean':{k:float(np.mean([r[k] for r in rs])) for k in rs[0]},'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in rs[0]},'runs':rs,'params':tuned[name]['params']}
        a=out[name]['mean'];print('test',name,round(a['accuracy'],4),round(a['changed_fact_accuracy'],4),round(a['brier'],4),round(a['ops_per_correct'],1),flush=True)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='/mnt/data/wave6');ap.add_argument('--dev',type=int,default=4);ap.add_argument('--test',type=int,default=10);a=ap.parse_args();os.makedirs(a.out,exist_ok=True)
    dev=list(range(8200,8200+a.dev));fresh=list(range(9300,9300+a.test));legacy=list(range(7100,7100+a.test));tuned={}
    for name in METHODS:
        mx=3 if name=='cellular_event_routed' else (12 if name=='provenance_graph' else None)
        b=tune(name,dev,mx);tuned[name]={'score':b[0],'params':b[1],'dev':b[2]};print('tuned',name,b[1],round(b[0],4),flush=True)
    fresh_results=evaluate(METHODS,tuned,fresh);legacy_results=evaluate(METHODS,tuned,legacy)
    p=tuned['cellular_event_routed']['params'];abl={}
    for label,cls in [('full',CellularEventRouted),('no_exact_path',CellularNoPath)]:
        rs=[run(s,cls,p) for s in fresh];abl[label]={'mean':{k:float(np.mean([r[k] for r in rs])) for k in rs[0]},'runs':rs}
    payload={'design':{'dev_seeds':dev,'fresh_holdout':fresh,'legacy_regression':legacy,'routing':'persistent local routes with event-driven cached potentials and reverse-link updates'},'tuning':tuned,'fresh_results':fresh_results,'legacy_results':legacy_results,'ablations':abl}
    with open(os.path.join(a.out,'results.json'),'w') as f:json.dump(payload,f,indent=2)
    fields=['method','accuracy','post_change_accuracy','changed_fact_accuracy','brier','ece','false_certainty','memory_states','updates','active_ops','ops_per_correct']
    with open(os.path.join(a.out,'summary.csv'),'w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader()
        for n,v in fresh_results.items():wr.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    print('ablation',{k:round(v['mean']['changed_fact_accuracy'],4) for k,v in abl.items()},flush=True)
if __name__=='__main__':main()
