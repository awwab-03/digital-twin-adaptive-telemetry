"""Edge devices: replay dataset segments in real time (50 Hz) and publish with a given policy.
usage: python3 device.py <scheme> <devices.json> <t0> <n_ticks> <D_ticks> <log.npz>"""
import sys, time, json, struct, numpy as np, zstandard as zs
import paho.mqtt.client as mqtt
from common import *
scheme, cfgf, T0, N, D = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
devs = json.load(open(cfgf))
X = {}
for d in devs:
    X[d['dev']] = np.load(f"{DATA}/{d['dataset']}.npy")[d['offset']:d['offset'] + N]

# Mix-Piece: pre-compressed windows (W=32) from the authors' implementation, zstd level 3
MPW = {}
if scheme == 'MP':
    zc = zs.ZstdCompressor(level=3)
    for d in devs:
        pf = f"{MP}/{d['dataset']}_e{MID[d['dataset']]:.3f}_W32.pay"
        raw = open(pf, 'rb').read(); o = 0; w = 0; s = d['offset'] // 32; out = {}
        while o < len(raw) and w < s + N // 32:
            L = struct.unpack('>i', raw[o:o + 4])[0]; o += 4
            if w >= s: out[(w - s) * 32 + 31] = zc.compress(raw[o:o + L])
            o += L; w += 1
        MPW[d['dev']] = out

clients = []
for d in devs:
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'dev{d["dev"]:02d}')
    c.max_queued_messages_set(0); c.connect('127.0.0.1', 1883, keepalive=60); c.loop_start(); clients.append(c)

st = {d['dev']: dict(last=None, lt=0, il=0, buf=bytearray(), cnt=0, first=None) for d in devs}
sent_msgs = 0; sent_pay = 0; late = []

def publish(dev, payload):
    global sent_msgs, sent_pay
    clients[dev].publish(topic(dev), payload, qos=0); sent_msgs += 1; sent_pay += len(payload)

def emit(d, k, entry):
    s = st[d['dev']]
    if D == 0:
        publish(d['dev'], entry); return
    if s['cnt'] and len(s['buf']) + 2 + len(entry) > MAXPAY:
        flush(d)
    if s['cnt'] == 0: s['first'] = k
    s['buf'] += entry; s['cnt'] += 1

def flush(d):
    s = st[d['dev']]
    if s['cnt']:
        publish(d['dev'], struct.pack('<H', s['cnt']) + bytes(s['buf']))
        s['buf'] = bytearray(); s['cnt'] = 0; s['first'] = None

while time.time() < T0: time.sleep(0.001)
for k in range(N):
    target = T0 + k * TICK
    now = time.time()
    if now < target: time.sleep(target - now)
    late.append(time.time() - target)
    for d in devs:
        x = float(X[d['dev']][k]); s = st[d['dev']]; eps = d['eps']; q = d['q']
        if scheme == 'FR':
            emit(d, k, struct.pack('<If', k, x))
        elif scheme in ('DB', 'DB+B'):
            if s['last'] is None or abs(x - s['last']) > eps or k - s['lt'] >= HB:
                s['last'] = x; s['lt'] = k; emit(d, k, struct.pack('<If', k, x))
        elif scheme in ('A', 'A+B'):
            if s['last'] is None or abs(x - s['last']) > eps - q / 2 or k - s['lt'] >= HB:
                i = int(round(x / q))
                if s['last'] is None or k - s['lt'] >= HB:
                    e = b'\x00' + struct.pack('<If', k, i * q)          # absolute entry, 9 bytes
                else:
                    e = varint(zz(i - s['il'])) + varint(k - s['lt'])  # delta entry
                s['il'] = i; s['last'] = i * q; s['lt'] = k; emit(d, k, e)
        elif scheme == 'MP':
            if k in MPW[d['dev']]: publish(d['dev'], MPW[d['dev']][k])
        if D and s['cnt'] and k - s['first'] >= D:
            flush(d)
for d in devs: flush(d)
time.sleep(1.0)
for c in clients: c.loop_stop(); c.disconnect()
np.savez(sys.argv[6], late=np.array(late), sent_msgs=sent_msgs, sent_pay=sent_pay)
