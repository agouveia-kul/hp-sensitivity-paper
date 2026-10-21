# -*- coding: utf-8 -*-
"""Planning use case for the capacity estimate (experiments, not in the paper yet).

One function per step of the planning experiments, called from
``planning_use_case.ipynb``. Intermediate results are pickled under ``PLAN_WORK``
(gitignored ``results/planning``); figures go to ``PLAN_FIG`` as PDF and PNG.
The paper's own caches in ``data/`` and artifacts in ``paper/`` are never written.

Step 0 rebuilds the published 20-split Kloten design from the cached pools with
the generators of ``outputs`` and checks the draft's numbers against tolerances.
"""
import os
import pickle

import numpy as np
import pandas as pd

import hp_figures as hf
import outputs as O
import utils as U
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

PLAN_WORK = os.path.join('results', 'planning')     # pickles (gitignored)
PLAN_FIG = os.path.join('figures', 'planning')      # PDF + PNG of every figure

PEN_BINS = [0, .15, .35, .65, 1.0]                  # Table IV penetration bins N_hp / N


def _pkl(name):
    os.makedirs(PLAN_WORK, exist_ok=True)
    return os.path.join(PLAN_WORK, name + '.pkl')


def _cached(name, build, rebuild=False):
    """Load ``name`` from PLAN_WORK, or build and save it."""
    path = _pkl(name)
    if os.path.exists(path) and not rebuild:
        with open(path, 'rb') as fh:
            return pickle.load(fh)
    out = build()
    with open(path, 'wb') as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def save_fig(fig, name):
    os.makedirs(PLAN_FIG, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(PLAN_FIG, f'{name}.{ext}'), dpi=300)
    return os.path.join(PLAN_FIG, name)


def wape_by_bin(G, est, act='cap'):
    """WAPE overall and per penetration bin of Table IV."""
    bins = pd.cut(G.N_hp / G.N, PEN_BINS)
    return [O._wape(G[est], G[act])] + [O._wape(g[est], g[act]) for _, g in G.groupby(bins, observed=True)]


# ===========================================================================
# Step 0 -- reproduce the baseline
# ===========================================================================
TARGETS = {  # draft value, tolerance
    'wape_i': (19.3, .5), 'wape_i_le15': (57.5, .5), 'wape_i_15_35': (26.3, .5),
    'wape_i_35_65': (17.0, .5), 'wape_i_gt65': (14.2, .5),
    'wape_ii': (14.5, .5), 'wape_iv': (21.1, .5),
    'median_over_pct': (16.0, .5), 'mae_kw': (17.0, .5), 'mean_hp_kw': (6.3, .05),
    'fig8_slope': (0.0202, .0005), 'fig8_r': (0.97, .005),
    'pilot_m_median': (0.018, .0005), 'pilot_m_q25': (0.017, .0005), 'pilot_m_q75': (0.019, .0005),
    'zero_hp_kw_per_hh': (0.28, .005),
    'sf15_peak_coldest': (0.56, .005), 'sf15_peak_year': (0.59, .005), 'p2m_coldest': (1.28, .005),
    'real_Hg': (2.0, 1.0), 'real_MqO': (-6.0, 1.0), 'real_Hamelin': (-9.0, 1.0),
}


def rebuild_kloten_design(rebuild=False):
    """The published 1260-aggregate design, rebuilt from the pools into PLAN_WORK.

    Runs ``outputs._kloten_design`` (seed 0, 20 splits, 3 reps, target aggregates
    drawn from all 1307 HP-free households) with its cache path redirected, so the
    paper's ``data/_kloten_design.pkl`` is read only for comparison.
    """
    path = _pkl('step0_kloten_design')
    old = O.KLOTEN_DESIGN
    O.KLOTEN_DESIGN = path
    try:
        return O._kloten_design(rebuild=rebuild or not os.path.exists(path))
    finally:
        O.KLOTEN_DESIGN = old


def _zero_hp_control(n_reps=50, seed=0):
    """Part (2) of ``outputs.sf_controls``: spurious capacity per HP-free household.

    ``sf_controls`` draws part (1) first from the same generator, so the full
    function is run and only its zero-HP frame kept.
    """
    _, Z = O.sf_controls(n_splits=120, n_reps=n_reps, seed=seed)
    return Z


