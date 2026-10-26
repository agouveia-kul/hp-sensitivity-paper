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
REBUILD_STEP1 = False   # rebuilds the per-aggregate daily SF and hourly flexibility (about 15 s)
REBUILD_STEP2 = False   # rebuilds the per-bin P10 and median frame (a few seconds)
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
    ('markdown', """## Step 1 — Headroom and flexible energy against temperature

Per aggregate and 1 °C bin of heating-regime days: P_down, P_up and F under W1
(constant window, per hour of window) and W2 (Δt ∝ 1/(T_in − T), normalised), for
the estimate and the actual, per kW of true installed capacity. Primary setting
N = 50, N_hp = 25; repeated at N = 10 and 30, and with the pilot intercept b_h
added to the estimate (diagnostic only). Expectations are in `FLEX_LOG.md`."""),
    ('code', """step1 = FT.step1(rebuild=REBUILD_STEP1)
P = step1[FT.PRIMARY]
print(P['fig'])
for k, v in P['checks'].items():
    print(k, v)
P['peaks'].round(2)"""),
    ('code', """P['bins']"""),
    ('code', """for k in [(30, 15), (10, 5), 'primary_with_b']:
    print('=====', k)
    display(step1[k]['peaks'].round(2), step1[k]['bins'])"""),
    ('markdown', """## Step 1b — Window referenced to the threshold, capped

W3: Δt = Δt_5 (T_h − 5)/(T_h − T), capped at r·Δt_5 with r ∈ {3, 6, 12}
(12 h and 24 h caps for a 4 h or 2 h window at 5 °C). F relative to its 5 °C
value, estimate against actual. Requested by Alex after Step 3."""),
    ('code', """step1b = FT.step1b()
P1b = step1b[FT.PRIMARY]
print(P1b['fig'])
for k, v in P1b['checks'].items():
    print(k, v)
P1b['peaks'].round(3)"""),
    ('code', """for k in [(30, 15), (10, 5)]:
    print('=====', k)
    display(step1b[k]['peaks'].round(3))"""),
    ('markdown', """## Step 2 — Firm flexibility and aggregation

Per aggregate and 2 °C bin (merged to ≥ 10 days): P10/median of daily F across
days, actual and estimate, and P10 of the actual over the median of the estimate.
N = 10–50 at 50% penetration, next to the daily fit quality of Fig. 9. Two
diagnostics (D2 in `FLEX_LOG.md`): the spread net of temperature, and the days
of the 11–13 °C bin."""),
    ('code', """step2 = FT.step2(rebuild=REBUILD_STEP2)
print(step2['fig'])
for k, v in step2['checks'].items():
    print(k, v)
step2['summary'].round(3)"""),
    ('code', """step2['bins'].round(3)"""),
    ('code', """display(step2['detrended'].round(3)); step2['shoulder'].round(3)"""),
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
