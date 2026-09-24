# Data

The raw data is **not in this repository**: several datasets are too large for GitHub,
and some cannot be redistributed. Each dataset is downloaded from its provider and
placed under `data/` at the repository root, at the paths below. `paper_results.ipynb`
then recomputes every figure and table from it.

Before each artifact is recomputed, the notebook checks the datasets it needs (files
present, readable, expected columns). If one is missing or in an unexpected format, the
notebook warns and shows the published result instead, so any subset of the data can
be used. To see what is in place without opening the notebook, run from the repo root:

```bash
python scripts/replication.py
```

## Which data each result needs

| Paper artifact | HEAPO | Swiss meters | WPuQ | Pecan St | NEEA | COFACTOR | ResStock | RHPP | HadCET | BPA | NREL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Table I (literature) | | | | | | | | | | | |
| Fig. 2, Fig. 3 (Austin fits) | | | | ✓ | | | | | | | |
| Table II (cross-dataset) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | | |
| Fig. 4 (flexibility schematic) | | | | | | | | | | | |
| Figs. 5–10, Tables III–IV (Kloten) | ✓ | ✓ | | | | | | | | | |
| Table V (real aggregates) | ✓ | ✓ | ✓ | | | | | | | | |
| Table VI (transfer) | ✓ | ✓ | ✓ | | | ✓ | | ✓ | ✓ | ✓ | ✓ |

HEAPO, the Swiss smart meters, WPuQ, COFACTOR, ResStock, HadCET, BPA and NREL are
openly licensed, so most results can be reproduced without any data agreement. Pecan
Street, NEEA and RHPP need registration or a licence from their providers.

## Folder layout

```
data/
├── heapo_data/                      HEAPO
│   ├── meta_data/  smart_meter_data/  weather_data/  reports/
├── Swiss_dataset/                   Swiss residential smart meters
│   ├── metadata.csv  weather_2020-2029.csv  smart_meter_data/  (2,447 files)
├── 2019_data_15min.hdf5             WPuQ
├── 2019_weather.hdf5                WPuQ
├── 15minute_data_austin/            Pecan Street
│   ├── 15minute_data_austin.csv  metadata.csv  open-meteo-30.27N97.75W157m.csv
├── POWER15_RAW_2023 v9.2.zip        NEEA
├── TEMPERATURE15 v9.2.zip           NEEA
├── SITES v9.2.csv                   NEEA
├── POINTS v9.2.csv                  NEEA
├── cofactor_ds1/building_*.txt      COFACTOR
├── RHPP_GB.zip                      RHPP
├── hadcet/meantemp_daily_totals.txt HadCET
├── bpa_hphc/*_hourly.csv            BPA
└── nrel_ccashp/*HOUR*.csv           NREL
```

`data/` may be a folder, a symbolic link or a directory junction (for a shared data
drive). It is gitignored.

## Datasets

### HEAPO — Swiss heat-pump households (Kloten and other Zurich stations)

