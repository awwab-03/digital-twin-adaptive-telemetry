"""Shared definitions for the live MQTT testbed (devices -> Mosquitto -> ingestion -> SQLite twin)."""
import json, struct, os, numpy as np
TICK = 0.02                       # 50 Hz
HB = 250                          # heartbeat after 5 s of silence
MAXPAY = 5 * 1024
DATA = '/home/claude/work/data'
MP = '/home/claude/work/emu/mp'
MID = {'Cricket': 2.5, 'Wafer': 2.5, 'WindSpeed': 2.5, 'Pressure': 0.25, 'SPX': 0.25}

def topic(dev):  # 15 characters, as in the emulator's overhead model
    return f'dt/dev{dev:02d}/sensor'

def zz(z): return (z << 1) if z >= 0 else ((-z) << 1) - 1
def unzz(u): return (u >> 1) if not (u & 1) else -((u + 1) >> 1)
def varint(u):
    out = bytearray()
    while u >= 128:
        out.append((u & 127) | 128); u >>= 7
    out.append(u); return bytes(out)
def read_varint(b, o):
    s = 0; r = 0
    while True:
        c = b[o]; o += 1; r |= (c & 127) << s; s += 7
        if c < 128: return r, o

def make_devices(n_dev, n_ticks, seed=7):
    """Assign each device a contiguous, 32-aligned segment of one dataset."""
    rng = np.random.default_rng(seed); names = list(MID); devs = []
    for d in range(n_dev):
        name = names[d % len(names)]
        x = np.load(f'{DATA}/{name}.npy'); rngv = float(x.max() - x.min())
        nwin = (len(x) - n_ticks) // 32
        off = int(rng.integers(0, nwin)) * 32
        eps = rngv * MID[name] / 100
        devs.append(dict(dev=d, dataset=name, offset=off, eps=eps, q=eps / 8, range=rngv))
    return devs
