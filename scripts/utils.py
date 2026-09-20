# -*- coding: utf-8 -*-
"""Shared helpers for ``paper_results.ipynb``.

Consolidates the paper-only helper scripts (``cross_fit``, ``hp_sf``,
``sf_transfer``, ``capacity_two_methods``, ``make_austin_arm_capacity``) plus the
notebook's figure/table display helpers into one module. The generator functions
live in ``outputs.py``; both import from here.

The curve-fitting primitives and figure styling stay in ``hp_common`` /
``hp_figures`` (the other notebooks import those directly) and are re-exported
below so the notebook has a single import surface.
"""
import os
import re
import pickle
from types import SimpleNamespace

import numpy as np
import pandas as pd

# --- re-exports: fitting primitives (defined in hp_common) -------------------
from hp_common import (                                         # noqa: F401
    hockey_stick, fit_hockey_stick, cooling_stick, fit_cooling_stick,
    bathtub_stick, fit_bathtub_stick, T_BALANCE_BOUNDS, T_COOLING_BOUNDS)
# --- re-exports: figure styling (defined in hp_figures) ----------------------
from hp_figures import (                                        # noqa: F401
    use_style, save, COL1, COL2, FIGDIR,
    C_HP, C_CH, C_DE, C_AC, C_NOHP, C_BASE)

import hp_design as hd


# ===========================================================================
# Cross-dataset fitter  (was cross_fit.py)
# ===========================================================================
def _sf_arm(T, sf, thr, side):
    """OLS SF arm anchored at ``thr``: heating below (side='h'), cooling above."""
    if not np.isfinite(thr):
        return (np.nan,) * 4
    m = (T < thr) if side == 'h' else (T > thr)
    if m.sum() < 10:
        return (np.nan,) * 4
    x = (thr - T[m]) if side == 'h' else (T[m] - thr)
    y = sf[m]
    if np.nanstd(y) == 0:
        return (np.nan,) * 4
    mm, bb = np.polyfit(x, y, 1)
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1 - np.sum((y - (bb + mm * x)) ** 2) / ss if ss > 0 else np.nan
    ext = (thr - T.min()) if side == 'h' else (T.max() - thr)
    return float(bb), float(mm), float(np.clip(bb + mm * ext, 0, 1)), float(r2)


def fit_row(label, n, T, net, heat, cool, cap_h, cap_c, frac_thr=0.05):
    """Fit the net-load curve and SF arms for one aggregated dataset row.

    Bathtub when both arms carry temperature-driven energy, otherwise a single
    hockey stick. SF arms are anchored at the net-load thresholds.
    """
    T = np.asarray(T, float); net = np.asarray(net, float)
    heat = np.asarray(heat, float) if heat is not None else np.zeros_like(T)
    cool = np.asarray(cool, float) if cool is not None else np.zeros_like(T)
    he, ce = float(np.nansum(heat)), float(np.nansum(cool))
    tot = he + ce
    hf = he / tot if tot > 0 else (1.0 if (cap_h and not cap_c) else 0.0)
    cf = ce / tot if tot > 0 else (1.0 if (cap_c and not cap_h) else 0.0)
    heat_present = bool(cap_h) and hf >= frac_thr
    cool_present = bool(cap_c) and cf >= frac_thr

    if heat_present and cool_present:
        base, sh, th, sc, tc, r2 = fit_bathtub_stick(T, net); mode = 'bathtub'
        if not np.isfinite(tc) or (tc - th) < 1.5:      # degenerate dead band -> dominant hockey stick
            if hf >= cf:
                base, sh, th, r2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
                sc = tc = np.nan; mode = 'heating hockey'; cool_present = False
            else:
                base, sc, tc, r2 = fit_cooling_stick(T, net, T_COOLING_BOUNDS)
                sh = th = np.nan; mode = 'cooling hockey'; heat_present = False
    elif heat_present:
        base, sh, th, r2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
        sc = tc = np.nan; mode = 'heating hockey'
    elif cool_present:
        base, sc, tc, r2 = fit_cooling_stick(T, net, T_COOLING_BOUNDS)
        sh = th = np.nan; mode = 'cooling hockey'
    else:
        base, sh, th, sc, tc, r2 = fit_bathtub_stick(T, net); mode = 'bathtub'

    bh = mh = sfcold = r2h = np.nan
    bc = mc = sfhot = r2c = np.nan
    if heat_present and cap_h:
        bh, mh, sfcold, r2h = _sf_arm(T, np.clip(heat / cap_h, 0, 1), th, 'h')
    if cool_present and cap_c:
        bc, mc, sfhot, r2c = _sf_arm(T, np.clip(cool / cap_c, 0, 1), tc, 'c')

    return dict(label=label, n=n, mode=mode, days=len(T),
                T_min=float(np.min(T)), T_max=float(np.max(T)),
                P_base=base, s_h=sh, T_h=th, s_c=sc, T_c=tc, R2=r2,
                b_h=bh, m_h=mh, SF_cold=sfcold, R2_SFh=r2h,
                b_c=bc, m_c=mc, SF_hot=sfhot, R2_SFc=r2c,
                cap_h=cap_h, cap_c=cap_c, heat_frac=hf, cool_frac=cf)


