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
# The base temperature is per substation, taken from that substation's own
# hockey-stick T_threshold, not a single constant applied to everyone.
# hp_common's HDH_THRESH (12 degC) is still the fallback for a substation with
# no threshold to borrow -- a failed hockey-stick fit, or none supplied at all.
# ---------------------------------------------------------------------------
def fit_hdh_all(design, ids=None, thresholds=None, hdh_thresh=None, verbose=True):
    """Fit daily mean load against daily cumulative HDH for every substation.

    ``thresholds`` maps substation_id -> base temperature (degC), typically the
    same substation's own hockey-stick T_threshold (e.g. `d24.set_index(
    'substation_id').T_threshold`), so the degree-hours integrate below the
    balance temperature THAT substation's net-load fit actually found. A
    substation missing from ``thresholds`` -- or every substation, if
    ``thresholds`` is None -- falls back to ``hdh_thresh`` (default
    `hp_common.HDH_THRESH`).

    Returns the same schema the detection functions expect, so the identical
    analysis can be run on it without special-casing. The threshold actually
    used for each substation is recorded in ``hdh_threshold``.
    """
    from hp_common import HDH_THRESH, daily_cumulative_hdh, fit_hdh_linear
    default_thresh = HDH_THRESH if hdh_thresh is None else hdh_thresh

    ids = list(design['meta'].index) if ids is None else list(ids)
    rows = []
    for k, sid in enumerate(ids):
        sid = int(sid)
        thresh = (thresholds.get(sid, default_thresh) if thresholds is not None
                  else default_thresh)
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
               'hdh_threshold': float(thresh),
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


def thermal_energy_estimates(design, load_fits, hdh_fits=None, resolution='24 h',
                             hdh_thresh=None):
    """Per-day thermal energy implied by each fit, against submetered ground truth.

    Both fits are trained on NET LOAD, never on heat pump energy specifically, so
    comparing their thermal component against the substation's own submetered
    heat pump circuits is a genuine test of what the "thermal" part of a net-load
    fit actually captures -- not a restatement of the R^2 already reported
    elsewhere, which is against net load.

    For every substation with N_hp > 0 and a successful fit under both
    parameterisations, for every day of the year:

    * ``actual_kWh``          -- the substation's submetered heat pump circuits,
      summed and integrated over the day. Independent of either fit.
    * ``hs_kWh``               -- the hockey-stick fit's thermal component,
      `slope * max(0, T_threshold - T_mean) * 24 h`, using only that day's mean
      temperature -- exactly the input the hockey stick was fitted on.
    * ``hdh_native_kWh``       -- the HDH fit's thermal component. The HDH model
      is fit against daily MEAN load, same as the hockey stick, so `slope *
      HDH_day` is a mean-power-equivalent (kW) and needs the same conversion to
      energy the hockey stick gets: `slope * HDH_day * 24 h`, where `HDH_day` is
      the TRUE cumulative heating-degree-hours built from the substation's
      sub-daily temperature, integrated below THAT substation's own
      `hdh_threshold` -- whatever base temperature `hdh_fits` was actually fit
      with, read from the fit rather than assumed here.
    * ``hdh_meanonly_kWh``     -- the same fitted HDH slope, but the input is now
      the degree-hours a day would have if it sat at its own mean temperature
      for all 24 hours, `max(0, hdh_threshold - T_mean) * 24 h` (one factor of
      24 turning a temperature deficit into a full day of it), then the same
      mean-power-to-energy conversion as above (a second, separate factor of
      24). This is what the HDH model gives with only a daily-mean temperature
      to work with, the same data requirement as the hockey stick.

    Because `max(0, x)` is convex, a day with the same mean temperature but
    bigger swings around the threshold has MORE true heating-degree-hours than
    the single-point approximation, so `hdh_meanonly_kWh` is a systematic
    underestimate of `hdh_native_kWh` whenever the threshold sits inside the
    day's temperature range -- not noise, a property of the transform.

    Passing ``hdh_fits=None`` returns the hockey-stick estimate alone, without
    the two degree-hour columns, which is the form the letter reports.

    Returns one row per (substation, day).
    """
    from hp_common import HDH_THRESH, daily_cumulative_hdh
    default_thresh = HDH_THRESH if hdh_thresh is None else hdh_thresh
    with_hdh = hdh_fits is not None
    has_own_thresh = with_hdh and 'hdh_threshold' in hdh_fits.columns

    hs = load_fits[(load_fits.response == 'Load') &
                   (load_fits.resolution == resolution) &
                   (~load_fits.failed) & (load_fits.N_hp > 0)]
    ids = sorted(set(hs.substation_id))
    if with_hdh:
        hdh_ok = hdh_fits[(~hdh_fits.failed) & (hdh_fits.N_hp > 0)]
        ids = sorted(set(ids) & set(hdh_ok.substation_id))
        hdh_ok = hdh_ok.set_index('substation_id')

    hs = hs.set_index('substation_id')

    rows = []
    for sid in ids:
        hs_row = hs.loc[sid]

        temp = hd.get_series(design, sid, 'Temperature')
        hp_load = pd.Series(design['hp_load'][sid], index=design['index'])
        dt_hours = temp.index.to_series().diff().median().total_seconds() / 3600

        T_mean = temp.resample('D').mean()
        actual = hp_load.resample('D').sum() * dt_hours

        d = pd.DataFrame({'T_mean': T_mean, 'actual_kWh': actual}).dropna()
        d['hs_kWh'] = (hs_row['slope'] *
                       (hs_row['T_threshold'] - d['T_mean']).clip(lower=0) * 24.0)

        if with_hdh:
            hdh_row = hdh_ok.loc[sid]
            # the base temperature this substation's HDH fit actually used, not
            # a constant assumed here -- fit_hdh_all records it per substation
            thresh = (float(hdh_row['hdh_threshold']) if has_own_thresh
                      else default_thresh)
            hdh_true = daily_cumulative_hdh(temp, thresh)
            hdh_approx = (thresh - T_mean).clip(lower=0) * 24.0
            d = d.join(pd.DataFrame({'hdh_true': hdh_true,
                                     'hdh_approx': hdh_approx}), how='inner')
            # HDH slope is fit against MEAN load (kW), same as the hockey
            # stick, so both need the same power-to-energy factor of 24 h.
            d['hdh_native_kWh'] = hdh_row['slope'] * d['hdh_true'] * 24.0
            d['hdh_meanonly_kWh'] = hdh_row['slope'] * d['hdh_approx'] * 24.0

        d['substation_id'] = sid
        d['N_total'] = int(hs_row['N_total'])
        d['N_hp'] = int(hs_row['N_hp'])
        rows.append(d.reset_index().rename(columns={'index': 'date'}))
    return pd.concat(rows, ignore_index=True)


