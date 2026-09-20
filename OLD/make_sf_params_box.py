# -*- coding: utf-8 -*-
"""Distribution of the fitted SF-curve parameters across the Swiss factorial
substations. SF(T) = b + m max(0, T_h^SF - T): base b, sensitivity m and
threshold T_h^SF. One panel per parameter, boxes grouped by number of HPs."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf

hf.use_style()
F = pd.read_parquet('data/factorial_fits.parquet')
S = F[(F.response == 'SF') & (F.resolution == '24 h') & (~F.failed) & (F.N_hp > 0)]
print(f'{len(S)} Swiss substations with an SF fit\n')

order = [5, 10, 20, 30, 40, 50]
params = [('base', 'base $b$', ''),
          ('slope', 'sensitivity $m$ ($^\\circ$C$^{-1}$)', ''),
          ('T_threshold', 'threshold $T_h^{\\mathrm{SF}}$ ($^\\circ$C)', '')]

fig, ax = plt.subplots(1, 3, figsize=(hf.COL2, 2.8))
for a, (col, label, _) in zip(ax, params):
    data = [S.loc[S.N_hp == k, col].values for k in order]
    bp = a.boxplot(data, positions=range(len(order)), widths=.6, showfliers=False,
                   whis=(5, 95), patch_artist=True, medianprops=dict(color=hf.C_HP, lw=1.4))
    for b in bp['boxes']:
        b.set(facecolor=hf.C_CH, alpha=.35, edgecolor='0.5')
    a.set_xticks(range(len(order))); a.set_xticklabels(order)
    a.set(xlabel='HPs aggregated $N_{hp}$', ylabel=label)
fig.tight_layout()
hf.save(fig, 'fig_sf_params_box')

print(f'{"param":14s}{"median":>10s}{"IQR":>20s}{"5-95%":>20s}')
for col, label, _ in params:
    q = S[col].quantile([.05, .25, .5, .75, .95])
    print(f'{col:14s}{q[.5]:10.4f}   [{q[.25]:.4f}, {q[.75]:.4f}]   [{q[.05]:.4f}, {q[.95]:.4f}]')
print('\nsaved -> paper/figures/fig_sf_params_box')
