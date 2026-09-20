# -*- coding: utf-8 -*-
"""Nested aggregation experiment: one substation per aggregation level.

The factorial design of ``hp_design`` answers a different question, and does
so by reusing the same households across hundreds of substations. That is
appropriate for traversing an (N, N_etl) grid, but it makes a poor
demonstration that adding consumers improves the fit, for two reasons: the
substations at successive N are independent draws rather than nested, so a
change between them mixes the effect of adding consumers with the effect of
swapping them; and the replicate count invites a precision claim the
overlapping membership does not support.

This module builds the minimal alternative. One substation per aggregation
level, each a strict superset of the one below it, so the step from N to N+4
is literally the addition of four consumers to a fixed aggregate. There are
no replicates, and none are implied: the result is a single realisation, read
as an illustration of a direction rather than as an estimate of a rate.

Roles are assigned once, before any aggregate is built. Half the pool carries
its heat pump circuit and half has it withheld, which holds ETL penetration
at 50 % across every level and keeps a household's role stable as N grows.
"""

import numpy as np
import pandas as pd

from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

RESOLUTIONS = ['1 h', '4 h', '8 h', '16 h', '24 h']
_RULE = {'1 h': '1h', '4 h': '4h', '8 h': '8h', '16 h': '16h', '24 h': '24h'}


def nested_levels(pool, step=4, penetration=0.5, seed=42):
    """Nested household sets, one per aggregation level.

    Returns a list of (N, members, hp_members) with members[i] a superset of
    members[i-1]. ``hp_members`` are the households contributing their heat
    pump circuit; the remainder contribute only their household circuit.
    """
    rng = np.random.default_rng(seed)
    hh = np.array(pool['households'])
    order = rng.permutation(len(hh))
    n_hp_role = int(round(len(hh) * penetration))
    hp_role = hh[order[:n_hp_role]]
    plain_role = hh[order[n_hp_role:]]

    levels, n = [], step
    while True:
        k = int(round(n * penetration))
        if k > len(hp_role) or (n - k) > len(plain_role):
            break
        members = list(hp_role[:k]) + list(plain_role[:n - k])
        levels.append((n, members, list(hp_role[:k])))
        n += step
    return levels


def nested_levels_flat(households, step=2, start=4, seed=42):
    """Nested household sets for a pool with no ETL/non-ETL split.

    Austin has an air conditioner in every house, so there is no penetration
    to hold fixed and no role to assign: each level is simply the first N of
    one fixed random ordering. Returns [(N, members), ...] with each members
    list a superset of the one below.
    """
    rng = np.random.default_rng(seed)
    order = list(np.array(list(households))[rng.permutation(len(households))])
    return [(n, order[:n]) for n in range(start, len(order) + 1, step)]


def fit_levels_bathtub(daily, levels):
    """Full V-shaped fit of every nested level, both arms free, at daily.

    ``daily`` maps household -> DataFrame with columns T and load, already at
    daily resolution. Unlike the heating-only datasets, Austin needs both arms
    of Equation (1), so ``fit_bathtub_stick`` is used rather than the
    hockey stick. See ``fit_levels_bathtub_multires`` for the resolution
    sweep.
    """
    from hp_common import fit_bathtub_stick

    rows = []
    for n, members in levels:
        agg = None
        for h in members:
            d = daily[h]
            agg = d['load'].copy() if agg is None else agg.add(d['load'],
                                                               fill_value=0)
        T = daily[members[0]]['T']
        d = pd.DataFrame({'T': T, 'y': agg}).dropna()
        base, hs, th, cs, tc, r2 = fit_bathtub_stick(d['T'].to_numpy(),
                                                     d['y'].to_numpy())
        rows.append({'N_total': n, 'base': base, 'heat_slope': hs,
                     'T_heat': th, 'cool_slope': cs, 'T_cool': tc,
                     'r2': r2, 'n_points': len(d)})
    return pd.DataFrame(rows)


def fit_levels_bathtub_multires(sub, temperature, levels,
                                resolutions=RESOLUTIONS):
    """Bathtub fit of every nested level at every averaging window.

    ``sub`` maps household -> a native-resolution consumption Series and
    ``temperature`` is a temperature Series at least as fine as the coarsest
    resolution requested. For every nested aggregate the summed load and the
    temperature are re-averaged to each window in turn, then fitted with both
    arms free. Returns one row per (level, resolution), matching the column
    layout ``fit_levels`` produces for the heating-only datasets, so the two
    can be plotted the same way.
    """
    from hp_common import fit_bathtub_stick

    rows = []
    for n, members in levels:
        agg = None
        for h in members:
            s = sub[h]
            agg = s.copy() if agg is None else agg.add(s, fill_value=0)
        # A common origin for both resamples. The load and temperature come
        # from different files with different start times, so a window that
        # does not tile a day -- 16 h -- would otherwise place their bin edges
        # on different marks and leave no overlap after alignment.
        origin = agg.index.min().floor('D')
        for res in resolutions:
            rule = _RULE[res]
            L = agg.resample(rule, origin=origin).mean()
            T = temperature.resample(rule, origin=origin).mean()
            d = pd.DataFrame({'T': T, 'y': L}).dropna()
            base, hs, th, cs, tc, r2 = fit_bathtub_stick(d['T'].to_numpy(),
                                                         d['y'].to_numpy())
            rows.append({'N_total': n, 'resolution': res, 'base': base,
                         'heat_slope': hs, 'T_heat': th, 'cool_slope': cs,
                         'T_cool': tc, 'r2': r2, 'n_points': len(d)})
    return pd.DataFrame(rows)


def aggregate(pool, members, hp_members):
    """Net load of one substation, as a Series on the pool's own index."""
    idx = {h: i for i, h in enumerate(pool['households'])}
    load = np.zeros(len(pool['index']), dtype=float)
    for h in members:
        load += pool['other_mat'][idx[h]]
    for h in hp_members:
        load += pool['hp_mat'][idx[h]]
    return pd.Series(load, index=pool['index'])


def fit_levels(pool, levels, resolutions=RESOLUTIONS):
    """Hockey-stick fit of every nested level at every resolution."""
    temp = pd.Series(pool['temperature']['WPUQ'], index=pool['index'])
    rows = []
    for n, members, hp_members in levels:
        load = aggregate(pool, members, hp_members)
        for res in resolutions:
            rule = _RULE[res]
            d = pd.DataFrame({'T': temp.resample(rule).mean(),
                              'y': load.resample(rule).mean()}).dropna()
            base, slope, thr, r2 = fit_hockey_stick(
                d['T'].to_numpy(), d['y'].to_numpy(), T_BALANCE_BOUNDS)
            rows.append({'N_total': n, 'N_hp': len(hp_members),
                         'resolution': res, 'base': base, 'slope': slope,
                         'T_threshold': thr, 'r2': r2, 'n_points': len(d)})
    return pd.DataFrame(rows)
