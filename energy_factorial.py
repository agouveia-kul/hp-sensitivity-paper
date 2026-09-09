# -*- coding: utf-8 -*-
"""Energy use case (Eq. 6) on the factorial design: the net-load fit's thermal
component integrated over the year, against submetered heat-pump energy."""
import numpy as np, pandas as pd, pickle
import hp_analysis as ha

design = pickle.load(open('data/design_factorial.pkl', 'rb'))
fits = pd.read_parquet('data/factorial_fits.parquet')
te = ha.thermal_energy_estimates(design, fits, resolution='24 h')
te['N_hp'] = te['N_hp'].astype(int)

# per-substation annual energy: estimated (heating arm) vs submetered actual
g = te.groupby('substation_id').agg(est=('hs_kWh', 'sum'), act=('actual_kWh', 'sum'),
                                    N_hp=('N_hp', 'first'))
g = g[g.act > 0]
g['ape'] = np.abs(g.est - g.act) / g.act * 100
g['ratio'] = g.est / g.act

# dead-band gap: share of submetered HP energy on days ABOVE each fit's threshold
thr = fits[(fits.response == 'Load') & (fits.resolution == '24 h')].set_index('substation_id')['T_threshold']
te['thr'] = te.substation_id.map(thr)
te['above'] = te.T_mean > te.thr
frac_above = te.groupby('substation_id').apply(
    lambda x: x.loc[x.above, 'actual_kWh'].sum() / x.actual_kWh.sum() * 100
    if x.actual_kWh.sum() > 0 else np.nan)
g['above_pct'] = frac_above

print(f'{len(g)} substations with submetered HP energy')
print('annual thermal energy vs submetered HP energy:')
print(f'  median ratio est/act = {g.ratio.median():.2f}  (est captures the temperature-driven share)')
print(f'  median APE           = {g.ape.median():.1f}%')
print(f'  median share of HP energy above the dead band = {g.above_pct.median():.1f}%')
print('\n-- by N_hp (median) --')
print(g.groupby('N_hp').agg(n=('ape', 'size'), ratio=('ratio', 'median'),
                            ape=('ape', 'median'), above=('above_pct', 'median')).round(2).to_string())

# correcting for the dead-band share: estimate vs the temperature-driven actual
te['act_below'] = np.where(te.above, 0.0, te.actual_kWh)
gb = te.groupby('substation_id').agg(est=('hs_kWh', 'sum'), act_td=('act_below', 'sum'))
gb = gb[gb.act_td > 0]
gb['ape'] = np.abs(gb.est - gb.act_td) / gb.act_td * 100
print(f'\nagainst the temperature-driven share only (days below threshold): '
      f'median APE {gb.ape.median():.1f}%, median ratio {(gb.est/gb.act_td).median():.2f}')
