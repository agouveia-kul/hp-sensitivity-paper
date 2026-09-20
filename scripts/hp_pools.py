"""Household pools for the Swiss and WPUQ datasets.

Both return the same dict structure as ``hp_design.build_pool`` so that
``hp_design.generate_design`` and the H1/H2 test modules work unchanged across
all three datasets:

    index, households, weather_of, hp_households, hp_peak, hp_mat, other_mat,
    temperature

Dataset notes
-------------
**Swiss** (`data/Swiss_dataset`) -- 15-min smart-meter CSVs, one per meter, plus
MeteoSwiss station KLO. Only ``kWh_to_installation`` is recorded, so a household
usable as a NON-HP member is one whose metadata says it has no heat pump
(``1_hp = False``); its whole consumption is then non-HP load. HP members come
from the objects that carry BOTH a dwelling meter and a dedicated ``Heat pump``
meter (paired through ``0_object_id``) -- the only place in this dataset with
submetered HP load, and hence the only source of ``HP_Peak`` ground truth.

**WPUQ** (`data/2019_data_15min.hdf5`) -- German single-family houses, each with
separately metered ``HEATPUMP`` and ``HOUSEHOLD`` groups. Verified independent
(r = -0.04; the HP series is strongly seasonal, the household series is not), so
``HOUSEHOLD`` plays the role of HEAPO's ``kWh_received_Other``.
"""

import os
import pickle

import numpy as np
import pandas as pd

SWISS_DIR = 'data/Swiss_dataset'
SWISS_WEATHER = os.path.join(SWISS_DIR, 'weather_2020-2029.csv')
SWISS_METERS = os.path.join(SWISS_DIR, 'smart_meter_data')
SWISS_CACHE = 'data/_swiss_pool_cache.pkl'

WPUQ_DATA = 'data/2019_data_15min.hdf5'
WPUQ_WEATHER = 'data/2019_weather.hdf5'
WPUQ_CACHE = 'data/_wpuq_pool_cache.pkl'

COVERAGE = 0.90       # fraction of the window a meter must cover

# Every electric-heating flag in the Swiss metadata. A household with ANY of
# these has a temperature-driven electric load and cannot be control material.
ELECTRIC_HEATING_FLAGS_FULL = ('1_ewh', '1_storage_heating', '1_direct_heating',
                               '1_hp-add', '1_hp-wh')

# Only these installation types are households. Common areas, underground
# garages, elevators and feed-in systems are building infrastructure.
DWELLING_TYPES = ('Apartment', 'Single-family house')


# ---------------------------------------------------------------------------
# Swiss
# ---------------------------------------------------------------------------
def _swiss_temperature(index):
    w = pd.read_csv(SWISS_WEATHER, sep=';', low_memory=False)
    ts = pd.to_datetime(w['reference_timestamp'], format='%d.%m.%Y %H:%M', utc=True)
    t = pd.to_numeric(w['tre200h0'], errors='coerce')
    s = pd.Series(t.to_numpy(), index=ts).sort_index().dropna()
    # hourly -> 15 min by time interpolation (as for HEAPO). NOTE: this means the
    # 15-min temperature carries no genuine sub-hourly variation.
    return (s.reindex(s.index.union(index)).interpolate(method='time')
             .reindex(index).ffill().bfill().to_numpy(dtype=np.float32))


def _read_swiss_meter(meter_id, index):
    f = os.path.join(SWISS_METERS, f'{meter_id}.csv')
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f, sep=';', usecols=['timestamp_utc', 'kWh_to_installation'])
    ts = pd.to_datetime(d['timestamp_utc'], utc=True)
    s = pd.Series(pd.to_numeric(d['kWh_to_installation'], errors='coerce').to_numpy(),
                  index=ts).sort_index()
    s = s[~s.index.duplicated()]
    win = s.reindex(index)
    if win.notna().sum() < COVERAGE * len(index):
        return None
    return (win.interpolate(method='time').fillna(0.0) * 4).to_numpy(dtype=np.float32)


