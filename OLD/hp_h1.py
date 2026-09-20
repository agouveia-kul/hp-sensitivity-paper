"""Hypothesis 1: does the response have a TEMPERATURE THRESHOLD?

The previous test fitted one straight line with ``linregress`` and counted a
substation as supporting the hypothesis when the slope was negative with
p < alpha. That tests the wrong null: "slope != 0" is the trivially-rejected
sub-claim that the response reacts to temperature at all. The actual hypothesis
is that the response is **hockey-stick** -- sloped below a balance temperature
and flat above it.

    H0 : y = a + b * T                        (single straight line)
    H1 : y = a + b * max(0, T_bal - T)        (hockey stick)

Under H0 the breakpoint ``T_bal`` is unidentified (the Davies problem), so the
likelihood-ratio statistic does **not** have a chi-squared null distribution and
neither ``scipy.stats.chi2`` nor ``scipy.stats.f`` is valid here. The null is
therefore obtained by a **parametric (residual) bootstrap** from the H0 fit.

Implementation note -- why not ``curve_fit`` in the inner loop
--------------------------------------------------------------
For a *fixed* ``T_bal`` the hockey stick is linear in ``(a, b)``, so the fit is
a closed-form 2-parameter OLS. Profiling ``T_bal`` over a fine grid and taking
the best RSS is the standard way to fit a threshold/segmented model: it is
exact up to the grid step, cannot land in a local minimum, and cannot fail to
converge. That matters because the test needs ~10^6 fits. ``curve_fit`` is used
only where a single fit is wanted. The RSS_hockey = RSS_linear guard the brief
asks for is retained for degenerate designs (see ``_profile_rss``).
"""

import os
import pickle

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from statsmodels.stats.proportion import proportion_confint

import hp_design as hd
from hp_common import min_points_for_resolution

ALPHA = 0.05
N_BOOT = 999          # full run
N_BOOT_QUICK = 99     # development runs (set QUICK=True in the notebook)

# Balance-temperature search grid. Matches T_BALANCE_BOUNDS from hp_common but
# is profiled rather than optimised, so the step size is the resolution of the
# T_bal estimate.
TBAL_GRID = np.arange(8.0, 20.001, 0.1)

# Moving-block length for the bootstrap, in days. Daily load residuals are
# serially correlated (median lag-1 autocorrelation ~0.46 in the zero-HP
# controls). An i.i.d. residual bootstrap ignores this and is badly
# anti-conservative: under a TRUE straight line with AR(1) noise it rejects at
# 0.11 / 0.18 / 0.25 for rho = 0.3 / 0.6 / 0.8 instead of 0.05. A 30-day moving
# block restores calibration (0.060 / 0.060 / 0.075) without costing power.
BLOCK_LEN = 30

CACHE_DIR = 'data/h1_cache'


# ---------------------------------------------------------------------------
# Closed-form fits
# ---------------------------------------------------------------------------
def _linear_fit(T, y):
    """OLS of y on T. Returns (a, b, rss, fitted)."""
    n = len(y)
    Sx, Sy = T.sum(), y.sum()
    Sxx, Sxy = T @ T, T @ y
    denom = n * Sxx - Sx * Sx
    if abs(denom) < 1e-12:
        a, b = float(y.mean()), 0.0
    else:
        b = (n * Sxy - Sx * Sy) / denom
        a = (Sy - b * Sx) / n
    fitted = a + b * T
    rss = float(((y - fitted) ** 2).sum())
    return a, b, rss, fitted


def _hockey_design(T, grid=TBAL_GRID):
    """Precompute max(0, T_bal - T) for every T_bal on the grid.

    Returns (G, n, Sx, Sxx, valid) where G is (n_grid, n_points). Computing this
    once per substation is what makes the bootstrap affordable: each replicate
    then costs one matrix-vector product plus vectorised scalar algebra.
    """
    G = np.maximum(0.0, grid[:, None] - T[None, :])
    n = T.shape[0]
    Sx = G.sum(axis=1)
    Sxx = (G * G).sum(axis=1)
    denom = n * Sxx - Sx * Sx
    valid = np.abs(denom) > 1e-9        # False where the column is constant
    return G, n, Sx, Sxx, denom, valid


