"""Addendum A: compose REPORT_WuThesis_ClaudeCodeVM_ADDENDUM_A_2026-11-07.md from generated parts + written text."""
import pickle, pandas as pd, numpy as np, hashlib, glob
P = pickle.load(open('out_addA/report_parts.pkl', 'rb')); C = pickle.load(open('out_addA/claim_parts.pkl', 'rb'))
X, H = P['X'], P['H']; aT, aS = X['agg']['T'], X['agg']['S']; hT, hS = H['agg']['T'], H['agg']['S']
sp = P['sp']
apx = C['APX']
apx_md = '| Thesis | Section / table | Claims with a changed check | Changed checks | Checks that reproduce the print on T but not on S |\n|---|---|---|---|---|\n' + \
    '\n'.join(f'| {"6.13" if r.target == "613" else "v7"} | {r.sec} | {r.claims} | {r.checks} | {r.flips} |' for r in apx.itertuples())
c1ch = '\n'.join(f'- {ix}: T "{r.label}" → S "{r.label_S}"' for ix, r in P['C1CH'].iterrows())
med = sp[[f'ratio_{p}' for p in 'HPNF'] + [f'dratio_{c}' for c in 'PNF']]
mg = med.groupby(sp.grp).median().round(3); mall = med.median().round(3); mmax = med.max().round(3); amax = med.idxmax()
ver = pd.read_csv('out_addA/input_verification.csv')
sha = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest()[:16] for f in sorted(glob.glob('out_addA/*.csv')) + sorted(glob.glob('code/addA_*.py'))}
shatab = '\n'.join(f'| `{f}` | `{h}` |' for f, h in sha.items())