def summer_hp_days(pool, min_days=60):
    """Daily (temperature, HP load) pairs for June-August, any submetered pool.

    One row per submetered household-day, restricted to households with at
    least `min_days` of summer coverage. Built to test whether a heat pump
    behaves as a reversible (cooling-capable) unit: if it does, load should
    RISE with temperature on the hottest days; if it is heating-only, plus
    perhaps a flat non-thermal baseline such as domestic hot water, load
    should be flat or falling. June-August only, so no residual space-heating
    season leaks in through a less specific "warm days" cutoff -- the 85th
    percentile of a whole year can still be a mild spring day. Works on any
    pool with the standard hp_households/hp_mat/hp_peak/weather_of/temperature
    structure (HEAPO, WPUQ, ...), not HEAPO-specific despite the first use.
    """
    idx = pool['index']
    temp = pool['temperature']
    wo = pool['weather_of']
    hp_hh = pool['hp_households']
    hp_mat = pool['hp_mat']
    hp_peak = pool['hp_peak']

    rows = []
    for i, hid in enumerate(hp_hh):
        station = wo.get(hid)
        if station not in temp:
            continue
        pk = hp_peak.get(hid, np.nan)
        if not np.isfinite(pk) or pk <= 0:
            continue
        T = pd.Series(temp[station], index=idx).resample('D').mean()
        load = pd.Series(hp_mat[i], index=idx).resample('D').mean()
        d = pd.DataFrame({'T': T, 'load': load}).dropna()
        jja = d[d.index.month.isin([6, 7, 8])]
        if len(jja) < min_days:
            continue
        jja = jja.assign(household=hid, sf=jja['load'] / pk)
        rows.append(jja.reset_index().rename(columns={'index': 'date'}))
    return pd.concat(rows, ignore_index=True)


