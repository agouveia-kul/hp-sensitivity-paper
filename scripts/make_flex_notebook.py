"""Write ``flex_temperature.ipynb``: one cell per step of ``flex_temperature.py``.

The notebook is generated so that its cells stay in step with the module; edit
the CELLS list below and re-run ``python scripts/make_flex_notebook.py``.
"""
import json

HEADER = """# Flexibility against temperature — experiments

Exploration of flexibility as a function of outdoor temperature for *Estimating
the Installed Capacity of Aggregated Thermostatically Controlled Loads from Net
Load and Temperature*. Each step calls one function of `scripts/flex_temperature.py`.
Step reports, expectations and deviations are in `FLEX_LOG.md`; figures go to
`figures/flex_temperature/`.

Every step pickles its results under `results/flex_temperature/`. With its
`REBUILD_*` flag at `False`, a step reloads them instead of recomputing."""

SETUP = """import os, sys
_root = os.getcwd()
while not os.path.isdir(os.path.join(_root, 'paper')) and os.path.dirname(_root) != _root:
    _root = os.path.dirname(_root)
os.chdir(_root)
for _p in ('scripts', 'src'):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import pandas as pd
import flex_temperature as FT
pd.set_option('display.width', 200)

# control flags: True recomputes the step and overwrites its pickles
REBUILD_STEP0 = False   # rebuilds the 1260-aggregate design and its hourly flexibility (about 15 s)
print('repo root:', _root)"""

CELLS = [
    ('markdown', """## Step 0 — Reproduce the current flexibility results

Rebuilds the published 20-split Kloten design (seed 0, 1260 aggregates) and its
hourly-reference actual flexibility, and checks every Section IV-F number of the
draft against its tolerance."""),
    ('code', """checks, step0 = FT.reproduce_flex(rebuild=REBUILD_STEP0)
print('rebuilt design identical to the paper cache:', step0['same_as_paper_cache'])
checks"""),
    ('code', """step0['context']"""),
]


def cell(kind, src):
    c = dict(cell_type=kind, metadata={}, source=src.splitlines(keepends=True))
    if kind == 'code':
        c.update(execution_count=None, outputs=[])
    return c


def main(path='flex_temperature.ipynb'):
    nb = dict(nbformat=4, nbformat_minor=5,
              metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                        'language_info': {'name': 'python', 'version': '3.12.10'}},
              cells=[cell('markdown', HEADER), cell('code', SETUP)] + [cell(k, s) for k, s in CELLS])
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    print('wrote', path)


if __name__ == '__main__':
    main()
