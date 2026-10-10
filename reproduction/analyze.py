import csv, os, glob, gzip, json, sys
import numpy as np, zstandard as zs
C = zs.ZstdCompressor(level=3)
def zsize(d):
    return sum(len(C.compress(open(f,'rb').read())) for f in glob.glob(d+'/*.bin'))
res = {}
for mode in ['full','window']:
    rows=[]
    p=f'out/{mode}/meta_{mode}.csv'
    for r in csv.DictReader(open(p)):
        b = zsize(f'out/{mode}/'+r['payload_file'])
        r['zbytes']=b; r['cr']=int(r['raw_bytes'])/b
        r['bound_ok']= float(r['max_err']) <= 1.1*float(r['eps_abs'])+1e-12
        rows.append(r)
    res[mode]=rows
# deadband (send-on-delta, zero-order hold) streaming baseline
def load(name):
    t=[];v=[]
    with gzip.open(f'data/{name}.csv.gz','rt') as f:
        for line in f:
            a,b=line.split(','); t.append(int(a)); v.append(float(b))
    return np.array(v)
def deadband(v, eps):
    sent=np.empty_like(v); last=v[0]; cnt=1; sent[0]=last
    for i in range(1,len(v)):
        if abs(v[i]-last)>eps: last=v[i]; cnt+=1
        sent[i]=last
    return cnt, sent
db=[]
for r in res['window']:
    if r['method']!='MixPiece' or r['window']!='0': continue
    v=load(r['dataset']); eps=float(r['eps_abs'])
    cnt,s=deadband(v,eps); err=v-s
    db.append(dict(dataset=r['dataset'],eps_pct=r['eps_pct'],n=len(v),msgs=cnt,bytes=cnt*8,
        cr=len(v)*8/(cnt*8), rmse=float(np.sqrt(np.mean(err**2))), maxerr=float(np.abs(err).max()), eps_abs=eps))
    print('db',r['dataset'],round(len(v)/cnt,2),flush=True)
json.dump({'full':res['full'],'window':res['window'],'deadband':db},open('results.json','w'),default=str,indent=1)
