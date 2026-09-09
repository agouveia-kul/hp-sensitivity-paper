# -*- coding: utf-8 -*-
"""Daily vs hourly resolution for the energy estimate (Eq. 6).

Daily : E = slope_24h * sum_days  max(0, Tthr_24h - T_day_mean) * 24h
Hourly: E = slope_1h  * sum_hours max(0, Tthr_1h  - T_hour)     * 1h
Both compared to the substation's submetered HP energy over the year.
Because max(0,.) is convex, hourly integration captures the sub-daily degree
hours the daily mean averages away."""
import numpy as np, pandas as pd, pickle
import hp_design as hd

design = pickle.load(open('data/design_factorial.pkl', 'rb'))
fits = pd.read_parquet('data/factorial_fits.parquet')
L = fits[(fits.response == 'Load') & (~fits.failed)]
d24 = L[L.resolution == '24 h'].set_index('substation_id')
d1 = L[L.resolution == '1 h'].set_index('substation_id')
meta = design['meta']

rows = []
for sid in meta.index:
    if int(meta.loc[sid, 'N_hp']) == 0 or sid not in d24.index or sid not in d1.index:
        continue
    temp = hd.get_series(design, sid, 'Temperature')          # 15-min
    hp = pd.Series(design['hp_load'][sid], index=design['index'])
    dt = temp.index.to_series().diff().median().total_seconds() / 3600
    actual = float((hp * dt).sum())
    if actual <= 0:
        continue
    Tday = temp.resample('D').mean()
    Thr = temp.resample('h').mean()
    s24, t24 = float(d24.loc[sid, 'slope']), float(d24.loc[sid, 'T_threshold'])
    s1, t1 = float(d1.loc[sid, 'slope']), float(d1.loc[sid, 'T_threshold'])
    e_day = float((s24 * (t24 - Tday).clip(lower=0) * 24.0).sum())
    e_hour = float((s1 * (t1 - Thr).clip(lower=0) * 1.0).sum())
    # isolate the integration effect: daily fit, but hourly degree-hours
    e_dayfit_hourdh = float((s24 * (t24 - Thr).clip(lower=0) * 1.0).sum())
    rows.append(dict(sid=sid, N_hp=int(meta.loc[sid, 'N_hp']), actual=actual,
                     e_day=e_day, e_hour=e_hour, e_mix=e_dayfit_hourdh))
g = pd.DataFrame(rows)
for col in ['e_day', 'e_hour', 'e_mix']:
    g[col + '_ape'] = np.abs(g[col] - g.actual) / g.actual * 100
    g[col + '_r'] = g[col] / g.actual

print(f'{len(g)} substations\n')
print('%-28s %8s %8s' % ('estimator', 'MdAPE%', 'ratio'))
for name, c in [('daily fit + daily integ.', 'e_day'),
                ('hourly fit + hourly integ.', 'e_hour'),
                ('daily fit + hourly integ.', 'e_mix')]:
    print('%-28s %7.1f %8.2f' % (name, g[c + '_ape'].median(), g[c + '_r'].median()))

print('\n-- MdAPE by N_hp --')
print(g.groupby('N_hp').agg(daily=('e_day_ape', 'median'),
                            hourly=('e_hour_ape', 'median')).round(1).to_string())

# ---- LaTeX table ------------------------------------------------------------
def r(name, c):
    w = np.abs(g[c] - g.actual).sum() / g.actual.sum() * 100
    return f"{name} & {w:.1f} & {g[c+'_r'].median():.2f} \\\\"
tex = r"""\begin{table}[t]
\centering
\caption{Energy-estimate accuracy against submetered HP energy, by the resolution of the fit and of the temperature integration}
\label{tab:energy}
\begin{tabular}{lcc}
\toprule
fit + integration & WAPE (\%) & median ratio \\
\midrule
""" + r("daily + daily", 'e_day') + "\n" \
    + r("hourly + hourly", 'e_hour') + "\n" \
    + r("daily + hourly", 'e_mix') + r"""
\bottomrule
\end{tabular}
\end{table}"""
open('paper/tab_energy.tex', 'w').write(tex)
print('\nwrote paper/tab_energy.tex')
