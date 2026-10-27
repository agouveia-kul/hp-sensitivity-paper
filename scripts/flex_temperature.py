# -*- coding: utf-8 -*-
"""Flexibility against outdoor temperature (exploration, not in the paper yet).

One function per step of the flexibility-temperature experiments, called from
``flex_temperature.ipynb``. Intermediate results are pickled under ``FLEX_WORK``
(gitignored ``results/flex_temperature``); figures go to ``FLEX_FIG`` as PDF and
PNG. The paper's own caches in ``data/`` and artifacts in ``paper/`` are never
written.

Step 0 rebuilds the published 20-split Kloten design and its hourly-reference
flexibility from the cached pools with the generators of ``outputs``, and checks
the draft's Section IV-F numbers against tolerances.
"""
import os
import pickle

import numpy as np
import pandas as pd

import outputs as O
import utils as U
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

FLEX_WORK = os.path.join('results', 'flex_temperature')     # pickles (gitignored)
FLEX_FIG = os.path.join('figures', 'flex_temperature')      # PDF + PNG of every figure

DT_FIG11 = 4                                                # window of the draft's Fig. 11 (h)


def _pkl(name):
    os.makedirs(FLEX_WORK, exist_ok=True)
    return os.path.join(FLEX_WORK, name + '.pkl')


def _cached(name, build, rebuild=False):
    """Load ``name`` from FLEX_WORK, or build and save it."""
    path = _pkl(name)
    if os.path.exists(path) and not rebuild:
        with open(path, 'rb') as fh:
            return pickle.load(fh)
    out = build()
    with open(path, 'wb') as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def save_fig(fig, name):
    os.makedirs(FLEX_FIG, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FLEX_FIG, f'{name}.{ext}'), dpi=300)
    return os.path.join(FLEX_FIG, name)


# ===========================================================================
# Step 0 -- reproduce the current flexibility results
# ===========================================================================
TARGETS = {  # draft value, tolerance
    'flex_ratio_median': (1.04, .02), 'flex_ratio_q25': (0.97, .02), 'flex_ratio_q75': (1.17, .02),
    'flex_wape_pct': (10.0, 1.0),
    'energy_factor_median': (0.97, .02), 'unused_cap_factor_median': (1.07, .02),
    'corr_flex_energy': (0.96, .02),
    'dailymean_over_hourly_actual_pct': (3.0, 1.0), 'ratio_vs_dailymean_actual': (1.01, .02),
    'deadband_floor_share_pct': (9.0, 1.0),
    'coldest_wape_pct': (21.0, 1.0), 'coldest_r2': (0.73, .02),
    'fig11_n_hp': (25, 0), 'fig11_pmax_kw': (144, 0.5),
    'fig11_floor_kwh_day': (19.0, 1.0), 'fig11_floor_share_pct': (14.0, 1.0),
    'fig11_actual_mwh': (5.2, .2), 'fig11_est_mwh': (4.7, .2),
    'pilot0_b': (0.021, .0005), 'pilot0_m': (0.019, .0005), 'pilot0_T_h': (16.6, .05), 'pilot0_r2': (0.94, .005),
}


def rebuild_design(rebuild=False):
    """The published 1260-aggregate design and its hourly-reference actual
    flexibility, rebuilt from the pools into FLEX_WORK.

    Runs ``outputs._kloten_design`` and ``outputs._kloten_flex_hourly`` (seed 0,
    20 splits, 3 reps) with both cache paths redirected, so the paper's caches
    in ``data/`` are read only for comparison.
    """
    paths = _pkl('step0_kloten_design'), _pkl('step0_kloten_flex_hourly')
    old = O.KLOTEN_DESIGN, O.KLOTEN_FLEX_H
    O.KLOTEN_DESIGN, O.KLOTEN_FLEX_H = paths
    try:
        Dz = O._kloten_design(rebuild=rebuild or not os.path.exists(paths[0]))
        Fh = O._kloten_flex_hourly(rebuild=rebuild or not os.path.exists(paths[1]))
    finally:
        O.KLOTEN_DESIGN, O.KLOTEN_FLEX_H = old
    return Dz, Fh


def _same_as_paper(G, Fh):
    """True when the rebuilt frames match the paper's caches in ``data/``."""
    with open(O.KLOTEN_DESIGN, 'rb') as fh:
        Gp = pickle.load(fh)['rows']
    Fp = pd.read_pickle(O.KLOTEN_FLEX_H)
    cols = ['cap', 's_h', 'T_h', 'cap_est', 'flex_b_est', 'flex_b_act', 'e_b_est', 'e_b_act', 'cold_est']
    return (len(G) == len(Gp) and np.allclose(G[cols].to_numpy(), Gp[cols].to_numpy())
            and len(Fh) == len(Fp) and np.allclose(Fh.to_numpy(), Fp.to_numpy()))


def fig11_split(Dz, split=0):
    """The target half of one split as in the draft's Fig. 11: daily actual
    (hourly reference) and estimated flexibility per hour of window."""
    K, T = Dz['K'], Dz['T']
    p = Dz['pilots'][split]; B = p['B']
    hp = K['hp'][B].sum(0); net = hp + K['own'][B].sum(0); cap = float(K['cap'][B].sum())
    _, sh, th, _ = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
    sf_e = O.sf_target(T, th, p['m']); cap_e = sh / p['m']
    fa = O._hourly_flex(O._kloten_hourly()['hp'][B].sum(0).reshape(len(T), 24), cap)
    fe = sf_e * (1 - sf_e) * cap_e
    return dict(B=B, cap=cap, cap_e=cap_e, s_h=sh, T_h=th, m=p['m'], fa=fa, fe=fe, sf_e=sf_e, T=T)


def pilot_fit_r2(Dz, split=0):
    """b_h, m_h, T_h and R^2_h of one split's pilot SF fit (Eq. sffit)."""
    K, T = Dz['K'], Dz['T']
    A = Dz['pilots'][split]['A']
    hp = K['hp'][A].sum(0)
    _, _, th, _ = fit_hockey_stick(T, hp + K['own'][A].sum(0), T_BALANCE_BOUNDS)
    b, m, _, r2 = U._sf_arm(T, np.clip(hp / K['cap'][A].sum(), 0, 1), th, 'h')
    return dict(b=float(b), m=float(m), T_h=float(th), r2=float(r2))


