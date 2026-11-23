# Task — Check Paper A for the LCL survey column shift

**Repo:** `hp-sensitivity-paper` (Paper A, currently in internal review).
**Branch:** `fix/lcl-survey-columns`, from the current default branch. Do not merge; Alex reviews.
**Type:** a diagnostic and impact assessment first, then a fix only if Alex approves. **Do not edit the manuscript** (`paper/`).

## Background
While building a pool for Paper B (repo `hp-capacity-detection`, iteration 05a), the agent found that the **LCL survey answers are shifted by one column** relative to `survey_questions.csv`. For example, a filter meant for "number of portable electric heaters = 0" (answer Q304) actually selects "number of TVs = 0".

Paper A's `_lcl_base` appears to use the same mapping for its **clean** and **heater-rich** LCL household splits. Those splits may therefore be mislabelled.

## Rules
- Never modify, move or delete anything in `data/` (shared with other repos). New caches go to a new, clearly named file. Don't overwrite existing pickles such as `_rhpp_lcl_boxes.pkl`.
- Never overwrite existing results. Write new outputs to `results/lcl_survey_check/`.
- Don't edit the notebooks' logic cells or the manuscript.
- Seed everything; report numbers that get worse.

## Step 1 — Confirm the bug
1. Find `_lcl_base` and every other place that reads the LCL survey (search for `survey`, `Q304` and the survey file name).
2. Show the evidence of the shift with 3–5 questions, comparing the answer ranges with the expected ones. For example:
   - a yes/no question containing counts;
   - a count question containing yes/no codes;
   - the heating-type question containing codes from the neighbouring question.
3. Write down the correct question-to-column mapping. Test it: every question's answers must fall within its documented answer set.

## Step 2 — Where Paper A uses the affected splits
List every function, notebook cell (read-only), result file, table and figure in the manuscript that depends on the LCL survey-based splits, including:
- the clean / heater-rich definitions;
- any s₀ or non-TCL heating estimate from LCL;
- the zero-HP control;
- RHPP+LCL substations.

For each, give the file and line, the manuscript table/figure/section (from `paper/hp_sensitivity_overleaf.tex`), and the reported number.

## Step 3 — Impact
Recompute every affected quantity with the corrected mapping, keeping everything else identical: seeds, splits, windows, code paths. Report it as a table with the columns: quantity, manuscript value, recomputed value, absolute and relative change, manuscript location.

Include at least:
- the household counts in each split;
- the fillers' temperature response per split;
- every WAPE or error figure that uses them;
- any statement in the text that compares clean vs heater-rich.

## Step 4 — Report (`results/lcl_survey_check/REPORT.md`, ≤ 1 page)
- **Goal / Branch / Changed** (code touched, if any; ideally none beyond a corrected mapping in a new function).
- **Evidence of the bug**, and the corrected mapping.
- **Impact table.**
- **Assessment:** which conclusions of Paper A change, and which don't.
- **Decisions for Alex:**
  1. adopt the corrected mapping in Paper A's pipeline (y/n);
  2. which manuscript numbers need updating;
  3. whether the internal reviewers should be told now.

Stop after the report and wait.
