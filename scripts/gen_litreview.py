# -*- coding: utf-8 -*-
"""Literature-review table for the DER detection/quantification introduction.
Curated ~15 rows spanning PV, EV/multi-DER, service transformer and heat-pump
work across detection, disaggregation, installed-capacity, coincidence/peak and
flexibility. Filter columns by editing DEFAULT_COLS; every field is kept in ROWS
so any column can be switched in. Writes paper/tables/tab_litreview.tex."""

# Each row: all attributes are stored; pick which become table columns below.
ROWS = [
    # --- Photovoltaics ---
    dict(ref='Zha16b', year=2016, der='PV', task='Detection + capacity', quantity='kWp',
         cap='Y', method='ML', level='Meter', input='Smart meter',
         submeter='Y', registry='N', transfer='N', valid='Real', region='US utility',
         scale='$10^3$ meters', metric='--'),
    dict(ref='Li19d', year=2019, der='PV', task='Capacity + energy', quantity='kWp, kWh',
         cap='Y', method='ML', level='Meter', input='Smart meter',
         submeter='Y', registry='N', transfer='N', valid='Real', region='China',
         scale='$10^2$ sites', metric='MAPE'),
    dict(ref='Was21', year=2021, der='PV', task='Capacity', quantity='kWp',
         cap='Y', method='Probabilistic', level='Feeder', input='Aggr.\\ net load',
         submeter='N', registry='N', transfer='N', valid='Mixed', region='South Africa',
         scale='Feeders', metric='--'),
    dict(ref='Sos17', year=2017, der='PV', task='Disaggregation', quantity='kW',
         cap='N', method='Physics', level='Feeder', input='Power flow + GHI',
         submeter='N', registry='N', transfer='N', valid='Real', region='CH',
         scale='Feeder', metric='--'),
    dict(ref='gouveia2026pvcapacity', year=2026, der='PV', task='Installed capacity', quantity='kWp',
         cap='Y', method='ML / physics', level='Substation', input='Aggr.\\ net load + GHI',
         submeter='N', registry='N', transfer='Part', valid='Mixed', region='Synthetic + BE',
         scale='$10^3$ subst.', metric='MAPE'),
    # --- Service transformer ---
    dict(ref='Azz24', year=2024, der='Transformer', task='Nameplate capacity', quantity='kVA',
         cap='Y', method='ML (model-free)', level='Transformer', input='Smart meter',
         submeter='N', registry='N', transfer='N', valid='Real', region='US',
         scale='Transformers', metric='--'),
    # --- Multi-DER ---
    dict(ref='Jar22', year=2022, der='PV/EV/HP', task='Detection', quantity='Presence',
         cap='N', method='ML', level='Meter', input='Net-demand',
         submeter='Y', registry='N', transfer='N', valid='Real', region='UK/IE',
         scale='$10^2$ homes', metric='F1'),
    dict(ref='Bec24', year=2024, der='PV/EV/HP', task='Coincidence / impact', quantity='Peak',
         cap='N', method='Empirical', level='Feeder', input='Smart-meter profiles',
         submeter='N', registry='Y', transfer='N', valid='Real', region='BE (Fluvius)',
         scale='$10^3$ feeders', metric='--'),
    # --- Heat pumps / ETL ---
    dict(ref='Wei20b', year=2020, der='HP', task='Detection', quantity='Presence',
         cap='N', method='ML', level='Meter', input='Smart meter + weather',
         submeter='Y', registry='N', transfer='N', valid='Real', region='CH',
         scale='$10^3$ homes', metric='AUC'),
    dict(ref='Bru23', year=2023, der='HP', task='Disaggregation / energy', quantity='kWh',
         cap='N', method='ML (deep)', level='Meter', input='15-min smart meter',
         submeter='Y', registry='N', transfer='N', valid='Real', region='CH',
         scale='$10^2$ homes', metric='$R^2$'),
    dict(ref='Per17b', year=2017, der='HVAC', task='Change-point disaggregation', quantity='kWh',
         cap='N', method='Change-point', level='Meter', input='Smart meter + temp.',
         submeter='N', registry='N', transfer='N', valid='Real', region='US (Austin)',
         scale='$10^3$ homes', metric='--'),
    dict(ref='And20b', year=2020, der='HP', task='Transferable load profile', quantity='Profile',
         cap='N', method='Physics (thermal)', level='Feeder', input='Temp.\\ + housing',
         submeter='N', registry='Y', transfer='Y', valid='Synthetic', region='UK',
         scale='Networks', metric='--'),
    dict(ref='Lov17', year=2017, der='HP', task='Coincidence / ADMD', quantity='Peak (ADMD)',
         cap='N', method='Field study', level='Population', input='Submetered HP (2-min)',
         submeter='Y', registry='Y', transfer='N', valid='Real', region='UK (RHPP)',
         scale='$\\sim$700 HPs', metric='ADMD'),
    dict(ref='Mul19', year=2019, der='HP', task='Flexibility / DR', quantity='kW shift',
         cap='N', method='Field study', level='Population', input='Submetered HP',
         submeter='Y', registry='Y', transfer='N', valid='Real', region='CH',
         scale='$10^2$ HPs', metric='--'),
    # --- This work ---
    dict(ref='THIS', year=2026, der='HP / ETL', task='Capacity + energy + flexibility', quantity='kW, kWh',
         cap='Y', method='Physics', level='Feeder', input='Net load + temp.\\ + transferred SF',
         submeter='N', registry='N', transfer='Y', valid='Real + synth.', region='CH + DE',
         scale='$10^3$ subst.', metric='WAPE 7--10\\%'),
]

