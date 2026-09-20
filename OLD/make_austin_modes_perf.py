# -*- coding: utf-8 -*-
"""Test energy / installed-capacity / flexibility estimation on the Austin
aggregate, comparing SPLIT (per-mode capacity) vs TOTAL (one ETL capacity).

Same homes throughout: the net-load bathtub (whole-home load) supplies the
observable numerator arms s_h, s_c; the submetered furnace/heater (heat) and
air (cool) circuits supply the ground-truth per-mode loads, capacities and SFs.
The SF is the population's own (no transfer), so capacity/flex error is the
net-load numerator error, and the split-vs-total contrast is the convention."""
import numpy as np, pandas as pd
import pecan_street as ps
from hp_capacity import robust_series_peak
from hp_common import fit_bathtub_stick

DATA = ps.DATA_DIR
COOL = ['air1', 'air2', 'air3', 'airwindowunit1']
HEAT = ['furnace1', 'furnace2', 'heater1', 'heater2', 'heater3']

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
df['heat'] = df[[c for c in HEAT if c in df]].sum(axis=1, min_count=1)
df['cool'] = df[[c for c in COOL if c in df]].sum(axis=1, min_count=1)
T = ps.load_austin_temperature()

net = h = c = None
capH = capC = capA = 0.0
nH = nC = 0
for hid, g in df.groupby('dataid'):
    gi = g.set_index('local_15min')
    tot = gi['total'].dropna()
    if len(tot) < 1000:
        continue
    if gi[cons_cols].max().max() > 30 or gi[['total', 'meter_ref']].corr().iloc[0, 1] < 0.9:
        continue                                     # QC vs whole-home meter
    nd = tot.resample('D').mean(); net = nd if net is None else net.add(nd, fill_value=0)
    hs, cs = gi['heat'].dropna(), gi['cool'].dropna()
    etl = (gi['heat'].fillna(0) + gi['cool'].fillna(0)).dropna()
    pkh = robust_series_peak(hs) if len(hs) > 1000 else np.nan
    pkc = robust_series_peak(cs) if len(cs) > 1000 else np.nan
    pka = robust_series_peak(etl) if len(etl) > 1000 else np.nan
    if np.isfinite(pkh) and pkh > 0.1:
        capH += pkh; nH += 1; hd = hs.resample('D').mean(); h = hd if h is None else h.add(hd, fill_value=0)
    if np.isfinite(pkc) and pkc > 0.2:
        capC += pkc; nC += 1; cd = cs.resample('D').mean(); c = cd if c is None else c.add(cd, fill_value=0)
    if np.isfinite(pka) and pka > 0.2:
        capA += pka
capA = capH + capC if capA == 0 else capA

d = pd.DataFrame({'T': T, 'net': net, 'P_H': h, 'P_C': c}).fillna({'P_H': 0, 'P_C': 0}).dropna(subset=['T', 'net'])
d['P_A'] = d['P_H'] + d['P_C']
d['SF_H'] = (d['P_H'] / capH).clip(0, 1)
d['SF_C'] = (d['P_C'] / capC).clip(0, 1)
d['SF_A'] = (d['P_A'] / capA).clip(0, 1)

# observable net-load bathtub -> numerator arms
base, s_h, T_h, s_c, T_c, r2 = fit_bathtub_stick(d['T'].to_numpy(), d['net'].to_numpy())
d['PH_hat'] = s_h * np.maximum(0, T_h - d['T'])
d['PC_hat'] = s_c * np.maximum(0, d['T'] - T_c)
print(f'homes: net QC set; heating {nH} (cap {capH:.0f} kW), cooling {nC} (cap {capC:.0f} kW), total cap {capA:.0f} kW')
print(f'net-load bathtub: base {base:.1f} s_h {s_h:.2f} T_h {T_h:.1f} s_c {s_c:.2f} T_c {T_c:.1f} R2 {r2:.3f}')

