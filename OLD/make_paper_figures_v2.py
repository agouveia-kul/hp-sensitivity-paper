# -*- coding: utf-8 -*-
"""Three figures for the reworked full paper: real-feeder SF, capacity scatter
and flexibility envelope. Styled to match hp_figures."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

hf.use_style()
BASE_S, SLOPE_S, THR_S = 0.027, 0.0161, 16.45          # Swiss pooled SF curve


def sf_swiss(T):
    return np.clip(BASE_S + SLOPE_S * np.maximum(0.0, THR_S - T), 0, 1)


# ---------------------------------------------------------------- 1. real feeder
def fig_real_feeder_sf():
    d = pd.read_csv('data/wpuq_real_feeder_sf.csv')
    T, SF = d['Temp'].to_numpy(), d['SF'].to_numpy()
    b, s, t, r = [float(x) for x in fit_hockey_stick(T, SF, T_BALANCE_BOUNDS)]
    Tmin = T.min()
    xg = np.linspace(min(Tmin, -10), 18, 100)
    fig, ax = plt.subplots(figsize=(hf.COL1, 2.9))
    ax.scatter(T, SF, s=6, c='0.75', alpha=.5, edgecolors='none', label='daily, real feeder', rasterized=True)
    ax.plot(xg, np.clip(b + s * np.maximum(0, t - xg), 0, 1), color=hf.C_DE, lw=1.8,
            label=f'WPUQ feeder fit ($R^2$={r:.2f})')
    ax.plot(xg, sf_swiss(xg), color=hf.C_CH, lw=1.6, ls='--', label='Swiss curve (transferred)')
    sfc = b + s * max(0, t - Tmin)
    ax.plot([Tmin], [sfc], 'o', color=hf.C_DE, ms=5)
    ax.annotate(f'0.32 at {Tmin:.1f}$^\\circ$C', (Tmin, sfc), textcoords='offset points',
                xytext=(6, -2), fontsize=6.5, color=hf.C_DE)
    ax.plot([Tmin], [sf_swiss(Tmin)], 'o', color=hf.C_CH, ms=4)
    ax.annotate('0.38', (Tmin, sf_swiss(Tmin)), textcoords='offset points',
                xytext=(6, 2), fontsize=6.5, color=hf.C_CH)
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('simultaneity factor')
    ax.set_ylim(0, 0.7)
    ax.legend(loc='upper right')
    fig.tight_layout()
    hf.save(fig, 'fig_real_feeder_sf')
    print('real feeder: slope', round(s, 4), 'thr', round(t, 1), 'R2', round(r, 2), 'SFcold', round(sfc, 3))


# ------------------------------------------------------------ 2. capacity scatter
def fig_capacity_scatter():
    d = pd.read_csv('data/capacity_two_methods_swiss.csv')
    d = d[(d.HP_Peak > 0) & (d.delta > 0)].dropna(subset=['delta', 'HP_Peak', 'SF_cold'])
    rng = np.random.default_rng(0)
    idx = np.arange(len(d)); rng.shuffle(idx)
    tr = d.iloc[idx[:len(idx) // 2]]; te = d.iloc[idx[len(idx) // 2:]]
    b = np.sum(tr.delta * tr.HP_Peak) / np.sum(tr.delta ** 2)
    sf_ref = float(tr.SF_cold.median())
    p1 = b * te.delta.to_numpy()
    p2 = te.delta.to_numpy() / sf_ref
    y = te.HP_Peak.to_numpy()
    mx = max(y.max(), p1.max(), p2.max()) * 1.02
    fig, ax = plt.subplots(figsize=(hf.COL1, 3.1))
    ax.plot([0, mx], [0, mx], color='0.4', lw=0.8, ls=':')
    ax.scatter(y, p1, s=7, c=hf.C_CH, alpha=.45, edgecolors='none', label='regression (18.5%)')
    ax.scatter(y, p2, s=7, c=hf.C_HP, alpha=.45, edgecolors='none', label='transferred SF (23.8%)')
    ax.set_xlabel('true installed capacity (kW)')
    ax.set_ylabel('estimated capacity (kW)')
    ax.set_xlim(0, mx); ax.set_ylim(0, mx)
    ax.set_aspect('equal')
    ax.legend(loc='upper left', title='within Switzerland, MAPE')
    fig.tight_layout()
    hf.save(fig, 'fig_capacity_scatter')
    print('capacity scatter: b', round(b, 2), 'sf_ref', round(sf_ref, 3), 'n_test', len(te))


# --------------------------------------------------------- 3. flexibility envelope
def fig_flexibility_envelope():
    T = np.linspace(-10, 18, 200)
    sf = sf_swiss(T)
    fig, ax = plt.subplots(figsize=(hf.COL1, 2.9))
    ax.fill_between(T, sf, 1.0, color=hf.C_AC, alpha=.22, lw=0, label='available (idle) fraction')
    ax.fill_between(T, 0.0, sf, color=hf.C_HP, alpha=.22, lw=0, label='drawn fraction')
    ax.plot(T, sf, color=hf.C_HP, lw=1.6)
    Tc = -8.2
    ax.axvline(Tc, color='0.5', lw=0.7, ls=':')
    ax.annotate('coldest day:\n$\\sim$58% idle', (Tc, 0.7), textcoords='offset points',
                xytext=(6, 0), fontsize=6.5)
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('fraction of installed heat pump capacity')
    ax.set_ylim(0, 1); ax.set_xlim(T.min(), T.max())
    ax.legend(loc='center right')
    fig.tight_layout()
    hf.save(fig, 'fig_flexibility_envelope')
    print('flexibility envelope saved')


if __name__ == '__main__':
    fig_real_feeder_sf()
    fig_capacity_scatter()
    fig_flexibility_envelope()
    print('done -> paper/figures/fig_real_feeder_sf, fig_capacity_scatter, fig_flexibility_envelope')
