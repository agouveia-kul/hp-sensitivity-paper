# Revision log — supervisor comments

Manuscript: `paper/hp_sensitivity_overleaf.tex`. Branch: `revision/supervisor-comments`, cut from `main` (a1e7d37). Alex merges.
The Phase 1 analysis is in `review/phase1_message_map.md`.

Status values: `done` · `partly` · `needs Alex` · `declined (reason)`. While work is pending, a row reads `open (fix)`, where *fix* is the step planned to close it.

Annotated PDF: `paper/TCL_Quantification_rdh.pdf` (13 pages). Its 59 annotations, with verbatim comment text, are in `review/annotations_rdh.md`. All pages and anchors below were checked against it, and they match R01–R57 one to one. The extra rows are an untexted highlight on "per cent" (part of R01) and two reply threads (R15, R37).

**The reviewed version differs slightly from `main`.** Its Table I is an older variant: rows [13]–[15] read PV/EV/HP Detection, Loads/DER Regional NILM, Loads Disaggregation, and the HP block has no Rou23 row. The current `tab_litreview.tex` is newer. The text of pp. 1, 3, 4 and 5 matches the current `.tex`. Equation numbers match.

Missing input: the Supervisor 2 marks. Alex does not have them yet (16 Oct). The S2 rows stay open, and S1 is checked against them once they arrive.

## Comment tracker

| ID | p. | Anchor | Comment | Action taken | Commit | Status |
|---|---|---|---|---|---|---|
| R01 | 1 | "On 200 German LV feeders … over twenty per cent" | Too anecdotal | ¶1 now opens with the European scale (EHPA: 2.9 M sold in 2025, +13%, 21 countries; stock 29.3 M); the 200-feeder figure is one supporting sentence | S1 | done |
| R02 | 1 | same | Use country/region figures | as R01; new ref `Ehp26` (EHPA market-data page, checked 16 Oct 2026) | S1 | done |
| R03 | 1 | the word "were" in "networks that were not sized for it" | "maybe" | "…loads LV networks that may not have been sized for this load" (Alex: as recommended) | S1 | done |
| R04 | 1 | "rooftop solar" | Injection peaks go the other way | rooftop solar dropped from the peak sentence; PV now introduced in ¶8 | S1 | done |
| R05 | 1 | "network operators must know how much thermostatic load…" | Why is it interesting? | new ¶3: three reasons the DSO needs installed capacity (scenarios, synchronised peak, design peak = capacity × SF), plus flexibility | S1 | done |
| R06 | 1 | "It meters aggregated net load" | "Often only aggregated net load is measured (smart meter level? at the substation?)" | ¶4: net load metered at the substation or feeder head; household smart meters where rolled out, access often restricted | S1 | done |
| R07 | 1 | same | "It" = the DSO | "the DSO" named as subject throughout ¶4 | S1 | done |
| R08 | 1 | "It" | Too many "it"s | "it" pass over the abstract, Sec. I and the rewritten Sec. II passages; the remaining Sec. II "it"s refer to the sentence subject | S1, S2 | done |
| R09 | 1 | "remain largely synthetic at the substation" | What does this mean? | "validated mostly on synthetic substation aggregates rather than on measured substation data" | S1 | done |
| R10 | 1 | title, "from Net Load and Temperature" | Explain setup and pilot | Sec. I ¶11 states the setup: feeder net load and temperature, plus the SF sensitivity calibrated once on a submetered pilot; their ratio gives the capacity. Abstract sentences 3–5 do the same | S1 | done |
| R11 | 2 | "service-transformer" | What is it? | Alex removed the transformer clause and the Azz24 row of Table I | S1b | done |
| R12 | 2 | "The simultaneity of an aggregated TCL population…" | Use this at the beginning | the planning role of the SF moved into ¶3 (motivation); ¶9 keeps only the prior-work limitation | S1 | done |
| R13 | 2 | "submetering the target feeder" | Say "at household level" | "without submetering the households of the target feeder" | S1 | done |
| R14 | 2 | contribution 1, SF slope sentence | Not understandable yet | contribution 1 rewritten without SF slope or balance point | S1 | done |
| R15 | 2 | same | Maybe not needed | the highlighted sentence removed | S1 | done |
| R16 | 2 | contribution 2 | A full conclusion; keep short | contribution 2 is one sentence listing what is evaluated, with no results | S1 | done |
| R17 | 3 | "same two fits" | Which two fits? | Sec. II ¶3 names the fits by their data: the net-load fit (DSO data only), the SF fit (submetered TCL load, in practice a pilot) | S1, S2 | done |
| R18 | 3 | contribution 3, flexibility details | Too much here | flexibility derivation removed from contribution 3 | S1 | done |
| R19 | 3 | Sec. II privacy sentences | Why not in the introduction? | privacy and DER-register sentences moved from Sec. II to Sec. I ¶4 and deleted from Sec. II | S1 | done |
| R20 | 3 | "it" | What is it? | "From it follow…" paragraph deleted; opening reworded | S1b, S2 | done |
| R21 | 3 | "problem" | Wording | "The problem is to recover…" paragraph deleted; its content is in the new opening | S2 | done |
| R22 | 3 | Sec. II opening paragraph | Hard to follow; data needs; Fig. 1 | Sec. II opening reduced to the three quantities and the data each needs. The overview figure moved to the end of Sec. I (now Fig. 1), in words only, with each box naming its section | S1b, S2 | done |
| R23 | 3 | "treats R2 as out of scope" | Cooling analysis would be analogous | II-A: the method characterises the heating and cooling regimes alike and leaves the dead band out of scope; the evaluation covers the heating regime only, since the data allow no cooling-transfer test (cooling is future work, Sec. VII) | S3 | done |
| R24 | 4 | "the hat marks a fitted function" | Rephrase | "From (2), the temperature-driven component of the aggregated load of an aggregate i, with its own fitted parameters, is" (3); hat sentence deleted | S5 | done |
| R25 | 4 | "P_base … discarded" | Needed? | "P_base … discarded" sentence deleted | S5 | done |
| R26 | 4 | strike-out of ", i.e., a larger share of consumers with a TCL" (l.218) | (strike-out, no text) | ", i.e., a larger share of consumers with a TCL" deleted | L | done |
| R27 | 4 | "Table II spans this range…" | Introduce Table II | Alex removed the "Table II spans this range…" sentence; II-C still opens by introducing Table II | S2b | done |
| R28 | 4 | "SF(T)" | How does this match planning? | New II-B paragraph: design SF = b_h + m_h(T_h − T_d); design peak = installed capacity × design SF (back to Sec. I); daily-mean caveat with the IV-C ratio. T_d added to the Nomenclature | S5 | done |
| R29 | 4 | "In this work," (99.9th pct) | Why not max? Say values unavailable | "Nameplate ratings are not available for most households, so the installed capacity of each TCL is taken as the peak of its submetered 15-min draw." The 99.9th percentile is removed from the paper (Alex) | S2b | done |
| R30 | 4 | "isolated metering spikes" | Data cleaning; just say max | "isolated metering spikes" removed with the percentile | S2b | done |
| R31 | 4 | "which takes the peak interval" | What is the peak interval? | "the 15-min interval of highest aggregate demand"; "coincidence factor" → "the SF used in network planning" | S5 | done |
| R32 | 4 | Kloten 1.28× / 1.75× | Data not yet introduced | Kloten 1.28× / 1.75× moved verbatim to IV-C, after the 15-min peak SF; II-B points there | S5 | done |
| R33 | 4 | "Using the total TCL installed capacity … underestimation" | Too obvious | Sentence kept as in the original (removed in S5, restored in S5b) | S5b | declined (Alex disagrees with the comment) |
| R34 | 4 | eqs (5)–(7) | Heating only, cooling analogous | Eqs. (5)-(7) kept generic for heating and cooling | S3 | declined (Alex: generic everywhere except the results) |
| R35 | 4 | "(7)" | "which data do you need to do this fit? This is not so straightforward to do, no? Explain this a bit better." (one sentence may be too little; see S2) | New II-B sentences after eq. (7): the SF fit needs, for the same aggregate, its daily submetered TCL load, its installed TCL capacity per regime and the daily mean temperature, with the thresholds from its own net-load fit; in practice only a submetered pilot provides the first two (II-D) | L | done |
| R36 | 5 | "R1, R3, or" | What are these? | R1/R2/R3 replaced by heating regime / dead band / cooling regime throughout the text, captions, Table II footnote and figure labels | S4 | done |
| R37 | 5 | same | Refer to the figure | II-A and II-C point to the Austin net-load figure (now Fig. 2), which labels the regimes in words | S4 | done |
| R38 | 5 | "so the transfer of Section II-D" | Weird sentence | "so the SF sensitivity is expected to transfer only within a climate class and TCL technology (Section II-D)" | L | done |
| R39 | 5 | II-D first sentence, "submetered TCL data" (l.308) | "aha, why only here?" | Sec. I ¶11 introduces submetering and the pilot; II-D explains why the SF fit needs it | S1, S2 | done |
| R40 | 5 | II-D pilot/target definitions | Already for Table II? What is calibration? | II-D defines calibrate, pilot, target and split in plain words, and states that Table II involves no transfer | S2 | done |
| R41 | 5 | "Section IV-C tests this hypothesis…" | Paper builds on an untested hypothesis | II-D states the transfer as a tested hypothesis with pointers; Sec. IV now shows the capacity result first and IV-C is explicitly the within-population test | S2, II-D, S7 | done |
| R42 | 5 | "R²_h" | What is this? | R²_h and R²_c defined at first appearance (Fig. 2 caption) and in II-C | S4 | done |
| R43 | 6 | P_net(t) | "T?" | t defined as time after eq. (1); T defined as the daily mean temperature in the eq. (2) gloss; III-A no longer mixes P_net(t) with the fitted P_TCL(T) | S4 | done |
| R44 | 6 | "R2 bounds the estimate" | Use "dead band" | "The dead band bounds the estimate." | S4 | done |
| R45 | 6 | "The temperature cancels, so" | Write "Note that…" | "Note that the temperature cancels, so the estimate needs no choice of evaluation day." | L | done |
| R46 | 6 | "The two regimes are estimated separately." | Heating only | III-B equations kept for both regimes; the reversible-HP paragraph shortened to two sentences | S3, S3b | declined (Alex: generic everywhere except the results) |
| R47 | 6 | III-C cancellation passage | Unclear; how is Δt_Th set? | III-C opens with the use (congestion management, flexibility products); the window is an exogenous building-stock parameter; the cancellation is two plain sentences; E_flex is linear in the window, so results are per hour or ratios. Literature range for the window: D4, needs Alex; D4 placed in III-C as precedent for the window (Hon13) | S6, D4 | done |
| R48 | 6 | "Over a year, this paper counts…" | Rephrase or move; why useful? | Annual counting moved to the IV-F opening, with why the annual sum is useful; IV-F's repeated cancellation sentence dropped | S6 | done |
| R49 | 7 | IV-A split procedure | Why? What is fitted and estimated? | IV-A opens with a purpose paragraph: emulates a DSO with one submetered pilot and many un-submetered feeders; each aggregate has its own true capacity; the estimate is its s_h / pilot m_h | S7 | done |
| R50 | 7 | Fig. 5 number recital | Just the conclusion | IV-D recital (three paragraphs) cut to one: trend plus the two end cells (0.42/0.60 → 0.91/0.95) | S7 | done |
| R51 | 8 | "Installed Capacity Estimation" | Why not first? | Sec. IV reordered: capacity first (IV-B), then why it works (IV-C), fit quality (IV-D), energy, flexibility | S7 | done |
| R52 | 8 | "1260 aggregates at a WAPE of 19%" | Different capacity per aggregate? | Purpose paragraph: "Its net load is known, and so is its true installed capacity, the sum of the capacities of its own HPs … each has its own true capacity" | S7 | done |
| R53 | 9 | "Transferring the full SF curve…" | Not understood | Estimators (i)–(iv) listed before Table IV, rows labelled to match; "Transferring the full SF curve…" now reads "The full pilot curve (iii)…" | S7 | done |
| R54 | 9 | "About three points" | Three points? | "About three percentage points of this unused-capacity factor" | L | done |
| R55 | 11 | VI-D "…but not the net-load numerator." | What was done to counter limits? | VI-D rewritten: each paragraph opens with its safeguard (pilot kept apart from targets; full estimator tested out of sample, within 10%; non-TCL response measured by the zero-HP control; real aggregates bound tariff control). Cooling moved to future work in Sec. VII | S8 | done |
| R56 | 12 | "s" over "ted" of "This paper presented" (Conclusion, l.578) | "s" | "This paper presents" | S8 | done |
| R57 | 12 | strike-out of "Most of this error stems from the net-load slope, … rather than from the transfer of the SF slope." (l.578) | (strike-out, no text) | Struck sentence deleted | S8 | done |
| S2 | — | General comment: hard to read because of sentence complexity (no sentences marked, Alex 22 Oct) | — | Content-first restructuring (Phase 1, S1–S8) and a whole-paper clarity and terminology pass | 1124de3 | done |

