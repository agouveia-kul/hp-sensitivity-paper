# -*- coding: utf-8 -*-
"""Sensitivity of the daily flexible energy to the thermal-inertia window Delta t.
Each day's heating energy must be met; within a window Delta t the population can
reshape it, giving daily flex energy E_flex(d) = SF_d (1-SF_d) P_max Delta t
(up = down). Computed over a year for the Swiss KLO heat-pump population from the
measured daily SF, swept over Delta t."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf, hp_pools as hpp
from hp_capacity import robust_series_peak

hf.use_style()
p = hpp.build_pool_combined(verbose=False)
idx = p['index']; w = p['weather_of']
rows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == 'KLO']
Pmax = float(sum(robust_series_peak(p['hp_mat'][r]) for r in rows))     # kW
load = pd.Series(p['hp_mat'][rows].sum(axis=0), index=idx).resample('D').mean()
T = pd.Series(p['temperature']['KLO'], index=idx).resample('D').mean()
d = pd.DataFrame({'T': T, 'sf': (load / Pmax).clip(0, 1)}).dropna()
print(f'KLO population: {len(rows)} HPs, P_max {Pmax:.0f} kW, {len(d)} days, mean SF {d.sf.mean():.3f}')

DTS = [1, 2, 4, 6, 8, 12, 24]                                  # hours
flex = {dt: d.sf * (1 - d.sf) * Pmax * dt for dt in DTS}       # kWh/day per Delta t
annual = {dt: float(flex[dt].sum()) / 1000 for dt in DTS}      # MWh/yr

fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
doy = np.arange(len(d))
for dt in [2, 4, 8, 24]:
    ax[0].plot(doy, flex[dt].values, lw=1.0, label=f'$\\Delta t$={dt} h')
ax[0].set(xlabel='day of year', ylabel='daily flexible energy (kWh)')
ax[0].legend(fontsize=6.5, loc='upper right', ncol=2)
ax[1].plot(DTS, [annual[dt] for dt in DTS], color=hf.C_HP, lw=1.6, marker='o', ms=4)
ax[1].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flexible energy (MWh)')
fig.tight_layout()
hf.save(fig, 'fig_flex_dt_sensitivity')

print('\nannual flexible energy vs Delta t:')
for dt in DTS:
    print(f'  dt={dt:2d} h : {annual[dt]:6.1f} MWh/yr   (peak day {flex[dt].max():.0f} kWh, '
          f'{flex[dt].max()/(Pmax*dt)*100:.0f}% of P_max*dt)')
print(f'\nfraction of days with non-trivial flex (>5% of max): '
      f'{(d.sf.between(0.05,0.95)).mean()*100:.0f}%')
print('saved -> paper/figures/fig_flex_dt_sensitivity')
