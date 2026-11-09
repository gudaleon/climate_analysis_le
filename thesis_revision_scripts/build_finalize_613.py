#!/usr/bin/env python
"""Build JW_Thesis_6.13_finalized.docx from original_copy.docx (a fresh copy
of the archived 6.13 clean thesis in the Drive mirror).

Finalizing the 6.13 thesis as the errors version adds one closing chapter,
Chapter 6, placed at the end of the thesis body, immediately before the
section break that precedes the References heading, so that the new chapter
sits in the same (portrait) section as Chapter 5. The body of the thesis is
not modified in any way: no existing paragraph, table or figure is touched.

Chapter text is held in this script as data (no external transcription).
Conventions follow the thesis's demonstrated practice: American -ize
spelling as in its headings ('Data Homogenization'), the '%' symbol for
percentages (106 uses in the document, no use of 'per cent'), Times New
Roman 12 pt runs for body text in the 'Normal' style (as in Chapter 5),
Times New Roman 10 pt for captions in the 'Caption' style, and Times New
Roman 9 pt for the added table (as in the v7 revision builds).

Sources for every number in the chapter: figures_error_framework/
DESIGN_AND_EVALUATION.md and tier_classification_613.csv (tiers, margins,
flips); reports/ADDENDUM_B_HARROW_PERTURBATION_v1.md and
reports/ADDENDUM_C_LONDON_PERTURBATION_v1.md (Harrow and London branches);
reports/ROSTER_OF_EDITS_FINAL.md Part F with executor_runs/wu_claude/
REPORT_WuThesis_ClaudeCodeVM_ADDENDUM_A_2026-11-07.md (the Fergus fork);
roster Part A items A1-A4 and Part E item E1 (the four Structural items).
"""
import re
from docx import Document
from docx.shared import Pt, Emu
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

WS = '/home/hatch/workspace/jeremy_wu_redteam'
SRC = WS + '/thesis_finalize_613/original_copy.docx'
OUT = WS + '/thesis_finalize_613/JW_Thesis_6.13_finalized.docx'
FIG = WS + '/figures_error_framework/error_framework_figure.png'
TEXT_WIDTH_EMU = 6858000  # portrait section of Ch. 5: 8.5in page, 0.5in margins

CHAPTER_TITLE = '6. Error Framework, Location Sensitivity and Final Conclusions'

INTRO = (
    "The preceding chapters report the results of this study as they were computed. "
    "This closing chapter reports what an independent audit of those results established, "
    "and draws the conclusion that follows from it. The audit recomputed every quantitative "
    "claim of the thesis from the archived data and code, using implementations written "
    "independently of the originals, and classified each of the thesis's 292 claims "
    "according to what the recomputation, and a set of sensitivity experiments run "
    "alongside it, did to that claim. The first section of this chapter states the "
    "classification and the findings that carry weight in it. The second section presents "
    "the classification in figure form. The third section reports the sensitivity "
    "experiment in which the downscaled model series were sampled from a neighbouring "
    "grid cell in place of the cell the thesis used. The fourth section draws the final "
    "conclusion of the thesis from the classification and the location experiment together."
)

