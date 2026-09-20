# -*- coding: utf-8 -*-
"""SF fit quality, invariance and transfer on the balanced factorial design
(1000 substations). Table 1 characterises the per-substation fits (training
side). Separately, one SF curve is fitted to the pooled training data: its
total in-sample WAPE is reported in a small table and the curve is plotted.
The held-out transfer error (peak-SF WAPE) is printed for the prose."""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from sf_transfer import build_frames, pooled_curve, predict, pickle_load
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS
import hp_figures as hf

def sf_anchored(T, Y, thr):
    """SF fit with the threshold FIXED at the net-load threshold: b and m from a
    linear fit on the days below it, and R2 scored on those same days."""
    m = T < thr
    if m.sum() < 10:
        return np.nan, np.nan, np.nan
    mm, bb = np.polyfit(thr - T[m], Y[m], 1)      # SF = bb + mm*(thr - T)
    pred = bb + mm * (thr - T[m])
    ss = np.sum((Y[m] - Y[m].mean()) ** 2)
    r2 = 1 - np.sum((Y[m] - pred) ** 2) / ss if ss > 0 else np.nan
    return bb, mm, r2


subs = build_frames(pickle_load('data/design_factorial.pkl'))
for s in subs:
    try:
        T, Y, L = np.asarray(s['T']), np.asarray(s['SF']), np.asarray(s['Load'])
        _, _, tt, _ = fit_hockey_stick(T, L, T_BALANCE_BOUNDS)   # net-load threshold
        b, sl, r2 = sf_anchored(T, Y, tt)                        # SF anchored there
        s['coldSF'] = float(np.clip(b + sl * max(0.0, tt - T.min()), 0, 1))
        s['base'] = float(b); s['slope'] = float(sl); s['thr'] = float(tt)
        s['self_r2'] = float(r2)
    except Exception:
        s['coldSF'] = s['base'] = s['slope'] = s['thr'] = s['self_r2'] = np.nan
    s['N_hp'] = int(round(s['hp_ratio'] * s['N_total']))
subs = [s for s in subs if np.isfinite(s['coldSF'])]
subs50 = [s for s in subs if int(s['N_total']) == 50]   # constant total size for Table 1
print(f'{len(subs)} usable SF fits; {len(subs50)} at N_total=50 (Table 1)')

# Table 1 characterises the fits at a constant size (N_total=50), isolating N_hp;
# the pooled curve and transfer below use the full design.
D = pd.DataFrame([{k: s[k] for k in ('N_hp', 'hp_ratio', 'HP_Peak',
                   'coldSF', 'base', 'slope', 'thr', 'self_r2')} for s in subs50])
print(f'invariance: rho(coldSF,rate)={spearmanr(D.hp_ratio, D.coldSF).statistic:+.3f} '
      f'rho(coldSF,power)={spearmanr(D.HP_Peak, D.coldSF).statistic:+.3f}; '
      f'median R2 {D.self_r2.median():.3f}')

# ---- one SF curve fitted to the pooled TRAINING data ------------------------
rng = np.random.default_rng(0)
idx = np.arange(len(subs)); rng.shuffle(idx)
ref = [subs[i] for i in idx[:len(idx)//2]]        # training / calibration half
tgt = [subs[i] for i in idx[len(idx)//2:]]        # held-out half
curve = pooled_curve(ref)
print(f"pooled training curve: SF = {curve['base']:.3f} + {curve['slope']:.4f}*max(0,{curve['t_thr']:.1f}-T), "
      f"R2 {curve['r2']:.3f}")

# total in-sample WAPE of the pooled curve against the training substations
def wape(pred, true):
    return np.abs(np.asarray(pred) - np.asarray(true)).sum() / np.asarray(true).sum() * 100
wrows = []
for s in ref:
    pred = np.clip(predict(curve, s['T']), 0, 1)
    wrows.append(dict(N_hp=s['N_hp'], num=np.abs(pred - s['SF']).sum(), den=np.sum(s['SF'])))
W = pd.DataFrame(wrows)
train_wape = W.groupby('N_hp').apply(lambda x: x.num.sum() / x.den.sum() * 100)
overall_train = W.num.sum() / W.den.sum() * 100
print('\ntotal training WAPE of pooled curve by N_hp:')
print(train_wape.round(1).to_string(), f'\n  all: {overall_train:.1f}%')

# held-out transfer (peak-SF WAPE) for the prose
trows = []
for s in tgt:
    Ts = np.asarray(s['T']); SFs = np.asarray(s['SF'])
    p_tr = np.clip(predict(curve, Ts), 0, 1)
    mb = Ts < curve['t_thr']                     # below-threshold convention
    r2 = (1 - np.sum((SFs[mb] - p_tr[mb]) ** 2) /
          np.sum((SFs[mb] - SFs[mb].mean()) ** 2)) if mb.sum() >= 10 else np.nan
    trows.append(dict(N_hp=s['N_hp'], pk_true=np.quantile(SFs, .99), pk_tr=np.quantile(p_tr, .99), r2=r2))
T = pd.DataFrame(trows)
pk = T.groupby('N_hp').apply(lambda x: wape(x.pk_tr, x.pk_true))
print(f'\nheld-out transfer: R2 {T.r2.median():.3f}, peak-SF WAPE all {wape(T.pk_tr, T.pk_true):.1f}%; '
      f'by N_hp {pk.round(1).to_dict()}')

# ---- Table 1: per-substation fitted parameters (no transfer column) ---------
def iqr(x): return x.quantile(.75) - x.quantile(.25)
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

# ---- small table: total WAPE of the pooled training curve -------------------
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

# ---- plot: the pooled training curve over the training data -----------------
hf.use_style()
Tall = np.concatenate([s['T'] for s in ref])
SFall = np.concatenate([s['SF'] for s in ref])
# reformulation: threshold fixed (net-load T_h, ~ pooled t_thr), OLS on days below it
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
ax.axvspan(thr, xl[1], color='0.5', alpha=.12, lw=0, zorder=0)     # excluded region above T_h
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
print('\nwrote paper/tables/tab_sf.tex, paper/tables/tab_sf_train.tex, figures/fig_sf_pooled')
