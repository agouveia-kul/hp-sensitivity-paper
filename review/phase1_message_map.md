# Phase 1 — Message map

Manuscript: `paper/hp_sensitivity_overleaf.tex` (the version on `main`, a1e7d37). Line numbers refer to that file.

---

## 1. Core message (3 sentences)

> A DSO can estimate the installed heat-pump capacity behind a feeder from two series it already holds, the feeder's net load and the outdoor temperature, plus one number calibrated once on a small pilot of households with submetered heating. That number is how fast the share of installed capacity in use grows as the temperature falls, and dividing the feeder's net-load temperature slope by it gives the capacity. The capacity is recovered at a WAPE of 19% on 1260 semi-synthetic Swiss aggregates and within 10% on three real aggregates outside the pilot, and the calibration transfers when the pilot matches the target in climate zone, HP technology and housing stock.

Secondary message, kept out of the three sentences: the same net-load fit gives the temperature-driven HP energy with no pilot (WAPE 9%), and both fits give a flexibility potential (WAPE 10% against its submetered reference).

### Corrections to the draft message, checked against the body

| Draft wording | Body says | Correction |
|---|---|---|
| "1260 semi-synthetic Swiss **feeders**" | Sums of measured households, no network (l.413) | Say "aggregates". |
| "within 10% on three real **feeders**" | Summed household meters, not a transformer or feeder-head measurement, no losses (l.529) | Say "real aggregates". Also, all three have **100% HP penetration** (l.529). The 10% must not be read as general, because the error grows as the HP share falls (l.479, l.492). |
| "One extra number" | Correct, $m_h$ only (l.308, l.458). The pilot also needs its installed capacity, taken as the 99.9th percentile of each HP's 15-min draw (l.251). | Keep. In Sec. II, state that the pilot needs heating load **and** capacity (R35). |
| "heat-pump (TCL) capacity" | The method is posed for TCLs, but every quantitative result is HP heating. Cooling is descriptive only (l.570). | In the core message say "heat-pump", and in the title and abstract keep "TCL". See D1. |
| "transfers when the pilot matches the target in climate zone, HP technology and housing stock" | Within 12% inside one climate zone or class; 13–14% between HP technologies; 1.65–1.7× between climate zones and between housing types (l.544–546) | Keep the conclusion's wording (l.578). The technology mismatch is modest, while the zone and housing mismatches are large. |
| "from data it already holds" | The estimate uses net load and temperature only. The consumer count is needed only for the future non-TCL correction (l.582). | Keep. Do not list the consumer count as an input of the method. |

---

## 2. Paragraph map

Verdicts: **yes** means the paragraph serves the core message, **weakly** means it serves it partly, and **no** means it does not. Problem codes: **0P** no point · **2P** two or more points · **EARLY** the point uses terms not yet defined · **FWD** forward reference to an undefined concept · **RECITAL** a list of numbers in running text · **IT** an unclear referent · **LONG** a sentence over 40 words.

### Abstract (one paragraph; mapped per sentence)

| # | Current opening | Point | Serves | Problem |
|---|---|---|---|---|
| A1 | "The electrification of heating and cooling is connecting more TCLs…" | TCLs are spreading in LV networks | yes | — |
| A2 | "However, DSOs rarely know the installed capacity…" | DSO lacks capacity | yes | Does not say why capacity matters |
| A3 | "This paper estimates that capacity from the aggregated net load and ambient temperature…" | Inputs | yes | Pilot missing from the setup (R10) |
| A4 | "The installed capacity follows as the ratio of two temperature sensitivities…" | Method | yes | EARLY: "piecewise-linear net-load fit", "SF fit", "submetered pilot" all undefined; a 38-word noun cluster |
| A5 | "Only the SF sensitivity is transferred; each aggregate keeps the threshold…" | Transfer detail | weakly | EARLY: "transferred" and "threshold temperature" undefined. A method detail placed in the abstract |
| A6 | "On 1260 semi-synthetic aggregates…WAPE of 19%" | Main accuracy | yes | "aggregate" undefined in the abstract |
| A7 | "On three real Swiss and German aggregates…within 10%…26%" | Out-of-sample accuracy | yes | "full SF curve" undefined |
| A8 | "The temperature-driven HP energy needs no pilot…9%, and a flexibility…10%" | Secondary results | yes | Second clause has no verb |
| A9–A10 | "Across populations from five countries…12%…13–14%…1.7-fold" | When the transfer holds | yes | Close to a RECITAL. Acceptable in an abstract |

