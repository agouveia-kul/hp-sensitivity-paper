# -*- coding: utf-8 -*-
"""Figure and table generators for ``paper_results.ipynb``.

One function per paper artifact, folded from the former per-figure/per-table
scripts. Shared helpers (fitters, styling, data loaders, the cross-dataset
fitter) come from ``utils``; the heavier data-pipeline modules that the other
notebooks also use (``hp_pools``, ``hp_design``, ``hp_analysis``,
``hp_capacity``, ``pecan_street``) are imported lazily inside each function so
``import outputs`` stays cheap and never triggers a data load on its own.

Every function writes its PDF/PNG to ``paper/figures`` or its ``.tex`` to
``paper/tables`` (via ``utils.save`` / direct write) and returns nothing except
where noted.
"""
import os
import pickle

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import hp_figures as hf
from hp_common import (fit_hockey_stick, fit_cooling_stick, fit_bathtub_stick,
                       bathtub_stick, T_BALANCE_BOUNDS)
import utils as U

SWISS_SF = dict(base=0.0288, slope=0.01795, t_thr=16.55)  # full Kloten pilot SF fit at its net-load T_h (50 HPs, 2023, robust peaks)
WPUQ_TRUE_KW = 238.51424035310907                       # measured WPUQ installed HP capacity
SF_PLAN = 0.425                                          # planning HP SF of national LV studies [Few24]

# Only the SF slope m_h transfers from the submetered pilot to a target. The
# target's temperature-driven SF is m_h * (T_h - T), anchored at zero at the
# target's own net-load threshold T_h: the net-load ETL arm is zero at T_h and
# the weather-independent ETL share (the pilot's intercept b_h) sits in P_base.
# Hence the per-regime capacity s_h / m_h, independent of temperature.
M_SWISS = SWISS_SF['slope']


def sf_target(T, t_h, m=M_SWISS):
    """Transferred temperature-driven SF of a target: m * (T_h - T), clipped."""
    return np.clip(m * np.maximum(0.0, t_h - np.asarray(T)), 0, 1)


# ===========================================================================
# Section 1 -- net-load bathtub
# ===========================================================================
def fig_bathtub_example():
    """Fig. 2: Austin bathtub fit with the terms of Eq. (1) mapped onto it."""
    import pecan_street as ps
    hf.use_style()
    pecan_daily, _ = ps.load_austin_ac_pool(verbose=False)
    agg = None
    for d in pecan_daily.values():
        agg = d['load'].copy() if agg is None else agg.add(d['load'], fill_value=0)
    T = pd.concat([d['T'] for d in pecan_daily.values()], axis=1).mean(axis=1)
    df = pd.DataFrame({'T': T, 'y': agg}).dropna()
    Tv, yv = df['T'].to_numpy(), df['y'].to_numpy()
    base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, yv)

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
    g = dict(color='0.35', lw=0.8, ls=(0, (3, 3)), zorder=3)
    ax.hlines(base, th, tc, **g)
    ax.annotate(r'$P_{\mathrm{base}}$', xy=(th, base), xytext=(4, 8),
                textcoords='offset points', fontsize=8, color='0.15')
    for xT, lab, dx in [(th, r'$T_h$', -1), (tc, r'$T_c$', 1)]:
        ax.vlines(xT, y0, base, **g)
        ax.annotate(lab, xy=(xT, y0), xytext=(dx * 6, 3), textcoords='offset points',
                    ha='center', fontsize=8, color='0.15')
    xh = th - (th - Tv.min()) * 0.45; yh = base + hs * (th - xh)
    ax.annotate(r'$s_h$', xy=(xh, yh), xytext=(-16, 12), textcoords='offset points',
                fontsize=8, color=hf.C_HP, arrowprops=dict(arrowstyle='-', lw=0.6, color='0.5'))
    xc = tc + (Tv.max() - tc) * 0.45; yc = base + cs * (xc - tc)
    ax.annotate(r'$s_c$', xy=(xc, yc), xytext=(-20, 6), textcoords='offset points',
                fontsize=8, color=hf.C_CH, arrowprops=dict(arrowstyle='-', lw=0.6, color='0.5'))
    # regimes: R1 heating (below T_h), R2 dead band, R3 cooling (above T_c)
    for (lo, hi), lab in zip([(Tv.min(), th), (th, tc), (tc, Tv.max())], ['R1', 'R2', 'R3']):
        ax.text((lo + hi) / 2, 0.05, lab, transform=ax.get_xaxis_transform(), ha='center', va='bottom',
                fontsize=8.5, color='0.35', fontweight='bold', zorder=6)
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('aggregate load (kW)')
    ax.legend(fontsize=7, loc='upper left')
    # each arm scored on the days of its own regime only (dead band excluded)
    r2h = _arm_r2(Tv, yv, th, hs, base)
    mc = Tv > tc; yc = yv[mc]
    r2c = float(1 - np.sum((yc - (base + cs * (Tv[mc] - tc))) ** 2) / np.sum((yc - yc.mean()) ** 2))
    ax.text(0.035, 0.72, f'$R^2_h$ {r2h:.2f}, $R^2_c$ {r2c:.2f}', transform=ax.transAxes,
            ha='left', va='top', fontsize=7, color='0.3')
    print(f'bathtub example: R2_h {r2h:.3f} R2_c {r2c:.3f} (all days {r2:.3f})')
    fig.tight_layout()
    hf.save(fig, 'fig_bathtub_example')
    print('saved -> fig_bathtub_example')