def build_pool_swiss(year='2023', cache_path=SWISS_CACHE, rebuild=False,
                     max_non_hp=None, verbose=True):
    """Pool from the Swiss dataset (single weather station: KLO)."""
    if os.path.exists(cache_path) and not rebuild:
        if verbose:
            print(f'loading cached Swiss pool from {cache_path}')
        with open(cache_path, 'rb') as fh:
            return pickle.load(fh)

    index = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:45',
                          freq='15min', tz='UTC')
    meta = pd.read_csv(os.path.join(SWISS_DIR, 'metadata.csv'), sep=';',
                       encoding='utf-8-sig')

    # --- paired objects: dwelling meter + dedicated heat-pump meter ---------
    hp_m = meta[meta['0_installation_type'] == 'Heat pump']
    dwell = meta[meta['0_installation_type'].isin(['Apartment', 'Single-family house'])]
    shared = sorted(set(hp_m['0_object_id'].dropna()) & set(dwell['0_object_id'].dropna()))

    households, other_rows = [], []
    hp_households, hp_rows, hp_peaks = [], [], []
    for obj in shared:
        hm = int(hp_m[hp_m['0_object_id'] == obj]['0_meter_id'].iloc[0])
        dm = int(dwell[dwell['0_object_id'] == obj]['0_meter_id'].iloc[0])
        hp_kw = _read_swiss_meter(hm, index)
        dw_kw = _read_swiss_meter(dm, index)
        if hp_kw is None or dw_kw is None:
            continue
        # household identity is the dwelling meter; its HP is the paired meter
        households.append(dm); other_rows.append(dw_kw)
        hp_households.append(dm); hp_rows.append(hp_kw)
        hp_peaks.append(float(np.nanmax(hp_kw)))
    if verbose:
        print(f'Swiss: {len(hp_households)} submetered HP pairs usable '
              f'(of {len(shared)} paired objects)')

    # --- non-HP dwellings: whole consumption is non-HP load ----------------
    # `dwell` is restricted to Apartment / Single-family house, so common areas,
    # underground garages, elevators and feed-in systems are excluded: they are
    # building infrastructure, not households, and their load has a different
    # temperature signature. Standalone equipment meters (water heater, EV
    # charger) are excluded for the same reason -- the only equipment paired to a
    # dwelling in this dataset is the heat pump, handled above.
    cand = dwell[~dwell['1_hp'].astype(bool)]
    cand = cand[~cand['0_meter_id'].isin(households)]
    ids = cand['0_meter_id'].astype(int).tolist()
    if max_non_hp is not None:
        ids = ids[:max_non_hp]
    for k, mid in enumerate(ids):
        kw = _read_swiss_meter(mid, index)
        if kw is None:
            continue
        households.append(mid); other_rows.append(kw)
        if verbose and (k + 1) % 250 == 0:
            print(f'  scanned {k + 1}/{len(ids)} non-HP dwellings, '
                  f'pool now {len(households)}')

    # households carrying some OTHER electric heating (not the submetered HP):
    # electric water heater, storage heating, direct heating, or an auxiliary /
    # water-heating heat pump. All are temperature-driven, so a household with
    # any of them cannot serve as control material.
    mflag = meta.set_index('0_meter_id')
    sub = mflag.reindex(households)
    is_eheat = sub[list(ELECTRIC_HEATING_FLAGS_FULL)].astype(str).eq('True').any(axis=1)
    eheat_households = [h for h, bad in zip(households, is_eheat) if bool(bad)]

    pool = {
        'index': index,
        'households': households,
        'weather_of': pd.Series('KLO', index=households),
        'hp_households': hp_households,
        'eheat_households': eheat_households,
        'hp_peak': pd.Series(hp_peaks, index=hp_households, dtype=float),
        'hp_mat': np.vstack(hp_rows) if hp_rows else np.zeros((0, len(index)), np.float32),
        'other_mat': np.vstack(other_rows),
        'temperature': {'KLO': _swiss_temperature(index)},
    }
    if verbose:
        print(f'Swiss pool: {len(households)} consumers, '
              f'{len(hp_households)} with submetered HP, {len(index)} timestamps')
    with open(cache_path, 'wb') as fh:
        pickle.dump(pool, fh, protocol=4)
    return pool