def _sf15_kloten():
    """15-min SF of the 50 Kloten HPs: peak on the coldest day, over the year, and
    the coldest day's 15-min peak over its daily mean."""
    import hp_pools as hpp
    from hp_capacity import robust_series_peak
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']
    hrows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == 'KLO']
    cap = sum(robust_series_peak(p['hp_mat'][i]) for i in hrows)
    sf = pd.Series(p['hp_mat'][hrows].sum(0) / cap, index=p['index'])
    Td = pd.Series(p['temperature']['KLO'], index=p['index']).resample('D').mean()
    day = Td.idxmin()
    on = sf[sf.index.normalize() == day]
    dmax = sf.resample('D').max(); dmean = sf.resample('D').mean()
    heat = Td < 16.55                                   # median heating day: below the pilot T_h
    return dict(n_hp=len(hrows), coldest_day=str(day.date()), T_coldest=float(Td.min()),
                sf15_peak_coldest=float(on.max()), sf15_peak_year=float(sf.max()),
                p2m_coldest=float(on.max() / on.mean()),
                p2m_median_heating=float((dmax[heat] / dmean[heat]).median()))


def reproduce_baseline(rebuild=False):
    """Step 0: every draft number of the prompt's section 1, against its tolerance.

    Returns (checks, extras): a frame with draft value, reproduced value, tolerance
    and pass flag, and a dict of the underlying objects.
    """
    Dz = rebuild_kloten_design(rebuild)
    G = Dz['rows'].copy(); Tmin = float(Dz['T'].min())
    with open(O.KLOTEN_DESIGN, 'rb') as fh:                         # the paper's cache
        G_paper = pickle.load(fh)['rows']
    same = (len(G) == len(G_paper)
            and np.allclose(G[['cap', 's_h', 'T_h', 'cap_est', 'cap_or']].to_numpy(),
                            G_paper[['cap', 's_h', 'T_h', 'cap_est', 'cap_or']].to_numpy()))

    G['cap_plan'] = G.s_h * (G.T_h - Tmin) / O.SF_PLAN
    wi, wii, wiv = wape_by_bin(G, 'cap_est'), wape_by_bin(G, 'cap_or'), wape_by_bin(G, 'cap_plan')
    x, y = G.cap.to_numpy(), G.s_h.to_numpy()
    pm = pd.Series([p['m'] for p in Dz['pilots']])
    K = Dz['K']

    Z = _cached('step0_zero_hp', _zero_hp_control, rebuild)
    sf15 = _cached('step0_sf15', _sf15_kloten, rebuild)
    R = _cached('step0_tab_real', _tab_real_quiet, rebuild)
    real = dict(zip(R['agg'], R['err']))

    got = {'wape_i': wi[0], 'wape_i_le15': wi[1], 'wape_i_15_35': wi[2], 'wape_i_35_65': wi[3],
           'wape_i_gt65': wi[4], 'wape_ii': wii[0], 'wape_iv': wiv[0],
           'median_over_pct': (np.median(G.cap_est / G.cap) - 1) * 100,
           'mae_kw': float(np.mean(np.abs(G.cap_est - G.cap))), 'mean_hp_kw': float(K['cap'].mean()),
           'fig8_slope': float(np.sum(x * y) / np.sum(x * x)), 'fig8_r': float(np.corrcoef(x, y)[0, 1]),
           'pilot_m_median': pm.median(), 'pilot_m_q25': pm.quantile(.25), 'pilot_m_q75': pm.quantile(.75),
           'zero_hp_kw_per_hh': float(Z.per_house.median()),
           'sf15_peak_coldest': sf15['sf15_peak_coldest'], 'sf15_peak_year': sf15['sf15_peak_year'],
           'p2m_coldest': sf15['p2m_coldest'],
           'real_Hg': real['Affoltern, CH'], 'real_MqO': real['Einsiedeln, CH'], 'real_Hamelin': real['Hamelin, DE']}
    rows = []
    for k, (target, tol) in TARGETS.items():
        v = got[k]
        # the draft rounds: a value matches when it rounds to the draft figure, or lies within tol
        rows.append(dict(quantity=k, draft=target, reproduced=v, tol=tol, ok=abs(v - target) <= tol))
    checks = pd.DataFrame(rows)
    extras = dict(G=G, pilots=Dz['pilots'], Z=Z, sf15=sf15, real=R, same_as_paper_cache=same,
                  wape=dict(i=wi, ii=wii, iv=wiv), n_free=int(K['free'].shape[0]), n_hp=int(len(K['cap'])))
    return checks, extras


