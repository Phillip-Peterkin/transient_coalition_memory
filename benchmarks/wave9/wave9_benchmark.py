import os, sys, json, csv
from collections import defaultdict
import numpy as np
sys.path.insert(0,'/mnt/data/wave7')
from wave7_benchmark import EnergeticCellular, FixedKCellular
sys.path.insert(0,'/mnt/data/wave4')
from wave4_benchmark import World, DynamicBayes, EWMA, ProvGraph, EPS, sigmoid, ece

class CertifiedCellular(EnergeticCellular):
    name='certified_cellular'
    def __init__(self, min_k=1, max_k=8, cert_delta=.025, hazard_gain=4.0,
                 header_cost=.20, min_margin=.02, **kw):
        super().__init__(min_k=min_k,max_k=max_k,theta=1e9,**kw)
        self.cert_delta=cert_delta
        self.hazard_gain=hazard_gain
        self.header_cost=header_cost
        self.min_margin=min_margin
        self.last_fb=defaultdict(lambda:-10**9)
        self.preview_ops=0.0
        self.activation_ops=0.0

    def _rows(self,key,reports):
        rows=[]
        for s,c,y in reports:
            sg=1 if y else -1
            ck=(key,y)
            strength=self.direct+self.wf*self.cf[ck]+self.ws*self.cs[ck]+self.wsrc*self.src[(s,c)]
            v=sg*strength
            rows.append((abs(v),v,s,c,y,ck))
        rows.sort(key=lambda x:x[0], reverse=True)
        # cheap route-header inspection, explicitly counted separately
        self.preview_ops += self.header_cost*len(rows)
        return rows

    def _state(self, rows):
        z=sum(r[1] for r in rows)
        pos=sum(abs(r[1]) for r in rows if r[1]>=0)
        neg=sum(abs(r[1]) for r in rows if r[1]<0)
        contradiction=min(pos,neg)/(max(pos,neg)+EPS)
        effective=z*(1-self.cg*contradiction)
        return effective, contradiction

    def predict(self,key,reports,t):
        rows=self._rows(key,reports)[:self.max_k]
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
        stop_reason='budget'
        cert_shift=1.0

        for n,row in enumerate(rows):
            active.append(row)
            self.activation_ops += 1.0
            current_z,current_con=self._state(active)
            self.ops += 2
            if len(active)<required:
                continue
            remaining=rows[n+1:]
            if not remaining:
                stop_reason='exhausted'; cert_shift=0.0; break

            # Decision certificate: compare the current coalition with its full
            # strongest available completion. No truth is used.
            full_z,full_con=self._state(active+remaining)
            p_now=sigmoid(current_z/max(self.temp,EPS))
            p_full=sigmoid(full_z/max(self.temp,EPS))
            cert_shift=abs(p_now-p_full)
            same_decision=((current_z>=0)==(full_z>=0))

            # Also require that no single unrecruited opposing report can flip it.
            sign=1 if current_z>=0 else -1
            strongest_opp=max([abs(r[1]) for r in remaining if r[1]*sign<0] or [0.0])
            single_safe=abs(current_z)>strongest_opp
            margin_safe=abs(current_z)>=self.min_margin

            if same_decision and single_safe and margin_safe and cert_shift<=self.cert_delta:
                stop_reason='certified'; break

        final_z,contradiction=self._state(active)
        p=sigmoid(final_z/max(self.temp,EPS))
        trace={'key':key,'p':p,'active':[(s,c,y,ck,abs(v)) for _,v,s,c,y,ck in active],
               'used':len(active),'contradiction':contradiction,'hazard':hazard,
               'required':required,'certificate_shift':cert_shift,'stop_reason':stop_reason}
        return p,trace

    def feedback(self,e):
        super().feedback(e)
        self.last_fb[e['key']]=e.get('time',self.last_fb[e['key']])

    def stats(self):
        s=super().stats()
        s['preview_ops']=self.preview_ops
        s['activation_ops']=self.activation_ops
        s['active_ops']=self.preview_ops + self.activation_ops*4 + self.up
        return s


class ShadowCertifiedCellular(CertifiedCellular):
    name='shadow_certified_cellular'
    def __init__(self, shadow_scale=.45, **kw):
        super().__init__(**kw)
        self.shadow_scale=shadow_scale

    def predict(self,key,reports,t):
        p,tr=super().predict(key,reports,t)
        active_ids={(s,c,y,ck) for s,c,y,ck,_ in tr['active']}
        rows=self._rows(key,reports)[:self.max_k]
        tr['shadow']=[(s,c,y,ck,abs(v)) for _,v,s,c,y,ck in rows
                      if (s,c,y,ck) not in active_ids]
        return p,tr

    def feedback(self,e):
        super().feedback(e)
        tr=e['trace']; truth=e['truth']; err=float(truth)-tr['p']
        shadow=tr.get('shadow',[])
        den=sum(a[-1] for a in shadow)+EPS
        for s,c,y,ck,strength in shadow:
            correct=1.0 if y==truth else -1.0
            elig=strength/den
            delta=self.shadow_scale*self.lr*correct*elig*(.35+abs(err))
            self.cf[ck]=self.fd*self.cf[ck]+delta
            self.cs[ck]=self.sd*self.cs[ck]+.10*delta
            sk=(s,c); self.src[sk]=self.srd*self.src[sk]+.16*delta
            self.up+=3

