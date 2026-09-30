# LCL survey column shift: impact on Paper A

**Goal.** Check whether Paper A uses the shifted LCL survey answers (UKDA SN 7857) and, if so, what changes.
**Branch.** `fix/lcl-survey-columns` (from `main`). Not merged.
**Changed.** `scripts/outputs.py`: `_lcl_base` now reads the heater count from Q303 (was Q304) with a corrected docstring; the Q248 gas filter is kept; `RHPP_LCL_BOXES` now points to `data/_rhpp_lcl_boxes_v2.pkl`. New: `scripts/lcl_survey_check.py` and `results/lcl_survey_check/` (including the regenerated `fig_rhpp.pdf/png`). Untouched: `paper/` (incl. the committed `fig_rhpp`), notebooks, the old `data/_rhpp_lcl_boxes.pkl`.

## Evidence of the bug
In `survey_answers.csv`, **column Qn holds the answers to the question labelled Q(n+1)** in `survey_questions.csv`. The shift is constant from Q01 to Q343. Q344 has no label, and label Q01 has no column. Checked against the documented answer sets in `survey_appliance.pdf` (`evidence_answer_sets.csv`):

| Question (form) | as labelled | corrected (col-1) |
|---|---|---|
| Q15 No. portable electric heater | Q304: 133 zeros, 1292 ones (TV-like) | **Q303**: 1777 zeros, 540 ones, 199 twos |
| Q15 No. television | Q305: 1433 zeros | **Q304**: 133 zeros, 1292 ones |
| Q10 central-heating fuel (documented: Gas, Electric, Oil, ...) | Q247: 100 % outside set (control-text) | Q246: 0 % outside set |
| Q17 display position (Kitchen, Hallway, ...) | Q328: 100 % outside (view frequencies) | Q327: 84 % inside; the rest is the free-text "Somewhere else" |
| Q6 caravan (text) | Q238: 100 % outside (numeric) | Q237: 0 % outside |

Independent consistency check: "TV count ≥ k" should coincide with "TV Type k answered". Agreement is 94 %/87 % (k=1/2) with the count taken from Q304, but 48 %/52 % with the count taken from Q305 as labelled. Full corrected mapping: `corrected_mapping.csv`.

## Where Paper A uses it
Only **one code path** reads the survey. `_lcl_base` (`scripts/outputs.py:1930`) is called from `rhpp_lcl_capacity` (:1962, line 1977), cached in `data/_rhpp_lcl_boxes.pkl` and plotted by `fig_rhpp` (:2557). The gas-central-heating filter uses Q248, which is already the correct column for the boiler question (form Q12). The heater count uses **Q304, which is actually the TV count** (it should be Q303). "Clean (0 portable heaters)" is therefore "0 TVs", and "heater-rich (≥ 2)" is "≥ 2 TVs".

**None of this reaches the manuscript.** `paper/hp_sensitivity_overleaf.tex` does not `\includegraphics` `fig_rhpp`. It cites no LCL result, has no clean vs heater-rich statement, and `lcl2013` in `references.bib` is never cited. The zero-HP control (Discussion, "0.28 kW") is computed on Kloten HP-free households (`outputs.py:476`), not LCL. `tab_transfer` says explicitly that RHPP has no faithful net load. `fig_rhpp.pdf/png` is an orphan file committed in d5cb1a8, and it is not in `replication.py` or `paper_results.ipynb`.

## Impact (`impact_summary.csv`; seed 0, 200 splits, 20+20 per pool, same window)
| Quantity | Original (committed fig) | Corrected | Δ abs | Manuscript |
|---|---|---|---|---|
| Households, clean / heater-rich | 53 / 627 | **866 / 120** | +813 / −507 | none |
| Base-load heating slope, clean (kW/°C/hh) | 0.0068 | 0.0072 | +0.0004 | none |
| Base-load heating slope, heater-rich | 0.0125 | **0.0211** | +0.0086 (+69 %) | none |
| Capacity error, clean, median [IQR] % | +8 [−1, +22] | +9 [−1, +23] | +1 | none |
| Capacity error, heater-rich | +16 [+2, +34] | **+28 [+11, +44]** | +12 (worse) | none |
| Oracle error, heater-rich | +15 | +27 | +12 (worse) | none |
| Net/HP slope, heater-rich | 1.15 | 1.28 | +0.13 | none |
| Slope ratio (both) | 0.99 / 1.01 | 1.00 / 1.00 | ≈ 0 | none |

Only 41 of the 53 old "clean" households survive as clean under the corrected mapping, and only 75 of the 627 old "heater-rich" households survive as heater-rich.

## Assessment
- **Unchanged:** every number and conclusion in the manuscript, since it uses none of these splits. The pilot-to-target slope ratio (≈ 1.00) is unaffected. The clean split is essentially unchanged in outcome.
- **Changed (figure only):** the heater-rich box in `fig_rhpp` is mislabelled and understates the damage. With real portable heaters the base-load slope is 1.7× larger and the capacity overestimate is about 28 %, not 16 %. This actually strengthens the "non-TCL response biases capacity upward" argument, if the figure is ever used.

## Decisions for Alex
1. Adopt Q303 in `_lcl_base`: **yes, done.**
2. Manuscript numbers to update: **none.**
3. Internal reviewers: **not informed.**

Reproduce: `PYTHONPATH=src:scripts python scripts/lcl_survey_check.py evidence|impact`. The original run reproduces `data/_rhpp_lcl_boxes.pkl` exactly.
