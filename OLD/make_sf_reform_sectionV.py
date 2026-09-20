# -*- coding: utf-8 -*-
"""How Section V changes if the SF heating arm is reformulated: threshold FIXED
(net-load T_h; it coincides with the SF threshold to ~0.1 C) and fitted as a
non-origin OLS on days below it, ignoring points above T_h. Compares the current
free-threshold hockey stick against this reform, per substation and pooled, and
reads off the implied capacity change (P_max ~ 1/SF_cold)."""
import numpy as np, pandas as pd
from sf_transfer import build_frames, pickle_load
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

subs = build_frames(pickle_load('data/design_factorial.pkl'))


def r2f(x, y, m, b):
    ss = np.sum((y - y.mean()) ** 2)
    return 1 - np.sum((y - (m * x + b)) ** 2) / ss if ss > 0 else np.nan


def reform(T, SF, thr):
    """OLS SF = b + m*(thr - T) on the below-threshold points only."""
    mask = T < thr
    x, y = (thr - T[mask]), SF[mask]
    m, b = np.polyfit(x, y, 1)
    return b, m, r2f(x, y, m, b)


rows = []
for s in subs:
    T, SF = np.asarray(s['T']), np.asarray(s['SF'])
    try:
        b0, m0, th0, r20 = fit_hockey_stick(T, SF, T_BALANCE_BOUNDS)
    except Exception:
        continue
    if (T < th0).sum() < 10:
        continue
    b1, m1, r21 = reform(T, SF, th0)                # threshold fixed at th0 (= net-load T_h)
    Tmin = T.min()
    sfc0 = np.clip(b0 + m0 * max(0, th0 - Tmin), 0, 1)
    sfc1 = np.clip(b1 + m1 * max(0, th0 - Tmin), 0, 1)
    rows.append(dict(N_hp=int(round(s['hp_ratio'] * s['N_total'])),
                     b0=b0, m0=m0, th0=th0, r20=r20, sfc0=sfc0,
                     b1=b1, m1=m1, r21=r21, sfc1=sfc1))
d = pd.DataFrame(rows)

print(f'n = {len(d)} substations\n')
print('=== per-substation SF params (median) ===')
print(f'  current (free-thr hockey): b {d.b0.median():.3f}  m {d.m0.median():.4f}  '
      f'T_h^SF {d.th0.median():.1f}  SF_cold {d.sfc0.median():.3f}  R2 {d.r20.median():.3f}')
print(f'  reform  (fixed-thr OLS)  : b {d.b1.median():.3f}  m {d.m1.median():.4f}  '
      f'T_h^SF {d.th0.median():.1f} (fixed)  SF_cold {d.sfc1.median():.3f}  R2 {d.r21.median():.3f}')
print(f'  SF_cold ratio reform/current: median {(d.sfc1/d.sfc0).median():.3f}  '
      f'-> capacity ratio current/reform {(d.sfc0/d.sfc1).median():.3f}')

# ---- pooled transferable curve (ref half, matching sf_table split) ----------
rng = np.random.default_rng(0)
idx = np.arange(len(subs)); rng.shuffle(idx)
ref = [subs[i] for i in idx[:len(idx) // 2]]
T = np.concatenate([s['T'] for s in ref]); SF = np.concatenate([s['SF'] for s in ref])
b0, m0, th0, r20 = fit_hockey_stick(T, SF, T_BALANCE_BOUNDS)
b1, m1, r21 = reform(T, SF, th0)
Tmin = T.min()
print('\n=== pooled transferable curve ===')
print(f'  current: SF = {b0:.3f} + {m0:.4f}*max(0,{th0:.1f}-T)   R2 {r20:.3f}   SF_cold {b0 + m0*(th0-Tmin):.3f}')
print(f'  reform : SF = {b1:.3f} + {m1:.4f}*max(0,{th0:.1f}-T)   R2 {r21:.3f}   SF_cold {b1 + m1*(th0-Tmin):.3f}')
