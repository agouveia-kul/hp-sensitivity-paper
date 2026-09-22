# -*- coding: utf-8 -*-
"""Figure and table generators for ``paper_results.ipynb``.

One function per paper artifact, folded from the former per-figure/per-table
scripts. Shared helpers (fitters, styling, data loaders, the cross-dataset
fitter) come from ``utils``; the heavier data-pipeline modules that the other
notebooks also use (``hp_pools``, ``hp_design``, ``hp_analysis``,
``hp_capacity``, ``pecan_street``) are imported lazily inside each function so
``import outputs`` stays cheap and never triggers a data load on its own.

Every function writes its PDF/PNG to ``paper/figures`` or its ``.tex`` to
``paper/tables`` (via ``utils.save`` / direct write) and returns nothing except
where noted.
"""
import os
import pickle

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import hp_figures as hf
from hp_common import (fit_hockey_stick, fit_cooling_stick, fit_bathtub_stick,
                       bathtub_stick, T_BALANCE_BOUNDS)
import utils as U

SWISS_SF = dict(base=0.027, slope=0.0161, t_thr=16.4)   # pooled Swiss SF reference curve
WPUQ_TRUE_KW = 238.51424035310907                       # measured WPUQ installed HP capacity


# ===========================================================================
# Section 1 -- net-load bathtub
# ===========================================================================
def fig_bathtub_example():
    """Fig. 2: Austin bathtub fit with the terms of Eq. (1) mapped onto it."""
    import pecan_street as ps
    hf.use_style()
    pecan_daily, _ = ps.load_austin_ac_pool(verbose=False)
    agg = None
    for d in pecan_daily.values():
        agg = d['load'].copy() if agg is None else agg.add(d['load'], fill_value=0)
    T = pd.concat([d['T'] for d in pecan_daily.values()], axis=1).mean(axis=1)
    df = pd.DataFrame({'T': T, 'y': agg}).dropna()
    Tv, yv = df['T'].to_numpy(), df['y'].to_numpy()
    base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, yv)

    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.grid(False)
    ax.scatter(Tv, yv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean load')
    xa = np.linspace(Tv.min(), th, 100)
    xd = np.linspace(tc, Tv.max(), 100)
    ax.plot(xa, base + hs * (th - xa), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
    ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
    ax.plot(xd, base + cs * (xd - tc), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
    ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)
    y0 = yv.min() - 3
    ax.set_ylim(y0, yv.max() * 1.06)
    g = dict(color='0.35', lw=0.8, ls=(0, (3, 3)), zorder=3)
    ax.hlines(base, th, tc, **g)
    ax.annotate(r'$P_{\mathrm{base}}$', xy=(th, base), xytext=(4, 8),
                textcoords='offset points', fontsize=8, color='0.15')
    for xT, lab, dx in [(th, r'$T_h$', -1), (tc, r'$T_c$', 1)]:
        ax.vlines(xT, y0, base, **g)
        ax.annotate(lab, xy=(xT, y0), xytext=(dx * 6, 3), textcoords='offset points',
                    ha='center', fontsize=8, color='0.15')
    xh = th - (th - Tv.min()) * 0.45; yh = base + hs * (th - xh)
    ax.annotate(r'$s_h$', xy=(xh, yh), xytext=(-16, 12), textcoords='offset points',
                fontsize=8, color=hf.C_HP, arrowprops=dict(arrowstyle='-', lw=0.6, color='0.5'))
    xc = tc + (Tv.max() - tc) * 0.45; yc = base + cs * (xc - tc)
    ax.annotate(r'$s_c$', xy=(xc, yc), xytext=(-20, 6), textcoords='offset points',
                fontsize=8, color=hf.C_CH, arrowprops=dict(arrowstyle='-', lw=0.6, color='0.5'))
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('aggregate load (kW)')
    ax.legend(fontsize=7, loc='upper left')
    ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes, ha='left', va='top', fontsize=7, color='0.3')
    fig.tight_layout()
    hf.save(fig, 'fig_bathtub_example')
    print('saved -> fig_bathtub_example')


def fig_bathtub_critical():
    """Fig. 4: bathtub with arms extrapolated to SF->1 and regions R1-R5."""
    hf.use_style()
    m = U.load_austin_arm_capacity()
    Tv, yv = m.d['T'].to_numpy(), m.d['net'].to_numpy()
    base, hs, th, cs, tc = m.base, m.s_h, m.T_h, m.s_c, m.T_c
    capH, capC = m.capH, m.capC
    peak_h = hs * (th - Tv.min())
    peak_c = cs * (Tv.max() - tc)
    cap_h = base + capH
    cap_c = base + capC
    Th_crit = th - capH / hs
    Tc_crit = tc + capC / cs

    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.grid(False)
    ax.scatter(Tv, yv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean load')
    xa = np.linspace(Tv.min(), th, 100)
    xd = np.linspace(tc, Tv.max(), 100)
    ax.plot(xa, base + hs * (th - xa), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
    ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
    ax.plot(xd, base + cs * (xd - tc), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
    ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)
    ax.plot([Tv.min(), Th_crit], [base + peak_h, cap_h],
            color=hf.C_HP, lw=1.4, ls=(0, (4, 2)), zorder=4, label='extrapolation ($\\mathrm{SF}\\!\\to\\!1$)')
    ax.plot([Tv.max(), Tc_crit], [base + peak_c, cap_c],
            color=hf.C_CH, lw=1.4, ls=(0, (4, 2)), zorder=4)
    g = dict(color='0.35', lw=0.8, ls=(0, (3, 3)), zorder=3)
    y0 = yv.min() - 3
    ax.vlines(Th_crit, y0, cap_h, **g)
    ax.vlines(Tc_crit, y0, cap_c, **g)
    ax.plot(Th_crit, cap_h, 'o', color=hf.C_HP, ms=5, zorder=5)
    ax.plot(Tc_crit, cap_c, 'o', color=hf.C_CH, ms=5, zorder=5)
    ax.annotate(r'$T_h^{\mathrm{crit}}$', xy=(Th_crit, y0), xytext=(4, 3),
                textcoords='offset points', ha='left', fontsize=8, color='0.15')
    ax.annotate(r'$T_c^{\mathrm{crit}}$', xy=(Tc_crit, y0), xytext=(4, 3),
                textcoords='offset points', ha='left', fontsize=8, color='0.15')
    ax.annotate(r'$P_h^{\max}$', xy=(Th_crit, cap_h), xytext=(0, 6),
                textcoords='offset points', ha='center', va='bottom', fontsize=8, color=hf.C_HP)
    ax.annotate(r'$P_c^{\max}$', xy=(Tc_crit, cap_c), xytext=(0, 6),
                textcoords='offset points', ha='center', va='bottom', fontsize=8, color=hf.C_CH)
    tmin, tmax = Tv.min(), Tv.max()
    for xb in (tmin, tmax):
        ax.axvline(xb, color='0.75', lw=0.6, ls=(0, (1, 2)), zorder=1)
    ax.set_xlim(Th_crit - 8, Tc_crit + 8)
    ax.set_ylim(y0, cap_c * 1.30)
    for (lo, hi), lab in zip([(Th_crit, tmin), (tmin, th), (th, tc), (tc, tmax), (tmax, Tc_crit)],
                             ['R4', 'R1', 'R2', 'R3', 'R5']):
        ax.text((lo + hi) / 2, 60, lab, ha='center', va='center', fontsize=8.5,
                color='0.35', fontweight='bold', zorder=6)
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('aggregate load (kW)')
    ax.legend(fontsize=7, loc='upper left')
    fig.tight_layout()
    hf.save(fig, 'fig_bathtub_critical')
    print('saved -> fig_bathtub_critical')


# ===========================================================================
# Section 2 -- simultaneity factor
# ===========================================================================
def fig_sf_arms_anchored():
    """Fig. 3 (overleaf): SF arms fit independently, anchored at the net-load thresholds."""
    hf.use_style()
    m = U.load_austin_arm_capacity()
    devices = m.devices
    CapH, CapC = m.capH, m.capC
    Th, Tc = m.T_h, m.T_c
    Tser = m.Tds
    idx = Tser.index

    def arm_sum(flag):
        s = pd.Series(0.0, index=idx)
        for dv in devices:
            if dv[flag]:
                s = s.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
        return s
    heatsum, coolsum = arm_sum('a_h'), arm_sum('a_c')
    dh = pd.DataFrame({'T': Tser, 'sf': (heatsum / CapH).clip(0, 1)}).dropna()
    dh = dh[dh['T'] < Th]
    dc = pd.DataFrame({'T': Tser, 'sf': (coolsum / CapC).clip(0, 1)}).dropna()
    dc = dc[dc['T'] > Tc]
    mh, bh = np.polyfit(Th - dh['T'], dh['sf'], 1)
    mc, bc = np.polyfit(dc['T'] - Tc, dc['sf'], 1)

    def r2f(x, y, mm, bb):
        ss = np.sum((y - y.mean()) ** 2)
        return 1 - np.sum((y - (mm * x + bb)) ** 2) / ss
    r2h = r2f((Th - dh['T']).to_numpy(), dh['sf'].to_numpy(), mh, bh)
    r2c = r2f((dc['T'] - Tc).to_numpy(), dc['sf'].to_numpy(), mc, bc)
    Tmin, Tmax = dh['T'].min(), dc['T'].max()

    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.grid(False)
    ax.scatter(dh['T'], dh['sf'], s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
    ax.scatter(dc['T'], dc['sf'], s=8, color='0.65', alpha=.45, edgecolor='none')
    ax.axvspan(Th, Tc, color='0.5', alpha=.08, lw=0)
    xa = np.linspace(Tmin, Th, 100)
    xd = np.linspace(Tc, Tmax, 100)
    ax.plot(xa, np.clip(bh + mh * (Th - xa), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
    ax.plot(xd, np.clip(bc + mc * (xd - Tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
    gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
    ax.vlines(Th, 0, 0.20, **gth)
    ax.annotate('$T_h$', xy=(Th, 0.20), xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, color='0.3')
    ax.vlines(Tc, 0, 0.20, **gth)
    ax.annotate('$T_c$', xy=(Tc, 0.20), xytext=(0, 3), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, color='0.3')
    ax.annotate(r'$\hat{\mathrm{SF}}_h(T) = b_h + m_h\,(T_h - T)$',
                xy=(5, bh + mh * (Th - 5)), xytext=(0, 0.40), textcoords='data',
                ha='left', va='bottom', fontsize=8, color=hf.C_HP,
                arrowprops=dict(arrowstyle='-', lw=0.7, color=hf.C_HP))
    ax.annotate(r'$\hat{\mathrm{SF}}_c(T) = b_c + m_c\,(T - T_c)$',
                xy=(27, bc + mc * (27 - Tc)), xytext=(27, 0.60), textcoords='data',
                ha='center', va='bottom', fontsize=8, color=hf.C_CH,
                arrowprops=dict(arrowstyle='-', lw=0.7, color=hf.C_CH))
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('simultaneity factor')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, loc='upper left')
    ax.text(0.035, 0.72, f'$R^2$ {r2h:.2f} (heat), {r2c:.2f} (cool)', transform=ax.transAxes,
            ha='left', va='top', fontsize=7, color='0.3')
    fig.tight_layout()
    hf.save(fig, 'fig_sf_arms_anchored')
    print('saved -> fig_sf_arms_anchored')


def fig_sf_austin_activity():
    """Fig. 3 (v5): activity-based SF with a bathtub fit."""
    hf.use_style()
    m = U.load_austin_arm_capacity()
    devices = m.devices
    CapH, CapC, CapB = m.capH, m.capC, m.capB
    T_h0, T_c0 = m.T_h, m.T_c
    Tser = m.Tds
    idx = Tser.index

    def arm_sum(flag):
        s = pd.Series(0.0, index=idx)
        for dv in devices:
            if dv[flag]:
                s = s.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
        return s
    heatsum, coolsum, bandsum = arm_sum('a_h'), arm_sum('a_c'), arm_sum('a_b')
    mask_h, mask_c = Tser < T_h0, Tser > T_c0
    mask_b = ~(mask_h | mask_c)
    SF = pd.Series(index=idx, dtype=float)
    SF[mask_h] = heatsum[mask_h] / CapH
    SF[mask_c] = coolsum[mask_c] / CapC
    SF[mask_b] = bandsum[mask_b] / CapB
    d = pd.DataFrame({'T': Tser, 'sf': SF.clip(0, 1)}).dropna()
    Tv, Sv = d['T'].to_numpy(), d['sf'].to_numpy()
    base, hs, th, cs, tc, r2 = fit_bathtub_stick(Tv, Sv)

    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.scatter(Tv, Sv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
    xa = np.linspace(Tv.min(), th, 100)
    xd = np.linspace(tc, Tv.max(), 100)
    ax.plot(xa, np.clip(base + hs * (th - xa), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
    ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
    ax.plot(xd, np.clip(base + cs * (xd - tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
    ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)
    gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
    ax.vlines(th, base, base + 0.12, **gth)
    ax.annotate('$T_h^{\\mathrm{SF}}$', xy=(th, base + 0.12), xytext=(-3, 1),
                textcoords='offset points', ha='right', fontsize=9, color='0.3')
    ax.vlines(tc, base, base + 0.12, **gth)
    ax.annotate('$T_c^{\\mathrm{SF}}$', xy=(tc, base + 0.12), xytext=(3, 1),
                textcoords='offset points', fontsize=9, color='0.3')
    ax.annotate('$b$', xy=((th + tc) / 2, base), xytext=(0, 6), textcoords='offset points',
                ha='center', va='bottom', fontsize=9, color='0.2')
    arw = dict(arrowstyle='-', lw=0.6, color='0.5')
    xm = th - (th - Tv.min()) * 0.5
    ax.annotate('$m_h$', xy=(xm, base + hs * (th - xm)), xytext=(-2, 10),
                textcoords='offset points', fontsize=9, color=hf.C_HP, arrowprops=arw)
    xmc = tc + (Tv.max() - tc) * 0.5
    ax.annotate('$m_c$', xy=(xmc, base + cs * (xmc - tc)), xytext=(-20, 8),
                textcoords='offset points', fontsize=9, color=hf.C_CH, arrowprops=arw)
    ax.set_xlabel('daily mean temperature ($^\\circ$C)')
    ax.set_ylabel('simultaneity factor')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, loc='upper left')
    ax.text(0.035, 0.72, f'$R^2$ {r2:.3f}', transform=ax.transAxes, ha='left', va='top', fontsize=7, color='0.3')
    fig.tight_layout()
    hf.save(fig, 'fig_sf_austin_activity')
    print('saved -> fig_sf_austin_activity')


def tab_sf():
    """tab_sf, tab_sf_train and fig_sf_pooled from the factorial design."""
    from scipy.stats import spearmanr

    def sf_anchored(T, Y, thr):
        m = T < thr
        if m.sum() < 10:
            return np.nan, np.nan, np.nan
        mm, bb = np.polyfit(thr - T[m], Y[m], 1)
        pred = bb + mm * (thr - T[m])
        ss = np.sum((Y[m] - Y[m].mean()) ** 2)
        r2 = 1 - np.sum((Y[m] - pred) ** 2) / ss if ss > 0 else np.nan
        return bb, mm, r2

    subs = U.build_frames(U.pickle_load('data/design_factorial.pkl'))
    for s in subs:
        try:
            T, Y, L = np.asarray(s['T']), np.asarray(s['SF']), np.asarray(s['Load'])
            _, _, tt, _ = fit_hockey_stick(T, L, T_BALANCE_BOUNDS)
            b, sl, r2 = sf_anchored(T, Y, tt)
            s['coldSF'] = float(np.clip(b + sl * max(0.0, tt - T.min()), 0, 1))
            s['base'] = float(b); s['slope'] = float(sl); s['thr'] = float(tt)
            s['self_r2'] = float(r2)
        except Exception:
            s['coldSF'] = s['base'] = s['slope'] = s['thr'] = s['self_r2'] = np.nan
        s['N_hp'] = int(round(s['hp_ratio'] * s['N_total']))
    subs = [s for s in subs if np.isfinite(s['coldSF'])]
    subs50 = [s for s in subs if int(s['N_total']) == 50]
    print(f'{len(subs)} usable SF fits; {len(subs50)} at N_total=50 (Table 1)')

    D = pd.DataFrame([{k: s[k] for k in ('N_hp', 'hp_ratio', 'HP_Peak',
                       'coldSF', 'base', 'slope', 'thr', 'self_r2')} for s in subs50])
    print(f'invariance: rho(coldSF,rate)={spearmanr(D.hp_ratio, D.coldSF).statistic:+.3f} '
          f'rho(coldSF,power)={spearmanr(D.HP_Peak, D.coldSF).statistic:+.3f}; '
          f'median R2 {D.self_r2.median():.3f}')

    rng = np.random.default_rng(0)
    idx = np.arange(len(subs)); rng.shuffle(idx)
    ref = [subs[i] for i in idx[:len(idx) // 2]]
    tgt = [subs[i] for i in idx[len(idx) // 2:]]
    curve = U.pooled_curve(ref)

    def wape(pred, true):
        return np.abs(np.asarray(pred) - np.asarray(true)).sum() / np.asarray(true).sum() * 100
    wrows = []
    for s in ref:
        pred = np.clip(U.predict(curve, s['T']), 0, 1)
        wrows.append(dict(N_hp=s['N_hp'], num=np.abs(pred - s['SF']).sum(), den=np.sum(s['SF'])))
    W = pd.DataFrame(wrows)
    train_wape = W.groupby('N_hp').apply(lambda x: x.num.sum() / x.den.sum() * 100)
    overall_train = W.num.sum() / W.den.sum() * 100

    trows = []
    for s in tgt:
        Ts = np.asarray(s['T']); SFs = np.asarray(s['SF'])
        p_tr = np.clip(U.predict(curve, Ts), 0, 1)
        mb = Ts < curve['t_thr']
        r2 = (1 - np.sum((SFs[mb] - p_tr[mb]) ** 2) /
              np.sum((SFs[mb] - SFs[mb].mean()) ** 2)) if mb.sum() >= 10 else np.nan
        trows.append(dict(N_hp=s['N_hp'], pk_true=np.quantile(SFs, .99), pk_tr=np.quantile(p_tr, .99), r2=r2))
    Tt = pd.DataFrame(trows)
    print(f'held-out transfer: R2 {Tt.r2.median():.3f}, peak-SF WAPE all {wape(Tt.pk_tr, Tt.pk_true):.1f}%')

    def iqr(x):
        return x.quantile(.75) - x.quantile(.25)
    par = D.groupby('N_hp').agg(r2=('self_r2', 'median'),
                                cold_m=('coldSF', 'median'), cold_i=('coldSF', iqr),
                                base_m=('base', 'median'), base_i=('base', iqr),
                                slp_m=('slope', 'median'), slp_i=('slope', iqr),
                                thr_m=('thr', 'median'), thr_i=('thr', iqr))

    def row(nhp, r):
        return (f"{nhp} & \\chg{{{r['r2']:.3f}}} & {r['cold_m']:.2f}\\,({r['cold_i']:.2f}) & "
                f"\\chg{{{r['base_m']:.3f}\\,({r['base_i']:.3f})}} & "
                f"{r['slp_m']:.3f}\\,({r['slp_i']:.3f}) & \\chg{{{r['thr_m']:.1f}\\,({r['thr_i']:.1f})}} \\\\")
    body = "\n".join(row(int(n), r) for n, r in par.iterrows())
    allr = (f"all & \\chg{{{D.self_r2.median():.3f}}} & {D.coldSF.median():.2f}\\,({iqr(D.coldSF):.2f}) & "
            f"\\chg{{{D.base.median():.3f}\\,({iqr(D.base):.3f})}} & "
            f"{D.slope.median():.3f}\\,({iqr(D.slope):.3f}) & \\chg{{{D.thr.median():.1f}\\,({iqr(D.thr):.1f})}} \\\\")
    tex = r"""\begin{table}[t]
\centering
\caption{Per-substation fitted SF parameters by number of aggregated HPs $N_{hp}$, as a median with its interquartile range}
\label{tab:sf}
\begin{tabular}{rccccc}
\toprule
$N_{hp}$ & $R^2$ & SF$_{\mathrm{cold}}$ & $b$ & $m$ ($^\circ$C$^{-1}$) & $T_h^{\mathrm{SF}}$ ($^\circ$C) \\
\midrule
""" + body + "\n\\midrule\n" + allr + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_sf.tex', 'w').write(tex)

    wbody = "\n".join(f"{int(n)} & {v:.1f} \\\\" for n, v in train_wape.items())
    wtex = r"""\begin{table}[t]
\centering
\caption{Total WAPE of the single pooled SF curve against the training substations, by $N_{hp}$}
\label{tab:sf-train}
\begin{tabular}{rc}
\toprule
$N_{hp}$ & total WAPE (\%) \\
\midrule
""" + wbody + "\n\\midrule\n" + f"all & {overall_train:.1f} \\\\" + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_sf_train.tex', 'w').write(wtex)

    hf.use_style()
    Tall = np.concatenate([s['T'] for s in ref])
    SFall = np.concatenate([s['SF'] for s in ref])
    thr = curve['t_thr']
    mb = Tall < thr
    m_r, b_r = np.polyfit(thr - Tall[mb], SFall[mb], 1)
    r2_r = 1 - np.sum((SFall[mb] - (b_r + m_r * (thr - Tall[mb]))) ** 2) / \
        np.sum((SFall[mb] - SFall[mb].mean()) ** 2)
    k = rng.choice(len(Tall), size=min(4000, len(Tall)), replace=False)
    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    ax.scatter(Tall[k], SFall[k], s=4, color='0.7', alpha=.3, edgecolor='none', label='training SF')
    ax.set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
    xl = ax.get_xlim()
    ax.axvspan(thr, xl[1], color='0.5', alpha=.12, lw=0, zorder=0)
    ax.set_xlim(xl)
    Tg = np.linspace(Tall.min(), thr, 150)
    ax.plot(Tg, np.clip(b_r + m_r * (thr - Tg), 0, 1), color=hf.C_HP, lw=1.9, label='pooled fit')
    Tp = 5.0
    ax.annotate(r'$\hat{\mathrm{SF}}(T)$', xy=(Tp, float(np.clip(b_r + m_r * (thr - Tp), 0, 1))),
                xytext=(18, 14), textcoords='offset points', fontsize=9, color=hf.C_HP,
                arrowprops=dict(arrowstyle='-', lw=0.6, color=hf.C_HP))
    ax.legend(fontsize=7, loc='upper left')
    ax.text(0.035, 0.55 / 0.75, f"$R^2$ {r2_r:.3f}", transform=ax.transAxes, ha='left', va='center', fontsize=7, color='0.3')
    fig.tight_layout()
    hf.save(fig, 'fig_sf_pooled')
    print('wrote tab_sf.tex, tab_sf_train.tex, fig_sf_pooled')


# ===========================================================================
# Section 3 -- energy and installed capacity
# ===========================================================================
def tab_energy():
    """tab_energy: daily vs hourly resolution for the energy estimate."""
    import hp_design as hd
    design = U.pickle_load('data/design_factorial.pkl')
    fits = pd.read_parquet('data/factorial_fits.parquet')
    L = fits[(fits.response == 'Load') & (~fits.failed)]
    d24 = L[L.resolution == '24 h'].set_index('substation_id')
    d1 = L[L.resolution == '1 h'].set_index('substation_id')
    meta = design['meta']
    rows = []
    for sid in meta.index:
        if int(meta.loc[sid, 'N_hp']) == 0 or sid not in d24.index or sid not in d1.index:
            continue
        temp = hd.get_series(design, sid, 'Temperature')
        hp = pd.Series(design['hp_load'][sid], index=design['index'])
        dt = temp.index.to_series().diff().median().total_seconds() / 3600
        actual = float((hp * dt).sum())
        if actual <= 0:
            continue
        Tday = temp.resample('D').mean()
        Thr = temp.resample('h').mean()
        s24, t24 = float(d24.loc[sid, 'slope']), float(d24.loc[sid, 'T_threshold'])
        s1, t1 = float(d1.loc[sid, 'slope']), float(d1.loc[sid, 'T_threshold'])
        e_day = float((s24 * (t24 - Tday).clip(lower=0) * 24.0).sum())
        e_hour = float((s1 * (t1 - Thr).clip(lower=0) * 1.0).sum())
        e_mix = float((s24 * (t24 - Thr).clip(lower=0) * 1.0).sum())
        rows.append(dict(sid=sid, N_hp=int(meta.loc[sid, 'N_hp']), actual=actual,
                         e_day=e_day, e_hour=e_hour, e_mix=e_mix))
    g = pd.DataFrame(rows)
    for col in ['e_day', 'e_hour', 'e_mix']:
        g[col + '_r'] = g[col] / g.actual
    print(f'{len(g)} substations')

    def r(name, c):
        w = np.abs(g[c] - g.actual).sum() / g.actual.sum() * 100
        return f"{name} & {w:.1f} & {g[c + '_r'].median():.2f} \\\\"
    tex = r"""\begin{table}[t]
\centering
\caption{Energy-estimate accuracy against submetered HP energy, by the resolution of the fit and of the temperature integration}
\label{tab:energy}
\begin{tabular}{lcc}
\toprule
fit + integration & WAPE (\%) & median ratio \\
\midrule
""" + r("daily + daily", 'e_day') + "\n" \
        + r("hourly + hourly", 'e_hour') + "\n" \
        + r("daily + hourly", 'e_mix') + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_energy.tex', 'w').write(tex)
    print('wrote tab_energy.tex')


def fig_energy_error(below_th=True):
    """Energy-estimate error distribution. below_th -> fig_energy_error_belowTh
    (T < T_h days only, overleaf); else the all-days fig_energy_error (v5)."""
    from scipy import stats  # noqa: F401
    import hp_analysis as ha
    design = U.pickle_load('data/design_factorial.pkl')
    fits = pd.read_parquet('data/factorial_fits.parquet')
    te = ha.thermal_energy_estimates(design, fits, resolution='24 h')
    te['N_hp'] = te.N_hp.astype(int)
    frame = te[te.hs_kWh > 0].copy() if below_th else te
    g = frame.groupby('substation_id').agg(est=('hs_kWh', 'sum'), act=('actual_kWh', 'sum'),
                                           N_hp=('N_hp', 'first'))
    g = g[g.act > 0].copy()
    g['spe'] = (g.est - g.act) / g.act * 100
    name = 'fig_energy_error_belowTh' if below_th else 'fig_energy_error'

    hf.use_style()
    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    ax[0].hist(g.spe.clip(-60, 60), bins=40, color=hf.C_CH, alpha=.8, edgecolor='none')
    ax[0].axvline(0, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax[0].axvline(g.spe.median(), color=hf.C_HP, lw=1.5, label=f'median {g.spe.median():+.0f}%')
    ax[0].set(xlabel='signed % error (est $-$ actual)', ylabel='substations')
    ax[0].legend(fontsize=7, loc='upper right')
    order = [5, 10, 20, 30, 40, 50]
    data = [g.loc[g.N_hp == k, 'spe'].values for k in order]
    bp = ax[1].boxplot(data, positions=range(len(order)), widths=.6, showfliers=False,
                       whis=(5, 95), patch_artist=True, medianprops=dict(color=hf.C_HP, lw=1.4))
    for b in bp['boxes']:
        b.set(facecolor=hf.C_CH, alpha=.35, edgecolor='0.5')
    ax[1].axhline(0, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax[1].set_xticks(range(len(order))); ax[1].set_xticklabels(order)
    ax[1].set(xlabel='HPs aggregated $N_{hp}$', ylabel='signed % error')
    fig.tight_layout()
    hf.save(fig, name)
    print('saved ->', name)


def fig_slope_capacity():
    """fig_slope_capacity: heating sensitivity vs installed HP capacity."""
    hf.use_style()
    F = pd.read_parquet('data/factorial_fits.parquet')
    L = F[(F.response == 'Load') & (F.resolution == '24 h') & (~F.failed) & (F.N_hp > 0)]
    x = L.HP_Peak.to_numpy()
    y = L.slope.to_numpy()
    nhp = L.N_hp.to_numpy()
    slope0 = np.sum(x * y) / np.sum(x * x)
    r = np.corrcoef(x, y)[0, 1]
    print(f'n={len(L)} Pearson r={r:.3f} through-origin slope={slope0:.4f}')
    fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
    sc = ax.scatter(x, y, c=nhp, s=9, cmap='viridis', alpha=.7, edgecolor='none')
    xl = np.array([0, x.max() * 1.02])
    ax.plot(xl, slope0 * xl, color=hf.C_HP, lw=1.4,
            label=f'through-origin fit\n($\\rho={r:.2f}$, $m={slope0:.3f}\\,^\\circ$C$^{{-1}}$)')
    ax.set(xlabel='installed HP capacity $P_{\\mathrm{ETL}}^{\\max}$ (kW)',
           ylabel='heating sensitivity $s_h$ (kW/$^\\circ$C)')
    ax.legend(fontsize=7, loc='upper left')
    cb = fig.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label('$N_{hp}$', fontsize=8)
    fig.tight_layout()
    hf.save(fig, 'fig_slope_capacity')
    print('saved -> fig_slope_capacity')


def tab_capacity():
    """tab_capacity: installed-capacity accuracy for the two estimators."""
    RNG = np.random.default_rng(0)
    d = U.fits_frame(U.pickle_load('data/design_factorial.pkl'))
    d['N_hp'] = (d.hp_ratio * d.N_total).round().astype(int)
    idx = np.arange(len(d)); RNG.shuffle(idx)
    tr = d.iloc[idx[:len(idx) // 2]].reset_index(drop=True)
    te = d.iloc[idx[len(idx) // 2:]].reset_index(drop=True)
    b = np.sum(tr.delta * tr.HP_Peak) / np.sum(tr.delta ** 2)
    sf_ref = float(tr.SF_cold.median())
    p_sf = te.delta / sf_ref
    p_or = te.delta / te.SF_cold
    A = te.HP_Peak.to_numpy()

    def wape(p):
        return np.abs(np.asarray(p) - A).sum() / A.sum() * 100

    def line(name, p):
        r2 = U.metrics(te.HP_Peak, p)[1]
        return f"{name} & {wape(p):.1f} & {np.median(np.asarray(p) / A):.2f} & {r2:.3f} \\\\"
    print(f'transferred-SF WAPE {wape(p_sf):.1f}% | oracle WAPE {wape(p_or):.1f}%')
    tex = r"""\begin{table}[t]
\centering
\caption{Installed-capacity accuracy on the held-out substations for two estimators}
\label{tab:capacity}
\begin{tabular}{lccc}
\toprule
estimator & WAPE (\%) & median ratio & $R^2$ \\
\midrule
""" + line(r"Eq.~\eqref{eq:capacity}, transferred SF", p_sf) + "\n" \
        + line("oracle (own SF)", p_or) + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_capacity.tex', 'w').write(tex)
    print('wrote tab_capacity.tex')


# ===========================================================================
# Section 4 -- flexibility
# ===========================================================================
def fig_flex_schedule():
    """fig_flex_schedule: schematic of the flexibility formulation."""
    hf.use_style()
    Pmax, base, af = 1.0, 0.4, 0.4
    RED, BLU = hf.C_HP, hf.C_CH
    fig, ax = plt.subplots(figsize=(hf.COL2, 2.9))
    ax.axhline(Pmax, color='0.6', lw=0.8, zorder=1)
    ax.axhline(base, color='0.35', lw=0.9, ls=(0, (4, 2)), zorder=2)
    xs, ys = [], []
    for k in range(3):
        xs += [k, k, k + af, k + af]; ys += [0, Pmax, Pmax, 0]
    xs += [3]; ys += [0]
    ax.step(xs, ys, where='post', color=RED, lw=1.7, zorder=6)
    ax.fill_between([0, 1], 0, base, color='0.55', alpha=.22, lw=0)
    ax.annotate('$E_{\\mathrm{old}}$ (before flex)', (0.7, base / 2), ha='center', va='center', fontsize=8, color='0.25')
    ax.fill_between([1, 1 + af], 0, Pmax, color=RED, alpha=.16, lw=0)
    ax.annotate('$E_{\\mathrm{new}}$ (after flex)', (1 + af / 2, 1.16), ha='center', va='bottom', fontsize=8, color=RED)
    ax.plot([1 + af / 2, 1 + af / 2], [Pmax, 1.15], color=RED, lw=0.6)
    ax.fill_between([2, 2 + af], base, Pmax, color=RED, alpha=.16, lw=0)
    ax.fill_between([2 + af, 3], 0, base, color=BLU, alpha=.20, lw=0)
    ax.annotate('$E_{\\mathrm{flex}}^{\\uparrow}$', (2 + af / 2, (base + Pmax) / 2), ha='center', va='center', fontsize=9, color=RED)
    ax.annotate('$E_{\\mathrm{flex}}^{\\downarrow}$', (2 + af + (1 - af) / 2, base / 2), ha='center', va='center', fontsize=9, color='#1f6f78')

    def bracket(x0, x1, y, label):
        ax.annotate('', (x0, y), (x1, y), arrowprops=dict(arrowstyle='<->', lw=0.9, color='0.3'))
        ax.text((x0 + x1) / 2, y + 0.03, label, ha='center', va='bottom', fontsize=9, color='0.2')
    bracket(2, 3, 1.24, '$\\Delta t$')
    bracket(2, 2 + af, 1.12, '$\\alpha_F$')
    ax.vlines([2, 2 + af], Pmax, 1.12, color='0.6', lw=0.5, ls=(0, (2, 2)), zorder=1)
    ax.annotate('$P_{\\mathrm{ETL}}^{\\max}$', (0.02, Pmax), xytext=(2, -10), textcoords='offset points', fontsize=8, color='0.3')
    ax.annotate('baseline $\\bar P_{\\mathrm{ETL}}(T)$', (1.7, base), xytext=(0, 4),
                textcoords='offset points', ha='center', fontsize=8, color='0.25')
    ax.set_xlim(0, 3); ax.set_ylim(0, 1.36)
    ax.set_xticks([]); ax.set_yticks([0, base, Pmax]); ax.set_yticklabels(['0', '', ''])
    ax.set_xlabel('time'); ax.set_ylabel('ETL power')
    fig.tight_layout()
    hf.save(fig, 'fig_flex_schedule')
    print('saved -> fig_flex_schedule')


def flex_figures():
    """fig_flex_ratio, fig_flex_season (+ fig_flex_klo_est_act, fig_flex_distribution,
    fig_flex_wpuq_est_act) from the flexibility sensitivity analysis."""
    import matplotlib.dates as mdates
    import hp_pools as hpp
    from hp_capacity import robust_series_peak
    hf.use_style()
    SW = dict(base=0.027, slope=0.0161, thr=16.4)

    def sfcurve(T, thr=SW['thr']):
        return np.clip(SW['base'] + SW['slope'] * np.maximum(0.0, thr - np.asarray(T)), 0, 1)

    def coef(sf, cap):
        sf = np.asarray(sf); return float(np.sum(sf * (1 - sf)) * cap)
    DTS = np.array([1, 2, 4, 6, 8, 12, 24])

    # (a) KLO population
    p = hpp.build_pool_combined(verbose=False)
    idx = p['index']; w = p['weather_of']
    hh = p['households']; orow = {h: i for i, h in enumerate(hh)}
    klo = [h for h in p['hp_households'] if w.get(h) == 'KLO']
    hrow = [p['hp_households'].index(h) for h in klo]
    Pmax = float(sum(robust_series_peak(p['hp_mat'][r]) for r in hrow))
    Td = pd.Series(p['temperature']['KLO'], index=idx).resample('D').mean()
    sf_meas = (pd.Series(p['hp_mat'][hrow].sum(axis=0), index=idx).resample('D').mean() / Pmax).clip(0, 1)
    net = pd.Series((p['hp_mat'][hrow] + p['other_mat'][[orow[h] for h in klo]]).sum(axis=0), index=idx).resample('D').mean()
    a = pd.DataFrame({'T': Td, 'sf': sf_meas, 'net': net}).dropna()
    nb, ns, nt, nr2 = fit_hockey_stick(a['T'].to_numpy(), a['net'].to_numpy(), T_BALANCE_BOUNDS)
    delta = ns * max(0.0, nt - a['T'].min())
    cap_est = delta / float(sfcurve(a['T'].min()))
    sf_est = sfcurve(a['T'].to_numpy())
    flex_act = a['sf'].to_numpy() * (1 - a['sf'].to_numpy()) * Pmax
    flex_est = sf_est * (1 - sf_est) * cap_est
    print(f'(a) KLO: P_max true {Pmax:.0f} kW, est {cap_est:.0f} kW; net-load R2 {nr2:.2f}')

    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    doy = np.arange(len(a))
    ax[0].plot(doy, flex_act * 4, color='0.5', lw=0.9, label='actual (measured SF)')
    ax[0].plot(doy, flex_est * 4, color=hf.C_HP, lw=1.1, label='estimated (transferred SF)')
    ax[0].set(xlabel='day of year', ylabel='daily flexible energy (kWh)', title='$\\Delta t = 4$ h')
    ax[0].legend(fontsize=6.5, loc='upper right')
    ax[1].plot(DTS, flex_act.sum() / 1000 * DTS, color='0.5', lw=1.4, marker='o', ms=3, label='actual')
    ax[1].plot(DTS, flex_est.sum() / 1000 * DTS, color=hf.C_HP, lw=1.4, marker='s', ms=3, label='estimated')
    ax[1].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flexible energy (MWh)')
    ax[1].legend(fontsize=7, loc='upper left')
    fig.tight_layout(); hf.save(fig, 'fig_flex_klo_est_act')

    # (b) distribution across 1000 substations
    subs = U.build_frames(U.pickle_load('data/design_factorial.pkl'))
    fr = U.fits_frame(U.pickle_load('data/design_factorial.pkl')).set_index('sid')
    sf_ref = float(fr.SF_cold.median())
    rows = []
    for s in subs:
        sid = s['sid']
        if sid not in fr.index:
            continue
        C_act = coef(np.clip(s['SF'], 0, 1), s['HP_Peak'])
        cap_e = float(fr.loc[sid, 'delta'] / sf_ref) if fr.loc[sid, 'delta'] > 0 else np.nan
        C_est = coef(sfcurve(s['T']), cap_e)
        rows.append(dict(N_hp=int(round(s['hp_ratio'] * s['N_total'])), C_act=C_act, C_est=C_est,
                         ratio=C_est / C_act if C_act > 0 else np.nan))
    b = pd.DataFrame(rows).dropna()
    print(f'(b) {len(b)} substations; est/actual annual ratio median {b.ratio.median():.2f}')

    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    q = {dt: (b.C_act * dt / 1000) for dt in DTS}
    med = [q[dt].median() for dt in DTS]
    lo = [q[dt].quantile(.25) for dt in DTS]; hi = [q[dt].quantile(.75) for dt in DTS]
    ax[0].fill_between(DTS, lo, hi, color=hf.C_CH, alpha=.25, lw=0, label='IQR')
    ax[0].plot(DTS, med, color=hf.C_CH, lw=1.6, marker='o', ms=3, label='median')
    ax[0].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flex per substation (MWh)')
    ax[0].legend(fontsize=7, loc='upper left')
    ax[1].hist(b.ratio.clip(0, 2.5), bins=40, color=hf.C_HP, alpha=.8, edgecolor='none')
    ax[1].axvline(1, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax[1].axvline(b.ratio.median(), color=hf.C_CH, lw=1.4, label=f'median {b.ratio.median():.2f}')
    ax[1].set(xlabel='estimated / actual annual flex', ylabel='substations')
    ax[1].legend(fontsize=7, loc='upper right')
    fig.tight_layout(); hf.save(fig, 'fig_flex_distribution')

    # paper figures: fig_flex_season and fig_flex_ratio
    DT_REF = 4
    fig, ax = plt.subplots(figsize=(hf.COL1, 2.7))
    ax.plot(a.index, flex_act * DT_REF, color='0.5', lw=0.9, label='actual')
    ax.plot(a.index, flex_est * DT_REF, color=hf.C_HP, lw=1.0, label='estimated')
    ax.set(xlabel='month', ylabel=f'daily flexible energy (kWh), $\\Delta t = {DT_REF}$ h')
    ax.xaxis.set_major_locator(mdates.MonthLocator((1, 4, 7, 10)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.legend(fontsize=7, loc='upper right')
    fig.tight_layout(); hf.save(fig, 'fig_flex_season')

    fig, ax = plt.subplots(figsize=(hf.COL1, 2.7))
    ax.hist(b.ratio.clip(0, 2.5), bins=40, color=hf.C_CH, alpha=.8, edgecolor='none')
    ax.axvline(1, color='0.4', lw=0.8, ls=(0, (3, 3)))
    ax.axvline(b.ratio.median(), color=hf.C_HP, lw=1.6, label=f'median {b.ratio.median():.2f}')
    ax.set(xlabel='estimated / actual annual flex', ylabel='substations')
    ax.legend(fontsize=7.5, loc='upper right')
    fig.tight_layout(); hf.save(fig, 'fig_flex_ratio')

    # (c) WPUQ real feeder
    d = pd.read_csv('data/wpuq_real_feeder_sf.csv', index_col=0, parse_dates=True)
    CAP_TRUE = 238.5
    Tw, sfw, netw = d['Temp'].to_numpy(), np.clip(d['SF'].to_numpy(), 0, 1), d['net'].to_numpy()
    nb, ns, nt, _ = fit_hockey_stick(Tw, netw, T_BALANCE_BOUNDS)
    delta_w = ns * max(0.0, nt - Tw.min())
    cap_w = delta_w / float(sfcurve(Tw.min(), thr=nt))
    sfw_est = sfcurve(Tw, thr=nt)
    flex_act_w = sfw * (1 - sfw) * CAP_TRUE
    flex_est_w = sfw_est * (1 - sfw_est) * cap_w
    print(f'(c) WPUQ feeder: cap true {CAP_TRUE:.0f} kW, est(hybrid) {cap_w:.0f} kW')
    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    doy = np.arange(len(Tw))
    ax[0].plot(doy, flex_act_w * 4, color='0.5', lw=0.9, label='actual (measured SF)')
    ax[0].plot(doy, flex_est_w * 4, color=hf.C_DE, lw=1.1, label='estimated (transferred SF)')
    ax[0].set(xlabel='day of year', ylabel='daily flexible energy (kWh)', title='$\\Delta t = 4$ h')
    ax[0].legend(fontsize=6.5, loc='upper right')
    ax[1].plot(DTS, flex_act_w.sum() / 1000 * DTS, color='0.5', lw=1.4, marker='o', ms=3, label='actual')
    ax[1].plot(DTS, flex_est_w.sum() / 1000 * DTS, color=hf.C_DE, lw=1.4, marker='s', ms=3, label='estimated')
    ax[1].set(xlabel='thermal-inertia window $\\Delta t$ (h)', ylabel='annual flexible energy (MWh)')
    ax[1].legend(fontsize=7, loc='upper left')
    fig.tight_layout(); hf.save(fig, 'fig_flex_wpuq_est_act')
    print('saved -> fig_flex_ratio, fig_flex_season (+ klo/distribution/wpuq)')


# ===========================================================================
# Section 5 -- real unseen feeder
# ===========================================================================
def fig_real_feeder():
    """Fig. 11: real WPUQ feeder net-load fit and feeder-own vs transferred SF."""
    d = pd.read_csv('data/wpuq_real_feeder_sf.csv', index_col=0, parse_dates=True)
    T = d['Temp'].to_numpy(); net = d['net'].to_numpy(); sf = d['SF'].to_numpy()
    Tmin = float(np.min(T))
    nb, ns, nt, nr2 = fit_hockey_stick(T, net, T_BALANCE_BOUNDS)
    delta = ns * max(0.0, nt - Tmin)
    st = nt
    _mb = T < st
    ss, sb = np.polyfit(st - T[_mb], sf[_mb], 1)
    sr2 = float(1 - np.sum((sf[_mb] - (sb + ss * (st - T[_mb]))) ** 2) /
                np.sum((sf[_mb] - sf[_mb].mean()) ** 2))
    sf_own = float(np.clip(sb + ss * max(0.0, st - Tmin), 0, 1))
    sf_hybrid = float(np.clip(SWISS_SF['base'] + SWISS_SF['slope'] * max(0.0, nt - Tmin), 0, 1))
    for name, sfv in [('default (Swiss slope, net-load T_h)', sf_hybrid), ('oracle (own SF)', sf_own)]:
        pred = delta / sfv
        print(f'  {name:36s}: P_max = {pred:5.0f} kW   error {(pred - WPUQ_TRUE_KW) / WPUQ_TRUE_KW * 100:+5.1f}%')

    hf.use_style()
    Tg = np.linspace(Tmin, nt, 150)
    Tmax = float(T.max())
    gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
    fig, ax = plt.subplots(1, 2, figsize=(hf.COL2, 3.0))
    ax[0].scatter(T, net, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily net load')
    ax[0].plot(Tg, nb + ns * (nt - Tg), color=hf.C_DE, lw=1.9, label=r'$\hat{P}_{\mathrm{net}}(T)$')
    ax[0].plot([nt, Tmax], [nb, nb], color='0.35', lw=1.9, zorder=4)
    ax[0].set(xlabel='daily mean temperature (°C)', ylabel='feeder net load (kW)')
    y0b = ax[0].get_ylim()[0]
    ax[0].vlines(nt, y0b, 40, **gth); ax[0].set_ylim(bottom=y0b)
    ax[0].annotate('$T_h$', xy=(nt, 40), xytext=(0, 3), textcoords='offset points',
                   ha='center', va='bottom', fontsize=9, color='0.3')
    leg0 = ax[0].legend(fontsize=7, loc='upper right')
    fig.canvas.draw()
    lx0 = leg0.get_window_extent().transformed(ax[0].transAxes.inverted()).x0
    ax[0].text(lx0, 0.72, f'$R^2$ {nr2:.2f}', transform=ax[0].transAxes,
               ha='left', va='center', fontsize=7, color='0.3')
    ax[1].scatter(T, sf, s=6, color='0.7', alpha=.4, edgecolor='none', label='daily feeder SF')
    ax[1].plot(Tg, np.clip(sb + ss * (nt - Tg), 0, 1), color=hf.C_DE, lw=1.9, label='feeder own SF')
    ax[1].plot(Tg, np.clip(SWISS_SF['base'] + SWISS_SF['slope'] * (nt - Tg), 0, 1),
               color=hf.C_HP, lw=2.1, label='transferred')
    xl1 = ax[1].get_xlim()
    ax[1].axvspan(nt, xl1[1], color='0.5', alpha=.12, lw=0, zorder=0)
    ax[1].set_xlim(xl1)
    ax[1].axvline(Tmin, color='0.5', lw=0.8, ls=(0, (2, 2)))
    ax[1].plot([Tmin, Tmin], [sf_own, sf_hybrid], color=hf.C_HP, lw=0, marker='o', ms=2.5)
    ax[1].vlines(nt, 0, 0.20, **gth)
    ax[1].annotate('$T_h$', xy=(nt, 0.20), xytext=(0, 3), textcoords='offset points',
                   ha='center', va='bottom', fontsize=9, color='0.3')
    ax[1].set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
    ax[1].legend(fontsize=7, loc='upper right')
    fig.tight_layout()
    hf.save(fig, 'fig_real_feeder')
    print('saved -> fig_real_feeder')


def tab_feeder_sweep():
    """tab_feeder_sweep: use-case error as HP circuits are removed from the real feeder."""
    import hp_pools as hpp
    from hp_capacity import robust_series_peak
    SWISS = SWISS_SF
    p = hpp.build_pool_wpuq(verbose=False)
    idx = p['index']; hp_mat, other_mat = p['hp_mat'], p['other_mat']
    n_house = hp_mat.shape[0]
    rp = np.array([robust_series_peak(hp_mat[i]) for i in range(n_house)])
    base_all = other_mat.sum(axis=0)
    temp = pd.Series(p['temperature']['WPUQ'], index=idx)
    Td = temp.resample('D').mean(); Tmin = float(Td.min())
    dt = 0.25
    sf_swiss_tmin = np.clip(SWISS['base'] + SWISS['slope'] * max(0, SWISS['t_thr'] - Tmin), 0, 1)

    def fit_daily(series):
        y = pd.Series(series, index=idx).resample('D').mean()
        dd = pd.DataFrame({'T': Td, 'y': y}).dropna()
        return fit_hockey_stick(dd['T'].to_numpy(), dd['y'].to_numpy(), T_BALANCE_BOUNDS)

    rng = np.random.default_rng(0)
    grid = [5, 10, 15, 20, 25, 30, 37]
    rows = []
    for nhp in grid:
        combos = [np.arange(n_house)] if nhp == n_house else \
                 [rng.choice(n_house, nhp, replace=False) for _ in range(200)]
        for S in combos:
            cap_true = rp[S].sum()
            net = base_all + hp_mat[S].sum(axis=0)
            hp_sum = hp_mat[S].sum(axis=0)
            nb, ns, nt, nr2 = fit_daily(net)
            delta = ns * max(0.0, nt - Tmin)
            sfser = hp_sum / cap_true
            sb, sslope, st, sr2 = fit_daily(sfser)
            sf_own = np.clip(sb + sslope * max(0.0, st - Tmin), 0, 1)
            sf_hyb = np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, nt - Tmin), 0, 1)
            cap_dep, cap_hyb, cap_or = delta / sf_swiss_tmin, delta / sf_hyb, delta / sf_own
            e_est = float((ns * (nt - Td).clip(lower=0) * 24).sum())
            e_act = float(hp_sum.sum() * dt)
            rows.append(dict(N_hp=nhp, cap_true=cap_true, net_r2=nr2,
                             e_cap_hyb=(cap_hyb - cap_true) / cap_true * 100,
                             e_energy=(e_est - e_act) / e_act * 100))
    dfr = pd.DataFrame(rows)
    g = dfr.groupby('N_hp').median(numeric_only=True)

    def row(nhp):
        r = g.loc[nhp]
        return f"{nhp} & \\chg{{{r['e_cap_hyb']:+.0f}}} & {r['e_energy']:+.0f} \\\\"
    body = "\n".join(row(k) for k in grid)
    tex = r"""\begin{table}[t]
\centering
\caption{Use-case estimates on the real feeder as HP circuits are removed, at a fixed 37-house base. Signed median error over 200 random subsets per count}
\label{tab:feeder-sweep}
\begin{tabular}{rcc}
\toprule
$N_{hp}$ & \chg{capacity (\%)} & energy (\%) \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}"""
    open('paper/tables/tab_feeder_sweep.tex', 'w').write(tex)
    print('wrote tab_feeder_sweep.tex')


# ===========================================================================
# Section 6 -- cross-dataset characterization
# ===========================================================================
def build_cross_table(repull=False):
    """Refit the cross-dataset table from scratchpad/cross_frames.pkl.

    ``repull=True`` re-pulls the three ResStock ASHP rows from the NREL S3
    bucket with the electric backup element folded into ETL heating (compressor
    + heating_hp_bkup), then refits. ``repull=False`` (default) just refits from
    the cached frames. Writes scratchpad/cross_table.csv.
    """
    cache = 'scratchpad/cross_frames.pkl'
    INPUTS = U.pickle_load(cache)
    if repull:
        import s3fs
        import pyarrow.parquet as pq
        from concurrent.futures import ThreadPoolExecutor
        fs = s3fs.S3FileSystem(anon=True)
        R2 = ("oedi-data-lake/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/"
              "2024/resstock_amy2018_release_2")
        HTTP = "https://oedi-data-lake.s3.amazonaws.com/" + R2.split('/', 1)[1]
        HC = 'out.electricity.heating.energy_consumption'
        BK = 'out.electricity.heating_hp_bkup.energy_consumption'
        CC = 'out.electricity.cooling.energy_consumption'
        TC = 'out.electricity.total.energy_consumption'
        meta = pd.read_parquet('scratchpad/resstock_meta_sfd.parquet'); UP = 3

        def read_one(bid, st):
            try:
                t = pq.read_table(fs.open(f"{R2}/timeseries_individual_buildings/by_state/upgrade={UP}/state={st}/{bid}-{UP}.parquet"),
                                  columns=['timestamp', HC, BK, CC, TC]).to_pandas(ignore_metadata=True)
            except Exception:
                return None
            t['timestamp'] = pd.to_datetime(t['timestamp']); return t.set_index('timestamp')

        def wx(gj, st):
            w = pd.read_csv(f"{HTTP}/weather/state={st}/{gj}_2018.csv", parse_dates=['date_time'])
            return w.set_index('date_time')['Dry Bulb Temperature [°C]'].resample('D').mean()

        for gj, st, lab in [('G2700530', 'MN', 'ResStock ASHP -- Hennepin MN (cold)'),
                            ('G5300330', 'WA', 'ResStock ASHP -- King WA (mild)'),
                            ('G0400130', 'AZ', 'ResStock ASHP -- Maricopa AZ (hot)')]:
            bids = list(np.random.default_rng(0).choice(meta[meta['in.county'] == gj]['bldg_id'].tolist(), 150, replace=False))
            heat = cool = tot = None; hpk = cpk = 0.0
            with ThreadPoolExecutor(max_workers=16) as ex:
                for r in ex.map(lambda b: read_one(b, st), bids):
                    if r is None:
                        continue
                    h = (r[HC] + r[BK]) * 4
                    c, s2 = r[CC] * 4, r[TC] * 4
                    heat = h if heat is None else heat.add(h, fill_value=0)
                    cool = c if cool is None else cool.add(c, fill_value=0)
                    tot = s2 if tot is None else tot.add(s2, fill_value=0)
                    hpk += float(h.max()); cpk += float(c.max())
            Td = wx(gj, st)
            dd = pd.DataFrame({'T': Td, 'net': tot.resample('D').mean(),
                               'heat': heat.resample('D').mean(), 'cool': cool.resample('D').mean()}).dropna()
            INPUTS[lab] = dict(n=150, T=dd['T'].to_numpy(), net=dd['net'].to_numpy(),
                               heat=dd['heat'].to_numpy(), cool=dd['cool'].to_numpy(), cap_h=hpk, cap_c=cpk)
            print(lab, 'done: cap_h', round(hpk), 'cap_c', round(cpk), flush=True)
        pickle.dump(INPUTS, open(cache, 'wb'))

    rows = [U.fit_row(lab, v['n'], v['T'], v['net'], v['heat'], v['cool'], v['cap_h'], v['cap_c'])
            for lab, v in INPUTS.items()]
    pd.DataFrame(rows).to_csv('scratchpad/cross_table.csv', index=False)
    print('wrote scratchpad/cross_table.csv')


def neea_fit():
    """Refit the NEEA WA/OR aggregates -> scratchpad/neea_rows.csv, neea_frames.pkl."""
    p = pd.read_parquet('data/neea_power_2023.parquet')
    site_state = p.groupby('ee_site_id')['state'].first()
    hp = p[p['End Use'] == 'Ductless Heatpump']; mains = p[p['End Use'] == 'Mains']
    hp_int = hp.groupby(['ee_site_id', 'MIN_T_l'], as_index=False)['power'].sum()
    mn_int = mains.groupby(['ee_site_id', 'MIN_T_l'], as_index=False)['power'].sum()
    hp_int['date'] = hp_int['MIN_T_l'].dt.floor('D'); mn_int['date'] = mn_int['MIN_T_l'].dt.floor('D')
    hp_peak = hp_int.groupby('ee_site_id')['power'].quantile(0.99)
    hp_day = hp_int.groupby(['ee_site_id', 'date'])['power'].mean().rename('hp')
    mn_day = mn_int.groupby(['ee_site_id', 'date'])['power'].mean().rename('net')
    cov = mn_day.groupby(level=0).size()
    t = pd.read_parquet('data/neea_temp_2023.parquet')
    t['date'] = t['MIN_T_l'].dt.floor('D'); t['C'] = (t['temp'] - 32) * 5.0 / 9.0
    t['state'] = t['ee_site_id'].map(site_state)
    reg_temp = t.groupby(['ee_site_id', 'date'])['C'].mean().groupby(level=1).mean()
    FR = {}; rows = []
    for st in ['WA', 'OR']:
        ssites = set(site_state[site_state == st].index)
        sites = sorted((set(hp_day.index.get_level_values(0)) & set(cov[cov >= 300].index)) & ssites)
        netW = mn_day[mn_day.index.get_level_values(0).isin(sites)].unstack(0)
        hpW = hp_day[hp_day.index.get_level_values(0).isin(sites)].unstack(0)
        keep = netW.notna().sum(axis=1) >= 0.7 * len(sites)
        net_agg = netW[keep].sum(axis=1, min_count=1)
        hp_agg = hpW.reindex(net_agg.index)[net_agg.notna()].sum(axis=1, min_count=1)
        cap = float(hp_peak[hp_peak.index.isin(sites)].sum())
        ts = t[t['state'] == st]
        temp_agg = ts.groupby(['ee_site_id', 'date'])['C'].mean().groupby(level=1).mean()
        if temp_agg.notna().sum() < 200:
            temp_agg = reg_temp
        d = pd.DataFrame({'net': net_agg, 'hp': hp_agg}).join(temp_agg.rename('Tc')).dropna()
        T = d['Tc'].to_numpy(); hpv = d['hp'].to_numpy(); netv = d['net'].to_numpy()
        heat = np.where(T < 15, hpv, 0.0); cool = np.where(T > 20, hpv, 0.0)
        row = U.fit_row(f'NEEA {st} (real HP)', len(sites), T, netv, heat, cool, cap, cap)
        rows.append(row)
        FR[f'NEEA {st} (real HP)'] = dict(n=len(sites), T=T, net=netv, heat=hpv, cool=hpv, cap_h=cap, cap_c=cap)
        print(f'{st}: {len(sites)} homes, {len(d)} days')
    pd.DataFrame(rows).to_csv('scratchpad/neea_rows.csv', index=False)
    pickle.dump(FR, open('scratchpad/neea_frames.pkl', 'wb'))
    print('wrote scratchpad/neea_rows.csv + neea_frames.pkl')


def tab_cross():
    """tab_cross: cross-dataset fit-parameter table from the cached CSVs."""
    df = pd.concat([pd.read_csv('scratchpad/cross_table.csv'),
                    pd.read_csv('scratchpad/neea_rows.csv')], ignore_index=True).set_index('label')
    ROW = {
        'German WPuQ (real HP)':               r'Hamelin, DE~\cite{Sch22}',
        'Swiss substation (real HP)':          r'Kloten, CH~\cite{Bru25,Kai26b}',
        'LCL London ASHP (real HP)':           r'London, UK$^\dagger$~\cite{lcl_heatpump}',
        'COFACTOR Norway (real HP)':           r'Oslo, NO~\cite{cofactor}',
        'Austin Pecan St (real)':              r'Austin, TX, US~\cite{pecanstreet}',
        'Carleton Ottawa (real AC)':           r'Ottawa, CA~\cite{carleton}',
        'NEEA WA (real HP)':                   r'WA, US~\cite{neea_eulr}',
        'NEEA OR (real HP)':                   r'OR, US~\cite{neea_eulr}',
        'ResStock ASHP -- Hennepin MN (cold)': r'Hennepin, MN, US~\cite{resstock}',
        'ResStock ASHP -- King WA (mild)':     r'King, WA, US~\cite{resstock}',
        'ResStock ASHP -- Maricopa AZ (hot)':  r'Maricopa, AZ, US~\cite{resstock}',
    }
    TECH = {   # ETL technologies behind the meter for each aggregate
        'German WPuQ (real HP)':               'WSHP',
        'Swiss substation (real HP)':          'ASHP, GSHP',
        'LCL London ASHP (real HP)':           'ASHP',
        'COFACTOR Norway (real HP)':           'GSHP, ER',
        'Austin Pecan St (real)':              'AC, ER',
        'Carleton Ottawa (real AC)':           'AC',
        'NEEA WA (real HP)':                   'DHP',
        'NEEA OR (real HP)':                   'DHP',
        'ResStock ASHP -- Hennepin MN (cold)': 'ASHP, ER',
        'ResStock ASHP -- King WA (mild)':     'ASHP, ER',
        'ResStock ASHP -- Maricopa AZ (hot)':  'ASHP, ER',
    }
    KOPPEN = {   # Koppen-Geiger climate class of each location (verify against your source)
        'German WPuQ (real HP)':               'Cfb',
        'Swiss substation (real HP)':          'Cfb',
        'LCL London ASHP (real HP)':           'Cfb',
        'COFACTOR Norway (real HP)':           'Dfb',
        'Austin Pecan St (real)':              'Cfa',
        'Carleton Ottawa (real AC)':           'Dfb',
        'NEEA WA (real HP)':                   'Csb',
        'NEEA OR (real HP)':                   'Csb',
        'ResStock ASHP -- Hennepin MN (cold)': 'Dfa',
        'ResStock ASHP -- King WA (mild)':     'Csb',
        'ResStock ASHP -- Maricopa AZ (hot)':  'BWh',
    }
    order = [k for k in ROW if k in df.index]
    COLS = [('$n$', 'n', '.0f'),
            (r'$P_{\mathrm{base}}$', 'P_base', '.0f'), ('$s_h$', 's_h', '.1f'), ('$T_h$', 'T_h', '.1f'), ('$R^2_h$', 'R2_net_h', '.2f'),
            ('$s_c$', 's_c', '.1f'), ('$T_c$', 'T_c', '.1f'), ('$R^2_c$', 'R2_net_c', '.2f'),
            ('$b_h$', 'b_h', '.3f'), ('$m_h$', 'm_h', '.3f'), (r'SF$_\mathrm{c}$', 'SF_cold', '.2f'), ('$R^2_h$', 'R2_SFh', '.2f'),
            ('$b_c$', 'b_c', '.3f'), ('$m_c$', 'm_c', '.3f'), (r'SF$_\mathrm{h}$', 'SF_hot', '.2f'), ('$R^2_c$', 'R2_SFc', '.2f')]

    # Two-slope coldest-day SF, reported in parentheses where a single arm underfits
    # the deepest cold. Hennepin: air-source COP fall-off + electric backup add a
    # second, steeper slope at a knee near -13 C, lifting SF_cold 0.45 -> 0.74.
    KNEE_SFC = {'ResStock ASHP -- Hennepin MN (cold)': 0.74}

    def cell(v, fmt):
        return '--' if (v is None or (isinstance(v, float) and not np.isfinite(v))) else format(v, fmt)

    def cell_at(lab, c, fmt):
        s = cell(df.loc[lab, c], fmt)
        if c == 'SF_cold' and lab in KNEE_SFC:
            s = s + r'\,(' + format(KNEE_SFC[lab], '.2f') + ')'
        return s
    rest = COLS[1:]
    body = '\n'.join(ROW[lab] + ' & ' + TECH[lab] + ' & ' + cell(df.loc[lab, 'n'], '.0f') + ' & ' + KOPPEN[lab]
                     + ' & ' + ' & '.join(cell_at(lab, c, f) for _, c, f in rest) + r' \\'
                     for lab in order)
    head2 = 'dataset & ETL tech & $n$ & Climate & ' + ' & '.join(h for h, _, _ in rest) + r' \\'
    tex = (
        r"\begin{table*}[t]" "\n" r"\centering" "\n"
        r"\caption{Net-load and SF fit parameters for one aggregate per dataset. $n$ is the number of aggregated consumers; Climate is the K{\"o}ppen--Geiger class~\cite{beck2018koppen}; under the net-load fit, $R^2_h$ and $R^2_c$ score the heating and cooling arms separately, each on the days of its own regime; $s_h,s_c$ [kW/$^\circ$C]; $T_h,T_c$ [$^\circ$C]; $m_h,m_c$ [$^\circ$C$^{-1}$]; SF$_\mathrm{c}$/SF$_\mathrm{h}$ the coldest-/hottest-day SF, a parenthetical SF$_\mathrm{c}$ giving the two-slope value where a single arm underfits the deepest cold (Hennepin, whose air-source backup adds a second slope near $-13\,^\circ$C). ETL-technology codes: ASHP air-source heat pump; GSHP ground-source heat pump; WSHP water-source heat pump; DHP ductless (mini-split) heat pump; AC air conditioning; ER electric resistance heating. $^\dagger$The LCL London aggregate is submetered heat-pump load only (6 homes, no other household load), so its net-load fit coincides with the HP load and $P_{\mathrm{base}}$ is the summer standby/hot-water floor; the small aggregation raises its SF slope relative to the larger pools.}" "\n"
        r"\label{tab:cross}" "\n" r"% \scriptsize" "\n" r"\setlength{\tabcolsep}{4pt}" "\n"
        r"\begin{tabular}{ll" + "c" * (len(COLS) + 1) + "}\n" r"\toprule" "\n"
        r" & & & & \multicolumn{7}{c}{Net-load fit $\hat{P}_{\mathrm{net}}(T)$} & \multicolumn{8}{c}{SF fit $\hat{\mathrm{SF}}(T)$}\\" "\n"
        r"\cmidrule(lr){5-11}\cmidrule(lr){12-19}" "\n"
        + head2 + "\n" r"\midrule" "\n" + body + "\n" r"\bottomrule" "\n"
        r"\end{tabular}" "\n" r"\end{table*}" "\n")
    open('paper/tables/tab_cross.tex', 'w').write(tex)
    print('wrote tab_cross.tex')


def fig_cross_montage(knee_thresh=0.02):
    """fig_cross_montage: per-dataset net-load bathtub (left) and SF (right).

    Where a single linear arm is convex, a piecewise arm with one extra threshold
    (a second knee) is overlaid dashed on that arm, but only if it raises the
    arm's R^2 by at least ``knee_thresh`` (default 0.02). Mostly this fires on the
    cold-climate ResStock heating arm (Hennepin), where electric backup + COP
    fall-off make the load convex."""
    from scipy.optimize import curve_fit

    def knee_fit(x, y, thr, side):
        """Fit a 1-knee and a 2-knee arm on the below/above-threshold subset;
        return the extra-knee predictor and both R^2 if the fit succeeds."""
        m = (x < thr) if side == 'h' else (x > thr)
        if not np.isfinite(thr) or m.sum() < 25:
            return None
        xs_, ys_ = x[m], y[m]
        ss = float(np.sum((ys_ - ys_.mean()) ** 2))
        if ss <= 0:
            return None
        hinge = (thr - xs_) if side == 'h' else (xs_ - thr)
        m1, b1 = np.polyfit(hinge, ys_, 1)
        r1 = 1 - np.sum((ys_ - (b1 + m1 * hinge)) ** 2) / ss

        def f(T, b, s1, s2, tk):
            h1 = np.maximum(0, thr - T) if side == 'h' else np.maximum(0, T - thr)
            h2 = np.maximum(0, tk - T) if side == 'h' else np.maximum(0, T - tk)
            return b + s1 * h1 + s2 * h2
        tk_lo, tk_hi = (xs_.min() + 1, thr - 1) if side == 'h' else (thr + 1, xs_.max() - 1)
        if tk_hi <= tk_lo:
            return None
        try:
            p, _ = curve_fit(f, xs_, ys_, p0=[np.median(ys_), max(m1, .1), max(m1, .1), (tk_lo + tk_hi) / 2],
                             bounds=([-np.inf, 0, 0, tk_lo], [np.inf, np.inf, np.inf, tk_hi]), maxfev=20000)
        except Exception:
            return None
        r2 = 1 - np.sum((ys_ - f(xs_, *p)) ** 2) / ss
        return dict(r1=r1, r2=r2, f=(lambda T: f(T, *p)))

    hf.use_style()
    FR = U.pickle_load('scratchpad/cross_frames.pkl')
    FR.update(U.pickle_load('scratchpad/neea_frames.pkl'))
    ORDER = [('German WPuQ (real HP)', 'Hamelin, DE'), ('Swiss substation (real HP)', 'Kloten, CH'),
             ('COFACTOR Norway (real HP)', 'Oslo, NO'),
             ('Austin Pecan St (real)', 'Austin, TX'), ('Carleton Ottawa (real AC)', 'Ottawa, CA'),
             ('NEEA WA (real HP)', 'WA, US'),
             ('NEEA OR (real HP)', 'OR, US'), ('ResStock ASHP -- Hennepin MN (cold)', 'Hennepin, MN'),
             ('ResStock ASHP -- King WA (mild)', 'King, WA'), ('ResStock ASHP -- Maricopa AZ (hot)', 'Maricopa, AZ')]
    ORDER = [(k, t) for k, t in ORDER if k in FR]
    nrow = len(ORDER)
    # common temperature axis across every panel, so the arms line up
    allT = np.concatenate([np.asarray(FR[k]['T'], float) for k, _ in ORDER])
    Tlo, Thi = float(np.floor(np.nanmin(allT))) - 1, float(np.ceil(np.nanmax(allT))) + 1
    fig, axes = plt.subplots(nrow, 2, figsize=(5.4, 1.55 * nrow), sharex=True)
    for i, (k, title) in enumerate(ORDER):
        v = FR[k]
        T, net = np.asarray(v['T']), np.asarray(v['net'])
        heat, cool = np.asarray(v['heat']), np.asarray(v['cool'])
        r = U.fit_row(k, v['n'], T, net, heat, cool, v['cap_h'], v['cap_c'])
        th, tc, base, sh, sc = r['T_h'], r['T_c'], r['P_base'], r['s_h'], r['s_c']
        axb, axs = axes[i, 0], axes[i, 1]
        for ax in (axb, axs):
            ax.grid(False); ax.tick_params(labelsize=6); ax.set_xlim(Tlo, Thi)
        xs = np.linspace(T.min(), T.max(), 200)
        axb.scatter(T, net, s=3, color='0.75', alpha=.4, edgecolor='none')
        lo = th if np.isfinite(th) else T.min(); hi = tc if np.isfinite(tc) else T.max()
        axb.plot([lo, hi], [base, base], color='0.3', lw=1.5, zorder=4)
        net_r2_note = ''
        if np.isfinite(th):
            xa = xs[xs <= th]; axb.plot(xa, base + sh * (th - xa), color=hf.C_HP, lw=1.6, zorder=4)
        if np.isfinite(tc):
            xd = xs[xs >= tc]; axb.plot(xd, base + sc * (xd - tc), color=hf.C_CH, lw=1.6, zorder=4)
        # --- net-load extra-knee overlay where an arm is convex ---
        for side, thr, col in [('h', th, hf.C_HP), ('c', tc, hf.C_CH)]:
            kk = knee_fit(T, net, thr, side)
            if kk and kk['r2'] - kk['r1'] >= knee_thresh:
                xr = xs[xs <= thr] if side == 'h' else xs[xs >= thr]
                axb.plot(xr, kk['f'](xr), color=col, lw=1.1, ls=(0, (3, 2)), zorder=6)
                net_r2_note = f"$\\to${kk['r2']:.2f}"
        axb.set_ylabel(title, fontsize=7.5)
        axb.text(0.04, 0.9, f"$R^2$ {r['R2']:.2f}{net_r2_note}", transform=axb.transAxes, fontsize=6, color='0.4', va='top')
        if np.isfinite(th) and v['cap_h']:
            mm = T < th
            axs.scatter(T[mm], np.clip(heat[mm] / v['cap_h'], 0, 1), s=3, color=hf.C_HP, alpha=.3, edgecolor='none')
            xa = xs[xs <= th]; axs.plot(xa, np.clip(r['b_h'] + r['m_h'] * (th - xa), 0, 1), color=hf.C_HP, lw=1.6, zorder=4)
            ks = knee_fit(T, np.clip(heat / v['cap_h'], 0, 1), th, 'h')
            if ks and ks['r2'] - ks['r1'] >= knee_thresh:
                xa = xs[xs <= th]; axs.plot(xa, np.clip(ks['f'](xa), 0, 1), color=hf.C_HP, lw=1.1, ls=(0, (3, 2)), zorder=6)
                axs.text(0.04, 0.9, f"$R^2$ {r['R2_SFh']:.2f}$\\to${ks['r2']:.2f}", transform=axs.transAxes, fontsize=6, color='0.4', va='top')
        if np.isfinite(tc) and v['cap_c']:
            mm = T > tc
            axs.scatter(T[mm], np.clip(cool[mm] / v['cap_c'], 0, 1), s=3, color=hf.C_CH, alpha=.3, edgecolor='none')
            xd = xs[xs >= tc]; axs.plot(xd, np.clip(r['b_c'] + r['m_c'] * (xd - tc), 0, 1), color=hf.C_CH, lw=1.6, zorder=4)
            ks = knee_fit(T, np.clip(cool / v['cap_c'], 0, 1), tc, 'c')
            if ks and ks['r2'] - ks['r1'] >= knee_thresh:
                xd = xs[xs >= tc]; axs.plot(xd, np.clip(ks['f'](xd), 0, 1), color=hf.C_CH, lw=1.1, ls=(0, (3, 2)), zorder=6)
        axs.set_ylim(0, 1)
        if i == 0:
            axb.set_title('net load (kW)', fontsize=7.5); axs.set_title('simultaneity factor', fontsize=7.5)
        if i < nrow - 1:
            axb.set_xticklabels([]); axs.set_xticklabels([])
    axes[-1, 0].set_xlabel('daily mean temperature ($^\\circ$C)', fontsize=7)
    axes[-1, 1].set_xlabel('daily mean temperature ($^\\circ$C)', fontsize=7)
    fig.tight_layout(h_pad=0.4, rect=[0, 0.012, 1, 1])
    fig.text(0.5, 0.004, 'dashed: fit with one extra threshold (knee), shown where it raises the '
             'arm $R^2$ by $\\geq$ %.2f' % knee_thresh, ha='center', fontsize=6, color='0.4')
    hf.save(fig, 'fig_cross_montage')
    print('saved -> fig_cross_montage')
