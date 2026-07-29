"""Multi-dataset pipeline: build pools, designs and test results for all arms.

One entry point, ``run_arm``, so the notebook can regenerate any arm from raw
data or load cached results, and every arm goes through the *same* design
generator and the *same* H1/H2 tests -- which is what makes the cross-dataset
comparison meaningful.

Arms
----
``heapo_clean`` / ``heapo_eheat``  -- Swiss submetered cohort (the primary data)
``swiss_clean`` / ``swiss_eheat``  -- large consumer pool, lifts the N ceiling
``wpuq``                           -- German, independent validation

``*_clean`` draws every non-HP member from households with **no electric heating
of any kind**, so the ``N_hp = 0`` cells are true controls. ``*_eheat`` draws
them from households that have other electric heating (electric water heater,
storage or direct heating), isolating its influence on the identical grid.
WPUQ carries no appliance metadata, so only the clean arm exists there.
"""

import os
import pickle

import pandas as pd

import hp_design as hd
import hp_h1 as h1
import hp_h2 as h2

ARMS = {
    'heapo_clean': dict(pool='heapo', eheat_frac=0.0, n_grid=[5, 10, 20]),
    'heapo_eheat': dict(pool='heapo', eheat_frac=1.0, n_grid=[5, 10, 20]),
    'swiss_clean': dict(pool='swiss', eheat_frac=0.0,
                        n_grid=[5, 10, 20, 50, 100, 200]),
    'swiss_eheat': dict(pool='swiss', eheat_frac=1.0,
                        n_grid=[5, 10, 20, 50, 100, 200]),
    'wpuq':        dict(pool='wpuq', eheat_frac=0.0, n_grid=[4, 8, 16, 32]),
}

DESIGN_PATH = 'data/design_{arm}.pkl'
H1_PATH = 'data/h1_{arm}.parquet'
H2_PATH = 'data/h2_{arm}.parquet'


def get_pool(name, rebuild=False):
    """Load (or build) a household pool by dataset name."""
    if name == 'heapo':
        import sys
        sys.path.insert(0, 'src')
        from heapo import HEAPO
        obj = HEAPO(data_path='data/heapo_data', use_local_time=False,
                    suppress_warning=True)
        return hd.build_pool(obj, rebuild=rebuild)
    import hp_pools as hpp
    if name == 'swiss':
        return hpp.build_pool_swiss(rebuild=rebuild)
    if name == 'wpuq':
        return hpp.build_pool_wpuq(rebuild=rebuild)
    raise ValueError(f'unknown pool {name!r}')


def run_arm(arm, regenerate_design=False, rerun_tests=False,
            rebuild_pool=False, n_reps=40, n_boot=None, verbose=True):
    """Build/load the design and the H1/H2 results for one arm.

    Returns (design, h1_results, h2_fits). Every stage is cached to disk, so a
    re-run with all flags False is instant.
    """
    cfg = ARMS[arm]
    dpath = DESIGN_PATH.format(arm=arm)
    n_boot = h1.N_BOOT if n_boot is None else n_boot

    if os.path.exists(dpath) and not regenerate_design and not rebuild_pool:
        design = hd.load_design(dpath)
        if verbose:
            print(f'[{arm}] loaded design ({len(design["meta"])} substations)')
    else:
        pool = get_pool(cfg['pool'], rebuild=rebuild_pool)
        design, cov = hd.generate_design(
            pool, n_grid=cfg['n_grid'], n_reps=n_reps,
            eheat_frac=cfg['eheat_frac'], verbose=verbose)
        hd.save_design(design, dpath)
        if verbose:
            print(f'[{arm}] generated {len(design["meta"])} substations '
                  f'({int(cov.skipped.sum())} cells skipped)')

    meta = design['meta']
    sf_ids = [int(s) for s in meta.index[meta['HP_Peak'] > 0]]
    all_ids = [int(s) for s in meta.index]

    h1path, h2path = H1_PATH.format(arm=arm), H2_PATH.format(arm=arm)
    if os.path.exists(h1path) and not rerun_tests:
        h1_res = pd.read_parquet(h1path)
    else:
        a = h1.run_h1(design, sf_ids, 'SF', n_boot=n_boot, n_jobs=-1, chunk=200,
                      block=h1.BLOCK_LEN,
                      cache_path=f'data/h1_cache/{arm}_SF.pkl', verbose=verbose)
        b = h1.run_h1(design, all_ids, 'NetLoad', n_boot=n_boot, n_jobs=-1,
                      chunk=200, block=h1.BLOCK_LEN,
                      cache_path=f'data/h1_cache/{arm}_NetLoad.pkl', verbose=verbose)
        h1_res = pd.concat([a.assign(response='SF'), b.assign(response='NetLoad')])
        h1_res.to_parquet(h1path)

    if os.path.exists(h2path) and not rerun_tests:
        h2_res = pd.read_parquet(h2path)
    else:
        h2_res = h2.fit_by_resolution(design, all_ids, cache_path=h2path,
                                      rebuild=True, verbose=verbose)
    return design, h1_res, h2_res


