"""Heat-pump installed-capacity estimation from aggregated feeder net load.

Single source of truth for the windowed-HDD feature pipeline used by
``HeatPumpDetection_clean.ipynb`` and any transfer notebooks. The feature
extractor is ported verbatim from the notebook (cell 103) so cached feature
matrices remain bit-for-bit reproducible; the helpers below implement the
methodological fixes for cross-feeder transfer:

* country-specific HDD base temperatures are respected -- 12 degC (CH),
  15 degC (DE/BW) are the national degree-day conventions, passed per dataset;
* an explicit size/scale anchor so an absolute-kW target can transfer across
  feeders of very different size (``add_scale_features``);
* a robust per-household capacity proxy (99.9th percentile, not the raw max)
  for building the synthetic-substation target (``robust_series_peak``);
* household-pool splitting so synthetic substations in train and test share no
  households -- the honest internal generalisation test
  (``household_pool_split``);
* confound-aware FeederBW targets: heat-pump-only capacity, total
  electric-heating capacity, and an HP-dominant mask (``feederbw_targets``);
* cross-validated XGBoost tuning with the final model trained to the
  early-stopped iteration count (``tune_xgb_cv``).
"""

import numpy as np
import pandas as pd
from tqdm import trange


# ===========================================================================
# Windowed-HDD feature extractor  (ported verbatim from notebook cell 103)
# ===========================================================================

def assign_time_window(ts):
    """4 broad time windows: night 00-06, morning 06-10, day 10-16, evening 16-24."""
    h = ts.hour
    if 0 <= h < 6:
        return "night"
    elif 6 <= h < 10:
        return "morning"
    elif 10 <= h < 16:
        return "day"
    else:
        return "evening"


def assign_hdd_bin(severity, mild_thresh, cold_thresh):
    """Daily severity bins: warm (0), mild, cold, extreme."""
    if pd.isna(severity):
        return np.nan
    if severity <= 0:
        return "warm"
    elif severity <= mild_thresh:
        return "mild"
    elif severity <= cold_thresh:
        return "cold"
    else:
        return "extreme"


def safe_std(x):
    x = pd.Series(x).dropna()
    if len(x) < 2:
        return np.nan
    return x.std(ddof=1)


def safe_skew(x):
    x = pd.Series(x).dropna()
    if len(x) < 3:
        return np.nan
    return x.skew()


def safe_kurtosis(x):
    x = pd.Series(x).dropna()
    if len(x) < 4:
        return np.nan
    return x.kurt()


def safe_quantile(x, q):
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return np.nan
    return x.quantile(q)


def safe_cov(x, y):
    x = pd.Series(x)
    y = pd.Series(y)
    mask = x.notna() & y.notna()
    x = x[mask]
    y = y[mask]
    if len(x) < 2:
        return np.nan
    return np.cov(x, y, ddof=1)[0, 1]


def safe_corr(x, y):
    x = pd.Series(x)
    y = pd.Series(y)
    mask = x.notna() & y.notna()
    x = x[mask]
    y = y[mask]
    if len(x) < 3:
        return np.nan
    if x.std(ddof=1) == 0 or y.std(ddof=1) == 0:
        return np.nan
    return x.corr(y)


def add_distribution_features(feature_dict, prefix, values,
                              include_minmax=True,
                              include_shape=True,
                              include_quantiles=True):
    """Add statistical features for a vector of load values."""
    s = pd.Series(values).dropna()

    feature_dict[f"{prefix}_Mean"] = s.mean() if len(s) > 0 else np.nan
    feature_dict[f"{prefix}_Std"] = safe_std(s)

    if include_minmax:
        feature_dict[f"{prefix}_Min"] = s.min() if len(s) > 0 else np.nan
        feature_dict[f"{prefix}_Max"] = s.max() if len(s) > 0 else np.nan
        feature_dict[f"{prefix}_Max-Min"] = (s.max() - s.min()) if len(s) > 0 else np.nan

    if include_shape:
        feature_dict[f"{prefix}_Skew"] = safe_skew(s)
        feature_dict[f"{prefix}_Kurtosis"] = safe_kurtosis(s)

    if include_quantiles:
        feature_dict[f"{prefix}_Q50"] = safe_quantile(s, 0.50)
        feature_dict[f"{prefix}_Q95"] = safe_quantile(s, 0.95)

    feature_dict[f"{prefix}_N_obs"] = len(s)


