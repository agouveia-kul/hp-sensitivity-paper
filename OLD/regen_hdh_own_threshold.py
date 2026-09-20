"""Refit the HDH parameterisation using each substation's own hockey-stick
threshold as its base temperature, instead of the fixed hp_common.HDH_THRESH
(12 degC) every substation shared before.

Only the HDH fits change -- the design and the hockey-stick (Load/SF) fits are
untouched, so this reads them from disk rather than rebuilding anything.
"""
import warnings

import pandas as pd

warnings.filterwarnings('ignore')

import hp_design as hd
import hp_analysis as ha

DESIGN_PATH = 'data/design_tri.pkl'
FITS_PATH = 'data/tri_fits.parquet'
HDH_PATH = 'data/tri_hdh_fits.parquet'


def main():
    design = hd.load_design(DESIGN_PATH)
    fits = pd.read_parquet(FITS_PATH)
    d24 = fits[(fits.response == 'Load') & (fits.resolution == '24 h') &
              (~fits.failed)]
    thresholds = d24.set_index('substation_id')['T_threshold']
    print(f'{len(thresholds)} substations with a hockey-stick threshold to borrow',
          flush=True)

    hdh_fits = ha.fit_hdh_all(design, thresholds=thresholds, verbose=True)
    hdh_fits.to_parquet(HDH_PATH)
    print(f'{len(hdh_fits)} HDH fits, {int(hdh_fits.failed.sum())} failed',
          flush=True)
    ok = hdh_fits[~hdh_fits.failed]
    print(f'threshold used: median {ok.hdh_threshold.median():.2f} degC, '
          f'range {ok.hdh_threshold.min():.2f}-{ok.hdh_threshold.max():.2f}',
          flush=True)


if __name__ == '__main__':
    main()
