# -*- coding: utf-8 -*-
"""Shared fitter for the cross-dataset characterisation table.

Given a daily aggregate (temperature, net load, submetered heating/cooling ETL
load and per-arm installed capacity), fit the net-load curve and the SF. If only
one arm carries the temperature-driven energy, fall back to a single hockey
stick; otherwise fit the full bathtub. SF arms are anchored at the net-load
thresholds (heating below T_h, cooling above T_c)."""
import numpy as np
from hp_common import (fit_bathtub_stick, fit_hockey_stick, fit_cooling_stick,
                       T_BALANCE_BOUNDS, T_COOLING_BOUNDS)


def _sf_arm(T, sf, thr, side):
    """OLS SF arm anchored at thr: heating below (side='h'), cooling above."""
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