## Decisions for Alex

Answered 16 Oct 2026: **D1 yes · D2 words · D5 capacity first · D7 as recommended · R03 and R56 as recommended.** D3, D4 and D6 are still open.

| ID | Question | Recommendation |
|---|---|---|
| D1 | Present the method heating-only, with cooling by symmetry? (Alex, 16 Oct: **no**. Generic in Sec. II–III; only the results, Sec. IV–V, are heating-only) | Yes. Every quantitative result is heating-only, and the cooling fits are descriptive (l.570). |
| D2 | Regime names: words or new symbols? (Alex, 16 Oct: **words**; applied in S4) | Words: heating regime, dead band, cooling regime. |
| D3 | Run the capacity-definition robustness check (max, HEAPO nameplate)? (Alex, 19 Oct: **run**; results below, needs Alex) | Run it. Numbers go in only after review. |
| D4 | Δt_Th literature range (verified source found: Hong et al. 2013, 1–2 h existing, up to 6 h improved; proposed sentence in S6 specs, placed in III-C 21 Oct) | Only with verified references; otherwise state it as an illustrative parameter. |
| D5 | Sec. IV with capacity first? (Alex: **yes**; applied in S7) | Yes. |
| D6 | Non-TCL correction implemented or kept as future work? (Alex: **future work**; kept in Sec. VII) | Future work. |
| D7 (new) | "feeder" vs "aggregate": the evaluated aggregates are summed household meters, not feeder-head measurements (l.529). | Use "feeder" for the DSO use case in Sec. I. Use "aggregate" (defined in Sec. I ¶11) for every result claim. Abstract: "aggregates of measured households". |

## Content specs

### Core message (Phase 1)
- A DSO can estimate the installed HP capacity behind a feeder from its net load and outdoor temperature, plus one number calibrated once on a small pilot with submetered heating.
- The number is how fast the share of installed capacity in use grows as the temperature falls. The net-load temperature slope divided by it gives the capacity.
- Accuracy: WAPE 19% on 1260 semi-synthetic Swiss aggregates; within 10% on three real aggregates outside the pilot, all at 100% HP penetration. The calibration transfers when the pilot matches the target in climate zone, HP technology and housing stock.
- Secondary: energy with no pilot (WAPE 9%); flexibility potential (WAPE 10%).

### Abstract (proposed; every number kept verbatim)
1. **Driver.** The electrification of heating and cooling connects more TCLs, such as HPs, to LV networks.
2. **Need and gap.** DSOs need the installed TCL capacity behind each feeder to plan for cold-weather peaks, but they rarely know it.
3. **Setup (new, R10).** The DSO holds each feeder's net load and the outdoor temperature. This paper estimates the capacity from these two series. A small pilot of households whose heating is submetered is calibrated once.
4. **Idea, in words.** The pilot gives one number: how fast the share of installed capacity in use grows as the temperature falls. The feeder's own net-load temperature slope divided by this number gives its capacity. Only this number transfers; each feeder keeps its own heating threshold temperature. *(Replaces A4–A5; no "SF slope", no symbols.)*
5. **Accuracy, semi-synthetic.** 1260 semi-synthetic aggregates of Swiss households: WAPE 19%, error growing as the share of households with an HP falls.
6. **Accuracy, real.** Three real Swiss and German aggregates outside the pilot, every household with an HP: within 10%, against up to 26% when the pilot's whole curve is transferred.
7. **Secondary outputs.** Temperature-driven HP energy: no pilot, WAPE 9%. Flexibility potential from both fits: WAPE 10% against its submetered reference. *(Fix the missing verb.)*
8. **When the transfer holds.** Five countries: within 12% inside one climate zone; 13–14% between HP technologies; up to 1.7-fold between climate zones and between social and private housing.

### Sec. I (proposed; Alex edits)

