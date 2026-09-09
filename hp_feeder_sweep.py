# -*- coding: utf-8 -*-
"""Sensitivity of the three use-case estimates to the number of heat pumps on
the REAL German feeder. Heat-pump circuits are removed from the aggregate (the
households and their base load stay), sweeping N_hp at a fixed 37-house base,
and capacity, energy and flexibility are re-estimated per random subset."""
import numpy as np, pandas as pd
import hp_pools as hpp
from hp_capacity import robust_series_peak
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

SWISS = dict(base=0.027, slope=0.0161, t_thr=16.4)
p = hpp.build_pool_wpuq(verbose=False)
idx = p['index']; hp_mat, other_mat = p['hp_mat'], p['other_mat']
n_house = hp_mat.shape[0]
rp = np.array([robust_series_peak(hp_mat[i]) for i in range(n_house)])
base_all = other_mat.sum(axis=0)                       # fixed 37-house base load
temp = pd.Series(p['temperature']['WPUQ'], index=idx)
Td = temp.resample('D').mean(); Tmin = float(Td.min())
dt = 0.25
sf_swiss_tmin = np.clip(SWISS['base'] + SWISS['slope'] * max(0, SWISS['t_thr'] - Tmin), 0, 1)

def fit_daily(series):
    y = pd.Series(series, index=idx).resample('D').mean()
    d = pd.DataFrame({'T': Td, 'y': y}).dropna()
    b, s, t, r2 = fit_hockey_stick(d['T'].to_numpy(), d['y'].to_numpy(), T_BALANCE_BOUNDS)
    return b, s, t, r2

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
        # own SF fit
        sfser = hp_sum / cap_true
        sb, ss, st, sr2 = fit_daily(sfser)
        sf_own = np.clip(sb + ss * max(0.0, st - Tmin), 0, 1)
        sf_hyb = np.clip(SWISS['base'] + SWISS['slope'] * max(0.0, nt - Tmin), 0, 1)
        # capacity
        cap_dep, cap_hyb, cap_or = delta / sf_swiss_tmin, delta / sf_hyb, delta / sf_own
        # energy: heating arm integrated vs submetered HP energy
        e_est = float((ns * (nt - Td).clip(lower=0) * 24).sum())
        e_act = float(hp_sum.sum() * dt)
        rows.append(dict(N_hp=nhp, cap_true=cap_true, net_r2=nr2, sf_r2=sr2,
                         e_cap_dep=(cap_dep - cap_true) / cap_true * 100,
                         e_cap_hyb=(cap_hyb - cap_true) / cap_true * 100,
                         e_cap_or=(cap_or - cap_true) / cap_true * 100,
                         e_energy=(e_est - e_act) / e_act * 100,
                         sf_cold_own=sf_own, headroom_kw=(1 - sf_own) * cap_true))
d = pd.DataFrame(rows)
g = d.groupby('N_hp').median(numeric_only=True)
sp = d.groupby('N_hp').agg(cap_dep_iqr=('e_cap_dep', lambda x: x.quantile(.75) - x.quantile(.25)),
                           en_iqr=('e_energy', lambda x: x.quantile(.75) - x.quantile(.25)))
pd.set_option('display.width', 160)
print('median by N_hp (errors in %, headroom in kW):')
print(g[['cap_true', 'net_r2', 'e_cap_dep', 'e_cap_hyb', 'e_cap_or', 'e_energy',
         'sf_cold_own', 'headroom_kw']].round(2).to_string())
print('\nspread (IQR) by N_hp:')
print(sp.round(1).to_string())

# ---- LaTeX table ------------------------------------------------------------
def row(nhp):
    r = g.loc[nhp]
    return f"{nhp} & {r['e_cap_dep']:+.0f} & {r['e_cap_hyb']:+.0f} & {r['e_energy']:+.0f} \\\\"
body = "\n".join(row(k) for k in grid)
tex = r"""\begin{table}[t]
\centering
\caption{Use-case estimates on the real feeder as HP circuits are removed, at a fixed 37-house base. Signed median error over 200 random subsets per count}
\label{tab:feeder-sweep}
\begin{tabular}{rccc}
\toprule
$N_{hp}$ & capacity, transf.\ (\%) & capacity, hybrid (\%) & energy (\%) \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}"""
open('paper/tab_feeder_sweep.tex', 'w').write(tex)
print('\nwrote paper/tab_feeder_sweep.tex')
