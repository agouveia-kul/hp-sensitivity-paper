# -*- coding: utf-8 -*-
"""Test the paper's net-load fit (all FeederBW feeders) and the deployable
installed-capacity estimate (HP-dominant subset) on the FeederBW dataset.

FeederBW gives feeder-head net load + temperature; the metadata gives registered
electric-heating capacity. No submetering, so the SF cannot be fitted here -- the
Swiss reference SF is transferred, as in the WPUQ validation."""
import numpy as np, pandas as pd, pickle, os
import hp_capacity as hc
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

SWISS = dict(base=0.027, slope=0.0161, t_thr=16.4)   # pooled Swiss SF reference
CACHE = 'data/_feederbw_daily_cache.pkl'

if os.path.exists(CACHE):
    daily, cap = pickle.load(open(CACHE, 'rb'))
    print(f'loaded cache: {len(daily)} feeders')
else:
    print('loading FeederBW (all downloaded feeders) ...', flush=True)
    fbw, static, end = hc.load_feederbw('data/FeederBW', year=2024)
    cap = hc.feederbw_capacity_frame(fbw.index, static, end)
    daily = {}
    for fid in fbw.index:
        L = pd.Series(fbw.loc[fid, 'Total_Load']); T = pd.Series(fbw.loc[fid, 'Temperature'])
        d = pd.DataFrame({'T': T.resample('D').mean(), 'y': L.resample('D').mean()}).dropna()
        if len(d) >= 60:
            daily[fid] = d
    pickle.dump((daily, cap), open(CACHE, 'wb'))
    print(f'cached: {len(daily)} feeders with >=60 daily points')

# ---- net-load fit sweep (all feeders) --------------------------------------
rows = []
for fid, d in daily.items():
    T, y = d['T'].to_numpy(), d['y'].to_numpy()
    try:
        b, s, t, r2 = fit_hockey_stick(T, y, T_BALANCE_BOUNDS)
    except Exception:
        continue
    Tmin = float(T.min())
    rows.append(dict(fid=fid, base=b, slope=s, Th=t, r2=r2, Tmin=Tmin,
                     delta=s * max(0.0, t - Tmin),
                     ElecHeat_kW=cap.ElecHeat_kW.get(fid, np.nan),
                     HP_kW=cap.HP_kW.get(fid, np.nan),
                     HP_frac=cap.HP_frac.get(fid, np.nan),
                     housing=cap.housing.get(fid, np.nan)))
f = pd.DataFrame(rows)
print(f'\n=== NET-LOAD FIT SWEEP ({len(f)} feeders) ===')
print(f'  R2      median {f.r2.median():.3f}  [IQR {f.r2.quantile(.25):.3f}, {f.r2.quantile(.75):.3f}]')
print(f'  slope   median {f.slope.median():.2f} kW/C')
print(f'  Th      median {f.Th.median():.1f} C  [IQR {f.Th.quantile(.25):.1f}, {f.Th.quantile(.75):.1f}]')
print(f'  R2 by housing tertile:')
f['htile'] = pd.qcut(f.housing, 3, labels=['small', 'mid', 'large'], duplicates='drop')
print(f.groupby('htile', observed=True).agg(n=('r2', 'size'), med_R2=('r2', 'median'),
      med_housing=('housing', 'median')).round(3).to_string())
print(f'  Pearson r(housing, R2) = {f[["housing","r2"]].dropna().corr().iloc[0,1]:.2f}')

# ---- capacity test on HP-dominant subset -----------------------------------
def sf_at(Tmin, thr):  # transferred Swiss SF evaluated at Tmin, with threshold thr
    return float(np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, thr - Tmin), 0, 1))

hp = f[(f.HP_frac >= 0.5) & (f.HP_kW > 0) & (f.delta > 0)].copy()
hp['sf_dep'] = [sf_at(r.Tmin, SWISS['t_thr']) for r in hp.itertuples()]
hp['sf_hyb'] = [sf_at(r.Tmin, r.Th) for r in hp.itertuples()]
hp['cap_dep'] = hp.delta / hp.sf_dep
hp['cap_hyb'] = hp.delta / hp.sf_hyb
hp['e_dep'] = (hp.cap_dep - hp.HP_kW) / hp.HP_kW * 100
hp['e_hyb'] = (hp.cap_hyb - hp.HP_kW) / hp.HP_kW * 100
print(f'\n=== CAPACITY TEST, HP-dominant feeders (HP_frac>=0.5), n={len(hp)} ===')
print('  target = registered HP nameplate capacity HP_kW')
print(hp[['fid', 'HP_frac', 'HP_kW', 'cap_dep', 'cap_hyb', 'e_dep', 'e_hyb']].round(1).to_string(index=False))
def wape(p, a): return np.abs(p - a).sum() / a.sum() * 100
if len(hp):
    print(f'\n  deployable (transferred Swiss SF): WAPE {wape(hp.cap_dep, hp.HP_kW):.0f}%  median ratio {np.median(hp.cap_dep/hp.HP_kW):.2f}')
    print(f'  hybrid (Swiss slope, net-load Th): WAPE {wape(hp.cap_hyb, hp.HP_kW):.0f}%  median ratio {np.median(hp.cap_hyb/hp.HP_kW):.2f}')
f.to_csv('data/feederbw_paper_test.csv', index=False)
print('\nsaved -> data/feederbw_paper_test.csv')
