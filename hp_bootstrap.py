"""Household-level bootstrap for the detection statistic.

Why this exists
---------------
The design draws 1500 substations, but they are built from 1384 households of
which only 77 carry a submetered heat pump, and each of those 77 appears in
about 250 substations. Resampling SUBSTATIONS therefore answers "what if I had
redrawn substations from these same 77 heat pumps?", which is nearly a no-op
and gives a confidence interval roughly four times too narrow. The question the
paper actually needs is "what if I had been given a different set of heat pump
households?", and only resampling HOUSEHOLDS answers it.

A delete-one-household jackknife is the cheap approximation, but the clusters
here are badly unbalanced -- dropping one household removes anywhere from 10 to
403 substations, depending on how large its weather station is -- so the
jackknife mostly measures how much got deleted. This module does the honest
version: resample households with replacement, redraw the design, refit.

What is resampled
-----------------
Households are resampled WITH replacement, stratified by (weather station,
has-heat-pump, free-of-other-electric-heating). Stratifying keeps every pool
size fixed, so the design realises exactly the same grid in every replicate and
the resulting spread reflects household identity rather than a design that
changed shape. Station membership is held fixed for the same reason: with only
three stations, resampling them would swamp the estimate.

Because the resample is with replacement, one household can occupy several
slots and a substation may draw more than one of them. That is the intended
bootstrap semantics, not a bug: the resampled population genuinely contains
that household more than once.

Speed
-----
``hp_analysis.fit_all`` fits five resolutions and two responses per substation.
Detection uses one number, the 24 h Load fit, so this module aggregates the
pool to daily means ONCE and then rebuilds each substation as a sum of daily
rows. ``validate_against_fits`` checks that path reproduces the stored fits.
"""
import numpy as np
import pandas as pd

from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

MIN_POINTS = 30


# ---------------------------------------------------------------------------
# Daily pre-aggregation
# ---------------------------------------------------------------------------
def _daily_mean(mat, day_code, n_days):
    """Row-wise daily mean of a (households x timesteps) matrix.

    NaNs are skipped per day, matching ``Series.resample('D').mean()``.
    """
    mat = np.asarray(mat, dtype=np.float64)
    ok = np.isfinite(mat)
    filled = np.where(ok, mat, 0.0)
    out = np.zeros((mat.shape[0], n_days))
    cnt = np.zeros((mat.shape[0], n_days))
    for d in range(n_days):
        sel = day_code == d
        out[:, d] = filled[:, sel].sum(axis=1)
        cnt[:, d] = ok[:, sel].sum(axis=1)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(cnt > 0, out / np.maximum(cnt, 1), np.nan)


def prepare(pool):
    """Collapse a pool to daily means and index it for fast substation rebuilds."""
    index = pool['index']
    days = pd.DatetimeIndex(index).normalize()
    day_code, day_uniq = pd.factorize(days, sort=True)
    n_days = len(day_uniq)

    households = list(pool['households'])
    hp_households = list(pool['hp_households'])
    row_of = {h: i for i, h in enumerate(households)}
    hp_row_of = {h: i for i, h in enumerate(hp_households)}

    other_daily = _daily_mean(pool['other_mat'], day_code, n_days)
    hp_daily = _daily_mean(pool['hp_mat'], day_code, n_days)
    temp_daily = {w: _daily_mean(np.asarray(v)[None, :], day_code, n_days)[0]
                  for w, v in pool['temperature'].items()}

    weather_of = pool['weather_of']
    eheat = set(pool.get('eheat_households', []))
    return {
        'households': households, 'hp_households': hp_households,
        'row_of': row_of, 'hp_row_of': hp_row_of,
        'other_daily': other_daily, 'hp_daily': hp_daily,
        'temp_daily': temp_daily, 'n_days': n_days,
        'weather_of': weather_of, 'eheat': eheat,
        'hp_peak': pool['hp_peak'],
    }


