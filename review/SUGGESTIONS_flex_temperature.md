# Suggestions — flexibility against temperature (draft mode, no edits made)

1. **Finding:** the annual flexibility ratio of 1.04 averages two opposite errors. It is +17% on the coldest days and −8 to −13% at 10–14 °C, and the net-load fit causes both, not the pilot.
2. **Finding:** the upward headroom carries the capacity error (+16–23%), while the downward headroom needs no pilot. The two never cross on an observed day.
3. **Window:** with the window referenced to an assumed indoor temperature T_in, F(T) is a plateau whose "peak" moves with T_in. Referenced to the threshold T_h instead (Step 1b), E_flex follows s_h(1 − SF) exactly, and per event it is 0.79 (estimate) and 0.73 (actual) of its 5 °C value on the coldest days. **Negative:** aggregating 5 to 25 HPs raises firm flexibility (P10/median) only from 0.85 to 0.87.
4. **Does the idea add to the paper?** Yes, in a narrow form. One temperature-axis figure can replace Figs. 10 and 11, showing up/down headroom and the temperature profile of the error. The window and firmness results fit in one sentence or a short paragraph each.
5. **Overall recommendation:** accept F1 and F2; modify F3 (a two-sentence remark on the T_h-referenced window) and F4; F5 not assessed. Together with F6, the paper loses one figure, and the word count changes by about +30 (within counting error), or about 0 with the lean F3.

Evidence for every number: `FLEX_LOG.md`, Steps 0–2 (branch `explore/flex-temperature`). Draft figures: `figures/flex_temperature/fig_flex_temperature.pdf` (Step 1) and `fig_firm_flex.pdf` (Step 2). Word counts are of the current `paper/content/body.tex`, prose only, ±10%.

Mark each suggestion in its `Alex:` line. Part C starts only for items marked accept or modify.

---

### F1 — Upward and downward headroom against T in Sec. III-C
- What: split the flexibility headroom into its downward part (curtailable load) and upward part (unused capacity), and state which one needs the pilot.
- Where: III-C, the paragraph after eq. (13), replacing its last sentence, "The instantaneous unused capacity $(1-\hat{\mathrm{SF}}(T))\,\hat{P}^{\max}$ is the special case of the on phase drawn to full power". Plus one sentence in IV-F, inside the new figure's paragraph (F2).
- Content:
  - The downward headroom is $\hat{P}_{\mathrm{TCL}}(T) = \hat{\mathrm{SF}}(T)\,\hat{P}^{\max}$, the fitted TCL load of (2). It needs the net-load fit only, so no pilot.
  - The upward headroom is $(1-\hat{\mathrm{SF}}(T))\,\hat{P}^{\max}$. It needs $\hat{P}^{\max}$ and inherits the capacity error.
  - The two are equal at SF = 0.5. On Kloten that point lies at −9 to −10 °C, colder than any observed day (coldest daily mean −8.2 °C), so the upward headroom exceeds the downward one on every heating day.
  - In IV-F: the estimated upward headroom is 1.16–1.23 times the actual in every temperature bin, and the downward headroom is within 0.99–1.02 of it from −2 to 7 °C.
  - No new symbol. $\hat{P}_{\mathrm{TCL}}$ already names the downward headroom, and "unused capacity" already names the upward one. The arrows ↑/↓ of Fig. 4 can label them in the new figure.
  - Sample: "The downward headroom equals the fitted TCL load and needs no pilot, whereas the upward headroom $(1-\hat{\mathrm{SF}})\,\hat{P}^{\max}$ inherits the error of the capacity estimate."
- Evidence: derived for the III-C part. Step 1 for the numbers (bin table, P_up est./act. column; E1.3: SF < 0.5 on 100% of aggregate-days).
- Length effect: III-C +20 words (two sentences replace one); IV-F +30 words. No figure.
- Reviewer risk: "This is a trivial restatement of SF and 1 − SF." Answer: it identifies which half of the flexibility depends on the transferred SF. That matters to a DSO, since only the upward half carries the pilot's error.
- Recommendation: accept — it is short, derived and backed by a measured asymmetry.
- Alex: [ accept | modify | reject ]