def reproduce_flex(rebuild=False):
    """Step 0: every Section IV-F number of the prompt's section 1, against its tolerance.

    Returns (checks, extras): a frame with draft value, reproduced value, tolerance
    and pass flag, and a dict of the underlying objects.
    """
    Dz, Fh = rebuild_design(rebuild)
    G = Dz['rows'].copy()
    same = _same_as_paper(G, Fh)

    act = Fh.act_h.to_numpy()
    ratio = G.flex_b_est / act
    er = G.e_b_est / G.e_b_act
    s = fig11_split(Dz, 0)
    warm = s['T'] >= s['T_h']
    floor = float(np.median(s['fa'][warm]) * DT_FIG11)
    pf = pilot_fit_r2(Dz, 0)

    got = {'flex_ratio_median': ratio.median(), 'flex_ratio_q25': ratio.quantile(.25),
           'flex_ratio_q75': ratio.quantile(.75), 'flex_wape_pct': O._wape(G.flex_b_est, act),
           'energy_factor_median': er.median(), 'unused_cap_factor_median': (ratio / er).median(),
           'corr_flex_energy': float(np.corrcoef(ratio, er)[0, 1]),
           'dailymean_over_hourly_actual_pct': (np.median(G.flex_b_act / act) - 1) * 100,
           'ratio_vs_dailymean_actual': float(np.median(G.flex_b_est / G.flex_b_act)),
           'deadband_floor_share_pct': float(np.median(1 - Fh.act_h / Fh.act_h_all) * 100),
           'coldest_wape_pct': O._wape(G.cold_est, Fh.cold_h),
           'coldest_r2': float(U.metrics(Fh.cold_h, G.cold_est)[1]),
           'fig11_n_hp': len(s['B']), 'fig11_pmax_kw': s['cap'],
           'fig11_floor_kwh_day': floor,
           'fig11_floor_share_pct': floor / (s['fa'].max() * DT_FIG11) * 100,
           'fig11_actual_mwh': float(s['fa'][~warm].sum() / 1000),
           'fig11_est_mwh': float(s['fe'][~warm].sum() / 1000),
           'pilot0_b': pf['b'], 'pilot0_m': pf['m'], 'pilot0_T_h': pf['T_h'], 'pilot0_r2': pf['r2']}
    rows = [dict(quantity=k, draft=t, reproduced=float(got[k]), tol=tol, ok=abs(got[k] - t) <= tol + 1e-9)
            for k, (t, tol) in TARGETS.items()]
    checks = pd.DataFrame(rows)

    # context for Step 1: where SF = 0.5, for the pilot curve (with b_h) and for the
    # estimate (Eq. sf-target: no intercept, the target's own T_h)
    T = Dz['T']
    pm = pd.Series([p['m'] for p in Dz['pilots']])
    ctx = dict(T_min=float(T.min()), T_max=float(T.max()), n_days=int(len(T)),
               T_cross_pilot0_with_b=pf['T_h'] - (0.5 - pf['b']) / pf['m'],
               T_cross_fig11_estimate=s['T_h'] - 0.5 / s['m'],
               n_days_below_fig11_cross=int((T < s['T_h'] - 0.5 / s['m']).sum()),
               n_heating_days_fig11=int((~warm).sum()),
               T_h_target_median=float(G.T_h.median()), T_h_target_iqr=(float(G.T_h.quantile(.25)), float(G.T_h.quantile(.75))),
               pilot_m_median=float(pm.median()), pilot_m_iqr=(float(pm.quantile(.25)), float(pm.quantile(.75))),
               fig11_sf_e_max=float(s['sf_e'].max()))
    extras = dict(G=G, Fh=Fh, pilots=Dz['pilots'], fig11=s, pilot0=pf, same_as_paper_cache=same, context=ctx)
    return checks, extras


# ===========================================================================
# Step 1 -- headroom and flexible energy against temperature
# ===========================================================================
T_IN = (20.0, 21.0)            # indoor temperatures of the W2 window (assumption, parameter range)
MIN_DAYS = 5                   # a temperature bin needs this many days
PRIMARY = (50, 25)             # (N, N_hp): 50 consumers at 50% HP penetration
SETTINGS = ((10, 5), (30, 15), (50, 25))
C_UP, C_DOWN = '#1f77b4', '#d95f02'      # blue / orange: colour-blind safe pair
C_W2 = ('#1b9e77', '#7570b3')            # T_in = 20, 21 degC


def _replay_members(Dz):
    """HP rows of every aggregate, row-aligned with ``Dz['rows']``.

    Replays the draw of ``outputs._kloten_design`` (one generator, seed 0, same
    order), as ``outputs._kloten_flex_hourly`` does.
    """
    K = Dz['K']
    rng = np.random.default_rng(0); nfree = K['free'].shape[0]
    out = []
    for _ in range(len(Dz['pilots'])):
        A, B = O._pilot_split(len(K['cap']), rng)
        for N in O.N_GRID_K:
            for nh in O.NHP_GRID_K:
                if nh > N:
                    continue
                for _ in range(3):
                    H = rng.choice(B, nh, replace=False)
                    if N > nh:
                        rng.choice(nfree, N - nh, replace=False)
                    out.append(H)
    caps = np.array([K['cap'][H].sum() for H in out])
    if len(out) != len(Dz['rows']) or not np.allclose(caps, Dz['rows'].cap.to_numpy()):
        raise RuntimeError('replay does not reproduce _kloten_design')
    return out


def daily_frames(rebuild=False):
    """Per aggregate and day: actual daily-mean SF and hourly-reference flexibility.

    Returns dict(T, sf_a, fa_h, members) with ``sf_a`` and ``fa_h`` arrays of
    shape (aggregates, days), row-aligned with the design rows. ``fa_h`` is the
    paper's actual flexibility per hour of window (kW): the mean over the day's
    hours of SF_t (1 - SF_t) P_max.
    """
    def build():
        Dz, _ = rebuild_design()
        G = Dz['rows']; K = Dz['K']; Kh = O._kloten_hourly(); T = Dz['T']; nd = len(T)
        members = _replay_members(Dz)
        sf_a = np.empty((len(G), nd), np.float32); fa_h = np.empty_like(sf_a)
        for i, H in enumerate(members):
            cap = float(G.cap.iat[i])
            sf_a[i] = np.clip(K['hp'][H].sum(0) / cap, 0, 1)
            fa_h[i] = O._hourly_flex(Kh['hp'][H].sum(0).reshape(nd, 24), cap)
        return dict(T=np.asarray(T, float), sf_a=sf_a, fa_h=fa_h, members=members)
    return _cached('step1_daily', build, rebuild)


def temperature_bins(T, min_days=MIN_DAYS, width=1):
    """``width`` degC bins of daily mean temperature; a bin with fewer than
    ``min_days`` days is merged into its neighbour towards the centre of the range.

    Returns (edges, merged) with ``merged`` the list of bins (lo, hi, days) that
    were merged away.
    """
    T = np.asarray(T)
    lo = np.floor(T.min())
    edges = list(np.arange(lo, np.ceil(T.max()) + width, width))
    if len(edges) < 2:
        edges.append(edges[0] + width)
    merged = []
    while True:
        n = np.histogram(T, edges)[0]
        bad = np.flatnonzero(n < min_days)
        if not len(bad) or len(n) == 1:
            return np.array(edges), merged
        k = bad[0]
        merged.append((edges[k], edges[k + 1], int(n[k])))
        # drop the inner edge of bin k: merges it with its neighbour towards the centre
        edges.pop(k + 1 if k < (len(n) - 1) / 2 else k)


def _peak(x, y):
    """Vertex of the parabola through the largest point and its two neighbours."""
    ok = np.isfinite(y)
    x, y = np.asarray(x)[ok], np.asarray(y)[ok]
    if len(y) == 0:
        return np.nan
    k = int(np.argmax(y))
    if k == 0 or k == len(y) - 1:
        return float(x[k])
    a, b, _ = np.polyfit(x[k - 1:k + 2], y[k - 1:k + 2], 2)
    if a >= 0:
        return float(x[k])
    return float(np.clip(-b / (2 * a), x[k - 1], x[k + 1]))


def _bin_means(v, idx, nb, mask):
    """Mean of ``v`` (aggregates x days) per bin over the masked days; NaN for
    bins with fewer than MIN_DAYS masked days of that aggregate."""
    out = np.full((v.shape[0], nb), np.nan); cnt = np.zeros((v.shape[0], nb), int)
    for b in range(nb):
        m = mask & (idx == b)[None, :]
        cnt[:, b] = m.sum(1)
        with np.errstate(invalid='ignore', divide='ignore'):
            out[:, b] = np.where(m, v, 0).sum(1) / cnt[:, b]
    out[cnt < MIN_DAYS] = np.nan
    return out, cnt


