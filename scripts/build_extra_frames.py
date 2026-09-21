# -*- coding: utf-8 -*-
"""Rebuild the two extra cross-dataset rows from their raw sources and add them
to scratchpad/cross_frames.pkl, in the same schema as the other cross entries
(dict(n, T, net, heat, cool, cap_h, cap_c)).

Both raw datasets are downloaded separately (see DATA.md) and live under data/
(gitignored). The fitted frames themselves are small and are cached in
scratchpad/cross_frames.pkl, so this script only needs to run when rebuilding
from raw.

Rows produced
-------------
- ``COFACTOR Norway (real HP)`` : Oslo/Bærum electric-heated apartment blocks,
  net = ElImp (whole-building), ETL = heating-system electricity, T = Tout.
  Source: Sørensen et al. 2026, Data in Brief, CC BY 4.0 (DOI 10.60609/3ab7-ez93).
  Expected raw: data/cofactor_ds1/building_*.txt
- ``Carleton Ottawa (real AC)`` : Ottawa 12-house cooling arm, net = Main,
  cooling ETL = AC (furnace/heating channel dropped -> cooling-only).
  Source: Saldanha & Beausoleil-Morrison 2012, Energy and Buildings, free with
  citation. Expected raw: data/carleton/Saldanha_Beausoleil-Morrison/processed_data/H*.csv
  Ottawa daily temperature is fetched from the open-meteo archive API.

Run from the repo root with scripts/ and src/ on PYTHONPATH:
    PYTHONPATH=scripts;src python scripts/build_extra_frames.py
"""
import glob
import io
import json
import os
import pickle
import urllib.request

import numpy as np
import pandas as pd

from hp_capacity import robust_series_peak

COFACTOR_DIR = 'data/cofactor_ds1'
CARLETON_DIR = 'data/carleton/Saldanha_Beausoleil-Morrison/processed_data'
CACHE = 'scratchpad/cross_frames.pkl'
# electric-heated blocks (GSHP / electric resistance / electric floor heating);
# district-heating blocks (6479-6495, 6892-6893) carry non-electric heat and are excluded.
COFACTOR_ELEC = [6470, 6471, 6472, 6473, 6474, 6475, 6476, 6477, 6478, 6499]


# ---------------------------------------------------------------------------
def _load_cofactor_building(bid):
    f = f'{COFACTOR_DIR}/building_{bid}.txt'
    meta = {}
    with open(f, encoding='utf-8') as fh:
        for _ in range(21):
            line = fh.readline().rstrip('\n')
            if ';' in line:
                k, v = line.split(';', 1); meta[k] = v
    df = pd.read_csv(f, sep=';', skiprows=int(meta['Header_line']) - 1)
    df['t'] = pd.to_datetime(df['TimeStamp'], utc=True)
    df = df.set_index('t')
    df = df[~df.index.duplicated(keep='first')].sort_index()
    for c in ['Tout', 'ElImp', 'ElMix', 'ElHt']:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df, int(meta['number_of_units'])


def _heat_channel(df):
    """Electricity to the heating system (Wh/h): prefer the clean ElHt channel,
    else ElMix (heating + other, per the dataset notes)."""
    if 'ElHt' in df and df['ElHt'].notna().mean() > 0.5:
        return df['ElHt']
    if 'ElMix' in df and df['ElMix'].notna().mean() > 0.5:
        return df['ElMix']
    return None


def build_cofactor_frame():
    nets, etls, tout, units = [], [], None, 0
    for b in COFACTOR_ELEC:
        df, n = _load_cofactor_building(b)
        hc = _heat_channel(df)
        if hc is None or 'ElImp' not in df:
            continue
        units += n
        nets.append(df['ElImp'].rename(f'n{b}'))
        etls.append(hc.rename(f'e{b}'))
        if tout is None:
            tout = df['Tout']
    net_h = pd.concat(nets, axis=1).sum(axis=1, min_count=1) / 1000.0        # kW
    etl_h = pd.concat(etls, axis=1).sum(axis=1, min_count=1) / 1000.0        # kW
    cap_h = float(robust_series_peak(etl_h.dropna()))
    d = pd.DataFrame({'T': tout, 'net': net_h, 'etl': etl_h}).dropna()
    dd = pd.DataFrame({'T': d['T'].resample('D').mean(), 'net': d['net'].resample('D').mean(),
                       'etl': d['etl'].resample('D').mean()}).dropna()
    return dict(n=units, T=dd['T'].to_numpy(), net=dd['net'].to_numpy(),
                heat=dd['etl'].to_numpy(), cool=np.zeros(len(dd)), cap_h=cap_h, cap_c=0.0)