### F2 — One flexibility–temperature figure replacing Figs. 10 and 11
- What: replace Figs. 10 and 11 with one two-panel figure on the temperature axis: (a) upward and downward headroom, (b) flexible energy per hour of window. Both panels are per kW of true installed capacity, estimate against actual.
- Where: IV-F. It replaces Fig. 10 (`fig:flex-ratio`), Fig. 11 (`fig:flex-season`), both captions and the Fig. 11 paragraph. The annual totals become one sentence each.
- Content:
  - Figure: panels (a) and (b) of `figures/flex_temperature/fig_flex_temperature.pdf`, without panel (c), the W2 window (see F3). It shows N = 50, N_hp = 25, median and IQR across the 60 aggregates, with the dead-band floor of the actual dotted in (b).
  - Text, in order:
    - Fig. 10 shrinks to its sentence, which stays as is: "median of 1.04 and an interquartile range of [0.97, 1.17], at a WAPE of 10%".
    - The temperature profile of the ratio: +17% in the coldest bin (−8 to −2 °C, 7 days), about +8% from −2 to 7 °C, 0.98–1.00 at 7–10 °C, −8 to −13% at 10–14 °C, and an underestimate within 2 °C of T_h.
    - The cause: the energy factor (net-load fit) carries the whole profile. The unused-capacity factor (1.02–1.06) and the hourly factor (1.02–1.04) stay flat across bins. This extends, without changing, the existing sentence "The flexibility estimate therefore inherits its accuracy mainly from the net-load fit".
    - A hedged mechanism: the measured HP load still runs at 0.05–0.06 kW per kW installed at 14–16 °C, where the linear arm reaches zero. The bins from 13 °C to T_h hold only 6% of the annual flexible energy, so the annual ratio is set by the colder bins.
    - The F1 sentence on upward and downward headroom.
    - Fig. 11 shrinks to one sentence: the dead-band floor (median 9% of annual actual; about 19 kWh/day on the example split at Δt = 4 h). The 5.2 against 4.7 MWh totals can go; the 1.04 ratio already carries that comparison.
  - The caption carries the validation caveat: the actual uses the same SF(1 − SF)·P^max formula with each aggregate's hourly submetered SF and true capacity, so the agreement checks the inputs, not observed flexibility.
  - Sample: "The estimate overstates the flexible energy by 17% on the coldest days and understates it by 8–13% between 10 and 14 °C, so the annual ratio of 1.04 averages two opposite errors."
- Evidence: Step 1 (bin table; headline 1; weight of the bins; E1.4 not met). Step 0 for the retained annual numbers.
- What is lost, checked against the Step 1 list:
  - (i) The full histogram over all 1260 aggregates and all (N, N_hp). The IQR sentence and the new figure's bands for N = 50 replace it. Recommend stating in the text that N = 10 and 30 show the same profile, with wider bands.
  - (ii) The calendar view, with a third of the days above T_h, mostly from late spring to early autumn. One clause keeps it.
  - (iii) Day-to-day tracking of one out-of-sample aggregate. It is lost; the bands show the spread instead.
  - (iv) The absolute kWh scale. The per-kW axis replaces it; the 144 kW, 4 h example keeps one number in the floor sentence.
  - Nothing in the abstract, conclusion or real-aggregates section cites Fig. 10 or 11 directly (checked with grep).
- Length effect: −1 figure. Text −316 words (Fig. 11 paragraph 169, the two captions 112, and the two dead-band sentences of the third IV-F paragraph, about 35). New caption about +65 and new paragraph about +100. Net about −150 words. If F3 is accepted, also cut the two sentences splitting the unused-capacity factor ("About three percentage points…", "About four more…", about 35 words), giving about −185.
- Reviewer risk: "The temperature profile shows the estimate is biased; the annual 1.04 looked better." Answer: the profile is a feature of the net-load fit, shared with the energy estimate, and it is stated rather than hidden. A DSO valuing cold-day flexibility needs exactly this. Second risk: "Why only N = 50?" Answer: the other N give the same profile (Step 1), and one sentence says so.
- Recommendation: accept — the paper loses a figure and gains the error profile and the up/down split, while the annual numbers survive as text. (Modify option: if you want to keep the full 1260-aggregate distribution, keep Fig. 10 and replace only Fig. 11; net then about −60 words and no figure saved.)
- Alex: [ accept | modify | reject ]

