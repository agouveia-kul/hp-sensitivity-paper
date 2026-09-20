# -*- coding: utf-8 -*-
"""D: zero-HP control. Aggregate only heat-pump-free households (no electric
heating) on the largest station, fit the net-load hockey stick, and run the
capacity estimator. Any positive slope is the neglected non-ETL temperature
response; the inferred capacity where no HP exists is the false positive."""
import numpy as np, pandas as pd
import hp_pools as hpp
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

SF_REF = 0.42
p = hpp.build_pool_combined(verbose=False)
idx = p['index']; w = p['weather_of']
hh = list(p['households']); orow = {h: i for i, h in enumerate(hh)}
other = p['other_mat']
hp_set = set(p['hp_households']); eheat = set(p.get('eheat_households', []))
clean_klo = [h for h in hh if w.get(h) == 'KLO' and h not in hp_set and h not in eheat]
temp = pd.Series(p['temperature']['KLO'], index=idx); Td = temp.resample('D').mean()
Tmin = float(Td.min())
print(f'{len(clean_klo)} heat-pump-free (no electric heating) households on KLO')

rng = np.random.default_rng(0)
rows = []
for N in [10, 20, 50, 100, 200]:
    if N > len(clean_klo):
        continue
    for _ in range(50):
        m = rng.choice(clean_klo, N, replace=False)
        net = other[[orow[h] for h in m]].sum(axis=0)
        nd = pd.Series(net, index=idx).resample('D').mean()
        d = pd.DataFrame({'T': Td, 'y': nd}).dropna()
        b, s, t, r2 = fit_hockey_stick(d['T'].to_numpy(), d['y'].to_numpy(), T_BALANCE_BOUNDS)
        delta = s * max(0.0, t - Tmin)
        rows.append(dict(N=N, slope=s, delta=delta, cap=delta / SF_REF,
                         base=b, per_home=delta / SF_REF / N))
g = pd.DataFrame(rows).groupby('N').median(numeric_only=True)
print('\nzero-HP control, median over 50 draws per size:')
print('  N   net-load slope(kW/C)  delta(kW)  inferred cap(kW)  per home(kW)')
for N, r in g.iterrows():
    print(f'  {N:3d}   {r.slope:8.2f}          {r.delta:7.1f}    {r.cap:9.1f}      {r.per_home:.3f}')
print(f'\nreference: a real HP draws ~2.5-11 kW peak each; SF_ref={SF_REF}')
print('interpretation: inferred cap here is the capacity the estimator would')
print('report on a HP-free feeder -- the non-ETL false positive.')
