# -*- coding: utf-8 -*-
"""Recompute the paper's figures and tables from the raw datasets.

``paper_results.ipynb`` drives this module. Each paper artifact is a *step* that
declares the datasets it needs. Before a step runs, every dataset it needs is
checked (files present, readable, expected columns/keys). If a check fails, or
the computation itself fails, a warning explains what is wrong and how to fix it,
and the published (cached) version of the artifact is shown instead. Recomputed
artifacts are written to ``results/`` -- the published copies in ``paper/`` are
never overwritten -- and every recomputed table and figure is compared with the
published one (tables line by line, figures pixel by pixel).

The raw data is not in the repository. Each dataset is downloaded by the user and
placed under ``data/`` as described in DATA.md (and in ``DATASETS`` below).

Command line (from the repo root, with scripts/ and src/ on the path)::

    python scripts/replication.py            # which datasets are in place
    python scripts/replication.py --run      # recompute everything, headless
    python scripts/replication.py --run tab_real,tab_transfer    # only these steps
"""
import contextlib
import difflib
import glob
import os
import re
import time
import traceback
import urllib.request
import warnings
import zipfile
from dataclasses import dataclass, field

import pandas as pd

PUB_FIG = os.path.join('paper', 'figures')
PUB_TAB = os.path.join('paper', 'tables')
RESULTS = 'results'
RES_FIG = os.path.join(RESULTS, 'figures')
RES_TAB = os.path.join(RESULTS, 'tables')
RES_WORK = os.path.join(RESULTS, 'work')


class ReplicationWarning(UserWarning):
    """A dataset is missing or malformed, or a recomputation failed."""


warnings.simplefilter('always', ReplicationWarning)


# ===========================================================================
# Format checks. Each returns a list of problems (empty = fine).
# ===========================================================================
def _file(path):
    return [] if os.path.isfile(path) else [f'missing file {path}']


def _files(pattern, min_n=1, what='file'):
    n = len(glob.glob(pattern))
    return [] if n >= min_n else [f'expected at least {min_n} {what}(s) matching {pattern}, found {n}']


def _columns(path, cols, **read_kw):
    if not os.path.isfile(path):
        return [f'missing file {path}']
    try:
        have = set(pd.read_csv(path, nrows=0, **read_kw).columns)
    except Exception as e:
        return [f'{path} cannot be read as CSV ({type(e).__name__}: {e})']
    miss = [c for c in cols if c not in have]
    return [f'{path} lacks column(s) {miss}'] if miss else []


def _zip(path, member, cols=None):
    if not os.path.isfile(path):
        return [f'missing file {path}']
    try:
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if re.search(member, n)]
            if not names:
                return [f'{path} has no member matching {member!r}']
            if cols:
                with z.open(names[0]) as fh:
                    have = set(pd.read_csv(fh, nrows=0).columns)
                miss = [c for c in cols if c not in have]
                if miss:
                    return [f'{path} -> {names[0]} lacks column(s) {miss}']
    except zipfile.BadZipFile:
        return [f'{path} is not a valid zip archive']
    return []


def _hdf5(path, keys):
    if not os.path.isfile(path):
        return [f'missing file {path}']
    try:
        import h5py
        with h5py.File(path, 'r') as h:
            miss = [k for k in keys if k not in h]
    except Exception as e:
        return [f'{path} cannot be opened as HDF5 ({type(e).__name__}: {e})']
    return [f'{path} lacks group(s) {miss}'] if miss else []


def _first(pattern):
    f = sorted(glob.glob(pattern))
    return f[0] if f else None


def _check_heapo():
    d = 'data/heapo_data'
    p = _file(f'{d}/meta_data/meta_data.csv') + _file(f'{d}/meta_data/households.csv')
    p += _files(f'{d}/smart_meter_data/15min/*.csv', 1000, 'household file')
    p += _files(f'{d}/weather_data/hourly/*.csv', 1, 'weather file')
    f = _first(f'{d}/smart_meter_data/15min/*.csv')
    if f:
        p += _columns(f, ['Household_ID', 'Timestamp', 'kWh_received_Total', 'kWh_received_HeatPump',
                          'kWh_received_Other'], sep=';')
    return p