def _tab_real_quiet():
    """``outputs.tab_real`` with its .tex redirected to PLAN_WORK (the frame is what is kept)."""
    old = O.TABDIR
    O.TABDIR = PLAN_WORK
    try:
        return O.tab_real()
    finally:
        O.TABDIR = old


# ===========================================================================
# Step 1 -- inventory of the data
# ===========================================================================
SWISS_META = os.path.join('data', 'Swiss_dataset', 'metadata.csv')
SWISS_METERS = os.path.join('data', 'Swiss_dataset', 'smart_meter_data')
HEAPO_HH = os.path.join('data', 'heapo_data', 'meta_data', 'households.csv')
HEAPO_COVER = os.path.join('data', '_heapo_daily_coverage.parquet')
HEAPO_PROTOCOLS = os.path.join('data', 'heapo_data', 'reports', 'protocols.csv')
LOCAL_TZ = 'Europe/Zurich'

# Heating windows scored for completeness. Nov-Mar winters, plus the heating months of
# a calendar year (Jan-Mar and Nov-Dec), which is how the paper's 2023 enters the fits.
WINTERS = {
    'W2019/20': ('2019-11-01', '2020-03-31'), 'W2020/21': ('2020-11-01', '2021-03-31'),
    'W2021/22': ('2021-11-01', '2022-03-31'), 'W2022/23': ('2022-11-01', '2023-03-31'),
    'W2023/24': ('2023-11-01', '2024-03-31'), 'W2024/25': ('2024-11-01', '2025-03-31'),
}
CAL_HEAT = {'cal2023 heat': ('2023', (1, 2, 3, 11, 12)), 'cal2024 heat': ('2024', (1, 2, 3, 11, 12))}


def kloten_members():
    """The Kloten pool split by source and role: HP households (with the Swiss HP
    meter paired to each Swiss dwelling) and the 1307 households without an HP."""
    import hp_pools as hpp
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']; eheat = set(p['eheat_households']); hp_set = set(p['hp_households'])
    hp = [h for h in p['hp_households'] if w.get(h) == 'KLO']
    free = [h for h in p['households'] if w.get(h) == 'KLO' and h not in hp_set and h not in eheat]
    meta = pd.read_csv(SWISS_META, sep=';', encoding='utf-8-sig')
    obj = meta.set_index('0_meter_id')['0_object_id']
    hpm = meta[meta['0_installation_type'] == 'Heat pump'].groupby('0_object_id')['0_meter_id'].first()
    pair = {h: int(hpm[obj[int(str(h).split(':')[1])]]) for h in hp if str(h).startswith('swiss:')}
    return dict(pool=p, hp=hp, free=free, swiss_hp_meter=pair)


def _swiss_coverage(meter_id):
    """Share of 15-min intervals present per window, for one raw Swiss meter file."""
    f = os.path.join(SWISS_METERS, f'{meter_id}.csv')
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f, sep=';', usecols=['timestamp_utc', 'kWh_to_installation', 'kWh_to_grid'])
    ts = pd.to_datetime(d['timestamp_utc'], utc=True)
    ok = pd.to_numeric(d['kWh_to_installation'], errors='coerce').notna().to_numpy()
    s = pd.Series(ok, index=ts.dt.tz_convert(LOCAL_TZ))
    s = s[~s.index.duplicated()]
    out = {}
    for k, (a, b) in WINTERS.items():
        n = len(pd.date_range(a, pd.Timestamp(b) + pd.Timedelta('23:45:00'), freq='15min', tz=LOCAL_TZ))
        out[k] = s.loc[a:f'{b} 23:59'].sum() / n
    for k, (yr, months) in CAL_HEAT.items():
        idx = pd.date_range(f'{yr}-01-01', f'{yr}-12-31 23:45', freq='15min', tz=LOCAL_TZ)
        idx = idx[idx.month.isin(months)]
        out[k] = s.reindex(idx).fillna(False).sum() / len(idx)
    exp = pd.to_numeric(d['kWh_to_grid'], errors='coerce')
    out['kWh_to_grid_total'] = float(exp.sum())
    return out


