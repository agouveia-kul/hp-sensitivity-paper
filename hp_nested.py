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