def extract_windowed_hdd_features_from_series(
    load_series,
    temp_series,
    resolution=15,
    T_base=12.0,
    mild_thresh=10.0,
    cold_thresh=25.0,
    weekday_only=True,
    window_order=None,
    bin_order=None,
    compare_pairs=None,
    stats_for_comparison=None,
    epsilon=1e-6,
    include_shape=True,
    include_minmax=True,
    include_quantiles=True,
    include_n_days=True,
    include_corr_features=False,
    include_climate_context=False,
    normalize_by_peak=False,
    return_aligned=False,
):
    """Windowed HDD-binned features from one load series and one temperature series.

    ``T_base`` is the national HDD base temperature and is intentionally
    dataset-specific (12 degC Switzerland, 15 degC Germany). The daily-severity
    bin thresholds (``mild_thresh`` / ``cold_thresh``) are on the same
    degree-hour scale in every dataset, so the four-bin structure stays
    comparable even though the base differs.
    """
    if window_order is None:
        window_order = ["night", "morning", "day", "evening"]
    if bin_order is None:
        bin_order = ["warm", "mild", "cold", "extreme"]
    if compare_pairs is None:
        compare_pairs = [
            ("mild", "warm"),
            ("cold", "warm"),
            ("extreme", "warm"),
            ("extreme", "cold"),
        ]
    if stats_for_comparison is None:
        stats_for_comparison = ["Mean", "Std", "Q50", "Q95", "Max"]

    if not isinstance(load_series.index, pd.DatetimeIndex):
        raise ValueError("load_series must have a DatetimeIndex")
    if not isinstance(temp_series.index, pd.DatetimeIndex):
        raise ValueError("temp_series must have a DatetimeIndex")

    load_series = load_series.resample(f"{resolution}min").mean().ffill()
    temp_series = temp_series.resample(f"{resolution}min").mean().ffill()

    if weekday_only:
        load_series = load_series[load_series.index.weekday < 5]
        temp_series = temp_series[temp_series.index.weekday < 5]

    aligned = pd.concat([load_series, temp_series], axis=1, join="inner")
    aligned.columns = ["Total_Load", "Temperature"]
    aligned = aligned.dropna()

    if aligned.empty:
        return ({}, aligned) if return_aligned else {}

    aligned["Date"] = aligned.index.date
    aligned["Window"] = [assign_time_window(ts) for ts in aligned.index]

    aligned["HDH"] = np.maximum(T_base - aligned["Temperature"], 0.0)
    aligned["HDH_qh"] = aligned["HDH"] * (resolution / 60.0)

    daily_severity = aligned.groupby("Date")["HDH_qh"].sum().rename("Daily_HDH_Severity")
    aligned = aligned.join(daily_severity, on="Date")

    aligned["HDD_Bin"] = aligned["Daily_HDH_Severity"].apply(
        lambda x: assign_hdd_bin(x, mild_thresh=mild_thresh, cold_thresh=cold_thresh)
    )

    feat = {}

    if include_climate_context:
        feat["Feature Daily_HDH_Severity_Mean"] = daily_severity.mean()
        feat["Feature Daily_HDH_Severity_Std"] = daily_severity.std(ddof=1)
        feat["Feature Daily_HDH_Severity_Max"] = daily_severity.max()
        feat["Feature N_weekdays"] = aligned["Date"].nunique()

    for window in window_order:
        for hdd_bin in bin_order:
            mask = (aligned["Window"] == window) & (aligned["HDD_Bin"] == hdd_bin)

            load_vals = aligned.loc[mask, "Total_Load"]
            temp_vals = aligned.loc[mask, "Temperature"]
            hdh_vals = aligned.loc[mask, "HDH"]
            n_days = aligned.loc[mask, "Date"].nunique()

            prefix = f"Feature {window}_{hdd_bin}"

            add_distribution_features(
                feat, prefix, load_vals,
                include_minmax=include_minmax,
                include_shape=include_shape,
                include_quantiles=include_quantiles,
            )

            if include_n_days:
                feat[f"{prefix}_N_days"] = n_days

            if include_corr_features:
                feat[f"{prefix}_Cov_Temp"] = safe_cov(load_vals, temp_vals)
                feat[f"{prefix}_Corr_Temp"] = safe_corr(load_vals, temp_vals)
                feat[f"{prefix}_Cov_HDH"] = safe_cov(load_vals, hdh_vals)
                feat[f"{prefix}_Corr_HDH"] = safe_corr(load_vals, hdh_vals)

    for window in window_order:
        for high_bin, low_bin in compare_pairs:
            for stat in stats_for_comparison:
                high_key = f"Feature {window}_{high_bin}_{stat}"
                low_key = f"Feature {window}_{low_bin}_{stat}"

                high_val = feat.get(high_key, np.nan)
                low_val = feat.get(low_key, np.nan)

                feat[f"Feature {window}_delta_{stat}_{high_bin}_{low_bin}"] = (
                    high_val - low_val
                    if pd.notna(high_val) and pd.notna(low_val)
                    else np.nan
                )
                feat[f"Feature {window}_ratio_{stat}_{high_bin}_{low_bin}"] = (
                    high_val / (low_val + epsilon)
                    if pd.notna(high_val) and pd.notna(low_val)
                    else np.nan
                )
                feat[f"Feature {window}_normdelta_{stat}_{high_bin}_{low_bin}"] = (
                    (high_val - low_val) / (low_val + epsilon)
                    if pd.notna(high_val) and pd.notna(low_val)
                    else np.nan
                )

    if normalize_by_peak:
        peak_load = aligned["Total_Load"].max()
        magnitude_keys = ["Mean", "Std", "Min", "Max", "Max-Min", "Q50", "Q95"]
        for col in list(feat.keys()):
            if any(col.endswith(f"_{k}") for k in magnitude_keys):
                feat[f"{col}_norm_peak"] = (
                    feat[col] / peak_load
                    if pd.notna(peak_load) and peak_load != 0 else np.nan)

    return (feat, aligned) if return_aligned else feat


