# Data

This repository is **code + small cached results only**. The raw and intermediate
datasets are archived separately because they are too large for GitHub and, in some
cases, cannot be redistributed (see [LICENSING.md](LICENSING.md)).

## What ships in the repo (cached mode, ≈3 MB)

Enough to open and re-run `paper_results.ipynb` in cached mode:

- `paper/figures/*.png`, `paper/figures/*.pdf` — the compiled figures
- `paper/tables/*.tex` — the compiled tables
- `scratchpad/cross_table.csv`, `scratchpad/neea_rows.csv` — cross-dataset fit rows
- `scratchpad/cross_frames.pkl`, `scratchpad/neea_frames.pkl` — per-dataset daily frames for the montage

## Regeneration bundle (Tier A, ≈750 MB)

Needed only to rebuild artifacts with `REGENERATE = True`. Archived at:

> **DOI / URL: `<FILL IN — e.g. Zenodo record 10.5281/zenodo.XXXXXXX>`**

Unpack so the files land at these paths (relative to the repo root):

| File | Size | Feeds |
|------|-----:|-------|
| `data/design_factorial.pkl` | 274 MB | tab_sf, tab_capacity, tab_energy, energy-error and flex figures |
| `data/_combined_pool_cache.pkl` | 240 MB | flex figures (KLO population) |
| `data/15minute_data_austin/` | 167 MB | all four Austin bathtub/SF figures |
| `data/neea_power_2023.parquet` | 52 MB | NEEA WA/OR cross rows |
| `data/_wpuq_pool_cache.pkl` | 11 MB | tab_feeder_sweep |
| `data/neea_temp_2023.parquet` | 3.9 MB | NEEA temperature |
| `scratchpad/resstock_meta_sfd.parquet` | 3.7 MB | ResStock building selection |
| `data/factorial_fits.parquet` | 784 KB | fig_slope_capacity, tab_energy |
| `data/wpuq_real_feeder_sf.csv` | 32 KB | fig_real_feeder, feeder sweep, flex |
| `data/sf_transfer_load.csv`, `data/sf_transfer_shape.csv` | ~240 KB | transfer diagnostics |
| `data/capacity_two_methods_swiss.csv`, `data/capacity_two_methods_wpuq.csv` | ~270 KB | capacity cross-checks |

**ResStock is not in the bundle.** `outputs.build_cross_table(repull=True)` streams
~450 single-building profiles for the ASHP-electrification scenario directly from the
public NREL S3 bucket (`oedi-data-lake`), using only the 3.7 MB metadata file above.

## Fetching

`scripts/fetch_data.py` scaffolds the download once the DOI/URL is set. It reads the
manifest above, downloads the archive, and unpacks it into `data/` and `scratchpad/`.
Fill in `BUNDLE_URL` (and optionally per-file checksums) before use.

## Tier B — rebuilding the pool caches from raw

The pool caches (`_combined_pool_cache.pkl`, `_wpuq_pool_cache.pkl`, `design_*.pkl`)
were themselves built from the raw **Swiss smart-meter** dataset (~7.4 GB), the
**heapo** household dataset (~5 GB) and **Pecan Street** (Austin). Rebuilding them from
raw is optional and gated by licensing — those raw datasets are obtained from their
original providers, not from this archive.