ELECTRIC_HEATING_FLAGS = ('1_ewh', '1_storage_heating', '1_direct_heating')


def filter_pool_electric_heating(pool, flags=ELECTRIC_HEATING_FLAGS,
                                 verbose=True):
    """Drop Swiss households that have OTHER electric heating.

    ``1_hp = False`` means "no heat pump", NOT "temperature-insensitive". 18% of
    the Swiss pool has an electric water heater, 3.2% storage heating and 1.5%
    direct heating -- all temperature-driven electric loads that put a genuine
    threshold in the net load. With them included the zero-penetration controls
    reject at 0.694 (vs 0.167 HEAPO / 0.150 WPUQ), and the rate tracks the
    contamination directly (0.258 at 0% contaminated members, 0.836 at 10-25%).

    Removing them makes the control condition mean what the test assumes: no
    temperature-driven electric load at all. Operates on an already-built pool,
    so no meter CSV is re-read.
    """
    meta = pd.read_csv(os.path.join(SWISS_DIR, 'metadata.csv'), sep=';',
                       encoding='utf-8-sig').set_index('0_meter_id')
    hh = list(pool['households'])
    sub = meta.reindex(hh)
    bad = sub[list(flags)].astype(str).eq('True').any(axis=1).to_numpy()
    keep_pos = np.flatnonzero(~bad)
    keep_ids = [hh[i] for i in keep_pos]
    keep_set = set(keep_ids)

    hp_hh = list(pool['hp_households'])
    hp_keep = [h for h in hp_hh if h in keep_set]
    hp_pos = [hp_hh.index(h) for h in hp_keep]

    out = dict(pool)
    out['households'] = keep_ids
    out['other_mat'] = pool['other_mat'][keep_pos]
    out['weather_of'] = pool['weather_of'].reindex(keep_ids)
    out['hp_households'] = hp_keep
    out['hp_mat'] = pool['hp_mat'][hp_pos] if hp_pos else pool['hp_mat'][:0]
    out['hp_peak'] = pool['hp_peak'].reindex(hp_keep)

    if verbose:
        print(f'electric-heating filter: kept {len(keep_ids)} of {len(hh)} consumers '
              f'({len(hh) - len(keep_ids)} dropped)')
        print(f'  submetered HP households: {len(hp_keep)} of {len(hp_hh)} kept')
    return out


COMBINED_CACHE = 'data/_combined_pool_cache.pkl'


def dwelling_groups(pool):
    """Dwelling category per household in the combined pool.

    Swiss households carry an installation type; every HEAPO dwelling in the pool
    is a single-family house. This is the only composition variable present for
    both cohorts.
    """
    meta = pd.read_csv(os.path.join(SWISS_DIR, 'metadata.csv'), sep=';',
                       encoding='utf-8-sig').set_index('0_meter_id')
    itype = meta['0_installation_type']

    def group(h):
        src, ident = h.split(':', 1)
        if src == 'swiss':
            t = itype.get(int(ident))
            if t == 'Apartment':
                return 'apartment'
            if t == 'Single-family house':
                return 'house'
            return 'other'
        return 'house'

    return pd.Series({h: group(h) for h in pool['households']})


def restrict_pool(pool, keep_households=None, keep_hp=None, verbose=True):
    """Sub-pool containing only the given households (and optionally HP subset).

    Used to build clustered-composition arms: restricting the pool and then
    running the unchanged design generator gives substations drawn from within a
    group rather than uniformly across the whole population.
    """
    hh = list(pool['households'])
    keep = list(hh if keep_households is None else keep_households)
    keep_set = set(keep)
    pos = [i for i, h in enumerate(hh) if h in keep_set]
    kept = [hh[i] for i in pos]

    hp_all = list(pool['hp_households'])
    hp_keep = [h for h in hp_all if h in keep_set]
    if keep_hp is not None:
        hp_keep = [h for h in hp_keep if h in set(keep_hp)]
    hp_pos = [hp_all.index(h) for h in hp_keep]

    out = dict(pool)
    out['households'] = kept
    out['other_mat'] = pool['other_mat'][pos]
    out['weather_of'] = pool['weather_of'].reindex(kept)
    out['hp_households'] = hp_keep
    out['hp_mat'] = pool['hp_mat'][hp_pos] if hp_pos else pool['hp_mat'][:0]
    out['hp_peak'] = pool['hp_peak'].reindex(hp_keep)
    out['eheat_households'] = [h for h in pool.get('eheat_households', [])
                               if h in keep_set]
    if verbose:
        print(f'restricted pool: {len(kept)} consumers, {len(hp_keep)} with submetered HP')
    return out