def fig_bathtub_critical():
    """Fig. 4: bathtub with arms extrapolated to SF->1 and regions R1-R5."""
    hf.use_style()
    m = U.load_austin_arm_capacity()
    Tv, yv = m.d['T'].to_numpy(), m.d['net'].to_numpy()
    base, hs, th, cs, tc = m.base, m.s_h, m.T_h, m.s_c, m.T_c
    capH, capC = m.capH, m.capC
    peak_h = hs * (th - Tv.min())
    peak_c = cs * (Tv.max() - tc)
    cap_h = base + capH
    cap_c = base + capC
    Th_crit = th - capH / hs
    Tc_crit = tc + capC / cs

    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.grid(False)
    ax.scatter(Tv, yv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean load')
    xa = np.linspace(Tv.min(), th, 100)
    xd = np.linspace(tc, Tv.max(), 100)
    ax.plot(xa, base + hs * (th - xa), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
    ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
    ax.plot(xd, base + cs * (xd - tc), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
    ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)
    ax.plot([Tv.min(), Th_crit], [base + peak_h, cap_h],
            color=hf.C_HP, lw=1.4, ls=(0, (4, 2)), zorder=4, label='extrapolation ($\\mathrm{SF}\\!\\to\\!1$)')
    ax.plot([Tv.max(), Tc_crit], [base + peak_c, cap_c],
            color=hf.C_CH, lw=1.4, ls=(0, (4, 2)), zorder=4)
    g = dict(color='0.35', lw=0.8, ls=(0, (3, 3)), zorder=3)
    y0 = yv.min() - 3
    ax.vlines(Th_crit, y0, cap_h, **g)
    ax.vlines(Tc_crit, y0, cap_c, **g)
    ax.plot(Th_crit, cap_h, 'o', color=hf.C_HP, ms=5, zorder=5)
    ax.plot(Tc_crit, cap_c, 'o', color=hf.C_CH, ms=5, zorder=5)
    ax.annotate(r'$T_h^{\mathrm{crit}}$', xy=(Th_crit, y0), xytext=(4, 3),
                textcoords='offset points', ha='left', fontsize=8, color='0.15')
    ax.annotate(r'$T_c^{\mathrm{crit}}$', xy=(Tc_crit, y0), xytext=(4, 3),
                textcoords='offset points', ha='left', fontsize=8, color='0.15')
    ax.annotate(r'$P_h^{\max}$', xy=(Th_crit, cap_h), xytext=(0, 6),
                textcoords='offset points', ha='center', va='bottom', fontsize=8, color=hf.C_HP)
    ax.annotate(r'$P_c^{\max}$', xy=(Tc_crit, cap_c), xytext=(0, 6),
                textcoords='offset points', ha='center', va='bottom', fontsize=8, color=hf.C_CH)
    tmin, tmax = Tv.min(), Tv.max()
    for xb in (tmin, tmax):
        ax.axvline(xb, color='0.75', lw=0.6, ls=(0, (1, 2)), zorder=1)
    ax.set_xlim(Th_crit - 8, Tc_crit + 8)
    ax.set_ylim(y0, cap_c * 1.30)
    for (lo, hi), lab in zip([(Th_crit, tmin), (tmin, th), (th, tc), (tc, tmax), (tmax, Tc_crit)],
                             ['R4', 'R1', 'R2', 'R3', 'R5']):
        ax.text((lo + hi) / 2, 60, lab, ha='center', va='center', fontsize=8.5,
                color='0.35', fontweight='bold', zorder=6)
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('aggregate load (kW)')
    ax.legend(fontsize=7, loc='upper left')
    fig.tight_layout()
    hf.save(fig, 'fig_bathtub_critical')
    print('saved -> fig_bathtub_critical')


# ===========================================================================
# Section 2 -- simultaneity factor
# ===========================================================================
def fig_sf_arms_anchored():
    """Fig. 3 (overleaf): SF arms fit independently, anchored at the net-load thresholds."""
    hf.use_style()
    m = U.load_austin_arm_capacity()
    devices = m.devices
    CapH, CapC = m.capH, m.capC
    Th, Tc = m.T_h, m.T_c
    Tser = m.Tds
    idx = Tser.index

    def arm_sum(flag):
        s = pd.Series(0.0, index=idx)
        for dv in devices:
            if dv[flag]:
                s = s.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
        return s
    heatsum, coolsum = arm_sum('a_h'), arm_sum('a_c')
    dh = pd.DataFrame({'T': Tser, 'sf': (heatsum / CapH).clip(0, 1)}).dropna()
    dh = dh[dh['T'] < Th]
    dc = pd.DataFrame({'T': Tser, 'sf': (coolsum / CapC).clip(0, 1)}).dropna()
    dc = dc[dc['T'] > Tc]
    mh, bh = np.polyfit(Th - dh['T'], dh['sf'], 1)
    mc, bc = np.polyfit(dc['T'] - Tc, dc['sf'], 1)

    def r2f(x, y, mm, bb):
        ss = np.sum((y - y.mean()) ** 2)
        return 1 - np.sum((y - (mm * x + bb)) ** 2) / ss
    r2h = r2f((Th - dh['T']).to_numpy(), dh['sf'].to_numpy(), mh, bh)
    r2c = r2f((dc['T'] - Tc).to_numpy(), dc['sf'].to_numpy(), mc, bc)
    Tmin, Tmax = dh['T'].min(), dc['T'].max()

    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.grid(False)
    ax.scatter(dh['T'], dh['sf'], s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
    ax.scatter(dc['T'], dc['sf'], s=8, color='0.65', alpha=.45, edgecolor='none')
    ax.axvspan(Th, Tc, color='0.5', alpha=.08, lw=0)
    xa = np.linspace(Tmin, Th, 100)
    xd = np.linspace(Tc, Tmax, 100)
    ax.plot(xa, np.clip(bh + mh * (Th - xa), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
    ax.plot(xd, np.clip(bc + mc * (xd - Tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
    gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
    ax.vlines(Th, 0, 0.20, **gth)
    ax.annotate('$T_h$', xy=(Th, 0.20), xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, color='0.3')
    ax.vlines(Tc, 0, 0.20, **gth)
    ax.annotate('$T_c$', xy=(Tc, 0.20), xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, color='0.3')
    ax.annotate(r'$\hat{\mathrm{SF}}_h(T) = b_h + m_h\,(T_h - T)$',
                xy=(5, bh + mh * (Th - 5)), xytext=(0, 0.40), textcoords='data',
                ha='left', va='bottom', fontsize=8, color=hf.C_HP,
                arrowprops=dict(arrowstyle='-', lw=0.7, color=hf.C_HP))
    ax.annotate(r'$\hat{\mathrm{SF}}_c(T) = b_c + m_c\,(T - T_c)$',
                xy=(27, bc + mc * (27 - Tc)), xytext=(27, 0.60), textcoords='data',
                ha='center', va='bottom', fontsize=8, color=hf.C_CH,
                arrowprops=dict(arrowstyle='-', lw=0.7, color=hf.C_CH))
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('simultaneity factor')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, loc='upper left')
    ax.text(0.035, 0.72, f'$R^2_h$ {r2h:.2f}, $R^2_c$ {r2c:.2f}', transform=ax.transAxes,
            ha='left', va='top', fontsize=7, color='0.3')
    fig.tight_layout()
    hf.save(fig, 'fig_sf_arms_anchored')
    print('saved -> fig_sf_arms_anchored')


def fig_sf_austin_activity():
    """Fig. 3 (v5): activity-based SF with a bathtub fit."""
    hf.use_style()
    m = U.load_austin_arm_capacity()
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
    ax.annotate('$b$', xy=((th + tc) / 2, base), xytext=(0, 6), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, color='0.2')
    arw = dict(arrowstyle='-', lw=0.6, color='0.5')
    xm = th - (th - Tv.min()) * 0.5
    ax.annotate('$m_h$', xy=(xm, base + hs * (th - xm)), xytext=(-2, 10),
                textcoords='offset points', fontsize=9, color=hf.C_HP, arrowprops=arw)
    xmc = tc + (Tv.max() - tc) * 0.5
    ax.annotate('$m_c$', xy=(xmc, base + cs * (xmc - tc)), xytext=(-20, 8),
                textcoords='offset points', fontsize=9, color=hf.C_CH, arrowprops=arw)
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('simultaneity factor')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, loc='upper left')
    ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes, ha='left', va='top', fontsize=7, color='0.3')
    fig.tight_layout()
    hf.save(fig, 'fig_sf_austin_activity')
    print('saved -> fig_sf_austin_activity')


# ===========================================================================
# Section IV -- synthetic Kloten aggregates WITHOUT replacement
# ===========================================================================
KLOTEN_DESIGN = 'data/_kloten_design.pkl'
N_GRID_K = (10, 20, 30, 40, 50)
NHP_GRID_K = (5, 10, 15, 20, 25)


def _kloten_hourly():
    """Hourly means of the Kloten HP, own and HP-free household loads, in the
    same row order as ``_daily_pools()['KLO']`` (energy-resolution comparison)."""
    import hp_pools as hpp
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']; eheat = set(p.get('eheat_households', []))
    hp_set = set(p['hp_households'])
    hrows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == 'KLO']
    hps = [p['hp_households'][i] for i in hrows]
    orow = {h: i for i, h in enumerate(p['households'])}
    free = [h for h in p['households'] if w.get(h) == 'KLO' and h not in hp_set and h not in eheat]

    def hourly(rows, mat):
        return pd.DataFrame(mat[rows].T, index=p['index']).resample('h').mean().to_numpy(np.float32).T
    T = pd.Series(p['temperature']['KLO'], index=p['index']).resample('h').mean().to_numpy()
    return dict(T=T, hp=hourly(hrows, p['hp_mat']),
                own=hourly([orow[h] for h in hps], p['other_mat']),
                free=hourly([orow[h] for h in free], p['other_mat']))


def _metrics_k(T, hp, net, Th, hph, neth, cap, m):
    """Every Section IV quantity for one aggregate (daily and hourly series)."""
    _, sh, th, r2n = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
    sf = np.clip(hp / cap, 0, 1)
    below = T < th
    ab, am, sfmax, r2a = U._sf_arm(T, sf, th, 'h')                     # own SF at T_h (oracle)
    _, s1, t1, _ = fit_hockey_stick(Th, neth, T_BALANCE_BOUNDS)        # hourly net-load fit
    sf_e = sf_target(T, th, m); cap_e = sh / m
    fa, fe = sf * (1 - sf), sf_e * (1 - sf_e)
    k = int(np.argmin(T))
    return dict(s_h=sh, T_h=th, net_r2=r2n, m_own=am, m_anch=am, b_anch=ab, r2_anch=r2a,
                sfmax=sfmax,
                cap_est=cap_e, cap_or=sh / am,
                e_act=float(hph.sum()), e_act_d=float(hp.sum() * 24),
                e_dd=float((sh * np.maximum(0, th - T) * 24).sum()),
                e_hh=float((s1 * np.maximum(0, t1 - Th)).sum()),
                e_dh=float((sh * np.maximum(0, th - Th)).sum()),
                e_b_est=float((sh * (th - T[below]) * 24).sum()), e_b_act=float(hp[below].sum() * 24),
                flex_est=float(fe.sum() * cap_e), flex_act=float(fa.sum() * cap),
                flex_sfonly=float(fe.sum() * cap),
                flex_b_est=float(fe[below].sum() * cap_e), flex_b_act=float(fa[below].sum() * cap),
                flex_floor=float(fa[~below].sum() / fa.sum()),
                cold_est=float(fe[k] * cap_e), cold_act=float(fa[k] * cap))


def _pilot_fit(T, K, A):
    """SF fit of a pilot aggregate (HPs A with their homes' other load), anchored
    at the pilot's own net-load threshold. Returns (b_h, m_h, T_h)."""
    hp = K['hp'][A].sum(0)
    _, _, th, _ = fit_hockey_stick(T, hp + K['own'][A].sum(0), T_BALANCE_BOUNDS)
    b, m, _, _ = U._sf_arm(T, np.clip(hp / K['cap'][A].sum(), 0, 1), th, 'h')
    return b, m, th


def _kloten_design(n_splits=20, reps=3, seed=0, rebuild=False):
    """Synthetic Kloten aggregates drawn WITHOUT replacement, disjoint from their pilot.

    Each split halves the 50 Kloten HPs at random. The pilot half is aggregated
    and its SF fit (Eq. sffit) gives m_h. Every test aggregate draws N_hp
    distinct HPs of the other half, with the same homes' other load, plus
    N - N_hp distinct HP-free, non-electric-heating Kloten homes. Cached.
    """
    if os.path.exists(KLOTEN_DESIGN) and not rebuild:
        with open(KLOTEN_DESIGN, 'rb') as fh:
            return pickle.load(fh)
    K = _daily_pools()['KLO']; Kh = _kloten_hourly()
    T, Th = K['T'], Kh['T']
    rng = np.random.default_rng(seed); nfree = K['free'].shape[0]
    pilots, rows = [], []
    for s in range(n_splits):
        A, B = _pilot_split(len(K['cap']), rng)
        pb, pm, pt = _pilot_fit(T, K, A)
        pilots.append(dict(split=s, A=A, B=B, b=pb, m=pm, t=pt))
        for N in N_GRID_K:
            for nh in NHP_GRID_K:
                if nh > N:
                    continue
                for _ in range(reps):
                    H = rng.choice(B, nh, replace=False)
                    F = rng.choice(nfree, N - nh, replace=False) if N > nh else np.array([], int)
                    hp = K['hp'][H].sum(0); net = hp + K['own'][H].sum(0) + K['free'][F].sum(0)
                    hph = Kh['hp'][H].sum(0); neth = hph + Kh['own'][H].sum(0) + Kh['free'][F].sum(0)
                    cap = float(K['cap'][H].sum())
                    rows.append(dict(split=s, N=N, N_hp=nh, cap=cap, m_pilot=pm,
                                     **_metrics_k(T, hp, net, Th, hph, neth, cap, pm)))
    out = dict(rows=pd.DataFrame(rows), pilots=pilots, T=T, K=K)
    with open(KLOTEN_DESIGN, 'wb') as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    print(f'built {len(rows)} Kloten aggregates ({n_splits} splits x {reps} reps per cell)')
    return out


def _wape(est, act):
    est, act = np.asarray(est), np.asarray(act)
    return np.abs(est - act).sum() / act.sum() * 100


def tab_sf():
    """Table II (SF invariance, N = 50) and the pilot SF figure (fig_sf_pilot)."""
    from scipy.stats import spearmanr
    Dz = _kloten_design(); G = Dz['rows']
    g50 = G[G.N == 50]

    def iqr(x):
        return x.quantile(.75) - x.quantile(.25)
    par = g50.groupby('N_hp').agg(r2=('r2_anch', 'median'), ri=('r2_anch', iqr), sm=('sfmax', 'median'), si=('sfmax', iqr),
                                  bm=('b_anch', 'median'), bi=('b_anch', iqr),
                                  mm=('m_anch', 'median'), mi=('m_anch', iqr))
    body = "\n".join(f"{int(n)} & {r.r2:.2f}\\,({r.ri:.2f}) & {r.sm:.2f}\\,({r.si:.2f}) & {r.bm:.3f}\\,({r.bi:.3f}) & "
                     f"{r.mm:.4f}\\,({r.mi:.4f}) \\\\" for n, r in par.iterrows())
    tex = r"""\begin{table}[t]
\centering
\caption{SF fits of the Kloten aggregates, median (interquartile range, IQR)}
\label{tab:sf}
\begin{tabular}{rcccc}
\toprule
$N_{hp}$ & $R^2_h$ & SF$^{\max}_h$ & $b_h$ & $m_h$ ($^\circ$C$^{-1}$) \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_sf.tex', 'w').write(tex)
    pm = pd.Series([p['m'] for p in Dz['pilots']])
    print(f'{len(g50)} aggregates at N=50; Spearman m_anch vs N_hp {spearmanr(g50.N_hp, g50.m_anch).statistic:+.3f}, '
          f'vs capacity {spearmanr(g50.cap, g50.m_anch).statistic:+.3f}')
    print(f'pilot m_h over {len(pm)} splits: median {pm.median():.4f} IQR {pm.quantile(.25):.4f}-{pm.quantile(.75):.4f}')

    # pilot figure: the pilot half of split 0
    p0 = Dz['pilots'][0]; K = Dz['K']; T = Dz['T']
    sfA = K['hp'][p0['A']].sum(0) / K['cap'][p0['A']].sum()
    mb = T < p0['t']
    r2p = 1 - np.sum((sfA[mb] - (p0['b'] + p0['m'] * (p0['t'] - T[mb]))) ** 2) / np.sum((sfA[mb] - sfA[mb].mean()) ** 2)
    print(f"pilot split 0: b {p0['b']:.4f} m {p0['m']:.4f} T_h {p0['t']:.2f}, R2 below threshold {r2p:.3f}")
    hf.use_style()
    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.scatter(T, sfA, s=6, color='0.6', alpha=.5, edgecolor='none', label='daily pilot SF')
    ax.set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
    xl = ax.get_xlim(); ax.axvspan(p0['t'], xl[1], color='0.5', alpha=.12, lw=0, zorder=0); ax.set_xlim(xl)
    Tg = np.linspace(T.min(), p0['t'], 150)
    ax.plot(Tg, np.clip(p0['b'] + p0['m'] * (p0['t'] - Tg), 0, 1), color=hf.C_HP, lw=1.9, label='pilot SF fit')
    ax.legend(fontsize=7, loc='upper right')
    ax.text(0.035, 0.55 / 0.75, f"$R^2_h$ {r2p:.2f}\n$m_h$ {p0['m']:.4f}", transform=ax.transAxes,
            ha='left', va='center', fontsize=7, color='0.3')
    fig.tight_layout(); hf.save(fig, 'fig_sf_pilot')
    print('wrote tab_sf.tex, fig_sf_pilot')


def sf_controls(n_splits=120, n_reps=50, station='KLO', seed=0):
    """Household-disjoint SF transfer and the zero-HP control (robust peaks).

    (1) The station's HP households are split into two random halves, n_splits
        times. The pilot half's aggregate SF is fitted with Eq. (sffit); its whole
        curve is scored (R^2 below its threshold) on the target half's SF, the
        same metric as tab_sf's aggregate-level split. The target half's net
        load (its HPs plus the same households' other load) gives s_h, and
        s_h / m_pilot the capacity, against the robust-peak truth.
    (2) HP-free, non-electric-heating households of the station are aggregated
        (N = 10..50, n_reps each, without replacement); s_h / M_SWISS of their
        net-load fit is capacity the estimator infers where no HP exists.
    """
    import hp_pools as hpp
    from hp_capacity import robust_series_peak
    rng = np.random.default_rng(seed)
    p = hpp.build_pool_combined(verbose=False)
    idx = p['index']; w = p['weather_of']
    orow = {h: i for i, h in enumerate(p['households'])}
    hps = [h for h in p['hp_households'] if w.get(h) == station]
    hrow = {h: p['hp_households'].index(h) for h in hps}
    peak = {h: robust_series_peak(p['hp_mat'][hrow[h]]) for h in hps}
    Td = pd.Series(p['temperature'][station], index=idx).resample('D').mean()

    def daily(x):
        y = pd.Series(x, index=idx).resample('D').mean()
        d = pd.DataFrame({'T': Td, 'y': y}).dropna()
        return d['T'].to_numpy(), d['y'].to_numpy()

    rows = []
    for _ in range(n_splits):
        perm = rng.permutation(hps); A, B = perm[:len(perm) // 2], perm[len(perm) // 2:]
        TA, sfA = daily(p['hp_mat'][[hrow[h] for h in A]].sum(0) / sum(peak[h] for h in A))
        _, netA = daily(p['hp_mat'][[hrow[h] for h in A]].sum(0) + p['other_mat'][[orow[h] for h in A]].sum(0))
        _, _, tA, _ = fit_hockey_stick(TA, netA, T_BALANCE_BOUNDS)
        bA, mA, _, _ = U._sf_arm(TA, sfA, tA, 'h')                    # pilot SF at its own T_h
        capB = sum(peak[h] for h in B)
        TB, sfB = daily(p['hp_mat'][[hrow[h] for h in B]].sum(0) / capB)
        _, netB = daily(p['hp_mat'][[hrow[h] for h in B]].sum(0)
                        + p['other_mat'][[orow[h] for h in B]].sum(0))
        _, sh, tB, _ = fit_hockey_stick(TB, netB, T_BALANCE_BOUNDS)
        mb = TB < tB                                                   # pilot curve at the target's T_h
        pred = bA + mA * (tB - TB[mb])
        r2 = 1 - np.sum((sfB[mb] - pred) ** 2) / np.sum((sfB[mb] - sfB[mb].mean()) ** 2)
        mB = U._sf_arm(TB, sfB, tB, 'h')[1]
        rows.append(dict(r2=r2, m_pilot=mA, cap_err=(sh / mA - capB) / capB * 100,
                         cap_err_oracle=(sh / mB - capB) / capB * 100))
    D = pd.DataFrame(rows)
    q = lambda s: f'{s.median():.3f} (IQR {s.quantile(.25):.3f}-{s.quantile(.75):.3f})'
    print(f'(1) household-disjoint, {len(A)} vs {len(B)} {station} HPs, {n_splits} splits:')
    print(f'    SF R2 (pilot curve at target T_h): {q(D.r2)}; pilot m_h {q(D.m_pilot)}')
    print(f'    capacity error s_h/m_pilot: {q(D.cap_err)} %; oracle own m: {q(D.cap_err_oracle)} %')

    eheat = set(p.get('eheat_households', []))
    free = [h for h in p['households'] if w.get(h) == station and h not in set(hps) and h not in eheat]
    zrows = []
    for n in (10, 20, 30, 40, 50):
        for _ in range(n_reps):
            mem = rng.choice(free, n, replace=False)
            T, y = daily(p['other_mat'][[orow[h] for h in mem]].sum(0))
            _, sh, _, _ = fit_hockey_stick(T, y, T_BALANCE_BOUNDS)
            zrows.append(dict(N=n, s_h=sh, per_house=max(sh, 0.0) / M_SWISS / n))
    Z = pd.DataFrame(zrows)
    mean_hp = np.mean(list(peak.values()))
    print(f'(2) zero-HP control, {len(free)} HP-free {station} households: spurious capacity per '
          f'household median {Z.per_house.median():.2f} kW (IQR {Z.per_house.quantile(.25):.2f}-'
          f'{Z.per_house.quantile(.75):.2f}); mean HP capacity {mean_hp:.2f} kW')
    print('    by N:', Z.groupby('N').per_house.median().round(2).to_dict())
    return D, Z


# ===========================================================================
# Hybrid evaluation -- real aggregates (headline) + without-replacement
# synthetic aggregates (sensitivity). Calendar 2023 (WPUQ: 2019), robust peaks.
# ===========================================================================
def _daily_pools():
    """Per-household daily means of HP and other load, robust peaks, daily T.

    A sum of daily means is the daily mean of the sum, so any aggregate's daily
    net load and SF follow from these matrices without touching 15-min data.
    """
    import hp_pools as hpp
    from hp_capacity import robust_series_peak

    def daily_mat(mat, idx):
        return pd.DataFrame(mat.T, index=idx).resample('D').mean()

    out = {}
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']; eheat = set(p.get('eheat_households', []))
    hpD = daily_mat(p['hp_mat'], p['index']); otD = daily_mat(p['other_mat'], p['index'])
    orow = {h: i for i, h in enumerate(p['households'])}
    for st in ('KLO', 'Hg', 'MqO'):
        hrows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == st]
        hps = [p['hp_households'][i] for i in hrows]
        free = [h for h in p['households'] if w.get(h) == st and h not in set(p['hp_households'])
                and h not in eheat]
        T = pd.Series(p['temperature'][st], index=p['index']).resample('D').mean()
        out[st] = dict(T=T.to_numpy(), hp=hpD.iloc[:, hrows].to_numpy().T,
                       own=otD.iloc[:, [orow[h] for h in hps]].to_numpy().T,
                       free=otD.iloc[:, [orow[h] for h in free]].to_numpy().T,
                       cap=np.array([robust_series_peak(p['hp_mat'][i]) for i in hrows]))
    q = hpp.build_pool_wpuq(verbose=False)
    T = pd.Series(q['temperature']['WPUQ'], index=q['index']).resample('D').mean()
    out['WPUQ'] = dict(T=T.to_numpy(), hp=daily_mat(q['hp_mat'], q['index']).to_numpy().T,
                       own=daily_mat(q['other_mat'], q['index']).to_numpy().T,
                       free=np.zeros((0, len(T))),
                       cap=np.array([robust_series_peak(q['hp_mat'][i]) for i in range(q['hp_mat'].shape[0])]))
    for k, v in out.items():
        ok = np.isfinite(v['T'])
        for f in ('T', 'hp', 'own', 'free'):
            v[f] = v[f][..., ok]
    return out


def _evaluate(T, hp, net, cap, m):
    """All use cases for one aggregate (daily hp and net sums, true capacity, pilot m)."""
    _, sh, th, r2n = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
    sf = np.clip(hp / cap, 0, 1)
    mo = U._sf_arm(T, sf, th, 'h')[1]
    cap_e = sh / m
    e_est = sh * np.maximum(0.0, th - T) * 24
    e_act = hp * 24
    below = T < th
    sf_e = sf_target(T, th, m)
    return dict(cap_err=(cap_e - cap) / cap * 100, cap_err_oracle=(sh / mo - cap) / cap * 100,
                cap_abs=abs(cap_e - cap), cap=cap, m_own=mo, net_r2=r2n,
                e_err=(e_est.sum() - e_act.sum()) / e_act.sum() * 100,
                e_err_below=(e_est[below].sum() - e_act[below].sum()) / e_act[below].sum() * 100,
                flex_ratio=np.sum(sf_e * (1 - sf_e)) * cap_e / (np.sum(sf * (1 - sf)) * cap))


def _pilot_split(n, rng):
    perm = rng.permutation(n)
    return perm[:n // 2], perm[n // 2:]


def norepl_sensitivity(n_splits=20, reps=5, seed=1, D=None,
                       n_hp_grid=(5, 10, 15, 20, 25), rate_grid=(0.02, 0.05, 0.10, 0.25, 0.50, 1.0)):
    """Sensitivity grid on synthetic Kloten aggregates drawn WITHOUT replacement.

    Per split: the pilot half of the Kloten HPs gives m_h; each aggregate draws
    N_hp distinct HPs from the other half (with the same homes' other load) and
    N_hp/rate - N_hp distinct HP-free households. No HP is shared between pilot
    and target, and none recurs within an aggregate.
    """
    D = _daily_pools() if D is None else D
    rng = np.random.default_rng(seed)
    K = D['KLO']; nfree = K['free'].shape[0]; rows = []
    for s in range(n_splits):
        A, B = _pilot_split(len(K['cap']), rng)
        _, m, _ = _pilot_fit(K['T'], K, A)
        for nh in n_hp_grid:
            for r in rate_grid:
                nf = int(round(nh / r)) - nh
                if nf > nfree:
                    continue
                for _ in range(reps):
                    H = rng.choice(B, nh, replace=False)
                    F = rng.choice(nfree, nf, replace=False) if nf else np.array([], int)
                    hp = K['hp'][H].sum(0)
                    net = hp + K['own'][H].sum(0) + K['free'][F].sum(0)
                    rows.append(dict(split=s, N_hp=nh, rate=r, N=nh + nf,
                                     **_evaluate(K['T'], hp, net, K['cap'][H].sum(), m)))
    G = pd.DataFrame(rows)

    def wape(g):
        return g.cap_abs.sum() / g.cap.sum() * 100
    print(f'{len(G)} aggregates ({n_splits} splits x {reps} reps per cell)')
    for metric, f in [('capacity WAPE %', wape),
                      ('capacity median error %', lambda g: g.cap_err.median()),
                      ('oracle median error %', lambda g: g.cap_err_oracle.median()),
                      ('energy (below T_h) median error %', lambda g: g.e_err_below.median()),
                      ('flex median ratio', lambda g: g.flex_ratio.median())]:
        tab = G.groupby(['N_hp', 'rate']).apply(f).unstack('rate')
        tab.columns = [f'{c * 100:g}%' for c in tab.columns]
        print(f'\n{metric} (rows N_hp, columns ETL rate):'); print(tab.round(2 if 'ratio' in metric else 1).to_string())
    sfm = G.groupby('N_hp').m_own.agg(['median', lambda x: x.quantile(.75) - x.quantile(.25)])
    sfm.columns = ['m_own median', 'IQR']
    print('\nown SF sensitivity by N_hp (invariance):'); print(sfm.round(4).to_string())
    return G


# ===========================================================================
# Section 3 -- energy and installed capacity
# ===========================================================================
def tab_energy():
    """tab_energy: fit/integration resolution on the Kloten aggregates."""
    G = _kloten_design()['rows']

    def r(name, c):
        return f"{name} & {_wape(G[c], G.e_act):.1f} & {np.median(G[c] / G.e_act):.2f} \\\\"
    tex = r"""\begin{table}[t]
\centering
\caption{Energy error on the Kloten aggregates}
\label{tab:energy}
\begin{tabular}{lcc}
\toprule
fit + integration & WAPE (\%) & median $\hat{E}_{\mathrm{TCL}}/E_{\mathrm{TCL}}$ \\
\midrule
""" + r("daily + daily", 'e_dd') + "\n" + r("hourly + hourly", 'e_hh') + "\n" + r("daily + hourly", 'e_dh') + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_energy.tex', 'w').write(tex)
    rho = np.corrcoef(G.e_dd, G.e_act)[0, 1]
    print(f'{len(G)} aggregates; daily+daily Pearson {rho:.3f}, WAPE {_wape(G.e_dd, G.e_act):.1f}%, '
          f'median ratio {np.median(G.e_dd / G.e_act):.3f}')
    print(f'share of HP energy on days >= T_h: median {np.median(1 - G.e_b_act / G.e_act_d) * 100:.1f}%; '
          f'below-threshold WAPE {_wape(G.e_b_est, G.e_b_act):.1f}%, ratio {np.median(G.e_b_est / G.e_b_act):.3f}')
    print('wrote tab_energy.tex')


def fig_energy_error(below_th=True):
    """Energy-estimate error across the Kloten aggregates (days below T_h)."""
    G = _kloten_design()['rows']
    e = (G.e_b_est - G.e_b_act) / G.e_b_act * 100 if below_th else (G.e_dd - G.e_act) / G.e_act * 100
    G = G.assign(spe=e)
    q = G.groupby('N_hp').spe.quantile([.25, .5, .75]).unstack()
    print(f'median {G.spe.median():+.1f}%'); print((q.assign(iqr=q[.75] - q[.25])).round(1).to_string())
    name = 'fig_energy_error_belowTh' if below_th else 'fig_energy_error'
    hf.use_style()
    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    ax[0].hist(G.spe.clip(-60, 60), bins=40, color=hf.C_CH, alpha=.8, edgecolor='none')
    ax[0].axvline(0, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax[0].axvline(G.spe.median(), color=hf.C_HP, lw=1.5, label=f'median {G.spe.median():+.0f}%')
    ax[0].set(xlabel='signed % error (est $-$ actual)', ylabel='aggregates')
    ax[0].legend(fontsize=7, loc='upper right')
    order = list(NHP_GRID_K)
    bp = ax[1].boxplot([G.loc[G.N_hp == k, 'spe'].values for k in order], positions=range(len(order)),
                       widths=.6, showfliers=False, whis=(5, 95), patch_artist=True,
                       medianprops=dict(color=hf.C_HP, lw=1.4))
    for b in bp['boxes']:
        b.set(facecolor=hf.C_CH, alpha=.35, edgecolor='0.5')
    ax[1].axhline(0, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax[1].set_xticks(range(len(order))); ax[1].set_xticklabels(order)
    ax[1].set(xlabel='HPs aggregated $N_{hp}$', ylabel='signed % error')
    fig.tight_layout(); hf.save(fig, name)
    print('saved ->', name)


def fig_slope_capacity():
    """fig_slope_capacity: heating sensitivity vs installed HP capacity (Kloten)."""
    G = _kloten_design()['rows']
    x, y = G.cap.to_numpy(), G.s_h.to_numpy()
    slope0 = np.sum(x * y) / np.sum(x * x); r = np.corrcoef(x, y)[0, 1]
    print(f'n={len(G)} Pearson r={r:.3f} through-origin slope={slope0:.4f}')
    hf.use_style()
    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    sc = ax.scatter(x, y, c=G.N_hp, s=9, cmap='viridis', alpha=.7, edgecolor='none')
    xl = np.array([0, x.max() * 1.02])
    ax.plot(xl, slope0 * xl, color=hf.C_HP, lw=1.4,
            label=f'through-origin fit\n($r={r:.2f}$, $m={slope0:.4f}\\,^\\circ$C$^{{-1}}$)')
    ax.set(xlabel='installed HP capacity $P_h^{\\max}$ (kW)', ylabel='heating sensitivity $s_h$ (kW/$^\\circ$C)')
    ax.legend(fontsize=7, loc='upper left')
    cb = fig.colorbar(sc, ax=ax, pad=0.02); cb.set_label('$N_{hp}$', fontsize=8)
    fig.tight_layout(); hf.save(fig, 'fig_slope_capacity')
    print('saved -> fig_slope_capacity')


def _hinge_slope(T, y, th):
    """OLS slope of y on max(0, th - T) with an intercept, all days. At a fixed threshold
    the net-load slope of fit_hockey_stick is this OLS slope, so it is linear in y and
    splits exactly into the TCL and non-TCL parts of the net load."""
    x = np.maximum(0.0, th - T)
    X = np.column_stack([np.ones_like(x), x])
    return float(np.linalg.lstsq(X, y, rcond=None)[0][1])


NONTCL_CORR = 'data/_kloten_nontcl_corr.pkl'


def kloten_nontcl_correction(n_splits=60, reps=3, seed=0, rebuild=False):
    """Non-TCL correction of the capacity estimate, (s_h - N sigma(T_h)) / m_h (Kloten).

    Mirrors ``_kloten_design`` (same HP halves, grid and reps), with one change: in each
    split the HP-free households are halved too. The calibration half gives sigma(t),
    the per-household non-TCL sensitivity at threshold t (``_hinge_slope`` of their mean
    daily load); the aggregates draw their HP-free households from the other half only,
    so no household informs both sigma and a target. sigma is evaluated at each target's
    own net-load threshold and multiplied by its consumer count N. Cached.
    """
    if os.path.exists(NONTCL_CORR) and not rebuild:
        with open(NONTCL_CORR, 'rb') as fh:
            return pickle.load(fh)
    K = _daily_pools()['KLO']; T = K['T']
    rng = np.random.default_rng(seed); nfree = K['free'].shape[0]
    rows, sig = [], []
    for s in range(n_splits):
        A, B = _pilot_split(len(K['cap']), rng)
        _, pm, _ = _pilot_fit(T, K, A)
        C, F = _pilot_split(nfree, rng)
        yC = K['free'][C].mean(0)
        _, sC, tC, _ = fit_hockey_stick(T, yC, T_BALANCE_BOUNDS)       # load correction: own hinge of the pool
        sig.append(dict(split=s, sigma_16=_hinge_slope(T, yC, 16.5), sigma_14=_hinge_slope(T, yC, 14.0),
                        s_C=sC, t_C=tC))
        for N in N_GRID_K:
            for nh in NHP_GRID_K:
                if nh > N:
                    continue
                for _ in range(reps):
                    H = rng.choice(B, nh, replace=False)
                    Fd = rng.choice(F, N - nh, replace=False) if N > nh else np.array([], int)
                    hp = K['hp'][H].sum(0); net = hp + K['own'][H].sum(0) + K['free'][Fd].sum(0)
                    cap = float(K['cap'][H].sum())
                    _, sh, th, _ = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
                    sg = _hinge_slope(T, yC, th)
                    m_own = U._sf_arm(T, np.clip(hp / cap, 0, 1), th, 'h')[1]
                    s_nontcl = _hinge_slope(T, net - hp, th)          # true non-TCL part of s_h
                    _, shL, thL, _ = fit_hockey_stick(T, net - N * sC * np.maximum(0.0, tC - T), T_BALANCE_BOUNDS)
                    rows.append(dict(split=s, N=N, N_hp=nh, cap=cap, s_h=sh, T_h=th, m_pilot=pm, m_own=m_own,
                                     sigma=sg, s_nontcl=s_nontcl, T_h_load=thL,
                                     cap_est=sh / pm, cap_corr=max(sh - N * sg, 0.0) / pm,
                                     cap_lcorr=shL / pm, cap_own_lcorr=shL / m_own,
                                     cap_own=sh / m_own, cap_own_corr=max(sh - N * sg, 0.0) / m_own))
    out = dict(rows=pd.DataFrame(rows), sigma=pd.DataFrame(sig))
    with open(NONTCL_CORR, 'wb') as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def report_nontcl_correction():
    """Print the Kloten correction by HP share and the Hamelin sweep with and without it."""
    R = kloten_nontcl_correction(); G = R['rows']; S = R['sigma']
    print(f"sigma (kW/C per household) at T_h=16.5: median {S.sigma_16.median():.4f} "
          f"[{S.sigma_16.quantile(.25):.4f}, {S.sigma_16.quantile(.75):.4f}]; at 14.0: {S.sigma_14.median():.4f}")
    per = G.s_nontcl / G.N
    print(f"true non-TCL slope per household in the targets: median {per.median():.4f} "
          f"[{per.quantile(.25):.4f}, {per.quantile(.75):.4f}]; share of s_h {np.median(G.s_nontcl / G.s_h) * 100:.0f}%")
    bins = pd.cut(G.N_hp / G.N, [0, .15, .35, .65, 1.0])
    for c in ('cap_est', 'cap_corr', 'cap_lcorr', 'cap_own', 'cap_own_corr', 'cap_own_lcorr'):
        w = [_wape(G[c], G.cap)] + [_wape(g[c], g.cap) for _, g in G.groupby(bins, observed=True)]
        r = [np.median(G[c] / G.cap)] + [np.median(g[c] / g.cap) for _, g in G.groupby(bins, observed=True)]
        print(f"{c:13s} WAPE " + ' '.join(f'{x:5.1f}' for x in w) + ' | median ratio ' + ' '.join(f'{x:.2f}' for x in r))
    # Hamelin: HP circuits removed, every household's other load kept (tab_feeder_sweep design)
    X = _daily_pools()['WPUQ']; Tw = X['T']; n = len(X['cap']); base = X['own'].sum(0)
    K = _daily_pools()['KLO']; yK = K['free'].mean(0)          # every Kloten HP-free household
    _, sK, tK, _ = fit_hockey_stick(K['T'], yK, T_BALANCE_BOUNDS)
    _, sHm, tHm, _ = fit_hockey_stick(Tw, X['own'].mean(0), T_BALANCE_BOUNDS)
    print(f"non-TCL hinge per household: Kloten HP-free {sK:.4f} kW/C below {tK:.1f} C; "
          f"Hamelin non-HP load {sHm:.4f} kW/C below {tHm:.1f} C")
    sig_ham = _hinge_slope(Tw, X['own'].mean(0), 13.9)
    print(f"sigma at 13.9 C: Hamelin non-HP load of its HP homes {sig_ham:.4f}, "
          f"Kloten HP-free {_hinge_slope(K['T'], yK, 13.9):.4f} kW/C per household")
    rng = np.random.default_rng(0); rows = []
    for nhp in (5, 10, 15, 20, 25, 30, 37):
        for Sx in ([np.arange(n)] if nhp == n else [rng.choice(n, nhp, replace=False) for _ in range(200)]):
            cap = X['cap'][Sx].sum(); net = base + X['hp'][Sx].sum(0)
            _, sh, th, _ = fit_hockey_stick(Tw, net, T_BALANCE_BOUNDS)
            rows.append(dict(N_hp=nhp, e=(sh / M_SWISS - cap) / cap * 100,
                             e_klo=(max(sh - n * _hinge_slope(K['T'], yK, th), 0) / M_SWISS - cap) / cap * 100,
                             e_ham=(max(sh - n * _hinge_slope(Tw, X['own'].mean(0), th), 0) / M_SWISS - cap) / cap * 100,
                             l_klo=(fit_hockey_stick(Tw, net - n * sK * np.maximum(0, tK - Tw), T_BALANCE_BOUNDS)[1]
                                    / M_SWISS - cap) / cap * 100,
                             l_ham=(fit_hockey_stick(Tw, net - n * sHm * np.maximum(0, tHm - Tw), T_BALANCE_BOUNDS)[1]
                                    / M_SWISS - cap) / cap * 100))
    H = pd.DataFrame(rows).groupby('N_hp').median()
    print('Hamelin sweep, median capacity error (%): uncorrected | slope corr. (Kloten, Hamelin sigma) | '
          'load corr. (Kloten, Hamelin hinge)')
    print(H.round(1).to_string())
    return G, S, H


def tab_baselines():
    """tab_baselines: capacity WAPE of the proposed estimate and three alternatives (Kloten),
    overall and by HP share N_hp / N.

    pilot m_h: s_h / m_pilot (Eq. capacity). target m_h: s_h / the aggregate's own SF
    sensitivity, so only the net-load sensitivity errs. Whole curve: the pilot's full SF
    fit (intercept and threshold) evaluated on the coldest day. Planning SF: coldest-day
    TCL load of the net-load fit divided by SF_PLAN.
    """
    Dz = _kloten_design(); G = Dz['rows'].copy(); Tmin = float(Dz['T'].min())
    P = {p['split']: p for p in Dz['pilots']}
    G['cap_whole'] = [r.s_h * (r.T_h - Tmin) / (P[r.split]['b'] + P[r.split]['m'] * (P[r.split]['t'] - Tmin))
                      for r in G.itertuples()]
    G['cap_plan'] = G.s_h * (G.T_h - Tmin) / SF_PLAN
    bins = pd.cut(G.N_hp / G.N, [0, .15, .35, .65, 1.0])
    rows = [(r'$s_h/m_h$, pilot $m_h$ \eqref{eq:capacity}', 'cap_est'),
            (r'$s_h/m_h$, target $m_h$', 'cap_or'),
            (r'full pilot SF curve', 'cap_whole'),
            (r'planning SF, $\hat{P}_{\mathrm{TCL}}(T_{\min})/0.425$', 'cap_plan')]
    lines = []
    for name, c in rows:
        w = [_wape(G[c], G.cap)] + [_wape(g[c], g.cap) for _, g in G.groupby(bins, observed=True)]
        print(f'{c:10s} ' + ' '.join(f'{x:5.1f}' for x in w) + f'  median ratio {np.median(G[c] / G.cap):.3f}')
        lines.append(name + ' & ' + ' & '.join(f'{x:.1f}' for x in w) + r' \\')
    tex = r"""\begin{table}[t]
\centering
\caption{Capacity WAPE (\%) on the Kloten aggregates, by HP penetration $N_{hp}/N$}
\label{tab:baselines}
\setlength{\tabcolsep}{2.5pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lccccc}
\toprule
estimate & all & $\le 15\%$ & 15--35\% & 35--65\% & $> 65\%$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    open('paper/tables/tab_baselines.tex', 'w').write(tex)
    print('wrote tab_baselines.tex')


def tab_capacity():
    """tab_capacity: per-regime capacity s_h / m_h, transferred vs oracle (Kloten)."""
    G = _kloten_design()['rows']

    def line(name, c):
        return f"{name} & {_wape(G[c], G.cap):.1f} & {np.median(G[c] / G.cap):.2f} \\\\"
    for n, g in G.groupby('N_hp'):
        print(f'  N_hp={n:2d}: transferred WAPE {_wape(g.cap_est, g.cap):5.1f}% ratio {np.median(g.cap_est / g.cap):.2f} | '
              f'oracle WAPE {_wape(g.cap_or, g.cap):5.1f}% ratio {np.median(g.cap_or / g.cap):.2f}')
    print(f"all: transferred WAPE {_wape(G.cap_est, G.cap):.1f}% ratio {np.median(G.cap_est / G.cap):.3f} "
          f"R2 {U.metrics(G.cap, G.cap_est)[1]:.3f} | oracle WAPE {_wape(G.cap_or, G.cap):.1f}% "
          f"ratio {np.median(G.cap_or / G.cap):.3f} R2 {U.metrics(G.cap, G.cap_or)[1]:.3f}")
    tex = r"""\begin{table}[t]
\centering
\caption{Capacity error on the Kloten aggregates}
\label{tab:capacity}
\begin{tabular}{lcc}
\toprule
$m_h$ in \eqref{eq:capacity} & WAPE (\%) & median $\hat{P}^{\max}_{h}/{P}^{\max}_{h}$ \\
\midrule
""" + line('transferred (pilot)', 'cap_est') + "\n" + line('oracle (own SF)', 'cap_or') + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_capacity.tex', 'w').write(tex)
    print('wrote tab_capacity.tex')


KLOTEN_FLEX_H = 'data/_kloten_flex_hourly_ref.pkl'


def _hourly_flex(hph, cap):
    """Actual flexibility per day and hour of window from hourly HP load (days x 24).

    The mean over the day's hours of SF_t (1 - SF_t) P_max, SF_t the hourly SF --
    the hourly reference for Eq. (flex-energy).
    """
    sf = np.clip(np.asarray(hph) / cap, 0, 1)
    return (sf * (1 - sf)).mean(1) * cap


def _station_hourly(st):
    """Hourly HP load (n_hp x hours) of a station of ``_daily_pools``, same row order."""
    import hp_pools as hpp
    if st == 'WPUQ':
        q = hpp.build_pool_wpuq(verbose=False)
        return pd.DataFrame(q['hp_mat'].T, index=q['index']).resample('h').mean().to_numpy(np.float32).T
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']
    rows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == st]
    return pd.DataFrame(p['hp_mat'][rows].T, index=p['index']).resample('h').mean().to_numpy(np.float32).T


def _kloten_flex_hourly(rebuild=False):
    """Hourly-reference actual flexibility of the Section IV aggregates (cached).

    Replays the draw of ``_kloten_design`` (same seed and order) to recover each
    aggregate's HPs, and returns, row-aligned with its rows: the actual flexible
    energy per hour of window on the R1 days (``act_h``) and over the whole year
    (``act_h_all``), and on the coldest day (``cold_h``), from the hourly SF.
    """
    if os.path.exists(KLOTEN_FLEX_H) and not rebuild:
        return pd.read_pickle(KLOTEN_FLEX_H)
    Dz = _kloten_design(); G = Dz['rows']
    K = _daily_pools()['KLO']; Kh = _kloten_hourly()
    T = K['T']; nd = len(T); k = int(np.argmin(T))
    rng = np.random.default_rng(0); nfree = K['free'].shape[0]
    out = []
    for _ in range(len(Dz['pilots'])):
        A, B = _pilot_split(len(K['cap']), rng)
        for N in N_GRID_K:
            for nh in NHP_GRID_K:
                if nh > N:
                    continue
                for _ in range(3):
                    H = rng.choice(B, nh, replace=False)
                    F = rng.choice(nfree, N - nh, replace=False) if N > nh else np.array([], int)
                    hp = K['hp'][H].sum(0); net = hp + K['own'][H].sum(0) + K['free'][F].sum(0)
                    cap = float(K['cap'][H].sum())
                    _, _, th, _ = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
                    fh = _hourly_flex(Kh['hp'][H].sum(0).reshape(nd, 24), cap)
                    out.append(dict(cap=cap, act_h=float(fh[T < th].sum()), act_h_all=float(fh.sum()), cold_h=float(fh[k])))
    R = pd.DataFrame(out)
    if len(R) != len(G) or not np.allclose(R.cap.to_numpy(), G.cap.to_numpy()):
        raise RuntimeError('replay does not reproduce _kloten_design; rebuild both')
    R.to_pickle(KLOTEN_FLEX_H)
    return R


def flex_figures():
    """fig_flex_ratio (Kloten aggregates) and fig_flex_season (a held-out Kloten half)."""
    import matplotlib.dates as mdates
    Dz = _kloten_design(); G = Dz['rows']; K = Dz['K']; T = Dz['T']
    Fh = _kloten_flex_hourly()
    # flexibility is counted on the days of the active regime only (R1: T < T_h; Kloten has no R3);
    # the actual is the hourly reference (hourly SF, averaged over the day)
    act = Fh.act_h.to_numpy()
    ratio = G.flex_b_est / act
    er = G.e_b_est / G.e_b_act
    print(f'{len(G)} aggregates, R1 days, hourly actual: ratio median {ratio.median():.2f} IQR [{ratio.quantile(.25):.2f}, '
          f'{ratio.quantile(.75):.2f}], WAPE {_wape(G.flex_b_est, act):.1f}%; energy factor {er.median():.2f}, headroom factor '
          f'{(ratio / er).median():.2f} [{(ratio / er).quantile(.25):.2f}, {(ratio / er).quantile(.75):.2f}], corr {np.corrcoef(ratio, er)[0, 1]:.2f}; '
          f'hourly / daily-mean actual {np.median(act / G.flex_b_act):.3f}; vs daily-mean actual {np.median(G.flex_b_est / G.flex_b_act):.2f}; '
          f'dead-band share of actual {np.median(1 - Fh.act_h / Fh.act_h_all) * 100:.0f}%; '
          f'coldest-day WAPE {_wape(G.cold_est, Fh.cold_h):.1f}% R2 {U.metrics(Fh.cold_h, G.cold_est)[1]:.3f}')
    hf.use_style()
    fig, ax = plt.subplots(figsize=(hf.COL1, 2.7))
    ax.hist(ratio.clip(0, 2.5), bins=40, color=hf.C_CH, alpha=.8, edgecolor='none')
    ax.axvline(1, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax.axvline(ratio.median(), color=hf.C_HP, lw=1.6, label=f'median {ratio.median():.2f}')
    ax.set(xlabel='estimated / actual annual flex (R1 days)', ylabel='aggregates')
    ax.legend(fontsize=7.5, loc='upper right')
    fig.tight_layout(); hf.save(fig, 'fig_flex_ratio')

    # season: the whole held-out half of split 0 (25 HPs and their homes), pilot m_h
    p0 = Dz['pilots'][0]; B = p0['B']
    hp = K['hp'][B].sum(0); net = hp + K['own'][B].sum(0); cap = float(K['cap'][B].sum())
    _, sh, th, _ = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
    sf_e = sf_target(T, th, p0['m']); cap_e = sh / p0['m']
    fa = _hourly_flex(_kloten_hourly()['hp'][B].sum(0).reshape(len(T), 24), cap)     # hourly reference
    fe = sf_e * (1 - sf_e) * cap_e
    DT = 4
    warm = T >= th
    print(f"season (held-out half, {len(B)} HPs): cap true {cap:.0f} est {cap_e:.0f} kW; annual per hour of "
          f"window (R1 days) actual {fa[~warm].sum() / 1000:.1f} est {fe[~warm].sum() / 1000:.1f} MWh; days >= T_h {warm.mean() * 100:.0f}%, "
          f"actual floor median {np.median(fa[warm]) * DT:.0f} kWh vs max {fa.max() * DT:.0f}; est max {fe.max() * DT:.0f}; "
          f"ceiling {0.25 * cap * DT:.0f} kWh")
    days = pd.date_range('2023-01-01', periods=len(T), freq='D')
    fig, ax = plt.subplots(figsize=(hf.COL1, 2.7))
    # only R1 days count; days at or above T_h are shaded and left out
    ax.fill_between(days, 0, 1, where=warm, transform=ax.get_xaxis_transform(), color='0.5', alpha=.12, lw=0,
                    label='$T \\geq T_h$ (not counted)')
    ax.plot(days, np.where(warm, np.nan, fa * DT), color='0.5', lw=0.9, label='actual')
    ax.plot(days, np.where(warm, np.nan, fe * DT), color=hf.C_HP, lw=1.0, label='estimated')
    ax.set(xlabel='month', ylabel=f'daily flexible energy (kWh), $\\Delta t = {DT}$ h')
    ax.xaxis.set_major_locator(mdates.MonthLocator((1, 4, 7, 10)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.legend(fontsize=7, loc='upper center')
    fig.tight_layout(); hf.save(fig, 'fig_flex_season')
    print('saved -> fig_flex_ratio, fig_flex_season')


KLOTEN_QUALITY = 'data/_kloten_quality.pkl'
QUALITY_RES = (('1 h', '1h'), ('4 h', '4h'), ('8 h', '8h'), ('16 h', '16h'), ('24 h', '24h'))


def _arm_r2(T, y, th, s, b):
    """R^2 of a heating arm b + s (th - T) on the points below th only."""
    m = T < th
    if m.sum() < 10:
        return np.nan
    yy = y[m]; ss = np.sum((yy - yy.mean()) ** 2)
    return float(1 - np.sum((yy - (b + s * (th - T[m]))) ** 2) / ss) if ss > 0 else np.nan


def _kloten_quality(n_splits=20, reps=3, seed=0, rebuild=False):
    """Heating-arm R^2_h of both fits on Kloten aggregates at a 50% ETL rate (cached).

    Same draw as ``_kloten_design`` (N_hp = N/2 HPs from the non-pilot half plus
    N/2 HP-free homes, without replacement), on the hourly series averaged over each
    window of ``QUALITY_RES``. The net-load fit is scored on the points below its
    threshold T_h, and the SF fit, anchored at that T_h, on the same points. Each
    cell also scores the capacity s_h / m_h, with s_h and the pilot's m_h (anchored
    at the pilot's own net-load threshold) fitted at the cell's resolution.
    """
    if os.path.exists(KLOTEN_QUALITY) and not rebuild:
        return pd.read_pickle(KLOTEN_QUALITY)
    K = _daily_pools()['KLO']; Kh = _kloten_hourly()
    idx = pd.date_range('2023-01-01', periods=len(Kh['T']), freq='h')
    rng = np.random.default_rng(seed); nfree = Kh['free'].shape[0]
    rows = []
    for _ in range(n_splits):
        A, B = _pilot_split(len(K['cap']), rng)
        hpA = Kh['hp'][A].sum(0); capA = float(K['cap'][A].sum())
        dA = pd.DataFrame({'T': Kh['T'], 'hp': hpA, 'net': hpA + Kh['own'][A].sum(0)}, index=idx)
        mA = {}
        for lab, rule in QUALITY_RES:
            x = dA.resample(rule).mean().dropna()
            _, _, thA, _ = fit_hockey_stick(x['T'].to_numpy(), x['net'].to_numpy(), T_BALANCE_BOUNDS)
            mA[lab] = U._sf_arm(x['T'].to_numpy(), np.clip(x['hp'].to_numpy() / capA, 0, 1), thA, 'h')[1]
        for N in N_GRID_K:
            nh = N // 2
            for _ in range(reps):
                H = rng.choice(B, nh, replace=False); F = rng.choice(nfree, N - nh, replace=False)
                hp = Kh['hp'][H].sum(0); net = hp + Kh['own'][H].sum(0) + Kh['free'][F].sum(0)
                cap = float(K['cap'][H].sum())
                d = pd.DataFrame({'T': Kh['T'], 'hp': hp, 'net': net}, index=idx)
                for lab, rule in QUALITY_RES:
                    x = d.resample(rule).mean().dropna()
                    T, y = x['T'].to_numpy(), x['net'].to_numpy()
                    b, sh, th, _ = fit_hockey_stick(T, y, T_BALANCE_BOUNDS)
                    _, _, _, r2s = U._sf_arm(T, np.clip(x['hp'].to_numpy() / cap, 0, 1), th, 'h')
                    rows.append(dict(N=N, resolution=lab, r2_net=_arm_r2(T, y, th, sh, b), r2_sf=r2s,
                                     cap=cap, cap_est=sh / mA[lab]))
    Q = pd.DataFrame(rows)
    Q.to_pickle(KLOTEN_QUALITY)
    return Q


def fig_quality_heatmap():
    """fig_quality_heatmap: median heating-arm R^2_h against spatial x temporal aggregation.

    Kloten aggregates at a 50% ETL rate (``_kloten_quality``). A COLUMN (fixed
    averaging window) varies N top to bottom -- the spatial effect; a ROW (fixed N)
    varies the window left to right -- the temporal effect.
    """
    Q = _kloten_quality()
    labs = [lab for lab, _ in QUALITY_RES]
    pivs = {c: Q.pivot_table(index='N', columns='resolution', values=c, aggfunc='median')[labs]
            for c in ('r2_net', 'r2_sf')}
    for c, p in pivs.items():
        print(c); print(p.round(2).to_string())
    all_vals = np.concatenate([p.values.ravel() for p in pivs.values()])
    vmin, vmax = float(np.nanmin(all_vals)), float(np.nanmax(all_vals))
    hf.use_style()
    fig, axes = plt.subplots(1, 2, figsize=(hf.COL2, 3.1))
    for ax, c, title in zip(axes, ['r2_net', 'r2_sf'], ['net-load fit', 'SF fit']):
        piv = pivs[c]
        vals = piv.values
        im = ax.imshow(vals, aspect='auto', origin='lower', cmap='magma', vmin=vmin, vmax=vmax)
        ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns, fontsize=7)
        ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index, fontsize=7)
        for i in range(len(piv.index)):
            for j in range(len(piv.columns)):
                v = vals[i, j]
                if np.isfinite(v):
                    level = (v - vmin) / (vmax - vmin) if vmax > vmin else 1.0
                    ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=6,
                            color='white' if level < 0.55 else 'black')
        ax.set_xlabel('averaging window')
        ax.set_title(title, fontsize=8.5)
        ax.grid(False)
    axes[0].set_ylabel('consumers per aggregate, $N$')
    cb = fig.colorbar(im, ax=axes, pad=0.02, aspect=28, fraction=0.05)
    cb.set_label('median $R^2_h$', fontsize=8)
    cb.ax.tick_params(labelsize=7)
    hf.save(fig, 'fig_quality_heatmap')
    print('saved -> fig_quality_heatmap')


def fig_capacity_heatmap():
    """fig_capacity_heatmap: capacity error against spatial x temporal aggregation (Kloten, 50% ETL rate).

    Left: WAPE of s_h / m_h per cell; right: median signed error. Same aggregates
    and resolutions as ``fig_quality_heatmap`` (``_kloten_quality``).
    """
    Q = _kloten_quality()
    labs = [lab for lab, _ in QUALITY_RES]
    Q = Q.assign(err=(Q.cap_est - Q.cap) / Q.cap * 100)
    wape = Q.groupby(['N', 'resolution']).apply(lambda g: (g.cap_est - g.cap).abs().sum() / g.cap.sum() * 100)
    pivs = {'WAPE (%)': wape.unstack()[labs],
            'median signed error (%)': Q.pivot_table(index='N', columns='resolution', values='err', aggfunc='median')[labs]}
    for c, p in pivs.items():
        print(c); print(p.round(1).to_string())
    hf.use_style()
    fig, axes = plt.subplots(1, 2, figsize=(hf.COL2, 3.1))
    for ax, (title, piv), cmap in zip(axes, pivs.items(), ('magma_r', 'RdBu_r')):
        vals = piv.values
        if cmap == 'RdBu_r':
            v = float(np.nanmax(np.abs(vals))); vmin, vmax = -v, v
        else:
            vmin, vmax = float(np.nanmin(vals)) - 1, float(np.nanmax(vals)) + 1
        im = ax.imshow(vals, aspect='auto', origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns, fontsize=7)
        ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index, fontsize=7)
        for i in range(len(piv.index)):
            for j in range(len(piv.columns)):
                x = vals[i, j]
                if np.isfinite(x):
                    level = abs(x) / vmax if cmap == 'RdBu_r' else (x - vmin) / (vmax - vmin)
                    dark = level > 0.6
                    ax.text(j, i, f'{x:+.0f}' if cmap == 'RdBu_r' else f'{x:.0f}', ha='center', va='center',
                            fontsize=6.5, color='white' if dark else 'black')
        ax.set_xlabel('averaging window')
        ax.set_title(title, fontsize=8.5)
        ax.grid(False)
        cb = fig.colorbar(im, ax=ax, pad=0.02, aspect=28, fraction=0.05)
        cb.ax.tick_params(labelsize=7)
    axes[0].set_ylabel('consumers per aggregate, $N$')
    hf.save(fig, 'fig_capacity_heatmap')
    print('saved -> fig_capacity_heatmap')


# ===========================================================================
# Section 4 -- flexibility
# ===========================================================================
def fig_flex_schedule():
    """fig_flex_schedule: schematic of the flexibility formulation, compressed
    into one cycle of the square-wave schedule."""
    hf.use_style()
    Pmax, base, af = 1.0, 0.4, 0.4
    RED, BLU = hf.C_HP, hf.C_CH
    fig, ax = plt.subplots(figsize=(hf.COL1 + 0.9, 3.3))

    ax.axhline(Pmax, color='0.6', lw=0.8, zorder=1)
    ax.axhline(base, color='0.35', lw=0.9, ls=(0, (4, 2)), zorder=2)

    # E^old_TCL: the baseline energy drawn over the whole window, marked with
    # diagonal hatching rather than a solid fill.
    ax.fill_between([0, 1], 0, base, facecolor='none', edgecolor='0.4',
                     hatch='////', lw=0, zorder=2)

    # P^new_TCL: the full-power pulse of duty cycle alpha_F.
    xs = [0, 0, af, af, 1]
    ys = [0, Pmax, Pmax, 0, 0]
    ax.step(xs, ys, where='post', color=RED, lw=1.9, zorder=6)

    # deviation from baseline: upward during the on phase, downward off phase.
    ax.fill_between([0, af], base, Pmax, color=RED, alpha=.20, lw=0, zorder=3)
    ax.fill_between([af, 1], 0, base, color=BLU, alpha=.28, lw=0, zorder=3)

    label_bg = dict(facecolor='white', edgecolor='none', alpha=.72, pad=1.2)
    ax.annotate('$E^{\\mathrm{old}}_{\\mathrm{TCL}}$', (af / 2, base / 2),
                ha='center', va='center', fontsize=8.5, color='0.3', zorder=7, bbox=label_bg)
    ax.annotate('$E_{\\mathrm{flex}}^{\\uparrow}$', (af / 2, (base + Pmax) / 2),
                ha='center', va='center', fontsize=9, color=RED, zorder=7)
    ax.annotate('$E_{\\mathrm{flex}}^{\\downarrow}$', (af + (1 - af) / 2, base / 2),
                ha='center', va='center', fontsize=9, color='#1f6f78', zorder=7, bbox=label_bg)

    ax.plot([af / 2, af / 2], [Pmax, 1.07], color=RED, lw=0.6, zorder=6)
    ax.annotate('$P^{\\mathrm{new}}_{\\mathrm{TCL}}$', (af / 2, 1.08),
                ha='center', va='bottom', fontsize=8.5, color=RED, zorder=7)

    ax.annotate('$P_{\\mathrm{TCL}}^{\\max}$', (0.72, Pmax), xytext=(0, 3),
                textcoords='offset points', ha='center', va='bottom', fontsize=8, color='0.3')
    ax.annotate('baseline $\\bar P_{\\mathrm{TCL}}(T)$', (0.72, base), xytext=(0, 4),
                textcoords='offset points', ha='center', va='bottom', fontsize=8, color='0.25')

    def bracket(x0, x1, y, label):
        ax.annotate('', (x0, y), (x1, y), arrowprops=dict(arrowstyle='<->', lw=0.9, color='0.3'))
        ax.text((x0 + x1) / 2, y + 0.04, label, ha='center', va='bottom', fontsize=9, color='0.2')
    bracket(0, af, 1.22, '$\\alpha_F$')
    bracket(0, 1, 1.38, '$\\Delta t_{Th}$')
    ax.vlines([0, 1], Pmax, 1.38, color='0.6', lw=0.5, ls=(0, (2, 2)), zorder=1)
    ax.vlines([af], Pmax, 1.22, color='0.6', lw=0.5, ls=(0, (2, 2)), zorder=1)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1.55)
    ax.set_xticks([]); ax.set_yticks([0, base, Pmax]); ax.set_yticklabels(['0', '', ''])
    ax.set_xlabel('time'); ax.set_ylabel('TCL power')
    fig.tight_layout()
    hf.save(fig, 'fig_flex_schedule')
    print('saved -> fig_flex_schedule')


# ===========================================================================
# Section 5 -- real unseen feeder
# ===========================================================================
def fig_real_feeder():
    """Fig. 11: real WPUQ feeder net-load fit and feeder-own vs transferred SF."""
    d = pd.read_csv('data/wpuq_real_feeder_sf.csv', index_col=0, parse_dates=True)
    T = d['Temp'].to_numpy(); net = d['net'].to_numpy(); sf = d['SF'].to_numpy()
    Tmin = float(np.min(T))
    nb, ns, nt, nr2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
    mh = T < nt
    nr2_h = float(1 - np.sum((net[mh] - (nb + ns * (nt - T[mh]))) ** 2) /
                  np.sum((net[mh] - net[mh].mean()) ** 2))
    # the aggregate's own SF fit, anchored at its net-load T_h -- validation only
    sb, ss, sf_own, sr2 = U._sf_arm(T, sf, nt, 'h')
    sf_tr = float(sf_target(Tmin, nt))
    print(f'  net-load: s_h {ns:.2f} kW/C, T_h {nt:.1f} C, R2 all days {nr2:.2f}, heating days {nr2_h:.2f}; '
          f'T_min {Tmin:.1f} C; P_ETL(T_min) {ns * (nt - Tmin):.0f} kW')
    print(f'  own SF (at T_h): b {sb:.3f} m {ss:.4f} R2(T<T_h) {sr2:.2f}; '
          f'SF(T_min) own {sf_own:.2f} vs transferred m(T_h-T_min) {sf_tr:.2f}')
    whole = SWISS_SF['base'] + SWISS_SF['slope'] * (SWISS_SF['t_thr'] - Tmin)
    for name, pred in [('transferred m_h (Eq. capacity)', ns / M_SWISS),
                       ('oracle (own m_h)', ns / ss),
                       ('whole Swiss curve (b, m, T^SF)', ns * (nt - Tmin) / whole)]:
        print(f'  {name:32s}: P_max = {pred:5.0f} kW   error {(pred - WPUQ_TRUE_KW) / WPUQ_TRUE_KW * 100:+5.1f}%')

    hf.use_style()
    Tg = np.linspace(Tmin, nt, 150)
    Tmax = float(T.max())
    gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    ax[0].scatter(T, net, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily net load')
    ax[0].plot(Tg, nb + ns * (nt - Tg), color=hf.C_DE, lw=1.9, label=r'$\hat{P}_{\mathrm{net}}(T)$')
    ax[0].plot([nt, Tmax], [nb, nb], color='0.35', lw=1.9, zorder=4)
    ax[0].set(xlabel='daily mean temperature (°C)', ylabel='aggregate net load (kW)')
    y0b = ax[0].get_ylim()[0]
    ax[0].vlines(nt, y0b, 40, **gth); ax[0].set_ylim(bottom=y0b)
    ax[0].annotate('$T_h$', xy=(nt, 40), xytext=(0, 3), textcoords='offset points',
                   ha='center', va='bottom', fontsize=9, color='0.3')
    leg0 = ax[0].legend(fontsize=7, loc='upper right')
    fig.canvas.draw()
    lx0 = leg0.get_window_extent().transformed(ax[0].transAxes.inverted()).x0
    ax[0].text(lx0, 0.72, f'$R^2_h$ {nr2_h:.2f}', transform=ax[0].transAxes,
               ha='left', va='center', fontsize=7, color='0.3')
    ax[1].scatter(T, sf, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily SF')
    ax[1].plot(Tg, np.clip(sb + ss * (nt - Tg), 0, 1), color=hf.C_DE, lw=1.9, label='own SF fit (validation)')
    ax[1].plot(Tg, sf_target(Tg, nt), color=hf.C_HP, lw=2.1, label=r'transferred $m_h$ from $T_h$')
    xl1 = ax[1].get_xlim()
    ax[1].axvspan(nt, xl1[1], color='0.5', alpha=.12, lw=0, zorder=0)
    ax[1].set_xlim(xl1)
    ax[1].axvline(Tmin, color='0.5', lw=0.8, ls=(0, (2, 2)))
    ax[1].plot([Tmin, Tmin], [sf_own, sf_tr], color=hf.C_HP, lw=0, marker='o', ms=2.5)
    ax[1].vlines(nt, 0, 0.20, **gth)
    ax[1].annotate('$T_h$', xy=(nt, 0.20), xytext=(0, 3), textcoords='offset points',
                   ha='center', va='bottom', fontsize=9, color='0.3')
    ax[1].set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
    ax[1].legend(fontsize=7, loc='upper right')
    fig.tight_layout()
    hf.save(fig, 'fig_real_feeder')
    print('saved -> fig_real_feeder')


def tab_feeder_sweep():
    """tab_feeder_sweep: use-case error as HP circuits are removed from the real feeder."""
    import hp_pools as hpp
    from hp_capacity import robust_series_peak
    SWISS = SWISS_SF
    p = hpp.build_pool_wpuq(verbose=False)
    idx = p['index']; hp_mat, other_mat = p['hp_mat'], p['other_mat']
    n_house = hp_mat.shape[0]
    rp = np.array([robust_series_peak(hp_mat[i]) for i in range(n_house)])
    base_all = other_mat.sum(axis=0)
    temp = pd.Series(p['temperature']['WPUQ'], index=idx)
    Td = temp.resample('D').mean(); Tmin = float(Td.min())
    dt = 0.25

    def fit_daily(series):
        y = pd.Series(series, index=idx).resample('D').mean()
        dd = pd.DataFrame({'T': Td, 'y': y}).dropna()
        return fit_hockey_stick(dd['T'].to_numpy(), dd['y'].to_numpy(), T_BALANCE_BOUNDS)

    rng = np.random.default_rng(0)
    grid = [5, 10, 15, 20, 25, 30, 37]
    rows = []
    for nhp in grid:
        combos = [np.arange(n_house)] if nhp == n_house else \
                 [rng.choice(n_house, nhp, replace=False) for _ in range(200)]
        for S in combos:
            cap_true = rp[S].sum()
            net = base_all + hp_mat[S].sum(axis=0)
            hp_sum = hp_mat[S].sum(axis=0)
            nb, ns, nt, nr2 = fit_daily(net)
            sfser = hp_sum / cap_true
            ys = pd.DataFrame({'T': Td, 'y': pd.Series(sfser, index=idx).resample('D').mean()}).dropna()
            sf_own = U._sf_arm(ys['T'].to_numpy(), ys['y'].to_numpy(), nt, 'h')[2]
            cap_est = ns / SWISS['slope']                       # Eq. (capacity), transferred m_h
            e_est = float((ns * (nt - Td).clip(lower=0) * 24).sum())
            e_act = float(hp_sum.sum() * dt)
            rows.append(dict(N_hp=nhp, cap_true=cap_true, net_r2=nr2, sf_own_cold=sf_own,
                             e_cap=(cap_est - cap_true) / cap_true * 100,
                             e_energy=(e_est - e_act) / e_act * 100))
    dfr = pd.DataFrame(rows)
    g = dfr.groupby('N_hp').median(numeric_only=True)
    q = dfr.groupby('N_hp').e_cap.quantile([.25, .75]).unstack()
    for k in grid:
        print(f"  N_hp={k:2d}: capacity {g.loc[k, 'e_cap']:+5.1f}% (IQR {q.loc[k, .25]:+.0f} to "
              f"{q.loc[k, .75]:+.0f}), energy {g.loc[k, 'e_energy']:+5.1f}%, own SF(T_min) {g.loc[k, 'sf_own_cold']:.2f}")

    def row(nhp, label=None):
        r = g.loc[nhp]
        return f"{label or nhp} & \\chg{{{r['e_cap']:+.0f}}} \\\\"
    body = "\n".join(row(k) for k in grid[:-1]) + "\n\\midrule\n" + row(grid[-1], '37 (all)')
    tex = r"""\begin{table}[t]
\centering
\caption{Median capacity error on Hamelin as HPs are removed}
\label{tab:feeder-sweep}
\begin{tabular}{cc}
\toprule
$N_{hp}$ & \chg{capacity (\%)} \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_feeder_sweep.tex', 'w').write(tex)
    print('wrote tab_feeder_sweep.tex')


def tab_real():
    """tab_real: real aggregates outside the pilot (Hg, MqO, WPUQ), full Kloten pilot."""
    D = _daily_pools(); K = D['KLO']
    kb, km, kt = _pilot_fit(K['T'], K, np.arange(len(K['cap'])))
    print(f'full Kloten pilot ({len(K["cap"])} HPs): b {kb:.4f} m {km:.5f} T_h {kt:.2f} '
          f'(module constants: {SWISS_SF})')
    names = {'Hg': 'Hg, CH', 'MqO': 'MqO, CH', 'WPUQ': 'Hamelin, DE'}
    rows = []
    for st in ('Hg', 'MqO', 'WPUQ'):
        X = D[st]; T = X['T']; hp = X['hp'].sum(0); net = hp + X['own'].sum(0); cap = float(X['cap'].sum())
        _, sh, th, r2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
        sf = np.clip(hp / cap, 0, 1)
        om = U._sf_arm(T, sf, th, 'h')[1]
        below = T < th; sf_e = sf_target(T, th, km); cap_e = sh / km
        whole = sh * (th - T.min()) / (kb + km * (kt - T.min()))
        plan = sh * (th - T.min()) / SF_PLAN                  # coldest-day TCL load / planning SF
        e_est = sh * np.maximum(0, th - T) * 24
        fe = sf_e * (1 - sf_e) * cap_e
        fa = _hourly_flex(_station_hourly(st).sum(0).reshape(len(T), 24), cap)        # hourly reference
        pe = sh * (th - T[below])
        rows.append(dict(e_r1=pe.sum() / hp[below].sum(), head=(fe[below].sum() / pe.sum()) / (fa[below].sum() / hp[below].sum()),
                         fe_r1=fe[below].sum(), fa_r1=fa[below].sum(), r1_days=int(below.sum()),
                         agg=names[st], n=len(X['cap']), cap=cap, cap_e=cap_e, err=(cap_e - cap) / cap * 100,
                         oracle=(sh / om - cap) / cap * 100, whole=(whole - cap) / cap * 100,
                         plan=(plan - cap) / cap * 100,
                         m_own=om, T_h=th, net_r2=r2,
                         e_all=(e_est.sum() - hp.sum() * 24) / (hp.sum() * 24) * 100,
                         e_below=(e_est[below].sum() - hp[below].sum() * 24) / (hp[below].sum() * 24) * 100,
                         flex=fe.sum() / fa.sum(), flex_b=fe[below].sum() / fa[below].sum(),
                         flex_true_cap=(sf_e * (1 - sf_e)).sum() * cap / fa.sum()))
    R = pd.DataFrame(rows)
    print(R.round(3).to_string(index=False))
    s = lambda v: f"${v:+.0f}$"
    body = "\n".join(f"{r.agg} & {r.n} & {r.cap:.0f} & {r.cap_e:.0f} & {s(r.err)} & {s(r.oracle)} & "
                     f"{s(r.whole)} & {s(r.plan)} & {r.flex_b:.2f} \\\\" for r in R.itertuples())
    tex = r"""\begin{table}[t]
\centering
\caption{Transfer to real aggregates outside Kloten}
\label{tab:real}
\setlength{\tabcolsep}{2.5pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccccccc}
\toprule
 & & & & \multicolumn{4}{c}{capacity error (\%)} & \\
\cmidrule(lr){5-8}
aggregate & $N_{hp}$ & $P_h^{\max}$ (kW) & $\hat{P}_h^{\max}$ (kW) & \begin{tabular}[b]{@{}c@{}}pilot\\$m_h$\end{tabular} & \begin{tabular}[b]{@{}c@{}}target\\$m_h$\end{tabular} & \begin{tabular}[b]{@{}c@{}}full\\curve\end{tabular} & \begin{tabular}[b]{@{}c@{}}planning\\SF\end{tabular} & flex \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    open('paper/tables/tab_real.tex', 'w').write(tex)
    print('wrote tab_real.tex')
    return R


def _neea_agg_temperature(sites):
    """Daily outdoor temperature (C) of a NEEA aggregate, matched in place to its homes.

    Each home takes its own outdoor-air sensor(s) (``*_oa_*`` streams, deg F in the
    source); on days without one, or for a home without a sensor, it takes the mean
    of the outdoor sensors of the homes assigned to the same NOAA station
    (``SITES v9.2.csv``). The aggregate temperature is the mean over its homes.
    Timestamps are local standard time, as for the load.
    """
    t = pd.read_parquet('data/neea_temp_2023.parquet')
    t = t[t['regname'].astype(str).str.contains('_oa_')].copy()
    t['ee_site_id'] = t['ee_site_id'].astype(int)
    t['day'] = t['MIN_T_l'].dt.floor('D'); t['C'] = (t['temp'] - 32) * 5.0 / 9.0
    own = t.groupby(['ee_site_id', 'day'])['C'].mean().unstack(0)               # days x homes
    stn_of = pd.read_csv('data/SITES v9.2.csv').set_index('ee_site_id')['station_id']
    stn = own.T.groupby(stn_of.reindex(own.columns).to_numpy()).mean().T          # days x stations
    cols = {}
    for h in sites:
        by_stn = stn[stn_of[h]] if stn_of.get(h) in stn.columns else None
        mine = own[h] if h in own.columns else None
        if mine is None and by_stn is None:
            continue
        cols[h] = mine.fillna(by_stn) if (mine is not None and by_stn is not None) else (mine if mine is not None else by_stn)
    return pd.DataFrame(cols).mean(axis=1)


def _neea_aggregates(min_days=330):
    """NEEA WA/OR aggregates of homes with submetered ductless HPs (15-min data).

    A site-day counts when both the HP and the mains meters report >= 90 of 96
    samples; a site enters its state's aggregate with >= min_days such days;
    the aggregate keeps the days on which every one of its sites counts. Each
    HP's capacity is the 99.9th percentile of its summed 15-min draw.
    """
    p = pd.read_parquet('data/neea_power_2023.parquet')
    st = p.groupby('ee_site_id')['state'].first()
    hp = p[p['End Use'] == 'Ductless Heatpump'].groupby(['ee_site_id', 'MIN_T_l'])['power'].sum()
    mn = p[p['End Use'] == 'Mains'].groupby(['ee_site_id', 'MIN_T_l'])['power'].sum()
    cap = hp.groupby(level=0).quantile(0.999)

    def daily(s):
        d = s.rename('power').reset_index(); d['day'] = d['MIN_T_l'].dt.floor('D')
        return d.groupby(['ee_site_id', 'day'])['power'].agg(['mean', 'size'])
    J = daily(hp).join(daily(mn), lsuffix='_h', rsuffix='_m', how='inner')
    J = J[(J['size_h'] >= 90) & (J['size_m'] >= 90)]
    good = J.groupby(level=0).size()
    out = {}
    for s in ('WA', 'OR'):
        sites = [x for x in good[good >= min_days].index if st.get(x) == s]
        H = J['mean_h'].unstack(0)[sites]; M = J['mean_m'].unstack(0)[sites]
        days = H.index[H.notna().all(axis=1) & M.notna().all(axis=1)]
        Ts = _neea_agg_temperature(sites)
        d = pd.DataFrame({'hp': H.loc[days].sum(axis=1), 'net': M.loc[days].sum(axis=1)}).join(Ts.rename('T')).dropna()
        out[s] = dict(T=d['T'].to_numpy(), hp=d['hp'].to_numpy(), net=d['net'].to_numpy(),
                      cap=float(cap[sites].sum()), n=len(sites), days=len(d), sites=list(sites))
    return out


NEEA_HEAT = ('Ductless Heatpump', 'Ducted Heatpump', 'Electric Baseboard Heaters',
             'Electric Furnace', 'Other Zonal Heat')
NEEA_COOL = ('Ductless Heatpump', 'Ducted Heatpump', 'Central AC', 'Room AC')


def _neea_aggregates_full(min_days=330, exclude=()):
    """NEEA WA/OR aggregates with EVERY electric heating and cooling circuit as ETL.

    Built from ``data/neea_heating_circuits_2023.parquet`` (scripts/neea_extract.py).
    Per regime, the ETL load is the sum of the heating (``NEEA_HEAT``) or cooling
    (``NEEA_COOL``) circuits and the installed capacity the sum of each circuit's
    99.9th-percentile 15-min draw. A site-day counts when the mains and every ETL
    circuit of the home report >= 90 of 96 samples; a home with a ductless HP enters
    its state's aggregate with >= min_days such days; the aggregate keeps the days on
    which every one of its homes counts.
    """
    p = pd.read_parquet('data/neea_heating_circuits_2023.parquet')
    p = p[p['End Use'].isin(set(NEEA_HEAT) | set(NEEA_COOL) | {'Mains'})]
    st = p.groupby('ee_site_id')['state'].first().astype(str)
    has_dhp = (set(p.loc[p['End Use'] == 'Ductless Heatpump', 'ee_site_id'])
               & set(p.loc[p['End Use'] == 'Mains', 'ee_site_id']))      # needs its own mains meter
    p = p[p['ee_site_id'].isin(has_dhp) & ~p['ee_site_id'].isin(
        set(pd.read_parquet('data/neea_power_2023.parquet', columns=['ee_site_id', 'End Use'])
            .query("`End Use` == 'Mains With Solar'")['ee_site_id']))]
    p['day'] = p['MIN_T_l'].dt.floor('D')
    # per-circuit robust peak and daily completeness
    circ = p.groupby(['ee_site_id', 'regname', 'End Use'], observed=True)['power']
    peak = circ.quantile(0.999).rename('peak').reset_index()
    cnt = p.groupby(['ee_site_id', 'regname', 'day'], observed=True).size().rename('n').reset_index()
    ok = cnt.assign(ok=cnt['n'] >= 90).groupby(['ee_site_id', 'day'])['ok'].all()
    full_days = ok[ok].reset_index()[['ee_site_id', 'day']]
    good = full_days.groupby('ee_site_id').size()

    def daily_sum(uses):
        q = p[p['End Use'].isin(uses)]
        s = q.groupby(['ee_site_id', 'MIN_T_l'])['power'].sum().rename('pw').reset_index()
        s['day'] = s['MIN_T_l'].dt.floor('D')
        return s.groupby(['ee_site_id', 'day'])['pw'].mean()
    heatD, coolD, mainsD, dhpD = (daily_sum(NEEA_HEAT), daily_sum(NEEA_COOL), daily_sum(('Mains',)),
                                  daily_sum(('Ductless Heatpump',)))
    out = {}
    for s in ('WA', 'OR'):
        sites = [x for x in good[good >= min_days].index if st.get(x) == s and x not in set(exclude)]
        okS = full_days[full_days['ee_site_id'].isin(sites)]
        days = okS.groupby('day').size()
        days = days[days == len(sites)].index
        pick = lambda D: D[D.index.get_level_values(0).isin(sites)].unstack(0).reindex(columns=sites).loc[days].sum(axis=1)
        Ts = _neea_agg_temperature(sites)
        d = pd.DataFrame({'heat': pick(heatD), 'cool': pick(coolD), 'net': pick(mainsD),
                          'dhp': pick(dhpD)}).join(Ts.rename('T')).dropna()
        pk = peak[peak['ee_site_id'].isin(sites)]
        inv = pk.groupby('End Use', observed=True)['ee_site_id'].nunique().to_dict()
        out[s] = dict(T=d['T'].to_numpy(), heat=d['heat'].to_numpy(), cool=d['cool'].to_numpy(),
                      net=d['net'].to_numpy(), dhp=d['dhp'].to_numpy(),
                      cap_h=float(pk[pk['End Use'].isin(NEEA_HEAT)]['peak'].sum()),
                      cap_c=float(pk[pk['End Use'].isin(NEEA_COOL)]['peak'].sum()),
                      cap_dhp=float(pk[pk['End Use'] == 'Ductless Heatpump']['peak'].sum()),
                      n=len(sites), days=len(d), sites=list(sites), homes_by_use=inv, dates=d.index)
    return out


NEEA_GROUPS = {   # circuit families for the net-load decomposition
    'heating ETL': NEEA_HEAT,
    'cooling-only AC': ('Central AC', 'Room AC'),
    'water heating': ('Electric Resistance Storage Water Heaters', 'Heat Pump Water Heater',
                      'Instantaneous Water Heater (Elec)'),
    'general circuits (Other)': ('Other', 'Needs Review'),
    'cooking': ('Stove/Oven/Range', 'Microwave'),
    'laundry': ('Clothes Washer', 'Clothes Dryer'),
    'fridge/freezer': ('Refrigerator/Freezer',),
    'dishwasher/disposal': ('Dishwasher', 'Garbage Disposal'),
    'hot tub': ('Hot Tub',),
    'EV charger': ('Electric Vehicle Charger',),
    'gas furnace blower': ('Gas Furnace (Component)',),
    'solar': ('Solar', 'Other With Solar'),
    'pumps (well/septic)': ('PUMP',),
    'EV charger (EVSE)': ('EVSE',),
    'other large loads': ('Other Large Load', 'Central Vacuum', 'EULR BOX'),
    'sub panel (may double-count)': ('Sub Panel',),
}


def neea_decompose(A=None):
    """Split each NEEA aggregate's net-load heating (and cooling) slope by circuit family.

    Uses the homes and days of ``_neea_aggregates_full``. Every family's daily load
    is regressed on the same hinges, max(0, T_h - T) and max(0, T - T_c), with the
    thresholds of the mains fit, so the family slopes add up to the mains slope.
    'unmetered' is mains minus the sum of every metered circuit.
    """
    from hp_common import fit_bathtub_stick
    A = _neea_aggregates_full() if A is None else A
    p = pd.read_parquet('data/neea_all_circuits_2023.parquet')
    p = p[p['End Use'].notna() & (p['End Use'].astype(str) != 'nan')]
    # sum the circuits of each end use per timestamp, then take the daily mean
    S = p.groupby(['ee_site_id', 'End Use', 'MIN_T_l'], observed=True)['power'].sum().reset_index()
    S['day'] = S['MIN_T_l'].dt.floor('D')
    D = S.groupby(['ee_site_id', 'End Use', 'day'], observed=True)['power'].mean().reset_index()
    fam = {u: g for g, uses in NEEA_GROUPS.items() for u in uses}
    out = {}
    for st in ('WA', 'OR'):
        X = A[st]; dates = X['dates']
        q = D[D['ee_site_id'].isin(X['sites']) & D['day'].isin(dates)]
        mains = q[q['End Use'] == 'Mains'].groupby('day')['power'].sum().reindex(dates)
        circ = q[~q['End Use'].isin(['Mains', 'Mains With Solar'])]
        unknown = sorted(set(circ['End Use']) - set(fam))
        circ = circ.assign(fam=circ['End Use'].map(fam).fillna('other (unmapped)'))
        F = circ.groupby(['day', 'fam'])['power'].sum().unstack('fam').reindex(dates).fillna(0.0)
        F['unmetered'] = mains - F.sum(axis=1)
        T = X['T']
        _, sh, th, sc, tc, _ = fit_bathtub_stick(T, mains.to_numpy())
        Xr = np.column_stack([np.ones_like(T), np.maximum(0, th - T), np.maximum(0, T - tc)])
        coef = {c: np.linalg.lstsq(Xr, F[c].to_numpy(), rcond=None)[0] for c in F.columns}
        tot_h = np.linalg.lstsq(Xr, mains.to_numpy(), rcond=None)[0][1]
        R = pd.DataFrame({'s_h (kW/C)': {c: v[1] for c, v in coef.items()},
                          's_c (kW/C)': {c: v[2] for c, v in coef.items()},
                          'mean load (kW)': F.mean()})
        R['share of mains s_h'] = R['s_h (kW/C)'] / tot_h
        R = R.sort_values('s_h (kW/C)', ascending=False)
        print(f"== {st}: {X['n']} homes, {len(dates)} days; mains T_h {th:.1f} C, T_c {tc:.1f} C; "
              f"mains s_h {tot_h:.3f} kW/C (sum of families {R['s_h (kW/C)'].sum():.3f})"
              + (f"; unmapped end uses {unknown}" if unknown else ''))
        print(R.round(3).to_string())
        out[st] = R
    return out


def neea_transfer_full(pilot='WA', target='OR', A=None):
    """Two-regime WA -> OR transfer with the complete heating and cooling ground truth."""
    from hp_common import fit_bathtub_stick
    A = _neea_aggregates_full() if A is None else A
    P, X = A[pilot], A[target]
    for s in (pilot, target):
        Y = A[s]
        print(f"{s}: {Y['n']} homes, {Y['days']} days; P_h {Y['cap_h']:.1f} kW, P_c {Y['cap_c']:.1f} kW "
              f"(ductless HPs {Y['cap_dhp']:.1f} kW); homes per circuit type {Y['homes_by_use']}")
    _, _, pth, _, ptc, _ = fit_bathtub_stick(P['T'], P['net'])
    pmh = U._sf_arm(P['T'], np.clip(P['heat'] / P['cap_h'], 0, 1), pth, 'h')[1]
    pmc = U._sf_arm(P['T'], np.clip(P['cool'] / P['cap_c'], 0, 1), ptc, 'c')[1]
    nb, sh, th, sc, tc, r2 = fit_bathtub_stick(X['T'], X['net'])
    T = X['T']
    sfh, sfc = np.clip(X['heat'] / X['cap_h'], 0, 1), np.clip(X['cool'] / X['cap_c'], 0, 1)
    omh, omc = U._sf_arm(T, sfh, th, 'h')[1], U._sf_arm(T, sfc, tc, 'c')[1]
    _, rsh, _, rr2 = fit_hockey_stick(T, X['net'] - X['heat'], T_BALANCE_BOUNDS)
    _, hsh, _, _ = fit_hockey_stick(T, X['heat'], T_BALANCE_BOUNDS)
    print(f"{target} net load: s_h {sh:.3f} (heating circuits alone {hsh:.3f}, rest {rsh:.3f} R2 {rr2:.2f}) "
          f"T_h {th:.1f}; s_c {sc:.3f} T_c {tc:.1f}; R2 {r2:.2f}; cooling days {(T > tc).sum()}")
    rows = []
    for reg, s, m, om, cap, mask, sf, dist in (
            ('heating', sh, pmh, omh, X['cap_h'], T < th, sfh, np.maximum(0, th - T)),
            ('cooling', sc, pmc, omc, X['cap_c'], T > tc, sfc, np.maximum(0, T - tc))):
        ce = s / m
        sfe = np.clip(m * dist, 0, 1)
        load = X['heat'] if reg == 'heating' else X['cool']
        e_est, e_act = (s * dist * 24)[mask].sum(), (load * 24)[mask].sum()
        fe, fa = (sfe * (1 - sfe))[mask].sum() * ce, (sf * (1 - sf))[mask].sum() * cap
        rows.append(dict(regime=reg, m_pilot=m, m_own=om, cap=cap, cap_e=ce, err=(ce - cap) / cap * 100,
                         oracle=(s / om - cap) / cap * 100, energy=(e_est - e_act) / e_act * 100,
                         flex=fe / fa, days=int(mask.sum())))
    R = pd.DataFrame(rows)
    print(R.round(3).to_string(index=False))
    return R


OSLO_BLOCKS = (6470, 6471, 6472, 6473, 6474, 6475, 6476, 6477, 6478, 6499)


def _oslo_blocks():
    """Daily frames of the ten electric-heated COFACTOR apartment blocks (Oslo/Baerum).

    Per block: outdoor temperature, net load (ElImp, whole block), heating-system
    electricity (ElHt, else ElMix), apartment import (ElImp_apt) and the block's
    heating capacity (99.9th percentile of its hourly heating-system draw), in kW.
    """
    from build_extra_frames import _load_cofactor_building, _heat_channel
    from hp_capacity import robust_series_peak
    out = {}
    for b in OSLO_BLOCKS:
        df, units = _load_cofactor_building(b)
        hc = _heat_channel(df)
        apt = pd.to_numeric(df['ElImp_apt'], errors='coerce') if 'ElImp_apt' in df else None
        h = pd.DataFrame({'T': df['Tout'], 'net': df['ElImp'] / 1000.0, 'etl': hc / 1000.0,
                          'apt': (apt / 1000.0) if apt is not None else np.nan})
        d = h.resample('D').mean()
        d = d[h['net'].resample('D').count() >= 20]
        out[b] = dict(daily=d, units=units, channel='ElHt' if (hc is df.get('ElHt')) else 'ElMix',
                      cap=float(robust_series_peak(h['etl'].dropna())))
    return out


def oslo_pool_transfer(B=None, blocks=OSLO_BLOCKS):
    """SF transfer between two disjoint halves of the Oslo ``blocks`` (every split).

    Each pool is aggregated on the days all ten blocks report. The pilot pool's SF
    fit, at its own net-load threshold, supplies m_h; the target pool's capacity is
    s_h / m_h (Eq. capacity), against the sum of its blocks' heating capacities.
    """
    from itertools import combinations
    B = _oslo_blocks() if B is None else B
    days = None
    for v in B.values():
        ok = v['daily'][['T', 'net', 'etl']].dropna().index
        days = ok if days is None else days.intersection(ok)
    D = {b: v['daily'].loc[days] for b, v in B.items()}
    print(f'{len(days)} common days ({days.min().date()} to {days.max().date()})')
    rows = []
    D = {b: D[b] for b in blocks}
    for b, d in D.items():
        T = d['T'].to_numpy(); _, sh, th, _ = fit_hockey_stick(T, d['net'].to_numpy(), T_BALANCE_BOUNDS)
        m = U._sf_arm(T, np.clip(d['etl'].to_numpy() / B[b]['cap'], 0, 1), th, 'h')[1]
        _, se, _, _ = fit_hockey_stick(T, d['etl'].to_numpy(), T_BALANCE_BOUNDS)
        sa = fit_hockey_stick(T, d['apt'].to_numpy(), T_BALANCE_BOUNDS)[1] if d['apt'].notna().all() else np.nan
        rows.append(dict(block=b, units=B[b]['units'], channel=B[b]['channel'], cap=B[b]['cap'], T_h=th,
                         s_net=sh, s_etl=se, s_apt=sa, etl_share_of_s=se / sh, m_h=m))
    print(pd.DataFrame(rows).set_index('block').round(4).to_string())

    def pool(bs):
        d = sum(D[b][['net', 'etl']] for b in bs)
        T = np.mean([D[b]['T'].to_numpy() for b in bs], axis=0)
        return T, d['net'].to_numpy(), d['etl'].to_numpy(), sum(B[b]['cap'] for b in bs)
    res = []
    for A in combinations(blocks, len(blocks) // 2):
        if blocks[0] not in A:
            continue                                    # each split once; both directions below
        Bset = tuple(b for b in blocks if b not in A)
        for pil, tgt in ((A, Bset), (Bset, A)):
            Tp, netp, etlp, capp = pool(pil)
            _, _, thp, _ = fit_hockey_stick(Tp, netp, T_BALANCE_BOUNDS)
            mp = U._sf_arm(Tp, np.clip(etlp / capp, 0, 1), thp, 'h')[1]
            Tt, nett, etlt, capt = pool(tgt)
            _, sh, tht, _ = fit_hockey_stick(Tt, nett, T_BALANCE_BOUNDS)
            mo = U._sf_arm(Tt, np.clip(etlt / capt, 0, 1), tht, 'h')[1]
            res.append(dict(m_pilot=mp, m_own=mo, err=(sh / mp - capt) / capt * 100,
                            oracle=(sh / mo - capt) / capt * 100, slope_ratio=mo / mp))
    R = pd.DataFrame(res)
    q = lambda s: f'{s.median():+.1f} [{s.quantile(.25):+.1f}, {s.quantile(.75):+.1f}]'
    print(f'{len(R)} pilot->target transfers ({len(R) // 2} splits x 2 directions)')
    print(f'  capacity error %  median [IQR]: {q(R.err)}')
    print(f'  oracle error %    median [IQR]: {q(R.oracle)}')
    print(f'  own/pilot slope ratio median [IQR]: {R.slope_ratio.median():.2f} '
          f'[{R.slope_ratio.quantile(.25):.2f}, {R.slope_ratio.quantile(.75):.2f}]; '
          f'|error| < 10% in {(R.err.abs() < 10).mean() * 100:.0f}% of transfers, < 20% in {(R.err.abs() < 20).mean() * 100:.0f}%')
    return R


def _bpa_homes():
    """Daily heating/cooling system load of the BPA HPHC field-study homes.

    Per home: outdoor temperature (deg C; the -40 sentinel is dropped), heat-pump
    system plus backup resistance power (kW, daily mean of hourly values, days with
    >= 20 hours) and the capacity as the 99.9th percentile of the hourly sum.
    """
    import glob
    out = {}
    for f in sorted(glob.glob('data/bpa_hphc/*_hourly*.csv')):
        d = pd.read_csv(f)
        t = pd.to_datetime(d['local_datetime'].str[:19], format='%m/%d/%Y %H:%M:%S')
        T = (d['OA_temp_F'].where(d['OA_temp_F'] > -39.9) - 32) * 5.0 / 9.0
        load = d['HP_system_pwr_kW'].fillna(0) + d['backup_system_kW'].fillna(0)
        h = pd.DataFrame({'T': T.to_numpy(), 'load': load.to_numpy(), 'hp': d['HP_system_pwr_kW'].fillna(0).to_numpy()},
                         index=t).groupby(level=0).agg({'T': 'mean', 'load': 'sum', 'hp': 'sum'})
        day = h.resample('D').agg({'T': 'mean', 'load': ['mean', 'count']})
        day.columns = ['T', 'load', 'n']
        day = day[day['n'] >= 20].drop(columns='n').dropna()
        # cooling capacity excludes the (heating-only) backup resistance
        out[d['site_id'].iloc[0]] = dict(daily=day, cap=float(h['load'].quantile(0.999)),
                                         cap_cool=float(h['hp'].quantile(0.999)))
    return out


def _pool_sf(H, homes, min_frac=0.8):
    """Pool heating load and SF slope for a set of homes.

    A day counts when at least ``min_frac`` of the homes report; the load of the
    missing homes is imputed at the pool's SF of that day (reporting load scaled by
    total over reporting capacity), which leaves the SF itself unchanged.
    """
    from hp_common import fit_bathtub_stick
    L = pd.DataFrame({h: H[h]['daily']['load'] for h in homes})
    Tt = pd.DataFrame({h: H[h]['daily']['T'] for h in homes})
    caps = pd.Series({h: H[h]['cap'] for h in homes})
    rep = L.notna() & Tt.notna()
    keep = rep.mean(axis=1) >= min_frac
    if keep.sum() < 60:
        return None
    L, Tt, rep = L[keep], Tt[keep], rep[keep]
    cap = float(caps.sum())
    cap_rep = rep.mul(caps, axis=1).sum(axis=1)
    load = (L.where(rep).sum(axis=1) * cap / cap_rep).to_numpy()
    T = Tt.where(rep).mean(axis=1).to_numpy()
    days = L.index
    try:
        _, sh, th, _, _, _ = fit_bathtub_stick(T, load)
    except Exception:
        _, sh, th, _ = fit_hockey_stick(T, load, T_BALANCE_BOUNDS)
    b, m, _, r2 = U._sf_arm(T, np.clip(load / cap, 0, 1), th, 'h')
    return dict(days=len(days), T_h=th, s_h=sh, cap=cap, b=b, m=m, r2=r2, heat_days=int((T < th).sum()))


def bpa_pool_transfer(groups, n_splits=300, seed=0, H=None, min_frac=0.8, size=None):
    """Disjoint-pool SF transfer among the BPA homes listed in ``groups`` (one set).

    Random half splits (both directions): the pilot half's SF slope m_h against the
    target half's own, and the target capacity s_h / m_h. The target's numerator is
    its own heating-system load, so the error isolates the SF transfer.
    """
    H = _bpa_homes() if H is None else H
    homes = [h for h in H if any(h.startswith(g) for g in groups)] if isinstance(groups, (tuple, list)) else groups
    rng = np.random.default_rng(seed)
    whole = _pool_sf(H, homes, min_frac)
    print(f"{len(homes)} homes; all together: {whole['days']} common days, {whole['heat_days']} heating days, "
          f"T_h {whole['T_h']:.1f} C, m_h {whole['m']:.4f} (R2 {whole['r2']:.2f})")
    rows, seen = [], set()
    for _ in range(n_splits * 3):
        k = size or len(homes) // 2
        draw = rng.permutation(homes)
        perm, other = tuple(sorted(draw[:k])), tuple(sorted(draw[k:2 * k]))
        key = min(perm, other)
        if key in seen:
            continue
        seen.add(key)
        P, Q = _pool_sf(H, list(perm), min_frac), _pool_sf(H, list(other), min_frac)
        if P is None or Q is None:
            continue
        for pil, tgt in ((P, Q), (Q, P)):
            rows.append(dict(ratio=tgt['m'] / pil['m'], err=(tgt['s_h'] / pil['m'] - tgt['cap']) / tgt['cap'] * 100,
                             oracle=(tgt['s_h'] / tgt['m'] - tgt['cap']) / tgt['cap'] * 100,
                             m_pilot=pil['m'], m_target=tgt['m'], days=tgt['days']))
        if len(seen) >= n_splits:
            break
    R = pd.DataFrame(rows)
    q = lambda s, f='+.1f': f'{s.median():{f}} [{s.quantile(.25):{f}}, {s.quantile(.75):{f}}]'
    print(f'  {len(R)} transfers ({len(seen)} splits x 2): slope ratio {q(R.ratio, ".2f")}; '
          f'capacity error {q(R.err)} %; oracle {q(R.oracle)} %; |err| < 10% in {(R.err.abs() < 10).mean() * 100:.0f}%')
    return R


def _nrel_homes():
    """Daily heating-system load of the NREL cold-climate ASHP field-study homes.

    ``HP_system_pwr_kW`` equals outdoor unit + air handler (fan and auxiliary heat
    included), so it is the whole heating system. Same daily/capacity conventions
    as ``_bpa_homes``; keyed 'NREL <site>'.
    """
    import glob
    out = {}
    for f in sorted(glob.glob('data/nrel_ccashp/*HOUR*.csv')):
        d = pd.read_csv(f, low_memory=False,
                        usecols=['site_id', 'local_datetime', 'OA_temp_F', 'HP_system_pwr_kW', 'auxheat_pwr_kW'])
        t = pd.to_datetime(d['local_datetime'].astype(str).str[:19], errors='coerce')
        T = (pd.to_numeric(d['OA_temp_F'], errors='coerce') - 32) * 5.0 / 9.0
        load = pd.to_numeric(d['HP_system_pwr_kW'], errors='coerce')
        aux = pd.to_numeric(d['auxheat_pwr_kW'], errors='coerce').fillna(0)
        h = pd.DataFrame({'T': T.to_numpy(), 'load': load.to_numpy(), 'hp': (load - aux).to_numpy()}, index=t)
        h = h[h.index.notna()].groupby(level=0).mean()
        day = h.resample('D').agg({'T': 'mean', 'load': ['mean', 'count']})
        day.columns = ['T', 'load', 'n']
        day = day[day['n'] >= 20].drop(columns='n').dropna()
        # cooling capacity excludes the (heating-only) auxiliary resistance heat
        out['NREL ' + str(d['site_id'].iloc[0]).replace('site_', '')] = dict(
            daily=day, cap=float(h['load'].dropna().quantile(0.999)), cap_cool=float(h['hp'].dropna().quantile(0.999)))
    return out


def cross_study_transfer(H, pilot, target, n_boot=300, frac=0.8, seed=0, label='', min_frac=0.8):
    """SF transfer from one pool of homes to another (e.g. BPA -> NREL).

    Point estimate on the full pools, plus a bootstrap that redraws ``frac`` of the
    homes of each pool. The target's numerator is its own heating-system load.
    """
    rng = np.random.default_rng(seed)
    P, Q = _pool_sf(H, pilot, min_frac), _pool_sf(H, target, min_frac)
    print(f"{label}: pilot {len(pilot)} homes (m_h {P['m']:.4f}, T_h {P['T_h']:.1f}, {P['heat_days']} heating days) -> "
          f"target {len(target)} homes (own m_h {Q['m']:.4f}, T_h {Q['T_h']:.1f}, {Q['heat_days']} heating days)")
    rows = []
    for _ in range(n_boot):
        p = list(rng.choice(pilot, max(2, int(round(frac * len(pilot)))), replace=False))
        q = list(rng.choice(target, max(2, int(round(frac * len(target)))), replace=False))
        Pb, Qb = _pool_sf(H, p, min_frac), _pool_sf(H, q, min_frac)
        if Pb is None or Qb is None:
            continue
        rows.append(dict(ratio=Qb['m'] / Pb['m'], err=(Qb['s_h'] / Pb['m'] - Qb['cap']) / Qb['cap'] * 100))
    R = pd.DataFrame(rows)
    print(f"   slope ratio own/pilot {Q['m'] / P['m']:.2f} (bootstrap {R.ratio.quantile(.1):.2f}-{R.ratio.quantile(.9):.2f}); "
          f"capacity error {(Q['s_h'] / P['m'] - Q['cap']) / Q['cap'] * 100:+.0f}% "
          f"(bootstrap 10-90% {R.err.quantile(.1):+.0f} to {R.err.quantile(.9):+.0f}%)")
    return R


def _read_xlsx_zip(raw):
    """First sheet of an .xlsx given as bytes -> DataFrame (no openpyxl needed)."""
    import io
    import re
    import xml.etree.ElementTree as ET
    import zipfile
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    X = zipfile.ZipFile(io.BytesIO(raw))
    ss = ([''.join(t.text or '' for t in si.iter('{%s}t' % ns['m']))
           for si in ET.fromstring(X.read('xl/sharedStrings.xml')).findall('m:si', ns)]
          if 'xl/sharedStrings.xml' in X.namelist() else [])
    rows = ET.fromstring(X.read('xl/worksheets/sheet1.xml')).find('m:sheetData', ns).findall('m:row', ns)

    def cells(r):
        out = {}
        for c in r.findall('m:c', ns):
            v = c.find('m:v', ns)
            out[re.match(r'[A-Z]+', c.get('r')).group()] = (ss[int(v.text)] if c.get('t') == 's' else v.text) if v is not None else None
        return out
    hdr = cells(rows[0])
    return pd.DataFrame([{hdr[k]: v for k, v in cells(r).items() if k in hdr} for r in rows[1:]])


def _hadcet():
    """Daily Central England Temperature (Met Office HadCET), deg C, indexed by date."""
    t = pd.read_csv('data/hadcet/meantemp_daily_totals.txt', sep=r'\s+', skiprows=1, names=['date', 'T'])
    t['date'] = pd.to_datetime(t['date'], errors='coerce')
    return t.dropna().set_index('date')['T'].astype(float)


def _rhpp_homes(drop_flagged=True, min_days=250):
    """RHPP Sample B2 homes (UKDA SN 8151) as {site: dict(daily=[T, load], cap, meta)}.

    Load = daily mean electric heating-system power (E_hp + E_dhw + E_sp + E_boost),
    capacity = 99.9th percentile of the 15-min load (``scripts/rhpp_extract.py``).
    RHPP has no outdoor temperature and no site locations, so T is the national
    HadCET daily mean for every home.
    """
    import zipfile
    D = pd.read_parquet('data/rhpp_daily.parquet')
    S = pd.read_parquet('data/rhpp_sites.parquet').set_index('site')
    with zipfile.ZipFile('data/RHPP_GB.zip') as z:
        M = _read_xlsx_zip(z.read('UKDA-8151-csv/mrdoc/excel/8151_rhpp_metadata.xlsx'))
    M['site'] = M['Site.ID'].str.upper()
    M = M.set_index('site')
    T = _hadcet()
    out = {}
    for site, g in D.groupby('site'):
        key = site.upper()
        meta = M.loc[key] if key in M.index else None
        if drop_flagged and meta is not None and str(meta.get('Incorrect.Monitoring') or '').strip():
            continue
        day = pd.DataFrame({'load': g.set_index('day')['E_total'].to_numpy()},
                           index=pd.DatetimeIndex(g['day']).normalize())
        day['T'] = T.reindex(day.index).to_numpy()
        day = day.dropna()
        if len(day) < min_days or S.loc[site, 'cap'] <= 0:
            continue
        out[key] = dict(daily=day[['T', 'load']], cap=float(S.loc[site, 'cap']),
                        hp=(str(meta['Heat.pump.type']).strip().upper() if meta is not None else '?'),
                        tenure=(str(meta['Site.type']).strip().lower() if meta is not None else '?'))
    return out


def _lcl_base(window=('2013-09-01', '2014-02-28'), tariffs=('n',)):
    """Daily mean load (kW) of gas-heated LCL households (UKDA SN 7857), by heater count.

    Returns (daily DataFrame days x households, Series household -> portable electric
    heaters). Only gas central-heating households are kept. The survey's heating
    answers sit one label off in survey_questions.csv: the heating-system answers are
    in Q248 and the number of portable electric heaters in Q304.
    """
    import io
    import zipfile
    p = 'UKDA-7857-csv/csv/data_collection/data_tables/'
    with zipfile.ZipFile('data/LCL_2013.zip') as Z:
        a = pd.read_csv(io.BytesIO(Z.read(p + 'survey_answers.csv')), encoding='latin-1', low_memory=False)
        sys_ = a['Q248'].astype(str)
        gas = sys_.str.contains('gas boiler', case=False) & sys_.str.contains('central heating', case=False)
        heaters = pd.to_numeric(a['Q304'], errors='coerce')
        sel = a.loc[gas & heaters.notna(), 'Household_id'].astype(str)
        htr = pd.Series(heaters[gas & heaters.notna()].to_numpy(), index=sel.to_numpy())
        parts = []
        for f in (f'consumption_{t}.csv' for t in tariffs):      # n: standard tariff; d: dynamic time-of-use
            cols = [c for c in pd.read_csv(Z.open(p + f), nrows=0).columns if c in set(sel)]
            x = pd.read_csv(Z.open(p + f), usecols=['GMT'] + cols)
            x['GMT'] = pd.to_datetime(x['GMT'])
            x = x.set_index('GMT').loc[window[0]:window[1] + ' 23:59']
            day = x.resample('D').mean() * 2.0                      # kWh per half hour -> kW
            day = day.where(x.resample('D').count() >= 0.8 * 48)
            parts.append(day)
    D = pd.concat(parts, axis=1)
    D = D.loc[:, D.notna().mean() >= 0.8]
    return D, htr.reindex(D.columns)


def rhpp_lcl_capacity(k=20, n_splits=200, seed=0, window=('2013-09-01', '2014-02-28'), tariffs=('n',)):
    """Semi-synthetic GB capacity test: RHPP heat pumps plus LCL gas-heated base load.

    Each split draws disjoint pilot and target pools of ``k`` RHPP homes and ``k`` LCL
    households. The pilot's SF slope, at its own net-load threshold, gives m_h; the
    target's net load (HP + base) gives s_h and the capacity s_h / m_h (Eq. capacity),
    scored against the sum of its HPs' capacities. Run for 'clean' bases (no portable
    electric heater) and 'heater-rich' bases (>= 2 portable heaters).
    """
    H0 = pickle.load(open('scratchpad/rhpp_homes.pkl', 'rb')) if os.path.exists('scratchpad/rhpp_homes.pkl') else _rhpp_homes()
    w = pd.date_range(*window)
    HP = {h: v for h, v in H0.items() if v['daily'].index.isin(w).sum() >= 0.8 * len(w)}
    L = pd.DataFrame({h: v['daily']['load'] for h, v in HP.items()}).reindex(w)
    caps = pd.Series({h: v['cap'] for h, v in HP.items()})
    T = _hadcet().reindex(w)
    B, htr = _lcl_base(window, tariffs)
    B = B.reindex(w)
    bases = {'clean (0 portable heaters)': list(htr.index[htr == 0]),
             'heater-rich (>= 2 portable heaters)': list(htr.index[htr >= 2])}
    zero = B[bases['clean (0 portable heaters)']]
    zm = pd.DataFrame({'T': T, 'y': zero.mean(axis=1)}).dropna()
    _, zs, _, _ = fit_hockey_stick(zm['T'].to_numpy(), zm['y'].to_numpy(), T_BALANCE_BOUNDS)
    print(f'{len(HP)} RHPP homes, {len(w)} days; LCL gas-heated bases: '
          + ', '.join(f'{n} {len(v)}' for n, v in bases.items())
          + f'; clean-base heating slope {zs:.4f} kW/C per household (Kloten HP-free 0.0055)')

    def pool(hps, bs):
        rep = L[hps].notna(); keep = rep.mean(axis=1) >= 0.8
        cap = float(caps[hps].sum())
        hp = (L[hps].sum(axis=1) * cap / rep.mul(caps[hps], axis=1).sum(axis=1))
        repb = B[bs].notna(); keep &= repb.mean(axis=1) >= 0.8
        base = B[bs].mean(axis=1) * len(bs)
        d = pd.DataFrame({'T': T, 'hp': hp, 'net': hp + base})[keep].dropna()
        return d['T'].to_numpy(), d['hp'].to_numpy(), d['net'].to_numpy(), cap

    rng = np.random.default_rng(seed)
    out = {}
    for name, pool_b in bases.items():
        if len(pool_b) < 2 * k:
            print(f'  {name}: only {len(pool_b)} households, need {2 * k}; skipped'); continue
        rows = []
        for _ in range(n_splits):
            hh = list(rng.choice(list(HP), 2 * k, replace=False)); bb = list(rng.choice(pool_b, 2 * k, replace=False))
            Tp, hpp, netp, capp = pool(hh[:k], bb[:k])
            _, _, thp, _ = fit_hockey_stick(Tp, netp, T_BALANCE_BOUNDS)
            mp = U._sf_arm(Tp, np.clip(hpp / capp, 0, 1), thp, 'h')[1]
            Tt, hpt, nett, capt = pool(hh[k:], bb[k:])
            _, sh, tht, _ = fit_hockey_stick(Tt, nett, T_BALANCE_BOUNDS)
            _, sh_hp, _, _ = fit_hockey_stick(Tt, hpt, T_BALANCE_BOUNDS)
            mo = U._sf_arm(Tt, np.clip(hpt / capt, 0, 1), tht, 'h')[1]
            below = Tt < tht
            e_est = (sh * (tht - Tt[below]) * 24).sum(); e_act = (hpt[below] * 24).sum()
            rows.append(dict(err=(sh / mp - capt) / capt * 100, oracle=(sh / mo - capt) / capt * 100,
                             ratio=mo / mp, bias=sh / sh_hp, energy=(e_est - e_act) / e_act * 100, days=len(Tt)))
        R = pd.DataFrame(rows)
        q = lambda s, f='+.0f': f'{s.median():{f}} [{s.quantile(.25):{f}}, {s.quantile(.75):{f}}]'
        print(f'  {name}, {k}+{k} per pool, {len(R)} splits, ~{int(R.days.median())} days: capacity {q(R.err)} %; '
              f'oracle {q(R.oracle)} %; slope ratio {q(R.ratio, ".2f")}; net/HP slope {q(R.bias, ".2f")}; '
              f'energy (below T_h) {q(R.energy)} %')
        out[name] = R
    return out


BPA_INLAND = ('CEC 11', 'CEC 12', 'CEC 13', 'CEC 31', 'CEC 32', 'CEC 33', 'CEC 41',
              'INL 02', 'INL 41', 'INL 42', 'INL 44', 'INL 46')
NREL_WA = ('NREL 1', 'NREL 2', 'NREL 4', 'NREL 5', 'NREL 6', 'NREL 7', 'NREL 8', 'NREL 11', 'NREL 12', 'NREL 13')


def tab_bpa_nrel():
    """tab_bpa_nrel: SF transfer with complete heating submetering (BPA and NREL).

    Within BPA: disjoint random halves (300 splits, both directions), median and
    interquartile range. Across the two studies: the full inland BPA pool against
    the ten NREL Washington homes, with a bootstrap that redraws 80% of each pool
    (10th-90th percentile). The target's numerator is its own heating-system load,
    so the capacity error isolates the SF transfer.
    """
    H = _bpa_homes(); H.update(_nrel_homes())
    groups = [('Tacoma, HZ1', [h for h in H if h.startswith('TAC')]),
              ('W. Washington, HZ1', [h for h in H if h[:3] in ('TAC', 'SNO')]),
              ('inland, HZ2', list(BPA_INLAND))]
    rows = []
    for name, hs in groups:
        whole = _pool_sf(H, hs)
        R = bpa_pool_transfer(hs, H=H)
        rows.append(f"BPA {name} & {len(hs) // 2}/{len(hs) - len(hs) // 2} & {whole['m']:.3f} & "
                    f"{R.ratio.median():.2f} [{R.ratio.quantile(.25):.2f}, {R.ratio.quantile(.75):.2f}] & "
                    f"{R.err.quantile(.25):+.0f} to {R.err.quantile(.75):+.0f} \\\\")
    for lab, pil, tgt in (('BPA inland $\\rightarrow$ NREL', list(BPA_INLAND), list(NREL_WA)),
                          ('NREL $\\rightarrow$ BPA inland', list(NREL_WA), list(BPA_INLAND))):
        P, Q = _pool_sf(H, pil), _pool_sf(H, tgt)
        R = cross_study_transfer(H, pil, tgt, label=lab)
        rows.append(f"{lab} & {len(pil)}/{len(tgt)} & {P['m']:.3f}/{Q['m']:.3f} & "
                    f"{Q['m'] / P['m']:.2f} ({R.ratio.quantile(.1):.2f}, {R.ratio.quantile(.9):.2f}) & "
                    f"{(Q['s_h'] / P['m'] - Q['cap']) / Q['cap'] * 100:+.0f} ({R.err.quantile(.1):+.0f}, {R.err.quantile(.9):+.0f}) \\\\")
    tex = r"""\begin{table}[t]
\centering
\caption{SF transfer with complete heating submetering (heat pump and backup heat). Top: disjoint halves of BPA pools, median and interquartile range over 600 transfers. Bottom: across the BPA and NREL studies, with the 10th--90th percentiles of a bootstrap over homes. The target's numerator is its own heating load, so the capacity error isolates the transfer}
\label{tab:bpa-nrel}
\setlength{\tabcolsep}{3pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccc}
\toprule
pilot $\rightarrow$ target & homes & $m_h$ ($^\circ$C$^{-1}$) & $m_h$ ratio & capacity error (\%) \\
\midrule
""" + '\n'.join(rows[:3]) + "\n\\midrule\n" + '\n'.join(rows[3:]) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    open('paper/tables/tab_bpa_nrel.tex', 'w', encoding='utf-8', newline='\n').write(tex)
    print('wrote tab_bpa_nrel.tex')


def _pool_frame(H, homes, min_frac=0.8):
    """Daily pooled temperature and heating-system load of a set of homes.

    Same day rule and imputation as ``_pool_sf``. Returns (T, load, cap_heat, cap_cool).
    """
    L = pd.DataFrame({h: H[h]['daily']['load'] for h in homes})
    Tt = pd.DataFrame({h: H[h]['daily']['T'] for h in homes})
    caps = pd.Series({h: H[h]['cap'] for h in homes})
    rep = L.notna() & Tt.notna()
    keep = rep.mean(axis=1) >= min_frac
    L, Tt, rep = L[keep], Tt[keep], rep[keep]
    cap = float(caps.sum())
    load = L.where(rep).sum(axis=1) * cap / rep.mul(caps, axis=1).sum(axis=1)
    T = Tt.where(rep).mean(axis=1)
    return T.to_numpy(), load.to_numpy(), cap, float(sum(H[h].get('cap_cool', 0.0) for h in homes))


def _rhpp_concurrent(min_cover=0.7, window=('2013-11-01', '2014-10-31')):
    """RHPP homes covering >= ``min_cover`` of RHPP's concurrent year, restricted to it."""
    H0 = (pickle.load(open('scratchpad/rhpp_homes.pkl', 'rb')) if os.path.exists('scratchpad/rhpp_homes.pkl')
          else _rhpp_homes())
    w = pd.date_range(*window)
    return {k: dict(v, daily=v['daily'][v['daily'].index.isin(w)]) for k, v in H0.items()
            if v['daily'].index.isin(w).sum() >= min_cover * len(w)}


def extra_cross_rows():
    """Table I rows for the datasets without whole-home load (BPA, NREL, RHPP).

    The heating-system load stands in for the net load, so only its thresholds are
    reported in the net-load block; the SF arms are anchored at those thresholds.
    Writes scratchpad/extra_rows.csv.
    """
    H = _bpa_homes(); H.update(_nrel_homes())
    specs = [('BPA W. Washington', [h for h in H if h[:3] in ('TAC', 'SNO')], 0.8),
             ('BPA inland', list(BPA_INLAND), 0.8),
             ('NREL Washington', list(NREL_WA), 0.8)]
    rows = []
    for lab, hs, mf in specs:
        T, load, cap, capc = _pool_frame(H, hs, mf)
        rows.append(U.fit_row(lab, len(hs), T, load, np.where(T < 15, load, 0.0), np.where(T > 20, load, 0.0), cap, capc))
    R = _rhpp_concurrent()
    T, load, cap, _ = _pool_frame(R, list(R), 0.7)
    rows.append(U.fit_row('RHPP GB', len(R), T, load, load, None, cap, 0.0))
    out = pd.DataFrame(rows)
    out.to_csv('scratchpad/extra_rows.csv', index=False)
    print(out[['label', 'n', 'mode', 'T_h', 'T_c', 'b_h', 'm_h', 'SF_cold', 'R2_SFh', 'm_c', 'SF_hot', 'R2_SFc']].round(3).to_string())
    return out


def tab_rhpp():
    """tab_rhpp: SF transfer across pool sizes and populations in RHPP (GB).

    182 homes covering >= 70% of RHPP's concurrent year (Nov 2013 - Oct 2014), HadCET
    temperature. Top: disjoint random pools of k homes (300 splits, both directions),
    median and interquartile range. Bottom: transfer between technologies and tenures,
    with the 10th-90th percentiles of a bootstrap over homes.
    """
    H = _rhpp_concurrent(); homes = list(H)
    whole = _pool_sf(H, homes, 0.7)
    rows = []
    for k in (10, 25, 50, len(homes) // 2):
        R = bpa_pool_transfer(homes, H=H, min_frac=0.7, size=k)
        rows.append(f"random pools, {k} vs {k} & {k}/{k} & {whole['m']:.3f} & "
                    f"{R.ratio.median():.2f} [{R.ratio.quantile(.25):.2f}, {R.ratio.quantile(.75):.2f}] & "
                    f"{R.err.quantile(.25):+.0f} to {R.err.quantile(.75):+.0f} \\\\")
    grp = {'ASHP': [h for h in homes if H[h]['hp'] == 'ASHP'], 'GSHP': [h for h in homes if H[h]['hp'] == 'GSHP'],
           'social': [h for h in homes if H[h]['tenure'] == 'rsl'], 'private': [h for h in homes if H[h]['tenure'] == 'domestic']}
    for a, b in (('ASHP', 'GSHP'), ('GSHP', 'ASHP'), ('social', 'private'), ('private', 'social')):
        P, Q = _pool_sf(H, grp[a], 0.7), _pool_sf(H, grp[b], 0.7)
        R = cross_study_transfer(H, grp[a], grp[b], label=f'{a} -> {b}', min_frac=0.7)
        rows.append(f"{a} $\\rightarrow$ {b} & {len(grp[a])}/{len(grp[b])} & {P['m']:.3f}/{Q['m']:.3f} & "
                    f"{Q['m'] / P['m']:.2f} ({R.ratio.quantile(.1):.2f}, {R.ratio.quantile(.9):.2f}) & "
                    f"{(Q['s_h'] / P['m'] - Q['cap']) / Q['cap'] * 100:+.0f} ({R.err.quantile(.1):+.0f}, {R.err.quantile(.9):+.0f}) \\\\")
    tex = r"""\begin{table}[t]
\centering
\caption{SF transfer in the GB RHPP trial (182 homes, heat pump and electric boost submetered). Top: disjoint random pools, median and interquartile range over 600 transfers. Bottom: between heat-pump technologies and between social and private housing, with the 10th--90th percentiles of a bootstrap over homes. The target's numerator is its own heating load}
\label{tab:rhpp}
\setlength{\tabcolsep}{3pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccc}
\toprule
pilot $\rightarrow$ target & homes & $m_h$ ($^\circ$C$^{-1}$) & $m_h$ ratio & capacity error (\%) \\
\midrule
""" + '\n'.join(rows[:4]) + "\n\\midrule\n" + '\n'.join(rows[4:]) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    open('paper/tables/tab_rhpp.tex', 'w', encoding='utf-8', newline='\n').write(tex)
    print('wrote tab_rhpp.tex')


def _daily_bootstrap(Dp, Dt, n_boot=300, frac=0.8, seed=0):
    """Own/pilot SF-slope ratios of a bootstrap that redraws ``frac`` of the HP homes of
    a pilot and a target daily pool (``_daily_pools`` entries), each SF fit anchored at
    its own net-load threshold (``_pilot_fit``)."""
    rng = np.random.default_rng(seed)
    npil, ntgt = len(Dp['cap']), len(Dt['cap'])
    out = []
    for _ in range(n_boot):
        A = rng.choice(npil, max(2, int(round(frac * npil))), replace=False)
        B = rng.choice(ntgt, max(2, int(round(frac * ntgt))), replace=False)
        out.append(_pilot_fit(Dt['T'], Dt, B)[1] / _pilot_fit(Dp['T'], Dp, A)[1])
    return pd.Series(out)


def tab_transfer(n_splits=300, seed=0):
    """tab_transfer: own/pilot SF-slope ratio between populations, all with the IQR.

    Random splits: disjoint halves (or pools of k homes), both directions; the median
    ratio and its IQR. Between groups: the ratio of the full pools and the IQR of a
    bootstrap that redraws 80% of the homes of each pool. The ratio minus one is the
    capacity error caused by the transfer alone.
    """
    q = lambda s: f"[{s.quantile(.25):.2f}, {s.quantile(.75):.2f}]"
    rows = {}
    # Kloten halves, from the daily pools
    D = _daily_pools(); K = D['KLO']; nk = len(K['cap'])
    rng = np.random.default_rng(seed); r = []
    for _ in range(n_splits):
        A, B = _pilot_split(nk, rng)
        ma, mb = _pilot_fit(K['T'], K, A)[1], _pilot_fit(K['T'], K, B)[1]
        r += [mb / ma, ma / mb]
    r = pd.Series(r); mk = _pilot_fit(K['T'], K, np.arange(nk))[1]
    rows['kk'] = (r'Kloten $\rightarrow$ Kloten', 'CH', f'{nk // 2}/{nk - nk // 2}', f'{mk:.3f}', r.median(), r)
    # Oslo block halves
    Ro = oslo_pool_transfer()
    rows['oo'] = (r'Oslo $\rightarrow$ Oslo', 'NO', '5/5 blocks', f'{Ro.m_pilot.median():.3f}',
                  Ro.slope_ratio.median(), Ro.slope_ratio)
    # RHPP pools, technologies and tenures
    Hr = _rhpp_concurrent(); homes = list(Hr); mr = _pool_sf(Hr, homes, 0.7)['m']
    for k in (10, len(homes) // 2):
        R = bpa_pool_transfer(homes, H=Hr, min_frac=0.7, size=k, n_splits=n_splits, seed=seed)
        rows[f'rr{k}'] = (r'RHPP $\rightarrow$ RHPP', 'GB', f'{k}/{k}', f'{mr:.3f}', R.ratio.median(), R.ratio)
    grp = {'ASHP': [h for h in homes if Hr[h]['hp'] == 'ASHP'], 'GSHP': [h for h in homes if Hr[h]['hp'] == 'GSHP'],
           'social': [h for h in homes if Hr[h]['tenure'] == 'rsl'],
           'private': [h for h in homes if Hr[h]['tenure'] == 'domestic']}
    for a, b in (('ASHP', 'GSHP'), ('GSHP', 'ASHP'), ('social', 'private'), ('private', 'social')):
        P, Q = _pool_sf(Hr, grp[a], 0.7), _pool_sf(Hr, grp[b], 0.7)
        R = cross_study_transfer(Hr, grp[a], grp[b], label=f'{a} -> {b}', min_frac=0.7, seed=seed)
        rows[a + b] = (rf'RHPP {a} $\rightarrow$ RHPP {b}', 'GB', f'{len(grp[a])}/{len(grp[b])}',
                       f"{P['m']:.3f}/{Q['m']:.3f}", Q['m'] / P['m'], R.ratio)
    # BPA heating zones and NREL
    Hb = _bpa_homes(); Hb.update(_nrel_homes())
    hz1 = [h for h in Hb if h[:3] in ('TAC', 'SNO')]; hz2 = list(BPA_INLAND); nrel = list(NREL_WA)
    for key, lab, hs in (('b1', 'HZ1', hz1), ('b2', 'HZ2', hz2)):
        R = bpa_pool_transfer(hs, H=Hb, n_splits=n_splits, seed=seed)
        rows[key] = (rf'BPA {lab} $\rightarrow$ BPA {lab}', 'US', f'{len(hs) // 2}/{len(hs) - len(hs) // 2}',
                     f"{_pool_sf(Hb, hs)['m']:.3f}", R.ratio.median(), R.ratio)
    for key, lab, pil, tgt in (('b2n', r'BPA HZ2 $\rightarrow$ NREL', hz2, nrel), ('nb2', r'NREL $\rightarrow$ BPA HZ2', nrel, hz2),
                               ('b12', r'BPA HZ1 $\rightarrow$ BPA HZ2', hz1, hz2), ('b21', r'BPA HZ2 $\rightarrow$ BPA HZ1', hz2, hz1)):
        P, Q = _pool_sf(Hb, pil), _pool_sf(Hb, tgt)
        R = cross_study_transfer(Hb, pil, tgt, label=lab, seed=seed)
        rows[key] = (lab, 'US', f'{len(pil)}/{len(tgt)}', f"{P['m']:.3f}/{Q['m']:.3f}", Q['m'] / P['m'], R.ratio)
    # Kloten -> real aggregates outside the pilot
    for st, lab, c in (('Hg', 'Hg', 'CH'), ('MqO', 'MqO', 'CH'), ('WPUQ', 'Hamelin', r'CH$\rightarrow$DE')):
        X = D[st]; mx = _pilot_fit(X['T'], X, np.arange(len(X['cap'])))[1]
        rows[st] = (rf'Kloten $\rightarrow$ {lab}', c, f"{nk}/{len(X['cap'])}", f'{mk:.3f}/{mx:.3f}', mx / mk,
                    _daily_bootstrap(K, X, seed=seed))
    blocks = [('Random splits', ['kk', 'oo', 'rr10', f'rr{len(homes) // 2}', 'b1', 'b2']),
              ('Between studies, same country and climate zone', ['Hg', 'MqO', 'b2n', 'nb2']),
              ('Between countries, same climate class (Cfb)', ['WPUQ']),
              ('Between HP technologies', ['ASHPGSHP', 'GSHPASHP']),
              ('Between social and private housing', ['socialprivate', 'privatesocial']),
              ('Between climate zones', ['b12', 'b21'])]
    body = []
    for title, keys in blocks:
        body.append(r'\multicolumn{4}{l}{\textit{' + title + r'}} \\')
        for k in keys:
            lab, c, n, m, est, dist = rows[k]
            print(f'{lab:45s} m_h {m:12s} {est:.2f} {q(dist)}')
            body.append(f'{lab} & {c} & {n} & {est:.2f} {q(dist)} \\\\')
        body.append(r'\midrule')
    tex = r"""\begin{table}[t]
\centering
\caption{Ratio of the target's own to the pilot's SF sensitivity [IQR over random splits or a bootstrap over homes]}
\label{tab:transfer}
\setlength{\tabcolsep}{2.5pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llcc}
\toprule
pilot $\rightarrow$ target & & homes & $m_h^{\mathrm{own}}/m_h^{\mathrm{pilot}}$ \\
\midrule
""" + '\n'.join(body[:-1]) + r"""
\bottomrule
\end{tabular}}
\end{table}"""
    open('paper/tables/tab_transfer.tex', 'w', encoding='utf-8', newline='\n').write(tex)
    print('wrote tab_transfer.tex')


NEEA_BASE = 'data/_neea_base_homes.pkl'
NEEA_ETL = NEEA_HEAT + tuple(u for u in NEEA_COOL if u not in NEEA_HEAT) + ('Gas Furnace (Component)',)


def _neea_site_temperature(sites):
    """Daily outdoor temperature (C) per NEEA home: own sensor, else its NOAA-station mean.

    Same rule as ``_neea_agg_temperature``, returned per home (days x homes).
    """
    t = pd.read_parquet('data/neea_temp_2023.parquet')
    t = t[t['regname'].astype(str).str.contains('_oa_')].copy()
    t['ee_site_id'] = t['ee_site_id'].astype(int)
    t['day'] = t['MIN_T_l'].dt.floor('D'); t['C'] = (t['temp'] - 32) * 5.0 / 9.0
    own = t.groupby(['ee_site_id', 'day'])['C'].mean().unstack(0)
    stn_of = pd.read_csv('data/SITES v9.2.csv').set_index('ee_site_id')['station_id']
    stn = own.T.groupby(stn_of.reindex(own.columns).to_numpy()).mean().T
    cols = {}
    for h in sites:
        by_stn = stn[stn_of[h]] if stn_of.get(h) in stn.columns else None
        mine = own[h] if h in own.columns else None
        if mine is None and by_stn is None:
            continue
        cols[h] = mine.fillna(by_stn) if (mine is not None and by_stn is not None) else (mine if mine is not None else by_stn)
    return pd.DataFrame(cols)


def _neea_base_homes(rebuild=False, min_days=250):
    """Daily non-ETL base load of NEEA HEMS homes in heating zones 1-2 (2023).

    Base = mains minus every metered heating/cooling circuit (``NEEA_ETL``: HPs,
    baseboard, furnaces, zonal heat, AC and the gas-furnace fan); water heating and
    all other loads stay in. Homes with solar are dropped. A day counts when the mains
    and every subtracted circuit report >= 90 of 96 samples; a home needs ``min_days``
    such days with temperature. ``gas`` flags homes whose POINTS inventory has a gas
    furnace and no electric heating circuit (AC allowed; it is subtracted). Built from
    ``data/neea_base_circuits_2023.parquet`` (``scripts/neea_extract.py --base``).
    """
    if os.path.exists(NEEA_BASE) and not rebuild:
        return pickle.load(open(NEEA_BASE, 'rb'))
    p = pd.read_parquet('data/neea_base_circuits_2023.parquet')
    p['End Use'] = p['End Use'].astype(str)
    solar = set(p.loc[p['End Use'].isin(['Mains With Solar', 'Solar', 'Other With Solar']), 'ee_site_id'])
    mains = set(p.loc[p['End Use'] == 'Mains', 'ee_site_id'])
    p = p[p['ee_site_id'].isin(mains - solar) & p['End Use'].isin(set(NEEA_ETL) | {'Mains'})]
    p['day'] = p['MIN_T_l'].dt.floor('D')
    cnt = p.groupby(['ee_site_id', 'regname', 'day'], observed=True).size()
    ok = (cnt >= 90).groupby(level=[0, 2]).all()
    ok = ok[ok]
    sign = np.where(p['End Use'] == 'Mains', 1.0, -1.0).astype('float32')
    b = (p.assign(pw=p['power'] * sign).groupby(['ee_site_id', 'MIN_T_l'])['pw'].sum().rename('pw').reset_index())
    b['day'] = b['MIN_T_l'].dt.floor('D')
    D = b.groupby(['ee_site_id', 'day'])['pw'].mean()
    D = D[D.index.isin(ok.index)].unstack(0)                                   # days x homes
    T = _neea_site_temperature(list(D.columns))
    sites = pd.read_csv('data/SITES v9.2.csv').set_index('ee_site_id')
    pts = pd.read_csv('data/POINTS v9.2.csv', low_memory=False)
    inv = pts.groupby('ee_site_id')['circuit_label_type_desc'].apply(lambda x: set(x.astype(str)))
    elec = set(NEEA_HEAT)
    out = {}
    for h in D.columns:
        if h not in T.columns:
            continue
        d = pd.DataFrame({'T': T[h], 'base': D[h]}).dropna()
        if len(d) < min_days:
            continue
        u = inv.get(h, set())
        out[h] = dict(daily=d, hz=int(sites.loc[h, 'hz']), state=str(sites.loc[h, 'state']),
                      gas=('Gas Furnace (Component)' in u) and not (u & elec))
    pickle.dump(out, open(NEEA_BASE, 'wb'))
    return out


def _match_base(base, Tref, window=30):
    """Base load of one donor home on the dates of ``Tref``, matched by temperature.

    For each target date, the donor day of the same day type (weekday/weekend) within
    +-``window`` days of the year whose temperature is nearest the target's. Returns
    (matched base Series on Tref's index, |dT| Series).
    """
    d = base.copy()
    doy, wk, Tb, Bb = d.index.dayofyear.to_numpy(), d.index.dayofweek.to_numpy() >= 5, d['T'].to_numpy(), d['base'].to_numpy()
    vals, gaps = np.full(len(Tref), np.nan), np.full(len(Tref), np.nan)
    for i, (day, t) in enumerate(Tref.items()):
        dd = np.abs(doy - day.dayofyear); dd = np.minimum(dd, 365 - dd)
        c = (dd <= window) & (wk == (day.dayofweek >= 5))
        if not c.any():
            continue
        j = np.flatnonzero(c)[np.argmin(np.abs(Tb[c] - t))]
        vals[i], gaps[i] = Bb[j], abs(Tb[j] - t)
    return pd.Series(vals, index=Tref.index), pd.Series(gaps, index=Tref.index)


def _pool_dated(H, homes, min_frac=0.8):
    """Daily pooled temperature and heating-system load on dates (as ``_pool_sf``)."""
    L = pd.DataFrame({h: H[h]['daily']['load'] for h in homes})
    Tt = pd.DataFrame({h: H[h]['daily']['T'] for h in homes})
    caps = pd.Series({h: H[h]['cap'] for h in homes})
    rep = L.notna() & Tt.notna()
    keep = rep.mean(axis=1) >= min_frac
    L, Tt, rep = L[keep], Tt[keep], rep[keep]
    cap = float(caps.sum())
    load = L.where(rep).sum(axis=1) * cap / rep.mul(caps, axis=1).sum(axis=1)
    return pd.DataFrame({'T': Tt.where(rep).mean(axis=1), 'hp': load}), cap


def _net_fit(T, y):
    """Heating sensitivity and threshold of a daily load (bathtub, else hockey stick)."""
    try:
        _, sh, th, _, _, _ = fit_bathtub_stick(T, y)
    except Exception:
        _, sh, th, _ = fit_hockey_stick(T, y, T_BALANCE_BOUNDS)
    return sh, th


def bpa_nrel_base_capacity(n_splits=200, seed=0, window=30):
    """Semi-synthetic BPA/NREL capacity test: heating systems plus NEEA base load.

    Each pool's net load is its homes' heating-system load plus the temperature-
    matched base load (``_match_base``) of as many NEEA homes of the same heating
    zone (1 for western Washington, 2 for inland BPA and NREL). Pilot and target draw
    disjoint base homes. Within an area, random halves; across studies, 80% of each
    pool. The pilot's SF slope at its own net-load threshold gives m_h; the target's
    net-load s_h gives s_h / m_h, scored against its heating-system capacity. Two base
    populations: gas-heated homes without electric heating ('gas') and all homes with
    their heating/cooling circuits removed ('all').
    """
    H = _bpa_homes(); H.update(_nrel_homes())
    NB = _neea_base_homes()
    west = [h for h in H if h[:3] in ('TAC', 'SNO')]
    areas = {'west': west, 'inland': list(BPA_INLAND), 'nrel': list(NREL_WA)}
    zone = {'west': 1, 'inland': 2, 'nrel': 2}
    # area reference temperature: mean over the area's homes
    Tref = {a: pd.DataFrame({h: H[h]['daily']['T'] for h in hs}).mean(axis=1).dropna() for a, hs in areas.items()}
    M, gap = {}, {}
    for a in areas:
        for b, v in NB.items():
            if v['hz'] == zone[a]:
                M[a, b], gap[a, b] = _match_base(v['daily'], Tref[a], window)
    pops = {z: {'gas': [b for b, v in NB.items() if v['hz'] == z and v['gas']],
                'all': [b for b, v in NB.items() if v['hz'] == z]} for z in (1, 2)}
    for z in (1, 2):
        g = np.concatenate([gap[a, b].dropna().to_numpy() for a in areas if zone[a] == z for b in pops[z]['all']])
        print(f'zone {z}: {len(pops[z]["all"])} base homes ({len(pops[z]["gas"])} gas-heated); '
              f'median |dT| of matched days {np.median(g):.2f} C, 95th pct {np.percentile(g, 95):.2f} C')

    def pool(area, hps, bs):
        d, cap = _pool_dated(H, hps)
        base = pd.concat([M[area, b] for b in bs], axis=1).reindex(d.index).sum(axis=1, min_count=len(bs))
        d = d.assign(net=d['hp'] + base).dropna()
        return d['T'].to_numpy(), d['hp'].to_numpy(), d['net'].to_numpy(), cap

    def one(pa, ph, ta, th_, bp, bt):
        Tp, hpp, netp, capp = pool(pa, ph, bp)
        _, thp = _net_fit(Tp, netp)
        mp = U._sf_arm(Tp, np.clip(hpp / capp, 0, 1), thp, 'h')[1]
        Tt, hpt, nett, capt = pool(ta, th_, bt)
        sh, tht = _net_fit(Tt, nett)
        sh_hp, _ = _net_fit(Tt, hpt)
        mo = U._sf_arm(Tt, np.clip(hpt / capt, 0, 1), tht, 'h')[1]
        return dict(err=(sh / mp - capt) / capt * 100, oracle=(sh / mo - capt) / capt * 100,
                    ratio=mo / mp, bias=sh / sh_hp)

    rng = np.random.default_rng(seed)
    cases = [('W. WA halves', 'west', 'west', 'half'), ('Inland halves', 'inland', 'inland', 'half'),
             ('Inland -> NREL', 'inland', 'nrel', 'boot'), ('NREL -> inland', 'nrel', 'inland', 'boot')]
    out = {}
    for pop in ('gas', 'all'):
        for lab, pa, ta, mode in cases:
            donors = pops[zone[ta]][pop]
            rows = []
            for _ in range(n_splits):
                if mode == 'half':
                    hs = list(rng.permutation(areas[pa])); k = len(hs) // 2
                    ph, th_ = hs[:k], hs[k:2 * k]
                else:
                    ph = list(rng.choice(areas[pa], int(round(.8 * len(areas[pa]))), replace=False))
                    th_ = list(rng.choice(areas[ta], int(round(.8 * len(areas[ta]))), replace=False))
                if len(donors) < len(ph) + len(th_):
                    break
                bb = list(rng.choice(donors, len(ph) + len(th_), replace=False))
                try:
                    rows.append(one(pa, ph, ta, th_, bb[:len(ph)], bb[len(ph):]))
                except Exception:
                    continue
            if not rows:
                print(f'  {pop:3s} {lab:15s}: only {len(donors)} donors, skipped'); continue
            R = pd.DataFrame(rows)
            q = lambda x, f='+.0f': f'{x.median():{f}} [{x.quantile(.25):{f}}, {x.quantile(.75):{f}}]'
            print(f'  {pop:3s} {lab:15s} ({len(donors)} donors, {len(R)} splits): capacity {q(R.err)} %; '
                  f'oracle {q(R.oracle)} %; slope ratio {q(R.ratio, ".2f")}; net/HP slope {q(R.bias, ".2f")}')
            out[pop, lab] = R
    return out


REAL_BOXES = 'data/_real_transfer_boxes.pkl'
RHPP_LCL_BOXES = 'data/_rhpp_lcl_boxes.pkl'
BPA_BASE_BOXES = 'data/_bpa_nrel_base_boxes.pkl'


def _real_transfer_boxes(rebuild=False):
    """Capacity-error distributions of the BPA/NREL and RHPP transfers (cached).

    Returns {'bpa': [(label, kind, errors, point)], 'rhpp': [...]}. ``kind`` is
    'within' (disjoint random pools, both directions), 'across' (bootstrap over
    80% of each pool's homes) or 'climate' (across climate classes); ``point`` is
    the error of the full pools, None for random pools.
    """
    if os.path.exists(REAL_BOXES) and not rebuild:
        return pickle.load(open(REAL_BOXES, 'rb'))

    def point(H, pil, tgt, mf):
        P, Q = _pool_sf(H, pil, mf), _pool_sf(H, tgt, mf)
        return (Q['s_h'] / P['m'] - Q['cap']) / Q['cap'] * 100

    H = _bpa_homes(); H.update(_nrel_homes())
    west = [h for h in H if h[:3] in ('TAC', 'SNO')]
    bpa = []
    for lab, hs in (('Tacoma halves', [h for h in H if h.startswith('TAC')]),
                    ('W. WA halves', west), ('Inland halves', list(BPA_INLAND))):
        bpa.append((lab, 'within', bpa_pool_transfer(hs, H=H).err.to_numpy(), None))
    for lab, pil, tgt, kind in (('Inland $\\rightarrow$ NREL', list(BPA_INLAND), list(NREL_WA), 'across'),
                                ('NREL $\\rightarrow$ inland', list(NREL_WA), list(BPA_INLAND), 'across'),
                                ('W. WA $\\rightarrow$ inland', west, list(BPA_INLAND), 'climate'),
                                ('Inland $\\rightarrow$ W. WA', list(BPA_INLAND), west, 'climate')):
        R = cross_study_transfer(H, pil, tgt, label=lab)
        bpa.append((lab, kind, R.err.to_numpy(), point(H, pil, tgt, 0.8)))

    R0 = _rhpp_concurrent(); homes = list(R0)
    rhpp = []
    for k in (10, 25, 50, len(homes) // 2):
        rhpp.append((f'{k} vs {k} homes', 'within',
                     bpa_pool_transfer(homes, H=R0, min_frac=0.7, size=k).err.to_numpy(), None))
    grp = {'ASHP': [h for h in homes if R0[h]['hp'] == 'ASHP'], 'GSHP': [h for h in homes if R0[h]['hp'] == 'GSHP'],
           'social': [h for h in homes if R0[h]['tenure'] == 'rsl'],
           'private': [h for h in homes if R0[h]['tenure'] == 'domestic']}
    for a, b in (('ASHP', 'GSHP'), ('GSHP', 'ASHP'), ('social', 'private'), ('private', 'social')):
        R = cross_study_transfer(R0, grp[a], grp[b], label=f'{a} -> {b}', min_frac=0.7)
        rhpp.append((f'{a} $\\rightarrow$ {b}', 'across', R.err.to_numpy(), point(R0, grp[a], grp[b], 0.7)))
    out = dict(bpa=bpa, rhpp=rhpp)
    pickle.dump(out, open(REAL_BOXES, 'wb'))
    return out


def _transfer_boxplot(ax, rows):
    """Horizontal capacity-error boxes: IQR box, 5th-95th whiskers, full-pool point.

    A row may carry a 5th element, the oracle errors, drawn as a hollow circle at
    their median.
    """
    col = {'within': hf.C_CH, 'across': hf.C_DE, 'climate': hf.C_NOHP, 'base': hf.C_BASE}
    y = np.arange(len(rows))[::-1]
    bp = ax.boxplot([r[2] for r in rows], positions=y, vert=False, widths=.6, showfliers=False,
                    whis=(5, 95), patch_artist=True, medianprops=dict(color='k', lw=1.2))
    for b, r in zip(bp['boxes'], rows):
        b.set(facecolor=col[r[1]], alpha=.45, edgecolor='0.4')
    for yi, r in zip(y, rows):
        if r[3] is not None:
            ax.plot(r[3], yi, 'D', ms=3.5, color='k', zorder=5)
        if len(r) > 4:
            ax.plot(np.median(r[4]), yi, 'o', ms=4.5, mfc='none', mec='k', mew=1.0, zorder=5)
    ax.axvline(0, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7)
    ax.set_xlabel('capacity error (%)')
    for r in rows:
        print(f'  {r[0]:28s} median {np.median(r[2]):+5.0f}  IQR {np.percentile(r[2], 25):+4.0f} to '
              f'{np.percentile(r[2], 75):+4.0f}  5-95 {np.percentile(r[2], 5):+4.0f} to {np.percentile(r[2], 95):+4.0f}'
              + ('' if r[3] is None else f'  full pools {r[3]:+.0f}'))


def fig_bpa_nrel():
    """fig_bpa_nrel: capacity error of the SF transfer within and across BPA and NREL."""
    B = list(_real_transfer_boxes()['bpa'])
    # semi-synthetic: heating systems plus temperature-matched NEEA base load (bpa_nrel_base_capacity)
    if not os.path.exists(BPA_BASE_BOXES):
        pickle.dump(bpa_nrel_base_capacity(), open(BPA_BASE_BOXES, 'wb'))
    L = pickle.load(open(BPA_BASE_BOXES, 'rb'))
    for case, lab in (('W. WA halves', 'W. WA halves'), ('Inland halves', 'Inland halves'),
                      ('Inland -> NREL', 'Inland $\\rightarrow$ NREL'), ('NREL -> inland', 'NREL $\\rightarrow$ inland')):
        for pop in ('gas', 'all'):
            R = L[pop, case]
            B.append((f'{lab}, {pop}', 'base', R.err.to_numpy(), None, R.oracle.to_numpy()))
    hf.use_style()
    fig, ax = plt.subplots(figsize=(hf.COL1, 4.2))
    ax.grid(False)
    _transfer_boxplot(ax, B)
    for yl in (len(B) - 3.5, len(B) - 5.5, 7.5):                # within | across studies | across climates | with base
        ax.axhline(yl, color='0.7', lw=0.6)
    fig.tight_layout(); hf.save(fig, 'fig_bpa_nrel')
    print('saved -> fig_bpa_nrel')


def fig_rhpp():
    """fig_rhpp: capacity error of the SF transfer across pool sizes and populations (RHPP)."""
    B = list(_real_transfer_boxes()['rhpp'])
    # semi-synthetic: RHPP heating plus LCL base load of gas-heated households (rhpp_lcl_capacity)
    if not os.path.exists(RHPP_LCL_BOXES):
        pickle.dump(rhpp_lcl_capacity(), open(RHPP_LCL_BOXES, 'wb'))
    L = pickle.load(open(RHPP_LCL_BOXES, 'rb'))
    for lab, key in (('+ base, no heaters', 'clean (0 portable heaters)'),
                     ('+ base, $\\geq$2 heaters', 'heater-rich (>= 2 portable heaters)')):
        B.append((lab, 'base', L[key].err.to_numpy(), None, L[key].oracle.to_numpy()))
    hf.use_style()
    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.grid(False)
    _transfer_boxplot(ax, B)
    for yl in (len(B) - 4.5, 1.5):                               # pool size | population | with base load
        ax.axhline(yl, color='0.7', lw=0.6)
    fig.tight_layout(); hf.save(fig, 'fig_rhpp')
    print('saved -> fig_rhpp')


def _bpa_report_bins(pdf='data/bpa_hphc/2026-hphchp-finalreport_web.pdf', first=135, last=152):
    """Heating-season bin tables of the BPA HPHC report (Appendix A, Tables 1B-1E).

    Returns {'whole': DataFrame, 'hvac': DataFrame}: sites x outdoor-temperature bins
    (deg F bin labels), average kW, parsed from ``pdftotext -layout``. Values are
    matched to the header bin nearest their position on the line, since sites lack
    some cold bins.
    """
    import re
    import subprocess
    txt = subprocess.run(['pdftotext', '-layout', '-f', str(first), '-l', str(last), pdf, '-'],
                         capture_output=True, text=True, check=True).stdout.split('\n')
    tables = {'1B': 'whole', '1C': 'whole', '1D': 'hvac', '1E': 'hvac'}
    out = {'whole': {}, 'hvac': {}}
    cur, head = None, None
    for i, line in enumerate(txt):
        m = re.search(r'Table (1[A-K])\.', line)
        if m:
            cur, head = tables.get(m.group(1)), None
            continue
        if cur is None:
            continue
        if re.match(r'\s*Site\s+-?\d', line):
            head = [(float(t.group()), (t.start() + t.end()) / 2) for t in re.finditer(r'-?\d+', line)]
            continue
        mm = re.match(r'\s*([A-Z]{3})\s+(-?\d)', line)
        if head is None or not mm:
            continue
        site = mm.group(1)
        j = i + 1
        while j < len(txt) and not txt[j].strip():
            j += 1
        suf = re.findall(r'\b(\d{2})\s*$', txt[j]) if j < len(txt) else []
        if not suf:
            continue
        vals = {}
        for t in re.finditer(r'-?\d+\.\d+', line):
            c = (t.start() + t.end()) / 2
            b = min(head, key=lambda h: abs(h[1] - c))[0]
            vals[b] = float(t.group())
        out[cur][f'{site} {suf[0]}'] = vals
    return {k: pd.DataFrame(v).T.sort_index(axis=1) for k, v in out.items()}


def bpa_net_load_bias(groups=None, t_max_f=45.0):
    """Net-load bias of the BPA homes from the report's whole-house and HVAC bin tables.

    For each site (and pools of sites), OLS slopes of whole-house and HVAC-only power
    against the bin temperature (bin label + 2.5 F, in C) over bins up to ``t_max_f``;
    non-HVAC = whole - HVAC. The ratio s_whole / s_hvac is the factor by which the
    net-load numerator overstates the HVAC (ETL) response, i.e. the oracle bias.
    """
    B = _bpa_report_bins()
    W, V = B['whole'], B['hvac']
    sites = sorted(set(W.index) & set(V.index))
    rows = []
    for s in sites:
        w, v = W.loc[s].dropna(), V.loc[s].dropna()
        bins = [b for b in w.index if b in v.index and b <= t_max_f]
        if len(bins) < 5:
            continue
        x = -((np.array(bins) + 2.5 - 32) * 5 / 9)                       # colder -> larger
        sw, sv = np.polyfit(x, w[bins].to_numpy(), 1)[0], np.polyfit(x, v[bins].to_numpy(), 1)[0]
        rows.append(dict(site=s, group=s[:3], bins=len(bins), s_whole=sw, s_hvac=sv, s_nonhvac=sw - sv,
                         bias=sw / sv if sv > 0 else np.nan))
    R = pd.DataFrame(rows).set_index('site')
    pd.set_option('display.width', 200)
    print(R.round(3).to_string())
    print(f"\nper-home non-HVAC heating slope: median {R.s_nonhvac.median():.4f} kW/C "
          f"(IQR {R.s_nonhvac.quantile(.25):.4f}-{R.s_nonhvac.quantile(.75):.4f}); "
          f"Kloten HP-free 0.0055, NEEA non-ETL 0.03-0.04")
    for name, g in (groups or {}).items():
        sub = R.loc[[s for s in g if s in R.index]]
        print(f"pool {name}: {len(sub)} homes, sum s_whole / sum s_hvac = {sub.s_whole.sum() / sub.s_hvac.sum():.2f} "
              f"(non-HVAC share of net-load slope {sub.s_nonhvac.sum() / sub.s_whole.sum() * 100:.0f}%)")
    return R


def neea_transfer(pilot='WA', target='OR', A=None, write=True):
    """Two-regime transfer: the pilot's SF sensitivities m_h, m_c on the target's
    net-load fit. Every ductless HP heats and cools, so both regimes estimate
    the same installed capacity."""
    from hp_common import fit_bathtub_stick
    A = _neea_aggregates() if A is None else A
    P, X = A[pilot], A[target]
    # SF arms anchored at each aggregate's own net-load thresholds
    _, _, pth, _, ptc, _ = fit_bathtub_stick(P['T'], P['net'])
    sfP = np.clip(P['hp'] / P['cap'], 0, 1)
    pmh, pmc = U._sf_arm(P['T'], sfP, pth, 'h')[1], U._sf_arm(P['T'], sfP, ptc, 'c')[1]
    sfX = np.clip(X['hp'] / X['cap'], 0, 1)
    nb, sh, th, sc, tc, r2 = fit_bathtub_stick(X['T'], X['net'])
    omh, omc = U._sf_arm(X['T'], sfX, th, 'h')[1], U._sf_arm(X['T'], sfX, tc, 'c')[1]
    T, cap = X['T'], X['cap']
    print(f"{pilot} pilot: {P['n']} homes, {P['days']} days, cap {P['cap']:.1f} kW; m_h {pmh:.4f} (T {pth:.1f}) "
          f"m_c {pmc:.4f} (T {ptc:.1f})")
    print(f"{target} target: {X['n']} homes, {X['days']} days, cap {cap:.1f} kW; own m_h {omh:.4f} m_c {omc:.4f}; "
          f"net-load s_h {sh:.3f} T_h {th:.1f} s_c {sc:.3f} T_c {tc:.1f} R2 {r2:.2f}")
    heat, cool = T < th, T > tc
    rows = []
    for reg, s, m, om, mask, sfe in (
            ('heating', sh, pmh, omh, heat, np.clip(pmh * np.maximum(0, th - T), 0, 1)),
            ('cooling', sc, pmc, omc, cool, np.clip(pmc * np.maximum(0, T - tc), 0, 1))):
        ce = s / m
        dist = np.maximum(0, th - T) if reg == 'heating' else np.maximum(0, T - tc)
        e_est = (s * dist * 24)[mask].sum(); e_act = (X['hp'] * 24)[mask].sum()
        fe = (sfe * (1 - sfe))[mask].sum() * ce; fa = (sfX * (1 - sfX))[mask].sum() * cap
        rows.append(dict(regime=reg, m_pilot=m, m_own=om, cap=cap, cap_e=ce, err=(ce - cap) / cap * 100,
                         oracle=(s / om - cap) / cap * 100, energy=(e_est - e_act) / e_act * 100, flex=fe / fa,
                         days=int(mask.sum())))
    R = pd.DataFrame(rows)
    print(R.round(3).to_string(index=False))
    if write:
        body = "\n".join(f"{r.regime} & {r.m_pilot:.3f} & {r.m_own:.3f} & {r.cap_e:.0f} & {r.err:+.0f} & "
                         f"{r.oracle:+.0f} & {r.energy:+.0f} & {r.flex:.2f} \\\\" for r in R.itertuples())
        tex = r"""\begin{table}[t]
\centering
\caption{Two-regime transfer from a Washington pilot to an Oregon aggregate of """ + str(X['n']) + \
            r""" homes with ductless HPs ($P^{\max} = """ + f"{cap:.0f}" + r"""$~kW, the same devices in both regimes). Errors are signed; energy and flex are scored on the days of each regime}
\label{tab:neea}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lccccccc}
\toprule
regime & $m_k$ (WA) & $m_k$ (OR) & $\hat{P}_k^{\max}$ (kW) & cap. (\%) & oracle (\%) & energy (\%) & flex \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}"""
        open('paper/tables/tab_neea.tex', 'w').write(tex)
        print('wrote tab_neea.tex')
    return R


# ===========================================================================
# Section 6 -- cross-dataset characterization
# ===========================================================================
# Hennepin-only: the ASHP compressor's own SF regression drops days colder than
# this from the fit -- below it the compressor is visibly derating and the
# HP-backup resistance element engages (binned backup share is <0.1% in every
# 2 C bin down to -10 C, then 6.5%/13%/35%/saturated as it gets colder), so
# those days are a different (backup-contaminated) regime, not SF noise.
SF_TMIN_H = {'ResStock ASHP -- Hennepin MN (cold)': -10.0}


def build_cross_table(repull=False):
    """Refit the cross-dataset table from scratchpad/cross_frames.pkl.

    ``repull=True`` re-pulls the three ResStock ASHP rows from the NREL S3
    bucket. Hennepin's ``heat`` is the ASHP compressor's own draw only
    (``out.electricity.heating``) -- the HP-backup resistance element
    (``heating_hp_bkup``) is genuinely backup here (every home in this upgrade
    has the ASHP as primary), not heating, so it is excluded from both the SF
    numerator and ``cap_h``. King WA and Maricopa AZ keep compressor+backup
    folded together, unchanged. ``repull=False`` (default) just refits from the
    cached frames. Writes scratchpad/cross_table.csv.
    """
    cache = 'scratchpad/cross_frames.pkl'
    INPUTS = U.pickle_load(cache)
    if repull:
        import s3fs
        import pyarrow.parquet as pq
        from concurrent.futures import ThreadPoolExecutor
        fs = s3fs.S3FileSystem(anon=True)
        R2 = ("oedi-data-lake/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/"
              "2024/resstock_amy2018_release_2")
        HTTP = "https://oedi-data-lake.s3.amazonaws.com/" + R2.split('/', 1)[1]
        HC = 'out.electricity.heating.energy_consumption'
        BK = 'out.electricity.heating_hp_bkup.energy_consumption'
        CC = 'out.electricity.cooling.energy_consumption'
        TC = 'out.electricity.total.energy_consumption'
        meta = pd.read_parquet('scratchpad/resstock_meta_sfd.parquet'); UP = 3

        def read_one(bid, st):
            try:
                t = pq.read_table(fs.open(f"{R2}/timeseries_individual_buildings/by_state/upgrade={UP}/state={st}/{bid}-{UP}.parquet"),
                                  columns=['timestamp', HC, BK, CC, TC]).to_pandas(ignore_metadata=True)
            except Exception:
                return None
            t['timestamp'] = pd.to_datetime(t['timestamp']); return t.set_index('timestamp')

        def wx(gj, st):
            w = pd.read_csv(f"{HTTP}/weather/state={st}/{gj}_2018.csv", parse_dates=['date_time'])
            return w.set_index('date_time')['Dry Bulb Temperature [°C]'].resample('D').mean()

        for gj, st, lab in [('G2700530', 'MN', 'ResStock ASHP -- Hennepin MN (cold)'),
                            ('G5300330', 'WA', 'ResStock ASHP -- King WA (mild)'),
                            ('G0400130', 'AZ', 'ResStock ASHP -- Maricopa AZ (hot)')]:
            bids = list(np.random.default_rng(0).choice(meta[meta['in.county'] == gj]['bldg_id'].tolist(), 150, replace=False))
            hennepin = lab == 'ResStock ASHP -- Hennepin MN (cold)'
            heat = cool = tot = None; hpk = cpk = 0.0
            with ThreadPoolExecutor(max_workers=16) as ex:
                for r in ex.map(lambda b: read_one(b, st), bids):
                    if r is None:
                        continue
                    h = (r[HC] if hennepin else (r[HC] + r[BK])) * 4
                    c, s2 = r[CC] * 4, r[TC] * 4
                    heat = h if heat is None else heat.add(h, fill_value=0)
                    cool = c if cool is None else cool.add(c, fill_value=0)
                    tot = s2 if tot is None else tot.add(s2, fill_value=0)
                    hpk += float(h.max()); cpk += float(c.max())
            Td = wx(gj, st)
            dd = pd.DataFrame({'T': Td, 'net': tot.resample('D').mean(),
                               'heat': heat.resample('D').mean(), 'cool': cool.resample('D').mean()}).dropna()
            INPUTS[lab] = dict(n=150, T=dd['T'].to_numpy(), net=dd['net'].to_numpy(),
                               heat=dd['heat'].to_numpy(), cool=dd['cool'].to_numpy(), cap_h=hpk, cap_c=cpk)
            print(lab, 'done: cap_h', round(hpk), 'cap_c', round(cpk), flush=True)
        pickle.dump(INPUTS, open(cache, 'wb'))

    rows = [U.fit_row(lab, v['n'], v['T'], v['net'], v['heat'], v['cool'], v['cap_h'], v['cap_c'],
                       sf_tmin_h=SF_TMIN_H.get(lab)) for lab, v in INPUTS.items()]
    pd.DataFrame(rows).to_csv('scratchpad/cross_table.csv', index=False)
    print('wrote scratchpad/cross_table.csv')


def neea_fit():
    """Table I NEEA WA/OR rows -> scratchpad/neea_rows.csv, neea_frames.pkl.

    Uses the same aggregates as Section V (``_neea_aggregates``): homes with >= 330
    complete days of 2023, capacity = 99.9th percentile of each ductless HP's
    15-min draw. HP energy is split between the regimes by the day's mean
    temperature (heating below 15 C, cooling above 20 C) to decide which arms exist.
    """
    A = _neea_aggregates()
    FR = {}; rows = []
    for st in ('WA', 'OR'):
        X = A[st]; T, hpv, netv = X['T'], X['hp'], X['net']
        heat = np.where(T < 15, hpv, 0.0); cool = np.where(T > 20, hpv, 0.0)
        lab = f'NEEA {st} (real HP)'
        rows.append(U.fit_row(lab, X['n'], T, netv, heat, cool, X['cap'], X['cap']))
        FR[lab] = dict(n=X['n'], T=T, net=netv, heat=hpv, cool=hpv, cap_h=X['cap'], cap_c=X['cap'])
        print(f"{st}: {X['n']} homes, {X['days']} days, cap {X['cap']:.1f} kW")
    pd.DataFrame(rows).to_csv('scratchpad/neea_rows.csv', index=False)
    pickle.dump(FR, open('scratchpad/neea_frames.pkl', 'wb'))
    print('wrote scratchpad/neea_rows.csv + neea_frames.pkl')


def tab_cross():
    """tab_cross: cross-dataset fit-parameter table (Table I) from the cached CSVs.

    Reproduces the hand-edited paper table: London is kept as a commented-out
    row, Hennepin carries footnote (a) and the NEEA rows footnote (b). The NEEA
    rows come from ``neea_fit`` (99.9th-percentile capacity, >= 330 days).
    """
    parts = [pd.read_csv('scratchpad/cross_table.csv'), pd.read_csv('scratchpad/neea_rows.csv')]
    if False and os.path.exists('scratchpad/extra_rows.csv'):   # BPA, NREL, RHPP rows (extra_cross_rows) -- not shown
        parts.append(pd.read_csv('scratchpad/extra_rows.csv'))
    df = pd.concat(parts, ignore_index=True).set_index('label')
    # Row order is fixed here (Ottawa dropped from the table); the AC-only Carleton
    # Ottawa aggregate stays in the cache and the montage but is excluded from ROW.
    ROW = {
        'German WPuQ (real HP)':               r'Hamelin, DE~\cite{Sch22}',
        'Swiss substation (real HP)':          r'Kloten, CH~\cite{Bru25,Kai26b}',
        'LCL London ASHP (real HP)':           r'London, UK~\cite{lcl_heatpump}',
        'COFACTOR Norway (real HP)':           r'Oslo, NO~\cite{cofactor}',
        'ResStock ASHP -- Hennepin MN (cold)': r'Hennepin, MN, US~\cite{resstock}\tnote{a}',
        'NEEA WA (real HP)':                   r'WA, US~\cite{neea_eulr}\tnote{b}',
        'NEEA OR (real HP)':                   r'OR, US~\cite{neea_eulr}\tnote{b}',
        'ResStock ASHP -- King WA (mild)':     r'King, WA, US~\cite{resstock}',
        'Austin Pecan St (real)':              r'Austin, TX, US~\cite{pecanstreet}',
        'ResStock ASHP -- Maricopa AZ (hot)':  r'Maricopa, AZ, US~\cite{resstock}',
    }
    COMMENTED = {'LCL London ASHP (real HP)'}     # kept in the source, hidden in the paper
    TECH = {   # ETL technologies behind the meter for each aggregate
        'German WPuQ (real HP)':               'WSHP',
        'Swiss substation (real HP)':          'ASHP, GSHP',
        'RHPP GB':                             'ASHP, GSHP, ER',
        'LCL London ASHP (real HP)':           'ASHP',
        'COFACTOR Norway (real HP)':           'GSHP, ER',
        'ResStock ASHP -- Hennepin MN (cold)': 'ASHP',
        'NEEA WA (real HP)':                   'DHP, ER',
        'NEEA OR (real HP)':                   'DHP, ER',
        'BPA W. Washington':                   'ASHP, DHP, ER',
        'BPA inland':                          'ASHP, DHP, ER',
        'NREL Washington':                     'ASHP, ER',
        'ResStock ASHP -- King WA (mild)':     'ASHP, ER',
        'Austin Pecan St (real)':              'AC, ER',
        'ResStock ASHP -- Maricopa AZ (hot)':  'ASHP, ER',
    }
    KOPPEN = {   # Koppen-Geiger climate class of each location
        'German WPuQ (real HP)':               'Cfb',
        'Swiss substation (real HP)':          'Cfb',
        'RHPP GB':                             'Cfb',
        'LCL London ASHP (real HP)':           'Cfb',
        'COFACTOR Norway (real HP)':           'Dfb',
        'ResStock ASHP -- Hennepin MN (cold)': 'Dfa',
        'NEEA WA (real HP)':                   'Csb',
        'NEEA OR (real HP)':                   'Csb',
        'BPA W. Washington':                   'Csb',
        'BPA inland':                          'Dsb, BSk',
        'NREL Washington':                     'Dsb, BSk',
        'ResStock ASHP -- King WA (mild)':     'Csb',
        'Austin Pecan St (real)':              'Cfa',
        'ResStock ASHP -- Maricopa AZ (hot)':  'BWh',
    }
    order = [k for k in ROW if k in df.index]
    COLS = [(r'$P_{\mathrm{base}}$', 'P_base', '.0f'), ('$s_h$', 's_h', '.1f'), ('$T_h$', 'T_h', '.1f'),
            ('$R^2_h$', 'R2_net_h', '.2f'), ('$s_c$', 's_c', '.1f'), ('$T_c$', 'T_c', '.1f'),
            ('$R^2_c$', 'R2_net_c', '.2f'), ('$b_h$', 'b_h', '.3f'), ('$m_h$', 'm_h', '.3f'),
            (r'SF$^{\max}_h$', 'SF_cold', '.2f'), ('$R^2_h$', 'R2_SFh', '.2f'), ('$b_c$', 'b_c', '.3f'),
            ('$m_c$', 'm_c', '.3f'), (r'SF$^{\max}_c$', 'SF_hot', '.2f'), ('$R^2_c$', 'R2_SFc', '.2f')]

    def cell(v, fmt):
        return '--' if (v is None or (isinstance(v, float) and not np.isfinite(v))) else format(v, fmt)

    # no whole-home load: only the thresholds of the heating-system load are shown
    NO_NET = {'RHPP GB', 'BPA W. Washington', 'BPA inland', 'NREL Washington'}
    NET_ONLY = {'P_base', 's_h', 'R2_net_h', 's_c', 'R2_net_c'}

    def row(lab):
        vals = [('--' if (lab in NO_NET and c in NET_ONLY) else cell(df.loc[lab, c], f)) for _, c, f in COLS]
        s = (ROW[lab] + ' & ' + TECH[lab] + ' & ' + cell(df.loc[lab, 'n'], '.0f') + ' & ' + KOPPEN[lab]
             + ' & ' + ' & '.join(vals) + r' \\')
        return ('%' + s) if lab in COMMENTED else s
    body = '\n'.join(row(lab) for lab in order)
    head = 'dataset & TCL tech & $n$ & Climate & ' + ' & '.join(h for h, _, _ in COLS) + r' \\'
    tex = (
        r"\begin{table*}[t]" "\n" r"\centering" "\n"
        r"\begin{threeparttable}" "\n"
        r"\caption{Net-load and SF fits, one aggregate per dataset}" "\n"
        r"\label{tab:cross}" "\n" r"\scriptsize" "\n" r"\setlength{\tabcolsep}{3.5pt}" "\n"
        r"\begin{tabular}{ll" + "c" * (len(COLS) + 2) + "}\n" r"\toprule" "\n"
        r" & & & & \multicolumn{7}{c}{Net-load fit $\hat{P}_{\mathrm{net}}(T)$} & \multicolumn{8}{c}{SF fit $\hat{\mathrm{SF}}(T)$}\\" "\n"
        r"\cmidrule(lr){5-11}\cmidrule(lr){12-19}" "\n"
        + head + "\n" r"\midrule" "\n" + body + "\n" r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
        r"\begin{tablenotes}[flushleft]\footnotesize" "\n"
        r"\item[] $n$: aggregated consumers. Climate: K{\"o}ppen--Geiger class~\cite{beck2018koppen}: Cfb, temperate oceanic; Dfa, Dfb, humid continental; Csb, warm-summer Mediterranean; Cfa, humid subtropical; BWh, hot desert. $R^2_h$, $R^2_c$: fit scores in R1 and R3. ASHP, GSHP, WSHP: air-, ground-, water-source HP; DHP: ductless (mini-split) HP; AC: air conditioning; ER: electric resistance heating." "\n"
        r"%\item[a] The LCL London aggregate is submetered heat-pump load only (nine homes, no other household load), restricted to 2014, the single year all nine are metered together. Its net-load fit therefore coincides with the HP load, $P_{\mathrm{base}}$ is the winter standby/hot-water floor, and the installed capacity is the sum of the nine per-home 2014 peaks. The 2014 record ends in March, so the window is winter-only and never reaches $T_h$, which weakens the fit." "\n"
        r"\item[a] Hennepin's SF uses the ASHP compressor's own draw only, excluding its electric-resistance HP-backup element" "\n"
        r"\item[b] The SF uses the submetered ductless HPs only. Most of these homes also have electric baseboard, furnace or other zonal heating circuits (17 of 22 in WA, 16 of 21 in OR), which the net load includes." "\n"
        "\n"
        r"\end{tablenotes}" "\n"
        r"\end{threeparttable}" "\n" r"\end{table*}")
    open('paper/tables/tab_cross.tex', 'w', encoding='utf-8', newline='\n').write(tex)
    print('wrote tab_cross.tex')


def fig_cross_montage(knee_thresh=0.02):
    """fig_cross_montage: per-dataset net-load bathtub (left) and SF (right).

    Where a single linear arm is convex, a piecewise arm with one extra threshold
    (a second knee) is overlaid dashed on that arm, but only if it raises the
    arm's R^2 by at least ``knee_thresh`` (default 0.02). Mostly this fires on the
    cold-climate ResStock heating arm (Hennepin), where electric backup + COP
    fall-off make the load convex."""
    from scipy.optimize import curve_fit

    def knee_fit(x, y, thr, side):
        """Fit a 1-knee and a 2-knee arm on the below/above-threshold subset;
        return the extra-knee predictor and both R^2 if the fit succeeds."""
        m = (x < thr) if side == 'h' else (x > thr)
        if not np.isfinite(thr) or m.sum() < 25:
            return None
        xs_, ys_ = x[m], y[m]
        ss = float(np.sum((ys_ - ys_.mean()) ** 2))
        if ss <= 0:
            return None
        hinge = (thr - xs_) if side == 'h' else (xs_ - thr)
        m1, b1 = np.polyfit(hinge, ys_, 1)
        r1 = 1 - np.sum((ys_ - (b1 + m1 * hinge)) ** 2) / ss

        def f(T, b, s1, s2, tk):
            h1 = np.maximum(0, thr - T) if side == 'h' else np.maximum(0, T - thr)
            h2 = np.maximum(0, tk - T) if side == 'h' else np.maximum(0, T - tk)
            return b + s1 * h1 + s2 * h2
        tk_lo, tk_hi = (xs_.min() + 1, thr - 1) if side == 'h' else (thr + 1, xs_.max() - 1)
        if tk_hi <= tk_lo:
            return None
        try:
            p, _ = curve_fit(f, xs_, ys_, p0=[np.median(ys_), max(m1, .1), max(m1, .1), (tk_lo + tk_hi) / 2],
                             bounds=([-np.inf, 0, 0, tk_lo], [np.inf, np.inf, np.inf, tk_hi]), maxfev=20000)
        except Exception:
            return None
        r2 = 1 - np.sum((ys_ - f(xs_, *p)) ** 2) / ss
        return dict(r1=r1, r2=r2, f=(lambda T: f(T, *p)))

    hf.use_style()
    FR = U.pickle_load('scratchpad/cross_frames.pkl')
    FR.update(U.pickle_load('scratchpad/neea_frames.pkl'))
    ORDER = [('German WPuQ (real HP)', 'Hamelin, DE'), ('Swiss substation (real HP)', 'Kloten, CH'),
             ('COFACTOR Norway (real HP)', 'Oslo, NO'),
             ('Austin Pecan St (real)', 'Austin, TX'), ('Carleton Ottawa (real AC)', 'Ottawa, CA'),
             ('NEEA WA (real HP)', 'WA, US'),
             ('NEEA OR (real HP)', 'OR, US'), ('ResStock ASHP -- Hennepin MN (cold)', 'Hennepin, MN'),
             ('ResStock ASHP -- King WA (mild)', 'King, WA'), ('ResStock ASHP -- Maricopa AZ (hot)', 'Maricopa, AZ')]
    ORDER = [(k, t) for k, t in ORDER if k in FR]
    nrow = len(ORDER)
    # common temperature axis across every panel, so the arms line up
    allT = np.concatenate([np.asarray(FR[k]['T'], float) for k, _ in ORDER])
    Tlo, Thi = float(np.floor(np.nanmin(allT))) - 1, float(np.ceil(np.nanmax(allT))) + 1
    fig, axes = plt.subplots(nrow, 2, figsize=(5.4, 1.55 * nrow), sharex=True)
    for i, (k, title) in enumerate(ORDER):
        v = FR[k]
        T, net = np.asarray(v['T']), np.asarray(v['net'])
        heat, cool = np.asarray(v['heat']), np.asarray(v['cool'])
        tmin_h = SF_TMIN_H.get(k)
        r = U.fit_row(k, v['n'], T, net, heat, cool, v['cap_h'], v['cap_c'], sf_tmin_h=tmin_h)
        th, tc, base, sh, sc = r['T_h'], r['T_c'], r['P_base'], r['s_h'], r['s_c']
        axb, axs = axes[i, 0], axes[i, 1]
        for ax in (axb, axs):
            ax.grid(False); ax.tick_params(labelsize=6); ax.set_xlim(Tlo, Thi)
        xs = np.linspace(T.min(), T.max(), 200)
        axb.scatter(T, net, s=3, color='0.75', alpha=.4, edgecolor='none')
        lo = th if np.isfinite(th) else T.min(); hi = tc if np.isfinite(tc) else T.max()
        axb.plot([lo, hi], [base, base], color='0.3', lw=1.5, zorder=4)
        net_r2_note = ''
        if np.isfinite(th):
            xa = xs[xs <= th]; axb.plot(xa, base + sh * (th - xa), color=hf.C_HP, lw=1.6, zorder=4)
        if np.isfinite(tc):
            xd = xs[xs >= tc]; axb.plot(xd, base + sc * (xd - tc), color=hf.C_CH, lw=1.6, zorder=4)
        # --- net-load extra-knee overlay where an arm is convex ---
        for side, thr, col in [('h', th, hf.C_HP), ('c', tc, hf.C_CH)]:
            kk = knee_fit(T, net, thr, side)
            if kk and kk['r2'] - kk['r1'] >= knee_thresh:
                xr = xs[xs <= thr] if side == 'h' else xs[xs >= thr]
                axb.plot(xr, kk['f'](xr), color=col, lw=1.1, ls=(0, (3, 2)), zorder=6)
                net_r2_note = f"$\\to${kk['r2']:.2f}"
        axb.set_ylabel(title, fontsize=7.5)
        axb.text(0.04, 0.9, f"$R^2$ {r['R2']:.2f}{net_r2_note}", transform=axb.transAxes, fontsize=6, color='0.4', va='top')
        if np.isfinite(th) and v['cap_h']:
            mm = T < th
            fit_mm = mm & (T >= tmin_h) if tmin_h is not None else mm
            if tmin_h is not None:
                excl = mm & (T < tmin_h)
                axs.scatter(T[excl], np.clip(heat[excl] / v['cap_h'], 0, 1), s=3, color='0.75', alpha=.4, edgecolor='none')
                axs.axvline(tmin_h, color='0.4', lw=.7, ls=(0, (3, 2)), zorder=3)
            axs.scatter(T[fit_mm], np.clip(heat[fit_mm] / v['cap_h'], 0, 1), s=3, color=hf.C_HP, alpha=.3, edgecolor='none')
            lo_h = tmin_h if tmin_h is not None else T.min()
            xa = xs[(xs <= th) & (xs >= lo_h)]; axs.plot(xa, np.clip(r['b_h'] + r['m_h'] * (th - xa), 0, 1), color=hf.C_HP, lw=1.6, zorder=4)
            if tmin_h is None:      # knee overlay only where sub-threshold days weren't already excluded
                ks = knee_fit(T, np.clip(heat / v['cap_h'], 0, 1), th, 'h')
                if ks and ks['r2'] - ks['r1'] >= knee_thresh:
                    xa = xs[xs <= th]; axs.plot(xa, np.clip(ks['f'](xa), 0, 1), color=hf.C_HP, lw=1.1, ls=(0, (3, 2)), zorder=6)
                    axs.text(0.04, 0.9, f"$R^2$ {r['R2_SFh']:.2f}$\\to${ks['r2']:.2f}", transform=axs.transAxes, fontsize=6, color='0.4', va='top')
        if np.isfinite(tc) and v['cap_c']:
            mm = T > tc
            axs.scatter(T[mm], np.clip(cool[mm] / v['cap_c'], 0, 1), s=3, color=hf.C_CH, alpha=.3, edgecolor='none')
            xd = xs[xs >= tc]; axs.plot(xd, np.clip(r['b_c'] + r['m_c'] * (xd - tc), 0, 1), color=hf.C_CH, lw=1.6, zorder=4)
            ks = knee_fit(T, np.clip(cool / v['cap_c'], 0, 1), tc, 'c')
            if ks and ks['r2'] - ks['r1'] >= knee_thresh:
                xd = xs[xs >= tc]; axs.plot(xd, np.clip(ks['f'](xd), 0, 1), color=hf.C_CH, lw=1.1, ls=(0, (3, 2)), zorder=6)
        axs.set_ylim(0, 1)
        if i == 0:
            axb.set_title('net load (kW)', fontsize=7.5); axs.set_title('simultaneity factor', fontsize=7.5)
        if i < nrow - 1:
            axb.set_xticklabels([]); axs.set_xticklabels([])
    axes[-1, 0].set_xlabel('daily mean temperature ($^\\circ$C)', fontsize=7)
    axes[-1, 1].set_xlabel('daily mean temperature ($^\\circ$C)', fontsize=7)
    fig.tight_layout(h_pad=0.4, rect=[0, 0.012, 1, 1])
    fig.text(0.5, 0.004, 'dashed: fit with one extra threshold (knee), shown where it raises the '
             'arm $R^2$ by $\\geq$ %.2f' % knee_thresh, ha='center', fontsize=6, color='0.4')
    hf.save(fig, 'fig_cross_montage')
    print('saved -> fig_cross_montage')
