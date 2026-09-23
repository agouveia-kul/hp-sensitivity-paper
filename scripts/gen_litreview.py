# -*- coding: utf-8 -*-
"""Literature-review table for the introduction.

Rows are grouped by the lines of research the introduction reviews: HP and DER
detection/disaggregation, temperature-response (change-point) models, PV and
transformer capacity, and HP coincidence, profiles and flexibility. Every field is
kept in ROWS so any column can be switched in via DEFAULT_COLS.
Writes paper/tables/tab_litreview.tex.
"""

G_DET = 'Detection and disaggregation'
G_TRF = 'Temperature-response models'
G_CAP = 'PV and transformer capacity'
G_COI = 'HP coincidence, profiles and flexibility'

# cap: recovers installed capacity; submeter: needs submetered device data or labels
# at the target; transfer: a calibration carries to un-submetered aggregates
ROWS = [
    # --- detection / disaggregation ---
    dict(group=G_DET, ref='Fei13', der='HP', task='Detection', level='Meter', method='ML (PU learning)',
         input='Smart meter', cap='N', submeter='Y', transfer='N'),
    dict(group=G_DET, ref='Wei20b', der='HP', task='Detection', level='Meter', method='ML',
         input='Smart meter + weather', cap='N', submeter='Y', transfer='N'),
    dict(group=G_DET, ref='Bru23', der='HP', task='Disaggregation', level='Meter', method='ML (deep)',
         input='15-min smart meter', cap='N', submeter='Y', transfer='N'),
    dict(group=G_DET, ref='Gis26', der='HP', task='Detection + disaggregation', level='Meter', method='ML (CNN)',
         input='Smart meter', cap='N', submeter='Y', transfer='N'),
    dict(group=G_DET, ref='Jar22', der='PV/EV/HP', task='Detection', level='Meter', method='ML',
         input='Net demand', cap='N', submeter='Y', transfer='N'),
    dict(group=G_DET, ref='Wan20', der='Loads/DER', task='Regional NILM', level='Substation', method='NILM',
         input='Substation load', cap='N', submeter='Y', transfer='N'),
    dict(group=G_DET, ref='Oma24', der='Loads', task='Disaggregation', level='Substation', method='ML (deep)',
         input='Substation load', cap='N', submeter='Y', transfer='N'),
    # --- temperature-response models ---
    dict(group=G_TRF, ref='Ali11', der='Cooling', task='Change-point model', level='Community', method='Change-point',
         input='Aggr.\\ load + temp.', cap='N', submeter='N', transfer='N'),
    dict(group=G_TRF, ref='Per17b', der='HVAC', task='Change-point model', level='Meter', method='Change-point',
         input='Smart meter + temp.', cap='N', submeter='N', transfer='N'),
    dict(group=G_TRF, ref='Mac19', der='Sector load', task='Weather effects', level='System', method='Regression',
         input='Sector load + weather', cap='N', submeter='N', transfer='N'),
    # --- PV and transformer capacity ---
    dict(group=G_CAP, ref='Zha16b', der='PV', task='Detection + capacity', level='Meter', method='ML',
         input='Smart meter', cap='Y', submeter='Y', transfer='N'),
    dict(group=G_CAP, ref='Li19d', der='PV', task='Capacity + energy', level='Meter', method='ML',
         input='Smart meter', cap='Y', submeter='Y', transfer='N'),
    dict(group=G_CAP, ref='Sos17', der='PV', task='Disaggregation', level='Feeder', method='Physics',
         input='Power flow + GHI', cap='N', submeter='N', transfer='N'),
    dict(group=G_CAP, ref='Was21', der='PV', task='Capacity', level='Feeder', method='Probabilistic',
         input='Aggr.\\ net load', cap='Y', submeter='N', transfer='N'),
    dict(group=G_CAP, ref='gouveia2026pvcapacity', der='PV', task='Capacity', level='Substation', method='ML / model-based',
         input='Aggr.\\ net load + GHI', cap='Y', submeter='N', transfer='Y'),
    dict(group=G_CAP, ref='Azz24', der='Transformer', task='Nameplate rating', level='Transformer', method='Model-free',
         input='Smart meter', cap='Y', submeter='N', transfer='N'),
    # --- HP coincidence, profiles and flexibility ---
    dict(group=G_COI, ref='Bec24', der='PV/EV/HP', task='Coincidence / impact', level='Feeder', method='Empirical',
         input='Smart-meter profiles', cap='N', submeter='N', transfer='N'),
    dict(group=G_COI, ref='Lov17', der='HP', task='Coincidence / ADMD', level='Population', method='Field study',
         input='Submetered HP', cap='N', submeter='Y', transfer='N'),
    dict(group=G_COI, ref='Che21b', der='HP', task='Peak in cold weather', level='Population', method='Field study',
         input='Submetered HP', cap='N', submeter='Y', transfer='N'),
    dict(group=G_COI, ref='And20b', der='HP', task='Load profiles', level='Feeder', method='Physics (thermal)',
         input='Temp.\\ + housing', cap='N', submeter='N', transfer='Y'),
    dict(group=G_COI, ref='Mul19', der='HP', task='Flexibility / DR', level='Population', method='Field study',
         input='Submetered HP', cap='N', submeter='Y', transfer='N'),
    # --- this work ---
    dict(group=None, ref='THIS', der='HP / ETL', task='Capacity, energy, flexibility', level='Feeder', method='Change-point + SF',
         input='Net load + temp.\\ + pilot SF', cap='Y', submeter='N', transfer='Y'),
]

