"""Shared heat-pump detection model code.

Extracted from ``HeatPumpDetection_clean.ipynb`` so that both that notebook and
``HeatPump_Hypotheses.ipynb`` use one definition of each model rather than
maintaining divergent copies.

Contents
--------
Constants
    ``T_BALANCE_BOUNDS``, ``HEATING_SEASON_THRESH``, ``MIN_HEATING_DAYS``,
    ``HDH_THRESH``, ``hour_groups``
Temperature hockey-stick model
    ``hockey_stick``, ``fit_hockey_stick``,
    ``daily_min_max_heating_season``, ``daily_mean_mean_heating_season``
Heating-degree-hour (HDH) model
    ``daily_cumulative_hdh`` (alias ``compute_daily_hdh``),
    ``daily_hdh_mean_load``, ``daily_hdh_energy``,
    ``hdh_linear``, ``fit_hdh_linear``
Resolution / data-hygiene helpers
    ``resolution_minutes``, ``min_points_for_resolution``,
    ``fill_numeric_na``, ``validate_series_columns``
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------
T_BALANCE_BOUNDS = (8, 20)     # degC, plausible balance-temperature range
HEATING_SEASON_THRESH = 12.0   # degC, daily-mean temperature threshold to keep a day
MIN_HEATING_DAYS = 20          # minimum heating-season DAYS required to attempt a fit
HDH_THRESH = 12.0              # degC, threshold for Heating Degree Hour accumulation
T_COOLING_BOUNDS = (15, 32)    # degC, plausible AC turn-on threshold range
DEADBAND_BOUNDS = (0, 24)      # degC, plausible Tc - Th width for the bathtub model

# Time-of-day windows. Pooling hours into 4 broad windows (rather than fitting 24
# separate hourly models) keeps each fit well-conditioned.
hour_groups = {
    'Night':     list(range(0, 6)),
    'Morning':   list(range(6, 12)),
    'Afternoon': list(range(12, 18)),
    'Evening':   list(range(18, 24)),
}

# Series-valued columns of the substation DataFrames. These hold pd.Series
# objects, not scalars, which is why fillna must never touch them.
SERIES_COLS = ('HP_Load', 'Total_Load', 'Temperature')


# ---------------------------------------------------------------------------
# Temperature hockey-stick model
#   Load(T) = base_load + hp_sensitivity * max(0, T_balance - T)
#
# Only 3 parameters, all physically bounded, so the degenerate solutions an
# unconstrained 2-segment piecewise fit can land on (positive cold-weather
# slopes, breakpoints outside the heating range) cannot happen, and
# hp_sensitivity maps directly onto installed HP capacity.
# ---------------------------------------------------------------------------
def hockey_stick(T, base_load, hp_sensitivity, T_balance):
    return base_load + hp_sensitivity * np.maximum(0, T_balance - T)


def fit_hockey_stick(x, y, T_balance_bounds=T_BALANCE_BOUNDS):
    """Fit a 3-parameter hockey-stick load-vs-temperature curve.

    Returns (base_load, hp_sensitivity, T_balance, r2). Raises if curve_fit
    fails (e.g. too few / degenerate points) so callers can catch and skip.
    """
    p0 = [np.median(y), 0.5, np.mean(T_balance_bounds)]
    bounds = (
        [0, 0, T_balance_bounds[0]],
        [np.inf, np.inf, T_balance_bounds[1]]
    )
    popt, _ = curve_fit(hockey_stick, x, y, p0=p0, bounds=bounds, maxfev=5000)
    y_pred = hockey_stick(x, *popt)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    base_load, hp_sensitivity, T_balance = popt
    return base_load, hp_sensitivity, T_balance, r2


def cooling_stick(T, base_load, ac_sensitivity, T_balance):
    """The cooling-season mirror of ``hockey_stick``: load rises ABOVE a
    balance temperature (AC turning on) rather than below one (heating)."""
    return base_load + ac_sensitivity * np.maximum(0, T - T_balance)


def fit_cooling_stick(x, y, T_balance_bounds=T_COOLING_BOUNDS):
    """Fit a 3-parameter cooling-stick load-vs-temperature curve.

    Same shape as ``fit_hockey_stick``, mirrored for cooling: the kink sits
    above ``T_balance`` instead of below it, and the search range defaults to
    a plausible AC turn-on window rather than a heating balance temperature.
    Returns (base_load, ac_sensitivity, T_balance, r2).
    """
    p0 = [np.median(y), 0.5, np.mean(T_balance_bounds)]
    bounds = (
        [0, 0, T_balance_bounds[0]],
        [np.inf, np.inf, T_balance_bounds[1]]
    )
    popt, _ = curve_fit(cooling_stick, x, y, p0=p0, bounds=bounds, maxfev=5000)
    y_pred = cooling_stick(x, *popt)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    base_load, ac_sensitivity, T_balance = popt
    return base_load, ac_sensitivity, T_balance, r2


def bathtub_stick(T, base_load, heat_slope, T_heat, cool_slope, deadband):
    """Two hockey sticks sharing one flat base, heating below ``T_heat`` and
    cooling above ``T_cool = T_heat + deadband``.

    ``deadband`` (>= 0 by construction, not ``T_cool`` itself) is the fitted
    parameter so a fit can never place the cooling threshold below the
    heating one -- a bathtub with a negative-width deadband is not a
    bathtub. ``T_cool`` is recovered as ``T_heat + deadband`` after fitting.
    """
    T_cool = T_heat + deadband
    return (base_load + heat_slope * np.maximum(0, T_heat - T)
                       + cool_slope * np.maximum(0, T - T_cool))


def fit_bathtub_stick(x, y, T_heat_bounds=T_BALANCE_BOUNDS,
                      deadband_bounds=DEADBAND_BOUNDS):
    """Fit the 5-parameter bathtub curve: ``hockey_stick`` and
    ``cooling_stick`` sharing one base load, joined by a deadband.

    Returns (base_load, heat_slope, T_heat, cool_slope, T_cool, r2). Raises
    if curve_fit fails, same as ``fit_hockey_stick``/``fit_cooling_stick``.
    """
    p0 = [np.median(y), 0.5, np.mean(T_heat_bounds), 0.5, np.mean(deadband_bounds)]
    bounds = (
        [0, 0, T_heat_bounds[0], 0, deadband_bounds[0]],
        [np.inf, np.inf, T_heat_bounds[1], np.inf, deadband_bounds[1]]
    )
    popt, _ = curve_fit(bathtub_stick, x, y, p0=p0, bounds=bounds, maxfev=10000)
    y_pred = bathtub_stick(x, *popt)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    base_load, heat_slope, T_heat, cool_slope, deadband = popt
    T_cool = T_heat + deadband
    return base_load, heat_slope, T_heat, cool_slope, T_cool, r2


def daily_min_max_heating_season(temperature, load,
                                 heating_season_thresh=HEATING_SEASON_THRESH,
                                 resolution='D'):
    """Build (daily_min_temperature, daily_max_load) pairs, restricted to
    heating-season days.

    Using the daily MINIMUM temperature (rather than the daily mean) ties
    the fit to the coldest part of the day, when HPs run hardest. Using the
    daily MAXIMUM load (rather than the mean) ties it to peak demand, which
    is what HP_Peak actually measures. Warm-season days are dropped so they
    don't bias the slope / balance-temperature estimate towards a flat,
    near-zero-sensitivity cloud of points.
    """
    daily_temp_min = temperature.resample(resolution).min()
    daily_load_max = load.resample(resolution).max()
    sm_data = pd.DataFrame({
        'Temperature_min': daily_temp_min,
        'Total_Load_max': daily_load_max
    }).dropna()
    sm_data = sm_data[sm_data['Temperature_min'] < heating_season_thresh]
    return sm_data['Temperature_min'].values, sm_data['Total_Load_max'].values


def daily_mean_mean_heating_season(temperature, load,
                                   heating_season_thresh=HEATING_SEASON_THRESH,
                                   resolution='D'):
    """Build (daily_mean_temperature, daily_mean_load) pairs, restricted to
    heating-season days.

    Using the daily MEAN temperature and MEAN load (rather than the daily
    min temperature / max load used above) smooths out sub-daily noise and
    ties the fit to the typical daytime operating point rather than to the
    single coldest hour or the instantaneous peak. Warm-season days are
    dropped so they don't bias the slope / balance-temperature estimate
    towards a flat, near-zero-sensitivity cloud of points.
    """
    daily_temp_mean = temperature.resample(resolution).mean()
    daily_load_mean = load.resample(resolution).mean()
    sm_data = pd.DataFrame({
        'Temperature_mean': daily_temp_mean,
        'Total_Load_mean': daily_load_mean
    }).dropna()
    sm_data = sm_data[sm_data['Temperature_mean'] < heating_season_thresh]
    return sm_data['Temperature_mean'].values, sm_data['Total_Load_mean'].values


# ---------------------------------------------------------------------------
# HDH (Heating Degree Hours) linear model
#   Load = base_load + hp_sensitivity * HDH
#   HDH_day = sum over sub-daily samples of max(0, HDH_THRESH - T) * dt_hours
#
# The zero-clipping hinge is already baked into the HDH transform itself (every
# sample above the threshold contributes 0), so a plain 2-parameter line
# captures the same "flat below threshold / rising above it" shape without a
# separate T_balance / breakpoint parameter.
# ---------------------------------------------------------------------------
def daily_cumulative_hdh(temperature, hdh_thresh=HDH_THRESH, resolution='D'):
    """Cumulative Heating Degree Hours (degC*h) per day.

    Sums max(0, hdh_thresh - T) over each sub-daily sample, weighted by the
    sample's duration in hours, so days with the same mean temperature but
    bigger swings around the threshold get different HDH totals.
    """
    temperature = temperature.sort_index()
    dt_hours = temperature.index.to_series().diff().median().total_seconds() / 3600
    hdh_per_sample = (hdh_thresh - temperature).clip(lower=0) * dt_hours
    return hdh_per_sample.resample(resolution).sum()


# The task brief refers to this function as `compute_daily_hdh`; the notebooks
# call it `daily_cumulative_hdh`. Keep both names bound to one implementation.
compute_daily_hdh = daily_cumulative_hdh


def daily_hdh_mean_load(temperature, load, hdh_thresh=HDH_THRESH, resolution='D'):
    """Build (daily_cumulative_HDH, daily_mean_load) pairs."""
    daily_hdh = daily_cumulative_hdh(temperature, hdh_thresh, resolution)
    daily_load_mean = load.resample(resolution).mean()
    sm_data = pd.DataFrame({'HDH': daily_hdh, 'Load_mean': daily_load_mean}).dropna()
    return sm_data['HDH'].values, sm_data['Load_mean'].values


def daily_hdh_energy(temperature, load, hdh_thresh=HDH_THRESH, resolution='D'):
    """Build (daily_cumulative_HDH, daily_energy) pairs."""
    daily_hdh = daily_cumulative_hdh(temperature, hdh_thresh, resolution)
    load_resolution = load.index.to_series().diff().median().total_seconds() / 3600
    daily_energy = load.resample(resolution).sum() * load_resolution
    sm_data = pd.DataFrame({'HDH': daily_hdh, 'Energy': daily_energy}).dropna()
    return sm_data['HDH'].values, sm_data['Energy'].values


def hdh_linear(hdh, base_load, hp_sensitivity):
    return base_load + hp_sensitivity * hdh


def fit_hdh_linear(x, y):
    """Fit a 2-parameter HDH-vs-load line.

    Returns (base_load, hp_sensitivity, r2). Raises if curve_fit fails so
    callers can catch and skip.
    """
    p0 = [np.median(y), 0.01]
    bounds = ([0, 0], [np.inf, np.inf])
    popt, _ = curve_fit(hdh_linear, x, y, p0=p0, bounds=bounds, maxfev=5000)
    y_pred = hdh_linear(x, *popt)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    base_load, hp_sensitivity = popt
    return base_load, hp_sensitivity, r2


# ---------------------------------------------------------------------------
# Resolution-aware minimum sample size
#
# A fixed point-count threshold means very different things across resolutions:
# 30 points is ~7.5 hours at 15 min but a month at daily resolution. Express the
# requirement in DAYS (MIN_HEATING_DAYS) and derive the point count from the
# resampling rule so every resolution demands the same span of real time.
# ---------------------------------------------------------------------------
_RESOLUTION_MINUTES_FALLBACK = {
    '15min': 15, '15T': 15, '30min': 30,
    '1h': 60, 'h': 60, 'H': 60, '1H': 60,
    '8h': 480, '8H': 480,
    'D': 1440, '1D': 1440, 'd': 1440,
}


def resolution_minutes(rule):
    """Length of one resampling interval in minutes (e.g. '8h' -> 480.0)."""
    try:
        offset = pd.tseries.frequencies.to_offset(rule)
        return offset.nanos / 1e9 / 60.0
    except (ValueError, AttributeError):
        if rule in _RESOLUTION_MINUTES_FALLBACK:
            return float(_RESOLUTION_MINUTES_FALLBACK[rule])
        raise ValueError(f'Cannot determine interval length for rule {rule!r}')


def min_points_for_resolution(rule, min_days=MIN_HEATING_DAYS):
    """Minimum resampled points corresponding to `min_days` days of data.

    Replaces the hard-coded `MIN_POINTS = 30`, which was inconsistent with
    `MIN_HEATING_DAYS = 20` and not comparable across resolutions. A floor of 4
    points is kept so a fit is never attempted with fewer points than the
    3-parameter hockey-stick model has parameters.
    """
    dt_min = resolution_minutes(rule)
    return max(4, int(np.ceil(min_days * 1440.0 / dt_min)))


# ---------------------------------------------------------------------------
# Data hygiene for the substation DataFrames
# ---------------------------------------------------------------------------
def fill_numeric_na(df, value=0):
    """``fillna`` restricted to numeric columns.

    ``substations_df`` stores pd.Series objects in the HP_Load / Total_Load /
    Temperature columns. A blanket ``df.fillna(0)`` on those columns either does
    nothing or replaces a whole Series with the integer ``0``, which then
    silently fails downstream ``isinstance(..., pd.Series)`` checks and drops the
    substation without any warning. Filling only the numeric columns keeps the
    intent (missing scalars -> 0) without corrupting the series columns.
    """
    out = df.copy()
    numeric_cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
    if numeric_cols:
        out[numeric_cols] = out[numeric_cols].fillna(value)
    return out


def validate_series_columns(df, series_cols=SERIES_COLS, verbose=True):
    """Split `df` into substations with usable series data and those without.

    A substation is usable when every column in `series_cols` holds a non-empty
    pd.Series. Returns ``(good_df, dropped_report)`` where `dropped_report` is a
    DataFrame indexed like the dropped rows with one boolean column per checked
    column marking which were bad. Anything dropped is logged rather than
    silently skipped.
    """
    present = [c for c in series_cols if c in df.columns]
    bad_flags = {}
    for col in present:
        bad_flags[col] = df[col].map(
            lambda v: not (isinstance(v, pd.Series) and len(v) > 0)
        )
    bad_df = pd.DataFrame(bad_flags, index=df.index)
    is_bad = bad_df.any(axis=1)

    good_df = df.loc[~is_bad]
    dropped_report = bad_df.loc[is_bad]

    if verbose:
        n_drop = int(is_bad.sum())
        print(f'validate_series_columns: {len(good_df)} of {len(df)} substations usable'
              f' ({n_drop} dropped for missing/empty series data)')
        if n_drop:
            for col in present:
                n_col = int(bad_df.loc[is_bad, col].sum())
                if n_col:
                    print(f'    {col}: {n_col} substations missing/empty')
    return good_df, dropped_report