def extract_windowed_hdd_features_from_entity_dataframe(
    entity_df,
    load_col="Total_Load",
    temp_col="Temperature",
    show_progress=True,
    use_entity_index=False,
    **kwargs,
):
    """Apply the extractor to a dataframe with a load series and temp series per row.

    By default the result is indexed positionally 0..n-1, matching the original
    notebook behaviour so cached feature matrices and downstream positional
    alignment are preserved. Pass ``use_entity_index=True`` to index the result
    by ``entity_df.index`` instead (safer, label-aligned), which the corrected
    transfer pipeline uses.
    """
    feat_dict = {}
    n = len(entity_df)
    iterator = trange(n, desc="Windowed HDD features") if show_progress else range(n)
    for i in iterator:
        feat = extract_windowed_hdd_features_from_series(
            load_series=entity_df.iloc[i][load_col],
            temp_series=entity_df.iloc[i][temp_col],
            return_aligned=False,
            **kwargs,
        )
        feat_dict[entity_df.index[i] if use_entity_index else i] = feat
    return pd.DataFrame.from_dict(feat_dict, orient="index")


# ===========================================================================
# Corrected-pipeline helpers
# ===========================================================================

def clip_non_negative(values):
    """Installed capacity cannot be negative; clip predictions at zero."""
    return np.maximum(np.asarray(values, dtype=float), 0.0)


def robust_series_peak(series, q=0.999):
    """Robust per-device peak power (kW) for a capacity proxy.

    The raw maximum of a 15-minute series is spike-sensitive and a poor
    nameplate proxy; the high quantile is stable while still tracking the
    rated draw. Used to build the synthetic-substation capacity target as the
    sum of household robust peaks.
    """
    s = pd.Series(series).dropna()
    if len(s) == 0:
        return np.nan
    return float(s.quantile(q))