def wape(hat, tru):
    return float(np.abs(np.asarray(hat) - np.asarray(tru)).sum() / np.asarray(tru).sum() * 100)

# ---------------- ENERGY (kWh, daily mean * 24 h) -- capacity-independent -----
dt = 24.0
EH_hat, EH_tru = d['PH_hat'].sum() * dt, d['P_H'].sum() * dt
EC_hat, EC_tru = d['PC_hat'].sum() * dt, d['P_C'].sum() * dt
print('\n== ENERGY ==')
print(f'  heating: est {EH_hat/1e3:6.1f} MWh vs true {EH_tru/1e3:6.1f}  ratio {EH_hat/EH_tru:.2f}')
print(f'  cooling: est {EC_hat/1e3:6.1f} MWh vs true {EC_tru/1e3:6.1f}  ratio {EC_hat/EC_tru:.2f}')
print(f'  SPLIT (per mode) WAPE  heat {abs(EH_hat-EH_tru)/EH_tru*100:4.1f}%  cool {abs(EC_hat-EC_tru)/EC_tru*100:4.1f}%')
print(f'  TOTAL (heat+cool):  est {(EH_hat+EC_hat)/1e3:.1f} vs true {(EH_tru+EC_tru)/1e3:.1f} MWh  '
      f'ratio {(EH_hat+EC_hat)/(EH_tru+EC_tru):.2f}')

# ---------------- INSTALLED CAPACITY -----------------------------------------
cold = d.nsmallest(5, 'T'); hot = d.nlargest(5, 'T')
SFH_cold, SFC_hot = cold['SF_H'].mean(), hot['SF_C'].mean()
SFA_cold, SFA_hot = cold['SF_A'].mean(), hot['SF_A'].mean()
PHh_cold, PCh_hot = (s_h * max(0, T_h - cold['T'].mean())), (s_c * max(0, hot['T'].mean() - T_c))
capH_hat = PHh_cold / SFH_cold
capC_hat = PCh_hot / SFC_hot
capA_hat_cold = PHh_cold / SFA_cold
capA_hat_hot = PCh_hot / SFA_hot
print('\n== INSTALLED CAPACITY ==')
print(f'  SPLIT: Cap_H est {capH_hat:5.0f} vs true {capH:5.0f} kW  ({capH_hat/capH:+.0%})   '
      f'Cap_C est {capC_hat:5.0f} vs true {capC:5.0f} kW  ({capC_hat/capC-1:+.0%})')
print(f'  TOTAL: Cap_A est {capA_hat_hot:5.0f} (hot) / {capA_hat_cold:5.0f} (cold) vs true {capA:5.0f} kW  '
      f'({capA_hat_hot/capA-1:+.0%} / {capA_hat_cold/capA-1:+.0%})')

# ---------------- FLEXIBILITY (annual, per 1 h window; kWh) -------------------
def flex(sf, cap):
    return float((sf * (1 - sf)).sum() * cap)      # sum over days of SF(1-SF) * cap * 1h
flexH_act, flexC_act = flex(d['SF_H'], capH), flex(d['SF_C'], capC)
flexA_act = flex(d['SF_A'], capA)
flexH_est, flexC_est = flex(d['SF_H'], capH_hat), flex(d['SF_C'], capC_hat)
flexA_est = flex(d['SF_A'], capA_hat_hot)
print('\n== FLEXIBILITY (annual MWh per hour of window) ==')
print(f'  SPLIT actual: heat {flexH_act/1e3:.1f} + cool {flexC_act/1e3:.1f} = {(flexH_act+flexC_act)/1e3:.1f} MWh/h')
print(f'  TOTAL actual: {flexA_act/1e3:.1f} MWh/h   (TOTAL/SPLIT = {flexA_act/(flexH_act+flexC_act):.2f})')
print(f'  SPLIT est/actual ratio {(flexH_est+flexC_est)/(flexH_act+flexC_act):.2f}   '
      f'TOTAL est/actual ratio {flexA_est/flexA_act:.2f}')
