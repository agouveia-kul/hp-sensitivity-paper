"""Analysis for the combined HEAPO + Swiss substation study.

Everything the notebook needs, in one place:

* multi-resolution hockey-stick fits of daily/sub-daily mean load and of the
  simultaneity factor against mean temperature
* the slope threshold at which a heat pump can be detected, given that
  substations with NO heat pumps also have non-zero slopes
* projected critical temperature (SF = 1)
* how fit quality varies with temporal resolution, spatial aggregation, and both

Detection note
--------------
A raw slope threshold cannot work across substation sizes: the slope grows with
BOTH heat pumps and ordinary consumers (~0.10-0.15 vs ~0.006 kW/degC each), so a
200-consumer substation with no heat pumps out-slopes a 20-consumer substation
with one. Detection therefore needs the slope normalised by something a DSO can
observe without a household census -- base load or peak load, never the consumer
count. All three statistics are scored here so the cost of that constraint is
visible.
"""

import numpy as np
import pandas as pd

import hp_design as hd
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

# Resolutions to compare. 'D' is 24 h; 16 h deliberately does not divide the day,
# which is harmless for a temperature regression but worth knowing.
RESOLUTIONS = [('1h', '1 h', 60), ('4h', '4 h', 240), ('8h', '8 h', 480),
               ('16h', '16 h', 960), ('D', '24 h', 1440)]
LABELS = [lab for _, lab, _ in RESOLUTIONS]
MIN_POINTS = 30


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------
def _series(design, sid):
    temp = hd.get_series(design, sid, 'Temperature')
    load = hd.get_series(design, sid, 'Total_Load')
    hp_peak = float(design['meta'].loc[sid, 'HP_Peak'])
    sf = (hd.get_series(design, sid, 'HP_Load') / hp_peak) if hp_peak > 0 else None
    return temp, load, sf, hp_peak


def fit_substation(design, sid, bounds=T_BALANCE_BOUNDS):
    """Fit load and SF against temperature at every resolution."""
    temp, load, sf, hp_peak = _series(design, sid)
    m = design['meta'].loc[sid]
    rows = []
    for rule, label, dt_min in RESOLUTIONS:
        t = temp.resample(rule).mean()
        frames = {'Load': load.resample(rule).mean()}
        if sf is not None:
            frames['SF'] = sf.resample(rule).mean()
        for resp, y in frames.items():
            d = pd.DataFrame({'T': t, 'y': y}).dropna()
            rec = {'substation_id': int(sid), 'response': resp,
                   'resolution': label, 'dt_minutes': dt_min,
                   'n_points': len(d), 'N_total': int(m['N_total']),
                   'N_hp': int(m['N_hp']), 'hp_ratio': float(m['hp_ratio']),
                   'HP_Peak': hp_peak, 'weather_id': m['weather_id'],
                   'N_eheat': int(m.get('N_eheat_realised', 0)),
                   'base': np.nan, 'slope': np.nan, 'T_threshold': np.nan,
                   'r2': np.nan, 'T_crit': np.nan, 'peak_load': np.nan,
                   'T_min_obs': np.nan, 'failed': True}
            if len(d) >= MIN_POINTS and d['T'].nunique() >= 3:
                try:
                    b, s, tb, r2 = fit_hockey_stick(d['T'].to_numpy(),
                                                    d['y'].to_numpy(), bounds)
                    rec.update(base=b, slope=s, T_threshold=tb, r2=r2,
                               failed=False,
                               peak_load=float(frames['Load'].max()),
                               T_min_obs=float(d['T'].min()))
                    if s > 0:
                        gap = (1.0 - b) if resp == 'SF' else hp_peak
                        if gap > 0:
                            rec['T_crit'] = tb - gap / s
                except Exception:
                    pass
            rows.append(rec)
    return rows


def fit_all(design, ids=None, verbose=True):
    ids = list(design['meta'].index) if ids is None else list(ids)
    out = []
    for k, sid in enumerate(ids):
        out.extend(fit_substation(design, int(sid)))
        if verbose and (k + 1) % 200 == 0:
            print(f'  {k + 1}/{len(ids)} substations fitted', flush=True)
    df = pd.DataFrame(out)
    ok = ~df['failed']
    df.loc[ok, 'slope_per_peak'] = df.loc[ok, 'slope'] / df.loc[ok, 'peak_load']
    df.loc[ok, 'slope_per_base'] = df.loc[ok, 'slope'] / df.loc[ok, 'base'].replace(0, np.nan)
    return df


