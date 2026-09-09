# -*- coding: utf-8 -*-
"""SF fit quality, invariance and transfer on the balanced factorial design
(1000 substations). Fitted-parameter distributions are taken over all 1000
substations; the transfer error is measured on a held-out half. Emits the
numbers and a compact LaTeX table (tab_sf.tex)."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sf_transfer import build_frames, pooled_curve, predict, pickle_load
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

subs = build_frames(pickle_load('data/design_factorial.pkl'))
for s in subs:
    try:
        b, sl, tt, r2 = fit_hockey_stick(s['T'], s['SF'], T_BALANCE_BOUNDS)
        s['coldSF'] = float(np.clip(b + sl * max(0.0, tt - s['T'].min()), 0, 1))
        s['slope'] = float(sl); s['self_r2'] = float(r2)
    except Exception:
        s['coldSF'] = s['slope'] = s['self_r2'] = np.nan
    s['N_hp'] = int(round(s['hp_ratio'] * s['N_total']))
subs = [s for s in subs if np.isfinite(s['coldSF'])]
print(f'{len(subs)} substations with usable SF fits')

D = pd.DataFrame([{k: s[k] for k in ('N_hp', 'hp_ratio', 'HP_Peak',
                   'coldSF', 'slope', 'self_r2')} for s in subs])
rho_pen = spearmanr(D.hp_ratio, D.coldSF).statistic
rho_cap = spearmanr(D.HP_Peak, D.coldSF).statistic
rho_pen_sl = spearmanr(D.hp_ratio, D.slope).statistic
print(f'invariance to ETL rate / installed power: '
      f'rho(coldSF,rate)={rho_pen:+.3f} rho(coldSF,power)={rho_cap:+.3f} '
      f'rho(slope,rate)={rho_pen_sl:+.3f}; median R2 {D.self_r2.median():.3f}')

# ---- transfer: substation-level 50/50 split, borrowed vs self ---------------
rng = np.random.default_rng(0)
idx = np.arange(len(subs)); rng.shuffle(idx)
ref = [subs[i] for i in idx[:len(idx)//2]]
tgt = [subs[i] for i in idx[len(idx)//2:]]
curve = pooled_curve(ref)
print(f"reference curve: SF = {curve['base']:.3f} + {curve['slope']:.4f}*max(0,{curve['t_thr']:.1f}-T)")
trows = []
for s in tgt:
    p_tr = np.clip(predict(curve, s['T']), 0, 1)
    try:
        b, sl, tt, _ = fit_hockey_stick(s['T'], s['SF'], T_BALANCE_BOUNDS)
        p_self = np.clip(b + sl * np.maximum(0.0, tt - s['T']), 0, 1)
    except Exception:
        p_self = np.full_like(s['SF'], np.nan)
    # peak (99th-percentile daily) SF: transferred vs true. Installed capacity
    # cancels, so this is the transferred-curve error alone, not a demand error.
    trows.append(dict(N_hp=s['N_hp'], pk_true=np.quantile(s['SF'], .99),
                      pk_tr=np.quantile(p_tr, .99), pk_self=np.quantile(p_self, .99),
                      r2_tr=1 - np.sum((s['SF'] - p_tr) ** 2) / np.sum((s['SF'] - s['SF'].mean()) ** 2)))
T = pd.DataFrame(trows)
def wape(pred, true):  # weighted absolute percentage error, %
    return (pred - true).abs().sum() / true.sum() * 100
print('overall transfer: borrow R2 %.3f, peak-SF WAPE borrow %.1f%% vs self %.1f%%, median ratio %.2f'
      % (T.r2_tr.median(), wape(T.pk_tr, T.pk_true), wape(T.pk_self, T.pk_true),
         (T.pk_tr / T.pk_true).median()))

# ---- per-N_hp summary -------------------------------------------------------
def iqr(x): return x.quantile(.75) - x.quantile(.25)
par = D.groupby('N_hp').agg(r2=('self_r2', 'median'),
                            cold_m=('coldSF', 'median'), cold_i=('coldSF', iqr),
                            slp_m=('slope', 'median'), slp_i=('slope', iqr))
tr = T.groupby('N_hp').apply(lambda x: wape(x.pk_tr, x.pk_true)).rename('ape')
g = par.join(tr)
print('\n--- by N_hp (ape = peak-SF WAPE) ---'); print(g.round(4).to_string())

# ---- LaTeX table ------------------------------------------------------------
def row(nhp, r):
    return (f"{nhp} & {r['r2']:.3f} & {r['cold_m']:.2f}\\,({r['cold_i']:.2f}) & "
            f"{r['slp_m']:.3f}\\,({r['slp_i']:.3f}) & {r['ape']:.1f} \\\\")
body = "\n".join(row(int(n), r) for n, r in g.iterrows())
allr = (f"all & {D.self_r2.median():.3f} & {D.coldSF.median():.2f}\\,({iqr(D.coldSF):.2f}) & "
        f"{D.slope.median():.3f}\\,({iqr(D.slope):.3f}) & {wape(T.pk_tr, T.pk_true):.1f} \\\\")
tex = r"""\begin{table}[t]
\centering
\caption{Per-substation fitted SF parameters and transfer error by number of aggregated HPs $N_{hp}$}
\label{tab:sf}
\begin{tabular}{rcccc}
\toprule
$N_{hp}$ & $R^2$ & SF$_{\mathrm{cold}}$ & $m$ ($^\circ$C$^{-1}$) & peak-SF WAPE (\%) \\
\midrule
""" + body + "\n\\midrule\n" + allr + r"""
\bottomrule
\end{tabular}
\end{table}"""
open('paper/tab_sf.tex', 'w').write(tex)
print('\nwrote paper/tab_sf.tex')
