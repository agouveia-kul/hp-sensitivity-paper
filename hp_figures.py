"""Publication figures for the identifiability paper.

Seven figures, saved as PDF and PNG at 300 dpi. Sized for single-column width,
so fonts are set in points against a 3.5 inch panel and multi-panel figures are
whole-width multiples of that. No titles are drawn inside the figures; captions
belong in the manuscript.
"""

import os

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

import hp_analysis as ha

FIGDIR = 'figures'

# One colour scheme for the whole set.
C_CH = '#1f77b4'        # Switzerland
C_DE = '#d95f02'        # Germany
C_HP = '#c0392b'        # substations containing heat pumps
C_NOHP = '#7f8c8d'      # substations without
C_ALT = '#2c7fb8'       # secondary series
M_CH, M_DE = 'o', 's'

COL1, COL2 = 3.5, 7.2   # single- and double-column widths in inches


def use_style():
    mpl.rcParams.update({
        'figure.dpi': 120, 'savefig.dpi': 300,
        'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 8,
        'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
        'axes.grid': True, 'grid.alpha': 0.3, 'grid.linewidth': 0.4,
        'axes.spines.top': False, 'axes.spines.right': False,
        'lines.linewidth': 1.4, 'lines.markersize': 3.5,
        'legend.frameon': False, 'savefig.bbox': 'tight',
    })


def save(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIGDIR, f'{name}.{ext}'), dpi=300)
    return os.path.join(FIGDIR, name)


