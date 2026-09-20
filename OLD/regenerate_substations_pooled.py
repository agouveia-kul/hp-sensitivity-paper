"""Regenerate synthetic HEAPO substations with a household-disjoint split.

Fixes for the capacity-estimation pipeline, applied at generation time:

* B1 -- the household pool is split into disjoint train/test sets FIRST, and
  train substations are built only from train households, test only from test.
  A substation in one split shares no household with a substation in the other,
  so the internal test measures generalisation to unseen households.
* A1 -- the per-household capacity is the robust 99.9th-percentile HP power,
  not the spike-sensitive raw max, and the substation target is their sum.
* C1 -- every member of a substation (HP and non-HP fill) is drawn from the
  same weather station, so one temperature series applies to the whole feeder.
* realistic penetration -- HP ratio is drawn low and includes zero, so the
  training distribution covers low-penetration and no-HP feeders like the real
  German ones, rather than the old 10--100 % range.

Run:  python regenerate_substations_pooled.py           # full build
      python regenerate_substations_pooled.py --dry-run # data prep + inspect only
"""
import os
import sys
import pickle
from datetime import timedelta
from random import Random

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from heapo import HEAPO
import hp_capacity as hc

DRY_RUN = "--dry-run" in sys.argv

START = "2023-01-01 00:00:00+00:00"
END = "2023-12-31 23:45:00+00:00"
MIN_SIZE, MAX_SIZE = 10, 120
# Balanced factorial design: equal number of substations per penetration level
# AND per feeder size (number of consumers), fully crossed. Both marginals are
# balanced by construction rather than by random uniform draws.
PEN_LEVELS = [round(0.1 * k, 1) for k in range(1, 11)]   # 0.10 .. 1.00 (10 levels)
SIZE_LEVELS = list(range(MIN_SIZE, MAX_SIZE + 1, 10))     # 10, 20, .. 120 (12 sizes)
REPLICATES = 9              # substations per (split, penetration, size) cell
N_SUBSTATIONS = 2 * len(PEN_LEVELS) * len(SIZE_LEVELS) * REPLICATES
MIN_STATION_POOL = 3        # a station needs >=3 HP households in the split to seed a substation
SEED = 42
OUT_PATH = "data/substations_data_pooled.pkl"
PREP_CACHE = "data/_regen_prep.pkl"

heapo = HEAPO(data_path="data/heapo_data", use_local_time=False, suppress_warning=True)

# ---------------------------------------------------------------------------
# 1-2) Household coverage + robust per-household HP peak  (cached: slow scan)
# ---------------------------------------------------------------------------
if os.path.exists(PREP_CACHE):
    print(f"Loading cached household prep from {PREP_CACHE} ...", flush=True)
    datarange, all_smd = pickle.load(open(PREP_CACHE, "rb"))
else:
    print("Loading household coverage (slow first-time scan) ...", flush=True)
    households = heapo.get_all_households()
    full_year = pd.date_range(START, END, freq="15min")
    submeter = {}
    for hid in households:
        try:
            d = heapo.load_smart_meter_data(hid, resolution="15min")
            d = d[(d["Timestamp"] >= pd.to_datetime(START)) & (d["Timestamp"] <= pd.to_datetime(END))]
            d = d.dropna(subset=["kWh_received_HeatPump", "kWh_received_Total", "kWh_received_Other"])
            if len(d) > full_year.shape[0] * 0.8:
                submeter[hid] = len(d)
        except Exception:
            pass

    meta = heapo.get_meta_data_overview()
    datarange = pd.DataFrame.from_dict(submeter, orient="index", columns=["n"])
    datarange = datarange.join(meta.set_index("Household_ID")["Weather_ID"])

    weather_ok = {}
    full_year_h = pd.date_range(START, END, freq="h")
    for wid in datarange["Weather_ID"].dropna().unique():
        try:
            w = heapo.load_weather_data(wid, resolution="hourly")
            w = w[(w["Timestamp"] >= pd.to_datetime(START)) & (w["Timestamp"] <= pd.to_datetime(END))]
            w = w.dropna(subset=["Temperature_avg_hourly"])
            if len(w) > full_year_h.shape[0] * 0.8:
                weather_ok[wid] = True
        except Exception:
            pass
    datarange = datarange[datarange["Weather_ID"].isin(weather_ok)]

    print(f"Computing robust HP peaks for {len(datarange)} households ...", flush=True)
    all_smd = heapo.load_smart_meter_data_multiple(datarange.index.tolist(), resolution="15min")
    all_smd = all_smd[(all_smd["Timestamp"] >= pd.to_datetime(START)) & (all_smd["Timestamp"] <= pd.to_datetime(END))]

    robust_peak = {}
    for hid in datarange.index:
        hp_kw = all_smd.loc[all_smd["Household_ID"] == hid, "kWh_received_HeatPump"] * 4
        robust_peak[hid] = hc.robust_series_peak(hp_kw, q=0.999)
    datarange["HP_robust_kW"] = pd.Series(robust_peak)

    pickle.dump((datarange, all_smd), open(PREP_CACHE, "wb"))
    print(f"Cached household prep -> {PREP_CACHE}")

# ---------------------------------------------------------------------------
# 3) Household-disjoint pool split  (B1)
# ---------------------------------------------------------------------------
train_hh, test_hh = hc.household_pool_split(datarange.index.tolist(), test_frac=0.5, seed=SEED)
datarange["split"] = ["train" if h in train_hh else "test" for h in datarange.index]

# HP members are drawn weather-consistently from the substation's station pool
# (they carry the temperature signal); the non-HP fill contributes only the
# weather-independent "Other" channel, so it is drawn from the whole split pool
# for diversity. Stations with too few HP households cannot seed a substation.
def station_pools(split):
    sub = datarange[datarange["split"] == split]
    return {wid: grp.index.tolist() for wid, grp in sub.groupby("Weather_ID")}