def step1_curves(N, N_hp, D=None, use_b=False):
    """Binned headroom and flexibility of the (N, N_hp) aggregates against T.

    Per aggregate and 1 degC bin of heating-regime days (T < own T_h): bin means
    of P_down, P_up and F (W1, per hour of window) for estimate and actual, all
    per kW of true installed capacity, and F under W2, Dt ~ 1/(T_in - T),
    normalised by its own maximum over the bins. Dead-band days (T >= T_h) give
    the actual floor, binned separately. ``use_b`` adds the pilot's intercept b_h
    to the estimated SF (diagnostic only; the paper's estimate has none).
    """
    Dz, _ = rebuild_design()
    D = daily_frames() if D is None else D
    G = Dz['rows']; T = D['T']
    sel = np.flatnonzero(((G.N == N) & (G.N_hp == N_hp)).to_numpy())
    g = G.iloc[sel].reset_index(drop=True)
    cap = g.cap.to_numpy()[:, None]; cap_e = g.cap_est.to_numpy()[:, None]
    th = g.T_h.to_numpy()[:, None]; m = g.m_pilot.to_numpy()[:, None]
    heat = T[None, :] < th
    sf_e = np.clip(m * np.maximum(0, th - T[None, :]), 0, 1)
    if use_b:
        b = np.array([Dz['pilots'][s]['b'] for s in g.split])[:, None]
        sf_e = np.where(heat, np.clip(b + sf_e, 0, 1), 0)
    sf_a = D['sf_a'][sel].astype(float); fa_h = D['fa_h'][sel].astype(float)

    edges, merged = temperature_bins(T[T < th.max()])
    nb = len(edges) - 1
    idx = np.clip(np.digitize(T, edges) - 1, 0, nb - 1)
    idx[(T < edges[0]) | (T >= edges[-1])] = -1
    q = dict(pdown_e=sf_e * cap_e / cap, pup_e=(1 - sf_e) * cap_e / cap,
             pdown_a=sf_a, pup_a=1 - sf_a,
             f_e=sf_e * (1 - sf_e) * cap_e / cap, f_a=fa_h / cap, f_ad=sf_a * (1 - sf_a))
    for t_in in T_IN:
        w = 1 / (t_in - T[None, :])
        q[f'w2_e_{t_in:g}'] = q['f_e'] * w
        q[f'w2_a_{t_in:g}'] = q['f_a'] * w
    B = {}
    for k, v in q.items():
        B[k], ndays = _bin_means(v, idx, nb, heat)
    for k in [k for k in B if k.startswith('w2_')]:
        B[k] = B[k] / np.nanmax(B[k], 1, keepdims=True)
    # exact identity per bin: ratio = energy factor x headroom factor x hourly factor
    B['ratio'] = B['f_e'] / B['f_a']
    B['energy_factor'] = B['pdown_e'] / B['pdown_a']
    B['headroom_factor'] = (B['f_e'] / B['pdown_e']) / (B['f_ad'] / B['pdown_a'])
    B['hourly_factor'] = B['f_ad'] / B['f_a']
    xb = np.array([T[idx == b].mean() for b in range(nb)])        # bin x: mean daily T of its days
    # dead-band floor of the actual (days >= own T_h), on its own 1 degC grid
    we, _ = temperature_bins(T[T >= th.min()])
    wi = np.clip(np.digitize(T, we) - 1, 0, len(we) - 2)
    wi[T < we[0]] = -1
    floor, _ = _bin_means(q['f_a'], wi, len(we) - 1, ~heat)
    xw = np.array([T[wi == b].mean() for b in range(len(we) - 1)])
    return dict(g=g, edges=edges, x=xb, merged=merged, ndays=ndays, B=B, floor=floor, x_floor=xw,
                share_sf_ge_half=dict(est=float((sf_e[heat] >= .5).mean()), act=float((sf_a[heat] >= .5).mean())),
                n_heat_days=int(heat.sum()))


def _qstr(v, f='{:.2f}'):
    v = pd.Series(np.asarray(v, float)).dropna()
    if not len(v):
        return '–'
    return (f + ' [' + f + ', ' + f + ']').format(v.median(), v.quantile(.25), v.quantile(.75))


def step1_peaks(C):
    """Peak temperature per curve: per aggregate, median within split, then
    median [IQR] over splits; plus the coldest bin as a share of the peak."""
    g, x, B = C['g'], C['x'], C['B']
    rows = []
    for name, keys in [('W1', ('f_e', 'f_a'))] + [(f'W2, T_in = {t:g} °C', (f'w2_e_{t:g}', f'w2_a_{t:g}')) for t in T_IN]:
        for who, k in zip(('estimate', 'actual'), keys):
            pk = np.array([_peak(x, B[k][i]) for i in range(len(g))])
            first = np.array([B[k][i][np.isfinite(B[k][i])][0] for i in range(len(g))])
            cold = first / np.nanmax(B[k], 1)
            per_split = pd.Series(pk).groupby(g.split.to_numpy()).median()
            rows.append(dict(window=name, curve=who,
                             peak_split_med=per_split.median(), peak_split_q25=per_split.quantile(.25),
                             peak_split_q75=per_split.quantile(.75),
                             peak_split_iqr=per_split.quantile(.75) - per_split.quantile(.25),
                             cold_over_peak=float(np.median(cold))))
    return pd.DataFrame(rows)


def step1_bin_table(C):
    """Per bin: days, median [IQR] across aggregates of F (W1) estimate, actual and
    their ratio, the ratio over splits, and the three factors of the ratio."""
    B, g = C['B'], C['g']
    rows = []
    for b in range(len(C['x'])):
        r = B['ratio'][:, b]
        rs = pd.Series(r).groupby(g.split.to_numpy()).median()
        rows.append({'bin (°C)': f"[{C['edges'][b]:.0f}, {C['edges'][b + 1]:.0f})",
                     'days': int(np.median(C['ndays'][:, b])), 'aggregates': int(np.isfinite(r).sum()),
                     'F est': _qstr(B['f_e'][:, b], '{:.3f}'), 'F act': _qstr(B['f_a'][:, b], '{:.3f}'),
                     'est/act (aggregates)': _qstr(r), 'est/act (splits)': _qstr(rs),
                     'P_up est/act': f"{np.nanmedian(B['pup_e'][:, b] / B['pup_a'][:, b]):.2f}",
                     'energy': f"{np.nanmedian(B['energy_factor'][:, b]):.2f}",
                     'headroom': f"{np.nanmedian(B['headroom_factor'][:, b]):.2f}",
                     'hourly': f"{np.nanmedian(B['hourly_factor'][:, b]):.2f}"})
    return pd.DataFrame(rows)


def step1_checks(C, peaks):
    """E1.1-E1.7 of FLEX_LOG.md against the primary-setting curves."""
    B, x = C['B'], C['x']
    res = {}

    def mono(k):    # warm to cold: never more than 2% below the next warmer bin
        med = np.nanmedian(B[k], 0)
        mc = med[np.isfinite(med)][::-1]
        drops = mc[1:] / mc[:-1] - 1
        return bool((drops >= -0.02).all()), float(drops.min())
    res['E1.1 estimate'] = mono('f_e'); res['E1.1 actual'] = mono('f_a')
    for t in T_IN:
        for who, rng_, tag in (('actual', (6.5, 9.5), 'E1.2a'), ('estimate', (4.5, 6.5), 'E1.2b')):
            p = peaks[(peaks.window == f'W2, T_in = {t:g} °C') & (peaks.curve == who)].iloc[0]
            res[f'{tag} T_in={t:g}'] = (bool(rng_[0] <= p.peak_split_med <= rng_[1] and p.cold_over_peak < 1),
                                        round(p.peak_split_med, 2))
    sh = C['share_sf_ge_half']
    res['E1.3 estimate'] = (sh['est'] <= .01, sh['est']); res['E1.3 actual'] = (sh['act'] <= .01, sh['act'])
    rm = np.nanmedian(B['ratio'], 0)
    res['E1.4'] = (bool(((rm >= .94) & (rm <= 1.14))[np.isfinite(rm)].all()),
                   (float(np.nanmin(rm)), float(np.nanmax(rm))))
    for who in ('estimate', 'actual'):
        iq = peaks[peaks.window.str.startswith('W2') & (peaks.curve == who)].peak_split_iqr
        res[f'E1.5 {who}'] = (bool((iq <= 2).all()), float(iq.max()))
    th = float(np.median(C['g'].T_h))
    warm = (x >= th - 3) & np.isfinite(rm)
    res['E1.6'] = (bool((rm[warm] < .94).all()), [round(v, 2) for v in rm[warm]])
    co = peaks[peaks.window.str.startswith('W2')].cold_over_peak
    res['E1.7'] = (bool((co >= .7).all()), float(co.min()))
    return res


