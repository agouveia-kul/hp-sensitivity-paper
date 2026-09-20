# -*- coding: utf-8 -*-
"""Re-pull ONLY the three ResStock ASHP rows with the electric backup element
folded into ETL heating (compressor + heating_hp_bkup), leaving the German,
Swiss and Austin cache entries untouched. Then re-fit the whole table."""
import pickle, numpy as np, pandas as pd
import s3fs, pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor
from cross_fit import fit_row

CACHE = 'scratchpad/cross_frames.pkl'
INPUTS = pickle.load(open(CACHE, 'rb'))
print('loaded cache with keys:', list(INPUTS.keys()), flush=True)

fs = s3fs.S3FileSystem(anon=True)
R2 = "oedi-data-lake/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2024/resstock_amy2018_release_2"
HTTP = "https://oedi-data-lake.s3.amazonaws.com/" + R2.split('/', 1)[1]
HC = 'out.electricity.heating.energy_consumption'            # HP compressor
BK = 'out.electricity.heating_hp_bkup.energy_consumption'    # electric resistance backup
CC = 'out.electricity.cooling.energy_consumption'
TC = 'out.electricity.total.energy_consumption'
meta = pd.read_parquet('scratchpad/resstock_meta_sfd.parquet'); UP = 3


def read_one(bid, st):
    try:
        t = pq.read_table(fs.open(f"{R2}/timeseries_individual_buildings/by_state/upgrade={UP}/state={st}/{bid}-{UP}.parquet"),
                          columns=['timestamp', HC, BK, CC, TC]).to_pandas(ignore_metadata=True)
    except Exception:
        return None
    t['timestamp'] = pd.to_datetime(t['timestamp']); return t.set_index('timestamp')


def wx(gj, st):
    w = pd.read_csv(f"{HTTP}/weather/state={st}/{gj}_2018.csv", parse_dates=['date_time'])
    return w.set_index('date_time')['Dry Bulb Temperature [°C]'].resample('D').mean()


for gj, st, lab in [('G2700530', 'MN', 'ResStock ASHP -- Hennepin MN (cold)'),
                    ('G5300330', 'WA', 'ResStock ASHP -- King WA (mild)'),
                    ('G0400130', 'AZ', 'ResStock ASHP -- Maricopa AZ (hot)')]:
    bids = meta[meta['in.county'] == gj]['bldg_id'].tolist()
    bids = list(np.random.default_rng(0).choice(bids, 150, replace=False))   # same seed as before
    heat = cool = tot = None; hpk = cpk = 0.0
    with ThreadPoolExecutor(max_workers=16) as ex:
        for r in ex.map(lambda b: read_one(b, st), bids):
            if r is None:
                continue
            h = (r[HC] + r[BK]) * 4          # ETL heating = compressor + backup, kWh/15min -> kW
            c, s2 = r[CC] * 4, r[TC] * 4
            heat = h if heat is None else heat.add(h, fill_value=0)
            cool = c if cool is None else cool.add(c, fill_value=0)
            tot = s2 if tot is None else tot.add(s2, fill_value=0)
            hpk += float(h.max()); cpk += float(c.max())
    Td = wx(gj, st)
    dd = pd.DataFrame({'T': Td, 'net': tot.resample('D').mean(),
                       'heat': heat.resample('D').mean(), 'cool': cool.resample('D').mean()}).dropna()
    INPUTS[lab] = dict(n=150, T=dd['T'].to_numpy(), net=dd['net'].to_numpy(),
                       heat=dd['heat'].to_numpy(), cool=dd['cool'].to_numpy(), cap_h=hpk, cap_c=cpk)
    print(lab, 'done: cap_h', round(hpk), 'cap_c', round(cpk), 'days', len(dd), flush=True)

pickle.dump(INPUTS, open(CACHE, 'wb'))
print('updated cache', flush=True)

rows = [fit_row(lab, v['n'], v['T'], v['net'], v['heat'], v['cool'], v['cap_h'], v['cap_c'])
        for lab, v in INPUTS.items()]
pd.DataFrame(rows).to_csv('scratchpad/cross_table.csv', index=False)
print('\n' + pd.DataFrame(rows)[['label', 'n', 'mode', 'P_base', 's_h', 'T_h', 's_c', 'T_c', 'R2',
                                 'm_h', 'SF_cold', 'R2_SFh']].round(3).to_string(index=False))
print('wrote scratchpad/cross_table.csv')
