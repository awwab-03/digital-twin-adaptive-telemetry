import json, glob, os, sqlite3, numpy as np, pandas as pd
from common import *
R = 'res'; devs = json.load(open(f'{R}/devices.json')); N = 3000
X = {d['dev']: np.load(f"{DATA}/{d['dataset']}.npy")[d['offset']:d['offset'] + N] for d in devs}
rows = []
for meta in sorted(glob.glob(f'{R}/*_meta.json')):
    m = json.load(open(meta)); tag = meta[:-10]
    ing = np.load(tag + '_ing.npz'); dev = np.load(tag + '_dev.npz')
    if 'T0' not in ing.files: continue
    T0 = float(ing['T0']); L = ing['lat']
    WARM = 100   # exclude the first 2 s (100 ticks): connection set-up of 50 MQTT clients
    L = L[L[:, 0] >= WARM]
    lat = (L[:, 2] - (T0 + L[:, 0] * TICK)) * 1000
    s = m['sys']
    # twin fidelity check from the database (not possible for MP blobs)
    maxerr = np.nan
    if m['scheme'] != 'MP':
        con = sqlite3.connect(tag + '.db'); q = pd.read_sql('SELECT dev,tick,value FROM twin', con); con.close()
        errs = []
        for d in devs:
            g = q[q.dev == d['dev']].sort_values('tick'); t = g.tick.values; v = g.value.values
            idx = np.searchsorted(t, np.arange(N), side='right') - 1
            errs.append(np.max(np.abs(X[d['dev']] - v[idx])) / d['eps'])
        maxerr = float(np.max(errs))
    rows.append(dict(scheme=m['scheme'], rep=m['rep'], sent=int(dev['sent_msgs']), recv=int(ing['nmsg']),
                     broker_pub_msgs=int(s['$SYS/broker/publish/messages/received']),
                     broker_bytes=int(s['$SYS/broker/bytes/received']), pub_payload=int(s['$SYS/broker/publish/bytes/received']),
                     lat_p50=np.percentile(lat, 50), lat_p95=np.percentile(lat, 95), lat_p99=np.percentile(lat, 99), lat_max=lat.max(), over_budget_pct=100*np.mean(lat > {'DB+B':640,'A+B':640,'MP':620}.get(m['scheme'],0)+20),
                     broker_cpu=m['broker_cpu_s'], ingest_cpu=m['ingest_cpu_s'], device_cpu=m['device_cpu_s'],
                     sched_p95_ms=np.percentile(dev['late'], 95) * 1000, max_err_over_eps=maxerr, n_updates=int(ing['nupd'])))
D = pd.DataFrame(rows); D.to_csv('live_runs.csv', index=False)
order = ['FR', 'DB', 'DB+B', 'A', 'A+B', 'MP']
agg = D.groupby('scheme').agg(['mean', 'std']).reindex([o for o in order if o in set(D.scheme)])
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40)
cols = ['broker_pub_msgs', 'broker_bytes', 'pub_payload', 'lat_p50', 'lat_p95', 'lat_p99', 'lat_max', 'over_budget_pct', 'broker_cpu', 'ingest_cpu', 'device_cpu', 'max_err_over_eps']
print(agg[cols].round(2).to_string()); print(D.groupby('scheme')[['sent', 'recv', 'rep', 'sched_p95_ms']].agg(['min', 'max', 'count']).to_string())
agg.to_csv('live_summary.csv')
