"""Hockey-stick fits of simultaneity factor and mean load against temperature.

Two responses, both on daily means, fitted per substation:

* **SF**   -- ``SF(t) = HP_Load(t) / HP_Peak`` averaged to daily means. Bounded
  in [0, 1] by construction because households are drawn without replacement.
* **Load** -- daily mean net load (kW).

Both are fitted with ``base + slope * max(0, T_threshold - T)`` and each yields a
projected **critical temperature**, the extrapolated point at which the heat
pumps would run at full installed capacity together (SF = 1):

* SF fit   : ``SF = 1``            ->  ``T_crit = T_threshold - (1 - base) / slope``
* Load fit : HP part = ``HP_Peak`` ->  ``T_crit = T_threshold - HP_Peak / slope``

The two are independent routes to the same physical quantity -- one from
submetered ground truth, one from the net load a DSO can actually observe -- so
comparing them measures how far the observable route can be trusted.
"""

import numpy as np
import pandas as pd

import hp_design as hd
from hp_common import fit_hockey_stick, T_BALANCE_BOUNDS


def daily_frame(design, sid):
    """Daily mean temperature, SF and net load for one substation."""
    temp = hd.get_series(design, sid, 'Temperature').resample('D').mean()
    load = hd.get_series(design, sid, 'Total_Load').resample('D').mean()
    hp_peak = design['meta'].loc[sid, 'HP_Peak']
    sf = None
    if hp_peak > 0:
        sf = (hd.get_series(design, sid, 'HP_Load') / hp_peak).resample('D').mean()
    d = pd.DataFrame({'T': temp, 'Load': load})
    if sf is not None:
        d['SF'] = sf
    return d.dropna(), float(hp_peak)


def fit_substation(design, sid, bounds=T_BALANCE_BOUNDS):
    """Fit both responses for one substation and project the critical temperature."""
    d, hp_peak = daily_frame(design, sid)
    if len(d) < 30 or hp_peak <= 0 or 'SF' not in d:
        return None
    m = design['meta'].loc[sid]
    T = d['T'].to_numpy()
    out = {'substation_id': int(sid), 'N_total': int(m['N_total']),
           'N_hp': int(m['N_hp']), 'hp_ratio': float(m['hp_ratio']),
           'HP_Peak': hp_peak, 'weather_id': m['weather_id'],
           'N_eheat': int(m.get('N_eheat_realised', 0)), 'T_min_obs': float(T.min())}

    for resp in ('SF', 'Load'):
        try:
            base, slope, t_thr, r2 = fit_hockey_stick(T, d[resp].to_numpy(), bounds)
        except Exception:
            continue
        out[f'{resp}_base'] = base
        out[f'{resp}_slope'] = slope
        out[f'{resp}_T_threshold'] = t_thr
        out[f'{resp}_r2'] = r2
        if slope > 0:
            # temperature at which the heat pumps would together reach full
            # installed capacity (SF = 1)
            gap = (1.0 - base) if resp == 'SF' else hp_peak
            out[f'{resp}_T_crit'] = t_thr - gap / slope
    return out


def fit_all(design, ids=None, verbose=True):
    ids = design['meta'].index if ids is None else ids
    rows = []
    for k, sid in enumerate(ids):
        r = fit_substation(design, int(sid))
        if r is not None:
            rows.append(r)
        if verbose and (k + 1) % 200 == 0:
            print(f'  {k + 1}/{len(ids)} fitted')
    df = pd.DataFrame(rows).set_index('substation_id')
    # observed maximum SF, for context on how far T_crit is extrapolated
    df['SF_max_modelled'] = df['SF_base'] + df['SF_slope'] * np.maximum(
        0.0, df['SF_T_threshold'] - df['T_min_obs'])
    return df


def describe(df, cols=None):
    """Median and IQR of the fitted parameters for both responses."""
    cols = cols or [c for c in df.columns
                    if c.startswith(('SF_', 'Load_')) and c != 'SF_max_modelled']
    rows = []
    for c in cols:
        s = df[c].replace([np.inf, -np.inf], np.nan).dropna()
        if not len(s):
            continue
        rows.append({'parameter': c, 'n': len(s), 'median': s.median(),
                     'q25': s.quantile(.25), 'q75': s.quantile(.75),
                     'min': s.min(), 'max': s.max()})
    return pd.DataFrame(rows)


def plot_distributions(df, figsize=(14, 9)):
    """Distributions of slope, threshold temperature and critical temperature."""
    import matplotlib.pyplot as plt

    specs = [
        ('SF_slope', 'SF slope (1/°C)', 'tab:blue'),
        ('SF_T_threshold', 'SF threshold temperature (°C)', 'tab:blue'),
        ('SF_T_crit', 'SF critical temperature, SF=1 (°C)', 'tab:blue'),
        ('Load_slope', 'Load slope (kW/°C)', 'tab:orange'),
        ('Load_T_threshold', 'Load threshold temperature (°C)', 'tab:orange'),
        ('Load_T_crit', 'Load critical temperature, SF=1 (°C)', 'tab:orange'),
    ]
    fig, axs = plt.subplots(2, 3, figsize=figsize)
    for ax, (col, label, colour) in zip(axs.flatten(), specs):
        s = df[col].replace([np.inf, -np.inf], np.nan).dropna()
        if not len(s):
            continue
        lo, hi = s.quantile(.01), s.quantile(.99)
        ax.hist(s, bins=40, range=(lo, hi), color=colour, alpha=.75,
                edgecolor='white')
        ax.axvline(s.median(), color='red', ls='--', lw=1.5,
                   label=f'median {s.median():.2f}')
        ax.set_xlabel(label)
        ax.set_ylabel('substations')
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle('Hockey-stick parameters: simultaneity factor (blue) vs net load (orange)')
    fig.tight_layout()
    return fig
