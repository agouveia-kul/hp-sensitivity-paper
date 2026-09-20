# -*- coding: utf-8 -*-
"""Validation on the real WPUQ feeder: apply the deployable capacity estimator
(net-load fit + transferred Swiss SF) and compare with the feeder's own SF."""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import hp_figures as hf
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

TRUE_KW = 238.51424035310907                      # measured installed HP capacity
SWISS = dict(base=0.027, slope=0.0161, t_thr=16.4)  # pooled Swiss SF reference curve

d = pd.read_csv('data/wpuq_real_feeder_sf.csv', index_col=0, parse_dates=True)
T = d['Temp'].to_numpy(); net = d['net'].to_numpy(); sf = d['SF'].to_numpy()
Tmin = float(np.min(T))
print(f'real feeder: {len(d)} days, T range [{Tmin:.1f}, {T.max():.1f}] C, true capacity {TRUE_KW:.0f} kW')

# net-load hockey fit -> coincident-peak proxy delta
nb, ns, nt, nr2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
delta = ns * max(0.0, nt - Tmin)
print(f'net-load fit: base {nb:.1f} kW, slope {ns:.2f} kW/C, T_h {nt:.1f} C, R2 {nr2:.3f}; delta {delta:.1f} kW')

# feeder OWN SF fit, anchored at the net-load threshold (T_h^SF = T_h by convention):
# only the slope and base are fitted, on the days below the net-load threshold.
st = nt
_mb = T < st
ss, sb = np.polyfit(st - T[_mb], sf[_mb], 1)          # sf = sb + ss*(st - T)
sr2 = float(1 - np.sum((sf[_mb] - (sb + ss * (st - T[_mb]))) ** 2) /
            np.sum((sf[_mb] - sf[_mb].mean()) ** 2))
sf_own = float(np.clip(sb + ss * max(0.0, st - Tmin), 0, 1))
sf_swiss = float(np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, SWISS['t_thr'] - Tmin), 0, 1))
print(f'own SF fit:  base {sb:.3f}, slope {ss:.4f}/C, T_h^SF {st:.1f} C, R2 {sr2:.3f}; SF(Tmin) own {sf_own:.3f}')
print(f'Swiss SF curve: slope {SWISS["slope"]:.4f}/C, T_h^SF {SWISS["t_thr"]:.1f}; SF(Tmin) transferred {sf_swiss:.3f}')

# hybrid: Swiss SF SLOPE, but SF threshold taken from the observable net-load fit
sf_hybrid = float(np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, nt - Tmin), 0, 1))
print(f'hybrid SF(Tmin) = Swiss slope at net-load T_h ({nt:.1f} C) = {sf_hybrid:.3f}')

# capacity estimates (Eq 5): default (net-load T_h) / oracle (own SF)
for name, sfv in [('default (Swiss slope, net-load T_h)', sf_hybrid),
                  ('oracle (own SF)', sf_own)]:
    pred = delta / sfv
    print(f'  {name:36s}: P_max = {pred:5.0f} kW   error {(pred-TRUE_KW)/TRUE_KW*100:+5.1f}%')

# ---- figure -----------------------------------------------------------------
hf.use_style()
Tg = np.linspace(Tmin, nt, 150)                       # sloped arm, below the threshold
Tmax = float(T.max())
gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)   # T_h marker, as in Figs 2, 3, 7
fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))

# left: net-load fit = orange heating arm + dark-grey dead-band line
ax[0].scatter(T, net, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily net load')
ax[0].plot(Tg, nb + ns * (nt - Tg), color=hf.C_DE, lw=1.9, label=r'$\hat{P}_{\mathrm{net}}(T)$')
ax[0].plot([nt, Tmax], [nb, nb], color='0.35', lw=1.9, zorder=4)   # dead-band line
ax[0].set(xlabel='daily mean temperature (°C)', ylabel='feeder net load (kW)')
y0b = ax[0].get_ylim()[0]
ax[0].vlines(nt, y0b, 40, **gth); ax[0].set_ylim(bottom=y0b)
ax[0].annotate('$T_h$', xy=(nt, 40), xytext=(0, 3), textcoords='offset points',
               ha='center', va='bottom', fontsize=9, color='0.3')
leg0 = ax[0].legend(fontsize=7, loc='upper right')
fig.canvas.draw()                                    # realise legend extent
lx0 = leg0.get_window_extent().transformed(ax[0].transAxes.inverted()).x0
ax[0].text(lx0, 0.72, f'$R^2$ {nr2:.2f}', transform=ax[0].transAxes,
           ha='left', va='center', fontsize=7, color='0.3')

# right: SF, feeder own fit vs transferred Swiss slope, both anchored at the net-load T_h
ax[1].scatter(T, sf, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily feeder SF')
ax[1].plot(Tg, np.clip(sb + ss * (nt - Tg), 0, 1), color=hf.C_DE, lw=1.9, label='feeder own SF')
ax[1].plot(Tg, np.clip(SWISS['base'] + SWISS['slope'] * (nt - Tg), 0, 1),
           color=hf.C_HP, lw=2.1, label='transferred')
xl1 = ax[1].get_xlim()
ax[1].axvspan(nt, xl1[1], color='0.5', alpha=.12, lw=0, zorder=0)   # above T_h, excluded
ax[1].set_xlim(xl1)
ax[1].axvline(Tmin, color='0.5', lw=0.8, ls=(0, (2, 2)))
ax[1].plot([Tmin, Tmin], [sf_own, sf_hybrid], color=hf.C_HP, lw=0, marker='o', ms=2.5)
ax[1].vlines(nt, 0, 0.20, **gth)
ax[1].annotate('$T_h$', xy=(nt, 0.20), xytext=(0, 3), textcoords='offset points',
               ha='center', va='bottom', fontsize=9, color='0.3')
ax[1].set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
ax[1].legend(fontsize=7, loc='upper right')
fig.tight_layout()
hf.save(fig, 'fig_real_feeder')
print('\nsaved -> paper/figures/fig_real_feeder')
