# -*- coding: utf-8 -*-
"""Diagnostic for the LCL survey column shift (UKDA SN 7857).

``survey_answers.csv`` column Qn holds the answers to the question that
``survey_questions.csv`` labels Q(n+1). This script (1) shows the evidence,
(2) writes and tests the corrected question-to-column mapping, and (3) reruns
the only Paper A computation that reads the survey (``rhpp_lcl_capacity``)
with the original and the corrected heater column, everything else identical.

Nothing under ``data/`` or ``paper/`` is touched; outputs go to
``results/lcl_survey_check/``.

    python scripts/lcl_survey_check.py evidence
    python scripts/lcl_survey_check.py impact
"""
import io
import os
import re
import sys
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = 'results/lcl_survey_check'
P = 'UKDA-7857-csv/csv/data_collection/data_tables/'


def load_survey(path='data/LCL_2013.zip'):
    with zipfile.ZipFile(path) as Z:
        q = pd.read_csv(io.BytesIO(Z.read(P + 'survey_questions.csv')), encoding='latin-1')
        a = pd.read_csv(io.BytesIO(Z.read(P + 'survey_answers.csv')), encoding='latin-1', low_memory=False)
    return q.set_index('Question_id')['Question'], a


def corrected_label(col, labels):
    """Question text that the answers in column ``col`` (e.g. 'Q304') belong to."""
    return labels.get(f'Q{int(col[1:]) + 1:02d}')


def corrected_column(qid):
    """Answer column holding the answers of question ``qid`` (e.g. 'Q304' -> 'Q303')."""
    return f'Q{int(qid[1:]) - 1:02d}'


# ---- documented answer sets (survey_appliance.pdf) ------------------------------------
YN = {'Yes', 'No', "Don't know", 'No reply'}
CH = {'No central heating', 'Gas', 'Electric (including storage heaters)', 'Oil',
      'Solid fuel (for example wood, coal)', 'Other central heating', "Don't know"}
CTRL = {"I switch the heating on manually at the boiler when needed",
        "I control the room temperature using the thermostatic valves on the radiators",
        "The heating switches on and off automatically at set times of the day",
        "The heating is controlled automatically by a thermostatic temperature control",
        "I'm not sure how it is controlled/used"}
WATER = {"Hot water storage tank with electric immersion heater",
         "Hot water storage tank with gas boiler - used for both central heating and hot water",
         "Hot water storage tank with gas boiler - used for hot water only",
         "Gas boiler (without hot water storage tank) - used for both central heating and hot water ('combi' boiler)",
         "Gas boiler (without hot water storage tank) - used for hot water only", "Another way", "Don't know"}
TVTYPE = {'Traditional/older style (CRT)', 'LED', 'LCD', 'Plasma', 'Other', "Don't know"}
TVSIZE = {'24 inches or less', '25 to 32 inches', '33 to 49 inches', '50 inches or more', "Don't know"}
POS = {'Kitchen', 'Hallway', 'Living Room', "I don't know where the display is"}
ACC = {'Detached', 'Semi-detached', 'Terraced - middle', 'Terraced - end',
       'In a purpose built block or tenement', 'Part of a converted house/building',
       'In a commercial building, (for example in an office building, hotel, or over a shop)',
       'A caravan or other mobile or temporary structure'}
WFH = {'Never', 'Occasionally', 'About half the time', 'Most/all weekdays'}
GENDER = {'Male', 'Female'}


def _ok(kind, s):
    """Fraction of non-null answers of Series ``s`` outside the documented set ``kind``."""
    s = s.dropna()
    if not len(s):
        return np.nan, 0
    if kind == 'count':
        n = pd.to_numeric(s, errors='coerce')
        bad = n.isna() | (n < 0) | (n != n.round())
    elif kind == 'multi':               # tick-all-that-apply: options joined by ';'
        bad = s.astype(str).map(lambda v: not all(t in ALLOWED_MULTI[0] for t in v.split(';')))
    else:
        bad = ~s.astype(str).isin(kind)
    return float(bad.mean()), int(len(s))


ALLOWED_MULTI = [None]