def _check_swiss():
    from hp_pools import ELECTRIC_HEATING_FLAGS_FULL
    d = 'data/Swiss_dataset'
    p = _columns(f'{d}/metadata.csv', ['0_meter_id', '0_installation_type', '0_object_id', '1_hp',
                                        *ELECTRIC_HEATING_FLAGS_FULL], sep=';', encoding='utf-8-sig')
    p += _columns(f'{d}/weather_2020-2029.csv', ['station_abbr', 'reference_timestamp', 'tre200h0'], sep=';')
    p += _files(f'{d}/smart_meter_data/*.csv', 2000, 'meter file')
    f = _first(f'{d}/smart_meter_data/*.csv')
    if f:
        p += _columns(f, ['timestamp_utc', 'kWh_to_installation'], sep=';')
    return p


def _check_wpuq():
    return (_hdf5('data/2019_data_15min.hdf5', ['NO_PV', 'WITH_PV'])
            + _hdf5('data/2019_weather.hdf5', ['WEATHER_SERVICE/IN/WEATHER_TEMPERATURE_TOTAL']))


def _check_pecan():
    d = 'data/15minute_data_austin'
    return (_columns(f'{d}/15minute_data_austin.csv', ['dataid', 'local_15min', 'grid', 'solar', 'solar2',
                                                        'air1', 'furnace1'])
            + _columns(f'{d}/metadata.csv', ['dataid', 'city', 'state'])
            + _file(f'{d}/open-meteo-30.27N97.75W157m.csv'))


def _check_neea():
    return (_zip('data/POWER15_RAW_2023 v9.2.zip', r'\.csv$', ['ee_site_id', 'End Use', 'power', 'MIN_T_l',
                                                                  'state', 'cz'])
            + _zip('data/TEMPERATURE15 v9.2.zip', r'\.csv$', ['ee_site_id', 'regname', 'temp', 'MIN_T_l'])
            + _columns('data/SITES v9.2.csv', ['ee_site_id', 'state', 'hz', 'station_id'])
            + _columns('data/POINTS v9.2.csv', ['ee_site_id', 'circuit_label_type_desc']))


def _check_cofactor():
    from build_extra_frames import COFACTOR_DIR, COFACTOR_ELEC
    p = []
    for b in COFACTOR_ELEC:
        f = f'{COFACTOR_DIR}/building_{b}.txt'
        if not os.path.isfile(f):
            p.append(f'missing file {f}')
            continue
        head = open(f, encoding='utf-8', errors='replace').read(2000)
        m = re.search(r'Header_line;(\d+)', head)
        if not m or 'number_of_units;' not in head:
            p.append(f'{f} lacks the COFACTOR metadata header (Header_line, number_of_units)')
            continue
        p += _columns(f, ['TimeStamp', 'Tout', 'ElImp'], sep=';', skiprows=int(m.group(1)) - 1)
    return p


def _check_resstock():
    import outputs as O
    p = []
    try:
        meta = pd.read_parquet('scratchpad/resstock_meta_sfd.parquet', columns=['bldg_id', 'in.county'])
        if not set(c for c, _, _ in O.RESSTOCK_COUNTIES) <= set(meta['in.county']):
            p.append('scratchpad/resstock_meta_sfd.parquet lacks the three study counties')
    except Exception as e:
        p.append(f'scratchpad/resstock_meta_sfd.parquet cannot be read ({type(e).__name__})')
    url = ('https://oedi-data-lake.s3.amazonaws.com/' + O.RESSTOCK_R2.split('/', 1)[1]
           + '/weather/state=MN/G2700530_2018.csv')
    try:
        urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=15)
    except Exception as e:
        p.append(f'NREL ResStock bucket not reachable ({type(e).__name__}); an internet connection is needed')
    return p