S61_TITLE = '6.1 A Three-Tier Error Framework'
S61 = [
    (
        "The classification has three tiers, assigned by rule rather than by judgment. "
        "A claim is Structural when it rests on a defect that changes what a number means: "
        "the quantity the executed code computed is not the quantity the text describes, "
        "so the printed statement is wrong about its own method or definition whatever "
        "the value of the number may be. A claim is Marginal when at least one of its "
        "recomputed checks changes in value, under the audit's corrections or on any of "
        "the alternative branches the audit computed, without the statement changing in "
        "kind: the number moves, and the finding the number carries does not reverse. "
        "A claim is Robust when no check on it changes under any correction or on any "
        "branch, a status attested by the coverage of the recomputation itself, which "
        "reproduced the archived annual index tables to 205,540 of 205,547 cells. Where "
        "a claim qualifies for two tiers, the higher tier takes it, so a Structural claim "
        "stands as Structural even where its values also move."
    ),
    (
        "Applied to the 292 claims of this thesis, the rules give 4 Structural claims, "
        "176 Marginal claims and 112 Robust claims (Table 6). The placement of the "
        "thesis's own summary statements is the part of the classification on which the "
        "final conclusion turns: none of the eight claims of the Abstract is Structural, "
        "five of them are Marginal and three Robust, and none of the six claims of the "
        "Conclusion chapter is Structural, two of them Marginal and four Robust. The "
        "errors the audit found are therefore real and numerous at the level of "
        "individual numbers, and none of them sits in the statements by which the thesis "
        "summarizes itself."
    ),
    (
        "The first Structural claim is the homogenization description of Section 2.2 "
        "(claim C14). The text states that the penalized maximal F test was applied "
        "directly to each temperature base series, and that daily precipitation was "
        "tested and adjusted with the transPMFred algorithm of the RHtests_dlyPrcp "
        "package. The executed chain does neither. Temperature detection is the "
        "penalized maximal t test in its reference-series form, each station tested "
        "against the mean of the other two, followed by quantile-matching adjustment; "
        "and precipitation is not tested and not adjusted at all, its column passing "
        "through the homogenization step value-identical on all 27,028 days at each "
        "station. The correction the record establishes is to the description rather "
        "than to any series: the temperature series analyzed in this thesis are the "
        "series the executed procedure produced, but the procedure that produced them "
        "is the reference-series t test, and no precipitation homogenization stands "
        "behind the precipitation results."
    ),
    (
        "The second Structural claim is the definition of the index TXb3TNb3 in "
        "Table 2 (claim C21), printed there as compound warm-event days. The executed "
        "index counts the opposite quantity: the annual number of cold compound "
        "events, an event being a run of more than three consecutive days on which "
        "both the daily maximum and the daily minimum temperature fall below their "
        "calendar-day fifth percentiles of the 1950\u20131986 baseline. The printed "
        "definition is wrong in its direction, cold rather than warm, and wrong in its "
        "quantity, events rather than days. The correction is to the definition; the "
        "index's observed values are zero in every London and Fergus year and zero or "
        "one at Harrow, so no result in the thesis turns on the mislabeled quantity."
    ),
    (
        "The third Structural claim is the evapotranspiration method named in "
        "Section 2.4 (claim C22), where the Standardized Precipitation "
        "Evapotranspiration Index is stated to have been computed with the "
        "Thornthwaite method built into Climpact. The executed code, Climpact 3.3.1, "
        "computes the precipitation-adjusted form of the Hargreaves estimate, and no "
        "Thornthwaite computation exists anywhere in the drought-index path. The "
        "correction is to the method's name and form. The SPEI values themselves are "
        "the Hargreaves values under both the printed and the corrected description, "
        "so the drought results of Chapters 3 and 4 stand as computed, under a "
        "corrected account of how they were computed."
    ),
    (
        "The fourth Structural claim is a comparison in Section 4.3 (claim C246), "
        "where the observed July decline in consecutive dry days at Fergus, five "
        "days, is described as a similar amount to London's. The London figure behind "
        "that comparison came from a defective monthly aggregation, in which the "
        "annual missing-value mask was recycled across the monthly vector. On the "
        "corrected branch London's July shortening is 2.5 days rather than 5.0, its "
        "July levels moving from 16.0 to 13.5 days, while its June shortening moves "
        "the other way, from 1.5 to 2.5 days. The Fergus figure is unaffected by the "
        "defect, but the comparison is an artifact of it: five days is not a similar "
        "amount to two and a half, and the sentence does not survive the correction."
    ),
    (
        "Two Marginal claims change in kind on a neighbouring-cell branch, and the "
        "framework names them rather than absorbing them into the count. The "
        "Abstract's statement that DTRgt15 was the only index outside the ensemble "
        "range at all three stations (claim C5) holds on the cells the thesis "
        "sampled and fails when Harrow's model series are taken from the neighbouring "
        "cell, where cold-wave amplitude also falls outside the range at every "
        "station. The statement in Section 4.4 that the September RX5day basin "
        "maximum is largest at Harrow (claim C258) likewise holds on the thesis's "
        "cells and fails when London's series are taken from the neighbouring cell, "
        "where London's perturbed value is the basin maximum. Both statements are "
        "therefore properties of the cells sampled, not of the basin, and Section 6.3 "
        "reports the experiments that establish this."
    ),
    (
        "The one axis of the classification that this framework initially recorded "
        "as open has since been tested, and it closes as a negative. In the "
        "companion bounding analysis of the same data, the audit established a "
        "pooling defect: the executed code combined the observations with the "
        "models in the Historical and Present windows where the methods text "
        "described pools of the ten models alone. In this version's own code path "
        "the defect does not run. Every pooled sample in the chain \u2014 the "
        "ensemble of the period-change computation and the pooled medians of "
        "Section 3.3 \u2014 is formed from the ten models alone in every window, "
        "and the audit's reproduction of the results workbook confirms the code "
        "reading: under pooling of the ten models alone it reproduces all 528 "
        "pooled period medians, all 396 ensemble change rows in their changes, "
        "their p-values and their sample sizes, and both pooled projected-change "
        "columns exactly, while the defect branch, with the observations folded "
        "into the Historical and Present pools, departs from the archived values "
        "in 153 of the pooled medians and in the ensemble sample size of every "
        "one of the 396 rows. No claim of this thesis is classified Structural on "
        "pooling grounds, and none needs to be; the tier counts of Table 6 stand "
        "as stated."
    ),
]

