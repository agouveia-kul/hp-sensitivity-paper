# -*- coding: utf-8 -*-
"""Planning use case for the capacity estimate (experiments, not in the paper yet).

One function per step of the planning experiments, called from
``planning_use_case.ipynb``. Intermediate results are pickled under ``PLAN_WORK``
(gitignored ``results/planning``); figures go to ``PLAN_FIG`` as PDF and PNG.
The paper's own caches in ``data/`` and artifacts in ``paper/`` are never written.

Step 0 rebuilds the published 20-split Kloten design from the cached pools with
the generators of ``outputs`` and checks the draft's numbers against tolerances.
"""
import os
import pickle

import numpy as np
import pandas as pd

import hp_figures as hf
import outputs as O
import utils as U
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

PLAN_WORK = os.path.join('results', 'planning')     # pickles (gitignored)
PLAN_FIG = os.path.join('figures', 'planning')      # PDF + PNG of every figure

PEN_BINS = [0, .15, .35, .65, 1.0]                  # Table IV penetration bins N_hp / N


def _pkl(name):
    os.makedirs(PLAN_WORK, exist_ok=True)
    return os.path.join(PLAN_WORK, name + '.pkl')


def _cached(name, build, rebuild=False):
    """Load ``name`` from PLAN_WORK, or build and save it."""
    path = _pkl(name)
    if os.path.exists(path) and not rebuild:
        with open(path, 'rb') as fh:
            return pickle.load(fh)
    out = build()
    with open(path, 'wb') as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def save_fig(fig, name):
    os.makedirs(PLAN_FIG, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(PLAN_FIG, f'{name}.{ext}'), dpi=300)
    return os.path.join(PLAN_FIG, name)


def wape_by_bin(G, est, act='cap'):
    """WAPE overall and per penetration bin of Table IV."""
    bins = pd.cut(G.N_hp / G.N, PEN_BINS)
    return [O._wape(G[est], G[act])] + [O._wape(g[est], g[act]) for _, g in G.groupby(bins, observed=True)]


# ===========================================================================
# Step 0 -- reproduce the baseline
# ===========================================================================
TARGETS = {  # draft value, tolerance
    'wape_i': (19.3, .5), 'wape_i_le15': (57.5, .5), 'wape_i_15_35': (26.3, .5),
    'wape_i_35_65': (17.0, .5), 'wape_i_gt65': (14.2, .5),
    'wape_ii': (14.5, .5), 'wape_iv': (21.1, .5),
    'median_over_pct': (16.0, .5), 'mae_kw': (17.0, .5), 'mean_hp_kw': (6.3, .05),
    'fig8_slope': (0.0202, .0005), 'fig8_r': (0.97, .005),
    'pilot_m_median': (0.018, .0005), 'pilot_m_q25': (0.017, .0005), 'pilot_m_q75': (0.019, .0005),
    'zero_hp_kw_per_hh': (0.28, .005),
    'sf15_peak_coldest': (0.56, .005), 'sf15_peak_year': (0.59, .005), 'p2m_coldest': (1.28, .005),
    'real_Hg': (2.0, 1.0), 'real_MqO': (-6.0, 1.0), 'real_Hamelin': (-9.0, 1.0),
}


def rebuild_kloten_design(rebuild=False):
    """The published 1260-aggregate design, rebuilt from the pools into PLAN_WORK.

    Runs ``outputs._kloten_design`` (seed 0, 20 splits, 3 reps, target aggregates
    drawn from all 1307 HP-free households) with its cache path redirected, so the
    paper's ``data/_kloten_design.pkl`` is read only for comparison.
    """
    path = _pkl('step0_kloten_design')
    old = O.KLOTEN_DESIGN
    O.KLOTEN_DESIGN = path
    try:
        return O._kloten_design(rebuild=rebuild or not os.path.exists(path))
    finally:
        O.KLOTEN_DESIGN = old


def _zero_hp_control(n_reps=50, seed=0):
    """Part (2) of ``outputs.sf_controls``: spurious capacity per HP-free household.

    ``sf_controls`` draws part (1) first from the same generator, so the full
    function is run and only its zero-HP frame kept.
    """
    _, Z = O.sf_controls(n_splits=120, n_reps=n_reps, seed=seed)
    return Z


