"""Cloud ingestion service: subscribe to all device topics, decode, commit to the SQLite twin store
(one transaction per message), and record per-update end-to-end latency.
usage: python3 ingest.py <scheme> <devices.json> <t0> <db> <out.npz> <stop_after_s>"""
import sys, time, json, struct, sqlite3, numpy as np
import paho.mqtt.client as mqtt
from common import *
scheme, cfgf, T0, dbf, outf, stop = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5], float(sys.argv[6])
devs = {d['dev']: d for d in json.load(open(cfgf))}
db = sqlite3.connect(dbf, check_same_thread=False)
db.execute('PRAGMA journal_mode=WAL'); db.execute('PRAGMA synchronous=NORMAL')
db.execute('CREATE TABLE IF NOT EXISTS twin(dev INT, tick INT, value REAL)'); db.commit()
state = {d: dict(il=0, lt=0) for d in devs}
mpseq = {}; lat = []; nmsg = 0; nupd = 0; cpu_ingest = 0.0

def decode_entries(dev, p, o, cnt):
    out = []; s = state[dev]; q = devs[dev]['q']
    for _ in range(cnt):
        if scheme in ('A', 'A+B'):
            if p[o] == 0:
                k, v = struct.unpack_from('<If', p, o + 1); o += 9; s['il'] = int(round(v / q))
            else:
                u, o = read_varint(p, o); dt, o = read_varint(p, o)
                s['il'] += unzz(u); k = s['lt'] + dt; v = s['il'] * q
            s['lt'] = k
        else:
            k, v = struct.unpack_from('<If', p, o); o += 8
        out.append((dev, k, v))
    return out

def on_message(c, u, m):
    global nmsg, nupd, cpu_ingest
    t_cpu = time.process_time()
    dev = int(m.topic[6:8]); p = m.payload; nmsg += 1
    if scheme == 'MP':
        # one compressed window per message; window ends at a tick multiple of 32 minus one
        rows = []; ticks = []
    else:
        batched = scheme in ('DB+B', 'A+B', 'FR+B')
        if batched:
            cnt = struct.unpack_from('<H', p, 0)[0]; rows = decode_entries(dev, p, 2, cnt)
        else:
            rows = decode_entries(dev, p, 0, 1)
    if scheme == 'MP':
        seq = mpseq.get(dev, 0); mpseq[dev] = seq + 1
        db.execute('INSERT INTO twin VALUES (?,?,?)', (dev, seq, len(p))); db.commit(); tc = time.time()
        for k in range(seq * 32, seq * 32 + 32): lat.append((k, dev, tc))   # every point of the window
        nupd += 1
    else:
        db.executemany('INSERT INTO twin VALUES (?,?,?)', rows); db.commit(); tc = time.time()
        for (_, k, _) in rows: lat.append((k, dev, tc))
        nupd += len(rows)
    cpu_ingest += time.process_time() - t_cpu

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='ingest')
c.on_message = on_message
c.connect('127.0.0.1', 1883, keepalive=60); c.subscribe('dt/+/sensor', qos=0); c.loop_start()
time.sleep(max(0, T0 + stop - time.time()))
c.loop_stop(); c.disconnect()
np.savez(outf, T0=T0, lat=np.array(lat, dtype=float),
         nmsg=nmsg, nupd=nupd, cpu_ingest=cpu_ingest)
db.close()
