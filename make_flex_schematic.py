# -*- coding: utf-8 -*-
"""Schematic for the flexibility formulation. Over each window Delta t the ETL
population must deliver a fixed energy. Window 1: before flexing it draws the
constant baseline (E_old). Window 2: after flexing it draws the same energy as a
full-power pulse of duty alpha_F (E_new = E_old). Window 3: the deviation from
baseline is the flexible energy, equal up and down. The alpha_F = SF identity is
deliberately NOT shown. Illustrative values only."""
import numpy as np, matplotlib.pyplot as plt
import hp_figures as hf

hf.use_style()
Pmax, base, af, Dt = 1.0, 0.4, 0.4, 1.0     # base = Pmax*af -> equal areas
RED, BLU = hf.C_HP, hf.C_CH

fig, ax = plt.subplots(figsize=(hf.COL2, 2.9))
ax.axhline(Pmax, color='0.6', lw=0.8, zorder=1)
ax.axhline(base, color='0.35', lw=0.9, ls=(0, (4, 2)), zorder=2)

# pulse train across all three windows (the schedule)
xs, ys = [], []
for k in range(3):
    xs += [k, k, k + af, k + af]; ys += [0, Pmax, Pmax, 0]
xs += [3]; ys += [0]
ax.step(xs, ys, where='post', color=RED, lw=1.7, zorder=6)

# window 1 -- E_old (baseline energy, before flex)
ax.fill_between([0, 1], 0, base, color='0.55', alpha=.22, lw=0)
ax.annotate('$E_{\\mathrm{old}}$ (before flex)', (0.7, base / 2), ha='center', va='center', fontsize=8, color='0.25')
# window 2 -- E_new (same energy, after flex)
ax.fill_between([1, 1 + af], 0, Pmax, color=RED, alpha=.16, lw=0)
ax.annotate('$E_{\\mathrm{new}}$ (after flex)', (1 + af / 2, 1.16), ha='center', va='bottom', fontsize=8, color=RED)
ax.plot([1 + af / 2, 1 + af / 2], [Pmax, 1.15], color=RED, lw=0.6)
# window 3 -- flexible energy, up and down
ax.fill_between([2, 2 + af], base, Pmax, color=RED, alpha=.16, lw=0)
ax.fill_between([2 + af, 3], 0, base, color=BLU, alpha=.20, lw=0)
ax.annotate('$E_{\\mathrm{flex}}^{\\uparrow}$', (2 + af / 2, (base + Pmax) / 2), ha='center', va='center', fontsize=9, color=RED)
ax.annotate('$E_{\\mathrm{flex}}^{\\downarrow}$', (2 + af + (1 - af) / 2, base / 2), ha='center', va='center', fontsize=9, color='#1f6f78')

def bracket(x0, x1, y, label):
    ax.annotate('', (x0, y), (x1, y), arrowprops=dict(arrowstyle='<->', lw=0.9, color='0.3'))
    ax.text((x0 + x1) / 2, y + 0.03, label, ha='center', va='bottom', fontsize=9, color='0.2')
bracket(2, 3, 1.24, '$\\Delta t$')
bracket(2, 2 + af, 1.12, '$\\alpha_F$')
ax.vlines([2, 2 + af], Pmax, 1.12, color='0.6', lw=0.5, ls=(0, (2, 2)), zorder=1)

ax.annotate('$P_{\\mathrm{ETL}}^{\\max}$', (0.02, Pmax), xytext=(2, -10), textcoords='offset points', fontsize=8, color='0.3')
ax.annotate('baseline $\\bar P_{\\mathrm{ETL}}(T)$', (1.7, base), xytext=(0, 4),
            textcoords='offset points', ha='center', fontsize=8, color='0.25')
ax.set_xlim(0, 3); ax.set_ylim(0, 1.36)
ax.set_xticks([]); ax.set_yticks([0, base, Pmax]); ax.set_yticklabels(['0', '', ''])
ax.set_xlabel('time'); ax.set_ylabel('ETL power')
fig.tight_layout()
hf.save(fig, 'fig_flex_schedule')
print('saved -> paper/figures/fig_flex_schedule')