TABLE6_CAPTION = (
    "Table 6. The three tiers of the error framework applied to the 292 claims of "
    "this thesis, showing the placement of the eight claims of the Abstract and the "
    "six claims of the Conclusion chapter. A claim is Structural when it rests on a "
    "defect that changes what a number means, Marginal when a recomputed value "
    "changes without the statement changing in kind, and Robust when no check on it "
    "changes under the audit's corrections or on any alternative branch the audit "
    "computed."
)
TABLE6_ROWS = [
    ['Tier', 'All claims (of 292)', 'Abstract claims (of 8)', 'Conclusion claims (of 6)'],
    ['Structural', '4', '0', '0'],
    ['Marginal', '176', '5', '2'],
    ['Robust', '112', '3', '4'],
    ['Total', '292', '8', '6'],
]

S62_TITLE = '6.2 Margins and Movements: The Framework in Figure Form'
S62_BEFORE = [
    (
        "Figure 8 presents the classification in graphical form, and it is built on "
        "the same principle as the classification itself: it plots instability "
        "rather than state. Displays of this material that plot the value of every "
        "case saturate, because almost every case agrees with almost every other and "
        "the result is a single colour with no trend in it; three- and "
        "four-dimensional renderings attempted for this thesis failed in exactly "
        "that way. The figure instead plots, for each of the 132 bounding cases, how "
        "far the case sits from the boundary at which its classification would "
        "change, and how the family counts move when that boundary is crossed."
    ),
    (
        "In Panel A each case is plotted at its normalized margin, defined as the "
        "signed distance from the observed Historical-to-Present change to the "
        "nearest edge of the ten-model range of changes, divided by the width of "
        "that range and signed so that a case inside the range is positive. The "
        "eight process families are ordered by their median margin, and the "
        "gradient down the panel is the thesis's exposure map. Diurnal temperature "
        "structure sits at the top as the only family whose median case falls "
        "outside its range (median \u22120.03), because DTRgt15 is a magnitude "
        "offset at all three stations while its partner index DTR sits inside the "
        "range at every station. Precipitation amount and frequency, extreme "
        "precipitation intensity and wet-dry spell persistence follow, with medians "
        "of 0.10, 0.15 and 0.16; heat extremes and heat waves and the loss of cold "
        "extremes sit at 0.30; growing season and heat accumulation sits at 0.39; "
        "and the baseline temperature regime closes the panel at 0.41, its cases "
        "clustered deep inside their ranges. Seventeen of the 132 cases sit outside "
        "their ranges, and nine sit exactly at zero, five of them degenerate cases "
        "in which the observed change and both range edges are exactly zero."
    ),
    (
        "The nine cases marked in red are those whose classification changes under "
        "a neighbouring-cell sampling of their own station or on the audit's "
        "independent homogenization layer. Five of the nine \u2014 RX1day at Fergus "
        "and at Harrow, and RX3day, RX5day and R95pTOT at London \u2014 sit in the "
        "extreme precipitation intensity family, which also holds cases deep inside "
        "the range, so that family is neither sound nor unsound but mixed at a fine "
        "grain. Two more are the Fergus spell cases, consecutive dry days and "
        "consecutive wet days, which exchange places across the range boundary "
        "between the two Fergus cells; one is Harrow's cold-wave amplitude; and "
        "one, Fergus TXn, changes only on the audit's independent homogenization "
        "layer."
    ),
    (
        "Panel B plots the movement of the family counts themselves: for each "
        "family, the change in its basin count of cases within the range when one "
        "station's model series are taken from the neighbouring cell. Of the 24 "
        "family-and-perturbation pairs, only three arrows are nonzero. Extreme "
        "precipitation intensity gains one case under the Fergus substitution and "
        "one under the London substitution, and the loss of cold extremes loses one "
        "case under the Harrow substitution. One net zero conceals internal "
        "movement, as the note beneath the panel records: at Fergus the wet-dry "
        "spell family loses consecutive dry days from the range and gains "
        "consecutive wet days into it, leaving its count unchanged while two of its "
        "six cases change class. The panel's near-emptiness is its content, and "
        "read together the two panels state the framework's conclusion in graphical "
        "form: the individual cases that sit at their edges are real, countable and "
        "named, and at the level of the family counts on which this thesis's "
        "conclusions rest, they cancel."
    ),
]
FIGURE8_CAPTION = (
    "Figure 8. Margins and movements of the 132 bounding cases of this thesis "
    "under the error framework of Section 6.1. Panel A plots each case at its "
    "normalized margin, the signed distance from the observed Historical-to-Present "
    "change to the nearest edge of the ten-model range of changes divided by the "
    "width of that range, positive inside the range, grouped by process family "
    "with the families ordered by their median margin; cases whose classification "
    "changes under a neighbouring-cell sampling of their own station or on the "
    "audit's independent homogenization layer are marked in red, and cases whose "
    "range has zero width are plotted at zero as open diamonds. Panel B plots, for "
    "each family, the change in the basin count of cases within the ensemble range "
    "under each single-station neighbouring-cell substitution of Section 6.3; a "
    "point at zero means the family's count does not move."
)