def build_pool_combined(heapo_pool=None, swiss_pool=None,
                        cache_path=COMBINED_CACHE, rebuild=False, verbose=True):
    """Merge the HEAPO and Swiss pools into one.

    Both cover calendar 2023 at 15 min and both are Swiss. HEAPO's weather
    station ``8jB`` is bit-for-bit identical to MeteoSwiss KLO, the station the
    Swiss dataset uses (verified: max |diff| = 0.0000 degC over all 8760 hourly
    values of 2023), so the two cohorts share a station and their households can
    legitimately sit in the same substation. HEAPO's other stations are carried
    through unchanged, and the same-station rule still applies per substation.

    Each dataset keeps the restrictions already imposed on it: >=90% coverage of
    the required series, dwellings only on the Swiss side (no common areas,
    underground garages, elevators or feed-in systems), and submetered heat-pump
    load as the only source of ``HP_Peak`` ground truth.
    """
    import pickle as _pickle

    if os.path.exists(cache_path) and not rebuild:
        if verbose:
            print(f'loading cached combined pool from {cache_path}')
        with open(cache_path, 'rb') as fh:
            return _pickle.load(fh)

    if heapo_pool is None:
        with open('data/_design_pool_cache.pkl', 'rb') as fh:
            heapo_pool = _pickle.load(fh)
    if swiss_pool is None:
        swiss_pool = build_pool_swiss(verbose=False)

    if not heapo_pool['index'].equals(swiss_pool['index']):
        raise ValueError('HEAPO and Swiss pools are on different time indices')
    index = heapo_pool['index']

    # HEAPO 8jB and Swiss KLO are the same physical station -- unify the label so
    # substations may draw from both cohorts.
    def _station(w):
        return 'KLO' if w == '8jB' else w

    # prefix ids so the two id spaces cannot collide
    def _hid(pref, h):
        return f'{pref}:{h}'

    households, weather, other_rows = [], {}, []
    hp_households, hp_rows, hp_peaks, eheat = [], [], [], []

    for pref, pool in (('heapo', heapo_pool), ('swiss', swiss_pool)):
        hp_index = {h: i for i, h in enumerate(pool['hp_households'])}
        eh = set(pool.get('eheat_households', []))
        for i, h in enumerate(pool['households']):
            key = _hid(pref, h)
            households.append(key)
            weather[key] = _station(pool['weather_of'].get(h))
            other_rows.append(pool['other_mat'][i])
            if h in eh:
                eheat.append(key)
            if h in hp_index:
                hp_households.append(key)
                hp_rows.append(pool['hp_mat'][hp_index[h]])
                hp_peaks.append(float(pool['hp_peak'].get(h, np.nan)))

    temperature = dict(swiss_pool['temperature'])           # KLO
    for w, arr in heapo_pool['temperature'].items():
        temperature.setdefault(_station(w), arr)

    pool = {
        'index': index,
        'households': households,
        'weather_of': pd.Series(weather).reindex(households),
        'hp_households': hp_households,
        'eheat_households': eheat,
        'hp_peak': pd.Series(hp_peaks, index=hp_households, dtype=float),
        'hp_mat': np.vstack(hp_rows),
        'other_mat': np.vstack(other_rows),
        'temperature': temperature,
    }
    if verbose:
        wo = pool['weather_of']
        hp_set, eh_set = set(hp_households), set(eheat)
        print(f'combined pool: {len(households)} consumers, '
              f'{len(hp_households)} with submetered HP, {len(eheat)} with other '
              f'electric heating')
        rows = []
        for w, grp in wo.groupby(wo):
            ids = set(grp.index)
            rows.append({'station': w, 'consumers': len(ids),
                         'hp_submetered': len(ids & hp_set),
                         'hp_clean': len(ids & hp_set - eh_set),
                         'clean': len(ids - eh_set)})
        print(pd.DataFrame(rows).sort_values('consumers', ascending=False)
              .to_string(index=False))
    with open(cache_path, 'wb') as fh:
        _pickle.dump(pool, fh, protocol=4)
    return pool


