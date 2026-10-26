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
