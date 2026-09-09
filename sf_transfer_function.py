# -*- coding: utf-8 -*-
"""Transfer the Swiss SF *function* (not the single coldest-day value) to German
temperature. Capacity = delta / SF_Swiss(T_min_target), i.e. evaluate the Swiss
SF(T) hockey stick at the target's own coldest temperature, instead of borrowing
the Swiss coldest-day SF (0.42) read at Switzerland's colder -8.2 C.

Compared on the synthetic WPUQ substations and on the single REAL WPUQ feeder,
against (a) the old constant 0.42 and (b) the target's own local SF (oracle).
"""
import numpy as np, pandas as pd, pickle
import hp_sf, hp_pools as hpp, hp_capacity as hc
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

# ---- Swiss SF function (pooled) ------------------------------------------------
BASE_S, SLOPE_S, THR_S = 0.027, 0.0161, 16.45          # Swiss pooled SF hockey stick
SF_COLD_SWISS = 0.42                                    # old transferred constant


def sf_swiss(T):
    return BASE_S + SLOPE_S * np.maximum(0.0, THR_S - T)


def frame(design):
    df = hp_sf.fit_all(design, verbose=False).reset_index()
    d = pd.DataFrame({'HP_Peak': df.HP_Peak, 'Tmin': df.T_min_obs, 'hp_ratio': df.hp_ratio,
                      'delta': df.Load_slope * np.maximum(0, df.Load_T_threshold - df.T_min_obs)})
    d['SF_own'] = (df.SF_base + df.SF_slope * np.maximum(0, df.SF_T_threshold - df.T_min_obs)).clip(0, 1)
    return d[(d.HP_Peak > 0) & (d.delta > 0)].dropna(subset=['delta', 'HP_Peak', 'SF_own'])


def report(d, tag):
    def m(pred):
        y = d.HP_Peak.to_numpy(); p = np.asarray(pred, float); ok = y > 0
        mape = np.mean(np.abs((y[ok] - p[ok]) / y[ok])) * 100
        r2 = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
        bias = (p.mean() - y.mean()) / y.mean() * 100
        return mape, r2, bias
    print(f'\n=== {tag}  (n={len(d)}, Tmin~{d.Tmin.median():.1f} C) ===')
    variants = [
        ('old  : delta / 0.42 (Swiss coldest-day constant)', d.delta / SF_COLD_SWISS),
        ('NEW  : delta / SF_Swiss(Tmin_target)              ', d.delta / sf_swiss(d.Tmin)),
        ('oracle: delta / own local SF                      ', d.delta / d.SF_own)]
    for name, pred in variants:
        mape, r2, bias = m(pred)
        print(f'  {name}: MAPE {mape:5.1f}%  R2 {r2:6.3f}  bias {bias:+6.1f}%')
    print(f'  SF_Swiss(Tmin={d.Tmin.median():.1f}) = {float(sf_swiss(d.Tmin.median())):.3f}   '
          f'(vs 0.42 constant, vs own SF median {d.SF_own.median():.3f})')


# ---- synthetic WPUQ substations ------------------------------------------------
wp = frame(pickle.load(open('data/design_wpuq.pkl', 'rb')))
report(wp, 'SYNTHETIC WPUQ substations')

# ---- single REAL WPUQ feeder ---------------------------------------------------
pool = hpp.build_pool_wpuq(verbose=False)
hp_mat, other_mat = pool['hp_mat'], pool['other_mat']
idx = pd.DatetimeIndex(pool['index'])
temp = np.asarray(pool['temperature']['WPUQ'], float).ravel()
HP_Peak = float(np.sum([hc.robust_series_peak(hp_mat[i]) for i in range(hp_mat.shape[0])]))
dd = pd.DataFrame({'Temp': temp, 'net': np.asarray((hp_mat + other_mat).sum(0), float)},
                  index=idx).resample('D').mean().dropna()
Tw = dd['Temp'].to_numpy(); Tmin = float(Tw.min())
bn, sn, tn, rn = [float(x) for x in fit_hockey_stick(Tw, dd['net'].to_numpy(), T_BALANCE_BOUNDS)]
delta = sn * max(0, tn - Tmin)
print(f'\n=== REAL WPUQ feeder (37 houses, true HP_Peak {HP_Peak:.1f} kW, Tmin {Tmin:.1f} C) ===')
print(f'  net-load delta = {delta:.1f} kW')
for name, sf in [('old  : Swiss coldest-day constant 0.42', SF_COLD_SWISS),
                 ('NEW  : SF_Swiss(Tmin=-5.4)           ', float(sf_swiss(Tmin))),
                 ('oracle: own SF at coldest day        ', 0.322)]:
    cap = delta / sf
    print(f'  {name} (SF={sf:.3f}): capacity {cap:6.1f} kW   error {(cap-HP_Peak)/HP_Peak*100:+5.1f}%')
