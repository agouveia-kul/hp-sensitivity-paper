"""Reduce the RHPP Sample B2 2-minute site files (UKDA SN 8151) to daily values.

For every site in ``data/RHPP_GB.zip``: daily mean electric heating-system load
(kW) = E_hp + E_dhw + E_sp + E_boost, the same split per component, daily mean
heat output (H_hp), and the heating-system capacity as the 99.9th percentile of the
15-min resampled load (the convention used for every other dataset). Writes
``data/rhpp_daily.parquet`` (site, day, loads) and ``data/rhpp_sites.parquet``.
Energy columns are Wh per 2 minutes, so kW = Wh * 30 / 1000.
"""
import io
import os
import zipfile

import numpy as np
import pandas as pd

ZIP = 'data/RHPP_GB.zip'
E_COLS = ['Ehp', 'Edhw', 'Esp', 'Eboost']


def main():
    days, sites = [], []
    with zipfile.ZipFile(ZIP) as z:
        names = sorted(n for n in z.namelist() if n.endswith('.csv') and 'processed_rhpp' in n)
        for k, n in enumerate(names):
            d = pd.read_csv(io.BytesIO(z.read(n)), usecols=['Year', 'Month', 'Day', 'Hour', 'Minute', 'Hhp', *E_COLS])
            t = pd.to_datetime(d[['Year', 'Month', 'Day', 'Hour', 'Minute']].rename(columns=str.lower))
            kw = d[E_COLS + ['Hhp']].apply(pd.to_numeric, errors='coerce') * 30.0 / 1000.0
            kw.index = t
            kw['E_total'] = kw[E_COLS].sum(axis=1, min_count=1)
            q15 = kw['E_total'].resample('15min').mean()
            day = kw.resample('D').mean()
            cnt = kw['E_total'].resample('D').count()
            day = day[cnt >= 0.8 * 720]                     # >= 80% of the 720 two-minute slots
            site = 'RHPP' + os.path.basename(n).split('processed_rhpp')[1].split('.')[0]
            day['site'] = site
            days.append(day.reset_index().rename(columns={'index': 'day'}))
            sites.append(dict(site=site, days=len(day), start=day.index.min(), end=day.index.max(),
                              cap=float(q15.dropna().quantile(0.999)),
                              share_boost=float(kw[['Edhw', 'Esp', 'Eboost']].sum().sum() / kw['E_total'].sum())))
            if (k + 1) % 50 == 0:
                print(f'  {k + 1}/{len(names)} sites', flush=True)
    D = pd.concat(days, ignore_index=True)
    D.to_parquet('data/rhpp_daily.parquet')
    S = pd.DataFrame(sites); S.to_parquet('data/rhpp_sites.parquet')
    print(f'wrote data/rhpp_daily.parquet ({len(D):,} site-days, {D.site.nunique()} sites) and data/rhpp_sites.parquet', flush=True)
    print(S.describe(include='all').to_string(), flush=True)


if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    main()
