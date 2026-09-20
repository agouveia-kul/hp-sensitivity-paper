"""Composition of the non-heat-pump reference group as an experimental factor.

Every design used so far fixes eheat_frac at 0.0: no non-heat-pump member has
any other electric heating. That makes the heat-pump-free reference group as
clean as the data allow, which is one defensible choice, not the only one -- a
real feeder's non-heat-pump population is not selected to be heating-free, it
just is whatever it is. The observed prevalence of other electric heating among
non-heat-pump-eligible households in the combined pool is 0.1937 (314 of 1621,
all on station KLO, the only station with non-heat-pump-eligible households at
all).

This builds the two arms eheat_frac=0.0 does not cover, at the SAME triangular
shape already used for the analysis set (N_total <= 50, no extension -- the
extension exists only for the confound heatmap and detection does not use it).
The heat pump tier is left alone (clean_hp=False) as before.

data/design_tri.pkl / data/tri_fits.parquet already ARE the eheat_frac=0.0 arm
and are not touched here.
"""
import warnings

import pandas as pd

warnings.filterwarnings('ignore')

import hp_design as hd
import hp_pools as hpp
import hp_analysis as ha

TRI_N = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
TRI_HP = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
TRI_REPS = 25

EHEAT_OBSERVED = 0.1937

ARMS = [
    ('observed', EHEAT_OBSERVED, 'data/design_tri_eheatobs.pkl',
     'data/tri_fits_eheatobs.parquet'),
    ('saturated', 1.0, 'data/design_tri_eheat1.pkl',
     'data/tri_fits_eheat1.parquet'),
]


def main():
    pool = hpp.build_pool_combined(verbose=False)

    for label, frac, design_path, fits_path in ARMS:
        design, cov = hd.generate_design(
            pool, n_grid=TRI_N, hp_grid=TRI_HP, n_reps=TRI_REPS,
            eheat_frac=frac, clean_hp=False, seed=42, verbose=False)
        meta = design['meta']
        print(f'[{label}] eheat_frac={frac}: {len(meta)} substations, cells filled '
              f'{int(cov.filled.sum())}/{int(cov.requested.sum())}', flush=True)
        skipped = cov[cov.skipped > 0]
        for _, r in skipped.iterrows():
            print(f"  SKIPPED N_total={r['N_total']:>4} N_hp={r['N_hp']:>3}: "
                  f"{r['reason']}", flush=True)
        hd.save_design(design, design_path)

        fits = ha.fit_all(design, verbose=False)
        fits.to_parquet(fits_path)
        print(f'[{label}] {len(fits)} fits, {int(fits.failed.sum())} failed', flush=True)

        d24 = fits[(fits.response == 'Load') & (fits.resolution == '24 h') &
                   (~fits.failed)]
        for stat in ['slope', 'slope_per_peak']:
            det = ha.detection_threshold(d24.assign(resolution='24 h'), stat, '24 h')
            _, auc = ha.roc(d24.assign(resolution='24 h'), stat, '24 h')
            print(f'  {stat:16s} AUC {auc:.4f}  sensitivity {det["sensitivity"]:.4f} '
                  f'at FPR {det["observed_fpr"]:.3f}', flush=True)
        print(flush=True)


if __name__ == '__main__':
    main()