def household_pool_split(households, test_frac=0.5, seed=42):
    """Partition a household pool into disjoint train and test sets.

    Synthetic substations must be built from disjoint household pools so that a
    train substation and a test substation never share a household. With a
    shared pool every household recurs in almost every substation, so any
    substation-level split leaks: the internal test then measures memorising a
    handful of households rather than generalising to unseen ones.
    """
    rng = np.random.default_rng(seed)
    hh = np.array(sorted(households))
    perm = rng.permutation(len(hh))
    n_test = int(round(len(hh) * test_frac))
    test_hh = set(hh[perm[:n_test]].tolist())
    train_hh = set(hh[perm[n_test:]].tolist())
    return train_hh, test_hh


def add_scale_features(X, scale, name="Feature Scale"):
    """Append an absolute size anchor to a peak-normalised feature matrix.

    The windowed-HDD shape features are peak-normalised to remove the size
    confound, which also removes the scale needed to predict an absolute-kW
    capacity. Re-introducing one explicit size feature (consumer or housing
    count) lets the model recover absolute magnitude and, crucially, transfer
    to feeders of a very different size from the training pool. ``scale`` is a
    Series aligned to ``X.index`` or an array in row order.
    """
    X = X.copy()
    if isinstance(scale, pd.Series):
        X[name] = scale.reindex(X.index).to_numpy()
    else:
        X[name] = np.asarray(scale, dtype=float)
    return X


# --- FeederBW confound-aware targets --------------------------------------

_ELECTRIC_HEATING_COLS = [
    "heat_pumps_kW",
    "storage_heaters_kW",
    "electric_heaters_kW",
    "flow-type_heaters_kW",
    "hot_water_tanks_kW",
]


def feederbw_targets(meta_static_df, dominance_frac=0.5):
    """Confound-aware capacity targets for FeederBW feeders.

    A feeder's net-load temperature response is driven by all its electric
    heating, not heat pumps alone; on FeederBW storage and resistive heaters
    dominate. Returns a frame indexed by feeder with:

    * ``HP_kW``       -- registered heat-pump capacity (HP-only target);
    * ``ElecHeat_kW`` -- total electric-heating capacity (HP + storage +
                         resistive + flow + hot-water), the quantity the
                         temperature response actually reflects;
    * ``HP_dominant`` -- True where heat pumps are at least ``dominance_frac``
                         of the electric-heating total, an HP-specific subset.
    """
    m = meta_static_df.copy()
    present = [c for c in _ELECTRIC_HEATING_COLS if c in m.columns]
    heat = m[present].fillna(0.0)
    hp = heat["heat_pumps_kW"] if "heat_pumps_kW" in heat else 0.0
    total = heat.sum(axis=1)
    out = pd.DataFrame(index=m.index)
    out["HP_kW"] = hp
    out["ElecHeat_kW"] = total
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(total > 0, np.asarray(hp) / np.asarray(total), 0.0)
    out["HP_dominant"] = frac >= dominance_frac
    return out


# --- Cross-validated XGBoost tuning ---------------------------------------