S63_TITLE = '6.3 The Effect of Downscaling Location'
S63 = [
    (
        "The location experiment asks how much of this thesis depends on which grid "
        "cell of the downscaled product stands for each station. The model series "
        "are single-cell extracts of the CanDCS-U6 product, the BCCAQv2 downscaling "
        "of the CMIP6 ensemble at one-twelfth of a degree, so each station's "
        "analysis rests on the ten model series of one cell, and a different choice "
        "of cell is a different input to every downstream table. At Fergus the "
        "question arose from the archive itself: the catalogue carries two adjacent "
        "cells for the station, and the packages from which this thesis was "
        "computed use the eastern one, download label FERGUS_SENS, grid longitude "
        "index 728, centre 43.708333\u00b0N, 80.291669\u00b0W, which serves the "
        "Shand Dam point printed in Section 2.1 (43.735\u00b0N, 80.330\u00b0W); "
        "the neighbouring cell one step west, label FERGUS, longitude index 727, "
        "centre 43.708333\u00b0N, 80.375002\u00b0W, is the cell the catalogue "
        "assigns to the station, and the two centres are about 6.7 km apart. "
        "Neither cell is graded against the other anywhere in this chapter: the "
        "Fergus experiment is a fork, and both of its branches are reported. At "
        "Harrow and London no ambiguity exists, and the same one-step-west "
        "displacement was applied as a designed perturbation, at Harrow from the "
        "station cell (longitude index 697, centre 42.041667\u00b0N, "
        "82.875002\u00b0W, 2.28 km from the station point) to its western neighbour "
        "(index 696, centre 42.041667\u00b0N, 82.958336\u00b0W, 4.91 km from the "
        "point), and at London from the station cell (longitude index 718, centre "
        "43.041667\u00b0N, 81.125002\u00b0W, 2.32 km from the point) to its "
        "western neighbour (index 717, centre 43.041667\u00b0N, 81.208336\u00b0W, "
        "4.76 km from the point). In each experiment the observations, their "
        "homogenization and the other two stations are held fixed, and only the "
        "named station's ten model series change. The perturbed inputs were "
        "verified before use: at Harrow and London the station cell was "
        "re-extracted from the source archive by the perturbed extraction's own "
        "code and reproduced the delivered series exactly, and at Fergus both "
        "cells were verified against the archive's checksums and the thesis "
        "packages' own files."
    ),
    (
        "The basin totals move by one or two cases in 132. On the cells the thesis "
        "used, 115 of the 132 cases fall within the ensemble range, with 7 "
        "magnitude offsets and 10 directional reversals. With Fergus on its "
        "station cell, 116 cases fall within the range, with 6 magnitude offsets "
        "and the same 10 directional reversals. With Harrow on its perturbed cell, "
        "114 cases fall within the range, with 9 magnitude offsets and 9 "
        "directional reversals. With London on its perturbed cell, 116 cases fall "
        "within the range, with 7 magnitude offsets and 9 directional reversals. "
        "The Abstract's bracketed figure of 115 cases, and its range of 86 to 89%, "
        "therefore describe the cells the thesis sampled; computed on any single "
        "neighbouring cell the count lies between 114 and 116, inside the span the "
        "Abstract prints."
    ),
    (
        "At the level of the individual station, Fergus moves from 38 to 39 of its "
        "44 cases within the range. RX1day and CWD enter the range and CDD leaves "
        "it, and all three are edge cases in which the observed change lies within "
        "one index unit of a range edge set by a single model; the station's two "
        "directional reversals, cold-wave amplitude and SDII, stand on both cells. "
        "Harrow moves from 39 to 38. Cold-wave amplitude leaves the range and "
        "becomes a magnitude offset, its observed change falling about one index "
        "unit below the perturbed range's minimum; R95p is a directional reversal "
        "on both cells, because the reversal rule of this version reads the "
        "ensemble median rather than the whole interval; and RX1day changes only "
        "its class within this version's scheme, from directional reversal to "
        "magnitude offset, because the sign of the ensemble-median model change "
        "differs between the cells. London moves from 38 to 39. RX3day and R95pTOT "
        "enter the range, RX5day leaves it and becomes a directional reversal, and "
        "cold-wave amplitude is a directional reversal on both cells, although its "
        "margin changes decisively: the observed change of \u22121.27 sits four "
        "thousandths of a unit below a model range beginning at \u22121.26 on the "
        "thesis cell, and 4.93 units below a model range lying wholly above zero, "
        "from +3.66 to +20.07, on the perturbed cell."
    ),
    (
        "The totals move little because the cell effect is small against the "
        "spread the thesis's conclusions use. Sized as the distance between the "
        "two cells' period medians against the ten-model spread of period medians, "
        "the effect's median across the 44 indices is, at Fergus, 5.6% in the "
        "Historical window, 3.9% in the Present, 1.6% in the Near Future and 1.1% "
        "in the Far Future; at Harrow, 6.8%, 2.9%, 2.2% and 1.5% across the same "
        "windows; and at London, 7.4%, 3.9%, 2.0% and 1.4%. The largest "
        "single-index ratio at any station is under half the spread: 0.45 for the "
        "diurnal temperature range at Harrow in the Historical window, 0.42 for "
        "the same index at Fergus, and 0.39 for daily precipitation intensity at "
        "London. The classification changes catalogued above arise not because the "
        "cell effect is large but because several observed changes sit within that "
        "small effect of their decision edges."
    ),
    (
        "The scope of the experiment is one displacement, and its conclusions do "
        "not extend past it. Only the western neighbour was tested at each "
        "station, so nothing here speaks to displacements east, north or south or "
        "to the diagonal cells. Only one grid step was tested, so nothing here "
        "measures how the sensitivity grows with distance. The stations were "
        "displaced one at a time, so the basin counts under a joint displacement "
        "of two or three stations are untested and cannot be obtained by adding "
        "the single-station movements. One downscaling product at one resolution "
        "was tested, so other products, driving ensembles, resolutions, members "
        "and scenarios are outside the result. The observation side was held fixed "
        "throughout by design, so the interaction between a cell move and a "
        "different homogenization decision is untested. Within that scope the "
        "experiment is complete: all three stations have been displaced, each "
        "alone, by the same step in the same direction."
    ),
]