def fig_flex_temperature(C, name='fig_flex_temperature'):
    """Draft figure: (a) P_up and P_down, (b) F under W1, (c) F under W2
    (normalised), estimate against actual, median and IQR across aggregates."""
    import matplotlib.pyplot as plt
    import hp_figures as hf
    hf.use_style()
    B, x = C['B'], C['x']
    th = float(np.median(C['g'].T_h))
    fig, axs = plt.subplots(3, 1, figsize=(hf.COL1, 5.6), sharex=True)

    def band(ax, M, color, ls, label, xx=x, fill=True, lw=1.3):
        med = np.nanmedian(M, 0); ok = np.isfinite(med)
        if fill:
            ax.fill_between(xx[ok], np.nanquantile(M, .25, 0)[ok], np.nanquantile(M, .75, 0)[ok], color=color,
                            alpha=.20 if ls == '-' else .12, lw=0)
        ax.plot(xx[ok], med[ok], color=color, ls=ls, lw=lw, label=label)

    from matplotlib.lines import Line2D
    ax = axs[0]
    band(ax, B['pup_a'], C_UP, '-', None)
    band(ax, B['pup_e'], C_UP, '--', None)
    band(ax, B['pdown_a'], C_DOWN, '-', None)
    band(ax, B['pdown_e'], C_DOWN, '--', None)
    ax.text(-4, 1.07, 'upward $(1-\\mathrm{SF})P^{\\max}$', color=C_UP, fontsize=6.5)
    ax.text(-4, 0.47, 'downward $\\mathrm{SF}\\,P^{\\max}$', color=C_DOWN, fontsize=6.5)
    ax.legend([Line2D([], [], color='0.3', ls='-'), Line2D([], [], color='0.3', ls='--')],
              ['actual', 'estimate'], fontsize=6, loc='center right')
    ax.set_ylabel('headroom per kW\ninstalled (kW/kW)')
    ax.set_ylim(0, 1.25)

    ax = axs[1]
    band(ax, B['f_a'], '0.25', '-', 'actual (hourly SF)')
    band(ax, B['f_e'], hf.C_HP, '--', 'estimate')
    band(ax, C['floor'], '0.55', ':', 'actual, $T \\geq T_h$ (not counted)', xx=C['x_floor'], fill=False, lw=1.1)
    ax.axhline(.25, color='0.6', lw=.6, ls=(0, (1, 2)))
    ax.set_ylabel('$F$ per h of window\nper kW installed')
    ax.set_ylim(0, .3)
    ax.legend(fontsize=6, loc='lower left')

    ax = axs[2]
    for t, c, lw in zip(T_IN, C_W2, (1.3, 0.9)):
        band(ax, B[f'w2_a_{t:g}'], c, '-', f'actual, $T_{{in}}$ = {t:g} °C', fill=(t == T_IN[0]), lw=lw)
        band(ax, B[f'w2_e_{t:g}'], c, '--', f'estimate, $T_{{in}}$ = {t:g} °C', fill=(t == T_IN[0]), lw=lw)
    ax.set_ylabel('$F$, $\\Delta t \\propto 1/(T_{in}-T)$\n(normalised)')
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=6, loc='lower left')
    ax.set_xlabel('daily mean temperature (°C)')
    for ax in axs:
        ax.axvline(th, color='0.45', lw=.7, ls=(0, (3, 3)))
    axs[1].annotate('$T_h$', (th, .27), xytext=(3, 0), textcoords='offset points', fontsize=7, color='0.3')
    for ax, lab in zip(axs, 'abc'):
        ax.text(-0.24, 1.0, f'({lab})', transform=ax.transAxes, fontsize=8, va='top')
    fig.tight_layout()
    path = save_fig(fig, name)
    plt.close(fig)
    return path


