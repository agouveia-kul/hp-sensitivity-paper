# -*- coding: utf-8 -*-
"""Download the regeneration data bundle (Tier A) for paper_results.ipynb.

Scaffold: set ``BUNDLE_URL`` to the archive's download URL (e.g. a Zenodo /
KU Leuven RDR record) and, optionally, fill ``SHA256`` for integrity checking.
Running this with a URL set downloads the archive and unpacks it so the files
land at the paths listed in DATA.md (relative to the repo root). Run from the
repo root:

    python scripts/fetch_data.py

Nothing here rehosts restricted data -- see LICENSING.md. ResStock is fetched
separately at runtime by ``outputs.build_cross_table(repull=True)``.
"""
import hashlib
import os
import sys
import tarfile
import urllib.request
import zipfile

# --- fill these in once the archive is published -----------------------------
BUNDLE_URL = ""                       # e.g. "https://zenodo.org/records/XXXXXXX/files/hp_bundle.zip"
SHA256 = ""                           # optional: sha256 of the downloaded archive

# Files the bundle must provide (see DATA.md). Used to report what is missing.
EXPECTED = [
    'data/design_factorial.pkl',
    'data/_combined_pool_cache.pkl',
    'data/_wpuq_pool_cache.pkl',
    'data/factorial_fits.parquet',
    'data/neea_power_2023.parquet',
    'data/neea_temp_2023.parquet',
    'data/wpuq_real_feeder_sf.csv',
    'data/sf_transfer_load.csv',
    'data/sf_transfer_shape.csv',
    'data/capacity_two_methods_swiss.csv',
    'data/capacity_two_methods_wpuq.csv',
    'data/15minute_data_austin',                 # directory
    'scratchpad/resstock_meta_sfd.parquet',
]


def _repo_root():
    root = os.getcwd()
    while not os.path.isdir(os.path.join(root, 'paper')) and os.path.dirname(root) != root:
        root = os.path.dirname(root)
    return root


def missing(root):
    return [p for p in EXPECTED if not os.path.exists(os.path.join(root, p))]


def _sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def fetch(root):
    archive = os.path.join(root, os.path.basename(BUNDLE_URL) or 'hp_bundle.zip')
    print(f'downloading {BUNDLE_URL} -> {archive}')
    urllib.request.urlretrieve(BUNDLE_URL, archive)
    if SHA256:
        got = _sha256(archive)
        if got != SHA256:
            sys.exit(f'checksum mismatch: expected {SHA256}, got {got}')
        print('checksum OK')
    print('unpacking into', root)
    if archive.endswith('.zip'):
        with zipfile.ZipFile(archive) as z:
            z.extractall(root)
    elif archive.endswith(('.tar.gz', '.tgz', '.tar')):
        with tarfile.open(archive) as t:
            t.extractall(root)
    else:
        sys.exit(f'unknown archive type: {archive}')
    print('done')


def main():
    root = _repo_root()
    miss = missing(root)
    if not miss:
        print('regeneration bundle already present -- nothing to fetch.')
        return
    print(f'{len(miss)} of {len(EXPECTED)} bundle items missing, e.g.:')
    for p in miss[:5]:
        print('  ', p)
    if not BUNDLE_URL:
        print('\nBUNDLE_URL is not set. Edit scripts/fetch_data.py (or download the')
        print('archive from the DOI in DATA.md and unpack it at the repo root) so the')
        print('files land at the paths listed in DATA.md.')
        return
    fetch(root)
    still = missing(root)
    print('OK' if not still else f'still missing after unpack: {still}')


if __name__ == '__main__':
    main()