def _profile_rss(design, y, rss_fallback):
    """Best hockey-stick RSS over the T_bal grid, by closed-form OLS.

    `rss_fallback` is returned when no grid point yields an identifiable design
    -- the "curve_fit failed" case the brief asks to handle as *no improvement*
    (RSS_hockey = RSS_linear) rather than by dropping the replicate, which would
    bias the null distribution.
    Returns (rss, a, b, t_bal).
    """
    G, n, Sx, Sxx, denom, valid = design
    if not valid.any():
        return rss_fallback, np.nan, np.nan, np.nan
    Sy = y.sum()
    Syy = y @ y
    Sxy = G @ y
    with np.errstate(invalid='ignore', divide='ignore'):
        b = (n * Sxy - Sx * Sy) / denom
        a = (Sy - b * Sx) / n
        rss = Syy - (a * Sy + b * Sxy)
    rss = np.where(valid, rss, np.inf)
    rss = np.where(np.isfinite(rss), rss, np.inf)
    k = int(np.argmin(rss))
    if not np.isfinite(rss[k]):
        return rss_fallback, np.nan, np.nan, np.nan
    return float(max(rss[k], 0.0)), float(a[k]), float(b[k]), float(TBAL_GRID[k])


# ---------------------------------------------------------------------------
# The test
# ---------------------------------------------------------------------------
def _resample_residuals(resid, n, rng, block):
    """Draw a bootstrap residual series.

    block=1 is the plain i.i.d. residual bootstrap. block>1 is a moving-block
    bootstrap, which preserves short-range serial dependence.

    This matters: daily load residuals here have a median lag-1 autocorrelation
    of ~0.46, and an i.i.d. bootstrap destroys it. That makes the null
    distribution of the statistic too narrow and the test badly
    anti-conservative -- in simulation, a TRUE straight line with AR(1) noise
    rejects at 0.11 / 0.18 / 0.25 for rho = 0.3 / 0.6 / 0.8 instead of 0.05.
    """
    if block <= 1:
        return rng.choice(resid, size=n, replace=True)
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, len(resid) - block + 1, size=n_blocks)
    return np.concatenate([resid[s:s + block] for s in starts])[:n]


def threshold_bootstrap_p(T, y, n_boot=N_BOOT, rng=None, grid=TBAL_GRID,
                          block=1):
    """H0: single straight line. H1: hockey stick.

    Returns (p_value, observed_statistic, fitted_params).

    Statistic      : (RSS_linear - RSS_hockey) / RSS_hockey
    Null resampling: residual bootstrap from the H0 linear fit, i.i.d. when
                     `block` is 1 and moving-block when `block` > 1
    p              : (1 + #{stat_null >= stat_obs}) / (n_boot + 1)

    The +1 correction keeps the p-value valid (it can never be exactly 0).
    """
    T = np.asarray(T, dtype=float)
    y = np.asarray(y, dtype=float)
    rng = np.random.default_rng() if rng is None else rng

    a_lin, b_lin, rss_lin, fitted_lin = _linear_fit(T, y)
    design = _hockey_design(T, grid)
    rss_hock, a_h, b_h, t_bal = _profile_rss(design, y, rss_fallback=rss_lin)

    denom = rss_hock if rss_hock > 1e-12 else 1e-12
    stat_obs = (rss_lin - rss_hock) / denom

    resid = y - fitted_lin
    n = len(y)
    ge = 0
    for _ in range(n_boot):
        y_star = fitted_lin + _resample_residuals(resid, n, rng, block)
        _, _, rss_lin_b, _ = _linear_fit(T, y_star)
        rss_hock_b, _, _, _ = _profile_rss(design, y_star, rss_fallback=rss_lin_b)
        d_b = rss_hock_b if rss_hock_b > 1e-12 else 1e-12
        if (rss_lin_b - rss_hock_b) / d_b >= stat_obs:
            ge += 1

    p_value = (1.0 + ge) / (n_boot + 1.0)
    params = {'base': a_h, 'slope': b_h, 't_bal': t_bal,
              'a_linear': a_lin, 'b_linear': b_lin,
              'rss_linear': rss_lin, 'rss_hockey': rss_hock, 'n_days': n}
    return p_value, float(stat_obs), params