DEFAULT_COLS = [
    ('Reference', 'ref'),
    ('DER', 'der'),
    ('Task', 'task'),
    ('Level', 'level'),
    ('Method', 'method'),
    ('Input', 'input'),
    (r'Installed\\capacity', 'cap'),       # recovers installed capacity
    (r'Submetering\\needed', 'submeter'),  # needs submetered device data or labels at the target
    ('Transferable', 'transfer'),           # a calibration carries to un-submetered aggregates
]
FLAGS = ('cap', 'submeter', 'transfer')   # shown as marks: Y -> check, Part -> (check), N -> blank
MARK = {'Y': r'\checkmark', 'Part': r'(\checkmark)', 'N': ''}

KEY = (r"\par\smallskip{\footnotesize Installed capacity: recovers the installed capacity. Submetering needed: "
       r"needs submetered device data or labels. Transferable: a calibration transfers to un-submetered aggregates. "
       r"Level: individual meter, feeder, substation or transformer, or a submetered population.}")


def cite(ref):
    return r'This work' if ref == 'THIS' else r'\cite{%s}' % ref


def build():
    cols = DEFAULT_COLS
    spec = ''.join('c' if k in FLAGS else 'l' for _, k in cols)

    def hdr(h, k):
        if '\\\\' not in h:
            return h
        return r'\begin{tabular}[b]{@{}%s@{}}%s\end{tabular}' % ('c' if k in FLAGS else 'l', h)
    head = ' & '.join(hdr(h, k) for h, k in cols) + r' \\'

    def cell(r, k):
        if k == 'ref':
            return cite(r['ref'])
        return MARK[r[k]] if k in FLAGS else str(r[k])
    lines, group = [], 'start'
    for r in ROWS:
        if r['group'] != group:
            if group != 'start':
                lines.append(r'\midrule')
            if r['group'] is not None:
                lines.append(r'\multicolumn{%d}{l}{\textit{%s}} \\' % (len(cols), r['group']))
            group = r['group']
        lines.append(' & '.join(cell(r, k) for _, k in cols) + r' \\')
    tex = (
        r"\begin{table*}[t]" "\n" r"\centering" "\n"
        r"\caption{Prior work on detecting and quantifying DERs}" "\n"
        r"\label{tab:litreview}" "\n" r"\footnotesize\setlength{\tabcolsep}{2.7pt}" "\n"
        r"\begin{tabular}{" + spec + "}\n" r"\toprule" "\n"
        + head + "\n" r"\midrule" "\n" + '\n'.join(lines) + "\n" r"\bottomrule" "\n"
        r"\end{tabular}" "\n"
        + KEY + "\n" r"\end{table*}" "\n")
    open('paper/tables/tab_litreview.tex', 'w', encoding='utf-8', newline='\n').write(tex)
    print('wrote paper/tables/tab_litreview.tex  (%d rows, %d columns)' % (len(ROWS), len(cols)))


if __name__ == '__main__':
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    build()
