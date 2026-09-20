# -*- coding: utf-8 -*-
"""What happens to the activity-based SF fit if the dead band is neglected:
compare a joint bathtub (all points) against two arms fitted only on their own
regime (heating T<T_h, cooling T>T_c), dropping the dead-band points."""
import numpy as np, pandas as pd
import make_austin_arm_capacity as m
from hp_common import (fit_bathtub_stick, fit_hockey_stick, fit_cooling_stick,
                       T_BALANCE_BOUNDS, T_COOLING_BOUNDS)

devices = m.devices
CapH, CapC, CapB = m.capH, m.capC, m.capB
T_h0, T_c0 = m.T_h, m.T_c
Tser = m.Tds
idx = Tser.index


def arm_sum(flag):
    s = pd.Series(0.0, index=idx)
    for dv in devices:
        if dv[flag]:
            s = s.add(dv['daily'].reindex(idx).fillna(0.0), fill_value=0)
    return s


heatsum, coolsum, bandsum = arm_sum('a_h'), arm_sum('a_c'), arm_sum('a_b')
mh_, mc_ = Tser < T_h0, Tser > T_c0
mb_ = ~(mh_ | mc_)
SF = pd.Series(index=idx, dtype=float)
SF[mh_] = heatsum[mh_] / CapH
SF[mc_] = coolsum[mc_] / CapC
SF[mb_] = bandsum[mb_] / CapB
d = pd.DataFrame({'T': Tser, 'sf': SF.clip(0, 1)}).dropna()

# (a) joint bathtub over ALL points (dead band included)
base, hs, th, cs, tc, r2 = fit_bathtub_stick(d['T'].to_numpy(), d['sf'].to_numpy())

# (b) arms only: drop the dead-band days, fit each arm on its own regime
dh = d[d['T'] < T_h0]
dc = d[d['T'] > T_c0]
bh, mh, thh, r2h = fit_hockey_stick(dh['T'].to_numpy(), dh['sf'].to_numpy(), T_BALANCE_BOUNDS)
bc, mc, tcc, r2c = fit_cooling_stick(dc['T'].to_numpy(), dc['sf'].to_numpy(), T_COOLING_BOUNDS)

Tmin, Tmax = d['T'].min(), d['T'].max()
sfmin_j = base + hs * max(0, th - Tmin)
sfmin_a = bh + mh * max(0, thh - Tmin)
sfmax_j = base + cs * max(0, Tmax - tc)
sfmax_a = bc + mc * max(0, Tmax - tcc)

print('\n== JOINT bathtub (dead band kept) ==')
print(f'  base b {base:.3f}   m_h {hs:.4f}  T_h {th:.1f}   m_c {cs:.4f}  T_c {tc:.1f}   R2 {r2:.3f}')
print('== ARMS ONLY (dead band dropped) ==')
print(f'  heating: b_h {bh:.3f}  m_h {mh:.4f}  T_h {thh:.1f}  (R2 {r2h:.3f})')
print(f'  cooling: b_c {bc:.3f}  m_c {mc:.4f}  T_c {tcc:.1f}  (R2 {r2c:.3f})')
print(f'  base: one b {base:.3f}  ->  two intercepts b_h {bh:.3f}, b_c {bc:.3f}  (step {abs(bh-bc):.3f})')
print('== capacity impact (P_max prop 1/SF) ==')
print(f'  SF at coldest: joint {sfmin_j:.3f} vs heating-arm {sfmin_a:.3f}  '
      f'-> Cap ratio arm/joint {sfmin_j/sfmin_a:.2f}')
print(f'  SF at hottest: joint {sfmax_j:.3f} vs cooling-arm {sfmax_a:.3f}  '
      f'-> Cap ratio arm/joint {sfmax_j/sfmax_a:.2f}')

# (c) arms with thresholds FIXED to the net-load fit, non-origin OLS
def r2f(x, y, mm, bb):
    ss = np.sum((y - y.mean()) ** 2)
    return 1 - np.sum((y - (mm * x + bb)) ** 2) / ss if ss > 0 else np.nan
xh = (T_h0 - dh['T']).to_numpy(); yh = dh['sf'].to_numpy()
xc = (dc['T'] - T_c0).to_numpy(); yc = dc['sf'].to_numpy()
mhf, bhf = np.polyfit(xh, yh, 1)
mcf, bcf = np.polyfit(xc, yc, 1)
sfmin_f = bhf + mhf * (T_h0 - Tmin)
sfmax_f = bcf + mcf * (Tmax - T_c0)
print('\n== ARMS with net-load thresholds FIXED (non-origin OLS) ==')
print(f'  net-load thresholds: T_h {T_h0:.1f}  T_c {T_c0:.1f}')
print(f'  heating: b_h {bhf:.3f}  m_h {mhf:.4f}  (R2 {r2f(xh, yh, mhf, bhf):.3f})')
print(f'  cooling: b_c {bcf:.3f}  m_c {mcf:.4f}  (R2 {r2f(xc, yc, mcf, bcf):.3f})')
print(f'  SF cold {sfmin_f:.3f} (joint {sfmin_j:.3f})  hot {sfmax_f:.3f} (joint {sfmax_j:.3f})  '
      f'-> Cap ratio cold {sfmin_j/sfmin_f:.2f}  hot {sfmax_j/sfmax_f:.2f}')
