"""Does a simultaneity-factor (SF) signature learned on SUBMETERED substations
transfer to substations of a similar population that have NO submetering?

SF(t) = HP_Load(t) / HP_Peak needs HP submetering to compute. A DSO cannot
measure it on most feeders. But the earlier analysis found the SF(T) hockey
stick is essentially invariant to ETL penetration and installed power -- it is a
normalised *population coincidence signature*. If so, a curve fitted on a
submetered REFERENCE set can be borrowed by an unsubmetered TARGET set.

We test three things on a held-out target set (never used to fit the curve):

  1. SF-shape transfer -- predict each target day's SF from the reference curve
     SF_ref(T); compare to the target's true (held-out) daily SF. Baseline: the
     target's OWN in-sample hockey stick (the best you could do WITH submetering).
  2. Load reconstruction -- the DSO use-case: reconstruct absolute aggregate HP
     load  HP_Load_hat(T) = SF_ref(T) * HP_Peak_target  using only a borrowed
     curve + registry installed capacity (no target submetering). Score the
     seasonal peak HP load and total HP energy.
  3. Robustness to population mismatch -- train the curve on the HIGH-penetration
     tercile and apply to the LOW-penetration tercile (and vice-versa), to show
     the transfer survives a population that is only *similar*, not identical.

Reference curve = one hockey stick fitted to the POOLED daily (T, SF) points of
the reference substations (the natural "pilot study" estimator).
"""
import numpy as np, pandas as pd
import hp_design as hd, hp_sf
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

RNG = np.random.default_rng(0)
MIN_DAYS = 60


def build_frames(design):
    """Per-substation daily arrays for every substation with real HP submetering."""
    meta = design['meta']
    subs = []
    for sid in meta.index:
        fr, peak = hp_sf.daily_frame(design, int(sid))
        if peak <= 0 or 'SF' not in fr or len(fr) < MIN_DAYS:
            continue
        subs.append(dict(
            sid=int(sid), hp_ratio=float(meta.loc[sid, 'hp_ratio']),
            N_total=int(meta.loc[sid, 'N_total']), HP_Peak=float(peak),
            T=fr['T'].to_numpy(), SF=fr['SF'].to_numpy(),
            Load=fr['Load'].to_numpy()))
    return subs


def pooled_curve(subs):
    """Fit one hockey stick to the pooled daily (T, SF) points of a group."""
    T = np.concatenate([s['T'] for s in subs])
    SF = np.concatenate([s['SF'] for s in subs])
    base, slope, t_thr, r2 = fit_hockey_stick(T, SF, T_BALANCE_BOUNDS)
    return dict(base=base, slope=slope, t_thr=t_thr, r2=r2)


def predict(curve, T):
    return curve['base'] + curve['slope'] * np.maximum(0.0, curve['t_thr'] - T)


def r2(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float)
    ss = np.sum((y - y.mean()) ** 2)
    return 1 - np.sum((y - p) ** 2) / ss if ss > 0 else np.nan


def eval_shape(curve, targets):
    """Pooled and per-substation SF-shape metrics: transferred vs self-fit."""
    rows = []
    for s in targets:
        p_tr = predict(curve, s['T'])
        # self fit (needs submetering) -- upper bound
        try:
            b, sl, tt, _ = fit_hockey_stick(s['T'], s['SF'], T_BALANCE_BOUNDS)
            p_self = b + sl * np.maximum(0.0, tt - s['T'])
        except Exception:
            p_self = np.full_like(s['SF'], np.nan)
        rows.append(dict(
            sid=s['sid'], hp_ratio=s['hp_ratio'], HP_Peak=s['HP_Peak'],
            rmse_tr=np.sqrt(np.mean((s['SF'] - p_tr) ** 2)),
            rmse_self=np.sqrt(np.mean((s['SF'] - p_self) ** 2)),
            bias_tr=np.mean(p_tr - s['SF']),
            r2_tr=r2(s['SF'], p_tr), r2_self=r2(s['SF'], p_self)))
    return pd.DataFrame(rows)


def eval_load(curve, targets):
    """DSO reconstruction of seasonal-peak HP load and total HP energy (kW / kWh-ish)."""
    rows = []
    for s in targets:
        p_tr = np.clip(predict(curve, s['T']), 0, 1)
        load_true = s['SF'] * s['HP_Peak']
        load_pred = p_tr * s['HP_Peak']
        # seasonal peak = 99th pct of daily mean HP load; energy = sum of daily means
        pk_t, pk_p = np.quantile(load_true, .99), np.quantile(load_pred, .99)
        en_t, en_p = load_true.sum(), load_pred.sum()
        rows.append(dict(sid=s['sid'], hp_ratio=s['hp_ratio'], HP_Peak=s['HP_Peak'],
                         peak_true=pk_t, peak_pred=pk_p, en_true=en_t, en_pred=en_p))
    d = pd.DataFrame(rows)
    d['peak_ape'] = (d.peak_pred - d.peak_true).abs() / d.peak_true * 100
    d['en_ape'] = (d.en_pred - d.en_true).abs() / d.en_true * 100
    return d


