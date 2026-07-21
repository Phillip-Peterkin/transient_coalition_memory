import os, sys, json, math, argparse, csv
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import World, Method, Majority, StaticBayes, DynamicBayes, EWMA, ProvGraph, run as run_v4, score, ece, EPS, sigmoid


def stable_hash(parts, seed=0):
    # deterministic 64-bit FNV-like hash, independent of Python hash randomization
    h=(1469598103934665603 ^ seed) & ((1<<64)-1)
    for p in parts:
        b=str(p).encode('utf-8')
        for x in b:
            h ^= x; h=(h*1099511628211)&((1<<64)-1)
        h ^= 255; h=(h*1099511628211)&((1<<64)-1)
    return h

_ADDR_CACHE={}
def addresses(parts, n_cells, fanout, salt):
    key=(parts,n_cells,fanout,salt)
    if key in _ADDR_CACHE: return _ADDR_CACHE[key]
    out=[]
    for j in range(fanout):
        h=stable_hash(parts, salt+104729*j)
        idx=h % n_cells
        sign=1.0 if ((h>>17)&1) else -1.0
        out.append((int(idx),sign))
    _ADDR_CACHE[key]=out
    return out

class CellularAddressed(Method):
    name='cellular_addressed'
    def __init__(self, lr=.16, fast_decay=.90, slow_decay=.996, source_decay=.996,
                 n_claim_cells=4096,n_path_cells=8192,claim_fanout=11,path_fanout=9,
                 min_k=4,margin=1.0,claim_fast=.95,claim_slow=.28,path=.38,source=.16,
                 direct=.20,error_gain=1.0,anti_credit=.45):
        self.lr=lr; self.fd=fast_decay; self.sd=slow_decay; self.srd=source_decay
        self.ncc=n_claim_cells; self.npc=n_path_cells; self.cfout=claim_fanout; self.pfout=path_fanout
        self.min_k=min_k; self.margin=margin; self.wcf=claim_fast; self.wcs=claim_slow; self.wp=path; self.ws=source
        self.direct=direct; self.error_gain=error_gain; self.anti=anti_credit
        self.cf=np.zeros(n_claim_cells,dtype=np.float64); self.cs=np.zeros(n_claim_cells,dtype=np.float64)
        self.pw=np.zeros(n_path_cells,dtype=np.float64); self.src=defaultdict(float)
        self.ops=0;self.up=0;self.trace_id=0;self.touched_c=set();self.touched_p=set()
    def _read(self, arr, ads):
        return sum(sign*arr[idx] for idx,sign in ads)/math.sqrt(len(ads))
    def _write(self, arr, ads, delta, touched):
        d=delta/math.sqrt(len(ads))
        for idx,sign in ads:
            arr[idx]+=sign*d; touched.add(idx)
    def predict(self,key,reports,t):
        contrib=[]
        for s,c,y in reports:
            sg=1 if y else -1
            ca=addresses(('claim',key,y),self.ncc,self.cfout,31)
            pa=addresses(('path',s,c,key,y),self.npc,self.pfout,73)
            claim=self.wcf*self._read(self.cf,ca)+self.wcs*self._read(self.cs,ca)
            path=self.wp*self._read(self.pw,pa)
            src=self.ws*self.src[(s,c)]
            v=sg*(self.direct+claim+path+src)
            contrib.append((abs(v),v,s,c,y,ca,pa))
        # begin broad, then stop only once a coherent margin is achieved
        contrib.sort(key=lambda x:x[0],reverse=True)
        active=[]; pos=neg=0.0
        for row in contrib:
            active.append(row)
            if row[1]>=0: pos+=abs(row[1])
            else: neg+=abs(row[1])
            if len(active)>=self.min_k and abs(pos-neg)>=self.margin: break
        z=sum(r[1] for r in active)
        contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        z*=max(.50,1-.35*contradiction)
        self.trace_id+=1
        self.ops += len(reports)*(self.cfout*2+self.pfout+2)+len(active)
        trace={'id':self.trace_id,'key':key,'z':z,'p':sigmoid(z),'active':[
            {'s':s,'c':c,'y':y,'v':v,'ca':ca,'pa':pa} for _,v,s,c,y,ca,pa in active]}
        return sigmoid(z),trace
    def feedback(self,e):
        tr=e['trace']; truth=e['truth']; target=1.0 if truth else 0.0
        pred=tr['p']; err=(target-pred)*self.error_gain
        # Exact delayed credit: directionally score each saved contribution against outcome.
        # A contributor is rewarded only when its signed influence supported truth; otherwise punished.
        active=tr['active']; raw=[]
        for a in active:
            correct_dir=1.0 if a['y']==truth else -1.0
            causal_mag=abs(a['v'])/(sum(abs(x['v']) for x in active)+EPS)
            # error drives correction; anti-credit ensures confidently wrong paths are actively erased
            delta=self.lr*(err*correct_dir*causal_mag + self.anti*correct_dir*causal_mag*abs(err))
            raw.append((a,delta))
        # Claim cells have fast and slow channels; update only addressed cells saved at prediction time.
        for a,delta in raw:
            self._write(self.cf,a['ca'],delta,self.touched_c)
            self._write(self.cs,a['ca'],.12*delta,self.touched_c)
            self._write(self.pw,a['pa'],.75*delta,self.touched_p)
            sk=(a['s'],a['c']); self.src[sk]=self.srd*self.src[sk]+.10*delta
            self.up += self.cfout*2+self.pfout+1
        # Outcome anchor is also distributed, but weaker than path-specific counterfactual credit.
        tca=addresses(('claim',e['key'],truth),self.ncc,self.cfout,31)
        fca=addresses(('claim',e['key'],1-truth),self.ncc,self.cfout,31)
        anchor=self.lr*.32*max(.15,abs(err))
        self._write(self.cf,tca,anchor,self.touched_c); self._write(self.cf,fca,-anchor,self.touched_c)
        self._write(self.cs,tca,.08*anchor,self.touched_c); self._write(self.cs,fca,-.08*anchor,self.touched_c)
        self.up += self.cfout*4
        # Lazy global decay only on touched cells keeps updates local but prevents lock-in.
        for a,_ in raw:
            for idx,_ in a['ca']:
                self.cf[idx]*=self.fd; self.cs[idx]*=self.sd
            for idx,_ in a['pa']: self.pw[idx]*=self.fd
    def stats(self):
        return {'memory_states':len(self.touched_c)+len(self.touched_p)+len(self.src),
                'updates':self.up,'active_ops':self.ops}