# form question -> (label regex, documented set); the label is the one in survey_questions.csv
CHECKS = [
    ('Q6 accommodation (house)', 'Accomodation: House', ACC),
    ('Q6 accommodation (caravan)', 'Accomodation: Mobile', ACC),
    ('Q7 rooms', 'Rooms in home', 'count'),
    ('Q9 insulation: double glazing', 'Insulation: Double glazing', YN),
    ('Q9 insulation: loft', 'Insulation: Roof or loft', YN),
    ('Q10 central heating fuel', 'Central heating$', 'multi:CH'),
    ('Q11 heating control', 'Central heating - control', 'multi:CTRL'),
    ('Q12 water heating', 'Heating water', WATER),
    ('Q15 No. portable electric heater', 'No. Portable electric heater', 'count'),
    ('Q15 No. television', 'No. Television', 'count'),
    ('Q16 TV 1 screen type', 'TV Type 1', TVTYPE),
    ('Q16 TV 1 screen size', 'TV Size 1', TVSIZE),
    ('Q17 display position', 'Position of smart meter', POS),
    ('Q1 member 1 gender', 'Household Member 1 Gender', GENDER),
]


def evidence():
    os.makedirs(OUT, exist_ok=True)
    lab, a = load_survey()
    rows = []
    for name, rx, kind in CHECKS:
        qid = next(k for k, v in lab.items() if re.search(rx, v))
        for tag, col in (('as labelled', qid), ('corrected (col-1)', corrected_column(qid))):
            if isinstance(kind, str) and kind.startswith('multi'):
                ALLOWED_MULTI[0] = CH if kind.endswith('CH') else CTRL
                bad, n = _ok('multi', a[col])
            else:
                bad, n = _ok(kind, a[col])
            s = a[col].dropna()
            rows.append(dict(question=name, label_id=qid, mapping=tag, column=col, n=n,
                             pct_outside_documented_set=round(100 * bad, 1),
                             top_values='; '.join(f'{k}:{v}' for k, v in s.astype(str).value_counts().head(4).items())[:110]))
    E = pd.DataFrame(rows)
    E.to_csv(f'{OUT}/evidence_answer_sets.csv', index=False)
    print(E[['question', 'mapping', 'column', 'n', 'pct_outside_documented_set', 'top_values']].to_string(index=False))

    # internal consistency: TV count k vs 'TV Type k' answered (form Q15 / Q16)
    tv = pd.to_numeric(a['Q304'], errors='coerce')            # corrected TV-count column (label Q305)
    tvl = pd.to_numeric(a['Q305'], errors='coerce')           # as-labelled TV column, actually desktop PCs
    cons = []
    for k in range(1, 7):
        typ = a[f'Q{314 + k}'].notna()                          # answers of labels Q316.. 'TV Type k' (col-1)
        for tag, cnt in (('corrected: TV count in Q304', tv), ('as labelled: TV count in Q305', tvl)):
            has = cnt >= k
            m = cnt.notna()
            cons.append(dict(k=k, mapping=tag, agree_pct=round(100 * (has[m] == typ[m]).mean(), 1)))
    C = pd.DataFrame(cons).pivot(index='k', columns='mapping', values='agree_pct')
    C.to_csv(f'{OUT}/evidence_tv_consistency.csv')
    print('\nTV count >= k  <=>  "TV Type k" answered (agreement %):'); print(C.to_string())

    # full corrected mapping
    M = pd.DataFrame({'answer_column': a.columns[1:]})
    M['survey_questions_label_as_labelled'] = M.answer_column.map(lab)
    M['question_actually_answered'] = M.answer_column.map(lambda c: corrected_label(c, lab))
    M.to_csv(f'{OUT}/corrected_mapping.csv', index=False)
    print(f'\nwrote corrected_mapping.csv ({len(M)} columns; Q344 has no label, label Q01 has no column)')
    heat = pd.to_numeric(a['Q303'], errors='coerce')
    print('\nheater count: Q304 as labelled', tv.value_counts().sort_index().head(4).to_dict(),
          '| Q303 corrected', heat.value_counts().sort_index().head(4).to_dict())


