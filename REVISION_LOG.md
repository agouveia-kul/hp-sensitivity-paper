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
| R10 | 1 | title, "from Net Load and Temperature" | Explain setup and pilot | new ¶11 states the setup (feeder net load + temperature, one number from a submetered pilot, ratio gives capacity); abstract sentences 3–5 do the same | S1 | done |
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
| R22 | 3 | Sec. II opening paragraph | Hard to follow; data needs; Fig. 1 | Opening reduced to the three quantities and the data each needs; Fig. 1 moved to the end of Sec. III (now Fig. 4), after its blocks are defined | S1b, S2 | done |
| R23 | 3 | "treats R2 as out of scope" | Cooling analysis would be analogous | II-A: "characterises R1 and R3 alike and leaves R2 out of scope"; the evaluation covers R1 only, since the data allow no test of the R3 transfer (Sec. VI) | S3 | done |
| R24 | 4 | "the hat marks a fitted function" | Rephrase | "From (2), the temperature-driven component of the aggregated load of an aggregate i, with its own fitted parameters, is" (3); hat sentence deleted | S5 | done |
| R25 | 4 | "P_base … discarded" | Needed? | "P_base … discarded" sentence deleted | S5 | done |
| R26 | 4 | strike-out of ", i.e., a larger share of consumers with a TCL" (l.218) | (strike-out, no text) | | | open (L, delete) |
| R27 | 4 | "Table II spans this range…" | Introduce Table II | Alex removed the "Table II spans this range…" sentence; II-C still opens by introducing Table II | S2b | done |
| R28 | 4 | "SF(T)" | How does this match planning? | New II-B paragraph: design SF = b_h + m_h(T_h − T_d); design peak = installed capacity × design SF (back to Sec. I); daily-mean caveat with the IV-C ratio. T_d added to the Nomenclature | S5 | done |
| R29 | 4 | "In this work," (99.9th pct) | Why not max? Say values unavailable | "Nameplate ratings are not available for most households, so the installed capacity of each TCL is taken as the peak of its submetered 15-min draw." The 99.9th percentile is removed from the paper (Alex) | S2b | done |
| R30 | 4 | "isolated metering spikes" | Data cleaning; just say max | "isolated metering spikes" removed with the percentile | S2b | done |
| R31 | 4 | "which takes the peak interval" | What is the peak interval? | "the 15-min interval of highest aggregate demand"; "coincidence factor" → "the SF used in network planning" | S5 | done |
| R32 | 4 | Kloten 1.28× / 1.75× | Data not yet introduced | Kloten 1.28× / 1.75× moved verbatim to IV-C, after the 15-min peak SF; II-B points there | S5 | done |
| R33 | 4 | "Using the total TCL installed capacity … underestimation" | Too obvious | Sentence kept as in the original (removed in S5, restored in S5b) | S5b | declined (Alex disagrees with the comment) |
| R34 | 4 | eqs (5)–(7) | Heating only, cooling analogous | Eqs. (5)-(7) kept generic for heating and cooling | S3 | declined (Alex: generic everywhere except the results) |
| R35 | 4 | "(7)" | "which data do you need to do this fit? This is not so straightforward to do, no? Explain this a bit better." (one sentence may be too little; see S2) | | | open (L) |
| R36 | 5 | "R1, R3, or" | What are these? | R1/R2/R3 replaced by heating regime / dead band / cooling regime throughout the text, captions, Table II footnote and figure labels | S4 | done |
| R37 | 5 | same | Refer to the figure | II-A and II-C point to the Austin net-load figure (Fig. 1), which now labels the regimes in words | S4 | done |
| R38 | 5 | "so the transfer of Section II-D" | Weird sentence | | | open (L) |
| R39 | 5 | II-D first sentence, "submetered TCL data" (l.308) | "aha, why only here?" | Sec. I ¶11 introduces submetering and the pilot; II-D explains why the SF fit needs it | S1, S2 | done |
| R40 | 5 | II-D pilot/target definitions | Already for Table II? What is calibration? | II-D defines calibrate, pilot, target and split in plain words, and states that Table II involves no transfer | S2 | done |
| R41 | 5 | "Section IV-C tests this hypothesis…" | Paper builds on an untested hypothesis | II-D presents the transfer as the single assumption, with early evidence (Table II; Kloten m_h vs number of HPs, Table III) and pointers to the tests; the section reorder follows in S7 | S2 | partly |
| R42 | 5 | "R²_h" | What is this? | R²_h and R²_c defined at first appearance (Fig. 1 caption) and in II-C | S4 | done |
| R43 | 6 | P_net(t) | "T?" | t defined as time after eq. (1); T defined as the daily mean temperature in the eq. (2) gloss; III-A no longer mixes P_net(t) with the fitted P_TCL(T) | S4 | done |
| R44 | 6 | "R2 bounds the estimate" | Use "dead band" | "The dead band bounds the estimate." | S4 | done |
| R45 | 6 | "The temperature cancels, so" | Write "Note that…" | | | open (L) |
| R46 | 6 | "The two regimes are estimated separately." | Heating only | III-B equations kept for both regimes; the reversible-HP paragraph shortened to two sentences | S3, S3b | declined (Alex: generic everywhere except the results) |
| R47 | 6 | III-C cancellation passage | Unclear; how is Δt_Th set? | III-C opens with the use (congestion management, flexibility products); the window is an exogenous building-stock parameter; the cancellation is two plain sentences; E_flex is linear in the window, so results are per hour or ratios. Literature range for the window: D4, needs Alex | S6 | partly |
| R48 | 6 | "Over a year, this paper counts…" | Rephrase or move; why useful? | Annual counting moved to the IV-F opening, with why the annual sum is useful; IV-F's repeated cancellation sentence dropped | S6 | done |
| R49 | 7 | IV-A split procedure | Why? What is fitted and estimated? | | | open (S7) |
| R50 | 7 | Fig. 5 number recital | Just the conclusion | | | open (S7) |
| R51 | 8 | "Installed Capacity Estimation" | Why not first? | | | open (S7, D5) |
| R52 | 8 | "1260 aggregates at a WAPE of 19%" | Different capacity per aggregate? | | | open (S7) |
| R53 | 9 | "Transferring the full SF curve…" | Not understood | | | open (S7) |
| R54 | 9 | "About three points" | Three points? | | | open (L) |
| R55 | 11 | VI-D "…but not the net-load numerator." | What was done to counter limits? | | | open (S8) |
| R56 | 12 | "s" over "ted" of "This paper presented" (Conclusion, l.578) | "s" | needs Alex → Alex: "This paper presents" (as recommended); applied in S8 | S1 | open (S8) |
| R57 | 12 | strike-out of "Most of this error stems from the net-load slope, … rather than from the transfer of the SF slope." (l.578) | (strike-out, no text) | | | open (S8, delete) |
| S2-xx | — | Supervisor 2 marks | — | | | needs Alex (file missing) |