# ---------------------------------------------------------------------------
# Per-substation driver
# ---------------------------------------------------------------------------
def daily_response(design, sid, response):
    """Daily-mean (temperature, response) for one substation.

    All days are kept -- including summer. The flat warm regime is exactly what
    identifies the breakpoint, so restricting to the heating season would remove
    the evidence the test relies on.
    """
    temp = hd.get_series(design, sid, 'Temperature').resample('D').mean()
    if response == 'SF':
        hp_peak = design['meta'].loc[sid, 'HP_Peak']
        if not hp_peak > 0:
            return None                      # SF undefined at zero penetration
        y = (hd.get_series(design, sid, 'HP_Load') / hp_peak).resample('D').mean()
    elif response == 'NetLoad':
        y = hd.get_series(design, sid, 'Total_Load').resample('D').mean()
    else:
        raise ValueError(f'unknown response {response!r}')
    d = pd.DataFrame({'T': temp, 'y': y}).dropna()
    if len(d) < min_points_for_resolution('D') or d['T'].nunique() < 3:
        return None
    return d['T'].to_numpy(), d['y'].to_numpy()


def _one_substation(sid, T, y, meta, response, n_boot, seed, block=1):
    """Run the test for one substation.

    Takes the already-extracted daily arrays rather than the design dict: the
    design is ~240 MB and joblib would otherwise pickle a copy of it to every
    worker, which costs far more than the fits themselves.
    """
    p, stat, params = threshold_bootstrap_p(
        T, y, n_boot=n_boot, rng=np.random.default_rng(seed), block=block)
    return {
        'substation_id': int(sid), 'response': response,
        'p_value': p, 'stat': stat, 'reject': bool(p < ALPHA),
        **params,
        # ground-truth design variables: stratification only, never model inputs
        'N_total': int(meta['N_total']), 'N_hp': int(meta['N_hp']),
        'hp_ratio': float(meta['hp_ratio']), 'weather_id': meta['weather_id'],
    }


def run_h1(design, ids, response, n_boot=N_BOOT, n_jobs=-1, chunk=100,
           cache_path=None, resume=True, seed=12345, verbose=True,
           block=BLOCK_LEN):
    """Run the threshold bootstrap over `ids`, caching incrementally.

    Results are appended to `cache_path` after every chunk, so an interrupted
    run resumes instead of refitting.
    """
    if cache_path is None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_path = os.path.join(CACHE_DIR, f'h1_{response}_{n_boot}_b{block}.pkl')

    done = {}
    if resume and os.path.exists(cache_path):
        with open(cache_path, 'rb') as fh:
            done = {r['substation_id']: r for r in pickle.load(fh)}
        if verbose:
            print(f'resuming: {len(done)} substations already cached in {cache_path}')

    todo = [int(s) for s in ids if int(s) not in done]
    if verbose:
        print(f'{response}: {len(todo)} substations to fit '
              f'({n_boot} bootstrap replicates each)')

    # Extract the daily series up front (~2 ms each) so the parallel workers
    # receive only small arrays, never the full design.
    prepared = []
    n_skip = 0
    for sid in todo:
        out = daily_response(design, sid, response)
        if out is None:
            n_skip += 1
            continue
        prepared.append((sid, out[0], out[1], design['meta'].loc[sid]))
    if verbose and n_skip:
        print(f'  {n_skip} substations skipped (response undefined or too few days)')

    for start in range(0, len(prepared), chunk):
        batch = prepared[start:start + chunk]
        res = Parallel(n_jobs=n_jobs, verbose=0)(
            delayed(_one_substation)(sid, T, y, meta, response, n_boot,
                                     seed + sid, block)
            for sid, T, y, meta in batch)
        for r in res:
            if r is not None:
                done[r['substation_id']] = r
        with open(cache_path, 'wb') as fh:
            pickle.dump(list(done.values()), fh, protocol=4)
        if verbose:
            print(f'  {min(start + chunk, len(prepared))}/{len(prepared)} done '
                  f'({len(done)} cached)')

    df = pd.DataFrame(list(done.values())).set_index('substation_id').sort_index()
    return df


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def wilson(count, nobs):
    """Wilson binomial confidence interval for a rejection proportion."""
    if nobs == 0:
        return (np.nan, np.nan)
    return proportion_confint(count, nobs, alpha=ALPHA, method='wilson')


