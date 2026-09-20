"""Controlled factorial substation design generator.

Replaces the ad-hoc generator in ``HeatPumpDetection_clean.ipynb`` (which drew
``hp_ratio ~ U(0.1, 1.0)`` and ``size ~ randint(2, 100)`` independently and
sampled households *with* replacement) with a controlled factorial design.

Three defects of the old generator are fixed here:

1a. **Sampling with replacement inflated SF.** A duplicated household is
    perfectly correlated with itself and contributes SF = 1 to the aggregate,
    biasing SF upward with a bias that grows with ``N`` once the pool is
    exhausted -- manufacturing a spurious ``N``-dependence in exactly the
    quantity H1 is about. Households are now drawn **without replacement**.

1b. **Weather-station inconsistency.** HP households came from one weather
    station but non-HP households were drawn globally, so they experienced a
    different temperature than the one the net load is regressed against. All
    members of a substation are now drawn from the **same** station.

1c. **Entangled factors.** ``N_hp`` was the product of two uniforms, so an
    effect could not be attributed to the number of heat pumps vs the number of
    consumers. A factorial grid over ``(N_total, hp_ratio)`` decouples them, and
    ``hp_ratio = 0`` cells are generated as the Type I error control for H1.

Output: ``data/substations_design.pkl``. ``data/substations_data.pkl`` is never
touched -- the modelling notebooks still depend on it.
"""

import os
import pickle
import sys
import warnings

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Design grid
# ---------------------------------------------------------------------------
N_GRID = [5, 10, 20, 50, 100, 200]                 # total consumers
RATIO_GRID = [0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0]  # HP penetration
N_REPS = 40                                          # replicates per cell

# Task 4 (data collapse) grid.
#
# Only 58 households carry a usable non-HP load series (`kWh_received_Other` is
# derived as Total - HeatPump, so it exists only where the heat pump is
# submetered), and the largest weather station holds 27 of them. N_total can
# therefore never exceed 27, and the main grid realises only N in {5, 10, 20}.
#
# That leaves a single (N_total, dt) coincidence -- (5, 1h) ~ (20, 15min) -- so
# the N_total * dt collapse cannot be tested on the main design. Re-spacing N as
# a x2 ladder within the same hard ceiling yields 4 coincident clusters and a
# 6.8x range in N, which is enough to test the law. The penetration grid and
# replicate count are unchanged, so the two designs stay comparable.
N_GRID_COLLAPSE = [4, 8, 16, 27]
COLLAPSE_DESIGN_PATH = 'data/substations_design_collapse.pkl'

START_DATE = '2023-01-01 00:00:00+00:00'
END_DATE = '2023-12-31 23:45:00+00:00'
FREQ = '15min'

DATA_COVERAGE_FRAC = 0.8   # fraction of the year a household/station must cover

POOL_CACHE = 'data/_design_pool_cache.pkl'
DESIGN_PATH = 'data/substations_design.pkl'