def run_all(arms=None, **kw):
    out = {}
    for arm in (arms or ARMS):
        out[arm] = run_arm(arm, **kw)
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def control_floor_table(results):
    """Control rejection rate vs substation size, per arm.

    Controls are ``N_hp == 0``; in the *_clean arms they additionally contain no
    other electric heating, which is what makes them true controls.
    """
    tab = {}
    for arm, (_, r1, _) in results.items():
        nl = r1[r1.response == 'NetLoad']
        c = nl[nl.N_hp == 0]
        if len(c):
            tab[arm] = c.groupby('N_total').reject.mean().round(3)
    return pd.DataFrame(tab)


def eheat_type_analysis(n_grid=(5, 10, 20, 50), n_reps=40, rerun=False,
                        verbose=True):
    """Split the Swiss "other electric heating" pool by TYPE and compare.

    "Electric heating" is not one thing, and the two types act in opposite
    directions:

    * **Electric SPACE heating** (storage / direct) is strongly temperature
      driven, so a control substation containing it rejects essentially always.
    * **Primary electric WATER heating** is weakly seasonal (inlet water
      temperature), so it raises the floor but less severely.

    Control-only designs (``hp_ratio = 0``) are enough here, so this is cheap.
    """
    import pickle

    import numpy as np

    import hp_pools as hpp

    with open(hpp.SWISS_CACHE, 'rb') as fh:
        pool = pickle.load(fh)
    meta = pd.read_csv(os.path.join(hpp.SWISS_DIR, 'metadata.csv'), sep=';',
                       encoding='utf-8-sig').set_index('0_meter_id')
    eh = pool.get('eheat_households', [])
    sub = meta.reindex(eh)
    is_space = sub[['1_storage_heating', '1_direct_heating']].astype(str).eq('True').any(axis=1)
    space = [h for h, b in zip(eh, is_space) if bool(b)]
    water = [h for h in eh if h not in set(space)]
    if verbose:
        print(f'Swiss other-electric-heating pool: {len(space)} with space heating, '
              f'{len(water)} with water heating only')

    out = {}
    for label, ids in [('space_heating', space), ('water_heating_only', water)]:
        p = dict(pool)
        p['eheat_households'] = ids
        design, _ = hd.generate_design(p, n_grid=list(n_grid), ratio_grid=[0.0],
                                       n_reps=n_reps, eheat_frac=1.0, verbose=False)
        sids = [int(s) for s in design['meta'].index]
        res = h1.run_h1(design, sids, 'NetLoad', n_boot=h1.N_BOOT, n_jobs=-1,
                        chunk=200, block=h1.BLOCK_LEN,
                        cache_path=f'data/h1_cache/swiss_eh_{label}.pkl',
                        resume=not rerun, verbose=False)
        j = design['meta'][['N_total']].join(res[['reject']], how='inner')
        out[label] = j.groupby('N_total').reject.mean().round(3)
    return pd.DataFrame(out)


def summary_table(results):
    rows = []
    for arm, (design, r1, f2) in results.items():
        nl, sf = r1[r1.response == 'NetLoad'], r1[r1.response == 'SF']
        c = nl[nl.N_hp == 0]
        lo, hi = h1.wilson(int(c.reject.sum()), len(c)) if len(c) else (float('nan'),) * 2
        wide = h2.to_wide(f2)
        fit, _ = h2.effect_size_model(f2)
        b, blo, bhi, _ = h2.coef_ci(fit)
        hp = f2[(~f2.failed) & (f2.N_hp > 0)]
        s = hp.groupby('resolution').slope.median().reindex(h2.LABELS)
        rows.append({
            'arm': arm, 'n_sub': len(design['meta']),
            'control_n': len(c),
            'control_rate': c.reject.mean() if len(c) else float('nan'),
            'control_lo': lo, 'control_hi': hi,
            'sf_detect': h1.detection_limit(h1.rejection_table(sf, 'hp_ratio')) if len(sf) else float('nan'),
            'nl_detect': h1.detection_limit(h1.rejection_table(nl, 'hp_ratio')) if len(nl) else float('nan'),
            'log_dt': b, 'log_dt_lo': blo, 'log_dt_hi': bhi,
            'r2_ratio': wide.median().iloc[-1] / wide.median().iloc[0],
            'slope_ratio': s.iloc[-1] / s.iloc[0],
        })
    return pd.DataFrame(rows)