def summer_cooling_test(summer_days):
    """Per-household Spearman correlation of summer load against temperature.

    A positive, significant correlation is the cooling signature (load rises
    with heat). The count of significant positive against significant
    negative correlations across households is the headline number, not any
    single household's result.

    A household whose summer load never varies at all has no correlation to
    compute -- not "not significant", genuinely undefined -- and is flagged
    via `constant=True` rather than silently landing in whichever bucket a NaN
    happens to fail both comparisons into.
    """
    from scipy.stats import spearmanr
    rows = []
    for hid, g in summer_days.groupby('household'):
        constant = g['load'].nunique() <= 1
        if constant:
            rho, p = np.nan, np.nan
        else:
            rho, p = spearmanr(g['T'], g['load'])
        rows.append({'household': hid, 'n_days': len(g), 'rho': float(rho),
                     'p': float(p), 'constant': constant})
    return pd.DataFrame(rows)


def _fit_stats(actual, pred):
    a, p = np.asarray(actual, float), np.asarray(pred, float)
    resid = p - a
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((a - a.mean()) ** 2)
    return pd.Series({
        'r2': 1 - ss_res / ss_tot if ss_tot > 0 else np.nan,
        'rmse_kWh': np.sqrt(np.mean(resid ** 2)),
        'mae_kWh': np.mean(np.abs(resid)),
        'bias_kWh': resid.mean(),
        'bias_pct': 100 * resid.mean() / a.mean() if a.mean() else np.nan,
    })


SEASON_OF_MONTH = {12: 'winter', 1: 'winter', 2: 'winter',
                   3: 'spring', 4: 'spring', 5: 'spring',
                   6: 'summer', 7: 'summer', 8: 'summer',
                   9: 'autumn', 10: 'autumn', 11: 'autumn'}
SEASON_ORDER = ['winter', 'spring', 'summer', 'autumn']

_THERMAL_METHODS = ('hs_kWh', 'hdh_native_kWh', 'hdh_meanonly_kWh')


def _methods_present(est, methods=_THERMAL_METHODS):
    """The estimator columns actually built, in canonical order.

    ``thermal_energy_estimates`` omits the degree-hour columns when no HDH
    fits are supplied, so every consumer of ``est`` reports whatever is
    there rather than assuming all three.
    """
    return [m for m in methods if m in est.columns]


def thermal_energy_rmse_by_season(est, methods=None):
    """RMSE against submetered ground truth, per substation, per season.

    Meteorological seasons (Dec-Feb winter, ... ), not the fitted heating
    threshold, so the split is the same for every substation regardless of its
    own fit. Each substation's RMSE in a season is computed only from that
    substation's own days in that season -- nothing is pooled across
    substations at this stage, so a substation with an unusually large error
    cannot be smoothed out by the rest before the summary sees it.
    """
    methods = _methods_present(est) if methods is None else methods
    d = est.copy()
    d['season'] = d['date'].dt.month.map(SEASON_OF_MONTH)

    def _rmse(g):
        out = {f'rmse_{m}': float(np.sqrt(np.mean((g[m] - g['actual_kWh']) ** 2)))
               for m in methods}
        out['n_days'] = len(g)
        return pd.Series(out)

    out = (d.groupby(['substation_id', 'season'], observed=True)
           .apply(_rmse, include_groups=False).reset_index())
    out['season'] = pd.Categorical(out['season'], categories=SEASON_ORDER,
                                   ordered=True)
    return out


def thermal_energy_rmse_summary(rmse_df, methods=None,
                                quantiles=(.25, .5, .75)):
    """Median and quantiles of the per-substation seasonal RMSE, by season."""
    if methods is None:
        methods = [m for m in _THERMAL_METHODS if f'rmse_{m}' in rmse_df.columns]
    cols = [f'rmse_{m}' for m in methods]
    g = rmse_df.groupby('season', observed=True)[cols]
    pieces = {f'q{int(q * 100):02d}': g.quantile(q) for q in quantiles}
    return pd.concat(pieces, axis=1).reindex(SEASON_ORDER)


def thermal_energy_summary(est, by='pooled'):
    """Accuracy of each estimator against submetered ground truth.

    `by='pooled'` scores every (substation, day) row together. `by='substation'`
    fits the same statistics within each substation first and returns the
    median across substations, so one substation with unusually many days
    cannot dominate the pooled number.
    """
    methods = _methods_present(est)
    if by == 'pooled':
        return pd.DataFrame({m: _fit_stats(est['actual_kWh'], est[m]) for m in methods}).T
    if by == 'substation':
        rows = {}
        for m in methods:
            per_sub = est.groupby('substation_id').apply(
                lambda g, m=m: _fit_stats(g['actual_kWh'], g[m]))
            rows[m] = per_sub.median()
        return pd.DataFrame(rows).T
    raise ValueError(f'unknown by {by!r}')


