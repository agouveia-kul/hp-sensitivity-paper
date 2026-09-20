# -*- coding: utf-8 -*-
"""Fig. 4: the Austin bathtub with each arm extended (dashed) to the critical
temperature where the aggregate would draw its full PER-MODE installed capacity
(SF -> 1). The per-arm capacities are the activity-based Cap_H, Cap_C of
make_austin_arm_capacity (the summed peaks of the devices active in each arm), so
a dual-mode device such as the furnace air-handler counts in both. Heating arm
reaches base + Cap_H at T_h^crit, cooling arm base + Cap_C at T_c^crit."""
import numpy as np, matplotlib.pyplot as plt
import hp_figures as hf
import make_austin_arm_capacity as m

hf.use_style()
Tv, yv = m.d['T'].to_numpy(), m.d['net'].to_numpy()
base, hs, th, cs, tc = m.base, m.s_h, m.T_h, m.s_c, m.T_c
capH, capC = m.capH, m.capC                       # activity-based per-mode capacity [kW]

peak_h = hs * (th - Tv.min())                     # arm heights at the observed extremes
peak_c = cs * (Tv.max() - tc)
cap_h = base + capH                               # aggregate load at each critical temp (SF=1)
cap_c = base + capC
Th_crit = th - capH / hs                          # where the arm reaches its own capacity
Tc_crit = tc + capC / cs

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.grid(False)
ax.scatter(Tv, yv, s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean load')
xa = np.linspace(Tv.min(), th, 100)
xd = np.linspace(tc, Tv.max(), 100)
ax.plot(xa, base + hs * (th - xa), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
ax.plot([th, tc], [base, base], color='0.2', lw=1.9, zorder=4, label='base load')
ax.plot(xd, base + cs * (xd - tc), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')
ax.axvspan(th, tc, color='0.5', alpha=.08, lw=0)

# extended arms (dashed) out to the critical temperatures
ax.plot([Tv.min(), Th_crit], [base + peak_h, cap_h],
        color=hf.C_HP, lw=1.4, ls=(0, (4, 2)), zorder=4, label='extrapolation ($\\mathrm{SF}\\!\\to\\!1$)')
ax.plot([Tv.max(), Tc_crit], [base + peak_c, cap_c],
        color=hf.C_CH, lw=1.4, ls=(0, (4, 2)), zorder=4)

# capacity ticks and critical-temperature markers
g = dict(color='0.35', lw=0.8, ls=(0, (3, 3)), zorder=3)
y0 = yv.min() - 3
ax.vlines(Th_crit, y0, cap_h, **g)
ax.vlines(Tc_crit, y0, cap_c, **g)
ax.plot(Th_crit, cap_h, 'o', color=hf.C_HP, ms=5, zorder=5)
ax.plot(Tc_crit, cap_c, 'o', color=hf.C_CH, ms=5, zorder=5)
ax.annotate(r'$T_h^{\mathrm{crit}}$', xy=(Th_crit, y0), xytext=(4, 3),
            textcoords='offset points', ha='left', fontsize=8, color='0.15')
ax.annotate(r'$T_c^{\mathrm{crit}}$', xy=(Tc_crit, y0), xytext=(4, 3),
            textcoords='offset points', ha='left', fontsize=8, color='0.15')
ax.annotate(r'$P_h^{\max}$', xy=(Th_crit, cap_h), xytext=(0, 6),
            textcoords='offset points', ha='center', va='bottom', fontsize=8, color=hf.C_HP)
ax.annotate(r'$P_c^{\max}$', xy=(Tc_crit, cap_c), xytext=(0, 6),
            textcoords='offset points', ha='center', va='bottom', fontsize=8, color=hf.C_CH)

# --- R1..R5 regions: observed heating R1 / dead band R2 / observed cooling R3,
#     with extrapolated R4 (cold) and R5 (hot) reaching SF=1 ---
tmin, tmax = Tv.min(), Tv.max()
for xb in (tmin, tmax):                             # observed-range limits
    ax.axvline(xb, color='0.75', lw=0.6, ls=(0, (1, 2)), zorder=1)
ax.set_xlim(Th_crit - 8, Tc_crit + 8)
ax.set_ylim(y0, cap_c * 1.30)
for (lo, hi), lab in zip([(Th_crit, tmin), (tmin, th), (th, tc), (tc, tmax), (tmax, Tc_crit)],
                         ['R4', 'R1', 'R2', 'R3', 'R5']):
    ax.text((lo + hi) / 2, 60, lab, ha='center', va='center', fontsize=8.5,
            color='0.35', fontweight='bold', zorder=6)
ax.set_xlabel('daily mean temperature (°C)')
ax.set_ylabel('aggregate load (kW)')
ax.legend(fontsize=7, loc='upper left')
fig.tight_layout()
hf.save(fig, 'fig_bathtub_critical')
print(f'base {base:.1f} capH {capH:.0f} capC {capC:.0f}  cap_h {cap_h:.0f} cap_c {cap_c:.0f}  '
      f'Th_crit {Th_crit:.1f}  Tc_crit {Tc_crit:.1f}')
print('saved -> paper/figures/fig_bathtub_critical')
