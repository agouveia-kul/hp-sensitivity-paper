# -*- coding: utf-8 -*-
"""Two routes to the ETL energy, compared against submetered HP energy.
  arm  : E = s_h max(0, T_h - T) dt          (net-load heating arm, observable)
  SF   : E = P_ETL_max SF(T) dt              (capacity x simultaneity factor)
The SF route carries the base term b of SF(T), a floor the arm drops above T_h.
But SF and P_max both need submetering, so the oracle SF route is near-circular
(SF x P_max = HP power by definition); the honest deployable SF route uses a
transferred SF and the estimated capacity delta / SF_ref. Daily (24 h) fits,
integrated over the hourly temperature series."""
import numpy as np, pandas as pd, pickle
import hp_design as hd

design = pickle.load(open('data/design_factorial.pkl', 'rb'))
F = pd.read_parquet('data/factorial_fits.parquet')
F = F[(F.resolution == '24 h') & (~F.failed) & (F.N_hp > 0)]
L = F[F.response == 'Load'].set_index('substation_id')
S = F[F.response == 'SF'].set_index('substation_id')
ids = sorted(set(L.index) & set(S.index))

def sf_curve(b, m, thr, T):
    return np.clip(b + m * np.maximum(0.0, thr - np.asarray(T)), 0.0, 1.0)

# transferred reference (population medians), as used for the capacity estimator
S = S.loc[[i for i in ids]]
sf_cold = np.clip(S.base + S.slope * np.maximum(0.0, S.T_threshold - S.T_min_obs), 0, 1)
b_ref, m_ref, sfcold_ref = float(S.base.median()), float(S.slope.median()), float(sf_cold.median())
print(f'transferred SF: base {b_ref:.3f}, slope {m_ref:.4f}, coldest-day SF_ref {sfcold_ref:.3f}\n')

rows = []
for sid in ids:
    l, s = L.loc[sid], S.loc[sid]
    T = hd.get_series(design, sid, 'Temperature')                     # hourly
    dt = T.index.to_series().diff().median().total_seconds() / 3600
    Th = hd.get_series(design, sid, 'HP_Load').reindex(T.index).fillna(0.0)
    act = float(Th.sum() * dt)                                        # actual kWh (year)
    Tv = T.to_numpy()

    # net-load heating arm (observable): daily slope, integrated hourly
    arm = float((l.slope * np.maximum(0.0, l.T_threshold - Tv)).sum() * dt)
    # SF route, oracle: own SF curve x true installed peak
    sf_own = sf_curve(s.base, s.slope, s.T_threshold, Tv)
    orac = float((sf_own * l.HP_Peak).sum() * dt)
    # SF route, deployable: transferred SF shape (local net-load threshold) x est capacity
    delta = l.slope * max(0.0, l.T_threshold - l.T_min_obs)
    cap_est = delta / sfcold_ref
    sf_dep = sf_curve(b_ref, m_ref, l.T_threshold, Tv)
    dep = float((sf_dep * cap_est).sum() * dt)

    rows.append(dict(sid=sid, N_hp=int(l.N_hp), act=act, arm=arm, orac=orac, dep=dep))

d = pd.DataFrame(rows)
d = d[d.act > 0]
def wape(p, a): return np.abs(p - a).sum() / a.sum() * 100
def ratio(p, a): return float(np.median(p / a))
a = d.act.to_numpy()
print(f'n = {len(d)} substations\n')
print(f'{"estimator":34s}{"WAPE":>7s}{"med ratio":>11s}')
for col, name in [('arm', 'net-load arm  s_h max(0,Th-T) dt'),
                  ('orac', 'SF route ORACLE  P_max SF(T) dt'),
                  ('dep', 'SF route deploy  P_est SF_ref dt')]:
    p = d[col].to_numpy()
    print(f'{name:34s}{wape(p,a):6.0f}%{ratio(p,a):11.2f}')

print('\n-- WAPE by N_hp --')
print(f'{"N_hp":>5s}{"arm":>8s}{"oracle":>8s}{"deploy":>8s}')
for k in [5, 10, 20, 30, 40, 50]:
    m = d.N_hp == k
    if m.sum():
        aa = d.loc[m, 'act'].to_numpy()
        print(f'{k:5d}{wape(d.loc[m,"arm"].to_numpy(),aa):7.0f}%'
              f'{wape(d.loc[m,"orac"].to_numpy(),aa):7.0f}%'
              f'{wape(d.loc[m,"dep"].to_numpy(),aa):7.0f}%')

# how much of the annual energy is the SF base-term floor (the DHW/dead-band part)
floor = b_ref * d.arm.mean() * 0  # placeholder; report base share below
print(f'\nSF base term b_ref = {b_ref:.3f}: a persistent floor of '
      f'{b_ref:.1%} of installed capacity that the arm has no term for.')