def _sf15_kloten():
    """15-min SF of the 50 Kloten HPs: peak on the coldest day, over the year, and
    the coldest day's 15-min peak over its daily mean."""
    import hp_pools as hpp
    from hp_capacity import robust_series_peak
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']
    hrows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == 'KLO']
    cap = sum(robust_series_peak(p['hp_mat'][i]) for i in hrows)
    sf = pd.Series(p['hp_mat'][hrows].sum(0) / cap, index=p['index'])
    Td = pd.Series(p['temperature']['KLO'], index=p['index']).resample('D').mean()
    day = Td.idxmin()
    on = sf[sf.index.normalize() == day]
    dmax = sf.resample('D').max(); dmean = sf.resample('D').mean()
    heat = Td < 16.55                                   # median heating day: below the pilot T_h
    return dict(n_hp=len(hrows), coldest_day=str(day.date()), T_coldest=float(Td.min()),
                sf15_peak_coldest=float(on.max()), sf15_peak_year=float(sf.max()),
                p2m_coldest=float(on.max() / on.mean()),
                p2m_median_heating=float((dmax[heat] / dmean[heat]).median()))


def reproduce_baseline(rebuild=False):
    """Step 0: every draft number of the prompt's section 1, against its tolerance.

    Returns (checks, extras): a frame with draft value, reproduced value, tolerance
    and pass flag, and a dict of the underlying objects.
    """
    Dz = rebuild_kloten_design(rebuild)
    G = Dz['rows'].copy(); Tmin = float(Dz['T'].min())
    with open(O.KLOTEN_DESIGN, 'rb') as fh:                         # the paper's cache
        G_paper = pickle.load(fh)['rows']
    same = (len(G) == len(G_paper)
            and np.allclose(G[['cap', 's_h', 'T_h', 'cap_est', 'cap_or']].to_numpy(),
                            G_paper[['cap', 's_h', 'T_h', 'cap_est', 'cap_or']].to_numpy()))

    G['cap_plan'] = G.s_h * (G.T_h - Tmin) / O.SF_PLAN
    wi, wii, wiv = wape_by_bin(G, 'cap_est'), wape_by_bin(G, 'cap_or'), wape_by_bin(G, 'cap_plan')
    x, y = G.cap.to_numpy(), G.s_h.to_numpy()
    pm = pd.Series([p['m'] for p in Dz['pilots']])
    K = Dz['K']

    Z = _cached('step0_zero_hp', _zero_hp_control, rebuild)
    sf15 = _cached('step0_sf15', _sf15_kloten, rebuild)
    R = _cached('step0_tab_real', _tab_real_quiet, rebuild)
    real = dict(zip(R['agg'], R['err']))

    got = {'wape_i': wi[0], 'wape_i_le15': wi[1], 'wape_i_15_35': wi[2], 'wape_i_35_65': wi[3],
           'wape_i_gt65': wi[4], 'wape_ii': wii[0], 'wape_iv': wiv[0],
           'median_over_pct': (np.median(G.cap_est / G.cap) - 1) * 100,
           'mae_kw': float(np.mean(np.abs(G.cap_est - G.cap))), 'mean_hp_kw': float(K['cap'].mean()),
           'fig8_slope': float(np.sum(x * y) / np.sum(x * x)), 'fig8_r': float(np.corrcoef(x, y)[0, 1]),
           'pilot_m_median': pm.median(), 'pilot_m_q25': pm.quantile(.25), 'pilot_m_q75': pm.quantile(.75),
           'zero_hp_kw_per_hh': float(Z.per_house.median()),
           'sf15_peak_coldest': sf15['sf15_peak_coldest'], 'sf15_peak_year': sf15['sf15_peak_year'],
           'p2m_coldest': sf15['p2m_coldest'],
           'real_Hg': real['Hg, CH'], 'real_MqO': real['MqO, CH'], 'real_Hamelin': real['Hamelin, DE']}
    rows = []
    for k, (target, tol) in TARGETS.items():
        v = got[k]
        # the draft rounds: a value matches when it rounds to the draft figure, or lies within tol
        rows.append(dict(quantity=k, draft=target, reproduced=v, tol=tol, ok=abs(v - target) <= tol))
    checks = pd.DataFrame(rows)
    extras = dict(G=G, pilots=Dz['pilots'], Z=Z, sf15=sf15, real=R, same_as_paper_cache=same,
                  wape=dict(i=wi, ii=wii, iv=wiv), n_free=int(K['free'].shape[0]), n_hp=int(len(K['cap'])))
    return checks, extras


def _tab_real_quiet():
    """``outputs.tab_real`` with its .tex redirected to PLAN_WORK (the frame is what is kept)."""
    old = O.TABDIR
    O.TABDIR = PLAN_WORK
    try:
        return O.tab_real()
    finally:
        O.TABDIR = old
