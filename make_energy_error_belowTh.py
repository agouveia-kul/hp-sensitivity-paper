# -*- coding: utf-8 -*-
"""Fig. 8 rerun, but the estimate is compared only against submetered consumption
on days below the heating threshold (T < T_h), i.e. the temperature-driven share
the heating arm actually models. Days with T >= T_h (where the arm is zero and
the submeter logs mostly domestic hot water) are excluded from the ground truth."""
import numpy as np, pandas as pd, pickle
from scipy import stats
import hp_analysis as ha
import hp_figures as hf
import matplotlib.pyplot as plt

design = pickle.load(open('data/design_factorial.pkl', 'rb'))
fits = pd.read_parquet('data/factorial_fits.parquet')
te = ha.thermal_energy_estimates(design, fits, resolution='24 h')
te['N_hp'] = te.N_hp.astype(int)
te_below = te[te.hs_kWh > 0].copy()          # T < T_h days (heating arm active)


def summarise(frame, label):
    g = frame.groupby('substation_id').agg(est=('hs_kWh', 'sum'),
                                           act=('actual_kWh', 'sum'), N_hp=('N_hp', 'first'))
    g = g[g.act > 0].copy()
    g['spe'] = (g.est - g.act) / g.act * 100
    g['ratio'] = g.est / g.act
    wape = np.abs(g.est - g.act).sum() / g.act.sum() * 100
    print(f'\n=== {label}  (n={len(g)}) ===')
    print(f'  median signed % error : {g.spe.median():+5.1f}%   '
          f'MdAPE {g.spe.abs().median():4.1f}%   WAPE {wape:4.1f}%   '
          f'median ratio {g.ratio.median():.2f}')
    tab = g.groupby('N_hp').agg(med=('spe', 'median'),
                                p25=('spe', lambda s: s.quantile(.25)),
                                p75=('spe', lambda s: s.quantile(.75)))
    tab['IQR'] = (tab.p75 - tab.p25).round(1)
    print(tab.round(1).to_string())
    return g


g_all = summarise(te, 'ALL days (current Fig. 8)')
g = summarise(te_below, 'T < T_h days only')

# ---- figure (T < T_h version) ----------------------------------------------
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
hf.save(fig, 'fig_energy_error_belowTh')
print('\nsaved -> paper/figures/fig_energy_error_belowTh')
