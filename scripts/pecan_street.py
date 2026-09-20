"""Pecan Street (Dataport) Austin loader -- cooling-arm ground truth.

Not part of the substation design used elsewhere in this notebook. Pecan
Street has no comparable ratio grid: it is a fixed, small pool of AC-
submetered Austin households, used only to check that the hockey-stick
machinery and the summer reversibility test (`hp_analysis.summer_hp_days` /
`summer_cooling_test`) extend to a genuinely cooling-only technology, as a
sanity check on the null result Sections 5.1/5.2 find for the real heat
pumps.

The metadata file covers Pecan Street's whole panel, not just Austin --
Ithaca NY, Detroit, Houston, Boulder and others are in the same file under
the same download, despite the folder name. Every household used here is
filtered on ``city == 'Austin', state == 'Texas'`` explicitly; nothing is
taken on the folder name's word.
"""

import numpy as np
import pandas as pd

DATA_DIR = 'data/15minute_data_austin'
AC_COLS = ['air1', 'air2', 'air3']
NON_CONSUMPTION_COLS = {'dataid', 'local_15min', 'grid', 'solar', 'solar2',
                        'leg1v', 'leg2v'}
# A residential circuit averaging this much power over 15 minutes is a
# sensor fault, not real consumption.
MAX_PLAUSIBLE_CIRCUIT_KW = 30
MIN_CORR_VS_METER = 0.9


def load_austin_temperature(path=f'{DATA_DIR}/open-meteo-30.27N97.75W157m.csv',
                            resample='D'):
    """Temperature (degC), Open-Meteo hourly, UTC -> US/Central.

    ``resample`` is a pandas offset alias applied to the hourly series; the
    default 'D' gives the daily mean used everywhere the fit is daily. Pass
    'h' to keep the native hourly series for a sub-daily study, and note the
    source is hourly, so 1~h is the finest resolution it can support.
    """
    t = pd.read_csv(path, skiprows=3)
    t.columns = ['time', 'T']
    t['time'] = (pd.to_datetime(t['time']).dt.tz_localize('UTC')
                .dt.tz_convert('US/Central'))
    s = t.set_index('time')['T']
    return s.resample(resample).mean() if resample else s


def circuit_daily_aggregate(dataids, cols, data_dir=DATA_DIR):
    """Daily-mean sum of the given circuit columns, across the given
    households -- for checking one HVAC-related circuit's own seasonal
    behaviour (e.g. ``air1`` alone) against the whole-home aggregate.
    """
    chunks = []
    for chunk in pd.read_csv(f'{data_dir}/15minute_data_austin.csv',
                             usecols=['dataid', 'local_15min'] + cols,
                             chunksize=500_000):
        chunks.append(chunk[chunk.dataid.isin(dataids)])
    df = pd.concat(chunks, ignore_index=True)
    df['local_15min'] = (pd.to_datetime(df['local_15min'], utc=True)
                         .dt.tz_convert('US/Central'))
    df['value'] = df[[c for c in cols if c in df.columns]].sum(axis=1, min_count=1)

    total = None
    for _, g in df.groupby('dataid'):
        daily = g.set_index('local_15min')['value'].resample('D').mean()
        total = daily.copy() if total is None else total.add(daily, fill_value=0)
    return total


