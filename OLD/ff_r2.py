# -*- coding: utf-8 -*-
"""R2 of both fits across temporal (resolution) and spatial (N_total, N_hp)
aggregation on the balanced factorial design. Saves fits and a summary."""
import numpy as np, pandas as pd, pickle, hp_analysis as ha

d = ha.fit_all(pickle.load(open('data/design_factorial.pkl', 'rb')), verbose=False).reset_index()
d.to_parquet('data/factorial_fits.parquet')
d = d[~d.failed]
d['N_hp'] = (d.hp_ratio * d.N_total).round().astype(int)

out = []
def p(s): out.append(str(s)); print(s, flush=True)

for resp in ['Load', 'SF']:
    x = d[d.response == resp]
    p(f'\n=== {resp} R2 by temporal resolution (median) ===')
    p(x.groupby('resolution').r2.median().round(3).to_string())

L = d[(d.response == 'Load') & (d.resolution == '24 h')]
S = d[(d.response == 'SF') & (d.resolution == '24 h')]
p('\n=== Load R2 by N_total (24h) ==='); p(L.groupby('N_total').r2.median().round(3).to_string())
p('\n=== Load R2 by N_hp (24h) ==='); p(L.groupby('N_hp').r2.median().round(3).to_string())
p('\n=== SF R2 by N_hp (24h) ==='); p(S.groupby('N_hp').r2.median().round(3).to_string())
p('\n=== Load R2 : resolution (rows) x N_total (cols), median ===')
p(d[d.response == 'Load'].pivot_table(index='resolution', columns='N_total',
                                      values='r2', aggfunc='median').round(2).to_string())
p('\n=== SF R2 : resolution x N_hp, median ===')
p(d[d.response == 'SF'].pivot_table(index='resolution', columns='N_hp',
                                    values='r2', aggfunc='median').round(2).to_string())
open('data/ff_r2_summary.txt', 'w').write('\n'.join(out))
p('\nsaved -> data/factorial_fits.parquet, data/ff_r2_summary.txt')