# ---------------------------------------------------------------------------
# Alternative parameterisation: daily cumulative heating degree hours
#
# The hockey stick estimates its own breakpoint; HDH instead fixes a base
# temperature and integrates the shortfall below it, so the hinge is built into
# the regressor and the model is a plain line. If the consumer/heat-pump
# confound survives both parameterisations it is a property of the problem
# rather than of the estimator, which is the point of running it.
#
# HDH_THRESH is the base temperature already defined in hp_common and used by
# the rest of the pipeline. No second constant is introduced here.
# ---------------------------------------------------------------------------
def fit_hdh_all(design, ids=None, hdh_thresh=None, verbose=True):
    """Fit daily mean load against daily cumulative HDH for every substation.

    Returns the same schema the detection functions expect, so the identical
    analysis can be run on it without special-casing.
    """
    from hp_common import HDH_THRESH, daily_cumulative_hdh, fit_hdh_linear
    thresh = HDH_THRESH if hdh_thresh is None else hdh_thresh

    ids = list(design['meta'].index) if ids is None else list(ids)
    rows = []
    for k, sid in enumerate(ids):
        sid = int(sid)
        temp = hd.get_series(design, sid, 'Temperature')
        load = hd.get_series(design, sid, 'Total_Load')
        m = design['meta'].loc[sid]
        hdh = daily_cumulative_hdh(temp, thresh)
        daily_load = load.resample('D').mean()
        d = pd.DataFrame({'x': hdh, 'y': daily_load}).dropna()
        rec = {'substation_id': sid, 'response': 'Load_HDH', 'resolution': '24 h',
               'dt_minutes': 1440, 'n_points': len(d),
               'N_total': int(m['N_total']), 'N_hp': int(m['N_hp']),
               'hp_ratio': float(m['hp_ratio']), 'HP_Peak': float(m['HP_Peak']),
               'base': np.nan, 'slope': np.nan, 'r2': np.nan,
               'peak_load': np.nan, 'failed': True}
        if len(d) >= MIN_POINTS and (d['x'] > 0).sum() >= MIN_POINTS:
            try:
                b, s, r2 = fit_hdh_linear(d['x'].to_numpy(), d['y'].to_numpy())
                rec.update(base=b, slope=s, r2=r2, failed=False,
                           peak_load=float(daily_load.max()))
            except Exception:
                pass
        rows.append(rec)
        if verbose and (k + 1) % 300 == 0:
            print(f'  {k + 1}/{len(ids)} HDH fits', flush=True)
    df = pd.DataFrame(rows)
    ok = ~df['failed']
    df.loc[ok, 'slope_per_peak'] = df.loc[ok, 'slope'] / df.loc[ok, 'peak_load']
    df.loc[ok, 'slope_per_base'] = (df.loc[ok, 'slope'] /
                                    df.loc[ok, 'base'].replace(0, np.nan))
    return df


