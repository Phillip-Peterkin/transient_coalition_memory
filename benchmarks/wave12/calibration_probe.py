import os, sys, json, csv
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.optimize import minimize_scalar, minimize
from sklearn.isotonic import IsotonicRegression

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'benchmarks' / 'wave11'))
from wave11_benchmark import BatchedReserveCellular, FairProvGraph
sys.path.insert(0, str(REPO_ROOT / 'benchmarks' / 'wave4'))
from wave4_benchmark import World, EPS, ece

CELL_PARAMS={'lr':.22,'fast_decay':.90,'contradiction_gain':.85,'uncertainty_cost':.38,'temp':.95,'anchor':.58,
       'min_k':1,'max_k':8,'header_cost':.08,'cert_delta':.08,'hazard_gain':3.0,'min_margin':0.0,
       'shadow_scale':.75,'reserve_claim_gain':1.2,'reserve_source_gain':0.0,'certify_slack':0.0}
GRAPH_PARAMS={'lr':.12,'decay':.98,'claim':.5}

def collect(seed, cls, params):
    w=World(seed); m=cls(**params); q=defaultdict(list)
    P=[];Y=[];changed=[];post=[];fc=[];used=[]
    for t in range(w.T):
        for ev in q.pop(t,[]): m.feedback(ev)
        for i in range(w.I):
            c=int(w.context[t,i]); key=(i,c); reps=w.reports(t,i)
            p,tr=m.predict(key,reps,t); y=int(w.truth[t,i])
            P.append(float(p));Y.append(y);post.append(t>=w.change_t)
            changed.append(t>=w.change_t and w.truth[t,i]!=w.truth[w.change_t-1,i])
            used.append(tr.get('used',len(reps)))
            if w.feedback_mask[t,i]:
                due=t+int(w.delays[t,i])
                if due<w.T:q[due].append({'key':key,'reports':reps,'truth':y,'pred':p,'trace':tr,'time':due})
    return {'p':np.asarray(P,float),'y':np.asarray(Y,int),'changed':np.asarray(changed,bool),'post':np.asarray(post,bool),
            'used':np.asarray(used,float),'stats':m.stats()}

def clip(p): return np.clip(np.asarray(p,float),1e-8,1-1e-8)
def logit(p):
    p=clip(p); return np.log(p/(1-p))
def sig(x): return 1/(1+np.exp(-np.clip(x,-50,50)))
def nll(p,y):
    p=clip(p); y=np.asarray(y,float)
    return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))

def metrics(p,y,changed=None):
    p=clip(p); y=np.asarray(y,int); pred=(p>=.5).astype(int); acc=pred==y
    out={'accuracy':float(acc.mean()),'brier':float(np.mean((p-y)**2)),'ece':float(ece(p,y)),
         'nll':nll(p,y),'false_certainty':float(np.mean(((p>.9)&(y==0))|((p<.1)&(y==1))))}
    if changed is not None: out['changed_fact_accuracy']=float(acc[np.asarray(changed,bool)].mean())
    return out

def fit_temperature(p,y):
    z=logit(p)
    def obj(logT): return nll(sig(z/np.exp(logT)),y)
    r=minimize_scalar(obj,bounds=(-4,4),method='bounded')
    return float(np.exp(r.x))

def fit_platt(p,y):
    z=logit(p)
    def obj(ab): return nll(sig(ab[0]*z+ab[1]),y)
    r=minimize(obj,np.array([1.0,0.0]),method='L-BFGS-B',bounds=[(0.01,10),(-10,10)])
    return float(r.x[0]),float(r.x[1])

def reliability_bins(p,y,n=10):
    p=np.asarray(p);y=np.asarray(y); rows=[]
    edges=np.linspace(0,1,n+1)
    for i in range(n):
        mask=(p>=edges[i]) & ((p<edges[i+1]) if i<n-1 else (p<=edges[i+1]))
        if mask.any(): rows.append({'lo':float(edges[i]),'hi':float(edges[i+1]),'count':int(mask.sum()),
                                    'mean_conf':float(p[mask].mean()),'empirical_rate':float(y[mask].mean()),
                                    'gap':float(abs(p[mask].mean()-y[mask].mean()))})
    return rows