### F3 — Temperature-dependent window, referenced to the threshold T_h *(revised after Step 1b)*
- What: in III-C, add a short derived remark. If the window is the time a building coasts on its gains, Δt_Th scales with 1/(T_h − T) and eq. (13) becomes proportional to s_h(1 − SF(T)). Report one cold-day number in IV-F. The 1/(T_in − T) form stays out of the paper.
- Where:
  - III-C, after "Since $E_{\mathrm{flex}}$ is linear in $\Delta t_{Th}$, Section~\ref{sec:res-flex} reports it per hour of window, or as ratios in which the window cancels." Two sentences.
  - IV-F, inside the new figure's paragraph (F2). One sentence.
  - Conclusion, future work: one sentence on calibrating the window, and on participation, against recorded flexibility events. It is shared with F4 and is F6 item 7.
- Content:
  - Derivation, in one sentence. A building with gains needs heat UA(T_h − T), where T_h is its balance temperature. With heating off, it cools at that rate over its heat capacity, so it can stay within a comfort band for a time proportional to 1/(T_h − T).
  - Consequence: E_flex = SF(1 − SF)·P̂^max·Δt_Th ∝ s_h(1 − SF(T)), since m_h·P̂^max = s_h. The shiftable thermal energy per event is the same at every temperature, and only the headroom 1 − SF limits it. Per event, flexibility is then largest on mild heating days and falls by about a fifth from 5 °C to the coldest days. This reverses the constant-window reading, and the data cannot tell the two apart.
  - Near T_h the window grows without bound, so it must be capped at the event length the DSO considers. The cap affects only the last 2–4 °C below T_h (onsets at 12.7, 14.6 and 15.6 °C for caps of 3, 6 and 12 times the 5 °C window), which hold about 6% of the heating-regime flexible energy.
  - Result for IV-F: on the coldest days, the estimated flexibility per event is 0.79 of its value at 5 °C, against 0.73 for the actual, whatever the cap. Estimate/actual per bin is unchanged from the constant window (within 0.01), since both share the window on each day.
  - Not for the paper: near T_h with long caps, the actual rises to 1.8–3.3 times its 5 °C value. That comes from its weather-independent floor (most plausibly hot water) multiplied by a long window, which is the same mechanism as the spike under 1/(T_in − T). A building's coasting time does not govern that load.
  - Why T_h and not T_in. T_h comes from the target's own net-load fit, so no unsourced constant is needed. The coasting constant (heat capacity × comfort band / UA) cancels in any normalised statement. The 1/(T_in − T) form ignores gains and depends on an assumed T_in: its "peak" moved by 1–2.5 °C between 20 and 21 °C (Step 1).
  - Notation: no new symbol is needed. The remark uses Δt_Th, s_h, SF and T_h, and the proportionality avoids naming the coasting constant.
  - Sample: "If the window is the time a building coasts on its internal gains, $\Delta t_{Th}$ scales with $1/(T_h - T)$, and \eqref{eq:flex-energy} becomes proportional to $s_h\,(1-\hat{\mathrm{SF}}(T))$."
- Evidence:
  - Step 1b: closed form matched within 0.2%; cold-day values 0.79 and 0.73 independent of the cap; ratio unchanged within 0.01; E1b.1 and E1b.3–6 met, E1b.2 met at r = 3 and missed at bin resolution for r = 6 and 12.
  - Step 1 for the rejected 1/(T_in − T) form.
  - The single-capacity derivation is first principles. A building-physics source would strengthen it (needs Alex; none cited here).
