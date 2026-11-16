"""Run one live configuration: fresh Mosquitto, ingestion service, device fleet. Collect broker $SYS counters,
process CPU times, latency and twin store. usage: python3 run_live.py <scheme> <D_ticks> <rep> <outdir> [n_dev n_ticks]"""
import sys, os, time, json, subprocess, signal, sqlite3, psutil, numpy as np
import paho.mqtt.client as mqtt
from common import *
scheme, D, rep, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
NDEV = int(sys.argv[5]) if len(sys.argv) > 5 else 50; N = int(sys.argv[6]) if len(sys.argv) > 6 else 3000
os.makedirs(out, exist_ok=True); tag = f'{out}/{scheme}_D{D}_r{rep}'
cfg = f'{out}/devices.json'
if not os.path.exists(cfg): json.dump(make_devices(NDEV, N), open(cfg, 'w'))
open(f'{out}/mosq.conf', 'w').write('listener 1883 127.0.0.1\nallow_anonymous true\nsys_interval 1\nmax_queued_messages 0\npersistence false\nlog_dest none\n')
if os.path.exists(tag + '.db'): os.remove(tag + '.db')
for f in [tag + '.db-wal', tag + '.db-shm']:
    if os.path.exists(f): os.remove(f)
broker = subprocess.Popen(['mosquitto', '-c', f'{out}/mosq.conf']); time.sleep(1.0)
bp = psutil.Process(broker.pid); bcpu0 = sum(bp.cpu_times()[:2])
T0 = time.time() + 3.0; dur = N * TICK
ing = subprocess.Popen([sys.executable, 'ingest.py', scheme, cfg, str(T0), tag + '.db', tag + '_ing.npz', str(dur + 4)])
time.sleep(1.0)
dev = subprocess.Popen([sys.executable, 'device.py', scheme, cfg, str(T0), str(N), str(D), tag + '_dev.npz'])
dp = psutil.Process(dev.pid); ip = psutil.Process(ing.pid)
dcpu = icpu = 0.0
while dev.poll() is None:
    try: dcpu = sum(dp.cpu_times()[:2]); icpu = sum(ip.cpu_times()[:2])
    except Exception: pass
    time.sleep(0.5)
ing.wait()
time.sleep(1.5)
sysv = {}
def on_m(c, u, m): sysv[m.topic] = m.payload.decode()
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='sysmon'); c.on_message = on_m
c.connect('127.0.0.1', 1883); c.subscribe('$SYS/broker/#'); c.loop_start(); time.sleep(2.5); c.loop_stop(); c.disconnect()
bcpu = sum(bp.cpu_times()[:2]) - bcpu0
broker.send_signal(signal.SIGTERM); broker.wait()
json.dump(dict(scheme=scheme, D=D, rep=rep, ndev=NDEV, ticks=N, broker_cpu_s=bcpu, device_cpu_s=dcpu, ingest_cpu_s=icpu,
               sys={k: v for k, v in sysv.items() if any(s in k for s in ['bytes/received', 'messages/received', 'publish/messages/received', 'publish/bytes/received', 'bytes/sent', 'messages/sent'])}),
          open(tag + '_meta.json', 'w'), indent=1)
print('done', scheme, D, rep, 'broker msgs', sysv.get('$SYS/broker/publish/messages/received'), 'bytes', sysv.get('$SYS/broker/bytes/received'))
