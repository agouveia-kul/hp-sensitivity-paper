# -*- coding: utf-8 -*-
"""NEEA 2023 full year, split by state (WA, OR): one aggregate per state with its
own outdoor temperature."""
import numpy as np, pandas as pd
from cross_fit import fit_row

p = pd.read_parquet('data/neea_power_2023.parquet')
p['date'] = p['MIN_T_l'].dt.floor('D')
site_state = p.groupby('ee_site_id')['state'].first()
hp = p[p['End Use'] == 'Ductless Heatpump']; mains = p[p['End Use'] == 'Mains']
hp_int = hp.groupby(['ee_site_id', 'MIN_T_l'], as_index=False)['power'].sum()
mn_int = mains.groupby(['ee_site_id', 'MIN_T_l'], as_index=False)['power'].sum()
hp_int['date'] = hp_int['MIN_T_l'].dt.floor('D'); mn_int['date'] = mn_int['MIN_T_l'].dt.floor('D')
hp_peak = hp_int.groupby('ee_site_id')['power'].quantile(0.99)
hp_day = hp_int.groupby(['ee_site_id', 'date'])['power'].mean().rename('hp')
mn_day = mn_int.groupby(['ee_site_id', 'date'])['power'].mean().rename('net')
cov = mn_day.groupby(level=0).size()

t = pd.read_parquet('data/neea_temp_2023.parquet')
t['date'] = t['MIN_T_l'].dt.floor('D'); t['C'] = (t['temp'] - 32) * 5.0 / 9.0
t['state'] = t['ee_site_id'].map(site_state)
reg_temp = t.groupby(['ee_site_id', 'date'])['C'].mean().groupby(level=1).mean()   # regional fallback

import pickle
FR = {}
rows = []
for st in ['WA', 'OR']:
    ssites = set(site_state[site_state == st].index)
    sites = sorted((set(hp_day.index.get_level_values(0)) & set(cov[cov >= 300].index)) & ssites)
    netW = mn_day[mn_day.index.get_level_values(0).isin(sites)].unstack(0)
    hpW = hp_day[hp_day.index.get_level_values(0).isin(sites)].unstack(0)
    keep = netW.notna().sum(axis=1) >= 0.7 * len(sites)
    net_agg = netW[keep].sum(axis=1, min_count=1)
    hp_agg = hpW.reindex(net_agg.index)[net_agg.notna()].sum(axis=1, min_count=1)
    cap = float(hp_peak[hp_peak.index.isin(sites)].sum())
    ts = t[t['state'] == st]
    temp_agg = ts.groupby(['ee_site_id', 'date'])['C'].mean().groupby(level=1).mean()
    if temp_agg.notna().sum() < 200:            # too few state sensors -> regional
        temp_agg = reg_temp
    d = pd.DataFrame({'net': net_agg, 'hp': hp_agg}).join(temp_agg.rename('Tc')).dropna()
    T = d['Tc'].to_numpy(); hpv = d['hp'].to_numpy(); netv = d['net'].to_numpy()
    heat = np.where(T < 15, hpv, 0.0); cool = np.where(T > 20, hpv, 0.0)
    row = fit_row(f'NEEA {st} (real HP)', len(sites), T, netv, heat, cool, cap, cap)
    print(f'{st}: {len(sites)} homes, {len(d)} days, T[{T.min():.1f},{T.max():.1f}], temp sensors {ts.ee_site_id.nunique()}', flush=True)
    print('  ', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
    rows.append(row)
    FR[f'NEEA {st} (real HP)'] = dict(n=len(sites), T=T, net=netv, heat=hpv, cool=hpv, cap_h=cap, cap_c=cap)
pd.DataFrame(rows).to_csv('scratchpad/neea_rows.csv', index=False)
pickle.dump(FR, open('scratchpad/neea_frames.pkl', 'wb'))
print('wrote scratchpad/neea_rows.csv + neea_frames.pkl')