# ---------------------------------------------------------------------------
# WPUQ
# ---------------------------------------------------------------------------
def build_pool_wpuq(data_path=WPUQ_DATA, weather_path=WPUQ_WEATHER,
                    cache_path=WPUQ_CACHE, rebuild=False, verbose=True):
    """Pool from the WPUQ (German) dataset. Every household has a submetered HP."""
    if os.path.exists(cache_path) and not rebuild:
        if verbose:
            print(f'loading cached WPUQ pool from {cache_path}')
        with open(cache_path, 'rb') as fh:
            return pickle.load(fh)

    import h5py

    with h5py.File(weather_path, 'r') as h:
        t = h['WEATHER_SERVICE']['IN']['WEATHER_TEMPERATURE_TOTAL']['table'][:]
    wt = pd.Series(t['TEMPERATURE:TOTAL'],
                   index=pd.to_datetime(t['index'], utc=True)).sort_index()
    wt = wt[~wt.index.duplicated()]

    households, other_rows, hp_households, hp_rows, hp_peaks = [], [], [], [], []
    index = None
    with h5py.File(data_path, 'r') as h:
        for grp in ['NO_PV', 'WITH_PV']:
            if grp not in h:
                continue
            for name in h[grp].keys():
                node = h[grp][name]
                if 'HEATPUMP' not in node or 'HOUSEHOLD' not in node:
                    continue
                hp = node['HEATPUMP']['table'][:]
                hh = node['HOUSEHOLD']['table'][:]
                i_hp = pd.to_datetime(hp['index'], unit='s', utc=True)
                i_hh = pd.to_datetime(hh['index'], unit='s', utc=True)
                s_hp = pd.Series(hp['P_TOT'] / 1000.0, index=i_hp).sort_index()
                s_hh = pd.Series(hh['P_TOT'] / 1000.0, index=i_hh).sort_index()
                s_hp = s_hp[~s_hp.index.duplicated()]
                s_hh = s_hh[~s_hh.index.duplicated()]
                if index is None:
                    index = s_hp.index
                a = s_hp.reindex(index).interpolate(method='time').fillna(0.0)
                b = s_hh.reindex(index).interpolate(method='time').fillna(0.0)
                if a.notna().sum() < COVERAGE * len(index):
                    continue
                households.append(name)
                other_rows.append(b.to_numpy(dtype=np.float32))
                hp_households.append(name)
                hp_rows.append(a.to_numpy(dtype=np.float32))
                hp_peaks.append(float(np.nanmax(a.to_numpy())))

    temp = (wt.reindex(wt.index.union(index)).interpolate(method='time')
              .reindex(index).ffill().bfill().to_numpy(dtype=np.float32))
    pool = {
        'index': index,
        'households': households,
        'weather_of': pd.Series('WPUQ', index=households),
        'hp_households': hp_households,
        'eheat_households': [],     # no appliance metadata in WPUQ
        'hp_peak': pd.Series(hp_peaks, index=hp_households, dtype=float),
        'hp_mat': np.vstack(hp_rows),
        'other_mat': np.vstack(other_rows),
        'temperature': {'WPUQ': temp},
    }
    if verbose:
        print(f'WPUQ pool: {len(households)} households (all with submetered HP), '
              f'{len(index)} timestamps')
        print('  NOTE: WPUQ carries no appliance metadata, so other electric '
              'heating cannot be identified; eheat_households is empty and only '
              'eheat_frac=0 is supported.')
    with open(cache_path, 'wb') as fh:
        pickle.dump(pool, fh, protocol=4)
    return pool
