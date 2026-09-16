# -*- coding: utf-8 -*-
"""Use-case validation of the flexible energy E_flex = SF(1-SF) P_max dt (up=down).
Estimated: transferred Swiss SF + Eq.(5) capacity. Actual: the substation's own
submetered SF + true capacity. Same formula, on the held-out half. dt cancels in
the metrics."""
import numpy as np, pandas as pd, pickle
from capacity_two_methods import fits_frame, metrics

RNG = np.random.default_rng(0)
d = fits_frame(pickle.load(open('data/design_factorial.pkl', 'rb')))
d['N_hp'] = (d.hp_ratio * d.N_total).round().astype(int)
idx = np.arange(len(d)); RNG.shuffle(idx)
tr = d.iloc[idx[:len(idx)//2]]; te = d.iloc[idx[len(idx)//2:]].copy()
sf_ref = float(tr.SF_cold.median())              # transferred coldest-day SF

# coldest-day flexible energy (per unit dt)
te['cap_est'] = te.delta / sf_ref                                   # Eq.(5) capacity
te['flex_est'] = sf_ref * (1 - sf_ref) * te.cap_est                 # = (1-sf_ref)*delta
te['flex_act'] = te.SF_cold * (1 - te.SF_cold) * te.HP_Peak         # own SF, true capacity
te = te[(te.flex_act > 0) & (te.delta > 0)]

def wape(p, a): return np.abs(np.asarray(p) - np.asarray(a)).sum() / np.asarray(a).sum() * 100
p, a = te.flex_est.to_numpy(), te.flex_act.to_numpy()
print(f'n = {len(te)} held-out substations')
print(f'transferred SF_ref = {sf_ref:.3f}\n')
print('=== flexible energy E_flex (up = down), coldest day ===')
print(f'  WAPE                 : {wape(p, a):.0f}%')
print(f'  median ratio est/act : {np.median(p / a):.2f}')
print(f'  R2 (across subs)     : {metrics(a, p)[1]:.3f}')
print(f'  Pearson r            : {np.corrcoef(a, p)[0,1]:.3f}')
print('\n-- WAPE by N_hp --')
for k in [5, 10, 20, 30, 40, 50]:
    m = te.N_hp.values == k
    if m.sum():
        print(f'  N_hp={k:2d} (n={m.sum():3d}): WAPE {wape(p[m], a[m]):5.0f}%  ratio {np.median(p[m]/a[m]):.2f}')

# decompose: how much of the error is the SF factor vs the capacity
te['flex_act_ownSF_estcap'] = te.SF_cold * (1 - te.SF_cold) * te.cap_est
print('\n-- error attribution (WAPE vs actual) --')
print(f'  full estimate (ref SF + est cap)         : {wape(te.flex_est, te.flex_act):.0f}%')
print(f'  own SF + est cap (isolates capacity err) : {wape(te.flex_act_ownSF_estcap, te.flex_act):.0f}%')
print(f'  ref SF + true cap (isolates SF err)      : {wape(sf_ref*(1-sf_ref)*te.HP_Peak, te.flex_act):.0f}%')
