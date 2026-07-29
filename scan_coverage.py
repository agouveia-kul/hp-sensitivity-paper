"""Scan every HEAPO household and build a daily submetering-coverage matrix.

For each household and each calendar day, count the 15-min samples where BOTH
`kWh_received_HeatPump` and `kWh_received_Other` are present -- the two series
the hypothesis tests need (SF needs the submetered HP load; the non-HP member
load needs `Other`).

The matrix is cached so the 1-year-window search can be re-run instantly.
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')
from heapo import HEAPO

OUT = 'data/_heapo_daily_coverage.parquet'
SAMPLES_PER_DAY = 96          # 15-min resolution


def main():
    h = HEAPO(data_path='data/heapo_data', use_local_time=False,
              suppress_warning=True)
    households = h.get_all_households()
    print(f'scanning {len(households)} households', flush=True)

    series = {}
    for k, hid in enumerate(households):
        try:
            df = h.load_smart_meter_data(hid, resolution='15min')
        except Exception:
            continue
        if df is None or not len(df):
            continue
        both = df['kWh_received_HeatPump'].notna() & df['kWh_received_Other'].notna()
        if not both.any():
            continue
        ts = pd.to_datetime(df.loc[both, 'Timestamp'], utc=True)
        counts = ts.dt.floor('D').value_counts().sort_index()
        series[hid] = counts
        if (k + 1) % 100 == 0:
            print(f'  {k + 1}/{len(households)} scanned, {len(series)} with data',
                  flush=True)

    cov = pd.DataFrame(series).fillna(0).astype('int16').sort_index()
    cov.index.name = 'date'
    cov.to_parquet(OUT)
    print(f'saved {cov.shape[0]} days x {cov.shape[1]} households -> {OUT}',
          flush=True)


if __name__ == '__main__':
    main()