def _check_rhpp():
    return (_zip('data/RHPP_GB.zip', r'processed_rhpp\d+\.csv$',
                 ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Hhp', 'Ehp', 'Edhw', 'Esp', 'Eboost'])
            + _zip('data/RHPP_GB.zip', r'8151_rhpp_metadata\.xlsx$'))


def _check_hadcet():
    f = 'data/hadcet/meantemp_daily_totals.txt'
    if not os.path.isfile(f):
        return [f'missing file {f}']
    try:
        import outputs as O
        t = O._hadcet()
    except Exception as e:
        return [f'{f} cannot be parsed ({type(e).__name__}: {e})']
    need = pd.date_range('2013-09-01', '2014-10-31')
    return [] if need.isin(t.index).all() else [f'{f} does not cover Sep 2013 - Oct 2014']


def _check_bpa():
    import outputs as O
    d = 'data/bpa_hphc'
    p = _files(f'{d}/*_hourly*.csv', 20, 'site file')
    f = _first(f'{d}/*_hourly*.csv')
    if f:
        p += _columns(f, ['site_id', 'local_datetime', 'OA_temp_F', 'HP_system_pwr_kW', 'backup_system_kW'])
    names = ' '.join(os.path.basename(x) for x in glob.glob(f'{d}/*_hourly*.csv'))
    miss = [s for s in O.BPA_INLAND if f'_{s}_' not in names] + [s for s in ('TAC', 'SNO') if f'_{s} ' not in names]
    return p + ([f'{d} lacks the site file(s) of {miss}'] if miss else [])


def _check_nrel():
    import outputs as O
    d = 'data/nrel_ccashp'
    p = _files(f'{d}/*HOUR*.csv', 10, 'site file')
    f = _first(f'{d}/*HOUR*.csv')
    if f:
        p += _columns(f, ['site_id', 'local_datetime', 'OA_temp_F', 'HP_system_pwr_kW', 'auxheat_pwr_kW'])
    names = ' '.join(os.path.basename(x) for x in glob.glob(f'{d}/*HOUR*.csv'))
    miss = [s for s in O.NREL_WA if f"site_{s.split()[1]}_" not in names]
    return p + ([f'{d} lacks the site file(s) of {miss}'] if miss else [])


# --- derived files built once from the raw download -------------------------
def _prepare_neea():
    import neea_extract
    if not (os.path.isfile(neea_extract.POWER_OUT) and os.path.isfile(neea_extract.TEMP_OUT)):
        print('extracting NEEA 2023 power and temperature from the raw zips (one-off, ~15 min) ...')
        neea_extract.extract_power_temp()


def _prepare_rhpp():
    if not (os.path.isfile('data/rhpp_daily.parquet') and os.path.isfile('data/rhpp_sites.parquet')):
        import rhpp_extract
        print('reducing the RHPP 2-minute site files to daily values (one-off, ~10 min) ...')
        rhpp_extract.main()


# ===========================================================================
# Datasets
# ===========================================================================
@dataclass
class Dataset:
    key: str
    name: str
    access: str          # open | registration | licence | network
    place: str           # where the files go, relative to the repo root
    source: str          # where to get it
    check: callable
    prepare: callable = None


DATASETS = {d.key: d for d in [
    Dataset('heapo', 'HEAPO (Swiss HP households, 2023)', 'open (CC BY 4.0)',
            'data/heapo_data/  (unzip heapo_data.zip: meta_data/, smart_meter_data/, weather_data/)',
            'https://zenodo.org/records/15056919', _check_heapo),
    Dataset('swiss', 'Swiss residential smart meters (Kloten, 2023)', 'open (CC BY 4.0)',
            'data/Swiss_dataset/  (unzip dataset.zip: metadata.csv, weather_2020-2029.csv, smart_meter_data/)',
            'https://zenodo.org/records/21398769', _check_swiss),
    Dataset('wpuq', 'WPuQ (Hamelin, DE, 2019)', 'open (CC BY 4.0)',
            'data/2019_data_15min.hdf5 and data/2019_weather.hdf5',
            'https://doi.org/10.5281/zenodo.5642902', _check_wpuq),
    Dataset('pecan', 'Pecan Street Dataport (Austin, 15-min)', 'licence (academic, no redistribution)',
            'data/15minute_data_austin/  (15minute_data_austin.csv, metadata.csv, '
            'open-meteo-30.27N97.75W157m.csv)',
            'https://dataport.pecanstreet.org', _check_pecan),
    Dataset('neea', 'NEEA HEMS 2023 (WA/OR)', 'registration (request form)',
            'data/POWER15_RAW_2023 v9.2.zip, data/TEMPERATURE15 v9.2.zip, data/SITES v9.2.csv, '
            'data/POINTS v9.2.csv',
            'https://neea.org/data/nw-end-use-load-research-project', _check_neea, _prepare_neea),
    Dataset('cofactor', 'COFACTOR Dataset 1 (Oslo/Baerum)', 'open (CC BY 4.0)',
            'data/cofactor_ds1/building_*.txt',
            'https://doi.org/10.60609/3ab7-ez93', _check_cofactor),
    Dataset('resstock', 'ResStock 2024.2 ASHP upgrade (NREL, public S3)', 'network (fetched at run time)',
            'nothing to place; needs internet (metadata: scratchpad/resstock_meta_sfd.parquet, in the repo)',
            'https://data.openei.org/s3_viewer?bucket=oedi-data-lake', _check_resstock),
    Dataset('rhpp', 'RHPP heat pump monitoring (GB, UKDS SN 8151)', 'licence (UK Data Service end-user licence)',
            'data/RHPP_GB.zip  (the UKDS "csv" download, renamed)',
            'https://datacatalogue.ukdataservice.ac.uk/studies/study/8151', _check_rhpp, _prepare_rhpp),
    Dataset('hadcet', 'HadCET daily Central England temperature', 'open (Open Government Licence)',
            'data/hadcet/meantemp_daily_totals.txt',
            'https://www.metoffice.gov.uk/hadobs/hadcet/data/meantemp_daily_totals.txt', _check_hadcet),
    Dataset('bpa', 'BPA HPHC heat pump field study (hourly)', 'public download (U.S. DOE Heat Pump Database)',
            'data/bpa_hphc/*_hourly*.csv', 'https://heatpumpdata.energy.gov', _check_bpa),
    Dataset('nrel', 'NREL cold-climate ASHP field study (hourly)', 'public download (U.S. DOE Heat Pump Database)',
            'data/nrel_ccashp/*HOUR*.csv', 'https://heatpumpdata.energy.gov', _check_nrel),
]}

_STATUS = {}          # dataset key -> list of problems (session cache)
_PREPARED = set()


_ROOTS = {'heapo': 'data/heapo_data', 'swiss': 'data/Swiss_dataset', 'pecan': 'data/15minute_data_austin',
          'cofactor': 'data/cofactor_ds1', 'bpa': 'data/bpa_hphc', 'nrel': 'data/nrel_ccashp',
          'hadcet': 'data/hadcet', 'rhpp': 'data/RHPP_GB.zip'}


def check(key, refresh=False):
    """Problems with one dataset (empty list = in place and in the expected format)."""
    if refresh or key not in _STATUS:
        root = _ROOTS.get(key)
        if root and not os.path.exists(root):
            _STATUS[key] = [f'not found ({root} does not exist)']
        else:
            try:
                probs = DATASETS[key].check()
            except Exception as e:
                probs = [f'check failed ({type(e).__name__}: {e})']
            _STATUS[key] = list(dict.fromkeys(probs))          # drop repeats, keep order
    return _STATUS[key]


# ===========================================================================
# Steps: one per generator; a generator may write several artifacts
# ===========================================================================
@dataclass
class Step:
    key: str
    label: str                     # the artifact's number in the paper
    outputs: list                  # published artifact names (fig_* -> PNG, tab_* -> .tex)
    needs: list
    build: callable
    minutes: str = ''              # rough runtime once the derived caches exist / first run
    captions: dict = field(default_factory=dict)


def _litreview():
    import gen_litreview
    gen_litreview.build(tabdir=RES_TAB)


def _tab_cross():
    import outputs as O
    O.build_cross_frames()
    O.build_cross_table()
    O.neea_fit()
    O.tab_cross()


def _o(name, *a, **k):
    def run():
        import outputs as O
        getattr(O, name)(*a, **k)
    return run


SWISS = ['heapo', 'swiss']
STEPS = {s.key: s for s in [
    Step('tab_litreview', 'Table I', ['tab_litreview'], [], _litreview, '<1'),
    Step('fig_austin_fits', 'Fig. 2', ['fig_austin_fits'], ['pecan'], _o('fig_austin_fits'), '1 / 3'),
    Step('tab_cross', 'Table II', ['tab_cross'], ['wpuq', 'heapo', 'swiss', 'cofactor', 'pecan', 'neea', 'resstock'],
         _tab_cross, '10 / 60'),
    Step('fig_flex_schedule', 'Fig. 3', ['fig_flex_schedule'], [], _o('fig_flex_schedule'), '<1'),
    Step('fig_slope_capacity', 'Fig. 4', ['fig_slope_capacity'], SWISS, _o('fig_slope_capacity'), '<1 / 30'),
    Step('fig_capacity_error', 'Fig. 5', ['fig_capacity_error'], SWISS, _o('fig_capacity_error'), '<1 / 30'),
    Step('flex_temperature_figure', 'Fig. 6', ['fig_flex_normalised'], SWISS, _o('flex_temperature_figure'), '<1 / 5'),
    Step('tab_real', 'Sec. V numbers', ['tab_real'], SWISS + ['wpuq'], _o('tab_real'), '2 / 5'),
    Step('tab_transfer', 'Table III', ['tab_transfer'],
         SWISS + ['wpuq', 'cofactor', 'rhpp', 'hadcet', 'bpa', 'nrel'], _o('tab_transfer'), '10 / 30'),
]}

RESULTS_LOG = {}      # step key -> dict(status, detail, seconds)


@contextlib.contextmanager
def _to_results():
    """Point every generator's output at results/ for the duration of a step."""
    import hp_figures as hf
    import outputs as O
    old = hf.FIGDIR, O.TABDIR, O.WORKDIR
    hf.FIGDIR, O.TABDIR, O.WORKDIR = RES_FIG, RES_TAB, RES_WORK
    for d in (RES_FIG, RES_TAB, RES_WORK):
        os.makedirs(d, exist_ok=True)
    try:
        yield
    finally:
        hf.FIGDIR, O.TABDIR, O.WORKDIR = old
        import matplotlib.pyplot as plt
        plt.close('all')        # generators leave figures open; don't let Jupyter show them twice


def _result_path(name, recomputed):
    if name.startswith('fig_'):
        return os.path.join(RES_FIG if recomputed else PUB_FIG, name + '.png')
    return os.path.join(RES_TAB if recomputed else PUB_TAB, name + '.tex')


def _norm_tex(path):
    """Table text for comparison: LaTeX comment lines, blank lines and trailing spaces dropped."""
    lines = open(path, encoding='utf-8').read().replace('\r\n', '\n').split('\n')
    return [ln.rstrip() for ln in lines if ln.strip() and not ln.lstrip().startswith('%')]


def compare_table(name):
    """(identical?, unified diff lines) between the recomputed and the published table."""
    a, b = _norm_tex(_result_path(name, False)), _norm_tex(_result_path(name, True))
    return a == b, list(difflib.unified_diff(a, b, 'published', 'recomputed', lineterm='', n=0))


def compare_figure(name):
    """(identical?, description) between the recomputed and the published PNG, pixel by pixel."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(_result_path(name, False)).convert('RGB'), dtype=np.int16)
    b = np.asarray(Image.open(_result_path(name, True)).convert('RGB'), dtype=np.int16)
    if a.shape != b.shape:
        return False, [f'image size differs: published {a.shape[1]}x{a.shape[0]}, recomputed {b.shape[1]}x{b.shape[0]}']
    share = float((np.abs(a - b).max(axis=2) > 0).mean())
    return share == 0.0, ([] if share == 0.0 else [f'{share * 100:.2f}% of the pixels differ'])


def _compare(name):
    return compare_table(name) if name.startswith('tab_') else compare_figure(name)


def _warn(msg):
    warnings.warn(msg, ReplicationWarning, stacklevel=3)


def _missing_message(step, bad):
    lines = [f'{step.label} ({", ".join(step.outputs)}): showing the PUBLISHED result, not a recomputation.']
    for k, probs in bad.items():
        d = DATASETS[k]
        lines.append(f'  - {d.name}: ' + '; '.join(probs[:3]) + (' ...' if len(probs) > 3 else ''))
        lines.append(f'      place it at {d.place}')
        lines.append(f'      get it from {d.source} [{d.access}]; see DATA.md')
    return '\n'.join(lines)


def run(key, recompute=True, show=True):
    """Recompute one step and display its artifacts; fall back to the published ones.

    Returns the status: 'recomputed', 'data missing' or 'failed' (the last two show
    the cached artifact). ``recompute=False`` only displays the published artifacts.
    """
    step = STEPS[key]
    status, detail, secs = 'cached (not requested)', '', 0.0
    if recompute:
        bad = {k: check(k) for k in step.needs if check(k)}
        if bad:
            status, detail = 'data missing', ', '.join(DATASETS[k].name for k in bad)
            _warn(_missing_message(step, bad))
        else:
            for d in (_result_path(n, True) for n in step.outputs):      # never show a stale result
                for f in (d, d[:-4] + '.pdf'):
                    if os.path.exists(f):
                        os.remove(f)
            t0 = time.time()
            try:
                for k in step.needs:
                    if DATASETS[k].prepare and k not in _PREPARED:
                        DATASETS[k].prepare()
                        _PREPARED.add(k)
                with _to_results():
                    step.build()
                missing = [n for n in step.outputs if not os.path.exists(_result_path(n, True))]
                if missing:
                    raise RuntimeError(f'the computation finished but did not write {missing}')
                status = 'recomputed'
            except Exception as e:
                status = 'failed'
                detail = f'{type(e).__name__}: {e}'
                repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                code = tuple(os.path.join(repo, d) + os.sep for d in ('scripts', 'src'))
                ours = [f for f in traceback.extract_tb(e.__traceback__)
                        if os.path.abspath(f.filename).startswith(code)
                        and not f.filename.endswith('replication.py')]
                where = (f'\n  raised in {os.path.relpath(ours[-1].filename)}:{ours[-1].lineno} ({ours[-1].name}): '
                         f'{ours[-1].line}') if ours else ''
                reads = ', '.join(DATASETS[k].name for k in step.needs) or 'no dataset'
                _warn(f'{step.label} ({", ".join(step.outputs)}): the recomputation failed, so the PUBLISHED '
                      f'result is shown.\n  {detail}{where}\n  This step reads: {reads}. A file in an unexpected '
                      f'format is the usual cause; check it against DATA.md.')
            secs = time.time() - t0
    RESULTS_LOG[key] = dict(status=status, detail=detail, seconds=secs)
    if status == 'recomputed':
        diffs = {n: _compare(n) for n in step.outputs}
        RESULTS_LOG[key]['matches_published'] = all(same for same, _ in diffs.values())
        RESULTS_LOG[key]['diffs'] = diffs
    if show:
        _display(step, status == 'recomputed')
    return status


def _display(step, recomputed):
    from IPython.display import Image, Markdown, display
    import utils as U
    tag = ('**recomputed** (`results/`)' if recomputed
           else '**published** version (`paper/`), not recomputed')
    for name in step.outputs:
        path = _result_path(name, recomputed)
        if name.startswith('fig_'):
            display(Markdown(f'**{step.label}** `{name}` - {tag}'))
            display(Image(filename=path, width=620 if 'montage' not in name else 520))
            if recomputed:
                same, how = RESULTS_LOG[step.key]['diffs'][name]
                display(Markdown('Pixel-identical to the published figure.' if same
                                 else f'**Differs from the published figure:** {how[0]}.'))
        else:
            display(Markdown(f'**{step.label}** - {tag}'))
            U.show_table(name, tabdir=os.path.dirname(path))
            if recomputed:
                same, diff = RESULTS_LOG[step.key]['diffs'][name]
                if same:
                    display(Markdown('Identical to the published table.'))
                else:
                    display(Markdown('**Differs from the published table:**\n```diff\n'
                                     + '\n'.join(diff[:60]) + ('\n...' if len(diff) > 60 else '') + '\n```'))


# ===========================================================================
# Reports
# ===========================================================================
def data_status(refresh=False):
    """One row per dataset: in place or not, where it goes, what needs it."""
    rows = []
    for k, d in DATASETS.items():
        probs = check(k, refresh)
        used = [s.label for s in STEPS.values() if k in s.needs]
        state = ('OK' if not probs
                 else 'MISSING' if all(p.startswith(('not found', 'missing file')) for p in probs)
                 else 'WRONG FORMAT / INCOMPLETE')
        rows.append({'dataset': d.name, 'status': state,
                     'needed for': ', '.join(used), 'access': d.access, 'place at': d.place,
                     'problem': '; '.join(probs[:2]) + (' ...' if len(probs) > 2 else '')})
    return pd.DataFrame(rows).set_index('dataset')


def summary():
    """One row per paper artifact: recomputed (and matching the published table) or cached."""
    rows = []
    for k, s in STEPS.items():
        r = RESULTS_LOG.get(k, dict(status='not run', detail='', seconds=0.0))
        match = r.get('matches_published')
        rows.append({'artifact': s.label, 'outputs': ', '.join(s.outputs), 'status': r['status'],
                     'matches published': ('' if match is None else ('yes' if match else 'NO')),
                     'detail': r['detail'], 'minutes': round(r['seconds'] / 60, 1)})
    return pd.DataFrame(rows).set_index('artifact')


def _main():
    import sys
    import matplotlib
    matplotlib.use('Agg')        # headless: no GUI backend (Tk aborts when the S3 download threads run)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    for p in ('scripts', 'src'):
        if os.path.abspath(p) not in sys.path:
            sys.path.insert(0, os.path.abspath(p))
    pd.set_option('display.width', 200, 'display.max_colwidth', 90)
    print(data_status()[['status', 'needed for', 'problem']].to_string())
    if '--run' in sys.argv:
        i = sys.argv.index('--run')
        keys = sys.argv[i + 1].split(',') if len(sys.argv) > i + 1 else list(STEPS)
        for k in keys:
            print(f'\n=== {STEPS[k].label}: {k}', flush=True)
            print('->', run(k, show=False), flush=True)
            for name, (same, diff) in RESULTS_LOG[k].get('diffs', {}).items():
                print(f'   {name}: identical to the published version' if same
                      else f'   {name} DIFFERS:\n   ' + '\n   '.join(diff[:40]))
        print('\n' + summary().drop(columns='outputs').to_string())


if __name__ == '__main__':
    _main()