# ---------------------------------------------------------------------------
# Stage 1 -- household pool (long-running; cached to disk)
# ---------------------------------------------------------------------------
def build_pool(heapo_obj, cache_path=POOL_CACHE, rebuild=False, verbose=True):
    """Build the aligned household pool.

    The pool is TWO-TIER, which is what makes the factorial grid realisable:

    * ``households`` / ``other_mat`` -- every household with enough
      ``kWh_received_Other`` data. Any of these can serve as a NON-HP member,
      because a non-HP member only ever contributes its non-HP load.
    * ``hp_households`` / ``hp_mat`` / ``hp_peak`` -- the subset that also has
      submetered ``kWh_received_HeatPump``. Only these can serve as HP members.

    Requiring HP submetering of *every* member (as the original ``datarangeDf``
    does) shrinks the pool to the ~57 submetered households and makes every
    ``N_total >= 50`` cell unfillable. Splitting the tiers caps ``N_hp`` by the
    submetered pool while letting ``N_total`` use the full station population.

    Returns a dict with:
        index         -- shared 15-min DatetimeIndex for the study year
        households    -- list of household IDs in other_mat row order
        weather_of    -- Series household_id -> weather_id (all households)
        hp_households -- list of household IDs in hp_mat row order
        hp_peak       -- Series household_id -> individual HP peak (kW)
        hp_mat        -- float32 (n_hp_households, n_timestamps) HP load, kW
        other_mat     -- float32 (n_households, n_timestamps) non-HP load, kW
        temperature   -- dict weather_id -> float32 array on `index`
    Cached because it costs a full pass over every household.
    """
    if os.path.exists(cache_path) and not rebuild:
        if verbose:
            print(f'Loading cached household pool from {cache_path}')
        with open(cache_path, 'rb') as fh:
            return pickle.load(fh)

    index = pd.date_range(start=START_DATE, end=END_DATE, freq=FREQ)
    n_t = len(index)
    min_points = int(n_t * DATA_COVERAGE_FRAC)

    meta = heapo_obj.get_meta_data_overview()
    weather_of_all = meta.set_index('Household_ID')['Weather_ID']
    all_households = heapo_obj.get_all_households()

    # --- weather stations with enough hourly data ---------------------------
    hourly_index = pd.date_range(start=START_DATE, end=END_DATE, freq='h')
    temperature = {}
    for wid in weather_of_all.unique():
        try:
            dfw = heapo_obj.load_weather_data(wid, resolution='hourly')
        except Exception:
            continue
        dfw = dfw[(dfw['Timestamp'] >= pd.to_datetime(START_DATE)) &
                  (dfw['Timestamp'] <= pd.to_datetime(END_DATE))]
        dfw = dfw.dropna(subset=['Temperature_avg_hourly'])
        if len(dfw) <= len(hourly_index) * DATA_COVERAGE_FRAC:
            continue
        temp = (dfw[['Timestamp', 'Temperature_avg_hourly']]
                .set_index('Timestamp')['Temperature_avg_hourly']
                .sort_index()
                .reindex(index.union(dfw['Timestamp']))
                .interpolate(method='time')
                .reindex(index))
        temp = temp.ffill().bfill()
        temperature[wid] = temp.to_numpy(dtype=np.float32)
    if verbose:
        print(f'{len(temperature)} weather stations with >= {DATA_COVERAGE_FRAC:.0%} coverage')

    # --- households: one pass, collecting both pool tiers -------------------
    hp_rows, other_rows, kept, hp_kept, hp_peaks = [], [], [], [], []
    for k, hid in enumerate(all_households):
        wid = weather_of_all.get(hid)
        if wid not in temperature:
            continue
        try:
            df = heapo_obj.load_smart_meter_data(hid, resolution=FREQ)
        except Exception:
            continue
        df = df[(df['Timestamp'] >= pd.to_datetime(START_DATE)) &
                (df['Timestamp'] <= pd.to_datetime(END_DATE))]
        if not len(df):
            continue
        df = df.set_index('Timestamp').sort_index()

        # Tier 1: usable as a NON-HP member (needs only the non-HP load)
        other_ok = df['kWh_received_Other'].notna().sum() > min_points
        if not other_ok:
            continue
        other = (df['kWh_received_Other'] * 4).reindex(index).interpolate(
            method='time').fillna(0.0)          # kWh per 15 min -> kW
        other_rows.append(other.to_numpy(dtype=np.float32))
        kept.append(hid)

        # Tier 2: additionally usable as an HP member (needs HP submetering)
        if df['kWh_received_HeatPump'].notna().sum() > min_points:
            hp = (df['kWh_received_HeatPump'] * 4).reindex(index).interpolate(
                method='time').fillna(0.0)
            hp_rows.append(hp.to_numpy(dtype=np.float32))
            hp_peaks.append(float(np.nanmax(hp.to_numpy())))
            hp_kept.append(hid)

        if verbose and (k + 1) % 200 == 0:
            print(f'  scanned {k + 1}/{len(all_households)} households, '
                  f'kept {len(kept)} ({len(hp_kept)} with HP submetering)')

    # Households whose NON-HP load still contains electric heating. In HEAPO
    # every household owns a heat pump, so a "non-HP member" is synthetic -- its
    # `Other` series with the HP removed. That series still carries an electric
    # water heater where one is installed, which is a temperature-driven load and
    # therefore disqualifies the household as control material.
    ewh_col = 'Survey_DHW_Production_ByElectricWaterHeater'
    if ewh_col in meta.columns:
        ewh = meta.set_index('Household_ID')[ewh_col]
        eheat_kept = [h for h in kept if str(ewh.get(h)) == 'True']
    else:
        eheat_kept = []
    if verbose:
        print(f'{len(eheat_kept)} of {len(kept)} households have an electric water '
              f'heater in their non-HP load')

    pool = {
        'index': index,
        'households': kept,
        'weather_of': weather_of_all.reindex(kept),
        'hp_households': hp_kept,
        'eheat_households': eheat_kept,
        'hp_peak': pd.Series(hp_peaks, index=hp_kept, dtype=float),
        'hp_mat': np.vstack(hp_rows) if hp_rows else np.zeros((0, n_t), np.float32),
        'other_mat': np.vstack(other_rows) if other_rows else np.zeros((0, n_t), np.float32),
        'temperature': temperature,
    }
    if verbose:
        print(f'Pool built: {len(kept)} households usable as consumers, '
              f'{len(hp_kept)} of them with HP submetering, {n_t} timestamps')
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as fh:
        pickle.dump(pool, fh, protocol=4)
    if verbose:
        print(f'Cached pool -> {cache_path}')
    return pool


