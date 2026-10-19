"""D3 robustness check: does the capacity definition change the Kloten capacity error?

The paper takes each HP's installed capacity as a robust peak of its submetered
15-min draw (99.9th percentile, ``hp_capacity.robust_series_peak``). This script
swaps that definition on BOTH sides of the estimate -- the pilot's SF calibration
and the targets' ground truth -- and rebuilds the 1260 Kloten aggregates with the
same seed, splits and draws as ``outputs._kloten_design``:

  p999       the paper's definition (must reproduce WAPE 19.3 %)
  max        the plain maximum of the 15-min draw
  nameplate  HEAPO protocol ``HeatPump_Installation_Normpoint_ElectricPower``,
             on the subset of Kloten HPs that have it (smaller design)

Run:  PYTHONPATH="src;scripts" python scripts/d3_capacity_definition.py
Nothing here feeds the manuscript; results go to REVISION_LOG.md for review.
"""
import numpy as np
import pandas as pd

import hp_pools as hpp
import outputs as O
from hp_capacity import robust_series_peak

PROTOCOLS = 'data/heapo_data/reports/protocols.csv'
NP_COL = 'HeatPump_Installation_Normpoint_ElectricPower'


def kloten_rows():
    """Row indices and household IDs of the Kloten HPs, in _daily_pools order."""
    p = hpp.build_pool_combined(verbose=False)
    w = p['weather_of']
    hrows = [i for i, h in enumerate(p['hp_households']) if w.get(h) == 'KLO']
    return p, hrows, [p['hp_households'][i] for i in hrows]


def nameplate(ids):
    pr = pd.read_csv(PROTOCOLS, sep=';', low_memory=False)
    idc = [c for c in pr.columns if c.lower() == 'household_id'][0]
    v = pd.to_numeric(pr[NP_COL], errors='coerce')
    ok = pr[idc].notna()
    s = v[ok].groupby(pr.loc[ok, idc].astype(int)).max()
    # pool IDs read 'heapo:107210'; protocol IDs are plain numbers
    return np.array([s.get(int(str(h).split(':')[-1]), np.nan) for h in ids], dtype=float)


def design(K, n_splits=20, reps=3, seed=0, hp_idx=None):
    """Same loop as outputs._kloten_design, with K['cap'] as given."""
    T = K['T']; Kh = O._kloten_hourly(); Th = Kh['T']
    rng = np.random.default_rng(seed); nfree = K['free'].shape[0]
    n = len(K['cap']) if hp_idx is None else len(hp_idx)
    rows = []
    for s in range(n_splits):
        A, B = O._pilot_split(n, rng)
        if hp_idx is not None:
            A, B = hp_idx[A], hp_idx[B]
        pb, pm, pt = O._pilot_fit(T, K, A)
        for N in O.N_GRID_K:
            for nh in O.NHP_GRID_K:
                if nh > N or nh > len(B):
                    continue
                for _ in range(reps):
                    H = rng.choice(B, nh, replace=False)
                    F = rng.choice(nfree, N - nh, replace=False) if N > nh else np.array([], int)
                    hp = K['hp'][H].sum(0); net = hp + K['own'][H].sum(0) + K['free'][F].sum(0)
                    hph = Kh['hp'][H].sum(0); neth = hph + Kh['own'][H].sum(0) + Kh['free'][F].sum(0)
                    cap = float(K['cap'][H].sum())
                    m = O._metrics_k(T, hp, net, Th, hph, neth, cap, pm)
                    rows.append(dict(split=s, N=N, N_hp=nh, cap=cap, m_pilot=pm,
                                     cap_est=m['cap_est'], cap_or=m['cap_or']))
    return pd.DataFrame(rows)


def summary(G, label):
    bins = pd.cut(G.N_hp / G.N, [0, .15, .35, .65, 1.0])
    w = [O._wape(G.cap_est, G.cap)] + [O._wape(g.cap_est, g.cap) for _, g in G.groupby(bins, observed=True)]
    return dict(definition=label, aggregates=len(G),
                wape=round(w[0], 1), wape_le15=round(w[1], 1), wape_15_35=round(w[2], 1),
                wape_35_65=round(w[3], 1), wape_gt65=round(w[4], 1),
                median_ratio=round(float(np.median(G.cap_est / G.cap)), 3),
                wape_own_m=round(O._wape(G.cap_or, G.cap), 1),
                pilot_m_median=round(float(G.groupby('split').m_pilot.first().median()), 4))


def main():
    K = O._daily_pools(include_wpuq=False)['KLO']
    p, hrows, ids = kloten_rows()
    assert len(hrows) == len(K['cap']), 'pool order changed'
    p999 = np.array([robust_series_peak(p['hp_mat'][i]) for i in hrows])
    assert np.allclose(p999, K['cap']), 'capacity definition differs from the paper'
    pmax = np.array([float(np.nanmax(p['hp_mat'][i])) for i in hrows])
    npl = nameplate(ids)

    r = pmax / p999
    print(f'{len(ids)} Kloten HPs; max / p99.9: median {np.median(r):.3f}, '
          f'IQR [{np.quantile(r, .25):.3f}, {np.quantile(r, .75):.3f}], range [{r.min():.3f}, {r.max():.3f}]')
    has = np.isfinite(npl) & (npl > 0)
    print(f'nameplate (norm-point electric power) available for {has.sum()} of {len(ids)} HPs')
    if has.any():
        q = npl[has] / p999[has]
        print(f'  nameplate / p99.9: median {np.median(q):.3f}, IQR [{np.quantile(q, .25):.3f}, {np.quantile(q, .75):.3f}]')

    out = [summary(design(dict(K, cap=p999)), 'p99.9 (paper)'),
           summary(design(dict(K, cap=pmax)), 'max')]
    if has.sum() >= 20:
        idx = np.flatnonzero(has)
        cap_np = p999.copy(); cap_np[has] = npl[has]
        out.append(summary(design(dict(K, cap=p999), hp_idx=idx), f'p99.9, nameplate subset ({has.sum()} HPs)'))
        out.append(summary(design(dict(K, cap=cap_np), hp_idx=idx), f'nameplate ({has.sum()} HPs)'))
    res = pd.DataFrame(out)
    pd.set_option('display.width', 200)
    print(res.to_string(index=False))
    res.to_csv('results/d3_capacity_definition.csv', index=False)
    print('wrote results/d3_capacity_definition.csv')


if __name__ == '__main__':
    main()