S64_TITLE = '6.4 Final Conclusions'
S64 = [
    (
        "The final conclusion of this thesis can now be stated with the audit's "
        "evidence attached to it. What survives entire is the physical account of "
        "Chapters 3, 4 and 5: the warming of the temperature extremes and the "
        "decline of the cold-side indices, the growth of heat-wave amplitude and "
        "frequency, the spatial heterogeneity of the observed precipitation "
        "response, and the seasonal reorganization of the freshet and "
        "summer-drought regimes. No claim of the Abstract and no claim of the "
        "Conclusion chapter is Structural, and no claim in either place changes "
        "the direction of its finding under the audit's corrections or on any "
        "neighbouring-cell branch; the recomputation behind those statements "
        "reproduced the archived annual index tables to 205,540 of 205,547 cells, "
        "and in the location experiments no abstract, discussion or conclusion "
        "claim of this thesis changes the sign of its printed finding on any "
        "branch."
    ),
    (
        "What is marginal is the precision with which parts of that account are "
        "stated. The bracketed count of 115 cases within the ensemble range is a "
        "property of the cells sampled and reads 114 to 116 on the neighbouring "
        "cells. The two superlatives named in Section 6.1 \u2014 the only index "
        "outside the range at all three stations, and the September maximum "
        "largest at Harrow \u2014 are properties of the cells in the same way, each "
        "failing on one neighbouring branch. The counts a reader is most likely to "
        "quote are therefore the counts least entitled to their last digit, and "
        "the correct statement of the thesis's central result is the bracketed "
        "range it already prints in its Abstract, now known to be a range over "
        "cells as well as over indices."
    ),
    (
        "For this version's own presentation, the arrow tables, the location "
        "experiment returns a precise verdict. At the level of families and basin "
        "counts the presentation is stable: the family counts of cases within the "
        "range move by at most one case under any single-station displacement, "
        "and no family changes its character. At the level of individual cells it "
        "is not stable. A one-cell move at Fergus changes 61 of the 1,496 Fergus "
        "arrow and shading cells, among them two pooled-ensemble cells and several "
        "outright reversals of a single model's direction; the corresponding "
        "counts are 79 of 1,496 cells at Harrow and 66 of 1,496 at London. The "
        "arrows are therefore reliable as a map of the ensemble's pattern and "
        "unreliable as a record of any one model's direction in any one cell, and "
        "they are to be read, as the bounding counts are to be read, at the level "
        "at which they are stable."
    ),
    (
        "The thesis therefore stands as follows. Its findings are robust where "
        "they are stated as findings, in the directions of change, the "
        "family-level counts and the physical narrative, and they are marginal "
        "where they are stated as exact numbers resting on a single cell, a "
        "single model or a single edge. That division is not a weakening of the "
        "work but its correct calibration: a study built on a downscaled ensemble "
        "at one-twelfth of a degree should claim the stability its methods "
        "actually have, which is stability of pattern under the perturbations "
        "that matter, demonstrated here for the choice of grid cell, and should "
        "present its edge cases as edge cases. The four corrections of "
        "Section 6.1, the two cell-dependent superlatives and the cases named in "
        "Figure 8 are the complete list of qualifications the audit attaches to "
        "the text as printed; with them stated, the conclusions of Chapter 5 are "
        "adopted as the conclusions of this thesis."
    ),
]