def fig_flex_temperature_paper(C=None, name='fig_flex_temperature'):
    """Paper figure (Sec. IV-F, F2): panels (a) and (b) of the Step 1 draft.

    (a) upward and downward headroom, (b) flexible energy per hour of window,
    both per kW of true installed capacity, estimate against actual, median and
    IQR across the N = 50, N_hp = 25 aggregates. Saved with ``hp_figures.save``
    (``paper/figures`` unless HP_FIGDIR is set).
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import hp_figures as hf
    C = step1_curves(*PRIMARY) if C is None else C
    hf.use_style()
    B, x = C['B'], C['x']
    th = float(np.median(C['g'].T_h))
    fig, axs = plt.subplots(2, 1, figsize=(hf.COL1, 3.9), sharex=True)

    def band(ax, M, color, ls, label=None, xx=x, fill=True, lw=1.3):
        med = np.nanmedian(M, 0); ok = np.isfinite(med)
        if fill:
            ax.fill_between(xx[ok], np.nanquantile(M, .25, 0)[ok], np.nanquantile(M, .75, 0)[ok], color=color,
                            alpha=.20 if ls == '-' else .12, lw=0)
        ax.plot(xx[ok], med[ok], color=color, ls=ls, lw=lw, label=label)

    ax = axs[0]
    band(ax, B['pup_a'], C_UP, '-'); band(ax, B['pup_e'], C_UP, '--')
    band(ax, B['pdown_a'], C_DOWN, '-'); band(ax, B['pdown_e'], C_DOWN, '--')
    ax.text(-4, 1.07, 'upward, $(1-\\mathrm{SF})\\,P^{\\max}$', color=C_UP, fontsize=6.5)
    ax.text(-4, 0.47, 'downward, $P_{\\mathrm{TCL}}$', color=C_DOWN, fontsize=6.5)
    ax.legend([Line2D([], [], color='0.3', ls='-'), Line2D([], [], color='0.3', ls='--')],
              ['actual', 'estimate'], fontsize=6.5, loc='center right')
    ax.set_ylabel('headroom / $P^{\\max}$')
    ax.set_ylim(0, 1.25)

    ax = axs[1]
    band(ax, B['f_a'], '0.25', '-', 'actual')
    band(ax, B['f_e'], hf.C_HP, '--', 'estimate')
    band(ax, C['floor'], '0.55', ':', 'actual, $T \\geq T_h$ (not counted)', xx=C['x_floor'], fill=False, lw=1.1)
    ax.axhline(.25, color='0.6', lw=.6, ls=(0, (1, 2)))
    ax.set_ylabel('$E_{\\mathrm{flex}} / (\\Delta t_{Th}\\,P^{\\max})$')
    ax.set_ylim(0, .3)
    ax.legend(fontsize=6.5, loc='lower left')
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    for ax in axs:
        ax.axvline(th, color='0.45', lw=.7, ls=(0, (3, 3)))
    axs[1].annotate('$T_h$', (th, .27), xytext=(3, 0), textcoords='offset points', fontsize=7, color='0.3')
    for ax, lab in zip(axs, 'ab'):
        ax.text(-0.2, 1.05, f'({lab})', transform=ax.transAxes, fontsize=8, va='top')
    fig.tight_layout()
    path = hf.save(fig, name)
    plt.close(fig)
    return path


def step1(rebuild=False):
    """Step 1: curves for every setting, peaks, bin tables, checks and the figure."""
    D = daily_frames(rebuild)
    out = {}
    for N, nh in SETTINGS:
        C = step1_curves(N, nh, D)
        out[(N, nh)] = dict(C=C, peaks=step1_peaks(C), bins=step1_bin_table(C))
    Cb = step1_curves(*PRIMARY, D, use_b=True)
    out['primary_with_b'] = dict(C=Cb, peaks=step1_peaks(Cb), bins=step1_bin_table(Cb))
    P = out[PRIMARY]
    P['checks'] = step1_checks(P['C'], P['peaks'])
    P['fig'] = fig_flex_temperature(P['C'])
    return out


# ===========================================================================
# Step 1b -- window referenced to the threshold T_h, capped
# ===========================================================================
CAP_RATIOS = (3, 6, 12)        # Dt_max / Dt_5: 12 h, 24 h at Dt_5 = 4 h; 12 h, 24 h at Dt_5 = 2 h
T_REF = 5.0                    # temperature of the reference window Dt_5 (degC)
C_CAP = ('#1b9e77', '#d95f02', '#7570b3')


def step1b_curves(N, N_hp, D=None, ratios=CAP_RATIOS):
    """Binned flexibility under W3, Dt = Dt_5 (T_h - 5)/(T_h - T) capped at r Dt_5.

    Per aggregate and 1 degC bin of heating-regime days, the bin mean of F_W1
    times Dt/Dt_5 (estimate and actual, per kW of true capacity), unnormalised
    and normalised by the aggregate's own value in the bin holding 5 degC. T_h is
    the aggregate's net-load threshold, for estimate and actual alike.
    """
    Dz, _ = rebuild_design()
    D = daily_frames() if D is None else D
    G = Dz['rows']; T = D['T']
    sel = np.flatnonzero(((G.N == N) & (G.N_hp == N_hp)).to_numpy())
    g = G.iloc[sel].reset_index(drop=True)
    cap = g.cap.to_numpy()[:, None]; cap_e = g.cap_est.to_numpy()[:, None]
    th = g.T_h.to_numpy()[:, None]; m = g.m_pilot.to_numpy()[:, None]
    heat = T[None, :] < th
    sf_e = np.clip(m * np.maximum(0, th - T[None, :]), 0, 1)
    f_e = sf_e * (1 - sf_e) * cap_e / cap
    f_a = D['fa_h'][sel].astype(float) / cap
    edges, _ = temperature_bins(T[T < th.max()])
    nb = len(edges) - 1
    idx = np.clip(np.digitize(T, edges) - 1, 0, nb - 1)
    idx[(T < edges[0]) | (T >= edges[-1])] = -1
    b5 = int(np.searchsorted(edges, T_REF, side='right') - 1)
    xb = np.array([T[idx == b].mean() for b in range(nb)])
    with np.errstate(divide='ignore', invalid='ignore'):
        w_raw = np.where(heat, (th - T_REF) / (th - T[None, :]), np.nan)
    out = dict(g=g, edges=edges, x=xb, b5=b5, T_c={}, B={})
    out['B']['ratio_w1'] = _bin_means(f_e, idx, nb, heat)[0] / _bin_means(f_a, idx, nb, heat)[0]
    for r in ratios:
        w = np.minimum(w_raw, r)
        e, _ = _bin_means(f_e * w, idx, nb, heat)
        a, _ = _bin_means(f_a * w, idx, nb, heat)
        out['B'][f'e_{r}'] = e / e[:, [b5]]
        out['B'][f'a_{r}'] = a / a[:, [b5]]
        out['B'][f'ratio_{r}'] = e / a
        out['T_c'][r] = th[:, 0] - (th[:, 0] - T_REF) / r
    # closed form for the estimate below the cap onset, at the median m_h and T_h
    mm, tt = float(np.median(m)), float(np.median(th))
    sf = np.clip(mm * np.maximum(0, tt - xb), 0, 1)
    out['closed'] = (1 - sf) / (1 - mm * (tt - xb[b5]))
    return out


def step1b_peaks(C, ratios=CAP_RATIOS):
    """Per cap ratio: peak temperature and peak value (median [IQR] over splits),
    median cap onset, and the coldest bin relative to 5 degC, estimate and actual."""
    g, x, B = C['g'], C['x'], C['B']
    rows = []
    for r in ratios:
        for who in ('e', 'a'):
            M = B[f'{who}_{r}']
            pk = pd.Series([_peak(x, M[i]) for i in range(len(g))]).groupby(g.split.to_numpy()).median()
            pv = pd.Series(np.nanmax(M, 1)).groupby(g.split.to_numpy()).median()
            cold = np.array([M[i][np.isfinite(M[i])][0] for i in range(len(g))])
            rows.append(dict(r=r, curve='estimate' if who == 'e' else 'actual',
                             T_c=float(np.median(C['T_c'][r])),
                             peak_med=pk.median(), peak_q25=pk.quantile(.25), peak_q75=pk.quantile(.75),
                             peak_value=pv.median(), cold_over_5C=float(np.median(cold))))
    return pd.DataFrame(rows)


def step1b_checks(C, P, ratio_w1_step1, ratios=CAP_RATIOS):
    """E1b.1-E1b.6 of FLEX_LOG.md."""
    B, x = C['B'], C['x']
    res = {}
    for r in ratios:
        tc = float(np.median(C['T_c'][r]))
        med = np.nanmedian(B[f'e_{r}'], 0)
        below = (x < tc - 1) & np.isfinite(med)
        dev = med[below] / C['closed'][below] - 1
        res[f'E1b.1 r={r}'] = (bool((np.abs(dev) <= .03).all()), float(np.abs(dev).max()))
    for r in ratios:
        p = P[(P.r == r) & (P.curve == 'estimate')].iloc[0]
        res[f'E1b.2 r={r}'] = (bool(abs(p.peak_med - p.T_c) <= 1), (round(p.peak_med, 2), round(p.T_c, 2)))
    ce = P[P.curve == 'estimate'].cold_over_5C; ca = P[P.curve == 'actual'].cold_over_5C
    res['E1b.3'] = (bool(((ce >= .75) & (ce <= .85)).all()), ce.round(3).tolist())
    res['E1b.4'] = (bool(((ca >= .70) & (ca <= .80)).all()), ca.round(3).tolist())
    for r in (6, 12):
        p = P[(P.r == r) & (P.curve == 'actual')].iloc[0]
        res[f'E1b.5 r={r}'] = (bool(p.peak_med >= 14 and p.peak_value > 1.2), (round(p.peak_med, 2), round(p.peak_value, 2)))
    for r in ratios:
        d = np.nanmedian(B[f'ratio_{r}'], 0) - np.nanmedian(ratio_w1_step1, 0)
        res[f'E1b.6 r={r}'] = (bool((np.abs(d[np.isfinite(d)]) <= .03).all()), float(np.nanmax(np.abs(d))))
    return res


def fig_window_th(C, name='fig_flex_window_th', ratios=CAP_RATIOS):
    """Draft figure: F under W3 relative to its 5 degC value, (a) estimate with the
    uncapped closed form, (b) actual; one line per cap ratio, IQR band for r = 6."""
    import matplotlib.pyplot as plt
    import hp_figures as hf
    hf.use_style()
    B, x = C['B'], C['x']
    th = float(np.median(C['g'].T_h))
    fig, axs = plt.subplots(2, 1, figsize=(hf.COL1, 4.2), sharex=True, sharey=True)
    for ax, who, title in ((axs[0], 'e', 'estimate'), (axs[1], 'a', 'actual')):
        for r, c in zip(ratios, C_CAP):
            M = B[f'{who}_{r}']; med = np.nanmedian(M, 0); ok = np.isfinite(med)
            if r == 6:
                ax.fill_between(x[ok], np.nanquantile(M, .25, 0)[ok], np.nanquantile(M, .75, 0)[ok], color=c, alpha=.18, lw=0)
            ax.plot(x[ok], med[ok], color=c, lw=1.3, ls=('-', '--', ':')[ratios.index(r)],
                    label=f'cap $r$ = {r}')
            ax.axvline(float(np.median(C['T_c'][r])), color=c, lw=.6, ls=(0, (1, 2)))
        if who == 'e':
            ok = x < th
            ax.plot(x[ok], C['closed'][ok], color='0.2', lw=.8, ls=(0, (4, 2)), label='uncapped, $(1-\\mathrm{SF})$')
        ax.axhline(1, color='0.6', lw=.6)
        ax.axvline(th, color='0.45', lw=.7, ls=(0, (3, 3)))
        ax.set_ylabel(f'{title}: $F$ relative\nto its 5 °C value')
        ax.legend(fontsize=6, loc='upper left')
    axs[1].set_xlabel('daily mean temperature (°C)')
    axs[0].annotate('$T_h$', (th, axs[0].get_ylim()[1] * .95), xytext=(3, 0), textcoords='offset points', fontsize=7, color='0.3')
    for ax, lab in zip(axs, 'ab'):
        ax.text(-0.27, 1.05, f'({lab})', transform=ax.transAxes, fontsize=8, va='top')
    fig.tight_layout()
    path = save_fig(fig, name)
    plt.close(fig)
    return path


def step1b():
    """Step 1b: W3 curves at N = 50 (primary), 30 and 10; peaks, checks and figure."""
    D = daily_frames()
    out = {}
    for N, nh in SETTINGS:
        C = step1b_curves(N, nh, D)
        out[(N, nh)] = dict(C=C, peaks=step1b_peaks(C))
    P = out[PRIMARY]
    C1 = step1_curves(*PRIMARY, D)
    P['checks'] = step1b_checks(P['C'], P['peaks'], C1['B']['ratio'])
    P['fig'] = fig_window_th(P['C'])
    return out


# ===========================================================================
# Step 2 -- firm flexibility and aggregation
# ===========================================================================
FIRM_Q = 0.10                  # lower quantile across days: "firm" flexibility
FIRM_MIN_DAYS = 10             # a bin needs this many days (Alex, Step 1 decision 1)
FIRM_WIDTH = 2                 # bin width (degC)


def step2_rows(D=None):
    """Long frame, one row per aggregate and 2 degC bin of its heating days.

    For F under W1 per kW of true capacity, the P10 and median across days of the
    actual (hourly reference) and of the estimate, their ratios r = P10/median,
    and P10(actual)/median(estimate) ("firm over promised"). N in N_GRID_K at
    50% penetration.
    """
    Dz, _ = rebuild_design()
    D = daily_frames() if D is None else D
    G = Dz['rows']; T = D['T']
    rows = []
    for N in O.N_GRID_K:
        sel = np.flatnonzero(((G.N == N) & (G.N_hp == N // 2)).to_numpy())
        g = G.iloc[sel]
        th_max = g.T_h.max()
        edges, _ = temperature_bins(T[T < th_max], FIRM_MIN_DAYS, FIRM_WIDTH)
        idx = np.clip(np.digitize(T, edges) - 1, 0, len(edges) - 2)
        for j, r in zip(sel, g.itertuples()):
            sf_e = O.sf_target(T, r.T_h, r.m_pilot)
            f_e = sf_e * (1 - sf_e) * r.cap_est / r.cap
            f_a = D['fa_h'][j].astype(float) / r.cap
            for b in range(len(edges) - 1):
                m = (T < r.T_h) & (idx == b) & (T >= edges[0])
                if m.sum() < FIRM_MIN_DAYS:
                    continue
                pa, ma = np.quantile(f_a[m], FIRM_Q), np.median(f_a[m])
                pe, me = np.quantile(f_e[m], FIRM_Q), np.median(f_e[m])
                rows.append(dict(N=N, N_hp=N // 2, split=r.split, row=j, bin=b,
                                 lo=edges[b], hi=edges[b + 1], x=float(T[m].mean()), days=int(m.sum()),
                                 med_a=ma, p10_a=pa, med_e=me, p10_e=pe,
                                 r_a=pa / ma, r_e=pe / me, firm_promised=pa / me))
    return pd.DataFrame(rows)


def _split_summary(L, col):
    """Per aggregate the median over its bins, then the median within each split;
    returns median, q25, q75 over the 20 splits for every N."""
    s = L.groupby(['N', 'split', 'row'])[col].median().groupby(['N', 'split']).median()
    return s.groupby('N').agg(med='median', q25=lambda v: v.quantile(.25), q75=lambda v: v.quantile(.75))


def step2_summary(L):
    """P10/median (actual, estimate) and firm over promised against N, with the
    daily-resolution fit quality of Fig. 9 from the paper's cache."""
    out = pd.concat({c: _split_summary(L, c) for c in ('r_a', 'r_e', 'firm_promised')}, axis=1)
    Q = pd.read_pickle(O.KLOTEN_QUALITY)
    q = Q[Q.resolution == '24 h'].groupby('N')[['r2_net', 'r2_sf']].median()
    out[('fig9', 'r2_net')] = q.r2_net.reindex(out.index)
    out[('fig9', 'r2_sf')] = q.r2_sf.reindex(out.index)
    return out