def thermal_energy_per_substation(est, method=None):
    """One row per substation, rather than the median across them.

    ``thermal_energy_summary(by='substation')`` collapses to a median, which
    hides how widely individual substations differ. That spread is the point
    when accuracy is read against aggregation level: the median can be flat
    while the dispersion around it collapses. Returns the design columns
    alongside the statistics so the result can be grouped by ``N_total`` or
    penetration directly.
    """
    if method is None:
        method = _methods_present(est)[0]
    rows = []
    for sid, g in est.groupby('substation_id'):
        stats = _fit_stats(g['actual_kWh'], g[method])
        stats['substation_id'] = sid
        stats['N_total'] = int(g['N_total'].iloc[0])
        stats['N_hp'] = int(g['N_hp'].iloc[0])
        stats['n_days'] = len(g)
        rows.append(stats)
    out = pd.DataFrame(rows)
    out['hp_ratio'] = out['N_hp'] / out['N_total']
    return out


def thermal_energy_summary_by(est, group_col, method=None):
    """Pooled accuracy statistics, one row per distinct value of ``group_col``.

    Unlike ``thermal_energy_summary``, which pools everything or splits by
    substation, this keeps a row per group -- e.g. ETL penetration, or a
    temperature bin -- so accuracy can be checked for uniformity across the
    grid rather than reported as one number. ``method`` defaults to the
    first estimator column present in ``est``.
    """
    if method is None:
        method = _methods_present(est)[0]
    rows = {}
    for key, g in est.groupby(group_col, observed=True):
        stats = _fit_stats(g['actual_kWh'], g[method])
        stats['n'] = len(g)
        rows[key] = stats
    return pd.DataFrame(rows).T


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

    The threshold grid is extended above the largest observed value so the curve
    starts at (0, 0). Without that point the area between the origin and the
    first threshold is dropped, which biases the AUC low by roughly 1/(2 |neg|).
    That is negligible when the negative class is large, but reaches 0.017 in a
    per-consumer-count stratum holding only 25 negatives, so the area is
    reported as the exact rank statistic rather than integrated off the curve.
    """
    d = df_load[(~df_load['failed']) & (df_load['resolution'] == resolution)]
    d = d[np.isfinite(d[statistic])]
    pos = d.loc[d['N_hp'] > 0, statistic].to_numpy()
    neg = d.loc[d['N_hp'] == 0, statistic].to_numpy()
    if not len(pos) or not len(neg):
        return None, np.nan
    thr = np.unique(np.concatenate([pos, neg]))
    thr = np.concatenate([thr, [np.nextafter(thr[-1], np.inf)]])
    tpr = np.array([(pos >= t).mean() for t in thr])
    fpr = np.array([(neg >= t).mean() for t in thr])
    # Mann-Whitney U on the pooled ranks: exact, and free of the discretisation
    # the trapezoid rule introduces when the two classes are small.
    r = pd.Series(np.concatenate([pos, neg])).rank().to_numpy()
    auc = float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2)
                / (len(pos) * len(neg)))
    curve = pd.DataFrame({'threshold': thr, 'tpr': tpr, 'fpr': fpr})
    return curve, auc


# Penetration bands for reporting. A triangular design realises a different
# hp_ratio in almost every cell (5/15 and 10/30 are both a third, 5/20 and 10/40
# both a quarter), so grouping on the exact ratio scatters the result over
# dozens of tiny groups. These bands are the penetration levels the earlier
# ratio grid used, so the numbers stay comparable across designs.
PENETRATION_BINS = (0.0, 0.05, 0.10, 0.25, 0.50, 0.75, 1.001)
PENETRATION_LABELS = ('<=5%', '5-10%', '10-25%', '25-50%', '50-75%', '>75%')
# nominal x position for each band, for plotting against a penetration axis
PENETRATION_X = (0.05, 0.10, 0.25, 0.50, 0.75, 1.00)


def confound_extremes(d24, value='slope'):
    """The sharpest instance of the consumer/heat-pump confound in a design.

    Finds the largest heat-pump-free substation (median `value` across its
    replicates), then the smallest, most heavily penetrated substation it
    still exceeds, if one exists. Used both to state the confound in prose and
    to mark it on the heatmap (`hp_figures.fig3_heatmap`), so the two always
    agree -- neither hard-codes a pair, both call this.

    Returns a dict: `free_N_total`, `free_value`, and `beaten` (None if the
    heat-pump-free cell is never exceeded within this design, else a dict with
    `N_total`, `hp_ratio`, `value`).
    """
    piv = d24.pivot_table(index='hp_ratio', columns='N_total', values=value,
                          aggfunc='median')
    out = {'free_N_total': None, 'free_value': None, 'beaten': None}
    if 0.0 not in piv.index or not piv.loc[0.0].notna().any():
        return out
    free_row = piv.loc[0.0]
    free_col, free_val = free_row.idxmax(), free_row.max()
    out['free_N_total'], out['free_value'] = int(free_col), float(free_val)

    positives = piv.drop(index=0.0, errors='ignore').stack()
    beaten = positives[positives < free_val]
    if not len(beaten):
        return out
    b = beaten.reset_index()
    b.columns = ['hp_ratio', 'N_total', 'value']
    b = b.sort_values(['N_total', 'hp_ratio'], ascending=[True, False])
    row = b.iloc[0]
    out['beaten'] = {'N_total': int(row.N_total), 'hp_ratio': float(row.hp_ratio),
                     'value': float(row.value)}
    return out


def by_penetration_quantile(pos, flag, q=5):
    """Detection rate per equal-frequency penetration bin.

    Unlike `by_penetration`, bin EDGES are not fixed -- they are chosen so every
    bin holds the same number of substations, which only the fixed thresholds in
    `PENETRATION_BINS` cannot guarantee (n ranged 50 to 550 across those bands on
    the full grid). Ties are broken by row order (`rank(method='first')`) rather
    than dropped, so replicate substations at the same hp_ratio can land in
    adjacent bins -- harmless, since they are exchangeable draws from the same
    design cell.
    """
    rank = pos['hp_ratio'].rank(method='first')
    bins = pd.qcut(rank, q=q)
    lab_map = {cat: f"{pos['hp_ratio'][bins == cat].min():.0%}-"
                    f"{pos['hp_ratio'][bins == cat].max():.0%}"
              for cat in bins.cat.categories}
    order = [lab_map[c] for c in bins.cat.categories]
    band = bins.map(lab_map).astype(pd.CategoricalDtype(categories=order, ordered=True))
    g = pd.DataFrame({'band': band, 'flag': np.asarray(flag)}).groupby(
        'band', observed=False)['flag']
    return pd.DataFrame({'n': g.size(), 'rate': g.mean()}), band


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


def _bootstrap_median_ci(values, n_boot=1000, seed=0):
    """Percentile bootstrap CI of the median, same convention as bootstrap_detection
    (2.5/97.5, n_boot=1000, seed=0)."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    boot = np.median(rng.choice(v, size=(n_boot, len(v)), replace=True), axis=1)
    return float(np.median(v)), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def quality_by_resolution(fits, response='Load', N_total=50, N_hp=25, n_boot=1000,
                          seed=0):
    """Median R2 (with a bootstrap CI) at ONE fixed (N_total, N_hp) cell, across
    resolution.

    Holding both counts fixed isolates resolution as the only thing varying --
    `quality_grid` sweeps N_total at each resolution too, which is a different
    question. The CI is a percentile bootstrap over the cell's replicate
    substations (25 in the standard design), not a spread statistic: it answers
    how precisely the median is known from this many replicates, not how much
    substations in the cell differ from each other.
    """
    d = fits[(fits.response == response) & (~fits.failed) &
             (fits.N_total == N_total) & (fits.N_hp == N_hp)]
    rows = []
    for res in LABELS:
        med, lo, hi = _bootstrap_median_ci(d.loc[d.resolution == res, 'r2'],
                                           n_boot=n_boot, seed=seed)
        rows.append({'resolution': res, 'n': int((d.resolution == res).sum()),
                     'median_r2': med, 'ci_lo': lo, 'ci_hi': hi})
    return pd.DataFrame(rows)


