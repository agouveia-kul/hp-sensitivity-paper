"""Extract NEEA HEMS 2023 heating/cooling circuits from the raw 15-min power zip.

Streams ``data/POWER15_RAW_2023 v9.2.zip`` (one ~34 GB CSV) in chunks, keeps the
sites that have at least one ductless HP circuit (``POINTS v9.2.csv``) and only
the circuits needed for a complete heating/cooling ground truth, and writes
``data/neea_heating_circuits_2023.parquet``. ``--base`` keeps every heating-zone 1-2
site instead (base-load donors, ``data/neea_base_circuits_2023.parquet``).
"""
import os
import zipfile

import pandas as pd

ZIP = 'data/POWER15_RAW_2023 v9.2.zip'
OUT = 'data/neea_heating_circuits_2023.parquet'
KEEP = ['Mains', 'Mains With Solar', 'Ductless Heatpump', 'Ducted Heatpump',
        'Electric Baseboard Heaters', 'Electric Furnace', 'Other Zonal Heat',
        'Central AC', 'Room AC', 'Gas Furnace (Component)']


def main(sites=None, keep=KEEP, out_path=OUT):
    """``sites``: iterable of ee_site_id (default: every site with a ductless HP);
    ``keep``: End Use values to keep (None keeps every circuit)."""
    pts = pd.read_csv('data/POINTS v9.2.csv', low_memory=False)
    if sites is None:
        sites = set(pts.loc[pts['circuit_label_type_desc'] == 'Ductless Heatpump', 'ee_site_id'])
    sites = set(int(s) for s in sites)
    print(f'{len(sites)} sites', flush=True)
    parts = []
    with zipfile.ZipFile(ZIP) as z, z.open(z.namelist()[0]) as fh:
        reader = pd.read_csv(fh, usecols=['ee_site_id', 'regname', 'power', 'End Use', 'MIN_T_l', 'state'],
                             dtype={'ee_site_id': 'int64', 'regname': 'category', 'End Use': 'category',
                                    'state': 'category', 'power': 'float32'},
                             chunksize=5_000_000)
        for k, ch in enumerate(reader):
            ch = ch[ch['ee_site_id'].isin(sites)]
            if keep is not None:
                ch = ch[ch['End Use'].isin(keep)]
            if len(ch):
                ch = ch.assign(MIN_T_l=pd.to_datetime(ch['MIN_T_l']))
                parts.append(ch)
            if (k + 1) % 10 == 0:
                print(f'  {k + 1} chunks read, {sum(len(p) for p in parts):,} rows kept', flush=True)
    out = pd.concat(parts, ignore_index=True)
    for c in ('regname', 'End Use', 'state'):
        out[c] = out[c].astype(str).astype('category')
    out.to_parquet(out_path)
    print(f'wrote {out_path}: {len(out):,} rows, {out.ee_site_id.nunique()} sites', flush=True)
    print(out['End Use'].value_counts().to_string(), flush=True)


POWER_OUT = 'data/neea_power_2023.parquet'
TEMP_ZIP = 'data/TEMPERATURE15 v9.2.zip'
TEMP_OUT = 'data/neea_temp_2023.parquet'


def extract_power_temp():
    """Mains and ductless-HP power, and 2023 outdoor temperature, as compact parquets.

    Writes ``data/neea_power_2023.parquet`` (Mains, Mains With Solar, Ductless Heatpump
    circuits) and ``data/neea_temp_2023.parquet`` (outdoor-air sensors, 2023, plausible
    range -40..115 F). These feed the NEEA rows of Table I (``outputs.neea_fit``).
    """
    keep = {'Mains', 'Mains With Solar', 'Ductless Heatpump'}
    parts = []
    for ch in pd.read_csv(ZIP, compression='zip', usecols=['ee_site_id', 'End Use', 'power', 'MIN_T_l', 'state', 'cz'],
                          chunksize=3_000_000):
        parts.append(ch[ch['End Use'].isin(keep)])
    p = pd.concat(parts, ignore_index=True)
    p['MIN_T_l'] = pd.to_datetime(p['MIN_T_l'])
    p.to_parquet(POWER_OUT)
    print(f'wrote {POWER_OUT}: {len(p):,} rows, {p.ee_site_id.nunique()} sites', flush=True)

    tparts = []
    for ch in pd.read_csv(TEMP_ZIP, compression='zip', usecols=['ee_site_id', 'regname', 'temp', 'MIN_T_l'],
                          chunksize=2_000_000):
        oa = ch[ch['regname'].str.contains('oa_temp', case=False, na=False)].copy()
        oa['MIN_T_l'] = pd.to_datetime(oa['MIN_T_l'])
        tparts.append(oa[oa['MIN_T_l'].dt.year == 2023])
    t = pd.concat(tparts, ignore_index=True)
    t = t[(t.temp > -40) & (t.temp < 115)]
    t.to_parquet(TEMP_OUT)
    print(f'wrote {TEMP_OUT}: {len(t):,} rows, {t.ee_site_id.nunique()} sites', flush=True)


if __name__ == '__main__':
    import sys
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    if len(sys.argv) > 1 and sys.argv[1] == '--power-temp':
        extract_power_temp()
    elif len(sys.argv) > 1 and sys.argv[1] == '--all-circuits':
        # every circuit of the homes in the NEEA WA/OR aggregates (scratchpad/neea_full_aggs.pkl)
        import pickle
        A = pickle.load(open('scratchpad/neea_full_aggs.pkl', 'rb'))
        main(sites=A['WA']['sites'] + A['OR']['sites'], keep=None,
             out_path='data/neea_all_circuits_2023.parquet')
    elif len(sys.argv) > 1 and sys.argv[1] == '--base':
        # base-load donors for the BPA/NREL semi-synthetic test: every site in heating
        # zones 1-2, with the circuits needed to remove heating/cooling and to spot solar
        s = pd.read_csv('data/SITES v9.2.csv')
        main(sites=s.loc[s['hz'].isin([1, 2]), 'ee_site_id'],
             keep=KEEP + ['Solar', 'Other With Solar'],
             out_path='data/neea_base_circuits_2023.parquet')
    else:
        main()