def run(seed,cls,params):
    w=World(seed);m=cls(**params);q=defaultdict(list)
    P=[];Y=[];changed=[];post=[];fc=[];used=[];haz=[];reasons=defaultdict(int)
    for t in range(w.T):
        for ev in q.pop(t,[]):m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]);key=(i,c);reps=w.reports(t,i);p,tr=m.predict(key,reps,t);y=int(w.truth[t,i])
            P.append(p);Y.append(y);post.append(t>=w.change_t)
            changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i])
            fc.append((p>.9 and y==0)or(p<.1 and y==1));used.append(tr.get('used',len(reps)))
            haz.append(tr.get('hazard',0));reasons[tr.get('stop_reason','na')]+=1
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i])
                if due<w.T:q[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr,'time':due})
    P=np.array(P);Y=np.array(Y);post=np.array(post);changed=np.array(changed)
    acc=((P>=.5).astype(int)==Y);st=m.stats()
    return {'accuracy':float(acc.mean()),'post_change_accuracy':float(acc[post].mean()),
            'changed_fact_accuracy':float(acc[changed].mean()),'brier':float(np.mean((P-Y)**2)),
            'ece':ece(P,Y),'false_certainty':float(np.mean(fc)),'memory_states':st['memory_states'],
            'updates':st['updates'],'active_ops':st['active_ops'],'ops_per_correct':float(st['active_ops']/max(1,acc.sum())),
            'avg_activated':float(np.mean(used)),'p90_activated':float(np.percentile(used,90)),
            'avg_hazard':float(np.mean(haz)),'stop_reasons':dict(reasons)}

def aggregate(cls,p,seeds):
    rs=[run(s,cls,p) for s in seeds]
    keys=[k for k,v in rs[0].items() if isinstance(v,(int,float))]
    return {'mean':{k:float(np.mean([r[k] for r in rs])) for k in keys},
            'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in keys},'runs':rs,'params':p}

def objective(m):
    return 3.0*m['changed_fact_accuracy']+m['accuracy']-.30*m['brier']-.010*m['avg_activated']

def main():
    out='/mnt/data/wave9';os.makedirs(out,exist_ok=True)
    base={'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58,
          'min_k':1,'max_k':8,'header_cost':.20}
    dev=[14000]
    holdout=[14100,14101]
    candidates=[]
    for d,hg,mm in [(.02,3.0,.0),(.04,3.0,.03),(.04,4.5,.0),(.06,4.5,.03)]:
        p=base.copy();p.update({'cert_delta':d,'hazard_gain':hg,'min_margin':mm});candidates.append(p)
    best=None
    for p in candidates:
        a=aggregate(CertifiedCellular,p,dev);sc=objective(a['mean'])
        if best is None or sc>best[0]:best=(sc,p,a)
    pbest=best[1]
    sp=pbest.copy();sp['shadow_scale']=.45
    shadow_best=(0.0,sp,aggregate(ShadowCertifiedCellular,sp,dev))
    methods={
      'provenance_graph':(ProvGraph,{'lr':.12,'decay':.98,'claim':.5}),
      'fixed_k8_cellular':(FixedKCellular,{'k':8,'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58}),
      'certified_cellular':(CertifiedCellular,pbest),
      'shadow_certified_cellular':(ShadowCertifiedCellular,sp)
    }
    results={n:aggregate(c,p,holdout) for n,(c,p) in methods.items()}
    payload={'design':{'dev':dev,'fresh_holdout':holdout,'scope':'gating-only decision certificate',
                       'no_truth_in_gate':True,'preview_headers_counted':True},
             'best_params':pbest,'shadow_best_params':shadow_best[1],'dev_result':best[2],'shadow_dev_result':shadow_best[2],'results':results}
    with open(out+'/results.json','w') as f:json.dump(payload,f,indent=2)
    fields=['method','accuracy','changed_fact_accuracy','brier','ece','false_certainty','avg_activated','p90_activated','ops_per_correct','memory_states']
    with open(out+'/summary.csv','w',newline='') as f:
        wri=csv.DictWriter(f,fieldnames=fields);wri.writeheader()
        for n,v in results.items():wri.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
    print('best',pbest)
    for n,v in results.items():
        m=v['mean'];print(n,round(m['accuracy'],4),round(m['changed_fact_accuracy'],4),round(m['brier'],4),round(m['avg_activated'],2),round(m['p90_activated'],1),round(m['ops_per_correct'],1))

if __name__=='__main__':main()
