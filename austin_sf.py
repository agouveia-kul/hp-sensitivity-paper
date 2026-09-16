# -*- coding: utf-8 -*-
"""Actual heating- and cooling-side SF for the Austin aggregate, from submetered
circuits. SF(T_d) = daily-mean aggregate ETL / sum of individual 99.9th-pct peaks;
reported at the coldest day (heating) and the hottest day (cooling)."""
import numpy as np, pandas as pd
import pecan_street as ps
from hp_capacity import robust_series_peak

DATA = ps.DATA_DIR
COOL = ['air1', 'air2', 'air3', 'airwindowunit1']
HEAT = ['furnace1', 'furnace2', 'heater1', 'heater2', 'heater3']

meta = pd.read_csv(f'{DATA}/metadata.csv', skiprows=[1])
meta['dataid'] = pd.to_numeric(meta['dataid'], errors='coerce')
cand = set(meta.dropna(subset=['dataid']).query("city=='Austin' and state=='Texas'").dataid.astype(int))

usecols = ['dataid', 'local_15min'] + COOL + HEAT
chunks = []
for ch in pd.read_csv(f'{DATA}/15minute_data_austin.csv', usecols=lambda c: c in usecols, chunksize=500_000):
    chunks.append(ch[ch.dataid.isin(cand)])
df = pd.concat(chunks, ignore_index=True)
df['local_15min'] = pd.to_datetime(df['local_15min'], utc=True).dt.tz_convert('US/Central')
df['cool'] = df[[c for c in COOL if c in df]].sum(axis=1, min_count=1)
df['heat'] = df[[c for c in HEAT if c in df]].sum(axis=1, min_count=1)

T = ps.load_austin_temperature(f'{DATA}/open-meteo-30.27N97.75W157m.csv')   # daily mean

def side_sf(mode, min_peak=0.2):
    peaks, daily = [], []
    for hid, g in df.groupby('dataid'):
        s = g.set_index('local_15min')[mode].dropna()
        if len(s) < 1000:
            continue
        pk = robust_series_peak(s)
        if not np.isfinite(pk) or pk < min_peak:            # household has no real load of this mode
            continue
        peaks.append(pk)
        daily.append(s.resample('D').mean())
    cap = float(np.nansum(peaks))                            # installed capacity = sum of peaks
    agg = pd.concat(daily, axis=1).sum(axis=1, min_count=1)  # aggregate daily load
    sf = (agg / cap).clip(0, 1)
    d = pd.DataFrame({'T': T, 'sf': sf}).dropna()
    return d, cap, len(peaks)

dh, cap_h, nh = side_sf('heat')
dc, cap_c, nc = side_sf('cool')
Tmin, Tmax = dh['T'].min(), dc['T'].max()

# SF at the temperature extreme (mean over the coldest / hottest 5 days, to de-noise)
sf_cold = dh.sort_values('T').head(5)['sf'].mean()
sf_hot = dc.sort_values('T').tail(5)['sf'].mean()
print(f'HEATING side: {nh} households, installed cap {cap_h:.0f} kW, T_min {Tmin:.1f} C')
print(f'  SF_cold (coldest 5 days)  = {sf_cold:.3f}   max daily SF = {dh.sf.max():.3f}')
print(f'COOLING side: {nc} households, installed cap {cap_c:.0f} kW, T_max {Tmax:.1f} C')
print(f'  SF_hot  (hottest 5 days)  = {sf_hot:.3f}   max daily SF = {dc.sf.max():.3f}')
