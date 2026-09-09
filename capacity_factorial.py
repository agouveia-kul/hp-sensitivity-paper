# -*- coding: utf-8 -*-
"""Installed-capacity results on the balanced factorial design (design_factorial).

Estimator of Equation (5):  P_max = delta / SF_ref, where
  delta  = Load_slope * (T_balance - T_min)   -- coincident peak from the
           observable net-load hockey stick (numerator, no submetering)
  SF_ref = coldest-day SF transferred from the submetered reference half.

Compared against a through-origin regression benchmark (HP_Peak ~ delta, fitted
on the reference half) and an oracle that divides by each substation's OWN
coldest-day SF (the ceiling reachable only with local submetering)."""
import numpy as np, pandas as pd, pickle
from capacity_two_methods import fits_frame, metrics

RNG = np.random.default_rng(0)
d = fits_frame(pickle.load(open('data/design_factorial.pkl', 'rb')))
d['N_hp'] = (d.hp_ratio * d.N_total).round().astype(int)
print(f'{len(d)} usable substations (HP_Peak>0, delta>0)')

idx = np.arange(len(d)); RNG.shuffle(idx)
tr = d.iloc[idx[:len(idx)//2]].reset_index(drop=True)
te = d.iloc[idx[len(idx)//2:]].reset_index(drop=True)

b = np.sum(tr.delta * tr.HP_Peak) / np.sum(tr.delta ** 2)   # regression coeff (origin)
sf_ref = float(tr.SF_cold.median())                          # transferred SF constant
p_reg = b * te.delta                          # Method 1 -- regression benchmark
p_sf = te.delta / sf_ref                       # Method 2 -- Eq (5), transferred SF
p_or = te.delta / te.SF_cold                    # oracle -- own SF (needs submetering)

print(f'regression coeff b = {b:.3f} (HP_Peak = {b:.2f}*delta);  '
      f'SF_ref = {sf_ref:.3f} -> 1/SF_ref = {1/sf_ref:.3f}')
print(f'\n{"estimator":34s} {"MdAPE":>6} {"MAPE":>6} {"R2":>7} {"bias":>7}')
for name, p in [('Eq.(5) transferred SF', p_sf),
                ('regression benchmark (b*delta)', p_reg),
                ('oracle (own SF)', p_or)]:
    mape, r2, bias = metrics(te.HP_Peak, p)
    mdape = float(np.median(np.abs(np.asarray(p) - te.HP_Peak) / te.HP_Peak * 100))
    print(f'{name:34s} {mdape:5.1f}% {mape:5.1f}% {r2:7.3f} {bias:+6.1f}%')

A = te.HP_Peak.to_numpy()
def wape(p): return np.abs(np.asarray(p) - A).sum() / A.sum() * 100
Nhp = (te.hp_ratio * te.N_total).round().astype(int).to_numpy()
print('\n-- Eq.(5) WAPE by number of aggregated heat pumps --')
for k in [5, 10, 20, 30, 40, 50]:
    m = Nhp == k
    print(f'  N_hp={k:2d} (n={m.sum():4d}): WAPE {np.abs(p_sf[m]-A[m]).sum()/A[m].sum()*100:5.1f}%')
print('\noverall Eq.(5) WAPE %.1f%% | regression %.1f%%' % (wape(p_sf), wape(p_reg)))

# ---- LaTeX table ------------------------------------------------------------
def line(name, p):
    r2 = metrics(te.HP_Peak, p)[1]
    return f"{name} & {wape(p):.1f} & {np.median(np.asarray(p)/A):.2f} & {r2:.3f} \\\\"
tex = r"""\begin{table}[t]
\centering
\caption{Installed-capacity accuracy on the held-out substations for three estimators}
\label{tab:capacity}
\begin{tabular}{lccc}
\toprule
estimator & WAPE (\%) & median ratio & $R^2$ \\
\midrule
""" + line(r"Eq.~\eqref{eq:capacity}, transferred SF", p_sf) + "\n" \
    + line("regression benchmark", p_reg) + "\n" \
    + line("oracle (own SF)", p_or) + r"""
\bottomrule
\end{tabular}
\end{table}"""
open('paper/tab_capacity.tex', 'w').write(tex)
print('wrote paper/tab_capacity.tex')

