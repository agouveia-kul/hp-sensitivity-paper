# -*- coding: utf-8 -*-
"""Extract the full-year 2023 NEEA file: Mains + Ductless Heatpump power and 2023
outdoor (oa_temp) temperature, into compact parquets."""
import pandas as pd
KEEP = {'Mains', 'Mains With Solar', 'Ductless Heatpump'}

parts = []
for ch in pd.read_csv('data/POWER15_RAW_2023 v9.2.zip', compression='zip',
                      usecols=['ee_site_id', 'End Use', 'power', 'MIN_T_l', 'state', 'cz'],
                      chunksize=3_000_000):
    parts.append(ch[ch['End Use'].isin(KEEP)])
p = pd.concat(parts, ignore_index=True)
p['MIN_T_l'] = pd.to_datetime(p['MIN_T_l'])
p.to_parquet('data/neea_power_2023.parquet')
print('POWER 2023 rows', len(p), 'sites', p.ee_site_id.nunique(),
      'span', p.MIN_T_l.min(), '->', p.MIN_T_l.max(), flush=True)

tparts = []
for ch in pd.read_csv('data/TEMPERATURE15 v9.2.zip', compression='zip',
                      usecols=['ee_site_id', 'regname', 'temp', 'MIN_T_l'], chunksize=2_000_000):
    oa = ch[ch['regname'].str.contains('oa_temp', case=False, na=False)].copy()
    oa['MIN_T_l'] = pd.to_datetime(oa['MIN_T_l'])
    tparts.append(oa[oa['MIN_T_l'].dt.year == 2023])
t = pd.concat(tparts, ignore_index=True)
t = t[(t.temp > -40) & (t.temp < 115)]
t.to_parquet('data/neea_temp_2023.parquet')
print('TEMP 2023 outdoor rows', len(t), 'sites', t.ee_site_id.nunique(), flush=True)
print('DONE')
