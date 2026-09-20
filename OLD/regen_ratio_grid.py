"""Rebuild every design on a rectangular N_total x HP_ratio grid.

Replaces the N_hp-indexed triangular design (and its rectangular extension)
with a full grid over five ratio levels -- 0, 25, 50, 75, 100 % -- realised at
every N_total in the design. N_total is restricted to multiples of 4, the
smallest step that keeps every one of the five ratios an exact integer count
of heat pumps (25 % of a multiple of 4 is always a whole number). N_total is
pushed as high as the pool allows while keeping the full grid intact: 100 %
penetration needs N_hp = N_total, and the submetered heat pump pool caps at
50 on the combined design's dominant weather station, so N_total stops at 48
(52 would need 52 heat pumps and does not exist).

The result is a complete rectangle -- no triangular structure, no missing
corner, no separate extension grid for a confound figure. Every (N_total,
ratio) cell has the same 25 (or 40, for WPUQ) replicates as every other.

Composition rule unchanged from the triangular design: eheat_frac=0.0 with
clean_hp=False -- no non-heat-pump member has any electric heating, heat pump
members may. See hp_design.generate_design's docstring for why the two tiers
differ.

HDH fits use each substation's own hockey-stick T_threshold as its base
temperature (see the thermal-energy validation), not hp_common's fixed
HDH_THRESH.
"""
import warnings

import pandas as pd

warnings.filterwarnings('ignore')

import hp_design as hd
import hp_pools as hpp
import hp_analysis as ha

RATIOS = [0.0, 0.25, 0.5, 0.75, 1.0]
N_TOTAL = list(range(4, 49, 4))          # combined pool: capped at 48 (HP pool = 50)
N_TOTAL_CLUSTERED = list(range(4, 49, 4))  # houses-only pool: 80 HP houses, same cap
N_TOTAL_STRICT = list(range(4, 21, 4))     # clean_hp=True: capped at 20 (21 clean HPs)
N_TOTAL_WPUQ = list(range(4, 37, 4))       # WPUQ: capped at 36 (37 households, all HP)

REPS = 25
REPS_WPUQ = 40

EHEAT_OBSERVED = 0.1937   # observed prevalence, combined pool (see composition section)

RULE = dict(eheat_frac=0.0, clean_hp=False, seed=42, verbose=False)


def build(pool, label, design_path, fits_path, hdh_path=None, rule=RULE, **grid):
    design, cov = hd.generate_design(pool, **grid, **rule)
    meta = design['meta']
    print(f'[{label}] {len(meta)} substations, cells filled '
          f'{int(cov.filled.sum())}/{int(cov.requested.sum())}', flush=True)
    print(pd.crosstab(meta.N_total, meta.hp_ratio).to_string(), flush=True)
    skipped = cov[cov.skipped > 0]
    for _, r in skipped.iterrows():
        print(f"  SKIPPED N_total={r['N_total']:>4} hp_ratio={r['hp_ratio']:.2f}: "
              f"{r['reason']}", flush=True)
    hd.save_design(design, design_path)

    fits = ha.fit_all(design, verbose=False)
    fits.to_parquet(fits_path)
    print(f'[{label}] {len(fits)} fits, {int(fits.failed.sum())} failed', flush=True)

    d24 = fits[(fits.response == 'Load') & (fits.resolution == '24 h') &
               (~fits.failed)]
    if hdh_path:
        thresholds = d24.set_index('substation_id')['T_threshold']
        ha.fit_hdh_all(design, thresholds=thresholds,
                       verbose=False).to_parquet(hdh_path)
        print(f'[{label}] HDH fits (per-substation threshold) -> {hdh_path}',
              flush=True)

    print(f'[{label}] median sensitivity (kW/K) by N_total x hp_ratio:', flush=True)
    print(d24.pivot_table(index='N_total', columns='hp_ratio', values='slope',
                          aggfunc='median').round(2).to_string(), flush=True)
    print(flush=True)


def main():
    pool = hpp.build_pool_combined(verbose=False)

    build(pool, 'ratio grid', 'data/design_ratio.pkl', 'data/ratio_fits.parquet',
          hdh_path='data/ratio_hdh_fits.parquet',
          n_grid=N_TOTAL, ratio_grid=RATIOS, n_reps=REPS)

    build(pool, 'observed prevalence', 'data/design_ratio_eheatobs.pkl',
          'data/ratio_fits_eheatobs.parquet',
          rule=dict(RULE, eheat_frac=EHEAT_OBSERVED),
          n_grid=N_TOTAL, ratio_grid=RATIOS, n_reps=REPS)

    build(pool, 'saturated', 'data/design_ratio_eheat1.pkl',
          'data/ratio_fits_eheat1.parquet',
          rule=dict(RULE, eheat_frac=1.0),
          n_grid=N_TOTAL, ratio_grid=RATIOS, n_reps=REPS)

    groups = hpp.dwelling_groups(pool)
    houses = [h for h in pool['households'] if groups[h] == 'house']
    build(hpp.restrict_pool(pool, houses, verbose=False), 'clustered houses',
          'data/design_clustered.pkl', 'data/clustered_fits.parquet',
          n_grid=N_TOTAL_CLUSTERED, ratio_grid=RATIOS, n_reps=REPS)

    build(pool, 'strict', 'data/design_ratio_strict.pkl',
          'data/ratio_strict_fits.parquet',
          rule=dict(RULE, clean_hp=True),
          n_grid=N_TOTAL_STRICT, ratio_grid=RATIOS, n_reps=REPS)

    build(hpp.build_pool_wpuq(verbose=False), 'wpuq',
          'data/design_wpuq_val.pkl', 'data/wpuq_val_fits.parquet',
          n_grid=N_TOTAL_WPUQ, ratio_grid=RATIOS, n_reps=REPS_WPUQ)


if __name__ == '__main__':
    main()