def step2_bins(L):
    """Median across aggregates of r (actual, estimate) and firm over promised, per bin and N."""
    lab = L.apply(lambda r: f'[{r.lo:.0f}, {r.hi:.0f})', axis=1)
    t = L.assign(bin_label=lab).groupby(['N', 'lo', 'bin_label'])[['days', 'r_a', 'r_e', 'firm_promised']].median()
    return t.reset_index(level='lo', drop=True)


def step2_checks(S, L):
    """E2.1-E2.5 of FLEX_LOG.md."""
    a, e = S[('r_a', 'med')], S[('r_e', 'med')]
    res = {'E2.1': (bool((a.diff().dropna() >= -0.01).all() and a.iloc[-1] > a.iloc[0]), a.round(3).tolist()),
           'E2.2': (bool(e.max() - e.min() <= 0.02), e.round(3).tolist()),
           'E2.3': (bool((e > a).all()), (e - a).round(3).tolist())}
    b50 = L[L.N == 50].groupby('bin')['r_a'].median()
    res['E2.4'] = (bool(b50.idxmin() == b50.index.max()), b50.round(3).tolist())
    res['E2.5'] = (bool(0.80 <= a.loc[50] <= 0.95), round(float(a.loc[50]), 3))
    return res


def fig_firm(S, L, name='fig_firm_flex'):
    """Draft figure: (a) P10/median against N, actual vs estimate, with firm over
    promised; (b) actual P10/median by temperature bin for N = 10, 30, 50."""
    import matplotlib.pyplot as plt
    import hp_figures as hf
    hf.use_style()
    fig, axs = plt.subplots(2, 1, figsize=(hf.COL1, 4.0))
    ax = axs[0]
    n = S.index.to_numpy()
    for col, c, ls, mk, lab in (('r_a', '0.25', '-', 'o', 'actual'), ('r_e', hf.C_HP, '--', 's', 'estimate'),
                                ('firm_promised', C_UP, ':', '^', 'P10 actual / median estimate')):
        ax.fill_between(n, S[(col, 'q25')], S[(col, 'q75')], color=c, alpha=.15, lw=0)
        ax.plot(n, S[(col, 'med')], color=c, ls=ls, marker=mk, label=lab)
    ax.set_xlabel('households per aggregate $N$ (50% with an HP)')
    ax.set_ylabel('P10 / median of daily $F$')
    ax.set_xticks(n)
    ax.legend(fontsize=6, loc='lower right')

    ax = axs[1]
    for N, c in zip((10, 30, 50), ('#9ecae1', '#4292c6', '#08306b')):
        t = L[L.N == N].groupby('bin').agg(x=('x', 'median'), r=('r_a', 'median'))
        ax.plot(t.x, t.r, color=c, marker='o', label=f'actual, $N$ = {N}')
    t = L[L.N == 50].groupby('bin').agg(x=('x', 'median'), r=('r_e', 'median'))
    ax.plot(t.x, t.r, color=hf.C_HP, ls='--', marker='s', label='estimate, $N$ = 50')
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('P10 / median of daily $F$')
    ax.legend(fontsize=6, loc='lower left')
    for ax, lab in zip(axs, 'ab'):
        ax.text(-0.27, 1.05, f'({lab})', transform=ax.transAxes, fontsize=8, va='top')
    fig.tight_layout()
    path = save_fig(fig, name)
    plt.close(fig)
    return path