# ===========================================================================
# Per-substation hockey-stick fits of SF and net load  (was hp_sf.py)
# ===========================================================================
def daily_frame(design, sid):
    """Daily mean temperature, SF and net load for one substation."""
    temp = hd.get_series(design, sid, 'Temperature').resample('D').mean()
    load = hd.get_series(design, sid, 'Total_Load').resample('D').mean()
    hp_peak = design['meta'].loc[sid, 'HP_Peak']
    sf = None
    if hp_peak > 0:
        sf = (hd.get_series(design, sid, 'HP_Load') / hp_peak).resample('D').mean()
    d = pd.DataFrame({'T': temp, 'Load': load})
    if sf is not None:
        d['SF'] = sf
    return d.dropna(), float(hp_peak)


def fit_substation(design, sid, bounds=T_BALANCE_BOUNDS):
    """Fit both responses for one substation and project the critical temperature."""
    d, hp_peak = daily_frame(design, sid)
    if len(d) < 30 or hp_peak <= 0 or 'SF' not in d:
        return None
    m = design['meta'].loc[sid]
    T = d['T'].to_numpy()
    out = {'substation_id': int(sid), 'N_total': int(m['N_total']),
           'N_hp': int(m['N_hp']), 'hp_ratio': float(m['hp_ratio']),
           'HP_Peak': hp_peak, 'weather_id': m['weather_id'],
           'N_eheat': int(m.get('N_eheat_realised', 0)), 'T_min_obs': float(T.min())}
    for resp in ('SF', 'Load'):
        try:
            base, slope, t_thr, r2 = fit_hockey_stick(T, d[resp].to_numpy(), bounds)
        except Exception:
            continue
        out[f'{resp}_base'] = base
        out[f'{resp}_slope'] = slope
        out[f'{resp}_T_threshold'] = t_thr
        out[f'{resp}_r2'] = r2
        if slope > 0:
            gap = (1.0 - base) if resp == 'SF' else hp_peak
            out[f'{resp}_T_crit'] = t_thr - gap / slope
    return out


def fit_all(design, ids=None, verbose=True):
    ids = design['meta'].index if ids is None else ids
    rows = []
    for k, sid in enumerate(ids):
        r = fit_substation(design, int(sid))
        if r is not None:
            rows.append(r)
        if verbose and (k + 1) % 200 == 0:
            print(f'  {k + 1}/{len(ids)} fitted')
    df = pd.DataFrame(rows).set_index('substation_id')
    df['SF_max_modelled'] = df['SF_base'] + df['SF_slope'] * np.maximum(
        0.0, df['SF_T_threshold'] - df['T_min_obs'])
    return df


# ===========================================================================
# Simultaneity-factor transfer frames  (was sf_transfer.py)
# ===========================================================================
MIN_DAYS = 60


def build_frames(design):
    """Per-substation daily arrays for every substation with real HP submetering."""
    meta = design['meta']
    subs = []
    for sid in meta.index:
        fr, peak = daily_frame(design, int(sid))
        if peak <= 0 or 'SF' not in fr or len(fr) < MIN_DAYS:
            continue
        subs.append(dict(
            sid=int(sid), hp_ratio=float(meta.loc[sid, 'hp_ratio']),
            N_total=int(meta.loc[sid, 'N_total']), HP_Peak=float(peak),
            T=fr['T'].to_numpy(), SF=fr['SF'].to_numpy(),
            Load=fr['Load'].to_numpy()))
    return subs


def pooled_curve(subs):
    """Fit one hockey stick to the pooled daily (T, SF) points of a group."""
    T = np.concatenate([s['T'] for s in subs])
    SF = np.concatenate([s['SF'] for s in subs])
    base, slope, t_thr, r2 = fit_hockey_stick(T, SF, T_BALANCE_BOUNDS)
    return dict(base=base, slope=slope, t_thr=t_thr, r2=r2)


