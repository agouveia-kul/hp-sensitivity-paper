# -*- coding: utf-8 -*-
"""Figure 2: the simultaneity-factor function fitted to an HP population on Swiss
data (the 50 heat pumps on the largest weather station, pooled). Legend top-left,
R^2 below it, threshold temperature T_h^SF marked as in Fig. 1."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf, hp_pools as hpp
from hp_capacity import robust_series_peak
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

hf.use_style()
p = hpp.build_pool_combined(verbose=False)
idx = p['index']; w = p['weather_of']
hp_hh = [h for h in p['hp_households'] if w.get(h) == 'KLO']
rows = [p['hp_households'].index(h) for h in hp_hh]
cap = sum(robust_series_peak(p['hp_mat'][r]) for r in rows)
load = p['hp_mat'][rows].sum(axis=0)
sf = pd.Series(load, index=idx).resample('D').mean() / cap
T = pd.Series(p['temperature']['KLO'], index=idx).resample('D').mean()
d = pd.DataFrame({'T': T, 'sf': sf}).dropna()
Tv, Sv = d['T'].to_numpy(), d['sf'].to_numpy()
b, s, t, r2 = fit_hockey_stick(Tv, Sv, T_BALANCE_BOUNDS)
print(f'KLO SF example: base {b:.3f} slope {s:.4f} Th {t:.1f} R2 {r2:.3f} n {len(d)}')
Tg = np.linspace(Tv.min(), Tv.max(), 200)

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.scatter(Tv, Sv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
ax.plot(Tg, np.clip(b + s * np.maximum(0, t - Tg), 0, 1), color=hf.C_HP, lw=1.9, label='SF fit', zorder=4)
# threshold temperature marker (as in Fig. 1)
gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
ax.vlines(t, b, b + 0.12, **gth)
ax.annotate('$T_h^{\\mathrm{SF}}$', xy=(t, b + 0.12), xytext=(3, 1),
            textcoords='offset points', fontsize=9, color='0.3')
ax.set_xlabel('daily mean temperature ($^\\circ$C)')
ax.set_ylabel('simultaneity factor')
ax.set_ylim(0, 0.8)
ax.legend(fontsize=7, loc='upper left')
ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes, ha='left', va='top', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_sf_example')
print('saved -> paper/figures/fig_sf_example')