def tune_xgb_cv(X_train, y_train, max_evals=100, n_splits=4, seed=42,
                early_stopping_rounds=25, verbose=True):
    """Tune XGBoost with K-fold CV inside the Hyperopt objective.

    Fixes two issues in the earlier single-split tuner: the objective is scored
    by cross-validation rather than one fixed hold-out split, and each fold
    uses early stopping so the searched ``n_estimators`` is a genuine cap. The
    final model is trained to the median early-stopped iteration count across
    folds at the best hyper-parameters, so the deployed model matches the one
    the search scored.
    """
    import time
    import xgboost as xgb
    from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
    from hyperopt.early_stop import no_progress_loss
    from sklearn.model_selection import KFold
    from sklearn.metrics import mean_squared_error

    X_train = pd.DataFrame(X_train)
    y_train = np.asarray(y_train).ravel()
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)

    def objective(space):
        losses, best_iters = [], []
        for tr, va in kf.split(X_train):
            reg = xgb.XGBRegressor(
                learning_rate=space["eta"],
                n_estimators=int(space["n_estimators"]),
                max_depth=int(space["max_depth"]),
                gamma=space["gamma"],
                subsample=space["subsample"],
                reg_alpha=space["reg_alpha"],
                reg_lambda=space["reg_lambda"],
                min_child_weight=int(space["min_child_weight"]),
                colsample_bytree=space["colsample_bytree"],
                eval_metric="mae",
                tree_method="hist",
                early_stopping_rounds=early_stopping_rounds,
                n_jobs=-1,
            )
            reg.fit(X_train.iloc[tr], y_train[tr],
                    eval_set=[(X_train.iloc[va], y_train[va])], verbose=False)
            pred = reg.predict(X_train.iloc[va])
            losses.append(mean_squared_error(y_train[va], pred))
            bi = getattr(reg, "best_iteration", None)
            best_iters.append(int(bi) if bi is not None else int(space["n_estimators"]))
        return {"loss": float(np.mean(losses)), "status": STATUS_OK,
                "best_n_estimators": int(np.median(best_iters))}

    space = {
        "eta": hp.uniform("eta", 0.01, 0.3),
        "max_depth": hp.quniform("max_depth", 3, 10, 1),
        "gamma": hp.uniform("gamma", 0, 10),
        "subsample": hp.uniform("subsample", 0.5, 1.0),
        "reg_alpha": hp.uniform("reg_alpha", 0, 1),
        "reg_lambda": hp.uniform("reg_lambda", 0, 10),
        "colsample_bytree": hp.uniform("colsample_bytree", 0.3, 1.0),
        "min_child_weight": hp.quniform("min_child_weight", 1, 20, 1),
        "n_estimators": hp.quniform("n_estimators", 50, 500, 10),
    }

    trials = Trials()
    t0 = time.time()
    best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=max_evals,
                trials=trials, early_stop_fn=no_progress_loss(30),
                show_progressbar=False)
    if verbose:
        print(f"XGB CV tuning: {time.time() - t0:.1f}s over {len(trials.trials)} evals")

    best_n = int(trials.best_trial["result"].get(
        "best_n_estimators", int(best["n_estimators"])))

    model = xgb.XGBRegressor(
        learning_rate=best["eta"],
        n_estimators=max(20, best_n),
        max_depth=int(best["max_depth"]),
        gamma=best["gamma"],
        subsample=best["subsample"],
        reg_alpha=best["reg_alpha"],
        reg_lambda=best["reg_lambda"],
        min_child_weight=int(best["min_child_weight"]),
        colsample_bytree=best["colsample_bytree"],
        eval_metric="mae",
        tree_method="hist",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    meta = dict(best)
    meta["n_estimators_final"] = max(20, best_n)
    return model, meta


def compute_metrics(y_true, y_pred):
    """RMSE, MAE, MAPE (over non-zero truth), R^2."""
    from sklearn.metrics import (root_mean_squared_error, mean_absolute_error,
                                 mean_absolute_percentage_error, r2_score)
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    rmse = root_mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mask = y_true != 0
    mape = (mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100
            if mask.sum() > 0 else np.nan)
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan
    return dict(rmse=rmse, mae=mae, mape=mape, r2=r2)


def select_scale_free_columns(X):
    """Names of the dimensionless features (peak-normalised magnitudes + ratios)."""
    return [c for c in X.columns
            if c.endswith("_norm_peak") or "ratio_" in c or "normdelta_" in c]


def series_peak(series):
    """Observed peak (max) of a load series, used as a scale anchor."""
    return float(pd.Series(series).dropna().max())


def capacity_feature_matrix(X_raw, scalefree_cols, size, peak):
    """Assemble the capacity model's feature matrix: scale-free + two size anchors.

    ``X_raw`` is the full windowed-HDD feature frame; ``scalefree_cols`` the
    dimensionless columns to keep; ``size`` and ``peak`` are Series aligned to
    ``X_raw.index`` (household/housing count and observed feeder peak load).
    Reindexing to ``scalefree_cols`` guarantees train and transfer datasets
    present identical columns in identical order.
    """
    X = X_raw.reindex(columns=list(scalefree_cols)).copy()
    X = add_scale_features(X, size, name="Feature Scale_size")
    X = add_scale_features(X, peak, name="Feature Scale_peak")
    return X.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)


