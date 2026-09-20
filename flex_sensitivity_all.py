# -*- coding: utf-8 -*-
"""Daily flexible-energy sensitivity to Delta t, three views:
 (a) estimated vs actual for the Swiss KLO HP population,
 (b) distribution of annual flex across the 1000 factorial substations,
 (c) the real WPUQ feeder, estimated vs actual.
E_flex(d) = SF_d (1-SF_d) P_max Delta t; annual flex is linear in Delta t, so we
carry the per-hour coefficient C = sum_d SF_d(1-SF_d) P_max  [kWh per hour]."""
import numpy as np, pandas as pd, pickle, matplotlib.pyplot as plt
import hp_figures as hf, hp_pools as hpp
from hp_capacity import robust_series_peak
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS
from sf_transfer import build_frames
from capacity_two_methods import fits_frame

hf.use_style()
SW = dict(base=0.027, slope=0.0161, thr=16.4)
def sfcurve(T, thr=SW['thr']):
    return np.clip(SW['base'] + SW['slope'] * np.maximum(0.0, thr - np.asarray(T)), 0, 1)
def coef(sf, cap):                      # kWh of daily flex per hour of Delta t, summed over year
    sf = np.asarray(sf); return float(np.sum(sf * (1 - sf)) * cap)
DTS = np.array([1, 2, 4, 6, 8, 12, 24])

# ================= (a) KLO population: estimated vs actual =================
p = hpp.build_pool_combined(verbose=False)
idx = p['index']; w = p['weather_of']
hh = p['households']; orow = {h: i for i, h in enumerate(hh)}
klo = [h for h in p['hp_households'] if w.get(h) == 'KLO']
hrow = [p['hp_households'].index(h) for h in klo]
Pmax = float(sum(robust_series_peak(p['hp_mat'][r]) for r in hrow))
Td = pd.Series(p['temperature']['KLO'], index=idx).resample('D').mean()
sf_meas = (pd.Series(p['hp_mat'][hrow].sum(axis=0), index=idx).resample('D').mean() / Pmax).clip(0, 1)
net = pd.Series((p['hp_mat'][hrow] + p['other_mat'][[orow[h] for h in klo]]).sum(axis=0), index=idx).resample('D').mean()
a = pd.DataFrame({'T': Td, 'sf': sf_meas, 'net': net}).dropna()
nb, ns, nt, nr2 = fit_hockey_stick(a['T'].to_numpy(), a['net'].to_numpy(), T_BALANCE_BOUNDS)
delta = ns * max(0.0, nt - a['T'].min())
cap_est = delta / float(sfcurve(a['T'].min()))
sf_est = sfcurve(a['T'].to_numpy())
flex_act = a['sf'].to_numpy() * (1 - a['sf'].to_numpy()) * Pmax          # kWh per hour dt
flex_est = sf_est * (1 - sf_est) * cap_est
print(f'(a) KLO: P_max true {Pmax:.0f} kW, est {cap_est:.0f} kW; net-load R2 {nr2:.2f}')
print(f'    annual flex per hour dt: actual {flex_act.sum()/1000:.1f} MWh, est {flex_est.sum()/1000:.1f} MWh  '
      f'(ratio {flex_est.sum()/flex_act.sum():.2f})')

fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
doy = np.arange(len(a))
ax[0].plot(doy, flex_act * 4, color='0.5', lw=0.9, label='actual (measured SF)')
ax[0].plot(doy, flex_est * 4, color=hf.C_HP, lw=1.1, label='estimated (transferred SF)')
ax[0].set(xlabel='day of year', ylabel='daily flexible energy (kWh)', title='$\\Delta t = 4$ h')
ax[0].legend(fontsize=6.5, loc='upper right')
ax[1].plot(DTS, flex_act.sum() / 1000 * DTS, color='0.5', lw=1.4, marker='o', ms=3, label='actual')
ax[1].plot(DTS, flex_est.sum() / 1000 * DTS, color=hf.C_HP, lw=1.4, marker='s', ms=3, label='estimated')
ax[1].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flexible energy (MWh)')
ax[1].legend(fontsize=7, loc='upper left')
fig.tight_layout(); hf.save(fig, 'fig_flex_klo_est_act')

# ================= (b) distribution across 1000 substations =================
subs = build_frames(pickle.load(open('data/design_factorial.pkl', 'rb')))
fr = fits_frame(pickle.load(open('data/design_factorial.pkl', 'rb'))).set_index('sid')
sf_ref = float(fr.SF_cold.median())
rows = []
for s in subs:
    sid = s['sid']
    if sid not in fr.index:
        continue
    sf_d = np.clip(s['SF'], 0, 1)
    C_act = coef(sf_d, s['HP_Peak'])                       # actual, per hour dt
    sfe = sfcurve(s['T'])
    cap_e = float(fr.loc[sid, 'delta'] / sf_ref) if fr.loc[sid, 'delta'] > 0 else np.nan
    C_est = coef(sfe, cap_e)
    rows.append(dict(N_hp=int(round(s['hp_ratio'] * s['N_total'])), C_act=C_act, C_est=C_est,
                     ratio=C_est / C_act if C_act > 0 else np.nan))
b = pd.DataFrame(rows).dropna()
print(f'\n(b) {len(b)} substations. annual flex per hour dt (kWh): '
      f'median {b.C_act.median():.0f} [IQR {b.C_act.quantile(.25):.0f}, {b.C_act.quantile(.75):.0f}]')
print(f'    est/actual annual ratio: median {b.ratio.median():.2f} '
      f'[IQR {b.ratio.quantile(.25):.2f}, {b.ratio.quantile(.75):.2f}]')

fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
q = {dt: (b.C_act * dt / 1000) for dt in DTS}              # MWh per substation
med = [q[dt].median() for dt in DTS]
lo = [q[dt].quantile(.25) for dt in DTS]; hi = [q[dt].quantile(.75) for dt in DTS]
ax[0].fill_between(DTS, lo, hi, color=hf.C_CH, alpha=.25, lw=0, label='IQR')
ax[0].plot(DTS, med, color=hf.C_CH, lw=1.6, marker='o', ms=3, label='median')
ax[0].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flex per substation (MWh)')
ax[0].legend(fontsize=7, loc='upper left')
ax[1].hist(b.ratio.clip(0, 2.5), bins=40, color=hf.C_HP, alpha=.8, edgecolor='none')
ax[1].axvline(1, color='0.4', lw=0.8, ls=(0, (3, 3)))
ax[1].axvline(b.ratio.median(), color=hf.C_CH, lw=1.4, label=f'median {b.ratio.median():.2f}')
ax[1].set(xlabel='estimated / actual annual flex', ylabel='substations')
ax[1].legend(fontsize=7, loc='upper right')
fig.tight_layout(); hf.save(fig, 'fig_flex_distribution')

# ================= paper figures for V-F (split into two) =================
# fig_flex_season: daily flexible energy over the year, estimated vs actual (KLO)
DT_REF = 4                                                       # h, representative window
import matplotlib.dates as mdates
fig, ax = plt.subplots(figsize=(hf.COL1, 2.7))
ax.plot(a.index, flex_act * DT_REF, color='0.5', lw=0.9, label='actual')
ax.plot(a.index, flex_est * DT_REF, color=hf.C_HP, lw=1.0, label='estimated')
ax.set(xlabel='month', ylabel=f'daily flexible energy (kWh), $\\Delta t = {DT_REF}$ h')
ax.xaxis.set_major_locator(mdates.MonthLocator((1, 4, 7, 10)))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.legend(fontsize=7, loc='upper right')
fig.tight_layout(); hf.save(fig, 'fig_flex_season')
frac_nontrivial = float((a['sf'].between(0.05, 0.95)).mean() * 100)
print(f'    seasonal: {frac_nontrivial:.0f}% of days non-trivial flex; '
      f'peak-day SF {a["sf"].max():.2f}, flex/(Pmax*dt) {(a["sf"]*(1-a["sf"])).max():.2f}')

# fig_flex_ratio: distribution of estimated/actual annual flex across substations
fig, ax = plt.subplots(figsize=(hf.COL1, 2.7))
ax.hist(b.ratio.clip(0, 2.5), bins=40, color=hf.C_CH, alpha=.8, edgecolor='none')
ax.axvline(1, color='0.4', lw=0.8, ls=(0, (3, 3)))
ax.axvline(b.ratio.median(), color=hf.C_HP, lw=1.6, label=f'median {b.ratio.median():.2f}')
ax.set(xlabel='estimated / actual annual flex', ylabel='substations')
ax.legend(fontsize=7.5, loc='upper right')
fig.tight_layout(); hf.save(fig, 'fig_flex_ratio')

# ================= (c) WPUQ real feeder =================
d = pd.read_csv('data/wpuq_real_feeder_sf.csv', index_col=0, parse_dates=True)
CAP_TRUE = 238.5
Tw, sfw, netw = d['Temp'].to_numpy(), np.clip(d['SF'].to_numpy(), 0, 1), d['net'].to_numpy()
nb, ns, nt, _ = fit_hockey_stick(Tw, netw, T_BALANCE_BOUNDS)
delta_w = ns * max(0.0, nt - Tw.min())
cap_w = delta_w / float(sfcurve(Tw.min(), thr=nt))         # hybrid: net-load threshold
sfw_est = sfcurve(Tw, thr=nt)                              # hybrid SF curve
flex_act_w = sfw * (1 - sfw) * CAP_TRUE
flex_est_w = sfw_est * (1 - sfw_est) * cap_w
print(f'\n(c) WPUQ feeder: cap true {CAP_TRUE:.0f} kW, est(hybrid) {cap_w:.0f} kW')
print(f'    annual flex per hour dt: actual {flex_act_w.sum()/1000:.2f} MWh, est {flex_est_w.sum()/1000:.2f} MWh  '
      f'(ratio {flex_est_w.sum()/flex_act_w.sum():.2f})')

fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
doy = np.arange(len(Tw))
ax[0].plot(doy, flex_act_w * 4, color='0.5', lw=0.9, label='actual (measured SF)')
ax[0].plot(doy, flex_est_w * 4, color=hf.C_DE, lw=1.1, label='estimated (transferred SF)')
ax[0].set(xlabel='day of year', ylabel='daily flexible energy (kWh)', title='$\\Delta t = 4$ h')
ax[0].legend(fontsize=6.5, loc='upper right')
ax[1].plot(DTS, flex_act_w.sum() / 1000 * DTS, color='0.5', lw=1.4, marker='o', ms=3, label='actual')
ax[1].plot(DTS, flex_est_w.sum() / 1000 * DTS, color=hf.C_DE, lw=1.4, marker='s', ms=3, label='estimated')
ax[1].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flexible energy (MWh)')
ax[1].legend(fontsize=7, loc='upper left')
fig.tight_layout(); hf.save(fig, 'fig_flex_wpuq_est_act')
print('\nsaved -> fig_flex_klo_est_act, fig_flex_distribution, fig_flex_wpuq_est_act')
