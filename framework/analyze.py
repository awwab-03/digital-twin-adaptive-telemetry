import pandas as pd, numpy as np
d = pd.read_csv('results_all.csv')
d['Dk'] = d.D.replace({31: 32, 127: 128, 511: 512})
mid = {**{k: 2.5 for k in ['Cricket','FaceFour','Lightning','MoteStrain','Wafer','WindSpeed','WindDirection']},
       **{k: 0.25 for k in ['Pressure','BTCUSD','ETHUSD','SPX','STOXX50E']}}
d['is_mid'] = d.apply(lambda r: abs(r.eps_pct - mid[r.dataset]) < 1e-9, axis=1)
main = d[(d.q_frac.isin([0, 0.125]))]
def key(r): return r.scheme
rng = np.random.default_rng(1)
def gm_ci(x, B=5000):
    x = np.log(np.asarray(x)); bs = [np.exp(rng.choice(x, len(x)).mean()) for _ in range(B)]
    return np.exp(x.mean()), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
# ratio of wire bytes vs fixed-rate (same dataset, eps, D)
fr = main[main.scheme == 'FixedRate'].set_index(['dataset','eps_pct','Dk']).wire_B
db0 = main[(main.scheme == 'Deadband')].set_index(['dataset','eps_pct']).wire_B
out = []
for (sch, Dk), g in main.groupby(['scheme','Dk']):
    rf = g.wire_B.values / fr.loc[list(zip(g.dataset, g.eps_pct, np.minimum(g.Dk,128)))].values
    rd = g.wire_B.values / db0.loc[list(zip(g.dataset, g.eps_pct))].values
    m, lo, hi = gm_ci(rf); m2, lo2, hi2 = gm_ci(rd)
    out.append(dict(scheme=sch, D=Dk, delay_ms=Dk*20, n=len(g), wire_vs_FR=m, lo=lo, hi=hi, wire_vs_DB=m2, lo2=lo2, hi2=hi2,
                    msgs_vs_FR=np.exp(np.log(g.msgs.values / main[(main.scheme=='FixedRate')&(main.Dk==0)].set_index(['dataset','eps_pct']).msgs.loc[list(zip(g.dataset,g.eps_pct))].values).mean()),
                    retro_max=g.retro_max_over_eps.max(), rt_nrmse=g.rt_nrmse_pct.mean(), p95=g.delay_p95_ms.mean(), edge_ns=g.edge_ns_per_sample.mean()))
S = pd.DataFrame(out).sort_values(['D','scheme'])
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(S.round(4).to_string())
S.to_csv('summary_by_scheme.csv', index=False)
# head-to-head: A+B vs MixPiece at matched freshness, per dataset at mid eps
print()
for Dk in [32, 128]:
    a = main[(main.scheme=='Deadband+A+B')&(main.Dk==Dk)].set_index(['dataset','eps_pct']).wire_B
    b = main[(main.scheme=='MixPiece-window')&(main.Dk==Dk)].set_index(['dataset','eps_pct']).wire_B
    r = (a/b).dropna(); print(Dk, 'A+B/MP wins', (r<1).sum(), '/', len(r), 'gm', np.exp(np.log(r).mean()).round(3), r.groupby(level=0).apply(lambda s: np.exp(np.log(s).mean())).round(2).to_dict())
# A+B at D=128 vs MP at W=512
a = main[(main.scheme=='Deadband+A+B')&(main.Dk==128)].set_index(['dataset','eps_pct']).wire_B
b = main[(main.scheme=='MixPiece-window')&(main.Dk==512)].set_index(['dataset','eps_pct']).wire_B
r=(a/b); print('A+B(D=128) / MP(W=512):', (r<1).sum(), '/', len(r), np.exp(np.log(r).mean()).round(3))
# q sensitivity
q = d[d.scheme.str.startswith('Deadband+A')]
for (qf, Dk), g in q.groupby(['q_frac','Dk']):
    if Dk in (0, 32):
        rd = g.wire_B.values / db0.loc[list(zip(g.dataset, g.eps_pct))].values
        print('q', qf, 'D', Dk, 'wire/DB gm', np.exp(np.log(rd).mean()).round(3), 'retro max', g.retro_max_over_eps.max().round(3), 'updates/DBupd', None)
# predictive variant
p = d[d.scheme=='Predictive(A-alt)']; dbu = d[d.scheme=='Deadband'].set_index(['dataset','eps_pct']).updates
print('pred updates/DB', np.exp(np.log(p.updates.values / dbu.loc[list(zip(p.dataset,p.eps_pct))].values).mean()).round(3),
      'wins', (p.updates.values < dbu.loc[list(zip(p.dataset,p.eps_pct))].values).sum(), '/', len(p))