- Length effect: III-C +45 words, IV-F +30, conclusion +20 (F6 item 7). No figure: `fig_flex_window_th.pdf` stays in the log. Net +95. Compensation: under F2, also cut the two IV-F sentences that split the unused-capacity factor into pilot and daily-resolution parts ("About three percentage points…", "About four more…", about 35 words). The new bin factors replace them.
- Reviewer risk:
  - "This assumes gains persist during the event and a single thermal capacity." Answer: the remark says so, labels it an alternative reading of Δt_Th, and states its main use as the cold-side number. That number does not depend on the cap.
  - "Which window is right?" Answer: the data hold no flexibility events. The paper states both readings and reports E_flex per hour of window, so either can be applied.
- Recommendation: modify (method remark plus one result sentence; replaces the earlier "future work only"). The T_h form needs no unsourced constant and has an exact closed form, so it earns two sentences in III-C. The 1/(T_in − T) form stays out. Lean variant, if the length budget must be strictly met: the III-C remark only (+45), dropping the IV-F sentence.
- Alex: [ accept | modify | reject ]

### F4 — Firm flexibility paragraph in the Discussion, linked to Fig. 9
- What: add a short paragraph to Sec. VI-B (Limitations) quantifying how firm the flexibility potential is from day to day, and how little aggregation changes that.
- Where: VI-B, after the paragraph on the non-TCL response. It gives a number to the III-C sentence "It therefore stands as a potential against temperature and window length, not as a firm reserve", which stays.
- Content:
  - On 9 days in 10, the measured potential at a given temperature stays within 13–15% of its median (P10/median 0.85 at 5 HPs, 0.87 at 25 HPs). With the temperature trend removed, the same holds: 0.84 to 0.87.
  - Aggregation barely helps, unlike fit quality in Fig. 9. Across N = 10–50, the daily net-load R² rises from 0.83 to 0.91, because the non-HP households even out. The HP load's own spread around its temperature line falls far less (R²_SF 0.92 to 0.95), and that spread sets the firmness. Hedge the mechanism: the spread left over is shared by all HPs.
  - The estimate carries the median, not the spread. Its own P10/median (0.91) only reflects temperature within a bin. On 9 days in 10, a DSO could count on 0.81 (N = 10) to 0.87 (N = 50) of the estimated median.
  - The least firm days are shoulder-season days at 11–13 °C (late August to early October, late May). They hold about half the flexibility of March or October days at the same mean temperature, which suggests heating switched off for the season. A daily-mean model cannot see that switch. Hedge it: the dates suggest it, but no heating-mode signal is metered.
  - State plainly that this is not participation in demand response. The datasets hold no flexibility events, so P10/median describes how the potential varies, not how HPs respond to a call. Participation goes to future work (shared sentence with F3).
  - Modify against the prompt: present a single haircut (about 0.81–0.87) measured on one station and one year, not a scaling law with feeder size. The data stop at 25 HPs, and at N = 50 the 3 aggregates per split share all 25.
  - Sample: "On nine days in ten, the measured potential at a given temperature stays within 13–15% of its median, for 5 and 25 HPs alike."
- Evidence: Step 2 (summary table against N; detrended diagnostic D2-i; shoulder days D2-ii; E2.1 met by +0.02; E2.4 not met).
- Length effect: about +55 words. No figure (`fig_firm_flex.pdf` stays in the log, not in the paper).
- Reviewer risk: "This is one station and one year; the haircut cannot be generalised." Answer: the paragraph says so and reports it as a measured bound for Kloten, not a transferable constant. Second risk: "Is this participation?" Answer: no, and the paragraph says so in one sentence.
- Recommendation: modify — keep the haircut and the Fig. 9 contrast, drop any scaling claim, cap at about 55 words.
- Alex: [ accept | modify | reject ]

### F5 — Flexibility at the planning condition
- What: not assessed. Step 2b was not run: `RESULTS_LOG.md` holds no overloaded aggregates and no headroom proxy R yet (the planning experiments stop at their Step 2).
- Where: —
- Content: revisit once the planning use case has overload results.
- Evidence: none.
- Length effect: 0.
- Reviewer risk: —
- Recommendation: reject for this revision — no evidence yet.
- Alex: [ accept | modify | reject ]

