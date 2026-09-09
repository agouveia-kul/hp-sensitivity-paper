# -*- coding: utf-8 -*-
"""Two installed-capacity estimators, both starting from the net-load hockey
stick's coincident-peak proxy  delta = slope * (T_balance - T_min):

  Method 1  regression : fit  HP_Peak ~ delta  (through origin) on SEEN
                         substations, apply the coefficient to UNSEEN ones.
  Method 2  transferred SF : HP_Peak = delta / SF_ref, where SF_ref is the
                         median coldest-day simultaneity factor of the SEEN
                         substations (capacity = coincident peak / coincidence).

Both need submetering on the seen set (Method 1 for the capacity label, Method 2
for SF); neither needs anything but net load + temperature on the unseen set.
Scored within Switzerland (train/test split) and across datasets (Swiss->WPUQ).
"""
import numpy as np, pandas as pd, pickle
import hp_sf

RNG = np.random.default_rng(0)


def fits_frame(design):
    df = hp_sf.fit_all(design, verbose=False)
    df = df.reset_index()
    d = pd.DataFrame({'sid': df['substation_id'], 'HP_Peak': df['HP_Peak'],
                      'hp_ratio': df['hp_ratio'], 'N_total': df['N_total'],
                      'slope': df['Load_slope']})
    span_L = np.maximum(0.0, df['Load_T_threshold'] - df['T_min_obs'])
    d['delta'] = df['Load_slope'] * span_L                     # net-load coincident peak proxy
    span_S = np.maximum(0.0, df['SF_T_threshold'] - df['T_min_obs'])
    d['SF_cold'] = (df['SF_base'] + df['SF_slope'] * span_S).clip(0, 1)
    d = d[(d.HP_Peak > 0) & (d.delta > 0)].dropna(subset=['delta', 'HP_Peak', 'SF_cold'])
    return d.reset_index(drop=True)


def metrics(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float); m = y > 0
    mape = np.mean(np.abs((y[m] - p[m]) / y[m])) * 100
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1 - np.sum((y - p) ** 2) / ss if ss > 0 else np.nan
    bias = (np.mean(p) - np.mean(y)) / np.mean(y) * 100
    return mape, r2, bias


def experiment(train, test, tag):
    b = np.sum(train.delta * train.HP_Peak) / np.sum(train.delta ** 2)   # M1 coeff (origin)
    sf_ref = float(train.SF_cold.median())                                # M2 constant
    p1 = b * test.delta
    p2 = test.delta / sf_ref
    print(f'\n=== {tag} ===   (train {len(train)}, test {len(test)})')
    print(f'  Method 1 coeff  b        = {b:.3f}   (HP_Peak = {b:.2f} * delta)')
    print(f'  Method 2 SF_ref (median) = {sf_ref:.3f}   -> 1/SF_ref = {1/sf_ref:.3f}')
    for name, p in [('Method 1  regression (b*delta)', p1),
                    ('Method 2  transferred SF (delta/SF)', p2)]:
        mape, r2, bias = metrics(test.HP_Peak, p)
        print(f'  {name:38s}: MAPE {mape:5.1f}%  R2 {r2:6.3f}  bias {bias:+6.1f}%')
    return b, sf_ref, p1, p2


def by_penetration(test, p1, p2, tag):
    print(f'  -- {tag}: MAPE by test penetration --')
    q = pd.qcut(test.hp_ratio, 4, labels=['q1', 'q2', 'q3', 'q4'], duplicates='drop')
    for g, idx in test.groupby(q, observed=True).groups.items():
        i = test.index.get_indexer(idx)
        m1 = metrics(test.HP_Peak.iloc[i], np.asarray(p1)[i])[0]
        m2 = metrics(test.HP_Peak.iloc[i], np.asarray(p2)[i])[0]
        print(f'     {g} pen~{test.hp_ratio.iloc[i].median():.2f} (n={len(i):4d}): '
              f'M1 {m1:5.1f}%   M2 {m2:5.1f}%')


def main():
    print('building Swiss (tri) fits ...', flush=True)
    swiss = fits_frame(pickle.load(open('data/design_tri.pkl', 'rb')))
    print(f'  {len(swiss)} usable Swiss substations', flush=True)
    print('building WPUQ fits ...', flush=True)
    wpuq = fits_frame(pickle.load(open('data/design_wpuq.pkl', 'rb')))
    print(f'  {len(wpuq)} usable WPUQ substations', flush=True)

    # within Switzerland: random 50/50
    idx = np.arange(len(swiss)); RNG.shuffle(idx)
    tr = swiss.iloc[idx[:len(idx)//2]].reset_index(drop=True)
    te = swiss.iloc[idx[len(idx)//2:]].reset_index(drop=True)
    _, _, p1, p2 = experiment(tr, te, 'WITHIN SWITZERLAND (seen -> unseen)')
    by_penetration(te, p1, p2, 'within-Swiss')

    # cross dataset: all Swiss -> WPUQ
    _, _, p1c, p2c = experiment(swiss, wpuq, 'CROSS DATASET  Swiss -> WPUQ')
    by_penetration(wpuq, p1c, p2c, 'Swiss->WPUQ')

    swiss.to_csv('data/capacity_two_methods_swiss.csv', index=False)
    wpuq.to_csv('data/capacity_two_methods_wpuq.csv', index=False)
    print('\nSaved -> data/capacity_two_methods_{swiss,wpuq}.csv')


if __name__ == '__main__':
    main()
