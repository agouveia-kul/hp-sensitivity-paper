# -*- coding: utf-8 -*-
"""Heating sensitivity s_h against total installed HP capacity, across the 1000
Swiss factorial substations. Both scale with the number of HPs, so the net-load
heating slope carries the installed capacity (and, with it, the ETL rate)."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf

hf.use_style()
F = pd.read_parquet('data/factorial_fits.parquet')
L = F[(F.response == 'Load') & (F.resolution == '24 h') & (~F.failed) & (F.N_hp > 0)]
x = L.HP_Peak.to_numpy()          # installed HP capacity [kW]
y = L.slope.to_numpy()            # heating sensitivity s_h [kW/degC]
nhp = L.N_hp.to_numpy()

slope0 = np.sum(x * y) / np.sum(x * x)             # through-origin fit s_h = k * cap
r = np.corrcoef(x, y)[0, 1]
print(f'n={len(L)}  Pearson r={r:.3f}  through-origin slope={slope0:.4f} (kW/degC per kW)')

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
print('saved -> paper/figures/fig_slope_capacity')
