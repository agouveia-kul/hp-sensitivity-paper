# Data licensing & redistribution checklist

The code in this repository is released under the repository's own licence. The
**source datasets are not** — each has its own terms. This file tracks, per dataset,
whether the raw data or a derivative may be redistributed in the public archive
(see [DATA.md](DATA.md)).

> ⚠️ **This is a working checklist, not legal advice.** Confirm each row against the
> provider's current licence and your data-management-plan / DUA obligations
> **before** uploading anything to a public archive. When in doubt, ship only the
> small **derived** artifacts (fitted CSVs) and link to the original source for the
> raw data.

| Dataset | Role in the paper | Files (raw / derived) | Source & access | Redistribute? | Recommended action |
|---|---|---|---|---|---|
| **ResStock** (NREL End-Use Load Profiles) | Cross-dataset ASHP rows (Hennepin, King, Maricopa) | raw: public S3 building parquets · derived: `resstock_meta_sfd.parquet` | NREL / DOE, open (public domain–style) | ✅ Yes (but no need) | **Fetch, don't host.** `build_cross_table(repull=True)` streams from the public `oedi-data-lake` bucket. Only the 3.7 MB metadata is in the bundle. |
| **WPuQ** (German, Hamelin) | Real unseen feeder; German cross row | raw: WPuQ smart-meter data · derived: `wpuq_real_feeder_sf.csv` (32 KB) | Schlemminger et al. 2022, published open dataset | ⚠️ Likely, verify | Confirm the dataset's licence (commonly CC-BY). The tiny derived CSV is almost certainly shareable with attribution; link the original for the raw. |
| **Swiss smart-meter pool** (HEAPO + MeteoSwiss KLO) | Swiss substations; Kloten cross row; pool caches | raw: `Swiss_dataset/`, `heapo_data/` · derived: `_combined_pool_cache.pkl`, `_swiss_pool_cache.pkl`, `design_*.pkl` | HEAPO + smart-meter pool (research data) | ⛔ Verify before hosting | Treat as restricted until confirmed. Prefer shipping only fitted parameters (`cross_table.csv`) unless the licence permits the derived pool caches. |
| **Pecan Street** (Austin) | Austin bathtub/SF; Austin cross row | raw: `15minute_data_austin/` · derived: Austin fit params in `cross_table.csv` | Pecan Street Dataport, academic licence | ⛔ **Do not redistribute raw** | Dataport's licence generally forbids public redistribution. **Exclude `15minute_data_austin/` from the public archive**; point users to Dataport and ship only the derived fit params. |
| **NEEA** (Pacific NW EULR) | Washington & Oregon cross rows | raw: `POWER15/TEMPERATURE15` zips · derived: `neea_power_2023.parquet`, `neea_temp_2023.parquet`, `neea_rows.csv` | NEEA, gated behind a request form | ⚠️ Verify before hosting | Access is registration-gated, so redistribution of raw (and possibly the parquet derivatives) is likely restricted. Confirm with NEEA; otherwise ship only `neea_rows.csv` and document the request process. |
| **COFACTOR-Norway** (Dataset 1, Oslo/Bærum) | Oslo cross row (electric-heated pool) | raw: 29 hourly CSVs (`building_*.txt`) · derived: fit params in `cross_table.csv` | Sørensen et al. 2026, SINTEF repo, **CC BY 4.0** | ✅ Yes | Openly licensed (CC BY 4.0). Cite the data descriptor + dataset DOI `10.60609/3ab7-ez93`. Raw is redistributable with attribution if you ever need to host it. |
| **Carleton / Ottawa** (Saldanha & Beausoleil-Morrison) | Ottawa cross row (cooling arm) | raw: `Elec_loads.tar.gz` (23/12 houses) · derived: fit params in `cross_table.csv` | Carleton SBES, free with citation | ✅ Yes (cite) | Provided for research "with only a request to cite the paper." Redistributable with attribution; simplest is to link the SBES download page and ship only the derived params. |

## Practical upshot

- **Safe to publish now:** all code, the compiled figures/tables, and the small
  **derived fit-parameter** files (`cross_table.csv`, `neea_rows.csv`, the pool-fit
  outputs) — these are aggregate parameters, not raw consumption traces.
- **Fetch, don't host:** ResStock (public S3).
- **Confirm before hosting in the archive:** WPuQ raw, Swiss/heapo-derived pool
  caches, NEEA parquet derivatives.
- **Exclude from the public archive unless a DUA says otherwise:** Pecan Street
  `15minute_data_austin/` (raw).

If the restricted items are excluded, the archive shrinks below the 750 MB Tier-A
figure and the notebook still renders fully in cached mode from the small derived
artifacts already committed here.
