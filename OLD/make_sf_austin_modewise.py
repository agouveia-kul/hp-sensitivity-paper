# -*- coding: utf-8 -*-
"""Mode-specific SF for the Austin ETL population. Each regime is normalised by
its own installed capacity: the heating arm (T < T_h) by the heating-capable
ETLs, the cooling arm (T > T_c) by the cooling-capable ETLs, and the dead band by
all ETLs. Because the denominator switches at the thresholds, the SF is piecewise
and generally steps there."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf
import austin_sf as asf
from hp_capacity import robust_series_peak
from hp_common import fit_bathtub_stick

hf.use_style()

# heating- and cooling-only SF are already computed in austin_sf (per-mode load / per-mode cap)
dh, dc = asf.dh, asf.dc
cap_h, cap_c = asf.cap_h, asf.cap_c

# all-ETL SF: sum every thermostatic circuit per household, cap = sum of household peaks
ETL = asf.COOL + asf.HEAT
df = asf.df.copy()
df['etl'] = df[[c for c in ETL if c in df]].sum(axis=1, min_count=1)
peaks, daily = [], []
for _, g in df.groupby('dataid'):
    s = g.set_index('local_15min')['etl'].dropna()
    if len(s) < 1000:
        continue
    pk = robust_series_peak(s)
    if not np.isfinite(pk) or pk < 0.2:
        continue
    peaks.append(pk)
    daily.append(s.resample('D').mean())
cap_a = float(np.nansum(peaks))
da = pd.DataFrame({'T': asf.T, 'sf': (pd.concat(daily, axis=1).sum(axis=1, min_count=1) / cap_a).clip(0, 1)}).dropna()

# thresholds from the all-ETL bathtub set the regime boundaries
base_a, _, th, _, tc, _ = fit_bathtub_stick(da['T'].to_numpy(), da['sf'].to_numpy())

# linear fits of each arm on its own regime (below-threshold heating is linear in T_h - T)
mh_hot = dh[dh['T'] < th]
mc_hot = dc[dc['T'] > tc]
m_h, b_h = np.polyfit(th - mh_hot['T'], mh_hot['sf'], 1)          # sf = b_h + m_h*(th - T)
m_c, b_c = np.polyfit(mc_hot['T'] - tc, mc_hot['sf'], 1)          # sf = b_c + m_c*(T - tc)
base_band = da[(da['T'] >= th) & (da['T'] <= tc)]['sf'].mean()

def r2(x, y, yhat):
    ss = np.sum((y - y.mean()) ** 2)
    return 1 - np.sum((y - yhat) ** 2) / ss if ss > 0 else np.nan
r2h = r2(mh_hot['T'].to_numpy(), mh_hot['sf'].to_numpy(), b_h + m_h * (th - mh_hot['T']).to_numpy())
r2c = r2(mc_hot['T'].to_numpy(), mc_hot['sf'].to_numpy(), b_c + m_c * (mc_hot['T'] - tc).to_numpy())
print(f'Cap_H {cap_h:.0f}  Cap_C {cap_c:.0f}  Cap_A {cap_a:.0f} kW   Th {th:.1f}  Tc {tc:.1f}')
print(f'heating arm: b {b_h:.3f} m {m_h:.4f} R2 {r2h:.3f} | cooling arm: b {b_c:.3f} m {m_c:.4f} R2 {r2c:.3f}')
print(f'band base (all-ETL) {base_band:.3f}   steps: heat {abs(b_h-base_band):.3f}  cool {abs(b_c-base_band):.3f}')

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
# scatter, each regime normalised by its own capacity
ax.scatter(dh[dh['T'] < th]['T'], dh[dh['T'] < th]['sf'], s=8, color=hf.C_HP, alpha=.30, edgecolor='none')
ax.scatter(dc[dc['T'] > tc]['T'], dc[dc['T'] > tc]['sf'], s=8, color=hf.C_CH, alpha=.30, edgecolor='none')
band = da[(da['T'] >= th) & (da['T'] <= tc)]
ax.scatter(band['T'], band['sf'], s=8, color='0.55', alpha=.35, edgecolor='none')
ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)

# fitted piecewise arms (drawn separately -> the steps at th, tc are visible)
xh = np.linspace(dh['T'].min(), th, 100)
xc = np.linspace(tc, dc['T'].max(), 100)
ax.plot(xh, np.clip(b_h + m_h * (th - xh), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
ax.plot([th, tc], [base_band, base_band], color='0.2', lw=1.9, zorder=4, label='base load')
ax.plot(xc, np.clip(b_c + m_c * (xc - tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
# thin connectors marking the denominator-switch steps
stp = dict(color='0.45', lw=0.8, ls=(0, (2, 2)), zorder=3)
ax.plot([th, th], [base_band, b_h], **stp)
ax.plot([tc, tc], [base_band, b_c], **stp)
ax.annotate('$T_h^{\\mathrm{SF}}$', xy=(th, max(b_h, base_band)), xytext=(-3, 3),
            textcoords='offset points', ha='right', fontsize=9, color='0.3')
ax.annotate('$T_c^{\\mathrm{SF}}$', xy=(tc, max(b_c, base_band)), xytext=(3, 3),
            textcoords='offset points', fontsize=9, color='0.3')

ax.set_xlabel('daily mean temperature ($^\\circ$C)')
ax.set_ylabel('simultaneity factor')
ax.set_ylim(0, 1)
ax.legend(fontsize=7, loc='upper left')
ax.text(0.035, 0.72, f'$R^2$ {r2h:.2f} (heat), {r2c:.2f} (cool)', transform=ax.transAxes,
        ha='left', va='top', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_sf_austin_modewise')
print('saved -> paper/figures/fig_sf_austin_modewise')
