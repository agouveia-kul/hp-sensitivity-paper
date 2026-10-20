# Response to supervisors – draft for Alex to edit

Manuscript: "Estimating the Installed Capacity of Aggregated Thermostatically Controlled Loads from Net Load and Temperature". Section, figure and table numbers refer to the revised version. The marked-up changes are in `review/hp_sensitivity_diff_vs_reviewed.pdf`.

## Overview

Thank you both for the careful reading. The main changes are structural:
- The abstract and introduction now state the setup before the results. A DSO holds the net load and temperature of a feeder. The SF sensitivity, how fast the share of installed capacity in use grows as the temperature falls, is calibrated once on a small submetered pilot. Their ratio gives the installed capacity.
- The SF sensitivity is defined before it is named, and the paper no longer refers to it as "the SF slope".
- An overview figure (Fig. 1) at the end of Sec. I maps each step of the method to its section. Table III at the end of Sec. III lists which fitted parameters each estimate uses.
- Sec. II-D now presents the transfer of the SF sensitivity as a hypothesis that Sections IV and V test.
- Sec. IV shows the installed capacity first. It opens with the purpose of the experiment and a schematic of one split (Fig. 5).
- The outputs appear in the same order throughout: installed capacity, energy, flexibility.

No result has changed.

## Reinhilde D'hulst

- **R01–R02.** Agreed. The introduction now opens with European figures (EHPA: about 2.9 million HPs sold in 2025, 29.3 million installed). The 200-feeder figure remains as one supporting sentence.
- **R03.** Softened to "loads LV networks that may not have been sized for this load".
- **R04.** Rooftop solar is removed from the sentence on cold-weather peaks.
- **R05, R12.** A new paragraph gives three reasons a DSO needs the installed capacity: planning scenarios, the synchronised peak and the design peak. The planning role of the SF moved there from the prior-work section.
- **R06–R08.** The paragraph now says where the DSO meters (substation or feeder head; household smart meters where rolled out, with restricted access) and names the DSO instead of "it". I also went through the abstract and Sec. I–II for unclear "it"s.
- **R09.** Reworded: these methods "have been validated mostly on synthetic substation aggregates rather than on measured substation data".
- **R10.** Agreed that the setup needed spelling out. A new paragraph in Sec. I states it in plain words, and the abstract does the same.
- **R11.** The transformer-rating example is removed, together with its row in Table I.
- **R13.** Now "without submetering the households of the target feeder".
- **R14–R18.** The contributions are now three short items with no results and no symbols. "Same two fits" is gone, and the fits are named by the data they need in Sec. II.
- **R19.** The privacy and DER-register sentences moved to the introduction.
- **R20–R22.** The Sec. II opening now states only the three quantities sought and the data each needs. The overview figure moved to Sec. I and uses words only.
- **R23.** Yes, the method applies to cooling alike, and Sec. II-A now says so. The evaluation covers heating only, because no available dataset allows a cooling transfer test. Cooling is listed as future work.
- **R24, R25.** Eq. (3) is now introduced as "From (2), the temperature-driven component … is". The sentence about $P_\text{base}$ being discarded is removed.
- **R26.** Struck clause removed.
- **R27.** Sec. II-C introduces Table II.
- **R28.** A new paragraph links the SF fit to planning. The design SF at a design temperature follows from the fit, and the design peak is the installed capacity times that SF, with a caveat on the daily-mean SF.
- **R29, R30.** The text now says nameplate ratings are unavailable for most households, so each HP's capacity is the peak of its submetered 15-min draw. The percentile detail is removed.
- **R31, R32.** "Peak interval" is replaced by "the 15-min interval of highest aggregate demand". The Kloten peak-to-mean ratios moved to Sec. IV-C, after the data are introduced.
- **R33.** Kept. We think the sentence explains why each regime needs its own capacity.
- **R34, R46.** We kept the problem and the fits generic for heating and cooling, since the method covers both. Only the results are heating-only.
- **R35.** Sec. II-B now states the inputs of the SF fit (submetered TCL load, installed capacity per regime, temperature, thresholds from the net-load fit) and that, in practice, only a pilot provides them.
- **R36, R37, R44.** R1/R2/R3 are now "heating regime", "dead band" and "cooling regime" throughout, including the figures. The text refers back to Fig. 2.
- **R38.** Rewritten: "so the SF sensitivity is expected to transfer only within a climate class and TCL technology (Section II-D)".
- **R39, R40.** Submetering and the pilot are introduced in Sec. I. Sec. II-D explains calibration, pilot, target and split in plain words, and notes that Table II involves no transfer.
- **R41.** Agreed. Sec. II-D now states the transfer as a hypothesis the paper tests, with pointers to the three tests.
- **R42.** $R^2_h$ and $R^2_c$ are defined at first use.
- **R43.** $t$ (time) and $T$ (daily mean temperature) are now defined and kept apart.
- **R45.** "Note that the temperature cancels…".
- **R47, R48.** Sec. III-C now opens with why a DSO or aggregator needs the flexibility. It treats the window as an exogenous building-stock parameter, with a reference for how much it varies. The cancellation is explained in two plain sentences, and the annual counting moved to Sec. IV-F.
- **R49, R52.** Sec. IV-A now opens with the purpose of the experiment. Each aggregate plays a feeder with its own true capacity. Fig. 5 shows one split.
- **R50.** The fit-quality paragraph gives the trend and the two end values only.
- **R51.** Sec. IV now starts with the installed capacity.
- **R53.** The four estimators are listed before Table IV, labelled (i)–(iv) as in the table.
- **R54.** "About three percentage points".
- **R55.** The limitations subsection now leads each limit with what the evaluation does to bound it. Cooling moved to future work.
- **R56, R57.** "This paper presents"; the struck sentence is removed.

## Supervisor 2

- **General comment** ("the content should come first, the sentences second"). The revision followed this. We first fixed a three-sentence core message and a paragraph-by-paragraph content map of the abstract and Sec. I–III, which are in the revision log. Every rewritten paragraph opens with its point, defines terms before using them and keeps to one idea per sentence. The abstract and Sec. I use no symbols.
- **Marked sentences (S2-xx).** *Pending.* The marked sentences have not reached us yet. The abstract and Sec. I will be rechecked against them once they arrive.