def build_wpuq_substations(pool, n=400, size_range=(10, 37), pen_max=0.5, seed=7,
                           robust_q=0.999):
    """Synthetic substations from the WPUQ pool of HP-equipped houses.

    WPUQ has one feeder of 37 single-family houses, each with a submetered heat
    pump. To test transfer across a *distribution* rather than a single n=1
    aggregate, many substations are drawn from these houses over a chosen size
    and penetration range: an HP member contributes its heat-pump + household
    load, a fill member only its household (non-HP) load. The target is the
    robust HP peak summed over the HP members, the same definition as the Swiss
    target. Returns a DataFrame with Total_Load, Temperature, size, HP_Peak.
    """
    rng = np.random.default_rng(seed)
    idx = pool["index"]
    hp_mat, other_mat = pool["hp_mat"], pool["other_mat"]
    n_house = hp_mat.shape[0]
    robust_hp = np.array([robust_series_peak(hp_mat[i], robust_q) for i in range(n_house)])
    temp = pd.Series(pool["temperature"]["WPUQ"], index=idx)

    rows = {}
    for k in range(n):
        size = int(rng.integers(size_range[0], size_range[1] + 1))
        n_hp = int(round(float(rng.uniform(0.0, pen_max)) * size))
        hp_members = rng.integers(0, n_house, n_hp)
        fill_members = rng.integers(0, n_house, size - n_hp)
        load = np.zeros(len(idx))
        for i in hp_members:
            load += hp_mat[i] + other_mat[i]
        for i in fill_members:
            load += other_mat[i]
        rows[k] = {"Total_Load": pd.Series(load, index=idx), "Temperature": temp,
                   "size": size, "HP_Peak": float(robust_hp[hp_members].sum()) if n_hp else 0.0}
    return pd.DataFrame.from_dict(rows, orient="index")


def build_wpuq_real_feeder(pool, robust_q=0.999):
    """The single REAL WPUQ feeder: the true aggregate of all houses.

    Unlike build_wpuq_substations (which draws many synthetic combinations),
    this sums every house's heat-pump + household load into one net-load series
    -- the actual feeder as measured. Every WPUQ house has a heat pump, so this
    is a ~100%-penetration feeder (well outside the Swiss training range). The
    target is the true installed HP capacity: the robust per-house peak summed
    over all houses. Returns a one-row DataFrame (Total_Load, Temperature, size,
    HP_Peak) matching build_wpuq_substations for the same feature pipeline.
    """
    idx = pool["index"]
    hp_mat, other_mat = pool["hp_mat"], pool["other_mat"]
    n_house = hp_mat.shape[0]
    robust_hp = np.array([robust_series_peak(hp_mat[i], robust_q) for i in range(n_house)])
    load = (hp_mat + other_mat).sum(axis=0)
    temp = pd.Series(pool["temperature"]["WPUQ"], index=idx)
    row = {"Total_Load": pd.Series(load, index=idx), "Temperature": temp,
           "size": int(n_house), "HP_Peak": float(robust_hp.sum())}
    return pd.DataFrame.from_dict({"WPUQ_real": row}, orient="index")