### F6 — Knock-on edits
- What: the edits elsewhere that keep the paper consistent with F1–F4, listed and not made. Each applies only if its parent suggestion is accepted.
- Where and content:
  1. **Contribution 3, Sec. I** (`body.tex:33`), if F1 and F2.
     - Before: "…and of a flexibility potential, which also uses the SF sensitivity."
     - After: "…and of a flexibility potential against temperature, whose upward headroom also uses the SF sensitivity."
     - +3 words.
  2. **Abstract** (`abstract.tex`): no change recommended. "a flexibility potential at a WAPE of 10%" stays true under every suggestion. Adding the cold-day error would cost about 10 words in an abstract already near the limit.
  3. **Fig. 1 labels** (`body.tex:49`, node `fl`): no change. "Flexibility" still names the output, and changing it would break the shared box sizes of Figs. 1 and 5.
  4. **Table III** (`tab:params`): no change. The flexibility row still uses $s_h, s_c, T_h, T_c$, $m_h, m_c$ and $\Delta t_{Th}$. The pilot-free downward headroom is the energy row's input, and F1's sentence says so in the text.
  5. **Highlights** (`highlights.tex:6`, `highlights.txt:7`): keep "Temperature-driven energy needs no pilot; flexibility follows from the same fits". If F2 is accepted and you want the error profile there, an alternative is "Flexibility follows from the same fits; its error changes sign with temperature" (79 characters). Recommendation: keep.
  6. **Conclusion, summary paragraph** (`body.tex`, sentence ending "…and a flexibility potential at a WAPE of 10%."), if F2.
     - Before: "…and a flexibility potential at a WAPE of 10%."
     - After: "…and a flexibility potential at a WAPE of 10%, overestimated by up to 17% on the coldest days."
     - +10 words.
  7. **Conclusion, future work** ("Four directions follow for future work."), if F3 or F4.
     - Add one sentence on a temperature-dependent window and on participation, calibrated on recorded flexibility events.
     - Change "Four" to "Five", or merge the sentence into the first direction (more diverse metered HPs).
     - +20 words, counted under F3.
  8. **Nomenclature:** no new entries (F1 adds no symbol).
  9. **Real aggregates, VI-A** (`body.tex:489`): no change. Its "follows the energy ratios" agrees with the energy-factor finding of F2.
  10. **Cross-references:** if F2, the two references (`body.tex:457` to `fig:flex-ratio`, `body.tex:475` to `fig:flex-season`) point to the new label. Grep finds no other reference to either label, and no figure follows them, so no other figure number shifts.
- Evidence: derived, no new result (numbers from F1–F4).
- Length effect: +13 words (items 1 and 6); item 7 counted under F3.
- Reviewer risk: inconsistency between abstract and IV-F if F2 is accepted without item 6. Answer: item 6 aligns the conclusion; the abstract's WAPE stays correct.
- Recommendation: accept the items that follow from the accepted suggestions; keep the abstract, Fig. 1, Table III and highlights unchanged.
- Alex: [ accept | modify | reject ]

---

## Total length effect if F1–F4 (and the F6 items they trigger) are all accepted

| Suggestion | Words | Figures |
|---|---|---|
| F1 | +50 | 0 |
| F2 (with the F3 compensation cut) | −185 | −1 (two removed, one added) |
| F3 (III-C remark, IV-F sentence, future-work sentence) | +95 | 0 |
| F4 (≤ 55 words) | +55 | 0 |
| F6 (items 1, 6) | +13 | 0 |
| **Total** | **≈ +28 (within the ±10% counting error on the ~1300 words affected)** | **−1** |

The net word change is within the counting error, and one single-column figure leaves, so the paper gets shorter on the page. To make the text strictly no longer, take the lean F3 (the III-C remark only, dropping its IV-F sentence, −30). That brings the total to about −2 words.

## Open items that need Alex
- T_in and building time constants: no verified source. The revised F3 needs neither: T_h comes from the net-load fit, and the coasting constant cancels.
- A building-physics source for the single-capacity derivation in F3 (optional; the derivation is first principles).
- The window cap is an event length the DSO chooses. F3 states only results that do not depend on it.
- The bending of the HP load with temperature near T_h (F2 mechanism) and the seasonal heating switch-off (F4) are readings of the data, not tested. Both are hedged in the content bullets.