# ---------------------------------------------------------------------------
# Stage 2 -- factorial design
# ---------------------------------------------------------------------------
def generate_design(pool, n_grid=N_GRID, ratio_grid=RATIO_GRID, n_reps=N_REPS,
                    seed=42, verbose=True, eheat_frac=0.0, hp_grid=None,
                    clean_hp=True, replace=False):
    """Generate the factorial design from a household pool.

    ``hp_grid`` switches the design from a penetration grid to an absolute
    heat-pump-count grid. For each ``N_total`` only the counts satisfying
    ``N_hp <= N_total`` are generated, so the realised ``N_total`` by ``N_hp``
    matrix is lower triangular and completely filled rather than sparse. The
    penetration ratio is still recorded for every substation, so analyses that
    stratify by penetration are unaffected.

    ``eheat_frac`` is the share of the NON-heat-pump members drawn from
    households that have some OTHER electric heating (electric water heater,
    storage or direct heating). Heat pumps are not the only temperature-driven
    electric load, so a control group is only a true control when it contains
    none of them:

    * ``eheat_frac = 0`` -> every non-HP member is free of electric heating, so
      the ``N_hp = 0`` cells are genuine zero-electric-heating controls.
    * ``eheat_frac = 1`` -> all non-HP members have other electric heating,
      which isolates its influence on the same grid.

    Pools that carry no electric-heating metadata (e.g. WPUQ) expose an empty
    ``eheat_households`` and only support ``eheat_frac = 0``.

    ``clean_hp`` decides whether the same exclusion is applied to the HEAT PUMP
    tier. An HP member contributes its non-HP load as well as its heat pump, so
    an electric water heater in that household enters the aggregate exactly as it
    would for any other member. Excluding them is therefore the stricter reading,
    but it is expensive: of the 50 submetered heat pumps on the largest station
    only 21 are themselves free of other electric heating, so ``clean_hp=True``
    caps ``N_hp`` at 21. ``clean_hp=False`` keeps the full heat-pump ladder while
    still drawing every NON-HP member from households with no electric heating,
    which is the relevant condition when the question is what the heat-pump-free
    reference group contains. Ignored when ``eheat_frac`` is None.

    Returns (design_dict, coverage_df).
    """
    rng = np.random.default_rng(seed)
    households = np.asarray(pool['households'])
    weather_of = pool['weather_of']
    hp_peak = pool['hp_peak']
    hp_mat, other_mat = pool['hp_mat'], pool['other_mat']
    row_of = {hid: i for i, hid in enumerate(households)}
    hp_row_of = {hid: i for i, hid in enumerate(pool['hp_households'])}

    # Pools per weather station, split three ways: households with a submetered
    # heat pump, households with some OTHER electric heating, and households
    # with no electric heating at all (the only valid control material).
    station_pool = {wid: np.asarray(grp.index)
                    for wid, grp in weather_of.groupby(weather_of)}
    # A household qualifies as a NON-HP member through its non-HP load series,
    # whether or not it owns a heat pump -- in HEAPO every household does, and
    # the non-HP member is that household's `Other` series with the HP removed.
    # The only disqualifier is OTHER electric heating, which stays in that
    # series. So `clean` is "no other electric heating", NOT "no heat pump", and
    # HP members are drawn from the heat pumps that are themselves clean.
    # eheat_frac=None means "natural prevalence": draw non-HP members from the
    # whole population and let electric heating occur at whatever rate it does
    # in the data. That is the realistic setting for a substation study; the
    # 0/1 settings exist to identify its effect, not to describe reality.
    natural = eheat_frac is None
    eheat_set = set() if natural else set(pool.get('eheat_households', []))
    hp_set = set(pool['hp_households']) - (eheat_set if clean_hp else set())
    clean_set = set(pool['households']) - eheat_set
    station_hp_pool = {w: np.asarray([h for h in v if h in hp_set])
                       for w, v in station_pool.items()}
    station_eheat_pool = {w: np.asarray([h for h in v if h in eheat_set])
                          for w, v in station_pool.items()}
    station_clean_pool = {w: np.asarray([h for h in v if h in clean_set])
                          for w, v in station_pool.items()}
    pool_sizes = pd.Series({w: len(v) for w, v in station_pool.items()}
                           ).sort_values(ascending=False)
    hp_pool_sizes = pd.Series({w: len(v) for w, v in station_hp_pool.items()}
                              ).reindex(pool_sizes.index)
    eheat_pool_sizes = pd.Series({w: len(v) for w, v in station_eheat_pool.items()}
                                 ).reindex(pool_sizes.index)
    clean_pool_sizes = pd.Series({w: len(v) for w, v in station_clean_pool.items()}
                                 ).reindex(pool_sizes.index)
    if verbose:
        print('Household pool per weather station:')
        print(pd.DataFrame({'all': pool_sizes, 'hp_submetered': hp_pool_sizes,
                            'other_electric_heating': eheat_pool_sizes,
                            'no_electric_heating': clean_pool_sizes}).to_string())

    _eheat_all = set(pool.get('eheat_households', []))
    meta_rows, hp_load, total_load, coverage = [], {}, {}, []
    sid = 0
    for n_total in n_grid:
        if hp_grid is not None:
            # triangular: only heat-pump counts that fit inside the substation
            cell_specs = [(h / n_total, int(h)) for h in hp_grid if h <= n_total]
        else:
            cell_specs = [(r, int(round(n_total * r))) for r in ratio_grid]
        for ratio, n_hp in cell_specs:
            filled = 0
            n_rest = n_total - n_hp
            n_eheat = 0 if natural else int(round(n_rest * eheat_frac))
            n_clean = n_rest - n_eheat
            # 1a/1b: one station must supply every member -- N_hp submetered
            # heat pumps, N_eheat with other electric heating, N_clean with none.
            # HP members are themselves drawn from the clean pool, so the clean
            # pool must cover both them and the clean non-HP members.
            eligible = [w for w in pool_sizes.index
                        if hp_pool_sizes[w] >= n_hp
                        and eheat_pool_sizes[w] >= n_eheat
                        and clean_pool_sizes[w] >= n_clean + n_hp]
            if not eligible:
                if int(pool_sizes.max()) < n_total:
                    reason = (f'no weather station has >= {n_total} consumers '
                              f'(max pool = {int(pool_sizes.max())})')
                elif int(hp_pool_sizes.max()) < n_hp:
                    reason = (f'no weather station has >= {n_hp} HP-submetered '
                              f'households (max HP pool = {int(hp_pool_sizes.max())})')
                elif int(eheat_pool_sizes.max()) < n_eheat:
                    reason = (f'no weather station has >= {n_eheat} households with '
                              f'other electric heating '
                              f'(max = {int(eheat_pool_sizes.max())})')
                else:
                    reason = (f'no weather station has >= {n_clean} households free of '
                              f'electric heating (max = {int(clean_pool_sizes.max())})')
                coverage.append({
                    'N_total': n_total, 'hp_ratio': ratio, 'N_hp': n_hp,
                    'N_eheat': n_eheat, 'requested': n_reps, 'filled': 0,
                    'skipped': n_reps, 'reason': reason,
                })
                continue

            for rep in range(n_reps):
                # round-robin over eligible stations keeps replicates balanced
                wid = eligible[rep % len(eligible)]
                if replace:
                    # Decoupled with-replacement draw: the heat pumps and the
                    # base households are two independent samples drawn WITH
                    # replacement, so a household (and its heat pump) may recur
                    # within a substation and the heat-pump count no longer
                    # constrains which base households appear. The base is the
                    # full N_total, drawn independently of the heat pumps, which
                    # decouples "how many houses" from "how many heat pumps".
                    hp_members = rng.choice(station_hp_pool[wid], size=n_hp,
                                            replace=True) if n_hp else np.array([], dtype=object)
                    n_clean_base = n_total - n_eheat
                    eheat_members = rng.choice(station_eheat_pool[wid], size=n_eheat,
                                               replace=True) if n_eheat else np.array([], dtype=object)
                    clean_members = rng.choice(station_clean_pool[wid], size=n_clean_base,
                                               replace=True) if n_clean_base else np.array([], dtype=object)
                    base_parts = [p for p in (clean_members, eheat_members) if len(p)]
                    members = np.concatenate(base_parts) if base_parts else np.array([], dtype=object)
                else:
                    # HP members must come from the submetered tier; the remaining
                    # consumers from the rest of the same station's population.
                    hp_members = rng.choice(station_hp_pool[wid], size=n_hp,
                                            replace=False) if n_hp else np.array([], dtype=object)
                    eheat_members = rng.choice(station_eheat_pool[wid], size=n_eheat,
                                               replace=False) if n_eheat else np.array([], dtype=object)
                    # clean non-HP members must not re-use a household already taken
                    # as an HP member (sampling stays without replacement)
                    clean_avail = np.setdiff1d(station_clean_pool[wid], hp_members)
                    clean_members = rng.choice(clean_avail, size=n_clean,
                                               replace=False) if n_clean else np.array([], dtype=object)
                    parts = [p for p in (hp_members, eheat_members, clean_members) if len(p)]
                    members = np.concatenate(parts) if parts else np.array([], dtype=object)

                rows_all = [row_of[h] for h in members]
                rows_hp = [hp_row_of[h] for h in hp_members]

                hp_series = (hp_mat[rows_hp].sum(axis=0) if rows_hp
                             else np.zeros(hp_mat.shape[1], np.float32))
                total_series = other_mat[rows_all].sum(axis=0) + hp_series

                hp_load[sid] = hp_series.astype(np.float32)
                total_load[sid] = total_series.astype(np.float32)
                meta_rows.append({
                    'substation_id': sid,
                    'N_total': n_total,
                    'N_hp': n_hp,
                    'N_eheat': n_eheat,
                    'N_clean': n_clean,
                    'eheat_frac': eheat_frac,
                    'N_eheat_realised': int(sum(1 for h in members if h in _eheat_all)),
                    'hp_ratio': ratio,
                    'weather_id': wid,
                    'replicate_idx': rep,
                    'pool_size': int(pool_sizes[wid]),
                    'n_distinct_households': int(len(set(members))),
                    'HP_Peak': float(hp_peak.reindex(hp_members).sum()) if n_hp else 0.0,
                    'households': list(members),
                    'hp_households': list(hp_members),
                })
                sid += 1
                filled += 1

            coverage.append({
                'N_total': n_total, 'hp_ratio': ratio, 'N_hp': n_hp,
                'N_eheat': n_eheat, 'requested': n_reps, 'filled': filled,
                'skipped': n_reps - filled,
                'reason': '' if filled == n_reps else 'partial',
            })

    meta_df = pd.DataFrame(meta_rows).set_index('substation_id')
    coverage_df = pd.DataFrame(coverage)

    used = set()
    for hh in meta_df['households']:
        used.update(hh)

    design = {
        'meta': meta_df,
        'hp_load': hp_load,
        'total_load': total_load,
        'temperature': pool['temperature'],
        'index': pool['index'],
        'coverage': coverage_df,
        'pool_sizes': pool_sizes,
        'hp_pool_sizes': hp_pool_sizes,
        'eheat_pool_sizes': eheat_pool_sizes,
        'clean_pool_sizes': clean_pool_sizes,
        'eheat_frac': eheat_frac,
        'clean_hp': clean_hp,
        'n_distinct_households_used': len(used),
        'n_distinct_households_available': len(households),
        'grid': {'N_GRID': list(n_grid), 'RATIO_GRID': list(ratio_grid),
                 'N_REPS': n_reps, 'seed': seed},
    }
    return design, coverage_df


