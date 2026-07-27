"""Task 4: the data collapse.

Claim: spatial aggregation (more households) and temporal averaging (coarser
dt) reduce estimator variance by the same mechanism, so fit quality should be
governed by an effective sample size ``N_eff ~ N * dt`` rather than by N and dt
separately. If true, points from very different (N, dt) combinations that share
a common product must fall on one curve.

Two things this module does that the claim needs:

* **Overlap check first.** If no distinct (N, dt) pairs land at comparable
  products there is nothing to collapse and the figure cannot test the law. This
  is cheap and gates the expensive fitting, so it runs first.
* **Both scalings.** The HP *signal* averages over the ``N_hp`` cycling heat
  pumps while the *noise* averages over all ``N_total`` households, so which
  product collapses better is itself the result. Both are fitted with the same
  functional form and compared by residual spread.

Slope confidence intervals use **HAC (Newey-West)** standard errors. Residuals
are strongly autocorrelated (see hp_h1), and naive OLS errors understate the
slope uncertainty by up to ~2.3x at 15 min resolution, which would flatter the
high-resolution end of exactly the trade-off being plotted.
"""

import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import logit

import hp_design as hd
from hp_common import fit_hockey_stick, min_points_for_resolution, T_BALANCE_BOUNDS

RESOLUTIONS = [('15min', '15 min', 15), ('1h', '1 hour', 60),
               ('8h', '8 hours', 480), ('D', 'daily', 1440)]
LABELS = [lab for _, lab, _ in RESOLUTIONS]
CACHE_PATH = 'data/collapse_fits.parquet'


# ---------------------------------------------------------------------------
# Overlap check -- run before the expensive fits
# ---------------------------------------------------------------------------
def overlap_check(meta, col='N_total', tol=0.2, verbose=True):
    """Do distinct (N, dt) pairs land at comparable N*dt products?

    Returns (clusters, table). A cluster is a set of >=2 distinct (N, dt) pairs
    whose products agree within `tol` (relative). Without clusters the collapse
    figure is untestable and the N grid needs re-spacing.
    """
    vals = sorted(v for v in meta[col].unique() if v > 0)
    rows = [{'N': n, 'resolution': lab, 'dt_minutes': dt, 'product': n * dt}
            for n in vals for _, lab, dt in RESOLUTIONS]
    tab = pd.DataFrame(rows).sort_values('product').reset_index(drop=True)

    clusters, used = [], set()
    for i in range(len(tab)):
        if i in used:
            continue
        grp = [j for j in range(len(tab))
               if abs(tab['product'][j] - tab['product'][i]) / tab['product'][i] <= tol]
        if len(grp) > 1:
            clusters.append([(int(tab['N'][j]), tab['resolution'][j]) for j in grp])
            used.update(grp)

    if verbose:
        span = tab['product'].max() / tab['product'].min()
        print(f'{col}: {len(vals)} levels x {len(RESOLUTIONS)} resolutions = '
              f'{len(tab)} combinations, {tab["product"].nunique()} distinct products, '
              f'range {span:.0f}x')
        print(f'  clusters with >=2 distinct (N, dt) pairs within {tol:.0%}: {len(clusters)}')
        for c in clusters:
            print(f'    {c}')
        if not clusters:
            print('  -> NOTHING TO COLLAPSE: the N grid needs widening/re-spacing.')
    return clusters, tab