# ---------------------------------------------------------------------------
# One substation, one fit
# ---------------------------------------------------------------------------
def _fit_one(prep, rows_all, rows_hp, wid):
    """24 h Load hockey stick for a substation given member row indices."""
    load = prep['other_daily'][rows_all].sum(axis=0)
    if len(rows_hp):
        load = load + prep['hp_daily'][rows_hp].sum(axis=0)
    t = prep['temp_daily'][wid]
    ok = np.isfinite(t) & np.isfinite(load)
    if ok.sum() < MIN_POINTS or len(np.unique(t[ok])) < 3:
        return None
    try:
        b, s, tb, r2 = fit_hockey_stick(t[ok], load[ok], T_BALANCE_BOUNDS)
    except Exception:
        return None
    peak = float(np.nanmax(load))
    if not np.isfinite(peak) or peak <= 0:
        return None
    return {'base': b, 'slope': s, 'T_threshold': tb, 'r2': r2,
            'peak_load': peak, 'slope_per_peak': s / peak}


def validate_against_fits(pool, design, fits, atol=1e-6):
    """Recompute slope_per_peak for the STORED design and compare.

    Confirms the daily-aggregation shortcut reproduces ``hp_analysis.fit_all``
    before any bootstrap result is trusted.
    """
    prep = prepare(pool)
    meta = design['meta']
    ref = fits[(fits.response == 'Load') & (fits.resolution == '24 h') &
               (~fits.failed)].set_index('substation_id')
    rows = []
    for sid in ref.index:
        m = meta.loc[sid]
        rows_all = [prep['row_of'][h] for h in m['households']]
        rows_hp = [prep['hp_row_of'][h] for h in m['hp_households']]
        got = _fit_one(prep, rows_all, rows_hp, m['weather_id'])
        if got is None:
            continue
        rows.append({'substation_id': sid, 'mine': got['slope_per_peak'],
                     'stored': ref.loc[sid, 'slope_per_peak']})
    cmp = pd.DataFrame(rows)
    cmp['abs_err'] = (cmp['mine'] - cmp['stored']).abs()
    cmp['rel_err'] = cmp['abs_err'] / cmp['stored'].abs()
    return cmp


# ---------------------------------------------------------------------------
# The bootstrap
# ---------------------------------------------------------------------------
def _strata(prep):
    """Household ids grouped by (weather station, has-HP, is-clean)."""
    weather_of = prep['weather_of']
    eheat, hp_set = prep['eheat'], set(prep['hp_households'])
    out = {}
    for wid, grp in weather_of.groupby(weather_of):
        for h in grp.index:
            key = (wid, h in hp_set, h not in eheat)
            out.setdefault(key, []).append(h)
    return {k: np.asarray(v, dtype=object) for k, v in out.items()}


def _station_slots(slots, prep):
    """Per-station slot arrays carrying INTEGER identity.

    A bootstrap resample repeats household ids, so ids cannot identify a member
    -- two copies of one household are two distinct slots that a substation may
    legitimately draw both of. Slot indices are unique by construction, which
    also lets ``setdiff1d`` exclude the exact copies taken as heat pump members
    while leaving that household's other copies available.
    """
    row_of, hp_row_of = prep['row_of'], prep['hp_row_of']
    out = {}
    for wid in sorted({w for (w, _, _) in slots}):
        hh, is_hp, is_clean = [], [], []
        for (w, hp, clean), arr in slots.items():
            if w != wid:
                continue
            hh.extend(arr.tolist())
            is_hp.extend([hp] * len(arr))
            is_clean.extend([clean] * len(arr))
        is_hp = np.asarray(is_hp, dtype=bool)
        out[wid] = {
            'n': len(hh),
            'hp': np.flatnonzero(is_hp),
            'clean': np.flatnonzero(np.asarray(is_clean, dtype=bool)),
            'row': np.asarray([row_of[h] for h in hh], dtype=np.int64),
            'hprow': np.asarray([hp_row_of[h] if p else -1
                                 for h, p in zip(hh, is_hp)], dtype=np.int64),
        }
    return out