### Sec. I — Introduction

| ¶ | Line | Current opening | Point | Serves | Problem / comment IDs |
|---|---|---|---|---|---|
| I-1 | 77 | "The electrification of residential heating and cooling is a central lever…" | HP uptake grows | yes | The 200-German-feeders figure is anecdotal (R01, R02) |
| I-2 | 79 | "This uptake supports decarbonisation, yet it loads LV networks…" | (a) peaks in cold weather; (b) operators must know the load | yes | 2P. Rooftop solar placed in the wrong direction (R04). "must know how much thermostatic load" is vague (R05). R03 "maybe" |
| I-3 | 81 | "A distribution system operator (DSO) rarely holds that information." | DSO lacks capacity | yes | IT ×2 (R06–R08). Metering location unspecified (R06). It comes **before** the paragraph explaining why capacity is needed, so the lack is stated before the need |
| I-4 | 83 | "Installed capacity, rather than the coincident peak, is the quantity sought here…" | Why capacity | yes | Order (should precede I-3). EARLY: "coincident peak" undefined; SF defined in passing (R05, R12) |
| I-5 | 87 | "Five lines of research approach this gap…" (NILM) | NILM stops short of capacity | yes | "this gap" refers to a gap not yet stated. "largely synthetic at the substation" (R09) |
| I-6 | 89 | "Change-point and degree-day models fit load as a piecewise-linear function…" | They see the signal but stop at coincident response | yes | — |
| I-7 | 91 | "For PV and other DERs, by contrast, installed-capacity estimation is well developed." | PV analogue exists | weakly | "service-transformer" (R11) |
| I-8 | 93 | "The simultaneity of an aggregated TCL population…inform network planning" | (a) SF matters for planning; (b) prior SF work is forward-only and submetered | yes | 2P. Point (a) belongs in the motivation (R12). Ends on a different subject ("Planners") |
| I-9 | 95 | "A separate body of work models aggregated TCL populations for control." | Control models assume a known population | weakly | One sentence is 44 words |
| I-10 | 97 | "To the best of the authors' knowledge, no prior method estimates…" | Gap | yes | "the target feeder", i.e. at household level? (R13). The idea is never stated in plain words (R10) |
| C1 | 99 | "Estimation of the installed TCL capacity behind a feeder…" | Contribution 1 | yes | "slope of the SF", "balance point": EARLY (R14, R15). 4 sentences |
| C2 | 100 | "Evidence on when the SF slope transfers…" | Contribution 2 | yes | RECITAL of results; reads as a conclusion (R16) |
| C3 | 101 | "Estimation of the temperature-driven TCL energy and of a flexibility potential from the same two fits." | Contribution 3 | yes | "same two fits" have not been named (R17). The flexibility derivation is too detailed for this place (R18) |
| I-11 | 104 | "The rest of the paper is structured as follows." | Roadmap | yes | Update after D5 |

### Sec. II — Problem and Approach

