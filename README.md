# Installed capacity of aggregated TCLs from net load and temperature

Estimating the **installed capacity, energy and flexibility** of aggregated
thermostatically controlled loads (heat pumps, electric heating, air conditioning)
from low-voltage net load and ambient temperature, using a net-load "bathtub" fit
plus a transferable **simultaneity factor** (SF). Companion code for the paper
*Estimating the Installed Capacity of Aggregated Thermostatically Controlled Loads
from Net Load and Temperature*.

## Replicating the results

```bash
pip install -r requirements.txt
python -m jupyterlab paper_results.ipynb      # then run all cells
```

[`paper_results.ipynb`](paper_results.ipynb) recomputes **every figure and table** of the
paper from the raw datasets:

1. Download the datasets and place them under `data/` as described in
   **[DATA.md](DATA.md)**. The data is not in this repository. Eight of the eleven
   datasets are public downloads; Pecan Street, NEEA and RHPP need registration or a
   licence from their providers.
2. Run the notebook. Each cell checks the datasets its artifact needs, recomputes it,
   and compares recomputed tables line by line with the published ones.
3. Where a dataset is missing or in an unexpected format, the cell warns and shows the
   published result from `paper/` instead. The notebook runs to the end with any subset
   of the data, including none.

Recomputed artifacts go to `results/`; the published copies in `paper/` are never
overwritten. To check which datasets are in place, or to recompute headless:

```bash
python scripts/replication.py            # data status
python scripts/replication.py --run      # recompute everything
```

On machines that block unsigned programs, `jupyter lab` fails with *Access is denied*.
`python -m jupyterlab` works there.

## Repository layout

| Path | What |
|------|------|
| `paper_results.ipynb` | Recomputes and shows every figure and table (main entry point). |
| `scripts/replication.py` | Dataset checks, placement instructions and the recompute-or-fallback runner. |
| `scripts/outputs.py` | One generator per paper figure/table. |
| `scripts/utils.py` | Fitting primitives, data loaders and table display helpers. |
| `scripts/hp_*.py`, `scripts/pecan_street.py`, `src/heapo.py` | Model and data-pipeline modules. |
| `scripts/neea_extract.py`, `scripts/rhpp_extract.py`, `scripts/build_extra_frames.py` | Reduce the raw NEEA, RHPP, COFACTOR and other downloads to the series the generators use. |
| `scripts/gen_litreview.py` | Table I (literature review). |
| `paper/` | Manuscript sources, with the published figures (`figures/`) and tables (`tables/`). |

`HeatPump_Hypotheses.ipynb` is the exploratory working notebook (slopes, thresholds,
detectability, resolution) that preceded the paper; it is not required to reproduce it.

**Related repositories** (split from the original `NILM` repository in 2026-09):
[**NILM**](https://github.com/agouveia-kul/NILM) holds the earlier PV installed-capacity work, and [**hp-capacity-detection**](https://github.com/agouveia-kul/hp-capacity-detection)
holds the data-driven (XGBoost / PLS / ridge) heat-pump capacity estimation.
`scripts/hp_common.py`, `hp_pools.py`, `hp_capacity.py` and `src/heapo.py` are
shared with hp-capacity-detection (identical at the split).

## Data and licensing

See **[DATA.md](DATA.md)** for where to get each dataset and where to place it, and
**[LICENSING.md](LICENSING.md)** for the redistribution status of each one.

## Citation

If you use this code or results, please cite the paper (see `paper/`).
