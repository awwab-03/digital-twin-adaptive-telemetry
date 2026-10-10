import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=json.load(open('results.json'))
full=R['full']; win=R['window']; db={d['dataset']:d for d in R['deadband']}
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
# Fig1: CR vs eps, 4 datasets
ds=['Cricket','WindSpeed','Wafer','SPX']
fig,ax=plt.subplots(1,4,figsize=(10,2.6))
for a,d in zip(ax,ds):
    for m,c in [('MixPiece','#1f5fa8'),('SimPiece','#d9822b')]:
        rr=[r for r in full if r['dataset']==d and r['method']==m]
        a.plot([float(r['eps_pct']) for r in rr],[r['cr'] for r in rr],marker='o',ms=3,color=c,label=m.replace('P','-P'))
    a.set_title(d); a.set_xlabel('ε (% of range)')
ax[0].set_ylabel('Compression ratio'); ax[0].legend(frameon=False)
plt.tight_layout(); plt.savefig('fig1.png',dpi=200)
# Fig2: CR vs window for MixPiece vs deadband
ds2=sorted(set(r['dataset'] for r in win))
fig,ax=plt.subplots(2,6,figsize=(11,4.2)); ax=ax.flatten()
for a,d in zip(ax,ds2):
    rr=sorted([r for r in win if r['dataset']==d and r['method']=='MixPiece'],key=lambda r:int(r['window']) or 10**9)
    xs=[int(r['window']) or len(rr) and 'full' for r in rr]
    lab=[str(int(r['window'])) if int(r['window']) else 'all' for r in rr]
    a.plot(range(len(rr)),[r['cr'] for r in rr],marker='o',ms=3,color='#1f5fa8',label='Mix-Piece (window W)')
    if d in db: a.axhline(db[d]['cr'],color='#c0392b',ls='--',lw=1,label='Online deadband (W=1)')
    a.set_xticks(range(len(rr))); a.set_xticklabels(lab,fontsize=7); a.set_title(d,fontsize=8)
for a in ax[len(ds2):]: a.axis('off')
ax[0].set_ylabel('CR'); ax[6].set_ylabel('CR'); ax[0].legend(frameon=False,fontsize=6)
fig.supxlabel('Batch window W (points buffered before transmission)',fontsize=8)
plt.tight_layout(); plt.savefig('fig2.png',dpi=200)
print('figs ok')