| ¶ | Line | Current opening | Point | Serves | Problem / comment IDs |
|---|---|---|---|---|---|
| II-0a | 111 | "Privacy concerns and limits on metering and data exchange leave DSOs without full observability…" | Four points: privacy, DER registers, high-SF DERs, data used | weakly | 2P+. The privacy and register sentences belong in Sec. I (R19). The data requirement is unclear (R22). "it" (R20) |
| II-0b | 113 | "A metered point of an LV network…aggregates the load…" | Defines "aggregate" | yes | Late: "aggregate" was already used in the abstract and Sec. I |
| II-0c | 115 | "The net load is the sum of a TCL and a non-TCL component," | Eq. (1); non-TCL response neglected | yes | — |
| II-0d | 122 | "The problem is to recover the aggregated TCL load…" | Three outputs; Fig. 1 | weakly | "problem" (R21). Fig. 1 shows $s_h$, $m_h$ and eq. numbers before they are defined (R22) |
| II-0e | 155 | "Two fits describe the TCL population's response…" | Names the two fits | yes | First mention of "submetered" in Sec. II (R39). This should be the paragraph that names the fits |
| II-A1 | 161 | "When an aggregate's net load is averaged over each day…" | Eq. (2), OLS | yes | One sentence of 53 words (l.168) |
| II-A2 | 172 | "Note that (2) needs only the net load…" | Data need + Fig. 2 + regimes | 2P | Regime names R1–R3 clash with $R^2$ (R36, R37). "R2 out of scope" (R23) |
| II-A3 | 181 | "For an aggregate $i$ with its own fitted parameters," | Eq. (3) | yes | Hat sentence (R24). $P_\mathrm{base}$ discarded (R25) |
| II-A4 | 213 | "The fitted parameters carry a physical interpretation." | Thresholds are behavioural | weakly | Repeats the dead band of II-A2 |
| II-A5 | 216 | "The sensitivities $s_h$ and $s_c$ … measure how much heating or cooling load…" | $s_h$ scales with capacity | **yes, a key premise** | Struck clause (R26). FWD to IV-B. This premise is buried in the middle of II-A |
| II-A6 | 220 | "The flat centre $P_\mathrm{base}$ is the load that remains…" | Base load out of scope | no | Repeats; candidate for deletion |
| II-A7 | 229 | "The balance between $s_h$ and $s_c$ reflects the local climate." | Climate sets the balance of the two arms | weakly | Forward reference to Table II, which is not introduced (R27) |
| II-B1 | 242 | "The SF, also called the coincidence factor, is the ratio…" | SF definition and planning role | yes | — |
| II-B2 | 246 | "Mathematically, the SF is the fraction of the aggregate's installed capacity…" | Eq. (4); capacity proxy | yes | 99.9th percentile not justified (R29); "metering spikes" (R30) |
| II-B3 | 253 | "Since $P_\mathrm{TCL}(T)$ is a daily mean, the SF of this paper is a daily-mean SF." | Daily-mean SF vs planning SF | weakly | EARLY: Kloten numbers (R32), "peak interval" (R31), the link to planning is missing (R28) |
| II-B4 | 257 | "An aggregate may have a mix of TCLs…" | Per-regime capacity | weakly | "too obvious" sentence (R33); heating only (R34) |
| II-B5 | 272 | "with $h$ denoting heating and $c$ cooling…The SF fit takes the same form" | Eq. (7); borrowed thresholds | yes | The data that eq. (7) needs is not stated (R35) |
| II-B6 | 292 | "The observed SF stays well below 1." | Unused share leads to flexibility | weakly | FWD to III-C |
| II-C1 | 299 | "Table II reports both fits…on aggregates from four countries…" | Fit quality across climates | weakly | RECITAL. "R1, R3" (R36, R37). $R^2_h$ undefined (R42) |
| II-C2 | 301 | "The threshold temperatures follow the local climate." | Thresholds follow climate; **$m$ removes size dependence** | yes | The key point arrives in the last sentence |
| II-C3 | 303 | "The SF sensitivities $m_h$ and $m_c$ group partly by Köppen class." | $m_h$ transfers only within one climate class and technology | yes | RECITAL (11 values). Point arrives in the second-to-last sentence. "so the transfer of Section II-D" (R38) |
| II-D1 | 308 | "The SF is computed from submetered TCL data, which a DSO rarely holds…" | The transfer; defines pilot, target, split | yes | Definitions arrive after Table II has been read (R40). "calibrated" unexplained |
| II-D2 | 310 | "The transfer rests on one hypothesis…" | Single assumption | yes | Untested at this point and given no early evidence (R41) |

### Sec. III — Aggregated TCL Quantification