# All available columns (header, key). Comment out any you do not want.
DEFAULT_COLS = [
    ('Ref.', 'ref'),
    ('DER', 'der'),
    ('Task', 'task'),
    ('Level', 'level'),
    ('Method', 'method'),
    ('Input', 'input'),
    ('Cap.?', 'cap'),          # recovers installed capacity
    ('Submet.?', 'submeter'),  # needs submetering / labels
    ('Transf.?', 'transfer'),
]
# Other keys available to swap in: year, quantity, registry, valid, region, scale, metric


def cite(ref):
    return r'This work' if ref == 'THIS' else r'\cite{%s}' % ref


def build():
    cols = DEFAULT_COLS
    spec = 'l' * 1 + 'l' * (len(cols) - 1)
    head = ' & '.join(h for h, _ in cols) + r' \\'
    body = '\n'.join(
        ' & '.join(cite(r['ref']) if k == 'ref' else str(r[k]) for _, k in cols) + r' \\'
        for r in ROWS)
    tex = (
        r"\begin{table*}[t]" "\n" r"\centering" "\n"
        r"\caption{Representative work on detecting and quantifying distributed energy resources (DERs) from grid or meter measurements, and the gap this paper addresses. Cap.: recovers installed capacity. Submet.: needs submetered device data or labels. Transf.: a calibration transfers to un-submetered feeders. Level: individual meter, feeder/substation/transformer, or a submetered population.}" "\n"
        r"\label{tab:litreview}" "\n" r"\footnotesize\setlength{\tabcolsep}{4pt}" "\n"
        r"\begin{tabular}{" + spec + "}\n" r"\toprule" "\n"
        + head + "\n" r"\midrule" "\n" + body + "\n" r"\bottomrule" "\n"
        r"\end{tabular}" "\n" r"\end{table*}" "\n")
    open('paper/tables/tab_litreview.tex', 'w', encoding='utf-8').write(tex)
    print(tex)
    print('wrote paper/tables/tab_litreview.tex  (%d rows, %d columns)' % (len(ROWS), len(cols)))


if __name__ == '__main__':
    build()
