import sys,json,os,csv,numpy as np
sys.path.insert(0,'/mnt/data/wave6')
import wave6_benchmark as w
base={
'majority':(w.Majority,{'window':7}),
'bayes_source':(w.StaticBayes,{'alpha':1.5}),
'dynamic_bayes':(w.DynamicBayes,{'forget':.985}),
'ewma_evidence':(w.EWMA,{'lr':.04,'decay':.99}),
'provenance_graph':(w.ProvGraph,{'lr':.12,'decay':.94,'claim':.5})}
cs=[
{'lr':.16,'fast_decay':.86,'min_k':7,'margin':.65,'path':.5,'claim_fast':1.0,'source':.18,'anti_credit':.5,'output_scale':1.0,'claim_fanout':5,'path_fanout':5},
{'lr':.24,'fast_decay':.92,'min_k':5,'margin':1.1,'path':.8,'claim_fast':1.0,'source':.08,'anti_credit':.8,'output_scale':.7,'claim_fanout':5,'path_fanout':3},
{'lr':.16,'fast_decay':.97,'min_k':3,'margin':1.6,'path':.25,'claim_fast':.7,'source':.18,'anti_credit':.2,'output_scale':.45,'claim_fanout':7,'path_fanout':3}]
dev=[8200,8201,8202]
best=None
for p in cs:
 rs=[w.run(s,w.CellularEventRouted,p) for s in dev]
 avg={k:float(np.mean([r[k] for r in rs])) for k in rs[0]}
 sc=w.score(avg)
 print('cell candidate',sc,p,avg['changed_fact_accuracy'],flush=True)
 if best is None or sc>best[0]: best=(sc,p,avg)
base['cellular_event_routed']=(w.CellularEventRouted,best[1])

def evalset(seeds):
 out={}
 for n,(cls,p) in base.items():
  rs=[w.run(s,cls,p) for s in seeds]
  out[n]={'mean':{k:float(np.mean([r[k] for r in rs])) for k in rs[0]},'sd':{k:float(np.std([r[k] for r in rs],ddof=1)) for k in rs[0]},'runs':rs,'params':p}
  a=out[n]['mean'];print(n,a['accuracy'],a['changed_fact_accuracy'],a['brier'],a['ops_per_correct'],flush=True)
 return out
fresh=evalset(list(range(9300,9308)))
legacy=evalset(list(range(7100,7108)))
p=best[1]
abl={}
for label,cls in [('full',w.CellularEventRouted),('no_exact_path',w.CellularNoPath)]:
 rs=[w.run(s,cls,p) for s in range(9300,9308)]
 abl[label]={'mean':{k:float(np.mean([r[k] for r in rs])) for k in rs[0]},'runs':rs}
payload={'design':{'dev_seeds':dev,'fresh_holdout':list(range(9300,9308)),'legacy_regression':list(range(7100,7108)),'routing':'persistent local routes with event-local cached potentials'},'cellular_dev_choice':{'score':best[0],'params':best[1],'dev':best[2]},'fresh_results':fresh,'legacy_results':legacy,'ablations':abl}
os.makedirs('/mnt/data/wave6',exist_ok=True)
json.dump(payload,open('/mnt/data/wave6/results.json','w'),indent=2)
fields=['method','accuracy','post_change_accuracy','changed_fact_accuracy','brier','ece','false_certainty','memory_states','updates','active_ops','ops_per_correct']
with open('/mnt/data/wave6/summary.csv','w',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader()
 for n,v in fresh.items():wr.writerow({'method':n,**{k:v['mean'][k] for k in fields[1:]}})
print('ABL', {k:v['mean']['changed_fact_accuracy'] for k,v in abl.items()})
