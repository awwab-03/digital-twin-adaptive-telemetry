"""Run every telemetry scheme on every dataset / error budget / freshness budget and
write one CSV row per configuration. Usage: python3 run_all.py <data_dir> <mp_dir> <out.csv>"""
import sys, os, gzip, time, glob, struct, csv
import numpy as np, zstandard as zs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edge

DATA, MP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TICK_MS = 20.0          # replay rate: 50 Hz (one dataset sample per 20 ms tick)
HB = 250                # heartbeat: at most 5 s of silence for every event-driven scheme
W_LS = 8                # window for the LS slope / model selection in component A
MAXPAY = 5 * 1024       # micro-batch payload cap (5 KB)
SENSOR = ['Cricket','FaceFour','Lightning','MoteStrain','Wafer','WindSpeed','WindDirection']
HP = ['Pressure','BTCUSD','ETHUSD','SPX','STOXX50E']
EPS = {d: [1.0, 2.5, 5.0] for d in SENSOR} | {d: [0.1, 0.25, 0.5] for d in HP}
DS = [0, 8, 32, 128]    # freshness budgets in ticks (0, 160 ms, 640 ms, 2.56 s)
WS = [32, 128, 512]     # Mix-Piece windows
ZC = zs.ZstdCompressor(level=3)
NREP = 5
QF = [0.125, 0.25, 0.5]   # quantisation step q as a fraction of eps (first = default)

def load(name):
    cache = f'{DATA}/{name}.npy'
    if os.path.exists(cache):
        return np.load(cache)
    with gzip.open(f'{DATA}/{name}.csv.gz', 'rt') as f:
        v = np.array([float(l.split(',')[1]) for l in f])
    np.save(cache, v); return v

def metrics(x, y, r, eps, rng, t_upd, arr, sizes, nmsg_extra=0):
    n = len(x)
    rt_err = np.abs(x - y); retro = np.abs(x - r)
    delay = (arr - t_upd) * TICK_MS
    hours = n * TICK_MS / 3.6e6
    nm = len(sizes) + nmsg_extra
    pay = int(sizes.sum())
    return dict(n=n, updates=len(t_upd), msgs=nm, payload_B=pay, wire_B=pay + edge.MQTT_OVH * nm,
                msgs_per_h=nm / hours, wireKB_per_h=(pay + edge.MQTT_OVH * nm) / 1024 / hours,
                rt_nrmse_pct=100 * np.sqrt(np.mean(rt_err ** 2)) / rng,
                rt_viol_pct=100 * np.mean(rt_err > eps * (1 + 1e-9)),
                retro_max_over_eps=float(retro.max() / eps),
                delay_p50_ms=float(np.percentile(delay, 50)), delay_p95_ms=float(np.percentile(delay, 95)),
                delay_max_ms=float(delay.max()))

def timed(fn, *a):
    ts = []
    out = fn(*a)  # warm (JIT)
    for _ in range(NREP):
        t0 = time.perf_counter(); out = fn(*a); ts.append(time.perf_counter() - t0)
    return out, float(np.mean(ts)), float(np.std(ts))

rows = []
names = sys.argv[4].split(',') if len(sys.argv) > 4 else SENSOR + HP
for name in names:
    x = load(name); n = len(x); rng = x.max() - x.min()
    for ep in EPS[name]:
        eps = rng * ep / 100
        base = dict(dataset=name, eps_pct=ep)
        # S0 fixed-rate streaming: every sample is an 8-byte entry (D=0: one message per sample)
        tall = np.arange(n, dtype=np.int64); e8 = np.full(n, 8, np.int64)
        for D in DS:
            arr, sizes = edge.pack_sizes(tall, e8, D, MAXPAY)
            y, r = edge.twin_view(x, tall, x, np.zeros(n), arr)
            rows.append(base | dict(scheme='FixedRate', D=D, W=0, q_frac=0, edge_ns_per_sample=0.0, edge_ns_sd=0.0)
                        | metrics(x, y, r, eps, rng, tall, arr, sizes))
        # S1 deadband baseline (8-byte absolute entries); with D>0 this is Deadband+B
        (t, v, s, m), mu, sd = timed(edge.deadband_zoh, x, eps, HB)
        eb = np.full(len(t), 8, np.int64)
        for D in DS:
            arr, sizes = edge.pack_sizes(t, eb, D, MAXPAY)
            y, r = edge.twin_view(x, t, v, s, arr)
            rows.append(base | dict(scheme='Deadband' if D == 0 else 'Deadband+B', D=D, W=0, q_frac=0,
                        edge_ns_per_sample=mu / n * 1e9, edge_ns_sd=sd / n * 1e9) | metrics(x, y, r, eps, rng, t, arr, sizes))
        # S3 proposed: component A (quantized delta deadband), with D>0 = A+B
        for qf in QF:
            (t, v, s, eb), mu, sd = timed(edge.deadband_quantized, x, eps, qf * eps, HB)
            for D in (DS if qf == QF[0] else [0, 32]):
                arr, sizes = edge.pack_sizes(t, eb, D, MAXPAY)
                y, r = edge.twin_view(x, t, v, s, arr)
                rows.append(base | dict(scheme='Deadband+A' if D == 0 else 'Deadband+A+B', D=D, W=0, q_frac=qf,
                            edge_ns_per_sample=mu / n * 1e9, edge_ns_sd=sd / n * 1e9) | metrics(x, y, r, eps, rng, t, arr, sizes))
        # S4 negative variant: dual-prediction deadband (hold/linear chosen by LS back-cast)
        (t, v, s, m), mu, sd = timed(edge.adaptive_predictive, x, eps, HB, W_LS)
        eb = np.where(m == 1, 13, 9).astype(np.int64)
        arr, sizes = edge.pack_sizes(t, eb, 0, MAXPAY)
        y, r = edge.twin_view(x, t, v, s, arr)
        rows.append(base | dict(scheme='Predictive(A-alt)', D=0, W=0, q_frac=0, edge_ns_per_sample=mu / n * 1e9,
                    edge_ns_sd=sd / n * 1e9) | metrics(x, y, r, eps, rng, t, arr, sizes))
        # S2 windowed Mix-Piece (base article): one message per window of W points
        for W in WS:
            pf = f'{MP}/{name}_e{ep:.3f}_W{W}'
            if not os.path.exists(pf + '.rec'):
                continue
            raw = open(pf + '.pay', 'rb').read(); off = 0; sizes = []
            while off < len(raw):
                L = struct.unpack('>i', raw[off:off + 4])[0]; off += 4
                sizes.append(len(ZC.compress(raw[off:off + L]))); off += L
            sizes = np.array(sizes, np.int64)
            rec = np.fromfile(pf + '.rec', dtype='>f8').astype(np.float64)
            starts = np.arange(0, n, W); ends = np.minimum(starts + W, n) - 1
            # twin receives window k when its last sample is taken; holds the last reconstructed value
            tw = ends.astype(np.int64); vw = rec[ends]; arrw = tw.copy()
            y, _ = edge.twin_view(x, tw, vw, np.zeros(len(tw)), arrw)
            # every point's information arrives at its window's end
            t_pt = np.arange(n, dtype=np.int64); arr_pt = np.repeat(tw, np.diff(np.append(starts, n)))
            mt = metrics(x, y, rec, eps, rng, t_pt, arr_pt, sizes)
            mt['updates'] = len(tw)
            rows.append(base | dict(scheme='MixPiece-window', D=W - 1, W=W, q_frac=0, edge_ns_per_sample=float('nan'), edge_ns_sd=float('nan')) | mt)
        print(name, ep, flush=True)
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('wrote', OUT, len(rows))
