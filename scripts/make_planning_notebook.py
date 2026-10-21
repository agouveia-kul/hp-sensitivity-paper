"""Write ``planning_use_case.ipynb``: one cell per step of ``planning.py``.

The notebook is generated so that its cells stay in step with the module; edit
the CELLS list below and re-run ``python scripts/make_planning_notebook.py``.
"""
import json

HEADER = """# Planning use case — experiments

Experiments for the planning use case of *Estimating the Installed Capacity of
Aggregated Thermostatically Controlled Loads from Net Load and Temperature*.
Each step calls one function of `scripts/planning.py`. Step reports, expectations
and deviations are in `RESULTS_LOG.md`; figures go to `figures/planning/`.

Every step pickles its results under `results/planning/`. With its `REBUILD_*`
flag at `False`, a step reloads them instead of recomputing."""

SETUP = """import os, sys
_root = os.getcwd()
while not os.path.isdir(os.path.join(_root, 'paper')) and os.path.dirname(_root) != _root:
    _root = os.path.dirname(_root)
os.chdir(_root)
for _p in ('scripts', 'src'):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import pandas as pd
import planning as PL
pd.set_option('display.width', 200)

# control flags: True recomputes the step and overwrites its pickles
REBUILD_STEP0 = False
print('repo root:', _root)"""

CELLS = [
    ('markdown', """## Step 0 — Reproduce the baseline

Rebuilds the published 20-split Kloten design (seed 0, 1260 aggregates, target
aggregates drawn from all 1307 households without an HP) and checks every draft
number against its tolerance."""),
    ('code', """checks, step0 = PL.reproduce_baseline(rebuild=REBUILD_STEP0)
print('rebuilt design identical to the paper cache:', step0['same_as_paper_cache'])
checks"""),
]


def cell(kind, src):
    c = dict(cell_type=kind, metadata={}, source=src.splitlines(keepends=True))
    if kind == 'code':
        c.update(execution_count=None, outputs=[])
    return c


def main(path='planning_use_case.ipynb'):
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