| ¶ | Line | Current opening | Point | Serves | Problem / comment IDs |
|---|---|---|---|---|---|
| III-0 | 324 | "The two fits, (3) and (7), are complementary." | What each fit can and cannot do | yes | Duplicates II-0d and the Fig. 1 caption |
| III-A1 | 329 | "The energy the TCL population draws follows from integrating…" | Eq. (9); also forecasting | yes | — |
| III-A2 | 338 | "R2 bounds the estimate." | Misses hot water | yes | "R2" → dead band (R44) |
| III-B1 | 343 | "The installed capacity is the sum of the individual peak demands…" | Net load never exposes capacity | yes | — |
| III-B2 | 345 | "Both must describe the same load." | Eq. (10)–(11); temperature cancels | **yes, the core** | Opens with an unclear "Both". R45 "Note that…" |
| III-B3 | 363 | "The two regimes are estimated separately." | Reversible HPs | weakly | R46 heating only |
| III-C1 | 374 | "The flexibility a TCL population offers is the energy it can shift…" | Definition; $\Delta t_{Th}$; eq. (12)–(14) | yes | Opens with the definition, not the use. $\Delta t_{Th}$ undetermined (R47) |
| III-C2 | 390 | "This use case draws on both fits and one external parameter." | Capacity cancels | weakly | Unclear (R47) |
| III-C3 | 392 | "Over a year, this paper counts one such window per day…" | Annual summation | weakly | Move to IV-F (R48) |
| III-C4 | 402 | "The bound is an idealisation, not a dispatchable schedule." | Caveat | yes | — |

**Summary of the map.** The abstract and Sec. I carry the right content, in the wrong order and in undefined terms. The need (I-4) follows the lack (I-3). The planning role of the SF (I-8) sits among the prior work. The method idea is never said in plain words before the contributions, and the contributions use "SF slope" and "balance point" before they are defined. In Sec. II, the opening paragraph mixes four points (II-0a). The two key premises, $s_h \propto$ capacity (II-A5) and "$m$ removes size dependence" (II-C2), are buried mid-paragraph. Pilot and target are defined only after Table II (II-D1). Sec. III is mostly sound; its problems are local (III-B2's opening, III-C).

---

## 3. Supervisor 2's marks

**Not available.** `review/<SUPERVISOR2_FILE>` and `review/TCL_Quantification_rdh.pdf` are not in the repository; nothing named `*rdh*`, `*TCL_Quantification*` or `*supervisor*` was found. The S2-xx rows therefore wait for Alex.

So that the mapping is quick once the marks arrive, the abstract and Sec. I sentences that fail rule 5 *in the agent's own reading* are listed below. These are **not** Supervisor 2's marks.

| Location | Sentence (start) | Rule-5 category |
|---|---|---|
| A4 | "The installed capacity follows as the ratio of two temperature sensitivities…" | Term before definition; noun chain ("piecewise-linear net-load fit") |
| A5 | "Only the SF sensitivity is transferred; each aggregate keeps…" | Terms before definition; two ideas in one sentence |
| A8 | "…and a flexibility potential derived from both fits at a WAPE of 10%…" | Missing verb |
| I-2, last | "To plan and operate these networks, network operators must know how much thermostatic load sits behind each metering point." | Point arrives early; vague object |
| I-3, 2nd | "It meters aggregated net load and can obtain weather data." | Unclear "it"; location missing |
| I-4, 3rd | "It bounds the peak the population can draw when its devices are synchronised, for instance after a tariff blocking period, in which the utility interrupts the HP supply, or during the activation of flexibility." | 35 words, three nested clauses; "it" refers two sentences back |
| I-5, 1st | "Five lines of research approach this gap…" | Refers forward to a gap not yet stated |
| I-8, 1st | "The simultaneity of an aggregated TCL population, and the coincident peak it produces, inform network planning…" | Abstract subject; point belongs earlier |
| I-9, 4th | "The state of such a population can be estimated from its aggregate power…" + the 44-word "These methods, however, assume…" | Length; two ideas |
| I-10, 2nd | "The change-point models observe the right signal but lack the step from coincident demand to installed capacity…" | Metaphor ("the step") before the idea is stated |
| C1, 3rd | "This paper adds the step from that coincident demand to installed capacity, by dividing it by the slope of the SF calibrated on a small set of submetered households." | "it" ambiguous; "slope of the SF" undefined |
| C3, 4th | "It equals the temperature-driven load times the unused share of capacity, one minus the SF, and is compared with…" | Two ideas; too detailed (R18) |

---

## 4. Proposed Sec. I structure — see `REVISION_LOG.md` › Content specs › Sec. I

## 5. Proposed abstract — see `REVISION_LOG.md` › Content specs › Abstract