def step2_detrended(D=None, f_min=0.05):
    """Diagnostic (D2): day-to-day spread of the actual F net of temperature.

    Per aggregate, a quadratic in T fitted to its actual F (per kW) over its
    heating days; on the days where the fit exceeds ``f_min`` (leaves out the
    near-threshold days where the ratio blows up), the P10 and standard deviation
    of actual / fit. Median within split, then median [IQR] over splits, per N.
    """
    Dz, _ = rebuild_design()
    D = daily_frames() if D is None else D
    G = Dz['rows']; T = D['T']
    rows = []
    for N in O.N_GRID_K:
        for j in np.flatnonzero(((G.N == N) & (G.N_hp == N // 2)).to_numpy()):
            r = G.iloc[j]; h = T < r.T_h
            f = D['fa_h'][j][h] / r.cap; t = T[h]
            fit = np.polyval(np.polyfit(t, f, 2), t); ok = fit > f_min
            q = f[ok] / fit[ok]
            rows.append(dict(N=N, split=r.split, p10=np.quantile(q, FIRM_Q), sd=q.std(), days=int(ok.sum())))
    s = pd.DataFrame(rows).groupby(['N', 'split'])[['p10', 'sd']].median()
    return s.groupby('N').agg(['median', lambda v: v.quantile(.25), lambda v: v.quantile(.75)]).rename(
        columns={'<lambda_0>': 'q25', '<lambda_1>': 'q75'})


def step2_shoulder(D=None, lo=11, hi=13):
    """Diagnostic (D2): the days of one bin at N = 50, ranked by the median actual
    F per kW over the 60 aggregates, with their date."""
    Dz, _ = rebuild_design()
    D = daily_frames() if D is None else D
    G = Dz['rows']; T = D['T']
    sel = np.flatnonzero(((G.N == 50) & (G.N_hp == 25)).to_numpy())
    fa = np.median(D['fa_h'][sel] / G.cap.to_numpy()[sel, None], 0)
    days = pd.date_range('2023-01-01', periods=len(T), freq='D')
    m = (T >= lo) & (T < hi)
    return pd.DataFrame({'date': days[m].date, 'T': T[m], 'F_per_kW': fa[m]}).sort_values('F_per_kW')


def flex_example(split=0, min_days=MIN_DAYS):
    """Daily flexibility of one example aggregate against temperature, binned.

    The aggregate is the target half of ``split`` (the draft's Fig. 11 example:
    25 HPs with their homes' other load). Per 2 degC bin merged to >= ``min_days``
    days, the median and IQR across days of the actual F (hourly reference, kW
    per hour of window), separately for heating-regime days and dead-band days.
    """
    Dz, _ = rebuild_design()
    s = fig11_split(Dz, split)
    T, fa = s['T'], s['fa']
    rows = []
    for regime, mask in (('heating', T < s['T_h']), ('dead band', T >= s['T_h'])):
        edges, merged = temperature_bins(T[mask], min_days, FIRM_WIDTH)
        idx = np.clip(np.digitize(T, edges) - 1, 0, len(edges) - 2)
        for b in range(len(edges) - 1):
            m = mask & (idx == b) & (T >= edges[0]) & (T < edges[-1])
            if not m.any():
                continue
            q25, med, q75 = np.quantile(fa[m], [.25, .5, .75])
            rows.append(dict(regime=regime, lo=edges[b], hi=edges[b + 1], x=float(T[m].mean()), days=int(m.sum()),
                             med=med, q25=q25, q75=q75))
    return s, pd.DataFrame(rows)


def fig_flex_example(split=0, name='fig_flex_example'):
    """Draft figure: one aggregate's flexible energy per hour of window against
    daily mean temperature. Actual as median and IQR across days per bin, daily
    values as dots; the estimate as its fitted curve."""
    import matplotlib.pyplot as plt
    import hp_figures as hf
    s, R = flex_example(split)
    hf.use_style()
    T, fa, th = s['T'], s['fa'], s['T_h']
    fig, ax = plt.subplots(figsize=(hf.COL1, 2.6))
    ax.scatter(T, fa, s=5, color='0.7', edgecolor='none', zorder=1, label='actual, daily')
    for regime, c, lab in (('heating', '0.2', 'actual, median and IQR'), ('dead band', '0.55', 'actual, $T \\geq T_h$ (not counted)')):
        r = R[R.regime == regime]
        ax.fill_between(r.x, r.q25, r.q75, color=c, alpha=.25, lw=0, zorder=2)
        ax.plot(r.x, r.med, color=c, lw=1.4, marker='o', ms=2.5, zorder=3, label=lab)
    tg = np.linspace(T.min(), th, 200)
    sf = O.sf_target(tg, th, s['m'])
    ax.plot(tg, sf * (1 - sf) * s['cap_e'], color=hf.C_HP, ls='--', lw=1.4, zorder=4, label='estimate')
    ax.axhline(.25 * s['cap'], color='0.6', lw=.6, ls=(0, (1, 2)))
    ax.annotate('$0.25\\,P^{\\max}$', (T.max(), .25 * s['cap']), xytext=(0, 2), textcoords='offset points',
                ha='right', va='bottom', fontsize=6.5, color='0.4')
    ax.axvline(th, color='0.45', lw=.7, ls=(0, (3, 3)))
    ax.annotate('$T_h$', (th, .22 * s['cap']), xytext=(3, 0), textcoords='offset points', fontsize=7, color='0.3')
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('$E_{\\mathrm{flex}}$ per h of window (kWh/h)')
    ax.set_ylim(0, .3 * s['cap'])
    ax.legend(fontsize=6, loc='lower left')
    fig.tight_layout()
    path = save_fig(fig, name)
    plt.close(fig)
    return path, R


def flex_all_normalised(D=None, min_days=MIN_DAYS):
    """Every aggregate's binned flexibility against T, normalised by its own maximum.

    Per aggregate and 2 degC bin (common edges over the heating range, merged to
    >= ``min_days`` days; per aggregate a bin needs ``min_days`` of its own days):
    median, q25 and q75 across days of the actual F (hourly reference) and the
    mean of the estimate, all divided by the aggregate's largest actual bin
    median. Dead-band days (T >= own T_h) are binned the same way, with the
    estimate left out. Returns a long frame, one row per aggregate and bin.
    """
    Dz, _ = rebuild_design()
    D = daily_frames() if D is None else D
    G = Dz['rows']; T = D['T']
    th = G.T_h.to_numpy()
    edges, _ = temperature_bins(T, min_days, FIRM_WIDTH)
    idx = np.clip(np.digitize(T, edges) - 1, 0, len(edges) - 2)
    xb = np.array([T[idx == b].mean() for b in range(len(edges) - 1)])
    rows = []
    for i, r in enumerate(G.itertuples()):
        fa = D['fa_h'][i].astype(float)
        sf_e = O.sf_target(T, r.T_h, r.m_pilot)
        fe = sf_e * (1 - sf_e) * r.cap_est
        cur = []
        for b in range(len(edges) - 1):
            for regime, m in (('heating', (idx == b) & (T < th[i])), ('dead band', (idx == b) & (T >= th[i]))):
                if m.sum() < min_days:
                    continue
                q25, med, q75 = np.quantile(fa[m], [.25, .5, .75])
                cur.append(dict(row=i, split=r.split, N=r.N, N_hp=r.N_hp, bin=b, x=xb[b], regime=regime,
                                days=int(m.sum()), med=med, q25=q25, q75=q75,
                                est=float(fe[m].mean()) if regime == 'heating' else np.nan))
        c = pd.DataFrame(cur)
        ref = c.loc[c.regime == 'heating', 'med'].max()
        for k in ('med', 'q25', 'q75', 'est'):
            c[k] = c[k] / ref
        rows.append(c)
    return pd.concat(rows, ignore_index=True)


def fig_flex_all(L=None, name='fig_flex_all_normalised', saver=None):
    """All aggregates on one axis, normalised by own maximum (paper Fig. 7 since
    the storyline pass; ``outputs.flex_temperature_figure`` saves it to paper/).

    (a) Actual: median over aggregates of their bin medians with the IQR across
    aggregates; estimate dashed with its IQR across aggregates; dead-band floor
    dotted. (b) Day-to-day IQR / median of the actual for 5, 15 and 25 HPs per
    aggregate. ``saver`` defaults to FLEX_FIG; pass ``hp_figures.save`` for paper/.
    """
    import matplotlib.pyplot as plt
    import hp_figures as hf
    L = flex_all_normalised() if L is None else L
    # show only bins that at least 10% of the aggregates reach
    cover = L.groupby(['regime', 'bin']).row.transform('nunique')
    L = L[cover >= 0.1 * L.row.nunique()]
    hf.use_style()
    fig, axs = plt.subplots(2, 1, figsize=(hf.COL1, 4.0), sharex=True, gridspec_kw=dict(height_ratios=[1.6, 1]))
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax = axs[0]
    h = L[L.regime == 'heating'].groupby('bin')
    x = h.x.first()
    ax.fill_between(x, h.med.quantile(.25), h.med.quantile(.75), color='0.2', alpha=.3, lw=0)
    ax.plot(x, h.med.median(), color='0.1', lw=1.4)
    ax.fill_between(x, h.est.quantile(.25), h.est.quantile(.75), color=hf.C_HP, alpha=.15, lw=0)
    ax.plot(x, h.est.median(), color=hf.C_HP, ls='--', lw=1.4)
    d = L[L.regime == 'dead band'].groupby('bin')
    ax.plot(d.x.first(), d.med.median(), color='0.5', ls=':', lw=1.2)
    ax.axhline(1, color='0.6', lw=.6)
    ax.set_ylabel('$E_{\\mathrm{flex}}$ / own maximum')
    ax.set_ylim(0, 1.3)
    handles = [(Patch(color='0.2', alpha=.3, lw=0), Line2D([], [], color='0.1', lw=1.4)),
               (Patch(color=hf.C_HP, alpha=.15, lw=0), Line2D([], [], color=hf.C_HP, ls='--', lw=1.4)),
               Line2D([], [], color='0.5', ls=':', lw=1.2)]
    ax.legend(handles, ['actual, median and IQR across aggregates', 'estimate, median and IQR',
                        'actual, $T \\geq T_h$ (not counted)'], fontsize=6, loc='upper right')
    ax = axs[1]
    for nh, c, ls in zip((5, 15, 25), ('#9ecae1', '#4292c6', '#08306b'), (':', '--', '-')):
        g = L[(L.regime == 'heating') & (L.N_hp == nh)].assign(w=lambda v: (v.q75 - v.q25) / v.med).groupby('bin')
        ax.plot(g.x.first(), g.w.median(), color=c, ls=ls, marker='o', ms=2.5, label=f'{nh} HPs')
    ax.set_ylabel('day-to-day IQR\n/ median')
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.legend(fontsize=6, loc='upper left')
    th = float(rebuild_design()[0]['rows'].T_h.median())
    for ax in axs:
        ax.axvline(th, color='0.45', lw=.7, ls=(0, (3, 3)))
    axs[0].annotate('median $T_h$', (th, 0.6), xytext=(3, 0), textcoords='offset points', fontsize=6.5, color='0.3')
    for ax, lab in zip(axs, 'ab'):
        ax.text(-0.22, 1.04, f'({lab})', transform=ax.transAxes, fontsize=8, va='top')
    fig.tight_layout()
    path = (saver or save_fig)(fig, name)
    plt.close(fig)
    return path


def flex_all_diagnostics(N=50, N_hp=25):
    """Two diagnostics for the normalised plot (Alex's questions), on the (N, N_hp) aggregates.

    iqr: per 2 degC bin of heating days, the day-to-day IQR / median of the actual
    F, raw and net of a linear temperature trend within the bin, with the bin's
    temperature span and spring share (Jan-Jun), median over aggregates.
    floor: per bin, the actual and estimated downward headroom per kW of true
    capacity, the aggregate's summer floor (median daily SF on days >= T_h + 2),
    and the estimated / actual ratio with and without the floor, median over
    aggregates.
    """
    Dz, _ = rebuild_design(); D = daily_frames(); G = Dz['rows']; T = D['T']
    days = pd.date_range('2023-01-01', periods=len(T), freq='D')
    edges, _ = temperature_bins(T, MIN_DAYS, FIRM_WIDTH)
    idx = np.clip(np.digitize(T, edges) - 1, 0, len(edges) - 2)
    sel = np.flatnonzero(((G.N == N) & (G.N_hp == N_hp)).to_numpy())
    r1, r2 = [], []
    for i in sel:
        r = G.iloc[i]
        fa = D['fa_h'][i].astype(float); sf_a = D['sf_a'][i].astype(float)
        pd_e = O.sf_target(T, r.T_h, r.m_pilot) * r.cap_est / r.cap
        floor = float(np.median(sf_a[T >= r.T_h + 2]))
        for b in range(len(edges) - 1):
            m = (idx == b) & (T < r.T_h)
            if m.sum() < MIN_DAYS:
                continue
            y, t = fa[m], T[m]
            res = y - np.polyval(np.polyfit(t, y, 1), t) + np.median(y)

            def rel_iqr(v):
                return (np.quantile(v, .75) - np.quantile(v, .25)) / np.median(y)
            r1.append(dict(bin=b, lo=edges[b], hi=edges[b + 1], days=int(m.sum()), T_span=float(t.max() - t.min()),
                           raw=rel_iqr(y), detrended=rel_iqr(res), spring=float((days[m].month <= 6).mean())))
            r2.append(dict(bin=b, x=float(t.mean()), act=float(sf_a[m].mean()), floor=floor,
                           est=float(pd_e[m].mean())))
    iqr = pd.DataFrame(r1).groupby(['bin', 'lo', 'hi']).median()
    fl = pd.DataFrame(r2).groupby('bin').median()
    fl['est/act'] = fl.est / fl.act
    fl['est/(act-floor)'] = fl.est / (fl.act - fl.floor)
    return dict(iqr=iqr, floor=fl)


def step2(rebuild=False):
    """Step 2: long frame, summary against N, bin table, checks, the figure and
    the two D2 diagnostics."""
    L = _cached('step2_rows', step2_rows, rebuild)
    S = step2_summary(L)
    return dict(L=L, summary=S, bins=step2_bins(L), checks=step2_checks(S, L), fig=fig_firm(S, L),
                detrended=step2_detrended(), shoulder=step2_shoulder())

