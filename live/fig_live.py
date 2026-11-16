import json, glob, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from common import TICK
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False, 'font.family': 'serif'})
C = {'FR':'#7f7f7f','DB':'#bbbbbb','DB+B':'#d9822b','A':'#9ecae1','A+B':'#1b9e77','MP':'#2a7fbf'}
LBL = {'FR':'Fixed-rate','DB':'Deadband','DB+B':'Deadband+B','A':'A','A+B':'A+B','MP':'Mix-Piece W=32'}
fig, ax = plt.subplots(figsize=(3.4, 2.2))
for s in ['FR','DB','A','DB+B','A+B','MP']:
    lat = []
    for f in sorted(glob.glob(f'res/{s}_D*_r*_ing.npz')):
        z = np.load(f)
        if 'T0' not in z.files: continue
        L = z['lat']; L = L[L[:, 0] >= 100]; lat.append((L[:, 2] - (float(z['T0']) + L[:, 0] * TICK)) * 1000)
    if not lat: continue
    lat = np.sort(np.concatenate(lat)); y = np.arange(1, len(lat) + 1) / len(lat)
    ax.plot(np.maximum(lat, 0.1), y, color=C[s], label=LBL[s], lw=1.3, ls='--' if s in ('DB','A') else '-')
ax.set_xscale('log'); ax.set_xlabel('Sample-to-commit latency (ms)'); ax.set_ylabel('CDF of updates')
ax.axvline(640, color='k', lw=0.6, ls=':'); ax.text(600, 0.05, '$D$=0.64 s ', fontsize=6.5, ha='right')
ax.legend(frameon=False, fontsize=6.2, loc='upper left'); ax.grid(alpha=0.3, lw=0.4)
plt.tight_layout(); plt.savefig('fig_live_latency.pdf'); plt.savefig('fig_live_latency.png', dpi=200); print('ok')
