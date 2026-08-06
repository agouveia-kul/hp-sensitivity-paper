"""Rebuild every design under one composition rule.

The rule is a separation between electric and non-electric heating, not between
heat pumps and everything else:

* a NON-heat-pump member must have no electric heating of any kind -- no
  electric water heater, no storage or direct heating, no auxiliary or
  water-heating heat pump. In practice these households heat with gas, oil or
  district heat, so the reference group is genuinely free of temperature-driven
  electric load.
* a heat pump member may carry other electric heating as well. Requiring
  otherwise would cap the ladder at the 21 submetered heat pumps that are
  themselves clean, and the strict variant shows it changes nothing: with the
  heat pump tier also cleaned, sensitivity at 20 heat pumps and 200 consumers
  moves from 3.57 to 3.58 kW/K.

This is ``eheat_frac=0.0`` with ``clean_hp=False``. The previous runs used
``eheat_frac=None`` (natural prevalence), which left about one non-heat-pump
member in five carrying an electric water heater and inflated the heat-pump-free
reference group the detection threshold is calibrated against.

WPUQ is deliberately not rebuilt here: it carries no appliance metadata, so its
``eheat_households`` is empty and ``eheat_frac=0.0`` reduces to exactly the same
draw as before. The German controls are clean by construction anyway, since they
are built by omitting the heat pump circuit from a metered house.

Everything else the notebook reads is produced here: the triangular design and
its rectangular extension, the wide design and its HDH fits, the houses-only
clustered arm, and the strict variant. Expect roughly an hour end to end.
"""
import warnings

import pandas as pd

warnings.filterwarnings('ignore')

import hp_design as hd
import hp_pools as hpp
import hp_analysis as ha

TRI_N = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100, 150, 200]
TRI_HP = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
TRI_REPS = 25

# Strict variant: the heat pump tier cleaned as well, which the notebook uses to
# show the exclusion buys nothing. Only 21 submetered heat pumps are themselves
# clean, so the ladder stops at 20; the extension columns are kept because the
# confound read is what the comparison is about.
STRICT_N = [5, 10, 15, 20, 50, 100, 150, 200]
STRICT_HP = [0, 5, 10, 15, 20]

# composition rule, applied identically everywhere
RULE = dict(eheat_frac=0.0, clean_hp=False, seed=42, verbose=False)


def build(pool, label, design_path, fits_path, hdh_path=None, rule=RULE, **grid):
    design, cov = hd.generate_design(pool, **grid, **rule)
    meta = design['meta']
    print(f'[{label}] {len(meta)} substations, cells filled '
          f'{int(cov.filled.sum())}/{int(cov.requested.sum())}', flush=True)
    print(pd.crosstab(meta.N_total, meta.N_hp).to_string(), flush=True)
    skipped = cov[cov.skipped > 0]
    for _, r in skipped.iterrows():
        print(f"  SKIPPED N_total={r['N_total']:>4} N_hp={r['N_hp']:>3}: "
              f"{r['reason']}", flush=True)
    # every remaining flagged member is a heat pump household, by construction
    print(f'[{label}] flagged members per substation: '
          f'median {meta.N_eheat_realised.median():.0f}, '
          f'max {meta.N_eheat_realised.max():.0f} '
          f'(all of them heat pump households)', flush=True)
    hd.save_design(design, design_path)

    fits = ha.fit_all(design, verbose=False)
    fits.to_parquet(fits_path)
    print(f'[{label}] {len(fits)} fits, {int(fits.failed.sum())} failed', flush=True)
    if hdh_path:
        ha.fit_hdh_all(design, verbose=False).to_parquet(hdh_path)
        print(f'[{label}] HDH fits -> {hdh_path}', flush=True)

    d24 = fits[(fits.response == 'Load') & (fits.resolution == '24 h') &
               (~fits.failed)]
    print(f'[{label}] median sensitivity (kW/K), rows N_hp, columns N_total:',
          flush=True)
    print(d24.pivot_table(index='N_hp', columns='N_total', values='slope',
                          aggfunc='median').round(2).to_string(), flush=True)
    print(flush=True)


def main():
    pool = hpp.build_pool_combined(verbose=False)

    build(pool, 'triangular', 'data/design_tri.pkl', 'data/tri_fits.parquet',
          hdh_path='data/tri_hdh_fits.parquet',
          n_grid=TRI_N, hp_grid=TRI_HP, n_reps=TRI_REPS)

    groups = hpp.dwelling_groups(pool)
    houses = [h for h in pool['households'] if groups[h] == 'house']
    build(hpp.restrict_pool(pool, houses, verbose=False), 'clustered houses',
          'data/design_clustered.pkl', 'data/clustered_fits.parquet',
          n_grid=[5, 10, 15, 20, 25, 30, 35, 40, 45, 50], hp_grid=TRI_HP,
          n_reps=TRI_REPS)

    build(pool, 'strict', 'data/design_tri_strict.pkl',
          'data/tri_strict_fits.parquet',
          rule=dict(RULE, clean_hp=True),
          n_grid=STRICT_N, hp_grid=STRICT_HP, n_reps=TRI_REPS)

    # WPUQ: the same triangular shape on the 37 available households. No
    # extension, because every WPUQ household owns a heat pump, so N_hp can
    # always reach N_total and there is nothing to the right of the triangle.
    build(hpp.build_pool_wpuq(verbose=False), 'wpuq',
          'data/design_wpuq_val.pkl', 'data/wpuq_val_fits.parquet',
          n_grid=[5, 10, 15, 20, 25, 30, 35],
          hp_grid=[0, 5, 10, 15, 20, 25, 30, 35], n_reps=40)


if __name__ == '__main__':
    main()
