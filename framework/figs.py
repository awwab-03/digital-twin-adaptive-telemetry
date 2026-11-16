import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S = pd.read_csv('summary_by_scheme.csv'); d = pd.read_csv('results_all.csv')
d['Dk'] = d.D.replace({31: 32, 127: 128, 511: 512})
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False, 'font.family': 'serif'})
C = {'FixedRate':'#7f7f7f','Deadband+B':'#d9822b','MixPiece-window':'#2a7fbf','Deadband+A+B':'#1b9e77'}
L = {'FixedRate':'Fixed-rate (batched)','Deadband+B':'Deadband + B','MixPiece-window':'Mix-Piece (window)','Deadband+A+B':'Proposed A + B'}
# Fig 1: wire bytes relative to fixed-rate streaming vs freshness budget
fig, ax = plt.subplots(figsize=(3.4, 2.5))
fr0 = d[(d.scheme=='FixedRate')&(d.Dk==0)].set_index(['dataset','eps_pct']).wire_B
for sch in ['FixedRate','Deadband+B','MixPiece-window','Deadband+A+B']:
    xs, ys, lo, hi = [], [], [], []
    for Dk in [0, 8, 32, 128, 512]:
        name = sch if Dk > 0 else {'Deadband+B':'Deadband','Deadband+A+B':'Deadband+A'}.get(sch, sch)
        g = d[(d.scheme==name)&(d.Dk==Dk)&(d.q_frac.isin([0,0.125]))]
        if len(g) == 0: continue
        r = np.log(g.wire_B.values / fr0.loc[list(zip(g.dataset,g.eps_pct))].values)
        rng = np.random.default_rng(0); bs = [np.exp(rng.choice(r, len(r)).mean()) for _ in range(2000)]
        xs.append(max(Dk,1)*20/1000 if Dk else 0.01); ys.append(np.exp(r.mean())); lo.append(np.percentile(bs,2.5)); hi.append(np.percentile(bs,97.5))
    ax.plot(xs, ys, marker='o', ms=3, color=C[sch], label=L[sch], lw=1.3)
    ax.fill_between(xs, lo, hi, color=C[sch], alpha=0.15, lw=0)
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xticks([0.01, 0.16, 0.64, 2.56, 10.24]); ax.set_xticklabels(['0', '0.16', '0.64', '2.56', '10.24'])
ax.set_xlabel('Freshness budget $D$ (s)'); ax.set_ylabel('Wire bytes / unbatched fixed-rate')
ax.legend(frameon=False, fontsize=6.2, ncol=2, loc='lower center', bbox_to_anchor=(0.5, 1.0)); ax.grid(alpha=0.3, which='both', lw=0.4)
plt.tight_layout(); plt.savefig('fig/fig_bytes_vs_D.pdf'); plt.savefig('fig/fig_bytes_vs_D.png', dpi=200)
# Fig 2: ablation at D = 640 ms
ab = [('Deadband',0,'DB'),('Deadband+A',0,'+A'),('Deadband+B',32,'+B'),('Deadband+A+B',32,'+A+B')]
db0 = d[d.scheme=='Deadband'].set_index(['dataset','eps_pct'])
fig, ax = plt.subplots(1, 2, figsize=(3.4, 1.9))
for k, (met, lab) in enumerate([('wire_B','Wire bytes'),('msgs','Messages')]):
    vals, errs = [], []
    for sch, Dk, _ in ab:
        g = d[(d.scheme==sch)&(d.Dk==Dk)&(d.q_frac.isin([0,0.125]))]
        r = np.log(g[met].values / db0.loc[list(zip(g.dataset,g.eps_pct))][met].values)
        rng = np.random.default_rng(0); bs = [np.exp(rng.choice(r, len(r)).mean()) for _ in range(2000)]
        vals.append(np.exp(r.mean())); errs.append([vals[-1]-np.percentile(bs,2.5), np.percentile(bs,97.5)-vals[-1]])
    ax[k].bar(range(4), vals, yerr=np.array(errs).T, color=['#bbbbbb','#9ecae1','#fdae6b','#1b9e77'], capsize=2, error_kw={'lw':0.7})
    for i, v in enumerate(vals): ax[k].text(i, v + 0.04, f'{v:.2f}', ha='center', fontsize=6.5)
    ax[k].set_xticks(range(4)); ax[k].set_xticklabels([a[2] for a in ab], fontsize=6.5); ax[k].set_title(lab + ' / deadband', fontsize=7.5)
    ax[k].set_ylim(0, 1.25)
plt.tight_layout(); plt.savefig('fig/fig_ablation.pdf'); plt.savefig('fig/fig_ablation.png', dpi=200)
# Fig 3: per-dataset A+B / Mix-Piece at matched freshness
order = ['Cricket','FaceFour','Lightning','MoteStrain','Wafer','WindSpeed','WindDirection','Pressure','BTCUSD','ETHUSD','SPX','STOXX50E']
fig, ax = plt.subplots(figsize=(3.4, 2.0)); w = 0.38
for j, (Dk, col) in enumerate([(32,'#1b9e77'),(128,'#66c2a5')]):
    a = d[(d.scheme=='Deadband+A+B')&(d.Dk==Dk)&(d.q_frac==0.125)].set_index(['dataset','eps_pct']).wire_B
    b = d[(d.scheme=='MixPiece-window')&(d.Dk==Dk)].set_index(['dataset','eps_pct']).wire_B
    r = np.log(a/b).groupby(level=0).mean().apply(np.exp).reindex(order)
    ax.bar(np.arange(12) + (j-0.5)*w, r.values, w, color=col, label=f'$D$ = {Dk*20/1000:g} s')
ax.axhline(1, color='k', lw=0.6, ls='--'); ax.set_xticks(range(12)); ax.set_xticklabels(order, rotation=55, ha='right', fontsize=6)
ax.set_ylabel('Bytes: A+B / Mix-Piece'); ax.legend(frameon=False, fontsize=6.5, ncol=2, loc='upper center'); ax.set_ylim(0, 1.3)
plt.tight_layout(); plt.savefig('fig/fig_vs_mixpiece.pdf'); plt.savefig('fig/fig_vs_mixpiece.png', dpi=200)
print('ok')