def quality_by_size(fits, response='Load', resolution='24 h', ratio=0.5,
                    n_boot=1000, seed=0, even_only=True):
    """Median R2 (with a bootstrap CI) at ONE fixed resolution and penetration
    ratio, across N_total.

    `ratio` must land on an exact N_hp for every N_total considered, or the
    cell does not exist in a design indexed by absolute heat pump count. With
    ratio=0.5 that means even N_total only (`even_only=True`, the default) --
    an odd N_total has no substation at exactly 50 %, it would have to be
    rounded, and rounding is exactly what this figure is built to avoid.
    """
    d = fits[(fits.response == response) & (fits.resolution == resolution) &
             (~fits.failed)]
    totals = sorted(d.N_total.unique())
    if even_only:
        totals = [n for n in totals if n % 2 == 0]
    rows = []
    for nt in totals:
        nh = round(nt * ratio)
        if not np.isclose(nh, nt * ratio):
            continue
        sub = d[(d.N_total == nt) & (d.N_hp == nh)]
        if not len(sub):
            continue
        med, lo, hi = _bootstrap_median_ci(sub['r2'], n_boot=n_boot, seed=seed)
        rows.append({'N_total': int(nt), 'N_hp': int(nh), 'n': len(sub),
                     'median_r2': med, 'ci_lo': lo, 'ci_hi': hi})
    return pd.DataFrame(rows)


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


