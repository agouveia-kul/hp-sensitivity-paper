"""Scaling laws for temperature-dependent aggregate load.

Replaces the hypothesis-test framing. With ~1000 substations per arm every test
is significant, so the informative quantities are effect sizes and how they
scale with the two forms of aggregation: the number of consumers/heat pumps
(spatial) and the averaging window (temporal).

Three laws, all fitted from the per-resolution hockey-stick fits:

1. **Slope is additive.** ``slope = a*N_hp + b*N_total``, intercept ~ 0. A heat
   pump contributes an order of magnitude more temperature sensitivity than an
   ordinary consumer, but ordinary consumers are not temperature-inert.

2. **Fit quality scales with heat pumps and with averaging, not with size.**
   ``logit(R2) ~ log(dt) + log(N_total) + log(N_hp)``: the ``N_hp`` and ``dt``
   terms are positive, the ``N_total`` term is NEGATIVE -- extra non-HP
   consumers add load uncorrelated with temperature and dilute the signal.

3. **At fixed penetration, aggregation always helps** -- because the heat pumps
   scale with the consumers. The net coefficient is ``b_N + b_hp > 0``, and it
   is largest at low penetration, where growing the substation adds heat pumps
   from a near-zero base.
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.special import logit

LABELS = ['15 min', '1 hour', '8 hours', 'daily']
EPS = 1e-4


def _prep(fits, hp_only=False):
    d = fits[~fits['failed']].copy()
    if hp_only:
        d = d[d['N_hp'] > 0]
    d['logit_r2'] = logit(d['r2'].clip(EPS, 1 - EPS))
    d['log_dt'] = np.log(d['dt_minutes'])
    d['log_N'] = np.log(d['N_total'])
    with np.errstate(divide='ignore'):
        d['log_Nhp'] = np.log(d['N_hp'].where(d['N_hp'] > 0))
    return d


# ---------------------------------------------------------------------------
# Law 1 -- the slope is additive in heat pumps and consumers
# ---------------------------------------------------------------------------
def slope_decomposition(fits, resolution='daily'):
    """OLS of the fitted slope on N_hp and N_total at one resolution."""
    d = fits[(~fits['failed']) & (fits['resolution'] == resolution)]
    m = smf.ols('slope ~ N_hp + N_total', data=d).fit()
    ci = m.conf_int()
    out = {}
    for k, name in [('N_hp', 'per_heat_pump'), ('N_total', 'per_consumer'),
                    ('Intercept', 'intercept')]:
        out[name] = (float(m.params[k]), float(ci.loc[k, 0]), float(ci.loc[k, 1]))
    out['r2'] = float(m.rsquared)
    out['n'] = int(m.nobs)
    return out


def slope_table(results, resolution='daily'):
    rows = []
    for arm, (_, _, fits) in results.items():
        s = slope_decomposition(fits, resolution)
        rows.append({
            'arm': arm,
            'per_heat_pump': s['per_heat_pump'][0],
            'hp_lo': s['per_heat_pump'][1], 'hp_hi': s['per_heat_pump'][2],
            'per_consumer': s['per_consumer'][0],
            'cons_lo': s['per_consumer'][1], 'cons_hi': s['per_consumer'][2],
            'intercept': s['intercept'][0], 'model_r2': s['r2'], 'n': s['n'],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Law 2 -- what actually drives fit quality
# ---------------------------------------------------------------------------
def r2_decomposition(fits):
    """logit(R2) ~ log(dt) + log(N_total) + log(N_hp), substation random effect."""
    d = _prep(fits, hp_only=True).dropna(subset=['log_Nhp'])
    if d['N_total'].nunique() < 2 or d['N_hp'].nunique() < 2:
        return None
    m = smf.mixedlm('logit_r2 ~ log_dt + log_N + log_Nhp', d,
                    groups=d['substation_id']).fit()
    ci = m.conf_int()
    return {k: (float(m.params[k]), float(ci.loc[k, 0]), float(ci.loc[k, 1]))
            for k in ['log_dt', 'log_N', 'log_Nhp']}


def r2_table(results):
    rows = []
    for arm, (_, _, fits) in results.items():
        r = r2_decomposition(fits)
        if r is None:
            continue
        row = {'arm': arm}
        for k, v in r.items():
            row[k] = v[0]
            row[f'{k}_lo'], row[f'{k}_hi'] = v[1], v[2]
        # net effect of growing the substation at fixed penetration
        row['net_fixed_ratio'] = r['log_N'][0] + r['log_Nhp'][0]
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Law 3 -- growth at fixed penetration
# ---------------------------------------------------------------------------
def fixed_ratio_scaling(fits):
    """Coefficient on log(N_total) within each penetration stratum.

    This is the deployment-relevant derivative: a real feeder has a penetration
    rate, and a bigger feeder has proportionally more heat pumps.
    """
    d = _prep(fits)
    rows = []
    for ratio, g in d[d['hp_ratio'] > 0].groupby('hp_ratio'):
        if g['N_total'].nunique() < 2:
            continue
        m = smf.mixedlm('logit_r2 ~ log_dt + log_N', g,
                        groups=g['substation_id']).fit()
        ci = m.conf_int()
        rows.append({
            'hp_ratio': ratio,
            'n_sizes': int(g['N_total'].nunique()),
            'log_N': float(m.params['log_N']),
            'lo': float(ci.loc['log_N', 0]), 'hi': float(ci.loc['log_N', 1]),
            'log_dt': float(m.params['log_dt']),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
def plot_scaling(fits, arm_name='', ax=None):
    """R2 against substation size, one line per resolution, at fixed penetration."""
    import matplotlib.pyplot as plt

    d = fits[~fits['failed']]
    ratios = sorted(r for r in d['hp_ratio'].unique() if r > 0)
    target = min(ratios, key=lambda r: abs(r - 0.5)) if ratios else None
    sub = d[d['hp_ratio'] == target]
    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(8, 5))
    for lab in LABELS:
        s = sub[sub['resolution'] == lab].groupby('N_total')['r2'].median()
        if len(s):
            ax.plot(s.index, s.values, 'o-', label=lab)
    ax.set_xscale('log')
    ax.set_xlabel('consumers per substation (N_total)')
    ax.set_ylabel('hockey-stick fit R²')
    ax.set_title(f'{arm_name}: fit quality vs aggregation '
                 f'(penetration = {target:.0%})' if target else arm_name)
    ax.grid(alpha=.3)
    ax.legend(fontsize=8, title='averaging window')
    return ax