def predict(curve, T):
    return curve['base'] + curve['slope'] * np.maximum(0.0, curve['t_thr'] - T)


def r2_score(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float)
    ss = np.sum((y - y.mean()) ** 2)
    return 1 - np.sum((y - p) ** 2) / ss if ss > 0 else np.nan


def pickle_load(p):
    with open(p, 'rb') as fh:
        return pickle.load(fh)


# ===========================================================================
# Installed-capacity frame  (was capacity_two_methods.py)
# ===========================================================================
def fits_frame(design):
    df = fit_all(design, verbose=False).reset_index()
    d = pd.DataFrame({'sid': df['substation_id'], 'HP_Peak': df['HP_Peak'],
                      'hp_ratio': df['hp_ratio'], 'N_total': df['N_total'],
                      'slope': df['Load_slope']})
    span_L = np.maximum(0.0, df['Load_T_threshold'] - df['T_min_obs'])
    d['delta'] = df['Load_slope'] * span_L                     # net-load coincident peak proxy
    span_S = np.maximum(0.0, df['SF_T_threshold'] - df['T_min_obs'])
    d['SF_cold'] = (df['SF_base'] + df['SF_slope'] * span_S).clip(0, 1)
    d = d[(d.HP_Peak > 0) & (d.delta > 0)].dropna(subset=['delta', 'HP_Peak', 'SF_cold'])
    return d.reset_index(drop=True)


def metrics(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float); m = y > 0
    mape = np.mean(np.abs((y[m] - p[m]) / y[m])) * 100
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1 - np.sum((y - p) ** 2) / ss if ss > 0 else np.nan
    bias = (np.mean(p) - np.mean(y)) / np.mean(y) * 100
    return mape, r2, bias


# ===========================================================================
# Austin per-arm installed capacity  (was make_austin_arm_capacity.py)
# ===========================================================================
COOL = ['air1', 'air2', 'air3', 'airwindowunit1']
HEAT = ['furnace1', 'furnace2', 'heater1', 'heater2', 'heater3']
ETLCOLS = COOL + HEAT
_FLOOR = 0.05        # kW daily-mean: a device is "on" that day above this
_SHARE = 0.25        # active in an arm if on for at least this share of the arm's days
_MINPK = 0.1         # kW: ignore circuits whose peak never reaches this
_AUSTIN = None       # cache


