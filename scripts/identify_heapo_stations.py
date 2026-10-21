"""Identify HEAPO's anonymised weather stations with MeteoSwiss SwissMetNet stations.

HEAPO labels its stations with random IDs. Each HEAPO station is matched in two steps:
  1. altitude from its own pressure, QFE (station height) against QNH (sea level),
     which narrows the MeteoSwiss candidates to stations of similar barometer height;
  2. exact comparison of the hourly 2023 air temperature with MeteoSwiss ``tre200h0``.

Result (21 Oct 2026): every pair below is identical in all 8760 hours of 2023.
    8jB -> KLO  Zuerich / Kloten     (barometer 428 m)
    Hg  -> REH  Zuerich / Affoltern  (barometer 445 m)
    MqO -> EIN  Einsiedeln           (barometer 912 m)

MeteoSwiss open data (STAC collection ch.meteoschweiz.ogd-smn):
    https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv
    https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/<abbr>/ogd-smn_<abbr>_h_historical_2020-2029.csv

Usage: python scripts/identify_heapo_stations.py <dir with the MeteoSwiss csv files>
(files named meta_stations.csv and <abbr>_h.csv, e.g. reh_h.csv)
"""
import sys

import numpy as np
import pandas as pd

HEAPO = 'data/heapo_data/weather_data/hourly'
PAIRS = {'8jB': 'KLO', 'Hg': 'REH', 'MqO': 'EIN'}


def heapo_2023(st):
    d = pd.read_csv(f'{HEAPO}/{st}.csv', sep=';')
    d['t'] = pd.to_datetime(d.Timestamp, utc=True).dt.tz_convert(None)
    return d[d.t.dt.year == 2023].set_index('t')


def altitude(d):
    qfe = d['Pressure_BarometricHeight_avg_hourly']
    qnh = d['Pressure_SeaLevelStandardAtmosphere_avg_hourly']
    return float(np.nanmedian(44330.8 * (1 - (qfe / qnh) ** 0.190263)))


def main(msdir):
    meta = pd.read_csv(f'{msdir}/meta_stations.csv', sep=';', encoding='latin-1').set_index('station_abbr')
    for st, abbr in PAIRS.items():
        d = heapo_2023(st)
        m = pd.read_csv(f'{msdir}/{abbr.lower()}_h.csv', sep=';', usecols=['reference_timestamp', 'tre200h0'],
                        encoding='latin-1')
        m['t'] = pd.to_datetime(m.reference_timestamp, format='%d.%m.%Y %H:%M')
        j = pd.concat([d.Temperature_avg_hourly, m.set_index('t').tre200h0], axis=1, join='inner').dropna()
        diff = (j.iloc[:, 0] - j.iloc[:, 1]).abs()
        print(f"{st:4s} -> {abbr} {meta.loc[abbr, 'station_name']}: altitude from pressure {altitude(d):.0f} m "
              f"(barometer {meta.loc[abbr, 'station_height_barometer_masl']:.0f} m); "
              f"{len(j)} hours, max |dT| = {diff.max():.4f} C")


if __name__ == '__main__':
    main(sys.argv[1])
