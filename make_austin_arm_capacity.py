# -*- coding: utf-8 -*-
"""Per-arm installed capacity by ACTIVITY, not by circuit label.

Thresholds T_h, T_c come from the net-load bathtub. Each submetered ETL circuit
is a device with its own installed capacity (robust peak). A device is flagged
active in an arm if it draws above a small floor on a meaningful share of that
arm's days. Per-arm installed capacity = sum of the peaks of the devices active
in that arm; a dual-mode device (e.g. the furnace air-handler) counts in both."""
import numpy as np, pandas as pd
import pecan_street as ps
from hp_capacity import robust_series_peak
from hp_common import fit_bathtub_stick

DATA = ps.DATA_DIR
COOL = ['air1', 'air2', 'air3', 'airwindowunit1']
HEAT = ['furnace1', 'furnace2', 'heater1', 'heater2', 'heater3']
ETLCOLS = COOL + HEAT
FLOOR = 0.05        # kW daily-mean: a device is "on" that day above this
SHARE = 0.25        # active in an arm if on for at least this share of the arm's days
MINPK = 0.1         # kW: ignore circuits whose peak never reaches this (no real device)

meta = pd.read_csv(f'{DATA}/metadata.csv', skiprows=[1])
meta['dataid'] = pd.to_numeric(meta['dataid'], errors='coerce')
meta = meta.dropna(subset=['dataid']); meta['dataid'] = meta.dataid.astype(int)
cand = set(meta[(meta.city == 'Austin') & (meta.state == 'Texas')].dataid)

all_cols = pd.read_csv(f'{DATA}/15minute_data_austin.csv', nrows=0).columns.tolist()
cons_cols = [c for c in all_cols if c not in ps.NON_CONSUMPTION_COLS]
chunks = []
for ch in pd.read_csv(f'{DATA}/15minute_data_austin.csv', chunksize=500_000):
    chunks.append(ch[ch.dataid.isin(cand)])
df = pd.concat(chunks, ignore_index=True)
df['local_15min'] = pd.to_datetime(df['local_15min'], utc=True).dt.tz_convert('US/Central')
df['total'] = df[cons_cols].sum(axis=1, min_count=1)
df['meter_ref'] = df[['grid', 'solar', 'solar2']].sum(axis=1, min_count=1)
T = ps.load_austin_temperature()

net = None
devices = []                       # one entry per (household, ETL circuit)
for hid, g in df.groupby('dataid'):
    gi = g.set_index('local_15min')
    tot = gi['total'].dropna()
    if len(tot) < 1000 or gi[cons_cols].max().max() > 30 or gi[['total', 'meter_ref']].corr().iloc[0, 1] < 0.9:
        continue
    nd = tot.resample('D').mean(); net = nd if net is None else net.add(nd, fill_value=0)
    for col in ETLCOLS:
        if col not in gi:
            continue
        s = gi[col].dropna()
        if len(s) < 1000:
            continue
        pk = robust_series_peak(s)
        if not np.isfinite(pk) or pk < MINPK:
            continue
        devices.append(dict(hid=hid, col=col, peak=float(pk),
                            daily=s.resample('D').mean()))

# net-load bathtub -> regime thresholds
d = pd.DataFrame({'T': T, 'net': net}).dropna()
base, s_h, T_h, s_c, T_c, r2 = fit_bathtub_stick(d['T'].to_numpy(), d['net'].to_numpy())
Tds = d.set_index(d.index)['T']
heat_days = Tds.index[Tds < T_h]
cool_days = Tds.index[Tds > T_c]
band_days = Tds.index[(Tds >= T_h) & (Tds <= T_c)]
print(f'net-load bathtub: T_h {T_h:.1f}  T_c {T_c:.1f}  (R2 {r2:.3f});  '
      f'{len(heat_days)} heating / {len(band_days)} dead-band / {len(cool_days)} cooling days')
print(f'{len(devices)} ETL devices across the QC set\n')

def share_on(daily, days):
    x = daily.reindex(days).dropna()
    return float((x > FLOOR).mean()) if len(x) else 0.0

for dv in devices:
    dv['a_h'] = share_on(dv['daily'], heat_days) >= SHARE
    dv['a_c'] = share_on(dv['daily'], cool_days) >= SHARE
    dv['a_b'] = share_on(dv['daily'], band_days) >= SHARE

def cap(flag):
    return sum(dv['peak'] for dv in devices if dv[flag])

capH, capC, capB = cap('a_h'), cap('a_c'), cap('a_b')
# union capacity (each device counted once) for reference
capU = sum(dv['peak'] for dv in devices if dv['a_h'] or dv['a_c'] or dv['a_b'])

print('== per-arm installed capacity (sum of peaks of devices active in the arm) ==')
print(f'  heating arm  Cap_H = {capH:5.0f} kW   ({sum(dv["a_h"] for dv in devices)} devices)')
print(f'  dead band    Cap_B = {capB:5.0f} kW   ({sum(dv["a_b"] for dv in devices)} devices)')
print(f'  cooling arm  Cap_C = {capC:5.0f} kW   ({sum(dv["a_c"] for dv in devices)} devices)')
print(f'  union (each device once)   = {capU:5.0f} kW\n')

# how each circuit family lands (to see dual-mode counting)
fam = {'air': COOL, 'furnace': ['furnace1', 'furnace2'], 'heater': ['heater1', 'heater2', 'heater3']}
print('== activity of each circuit family (device counts active per arm) ==')
for name, cols in fam.items():
    grp = [dv for dv in devices if dv['col'] in cols]
    if not grp:
        continue
    both = sum(dv['a_h'] and dv['a_c'] for dv in grp)
    print(f'  {name:8s}: {len(grp):2d} devices, {sum(dv["peak"] for dv in grp):4.0f} kW | '
          f'active heat {sum(dv["a_h"] for dv in grp):2d}  cool {sum(dv["a_c"] for dv in grp):2d}  '
          f'band {sum(dv["a_b"] for dv in grp):2d}  (both arms {both})')

print('\n== compare to earlier conventions ==')
print('  circuit-label split : Cap_H 23  Cap_C 75  (furnace forced into heating only)')
print('  total ETL           : Cap_A 92')
print(f'  activity-based      : Cap_H {capH:.0f}  Cap_C {capC:.0f}  (furnace shared into both)')
