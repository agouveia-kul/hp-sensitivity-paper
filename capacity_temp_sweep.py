# -*- coding: utf-8 -*-
"""Installed capacity estimated at temperatures OTHER than T_min.
P_max(T) = P_ETL(T) / SF(T) is an identity at every active temperature, so we
sweep the evaluation temperature up from each substation's coldest day and see
what the estimate does. Also the slope estimator P_max = s_h/m, which uses the
whole line rather than one point."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf

F = pd.read_parquet('data/factorial_fits.parquet')
F = F[(F.resolution == '24 h') & (~F.failed) & (F.N_hp > 0)]
L = F[F.response == 'Load'].set_index('substation_id')
S = F[F.response == 'SF'].set_index('substation_id')
ids = sorted(set(L.index) & set(S.index))
L, S = L.loc[ids], S.loc[ids]

# transferred reference SF (population medians), as in the paper's deployable route
sf_cold = np.clip(S.base + S.slope * np.maximum(0, S.T_threshold - S.T_min_obs), 0, 1)
b_ref, m_ref = float(S.base.median()), float(S.slope.median())
true = L.HP_Peak.to_numpy()

def petl(T):                         # net-load heating arm at temperature T (per substation)
    return (L.slope * np.maximum(0.0, L.T_threshold - T)).to_numpy()
def sf_own(T):
    return np.clip((S.base + S.slope * np.maximum(0.0, S.T_threshold - T)).to_numpy(), 1e-3, 1)
def sf_transf(T):                    # transferred slope+base, local net-load threshold
    return np.clip(b_ref + m_ref * np.maximum(0.0, (L.T_threshold - T).to_numpy()), 1e-3, 1)
def wape(p, a): return np.sum(np.abs(p - a)) / np.sum(a) * 100
def mape(p, a): return np.mean(np.abs(p - a) / a) * 100
def rmse(p, a): return float(np.sqrt(np.mean((p - a) ** 2)))

DTS = [0, 2, 4, 6, 8, 10, 12]        # deg C above each substation's own T_min
print(f'n = {len(ids)} substations;  transferred SF: base {b_ref:.3f}, slope {m_ref:.4f}\n')
print(f'{"dT":>4s} {"n":>5s} | {"OWN: ratio":>10s}{"WAPE":>6s}{"MAPE":>6s}{"RMSE":>7s} | '
      f'{"TRA: ratio":>10s}{"WAPE":>6s}{"MAPE":>6s}{"RMSE":>7s}')
rows = []
for dt in DTS:
    T = (L.T_min_obs + dt).to_numpy()
    active = (T < (L.T_threshold.to_numpy() - 0.5)) & (T < S.T_threshold.to_numpy())
    a = true[active]
    for tag, sf in [('own', sf_own(T)), ('transf', sf_transf(T))]:
        p = (petl(T) / sf)[active]
        rows.append(dict(dt=dt, tag=tag, n=int(active.sum()),
                         ratio=float(np.median(p / a)), wape=wape(p, a),
                         mape=mape(p, a), rmse=rmse(p, a)))
    o = [x for x in rows if x['dt'] == dt and x['tag'] == 'own'][0]
    t = [x for x in rows if x['dt'] == dt and x['tag'] == 'transf'][0]
    print(f'{dt:>4d} {o["n"]:>5d} | {o["ratio"]:>10.2f}{o["wape"]:>5.0f}%{o["mape"]:>5.0f}%{o["rmse"]:>6.0f}kW | '
          f'{t["ratio"]:>10.2f}{t["wape"]:>5.0f}%{t["mape"]:>5.0f}%{t["rmse"]:>6.0f}kW')

# slope estimator: P_max = s_h / m  (whole-line ratio of sensitivities)
slope_est_own = (L.slope / S.slope).to_numpy()
slope_est_transf = (L.slope / m_ref).to_numpy()
print(f'\nslope estimator P_max = s_h/m :')
print(f'  own m      : ratio {np.median(slope_est_own/true):.2f}, WAPE {wape(slope_est_own, true):.0f}%')
print(f'  transf m   : ratio {np.median(slope_est_transf/true):.2f}, WAPE {wape(slope_est_transf, true):.0f}%')
print(f'  (reference: Eq.5 at Tmin, transferred = the paper\'s 10% WAPE)')

# ---- figure -----------------------------------------------------------------
hf.use_style()
d = pd.DataFrame(rows)
xlab = 'evaluation temperature above $T_{\\min}$ ($^\\circ$C)'
fig, ax = plt.subplots(2, 2, figsize=(hf.COL2, 5.0))
panels = [('ratio', 'median estimated / true capacity'), ('wape', 'WAPE (%)'),
          ('mape', 'MAPE (%)'), ('rmse', 'RMSE (kW)')]
for a, (col, ylab) in zip(ax.ravel(), panels):
    for tag, c, lab in [('own', hf.C_CH, 'own SF'), ('transf', hf.C_HP, 'transferred SF')]:
        g = d[d.tag == tag]
        a.plot(g.dt, g[col], marker='o', ms=3, color=c, label=lab)
    if col == 'ratio':
        a.axhline(1, color='0.4', lw=0.8, ls=(0, (3, 3)))
    a.set(xlabel=xlab, ylabel=ylab)
    a.legend(fontsize=7)
fig.tight_layout(); hf.save(fig, 'fig_capacity_temp_sweep')
print('\nsaved -> paper/figures/fig_capacity_temp_sweep')