## Decisions for Alex

Answered 16 Oct 2026: **D1 yes · D2 words · D5 capacity first · D7 as recommended · R03 and R56 as recommended.** D3, D4 and D6 are still open.

| ID | Question | Recommendation |
|---|---|---|
| D1 | Present the method heating-only, with cooling by symmetry? (Alex, 16 Oct: **no**. Generic in Sec. II–III; only the results, Sec. IV–V, are heating-only) | Yes. Every quantitative result is heating-only, and the cooling fits are descriptive (l.570). |
| D2 | Regime names: words or new symbols? (Alex, 16 Oct: **words**; applied in S4) | Words: heating regime, dead band, cooling regime. |
| D3 | Run the capacity-definition robustness check (max, HEAPO nameplate)? (Alex, 19 Oct: **run**; results below, needs Alex) | Run it. Numbers go in only after review. |
| D4 | Δt_Th literature range (verified source found: Hong et al. 2013, 1–2 h existing, up to 6 h improved; proposed sentence in S6 specs, **needs Alex**) | Only with verified references; otherwise state it as an illustrative parameter. |
| D5 | Sec. IV with capacity first? | Yes. |
| D6 | Non-TCL correction implemented or kept as future work? | Future work. |
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
- **D4: saved, not inserted.** Alex: it may fit better in the numerical results. Candidate place: IV-F, next to the illustrative 4 h window of the flex-season figure. Sentence to adapt there, with `Hon13` (Hong, Kelly, Thomson & Richardson 2013, *Proc. IMechE Part A* 227(1):30–42, doi:10.1177/0957650912454830, verified): "A study of UK dwellings places this window at 1–2 h for the existing stock and up to 6 h with improved insulation and thermal buffering \cite{Hon13}, which brackets the 4 h used here." The bib entry is to be added when it goes in.
- **Overview figure (former Fig. 4, method pipeline):** Alex sees it as a summary of the whole paper, so it moves to the end of Sec. I, after the roadmap. Each box names the section that defines it. Symbols and equation numbers are dropped from the boxes, since they are not defined yet in Sec. I. The caption is shortened. The back-reference sentence at the end of Sec. III is removed.
- Done: the overview figure is now Fig. 1, at the end of Sec. I after the roadmap ("Fig. 1 maps each step of the method to the section that defines it"). The boxes carry unlinked section labels in grey (II-A, II-B, II-D, III-A, III-B, III-C), the arrow label "only m" becomes "SF sensitivity", and the box symbols and equation numbers are gone. Caption: "Overview of the method, with the section that defines each step. Sections IV and V evaluate the three outputs." All other figures renumber by one.
- R22 (Fig. 1 unclear at the start of Sec. II) stays closed: the figure now uses words only and sits before Sec. II, with every box pointing to where it is defined.
