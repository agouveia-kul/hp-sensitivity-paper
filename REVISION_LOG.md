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
| R01 | 1 | "On 200 German LV feeders … over twenty per cent" | Too anecdotal | | | open (S1 ¶1) |
| R02 | 1 | same | Use country/region figures | | | open (S1 ¶1) |
| R03 | 1 | the word "were" in "networks that were not sized for it" | "maybe" | | | needs Alex (rec.: soften to "that may not have been sized for it") |
| R04 | 1 | "rooftop solar" | Injection peaks go the other way | | | open (S1 ¶2) |
| R05 | 1 | "network operators must know how much thermostatic load…" | Why is it interesting? | | | open (S1 ¶3) |
| R06 | 1 | "It meters aggregated net load" | "Often only aggregated net load is measured (smart meter level? at the substation?)" | | | open (S1 ¶4) |
| R07 | 1 | same | "It" = the DSO | | | open (S1 ¶4) |
| R08 | 1 | "It" | Too many "it"s | | | open (S1, S2 "it" pass) |
| R09 | 1 | "remain largely synthetic at the substation" | What does this mean? | | | open (S1 ¶5) |
| R10 | 1 | title, "from Net Load and Temperature" | Explain setup and pilot | | | open (S1 ¶11, abstract) |
| R11 | 2 | "service-transformer" | What is it? | | | open (S1 ¶8) |
| R12 | 2 | "The simultaneity of an aggregated TCL population…" | Use this at the beginning | | | open (S1 ¶3) |
| R13 | 2 | "submetering the target feeder" | Say "at household level" | | | open (S1 ¶10) |
| R14 | 2 | contribution 1, SF slope sentence | Not understandable yet | | | open (S1 ¶12) |
| R15 | 2 | same | Maybe not needed | | | open (S1 ¶12) |
| R16 | 2 | contribution 2 | A full conclusion; keep short | | | open (S1 ¶12) |
| R17 | 3 | "same two fits" | Which two fits? | | | open (S1 ¶12, S2) |
| R18 | 3 | contribution 3, flexibility details | Too much here | | | open (S1 ¶12) |
| R19 | 3 | Sec. II privacy sentences | Why not in the introduction? | | | open (S1 ¶4, S2) |
| R20 | 3 | "it" | What is it? | | | open (S2) |
| R21 | 3 | "problem" | Wording | | | open (S2) |
| R22 | 3 | Sec. II opening paragraph | Hard to follow; data needs; Fig. 1 | | | open (S2) |
| R23 | 3 | "treats R2 as out of scope" | Cooling analysis would be analogous | | | open (S3, D1) |
| R24 | 4 | "the hat marks a fitted function" | Rephrase | | | open (S5) |
| R25 | 4 | "P_base … discarded" | Needed? | | | open (S5, delete) |
| R26 | 4 | strike-out of ", i.e., a larger share of consumers with a TCL" (l.218) | (strike-out, no text) | | | open (L, delete) |
| R27 | 4 | "Table II spans this range…" | Introduce Table II | | | open (L) |
| R28 | 4 | "SF(T)" | How does this match planning? | | | open (S5) |
| R29 | 4 | "In this work," (99.9th pct) | Why not max? Say values unavailable | | | open (S5) |
| R30 | 4 | "isolated metering spikes" | Data cleaning; just say max | | | open (S5) |
| R31 | 4 | "which takes the peak interval" | What is the peak interval? | | | open (S5) |
| R32 | 4 | Kloten 1.28× / 1.75× | Data not yet introduced | | | open (S5, move) |
| R33 | 4 | "Using the total TCL installed capacity … underestimation" | Too obvious | | | open (S5, delete) |
| R34 | 4 | eqs (5)–(7) | Heating only, cooling analogous | | | open (S3, D1) |
| R35 | 4 | "(7)" | "which data do you need to do this fit? This is not so straightforward to do, no? Explain this a bit better." (one sentence may be too little; see S2) | | | open (L) |
| R36 | 5 | "R1, R3, or" | What are these? | | | open (S4, D2) |
| R37 | 5 | same | Refer to the figure | | | open (S4) |
| R38 | 5 | "so the transfer of Section II-D" | Weird sentence | | | open (L) |
| R39 | 5 | II-D first sentence, "submetered TCL data" (l.308) | "aha, why only here?" | | | open (S1 ¶11) |
| R40 | 5 | II-D pilot/target definitions | Already for Table II? What is calibration? | | | open (S2) |
| R41 | 5 | "Section IV-C tests this hypothesis…" | Paper builds on an untested hypothesis | | | open (S2, S7) |
| R42 | 5 | "R²_h" | What is this? | | | open (S4) |
| R43 | 6 | P_net(t) | "T?" | | | open (S4) |
| R44 | 6 | "R2 bounds the estimate" | Use "dead band" | | | open (S4) |
| R45 | 6 | "The temperature cancels, so" | Write "Note that…" | | | open (L) |
| R46 | 6 | "The two regimes are estimated separately." | Heating only | | | open (S3, D1) |
| R47 | 6 | III-C cancellation passage | Unclear; how is Δt_Th set? | | | open (S6, D4) |
| R48 | 6 | "Over a year, this paper counts…" | Rephrase or move; why useful? | | | open (S6) |
| R49 | 7 | IV-A split procedure | Why? What is fitted and estimated? | | | open (S7) |
| R50 | 7 | Fig. 5 number recital | Just the conclusion | | | open (S7) |
| R51 | 8 | "Installed Capacity Estimation" | Why not first? | | | open (S7, D5) |
| R52 | 8 | "1260 aggregates at a WAPE of 19%" | Different capacity per aggregate? | | | open (S7) |
| R53 | 9 | "Transferring the full SF curve…" | Not understood | | | open (S7) |
| R54 | 9 | "About three points" | Three points? | | | open (L) |
| R55 | 11 | VI-D "…but not the net-load numerator." | What was done to counter limits? | | | open (S8) |
| R56 | 12 | "s" over "ted" of "This paper presented" (Conclusion, l.578) | "s" | | | needs Alex (rec.: "This paper presents") |
| R57 | 12 | strike-out of "Most of this error stems from the net-load slope, … rather than from the transfer of the SF slope." (l.578) | (strike-out, no text) | | | open (S8, delete) |
| S2-xx | — | Supervisor 2 marks | — | | | needs Alex (file missing) |

## Decisions for Alex

| ID | Question | Recommendation |
|---|---|---|
| D1 | Present the method heating-only, with cooling by symmetry? | Yes. Every quantitative result is heating-only, and the cooling fits are descriptive (l.570). |
| D2 | Regime names: words or new symbols? | Words: heating regime, dead band, cooling regime. |
| D3 | Run the capacity-definition robustness check (max, HEAPO nameplate)? | Run it. Numbers go in only after review. |
| D4 | Δt_Th literature range | Only with verified references; otherwise state it as an illustrative parameter. |
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
| 1 | Heating electrification is growing fast. | Electrifying heating and cooling is a decarbonisation lever; TCLs = HPs, resistive heaters, air conditioners; HPs lead (`Iea22`). European scale: EHPA 2026 market report (29.3 M HPs in 21 countries; 2.88 M sold in 2025, +13%), **to verify against the primary EHPA source in S1**. `Tre26` 200 German feeders: at most one clause (R01, R02). |
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
