# -*- coding: utf-8 -*-
"""Figure 3 (Austin variant): the simultaneity factor of the Austin furnace
(air-handler) circuits. The furnace blower runs in BOTH heating and cooling, so
its SF against temperature is bathtub-shaped: it rises on the cold side (heating)
and the hot side (cooling), with a flat centre. A single bathtub is fitted and
its arms coloured as in Fig. 2 (heating red, cooling blue, base grey)."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf
import austin_sf as asf
from hp_capacity import robust_series_peak
from hp_common import fit_bathtub_stick

hf.use_style()

# furnace (air-handler) load per household -> installed capacity and daily aggregate
df = asf.df.copy()
df['furn'] = df[['furnace1', 'furnace2']].sum(axis=1, min_count=1)
peaks, daily = [], []
for hid, g in df.groupby('dataid'):
    s = g.set_index('local_15min')['furn'].dropna()
    if len(s) < 1000:
        continue
    pk = robust_series_peak(s)
    if not np.isfinite(pk) or pk < 0.1:
        continue
    peaks.append(pk)
    daily.append(s.resample('D').mean())
cap = float(np.nansum(peaks))
agg = pd.concat(daily, axis=1).sum(axis=1, min_count=1)
sf = (agg / cap).clip(0, 1)
d = pd.DataFrame({'T': asf.T, 'sf': sf}).dropna()
Tv, Sv = d['T'].to_numpy(), d['sf'].to_numpy()

base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, Sv)
print(f'furnace SF bathtub: {len(peaks)} households, cap {cap:.0f} kW, '
      f'base {base:.3f} hs {hs:.4f} Th {th:.1f} cs {cs:.4f} Tc {tc:.1f} R2 {r2:.3f} n {len(d)}')

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.scatter(Tv, Sv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
xa = np.linspace(Tv.min(), th, 100)
xd = np.linspace(tc, Tv.max(), 100)
ax.plot(xa, np.clip(base + hs * (th - xa), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
ax.plot(xd, np.clip(base + cs * (xd - tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)

# threshold-temperature markers
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
hf.save(fig, 'fig_sf_austin')
print('saved -> paper/figures/fig_sf_austin')
