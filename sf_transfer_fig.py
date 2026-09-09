"""Figure: transferability of the SF coincidence signature from submetered to
un-submetered substations -- within a population (near-perfect) and across
independent populations (portable only after localising the balance threshold).
"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from sf_transfer import build_frames, pooled_curve, eval_shape, eval_load, predict, pickle_load
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS

ref = build_frames(pickle_load('data/design_tri.pkl'))
tgt = build_frames(pickle_load('data/design_wpuq.pkl'))
c_ch = pooled_curve(ref); c_de = pooled_curve(tgt)

# within-population: random 50/50 split of Swiss
rng = np.random.default_rng(0); idx = np.arange(len(ref)); rng.shuffle(idx)
r_in = [ref[i] for i in idx[:len(idx)//2]]; t_in = [ref[i] for i in idx[len(idx)//2:]]
c_in = pooled_curve(r_in)
shp = eval_shape(c_in, t_in); ld = eval_load(c_in, t_in)
q = pd.qcut(shp.hp_ratio, 4, labels=['0.13', '0.30', '0.50', '0.95'], duplicates='drop')
j = shp.join(ld[['peak_ape']])
by = j.groupby(q, observed=True).agg(borrow=('peak_ape', 'median')).reset_index()
self_pk = []  # self-fit peak APE per stratum (upper bound)
for g in by['hp_ratio']:
    sub = [s for s in t_in if f'{s["hp_ratio"]:.2f}'[:4]]  # placeholder
self_ref = ld.peak_ape.median()

# cross-population ladder
def enape(curve_or_fn, targets, local_thr=False, local_base=False):
    e = []
    for s in targets:
        T, SF = s['T'], s['SF']
        b, sl, tt = c_ch['base'], c_ch['slope'], c_ch['t_thr']
        if local_thr or local_base:
            try:
                b0, sl0, tt0, _ = fit_hockey_stick(T, SF, T_BALANCE_BOUNDS)
            except Exception:
                continue
            if local_thr: tt = tt0
            if local_base: b = b0
        p = np.clip(b + sl * np.maximum(0, tt - T), 0, 1)
        lt = SF * s['HP_Peak']; lp = p * s['HP_Peak']
        e.append(abs(lp.sum() - lt.sum()) / lt.sum() * 100)
    return np.nanmedian(e)

ladder = [('Swiss curve\n(full transfer)', enape(None, tgt)),
          ('+ local\nthreshold', enape(None, tgt, local_thr=True)),
          ('+ local base\n(slope only)', enape(None, tgt, local_thr=True, local_base=True)),
          ('WPUQ own\npooled', None)]
_ldde = eval_load(c_de, tgt); ladder[-1] = ('WPUQ own\npooled', _ldde.en_ape.median())

fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.2))

# A: the two population signatures
Tg = np.linspace(-12, 18, 100)
for s in rng.choice(len(tgt), 200, replace=False):
    ax[0].scatter(tgt[s]['T'], tgt[s]['SF'], s=2, c='0.8', alpha=.15, rasterized=True)
ax[0].plot(Tg, np.clip(predict(c_ch, Tg), 0, 1), 'C0', lw=2.5, label=f"Swiss  (slope {c_ch['slope']:.4f}, T$_h$ {c_ch['t_thr']:.1f})")
ax[0].plot(Tg, np.clip(predict(c_de, Tg), 0, 1), 'C3', lw=2.5, label=f"WPUQ  (slope {c_de['slope']:.4f}, T$_h$ {c_de['t_thr']:.1f})")
ax[0].set(xlabel='daily mean temperature (C)', ylabel='simultaneity factor SF', title='A  Population SF signatures')
ax[0].legend(fontsize=8, loc='upper right'); ax[0].grid(alpha=.3)

# B: within-population transfer by penetration
x = np.arange(len(by))
ax[1].bar(x, by['borrow'], .55, color='C0', label='borrowed curve (no target submetering)')
ax[1].axhline(self_ref, color='k', ls='--', lw=1.2, label=f'pooled self-fit ref ({self_ref:.1f}%)')
ax[1].set_xticks(x); ax[1].set_xticklabels(by['hp_ratio'])
ax[1].set(xlabel='target penetration (HP ratio)', ylabel='seasonal-peak HP load error (%)',
          title='B  Within population (Swiss->Swiss)', ylim=(0, 12))
ax[1].legend(fontsize=8); ax[1].grid(alpha=.3, axis='y')

# C: cross-population ladder
labels = [l for l, _ in ladder]; vals = [v for _, v in ladder]
cols = ['C3', 'C1', 'C0', '0.5']
ax[2].bar(range(len(vals)), vals, .6, color=cols)
for i, v in enumerate(vals):
    ax[2].text(i, v + 1.5, f'{v:.0f}%', ha='center', fontsize=9)
ax[2].set_xticks(range(len(labels))); ax[2].set_xticklabels(labels, fontsize=8)
ax[2].set(ylabel='total HP energy error (%)', title='C  Cross population (Swiss->WPUQ)', ylim=(0, 90))
ax[2].grid(alpha=.3, axis='y')

fig.suptitle('Borrowing the simultaneity-factor signature for un-submetered substations', fontsize=12)
fig.tight_layout(rect=(0, 0, 1, .96))
fig.savefig('paper/figures/fig_sf_transfer.png', dpi=150)
print('within-pop borrow peakAPE by pen:', by.to_dict('records'), '| self', round(self_ref, 1))
print('cross-pop energyAPE ladder:', [(l.replace(chr(10), ' '), round(v, 1)) for l, v in ladder])
print('Saved -> paper/figures/fig_sf_transfer.png')
