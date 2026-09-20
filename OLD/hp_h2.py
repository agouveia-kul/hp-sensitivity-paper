"""Hypothesis 2: does hockey-stick fit quality improve as resolution coarsens?

Per substation the net load and temperature are averaged to 15 min / 1 h / 8 h /
daily and a hockey stick is fitted at each, giving four **paired** observations
per substation (complete cases only).

Three things the first pass got wrong or omitted:

3a. ``friedmanchisquare`` is an *unordered* omnibus -- it asks only whether the
    four resolutions differ. The alternative here is ordered
    (daily > 8h > 1h > 15min), so **Page's trend test** is both the correct
    instrument and more powerful. The Wilcoxon post-hoc is extended from the
    single daily-vs-15min contrast to all adjacent pairs plus the extreme pair,
    Holm-corrected.

3b. A rising R² under averaging is **partly mechanical**: averaging strips
    high-frequency variance that was largely unexplained, so R² is close to
    obliged to increase and the p-value will be ~0 regardless. The substantive
    result is the **effect size** -- the ``log_dt`` coefficient of a
    mixed-effects model on logit(R²), with its 95% CI -- and whether the
    averaging benefit interacts with penetration.

3c. Coarsening averages the **regressor** as well as the response, reducing
    attenuation bias, so the fitted **slope** should drift upward too, not just
    R². The loop therefore keeps ``base``, ``slope`` and ``T_balance``.
"""

import os
import pickle

import numpy as np
import pandas as pd
from scipy.special import logit
from scipy.stats import page_trend_test, wilcoxon
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf

import hp_design as hd
from hp_common import (fit_hockey_stick, min_points_for_resolution,
                       T_BALANCE_BOUNDS)

# Ordered by hypothesised INCREASING R². Page's test needs this ordering.
RESOLUTIONS = [('15min', '15 min', 15), ('1h', '1 hour', 60),
               ('8h', '8 hours', 480), ('D', 'daily', 1440)]
LABELS = [lab for _, lab, _ in RESOLUTIONS]

CACHE_PATH = 'data/h2_fits.parquet'


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------
def fit_by_resolution(design, ids, cache_path=CACHE_PATH, rebuild=False,
                      verbose=True):
    """Fit the hockey stick at every resolution for every substation.

    Returns a tidy long-format table (one row per substation x resolution) with
    base / slope / T_balance / r2 retained -- the slope is needed for the
    errors-in-variables check in 3c, and discarding it would make that
    impossible.
    """
    if os.path.exists(cache_path) and not rebuild:
        if verbose:
            print(f'loading cached H2 fits from {cache_path}')
        return pd.read_parquet(cache_path)

    meta = design['meta']
    rows = []
    for k, sid in enumerate(ids):
        sid = int(sid)
        total = hd.get_series(design, sid, 'Total_Load')
        temp = hd.get_series(design, sid, 'Temperature')
        m = meta.loc[sid]
        for rule, label, dt_min in RESOLUTIONS:
            d = pd.DataFrame({'T': temp.resample(rule).mean(),
                              'L': total.resample(rule).mean()}).dropna()
            rec = {'substation_id': sid, 'resolution': label,
                   'dt_minutes': dt_min, 'n_points': len(d),
                   'N_total': int(m['N_total']), 'N_hp': int(m['N_hp']),
                   'hp_ratio': float(m['hp_ratio']), 'weather_id': m['weather_id'],
                   'base': np.nan, 'slope': np.nan, 't_balance': np.nan,
                   'r2': np.nan, 'failed': True, 'fail_reason': ''}
            if len(d) < min_points_for_resolution(rule):
                rec['fail_reason'] = 'too_few_points'
            else:
                try:
                    b, s, tb, r2 = fit_hockey_stick(d['T'].to_numpy(),
                                                    d['L'].to_numpy(),
                                                    T_BALANCE_BOUNDS)
                    rec.update(base=b, slope=s, t_balance=tb, r2=r2,
                               failed=False)
                except Exception as exc:
                    rec['fail_reason'] = type(exc).__name__
            rows.append(rec)
        if verbose and (k + 1) % 200 == 0:
            print(f'  {k + 1}/{len(ids)} substations fitted')

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_parquet(cache_path)
    if verbose:
        print(f'saved {len(df)} rows -> {cache_path}')
    return df


def to_wide(df):
    """Complete-case wide table (substations fitted at ALL four resolutions)."""
    ok = df[~df['failed']]
    wide = ok.pivot(index='substation_id', columns='resolution', values='r2')
    wide = wide.reindex(columns=LABELS)
    return wide.dropna()


