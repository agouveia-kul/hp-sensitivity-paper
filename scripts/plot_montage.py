# -*- coding: utf-8 -*-
"""Fig.2 (net-load bathtub) and Fig.3 (SF) equivalents for every dataset, as a
grid: rows = datasets, left col = net load vs T, right col = SF vs T."""
import pickle, numpy as np, matplotlib.pyplot as plt
import hp_figures as hf
from cross_fit import fit_row

hf.use_style()
FR = pickle.load(open('scratchpad/cross_frames.pkl', 'rb'))
FR.update(pickle.load(open('scratchpad/neea_frames.pkl', 'rb')))
ORDER = [('German WPuQ (real HP)', 'Hamelin, DE'), ('Swiss substation (real HP)', 'Kloten, CH'),
         ('Austin Pecan St (real)', 'Austin, US'), ('NEEA WA (real HP)', 'Washington, US'),
         ('NEEA OR (real HP)', 'Oregon, US'), ('ResStock ASHP -- Hennepin MN (cold)', 'Hennepin, US'),
         ('ResStock ASHP -- King WA (mild)', 'King, US'), ('ResStock ASHP -- Maricopa AZ (hot)', 'Maricopa, US')]
ORDER = [(k, t) for k, t in ORDER if k in FR]
nrow = len(ORDER)
fig, axes = plt.subplots(nrow, 2, figsize=(5.4, 1.55 * nrow))

for i, (k, title) in enumerate(ORDER):
    v = FR[k]
    T, net = np.asarray(v['T']), np.asarray(v['net'])
    heat, cool = np.asarray(v['heat']), np.asarray(v['cool'])
    r = fit_row(k, v['n'], T, net, heat, cool, v['cap_h'], v['cap_c'])
    th, tc, base, sh, sc = r['T_h'], r['T_c'], r['P_base'], r['s_h'], r['s_c']
    axb, axs = axes[i, 0], axes[i, 1]
    for ax in (axb, axs):
        ax.grid(False); ax.tick_params(labelsize=6)
    xs = np.linspace(T.min(), T.max(), 200)
    # --- net-load bathtub ---
    axb.scatter(T, net, s=3, color='0.75', alpha=.4, edgecolor='none')
    lo = th if np.isfinite(th) else T.min(); hi = tc if np.isfinite(tc) else T.max()
    axb.plot([lo, hi], [base, base], color='0.3', lw=1.5, zorder=4)
    if np.isfinite(th):
        xa = xs[xs <= th]; axb.plot(xa, base + sh * (th - xa), color=hf.C_HP, lw=1.6, zorder=4)
    if np.isfinite(tc):
        xd = xs[xs >= tc]; axb.plot(xd, base + sc * (xd - tc), color=hf.C_CH, lw=1.6, zorder=4)
    axb.set_ylabel(title, fontsize=7.5)
    axb.text(0.04, 0.9, f"$R^2$ {r['R2']:.2f}", transform=axb.transAxes, fontsize=6, color='0.4', va='top')
    # --- SF ---
    if np.isfinite(th) and v['cap_h']:
        m = T < th
        axs.scatter(T[m], np.clip(heat[m] / v['cap_h'], 0, 1), s=3, color=hf.C_HP, alpha=.3, edgecolor='none')
        xa = xs[xs <= th]; axs.plot(xa, np.clip(r['b_h'] + r['m_h'] * (th - xa), 0, 1), color=hf.C_HP, lw=1.6, zorder=4)
    if np.isfinite(tc) and v['cap_c']:
        m = T > tc
        axs.scatter(T[m], np.clip(cool[m] / v['cap_c'], 0, 1), s=3, color=hf.C_CH, alpha=.3, edgecolor='none')
        xd = xs[xs >= tc]; axs.plot(xd, np.clip(r['b_c'] + r['m_c'] * (xd - tc), 0, 1), color=hf.C_CH, lw=1.6, zorder=4)
    axs.set_ylim(0, 1)
    if i == 0:
        axb.set_title('net load (kW)', fontsize=7.5); axs.set_title('simultaneity factor', fontsize=7.5)
    if i < nrow - 1:
        axb.set_xticklabels([]); axs.set_xticklabels([])
axes[-1, 0].set_xlabel('daily mean temperature ($^\\circ$C)', fontsize=7)
axes[-1, 1].set_xlabel('daily mean temperature ($^\\circ$C)', fontsize=7)
fig.tight_layout(h_pad=0.4)
hf.save(fig, 'fig_cross_montage')
print('saved paper/figures/fig_cross_montage')
