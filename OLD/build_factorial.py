# -*- coding: utf-8 -*-
"""Balanced factorial substation design: every feasible (N, N_hp) cell gets an
equal number of replicates, N_hp capped at 50, 1000 substations in total.

Both N_total and N_hp are capped at 50. n_grid x hp_grid crossed triangularly
(N_hp <= N_total) gives 20 feasible cells; 50 replicates each -> 1000
substations, with penetration reaching 1.0 at every size. Heat pumps and base
households are drawn as two independent samples WITH replacement (decoupled), so
a household may recur within a substation and the heat-pump count does not
constrain which base households appear."""
import warnings; warnings.filterwarnings('ignore')
import pandas as pd
import hp_design as hd, hp_pools as hpp

N_GRID = [10, 20, 30, 40, 50]
HP_GRID = [5, 10, 20, 30, 40, 50]
N_REPS = 50
RULE = dict(eheat_frac=0.0, clean_hp=False, seed=42, verbose=False, replace=True)

pool = hpp.build_pool_combined(verbose=False)
design, cov = hd.generate_design(pool, n_grid=N_GRID, hp_grid=HP_GRID,
                                 n_reps=N_REPS, **RULE)
meta = design['meta']
print(f'{len(meta)} substations; cells filled {int(cov.filled.sum())}/{int(cov.requested.sum())}')
print('skipped cells:', int((cov.skipped > 0).sum()))
for _, r in cov[cov.skipped > 0].iterrows():
    print(f"  SKIP N={r['N_total']} N_hp={r['N_hp']}: {r['reason']}")
print('\n(N_total x N_hp) cell counts:')
print(pd.crosstab(meta.N_total, meta.N_hp).to_string())
print('\npenetration values realised:', sorted(meta.hp_ratio.round(3).unique().tolist()))
hd.save_design(design, 'data/design_factorial.pkl')
print('\nsaved -> data/design_factorial.pkl')
