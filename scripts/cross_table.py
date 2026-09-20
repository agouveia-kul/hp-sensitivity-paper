# -*- coding: utf-8 -*-
"""Cross-dataset characterisation table. Input daily frames are cached to
scratchpad/cross_frames.pkl so re-fits (e.g. after tuning cross_fit) are instant.
Rows: German WPuQ, Swiss substation, Austin, ResStock ASHP (cold/mild/hot)."""
import os, pickle, numpy as np, pandas as pd
from cross_fit import fit_row

CACHE = 'scratchpad/cross_frames.pkl'
INPUTS = {}   # label -> dict(n, T, net, heat, cool, cap_h, cap_c)

if os.path.exists(CACHE):
    INPUTS = pickle.load(open(CACHE, 'rb'))
    print('loaded cached frames', flush=True)
else:
    # ---- German WPuQ ----
    d = pd.read_csv('data/wpuq_real_feeder_sf.csv', index_col=0, parse_dates=True)
    cap = 238.514
    INPUTS['German WPuQ (real HP)'] = dict(n=37, T=d['Temp'].to_numpy(), net=d['net'].to_numpy(),
                                           heat=(d['SF'] * cap).to_numpy(), cool=None, cap_h=cap, cap_c=0.0)
    print('German done', flush=True)
    # ---- Swiss substation (largest N_hp) ----
    from sf_transfer import build_frames, pickle_load
    subs = [s for s in build_frames(pickle_load('data/design_factorial.pkl')) if np.all(np.isfinite(s['SF']))]
    s = max(subs, key=lambda x: x['hp_ratio'] * x['N_total']); cap = float(s['HP_Peak'])
    INPUTS['Swiss substation (real HP)'] = dict(n=int(round(s['hp_ratio'] * s['N_total'])),
                                                T=np.asarray(s['T']), net=np.asarray(s['Load']),
                                                heat=np.asarray(s['SF']) * cap, cool=None, cap_h=cap, cap_c=0.0)
    print('Swiss done', flush=True)
    # ---- Austin Pecan Street ----
    import make_austin_arm_capacity as ma
    idx = ma.Tds.index
    def arm_sum(flag):
        acc = pd.Series(0.0, index=idx)
        for dv in ma.devices:
            if dv[flag]:
                acc = acc.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
        return acc
    dd = pd.DataFrame({'T': ma.d['T'], 'net': ma.d['net'], 'heat': arm_sum('a_h'), 'cool': arm_sum('a_c')}).dropna()
    INPUTS['Austin Pecan St (real)'] = dict(n=len({dv['hid'] for dv in ma.devices}), T=dd['T'].to_numpy(),
                                            net=dd['net'].to_numpy(), heat=dd['heat'].to_numpy(),
                                            cool=dd['cool'].to_numpy(), cap_h=ma.capH, cap_c=ma.capC)
    print('Austin done', flush=True)
    # ---- ResStock ASHP ----
    import s3fs, pyarrow.parquet as pq
    from concurrent.futures import ThreadPoolExecutor
    fs = s3fs.S3FileSystem(anon=True)
    R2 = "oedi-data-lake/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2024/resstock_amy2018_release_2"
    HTTP = "https://oedi-data-lake.s3.amazonaws.com/" + R2.split('/', 1)[1]
    HC, CC, TC = ('out.electricity.heating.energy_consumption', 'out.electricity.cooling.energy_consumption',
                  'out.electricity.total.energy_consumption')
    meta = pd.read_parquet('scratchpad/resstock_meta_sfd.parquet'); UP = 3
    def read_one(bid, st):
        try:
            t = pq.read_table(fs.open(f"{R2}/timeseries_individual_buildings/by_state/upgrade={UP}/state={st}/{bid}-{UP}.parquet"),
                              columns=['timestamp', HC, CC, TC]).to_pandas(ignore_metadata=True)
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
        bids = list(np.random.default_rng(0).choice(bids, 150, replace=False))
        heat = cool = tot = None; hpk = cpk = 0.0
        with ThreadPoolExecutor(max_workers=16) as ex:
            for r in ex.map(lambda b: read_one(b, st), bids):
                if r is None: continue
                h, c, s2 = r[HC] * 4, r[CC] * 4, r[TC] * 4
                heat = h if heat is None else heat.add(h, fill_value=0)
                cool = c if cool is None else cool.add(c, fill_value=0)
                tot = s2 if tot is None else tot.add(s2, fill_value=0)
                hpk += float(h.max()); cpk += float(c.max())
        Td = wx(gj, st)
        dd = pd.DataFrame({'T': Td, 'net': tot.resample('D').mean(),
                           'heat': heat.resample('D').mean(), 'cool': cool.resample('D').mean()}).dropna()
        INPUTS[lab] = dict(n=150, T=dd['T'].to_numpy(), net=dd['net'].to_numpy(),
                           heat=dd['heat'].to_numpy(), cool=dd['cool'].to_numpy(), cap_h=hpk, cap_c=cpk)
        print(lab, 'done', flush=True)
    pickle.dump(INPUTS, open(CACHE, 'wb'))

rows = [fit_row(lab, v['n'], v['T'], v['net'], v['heat'], v['cool'], v['cap_h'], v['cap_c'])
        for lab, v in INPUTS.items()]
pd.DataFrame(rows).to_csv('scratchpad/cross_table.csv', index=False)
print('\n' + pd.DataFrame(rows)[['label', 'n', 'mode', 'P_base', 's_h', 'T_h', 's_c', 'T_c', 'R2',
                                 'm_h', 'SF_cold', 'R2_SFh']].round(3).to_string(index=False))
print('wrote scratchpad/cross_table.csv')