def rejection_table(df, by):
    """Rejection proportion with Wilson CI, stratified by `by`."""
    rows = []
    for key, grp in df.groupby(by):
        k, n = int(grp['reject'].sum()), len(grp)
        lo, hi = wilson(k, n)
        tb = grp.loc[grp['reject'], 't_bal'].dropna()
        rows.append({
            by: key, 'n': n, 'n_reject': k, 'reject_rate': k / n,
            'ci_low': lo, 'ci_high': hi,
            'tbal_median': tb.median() if len(tb) else np.nan,
            'tbal_q25': tb.quantile(.25) if len(tb) else np.nan,
            'tbal_q75': tb.quantile(.75) if len(tb) else np.nan,
        })
    return pd.DataFrame(rows)


def detection_limit(tab, by='hp_ratio', threshold=0.8):
    """Lowest penetration whose rejection rate exceeds `threshold`."""
    ok = tab[(tab[by] > 0) & (tab['reject_rate'] > threshold)]
    return float(ok[by].min()) if len(ok) else np.nan


def control_check(df_netload, alpha=ALPHA):
    """Type I error check on the hp_ratio == 0 substations.

    The controls contain no heat pump, so the rejection rate must sit near
    alpha. A materially higher rate means the test itself is broken and nothing
    else in the output can be trusted.
    """
    ctrl = df_netload[df_netload['hp_ratio'] == 0.0]
    k, n = int(ctrl['reject'].sum()), len(ctrl)
    lo, hi = wilson(k, n)
    ok = bool(lo <= alpha <= hi) or (k / n <= alpha if n else False)
    return {'n': n, 'n_reject': k, 'rate': (k / n) if n else np.nan,
            'ci_low': lo, 'ci_high': hi, 'consistent_with_alpha': ok}


# ---------------------------------------------------------------------------
# Secondary: is the response linear below the threshold?
# ---------------------------------------------------------------------------
def curvature_test(design, df, response, t_bal_map=None, alpha=ALPHA):
    """Refit below T_bal with a quadratic term and test H0: c = 0.

    `t_bal_map` supplies an externally estimated T_bal per substation. When it
    is None the substation's own estimate is reused, which makes the nominal
    t-test mildly optimistic because the breakpoint was chosen on the same data.
    """
    import statsmodels.api as sm
    rows = []
    for sid, r in df.iterrows():
        t_bal = (t_bal_map.get(sid, np.nan) if t_bal_map is not None
                 else r['t_bal'])
        if not np.isfinite(t_bal):
            continue
        out = daily_response(design, sid, response)
        if out is None:
            continue
        T, y = out
        m = T < t_bal
        if m.sum() < 12:
            continue
        x = t_bal - T[m]
        X = sm.add_constant(np.column_stack([x, x ** 2]))
        try:
            fit = sm.OLS(y[m], X).fit()
        except Exception:
            continue
        rows.append({'substation_id': sid, 'c': fit.params[2],
                     'p_c': fit.pvalues[2], 'n_below': int(m.sum()),
                     'hp_ratio': r['hp_ratio'], 'N_hp': r['N_hp']})
    out = pd.DataFrame(rows)
    if len(out):
        out['reject_linear'] = out['p_c'] < alpha
    return out
