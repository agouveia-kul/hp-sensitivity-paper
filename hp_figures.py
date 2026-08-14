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

# The manuscript lives in paper/ and reads its figures relative to its own
# directory, so figures are written there rather than to a figures/ folder at
# the repository root. Overridable for callers that want them elsewhere.
FIGDIR = os.environ.get('HP_FIGDIR', os.path.join('paper', 'figures'))

# One colour scheme for the whole set.
C_CH = '#1f77b4'        # Switzerland
C_DE = '#d95f02'        # Germany
C_HP = '#c0392b'        # substations containing heat pumps
C_NOHP = '#7f8c8d'      # substations without
C_ALT = '#2c7fb8'       # secondary series
C_BASE = '#6a3d9a'      # the base-load-normalised sensitivity
C_AC = '#1a9988'        # cooling / air-conditioning load
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

    counts = meta.pivot_table(index='hp_ratio', columns='N_total',
                              values='N_hp', aggfunc='size')
    ax = axs[0]
    im = ax.imshow(counts.notna().astype(float), aspect='auto', origin='lower',
                   cmap='Blues', vmin=0, vmax=1.6)
    ax.set_xticks(range(len(counts.columns)))
    ax.set_xticklabels(counts.columns)
    ax.set_yticks(range(len(counts.index)))
    ax.set_yticklabels([f'{r:.0%}' for r in counts.index])
    for i in range(len(counts.index)):
        for j in range(len(counts.columns)):
            v = counts.iloc[i, j]
            if np.isfinite(v):
                ax.text(j, i, int(v), ha='center', va='center', fontsize=5.5)
    ax.set_xlabel('consumers per substation')
    ax.set_ylabel('heat pump penetration')
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
def fig2_slopes(d24, name='fig2_slopes', name_threshold='fig2_threshold',
                name_peak='fig2_slopes_peaknorm'):
    """Slope with and without heat pumps, the threshold temperature, and
    slope normalised by peak load -- three single-panel figures, saved
    separately so each can be placed independently in the manuscript.
    """
    no_hp = d24[d24.N_hp == 0]
    with_hp = d24[d24.N_hp > 0]

    fig1, ax1 = plt.subplots(figsize=(COL1, 2.7))
    bins = np.linspace(0, d24.slope.quantile(.99), 40)
    ax1.hist(no_hp.slope, bins=bins, color=C_NOHP, alpha=.75,
             label='no heat pumps', edgecolor='white', linewidth=.3)
    ax1.hist(with_hp.slope, bins=bins, color=C_HP, alpha=.65,
             label='with heat pumps', edgecolor='white', linewidth=.3)
    ax1.set_xlabel('thermal sensitivity (kW K$^{-1}$)')
    ax1.set_ylabel('substations')
    ax1.legend()
    fig1.tight_layout()
    path = save(fig1, name)

    fig2, ax2 = plt.subplots(figsize=(COL1, 2.7))
    ax2.hist(d24.T_threshold, bins=40, color=C_CH, alpha=.8,
            edgecolor='white', linewidth=.3)
    ax2.axvline(d24.T_threshold.median(), color='k', ls='--', lw=1.1,
               label=f'median {d24.T_threshold.median():.1f} °C')
    ax2.set_xlabel('threshold temperature (°C)')
    ax2.set_ylabel('substations')
    ax2.legend()
    fig2.tight_layout()
    path_threshold = save(fig2, name_threshold)

    fig3, ax3 = plt.subplots(figsize=(COL1, 2.7))
    bins_peak = np.linspace(0, d24.slope_per_peak.quantile(.99), 40)
    ax3.hist(no_hp.slope_per_peak, bins=bins_peak, color=C_NOHP, alpha=.75,
             label='no heat pumps', edgecolor='white', linewidth=.3)
    ax3.hist(with_hp.slope_per_peak, bins=bins_peak, color=C_HP, alpha=.65,
             label='with heat pumps', edgecolor='white', linewidth=.3)
    ax3.set_xlabel('sensitivity / peak load (K$^{-1}$)')
    ax3.set_ylabel('substations')
    ax3.legend()
    fig3.tight_layout()
    path_peak = save(fig3, name_peak)

    return [path, path_threshold, path_peak]