- **Source:** Brudermueller et al., 2025, [Zenodo 10.5281/zenodo.15056919](https://zenodo.org/records/15056919), `heapo_data.zip` (458 MB, 5.3 GB unzipped).
- **Licence:** CC BY 4.0.
- **Place:** unzip so that `data/heapo_data/meta_data/meta_data.csv` and
  `data/heapo_data/smart_meter_data/15min/<household>.csv` exist.

### Swiss residential smart meters (Kloten, 2023)

- **Source:** Kaiser et al., 2026, [Zenodo 10.5281/zenodo.21398769](https://zenodo.org/records/21398769), `dataset.zip` (904 MB).
- **Licence:** CC BY 4.0.
- **Place:** unzip into `data/Swiss_dataset/` so that `data/Swiss_dataset/metadata.csv`,
  `data/Swiss_dataset/weather_2020-2029.csv` and `data/Swiss_dataset/smart_meter_data/`
  exist (rename the unzipped folder if needed).

### WPuQ — Hamelin, Germany (2019)

- **Source:** Schlemminger et al., 2022, [Zenodo 10.5281/zenodo.5642902](https://doi.org/10.5281/zenodo.5642902).
  Download the two single files `2019_data_15min.hdf5` (459 MB) and `2019_weather.hdf5` (31 MB).
- **Licence:** CC BY 4.0.
- **Place:** `data/2019_data_15min.hdf5`, `data/2019_weather.hdf5`.

### Pecan Street Dataport — Austin, Texas (15 min)

- **Source:** [Pecan Street Dataport](https://dataport.pecanstreet.org), after
  registration (academic access is available). Download the *15-minute data, Austin*
  sample (`15minute_data_austin.csv`) and its `metadata.csv`.
- **Licence:** Dataport academic licence. Do not redistribute the raw data.
- **Temperature:** hourly 2 m temperature from the
  [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api)
  for latitude 30.27, longitude −97.75, covering the dates of the load data, exported as
  CSV with times in GMT. Save it as `open-meteo-30.27N97.75W157m.csv`. The file keeps
  Open-Meteo's three header lines, then `time,temperature_2m (°C)`.
- **Place:** all three files in `data/15minute_data_austin/`.

### NEEA — Home Energy Metering Study (HEMS), Washington and Oregon, 2023

- **Source:** [Northwest End-Use Load Research Project](https://neea.org/data/nw-end-use-load-research-project),
  data release v9.2, obtained through NEEA's data request form.
- **Licence:** NEEA data-use terms. Do not redistribute.
- **Place:** `data/POWER15_RAW_2023 v9.2.zip` (1.9 GB), `data/TEMPERATURE15 v9.2.zip`
  (170 MB), `data/SITES v9.2.csv`, `data/POINTS v9.2.csv`, with the file names unchanged.
- **First run:** the notebook extracts the mains, ductless-HP and outdoor-temperature
  series once into `data/neea_power_2023.parquet` and `data/neea_temp_2023.parquet`.

### COFACTOR Dataset 1 — Oslo/Bærum apartment blocks

- **Source:** Sørensen et al., 2026, *Data in Brief* 65:112580,
  [DOI 10.60609/3ab7-ez93](https://doi.org/10.60609/3ab7-ez93), `COFACTOR_Res_Dataset1_files.zip` (33 MB).
- **Licence:** CC BY 4.0.
- **Place:** the `building_*.txt` files in `data/cofactor_ds1/`. The electric-heated
  blocks 6470–6478 and 6499 are required.

### ResStock — NREL End-Use Load Profiles, 2024.2 release, ASHP upgrade

- **Source:** NREL's public [oedi-data-lake](https://data.openei.org/s3_viewer?bucket=oedi-data-lake)
  S3 bucket. The notebook streams the 450 buildings it needs at run time (150 per county:
  Hennepin MN, King WA, Maricopa AZ). The building metadata it samples from
  (`scratchpad/resstock_meta_sfd.parquet`) is in the repository.
- **Licence:** open.
- **Place:** nothing. An internet connection is needed.

### RHPP — Renewable Heat Premium Payment heat-pump monitoring (GB)

- **Source:** UK Data Service, [SN 8151](https://datacatalogue.ukdataservice.ac.uk/studies/study/8151).
  Registration and the UKDS End User Licence are required. Download the CSV edition.
- **Licence:** UKDS End User Licence. Do not redistribute.
- **Place:** the downloaded zip, renamed to `data/RHPP_GB.zip` (it contains
  `UKDA-8151-csv/csv/processed_rhpp*.csv` and the metadata spreadsheet).
- **First run:** the notebook reduces the 2-minute site files once to
  `data/rhpp_daily.parquet` and `data/rhpp_sites.parquet`.

### HadCET — daily Central England temperature

- **Source:** Met Office Hadley Centre,
  [meantemp_daily_totals.txt](https://www.metoffice.gov.uk/hadobs/hadcet/data/meantemp_daily_totals.txt).
- **Licence:** Open Government Licence.
- **Place:** `data/hadcet/meantemp_daily_totals.txt`.

### BPA HPHC and NREL cold-climate ASHP field studies

- **Source:** [U.S. DOE Heat Pump Database](https://heatpumpdata.energy.gov): the hourly
  site files of the BPA *High-Performance High-Capacity Heat Pump* field study and of the
  NREL *cold-climate ASHP* field validation.
- **Licence:** public download; check the database's terms of use before redistributing.
- **Place:** the BPA files (named like `BPA_HPHC_HP_2026_CEC 11_hourly.csv`) in
  `data/bpa_hphc/`, and the NREL files (named like `NREL_2021_2023_site_10_hp_HOUR.csv`)
  in `data/nrel_ccashp/`, with the file names unchanged. Table VI needs the inland BPA
  sites CEC 11–13, 31–33, 41 and INL 02, 41, 42, 44, 46, the Tacoma (TAC) and Snohomish
  (SNO) sites, and NREL sites 1, 2, 4–8 and 11–13.

## Derived caches

The first recomputation writes intermediate files next to the raw data, all with names
starting with `_` (for example `data/_combined_pool_cache.pkl` for the merged Swiss
household pool and `data/_kloten_design.pkl` for the 1,260 Kloten aggregates). Later runs
reuse them. Delete them to rebuild everything from the raw files. Recomputed figures,
tables and cross-dataset work files go to `results/`.

## Datasets not needed for the paper

`scripts/build_extra_frames.py` can also build the London (Low Carbon London heat-pump
trial) and Ottawa (Carleton) aggregates for exploratory use. The paper does not report
them: the London row is commented out of Table II, and Ottawa appears in neither table.
