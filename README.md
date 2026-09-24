# Heat-pump sensitivity from LV net load and temperature

Estimating aggregated heat-pump (ETL) **installed capacity, energy and flexibility**
from low-voltage net load and ambient temperature, using a net-load "bathtub" fit
plus a transferable **simultaneity factor** (SF). Companion code and results for the
paper *Estimating aggregated heat-pump installed capacity, energy and flexibility
from LV net load and ambient temperature*.

## Quick start (cached mode — no large data needed)

```bash
pip install -r requirements.txt
jupyter lab paper_results.ipynb   # run top to bottom
```

[`paper_results.ipynb`](paper_results.ipynb) reproduces and displays **every figure
and table** in the paper. It runs in **cached mode**: it reads the small artifacts
committed under [`paper/figures/`](paper/figures), [`paper/tables/`](paper/tables)
and [`scratchpad/`](scratchpad) (≈3 MB total) and never touches the multi-GB raw
datasets. The committed notebook already has its figures embedded, so it renders in
full on GitHub without running anything.

## Repository layout

| Path | What |
|------|------|
| `paper_results.ipynb` | The results walkthrough (main entry point). |
| `scripts/utils.py` | Fitting primitives, data loaders, and the notebook's `show_fig` / `show_table` display helpers. |
| `scripts/outputs.py` | One function per paper figure/table; rebuilds it from source. |
| `scripts/hp_*.py`, `scripts/pecan_street.py`, `src/heapo.py` | Supporting model / data-pipeline modules. |
| `paper/figures/`, `paper/tables/` | Compiled figures (PDF+PNG) and LaTeX tables shown in the notebook. |
| `paper/` | The manuscript sources. |
| `OLD/` | Retired exploration scripts and notebooks (kept on disk, not version-controlled). |

`HeatPump_Hypotheses.ipynb` is the exploratory working notebook (slopes, thresholds,
detectability, resolution) that preceded the paper; it is not required to reproduce it.

**Related repositories** (split from the original `NILM` repository in 2026-09):
**NILM** holds the earlier PV installed-capacity work, and **hp-capacity-detection**
holds the data-driven (XGBoost / PLS / ridge) heat-pump capacity estimation.
`scripts/hp_common.py`, `hp_pools.py`, `hp_capacity.py` and `src/heapo.py` are
shared with hp-capacity-detection (identical at the split).

## Reproducing from source (optional)

The last section of the notebook regenerates artifacts behind a `REGENERATE` switch:

```python
REGENERATE = True     # rebuild every cached figure/table from source
```

This needs the **regeneration data bundle** (~750 MB), which is too large for GitHub
and is archived separately — see **[DATA.md](DATA.md)**. Download it into `data/` and
`scratchpad/` (a helper is scaffolded in [`scripts/fetch_data.py`](scripts/fetch_data.py)),
then run the notebook with `REGENERATE = True`. The one heavy step,
`outputs.build_cross_table(repull=True)`, re-pulls ~450 ResStock building profiles
from the public NREL S3 bucket and is left out of the default rebuild.

Two reproducibility tiers:

- **Tier A — regeneration bundle (~750 MB):** rebuilds all figures/tables from the
  cached pool/design intermediates. This is what the archive holds.
- **Tier B — from raw (~13 GB more):** rebuilding the pool caches themselves from the
  raw Swiss / heapo / Pecan Street data. Optional, and partly restricted by dataset
  licensing (see **[LICENSING.md](LICENSING.md)**).

## Data and licensing

Raw and intermediate data are **not** in this repository. See **[DATA.md](DATA.md)**
for what the bundle contains and where to get it, and **[LICENSING.md](LICENSING.md)**
for the redistribution status of each source dataset (Pecan Street, WPuQ, the Swiss
smart-meter pool, NEEA, ResStock).

## Citation

If you use this code or results, please cite the paper (see `paper/`).