# ---------------------------------------------------------------------------
# Verification report
# ---------------------------------------------------------------------------
def report_design(design):
    """Print the coverage table and the checks required before proceeding."""
    meta, cov = design['meta'], design['coverage']

    print('=' * 72)
    print('COVERAGE TABLE (cells requested / filled / skipped)')
    print('=' * 72)
    print(cov.to_string(index=False))

    tot_req, tot_fill = cov['requested'].sum(), cov['filled'].sum()
    print(f'\nTotal: {tot_fill} / {tot_req} substations generated '
          f'({tot_req - tot_fill} skipped)')
    skipped = cov[cov['skipped'] > 0]
    if len(skipped):
        print('\nSkipped cells and reasons:')
        for _, r in skipped.iterrows():
            print(f"  N_total={r['N_total']:>4} hp_ratio={r['hp_ratio']:<5} "
                  f"-> {r['skipped']} skipped: {r['reason']}")

    print('\n' + '=' * 72)
    print('DECOUPLING CHECK: N_total vs N_hp in the realised design')
    print('=' * 72)
    if len(meta):
        corr = meta['N_total'].corr(meta['N_hp'])
        print(f'Pearson r(N_total, N_hp) = {corr:.3f}   '
              f'(the old design entangled them; the grid spreads N_hp within each N_total)')
        print('\nN_hp values available at each N_total:')
        print(pd.crosstab(meta['N_total'], meta['N_hp']).to_string())

    print('\n' + '=' * 72)
    print('ZERO-PENETRATION CONTROLS (Type I error control for H1)')
    print('=' * 72)
    zero = meta[meta['hp_ratio'] == 0.0]
    print(f'hp_ratio == 0 substations: {len(zero)}')
    if len(zero):
        print(f'  all have N_hp == 0 : {bool((zero["N_hp"] == 0).all())}')
        print(f'  all have HP_Peak == 0 : {bool((zero["HP_Peak"] == 0).all())}')
        print(f'  N_total values present: {sorted(zero["N_total"].unique().tolist())}')

    print('\n' + '=' * 72)
    print('PSEUDO-REPLICATION AUDIT')
    print('=' * 72)
    print(f'Substations generated          : {len(meta)}')
    print(f'Distinct households used       : {design["n_distinct_households_used"]}')
    print(f'Distinct households available  : {design["n_distinct_households_available"]}')
    print('Household pool per weather station (all consumers / HP-submetered):')
    print(pd.DataFrame({'all': design['pool_sizes'],
                        'hp_submetered': design.get('hp_pool_sizes')}).to_string())
    if len(meta):
        print('\nSubstations per weather station:')
        print(meta['weather_id'].value_counts().to_string())
        dup = meta['n_distinct_households'] != meta['N_total']
        print(f'\nSampling-without-replacement check: '
              f'{int((~dup).sum())}/{len(meta)} substations have '
              f'n_distinct_households == N_total '
              f'({"OK" if not dup.any() else "MISMATCH"})')


