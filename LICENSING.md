# Data licensing

The code in this repository is released under the repository's own licence. The
**source datasets are not**: each has its own terms, and none of them is in this
repository. Users download each dataset from its provider (see [DATA.md](DATA.md)).

> This is a working summary, not legal advice. Check each provider's current terms
> before redistributing any data or derivative.

| Dataset | Role in the paper | Terms | Redistribution |
|---|---|---|---|
| **HEAPO** (Brudermueller et al. 2025) | Kloten, Hg, MqO households | CC BY 4.0 ([Zenodo](https://zenodo.org/records/15056919)) | Allowed with attribution |
| **Swiss residential smart meters** (Kaiser et al. 2026) | Kloten households | CC BY 4.0 ([Zenodo](https://zenodo.org/records/21398769)) | Allowed with attribution |
| **WPuQ** (Schlemminger et al. 2022) | Hamelin feeder | CC BY 4.0 ([Zenodo](https://doi.org/10.5281/zenodo.5642902)) | Allowed with attribution |
| **COFACTOR Dataset 1** (Sørensen et al. 2026) | Oslo row, Oslo transfer | CC BY 4.0 | Allowed with attribution |
| **ResStock** (NREL) | Hennepin, King, Maricopa rows | Open (public S3) | Fetched at run time; no need |
| **HadCET** (Met Office) | Temperature for RHPP | Open Government Licence | Allowed with attribution |
| **BPA HPHC**, **NREL cold-climate ASHP** | Transfer rows in Table VI | Public download, U.S. DOE Heat Pump Database | Check the database's terms |
| **Pecan Street Dataport** | Austin (Figs. 2–3, Table II) | Dataport academic licence | **Not allowed** for raw data |
| **NEEA HEMS** | Washington and Oregon rows | NEEA data request and terms of use | **Not allowed** without NEEA's consent |
| **RHPP** (UK Data Service SN 8151) | GB transfer rows in Table VI | UKDS End User Licence | **Not allowed** |

## What the repository contains

- All code, the manuscript, and the published figures and tables (`paper/`).
- Small derived files: fitted cross-dataset parameters and daily aggregate frames
  (`scratchpad/cross_table.csv`, `neea_rows.csv`, `cross_frames.pkl`, `neea_frames.pkl`)
  and the ResStock building metadata used to draw the sample
  (`scratchpad/resstock_meta_sfd.parquet`). These are aggregate parameters and
  aggregate daily series, not individual consumption traces. Before publishing the
  repository, confirm that the NEEA and Pecan Street terms allow even these aggregates.