# ---------------------------------------------------------------------------
_CARLETON_COLS = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'NonHVAC', 'Main', 'AC',
                  'Furnace', 'Stove', 'Dish', 'Dryer']


def _ottawa_daily_temp(start, end):
    url = (f'https://archive-api.open-meteo.com/v1/archive?latitude=45.42&longitude=-75.70'
           f'&start_date={start}&end_date={end}&daily=temperature_2m_mean&timezone=America%2FToronto')
    wx = json.load(urllib.request.urlopen(url, timeout=60))['daily']
    return pd.Series(wx['temperature_2m_mean'], index=pd.to_datetime(wx['time']))


def build_carleton_frame(min_houses=10):
    daily = {}; ac_peak = 0.0
    for f in sorted(glob.glob(f'{CARLETON_DIR}/H*.csv')):
        if os.path.basename(f).startswith('._'):
            continue
        raw = open(f, encoding='latin-1').read().splitlines()
        hdr = next(i for i, l in enumerate(raw) if l.startswith('Year,Month,Day'))
        df = pd.read_csv(io.StringIO('\n'.join(raw[hdr + 1:])), header=None,
                         usecols=range(len(_CARLETON_COLS)), names=_CARLETON_COLS)
        df = df.apply(pd.to_numeric, errors='coerce').dropna(subset=['Year', 'Month', 'Day', 'Hour', 'Minute'])
        ts = pd.to_datetime(dict(year=df.Year, month=df.Month, day=df.Day,
                                 hour=df.Hour, minute=df.Minute), errors='coerce')
        df = df.set_index(ts)
        df = df[df.index.notna()].dropna(subset=['Main'])
        if df['AC'].notna().any():
            ac_peak += float(robust_series_peak(df['AC'].dropna()))
        daily[os.path.basename(f)] = df[['Main', 'AC']].resample('D').mean()
    alld = pd.concat(daily, axis=1)
    present = alld.xs('Main', axis=1, level=1).notna().sum(axis=1)
    agg = pd.DataFrame({v: alld.xs(v, axis=1, level=1).sum(axis=1, min_count=1) for v in ['Main', 'AC']})
    agg = agg[present >= min_houses]
    T = _ottawa_daily_temp(agg.index.min().date(), agg.index.max().date())
    k = agg.join(T.rename('T')).dropna()
    return dict(n=len(daily), T=k['T'].to_numpy(), net=k['Main'].to_numpy(),
                heat=np.zeros(len(k)), cool=k['AC'].to_numpy(), cap_h=0.0, cap_c=ac_peak)


# ---------------------------------------------------------------------------
def main():
    cof = build_cofactor_frame()
    car = build_carleton_frame()
    print(f"COFACTOR Norway pool: n={cof['n']}, {len(cof['T'])} days, cap_h={cof['cap_h']:.0f} kW")
    print(f"Carleton Ottawa:      n={car['n']}, {len(car['T'])} days, cap_c={car['cap_c']:.0f} kW")
    FR = pickle.load(open(CACHE, 'rb'))
    FR['COFACTOR Norway (real HP)'] = cof
    FR['Carleton Ottawa (real AC)'] = car
    pickle.dump(FR, open(CACHE, 'wb'))
    print('updated', CACHE, '->', list(FR.keys()))
    print('now run: outputs.build_cross_table(repull=False); outputs.tab_cross(); outputs.fig_cross_montage()')


if __name__ == '__main__':
    main()