def save_design(design, path=DESIGN_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as fh:
        pickle.dump(design, fh, protocol=4)
    size_mb = os.path.getsize(path) / 1e6
    print(f'Design written -> {path} ({size_mb:.0f} MB)')


def load_design(path=DESIGN_PATH):
    with open(path, 'rb') as fh:
        return pickle.load(fh)


# ---------------------------------------------------------------------------
# Convenience accessors for the analysis notebooks
# ---------------------------------------------------------------------------
def get_series(design, sid, what):
    """Return a pd.Series for substation `sid`.

    `what` is 'HP_Load', 'Total_Load' or 'Temperature'. Series are rebuilt from
    the stored float32 arrays and the single shared index, so the design file
    does not carry 1 680 copies of the same DatetimeIndex or of the 8 distinct
    temperature series.
    """
    index = design['index']
    if what == 'HP_Load':
        return pd.Series(design['hp_load'][sid], index=index)
    if what == 'Total_Load':
        return pd.Series(design['total_load'][sid], index=index)
    if what == 'Temperature':
        wid = design['meta'].loc[sid, 'weather_id']
        return pd.Series(design['temperature'][wid], index=index)
    raise ValueError(f'unknown series {what!r}')


def main(rebuild_pool=False, n_reps=N_REPS, seed=42,
         n_grid=N_GRID, path=DESIGN_PATH):
    warnings.filterwarnings('ignore')
    sys.path.insert(0, 'src')
    from heapo import HEAPO

    heapo_obj = HEAPO(data_path='data/heapo_data', use_local_time=False,
                      suppress_warning=True)
    pool = build_pool(heapo_obj, rebuild=rebuild_pool)
    design, _ = generate_design(pool, n_grid=n_grid, n_reps=n_reps, seed=seed)
    report_design(design)
    save_design(design, path)
    return design


def main_collapse(rebuild_pool=False, n_reps=N_REPS, seed=42):
    """Generate the Task 4 (data collapse) design on the re-spaced N grid."""
    return main(rebuild_pool=rebuild_pool, n_reps=n_reps, seed=seed,
                n_grid=N_GRID_COLLAPSE, path=COLLAPSE_DESIGN_PATH)


if __name__ == '__main__':
    _reps = (int(sys.argv[sys.argv.index('--reps') + 1])
             if '--reps' in sys.argv else N_REPS)
    if '--collapse' in sys.argv:
        main_collapse(rebuild_pool='--rebuild' in sys.argv, n_reps=_reps)
    else:
        main(rebuild_pool='--rebuild' in sys.argv, n_reps=_reps)