R = f"""# RED-TEAM ADDENDUM A — The Fergus grid-cell fork (Branch T beside Branch S)

Platform: ClaudeCodeVM (Claude Code executor, programme Linux VM). Run date: 2026-11-07. Companion file to the closed main report `REPORT_WuThesis_ClaudeCodeVM_2026-11-07.md` in the same working folder (`/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_claude`). Addendum code is in `code/addA_*.py`; addendum outputs are in `out_addA/`. The main-run outputs in `out/` and `pass1_frozen/` were read and were not modified.

**Drive filing.** This file was written to the VM working folder only. **No file was created in Google Drive.** It needs filing from this copy.

**Rule followed throughout.** Branch S is a fork branch, not a correction. Nothing below grades either cell against the other, and no thesis number is called an error because Branch S gives a different value. Wherever a number differs, the report gives the value on each branch. A Fergus conclusion is called **fork-independent** only where both cells support the same reading.

---

## 1. Execution statement

**Environment.** Linux VM, 4 cores, about 1.3 GB of available RAM. Python 3.12 (`/home/hatch/workspace/.venvs/gis/bin/python`, numpy, pandas, scipy, netCDF4, cftime). **There is no R on this VM**: `which Rscript R` returns nothing, as in the main run. Neither Climpact nor the authors' R chain was run. Every number in this addendum comes from the same independent Python implementation used in the main audit:
- `cdx.py`, the Climpact 3.3 / climdex reimplementation that reproduces the authors' annual tables to 205,540 of 205,547 cells;
- `spei.py`;
- `analysis.py`, `facts.py`, `v7branch.py` and `monthly.py`;
- the main run's claim rules, `rules_613.py` and `rules_v7.py`.

None of these files was edited. The addendum adds only drivers (`addA_verify.py`, `addA_indices.py`, `addA_monthly.py`, `addA_compare.py`, `addA_tables.py`, `addA_spread.py`, `addA_adc.py`, `addA_claimlists.py`, `addA_report_tables.py`, `addA_make_report.py`), which point the unchanged code at the Branch S files.

**Same settings as the main audit (verified, not assumed):**
- **Indices:** 44 annual indices, plus 14 monthly indices for the upper/lower-quartile monthly analysis. Base period 1950–1986, with Zhang in-base bootstrapping for percentile indices. Climdex missing-value masks (≤ 15 missing days per year, ≤ 3 per month). −99.9 is treated as missing.
- **Periods:** Historical (H) 1950–1986, Present (P) 1987–2023, Near Future (N) 2024–2062, Far Future (F) 2063–2100.
- **Wilcoxon test:** rank-sum in the R `wilcox.test(exact = FALSE, correct = TRUE)` form, two-sided, with mid-ranks for ties and a tie-corrected variance. A model–period cell passes when p ≥ 0.05. A cell where all pooled values are identical has p = NA and counts as a fail.
- **Rounding:** annual index values are rounded to 6 dp before the statistics. This is the main run's primary-layer setting. I checked it by rebuilding the main run's V4 facts from `out/idx` with this setting: all p-values, changes, envelope rows and period medians are bit-identical (maximum difference 0.0). Without the rounding, the p-values differ by up to 0.0095.
- **Post hoc branches:**
  - 6.13 arrow branch: Δ is the median of the later period minus the Historical median. The arrow is "–" when |Δ| < 1e-9. A cell is shaded significant when p < 0.05 and the arrow is not "–".
  - Envelope: the observed change is "within" when it lies between the minimum and maximum of the ten model changes. Under the 6.13 rule, a reversal is a change outside the range whose sign is opposite to the median of the model changes.
  - Consensus: at least 8 of 10 models significant in the same direction.
  - v7 bounding branch: Bounded / Unbounded (magnitude offset) / Sign reversal, where a sign reversal is a change whose sign is opposite to the whole model interval. Also the Table 5 tiers, skill vs change (skilful = at least 10 of 20 passes, with Fisher's exact test), the C1 pooled boxes (which include the observations) and the D1 process confidence.

**Controls run before computing Branch S:**
1. My `cdx.py` run on the PCIC `FERGUS_SENS_EC-Earth3-Veg.txt` file reproduces the main run's `out/idx/Fergus_EC_annual.csv` exactly (maximum |difference| 0.0, same NA pattern).
2. My `monthly.py` run on Branch T EC reproduces the main run's monthly statistics (maximum difference 1.4 × 10⁻¹⁴).

**Layers.** The **primary layer is V4**, as in the main report: my own indices and statistics on the authors' homogenised v4 observation series. As a robustness check, every Branch S result was also recomputed on **H1**, the observations from my own Pass-1 homogenisation (reviewed candidate list). The observations are the same on both branches. Only the ten Fergus model series change.

**What was run for Branch S.** The full first-pass pipeline for Fergus:
- 44 annual and 14 monthly indices for the ten models;
- SPEI/SPI with Hargreaves PET, at the printed Fergus latitude 43.735°, as in the main run;
- the Test 1 Wilcoxon performance tests;
- period changes, the envelope, consensus, projections, pooled period medians and C1 boxes;
- Table 5 tiers, skill vs change and D1;
- the monthly upper-quartile analysis.

London and Harrow inputs and results are bit-identical to the main run. Every numeric claim rule from the main audit (both inventories, all table-cell rules) was then run once on Branch T and once on Branch S, and every check whose value changed was recorded (`out_addA/claim_check_changes_sec.csv`).

**Branch T values** are the main audit's own recomputed results (`out/facts_AUTHORS_v4.pkl`, `out/facts_H1_reviewed.pkl`, `out/monthly_stats_H1_reviewed.csv`), read from the saved files and not recomputed.

**What did not run:**
- Climpact and R (none on the VM).
- No figure was image-checked.
- The authors' annual tables (layer AT in the main report) exist only for Branch T, so the † mechanism of the main report has no Branch S counterpart.

**Evidence chain for every number below**, unless a table caption says otherwise: station Fergus; layer V4; the ten CanDCS-U6 models (ACCESS-ESM1-5, BCC-CSM2-MR, CanESM5, CNRM-ESM2-1, EC-Earth3-Veg, GFDL-ESM4, INM-CM5-0, MIROC-ES2L, MRI-ESM2-0, NorESM2-LM) under historical + SSP5-8.5; periods and test settings as above. The branches are:
- **T** = PCIC label `FERGUS_SENS`, grid cell (lat 32, lon 728), centre 43.708333°N 80.291669°W.
- **S** = PCIC label `FERGUS`, grid cell (lat 32, lon 727), centre 43.708333°N 80.375002°W.

"Δ" in a table is S − T unless stated otherwise.

**Axes this addendum does not test.** It tests sensitivity to the choice between **two adjacent cells of one downscaled product** (CanDCS-U6, BCCAQv2 + ANUSPLIN300, 1/12°). It does **not** test:
- other downscaling products or methods;
- other grid resolutions;
- other cells around Fergus (for example the cells to the north or south);
- the observations or their homogenisation, which are identical between the branches;
- other ensemble members, scenarios or periods;
- the Climpact executable itself.

---

## 2. Input verification (Branch S and Branch T)

`addA_verify.py` checked all 60 Fergus raw NetCDF subsets (2 labels × 10 models × pr/tasmax/tasmin) against `metadata.csv`. Results (`out_addA/input_verification.csv`):

- **SHA-256 checksums:** 60 / 60 match the `sha256` column of `metadata.csv`.
- **Grid cell:** each NetCDF's global attributes name the expected label and grid indices. For `FERGUS` these are (32, 727), with lat/lon 43.708333 / −80.375002. For `FERGUS_SENS` they are (32, 728), with 43.708333 / −80.291669. Both agree with `metadata.csv`.
- **Rows and dates:** row counts equal `row_count` (55,152 for the Gregorian and proleptic-Gregorian models; 55,115 for the five 365-day models: BCC, CanESM, GFDL, INM and NorESM). Every NetCDF date (decoded with the file's own calendar) equals the year/month/day columns of the text file.
- **Values:** the 1-decimal text series equal the full-precision NetCDF values to within rounding (maximum |difference| 0.049995) for all three variables and all 20 series. There are no missing values.
- **Package identity:** the thesis packages' `Fergus_<model>.txt` files (Package 1 and Package 2) are byte-identical to the PCIC `FERGUS_SENS_*` text files for all ten models, and differ from the `FERGUS_*` files. This confirms that Branch T is the thesis branch.

**How different the two cells are, day by day (S − T over 1950–2100, per model):**
- precipitation +0.026 to +0.030 mm/day (about +10 mm/yr);
- daily maximum temperature −0.059 to −0.064 °C;
- daily minimum temperature +0.005 to +0.028 °C;
- mean absolute daily differences 0.14–0.19 mm and 0.12–0.15 °C;
- daily correlations 0.994–0.996 (pr) and 0.9995–0.9998 (tx, tn).

---

## 3. Item 1 — Annual index values and ensemble period medians, Branch T beside Branch S

**All 44 indices differ between the branches in at least one model-year**, so every index is listed. Table 1 gives:
- the number of annual model-year cells (10 models × 151 years = 1,510) that differ;
- the mean and largest S − T difference in a single model-year;
- the **pooled ten-model ensemble period medians** for each branch (the 6.13 / v7 period-median definition: the median of all model-years in the period, observations excluded).

The per-model period medians (440 rows) are in Appendix A1. The full annual cell differences are in `out_addA/fergus_annual_cell_diffs_AUTHORS_v4.csv`, and the per-model period medians in `out_addA/fergus_model_period_medians_AUTHORS_v4.csv`.

*Table 1. Fergus, layer-independent (model-only). Pooled ensemble period medians, T / S (S − T), in each index's own unit.*

{P['T1A']}

Reading Table 1:
- **Temperature:** the cell effect on pooled medians is a few hundredths to about 0.1 °C for the temperature-level indices, and about a day for most count indices. The S cell is slightly cooler in TX and slightly warmer in TN, so DTR is lower on S.
- **Precipitation:** the S cell is wetter. PRCPTOT pooled medians are about +10 mm higher in every period, and R95p is +2 to +6 mm higher.
- **Changes over time:** the period medians shift together, so the H→F differences change much less than the levels.

---

## 4. Item 2 — Test 1 performance at Fergus

*Table 2. Fergus Wilcoxon pass counts (p ≥ 0.05), observations = authors' v4 homogenised series (V4). Temperature: 31 indices × 2 periods = 62. Precipitation: 13 × 2 = 26. "Both-period" = temperature indices passing in both H and P (the 6.13 / v7 tie-break). Printed form: H panel and P panel per model, as in Tables A1/A2 and the inventories.*

{P['T2']}

**Temperature ranking at Fergus (total of 62):**
- T: {P['RK']['tT']}
- S: {P['RK']['tS']}

**Precipitation ranking at Fergus (total of 26):**
- T: {P['RK']['pT']}
- S: {P['RK']['pS']}

**Basin precipitation sum (of 78; London and Harrow unchanged):**
- T: {P['RK']['bT']}
- S: {P['RK']['bS']}

**Reference-model selection for Fergus on each branch:**

| Rule (as printed) | Branch T | Branch S | Changes? |
|---|---|---|---|
| 6.13, C34: highest temperature total; ties broken by more both-period passes | BCC 56 = EC 56 → tie-break EC 27 vs BCC 26 → **EC-Earth3-Veg** | EC 56 alone (NorESM 55, BCC 54) → **EC-Earth3-Veg**; no tie-break needed | Selection **no**; the route to it **yes** |
| v7, V7-C288: "the model with the highest cumulative pass total" (tie-break printed only in V7-C290) | Tie BCC/EC at 56: the rule as stated in V7-C288 does not decide; V7-C290's tie-break gives **EC-Earth3-Veg** | **EC-Earth3-Veg** uniquely, by the V7-C288 rule alone | Selection **no** |
| Both theses, precipitation: highest summed pass count across the three stations (C33/C214, V7-C286/C292) | **BCC-CSM2-MR** 57 of 78 (next 55: ACCESS, CanESM, EC) | **BCC-CSM2-MR** 56 of 78 (next 55: CanESM, CNRM, MIROC) | Selection **no**; margin 2 → 1; printed 57 → 56 |
| Both theses: BCC "ranked first for precipitation at Fergus" (C214, V7-C292) | BCC 20 of 26, first | BCC 19 of 26, first (GFDL 18) | **no** |

**Robustness on H1 (my own homogenisation):** the Fergus temperature reference is EC-Earth3-Veg on both branches (T: EC 58; S: EC 57), and the precipitation reference is BCC on both.

**Fork-independent:** EC-Earth3-Veg as the Fergus temperature reference and BCC-CSM2-MR as the precipitation reference, under each thesis's selection rule.

**Cell-dependent:**
- the BCC/EC tie and the 27-vs-26 tie-break printed in C31/C34/V7-C279/V7-C290 (on S there is no tie);
- NorESM2-LM's Fergus rank (3rd on T, 2nd on S);
- the bottom of the printed range "35 to 56" (36 on S);
- the precipitation counts per model (Table 2);
- the basin sum of 57 (56 on S).

Per model, the temperature totals move by −2 to +3 between the branches. The ten-model spread is 21 passes on T (35–56) and 20 on S (36–56).

---

## 5. Item 3 — The change layer at Fergus, Branch T beside Branch S

### 5a. Bounding branch: observed change against the ten-model change range (H→P)

*Table 3. Fergus, layer V4. Observed Δ = median(P) − median(H) of the observed series, identical on both branches. The model range is the minimum and maximum of the ten model H→P median changes on each branch. "Bounding (v7)" = Bounded / Unbounded (magnitude offset) / Sign reversal (opposite to the whole interval). "6.13 class" = within / magnitude / directional reversal (opposite to the median of the model changes).*

{P['T3A']}

**Three Fergus classifications change. All are edge cases where the observed change lies within one index unit of the edge of the model range, and the edge is set by a single model:**

1. **RX1day:** observed −2.3 mm.
   - T: the lowest model change is INM −2.0 mm, so the observed change is 0.3 mm below the range: Unbounded (6.13: magnitude).
   - S: the lowest is MIROC −3.3 mm, so it is Bounded (within).
2. **CDD:** observed +1.5 days.
   - T: the highest is CNRM +2.0, so it is Bounded.
   - S: the highest is +1.0, so it is Unbounded (6.13: magnitude), lying above the range.
3. **CWD:** observed −1.0 day.
   - T: no model change is below 0, so it is Unbounded (magnitude).
   - S: BCC is −1.0, so the observed change sits exactly on the lower edge and counts as Bounded under the inclusive rule.

The two Fergus **sign reversals** under the v7 rule (CWA, SDII) and the two Fergus **directional reversals** under the 6.13 rule (CWA, SDII) are the same on both branches. Fergus temperature bounding is 28 of 31 on both branches. Fergus precipitation bounding is 10 of 13 on T and 11 of 13 on S. Fergus overall is 38 of 44 on T and 39 of 44 on S.

On H1 the same three indices flip in the same directions (Fergus 37 → 38; basin 114 → 115).

**Table 5 basin tiers (v7) that change because of these flips:**
- RX1day (V7-C376): "Station-Specific Moderate Confidence" → "Station-Specific High Confidence".
- CWD (V7-C379): "Station-Specific High Confidence" → "Basin-Wide High Confidence".
- CDD (V7-C387): "Basin-Wide High Confidence" → "Station-Specific High Confidence".

The other 41 tiers are unchanged.

**C1 pooled-box shift labels (v7 Appendix C; pools include the observations) that change at Fergus:**
{c1ch}

The location shift (Increase / Decrease / No Shift) changes only for CWD. The other two changes are spread classes.

**D1 process confidence (v7 Table 6 / Appendix D):** all eight confidence ratings are the same on both branches. Two inputs move:

{P['TD1']}

### 5b. Arrow branch (6.13 rules): direction arrows and significance shading at Fergus

The Fergus change tables hold 1,496 arrow cells:
- Table B (H→P): 44 indices × (observations + 10 models + ensemble) = 528 cells;
- Table C (H→N and H→F): 44 × 2 × (10 models + ensemble) = 968 cells.

**61 of 1,496 Fergus cells change between the branches:**
- in the H→P table, 30 of 528 (20 direction changes, 10 shading-only changes);
- in the H→N/H→F tables, 31 of 968 (19 direction changes, 12 shading-only changes).

**No cell in the observations column changes**, because the observations are identical. Two pooled-ensemble (ENS) cells change:
- R10mm H→P: ↑* on T → – on S (the pooled median change is 1 day on T and 0 on S);
- CWD H→F: – on T → ↑* on S.

All other changes are single-model cells. They concentrate in count indices whose medians change by whole days, where a one-day median shift turns an arrow into "–" or back (R10mm, R20mm, CDD, CWD, DTRgt15), and in cells whose p-value lies near 0.05. "*" marks a significant shaded cell. The full cell list (Branch T values; the main run reproduced all printed arrows on T) follows.

*Table 4. Every Fergus arrow-table cell that differs between the branches (layer-independent: models and ensemble only).*

{P['T3B']}

### 5c. Consensus at Fergus (≥ 8 of 10 models significant in the same direction)

*Table 5. Fergus consensus entries that change (counts of models with a significant increase / decrease).*

{P['T3C']}

| Horizon | Fergus consensus count, T | Fergus consensus count, S |
|---|---|---|
| Near Future, all 44 | {aT['cons']['Fergus_N_T'] + aT['cons']['Fergus_N_P']} (temperature {aT['cons']['Fergus_N_T']}, precipitation {aT['cons']['Fergus_N_P']}) | {aS['cons']['Fergus_N_T'] + aS['cons']['Fergus_N_P']} (temperature {aS['cons']['Fergus_N_T']}, precipitation {aS['cons']['Fergus_N_P']}: SDII enters) |
| Far Future, all 44 | {aT['cons']['Fergus_F_T'] + aT['cons']['Fergus_F_P']} (temperature {aT['cons']['Fergus_F_T']}, precipitation {aT['cons']['Fergus_F_P']}) | {aS['cons']['Fergus_F_T'] + aS['cons']['Fergus_F_P']} (temperature {aS['cons']['Fergus_F_T']}, precipitation {aS['cons']['Fergus_F_P']}) |

The ensemble-median projected changes and model ranges at Fergus for both horizons and all 44 indices, on each branch, are in Appendix A2.

---

## 6. Item 4 — Headline aggregates per branch, and the Fergus claims that change

### 6a. Aggregates (layer V4; H1 in brackets)

| Aggregate | Branch T | Branch S (Fergus on cell 32/727) |
|---|---|---|
| Bounded H→P cases, out of 132 | **{aT['bounded']}** [H1 {hT['bounded']}] | **{aS['bounded']}** [H1 {hS['bounded']}] |
| Per station: London / Fergus / Harrow | {aT['per_station']['London']} / {aT['per_station']['Fergus']} / {aT['per_station']['Harrow']} | {aS['per_station']['London']} / {aS['per_station']['Fergus']} / {aS['per_station']['Harrow']} |
| Basin percentage | {100*aT['bounded']/132:.1f}% | {100*aS['bounded']/132:.1f}% |
| v7 classes: Bounded / Unbounded / Sign reversal | {aT['cv7']['bounded']} / {aT['cv7']['unbounded']} / {aT['cv7']['sign_reversal']} | {aS['cv7']['bounded']} / {aS['cv7']['unbounded']} / {aS['cv7']['sign_reversal']} |
| 6.13 classes: within / magnitude / directional reversal | {aT['c613']['within']} / {aT['c613']['magnitude']} / {aT['c613']['reversal']} | {aS['c613']['within']} / {aS['c613']['magnitude']} / {aS['c613']['reversal']} |
| Indices bounded at all three stations | {aT['bounded_all3']} | {aS['bounded_all3']} (CWD joins; CDD leaves) |
| Station most often bounded | Harrow 39 (Fergus 38) | **tie**: Fergus 39 = Harrow 39 |
| Near-Future consensus by station (L / F / H), all 44 | {aT['cons']['London_N_T']+aT['cons']['London_N_P']} / {aT['cons']['Fergus_N_T']+aT['cons']['Fergus_N_P']} / {aT['cons']['Harrow_N_T']+aT['cons']['Harrow_N_P']} → range 26–27 | {aS['cons']['London_N_T']+aS['cons']['London_N_P']} / {aS['cons']['Fergus_N_T']+aS['cons']['Fergus_N_P']} / {aS['cons']['Harrow_N_T']+aS['cons']['Harrow_N_P']} → range 26–28 |
| Far-Future consensus by station (L / F / H) | {aT['cons']['London_F_T']+aT['cons']['London_F_P']} / {aT['cons']['Fergus_F_T']+aT['cons']['Fergus_F_P']} / {aT['cons']['Harrow_F_T']+aT['cons']['Harrow_F_P']} → 36–37 | {aS['cons']['London_F_T']+aS['cons']['London_F_P']} / {aS['cons']['Fergus_F_T']+aS['cons']['Fergus_F_P']} / {aS['cons']['Harrow_F_T']+aS['cons']['Harrow_F_P']} → 36–37 |
| Precipitation consensus, Near / Far (range over stations) | 0–1 / 10–11 | 0–1 / 10–11 (Fergus Near 0 → 1) |
| v7 skill vs change (skilful = ≥ 10/20): a / b / c / d | {aT['skill']['a']} / {aT['skill']['b']} / {aT['skill']['c']} / {aT['skill']['d']} | {aS['skill']['a']} / {aS['skill']['b']} / {aS['skill']['c']} / {aS['skill']['d']} |
| Misjudged by a skill-only screen | {aT['skill']['misjudged']} | {aS['skill']['misjudged']} |
| **Fisher's exact p (skill vs bounding)** | **{aT['skill']['fisher']:.3f}** [H1 {hT['skill']['fisher']:.3f}] | **{aS['skill']['fisher']:.3f}** [H1 {hS['skill']['fisher']:.3f}] |
| D1 confidence ratings (8 groups) | as printed | identical |

The Fisher row is the one aggregate whose **conventional reading flips** with the cell. On T the skill–bounding association is significant at 0.05 (p = 0.043, as printed in V7-C340). On S it is not (p = 0.081). The same happens on the H1 layer (0.045 → 0.084). Four Fergus cases change cell in the 2×2 table:
- R10mm: passes 9 → 11, so not skilful → skilful (bounded on both branches);
- RX1day: not skilful on both branches, not bounded → bounded;
- CDD: skilful on both branches, bounded → not bounded;
- CWD: skilful on both branches, not bounded → bounded.

The net effect is a +1 and d −1. The **misjudged count (29) is fork-independent**.

### 6b. Fergus numbers in the Abstract, Discussion and Conclusion that change between the branches

Method: every numeric claim rule of the main audit was evaluated on both branches. Below are all Abstract / Discussion / Conclusion claims (sections as assigned in the inventories) with at least one check whose recomputed value differs between T and S. Each entry gives the printed value, the T value and the S value. "Changes at printed precision" means the T value reproduces the print and the S value does not; "moves within printed rounding" means both round to the print. Notes in *italics* restate a printed range where the Fergus end moves.

{C['ADC']}

*Notes on the entries above (S values; London and Harrow unchanged):*
- *C4 / V7-C4 / V7-C655: 115 of 132 (87%) → 116 of 132 (88%).*
- *C9: Near-Future consensus "26–27" → 26–28.*
- *C7 / C261 / C268 / V7-C658: WSDI3 Far-Future medians "154–172" → 157–172 (Fergus 154 → 157).*
- *C214 / C264 / V7-C650: BCC basin sum 57 → 56; still first.*
- *C217: Fergus 38 → 39 of 44.*
- *C263: seven magnitude biases → six.*
- *C232: January RX1day N→F "6.9 to 8.7 mm" → 6.9 to 10.7 mm (Fergus BCC 8.65 → 10.7).*
- *C241 / V7-C601: March PRCPTOT "16% to 32% above Historical" → 16% to 41%.*
- *C247: Fergus SPEI-6 Jul–Sep Far Future "−0.78 to −0.04" → −0.75 to −0.03; PRCPTOT JJAS N→F declines "13% to 31%" → 12% to 31%.*
- *C251 / C258 / V7-C604 / V7-C626: September RX5day F−H "9.5 to 18.5 mm" → 14.2 to 18.5 mm (Fergus 9.45 → 14.2 and still the lowest; London 16.4, Harrow 18.5).*
- *V7-C589: "Harrow ... most often bounded, at 88.6%" → Harrow and Fergus tied at 39/44 (88.6%).*
- *V7-C590: TXn JFM N→F "3.4 to 8.1 °C" → 3.4 to 8.2 °C.*
- *V7-C593: Fergus RX1day is no longer outside the envelope on S, so "fell outside the envelope at one or two stations" for RX1day becomes Harrow only.*
- *V7-C594: "annual CDD change was bounded at all three stations" does not hold on S (Fergus CDD is Unbounded).*
- *V7-C598: September TXx N→F "2.1 to 5.2 °C" → 2.1 to 5.3 °C.*
- *V7-C602: R95p "+63% to +67%" → +62% to +67%; R99p "+124% to +154%" → +124% to +156%.*
- *V7-C616: Table 6 "about two thirds" of extreme-intensity changes reproduced: 66.7% → 70.8%.*
- *V7-C620: Fergus ice days "80.0 to 21.0" → 81.0 to 22.0.*
- *V7-C624: June–September rainfall declines "13% to 35%" → 12% to 35%.*

**Sign, classification and ranking changes among the Abstract / Discussion / Conclusion claims:**
- **Classification:**
  - V7-C593: Fergus RX1day changes from outside the envelope to inside.
  - V7-C594: Fergus CDD changes from inside the envelope to outside.
  - C263: the magnitude-bias count changes.
- **Ranking:** V7-C589 (Harrow uniquely most bounded → tie with Fergus).
- **Sign:** no Abstract / Discussion / Conclusion claim changes sign. Outside these sections, the sign changes are:
  - single-model arrow cells (Table 4);
  - two Fergus BCC monthly values in Results claim C187: August PRCPTOT H→P +2.25 → −0.70 mm, and September RX1day H→P +4.2 → 0.0 mm;
  - the Table B1 model-minimum entries of V7-C806 (0 → +1) and V7-C840 (0 → −1).

**Fergus claims in the Abstract / Discussion / Conclusion that were tested and do not change** (fork-independent at printed precision):
- **6.13:** C8, C218, C221, C226, C227, C230, C235, C239, C246, C253, C257, C260, C269, C270.
- **v7:** V7-C587, C592, C596, C599, C606, C609, C611, C615, C627, C637, C640, C647, C654, C656, C660.

They include:
- all observed-change statements (the observations are identical);
- the two Fergus sign reversals, CWA and SDII (V7-C656, C218);
- "temperature agreement strongest at Fergus" (V7-C587 / V7-C654: Fergus temperature passes 487 on T and 492 on S, against London 471 and Harrow 382);
- September CDD +2.0 days at Fergus (C253);
- the 6.0 to 6.1 °C warming at every station (V7-C618; Fergus 6.14 / 6.13);
- the Far-Future TMm ensemble-median change of 6.53 °C (C6).

### 6c. All other claims with a changed check

Over both inventories, {C['n_claims']} claims have at least one check whose value differs between the branches: {C['per_t'].get('613', 0)} in 6.13 and {C['per_t'].get('v7', 0)} in v7. Of these, {C['per_t_flip'].get('613', 0)} (6.13) and {C['per_t_flip'].get('v7', 0)} (v7) have at least one check that reproduces the print on T but not on S. Most are table-cell claims, summarised here. Results-section claims are listed in Appendix A3.

{apx_md}

The p-value tables differ in almost every Fergus cell, as expected: each Fergus model sample changes. The pass/fail status of those cells is summarised in Table 2.

---

## 7. Item 5 — Closing statement: what the one-cell move does and does not change

**What it does not change.**
- **Observations:** every observed Fergus statement is identical on both branches, because the observations are the same.
- **Reference models:** EC-Earth3-Veg for temperature and BCC-CSM2-MR for precipitation are selected at Fergus under each thesis's printed rule, on both branches and on both observation layers.
- **Reversals:** the two Fergus sign reversals of the v7 rule (cold-wave amplitude CWA and daily intensity SDII) and the two Fergus directional reversals of the 6.13 rule are the same in both cells.
- **Basin counts:** 3 v7 sign reversals and 10 6.13 reversals on both branches.
- **Process confidence:** the eight D1 ratings are identical.
- **Projected warming:** Far-Future TMm ensemble-median change 6.53 °C in both cells; heat-index growth.
- **Far-Future consensus:** 36 at Fergus on both branches.
- **Skill screen:** the count of cases a skill-only screen would misjudge is 29 on both branches.
- **Temperature agreement:** Fergus remains the station with the strongest temperature agreement.

These Fergus conclusions are **fork-independent**.

**What it does change.**
- **Bounding at Fergus:** 38 of 44 on T and 39 of 44 on S. The basin headline therefore reads 115 of 132 on T and 116 of 132 on S.
- **Three classifications** (RX1day, CDD, CWD), and with them three Table 5 basin tiers and the "CDD bounded at all three stations" statement.
- **The Fisher test:** the skill–bounding association is significant at 0.05 on T (p = 0.043) and not on S (p = 0.081), on both observation layers.
- **Test 1 details:** the BCC/EC tie and its printed tie-break at Fergus; NorESM2-LM's Fergus rank; the basin precipitation sum (57 vs 56).
- **Arrow tables:** 61 of 1,496 Fergus arrow/shading cells, two of them ensemble cells.
- **Near-Future consensus:** Fergus 27 vs 28.
- **Fergus BCC monthly precipitation magnitudes** that set the ends of several printed cross-station ranges:
  - September RX5day F−H 9.45 vs 14.2 mm;
  - March PRCPTOT F vs H +31.6% vs +41.2%;
  - January RX1day N→F 8.65 vs 10.7 mm.

These Fergus conclusions are **cell-dependent**. Each is stated per branch above, and neither branch is preferred.

**How large the cell effect is compared with the spread across models.** For each index and period, I took the median over the ten models of |S − T| in the model's period median and divided it by the range of the ten model period medians on Branch T. The median of this ratio over the 44 indices is:
- {mall['ratio_H']:.3f} (Historical), {mall['ratio_P']:.3f} (Present), {mall['ratio_N']:.3f} (Near) and {mall['ratio_F']:.3f} (Far);
- for temperature indices, {mg.loc['T','ratio_H']:.3f} / {mg.loc['T','ratio_P']:.3f} / {mg.loc['T','ratio_N']:.3f} / {mg.loc['T','ratio_F']:.3f};
- for precipitation indices, {mg.loc['P','ratio_H']:.3f} / {mg.loc['P','ratio_P']:.3f} / {mg.loc['P','ratio_N']:.3f} / {mg.loc['P','ratio_F']:.3f}.

For the model H→P, H→N and H→F changes, the same ratio has a median of {mall['dratio_P']:.3f}, {mall['dratio_N']:.3f} and {mall['dratio_F']:.3f}. Its largest values are {mmax['dratio_P']:.2f} ({amax['dratio_P']}, H→P), {mmax['dratio_N']:.2f} ({amax['dratio_N']}, H→N) and {mmax['dratio_F']:.2f} ({amax['dratio_F']}, H→F). Details are in `out_addA/fergus_cell_vs_spread.csv`.

In plain terms, moving the Fergus series one cell west changes a typical model's values by about 1–6% of the spread across the ten models. The effect is about 1–4% for changes between periods, smaller for temperature than for precipitation, and smaller for future than for historical periods. Per model, Test 1 temperature totals move by at most 3 passes, against a ten-model spread of 20–21. On either branch, the typical spread across models is therefore more than an order of magnitude larger than the cell effect (median ratios 0.007–0.074). For single indices the gap is smaller: the largest ratio is {mmax['ratio_H']:.2f} ({amax['ratio_H']}, Historical period medians), and for Test 1 totals it is 3 against 20–21.

The cell effect still changes conclusions in two kinds of place:
- **Rules with sharp edges.** These are envelope classifications in which the observed change lies within about one index unit of the edge of the model range, set by a single model (RX1day, CDD, CWD), and any 0.05 threshold that a statistic sits close to (Fisher p = 0.043; individual Wilcoxon cells).
- **Single-model monthly magnitudes.** The monthly analysis rests on one reference model, so its numbers do not average out across the ensemble.

Results built on ensemble medians, consensus counts or the ranking across models change little. Across them, one consensus entry changes (Fergus Near-Future SDII), two ensemble arrow cells change, and no reference-model selection changes.

**Scope of this statement.** It applies only to the choice between the two adjacent cells, (32, 728) and (32, 727), of CanDCS-U6 / BCCAQv2 + ANUSPLIN300 at Fergus. It says nothing about other downscaling products, other grid resolutions, other neighbouring cells, other ensemble members or scenarios, or the observations and their homogenisation.

---

## Appendix A1 — Per-model period medians at Fergus, Branch T / Branch S (S − T)

*Fergus, ten models, median of the annual index values in each period (H 1950–86, P 1987–2023, N 2024–62, F 2063–2100), each index in its own unit. Same index code and settings on both branches.*

{P['T1B']}

## Appendix A2 — Projected changes at Fergus (ten-model median of model Δ and model range), Branch T / Branch S

{P['T3D']}

## Appendix A3 — Results-section claims (not Abstract / Discussion / Conclusion, not table-cell rows) with a changed check

{C['BODY']}

## Appendix A4 — Addendum files and checksums (SHA-256, first 16 hex)

| File | SHA-256 (16) |
|---|---|
{shatab}
"""
open('REPORT_WuThesis_ClaudeCodeVM_ADDENDUM_A_2026-11-07.md', 'w').write(R)
print(len(R))