pools = {"train": station_pools("train"), "test": station_pools("test")}
split_pool = {s: datarange[datarange["split"] == s].index.tolist() for s in ("train", "test")}
# stations usable as a substation seed, and selection weights ~ pool size
seed_stations = {
    s: [(w, v) for w, v in pools[s].items() if len(v) >= MIN_STATION_POOL]
    for s in ("train", "test")
}

print("\n=== INSPECTION ===")
print(f"households kept: {len(datarange)}  | train {len(train_hh)}  test {len(test_hh)}")
print(f"weather stations: {datarange['Weather_ID'].nunique()}")
print("households per station per split:")
for split in ("train", "test"):
    sizes = {w: len(v) for w, v in pools[split].items()}
    print(f"  {split}: {sizes}")
print("robust HP peak per household (kW): "
      f"min {datarange['HP_robust_kW'].min():.1f}  median {datarange['HP_robust_kW'].median():.1f}  max {datarange['HP_robust_kW'].max():.1f}")

# FeederBW scale reference for the size anchor
try:
    fbw = pd.read_csv("data/FeederBW/feeder_metadata.csv")
    hu = fbw.groupby("feeder")["housing_units_count"].first().dropna()
    print(f"FeederBW housing_units_count: min {hu.min():.0f} median {hu.median():.0f} max {hu.max():.0f}")
except Exception as e:
    print("FeederBW housing units unavailable:", e)

if DRY_RUN:
    print("\n[dry-run] stopping before substation generation.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# 4) Generate substations from disjoint pools
# ---------------------------------------------------------------------------
print(f"\nGenerating {N_SUBSTATIONS} substations ...", flush=True)
rng = Random(SEED)
nprng = np.random.default_rng(SEED)
dt_index = pd.date_range(START, END, freq="15min")
peak_lookup = datarange["HP_robust_kW"].to_dict()

# Pre-align each household's HP and Other channels to the common index ONCE
# (households recur across thousands of substations); building a substation is
# then a sum of cached arrays rather than repeated reindex/interpolate.
print("Pre-aligning household series ...", flush=True)
hp_arr, other_arr = {}, {}
for hid, g in all_smd.groupby("Household_ID"):
    gi = g.set_index("Timestamp").sort_index()
    hp_arr[hid] = (gi["kWh_received_HeatPump"].reindex(dt_index)
                   .interpolate("time").fillna(0).to_numpy(dtype=np.float64))
    other_arr[hid] = (gi["kWh_received_Other"].reindex(dt_index)
                      .interpolate("time").fillna(0).to_numpy(dtype=np.float64))

weather_cache = {}
def get_weather(wid):
    if wid not in weather_cache:
        w = heapo.load_weather_data(wid, resolution="hourly")
        w = w[(w["Timestamp"] >= pd.to_datetime(START)) & (w["Timestamp"] <= pd.to_datetime(END))]
        w = w.set_index("Timestamp")["Temperature_avg_hourly"].resample("15min").interpolate("time")
        weather_cache[wid] = w.reindex(dt_index).astype(np.float32)
    return weather_cache[wid]

n_pts = len(dt_index)
# balanced grid: every (split, penetration, size) cell gets REPLICATES draws, so
# each penetration level and each size holds an equal number of substations.
jobs = [(split, pen, size)
        for split in ("train", "test")
        for pen in PEN_LEVELS
        for size in SIZE_LEVELS
        for _ in range(REPLICATES)]

substations = {}
for i, (split, pen, size) in enumerate(jobs):
    stations = seed_stations[split]
    weights = np.array([len(v) for _, v in stations], dtype=float)
    wid = stations[nprng.choice(len(stations), p=weights / weights.sum())][0]
    pool = pools[split][wid]

    n_hp = int(round(pen * size))

    hp_members = [rng.choice(pool) for _ in range(n_hp)]                    # weather-consistent, with replacement
    fill_members = [rng.choice(split_pool[split]) for _ in range(size - n_hp)]  # non-thermal fill, any station

    hp_load = np.zeros(n_pts)
    total_load = np.zeros(n_pts)
    for hid in hp_members:
        hp_load += hp_arr[hid]
        total_load += hp_arr[hid] + other_arr[hid]
    for hid in fill_members:
        total_load += other_arr[hid]

    hp_load *= 4.0
    total_load *= 4.0

    substations[i] = {
        "size": size,
        "HP_ratio": pen,
        "weather_id": wid,
        "split": split,
        "households_hp": hp_members,
        "households": fill_members,
        "HP_Load": pd.Series(hp_load.astype(np.float32), index=dt_index),
        "Total_Load": pd.Series(total_load.astype(np.float32), index=dt_index),
        "Temperature": get_weather(wid),
        "HP_Peak": float(np.sum([peak_lookup[h] for h in hp_members])) if n_hp else 0.0,
    }
    if (i + 1) % 250 == 0:
        print(f"  {i + 1}/{N_SUBSTATIONS}", flush=True)

df = pd.DataFrame.from_dict(substations, orient="index")
os.makedirs("data", exist_ok=True)
pickle.dump(df, open(OUT_PATH, "wb"))
size_gb = os.path.getsize(OUT_PATH) / 1e9
print(f"\nSaved {len(df)} substations -> {OUT_PATH} ({size_gb:.2f} GB)")
print(f"target HP_Peak (kW): min {df['HP_Peak'].min():.1f} median {df['HP_Peak'].median():.1f} max {df['HP_Peak'].max():.1f}")
print(f"split counts: {df['split'].value_counts().to_dict()}")
