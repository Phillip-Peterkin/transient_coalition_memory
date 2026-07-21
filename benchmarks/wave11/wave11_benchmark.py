import os, sys, json, csv
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data')
sys.path.insert(0,'/mnt/data/wave10')
from wave10_benchmark import CompressedReserveCellular
sys.path.insert(0,'/mnt/data/wave7')
from wave7_benchmark import FixedKCellular
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import World, ProvGraph, EPS, sigmoid, ece

class BatchedReserveCellular(CompressedReserveCellular):
    name='exact_batched_reserve_cellular'
    def __init__(self, **kw):
        super().__init__(**kw)
        self.infer_reads=0.0
        self.learn_writes=0.0

    def predict(self,key,reports,t):
        p,tr=super().predict(key,reports,t)
        self.infer_reads += self.header_cost*len(reports) + tr['used']
        return p,tr

    @staticmethod
    def _closed_form(old, decay, deltas):
        # Exactly equals repeated: state = decay*state + delta
        n=len(deltas)
        if n==0: return old
        out=(decay**n)*old
        for j,d in enumerate(deltas):
            out += (decay**(n-1-j))*d
        return out

    def feedback(self,e):
        tr=e['trace']; truth=e['truth']; err=float(truth)-tr['p']
        self.last_fb[e['key']]=e.get('time',self.last_fb[e['key']])

        # Preserve the exact original update order, but solve each answer
        # coalition's repeated recurrence in closed form and write once.
        active_by_ck=defaultdict(list)
        source_by_sk=defaultdict(list)
        active=tr['active']; den=sum(a[-1] for a in active)+EPS
        for s,c,y,ck,strength in active:
            correct=1.0 if y==truth else -1.0
            elig=strength/den
            d=self.lr*correct*elig*(.35+abs(err))
            active_by_ck[ck].append(d)
            source_by_sk[(s,c)].append(.16*d)

        tk=(e['key'],truth); fk=(e['key'],1-truth)
        anchor=self.lr*self.anchor*(.25+abs(err))
        m0,m1=tr.get('shadow_mass',(0.0,0.0)); total=m0+m1
        reserve={}
        if total>EPS:
            for y,m in ((0,m0),(1,m1)):
                if m>EPS:
                    correct=1.0 if y==truth else -1.0
                    reserve[(e['key'],y)] = self.shadow_scale*self.lr*correct*(m/total)*(.35+abs(err))*self.reserve_claim_gain

        all_cks=set(active_by_ck)|{tk,fk}|set(reserve)
        for ck in all_cks:
            # Active sequence.
            cf=self._closed_form(self.cf[ck],self.fd,active_by_ck.get(ck,[]))
            cs=self._closed_form(self.cs[ck],self.sd,[.10*d for d in active_by_ck.get(ck,[])])
            # Original anchor sequence always touches true and false claims.
            ad = anchor if ck==tk else (-anchor if ck==fk else None)
            if ad is not None:
                cf=self.fd*cf+ad
                cs=self.sd*cs+.08*ad
            # Original reserve sequence follows anchor when present.
            if ck in reserve:
                rd=reserve[ck]
                cf=self.fd*cf+rd
                cs=self.sd*cs+.10*rd
            self.cf[ck]=cf; self.cs[ck]=cs
            self.learn_writes += 2

        # Active sources are generally unique, but preserve exact recurrence if not.
        for sk,deltas in source_by_sk.items():
            self.src[sk]=self._closed_form(self.src[sk],self.srd,deltas)
            self.learn_writes += 1

        self.up += 2*len(all_cks)+len(source_by_sk)

    def stats(self):
        s=super().stats()
        s['active_ops']=self.infer_reads+self.learn_writes
        s['inference_ops']=self.infer_reads
        s['learning_ops']=self.learn_writes
        return s

class FairProvGraph(ProvGraph):
    name='fair_provenance_graph'
    def __init__(self,**kw):
        super().__init__(**kw)
        self.infer_reads=0.0; self.learn_writes=0.0
    def predict(self,key,reports,t):
        p,tr=super().predict(key,reports,t)
        # one claim read plus one source read per report
        self.infer_reads += 1 + len(reports)
        return p,tr
    def feedback(self,e):
        super().feedback(e)
        # one claim write plus one source write per report
        self.learn_writes += 1 + len(e['reports'])
    def stats(self):
        s=super().stats(); s['active_ops']=self.infer_reads+self.learn_writes
        s['inference_ops']=self.infer_reads; s['learning_ops']=self.learn_writes
        return s