# ---------------------------------------------------------------------------
def fig3_heatmap(d24, name='fig3_confound', name_peak='fig3_confound_peaknorm',
                 name_base='fig3_confound_base'):
    """Central figure: median sensitivity and base load over consumers and
    penetration.

    The grid is a complete rectangle -- every one of the five penetration
    levels (0, 25, 50, 75, 100 %) realised at every N_total -- so there is no
    triangular structure and no missing corner to explain. Indexed by
    hp_ratio rather than absolute N_hp: at a fixed ratio, N_hp itself differs
    across columns (25 % of 4 consumers is 1 heat pump, 25 % of 48 is 12), so
    a row of constant ratio is not a row of constant N_hp. It is still the
    row that isolates the consumer-count effect at constant penetration,
    which is what this figure is for.

    Three independent panels are produced: the raw slope (kW/K), confounded
    with consumer count; the slope normalised by peak load (1/K), the
    statistic Section 2's detection test actually uses; and the fitted base
    load (kW) -- the hockey stick's temperature-independent term, which
    carries the same consumer-count confound the slope does, and separately
    shows heat-pump baseload running well above ordinary consumer baseload at
    every consumer count (the 0 %/100 % base-load comparison earlier in the
    notebook is one cell of this same surface). No cell in any panel is
    highlighted -- the confound pair is located from the data and stated in
    prose, in the cell that follows this figure, rather than drawn onto the
    heatmap.

    The colour scale is logarithmic in every panel. Each quantity spans well
    over a decade across the grid, and on a linear scale the low-penetration,
    small-N_total corner would be indistinguishable from zero.
    """
    paths = []
    panels = [
        ('slope', name, 'median thermal sensitivity (kW K$^{-1}$)', '{:.2f}'),
        ('slope_per_peak', name_peak,
         'median sensitivity / peak load (K$^{-1}$)', '{:.3f}'),
        ('base', name_base, 'median base load (kW)', '{:.1f}'),
    ]
    for value, cname, cblabel, fmt in panels:
        piv = d24.pivot_table(index='hp_ratio', columns='N_total', values=value,
                              aggfunc='median')
        vals = piv.values
        finite = vals[np.isfinite(vals)]
        norm = (mpl.colors.LogNorm(vmin=finite[finite > 0].min(), vmax=finite.max())
                if (finite > 0).all() else None)

        fig, ax = plt.subplots(figsize=(COL2, 3.0))
        im = ax.imshow(vals, aspect='auto', origin='lower', cmap='magma', norm=norm)
        ax.set_xticks(range(len(piv.columns)))
        ax.set_xticklabels(piv.columns)
        ax.set_yticks(range(len(piv.index)))
        ax.set_yticklabels([f'{r:.0%}' for r in piv.index])
        for i in range(len(piv.index)):
            for j in range(len(piv.columns)):
                v = vals[i, j]
                if np.isfinite(v):
                    level = norm(v) if norm is not None else v / np.nanmax(vals)
                    shade = 'white' if level < 0.55 else 'black'
                    ax.text(j, i, fmt.format(v), ha='center', va='center',
                            fontsize=5.5, color=shade)

        ax.set_xlabel('consumers per substation')
        ax.set_ylabel('heat pump penetration')
        ax.grid(False)
        cb = fig.colorbar(im, ax=ax, pad=0.02)
        cb.set_label(cblabel)
        cb.ax.tick_params(labelsize=6)
        fig.tight_layout()
        paths.append(save(fig, cname))
    return paths


