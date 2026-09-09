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

# feeder OWN SF fit
sb, ss, st, sr2 = fit_hockey_stick(T, sf, T_BALANCE_BOUNDS)
sf_own = float(np.clip(sb + ss * max(0.0, st - Tmin), 0, 1))
sf_swiss = float(np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, SWISS['t_thr'] - Tmin), 0, 1))
print(f'own SF fit:  base {sb:.3f}, slope {ss:.4f}/C, T_h^SF {st:.1f} C, R2 {sr2:.3f}; SF(Tmin) own {sf_own:.3f}')
print(f'Swiss SF curve: slope {SWISS["slope"]:.4f}/C, T_h^SF {SWISS["t_thr"]:.1f}; SF(Tmin) transferred {sf_swiss:.3f}')

# hybrid: Swiss SF SLOPE, but SF threshold taken from the observable net-load fit
sf_hybrid = float(np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, nt - Tmin), 0, 1))
print(f'hybrid SF(Tmin) = Swiss slope at net-load T_h ({nt:.1f} C) = {sf_hybrid:.3f}')

# capacity estimates (Eq 5): deployable / hybrid / oracle
for name, sfv in [('deployable (transferred Swiss SF)', sf_swiss),
                  ('hybrid (Swiss slope, net-load T_h)', sf_hybrid),
                  ('oracle (own SF)', sf_own)]:
    pred = delta / sfv
    print(f'  {name:36s}: P_max = {pred:5.0f} kW   error {(pred-TRUE_KW)/TRUE_KW*100:+5.1f}%')

# ---- figure -----------------------------------------------------------------
hf.use_style()
Tg = np.linspace(Tmin, T.max(), 200)
fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)   # threshold tick, as in Figs 1-2

ax[0].scatter(T, net, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily net load')
ax[0].plot(Tg, nb + ns * np.maximum(0, nt - Tg), color=hf.C_DE, lw=1.9, label=f'hockey fit ($R^2$ {nr2:.2f})')
# net-load threshold, marked as in Figs 1-2 (shared with the hybrid SF threshold in panel B)
y0, y1 = ax[0].get_ylim(); hA = 0.16 * (y1 - y0)
ax[0].vlines(nt, nb, nb + hA, **gth)
ax[0].annotate('$T_h$', xy=(nt, nb + hA), xytext=(3, 1), textcoords='offset points', fontsize=9, color='0.3')
ax[0].set(xlabel='daily mean temperature (°C)', ylabel='feeder net load (kW)')
ax[0].legend(fontsize=7, loc='upper right')

ax[1].scatter(T, sf, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily feeder SF')
ax[1].plot(Tg, np.clip(sb + ss * np.maximum(0, st - Tg), 0, 1), color=hf.C_DE, lw=1.9,
           label=f'feeder fit ($T_h^{{SF}}$ {st:.1f}°C)')
sw_thr = SWISS['t_thr']
ax[1].plot(Tg, np.clip(SWISS['base'] + SWISS['slope'] * np.maximum(0, sw_thr - Tg), 0, 1),
           color=hf.C_CH, lw=1.9, ls=(0, (4, 2)), label=f'Swiss transferred ($T_h^{{SF}}$ {sw_thr:.1f}°C)')
ax[1].plot(Tg, np.clip(SWISS['base'] + SWISS['slope'] * np.maximum(0, nt - Tg), 0, 1),
           color=hf.C_AC, lw=1.9, ls=(0, (1, 1)), label=f'hybrid (Swiss slope, net-load $T_h$ {nt:.1f}°C)')
ax[1].axvline(Tmin, color='0.5', lw=0.8, ls=(0, (2, 2)))
ax[1].plot([Tmin, Tmin, Tmin], [sf_own, sf_swiss, sf_hybrid], color=hf.C_HP, lw=0, marker='o', ms=2.5)
# hybrid SF threshold, marked as in Figs 1-2, and shared with the net-load T_h of panel A
hyb_base = float(np.clip(SWISS['base'], 0, 1))
ax[1].vlines(nt, hyb_base, hyb_base + 0.11, **gth)
ax[1].annotate('$T_h$', xy=(nt, hyb_base + 0.11), xytext=(3, 1), textcoords='offset points', fontsize=9, color='0.3')
ax[1].set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
ax[1].legend(fontsize=6.5, loc='upper right')
fig.tight_layout()
hf.save(fig, 'fig_real_feeder')
print('\nsaved -> paper/figures/fig_real_feeder')