class CellularNoAddress(CellularAddressed):
    name='cellular_no_address'
    def feedback(self,e):
        # Ablation: remove exact path update, keep distributed claim/source learning.
        tr=e['trace']; truth=e['truth']; target=1.0 if truth else 0.0; err=(target-tr['p'])*self.error_gain
        active=tr['active']; den=sum(abs(x['v']) for x in active)+EPS
        for a in active:
            correct=1.0 if a['y']==truth else -1.0; mag=abs(a['v'])/den
            delta=self.lr*(err*correct*mag+self.anti*correct*mag*abs(err))
            self._write(self.cf,a['ca'],delta,self.touched_c);self._write(self.cs,a['ca'],.12*delta,self.touched_c)
            sk=(a['s'],a['c']);self.src[sk]=self.srd*self.src[sk]+.10*delta
            self.up+=self.cfout*2+1
        tca=addresses(('claim',e['key'],truth),self.ncc,self.cfout,31);fca=addresses(('claim',e['key'],1-truth),self.ncc,self.cfout,31)
        anchor=self.lr*.32*max(.15,abs(err));self._write(self.cf,tca,anchor,self.touched_c);self._write(self.cf,fca,-anchor,self.touched_c)
        self.up+=self.cfout*2

METHODS={
'majority':(Majority,{'window':[1,3,7]}),
'bayes_source':(StaticBayes,{'alpha':[1.5,2.0,4.0]}),
'dynamic_bayes':(DynamicBayes,{'forget':[.94,.97,.985,.995]}),
'ewma_evidence':(EWMA,{'lr':[.04,.08,.15],'decay':[.90,.96,.99]}),
'provenance_graph':(ProvGraph,{'lr':[.06,.12,.2],'decay':[.94,.98,.995],'claim':[.2,.5,.9]}),
'cellular_addressed':(CellularAddressed,{
    'lr':[.10,.16,.24],'fast_decay':[.86,.92,.97],'min_k':[3,5,7],'margin':[.65,1.1,1.6],
    'path':[.22,.42,.7],'claim_fast':[.7,1.0],'source':[.08,.18],'anti_credit':[.2,.5,.8]})}

def combos(grid):
    import itertools
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
    cls,grid=METHODS[name];cs=list(combos(grid))
    if max_configs and len(cs)>max_configs:
        rng=np.random.default_rng(555);inds=rng.choice(len(cs),max_configs,replace=False);cs=[cs[i] for i in inds]
    best=None
    for p in cs:
        rs=[run(s,cls,p) for s in seeds];avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]};sc=score(avg)
        if best is None or sc>best[0]:best=(sc,p,avg)
    return best

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='/mnt/data/wave5');ap.add_argument('--dev',type=int,default=4);ap.add_argument('--test',type=int,default=10);a=ap.parse_args();os.makedirs(a.out,exist_ok=True)
    dev=list(range(5100,5100+a.dev));test=list(range(7100,7100+a.test));tuned={};results={}
    for name in METHODS:
        mx=12 if name=='cellular_addressed' else (12 if name=='provenance_graph' else None)
        b=tune(name,dev,mx);tuned[name]={'score':b[0],'params':b[1],'dev':b[2]};print('tuned',name,b[1],round(b[0],4),flush=True)
    for name,(cls,_) in METHODS.items():
        rs=[run(s,cls,tuned[name]['params']) for s in test];avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]};sd={k:float(np.std([r[k] for r in rs],ddof=1)) for k in rs[0]}
        results[name]={'mean':avg,'sd':sd,'runs':rs,'params':tuned[name]['params']};print('test',name,round(avg['accuracy'],4),round(avg['changed_fact_accuracy'],4),round(avg['brier'],4),round(avg['ops_per_correct'],1),flush=True)
    # exact address ablation on tuned params
    p=tuned['cellular_addressed']['params'];abl={}
    for label,cls in [('full',CellularAddressed),('no_exact_path',CellularNoAddress)]:
        rs=[run(s,cls,p) for s in test];abl[label]={'mean':{k:float(np.mean([r[k] for r in rs])) for k in rs[0]},'runs':rs}
    payload={'design':{'dev_seeds':dev,'test_seeds':test,'temporary_address':'prediction-time saved distributed cell addresses with delayed directional credit'},'tuning':tuned,'results':results,'ablations':abl}
    with open(os.path.join(a.out,'results.json'),'w') as f:json.dump(payload,f,indent=2)
    fields=['method','accuracy','post_change_accuracy','changed_fact_accuracy','brier','ece','false_certainty','memory_states','updates','active_ops','ops_per_correct']
    with open(os.path.join(a.out,'summary.csv'),'w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader()
        for n,v in results.items():wr.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    print('ablation', {k:round(v['mean']['changed_fact_accuracy'],4) for k,v in abl.items()},flush=True)
if __name__=='__main__':main()