| ¶ | Point | Content |
|---|---|---|
| 1 | Heating electrification is growing fast. | Electrifying heating and cooling is a decarbonisation lever; TCLs = HPs, resistive heaters, air conditioners; HPs lead (`Iea22`). European scale: EHPA 2026 market report (29.3 M HPs in 21 countries; 2.88 M sold in 2025, +13%), **checked (S1):** the EHPA market-data page (https://ehpa.org/market-data/, 16 Oct 2026) gives 2.9 M sold in 2025, +13%, 21 countries, stock 29.3 M. The brief's "2.88 M" could not be confirmed at the primary source, so the text says "about 2.9 million". `Tre26` 200 German feeders: at most one clause (R01, R02). |
| 2 | This load stresses LV networks in cold weather. | TCL load follows the outdoor temperature. In cold spells many devices run together, which raises coincident feeder and transformer peaks (`Vel11, Akm14, Som21, Bec24, Lia26`). These peaks add to EV peaks. Rooftop solar: drop it, or say it causes reverse-flow peaks at a different time (R04). R03 wording per Alex. |
| 3 | The DSO needs the installed capacity. | (a) Planning scenarios, because capacity scales with adoption. (b) Worst case when devices synchronise, after a blocking period or a flexibility activation. (c) Design peak = capacity × SF at the design temperature, with SF defined in words as "the share of installed capacity drawn at once" (`Lov17, Che21b, Rou23, Few24`). Flexibility is bounded by unused capacity (`Mul19, Zir19, Dhu15`). Absorbs the current I-4 and the first half of I-8 (R05, R12). *Reference numbers checked against the reviewed PDF: [28] Lov17, [29] Che21b, [41] Rou23, [55] Few24; [32] Mul19, [33] Dhu15, [42] Zir19; [2] Tre26, [8] Gou26.* |
| 4 | The DSO does not know it. | Privacy and data-exchange limits restrict access to household data; DER registers lag what is connected (moved from Sec. II l.111, R19; **the current sentence has no citation**, so add `Gou26` or leave it uncited). The DSO holds: net load at the substation or feeder head, plus smart meters where rolled out, often with restricted access (R06); outdoor temperature; consumer count per feeder (`Gou26, Tre26`). It lacks appliance registers and nameplate ratings. Subject "the DSO" named in every sentence (R07, R08). |
| 5 | Prior work 1: detection and disaggregation | NILM and HP detection on customer meters (`Fei13, Wei20b, Ray19`; `Bru23, Gis26`); substation extensions (`Wan20, Oma24`). Limitation: need labelled or submetered training data, stop short of capacity, and "have been validated mostly on synthetic substation aggregates rather than on measured substation data" (R09). |
| 6 | Prior work 2: temperature-response models | Change-point and degree-day models (`Fel08, Ruc92, Kis04`, review `Faz16`; `Ali11, Per17b, Mac19`). Recover sensitivities and threshold without labels. Limitation: stop at the coincident response. |
| 7 | Prior work 3: TCL aggregate models for control | `Cal09, Hao15, Mat13, Led18`. Limitation: assume known device models or learn them from device-level data; control time scales. |
| 8 | Prior work 4: PV and transformer capacity | `Was21, Liu22, Gou25, gouveia2026pvcapacity`; distribution-transformer rating `Azz24` (R11). Irradiance plays the role temperature could play for TCLs; the TCL counterpart is missing (`Gou26`). |
| 9 | Prior work 5: HP demand and coincidence | Forward models from a known HP count to demand (`And20`); simultaneity measured on submetered populations of known size (`Lov17, Che21b, Rou23`). Limitation: they do not recover capacity from an un-submetered feeder. |
| 10 | The gap | No method estimates installed TCL capacity from feeder net load without submetering households on the target feeder (R13). Change-point models see the signal but stop at the coincident response. Simultaneity studies make the step to capacity, but only on submetered populations. Control models assume the population is known. This paper joins the first two. |
| 11 | The idea in plain words (new, R10) | The DSO measures the feeder's net load and temperature. Once, it submeters the heating of a small pilot and learns one number: how fast the share of installed capacity in use grows as the temperature falls. The feeder's net-load slope divided by that number gives its capacity. The feeder's households are never submetered. Define "pilot", "target", "submetered" (R39, R40) and "aggregate" (D7). |
| 12 | Contributions: three items, 1–2 sentences each, no results, no symbols (R14–R18) | (1) A method to estimate installed TCL capacity behind a feeder from its net load and temperature, calibrated once on a small submetered pilot. (2) An evaluation of when that calibration transfers: across HP penetration, aggregate size and resolution within one population; on real aggregates outside the pilot; across populations of five countries. (3) Estimates of the temperature-driven energy, with no pilot needed, and of the flexibility potential, from the net-load fit and the SF fit (named here, R17). |
| 13 | Roadmap | Final section order after D5. |

Changes from the brief's default spec: prior work becomes five paragraphs (¶5–9) in **Table I's category order**, because Table I has five categories and the current prose already has five lines. The idea paragraph also defines "aggregate" (D7). Contribution (2) says "real aggregates", not "real feeders".

### S1 notes (as written)
- Abstract: 248 words (IEEE limit 250). Every number of the old abstract is kept verbatim. Spec item 4's clause "each feeder keeps its own heating threshold temperature" is dropped for length, because the threshold is not yet a defined idea for the reader. Its content survives in "against up to 26% when the pilot's whole curve is transferred".
- Sec. I: 13 paragraphs, as in the spec. Prior work follows Table I's five categories, in prose order NILM → change-point → control → PV → HP coincidence.
- Sec. I sentence statistics: max 31 words, median 18. The median is below the voice skill's 22 because of Supervisor 2's one-idea-per-sentence rule; the supervisor wins (rule 4).
- The privacy sentence in ¶4 has no citation, as before. `Gou26, Tre26` stay on the sentence they supported before (consumer count, registers, ratings).
- EV is defined in ¶2 and added to the Nomenclature.
- Reviewer-2 recheck pending: the S2-xx marks have not arrived.

### S1b — Alex's edits and follow-up (16 Oct)
- Alex's edits, kept as made: dropped the 26% clause from the abstract, the synchronisation sentence (¶3), the Azz24 clause (¶8) with its Table I row and group name, and the "aggregate" definition (¶11); "per cent" → "percent".
- Alex: "one number" is too vague. The abstract and ¶11 now define the SF (share of installed capacity in use) and its sensitivity (how fast that share grows as the temperature falls), then call it the **SF sensitivity**. For symmetry, the feeder's rate is named the **net-load sensitivity**. Both are the body's existing terms. Contributions 2 and 3 use the names.
- Alex: the Sec. II opening sentence "DERs that consume or generate with a high simultaneity factor…" did not connect to what followed. It is deleted, its point (high-simultaneity loads drive peaks) is already in Sec. I ¶2–3, and the dangling "therefore" went with it.
- Abstract: 250 words. "against its submetered reference" and "measured" were dropped for length; no number changed.
- **Open for Alex:** (a) `scripts/gen_litreview.py` still emits the Azz24 row and the "PV and transformer capacity" group, so regenerating Table I would undo the edit. (b) With the "aggregate" definition gone, contribution 2 uses "aggregate size" and "real aggregates" before Sec. II defines the term. (c) "percent" is US spelling; the voice skill uses British "per cent".

### S2 content specs (Sec. II opening, fit naming, II-D)
**II ¶1 — point: three quantities, and the data each needs (R22, R21).**
- Quantities for the TCLs of an aggregate: installed capacity, temperature-driven energy, flexibility potential.
- Definition: aggregate = a metered point (substation or feeder) plus the consumers behind it.
- Data: energy needs only net load + outdoor temperature (held by the DSO). Capacity and flexibility also need the SF sensitivity, calibrated once on a submetered pilot (→ II-D).
- Removed: "This work uses the load profiles…" (repeats Sec. I ¶4); "The problem is to recover P_TCL…" (R21); Fig. 1 reference (R22).

**II ¶3 — point: two fits, named by the data they need (R17, R20).**
- The net-load fit uses only DSO data (→ II-A). The SF fit needs submetered TCL load and capacity, which in practice only a pilot gives (→ II-B).
- Same piecewise-linear form; daily means reduce thermal inertia (`Per17b`).

**Fig. 1 (R22).** Moved to the end of Sec. III, after every block it shows is defined, and introduced by one sentence. Caption unchanged.

**II-D ¶1 — point: the method rests on a single assumption (R41).**
- Assumption: within a population, the SF sensitivity does not depend on the installed capacity or TCL penetration of an aggregate.
- Population = the households of one dataset or study.
- Early evidence, pointing back and forward: Table II, where the SF sensitivities remove the size dependence of the net-load sensitivities (II-C); and within Kloten, m_h varies little with the number of HPs (Table III, IV-C).

**II-D ¶2 — point: what calibration means (R39, R40).**
- The SF fit needs submetered TCL data, which the DSO rarely holds for the aggregate under study.
- Calibrate = measure once on a pilot. Pilot = small set of households of the population with submetered TCL load, hence known capacity.
- Target = an aggregate of the same population whose capacity is estimated, with no household submetered. Split = one random partition of a population into a pilot and targets.
- Table II involves no transfer: both fits are made on each dataset's own data (R40).

**II-D ¶3 — point: only the SF sensitivity transfers (kept content).**
- The thresholds come from the target's own net-load fit; the intercepts sit in P_base. Ratio (10) gives capacity if the assumption holds.
- Tested within Kloten (IV-C) and across populations (V). The sentence "This is the mechanism the rest of the paper builds on" is dropped (R41).

### S2 notes (as written)
- The rewritten passages (Sec. II opening, II-D) have no sentence over 32 words; median 17–19.
- Still over 40 words elsewhere in Sec. II, left for the step that rewrites them: the eq. (2) "where" gloss (55 words, S3), the eq. (4) definition (51, S5) and the eq. (5) definition (40, S3).
- II-A2 still opens "Note that (2) needs only the net load and ambient temperature…", which now repeats Sec. II ¶3. A candidate for batch L.

### S2b — Alex's edits and the percentile (16 Oct)
- Alex's edits, kept as made: wording in II-A ("chosen as", "all else being equal", "rather than being a property of any building or device"); the repeated dead-band sentence deleted; the P_base paragraph commented out; the "Table II spans this range…" sentence deleted; "also called the coincidence factor" deleted from II-B.
- Alex: drop the 99.9th percentile, which is an implementation detail. The only mention (II-B, after eq. (4)) now reads "taken as the peak of its submetered 15-min draw". The code still uses the 99.9th percentile; no number changes.
- **For Alex:** (a) "peak" is a slight simplification of the 99.9th percentile, and running D3 (capacity WAPE with the plain max) would show the difference is immaterial. D3 is still open. (b) With "also called the coincidence factor" gone, the next paragraph's "lower than the coincidence factor used in network planning" uses an undefined term. S5 rewrites that paragraph (R31) and will say "the planning SF".

### S3 content specs (revised by Alex, 16 Oct: keep the problem and fits generic)
**Scope change.** Alex disagrees with heating-only for the problem definition and the fits. Eqs. (1)–(7) and II-A/II-B stay generic, so R34 is declined. Heating-only is applied only to the Sec. III-B capacity derivation (R46).

**II-A, regimes sentence (R23).** Point: the method treats both regimes alike; only the evaluation is heating-only.
- The paper characterises the heating and cooling regimes and leaves the dead band out of scope.
- The same analysis applies to cooling. The evaluation of Sec. IV–V is heating-only because the available data allow no test of the cooling transfer (Sec. VI-D: the NEEA Washington pilot has no day above its cooling threshold in 2023).

**III-B, capacity (R46).** Point: the ratio of the two sensitivities gives the capacity, shown for heating.
- The matching SF of the target in the heating regime is m_h (T_h^i − T), starting at zero at the target's own threshold.
- Dividing the heating arm by it gives P_h^max,i = s_h^i / m_h; the temperature cancels.
- Cooling follows by symmetry, with (T − T_c^i) in place of (T_h^i − T), giving P_c^max,i = s_c^i / m_c.
- Reversible HPs, in one sentence: they count in both regimes, so the total lies between the larger of the two and their sum.

### S3b — generic everywhere (Alex, 16 Oct)
- Alex: keep the method generic everywhere except the results, which look only at heating. III-B is restored to the two-regime eqs. (9)–(10) and $m_k$.
- Net effect of S3 + S3b on the text: the R23 sentence in II-A (the evaluation covers R1 only, because the data allow no R3 transfer test), and the reversible-HP paragraph cut from four sentences to two.

### S4 content specs (notation and terms)
**Regime names (D2: words; R36, R37, R44).**
- R1/R2/R3 → "heating regime", "dead band", "cooling regime" in all text, captions, the Table II footnote and the two figures that print them (Austin net-load fit; x-label of the flexibility-ratio histogram). The figures are regenerated with word labels only; no plotted value changes.
- II-C points back to Fig. 1 (Austin) at the first use of the regimes (R37).

**R²_h at first use (R42).** II-C: each fit is scored by its coefficient of determination on the days of its own regime, R²_h for heating and R²_c for cooling. The Austin caption says the same.

**Time vs temperature (R43).**
- After eq. (1): t is time. The fits use daily means and are written against the daily mean temperature T.
- III-A: the fitted TCL load P̂_TCL(T) separates the daily TCL load from the daily net load; no P_net(t) there.

### S4 notes (as written)
- Figures regenerated with word labels only: `fig_bathtub_example` (the script prints R²_h 0.679, R²_c 0.915, as published) and `fig_flex_ratio` (x-label; histogram and median 1.04 identical). `fig_flex_season` is not regenerated; its legend was already in words.
- `scripts/outputs.py` updated to match: the figure labels and the Table II footnote string, so regenerating does not undo S4.
- The 55-word eq. (2) gloss is split in two (35 words with the equation, then 23).

### S5 content specs (capacity definition and SF for planning; D3 = run)
- **R24, R25 (eq. 3):** introduce it as "From (2), the temperature-driven component of the aggregated load of an aggregate i … is". Delete the hat sentence and the "P_base … discarded" sentence.
- **R31, R32 (II-B, daily-mean SF):** keep the point that this paper's SF is a daily mean, lower than the planning SF, which takes the 15-min interval of highest aggregate demand. Keep why the daily mean suits the paper (capacity from the slope; inertia, `Per17b`). Move the Kloten ratios (1.28× coldest day, 1.75× median heating day), verbatim, to IV-C next to the 15-min peak SF (0.56 / 0.59), and point to them from II-B. "Coincidence factor" becomes "the SF used in network planning".
- **R28 (planning link):** the SF fit gives the SF at any temperature of its regime. Design SF = b_h + m_h (T_h − T_d) at a design temperature T_d < T_h, and design peak = installed capacity × design SF (back to Sec. I ¶3). With the daily-mean SF this is a daily-mean design load; the 15-min peak lies above it by the IV-C ratio. New symbol T_d goes in the Nomenclature.
- **R33:** delete "Using the total TCL installed capacity in (4) would lead to an underestimation…"; then "Each regime therefore has its own capacity".
- **D3:** `scripts/d3_capacity_definition.py` rebuilds the 1260 Kloten aggregates (same seed, splits and draws) with the capacity defined as (a) the paper's robust peak, (b) the plain 15-min max, and (c) the HEAPO certificate electric power at the norm point, on the subset that has it. The definition changes on both the pilot and the target side. The numbers go to the log only, as needs Alex.

### S5 notes and D3 results (needs Alex — not in the paper)
- Script: `scripts/d3_capacity_definition.py` (output `results/d3_capacity_definition.csv`, gitignored). It rebuilds the 1260 Kloten aggregates with the same seed, splits and draws, and changes the capacity definition on both the pilot (its m_h) and the target (its ground truth).
- **Sanity check:** the paper definition reproduces the published numbers exactly, WAPE 19.3% and 14.5% with the target's own m_h.

| Capacity definition | Aggregates | WAPE | ≤15% HP | 15–35% | 35–65% | >65% | Median ratio | WAPE, own m_h | Pilot m_h (median) |
|---|---|---|---|---|---|---|---|---|---|
| robust peak (paper) | 1260 | 19.3 | 57.5 | 26.3 | 17.0 | 14.2 | 1.159 | 14.5 | 0.0178 |
| plain 15-min max | 1260 | 19.5 | 56.9 | 26.1 | 17.2 | 14.8 | 1.155 | 14.5 | 0.0160 |

- Per HP, max / robust peak: median 1.041, IQR [1.019, 1.128], range [1.006, 1.568] (50 Kloten HPs).
- **The capacity error barely moves (+0.2 points)**, because the definition enters both the pilot's m_h and the target's truth and largely cancels. The pilot m_h itself drops by about 10% (0.0178 → 0.0160), because each SF is normalised by a larger capacity. So the published m_h values are tied to the robust-peak definition, which matters if anyone compares them with a nameplate-based SF.
- **Nameplate check: not feasible.** HEAPO protocols (`HeatPump_Installation_Normpoint_ElectricPower`, kW at the certified operating point) cover 214 households, 67 of them with that power. None of the 50 Kloten HPs has a protocol, and only 2 of the 81 submetered HPs in the pool do (one at Hg, one at HbsbG). For those two, certificate power / robust peak = 0.74 and 0.87, which shows the rating point sits below the measured peak but is too few to test anything.
- Suggested wording if Alex wants it in the paper (not inserted): "Taking the plain 15-min maximum instead changes the capacity WAPE on the Kloten aggregates from 19.3% to 19.5%, since the definition enters both the pilot's sensitivity and the ground truth."
- Text: equation glosses for (4) and (5) still read long because each sentence includes the display equation; the prose parts are under 40 words.

### S5b — R33 restored; change-tracked PDF (19 Oct)
- Alex disagrees with R33: the "Using the total TCL installed capacity … underestimation" sentence and "Therefore, each regime will have its own capacity, which is defined as" are restored verbatim.
- `review/hp_sensitivity_diff_vs_reviewed.pdf`: latexdiff of the reviewed version (commit 5672089, same text as `main`) against the current text. Blue wavy underline = added, red strike-through = deleted. Built with Strawberry Perl (the MiKTeX latexdiff lacks Algorithm::Diff). `\chg{}` wrappers were stripped in the scratch copies only, since latexdiff cannot split them.
- **Not marked in that PDF:** changes inside tables (Table I Azz24 row and group name; Table II footnote) and inside figures (Austin and flex-ratio labels). Moved text (Fig. 1, the privacy sentences, the Kloten ratios) shows as a deletion plus an insertion.
- The reviewed PDF's Table I was an older variant than `main` (see Phase 1 notes), so the diff baseline is `main`, not that PDF.

### II-D rework (Alex, 19 Oct: repetition, unclear message, results front-loaded; frame it as a tested hypothesis)
**¶1, point: why a transfer is needed and what calibration means.**
- The SF fit needs submetered TCL data, which the DSO rarely holds for the aggregate under study.
- The method calibrates the SF sensitivity once on a pilot and reuses it on targets. Pilot = small submetered set, so its capacity is known. Target = un-submetered aggregate whose capacity is sought. Both belong to one population (the households of one dataset or study). Split = one random pilot/target partition.
- Table II involves no transfer (R40, kept).

**¶2, point: only the SF sensitivity transfers.** Thresholds come from the target's own net-load fit; intercepts sit in P_base. Kept, slightly shortened.

**¶3, point: the transfer is a hypothesis, tested in three steps.**
- Hypothesis: within a population, the SF sensitivity does not depend on the installed capacity or the TCL penetration of an aggregate. The paper tests it rather than assuming it.
- Why it matters: the capacity estimate divides by the transferred sensitivity (III-B), so a mismatch passes directly into the capacity.
- Tests: within one population (IV-C), on real aggregates outside the pilot (V-A), across populations of five countries (V-B).

**Removed:** the Table II "first support" sentence and the Kloten m_h evidence (results, front-loaded in S2); "Under this assumption … also holds for the other aggregates" (repeats ¶1); "If the assumption holds, the net-load sensitivity … gives the installed capacity" (repeats Sec. I ¶11 and III-B).
- Alex's edits in this round, kept: the Köppen–Geiger citation added in II-C ¶3; "has no cooling whatsoever" (Hamelin); Table I footnote trimmed to the abbreviation list (the explanatory part commented out).
- The refreshed change-tracked PDF is `review/hp_sensitivity_diff_vs_reviewed_new.pdf`, because the old file was locked by a viewer. Close the viewer and it will replace the old one at the next refresh.

### S6 content specs (III-C flexibility; R47, R48; D4)
**III-C ¶1, point: why the flexibility matters, and what the window is.**
- Use: a DSO or aggregator needs to know how much heating energy the TCLs behind a feeder could shift, for congestion management or a flexibility product.
- Definition: the energy shifted from the baseline without breaching comfort (`Zir19`).
- Δt_Th is exogenous, a property of the building stock rather than an output of the fits. A larger window means better insulation or wider comfort bands (`Cha16`). Insulation and comfort data are lacking.

**III-C ¶2 (eqs. 12–14):** unchanged.

**III-C ¶3, point: the capacity estimate drops out (R47).** Two plain sentences. The shiftable load comes from the net-load fit. The transferred SF only sets the headroom above it, so the capacity estimate drops out. E_flex is linear in Δt_Th, so the results are given per hour of window or as ratios.

**R48:** "Over a year, this paper counts…" moves to IV-F, which opens with it. It adds why the annual sum is useful (the yearly shiftable heating volume, which is what a flexibility product is valued on). IV-F's opening restatement of the cancellation is dropped, since it now lives in III-C.

**D4 (needs Alex):** verified source, Hong, Kelly, Thomson & Richardson, "Assessing heat pumps as flexible load", *Proc. IMechE Part A: J. Power and Energy* 227(1):30–42, 2013, doi:10.1177/0957650912454830 (abstract checked on Strathprints, 20 Oct 2026). Existing dwellings shift HP operation by only 1–2 h before comfort suffers; up to 6 h with much better insulation and thermal buffering. Proposed sentence, **not inserted**: "A study of UK dwellings places this window at 1–2 h for the existing stock and up to 6 h with improved insulation and thermal buffering \cite{Hon13}, which brackets the 4 h used for illustration in Section IV-F."

### S6 notes (as written)
- The manuscript PDF in `paper/` was locked by a viewer, so the build was verified from a scratch copy: 13 pages, 0 undefined references.
- `review/hp_sensitivity_diff_vs_reviewed.pdf` is refreshed (15 pages).

### S6b — D4 saved; overview figure moved up (Alex, 20 Oct)
- **D4: saved, not inserted.** Alex: it may fit better in the numerical results. Candidate place: IV-F, next to the illustrative 4 h window of the flex-season figure. Sentence to adapt there, with `Hon13` (Hong, Kelly, Richardson & Thomson 2013, *Proc. IMechE Part A* 227(1):30–42, doi:10.1177/0957650912454830, verified; author order corrected from Crossref 21 Oct): "A study of UK dwellings places this window at 1–2 h for the existing stock and up to 6 h with improved insulation and thermal buffering \cite{Hon13}, which brackets the 4 h used here." The bib entry is to be added when it goes in.
- **Overview figure (former Fig. 4, method pipeline):** Alex sees it as a summary of the whole paper, so it moves to the end of Sec. I, after the roadmap. Each box names the section that defines it. Symbols and equation numbers are dropped from the boxes, since they are not defined yet in Sec. I. The caption is shortened. The back-reference sentence at the end of Sec. III is removed.
- Done: the overview figure is now Fig. 1, at the end of Sec. I after the roadmap ("Fig. 1 maps each step of the method to the section that defines it"). The boxes carry unlinked section labels in grey (II-A, II-B, II-D, III-A, III-B, III-C), the arrow label "only m" becomes "SF sensitivity", and the box symbols and equation numbers are gone. Caption: "Overview of the method, with the section that defines each step. Sections IV and V evaluate the three outputs." All other figures renumber by one.
- R22 (Fig. 1 unclear at the start of Sec. II) stays closed: the figure now uses words only and sits before Sec. II, with every box pointing to where it is defined.
- Fig. 1, second pass (Alex, 20 Oct): boxes enlarged (19 × 10 mm, up from 15 × 7), gaps tightened, the pilot box no longer carries a section label, and the arrow label is on two lines ("SF / sensitivity"). Summary table for the end of Sec. III proposed to Alex, not yet added.
- Option A added (Alex, 20 Oct) as Table III at the end of Sec. III, with the lead-in "Table III summarises which fitted parameters each estimate uses, and which data they come from." The later tables renumber by one.

### S7 content specs (Sec. IV order and purpose; D5 = capacity first; R49–R53)
**Order:** IV-A data and design → IV-B installed capacity (old IV-E + baselines) → IV-C why the estimate works (old IV-C + the s_h-vs-capacity paragraph and figure from old IV-B) → IV-D fit quality vs aggregation (old IV-B, shortened) → IV-E energy → IV-F flexibility.

**IV-A, new opening ¶, point: what the experiment emulates (R49, R52).**
- It emulates a DSO that submeters one pilot and estimates the installed capacity of many feeders without submetering them.
- Each semi-synthetic aggregate plays one such feeder: its net load is known, and so is its true capacity, the sum of the capacities of its own HPs. The aggregates differ in size and HP penetration, so each has its own true capacity.
- Per aggregate: estimate = its own net-load sensitivity / the pilot's SF sensitivity (10), scored against its true capacity.
- Then the existing data, split and metric paragraphs.

**IV-B (capacity):** the opening points to IV-C for the pilot sensitivity's stability. The heatmap paragraph no longer leans on IV-D ("the same grid on which Section IV-D scores the fit quality"). **Before Table V, a list of the estimators (R53):** (i) proposed, s_h / pilot m_h; (ii) own sensitivity, s_h / own m_h, removing the transfer to isolate the numerator error; (iii) full pilot curve, intercept and threshold included, evaluated on the coldest day; (iv) planning SF, coldest-day TCL load / 0.425 (`Few24`). The two discussion paragraphs refer to (i)–(iv), and the table rows carry the same labels (`tab_baselines.tex` and `outputs.py`).

**IV-C, new opening, point:** the estimate divides a sensitivity that grows with installed capacity by one that does not; this is the within-population test of the II-D hypothesis. Then the SF invariance (Table IV, pilot figure, direct test), then the s_h-vs-capacity paragraph and figure moved from old IV-B. "Beyond fitting well" and the forward pointer to the capacity section are dropped.

**IV-D (R50):** the three recital paragraphs become one. More consumers and longer windows both raise the median R²_h, and the effects compound from 0.42 / 0.60 (10 consumers, hourly) to 0.91 / 0.95 (50 consumers, daily). The two aggregations partly substitute for each other, and the daily mean sits at the right edge with 16 h close behind. The intermediate values remain in the figure.

**Not done (option for Alex):** a small schematic of one split (pilot half → m_h; target half → aggregates).

### S7 notes (as written)
- Number check: the only numbers removed from Sec. IV are the intermediate R² values of the old fit-quality recital (0.64, 0.78, 0.83, 0.58, 0.66, 0.76, 0.86, 0.87, 0.94 and repeats); they remain in the figure. No number was added or changed.
- Floats renumber: Table IV = baselines, Table V = SF invariance, Fig. 5 = capacity heatmap, Fig. 8 = fit-quality heatmap.
- The pre-existing 44-word sentence in IV-C on the 15-min peak SF is split in two.
- `scripts/outputs.py` updated so that regenerating Table IV keeps the (i)–(iv) row labels.

### Output order: capacity → energy → flexibility everywhere (Alex, 20 Oct)
- Sec. III: subsections swapped, so III-A is now installed capacity and III-B is energy (III-C flexibility unchanged). Equations renumber: capacity (9), energy (10).
- Sec. III intro: "their installed capacity, energy consumption and flexibility potential". Capacity needs the transferred SF sensitivity; energy follows from the net-load fit alone; "Flexibility needs both."
- Roadmap: "derives the installed capacity, energy and flexibility".
- Table III rows: capacity, energy, flexibility.
- Already in this order: the abstract, Sec. I ¶11 and contributions, the Sec. II opening, Fig. 1 (capacity box above energy) and Sec. IV (IV-B capacity, IV-E energy, IV-F flexibility). Sec. V reports capacity, then the flexibility ratio.
- Alex's edit kept: the Table III footnote ("Not used by any estimate…") commented out.

### Split schematic (R49 option) — draft only, not in the manuscript (20 Oct)
- `review/drafts/split_schematic.tex` (standalone TikZ, same box style as Fig. 1) and `.png` (rendered at IEEE column width).
- Content, all from IV-A: 50 submetered Kloten HPs, split at random 20 times → a 25-HP pilot → SF fit → m_h; the 25-HP target half plus the 1307 households without an HP → aggregates (N = 10–50, N_hp = 5–25) → net-load fit → s_h, and their true capacity (the sum over their HPs) → estimate s_h / m_h → WAPE over all 20 splits (1260).
- If adopted: it goes in IV-A after the purpose paragraph, and the caption drops the "Fig. X." prefix.
- Added (Alex, 20 Oct): the split schematic is Fig. 5 in IV-A, after the purpose paragraph, which now ends "Fig. 5 sketches one split." The caption is the draft's, without the "Fig. X" prefix. The paper is now 14 pages (was 13).
- Alex's edit kept: the Table I footnote wrapped in `flushleft`.

### S8 content specs (VI-D limitations, R55; conclusion, R56, R57; D6 = future work)
**VI-D, point: each limitation, then what bounds it (facts from the paper only).**
1. Overlapping aggregates within a split (same 25 HPs) → 20 random splits, draws without replacement, pilot disjoint from every target, no household repeated within an aggregate.
2. Few real aggregates (three, one with six HPs, all at 100% HP penetration) → fully out of sample (no pilot HP among them). Table VII widens the SF-transfer test to five populations, but cannot test the net-load numerator, because none of those datasets yields a faithful net load.
3. Non-TCL temperature response neglected → quantified by the zero-HP control (VI-A: median 0.28 kW of spurious capacity per household), so the bias is predictable from the consumer count the DSO holds. The correction stays future work (D6, Sec. VII).
4. Cooling untested → no mitigation available: NEEA allows no cooling transfer, Oregon shows the numerator failing (+45% heating, +72% cooling), and the cooling fits are descriptive only. Needs a fully submetered cooling population (Sec. VII).
5. Tariff control and §14a throttling → may bias the numerator downwards, but the real aggregates stay within 10%.
6. Scarce submetered data → a wider pilot would relieve it.

**Conclusion.**
- R56: "This paper presents". R57: "Most of this error stems from the net-load slope…" deleted.
- Terms aligned with Sec. I: "two slopes" → "two sensitivities", "SF slope" → "SF sensitivity", "calibration households" → "pilot".
- Flexibility added after energy (abstract number, WAPE 10%), to keep the order capacity → energy → flexibility.
- Future-work paragraph unchanged; the non-TCL correction stays there (D6).

### S8 notes (as written)
- New label `sec:accuracy` on VI-A, so the limitations can point to the zero-HP control.
- Numbers added: 0.28 kW (verbatim from VI-A) in VI-D, and the flexibility WAPE of 10% in the conclusion (as in the abstract and IV-F). None removed.
- The conclusion now reports capacity, energy and flexibility, in that order.
- Fig. 5 redrawn for legibility (Alex, 20 Oct): the five-column layout was shrunk to about half size to fit the column. The new three-column, top-to-bottom layout (`review/drafts/split_schematic_v2.tex`) fits the column at near full size, and its font is \footnotesize instead of \scriptsize. Same boxes, arrows and content; caption unchanged; still 14 pages. `calc` added to the TikZ libraries.

### VI-D reframed (Alex, 20 Oct: the limitations undercut the work)
- VI-D opens "The evaluation keeps every test out of sample, and three limits remain." Then: (1) overlapping aggregates within a split, (2) three real aggregates plus the five-population transfer test, (3) the non-TCL response, sized by the zero-HP control and predictable from the consumer count. The tariff paragraph opens "Deliberate control of the HPs could add a fourth source of error." Its closing data-shortage sentence is dropped (already in future work).
- Cooling moved from VI-D into the first future-work direction of Sec. VII, with the NEEA/Washington reason for why no cooling transfer was possible.
- **Removed by Alex's decision:** the Oregon numerator result (capacity overestimated by 45% in heating and 72% in cooling, about a third of the heating sensitivity unmetered) and "The cooling fits of Table II are therefore descriptive only". The II-A sentence still says the evaluation covers the heating regime only.
- VI-D rewritten again (Alex: the previous version still led and ended each paragraph on the weakness). Each paragraph now opens with the safeguard: pilot kept apart from its targets; the full estimator tested fully out of sample and within 10% on the real aggregates; the non-TCL response measured rather than assumed away; the real aggregates bounding the effect of deliberate HP control. The residual limit follows, and each paragraph ends on coverage or a bound. The span of HP penetration in the Kloten design (10%–100%, from N_hp = 5–25, N = 10–50, N_hp ≤ N) is stated. The "regime-specific structure" clause is dropped (Alex). No result changed.

### Batch L (21 Oct)
- R26, R35, R38, R45, R54 applied as above.
- Also fixed: II-A "Section IV-D confirms this, with s_h tracking installed capacity" now points to IV-C, where that evidence moved in S7. Every other cross-reference into Sec. IV was checked and still points to the right subsection.
- D4 draft (21 Oct), not placed: `review/drafts/d4_window_range.md` has the IV-F insertion (two versions), the `Hon13` bib entry with metadata checked at Crossref, and the placement. Crossref author order: Hong, Kelly, Richardson, Thomson.

### D4 placed in III-C (Alex, 21 Oct) — closes R47
- After "…or wider comfort bands [Cha16]": "Load-shifting studies of HPs treat this window the same way, as a property of the building [Hon13]. In simulations of UK residential buildings, HP operation could be shifted by 1–2 h in the baseline case and by up to 6 h with much improved insulation and thermal buffering." The source is used as precedent for the variable, not as justification for the illustrative 4 h, and IV-F is unchanged. `Hon13` added to `references.bib` (Crossref metadata).
- **Terminology check (Alex):** the paper uses "household" (57×) for the metered unit and "building" (15×) for the physical structure and its thermal properties; "dwelling" never appears. The new sentences therefore say "building" and "UK residential buildings", not "dwelling". Fixed mixes: "homes" → "households" in Table VII (caption and column header) and in the Table II footnote, and in their generator in `scripts/outputs.py`. Kept as specific terms: "whole-home energy signature" (the term of `Wes20`), "single-family houses" (WPuQ) and "Oslo apartments" (COFACTOR), which describe a dataset's building type.

## Phase 4 — final checks (21 Oct)
- **Numbers.** Every number in the abstract and conclusion appears identically in the body or its tables. Sec. I's only body-less numbers are cited market background (EHPA 2.9 M / 29.3 M, 2025; Tre26 200 feeders), which belong to the sources, not to the results.
- **Symbols.** Each symbol is defined at its first use in the text (equation plus gloss, the Fig. 2 caption for R², a sentence for T_d). Fix: the Fig. 5 aggregate box used N and N_hp before IV-A defines them, so it now reads "10–50 households, 5–25 HPs".
- **Cross-references.** All resolve; clean build, 14 pages, 0 undefined references. Sec. IV references were rechecked after the reorder (batch L).
- **Voice.** Fixes: three sentences over 40 words split (V-B population list, which also had an Oxford comma; VI-C pilot size; Sec. VII cooling); two unclear "It"s named ("The SF is by definition bounded…", "$R^2_h$ is lowest in Austin…"). Now 522 sentences, longest 39 words, median 18 (below the skill's 22, by the one-idea-per-sentence rule); no expletive openers; no US "-ize"; no em dashes; no avoid-list words. **Left for Alex:** "percent" (Sec. I ¶1, Alex's edit; British is "per cent").
- **Read-through test.** The first sentences of Sec. I–III and the conclusion carry the core message in order: growth → stress → need → lack → prior work → gap → idea → contributions; quantities and data → two fits → transfer as a tested hypothesis; capacity → energy → flexibility → summary table. Fixed: III-A "Both must describe the same load" → "The net-load arm and the SF must describe the same load". **Suggestion, not applied:** II-C opens by describing Table II ("Table II reports both fits…") rather than stating its point (both fits hold across climates; thresholds follow the climate).
- **Deliverables.** `review/hp_sensitivity_diff_vs_reviewed.pdf` (latexdiff against the reviewed version); this log, with every row given a status; `review/RESPONSE_TO_SUPERVISORS.md` (draft for Alex).
- Supervisor 2 marked no sentences (Alex, 22 Oct); the general comment is answered by the clarity and terminology pass below.

## Clarity and terminology pass (22 Oct; Supervisor 2's general comment)
Supervisor 2 marked no sentences; the comment is that the paper is hard to read because of sentence complexity. Whole-paper pass, two parts.

**Terminology: one term per concept** (counts before → after; text, captions, Table II footnote, figure labels)
| Concept | Before | Now |
|---|---|---|
| temperature | outdoor (5) / ambient (6) | outdoor temperature (incl. the Fig. 1 box) |
| unit | households (62) / consumers (23) | households (incl. N in the Nomenclature, "household count", heatmap axis labels, Table II footnote) |
| s_h | net-load sensitivity / heating sensitivity (3) / net-load numerator (2) | net-load sensitivity ("numerator" kept only where the ratio is explained) |
| m_h | SF sensitivity / transferred, pilot or pilot's sensitivity (11) / slope of the SF | SF sensitivity; "the pilot's SF sensitivity" when the source matters |
| ground truth | true capacity (5) / submetered capacity (7) | true capacity |
| energy | temperature-driven energy / energy consumption (4) / heating-regime energy (3) | temperature-driven energy |
| estimator (iii) | full SF curve / full calibrated SF curve / full pilot curve | full pilot curve; in the conclusion "the pilot's full SF curve, intercept and threshold included" |
| split halves | target half / held-out / second / other half (7) | target half |
| threshold | threshold / balance-point (2) | threshold temperature; the one "also known as balance-point" definition kept |
| spelling | percent / per cent | percent (follows Alex's edit) |
| subsection titles | III: TCL Installed Capacity Estimation / TCL Energy Consumption Estimation / Flexibility Quantification; IV: Installed Capacity Estimation / Energy Consumption Estimation / Flexibility Potential | III: Installed Capacity / Temperature-Driven Energy / Flexibility Potential Estimation; IV: Installed Capacity / Temperature-Driven Energy / Flexibility Potential |

Figures `fig_capacity_heatmap` and `fig_quality_heatmap` regenerated with the axis label "households per aggregate, N" (values identical; `scripts/outputs.py` updated, as is the Table II footnote string).

**Clarity: sentence-level edits** (no number changed; whole-paper token check)
- Removed a redundant sentence (II-A "Note that (2) needs only the net load…", already said at the start of Sec. II).
- Plainer definitions: SF as "the share of the aggregate's installed capacity drawn"; "total" instead of "cumulative" installed capacity; "The measured SF is then defined per regime".
- III-A: "The estimate is therefore only as good as the transferred sensitivity" → "as good as these two sensitivities", which agrees with the results (the net-load sensitivity dominates the error).
- III-B: "The fitted TCL load alone suffices" → "No pilot is needed"; the forecast sentence split.
- III-C: the noun chain "temperature-set energy demand" sentence merged into one plain sentence.
- IV-D: "Spatial / temporal aggregation averages out the intermittent, non-thermal behaviour…" → "Summing more households evens out their individual, non-thermal behaviour. Averaging over longer windows does the same over time…".
- 17 two-idea or nested sentences split (Sec. I HP peak; II-B TCL types and SF-fit inputs; II-C Köppen conclusion; IV-B penetration; IV-C pilot fit; IV-D end cells; IV-E dead-band energy and the hourly-integration sentence; IV-F unused-capacity factor and dead-band floor; V-A planning estimate; V-B housing; VI-D tariffs; VII real aggregates). Openers naming their subject: IV-C "Only the pilot's SF sensitivity transfers…", "The net-load sensitivity, in turn, grows with the installed capacity"; VI-B "The SF sensitivity generalises…".
- After the pass: 535 sentences, longest 39 words, median 17.

## HEAPO stations named (Alex, 21 Oct)
- Hg = **Zürich / Affoltern** (MeteoSwiss REH, 445 m) and MqO = **Einsiedeln** (EIN, 912 m, canton Schwyz). The method is the one that identified 8jB = Kloten: the station altitude, estimated from HEAPO's own pressure (QFE vs QNH), narrows the candidates, and the hourly 2023 air temperature is then identical to MeteoSwiss `tre200h0` in all 8760 hours (max |ΔT| = 0.0000 °C). The next candidates differ by up to 7–11 °C. Reproducible with `scripts/identify_heapo_stations.py` (MeteoSwiss open data, ch.meteoschweiz.ogd-smn).
- The manuscript's first mention (V-A) reads "Zürich-Affoltern (Affoltern below) and Einsiedeln"; "Affoltern" and "Einsiedeln" are used everywhere else (V-A, V-B, VI-B, Tables VI and VII). Generator labels updated in `scripts/outputs.py` (station keys unchanged) and `scripts/planning.py`.
- Alex's edit kept: the Table VII column header "country", now also in the generator.
- II-C opener (Alex, 21 Oct): "Table II reports both fits, P̂_net(T) and SF̂(T), on aggregates from four countries and a range of climates…" → "Both fits hold across climates. Table II reports them on aggregates from four countries, with each climate given as its Köppen–Geiger class." The paragraph now opens with its point.

## Citation placement (Alex, 22 Oct; checked third-party audit)
An external citation audit was checked against the sources before acting on it. It was right on Tre26, Bec24 and the Lov17/Che21b/Rou23 wording. It was wrong on Few24: the Methods state that HPs "contribute 4kW… associated with coincidence factors of 0.425… informed by data from field trials of HPs and EVs in the UK", a diversified peak of 4 kW × 0.425 = 1.7 kW per HP (open PDF on Imperial Spiral). Its dataset complaints misread which sentence the citations sit on.
- Sec. I ¶4: the privacy sentence now also carries the incomplete or out-of-date DER records, citing `Gou26`. "The DSO usually knows how many households each feeder serves" cites `Tre26` (housing units per feeder in its metadata). The clause "but seldom holds the appliance registers or nameplate ratings…" is dropped, because `Tre26` itself holds DSO-recorded low-carbon-technology power.
- Sec. I ¶2: HP peak in cold spells [Vel11, Akm14, Som21, Bec24, Lia26]; new sentence "Electric vehicles (EVs) add further load to the same feeders [Bec24]". This replaces "comes on top of the peak of EVs", which Bec24 does not show (it analyses HP-only and EV-only feeders).
- Sec. I ¶3: design peak = installed capacity × SF [Few24]; "For HPs, it is set by cold weather, when their coincident demand peaks [Lov17, Che21b, Rou23]".
- Sec. I ¶9: "Studies of HP demand measure the coincident peak, as an after-diversity maximum demand, or model the coincidence factor…" [Lov17, Che21b, Rou23].
- IV-B (iv) and IV-C: "national LV (network) studies" → "a Great Britain-wide LV network study" (one study cited), plus "UK field trials".
- No number changed and no new reference added; clean build, 14 pages.

## Figs. 1 and 5 harmonised (Alex, 22 Oct)
- Shared TikZ styles defined once in the preamble (`flow`, `fin` grey inputs, `fproc` processes, `fout` thick outputs, `flab` grey labels): \footnotesize text, 22 × 9 mm boxes.
- Both drawn on a three-column grid 86 mm wide, so they render at the same scale. Before, Fig. 1 (≈101 mm, scaled down) had visibly smaller text than Fig. 5.
- Fig. 1 relaid out in three columns: inputs | SF fit, net-load fit | installed capacity, flexibility, energy (outputs thick). Same boxes, section labels and arrows, except the direct SF-fit → flexibility arrow, which is dropped: the SF sensitivity reaches flexibility through the capacity box, as before.
- Fig. 5 unchanged in content; it now uses the shared styles.

## Two templates from one source: IEEE and Elsevier / Applied Energy (Alex, 26 Oct)
- **Shared text** in `paper/content/`: `abstract.tex`, `nomenclature.tex` (`\nomentry{symbol}{description}`), `body.tex` (Introduction to Conclusion), `macros.tex` (`\chg`, TikZ styles), `highlights.tex`. Edit the paper there; both versions pick the change up.
- **Wrappers**: `paper/hp_sensitivity_overleaf.tex` (IEEEtran, same file name and output as before; the IEEE PDF has exactly the same words as before the split) and `paper/hp_sensitivity_elsevier.tex` (elsarticle `[preprint,12pt]`, `\journal{Applied Energy}`, numbered references with `elsarticle-num`; 42 pages, clean build).
- **Widths**: the body uses `\figw` for single-column figures and `\tabw` for tables, set per wrapper (IEEE: column width; Elsevier: 0.6 and 1.0 text width). Tables only shrink to fit (`\adjustbox{max width=\tabw}`), including in the generator `scripts/outputs.py`.
- **Applied Energy requirements** (guide for authors, read 26 Oct): abstract ≤ 250 words (ours: 250); 1–7 keywords (Elsevier version drops "smart meter data", 7 left); 3–5 highlights of ≤ 85 characters, also as a separate file (`paper/highlights.txt`; drafts of 75–80 characters, **for Alex to review**); numbered references in square brackets in citation order; numbered sections. The required end sections are placeholders marked TODO: CRediT, competing interests, generative-AI declaration, data availability, acknowledgements/funding. **Affiliations are TODO** in the Elsevier front matter; the corresponding-author e-mail is set.
- Elsevier only: relaxed float fractions, so the tall transfer table stays in Sec. 5.2 instead of drifting past the references.
- Overleaf: upload the `content/` folder along with the wrapper(s).
- Alex's in-progress edits to the manuscript ("energy demand", the moved "This paper joins…" sentence, contribution 2, and the "% this sentence is weird" note on the TCL-control sentence) are carried over unchanged into `content/body.tex`.
- **Layout fixes (Alex, 26 Oct; after switching to `[5p,times,twocolumn]`):** float widths now follow the class option. Two-column: figures and tables at the column width, as in IEEE. One-column preprint: figures at 0.6 text width, tables up to the text width. All three builds (Elsevier two-column 17 pp, Elsevier preprint 39 pp, IEEE 14 pp) have no overfull boxes. The reference list uses footnote size with tight spacing (`\bibfont`, `\bibsep`). URLs and DOIs are in the text font (`\urlstyle{same}`) and may break anywhere (`xurl`).
- Fig. 8 y-axis relabelled "net-load sensitivity s_h" (was "heating sensitivity"), matching the text; regenerated with identical values (r = 0.97, slope 0.020).
- "% this sentence is weird" (Sec. I, TCL control models): replacement suggested to Alex, not applied.
- Sec. I, TCL control models (Alex chose option A): "These models describe a population through the thermal parameters of its devices. Callaway [Cal09] uses such a model to make a population follow a load signal, and Hao et al. [Hao15] represent a population as a stochastic battery whose power and energy limits bound its flexibility." The "% this sentence is weird" note is removed.

## Automatic table sizing (Alex, 26 Oct)
- New `autotable` environment in `paper/content/macros.tex` (needs `environ`, loaded by both wrappers): `\begin{autotable}[notes]{caption}{label} tabular \end{autotable}`.
- Rule: set the tabular at `\footnotesize`, then `\scriptsize`; use one column if it fits (it may shrink to `\autotableshrink` = 0.9 of its `\scriptsize` width), else span both columns (`table*`) at `\footnotesize`, then `\scriptsize`; only a table wider than the text block is scaled down. In a one-column layout every table is a plain `table`. The log reports each choice (`autotable tab:...`).
- All seven tables in the paper use it, plus the generators in `scripts/outputs.py` and `scripts/gen_litreview.py`. Table notes (Tables I and II) are the optional argument; `\tnote{a}` marks a note. `threeparttable`, `\tabw` and the per-table `\adjustbox`/`\resizebox` are gone.
- Result: IEEE — Tables I, II span both columns, the rest single column (IV and VI at `\scriptsize`). Elsevier 5p — same, with Tables 4 and 6 at `\scriptsize`. Preprint — all single column; Tables 1 and 2 are still scaled down (as before), and Table 2 no longer overflows the margin by 190 pt.
- Table typography changes only: every table's numbers are unchanged (numeric tokens identical per file). Page counts unchanged (IEEE 14, Elsevier 5p 17, preprint 39).

## Affiliations (Alex, 26 Oct)
- Elsevier wrapper: affiliations copied from Gouveia et al., IJEPES 177 (2026) 111848 (ScienceDirect, read 26 Oct): a ESAT, KU Leuven; b EnergyVille; c VITO; d Orion Grid Technologies; all Belgium. Gouveia a,b,c; Hashmi a,b; D'hulst b,c,d; Van Hertem a,b. The IEEE wrapper still has no affiliations.

## Shortening, tier 1 (Alex, 26 Oct)
Layout and repetition only; no result changed, no number added, every citation kept (checked per item). IEEE 14 → 12 pages, Elsevier 5p 17 → 16, preprint 39 → 36. Body 9,077 → 8,461 words; 11 → 8 figures.
1. **Sec. II, Figs. 2 and 3** (Austin net-load and SF fits) → one two-panel figure, `fig_austin_fits` (a) above (b), shared temperature axis. Same fits (R²_h 0.68/0.91; SF m_h 0.0186, R² 0.84/0.94). Label `fig:austin`; text refers to (a) and (b).
2. **Flatter plots:** slope against capacity, flexibility ratio, flexibility season and flexibility schedule (heights only). The season plot's y-label drops "Δt = 4 h", which its caption already gives.
3. **Sec. IV-B/IV-D:** the two heatmaps → one full-width figure `fig_aggregation_heatmap` (median R²_h of both fits, capacity WAPE). The median signed-error panel is dropped; its range (9–14%) stays in the text. IV-D is folded into IV-B as one paragraph; "sixteen hours close behind" dropped.
4. **Sec. IV-C:** the figure of one Kloten pilot's SF fit is dropped; its fitted line stays in the text.
5. **Sec. VI:** Accuracy, Generalisation and Data Requirements → "Error Sources and Transfer" (365 words); Limitations kept as approved, minus the repeated 0.28 kW figure (848 → 649 words).
6. **Sec. VII:** summary paragraph cut to the method, the two accuracy figures, the transfer rule and energy/flexibility; future work tightened (459 → 356 words). Dropped from the summary only: 12–14% at fifty households, 26% for the full curve.
7. **Sec. I:** opening statistics tightened ("13% more than in 2024" dropped); literature paragraphs and gap paragraph shortened; the roadmap paragraph replaced by one sentence pointing to Fig. 1 (1332 → 1152 words).
- `scripts/outputs.py`: new `fig_austin_fits` and `fig_aggregation_heatmap`; the old single-panel functions remain.
- Diff PDF: the latexdiff build now writes autotables back as plain floats in its scratch copy (latexdiff marked up their arguments).

## Openers and repetition (Alex, 27 Oct; on explore/flex-temperature)
Each paragraph now opens with its main message where it did not; repeated claims cut. No number changed or added, except the two dropped in Sec. IV-E (R4). Every citation kept. IEEE 12 pages, Elsevier 5p 16 → 15, preprint 36 → 35; body 8,489 → 8,277 words.
- **Sec. II-D:** opens with "The method calibrates the SF sensitivity once on a submetered pilot and reuses it on every target."
- **Sec. III-A:** opens with the estimate, $s_k/m_k$. **III-B:** "follows from the net-load fit alone, with no pilot" (the later "No pilot is needed" removed). **III-C:** opens with the definition and (12); the 409-word paragraph split into window, derivation and interpretation ("The shiftable load comes from the net-load fit…").
- **Sec. IV-B:** paragraph restating III-A removed; the subsection opens with the 19% WAPE. Aggregation paragraph opens with its finding; the two sentences it replaces removed. **IV-C:** the "only the pilot's SF sensitivity transfers" sentences removed (R1); the direct test opens with its result. **IV-D:** opens with the 9% WAPE. **IV-E:** opens with the 1.04 median ratio; setup shortened; coldest-day WAPE 21% and R² 0.73 removed (R4; the temperature figure covers the coldest days); temperature paragraph opens with "The annual agreement hides two opposite errors across temperature".
- **Sec. V-A:** results paragraph opens with "within 10%"; the threshold paragraph split, with the baselines in their own paragraph. **V-B:** opens with Table VII's scope. Subsection titles without `\chg{}`.
- **Sec. VI-A:** the restated transfer argument removed (R1). **Limitations:** "within 10%" removed from ¶2 and ¶5 (R2); flexibility paragraph opens with "The estimate gives the median flexibility at each temperature, not its day-to-day spread."

## Table II notes (Alex, 27 Oct)
- Header $n$ → $N$ (the nomenclature symbol for households), so the "$n$: aggregated households" note goes. The $R^2_h$, $R^2_c$ note goes (nomenclature and II-C define them). The commented-out LCL note is deleted.
- Notes (a) Hennepin and (b) WA/OR merged into one note (a) on all three rows: "The SF uses the HPs' own draw only: Hennepin excludes the resistance backup, and WA and OR exclude the electric baseboard, furnace or other zonal heating circuits (17 of 22 and 16 of 21 households) that the net load includes."
- Köppen key and HP abbreviations kept. Cell values unchanged; `scripts/outputs.py` (`tab_cross`) writes the same notes.

## Pending — to address later (Alex, 9 Nov)
Raised on 9 Nov and parked while the error metric and ranges change. Not done yet:
1. **Contributions with key results.** Add one result to each of the three labelled contributions (Alex's labels: Installed Capacity Estimation, SF Sensitivity Transfer, Flexibility Potential Estimation), using the new metric. Note: Supervisor 1's R14–R18 asked for no results in the contributions; confirm with her.
2. **Storyline around the three pillars** (installed capacity, SF transferability, flexibility potential). Candidates from the 9 Nov audit:
   - fold the temperature-driven energy into the flexibility pillar (III-B, IV-D, the energy row of Table III, energy clauses in the abstract, V-A and the Conclusion);
   - cut the II-A interpretation paragraphs (behavioural thresholds; climate balance of s_h and s_c);
   - reduce Table II to the SF columns plus T_h, or move the full table to an appendix;
   - drop the R² panels of the aggregation figure, or replace that figure with the error plot;
   - cut the IV-E concavity / dead-band-floor paragraph;
   - shorten (Alex's call, supervisor-requested): the II-B design-peak paragraph (R28), the 15-min peak SF numbers in IV-C (R31–R32), the §14a paragraph in Limitations;
   - optional: regroup Sec. IV–V by pillar (A capacity, B SF transferability, C flexibility).
3. **Tier 2 shortening items** still open: Table V as a sentence, merged equations, baseline descriptions into Table IV row labels.
4. **Elsevier version:** CRediT, competing-interest, generative-AI, data-availability and acknowledgement sections are TODO (FlexIQ C2M/24/028 funding, if it applies). IEEE version has no affiliations.
5. **Smaller open items:** "percent" (US) once in Sec. I; `scripts/gen_litreview.py` still emits the Azz24 row; nine `\chg{}` markers left (no effect on output); TeXstudio "save before compile" can overwrite tables regenerated outside it.

## Error metric and ranges (Alex, 9 Nov)
- **nMAE replaces WAPE everywhere:** nMAE = mean |ŷ − y| / max y over the scored set (each percentage error scaled by y_i / max y). The set's maximum: all 1260 aggregates for the headline numbers; each penetration group in Table IV; each cell in the aggregation figure; the three real aggregates. New values: capacity 9.5% (own sensitivity 7.1%, full curve 7.5%, planning 10.3%); 22% at 5 HPs to 13% at 25; Table IV groups 29–37% below 15% penetration, 5–9% above 65%; energy 4.1%; flexibility 4.8%; real aggregates 3.8%.
- **Changed finding:** in the aggregation figure the capacity nMAE stays at 10–12% in every cell, so the sentence that the household count matters is replaced: neither form of aggregation matters much; HP penetration drives the error.
- **10–90% ranges replace IQRs everywhere:** Table V spreads (m_h 0.0084 → 0.0023), pilot m_h 0.017–0.019, direct test R² 0.77–0.95 and capacity −8% to +27%, annual flexibility ratio [0.92, 1.35], VI-A ratio 0.84–1.22, Table VII (all ranges wider, ratios unchanged), V-B RHPP −28/+39% at 10 to −11/+13% at 91, Fig. 8 bands and day-to-day spread. "Ranges are 10–90% ranges" is stated once in IV-A; the IQR nomenclature entry is removed.
- **New Fig. 5 (IV-B):** signed capacity error / max true capacity of all 1260 Kloten aggregates (177 kW), median and 10–90% in 20 kW bins. Median +5% to +10% at every size; range about −6% to +21% up to 160 kW; above 160 kW one split's pilot (m_h 0.014 °C⁻¹, lowest of 20) overestimates its target half by up to 65%. The lead-in sentence and caption are new wording, written after the plot changed to the overall maximum.
- Abstract (250 words), highlights, Conclusion, Fig. 4 box, Table IV/V/VII captions updated. IEEE 13 pages, Elsevier 5p 16.

## Fig. 5 by HP penetration (Alex, 9 Nov)
- **Fig. 5 redrawn:** ratio of estimated to true capacity (ŷ/y, each aggregate against its own true value) against HP penetration N_hp/N, median line and 10–90% shade, no binning and no points. Replaces the error / overall-max version in 20 kW bins. `outputs.fig_capacity_error(kind='pen')` is now the default; 'ratio' and 'norm' are kept.
- **IV-B lead-in and caption rewritten:** median 1.66 at 10% penetration, 1.07–1.13 from 50% on; range 1.30–2.21 at 10%, about 0.9–1.3 above 50%; below 15% even P10 overestimates, by 5–30%. The outlier-pilot sentence (split with m_h 0.014) is gone with the old plot.
- **Why the ratio falls with penetration (new IV-B paragraph):** s_h also absorbs the temperature response of the non-HP load. With each aggregate's own m_h the median ratio still falls, 1.57 → 1.06, so the pilot is not the cause. Heating slopes at a common 16.5 °C threshold: HP 0.112 kW/°C, other load of its home 0.0098, HP-free home 0.0064. Predicted ratio 1 + (s_o + s_f(1−p)/p)/s_hp is within 0.11 of the median at every penetration. A tenth of the HP-free homes give 81% of their response (median slope 0.0019), hence the wide band at low penetration. Numbers from `outputs.capacity_bias_decomposition()`. IV-B ¶1 now says the overestimate "comes from" the non-TCL response (was "is consistent with"), and its "possibly because" sentence is deleted.

## Cuts, round 1 (Alex, 9 Nov)
- **A. Aggregation in time and space removed:** the aggregation figure (net-load and SF R²_h and capacity nMAE against households per aggregate and averaging window) and its two IV-B paragraphs are deleted, including the 10–12% nMAE-per-cell finding and "the daily mean suffices". Contribution 2 drops "and data resolution". Limitations ¶4 drops the sentence comparing the flexibility spread with the fit quality of that figure. The optional one-sentence justification of the daily mean was not added. `outputs.fig_aggregation_heatmap` is left in the scripts.
- **B. Duplication with the new IV-B bias paragraph removed:** VI-A ¶1 no longer gives the zero-HP control (0.28 kW of spurious capacity per household, about 45% at 10% penetration, about 4% at 100%), which sized the same effect by another method with different numbers; it now points to IV-B. Limitations ¶3 refers to IV-B instead of the zero-HP control. IV-C drops "This slope exceeds the pilot SF sensitivity by about 12%, a first sign of…". IV-B drops "This points to the net-load sensitivity as the dominant error at low penetration."
- **C2. IV-E dead-band floor shortened:** the mild-weather paragraph is cut to two sentences (HP use that does not depend on temperature, most plausibly hot water; measured 0.05–0.06 kW per kW at 14–16 °C). Removed: the 9% floor on dead-band days, the 9–18% overestimate once the floor is removed, the steeper-arm and "buildings stop heating at different temperatures" explanations. C1 (II-A interpretation paragraphs) was not applied. IEEE 12 pages, Elsevier 5p 15.

## Pending after cuts round 1 (Alex, 9 Nov)
- **C1 kept as is for now:** the II-A interpretation paragraphs (behavioural thresholds; climate balance of s_h and s_c) stay.
- **To come back to later:** D1 fold the temperature-driven energy into the flexibility pillar (II-E, IV-D, Table III energy row, abstract, Conclusion); D2 reduce Table II to the SF columns plus T_h, or move it to an appendix; D3 supervisor-requested items (II-B design-peak paragraph R28, IV-C 15-min peak SF numbers R31–R32, §14a paragraph in Limitations), kept unless Alex decides otherwise.

## Optional non-TCL correction (Alex, 9 Nov)
- **Sec. II:** after \eqref{eq:decomp}, the per-household non-TCL sensitivity s_n is named; the neglected term grows with N and weighs most at low TCL penetration. Replaces "Section VI revisits this assumption."
- **Sec. III-A:** new optional correction, Eq. capacity-corr: (s_h − N s_n)/m_h, with s_n fitted on households without TCLs (e.g., a feeder without HPs); needs N only, not which households hold a TCL. Nomenclature gains s_n.
- **IV-B ¶3 rewritten** around the correction. In each split, s_n is fitted on 50 HP-free homes that no aggregate of that split contains (489–525 spare per split), at each aggregate's own threshold: median 0.005 kW/°C. Corrected median ratio 1.19 at 10% penetration (uncorrected 1.66), 1.00–1.11 from 15% on; nMAE 9.5% → 7.5%; overall median ratio 1.16 → 1.05. The spread stays. Counter-example: the pilot's other load (0.011 kW/°C) leaves the estimate a third too low at low penetration. The closed-form ratio formula and "within 0.11" are gone. Numbers from `outputs.capacity_correction()`; the draw replay `_kloten_free_draws` checks itself against the cached capacities.
- **Fig. 5:** corrected median and 10–90% band added (orange) next to the uncorrected one; y from 0.5.
- The previewed numbers (calibration homes possibly shared with aggregates) were 1.12 at 10% and nMAE 8.1%; the disjoint set gives 1.19 and 7.5%.
- **Limitations ¶3:** "Section VII outlines a correction" → "Section III-A gives a correction".
- **Conclusion:** the correction leaves the future-work list ("Five directions" → "Four directions") and becomes a result sentence after the real-aggregate result: subtracting a per-household non-TCL sensitivity, fitted on households without TCLs, removes most of the overestimate and lowers the nMAE to 7.5%. Abstract and highlights unchanged.
- **III-A, after Eq. capacity-corr:** "The correction needs no knowledge of which households hold a TCL." → "On a target aggregate, the correction needs only its household count N^i, not which of its households hold a TCL." (Alex: the point applies to unseen aggregates; the repeated "aggregate" is fine.)
- **Non-TCL sensitivity per regime:** s_n → s_{n,h}, s_{n,c} (Sec. II, IV-B, nomenclature). III-A now states that s_{n,k} comes from the same net-load fit (Eq. bathtub), applied to an aggregate without TCLs (e.g., a feeder without HPs or air conditioners) at the target's thresholds and divided by its household count; Eq. capacity-corr gives both regimes. The cooling correction is untested, like the cooling regime as a whole.

## Estimator comparisons removed (Alex, 9 Nov; option 1)
- **IV-B:** Table IV (capacity nMAE of four estimators by penetration group) and its text are deleted: the list of estimators (i)–(iv) and the two paragraphs on (ii) against (i) and on (iii) and (iv) (full pilot curve 7.5%, planning SF of 0.425 at 10.3%, the b_h ≈ 0.03 offset argument).
- **V-A:** the \chg paragraph on the full curve and the planning estimate is replaced by its own-m_h sentences (errors +6%, +5%, +3%; small since every household has an HP). The threshold paragraph with the full-curve errors (−3%, −20%, −26%) stays as the evidence that only the sensitivity transfers (option 1); VI-A ¶2 keeps its full-curve sentence.
- **Table VI:** the planning-SF column is dropped; other values unchanged.
- **VI-A ¶1:** "With each aggregate's own SF sensitivity, the nMAE is 7.1%, against 9.5% with the pilot's." (no table reference).
- Few24 and 0.425 stay in Sec. I and IV-C (15-min peak SF against the planning value). `outputs.tab_baselines` is left in the scripts.
- **Table V → Fig. 6(b):** Table V (SF fits at N = 50 by N_hp) is removed. Fig. 6 gains panel (b): each aggregate's own m_h against installed capacity, as the 10–90% range over a 40 kW rolling window (evaluated every kW with ≥ 100 aggregates), the median of all 1260 aggregates (0.0180) and the median of the 20 pilots (0.0178). Colour bar label "number of HPs". IV-C now cites Fig. 6(b): m_h holds near 0.018 at every capacity (Spearman −0.06), maximum heating SF near 0.47 (was 0.48 at N = 50); the 10–90% width of m_h at five HPs is 0.0092 over all aggregates (was 0.0084 at N = 50), 0.0023 at twenty-five unchanged. R²_h and b_h by N_hp are no longer reported.
- **Fig. 6 x-axis:** limited to the capacities the aggregates span (about 15–181 kW) instead of starting at 0; the through-origin line in (a) is drawn over that range only.
- **Fig. 5 x-axis:** 8–102% with ticks every 10%, covering only the penetrations of the design (10–100%).
- **Fig. 7:** the dotted "actual, T ≥ T_h" dead-band curve and its legend entry are removed, and the x-axis ends 1 °C after the last heating-regime bin (about 19 °C) instead of running to 26 °C. The "median T_h" label sits left of its line. No text referred to the dotted curve.
- **Day-to-day flexibility spread scrapped:** Fig. 7(b) (day-to-day 10–90% range over the median by 2 °C bin, for 5, 15 and 25 HPs) is removed, so Fig. 7 is one panel; caption and the IV-E reference updated. Limitations ¶4 loses "On nine days in ten, the measured flexibility stays above 85% of its median with 5 HPs and 87% with 25. The spread is narrowest on cold days and widest at 13–15 °C…"; it keeps "The estimate gives the median flexibility at each temperature, not its day-to-day spread."
- **Fig. 7 per kW installed:** flexible energy per hour of window and per kW of true installed capacity (actual = mean SF(1−SF), ceiling 0.25), replacing the own-maximum normalisation that the sparse coldest bin anchored. Bins are 2 °C and no longer merged (the 1-, 3- and 5-day cold bins show separately), with a day-count strip below. Estimate/actual: 1.16–1.19 below −1 °C, 1.09–1.11 from 0 to 6 °C, 0.89–0.91 at 12–14 °C, so the IV-E numbers (18% on the coldest days, 9–11% at 11–15 °C) hold. Code: `FT.flex_all_per_kw`, `FT.fig_flex_per_kw`; `outputs.flex_temperature_figure` now calls them. Also fixed two lost backslashes in `FT.fig_flex_all`.
- **III-A (Alex's edit in TeXstudio):** deleted "The two regimes are estimated separately. A reversible HP counts in both P̂_h^max and P̂_c^max, so the total installed capacity of a population of reversible HPs lies between the larger of the two and their sum."
- **IV-E:** added "The estimate is closest to the actual, within 2%, between 7 and 11 °C, around the mean temperature of the heating days, 7.4 °C." (estimate/actual 1.02 at 7–9 °C and 0.99 at 9–11 °C; mean of each aggregate's heating-day temperatures pooled, 7.4 °C). The 11–13 °C bin, second in heating days, is 11% low, so the wording avoids "the most frequent bins".
- **IV-E:** deleted "For the aggregates of 50 households with 25 HPs, only the energy factor follows this profile, and the days above 13 °C hold only 6% of the flexible energy." It was left over from the 60-aggregate Fig. 7; the first clause repeated the opening and coldest-days paragraphs, and the share is now 5.2% over all 1260 aggregates.
- **Fig. 5 labels:** legend "corrected" → "corrected with known N"; caption "corrected" → "corrected with the known household count N" (Alex's wording).

## Pending — "real aggregates" (Alex, 10 Nov)
- **Refrain from calling Affoltern and Einsiedeln "real aggregates".** Each is the set of HEAPO households of one weather station: in the same area, but not guaranteed to share an LV network. Term to revisit wherever it is used: Sec. V title and V-A heading, the abstract, the Conclusion, VI-A, Fig. 4 box. The contribution 1 result sentence drops its "within 10% on three real aggregates" clause for this reason.
- **Hamelin (WPuQ) stays a real aggregate** (Alex, 10 Nov): its 37 houses are connected to the same LV network, even though the net load is summed from individual meters rather than metered at the transformer.

## Contributions with key results (Alex, 10 Nov)
- **Contribution 1:** adds "On 1260 semi-synthetic Swiss aggregates, the capacity is recovered at an nMAE of 9.5%, or 7.5% when the total number of households is known." (Alex's wording for the corrected value; the real-aggregate clause was dropped, see the "real aggregates" pending note.)
- **Contribution 2:** rewritten as one ordered list of the transfers tested: median ratio 1.00 between aggregates of one population; within 10% between cities, 12% between countries, 14% between HP technologies; 1.65-fold between housing tenures ("tenure" replaces "type" for social versus private) and 1.7-fold between climate zones.
- **Contribution 3:** flexibility only, the energy estimate is no longer named: a method to quantify the flexibility potential against temperature, 4.8% nMAE on the annual flexible energy.
- Supervisor 1's R14–R18 (no results in the contributions) overruled by Alex: contributions carry a summarised headline result. IEEE 12 pages, Elsevier 5p 15.

## "Real aggregates" wording (Alex, 10 Nov)
- **Terms:** Affoltern and Einsiedeln are now "regional aggregates" (households of one area, not necessarily on one LV network); Hamelin stays "a real aggregate" of 37 houses on one LV network; the three together are "aggregates outside the pilot".
- **Changed:** abstract ("On three aggregates outside the pilot, where every household has an HP, …"; 249 words); II-F reference to V-A; Sec. V title "Real Aggregates" → "Validation outside the Pilot"; V-A heading → "Aggregates outside the Pilot"; V-A ¶1 and ¶3 drop "real"; V-A ¶2 names the two regional aggregates, adds "Their households share an area but not necessarily an LV network." and describes Hamelin as a real aggregate on one LV network; Limitations ¶2 and ¶4 ("these aggregates", "the aggregates outside the pilot"); Conclusion ("two Swiss regional aggregates and a German LV network"); Table IV caption "Transfer to aggregates outside the Kloten pilot" (also in `outputs.tab_real`). The label sec:real-agg is kept. Resolves the "real aggregates" pending note. IEEE 12 pages, Elsevier 5p 15.

## D1: temperature-driven energy folded into the flexibility (Alex, 10 Nov)
- **Two outputs, not three:** Sec. II ¶1 and the Sec. III intro now name installed capacity and flexibility potential; the temperature-driven energy is the baseline the flexibility builds on, given by the net-load fit without a pilot.
- **Fig. 1:** the "Energy" output box becomes an intermediate "Baseline energy" box (Sec. III-B) feeding Flexibility; caption "the two outputs".
- **III-B "Temperature-Driven Energy Estimation" removed as a subsection:** eq. (energy) and the dead-band sentence move into the Flexibility subsection as its baseline paragraph. Dropped: annual energy as the sum over days; separating / forecasting the daily TCL load; "captures the temperature-driven share, not the annual total".
- **Table III:** Energy row deleted.
- **IV-D "Temperature-Driven Energy" removed as a subsection:** its median ratio 0.97 and nMAE 4.1% move into the IV-E decomposition as the first factor (baseline energy). Dropped energy-only results: about 7% of annual HP energy in the dead band, annual ratio 0.90, hourly integration lifting it to 0.94. "energy ratios" → "energy factor(s)" in IV-E and V-A.
- **Abstract** (236 words): "The same fits recover a flexibility potential at an nMAE of 4.8%, overestimated by 18% on the coldest days."
- **Conclusion:** ¶1 drops the energy nMAE; ¶2 "…the temperature-driven TCL energy that the flexibility builds on"; last future-work direction now closes "the gap between the estimated and the measured flexibility in mild weather".
- **Highlights:** 3 "9.5% nMAE on 1260 semi-synthetic aggregates; within 10% outside the pilot" (leftover "real ones"); 4 "housing types" → "housing tenures"; 5 "The same fits quantify the flexibility potential at a 4.8% nMAE".
- **Table I:** "This work" task "Capacity, flexibility" (tex and `gen_litreview.py`).
- IEEE 12 pages, Elsevier 5p 15.

## D2: Table II kept as is (Alex, 10 Nov)
- Options offered: (1) drop P_base, b_h, b_c, SF^max_h, SF^max_c (19 → 14 columns, text unchanged); (2) SF columns plus T_h, cutting the II-E net-load sentences; (3) full table in an appendix. Alex: keep all 19 columns for now. Option 1 remains the fallback if space is needed.

## D3: supervisor-requested passages shortened (Alex, 10 Nov)
- **II-B design peak (R28), 4 → 2 sentences:** "The SF fit also links to the design peak of Section I. At a design temperature T_d < T_h, the design SF is b_h + m_h (T_h − T_d), and the installed capacity times this SF gives a daily-mean design load, which the 15-min design peak exceeds (Section IV-C)."
- **IV-C 15-min peak SF (R31–R32), 4 → 3 sentences, \chg removed:** "…reaches 0.56 on the coldest day, which is 1.28 times the daily mean. This lies above the HP SF of 0.425…". Dropped: 0.59 over the year; 1.75 times on a median heating day.
- **Limitations, tariff control, 6 → 4 sentences:** opens "Deliberate HP control may also bias the estimate." (replaces "…also bound the effect of…", which Alex found unclear); tariffs and §14a in one sentence; ends "The aggregates outside the pilot may run under such tariffs, yet their estimates show no visible error from it." Dropped: "The WPuQ campaign predates §14a, but blocking-period tariffs do not."
- Five \chg markers remain. IEEE 11 pages, Elsevier 5p 14 (with D1).

## Abstract and highlights (Alex, 10 Nov)
- **Abstract (238 words):** capacity result now "…an nMAE of 9.5%, or 7.5% when the total number of households is known. The error grows as fewer households have an HP."; the flexibility sentence ends at "an nMAE of 4.8%" (the "overestimated by 18% on the coldest days" clause is removed, Alex).
- **Highlights (version A):** bullets 1–2 merged into "Heat-pump capacity is estimated from feeder net load, temperature and a small pilot" (83 characters); new bullet 3 "Knowing the total number of households lowers the capacity nMAE to 7.5%" (71). Others unchanged. IEEE 11 pages, Elsevier 5p 14.

## C1: II-A threshold paragraph (Alex, 10 Nov; option 3)
- The three II-A interpretation paragraphs stay. The threshold paragraph no longer calls T_h and T_c "behavioural… rather than a property of any building or device", which contradicted V-A (threshold set by insulation, internal gains and setpoint, Men18). Now: "…mark where the population, on average, begins to heat or cool. They reflect both its buildings and its habits. … settle at values typical of the region (Section II-E)." Options not taken: cut the threshold and climate-balance paragraphs and shorten the sensitivity one (1); cut all three (2).

## Small items (Alex, 10 Nov)
- **Sec. I ¶1:** "over twenty percent" → "over 20%".
- **\chg wrappers:** the last five removed (II-B, II-E, three V-B paragraphs); text and output unchanged. The macro stays in macros.tex.
- **gen_litreview.py:** Azz24 row removed. Note: the generator is out of sync with the hand-edited Table I in more than this row (footnote, Jar22, Wan20, Oma24, Per17b, Mat13, Hao15, Zha16b, And20b, the missing Rou23 row, the PV-capacity group name). Synced in the next entry.
- **replication.py:** step list now matches the paper (Table I, Fig. 2 fig_austin_fits, Table II, Fig. 3, Fig. 5 fig_capacity_error, Fig. 6, Fig. 7, Table IV tab_real, Table V tab_transfer). Dropped steps for artifacts no longer in the paper: fig_bathtub_example, fig_sf_arms_anchored, fig_quality_heatmap, tab_sf/fig_sf_pilot, fig_capacity_heatmap, tab_baselines. The two new steps run and reproduce the published Figs. 2 and 5.
- **Not done:** unused generators stay in outputs.py and flex_temperature.py, since paper_results.ipynb still calls most of them.
- Corrected the "real aggregates" entry: tab_real is Table IV, not Table VI.

## Table I generator synced (Alex, 10 Nov)
- `gen_litreview.py` now carries every hand edit of Table I: Jar22, Wan20, Oma24, Per17b (AC, submetered, target), Mat13 and Hao15 (no training), Zha16b (statistical, cloud cover), And20b (data-driven thermal relation), the Rou23 row, the group name "PV capacity", the column definitions kept as a commented-out line of the note, and no HVAC abbreviation. Its output equals the paper's table except two leading tabs in the note, so tab_litreview.tex was rewritten from the generator (no change in the PDF). `replication.py --run tab_litreview` now reports a match.

## Secs. IV–V regrouped by pillar (Alex, 10 Nov)
- **New structure:** IV Data and Evaluation Design (intro with the error metrics; A Kloten Pilot and Semi-Synthetic Aggregates; B Aggregates outside the Pilot; C Populations with Submetered Heating). V Results (A Installed Capacity; B Transfer of the SF Sensitivity; C Flexibility Potential). The old IV "Numerical Results" and V "Validation outside the Pilot" are gone; Discussion is now VI, Conclusion VII.
- **Moves (wording unchanged):** s_h-tracks-capacity paragraph and Fig. slope_capacity from old IV-C to V-A; outside-pilot capacity errors, Table IV and own-SF errors to V-A; old IV-C invariance, 15-min peak, split and target-half paragraphs, the thresholds paragraph and the Table V results to V-B; the 0.93–0.96 outside-pilot flexibility result to the end of V-C. The data paragraphs of old V-A and V-B moved to IV-B and IV-C.
- **New or changed sentences:** IV intro "The evaluation draws on three sets of data, each further from the pilot. …"; IV-A "The main experiment emulates …"; IV-B "Three aggregates lie outside the Kloten pilot, each summed from its own field meters. Their submetered data serve only to validate the results, never as input."; IV-C "The SF transfer is further tested on every population with submetered heating available to this study, beyond the one Swiss pilot."; V intro "This section reports the results in the order of the three contributions: …"; V-A "The net-load sensitivity grows with the installed capacity, as Section II-A anticipated."; "On all three aggregates outside the pilot, …"; V-B opener "The capacity estimate divides the net-load sensitivity, which grows with the installed capacity, by the SF sensitivity, which should not. …"; "Outside the pilot, the thresholds show why …"; "Table V reports the transfer on the populations of Section IV-C."; V-C "On the three aggregates outside the pilot, the flexibility ratio …". Dropped: old V-A ¶1 ("Section IV tested the method within one population …"; "Swiss and German aggregates test the heating regime with the Kloten pilot.") and the old IV-C opener.
- **Cross-references:** Fig. 1 caption and the II-A dead-band sentence cite Section V only; II-A s_h sentence → V-A; II-C expectation → V-B; II-D hypothesis "Section V-B tests it in three steps, each wider than the last: within one population, on aggregates outside the pilot and across populations from five countries."; Limitations → V-A. Labels sec:validation, sec:real-agg and sec:transfer-pop removed; sec:data-kloten, sec:data-real and sec:data-pop added.
- **Numbering:** fig_slope_capacity is now Fig. 5 and fig_capacity_error Fig. 6 (replication.py labels swapped). No number in the text changed.
- IEEE 12 pages (two references spill onto p. 12), Elsevier 5p 15 (likewise). Was 11 / 14.

## Page trims after the regroup (Alex, 10 Nov; T2–T5)
- The regroup pushed two references onto a 12th (IEEE) / 15th (Elsevier) page. Four repeated sentences cut:
- **VI-A ¶2 (T2):** "Transferring the full pilot curve, threshold and intercept included, raises the capacity error to 20% at Einsiedeln and 26% at Hamelin." (repeats V-B).
- **Limitations ¶2 (T3):** "Table V tests the SF transfer further, on populations from five countries." (repeats V-B and II-D).
- **IV-C (T4):** "On these datasets, only the SF transfer is tested." (said in the IV intro and the paragraph's last sentence).
- **V-B opener (T5):** second sentence now "This subsection tests the second, the hypothesis of Section II-D." (the three steps are listed in II-D).
- Not taken: dropping the V intro sentence (T1) and the VI-A factor sentence (T6). IEEE 11 pages, Elsevier 5p 14.

## Table IV (tab_real) dropped (Alex, 10 Nov)
- After the regroup, the table mixed V-A (capacity), V-B (full-curve errors) and V-C (flexibility) results. Every value except the kW capacities was already in the text, so the table is removed and the transfer table becomes Table IV.
- **V-A:** "On all three aggregates outside the pilot, the capacity estimate lies within 10% of the true capacity, at an nMAE of 3.8%. It gives 112 against 109 kW at Affoltern (+2%), 48 against 51 kW at Einsiedeln (−6%) and 217 against 239 kW at Hamelin (−9%)."
- **V-C:** the flexibility ratio "is 0.96 at Affoltern and 0.93 at Einsiedeln and Hamelin" (was "lies between 0.93 and 0.96").
- `tab_real()` and paper/tables/tab_real.tex stay as the source of these numbers; replication.py labels: tab_real "Sec. V numbers", tab_transfer "Table IV".
- IEEE 11 pages (last page now has room), Elsevier 5p 14.

## Full-pilot SF fit moved from IV-B to V-B (Alex, 10 Nov)
- **IV-B:** ends "For these aggregates, the pilot comprises all 50 Kloten HPs." (was "The pilot now comprises …" followed by the fit and "only its sensitivity m_h = 0.018 °C⁻¹ transfers").
- **V-B thresholds paragraph:** second sentence "The SF fit of the full Kloten pilot, at its own net-load threshold, is SF_h(T) = 0.029 + 0.018 (16.6 − T)."; "The net-load thresholds of the targets are … against 16.6 °C for the pilot." No number changed. IEEE 11 pages, Elsevier 5p 14.

## V-A self-reference removed (Alex, 10 Nov)
- After the regroup, V-A cited itself. Now: "Einsiedeln holds only six HPs, below the ten from which the Kloten aggregates give reliable estimates, so its result is indicative." No other section cites itself. IEEE 11 pages, Elsevier 5p 14.

## Fig. 7: legend, axis label, caption (Alex, 10 Nov)
- **Figure (flex_temperature.fig_flex_per_kw, regenerated):** legend moved to the lower left of the top panel; y-axis label "E_flex / (P^max Δt_Th)" (was "E_flex per kW installed (kWh/h per kW)"). Data unchanged; the pixel diff before the label change covered only the two legend positions.
- **Caption (~75 → ~35 words):** "Flexible energy normalised by the window Δt_Th and the true installed capacity, E_flex/(P^max Δt_Th), against daily mean temperature, for the 1260 Kloten aggregates in 2 °C bins. Bottom: number of days of 2023 in each bin." Dropped: "median and 10–90% range across aggregates" (in the legend); the SF(1−SF) ≤ 0.25 sentence (Alex); the "not observed flexibility" caveat (V-C and Limitations cover it). IEEE 11 pages, Elsevier 5p 14.

## Normalised flexible energy: III-B and Fig. 7 caption (Alex, 10 Nov)
- **III-B:** "Since E_flex is linear in Δt_Th, Section V-C reports the normalised flexible energy E_flex/(P^max Δt_Th), with P^max the true installed capacity. Dividing by the window frees the results from a parameter that this paper takes as given rather than estimates. Dividing by the capacity makes aggregates with different numbers and sizes of HPs comparable." (was "… reports it per hour of window, or as ratios in which the window cancels."; V-C already says Δt_Th cancels in the ratio).
- **Fig. 7 caption:** "Normalised flexible energy E_flex/(P^max Δt_Th) against daily mean temperature, for the 1260 Kloten aggregates in 2 °C bins, where P^max is the true installed capacity. Bottom: …" (the previous wording read as if the expression defined the capacity, Alex). IEEE 11 pages, Elsevier 5p 14.

## Page cut to 10 (IEEE), route 3 (Alex, 10 Nov)
- **S1, nomenclature:** removed from the IEEE wrapper only (hp_sensitivity_overleaf.tex); the Elsevier version keeps it.
- **S2, Fig. 4 (Kloten split diagram):** removed, with "Fig. 4 sketches one split." in IV-A; the split paragraph describes it in full. Figs. 5–7 are now Figs. 4–6 (replication.py labels updated).
