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

subs = build_frames(pickle_load('data/design_factorial.pkl'))
for s in subs:
    try:
        b, sl, tt, r2 = fit_hockey_stick(s['T'], s['SF'], T_BALANCE_BOUNDS)
        s['coldSF'] = float(np.clip(b + sl * max(0.0, tt - s['T'].min()), 0, 1))
        s['base'] = float(b); s['slope'] = float(sl); s['thr'] = float(tt); s['self_r2'] = float(r2)
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
    p_tr = np.clip(predict(curve, s['T']), 0, 1)
    trows.append(dict(N_hp=s['N_hp'], pk_true=np.quantile(s['SF'], .99), pk_tr=np.quantile(p_tr, .99),
                      r2=1 - np.sum((s['SF'] - p_tr) ** 2) / np.sum((s['SF'] - s['SF'].mean()) ** 2)))
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
    return (f"{nhp} & {r['r2']:.3f} & {r['cold_m']:.2f}\\,({r['cold_i']:.2f}) & "
            f"{r['base_m']:.3f}\\,({r['base_i']:.3f}) & "
            f"{r['slp_m']:.3f}\\,({r['slp_i']:.3f}) & {r['thr_m']:.1f}\\,({r['thr_i']:.1f}) \\\\")
body = "\n".join(row(int(n), r) for n, r in par.iterrows())
allr = (f"all & {D.self_r2.median():.3f} & {D.coldSF.median():.2f}\\,({iqr(D.coldSF):.2f}) & "
        f"{D.base.median():.3f}\\,({iqr(D.base):.3f}) & "
        f"{D.slope.median():.3f}\\,({iqr(D.slope):.3f}) & {D.thr.median():.1f}\\,({iqr(D.thr):.1f}) \\\\")
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
k = rng.choice(len(Tall), size=min(4000, len(Tall)), replace=False)
fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.scatter(Tall[k], SFall[k], s=4, color='0.7', alpha=.3, edgecolor='none', label='training SF')
Tg = np.linspace(Tall.min(), Tall.max(), 200)
ax.plot(Tg, np.clip(predict(curve, Tg), 0, 1), color=hf.C_CH, lw=1.9, label='pooled fit')
Tp = 5.0
ax.annotate(r'$\hat{\mathrm{SF}}(T)$', xy=(Tp, float(np.clip(predict(curve, Tp), 0, 1))),
            xytext=(18, 14), textcoords='offset points', fontsize=9, color=hf.C_CH,
            arrowprops=dict(arrowstyle='-', lw=0.6, color=hf.C_CH))
ax.set(xlabel='daily mean temperature (°C)', ylabel='simultaneity factor SF', ylim=(0, 0.75))
ax.legend(fontsize=7, loc='upper right')
ax.text(0.965, 0.55, f"$R^2$ {curve['r2']:.3f}", transform=ax.transAxes, ha='right', va='center', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_sf_pooled')
print('\nwrote paper/tables/tab_sf.tex, paper/tables/tab_sf_train.tex, figures/fig_sf_pooled')