def main():
    outdir=str(REPO_ROOT / 'benchmarks' / 'wave12');os.makedirs(outdir,exist_ok=True)
    dev_seeds=[15400,15401,15402,15403]
    test_seeds=[15500,15501,15502,15503]
    dev=[collect(s,BatchedReserveCellular,CELL_PARAMS) for s in dev_seeds]
    test=[collect(s,BatchedReserveCellular,CELL_PARAMS) for s in test_seeds]
    graph=[collect(s,FairProvGraph,GRAPH_PARAMS) for s in test_seeds]
    cat=lambda rs,k:np.concatenate([r[k] for r in rs])
    pd,yd=cat(dev,'p'),cat(dev,'y')
    pt,yt,ct=cat(test,'p'),cat(test,'y'),cat(test,'changed')
    pg,yg,cg=cat(graph,'p'),cat(graph,'y'),cat(graph,'changed')

    T=fit_temperature(pd,yd)
    a,b=fit_platt(pd,yd)
    iso=IsotonicRegression(out_of_bounds='clip').fit(pd,yd)
    mappings={
      'uncalibrated':pt,
      'temperature':sig(logit(pt)/T),
      'platt':sig(a*logit(pt)+b),
      'isotonic':iso.predict(pt),
    }
    result={'design':{'scope':'post-hoc calibration only','substrate_locked':True,'gate_locked':True,'learning_locked':True,
                      'dev_seeds':dev_seeds,'untouched_test_seeds':test_seeds},
            'fit':{'temperature_T':T,'platt_a':a,'platt_b':b,
                   'dev_uncalibrated':metrics(pd,yd),
                   'dev_temperature':metrics(sig(logit(pd)/T),yd),
                   'dev_platt':metrics(sig(a*logit(pd)+b),yd),
                   'dev_isotonic':metrics(iso.predict(pd),yd)},
            'test':{},'graph_test':metrics(pg,yg,cg)}
    for name,p in mappings.items():
        result['test'][name]=metrics(p,yt,ct)
        result['test'][name]['reliability_bins']=reliability_bins(p,yt)
    # operation and activation invariance
    ops=[]; inf=[]; learn=[]; activated=[]
    for r in test:
        st=r['stats']; correct=((r['p']>=.5).astype(int)==r['y']).sum()
        ops.append(st['active_ops']/correct); inf.append(st['inference_ops']/correct); learn.append(st['learning_ops']/correct); activated.append(r['used'].mean())
    result['invariants']={'avg_activated':float(np.mean(activated)),'ops_per_correct':float(np.mean(ops)),
                          'inference_ops_per_correct':float(np.mean(inf)),'learning_ops_per_correct':float(np.mean(learn)),
                          'classification_decisions_identical_for_temperature':bool(np.array_equal(pt>=.5,mappings['temperature']>=.5)),
                          'classification_decisions_identical_for_platt':bool(np.array_equal(pt>=.5,mappings['platt']>=.5)),
                          'classification_decisions_identical_for_isotonic':bool(np.array_equal(pt>=.5,mappings['isotonic']>=.5))}
    with open(outdir+'/results.json','w') as f: json.dump(result,f,indent=2)
    fields=['method','accuracy','changed_fact_accuracy','brier','ece','nll','false_certainty']
    with open(outdir+'/summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        w.writerow({'method':'provenance_graph',**result['graph_test']})
        for name,m in result['test'].items(): w.writerow({'method':name,**{k:m[k] for k in fields[1:]}})
    print('Fit:',json.dumps(result['fit'],indent=2))
    print('\nTEST')
    print('graph',result['graph_test'])
    for name,m in result['test'].items(): print(name,{k:round(v,6) for k,v in m.items() if isinstance(v,(int,float))})
    print('\nINVARIANTS',result['invariants'])

if __name__=='__main__': main()