def run(seed,cls,params):
    w=World(seed);m=cls(**params);q=defaultdict(list)
    P=[];Y=[];changed=[];post=[];fc=[];used=[]
    for t in range(w.T):
        for ev in q.pop(t,[]): m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]); key=(i,c); reps=w.reports(t,i)
            p,tr=m.predict(key,reps,t); y=int(w.truth[t,i])
            P.append(p);Y.append(y);post.append(t>=w.change_t)
            changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i])
            fc.append((p>.9 and y==0) or (p<.1 and y==1)); used.append(tr.get('used',len(reps)))
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i])
                if due<w.T:q[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr,'time':due})
    P=np.asarray(P);Y=np.asarray(Y);post=np.asarray(post);changed=np.asarray(changed)
    acc=((P>=.5).astype(int)==Y); st=m.stats()
    out={'accuracy':float(acc.mean()),'post_change_accuracy':float(acc[post].mean()),
         'changed_fact_accuracy':float(acc[changed].mean()),'brier':float(np.mean((P-Y)**2)),
         'ece':ece(P,Y),'false_certainty':float(np.mean(fc)),'memory_states':st['memory_states'],
         'updates':st['updates'],'active_ops':st['active_ops'],
         'ops_per_correct':float(st['active_ops']/max(1,acc.sum())),
         'avg_activated':float(np.mean(used)),'p90_activated':float(np.percentile(used,90))}
    out['inference_ops_per_correct']=float(st.get('inference_ops',0)/max(1,acc.sum()))
    out['learning_ops_per_correct']=float(st.get('learning_ops',0)/max(1,acc.sum()))
    return out

def aggregate(cls,p,seeds):
    rs=[run(s,cls,p) for s in seeds]
    keys=[k for k,v in rs[0].items() if isinstance(v,(int,float))]
    return {'mean':{k:float(np.mean([r[k] for r in rs])) for k in keys},
            'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in keys},'runs':rs,'params':p}

def main():
    out='/mnt/data/wave11';os.makedirs(out,exist_ok=True)
    # Locked Wave X decision parameters.
    p={'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58,
       'min_k':1,'max_k':8,'header_cost':.08,'cert_delta':.08,'hazard_gain':3.0,'min_margin':0.0,
       'shadow_scale':.75,'reserve_claim_gain':1.2,'reserve_source_gain':0.0,'certify_slack':0.0}
    graph={'lr':.12,'decay':.98,'claim':.5}
    # Old Wave X seeds plus four never-used holdouts.
    regression=[15200,15201]
    fresh=[15300,15301,15302,15303]
    methods={'fair_provenance_graph':(FairProvGraph,graph),
             'batched_reserve_cellular':(BatchedReserveCellular,p)}
    results={n:{'regression':aggregate(c,pa,regression),'fresh':aggregate(c,pa,fresh)} for n,(c,pa) in methods.items()}
    payload={'design':{'scope':'feedback batching only','decision_policy_locked':True,
              'regression_seeds':regression,'fresh_holdout':fresh,
              'operation_accounting':'scalar evidence reads plus scalar state writes for every method'},
             'params':{'cellular':p,'graph':graph},'results':results}
    with open(out+'/results.json','w') as f:json.dump(payload,f,indent=2)
    fields=['split','method','accuracy','changed_fact_accuracy','brier','ece','false_certainty','avg_activated','p90_activated','ops_per_correct','inference_ops_per_correct','learning_ops_per_correct','memory_states']
    with open(out+'/summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for n,v in results.items():
            for split in ('regression','fresh'):
                m=v[split]['mean'];w.writerow({'split':split,'method':n,**{k:m[k] for k in fields[2:]}})
    for split in ('regression','fresh'):
        print('\n'+split.upper())
        for n,v in results.items():
            m=v[split]['mean'];print(n,'acc',round(m['accuracy'],4),'changed',round(m['changed_fact_accuracy'],4),
                'activated',round(m['avg_activated'],2),'ops/correct',round(m['ops_per_correct'],2),
                'infer',round(m['inference_ops_per_correct'],2),'learn',round(m['learning_ops_per_correct'],2))

if __name__=='__main__':main()