def _auc(slope_per_peak, is_pos):
    pos, neg = slope_per_peak[is_pos], slope_per_peak[~is_pos]
    if not len(pos) or not len(neg):
        return np.nan
    r = pd.Series(np.concatenate([pos, neg])).rank().to_numpy()
    return (r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def _draw_and_fit(prep, station, n_grid, ratio_grid, n_reps, rng):
    """Redraw the whole design over a resampled slot population and fit it.

    Mirrors ``hp_design.generate_design`` at ``eheat_frac=0, clean_hp=False``:
    one weather station supplies every member, heat pump members come from the
    submetered tier, and the remaining members are drawn from that station's
    households free of other electric heating, excluding the slots already
    taken as heat pump members.
    """
    sizes = pd.Series({w: s['n'] for w, s in station.items()}
                      ).sort_values(ascending=False)
    empty = np.array([], dtype=np.int64)

    spp, is_pos = [], []
    for n_total in n_grid:
        for ratio in ratio_grid:
            n_hp = int(round(n_total * ratio))
            n_clean = n_total - n_hp
            eligible = [w for w in sizes.index
                        if len(station[w]['hp']) >= n_hp
                        and len(station[w]['clean']) >= n_clean + n_hp]
            if not eligible:
                continue
            for rep in range(n_reps):
                st = station[eligible[rep % len(eligible)]]
                hp_members = (rng.choice(st['hp'], size=n_hp, replace=False)
                              if n_hp else empty)
                avail = np.setdiff1d(st['clean'], hp_members)
                clean_members = (rng.choice(avail, size=n_clean, replace=False)
                                 if n_clean else empty)
                members = np.concatenate([hp_members, clean_members])
                got = _fit_one(prep, st['row'][members],
                               st['hprow'][hp_members],
                               eligible[rep % len(eligible)])
                if got is None:
                    continue
                spp.append(got['slope_per_peak'])
                is_pos.append(n_hp > 0)
    return np.asarray(spp), np.asarray(is_pos, dtype=bool)


def household_bootstrap(pool, n_grid, ratio_grid, n_reps=25, B=200, seed=0,
                        draw_seed=42, verbose=True):
    """AUC under repeated household resampling.

    Returns a DataFrame with one row per bootstrap replicate. ``draw_seed`` is
    held fixed across replicates so the substation draw contributes as little
    extra noise as possible and the spread reflects household identity.
    """
    prep = prepare(pool)
    strata = _strata(prep)
    rng_boot = np.random.default_rng(seed)

    rows = []
    for b in range(B):
        if b == 0:
            slots = strata                      # replicate 0 = the real pool
        else:
            slots = {k: rng_boot.choice(v, size=len(v), replace=True)
                     for k, v in strata.items()}
        spp, is_pos = _draw_and_fit(prep, _station_slots(slots, prep),
                                    n_grid, ratio_grid, n_reps,
                                    np.random.default_rng(draw_seed))
        rows.append({'replicate': b, 'auc': _auc(spp, is_pos),
                     'n_substations': len(spp)})
        if verbose and (b + 1) % 10 == 0:
            print(f'  {b + 1}/{B} bootstrap replicates', flush=True)
    return pd.DataFrame(rows)


def summarise(boot, point=None, level=95):
    """Percentile interval from the bootstrap replicates (replicate 0 excluded)."""
    v = boot.loc[boot.replicate > 0, 'auc'].dropna().to_numpy()
    a = (100 - level) / 2
    lo, hi = np.percentile(v, [a, 100 - a])
    point = float(boot.loc[boot.replicate == 0, 'auc'].iloc[0]) if point is None else point
    return {'point': point, 'lo': float(lo), 'hi': float(hi),
            'se': float(v.std(ddof=1)), 'B': len(v), 'level': level}