def parameterisation_comparison(load_fits, hdh_fits, resolution='24 h',
                                n_boot=1000, specificity=0.95, seed=0):
    """Detection performance of the two parameterisations, side by side."""
    rows = []
    for name, df in [('hockey stick', load_fits[load_fits.resolution == resolution]),
                     ('HDH linear', hdh_fits)]:
        for stat in ['slope', 'slope_per_peak', 'slope_per_base']:
            r = bootstrap_detection(df, stat, resolution, n_boot, specificity, seed)
            if r is None:
                continue
            rows.append({'parameterisation': name, 'statistic': stat,
                         'auc': r['auc'], 'auc_lo': r['auc_ci'][0],
                         'auc_hi': r['auc_ci'][1], 'threshold': r['threshold'],
                         'sensitivity': r['sensitivity'],
                         'sens_lo': r['sensitivity_ci'][0],
                         'sens_hi': r['sensitivity_ci'][1]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Detection: which slope value confidently indicates a heat pump?
# ---------------------------------------------------------------------------
def roc(df_load, statistic='slope', resolution='24 h'):
    """ROC of `statistic` separating substations with heat pumps from those without.

    Returns (curve, auc). Positives are N_hp > 0.
    """
    d = df_load[(~df_load['failed']) & (df_load['resolution'] == resolution)]
    d = d[np.isfinite(d[statistic])]
    pos = d.loc[d['N_hp'] > 0, statistic].to_numpy()
    neg = d.loc[d['N_hp'] == 0, statistic].to_numpy()
    if not len(pos) or not len(neg):
        return None, np.nan
    thr = np.unique(np.concatenate([pos, neg]))
    tpr = np.array([(pos >= t).mean() for t in thr])
    fpr = np.array([(neg >= t).mean() for t in thr])
    order = np.argsort(fpr)
    auc = float(np.trapz(tpr[order], fpr[order]))
    curve = pd.DataFrame({'threshold': thr, 'tpr': tpr, 'fpr': fpr})
    return curve, abs(auc)


# Penetration bands for reporting. A triangular design realises a different
# hp_ratio in almost every cell (5/15 and 10/30 are both a third, 5/20 and 10/40
# both a quarter), so grouping on the exact ratio scatters the result over
# dozens of tiny groups. These bands are the penetration levels the earlier
# ratio grid used, so the numbers stay comparable across designs.
PENETRATION_BINS = (0.0, 0.05, 0.10, 0.25, 0.50, 0.75, 1.001)
PENETRATION_LABELS = ('<=5%', '5-10%', '10-25%', '25-50%', '50-75%', '>75%')
# nominal x position for each band, for plotting against a penetration axis
PENETRATION_X = (0.05, 0.10, 0.25, 0.50, 0.75, 1.00)


def by_penetration(pos, flag, bins=PENETRATION_BINS, labels=PENETRATION_LABELS):
    """Detection rate per penetration band, with the count behind each one."""
    band = pd.cut(pos['hp_ratio'], bins=bins, labels=labels, right=False,
                  include_lowest=True)
    g = pd.DataFrame({'band': band, 'flag': np.asarray(flag)}).groupby(
        'band', observed=False)['flag']
    out = pd.DataFrame({'n': g.size(), 'rate': g.mean()})
    out['x'] = list(PENETRATION_X)[:len(out)]
    return out


def detection_threshold(df_load, statistic='slope', resolution='24 h',
                        specificity=0.95):
    """Threshold at the requested specificity, and what it detects.

    The threshold is the `specificity` quantile of the NO-heat-pump distribution:
    above it, at most (1 - specificity) of HP-free substations are flagged.
    """
    d = df_load[(~df_load['failed']) & (df_load['resolution'] == resolution)]
    d = d[np.isfinite(d[statistic])]
    neg = d.loc[d['N_hp'] == 0, statistic]
    pos = d.loc[d['N_hp'] > 0]
    if not len(neg) or not len(pos):
        return None
    thr = float(neg.quantile(specificity))
    out = {'statistic': statistic, 'resolution': resolution,
           'specificity': specificity, 'threshold': thr,
           'n_neg': len(neg), 'n_pos': len(pos),
           'observed_fpr': float((neg >= thr).mean()),
           'sensitivity': float((pos[statistic] >= thr).mean())}
    by_ratio = (pos.assign(flag=pos[statistic] >= thr)
                .groupby('hp_ratio')['flag'].mean())
    by_nhp = (pos.assign(flag=pos[statistic] >= thr)
              .groupby('N_hp')['flag'].mean())
    out['by_hp_ratio'] = by_ratio
    out['by_N_hp'] = by_nhp
    out['by_penetration'] = by_penetration(pos, pos[statistic] >= thr)
    return out


def detection_at(df_load, threshold, statistic='slope_per_peak',
                 resolution='24 h'):
    """Detection rates at an externally supplied threshold.

    Used to score one dataset with a threshold calibrated on another. Scoring a
    dataset with its own 95th percentile makes the operating point depend on how
    clean that dataset's heat-pump-free group happens to be, which is not
    comparable across datasets and not what an operator would do.
    """
    d = df_load[(~df_load['failed']) & (df_load['resolution'] == resolution)]
    d = d[np.isfinite(d[statistic])]
    pos, neg = d[d['N_hp'] > 0], d[d['N_hp'] == 0]
    if not len(pos):
        return None
    flag = pos[statistic] >= threshold
    return {'statistic': statistic, 'resolution': resolution,
            'threshold': float(threshold), 'external': True,
            'n_pos': len(pos), 'n_neg': len(neg),
            'sensitivity': float(flag.mean()),
            'observed_fpr': float((neg[statistic] >= threshold).mean()) if len(neg) else np.nan,
            'by_hp_ratio': pos.assign(flag=flag).groupby('hp_ratio')['flag'].mean(),
            'by_N_hp': pos.assign(flag=flag).groupby('N_hp')['flag'].mean(),
            'by_penetration': by_penetration(pos, flag)}


def statistic_comparison(df_load, resolution='24 h', specificity=0.95):
    """Score the candidate detection statistics side by side."""
    rows = []
    for stat in ['slope', 'slope_per_peak', 'slope_per_base']:
        _, auc = roc(df_load, stat, resolution)
        det = detection_threshold(df_load, stat, resolution, specificity)
        if det is None:
            continue
        rows.append({'statistic': stat, 'auc': auc,
                     'threshold': det['threshold'],
                     'sensitivity': det['sensitivity'],
                     'observed_fpr': det['observed_fpr']})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Uncertainty on the detection numbers
#
# The operating threshold is the 95th percentile of the heat-pump-free group, so
# it is an estimate from a finite sample and carries real sampling uncertainty.
# It is also the number an operator would act on, so a point estimate is not
# enough. Substations are the resampling unit.
# ---------------------------------------------------------------------------
def _fast_auc(pos, neg):
    """AUC via the rank-sum identity; far cheaper than sweeping thresholds."""
    n_pos, n_neg = len(pos), len(neg)
    if n_pos == 0 or n_neg == 0:
        return np.nan
    allv = np.concatenate([pos, neg])
    order = allv.argsort(kind='mergesort')
    ranks = np.empty(len(allv), float)
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks over ties so tied scores do not inflate the statistic
    _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=ranks)
    ranks = (sums / cnt)[inv]
    return (ranks[:n_pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def _panel(df_load, statistic, resolution):
    d = df_load[(~df_load['failed']) & (df_load['resolution'] == resolution)]
    d = d[np.isfinite(d[statistic])]
    return (d.loc[d['N_hp'] > 0, statistic].to_numpy(),
            d.loc[d['N_hp'] == 0, statistic].to_numpy())


def bootstrap_detection(df_load, statistic='slope_per_peak', resolution='24 h',
                        n_boot=1000, specificity=0.95, seed=0):
    """Percentile intervals for AUC, operating threshold and sensitivity.

    Positives and negatives are resampled separately, which keeps the class
    balance of the design fixed and varies only the sampling of substations.
    """
    pos, neg = _panel(df_load, statistic, resolution)
    if not len(pos) or not len(neg):
        return None
    rng = np.random.default_rng(seed)
    aucs, thrs, sens = np.empty(n_boot), np.empty(n_boot), np.empty(n_boot)
    for b in range(n_boot):
        p = rng.choice(pos, size=len(pos), replace=True)
        q = rng.choice(neg, size=len(neg), replace=True)
        aucs[b] = _fast_auc(p, q)
        t = np.quantile(q, specificity)
        thrs[b] = t
        sens[b] = (p >= t).mean()

    def ci(a):
        return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))

    thr_obs = float(np.quantile(neg, specificity))
    return {'statistic': statistic, 'resolution': resolution,
            'n_pos': len(pos), 'n_neg': len(neg),
            'auc': _fast_auc(pos, neg), 'auc_ci': ci(aucs),
            'threshold': thr_obs, 'threshold_ci': ci(thrs),
            'sensitivity': float((pos >= thr_obs).mean()), 'sensitivity_ci': ci(sens)}


def bootstrap_table(df_load, statistics=('slope', 'slope_per_peak', 'slope_per_base'),
                    resolution='24 h', n_boot=1000, specificity=0.95, seed=0):
    rows = []
    for s in statistics:
        r = bootstrap_detection(df_load, s, resolution, n_boot, specificity, seed)
        if r is None:
            continue
        rows.append({'statistic': s, 'auc': r['auc'],
                     'auc_lo': r['auc_ci'][0], 'auc_hi': r['auc_ci'][1],
                     'threshold': r['threshold'],
                     'thr_lo': r['threshold_ci'][0], 'thr_hi': r['threshold_ci'][1],
                     'sensitivity': r['sensitivity'],
                     'sens_lo': r['sensitivity_ci'][0], 'sens_hi': r['sensitivity_ci'][1]})
    return pd.DataFrame(rows)


def bootstrap_resolution_contrast(df_load, statistic='slope_per_peak',
                                  reference='24 h', n_boot=1000,
                                  specificity=0.95, seed=0):
    """Paired bootstrap of AUC and sensitivity differences across resolutions.

    The same substations appear at every resolution, so a replicate resamples
    substation IDs once and evaluates every resolution on that same draw. The
    difference is then paired and its interval is much tighter than comparing
    two independent intervals by eye.
    """
    d = df_load[~df_load['failed']]
    wide = d.pivot_table(index='substation_id', columns='resolution',
                         values=statistic, aggfunc='first')
    nhp = d.groupby('substation_id')['N_hp'].first()
    keep = wide.dropna().index.intersection(nhp.index)
    wide, nhp = wide.loc[keep], nhp.loc[keep]
    pos_idx = np.flatnonzero((nhp > 0).to_numpy())
    neg_idx = np.flatnonzero((nhp == 0).to_numpy())
    cols = [c for c in LABELS if c in wide.columns]
    M = wide[cols].to_numpy()

    rng = np.random.default_rng(seed)
    n_res = len(cols)
    auc_b = np.empty((n_boot, n_res))
    sen_b = np.empty((n_boot, n_res))
    for b in range(n_boot):
        pi = rng.choice(pos_idx, size=len(pos_idx), replace=True)
        qi = rng.choice(neg_idx, size=len(neg_idx), replace=True)
        for j in range(n_res):
            p, q = M[pi, j], M[qi, j]
            auc_b[b, j] = _fast_auc(p, q)
            sen_b[b, j] = (p >= np.quantile(q, specificity)).mean()

    ref = cols.index(reference)
    rows = []
    for j, c in enumerate(cols):
        p, q = M[pos_idx, j], M[neg_idx, j]
        thr = np.quantile(q, specificity)
        d_auc = auc_b[:, j] - auc_b[:, ref]
        d_sen = sen_b[:, j] - sen_b[:, ref]
        rows.append({
            'resolution': c,
            'auc': _fast_auc(p, q),
            'sensitivity': float((p >= thr).mean()),
            'd_auc_vs_ref': float(np.mean(d_auc)),
            'd_auc_lo': float(np.percentile(d_auc, 2.5)),
            'd_auc_hi': float(np.percentile(d_auc, 97.5)),
            'd_sens_vs_ref': float(np.mean(d_sen)),
            'd_sens_lo': float(np.percentile(d_sen, 2.5)),
            'd_sens_hi': float(np.percentile(d_sen, 97.5)),
        })
    return pd.DataFrame(rows), reference


# ---------------------------------------------------------------------------
# Fit diagnostics and pool reporting
# ---------------------------------------------------------------------------
def boundary_report(fits, bounds=T_BALANCE_BOUNDS, resolution='24 h', tol=1e-3):
    """How many fits sit on the T_threshold search bounds, and does it matter.

    A fit pinned at a bound has not identified a breakpoint from the data, so the
    median is re-reported with those fits excluded.
    """
    rows = []
    for resp in ('Load', 'SF'):
        d = fits[(~fits['failed']) & (fits['response'] == resp) &
                 (fits['resolution'] == resolution)]
        if not len(d):
            continue
        lo = (d['T_threshold'] <= bounds[0] + tol).sum()
        hi = (d['T_threshold'] >= bounds[1] - tol).sum()
        free = d[(d['T_threshold'] > bounds[0] + tol) &
                 (d['T_threshold'] < bounds[1] - tol)]
        rows.append({'response': resp, 'n': len(d),
                     'pinned_low': int(lo), 'pinned_high': int(hi),
                     'pinned_frac': float((lo + hi) / len(d)),
                     'median_all': float(d['T_threshold'].median()),
                     'median_unpinned': float(free['T_threshold'].median()),
                     'shift': float(free['T_threshold'].median() -
                                    d['T_threshold'].median())})
    return pd.DataFrame(rows)


def pool_report(design, pool):
    """Households and, separately, heat-pump households used against available.

    The heat-pump pool is the binding constraint on every SF result, so it is
    reported in its own right rather than folded into the household count.
    """
    used_hp = set()
    for hh in design['meta']['hp_households']:
        used_hp.update(hh)
    used_all = set()
    for hh in design['meta']['households']:
        used_all.update(hh)
    return {
        'households_used': len(used_all),
        'households_available': len(pool['households']),
        'hp_households_used': len(used_hp),
        'hp_households_available': len(pool['hp_households']),
        'hp_peak_median': float(pool['hp_peak'].median()),
        'hp_peak_min': float(pool['hp_peak'].min()),
        'hp_peak_max': float(pool['hp_peak'].max()),
    }


# ---------------------------------------------------------------------------
# Fit quality vs resolution and aggregation
# ---------------------------------------------------------------------------
def quality_grid(df, response='Load', value='r2'):
    """Median `value` by substation size x resolution."""
    d = df[(~df['failed']) & (df['response'] == response)]
    return d.pivot_table(index='N_total', columns='resolution', values=value,
                         aggfunc='median')[LABELS]


def quality_model(df, response='Load'):
    """logit(R2) ~ log(dt) + log(N_total) + log(N_hp), substation random effect."""
    import statsmodels.formula.api as smf
    from scipy.special import logit
    d = df[(~df['failed']) & (df['response'] == response) & (df['N_hp'] > 0)].copy()
    d['y'] = logit(d['r2'].clip(1e-4, 1 - 1e-4))
    d['log_dt'] = np.log(d['dt_minutes'])
    d['log_N'] = np.log(d['N_total'])
    d['log_Nhp'] = np.log(d['N_hp'])
    m = smf.mixedlm('y ~ log_dt + log_N + log_Nhp', d,
                    groups=d['substation_id']).fit()
    ci = m.conf_int()
    return pd.DataFrame({
        'term': ['log_dt', 'log_N', 'log_Nhp'],
        'coef': [m.params[k] for k in ['log_dt', 'log_N', 'log_Nhp']],
        'lo': [ci.loc[k, 0] for k in ['log_dt', 'log_N', 'log_Nhp']],
        'hi': [ci.loc[k, 1] for k in ['log_dt', 'log_N', 'log_Nhp']],
    })


def local_scaling_slopes(fits, response='Load', by='N_total', hp_only=True):
    """Local d logit(R2) / d log(dt) between adjacent resolutions.

    The pooled mixed model fits one coefficient on log(dt), but the relationship
    is not linear in that space, so that coefficient averages over a slope that
    varies with both resolution and aggregation. Differencing adjacent
    resolutions within each substation keeps the comparison paired and exposes
    the variation.

    The benchmark is 1.0: if the residuals were independent, averaging m samples
    would divide the residual variance by m, so 1 - R2 would scale as 1/dt and
    logit(R2) would rise by exactly one per e-fold of dt. Values below 1 mean the
    residuals are correlated, so averaging buys less than independence would.
    """
    from scipy.special import logit
    d = fits[(~fits['failed']) & (fits['response'] == response)]
    if hp_only:
        d = d[d['N_hp'] > 0]
    d = d.assign(y=logit(d['r2'].clip(1e-4, 1 - 1e-4)))
    wide = d.pivot_table(index=['substation_id', by], columns='resolution',
                         values='y', aggfunc='first')
    cols = [c for c in LABELS if c in wide.columns]
    dt = {lab: dtm for _, lab, dtm in RESOLUTIONS}
    rows = []
    for a, b in zip(cols[:-1], cols[1:]):
        step = np.log(dt[b]) - np.log(dt[a])
        s = ((wide[b] - wide[a]) / step).dropna()
        g = s.groupby(level=1)
        for key, vals in g:
            rows.append({'response': response, by: key, 'from': a, 'to': b,
                         'n': len(vals), 'alpha': float(vals.median()),
                         'q25': float(vals.quantile(.25)),
                         'q75': float(vals.quantile(.75))})
    return pd.DataFrame(rows)


def scaling_summary(fits, response='Load'):
    """Local alpha pooled over aggregation levels, per resolution step."""
    loc = local_scaling_slopes(fits, response)
    return (loc.groupby(['from', 'to'])
            .apply(lambda g: pd.Series({
                'alpha_median': g['alpha'].median(),
                'alpha_min': g['alpha'].min(),
                'alpha_max': g['alpha'].max()}))
            .reset_index())


def observed_temperature_range(design, rule='D'):
    """Range of daily mean temperature actually seen, across all stations."""
    lo, hi = np.inf, -np.inf
    for arr in design['temperature'].values():
        s = pd.Series(arr, index=design['index']).resample(rule).mean().dropna()
        lo, hi = min(lo, float(s.min())), max(hi, float(s.max()))
    return lo, hi


def flexibility_envelope(sf_fits, design, resolution='24 h', pad=8.0, n=200):
    """Downward and upward flexibility as fractions of installed capacity.

    Downward flexibility is bounded by what is currently drawing power, which is
    SF(T). Upward flexibility is bounded by the idle fraction, 1 - SF(T). Both
    stay dimensionless: converting to kW would need an installed-capacity
    estimate, which is out of scope.

    SF is clipped to [0, 1] because the fitted line is not bounded and can leave
    the physical range once extrapolated.
    """
    d = sf_fits[(~sf_fits['failed']) & (sf_fits['resolution'] == resolution)]
    t_lo, t_hi = observed_temperature_range(design)
    grid = np.linspace(t_lo - pad, t_hi, n)

    base = d['base'].to_numpy()[:, None]
    slope = d['slope'].to_numpy()[:, None]
    thr = d['T_threshold'].to_numpy()[:, None]
    sf = np.clip(base + slope * np.maximum(0.0, thr - grid[None, :]), 0.0, 1.0)

    out = pd.DataFrame({
        'T': grid,
        'sf_median': np.median(sf, axis=0),
        'sf_q25': np.percentile(sf, 25, axis=0),
        'sf_q75': np.percentile(sf, 75, axis=0),
        'observed': (grid >= t_lo) & (grid <= t_hi),
    })
    # downward is what is running; upward is what is idle
    out['down_median'] = out['sf_median']
    out['down_q25'], out['down_q75'] = out['sf_q25'], out['sf_q75']
    out['up_median'] = 1.0 - out['sf_median']
    out['up_q25'], out['up_q75'] = 1.0 - out['sf_q75'], 1.0 - out['sf_q25']
    return out, (t_lo, t_hi)


def sf_at_coldest(sf_fits, resolution='24 h', clip=True):
    """Each substation's own fitted SF on its own coldest observed day.

    One value per substation, evaluated at that substation's ``T_min_obs``
    rather than at a pooled minimum shared by every station. Report the median
    of what this returns, not a curve read off at one temperature: the median of
    the per-substation values and the value of the median curve are different
    quantities whenever the substations do not all see the same coldest day.
    """
    d = sf_fits[(~sf_fits['failed']) & (sf_fits['resolution'] == resolution)]
    sf = d['base'] + d['slope'] * np.maximum(0.0, d['T_threshold'] - d['T_min_obs'])
    return sf.clip(0.0, 1.0) if clip else sf


def flexibility_summary(sf_fits, envelope, t_range, resolution='24 h'):
    """Headline numbers: SF and dSF/dT at the edges of the observed range.

    dSF/dT is minus the fitted slope below the threshold and zero above it, so it
    says how fast the downward resource grows as conditions worsen.
    """
    d = sf_fits[(~sf_fits['failed']) & (sf_fits['resolution'] == resolution)]
    t_lo, t_hi = t_range
    # per-substation value on each substation's own coldest day, then the median
    cold = sf_at_coldest(sf_fits, resolution)
    rows = {
        'T_observed_min': t_lo,
        'T_observed_max': t_hi,
        'SF_at_coldest_observed': float(cold.median()),
        'SF_at_coldest_q25': float(cold.quantile(.25)),
        'SF_at_coldest_q75': float(cold.quantile(.75)),
        'n_substations': int(len(cold)),
        'down_at_coldest': float(cold.median()),
        'up_at_coldest': float(1.0 - cold.median()),
        'dSF_dT_median': float(-d['slope'].median()),
        'dSF_dT_q25': float(-d['slope'].quantile(.75)),
        'dSF_dT_q75': float(-d['slope'].quantile(.25)),
        'dSF_per_5K': float(-5.0 * d['slope'].median()),
    }
    return pd.Series(rows)


def describe_params(df, response, cols=('slope', 'T_threshold', 'T_crit'),
                    resolution='24 h'):
    d = df[(~df['failed']) & (df['response'] == response) &
           (df['resolution'] == resolution)]
    rows = []
    for c in cols:
        s = d[c].replace([np.inf, -np.inf], np.nan).dropna()
        if not len(s):
            continue
        rows.append({'parameter': c, 'n': len(s), 'median': s.median(),
                     'q25': s.quantile(.25), 'q75': s.quantile(.75),
                     'min': s.min(), 'max': s.max()})
    return pd.DataFrame(rows)