def inventory_years(rebuild=False):
    """1.1: completeness (share of 15-min intervals present) per winter, Kloten members.

    Swiss members are scored on their raw files (HP households on BOTH the dwelling and
    the paired HP meter). HEAPO members are scored on ``_heapo_daily_coverage.parquet``,
    the daily interval counts kept from the earlier HEAPO download (raw files absent).
    """
    def build():
        M = kloten_members(); rows = []
        for role, hh in (('hp', M['hp']), ('free', M['free'])):
            for h in hh:
                src, hid = str(h).split(':')
                if src != 'swiss':
                    continue
                cov = _swiss_coverage(int(hid))
                if role == 'hp':
                    c2 = _swiss_coverage(M['swiss_hp_meter'][h])
                    cov = {k: min(cov[k], c2[k]) for k in cov if k != 'kWh_to_grid_total'} | \
                          {'kWh_to_grid_total': cov['kWh_to_grid_total']}
                rows.append(dict(household=h, source=src, role=role, **cov))
        C = pd.read_parquet(HEAPO_COVER)
        C.index = pd.to_datetime(C.index).tz_convert(LOCAL_TZ).normalize()
        for role, hh in (('hp', M['hp']), ('free', M['free'])):
            for h in hh:
                src, hid = str(h).split(':')
                if src != 'heapo':
                    continue
                col = int(hid) if int(hid) in C.columns else (hid if hid in C.columns else None)
                r = dict(household=h, source=src, role=role, in_cover_file=col is not None)
                for k, (a, b) in WINTERS.items():
                    days = pd.date_range(a, b, freq='D', tz=LOCAL_TZ)
                    r[k] = (C[col].reindex(days).fillna(0).sum() / (96 * len(days))) if col is not None else np.nan
                for k, (yr, months) in CAL_HEAT.items():
                    days = pd.date_range(f'{yr}-01-01', f'{yr}-12-31', freq='D', tz=LOCAL_TZ)
                    days = days[days.month.isin(months)]
                    r[k] = (C[col].reindex(days).fillna(0).sum() / (96 * len(days))) if col is not None else np.nan
                rows.append(r)
        return pd.DataFrame(rows)
    return _cached('step1_years', build, rebuild)


def inventory_pv(Y=None):
    """1.2: PV flags of the Kloten members, by source and role.

    HEAPO: ``Installation_HasPVSystem`` (households.csv). Swiss: ``0_max_net_injection``
    (set by the dataset for meters that export) and the exported energy of the raw file
    (``kWh_to_grid``, from the 1.1 scan). Both pools keep only the imported energy
    (HEAPO ``kWh_received_*``, Swiss ``kWh_to_installation``), so a PV household enters
    the aggregates with its grid import, export discarded.
    """
    M = kloten_members(); Y = inventory_years() if Y is None else Y
    hh = pd.read_csv(HEAPO_HH, sep=';').set_index('Household_ID')['Installation_HasPVSystem']
    meta = pd.read_csv(SWISS_META, sep=';', encoding='utf-8-sig').set_index('0_meter_id')
    exp = Y.set_index('household')['kWh_to_grid_total']
    rows = []
    for role, members in (('hp', M['hp']), ('free', M['free'])):
        for h in members:
            src, hid = str(h).split(':'); hid = int(hid)
            if src == 'heapo':
                rows.append(dict(household=h, source=src, role=role, pv_flag=bool(hh.get(hid, False)),
                                 max_inj=np.nan, kwh_export=np.nan))
            else:
                mi = meta['0_max_net_injection'].get(hid, np.nan)
                rows.append(dict(household=h, source=src, role=role, pv_flag=bool(np.isfinite(mi)),
                                 max_inj=mi, kwh_export=exp.get(h, np.nan)))
    return pd.DataFrame(rows)