# ---------- convention assertions on the chapter text ----------
ALL_TEXT = ' '.join([INTRO] + S61 + S62_BEFORE + S63 + S64 +
                    [TABLE6_CAPTION, FIGURE8_CAPTION])
for pat in [r'per cent', r'homogenisation', r'behaviour', r'normalisation',
            r'summarised|summarising', r'labelled|labelling',
            r'characterised|characterising', r'organised|organising',
            r'judgement', r'artefact', r'\bpercent\b']:
    assert not re.search(pat, ALL_TEXT), (pat, re.search(pat, ALL_TEXT).group(0))
print('chapter text conventions OK; paragraphs:',
      1 + len(S61) + len(S62_BEFORE) + len(S63) + len(S64))

# ---------- open the document and locate the insertion anchor ----------
d = Document(SRC)
paras = d.paragraphs
ref_hits = [i for i, p in enumerate(paras)
            if p.style.name == 'Heading 1' and p.text.strip() == 'References']
assert len(ref_hits) == 1, ref_hits
ref_i = ref_hits[0]
anchor_para = paras[ref_i - 1]
assert anchor_para.text.strip() == ''
pPr = anchor_para._p.pPr
assert pPr is not None and pPr.find(qn('w:sectPr')) is not None, \
    'paragraph before References does not carry the section break'