# ---------------------------------------------------------------------------
def fig1_design(meta, wpuq_sf, sf_real, name='fig1_design'):
    """Design coverage, and synthetic aggregation against the real feeder."""
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.7))

    counts = meta.pivot_table(index='N_hp', columns='N_total',
                              values='hp_ratio', aggfunc='size')
    ax = axs[0]
    im = ax.imshow(counts.notna().astype(float), aspect='auto', origin='lower',
                   cmap='Blues', vmin=0, vmax=1.6)
    ax.set_xticks(range(len(counts.columns)))
    ax.set_xticklabels(counts.columns)
    ax.set_yticks(range(len(counts.index)))
    ax.set_yticklabels(counts.index)
    for i in range(len(counts.index)):
        for j in range(len(counts.columns)):
            v = counts.iloc[i, j]
            if np.isfinite(v):
                ax.text(j, i, int(v), ha='center', va='center', fontsize=5.5)
    ax.set_xlabel('consumers per substation')
    ax.set_ylabel('heat pumps per substation')
    ax.grid(False)

    ax = axs[1]
    g = wpuq_sf.groupby('N_hp')['sf_cold']
    med = g.median()
    ax.fill_between(med.index, g.quantile(.25), g.quantile(.75),
                    color=C_DE, alpha=.20, lw=0)
    ax.plot(med.index, med.values, marker=M_DE, color=C_DE,
            label='synthetic substations')
    ax.axhline(sf_real, color='k', ls='--', lw=1.1,
               label='real measured feeder')
    # ax.set_xscale('log')
    ax.set_xlabel('heat pumps per substation')
    ax.set_ylabel('simultaneity factor at coldest day')
    # ax.set_ylim(0, 0.6)
    ax.legend(loc='lower right')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig2_slopes(d24, name='fig2_slopes'):
    """Slope with and without heat pumps, and the threshold temperature."""
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.7))
    no_hp = d24[d24.N_hp == 0]
    with_hp = d24[d24.N_hp > 0]

    ax = axs[0]
    bins = np.linspace(0, d24.slope.quantile(.99), 40)
    ax.hist(no_hp.slope, bins=bins, color=C_NOHP, alpha=.75,
            label='no heat pumps', edgecolor='white', linewidth=.3)
    ax.hist(with_hp.slope, bins=bins, color=C_HP, alpha=.65,
            label='with heat pumps', edgecolor='white', linewidth=.3)
    ax.set_xlabel('thermal sensitivity (kW K$^{-1}$)')
    ax.set_ylabel('substations')
    ax.legend()

    ax = axs[1]
    ax.hist(d24.T_threshold, bins=40, color=C_CH, alpha=.8,
            edgecolor='white', linewidth=.3)
    ax.axvline(d24.T_threshold.median(), color='k', ls='--', lw=1.1,
               label=f'median {d24.T_threshold.median():.1f} °C')
    ax.set_xlabel('threshold temperature (°C)')
    ax.set_ylabel('substations')
    ax.legend()
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig3_heatmap(d24, name='fig3_confound', mark='auto', split_after=50):
    """Central figure: median slope over consumers and heat pumps.

    The grid is triangular up to ``split_after`` consumers, where the heat pump
    count is free to reach the consumer count, and rectangular beyond it, where
    the submetered pool caps the heat pumps at 50 however many consumers are
    added around them. The rectangular part is what makes the confound legible:
    along a row of constant N_hp, nothing changes across those columns except
    the number of consumers, so the row measures the consumer effect on its own.

    Two cells are outlined to state the confound at its sharpest. With
    ``mark='auto'`` they are found from the data rather than fixed: the largest
    heat-pump-free substation, against the most heavily penetrated substation at
    ``split_after`` consumers that it still out-slopes. How wide that inversion
    band is depends strongly on what the heat-pump-free group is allowed to
    contain, so hard-coding the pair would misreport it after a change of
    composition rule.

    The colour scale is logarithmic. Sensitivity spans well over a decade across
    the grid, and on a linear scale the extension columns would saturate and
    flatten the whole triangle into one shade.
    """
    piv = d24.pivot_table(index='N_hp', columns='N_total', values='slope',
                          aggfunc='median')
    vals = piv.values
    finite = vals[np.isfinite(vals)]
    norm = (mpl.colors.LogNorm(vmin=finite[finite > 0].min(), vmax=finite.max())
            if (finite > 0).all() else None)

    fig, ax = plt.subplots(figsize=(COL2, 3.4))
    im = ax.imshow(vals, aspect='auto', origin='lower', cmap='magma', norm=norm)
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index)
    for i in range(len(piv.index)):
        for j in range(len(piv.columns)):
            v = vals[i, j]
            if np.isfinite(v):
                # position within the colour ramp decides the label colour
                level = norm(v) if norm is not None else v / np.nanmax(vals)
                shade = 'white' if level < 0.55 else 'black'
                ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                        fontsize=5.5, color=shade)

    # boundary between the complete triangle and the rectangular extension.
    # The bracket sits above the axes: inside it would collide with the top row.
    cols = list(piv.columns)
    top = len(piv.index) - .5
    if split_after in cols and split_after != cols[-1]:
        x0, x1 = cols.index(split_after) + .5, len(cols) - .5
        ax.axvline(x0, color='w', lw=1.4)
        ax.annotate('', xy=(x1, top + .25), xytext=(x0, top + .25),
                    arrowprops=dict(arrowstyle='<->', color='0.3', lw=.9),
                    annotation_clip=False)
        ax.text((x0 + x1) / 2, top + .45, 'heat pumps fixed, consumers added',
                ha='center', va='bottom', fontsize=6, color='0.3')
        ax.text((x0 - .5) / 2, top + .45, 'complete triangle',
                ha='center', va='bottom', fontsize=6, color='0.3')
    # the empty corner is a property of the grid, not missing data
    ax.text(len(cols) * .17, top * .78, 'N$_{hp}$ > N$_{total}$\nnot generated',
            ha='center', va='center', fontsize=6, color='0.45')

    # outline the two cells that carry the argument
    # if mark == 'auto':
    #     free = piv.loc[0, cols[-1]]
    #     col = piv[split_after].dropna().drop(0, errors='ignore')
    #     beaten = col[col < free]
    #     mark = (((0, cols[-1]), (int(beaten.index.max()), split_after))
    #             if len(beaten) else ())
    # for nhp, ntot in mark:
    #     if nhp in piv.index and ntot in cols:
    #         i, j = list(piv.index).index(nhp), cols.index(ntot)
    #         ax.add_patch(mpl.patches.Rectangle((j - .5, i - .5), 1, 1,
    #                                            fill=False, edgecolor='#00d0ff',
    #                                            lw=1.6, zorder=6))
    ax.set_xlabel('consumers per substation')
    ax.set_ylabel('heat pumps per substation')
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label('median thermal sensitivity (kW K$^{-1}$)')
    cb.ax.tick_params(labelsize=6)
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig4_detection(load_fits, wpuq_load, det_ch, det_de, name='fig4_detection'):
    """ROC for the candidate statistics, and detection against penetration.

    A ROC curve sweeps every threshold, so neither the curve nor its area
    depends on the operating point. What the shared threshold does fix is where
    on each curve a deployed detector would sit, so the Swiss-calibrated
    operating point is marked on each curve. Germany is marked at the Swiss
    threshold rather than its own, which is why its point sits at essentially
    zero false positives.
    """
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.7))

    def mark(ax, curve, thr, col, mk):
        j = int((curve.threshold - thr).abs().values.argmin())
        ax.plot(curve.fpr.iloc[j], curve.tpr.iloc[j], mk, color=col, ms=5,
                markeredgecolor='k', markeredgewidth=.5, zorder=6)

    ax = axs[0]
    styles = [('slope', 'slope', '-', C_NOHP),
              ('slope_per_peak', 'slope / peak load', '-', C_CH),
              ('slope_per_base', 'slope / base load', '--', C_ALT)]
    for stat, lab, ls, col in styles:
        curve, auc = ha.roc(load_fits, stat)
        ax.plot(curve.fpr, curve.tpr, ls, color=col, label=f'{lab} ({auc:.2f})')
        thr = ha.detection_threshold(load_fits, stat, '24 h')['threshold']
        # mark(ax, curve, thr, col, M_CH)
    curve, auc = ha.roc(wpuq_load, 'slope_per_peak')
    ax.plot(curve.fpr, curve.tpr, '-', color=C_DE,
            label=f'Germany, normalised ({auc:.2f})')
    # mark(ax, curve, det_de['threshold'], C_DE, M_DE)
    ax.plot([0, 1], [0, 1], ':', color='k', lw=.7)
    ax.set_xlabel('false positive rate')
    ax.set_ylabel('true positive rate')
    # ax.text(0.97, 0.06, 'markers: Swiss operating point', fontsize=6,
    #         ha='right', transform=ax.transAxes)
    ax.legend(loc='lower right', bbox_to_anchor=(1.0, 0.12))

    ax = axs[1]
    # Banded penetration: on a triangular grid nearly every cell realises its
    # own hp_ratio, so the exact ratio gives dozens of groups of a few
    # substations each. The bands are the levels the earlier ratio grid used.
    for det, lab, col, mk in [(det_ch, 'Switzerland', C_CH, M_CH),
                              (det_de, 'Germany', C_DE, M_DE)]:
        s = det['by_penetration'].dropna(subset=['rate'])
        ax.plot(s.x * 100, s.rate, marker=mk, color=col, label=lab)
    ax.axhline(.8, color='k', ls='-.', lw=.8)
    ax.text(98, .755, '80 % detection', fontsize=6, ha='right')
    ax.set_xlabel('heat pump penetration (%)')
    ax.set_ylabel('detection rate')
    ax.set_ylim(0, 1.02)
    ax.legend(loc='lower right')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig5_scaling(fits, name='fig5_scaling'):
    """Fit quality over resolution and aggregation, and the local exponents."""
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.7))
    cmap = plt.get_cmap('viridis')

    ax = axs[0]
    grid = ha.quality_grid(fits, 'Load')
    for k, n in enumerate(grid.index):
        ax.plot(range(len(grid.columns)), grid.loc[n], marker='o',
                color=cmap(k / max(len(grid.index) - 1, 1)), label=f'{n}')
    ax.set_xticks(range(len(grid.columns)))
    ax.set_xticklabels(grid.columns)
    ax.set_xlabel('averaging window')
    ax.set_ylabel('median $R^2$, net load')
    ax.set_ylim(0, 1)
    ax.legend(title='consumers', ncol=2)

    ax = axs[1]
    steps = [('1 h', '4 h'), ('4 h', '8 h'), ('8 h', '16 h'), ('16 h', '24 h')]
    labels = [f'{a}–{b}' for a, b in steps]
    for resp, col, mk in [('Load', C_CH, M_CH), ('SF', C_DE, M_DE)]:
        loc = ha.local_scaling_slopes(fits, resp)
        med = [loc[(loc['from'] == a) & (loc['to'] == b)].alpha.median()
               for a, b in steps]
        q1 = [loc[(loc['from'] == a) & (loc['to'] == b)].alpha.quantile(.25)
              for a, b in steps]
        q3 = [loc[(loc['from'] == a) & (loc['to'] == b)].alpha.quantile(.75)
              for a, b in steps]
        x = np.arange(len(steps))
        ax.fill_between(x, q1, q3, color=col, alpha=.18, lw=0)
        ax.plot(x, med, marker=mk, color=col,
                label='net load' if resp == 'Load' else 'simultaneity factor')
    ax.axhline(1.0, color='k', ls='--', lw=1.0)
    ax.text(0.05, 1.03, 'independent averaging', fontsize=6)
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels(labels)
    ax.set_xlabel('resolution step')
    ax.set_ylabel(r'local exponent $\alpha$')
    ax.set_ylim(0, 1.5)
    ax.legend(loc='upper left')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig6_sf(env_ch, rng_ch, env_de, rng_de, tcrit_ch, tcrit_de, name='fig6_sf'):
    """SF against temperature in both climates, with the design point marked.

    The temperature at which the fitted line would reach SF = 1 is annotated to
    show how far outside the data that extrapolation lies.
    """
    fig, ax = plt.subplots(figsize=(COL1 + 0.8, 2.9))
    for env, col, mk, lab in [(env_ch, C_CH, M_CH, 'Switzerland'),
                              (env_de, C_DE, M_DE, 'Germany')]:
        obs, ext = env[env.observed], env[~env.observed]
        ax.fill_between(obs['T'], obs.sf_q25, obs.sf_q75, color=col, alpha=.18, lw=0)
        ax.plot(obs['T'], obs.sf_median, color=col, label=lab)
        ax.plot(ext['T'], ext.sf_median, color=col, ls='--', lw=1.0)
        cold = obs.iloc[0]
        ax.plot(cold['T'], cold.sf_median, marker=mk, color=col, ms=5,
                markeredgecolor='k', markeredgewidth=.5, zorder=5)
        ax.annotate(f'{cold.sf_median:.2f}', (cold['T'], cold.sf_median),
                    textcoords='offset points', xytext=(6, 5), fontsize=6, color=col)
    ax.axhline(1.0, color='k', ls=':', lw=.9)
    ax.text(0.02, 0.96, 'full coincidence', fontsize=6, transform=ax.transAxes)
    # the extrapolation the paper argues against
    ax.annotate(f'SF = 1 requires {tcrit_ch:.0f} °C (CH), {tcrit_de:.0f} °C (DE):\n'
                'far outside the observed range',
                xy=(0.02, 0.78), xycoords='axes fraction', fontsize=6,
                color='0.25')
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('simultaneity factor')
    ax.set_ylim(0, 1.1)
    ax.legend(loc='center left', bbox_to_anchor=(0.02, 0.58))
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig7_flexibility(env, rng, name='fig7_flexibility'):
    """Upward and downward flexibility as fractions of installed capacity."""
    fig, ax = plt.subplots(figsize=(COL1 + 0.8, 2.9))
    obs, ext = env[env.observed], env[~env.observed]
    ax.fill_between(obs['T'], obs.down_q25, obs.down_q75, color=C_HP, alpha=.18, lw=0)
    ax.plot(obs['T'], obs.down_median, color=C_HP, label='downward, SF(T)')
    ax.plot(ext['T'], ext.down_median, color=C_HP, ls='--', lw=1.0)
    ax.fill_between(obs['T'], obs.up_q25, obs.up_q75, color=C_CH, alpha=.18, lw=0)
    ax.plot(obs['T'], obs.up_median, color=C_CH, label='upward, 1 − SF(T)')
    ax.plot(ext['T'], ext.up_median, color=C_CH, ls='--', lw=1.0)
    ax.axvspan(env['T'].min(), rng[0], color='0.85', alpha=.5, lw=0)
    ax.text(env['T'].min() + 0.4, 0.93, 'extrapolated', fontsize=6, color='0.35')
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('fraction of installed capacity')
    ax.set_ylim(0, 1)
    ax.legend(loc='center right')
    fig.tight_layout()
    return save(fig, name)