def blocking_profile(cold_T=0.0, off_frac=0.05):
    """1.3: share of the 50 Kloten HPs at near-zero load against local time of day.

    Near zero: below ``off_frac`` of the HP's robust peak. Cold days: daily mean below
    ``cold_T``. Returns per-slot shares (cold weekdays, cold weekends, mild heating days),
    the per-HP probability of being off per slot on cold weekdays, and the HP ids.
    """
    from hp_capacity import robust_series_peak
    M = kloten_members(); p = M['pool']
    rows = [p['hp_households'].index(h) for h in M['hp']]
    cap = np.array([robust_series_peak(p['hp_mat'][i]) for i in rows])
    idx = p['index'].tz_convert(LOCAL_TZ)
    X = pd.DataFrame(p['hp_mat'][rows].T / cap, index=idx)
    Td = pd.Series(p['temperature']['KLO'], index=idx).resample('D').mean()
    day = X.index.normalize()
    cold = day.isin(Td.index[Td < cold_T]); mild = day.isin(Td.index[(Td >= 5) & (Td < 12)])
    wkd = X.index.dayofweek < 5
    slot = X.index.hour * 4 + X.index.minute // 15
    off = (X < off_frac)

    def share(mask):
        return off[mask].mean(1).groupby(slot[mask]).mean()

    def sf(mask):
        return (X[mask] * cap).sum(1).groupby(slot[mask]).mean() / cap.sum()
    prof = pd.DataFrame({'cold_wkd': share(cold & wkd), 'cold_wke': share(cold & ~wkd),
                         'mild_wkd': share(mild & wkd),
                         'sf_cold_wkd': sf(cold & wkd), 'sf_cold_wke': sf(cold & ~wkd)})
    per_hp = off[cold & wkd].groupby(slot[cold & wkd]).mean()          # slots x HPs
    per_hp.columns = M['hp']
    return dict(profile=prof, per_hp=per_hp, cap=cap, n_cold=int((Td < cold_T).sum()),
                n_cold_wkd=int(((Td < cold_T) & (Td.index.dayofweek < 5)).sum()), ids=M['hp'])


def blocked_windows(per_hp, p_off=0.8, min_slots=2):
    """Per HP, the clock windows (runs of >= min_slots 15-min slots) in which it is off
    on at least ``p_off`` of the cold weekdays: the signature of a recurring block."""
    out = {}
    for h in per_hp.columns:
        s = (per_hp[h] >= p_off).to_numpy(); runs, k = [], 0
        while k < len(s):
            if s[k]:
                j = k
                while j < len(s) and s[j]:
                    j += 1
                if j - k >= min_slots:
                    runs.append((k, j))
                k = j
            else:
                k += 1
        out[h] = runs
    return out


def fig_blocking(B, name='fig_step1_blocking'):
    """Share of Kloten HPs at near-zero load and the HP SF against local time, cold days."""
    import matplotlib.pyplot as plt
    hf.use_style()
    P = B['profile']; x = P.index / 4
    fig, axs = plt.subplots(1, 2, figsize=(hf.COL2, 2.6))
    ax = axs[0]
    ax.plot(x, P.cold_wkd, color='k', lw=1.4, label=f"cold weekdays ({B['n_cold_wkd']})")
    ax.plot(x, P.cold_wke, color='0.45', lw=1.2, ls='--', label='cold weekends')
    ax.plot(x, P.mild_wkd, color='0.65', lw=1.0, ls=':', label='mild weekdays (5-12 °C)')
    ax.set(xlabel='local time (h)', ylabel='share of HPs near zero', xlim=(0, 24), ylim=(0, 1),
           xticks=range(0, 25, 3))
    ax.legend(fontsize=6.5, loc='upper right')
    ax.text(0.02, 0.97, '(a)', transform=ax.transAxes, va='top')
    ax = axs[1]
    ax.plot(x, P.sf_cold_wkd, color='k', lw=1.4, label='cold weekdays')
    ax.plot(x, P.sf_cold_wke, color='0.45', lw=1.2, ls='--', label='cold weekends')
    ax.set(xlabel='local time (h)', ylabel='SF of the 50 HPs', xlim=(0, 24), ylim=(0, None),
           xticks=range(0, 25, 3))
    ax.legend(fontsize=6.5, loc='lower right')
    ax.text(0.02, 0.97, '(b)', transform=ax.transAxes, va='top')
    fig.tight_layout()
    return save_fig(fig, name)


def inventory_nameplate():
    """1.4: protocol ratings of the submetered HPs at Kloten, Hg and MqO (HEAPO only;
    the Swiss dataset has no protocols)."""
    import hp_pools as hpp
    p = hpp.build_pool_combined(verbose=False); w = p['weather_of']
    pr = pd.read_csv(HEAPO_PROTOCOLS, sep=';', low_memory=False)
    idc = [c for c in pr.columns if c.lower() == 'household_id'][0]
    cols = ['HeatPump_Installation_HeatingCapacity', 'HeatPump_Installation_Normpoint_ElectricPower',
            'HeatPump_Installation_Normpoint_HeatingPower']
    have = {c: set(pr.loc[pd.to_numeric(pr[c], errors='coerce') > 0, idc].dropna().astype(int)) for c in cols}
    proto = set(pr[idc].dropna().astype(int))
    rows = []
    for st in ('KLO', 'Hg', 'MqO'):
        hps = [h for h in p['hp_households'] if w.get(h) == st]
        heapo = [int(str(h).split(':')[1]) for h in hps if str(h).startswith('heapo:')]
        rows.append(dict(station=st, n_hp=len(hps), heapo=len(heapo), with_protocol=sum(h in proto for h in heapo),
                         **{c.split('_')[-1]: sum(h in have[c] for h in heapo) for c in cols}))
    return pd.DataFrame(rows)