def build_substations_norepl(pool, n_train=1000, n_test=1000, min_size=10,
                             max_size=120, pen_range=(0.1, 1.0), test_frac=0.25,
                             min_station_pool=3, robust_q=0.999, seed=42):
    """Synthetic substations from a household pool, drawn WITHOUT replacement.

    Every dwelling in a substation is a distinct household (no profile is stacked
    on itself), so feeder size and penetration are bounded by the number of
    distinct HP households available on the feeder's weather station.

    * Household-disjoint split (B1): HP households are split per station and the
      non-HP fill pool globally into train/test; a train substation shares no
      household with a test one.
    * Weather-consistent HP members (C1): the HP members of a substation are all
      drawn from one station, so a single temperature series applies. The non-HP
      fill contributes only its weather-independent load and is drawn from the
      whole (global) non-HP pool.
    * Robust target (A1): HP_Peak is the sum of the robust (99.9th-pct) per-house
      peaks over the distinct HP members.

    Returns a DataFrame (size, HP_ratio, weather_id, split, HP_Peak, Total_Load,
    Temperature) matching the other substation builders for the same pipeline.
    """
    rng = np.random.default_rng(seed)
    idx = pool["index"]
    hp_mat, other_mat = pool["hp_mat"], pool["other_mat"]
    households = list(pool["households"])
    hp_households = list(pool["hp_households"])
    wof = pool["weather_of"]

    other_pos = {h: i for i, h in enumerate(households)}
    hp_pos = {h: i for i, h in enumerate(hp_households)}
    robust_hp = {h: robust_series_peak(hp_mat[hp_pos[h]], robust_q)
                 for h in hp_households}
    hp_set = set(hp_households)
    non_hp = [h for h in households if h not in hp_set]

    # station -> HP households
    by_station = {}
    for h in hp_households:
        by_station.setdefault(wof[h], []).append(h)

    # household-disjoint split: HP per station (stratified), fill globally
    def split_list(items, tf):
        it = list(items)
        rng.shuffle(it)
        k = int(round((1.0 - tf) * len(it)))
        return it[:k], it[k:]

    hp_split = {"train": {}, "test": {}}
    for st, hs in by_station.items():
        tr, te = split_list(hs, test_frac)
        if tr:
            hp_split["train"][st] = tr
        if te:
            hp_split["test"][st] = te
    fill_tr, fill_te = split_list(non_hp, test_frac)
    fill_split = {"train": fill_tr, "test": fill_te}

    # stations usable as a seed (>= min_station_pool HP households in the split)
    seeds = {sp: [(st, hs) for st, hs in hp_split[sp].items()
                  if len(hs) >= min_station_pool]
             for sp in ("train", "test")}
    temp_cache = {st: pd.Series(arr, index=idx)
                  for st, arr in pool["temperature"].items()}

    lo, hi = pen_range
    rows = {}
    k = 0
    for split, n in (("train", n_train), ("test", n_test)):
        stations = seeds[split]
        weights = np.array([len(hs) for _, hs in stations], float)
        weights /= weights.sum()
        fill_pool = np.array(fill_split[split], dtype=object)
        for _ in range(n):
            st, hp_pool = stations[rng.choice(len(stations), p=weights)]
            nH = len(hp_pool)
            pen = float(rng.uniform(lo, hi))
            # without replacement: n_hp = round(pen*size) <= nH  =>  size <= nH/pen
            size_max = min(max_size, int(nH / pen))
            if size_max < min_size:               # station too small at this pen
                pen = min(hi, nH / min_size)
                size_max = min(max_size, int(nH / pen))
            size = int(rng.integers(min_size, size_max + 1))
            n_hp = min(int(round(pen * size)), nH)
            n_hp = max(n_hp, 1)
            n_fill = size - n_hp

            hp_members = rng.choice(hp_pool, n_hp, replace=False)
            fill_members = (rng.choice(fill_pool, min(n_fill, len(fill_pool)),
                                       replace=False) if n_fill > 0 else [])

            hp_rows = [hp_pos[h] for h in hp_members]
            oth_rows = ([other_pos[h] for h in hp_members]
                        + [other_pos[h] for h in fill_members])
            load = hp_mat[hp_rows].sum(axis=0) + other_mat[oth_rows].sum(axis=0)
            rows[k] = {
                "size": size, "HP_ratio": n_hp / size, "weather_id": st,
                "split": split,
                "HP_Peak": float(sum(robust_hp[h] for h in hp_members)),
                "Total_Load": pd.Series(load.astype(np.float32), index=idx),
                "Temperature": temp_cache[st],
            }
            k += 1
    return pd.DataFrame.from_dict(rows, orient="index")


# --- FeederBW loading (in-distribution electric-heating estimation) --------