# ---------------------------------------------------------------------------
def fig4_detection(load_fits, wpuq_load=None, det_ch=None, det_de=None,
                   name='fig4_detection'):
    """ROC for the candidate statistics, and detection against penetration.

    A ROC curve sweeps every threshold, so neither the curve nor its area
    depends on the operating point. What the shared threshold does fix is where
    on each curve a deployed detector would sit, so the Swiss-calibrated
    operating point is marked on each curve. Germany is marked at the Swiss
    threshold rather than its own, which is why its point sits at essentially
    zero false positives.

    Passing ``wpuq_load=None`` and ``det_de=None`` omits the German series
    entirely, giving a training-set-only figure for use before the validation
    dataset has been introduced.
    """
    show_de = wpuq_load is not None and det_de is not None
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.7))

    def mark(ax, curve, thr, col, mk):
        j = int((curve.threshold - thr).abs().values.argmin())
        ax.plot(curve.fpr.iloc[j], curve.tpr.iloc[j], mk, color=col, ms=5,
                markeredgecolor='k', markeredgewidth=.5, zorder=6)

    ax = axs[0]
    for stat, lab, ls, col in DETECTION_STATS:
        curve, auc = ha.roc(load_fits, stat)
        ax.plot(curve.fpr, curve.tpr, ls, color=col, label=f'{lab} ({auc:.3f})')
        thr = ha.detection_threshold(load_fits, stat, '24 h')['threshold']
        # mark(ax, curve, thr, col, M_CH)
    if show_de:
        curve, auc = ha.roc(wpuq_load, 'slope_per_peak')
        ax.plot(curve.fpr, curve.tpr, '-', color=C_DE,
                label=f'validation set, normalised ({auc:.3f})')
        # mark(ax, curve, det_de['threshold'], C_DE, M_DE)
    ax.plot([0, 1], [0, 1], ':', color='k', lw=.7)
    ax.set_xlabel('false positive rate')
    ax.set_ylabel('true positive rate')
    ax.legend(loc='lower right', bbox_to_anchor=(1.0, 0.12))

    ax = axs[1]
    # hp_ratio is exactly one of four values among substations with a heat
    # pump, so plotting it directly is exact -- no banding needed.
    series = [(det_ch, 'training set', C_CH, M_CH)]
    if show_de:
        series.append((det_de, 'validation set', C_DE, M_DE))
    for det, lab, col, mk in series:
        s = det['by_hp_ratio'].sort_index()
        ax.plot(s.index * 100, s.values, marker=mk, color=col, label=lab)
    ax.axhline(.8, color='k', ls='-.', lw=.8)
    ax.text(98, .755, '80 % detection', fontsize=6, ha='right')
    ax.set_xlabel('heat pump penetration (%)')
    ax.set_ylabel('detection rate')
    ax.set_ylim(0, 1.02)
    if show_de:
        ax.legend(loc='lower right')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
# Statistic styling shared by fig4_detection and fig_within_stratum_auc, so a
# colour means the same statistic in both. The base-normalised series gets its
# own hue rather than a second blue: it sits almost on top of the
# peak-normalised curve in both figures, so line style alone does not separate
# them.
DETECTION_STATS = [('slope', 'slope', '-', C_NOHP),
                   ('slope_per_peak', 'slope / peak load', '-', C_CH),
                   ('slope_per_base', 'slope / base load', '--', C_BASE)]


def fig_aggregation_quality(fits, response='Load', hp_ratio=0.5,
                            name='fig_aggregation_quality'):
    """Fit quality against both aggregation axes at once.

    One line per consumer count, against the averaging window. Both axes move
    the fit the same way, which is the point: consumer count and averaging
    window are two forms of the same operation.

    ``hp_ratio`` holds ETL penetration fixed, at 50 % by default, so the only
    thing varying between lines is the aggregation level. Pooling over
    penetration instead would blend the 0 % cells, whose R^2 is far lower,
    into every line and flatten the very effect the figure is drawn to show.
    Pass ``hp_ratio=None`` to recover the pooled view.

    Drawn as a single panel with a colour bar rather than a twelve-entry
    legend, and deliberately without the simultaneity-factor exponents that
    ``fig5_scaling`` carries alongside it.
    """
    fig, ax = plt.subplots(figsize=(COL1 + 0.5, 2.9))
    if hp_ratio is not None:
        fits = fits[np.isclose(fits['hp_ratio'], hp_ratio)]
    grid = ha.quality_grid(fits, response)
    cmap = plt.get_cmap('viridis')
    ns = list(grid.index)
    norm = mpl.colors.Normalize(vmin=min(ns), vmax=max(ns))

    for n in ns:
        ax.plot(range(len(grid.columns)), grid.loc[n], marker='o', ms=2.5,
                lw=1.1, color=cmap(norm(n)))
    ax.set_xticks(range(len(grid.columns)))
    ax.set_xticklabels(grid.columns)
    ax.set_xlabel('averaging window')
    ax.set_ylabel(f'median $R^2$, net load')
    ax.set_ylim(0.25, 1.0)

    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    cb = fig.colorbar(sm, ax=ax, pad=0.02, aspect=28)
    cb.set_label('consumers per substation, $N$', fontsize=7)
    cb.set_ticks([min(ns), 16, 32, max(ns)])
    cb.ax.tick_params(labelsize=6)
    fig.tight_layout()
    return save(fig, name)