def load_austin_ac_pool(data_dir=DATA_DIR, verbose=True):
    """Daily (T, consumption) pairs for every usable Austin AC household.

    ``consumption`` sums every appliance/circuit column EXCEPT ``grid`` and
    ``solar``/``solar2``, so PV feed-in cannot net the reconstructed load
    negative -- ``grid`` alone is net import and goes negative under a home's
    own PV on sunny days, which a temperature-load fit cannot use directly.

    A household is dropped if its city/state is not exactly Austin, Texas;
    if it has no real ``air1``/``air2``/``air3`` data despite the metadata
    flag; if any individual circuit averages an implausible power over 15
    minutes (a sensor fault, not real consumption); or if the reconstructed
    total correlates below 0.9 with the whole-home meter (``grid + solar``),
    the QC check the reconstruction is measured against.

    Returns (daily, qc): ``daily`` maps dataid -> DataFrame with columns
    ``T`` and ``load``; ``qc`` is the per-household QC table, including
    dropped households, so the exclusions are inspectable rather than
    silent.
    """
    meta = pd.read_csv(f'{data_dir}/metadata.csv', skiprows=[1])
    meta['dataid'] = pd.to_numeric(meta['dataid'], errors='coerce')
    meta = meta.dropna(subset=['dataid'])
    meta['dataid'] = meta['dataid'].astype(int)
    austin_ac = meta[(meta.city == 'Austin') & (meta.state == 'Texas') &
                     meta[AC_COLS].eq('yes').any(axis=1)]
    candidate_ids = set(austin_ac.dataid)

    all_cols = pd.read_csv(f'{data_dir}/15minute_data_austin.csv', nrows=0).columns.tolist()
    consumption_cols = [c for c in all_cols if c not in NON_CONSUMPTION_COLS]

    chunks = []
    for chunk in pd.read_csv(f'{data_dir}/15minute_data_austin.csv', chunksize=500_000):
        chunks.append(chunk[chunk.dataid.isin(candidate_ids)])
    df = pd.concat(chunks, ignore_index=True)
    df['local_15min'] = (pd.to_datetime(df['local_15min'], utc=True)
                         .dt.tz_convert('US/Central'))
    df['consumption'] = df[consumption_cols].sum(axis=1, min_count=1)
    df['meter_ref'] = df[['grid', 'solar', 'solar2']].sum(axis=1, min_count=1)
    temperature = load_austin_temperature(f'{data_dir}/open-meteo-30.27N97.75W157m.csv')

    qc_rows, daily = [], {}
    for hid, g in df.groupby('dataid'):
        max_circuit = g[consumption_cols].max().max()
        n_air = g[[c for c in AC_COLS if c in g.columns]].notna().any(axis=1).sum()
        corr = g[['consumption', 'meter_ref']].corr().iloc[0, 1]
        ok = (n_air > 0 and max_circuit <= MAX_PLAUSIBLE_CIRCUIT_KW and
             corr >= MIN_CORR_VS_METER)
        qc_rows.append({'dataid': hid, 'n_points': len(g), 'n_air_points': n_air,
                        'max_circuit_kw': max_circuit, 'corr_vs_meter': corr,
                        'usable': ok})
        if ok:
            daily[hid] = pd.DataFrame({
                'T': temperature,
                'load': g.set_index('local_15min')['consumption'].resample('D').mean(),
            }).dropna()

    qc = pd.DataFrame(qc_rows).sort_values('corr_vs_meter')
    if verbose:
        n_bad = (~qc.usable).sum()
        print(f'{len(qc)} Austin, Texas households flagged for AC in metadata; '
              f'{len(qc) - n_bad} usable after QC ({n_bad} dropped)')
    return daily, qc


def load_austin_ac_subdaily(data_dir=DATA_DIR, verbose=True):
    """Native 15-minute consumption per household, plus hourly temperature.

    The same households and the same QC as ``load_austin_ac_pool``, but the
    consumption is returned at its native 15-minute resolution rather than
    collapsed to daily, so an aggregate can be re-averaged at several windows
    for a resolution study. Returns (sub, temperature_hourly, qc), with
    ``sub`` mapping dataid -> a 15-minute consumption Series.
    """
    meta = pd.read_csv(f'{data_dir}/metadata.csv', skiprows=[1])
    meta['dataid'] = pd.to_numeric(meta['dataid'], errors='coerce')
    meta = meta.dropna(subset=['dataid'])
    meta['dataid'] = meta['dataid'].astype(int)
    austin_ac = meta[(meta.city == 'Austin') & (meta.state == 'Texas') &
                     meta[AC_COLS].eq('yes').any(axis=1)]
    candidate_ids = set(austin_ac.dataid)

    all_cols = pd.read_csv(f'{data_dir}/15minute_data_austin.csv',
                           nrows=0).columns.tolist()
    consumption_cols = [c for c in all_cols if c not in NON_CONSUMPTION_COLS]

    chunks = []
    for chunk in pd.read_csv(f'{data_dir}/15minute_data_austin.csv',
                             chunksize=500_000):
        chunks.append(chunk[chunk.dataid.isin(candidate_ids)])
    df = pd.concat(chunks, ignore_index=True)
    df['local_15min'] = (pd.to_datetime(df['local_15min'], utc=True)
                         .dt.tz_convert('US/Central'))
    df['consumption'] = df[consumption_cols].sum(axis=1, min_count=1)
    df['meter_ref'] = df[['grid', 'solar', 'solar2']].sum(axis=1, min_count=1)

    qc_rows, sub = [], {}
    for hid, g in df.groupby('dataid'):
        max_circuit = g[consumption_cols].max().max()
        n_air = g[[c for c in AC_COLS if c in g.columns]].notna().any(axis=1).sum()
        corr = g[['consumption', 'meter_ref']].corr().iloc[0, 1]
        ok = (n_air > 0 and max_circuit <= MAX_PLAUSIBLE_CIRCUIT_KW and
              corr >= MIN_CORR_VS_METER)
        qc_rows.append({'dataid': hid, 'n_points': len(g), 'n_air_points': n_air,
                        'max_circuit_kw': max_circuit, 'corr_vs_meter': corr,
                        'usable': ok})
        if ok:
            sub[hid] = (g.set_index('local_15min')['consumption'].sort_index())

    temperature = load_austin_temperature(
        f'{data_dir}/open-meteo-30.27N97.75W157m.csv', resample='h')
    qc = pd.DataFrame(qc_rows).sort_values('corr_vs_meter')
    if verbose:
        n_bad = (~qc.usable).sum()
        print(f'{len(qc)} Austin, Texas households; {len(qc) - n_bad} usable '
              f'after QC, kept at 15-minute resolution')
    return sub, temperature, qc
