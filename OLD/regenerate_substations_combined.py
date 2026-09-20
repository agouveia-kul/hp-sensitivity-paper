"""Regenerate synthetic Swiss substations from the COMBINED (HEAPO + Swiss)
household pool, drawn WITHOUT replacement.

Complements HEAPO's 57 submetered-HP households with the 24 from the Swiss
smart-meter dataset (whose station KLO is identical to HEAPO's 8jB), giving 81
distinct HP households -- 50 of them on the merged KLO station -- plus ~1620
non-HP dwellings as fill. Every dwelling in a substation is now a distinct
household (no profile stacked on itself); feeder size/penetration are bounded by
the distinct HP households on the feeder's station. Household-disjoint split,
robust 99.9th-pct capacity target.

Writes data/substations_data_pooled.pkl (same path the pipeline consumes).
"""
import os
import pickle

import hp_pools as hpp
import hp_capacity as hc

N_TRAIN, N_TEST = 1000, 1000
MIN_SIZE, MAX_SIZE = 10, 120
PEN_RANGE = (0.1, 1.0)
TEST_FRAC = 0.25            # train keeps ~75% of each station's HP households
MIN_STATION_POOL = 3
SEED = 42
OUT = "data/substations_data_pooled.pkl"

pool = hpp.build_pool_combined(verbose=True)
n_hp = len(pool["hp_households"])
print(f"\ncombined pool: {len(pool['households'])} households | {n_hp} with HP")

df = hc.build_substations_norepl(
    pool, n_train=N_TRAIN, n_test=N_TEST, min_size=MIN_SIZE, max_size=MAX_SIZE,
    pen_range=PEN_RANGE, test_frac=TEST_FRAC, min_station_pool=MIN_STATION_POOL,
    seed=SEED)

os.makedirs("data", exist_ok=True)
pickle.dump(df, open(OUT, "wb"))
gb = os.path.getsize(OUT) / 1e9
print(f"\nSaved {len(df)} substations -> {OUT} ({gb:.2f} GB)")
print(f"split: {df['split'].value_counts().to_dict()}")
print(f"size: min {df['size'].min()} median {int(df['size'].median())} max {df['size'].max()}")
print(f"penetration (HP_ratio): min {df['HP_ratio'].min():.2f} "
      f"median {df['HP_ratio'].median():.2f} max {df['HP_ratio'].max():.2f}")
print(f"weather stations: {df['weather_id'].value_counts().to_dict()}")
print(f"HP_Peak target (kW): min {df['HP_Peak'].min():.1f} "
      f"median {df['HP_Peak'].median():.1f} max {df['HP_Peak'].max():.1f}")
for sp in ("train", "test"):
    s = df[df.split == sp]["HP_Peak"]
    print(f"  {sp}: HP_Peak median {s.median():.1f} max {s.max():.1f}  "
          f"(WPUQ real feeder = 238.5 kW)")