anchor = anchor_para._p
print('anchor: paragraph', ref_i - 1, '(empty, carries sectPr); References at', ref_i)

BODY = 'Normal'

def styled_run(p, text, font_name='Times New Roman', size=Pt(12)):
    r = p.add_run(text)
    r.font.name = font_name
    r.font.size = size
    return r

def new_para(text, style, font_size=Pt(12)):
    p = d.add_paragraph(style=style)
    if text:
        styled_run(p, text, size=font_size)
    anchor.addprevious(p._p)
    return p

def new_heading(text, style):
    p = d.add_paragraph(style=style)
    p.add_run(text)
    anchor.addprevious(p._p)
    return p

# ---------- build the chapter ----------
new_heading(CHAPTER_TITLE, 'Heading 1')
new_para(INTRO, BODY)

new_heading(S61_TITLE, 'Heading 2')
for t in S61[:2]:
    new_para(t, BODY)
new_para(TABLE6_CAPTION, 'Caption', font_size=Pt(10))

tbl = d.add_table(rows=len(TABLE6_ROWS), cols=4)
anchor.addprevious(tbl._tbl)
tbl.style = 'Normal Table'
tblPr = tbl._tbl.tblPr
tblW = parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>')
tblLook = parse_xml(f'<w:tblLook {nsdecls("w")} w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>')
for el in list(tblPr):
    if el.tag in (qn('w:tblW'), qn('w:tblLook')):
        tblPr.remove(el)
tblPr.append(tblW); tblPr.append(tblLook)
for ri, rowvals in enumerate(TABLE6_ROWS):
    for ci, val in enumerate(rowvals):
        cell = tbl.cell(ri, ci)
        cell.text = ''
        p = cell.paragraphs[0]
        p.style = d.styles['Normal']
        run = p.add_run(val)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9)
        if ri == 0:
            run.bold = True
        rPr = run._r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rPr.append(rFonts)
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rFonts.set(qn(attr), 'Times New Roman')

for t in S61[2:]:
    new_para(t, BODY)

new_heading(S62_TITLE, 'Heading 2')
for t in S62_BEFORE:
    new_para(t, BODY)
fig_para = d.add_paragraph(style=BODY)
anchor.addprevious(fig_para._p)
run = fig_para.add_run()
run.add_picture(FIG, width=Emu(TEXT_WIDTH_EMU))
new_para(FIGURE8_CAPTION, 'Caption', font_size=Pt(10))

new_heading(S63_TITLE, 'Heading 2')
for t in S63:
    new_para(t, BODY)

new_heading(S64_TITLE, 'Heading 2')
for t in S64:
    new_para(t, BODY)

d.save(OUT)
print('saved', OUT)
