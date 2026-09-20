# -*- coding: utf-8 -*-
"""SF like Fig. 3 but the dead-band points are ignored and each arm is fitted
independently as a non-origin linear regression, anchored at the threshold
temperatures taken from the net-load fit (T_h, T_c). The SF then contributes only
a slope and an intercept per arm; the thresholds come from the observable fit."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import hp_figures as hf
import make_austin_arm_capacity as m

hf.use_style()
devices = m.devices
CapH, CapC = m.capH, m.capC
Th, Tc = m.T_h, m.T_c                    # thresholds from the net-load fit
Tser = m.Tds
idx = Tser.index


def arm_sum(flag):
    s = pd.Series(0.0, index=idx)
    for dv in devices:
        if dv[flag]:
            s = s.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
    return s


heatsum, coolsum = arm_sum('a_h'), arm_sum('a_c')
dh = pd.DataFrame({'T': Tser, 'sf': (heatsum / CapH).clip(0, 1)}).dropna()
dh = dh[dh['T'] < Th]                     # heating regime only
dc = pd.DataFrame({'T': Tser, 'sf': (coolsum / CapC).clip(0, 1)}).dropna()
dc = dc[dc['T'] > Tc]                     # cooling regime only

mh, bh = np.polyfit(Th - dh['T'], dh['sf'], 1)      # sf = bh + mh*(Th - T)
mc, bc = np.polyfit(dc['T'] - Tc, dc['sf'], 1)      # sf = bc + mc*(T - Tc)


def r2f(x, y, mm, bb):
    ss = np.sum((y - y.mean()) ** 2)
    return 1 - np.sum((y - (mm * x + bb)) ** 2) / ss
r2h = r2f((Th - dh['T']).to_numpy(), dh['sf'].to_numpy(), mh, bh)
r2c = r2f((dc['T'] - Tc).to_numpy(), dc['sf'].to_numpy(), mc, bc)
Tmin, Tmax = dh['T'].min(), dc['T'].max()

fig, ax = plt.subplots(figsize=(hf.COL1, 3.0))
ax.grid(False)
ax.scatter(dh['T'], dh['sf'], s=8, color='0.65', alpha=.45, edgecolor='none', label='daily mean SF')
ax.scatter(dc['T'], dc['sf'], s=8, color='0.65', alpha=.45, edgecolor='none')
ax.axvspan(Th, Tc, color='0.5', alpha=.08, lw=0)    # dead band (excluded)
xa = np.linspace(Tmin, Th, 100)
xd = np.linspace(Tc, Tmax, 100)
ax.plot(xa, np.clip(bh + mh * (Th - xa), 0, 1), color=hf.C_HP, lw=1.9, zorder=4, label='heating arm')
ax.plot(xd, np.clip(bc + mc * (xd - Tc), 0, 1), color=hf.C_CH, lw=1.9, zorder=4, label='cooling arm')

# net-load thresholds
gth = dict(color='0.45', lw=0.8, ls=(0, (3, 3)), zorder=3)
ax.vlines(Th, 0, 0.20, **gth)
ax.annotate('$T_h$', xy=(Th, 0.20), xytext=(0, 3), textcoords='offset points',
            ha='center', va='bottom', fontsize=9, color='0.3')
ax.vlines(Tc, 0, 0.20, **gth)
ax.annotate('$T_c$', xy=(Tc, 0.20), xytext=(0, 3), textcoords='offset points',
            ha='center', va='bottom', fontsize=9, color='0.3')

# arm equations, each with a leader to its curve
ax.annotate(r'$\hat{\mathrm{SF}}_h(T) = b_h + m_h\,(T_h - T)$',
            xy=(5, bh + mh * (Th - 5)), xytext=(0, 0.40), textcoords='data',
            ha='left', va='bottom', fontsize=8, color=hf.C_HP,
            arrowprops=dict(arrowstyle='-', lw=0.7, color=hf.C_HP))
ax.annotate(r'$\hat{\mathrm{SF}}_c(T) = b_c + m_c\,(T - T_c)$',
            xy=(27, bc + mc * (27 - Tc)), xytext=(27, 0.60), textcoords='data',
            ha='center', va='bottom', fontsize=8, color=hf.C_CH,
            arrowprops=dict(arrowstyle='-', lw=0.7, color=hf.C_CH))

ax.set_xlabel('daily mean temperature ($^\\circ$C)')
ax.set_ylabel('simultaneity factor')
ax.set_ylim(0, 1)
ax.legend(fontsize=7, loc='upper left')
ax.text(0.035, 0.72, f'$R^2$ {r2h:.2f} (heat), {r2c:.2f} (cool)', transform=ax.transAxes,
        ha='left', va='top', fontsize=7, color='0.3')
fig.tight_layout()
hf.save(fig, 'fig_sf_arms_anchored')
print(f'heating b_h {bh:.3f} m_h {mh:.4f} R2 {r2h:.3f} | cooling b_c {bc:.3f} m_c {mc:.4f} R2 {r2c:.3f} | Th {Th:.1f} Tc {Tc:.1f}')
print('saved -> paper/figures/fig_sf_arms_anchored')