def inventory_real():
    """1.5: are the real aggregates sums of separately metered households?"""
    import hp_pools as hpp
    p = hpp.build_pool_combined(verbose=False); w = p['weather_of']
    q = hpp.build_pool_wpuq(verbose=False)
    hp_set = set(p['hp_households']); eheat = set(p['eheat_households'])
    rows = []
    for st in ('Hg', 'MqO'):
        hps = [h for h in p['hp_households'] if w.get(h) == st]
        other = [h for h in p['households'] if w.get(h) == st and h not in hp_set]
        rows.append(dict(aggregate=st, n_hp_households=len(hps), hp_series=len(hps),
                         other_load_series=len(hps), non_hp_households=len(other),
                         non_hp_without_eheat=sum(h not in eheat for h in other), resolution='15 min'))
    rows.append(dict(aggregate='Hamelin (WPuQ)', n_hp_households=q['hp_mat'].shape[0],
                     hp_series=q['hp_mat'].shape[0], other_load_series=q['other_mat'].shape[0],
                     non_hp_households=0, non_hp_without_eheat=0,
                     resolution=str(q['index'][1] - q['index'][0])))
    return pd.DataFrame(rows)


def step1_inventory(rebuild=False):
    """Step 1: every inventory item, cached. The coverage scan (1.1) reads ~1700 raw files."""
    Y = inventory_years(rebuild)

    def build():
        B = blocking_profile()
        return dict(pv=inventory_pv(Y), blocking=B, windows=blocked_windows(B['per_hp']),
                    nameplate=inventory_nameplate(), real=inventory_real())
    out = _cached('step1_inventory', build, rebuild)
    out['years'] = Y
    return out


def years_table(Y):
    """Households with >= 90 % of 15-min intervals per window, by source and role."""
    cols = list(WINTERS) + list(CAL_HEAT)
    return (Y[cols] >= 0.9).groupby([Y.source, Y.role]).sum().T


# ===========================================================================
# Shared design of Steps 2-5: split pool and 15-min Kloten matrices
# ===========================================================================
SPLIT_SEED = 2026          # seeds the non-HP halves, one child seed per split
N_SPLITS = 20
_K15 = {}