_FBW_HEAT_COLS = ["heat_pumps_kW", "storage_heaters_kW", "electric_heaters_kW",
                  "flow-type_heaters_kW", "hot_water_tanks_kW"]


def load_feederbw(feederbw_dir="data/FeederBW", year=2024):
    """Load downloaded FeederBW feeders into net-load / temperature series + metadata.

    Returns (feeder_df, static, end) where feeder_df is indexed by feeder id
    with a Total_Load and Temperature series for ``year``; ``static`` / ``end``
    are the first / last metadata rows in ``year`` (for capacity targets and
    stability). Only feeders whose measurement parquet has been downloaded are
    included, so this scales as more batches are added.
    """
    from pathlib import Path
    fdir = Path(feederbw_dir)
    meta = pd.read_csv(fdir / "feeder_metadata.csv")
    meta["date"] = pd.to_datetime(meta["date"])
    wx = pd.read_parquet(fdir / "weather_data.parquet")
    lo, hi = pd.Timestamp(f"{year}-01-01", tz="UTC"), pd.Timestamp(f"{year + 1}-01-01", tz="UTC")

    m_y = meta[(meta.date >= lo.tz_localize(None)) & (meta.date < hi.tz_localize(None))]
    start = m_y.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder")
    end = m_y.sort_values("date").drop_duplicates("feeder", keep="last").set_index("feeder")
    static = start.combine_first(
        meta.sort_values("date").drop_duplicates("feeder", keep="first").set_index("feeder"))

    # glob recursively across every downloaded measurement batch (nesting differs
    # between the 001-040 zip and the later ones); one parquet per feeder id.
    files = {}
    for fp in sorted(fdir.rglob("feeder_*.parquet")):
        try:
            files.setdefault(int(fp.stem.split("_")[-1]), fp)
        except ValueError:
            continue

    rows = {}
    for fid, fp in files.items():
        fdf = pd.read_parquet(fp)
        fdf["timestamp_UTC"] = pd.to_datetime(fdf["timestamp_UTC"], utc=True)
        fdf = fdf[(fdf["timestamp_UTC"] >= lo) & (fdf["timestamp_UTC"] < hi)]
        fdf = fdf.sort_values("timestamp_UTC").set_index("timestamp_UTC")
        w = wx[wx["feeder"] == fid].copy()
        w["timestamp_UTC"] = pd.to_datetime(w["timestamp_UTC"], utc=True)
        w = w.sort_values("timestamp_UTC").set_index("timestamp_UTC")
        load = fdf["active_power_kW"].resample("15min").mean().rename("Total_Load")
        temp = (w["air_temperature_C"].resample("15min").interpolate("time")
                .ffill().bfill().rename("Temperature"))
        a = pd.concat([load, temp], axis=1, join="inner").dropna()
        if not a.empty and fid in static.index:
            rows[fid] = {"Total_Load": a["Total_Load"], "Temperature": a["Temperature"]}
    fbw = pd.DataFrame.from_dict(rows, orient="index")
    fbw.index.name = "Feeder_ID"
    return fbw, static, end


def feederbw_capacity_frame(fbw_index, static, end):
    """Per-feeder targets, stability flag, size and substation for FeederBW.

    Columns: ElecHeat_kW, HP_kW, HP_frac, housing, substation, elecheat_stable.
    """
    s = static.reindex(fbw_index)
    h = s[[c for c in _FBW_HEAT_COLS if c in s.columns]].fillna(0)
    e = end.reindex(fbw_index)[[c for c in _FBW_HEAT_COLS if c in end.columns]].fillna(0)
    out = pd.DataFrame(index=fbw_index)
    out["ElecHeat_kW"] = h.sum(axis=1)
    out["HP_kW"] = h["heat_pumps_kW"] if "heat_pumps_kW" in h else 0.0
    out["HP_frac"] = np.where(out.ElecHeat_kW > 0, out.HP_kW / out.ElecHeat_kW, 0.0)
    out["housing"] = s["housing_units_count"]
    out["substation"] = s["substation"]
    out["elecheat_stable"] = (e.sum(axis=1) - out["ElecHeat_kW"]).abs().fillna(1e9) == 0
    return out