def fig_nested_aggregation(nested_fits, name='fig_nested_aggregation'):
    """Fit quality against consumer count for one nested sequence.

    Each point is a single substation, and the substation at N contains the
    one at N-4, so the horizontal axis is literally the addition of consumers
    to a fixed aggregate rather than a comparison between independent draws.
    No band is drawn because there are no replicates to draw one from.
    """
    fig, ax = plt.subplots(figsize=(COL1 + 0.5, 2.9))
    res = [r for r in ['1 h', '4 h', '8 h', '16 h', '24 h']
           if r in set(nested_fits['resolution'])]
    cmap = plt.get_cmap('viridis')
    for k, r in enumerate(res):
        d = nested_fits[nested_fits.resolution == r].sort_values('N_total')
        ax.plot(d.N_total, d.r2, marker='o', ms=3, lw=1.2,
                color=cmap(k / max(len(res) - 1, 1)), label=r)
    ax.set_xlabel('consumers per substation, $N$')
    ax.set_ylabel('net-load $R^2$')
    ax.set_xticks(sorted(nested_fits.N_total.unique()))
    ax.legend(title='averaging window', fontsize=6.5, title_fontsize=6.5,
              loc='lower right', ncol=2, alignment='left')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig_within_stratum_auc(load_fits, resolution='24 h',
                           name='fig_within_stratum_auc'):
    """Detection AUC at known consumer count against AUC pooled over unknown.

    Solid lines score positives against negatives sharing the same N, so the
    size confound is absent by construction. Dotted lines are the same
    statistic pooled over every N, the operational case where N is unknown.
    The vertical distance between a pair is what not knowing N costs, and the
    ordering of the three statistics inverts between the two views.
    """
    fig, ax = plt.subplots(figsize=(COL1 + 0.6, 2.9))
    ax.set_xlim(2, 50)

    for stat, lab, ls, col in DETECTION_STATS:
        ns, aucs = [], []
        for n, g in load_fits.groupby('N_total'):
            _, a = ha.roc(g, stat, resolution)
            if np.isfinite(a):
                ns.append(n)
                aucs.append(a)
        ax.plot(ns, aucs, ls, marker=M_CH, color=col, label=lab, zorder=3)
        _, pooled = ha.roc(load_fits, stat, resolution)
        ax.axhline(pooled, color=col, ls=':', lw=1.1, zorder=2)
        ax.annotate(f'{pooled:.3f}', (50, pooled), color=col, fontsize=6,
                    va='center', ha='left', textcoords='offset points',
                    xytext=(3, 0))

    ax.set_xlabel('consumers per substation, $N$')
    ax.set_ylabel('detection AUC')
    ax.set_xticks([8, 16, 24, 32, 40, 48])
    ax.set_ylim(0.954, 1.004)
    ax.legend(loc='lower right', ncol=1, fontsize=6.5,
              title='solid: $N$ known   dotted: $N$ unknown',
              title_fontsize=6.5, alignment='left')
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
def fig6_sf(env_ch, rng_ch, env_de, rng_de, tcrit_ch, tcrit_de, name='fig6_sf',
            sf_cold_ch=None, sf_cold_de=None):
    """SF against temperature in both climates, with the design point marked.

    The temperature at which the fitted line would reach SF = 1 is annotated to
    show how far outside the data that extrapolation lies.

    ``sf_cold_ch`` / ``sf_cold_de`` are the medians of ``ha.sf_at_coldest``,
    each substation evaluated on its OWN coldest day. Pass them so the marker
    shows the same number the paper's table reports. Reading the median curve
    at the pooled coldest temperature instead gives a different quantity
    whenever the substations span more than one weather station -- 0.44 rather
    than 0.42 for Switzerland's three stations, though the two coincide for
    single-station WPUQ. Omitting them falls back to the curve value.
    """
    fig, ax = plt.subplots(figsize=(COL1 + 0.8, 2.9))
    # labels match the two column headers of the validation table in the paper
    for env, col, mk, lab, sf_cold in [
            (env_ch, C_CH, M_CH, 'Switzerland', sf_cold_ch),
            (env_de, C_DE, M_DE, 'WPUQ', sf_cold_de)]:
        obs, ext = env[env.observed], env[~env.observed]
        ax.fill_between(obs['T'], obs.sf_q25, obs.sf_q75, color=col, alpha=.18, lw=0)
        ax.plot(obs['T'], obs.sf_median, color=col, label=lab)
        ax.plot(ext['T'], ext.sf_median, color=col, ls='--', lw=1.0)
        cold = obs.iloc[0]
        y = float(cold.sf_median) if sf_cold is None else float(sf_cold)
        ax.plot(cold['T'], y, marker=mk, color=col, ms=5,
                markeredgecolor='k', markeredgewidth=.5, zorder=5)
        ax.annotate(f'{y:.2f}', (cold['T'], y),
                    textcoords='offset points', xytext=(6, 5), fontsize=6, color=col)
    ax.axhline(1.0, color='k', ls=':', lw=.9)
    ax.text(0.02, 0.96, 'full coincidence', fontsize=6, transform=ax.transAxes)
    # the extrapolation the paper argues against
    ax.annotate(f'SF = 1 requires {tcrit_ch:.0f} °C and {tcrit_de:.0f} °C '
                'respectively:\nfar outside the observed range',
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


# ---------------------------------------------------------------------------
def fig_hockey_stick_example(design, sid_no_hp, sid_all_hp,
                             name='fig_hockey_stick_example'):
    """Two real substations' hockey-stick fits, at 0 % and 100 % penetration.

    Every point plotted is a real day at that substation -- daily mean
    temperature and daily mean net load, rebuilt from the design and refitted
    with ``hp_common.fit_hockey_stick``, the same fit ``ha.fit_all`` produces
    at 24 h resolution. Nothing here is synthetic.

    Left, 0 % penetration: no heat pump on the substation, and every member
    is drawn clean of other electric heating too (the composition rule
    described above), yet the fit still finds a real, non-trivial slope --
    ordinary temperature-sensitive load (unlabelled heating, appliance use)
    that a raw-slope threshold cannot tell apart from a small heat pump.

    Right, 100 % penetration: every member has a heat pump. The kink is most
    of the signal, so base load, slope and threshold temperature are all
    identified far more precisely.

    Both panels share a y-axis, at the right panel's scale -- the point is
    not just the shape of each fit but how much bigger the 100 % substation's
    load is at every temperature, on the same total consumer count. The two
    substations are required to share N_total: the ratio of consumers with a
    thermostatic (heat pump) load is the only thing that differs between
    them, and each panel states that count so the comparison is checkable
    from the figure itself, not just asserted in code.
    """
    from hp_common import hockey_stick, fit_hockey_stick
    import hp_design as hd

    meta = design['meta']
    n_no_hp, n_all_hp = int(meta.loc[sid_no_hp, 'N_total']), int(meta.loc[sid_all_hp, 'N_total'])
    if n_no_hp != n_all_hp:
        raise ValueError(f'substations have different N_total ({n_no_hp} vs '
                         f'{n_all_hp}) -- pick a pair with the same consumer count')
    n_total = n_no_hp

    panels = [(sid_no_hp, f'0 % heat pump penetration ({n_total} consumers)', C_NOHP),
             (sid_all_hp, f'100 % heat pump penetration ({n_total} consumers)', C_HP)]

    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.9), sharey=True)
    for ax, (sid, label, col) in zip(axs, panels):
        temp = hd.get_series(design, sid, 'Temperature')
        load = hd.get_series(design, sid, 'Total_Load')
        d = pd.DataFrame({'T': temp.resample('D').mean(),
                          'y': load.resample('D').mean()}).dropna()
        base, slope, tbal, r2 = fit_hockey_stick(d['T'].to_numpy(), d['y'].to_numpy())
        Tg = np.linspace(d['T'].min(), d['T'].max(), 200)

        ax.scatter(d['T'], d['y'], s=8, color='0.6', alpha=.5, edgecolor='none',
                  label='daily mean')
        ax.plot(Tg, hockey_stick(Tg, base, slope, tbal), color=col, lw=1.8,
               label='hockey-stick fit')
        ax.set_title(label, fontsize=8)
        ax.set_xlabel('daily mean temperature (°C)')
        ax.text(0.5, 0.97,
               f'base {base:.1f} kW, slope {slope:.2f} kW/°C\n'
               f'$T_b$ {tbal:.1f} °C, $R^2$ {r2:.2f}, n={len(d)} days',
               transform=ax.transAxes, fontsize=6, va='top')
        ax.legend(fontsize=6, loc='center left')
    axs[0].set_ylabel('net load (kW)')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig_cooling_stick_example(T, load, n_homes=None, name='fig_hockey_stick_cooling_example'):
    """A Pecan Street (Austin) aggregate's cooling-stick fit.

    Not part of the substation design used elsewhere in this notebook --
    Pecan Street has no comparable ratio grid, only a fixed pool of AC-
    submetered homes (see the cooling-arm validation). ``load`` is expected
    to already be the sum of every usable household's whole-home consumption
    (each one built from its own appliance circuits, excluding
    ``grid``/``solar`` so PV feed-in cannot net any single home's load
    negative) against daily mean temperature, refitted with
    ``hp_common.fit_cooling_stick`` -- the mirror image of the heating
    hockey stick, with the kink above the balance temperature (AC turning
    on) instead of below it. It exists only to show the same model and
    fitting machinery extends to cooling, not to argue a detection result --
    the cooling arm's pool is far too small and structurally different
    (see the notebook discussion) for that.

    ``T`` and ``load`` are daily mean series (temperature in degC, load in
    kW), already aligned; ``n_homes`` is used only for the panel title.
    """
    from hp_common import cooling_stick, fit_cooling_stick

    d = pd.DataFrame({'T': T, 'y': load}).dropna()
    base, slope, tbal, r2 = fit_cooling_stick(d['T'].to_numpy(), d['y'].to_numpy())
    Tg = np.linspace(d['T'].min(), d['T'].max(), 200)

    fig, ax = plt.subplots(figsize=(COL1, 2.9))
    ax.scatter(d['T'], d['y'], s=8, color='0.6', alpha=.5, edgecolor='none',
              label='daily mean')
    ax.plot(Tg, cooling_stick(Tg, base, slope, tbal), color=C_AC, lw=1.8,
           label='cooling-stick fit')
    label = 'Pecan Street (Austin), cooling arm'
    if n_homes is not None:
        label += f' -- {n_homes} homes aggregated'
    ax.set_title(label, fontsize=8)
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('aggregate load (kW)')
    ax.text(0.03, 0.97,
           f'base {base:.1f} kW, slope {slope:.2f} kW/°C\n'
           f'$T_b$ {tbal:.1f} °C, $R^2$ {r2:.2f}, n={len(d)} days',
           transform=ax.transAxes, fontsize=6, va='top')
    ax.legend(fontsize=6, loc='center left')
    fig.tight_layout()
    return save(fig, name)