def load_austin_arm_capacity(verbose=False):
    """Austin device list, activity flags, per-arm capacities and net-load
    thresholds. Cached: repeated calls reuse the first build.

    Returns a namespace with ``d, devices, base, s_h, T_h, s_c, T_c, Tds,
    capH, capC, capB``.
    """
    global _AUSTIN
    if _AUSTIN is not None:
        return _AUSTIN
    import pecan_street as ps
    from hp_capacity import robust_series_peak
    DATA = ps.DATA_DIR

    meta = pd.read_csv(f'{DATA}/metadata.csv', skiprows=[1])
    meta['dataid'] = pd.to_numeric(meta['dataid'], errors='coerce')
    meta = meta.dropna(subset=['dataid']); meta['dataid'] = meta.dataid.astype(int)
    cand = set(meta[(meta.city == 'Austin') & (meta.state == 'Texas')].dataid)

    all_cols = pd.read_csv(f'{DATA}/15minute_data_austin.csv', nrows=0).columns.tolist()
    cons_cols = [c for c in all_cols if c not in ps.NON_CONSUMPTION_COLS]
    chunks = []
    for ch in pd.read_csv(f'{DATA}/15minute_data_austin.csv', chunksize=500_000):
        chunks.append(ch[ch.dataid.isin(cand)])
    df = pd.concat(chunks, ignore_index=True)
    df['local_15min'] = pd.to_datetime(df['local_15min'], utc=True).dt.tz_convert('US/Central')
    df['total'] = df[cons_cols].sum(axis=1, min_count=1)
    df['meter_ref'] = df[['grid', 'solar', 'solar2']].sum(axis=1, min_count=1)
    T = ps.load_austin_temperature()

    net = None
    devices = []
    for hid, g in df.groupby('dataid'):
        gi = g.set_index('local_15min')
        tot = gi['total'].dropna()
        if len(tot) < 1000 or gi[cons_cols].max().max() > 30 or gi[['total', 'meter_ref']].corr().iloc[0, 1] < 0.9:
            continue
        nd = tot.resample('D').mean(); net = nd if net is None else net.add(nd, fill_value=0)
        for col in ETLCOLS:
            if col not in gi:
                continue
            s = gi[col].dropna()
            if len(s) < 1000:
                continue
            pk = robust_series_peak(s)
            if not np.isfinite(pk) or pk < _MINPK:
                continue
            devices.append(dict(hid=hid, col=col, peak=float(pk), daily=s.resample('D').mean()))

    d = pd.DataFrame({'T': T, 'net': net}).dropna()
    base, s_h, T_h, s_c, T_c, r2 = fit_bathtub_stick(d['T'].to_numpy(), d['net'].to_numpy())
    Tds = d.set_index(d.index)['T']
    heat_days = Tds.index[Tds < T_h]
    cool_days = Tds.index[Tds > T_c]
    band_days = Tds.index[(Tds >= T_h) & (Tds <= T_c)]

    def share_on(daily, days):
        x = daily.reindex(days).dropna()
        return float((x > _FLOOR).mean()) if len(x) else 0.0
    for dv in devices:
        dv['a_h'] = share_on(dv['daily'], heat_days) >= _SHARE
        dv['a_c'] = share_on(dv['daily'], cool_days) >= _SHARE
        dv['a_b'] = share_on(dv['daily'], band_days) >= _SHARE

    def cap(flag):
        return sum(dv['peak'] for dv in devices if dv[flag])
    capH, capC, capB = cap('a_h'), cap('a_c'), cap('a_b')
    if verbose:
        print(f'net-load bathtub: T_h {T_h:.1f} T_c {T_c:.1f} (R2 {r2:.3f}); '
              f'{len(devices)} ETL devices; Cap_H {capH:.0f} Cap_B {capB:.0f} Cap_C {capC:.0f} kW')

    _AUSTIN = SimpleNamespace(d=d, devices=devices, base=base, s_h=s_h, T_h=T_h,
                              s_c=s_c, T_c=T_c, r2=r2, Tds=Tds,
                              capH=capH, capC=capC, capB=capB)
    return _AUSTIN


# ===========================================================================
# Notebook display helpers
# ===========================================================================
_CLEAN = [
    (r'\\chg\{([^{}]*)\}', r'\1'), (r'\\mathrm\{([^{}]*)\}', r'\1'),
    (r'\\text\{([^{}]*)\}', r'\1'), (r'\\eqref\{[^{}]*\}', ''),
    (r'\\ref\{[^{}]*\}', ''), (r'\\,', ' '), (r'\\%', '%'),
    (r'\\\\', ''), (r'\^\{?\\circ\}?', '°'), (r'\$', ''),
    (r'\{|\}', ''), (r'~', ' '),
]


def _clean(s):
    for pat, rep in _CLEAN:
        s = re.sub(pat, rep, s)
    return s.strip()


def show_fig(name, width=560, caption=None):
    """Display a paper figure PNG (from FIGDIR) with an optional caption."""
    from IPython.display import Image, Markdown, display
    path = os.path.join(FIGDIR, name + '.png')
    if not os.path.exists(path):
        print('MISSING:', path); return
    display(Image(filename=path, width=width))
    if caption:
        display(Markdown(f'*{caption}*'))


def show_table(texname, tabdir=os.path.join('paper', 'tables'), caption=None):
    """Parse a booktabs LaTeX table into a DataFrame and render it."""
    from IPython.display import Markdown, display
    tex = open(os.path.join(tabdir, texname + '.tex'), encoding='utf-8').read()
    if caption is None:
        m = re.search(r'\\caption\{(.*?)\}\s*\n', tex, re.S)
        caption = _clean(m.group(1)) if m else texname
    body = re.search(r'\\toprule(.*?)\\bottomrule', tex, re.S).group(1)
    rows = []
    for line in body.split(r'\\'):
        line = line.strip()
        if 'rule' in line:
            line = re.sub(r'\\[a-z]*rule(\([^)]*\))?\{?[0-9-]*\}?', '', line).strip()
        if not line:
            continue
        cells = [_clean(c) for c in line.split('&')]
        if any(cells):
            rows.append(cells)
    if not rows:
        print(tex); return None
    hdr, *data = rows
    data = [r for r in data if len(r) == len(hdr)]
    df = pd.DataFrame(data, columns=hdr)
    display(Markdown(f'**{texname}** — {caption}'))
    display(df)
    return df
