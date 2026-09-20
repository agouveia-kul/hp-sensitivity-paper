"""Quality-check the registered installed HP capacity against submetered load.

The protocols record a nameplate electrical rating at the design ("Normpoint")
condition. The hypothesis tests use `HP_Peak` -- the measured peak of the
submetered heat-pump series -- as ground truth for installed capacity, so it
matters whether the two agree.
"""
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')
from heapo import HEAPO

OUT = 'data/capacity_check.csv'


def registered_table(h):
    p = h.get_all_protocols()
    hid = h.household_id
    q = p[p[hid].notna()].copy()
    num = ['HeatPump_Installation_HeatingCapacity',
           'HeatPump_Installation_Normpoint_ElectricPower',
           'HeatPump_Installation_Normpoint_COP',
           'HeatPump_Installation_Normpoint_HeatingPower']
    for c in num:
        q[c] = pd.to_numeric(q[c], errors='coerce')
    # a few households have two visits; keep the most recent
    g = q.sort_values('Visit_Year').groupby(hid).last()
    g = g.rename(columns={
        'HeatPump_Installation_HeatingCapacity': 'reg_thermal_kW',
        'HeatPump_Installation_Normpoint_ElectricPower': 'reg_electric_kW',
        'HeatPump_Installation_Normpoint_COP': 'reg_cop',
        'HeatPump_Installation_Normpoint_HeatingPower': 'reg_heating_kW',
        'HeatPump_Installation_Type': 'hp_type'})
    return g[['reg_thermal_kW', 'reg_electric_kW', 'reg_cop', 'reg_heating_kW',
              'hp_type']]


def measured_stats(h, household_id):
    """Statistics of the submetered HP series (kW) over all available data."""
    try:
        df = h.load_smart_meter_data(household_id, resolution='15min')
    except Exception:
        return None
    if df is None or not len(df):
        return None
    s = df['kWh_received_HeatPump'].dropna()
    if len(s) < 96 * 30:                      # need at least ~a month
        return None
    kw = (s * 4).to_numpy(dtype=float)        # kWh/15min -> kW
    ts = pd.to_datetime(df.loc[s.index, 'Timestamp'], utc=True)
    hourly = pd.Series(kw, index=ts).resample('h').mean()
    return {
        'n_samples': len(kw),
        'years': (ts.max() - ts.min()).days / 365.25,
        'meas_peak_kW': float(np.max(kw)),
        'meas_p999_kW': float(np.quantile(kw, 0.999)),
        'meas_p99_kW': float(np.quantile(kw, 0.99)),
        'meas_p95_kW': float(np.quantile(kw, 0.95)),
        'meas_peak_hourly_kW': float(hourly.max()),
        'meas_mean_kW': float(np.mean(kw)),
        'annual_kWh': float(np.sum(kw) / 4 / max((ts.max() - ts.min()).days / 365.25, 1e-9)),
    }


def main():
    h = HEAPO(data_path='data/heapo_data', use_local_time=False,
              suppress_warning=True)
    reg = registered_table(h)
    print(f'{len(reg)} households with a linked protocol', flush=True)

    rows = []
    for k, hid in enumerate(reg.index):
        st = measured_stats(h, hid)
        if st is None:
            continue
        rows.append({'Household_ID': hid, **st, **reg.loc[hid].to_dict()})
        if (k + 1) % 50 == 0:
            print(f'  {k + 1}/{len(reg)} processed', flush=True)

    df = pd.DataFrame(rows).set_index('Household_ID')
    # derived electrical rating from the thermal rating and COP
    df['reg_electric_from_thermal_kW'] = df['reg_thermal_kW'] / df['reg_cop']
    df.to_csv(OUT)
    print(f'saved {len(df)} rows -> {OUT}', flush=True)
    return df


if __name__ == '__main__':
    main()