def dropout_audit(df, wide):
    """Which substations are lost to `dropna`, and where do failures cluster."""
    all_ids = df['substation_id'].unique()
    kept = set(wide.index)
    lost = [s for s in all_ids if s not in kept]
    print(f'complete cases: {len(kept)} of {len(all_ids)} substations '
          f'({len(lost)} dropped for failing at >=1 resolution)')
    if not lost:
        return
    bad = df[df['substation_id'].isin(lost) & df['failed']]
    print('\n  failures by resolution:')
    print(bad['resolution'].value_counts().to_string())
    print('\n  failures by reason:')
    print(bad['fail_reason'].value_counts().to_string())
    print('\n  dropped substations by penetration:')
    tab = (df[df['substation_id'].isin(lost)]
           .drop_duplicates('substation_id')['hp_ratio'].value_counts().sort_index())
    tot = df.drop_duplicates('substation_id')['hp_ratio'].value_counts().sort_index()
    print(pd.DataFrame({'dropped': tab, 'total': tot,
                        'frac': (tab / tot).round(3)}).fillna(0).to_string())


# ---------------------------------------------------------------------------
# 3a -- ordered trend test + Holm-corrected post-hoc
# ---------------------------------------------------------------------------
def page_test(wide):
    """Page's L for the ordered alternative daily > 8h > 1h > 15min."""
    res = page_trend_test(wide[LABELS].to_numpy(), ranked=False)
    return res


def pairwise_wilcoxon(wide, alpha=0.05):
    """Adjacent pairs plus the extreme pair, Holm-corrected."""
    pairs = [(LABELS[0], LABELS[1]), (LABELS[1], LABELS[2]),
             (LABELS[2], LABELS[3]), (LABELS[0], LABELS[3])]
    rows = []
    for a, b in pairs:
        stat, p = wilcoxon(wide[b], wide[a], alternative='greater')
        rows.append({'pair': f'{b} > {a}', 'stat': stat, 'p_raw': p,
                     'median_diff': float((wide[b] - wide[a]).median())})
    out = pd.DataFrame(rows)
    rej, p_adj, _, _ = multipletests(out['p_raw'], alpha=alpha, method='holm')
    out['p_holm'], out['reject'] = p_adj, rej
    return out


# ---------------------------------------------------------------------------
# 3b -- effect size
# ---------------------------------------------------------------------------
def negative_r2_audit(df):
    """Count substation-resolution pairs with R2 < 0.

    A negative R2 means the constrained hockey stick fits worse than the mean.
    With base >= 0 and slope >= 0 that is a legitimate "no threshold present"
    outcome rather than a numerical failure -- most of them are the zero-
    penetration controls -- but clipping them to 1e-4 before the logit collapses
    them all onto one value, so the models are also refitted with them dropped.
    """
    ok = df[~df['failed']]
    neg = ok[ok['r2'] < 0]
    print(f'R2 < 0 in {len(neg)} of {len(ok)} substation-resolution pairs '
          f'({len(neg) / len(ok):.1%})')
    if len(neg):
        print('\n  by resolution:')
        print(neg['resolution'].value_counts().reindex(LABELS).fillna(0).to_string())
        print('\n  by penetration (share of that stratum):')
        a = neg.groupby('hp_ratio').size()
        b = ok.groupby('hp_ratio').size()
        print(pd.DataFrame({'neg': a, 'total': b,
                            'frac': (a / b).round(3)}).fillna(0).to_string())
    return neg


def effect_size_model(df, drop_negative=False, eps=1e-4):
    """Mixed-effects model of logit(R2) on log(dt), substation as random effect."""
    d = df[~df['failed']].copy()
    if drop_negative:
        d = d[d['r2'] > 0]
    d['logit_r2'] = logit(d['r2'].clip(eps, 1 - eps))
    d['log_dt'] = np.log(d['dt_minutes'])
    fit = smf.mixedlm('logit_r2 ~ log_dt', d, groups=d['substation_id']).fit()
    return fit, d


def interaction_model(d):
    """Does the averaging benefit depend on penetration?"""
    return smf.mixedlm('logit_r2 ~ log_dt * hp_ratio', d,
                       groups=d['substation_id']).fit()


def coef_ci(fit, name='log_dt'):
    ci = fit.conf_int().loc[name]
    return float(fit.params[name]), float(ci[0]), float(ci[1]), float(fit.pvalues[name])
