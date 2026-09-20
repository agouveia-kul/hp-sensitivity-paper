# -*- coding: utf-8 -*-
"""Exploratory: a single COMBINED SF for the whole Austin ETL population, summing
every thermostatic circuit (AC + furnace + resistive heaters) per household. The
installed capacity is the sum of the household combined peaks; the SF is the daily
aggregate over that capacity. A bathtub is fitted and its arms coloured as in Fig. 2."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf
import austin_sf as asf
from hp_capacity import robust_series_peak
from hp_common import fit_bathtub_stick

hf.use_style()
ETL = asf.COOL + asf.HEAT                          # air1/2/3, airwindowunit1, furnace1/2, heater1/2/3
df = asf.df.copy()
df['etl'] = df[[c for c in ETL if c in df]].sum(axis=1, min_count=1)

peaks, daily = [], []
for hid, g in df.groupby('dataid'):
    s = g.set_index('local_15min')['etl'].dropna()
    if len(s) < 1000:
        continue
    pk = robust_series_peak(s)
    if not np.isfinite(pk) or pk < 0.2:
        continue
    peaks.append(pk)
    daily.append(s.resample('D').mean())
cap = float(np.nansum(peaks))
agg = pd.concat(daily, axis=1).sum(axis=1, min_count=1)
sf = (agg / cap).clip(0, 1)
d = pd.DataFrame({'T': asf.T, 'sf': sf}).dropna()
Tv, Sv = d['T'].to_numpy(), d['sf'].to_numpy()

base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, Sv)
sf_cold = d.sort_values('T').head(5)['sf'].mean()
sf_hot = d.sort_values('T').tail(5)['sf'].mean()
print(f'combined ETL SF: {len(peaks)} households, cap {cap:.0f} kW, '
      f'base {base:.3f} hs {hs:.4f} Th {th:.1f} cs {cs:.4f} Tc {tc:.1f} R2 {r2:.3f}')
print(f'  SF_cold {sf_cold:.3f}  SF_hot {sf_hot:.3f}  max daily SF {Sv.max():.3f}')

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.scatter(Tv, Sv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
xa = np.linspace(Tv.min(), th, 100)
xd = np.linspace(tc, Tv.max(), 100)
ax.plot(xa, np.clip(base + hs * (th - xa), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
ax.plot(xd, np.clip(base + cs * (xd - tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)
gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
ax.vlines(th, base, base + 0.12, **gth)
ax.annotate('$T_h^{\\mathrm{SF}}$', xy=(th, base + 0.12), xytext=(-3, 1),
            textcoords='offset points', ha='right', fontsize=9, color='0.3')
ax.vlines(tc, base, base + 0.12, **gth)
ax.annotate('$T_c^{\\mathrm{SF}}$', xy=(tc, base + 0.12), xytext=(3, 1),
            textcoords='offset points', fontsize=9, color='0.3')
ax.set_xlabel('daily mean temperature ($^\\circ$C)')
ax.set_ylabel('simultaneity factor')
ax.set_ylim(0, 1)
ax.legend(fontsize=7, loc='upper left')
ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes,
        ha='left', va='top', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_sf_austin_combined')
print('saved -> paper/figures/fig_sf_austin_combined')
