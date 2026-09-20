"""Cross-dataset comparison: do the HEAPO conclusions replicate?

HEAPO (Swiss, submetered)  -- primary, where the conclusions were formed
Swiss  (large consumer pool) -- complements: lifts the N_total ceiling
WPUQ   (German, submetered) -- independent validation: different country,
                               climate, households and measurement chain

A conclusion counts as replicated when the *direction and rough magnitude* hold,
not when the numbers coincide -- the datasets differ in penetration range,
household count and climate.
"""
import warnings

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare

warnings.filterwarnings('ignore')

import hp_h1 as h1
import hp_h2 as h2

DATASETS = {
    'HEAPO': {'h1': 'data/h1_results_block.parquet', 'h2': 'data/h2_fits.parquet'},
    'Swiss (all)': {'h1': 'data/swiss_h1.parquet', 'h2': 'data/swiss_h2_fits.parquet'},
    'Swiss (clean)': {'h1': 'data/swiss_clean_h1.parquet',
                      'h2': 'data/swiss_clean_h2_fits.parquet'},
    'WPUQ':  {'h1': 'data/wpuq_h1.parquet', 'h2': 'data/wpuq_h2_fits.parquet'},
}


def _load(path):
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def h1_summary(name, path):
    t = _load(path)
    if t is None:
        return None
    sf, nl = t[t.response == 'SF'], t[t.response == 'NetLoad']
    ctrl = nl[nl.N_hp == 0]
    lo, hi = h1.wilson(int(ctrl.reject.sum()), len(ctrl)) if len(ctrl) else (np.nan, np.nan)
    row = {
        'dataset': name,
        'n_sf': len(sf), 'n_netload': len(nl), 'n_controls': len(ctrl),
        'control_rate': ctrl.reject.mean() if len(ctrl) else np.nan,
        'control_ci': f'[{lo:.3f}, {hi:.3f}]' if len(ctrl) else '',
        'sf_detect_limit': h1.detection_limit(h1.rejection_table(sf, 'hp_ratio')) if len(sf) else np.nan,
        'nl_detect_limit': h1.detection_limit(h1.rejection_table(nl, 'hp_ratio')) if len(nl) else np.nan,
        'sf_tbal_median': sf.loc[sf.reject, 't_bal'].median() if len(sf) else np.nan,
        'nl_tbal_median': nl.loc[nl.reject, 't_bal'].median() if len(nl) else np.nan,
    }
    return row


def h2_summary(name, path):
    f = _load(path)
    if f is None:
        return None
    wide = h2.to_wide(f)
    if not len(wide):
        return None
    page = h2.page_test(wide)
    fit, d = h2.effect_size_model(f)
    b, lo, hi, _ = h2.coef_ci(fit)
    hp = f[(~f.failed) & (f.N_hp > 0)]
    s = hp.groupby('resolution').slope.median().reindex(h2.LABELS)
    r = wide.median()
    return {
        'dataset': name, 'n_substations': len(wide),
        'page_L': page.statistic, 'page_p': page.pvalue,
        'log_dt': b, 'log_dt_lo': lo, 'log_dt_hi': hi,
        'r2_15min': r[h2.LABELS[0]], 'r2_daily': r[h2.LABELS[-1]],
        'r2_ratio': r[h2.LABELS[-1]] / r[h2.LABELS[0]],
        'slope_15min': s.iloc[0], 'slope_daily': s.iloc[-1],
        'slope_ratio': s.iloc[-1] / s.iloc[0],
    }


def main():
    print('=' * 84)
    print('H1  THRESHOLD TEST -- replication across datasets')
    print('=' * 84)
    rows = [r for r in (h1_summary(n, p['h1']) for n, p in DATASETS.items()) if r]
    if rows:
        print(pd.DataFrame(rows).round(3).to_string(index=False))
        print('\n  control_rate is the false-positive floor (no heat pumps present).')
        print('  detect_limit = lowest penetration with >80% rejection.')

    print('\n' + '=' * 84)
    print('H2  RESOLUTION EFFECT -- replication across datasets')
    print('=' * 84)
    rows2 = [r for r in (h2_summary(n, p['h2']) for n, p in DATASETS.items()) if r]
    if rows2:
        df = pd.DataFrame(rows2)
        print(df.round(4).to_string(index=False))
        print('\n  log_dt is the headline effect size: change in logit(R2) per e-fold of dt.')
        print('  slope_ratio ~1 supports response-variance reduction rather than')
        print('  regressor de-attenuation (the errors-in-variables prediction).')

    print('\n' + '=' * 84)
    print('VERDICT')
    print('=' * 84)
    if rows2:
        df = pd.DataFrame(rows2)
        same_sign = (df.log_dt > 0).all()
        overlap = (df.log_dt.min() > 0) and (df.log_dt_hi.max() / max(df.log_dt_lo.min(), 1e-9) < 10)
        print(f'  H2 direction (R2 rises as dt coarsens) holds in '
              f'{int((df.log_dt > 0).sum())}/{len(df)} datasets: '
              f'{"REPLICATED" if same_sign else "NOT replicated"}')
        print(f'  slope stability (ratio within 0.8-1.25) in '
              f'{int(df.slope_ratio.between(0.8, 1.25).sum())}/{len(df)} datasets')
    if rows:
        d1 = pd.DataFrame(rows)
        print(f'  H1 control floor above alpha=0.05 in '
              f'{int((d1.control_rate > 0.05).sum())}/{len(d1)} datasets '
              f'(range {d1.control_rate.min():.3f}-{d1.control_rate.max():.3f})')

    print('\n' + '=' * 84)
    print('CONTROL FLOOR vs SUBSTATION SIZE  (the net-load result that matters)')
    print('=' * 84)
    tab = {}
    for name, paths in DATASETS.items():
        t = _load(paths['h1'])
        if t is None:
            continue
        nl = t[t.response == 'NetLoad']
        c = nl[nl.N_hp == 0]
        if len(c):
            tab[name] = c.groupby('N_total').reject.mean().round(3)
    if tab:
        print(pd.DataFrame(tab).to_string())
        print('\n  Non-HP load is not temperature-inert: gas/oil-heated dwellings still')
        print('  run circulation pumps and controls in winter. Aggregating more of them')
        print('  averages away noise, so the test gains power to detect that small real')
        print('  signal -- the false-positive floor RISES with substation size.')


if __name__ == '__main__':
    main()