# ---------------------------------------------------------------------------
# Fitting (keeps slope + HAC standard error)
# ---------------------------------------------------------------------------
def fit_collapse(design, ids=None, cache_path=CACHE_PATH, rebuild=False,
                 verbose=True):
    """Fit the hockey stick at every resolution, retaining slope CIs."""
    if os.path.exists(cache_path) and not rebuild:
        if verbose:
            print(f'loading cached collapse fits from {cache_path}')
        return pd.read_parquet(cache_path)

    meta = design['meta']
    ids = meta.index if ids is None else ids
    rows = []
    for k, sid in enumerate(ids):
        sid = int(sid)
        total = hd.get_series(design, sid, 'Total_Load')
        temp = hd.get_series(design, sid, 'Temperature')
        m = meta.loc[sid]
        for rule, label, dt_min in RESOLUTIONS:
            d = pd.DataFrame({'T': temp.resample(rule).mean(),
                              'L': total.resample(rule).mean()}).dropna()
            rec = {'substation_id': sid, 'resolution': label, 'dt_minutes': dt_min,
                   'n_points': len(d), 'N_total': int(m['N_total']),
                   'N_hp': int(m['N_hp']), 'hp_ratio': float(m['hp_ratio']),
                   'r2': np.nan, 'slope': np.nan, 'slope_se': np.nan,
                   't_balance': np.nan, 'failed': True}
            if len(d) >= min_points_for_resolution(rule):
                try:
                    T, y = d['T'].to_numpy(), d['L'].to_numpy()
                    b0, s, tb, r2 = fit_hockey_stick(T, y, T_BALANCE_BOUNDS)
                    # slope SE conditional on the fitted breakpoint, with HAC
                    # errors because the residuals are serially correlated
                    x = np.maximum(0.0, tb - T)
                    lag = max(1, int(len(y) ** 0.25))
                    ols = sm.OLS(y, sm.add_constant(x)).fit(
                        cov_type='HAC', cov_kwds={'maxlags': lag})
                    rec.update(r2=r2, slope=s, slope_se=float(ols.bse[1]),
                               t_balance=tb, failed=False)
                except Exception:
                    pass
            rows.append(rec)
        if verbose and (k + 1) % 200 == 0:
            print(f'  {k + 1}/{len(ids)} substations fitted')

    df = pd.DataFrame(rows)
    df['ci_halfwidth'] = 1.96 * df['slope_se']
    with np.errstate(divide='ignore', invalid='ignore'):
        df['ci_rel'] = df['ci_halfwidth'] / df['slope'].abs()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_parquet(cache_path)
    if verbose:
        print(f'saved {len(df)} rows -> {cache_path}')
    return df


# ---------------------------------------------------------------------------
# Collapse quality
# ---------------------------------------------------------------------------
def collapse_quality(df, n_col, deg=3, eps=1e-4):
    """Fit logit(R2) against log(N*dt) and measure the spread around the curve.

    The tighter the collapse, the smaller the residual spread. Both candidate
    scalings are fitted with the SAME functional form on the SAME rows, so the
    comparison is like-for-like.
    """
    d = df[(~df['failed']) & (df[n_col] > 0)].copy()
    d['neff'] = d[n_col] * d['dt_minutes']
    d['log_neff'] = np.log(d['neff'])
    d['logit_r2'] = logit(d['r2'].clip(eps, 1 - eps))
    coef = np.polyfit(d['log_neff'], d['logit_r2'], deg)
    pred = np.polyval(coef, d['log_neff'])
    resid = d['logit_r2'] - pred
    ss_tot = float(((d['logit_r2'] - d['logit_r2'].mean()) ** 2).sum())
    return {
        'n_col': n_col, 'n_rows': len(d), 'coef': coef,
        'resid_sd': float(resid.std()),
        'resid_iqr': float(resid.quantile(.75) - resid.quantile(.25)),
        'curve_r2': float(1 - (resid ** 2).sum() / ss_tot) if ss_tot > 0 else np.nan,
        'data': d,
    }


def find_knee(coef, log_lo, log_hi):
    """Point of maximum curvature of the fitted logit(R2) vs log(N*dt) curve."""
    xs = np.linspace(log_lo, log_hi, 500)
    d1 = np.polyval(np.polyder(coef, 1), xs)
    d2 = np.polyval(np.polyder(coef, 2), xs)
    curvature = np.abs(d2) / (1 + d1 ** 2) ** 1.5
    return float(np.exp(xs[int(np.argmax(curvature))]))
