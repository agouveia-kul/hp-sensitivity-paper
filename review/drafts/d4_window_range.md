# D4 — literature range for the window Δt_Th (draft, not placed)

## Source (verified 21 Oct 2026)
- Crossref metadata for doi:10.1177/0957650912454830: J. Hong, N. J. Kelly, I. Richardson, M. Thomson, "Assessing heat pumps as flexible load", *Proc. IMechE Part A: J. Power and Energy* 227(1):30–42, online 2012, issue 2013.
- Abstract, checked on Strathprints: shifting heat pump operation in the existing building stock is limited, "with time shifts of only 1–2 h achieved before there was a serious impact on the comfort of the occupant". With dramatically improved insulation and substantial thermal buffering, "sizable time shifts of up to 6 h were achievable".
- The 20 Oct log entry gave the author order as "Hong, Kelly, Thomson & Richardson". Crossref has Richardson third and Thomson fourth.

## Placement
IV-F, in the paragraph on the seasonal flexibility figure, right after
"…25 HPs with $P_h^{\max} = 144$~kW, drawn for an illustrative window $\Delta t_{Th} = 4$~h."

## Insertion (two sentences)
```latex
For comparison, a study of UK dwellings found that HP operation can be shifted by only 1--2~h in the existing stock before occupant comfort suffers, and by up to 6~h with much improved insulation and thermal buffering \cite{Hon13}. The illustrative 4~h lies within this range.
```

Shorter alternative (one sentence):
```latex
This lies within the 1--6~h over which HP operation could be shifted in UK dwellings, from the existing stock to well-insulated, thermally buffered homes \cite{Hon13}.
```

## Bib entry (`paper/references.bib`)
```bibtex
@article{Hon13,
  author  = {J. Hong and N. J. Kelly and I. Richardson and M. Thomson},
  title   = {{Assessing heat pumps as flexible load}},
  journal = {Proc. Inst. Mech. Eng. A: J. Power Energy},
  volume  = {227},
  number  = {1},
  pages   = {30--42},
  year    = {2013},
  doi     = {10.1177/0957650912454830}
}
```

## Notes
- The draft does not say "air-source" or "simulation", because the abstract does not confirm either.
- The paper's window Δt_Th (within which the population must deliver a fixed thermal energy) is mapped to Hong et al.'s "time shift" of HP operation. The two are close but not identical, hence "for comparison" rather than "this window is…".
- Placing it closes R47 fully (R47 is now "partly", with only D4 open).
