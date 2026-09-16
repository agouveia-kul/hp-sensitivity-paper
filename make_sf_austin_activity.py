# -*- coding: utf-8 -*-
"""SF with activity-based per-arm installed capacity, then a bathtub fit.

Reuses make_austin_arm_capacity for the device list, activity flags, per-arm
capacities and net-load thresholds. Each day's SF is the load of the devices
active in that day's regime, divided by that arm's installed capacity:
  T < T_h : heating-active load / Cap_H
  band    : band-active load    / Cap_B
  T > T_c : cooling-active load / Cap_C
A bathtub curve is then fitted to the resulting SF(T) points."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf
import make_austin_arm_capacity as m
from hp_common import fit_bathtub_stick

hf.use_style()
devices = m.devices
CapH, CapC, CapB = m.capH, m.capC, m.capB
T_h0, T_c0 = m.T_h, m.T_c
Tser = m.Tds
idx = Tser.index

def arm_sum(flag):
    s = pd.Series(0.0, index=idx)
    for dv in devices:
        if dv[flag]:
            s = s.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
    return s

heatsum, coolsum, bandsum = arm_sum('a_h'), arm_sum('a_c'), arm_sum('a_b')
mask_h, mask_c = Tser < T_h0, Tser > T_c0
mask_b = ~(mask_h | mask_c)
SF = pd.Series(index=idx, dtype=float)
SF[mask_h] = heatsum[mask_h] / CapH
SF[mask_c] = coolsum[mask_c] / CapC
SF[mask_b] = bandsum[mask_b] / CapB
d = pd.DataFrame({'T': Tser, 'sf': SF.clip(0, 1)}).dropna()
Tv, Sv = d['T'].to_numpy(), d['sf'].to_numpy()

base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, Sv)
print(f'activity-SF bathtub: base {base:.3f} hs {hs:.4f} Th {th:.1f} cs {cs:.4f} Tc {tc:.1f} R2 {r2:.3f}')
print(f'  Cap_H {CapH:.0f}  Cap_B {CapB:.0f}  Cap_C {CapC:.0f} kW')
print(f'  SF cold {d[d.T < th]["sf"].max():.2f}  band {d[(d.T>=th)&(d.T<=tc)]["sf"].median():.2f}  '
      f'hot {d[d.T > tc]["sf"].max():.2f}')

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

# base fraction and arm slopes, coloured to match each arm
ax.annotate('$b$', xy=((th + tc) / 2, base), xytext=(0, 6), textcoords='offset points',
            ha='center', va='bottom', fontsize=9, color='0.2')
arw = dict(arrowstyle='-', lw=0.6, color='0.5')
xm = th - (th - Tv.min()) * 0.5
ax.annotate('$m$', xy=(xm, base + hs * (th - xm)), xytext=(-16, 10),
            textcoords='offset points', fontsize=9, color=hf.C_HP, arrowprops=arw)
xmc = tc + (Tv.max() - tc) * 0.5
ax.annotate('$m_c$', xy=(xmc, base + cs * (xmc - tc)), xytext=(-20, 8),
            textcoords='offset points', fontsize=9, color=hf.C_CH, arrowprops=arw)
ax.set_xlabel('daily mean temperature ($^\\circ$C)')
ax.set_ylabel('simultaneity factor')
ax.set_ylim(0, 1)
ax.legend(fontsize=7, loc='upper left')
ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes,
        ha='left', va='top', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_sf_austin_activity')
print('saved -> paper/figures/fig_sf_austin_activity')
