# -*- coding: utf-8 -*-
"""Energy-estimate error beyond MdAPE: several metrics and the distribution,
overall and by number of aggregated heat pumps. Daily fit + daily integration."""
import numpy as np, pandas as pd, pickle
from scipy import stats
import hp_analysis as ha
import hp_figures as hf
import matplotlib.pyplot as plt

design = pickle.load(open('data/design_factorial.pkl', 'rb'))
fits = pd.read_parquet('data/factorial_fits.parquet')
te = ha.thermal_energy_estimates(design, fits, resolution='24 h')
te['N_hp'] = te.N_hp.astype(int)
g = te.groupby('substation_id').agg(est=('hs_kWh', 'sum'), act=('actual_kWh', 'sum'),
                                    N_hp=('N_hp', 'first'))
g = g[g.act > 0].copy()
g['spe'] = (g.est - g.act) / g.act * 100          # signed % error (neg = under)
g['ape'] = g.spe.abs()
g['ratio'] = g.est / g.act

y, p = g.act.to_numpy(), g.est.to_numpy()
rmse = np.sqrt(np.mean((p - y) ** 2))
nrmse = rmse / y.mean() * 100
r2 = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
print(f'n = {len(g)} substations\n')
print('=== overall ===')
print(f'  MdAPE (median |%err|)      : {g.ape.median():5.1f}%')
print(f'  MAPE  (mean   |%err|)      : {g.ape.mean():5.1f}%')
print(f'  median signed % error      : {g.spe.median():+5.1f}%')
print(f'  mean   signed % error      : {g.spe.mean():+5.1f}%')
print(f'  RMSE                       : {rmse:6.0f} kWh')
print(f'  nRMSE (RMSE / mean actual) : {nrmse:5.1f}%')
print(f'  R2 (across substations)    : {r2:5.3f}')
print(f'  Pearson r(actual, est)     : {stats.pearsonr(y, p)[0]:5.3f}')
print(f'  skew of signed % error     : {stats.skew(g.spe):+5.2f}')
print('\n  signed-%-error percentiles p10/25/50/75/90:',
      np.round(np.percentile(g.spe, [10, 25, 50, 75, 90]), 1))

print('\n=== by N_hp (signed % error) ===')
tab = g.groupby('N_hp').agg(n=('spe', 'size'), med_spe=('spe', 'median'),
                            p25=('spe', lambda s: s.quantile(.25)),
                            p75=('spe', lambda s: s.quantile(.75)),
                            mdape=('ape', 'median'), mape=('ape', 'mean'))
tab['IQR'] = tab.p75 - tab.p25
print(tab.round(1).to_string())

# ---- figure -----------------------------------------------------------------
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
hf.save(fig, 'fig_energy_error')
print('\nsaved -> paper/figures/fig_energy_error')
