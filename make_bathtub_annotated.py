# -*- coding: utf-8 -*-
"""Regenerate Figure 1: the Austin bathtub fit, with the terms of Equation (1)
(P_base, T_h, T_c, s_h, s_c) mapped onto the curve."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf, pecan_street as ps
from hp_common import bathtub_stick, fit_bathtub_stick, fit_cooling_stick

hf.use_style()
pecan_daily, _ = ps.load_austin_ac_pool(verbose=False)
agg = None
for d in pecan_daily.values():
    agg = d['load'].copy() if agg is None else agg.add(d['load'], fill_value=0)
T = pd.concat([d['T'] for d in pecan_daily.values()], axis=1).mean(axis=1)
df = pd.DataFrame({'T': T, 'y': agg}).dropna()
Tv, yv = df['T'].to_numpy(), df['y'].to_numpy()
base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, yv)
_, _, _, r2c = fit_cooling_stick(Tv, yv)
Tg = np.linspace(Tv.min(), Tv.max(), 300)
print(f'base {base:.1f} hs {hs:.2f} th {th:.1f} cs {cs:.2f} tc {tc:.1f} R2 {r2:.3f} n {len(df)}')

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.grid(False)
ax.scatter(Tv, yv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean load')
xa = np.linspace(Tv.min(), th, 100)
xd = np.linspace(tc, Tv.max(), 100)
ax.plot(xa, base + hs * (th - xa), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
ax.plot(xd, base + cs * (xd - tc), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)
y0 = yv.min() - 3
ax.set_ylim(y0, yv.max() * 1.06)

# --- map Equation (1) terms onto the curve ---
g = dict(color='0.35', lw=0.8, ls=(0, (3, 3)), zorder=3)
# P_base: flat dead-band level
ax.hlines(base, th, tc, **g)
ax.annotate(r'$P_{\mathrm{base}}$', xy=(th, base), xytext=(4, 8),
            textcoords='offset points', fontsize=8, color='0.15')
# thresholds T_h, T_c
for xT, lab, dx in [(th, r'$T_h$', -1), (tc, r'$T_c$', 1)]:
    ax.vlines(xT, y0, base, **g)
    ax.annotate(lab, xy=(xT, y0), xytext=(dx * 6, 3), textcoords='offset points',
                ha='center', fontsize=8, color='0.15')
# slopes s_h, s_c on the two arms
xh = th - (th - Tv.min()) * 0.45; yh = base + hs * (th - xh)
ax.annotate(r'$s_h$', xy=(xh, yh), xytext=(-16, 12), textcoords='offset points',
            fontsize=8, color=hf.C_HP, arrowprops=dict(arrowstyle='-', lw=0.6, color='0.5'))
xc = tc + (Tv.max() - tc) * 0.45; yc = base + cs * (xc - tc)
ax.annotate(r'$s_c$', xy=(xc, yc), xytext=(-20, 6), textcoords='offset points',
            fontsize=8, color=hf.C_CH, arrowprops=dict(arrowstyle='-', lw=0.6, color='0.5'))

ax.set_xlabel('daily mean temperature (°C)')
ax.set_ylabel('aggregate load (kW)')
ax.legend(fontsize=7, loc='upper left')
ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes, ha='left', va='top', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_bathtub_example')
print('saved -> paper/figures/fig_bathtub_example')