def summ(df, cols):
    return {c: (float(df[c].median()), float(df[c].quantile(.25)), float(df[c].quantile(.75))) for c in cols}


def main():
    design = pickle_load('data/design_tri.pkl')
    print('building daily frames ...', flush=True)
    subs = build_frames(design)
    print(f'{len(subs)} submetered substations (>= {MIN_DAYS} days, HP_Peak>0)\n', flush=True)
    idx = np.arange(len(subs))

    # ---- 1) random 50/50 reference/target split -------------------------------
    RNG.shuffle(idx)
    ref = [subs[i] for i in idx[:len(idx)//2]]
    tgt = [subs[i] for i in idx[len(idx)//2:]]
    curve = pooled_curve(ref)
    print(f'REFERENCE pooled SF curve (n={len(ref)}): '
          f"SF = {curve['base']:.3f} + {curve['slope']:.4f}*max(0,{curve['t_thr']:.1f}-T)  "
          f"pooled R2={curve['r2']:.3f}")
    Tcrit = curve['t_thr'] - (1 - curve['base']) / curve['slope']
    print(f'         extrapolated T_crit (SF=1) = {Tcrit:.1f} C\n')

    shp = eval_shape(curve, tgt)
    ld = eval_load(curve, tgt)
    print('--- SF-shape transfer on held-out target (median [IQR]) ---')
    for k, (m, lo, hi) in summ(shp, ['rmse_tr', 'rmse_self', 'bias_tr', 'r2_tr', 'r2_self']).items():
        print(f'  {k:10s}: {m:+.4f}  [{lo:+.4f}, {hi:+.4f}]')
    print('\n--- DSO load reconstruction (borrowed curve x registry HP_Peak) ---')
    for k, (m, lo, hi) in summ(ld, ['peak_ape', 'en_ape']).items():
        print(f'  {k:10s}: {m:5.1f}%  [{lo:.1f}, {hi:.1f}]')
    print(f'  seasonal-peak HP load: median true {ld.peak_true.median():.1f} kW, '
          f'pred {ld.peak_pred.median():.1f} kW')

    # ---- 2) by penetration stratum (invariance -> stable transfer) ------------
    print('\n--- transfer error by TARGET penetration stratum ---')
    q = pd.qcut(shp.hp_ratio, 4, labels=['p1', 'p2', 'p3', 'p4'], duplicates='drop')
    j = shp.join(ld[['peak_ape', 'en_ape']])
    for g, sub in j.groupby(q, observed=True):
        print(f'  {g} hp_ratio~{sub.hp_ratio.median():.2f} (n={len(sub):4d}): '
              f'SF r2_tr {sub.r2_tr.median():.3f} | rmse_tr {sub.rmse_tr.median():.4f} '
              f'(self {sub.rmse_self.median():.4f}) | peakAPE {sub.peak_ape.median():4.1f}%')

    # ---- 3) cross-penetration transfer (population MISMATCH) ------------------
    print('\n--- cross-penetration transfer (train HIGH -> test LOW and reverse) ---')
    ratios = np.array([s['hp_ratio'] for s in subs])
    lo_c, hi_c = np.quantile(ratios, [1/3, 2/3])
    low = [s for s in subs if s['hp_ratio'] <= lo_c]
    high = [s for s in subs if s['hp_ratio'] >= hi_c]
    for name, rr, tt in [('HIGH->LOW', high, low), ('LOW->HIGH', low, high)]:
        c = pooled_curve(rr)
        sp = eval_shape(c, tt); lp = eval_load(c, tt)
        print(f'  {name}: ref pen~{np.median([s["hp_ratio"] for s in rr]):.2f} -> '
              f'tgt pen~{np.median([s["hp_ratio"] for s in tt]):.2f} | '
              f"curve slope {c['slope']:.4f} base {c['base']:.3f} | "
              f'SF r2_tr {sp.r2_tr.median():.3f} rmse_tr {sp.rmse_tr.median():.4f} '
              f'(self {sp.rmse_self.median():.4f}) | peakAPE {lp.peak_ape.median():.1f}%')

    shp.to_csv('data/sf_transfer_shape.csv', index=False)
    ld.to_csv('data/sf_transfer_load.csv', index=False)
    print('\nSaved -> data/sf_transfer_shape.csv, data/sf_transfer_load.csv')


def pickle_load(p):
    import pickle
    return pickle.load(open(p, 'rb'))


if __name__ == '__main__':
    main()
