# -*- coding: utf-8 -*-
"""B2: household-disjoint SF transfer with repeated group-level splits.

The 50 heat pumps on the largest weather station (one population) are split into
two disjoint halves; a pooled SF curve fitted on aggregates drawn from one half
is applied to aggregates drawn from the other, so no heat pump appears in both
calibration and evaluation. Repeated over many random splits to give a
distribution of the transfer error -- the honest within-population
generalisation, versus the substation-level (shared-household) resampling."""
import numpy as np, pandas as pd
import hp_pools as hpp
from hp_capacity import robust_series_peak
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

p = hpp.build_pool_combined(verbose=False)
idx = p['index']; w = p['weather_of']
hp_hh = [h for h in p['hp_households'] if w.get(h) == 'KLO']
row = {h: i for i, h in enumerate(p['hp_households'])}
hp_mat = p['hp_mat']
peak = {h: float(robust_series_peak(hp_mat[row[h]])) for h in hp_hh}
temp = pd.Series(p['temperature']['KLO'], index=idx)
Td = temp.resample('D').mean()
print(f'{len(hp_hh)} heat pumps on KLO')

def agg_sf(members):
    load = hp_mat[[row[h] for h in members]].sum(axis=0)
    ld = pd.Series(load, index=idx).resample('D').mean()
    cap = sum(peak[h] for h in members)
    d = pd.DataFrame({'T': Td, 'sf': ld / cap}).dropna()
    return d['T'].to_numpy(), d['sf'].to_numpy()

def fit(T, sf):
    b, s, t, r2 = fit_hockey_stick(T, sf, T_BALANCE_BOUNDS)
    return b, s, t, r2

def pooled(members_list):
    Ts, Ss = [], []
    for m in members_list:
        T, s = agg_sf(m); Ts.append(T); Ss.append(s)
    return fit(np.concatenate(Ts), np.concatenate(Ss))

SIZES = [5, 10, 20]
rng = np.random.default_rng(0)
rows = []
for split in range(120):
    hp = list(hp_hh); rng.shuffle(hp)
    A, B = hp[:len(hp)//2], hp[len(hp)//2:]           # disjoint halves (25/25)
    ref_aggs = [list(rng.choice(A, k, replace=False)) for k in rng.choice(SIZES, 25)]
    curve = pooled(ref_aggs)                           # reference curve from half A
    b, s, t, _ = curve
    for k in SIZES:
        for _ in range(8):
            m = list(rng.choice(B, k, replace=False))  # target from half B
            T, sf = agg_sf(m)
            pred = np.clip(b + s * np.maximum(0, t - T), 0, 1)
            pk_t, pk_p = np.quantile(sf, .99), np.quantile(pred, .99)
            ss = np.sum((sf - sf.mean()) ** 2)
            r2_bor = 1 - np.sum((sf - pred) ** 2) / ss
            _, _, _, r2_self = fit(T, sf)
            rows.append(dict(split=split, n_hp=k, pk_t=pk_t, pk_p=pk_p,
                             r2_bor=r2_bor, r2_self=r2_self))
d = pd.DataFrame(rows)

def wape(g): return (g.pk_p - g.pk_t).abs().sum() / g.pk_t.sum() * 100
per_split = d.groupby('split').apply(lambda g: pd.Series({
    'wape': wape(g), 'r2_bor': g.r2_bor.median(), 'r2_self': g.r2_self.median()}))
def ci(x): return f'{x.median():.2f} [{x.quantile(.25):.2f}, {x.quantile(.75):.2f}]'
print('\nHOUSEHOLD-DISJOINT transfer over 120 splits (median [IQR]):')
print('  peak-SF WAPE (%)   :', ci(per_split.wape))
print('  borrowed R2        :', ci(per_split.r2_bor))
print('  self-fit R2        :', ci(per_split.r2_self))
print('\n  peak-SF WAPE by N_hp (median over splits):')
for k in SIZES:
    sub = d[d.n_hp == k].groupby('split').apply(wape)
    print(f'    N_hp={k:2d}: {sub.median():.1f}%  [{sub.quantile(.25):.1f}, {sub.quantile(.75):.1f}]')
