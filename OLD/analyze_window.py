"""Find the 1-year window with the most households at >=90% submetering coverage.

Consumes the daily coverage matrix from scan_coverage.py (days x households,
each cell = number of 15-min samples that day where BOTH kWh_received_HeatPump
and kWh_received_Other are present).
"""
import numpy as np
import pandas as pd

COV = 'data/_heapo_daily_coverage.parquet'
WINDOW_DAYS = 365
SAMPLES_PER_DAY = 96
COVERAGE = 0.90


def window_counts(cov, window_days=WINDOW_DAYS, coverage=COVERAGE):
    """Households meeting the coverage threshold for every possible window start."""
    full = pd.date_range(cov.index.min(), cov.index.max(), freq='D')
    c = cov.reindex(full).fillna(0).to_numpy(dtype=np.int32)
    required = coverage * window_days * SAMPLES_PER_DAY

    cum = np.vstack([np.zeros((1, c.shape[1]), np.int64), np.cumsum(c, axis=0)])
    n_start = len(full) - window_days + 1
    if n_start <= 0:
        raise ValueError('data span shorter than the window')
    totals = cum[window_days:window_days + n_start] - cum[:n_start]
    counts = (totals >= required).sum(axis=1)
    return pd.DataFrame({'start': full[:n_start],
                         'end': full[:n_start] + pd.Timedelta(days=window_days - 1),
                         'n_households': counts}), totals, full[:n_start]


def main():
    cov = pd.read_parquet(COV)
    cov.index = pd.to_datetime(cov.index)
    print(f'coverage matrix: {cov.shape[0]} days x {cov.shape[1]} households')
    print(f'span: {cov.index.min().date()} -> {cov.index.max().date()}')

    res, totals, starts = window_counts(cov)
    best = res.loc[res['n_households'].idxmax()]
    print(f'\n{"=" * 70}')
    print(f'BEST 1-YEAR WINDOW at >={COVERAGE:.0%} coverage of BOTH series')
    print(f'{"=" * 70}')
    print(f'  {best["start"].date()} -> {best["end"].date()} : '
          f'{best["n_households"]} households')

    print('\ntop 10 non-overlapping-ish window starts:')
    top = res.sort_values('n_households', ascending=False).head(400)
    chosen, used = [], []
    for _, r in top.iterrows():
        if all(abs((r['start'] - u).days) > 60 for u in used):
            chosen.append(r); used.append(r['start'])
        if len(chosen) == 10:
            break
    for r in chosen:
        print(f'  {r["start"].date()} -> {r["end"].date()} : {r["n_households"]:4d}')

    # calendar years for reference
    print('\ncalendar-year comparison:')
    for yr in range(int(cov.index.min().year), int(cov.index.max().year) + 1):
        s = pd.Timestamp(f'{yr}-01-01', tz='UTC')
        m = res[res['start'] == s]
        if len(m):
            print(f'  {yr}: {int(m.iloc[0]["n_households"]):4d} households')

    # sensitivity to the coverage threshold at the best window
    print('\nsensitivity at the best window:')
    i = int(np.argmax(res['n_households'].to_numpy()))
    for cvg in [0.80, 0.85, 0.90, 0.95, 0.99]:
        req = cvg * WINDOW_DAYS * SAMPLES_PER_DAY
        print(f'  >={cvg:.0%}: {int((totals[i] >= req).sum()):4d} households')

    res.to_parquet('data/_window_scan.parquet')
    ids = cov.columns[totals[i] >= COVERAGE * WINDOW_DAYS * SAMPLES_PER_DAY]
    pd.Series(ids, name='Household_ID').to_csv('data/best_window_households.csv',
                                               index=False)
    print(f'\nsaved window scan and {len(ids)} household IDs for the best window')


if __name__ == '__main__':
    main()