# ---------------------------------------------------------------------------
# Technology fingerprint: is the cold-side response convex?
# ---------------------------------------------------------------------------
def curvature_test(pool, agg='mean', min_points=30, T_bounds=T_BALANCE_BOUNDS):
    """Per-household test of curvature below the fitted balance temperature.

    A heat pump draws Q_heat(T) / COP(T), and COP falls as T falls, so its
    electrical load should curve upward (convex) below the balance temperature.
    Resistive heating has COP = 1 and stays linear. This fits each submetered
    heat pump circuit's own hockey stick to (SF, T), then adds a quadratic term
    on the cold side alone and reports whether it earns its keep.

    ``agg`` selects the daily aggregation used to build the (T, SF) pairs:

    * ``'mean'`` -- daily mean T against daily mean SF. The convention used for
      every other hockey-stick fit in this notebook. Ties the fit to typical
      operation, which is also where thermostatic on/off cycling does the most
      damage to a curvature signal built on a handful of extra degrees of
      freedom.
    * ``'minmax'`` -- daily minimum T against daily maximum SF, the convention
      ``hp_common.daily_min_max_heating_season`` uses elsewhere in this
      codebase. Ties the fit to the coldest, hardest-running part of the day.
      It does not test the same physical claim: a fixed equipment capacity
      makes the daily MAX saturate as it gets colder regardless of COP, which
      shows up as curvature of the opposite sign to the one predicted here.

    Returns one row per household with a usable fit: the linear and quadratic
    R^2 on the cold-side subset, their difference, and the quadratic term's
    coefficient (curvature > 0 is convex, the heat-pump prediction).
    """
    idx = pool['index']
    temp = pool['temperature']
    wo = pool['weather_of']
    hp_hh = pool['hp_households']
    hp_mat = pool['hp_mat']
    hp_peak = pool['hp_peak']

    rows = []
    for i, h in enumerate(hp_hh):
        pk = hp_peak.get(h, np.nan)
        if not np.isfinite(pk) or pk <= 0:
            continue
        station = wo.get(h)
        if station not in temp:
            continue
        T = pd.Series(temp[station], index=idx)
        sf = pd.Series(hp_mat[i], index=idx) / pk
        if agg == 'mean':
            d = pd.DataFrame({'T': T.resample('D').mean(),
                              'sf': sf.resample('D').mean()}).dropna()
        elif agg == 'minmax':
            d = pd.DataFrame({'T': T.resample('D').min(),
                              'sf': sf.resample('D').max()}).dropna()
        else:
            raise ValueError(f'unknown agg {agg!r}')
        if len(d) < 2 * min_points or d['T'].nunique() < 5:
            continue
        try:
            base, slope, Tb, r2 = fit_hockey_stick(d['T'].to_numpy(),
                                                    d['sf'].to_numpy(), T_bounds)
        except Exception:
            continue
        if slope <= 0:
            continue
        sub = d[d['T'] < Tb]
        if len(sub) < min_points:
            continue
        y = sub['sf'].to_numpy()
        dd = (Tb - sub['T']).to_numpy()
        X1 = np.column_stack([np.ones_like(dd), dd])
        X2 = np.column_stack([np.ones_like(dd), dd, dd ** 2])
        c1, *_ = np.linalg.lstsq(X1, y, rcond=None)
        c2, *_ = np.linalg.lstsq(X2, y, rcond=None)
        r2_lin = 1 - np.sum((y - X1 @ c1) ** 2) / np.sum((y - y.mean()) ** 2)
        r2_quad = 1 - np.sum((y - X2 @ c2) ** 2) / np.sum((y - y.mean()) ** 2)
        rows.append({'household': h, 'n_cold_days': len(sub), 'HP_Peak': pk,
                     'T_balance': Tb, 'r2_lin': r2_lin, 'r2_quad': r2_quad,
                     'd_r2': r2_quad - r2_lin, 'curvature': c2[2]})
    return pd.DataFrame(rows)