def _lcl_base_cols(heater_col, window=('2013-09-01', '2014-02-28'), tariffs=('n',), heating_col='Q248'):
    """Copy of ``outputs._lcl_base`` with the heater-count column as a parameter.

    Same gas-central-heating filter (heating_col, already the corrected column for
    the water/heating-system question), same window, same day and coverage rules.
    """
    a = load_survey()[1]
    sys_ = a[heating_col].astype(str)
    gas = sys_.str.contains('gas boiler', case=False) & sys_.str.contains('central heating', case=False)
    heaters = pd.to_numeric(a[heater_col], errors='coerce')
    sel = a.loc[gas & heaters.notna(), 'Household_id'].astype(str)
    htr = pd.Series(heaters[gas & heaters.notna()].to_numpy(), index=sel.to_numpy())
    parts = []
    with zipfile.ZipFile('data/LCL_2013.zip') as Z:
        for f in (f'consumption_{t}.csv' for t in tariffs):
            cols = [c for c in pd.read_csv(Z.open(P + f), nrows=0).columns if c in set(sel)]
            x = pd.read_csv(Z.open(P + f), usecols=['GMT'] + cols)
            x['GMT'] = pd.to_datetime(x['GMT'])
            x = x.set_index('GMT').loc[window[0]:window[1] + ' 23:59']
            day = x.resample('D').mean() * 2.0
            day = day.where(x.resample('D').count() >= 0.8 * 48)
            parts.append(day)
    D = pd.concat(parts, axis=1)
    D = D.loc[:, D.notna().mean() >= 0.8]
    return D, htr.reindex(D.columns)


def impact():
    import contextlib
    import pickle
    import outputs as O
    from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS
    os.makedirs(OUT, exist_ok=True)
    w = pd.date_range('2013-09-01', '2014-02-28')
    T = O._hadcet().reindex(w)
    res = {}
    for tag, col in (('original', 'Q304'), ('corrected', 'Q303')):
        # the pipeline itself: rhpp_lcl_capacity calls the module-level _lcl_base
        O._lcl_base = (lambda window=('2013-09-01', '2014-02-28'), tariffs=('n',), c=col:
                       _lcl_base_cols(c, window, tariffs))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            R = O.rhpp_lcl_capacity()
        pickle.dump(R, open(f'{OUT}/boxes_{tag}.pkl', 'wb'))
        open(f'{OUT}/log_{tag}.txt', 'w').write(buf.getvalue())
        print(f'--- {tag} ({col}) ---'); print(buf.getvalue())
        B, htr = _lcl_base_cols(col)
        B = B.reindex(w)
        sets = {'clean': list(htr.index[htr == 0]), 'heater-rich': list(htr.index[htr >= 2])}
        for name, hs in sets.items():
            m = pd.DataFrame({'T': T, 'y': B[hs].mean(axis=1)}).dropna()
            _, sl, th, _ = fit_hockey_stick(m['T'].to_numpy(), m['y'].to_numpy(), T_BALANCE_BOUNDS)
            r = dict(mapping=tag, split=name, households=len(hs), gas_households=len(htr),
                     slope_kW_per_C=sl, T_balance=th, mean_daily_kW=float(B[hs].mean().mean()))
            res[(tag, name)] = r
    rows = []
    for (tag, name), r in res.items():
        key = 'clean (0 portable heaters)' if name == 'clean' else 'heater-rich (>= 2 portable heaters)'
        Rt = pickle.load(open(f'{OUT}/boxes_{tag}.pkl', 'rb')).get(key)
        if Rt is not None:
            for kk in ('err', 'oracle', 'ratio', 'bias', 'energy'):
                r[f'{kk}_median'] = float(Rt[kk].median()); r[f'{kk}_q25'] = float(Rt[kk].quantile(.25))
                r[f'{kk}_q75'] = float(Rt[kk].quantile(.75))
            r['abs_err_median'] = float(Rt.err.abs().median()); r['splits'] = len(Rt); r['days'] = int(Rt.days.median())
        rows.append(r)
    S = pd.DataFrame(rows)
    S.to_csv(f'{OUT}/impact_summary.csv', index=False)
    print(S.T.to_string())
    # overlap of the household sets
    _, ho = _lcl_base_cols('Q304'); _, hc = _lcl_base_cols('Q303')
    print('old vs new clean overlap:', len(set(ho.index[ho == 0]) & set(hc.index[hc == 0])),
          'of', (ho == 0).sum(), '/', (hc == 0).sum(),
          '| heater-rich overlap:', len(set(ho.index[ho >= 2]) & set(hc.index[hc >= 2])),
          'of', (ho >= 2).sum(), '/', (hc >= 2).sum())
    # reproduction of the cached published-side pickle (read-only)
    C = pickle.load(open('data/_rhpp_lcl_boxes.pkl', 'rb'))
    for k in C:
        a_ = C[k].err.to_numpy(); b_ = pickle.load(open(f'{OUT}/boxes_original.pkl', 'rb'))[k].err.to_numpy()
        print('cache reproduces original run:', k, len(a_) == len(b_) and np.allclose(a_, b_))



if __name__ == '__main__':
    {'evidence': evidence, 'impact': impact}.get(sys.argv[1] if len(sys.argv) > 1 else 'evidence')()