def plan_splits(rebuild=False):
    """The 20 splits of the new steps.

    The HP halves are the published ones (pilot A, target B of ``outputs._kloten_design``),
    so any change against Table IV comes from the non-HP pool alone. The 1307 households
    without an HP are halved per split with its own seed: C (pilot side, calibration only)
    and F (target side, aggregates only). Indices are rows of ``_daily_pools()['KLO']``.
    """
    def build():
        Dz = rebuild_kloten_design()
        nfree = Dz['K']['free'].shape[0]
        seeds = np.random.SeedSequence(SPLIT_SEED).spawn(N_SPLITS)
        out = []
        for s, p in enumerate(Dz['pilots']):
            perm = np.random.default_rng(seeds[s]).permutation(nfree)
            out.append(dict(split=s, A=np.asarray(p['A']), B=np.asarray(p['B']),
                            C=np.sort(perm[:nfree // 2]), F=np.sort(perm[nfree // 2:]),
                            m=p['m'], b=p['b'], t=p['t'], seed=seeds[s].entropy))
        return out
    return _cached('splits', build, rebuild)


def kloten_15min():
    """15-min Kloten loads in local time, rows in ``_daily_pools()['KLO']`` order.

    whole: HP households' HP plus other load (50 x T); hp: HP load only; free: the
    1307 households without an HP; cap: robust peaks; T: daily mean temperature per
    interval's day; cold5: mask of the five coldest days; wkd: weekday mask.
    Memoized for the session (about 200 MB).
    """
    if 'KLO' in _K15:
        return _K15['KLO']
    from hp_capacity import robust_series_peak
    M = kloten_members(); p = M['pool']
    orow = {h: i for i, h in enumerate(p['households'])}
    hrows = [p['hp_households'].index(h) for h in M['hp']]
    hp = p['hp_mat'][hrows].astype(np.float32)
    whole = hp + p['other_mat'][[orow[h] for h in M['hp']]]
    free = p['other_mat'][[orow[h] for h in M['free']]].astype(np.float32)
    idx = p['index'].tz_convert(LOCAL_TZ)
    Td = pd.Series(p['temperature']['KLO'], index=idx).resample('D').mean()
    day = idx.normalize()
    cold5 = np.asarray(day.isin(Td.nsmallest(5).index))
    K = _daily_pools_klo()
    assert np.allclose(K['cap'], [robust_series_peak(r) for r in hp]), 'row order differs from _daily_pools'
    _K15['KLO'] = dict(whole=whole, hp=hp, free=free, cap=K['cap'], index=idx, cold5=cold5,
                       wkd=np.asarray(idx.dayofweek < 5), Td=Td)
    return _K15['KLO']


def _daily_pools_klo():
    return O._daily_pools(include_wpuq=False)['KLO']


PEAK_METRICS = ('max', 'p999', 'cold5', 'max_wkd', 'max_wke')


def peak_metrics(x, K):
    """Peak of one 15-min aggregate load: annual maximum (primary), 99.9th percentile,
    maximum over the five coldest days, and the weekday / weekend maxima (diagnostic).
    ``i_max`` is the interval of the annual maximum."""
    n = len(x); k = int(np.ceil(0.999 * (n - 1)))
    i = int(np.argmax(x))
    return dict(max=float(x[i]), p999=float(np.partition(x, k)[k]), cold5=float(x[K['cold5']].max()),
                max_wkd=float(x[K['wkd']].max()), max_wke=float(x[~K['wkd']].max()), i_max=i)


def rebound_mask(K):
    """Weekday intervals in the 45 min after the two Kloten block releases (12:00, 18:45)."""
    hm = K['index'].hour * 60 + K['index'].minute
    return K['wkd'] & np.asarray(((hm >= 720) & (hm < 765)) | ((hm >= 1125) & (hm < 1170)))


# ===========================================================================
# Step 2 -- increment model on the pilot side
# ===========================================================================
C_N = (30, 40, 50)
C_K = (0, 5, 10, 15, 20, 25)


def increment_model(draws=100, rebuild=False):
    """Step 2: c(N, k0, k1) = [peak(future) - peak(current)] / sum of added HP capacities.

    Pilot side only: HP households of the pilot half A (whole-house load) and the
    pilot-side households without an HP, C. Per draw, the 25 pilot HPs are ordered at
    random and 50 households of C are drawn; the aggregate (N, k) holds the first k HPs
    and the first N - k households of C. The future of (N, k0) is (N, k1): the last
    k1 - k0 non-HP households of the current aggregate are replaced by the next HPs,
    so the two share every other household. All (N, k0 < k1) cells come from the same
    draws. Returns one row per (split, draw, N, k0, k1).

    Diagnostics next to the prompt's c (whole-house replacement):
      c_on_*   switch-on: the HP circuits of the k1 - k0 added HPs are added to the
               current aggregate, whose households all stay (adoption by existing
               households; the reverse of Step 6's switch-off);
      c_hp_*   HP circuits only, no other load at all: the increment of the HP fleet;
      reb_*    whether the annual maximum falls in a post-release window (rebound).
    """
    def build():
        K = kloten_15min(); rows, units = [], []
        reb = rebound_mask(K)
        for sp in plan_splits():
            s = sp['split']
            rng = np.random.default_rng(np.random.SeedSequence([SPLIT_SEED, 2, s]))
            units.append(dict(split=s, P_unit=float(K['cap'][sp['A']].mean()),
                              P_unit_sd=float(K['cap'][sp['A']].std())))
            for d in range(draws):
                H = rng.permutation(sp['A']); F = rng.choice(sp['C'], max(C_N), replace=False)
                z = np.zeros(K['whole'].shape[1], np.float32)
                hp_cum, hpc_cum, nf_cum = {0: z}, {0: z}, {0: z}
                for k in C_K[1:]:
                    hp_cum[k] = hp_cum[k - 5] + K['whole'][H[k - 5:k]].sum(0)
                    hpc_cum[k] = hpc_cum[k - 5] + K['hp'][H[k - 5:k]].sum(0)
                cap_cum = {k: float(K['cap'][H[:k]].sum()) for k in C_K}
                for j in range(5, max(C_N) + 1, 5):
                    nf_cum[j] = nf_cum[j - 5] + K['free'][F[j - 5:j]].sum(0)
                cur = {(N, k): hp_cum[k] + nf_cum[N - k] for N in C_N for k in C_K}
                pk = {key: peak_metrics(x, K) for key, x in cur.items()}
                pc = {k: peak_metrics(hpc_cum[k], K) for k in C_K[1:]}
                for N in C_N:
                    for k0 in C_K:
                        for k1 in C_K:
                            if k1 <= k0:
                                continue
                            dc = cap_cum[k1] - cap_cum[k0]
                            on = peak_metrics(cur[(N, k0)] + hpc_cum[k1] - hpc_cum[k0], K)
                            hp0 = pc[k0]['max'] if k0 else 0.0
                            rows.append(dict(split=s, draw=d, N=N, k0=k0, k1=k1, cap_added=dc,
                                             **{f'cur_{m}': pk[(N, k0)][m] for m in PEAK_METRICS},
                                             **{f'c_{m}': (pk[(N, k1)][m] - pk[(N, k0)][m]) / dc
                                                for m in PEAK_METRICS},
                                             c_on_max=(on['max'] - pk[(N, k0)]['max']) / dc,
                                             c_on_p999=(on['p999'] - pk[(N, k0)]['p999']) / dc,
                                             c_hp_max=(pc[k1]['max'] - hp0) / dc,
                                             reb_cur=bool(reb[pk[(N, k0)]['i_max']]),
                                             reb_fut=bool(reb[pk[(N, k1)]['i_max']]),
                                             reb_on=bool(reb[on['i_max']])))
        return dict(rows=pd.DataFrame(rows), units=pd.DataFrame(units))
    return _cached('step2_increment', build, rebuild)


def step2_tables(G, metrics=('max', 'p999', 'cold5', 'on_max', 'hp_max')):
    """Pooled c per N and variant: median [IQR] over splits of the per-split median over
    all (k0, k1) cells and draws, plus the spread of the cell medians within N."""
    rows = []
    for m in metrics:
        col = f'c_{m}'
        per = G.groupby(['N', 'split'])[col].median().groupby('N')
        cells = split_summary(G, ['N', 'k0', 'k1'], col)['med'].groupby('N')
        for N in C_N:
            x = per.get_group(N)
            rows.append(dict(variant=m, N=N, med=x.median(), q25=x.quantile(.25), q75=x.quantile(.75),
                             cell_lo=cells.get_group(N).min(), cell_hi=cells.get_group(N).max()))
    return pd.DataFrame(rows).set_index(['variant', 'N'])


def split_summary(G, by, col, stat='median'):
    """Per-split statistic of ``col`` within each ``by`` cell, then median [IQR], min and
    max over the splits (the primary uncertainty of the new steps)."""
    per = G.groupby(by + ['split'])[col].agg(stat).reset_index()
    return per.groupby(by)[col].agg(med='median', q25=lambda x: x.quantile(.25),
                                    q75=lambda x: x.quantile(.75), lo='min', hi='max')


C_VARIANTS = (('c_max', 'whole-house replacement'), ('c_on_max', 'switch-on'), ('c_hp_max', 'HP circuits only'))


def fig_increment(G, variants=C_VARIANTS, N=40, name='fig_step2_increment'):
    """Median over splits of the per-split median c per (k0, k1), one panel per variant,
    at one household count (c_hp does not depend on N)."""
    import matplotlib.pyplot as plt
    hf.use_style()
    fig, axs = plt.subplots(1, len(variants), figsize=(hf.COL2, 2.5), sharey=True)
    for ax, (col, label) in zip(axs, variants):
        S = split_summary(G[G.N == N], ['k0', 'k1'], col)['med']
        M = S.unstack('k1').reindex(index=list(C_K[:-1]), columns=list(C_K[1:]))
        im = ax.imshow(M.to_numpy(), origin='lower', cmap='cividis', vmin=0.3, vmax=0.9, aspect='auto')
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M.iat[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=6,
                            color='k' if v > 0.62 else 'w')
        ax.set_xticks(range(M.shape[1])); ax.set_xticklabels(M.columns)
        ax.set_yticks(range(M.shape[0])); ax.set_yticklabels(M.index)
        ax.set(xlabel='HPs after, $k_1$', title=label); ax.grid(False)
    axs[0].set_ylabel('HPs before, $k_0$')
    cb = fig.colorbar(im, ax=axs, pad=0.02, fraction=0.03)
    cb.set_label('increment $c$ (kW per kW added)', fontsize=7)
    return save_fig(fig, name)
