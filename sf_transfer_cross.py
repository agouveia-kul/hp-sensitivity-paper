"""Cross-population SF transfer: fit the coincidence signature on the SWISS
(HEAPO) submetered pool, borrow it for the GERMAN (WPUQ) substations that are
treated as un-submetered. Different country, different houses, different heat
pumps, different weather -- a genuinely *similar but independent* population.

Compares the transferred Swiss curve against (a) WPUQ's own pooled curve and
(b) each WPUQ substation's own self-fit, on SF shape and on DSO load
reconstruction (curve x installed HP_Peak).
"""
import numpy as np, pandas as pd
from sf_transfer import (build_frames, pooled_curve, eval_shape, eval_load,
                         summ, pickle_load)


def main():
    swiss = pickle_load('data/design_tri.pkl')
    wpuq = pickle_load('data/design_wpuq.pkl')
    print('building frames ...', flush=True)
    ref = build_frames(swiss)                     # Swiss submetered reference
    tgt = build_frames(wpuq)                       # German target
    print(f'Swiss reference: {len(ref)} subs | WPUQ target: {len(tgt)} subs\n')

    c_ch = pooled_curve(ref)
    c_de = pooled_curve(tgt)                        # WPUQ's own signature (for context)
    Tcrit_ch = c_ch['t_thr'] - (1 - c_ch['base']) / c_ch['slope']
    Tcrit_de = c_de['t_thr'] - (1 - c_de['base']) / c_de['slope']
    print(f"SWISS curve : SF = {c_ch['base']:.3f} + {c_ch['slope']:.4f}*max(0,{c_ch['t_thr']:.1f}-T)"
          f"  R2={c_ch['r2']:.3f}  T_crit={Tcrit_ch:.1f}C")
    print(f"WPUQ  curve : SF = {c_de['base']:.3f} + {c_de['slope']:.4f}*max(0,{c_de['t_thr']:.1f}-T)"
          f"  R2={c_de['r2']:.3f}  T_crit={Tcrit_de:.1f}C\n")

    for name, curve in [('SWISS->WPUQ (transferred)', c_ch),
                        ('WPUQ->WPUQ  (own pooled)  ', c_de)]:
        shp = eval_shape(curve, tgt); ld = eval_load(curve, tgt)
        s = summ(shp, ['r2_tr', 'rmse_tr', 'rmse_self', 'bias_tr'])
        l = summ(ld, ['peak_ape', 'en_ape'])
        print(f'--- {name} on WPUQ target (median) ---')
        print(f"  SF r2 {s['r2_tr'][0]:.3f} | rmse {s['rmse_tr'][0]:.4f} "
              f"(self {s['rmse_self'][0]:.4f}) | bias {s['bias_tr'][0]:+.4f} | "
              f"peakAPE {l['peak_ape'][0]:.1f}% | energyAPE {l['en_ape'][0]:.1f}%")
    print('\n(self = each WPUQ substation fitted on its own submetering = upper bound)')


if __name__ == '__main__':
    main()