# ---------------------------------------------------------------------------
def fig_bathtub_example(T, load, n_homes=None, name='fig_bathtub_example'):
    """A Pecan Street (Austin) aggregate's bathtub-curve fit: heating below
    ``T_heat``, a flat deadband, cooling above ``T_cool``.

    Same real, PV-independent aggregate consumption as
    ``fig_cooling_stick_example`` -- this refits it with
    ``hp_common.fit_bathtub_stick`` instead of ``fit_cooling_stick``, adding
    a heating-side hockey stick sharing the same base load. Whether that
    second term is worth having is an R^2 comparison against the cooling-only
    fit, not assumed: Texas AC-first homes commonly carry electric backup
    heat, so a cold-end signature is plausible, not guaranteed.

    ``T`` and ``load`` are daily mean series (temperature in degC, load in
    kW), already aligned; ``n_homes`` is used only for the panel title.
    """
    from hp_common import bathtub_stick, fit_bathtub_stick, fit_cooling_stick

    d = pd.DataFrame({'T': T, 'y': load}).dropna()
    base, hs, th, cs, tc, r2 = fit_bathtub_stick(d['T'].to_numpy(), d['y'].to_numpy())
    _, _, _, r2_cool = fit_cooling_stick(d['T'].to_numpy(), d['y'].to_numpy())
    Tg = np.linspace(d['T'].min(), d['T'].max(), 300)

    fig, ax = plt.subplots(figsize=(COL1, 2.9))
    ax.scatter(d['T'], d['y'], s=8, color='0.6', alpha=.5, edgecolor='none',
              label='daily mean')
    ax.plot(Tg, bathtub_stick(Tg, base, hs, th, cs, tc - th), color=C_AC, lw=1.8,
           label='bathtub fit')
    ax.axvspan(th, tc, color=C_AC, alpha=.08, lw=0)
    label = 'Pecan Street (Austin), bathtub fit'
    if n_homes is not None:
        label += f' -- {n_homes} homes aggregated'
    # ax.set_title(label, fontsize=8)
    ax.set_xlabel('daily mean temperature (°C)')
    ax.set_ylabel('aggregate load (kW)')
    ax.text(0.03, 0.97,
           f'base {base:.1f} kW\n'
           f'heat {hs:.2f} kW/°C below $T_h$ {th:.1f} °C\n'
           f'cool {cs:.2f} kW/°C above $T_c$ {tc:.1f} °C\n'
           f'$R^2$ {r2:.3f} (cooling-only {r2_cool:.3f}), n={len(d)} days',
           transform=ax.transAxes, fontsize=6, va='top')
    ax.legend(fontsize=6, loc='center left')
    fig.tight_layout()
    return save(fig, name)
