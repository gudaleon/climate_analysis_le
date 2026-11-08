#!/usr/bin/env python3
"""Assemble REPORT_WuThesis_GrokBuild_2026-11-07.md"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import pandas as pd
import numpy as np

OUT = Path("/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_grok/pass1/out")
DEST = Path("/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_grok/REPORT_WuThesis_GrokBuild_2026-11-07.md")
PKG613 = Path("/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data")

v613 = json.load(open(OUT / "verdicts_613.json"))
vv7 = json.load(open(OUT / "verdicts_v7.json"))
env2 = pd.read_csv(OUT / "pass2_author_tables_envelope.csv")
env1 = pd.read_csv(OUT / "envelope.csv")
pc2 = pd.read_csv(OUT / "pass2_author_tables_pass_counts.csv")
head = json.load(open(OUT / "headlines.json"))
svc1 = json.load(open(OUT / "skill_vs_change.json"))
svc2 = json.load(open(OUT / "pass2_author_tables_skill.json"))
pcic = pd.read_csv(OUT / "pcic_vs_authors_models.csv")
integ = pd.read_csv(OUT / "integrity.csv")
null = pd.read_csv(OUT / "envelope_null_permute.csv")
loo = pd.read_csv(OUT / "envelope_loo.csv")
pmed = pd.read_csv(OUT / "period_medians.csv")
cons2 = pd.read_csv(OUT / "pass2_author_tables_consensus.csv")

# Re-score Table C1 against author-table pooled medians
NAME_MAP = {
    "csdi": "CSDI6", "csdi3": "CSDI3", "wsdi": "WSDI6", "wsdi3": "WSDI3",
    "fd": "FD", "id": "ID", "su": "SU", "tr": "TR", "tnn": "TNn", "tnx": "TNx",
    "txx": "TXx", "txn": "TXn", "txm": "TXm", "tmm": "TMm", "tnm": "TNm",
    "tn10p": "TN10p", "tn90p": "TN90p", "tx10p": "TX10p", "tx90p": "TX90p",
    "dtr": "DTR", "dtrgt15": "DTRgt15", "gddgrow10": "GDDgrow10",
    "txb3tnb3": "TXb3TNb3", "txge30": "TXge30", "txgt50p": "TXgt50p",
    "tnltm20": "TNltm20", "gsl": "GSL", "cwa": "CWA", "cwf": "CWF",
    "hwa": "HWA", "hwf": "HWF", "prcptot": "PRCPTOT", "r10mm": "R10mm",
    "r20mm": "R20mm", "rx1day": "RX1day", "rx3day": "RX3day", "rx5day": "RX5day",
    "sdii": "SDII", "r95p": "R95p", "r95ptot": "R95pTOT", "r99p": "R99p",
    "r99ptot": "R99pTOT", "cdd": "CDD", "cwd": "CWD",
}
MODELS = ["ACCESS", "BCC", "CanESM", "CNRM", "EC", "GFDL", "INM", "MIROC", "MRI", "NorESM"]

def load_annual(st):
    df = pd.read_excel(PKG613 / "2_Data" / "3_Annual_index_tables" / f"All_{st}_observed_and_10_models_1950-2100.xlsx")
    df.columns = [str(c).strip() for c in df.columns]
    df["Index"] = df["Index"].astype(str).str.strip().str.lower().map(NAME_MAP)
    for c in MODELS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c] == -99.9, c] = np.nan
    return df

pooled_hist = {}
for st in ["London", "Fergus", "Harrow"]:
    df = load_annual(st)
    sub = df[(df.Year >= 1950) & (df.Year <= 1986)]
    for idx, g in sub.groupby("Index"):
        vals = np.concatenate([g[m].to_numpy(float) for m in MODELS])
        vals = vals[np.isfinite(vals)]
        pooled_hist[(st, idx)] = float(np.median(vals)) if vals.size else np.nan

import re
c1_pat = re.compile(r"Table C1 reports for (\w+) station index (\S+) the Historical \(1950–1986\) entry printed as \"([-\d.]+)")
for row in vv7:
    m = c1_pat.search(row["text"])
    if not m:
        continue
    st, idx, hist = m.group(1), m.group(2), float(m.group(3))
    rec = pooled_hist.get((st, idx), np.nan)
    ok = np.isfinite(rec) and abs(rec - hist) <= max(0.05, 0.005 * abs(hist) + 0.05)
    # printed C1 uses 1 decimal often; allow 0.05
    if abs(hist) >= 10:
        ok = np.isfinite(rec) and abs(rec - hist) <= 0.15
    row["printed"] = f"{st} {idx} Hist {hist}"
    row["recomputed"] = f"author-table pooled median {rec:.4g}"
    row["verdict"] = "CONFIRMED" if ok else "DISPUTED"
    row["evidence"] = "Pass 2 pooled median of the ten model annual values 1950-1986 from the authors' annual tables (the input to Table C1)."

def md_table(rows, extra_cols=None):
    lines = ["| Claim | Printed | Recomputed | Verdict | Evidence |",
             "|---|---|---|---|---|"]
    for r in rows:
        def esc(x):
            return str(x).replace("|", "/").replace("\n", " ")[:220]
        lines.append(f"| {r['id']} | {esc(r.get('printed') or r['text'][:80])} | {esc(r.get('recomputed',''))} | **{r['verdict']}** | {esc(r.get('evidence',''))} |")
    return "\n".join(lines)

c613_counts = Counter(r["verdict"] for r in v613)
v7_counts = Counter(r["verdict"] for r in vv7)

parts = []
parts.append("""# RED TEAM AUDIT REPORT — Jeremy Liyan Wu MSc thesis (two new-data versions)

**File:** `REPORT_WuThesis_GrokBuild_2026-11-07.md`  
**Auditor:** Grok Build executor (independent hostile audit)  
**Date:** 2026-11-07  
**Targets:** Thesis 6.13 method, new data (C1–C292) and thesis v7 defence framework, new data (V7-C1–V7-C1032)

This report does not summarise the theses. It records what was executed, what was recomputed, and a verdict for every inventory claim.

---

## 1. Execution statement

**Environment.** Linux VM. Python `/home/hatch/workspace/.venvs/gis/bin/python` (numpy 2.5.4, pandas 3.0.6, scipy 1.16.3, xarray, netCDF4, openpyxl). **No system R.** The authors' R chain was not re-executed. Pass 1 is an independent Python reimplementation from the daily series. Pass 2 audits the R source and recomputes the analysis layer from the authors' annual index tables in Python. A claim is not marked CANNOT VERIFY merely because R could not be run.

**Order.** Pass 1 completed before any numbered R analysis script, results workbook, or Climpact output file was used as an input to the numbers. Package READMEs, step READMEs, theses/layout text, claims inventories, ECCC sources, merged daily series, model daily series, and the programme PCIC download were read in Pass 1. After Pass 1 finished, Pass 2 read `common.R`, `v613_helpers.R`, `v7_helpers.R`, steps 04–10, the annual index workbooks, the monthly upper-quartile summary, and the homogenised series.

**Pass 1 code (this run).** Written and executed under `executor_runs/wu_grok/pass1/`:
- `io_daily.py` — rebuild of the 1950–2023 station merges from ECCC sources (printed splice vs executed splice); SHA-256 comparison of 30 model files to `/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final/txt/`; daily integrity (tmin>tmax, negatives, calendars).
- `homogenise.py` — independent two-round quantile matching (Mq=20) on the documented 19-break and 18-break lists; automatic F-test detection branch.
- `indices.py` — 44 annual indices plus monthly subset from the daily series (base 1950–1986, Zhang leave-one-out calendar-day percentiles, EHF/ECF heat/cold waves, Thornthwaite SPI/SPEI).
- `stats.py` — Wilcoxon rank-sum matching the printed settings (two-sided, exact disabled, continuity correction 0.5, midranks); envelope (6.13 reversal vs ensemble median; v7 sign reversal vs every model); 8-of-10 consensus; skill-vs-change Fisher; leave-one-out envelope; permutation null for bracketing.
- `run_pass1.py` — orchestration (72 annual jobs in an 8-process pool; 966.7 s).

**Pass 1 inputs.** ECCC station sources and merged series in Package 1 `2_Data/1_Observations/`; 30 model daily series compared to PCIC `txt/` (independent provenance). Primary observed daily series = executed merge (byte-identical to the package merged files). Homogenisation applied independently; authors' homogenised files were not used as Pass 1 inputs.

**Pass 2 inputs.** Authors' `All_*_observed_and_10_models_1950-2100.xlsx`; `Monthly_upper_quartile_summary.xlsx`; R steps 04–10 and helpers; homogenised `*_v4.txt` for series comparison only.

**What did not run.** Authors' RHtestsV4 / Climpact 3.3.1 / R `wilcox.test` (no R). Independent QM is not RHtests `QMadj.GaussianDLY.wRef`. Independent EHF is not Climpact's EHF binary. SPI/SPEI is a Python gamma/log-logistic approximation, not the R SPEI package.

**Subtree completeness (checked before Pass 2 use).**
- Package 1 `2_Models/c_Climpact_indices`: 2,941 files, 163,433,847 bytes — matches the pack manifest. Whole `2_Models` = 2,971 files (manifest 3,143; the unzipped PCIC folder is absent; the programme PCIC copy was used instead).
- Package 1 `5_Figures`: **0 files** (manifest 55).
- Package 2 `5_Figures`: **0 files** (manifest 56).
- Package 2 `2_Models`: 1,313 files (manifest 2,972); `c_Climpact_indices` 1,283 files — incomplete. Pass 2 therefore used Package 1 annual tables and monthly workbooks (present in both packages) rather than Package 2 Climpact csvs.
- Figure-only claims are CANNOT VERIFY with this missing input named.

**Wilcoxon settings (primary).** Two-sided Mann–Whitney; exact computation off; continuity correction on (c = 0.5); midranks for ties; missing `-99.9` dropped; pass at p ≥ 0.05. Authors' `wilcox_p` additionally returns p = 1 when all values in the pooled sample are identical. Sensitivity: continuity off (pass-count table written).

**Primary vs secondary number layers.**
- Layer A (Pass 1): daily series → independent indices → tests. This is the hostile independent value.
- Layer B (Pass 2): authors' Climpact annual tables → independent Python tests. This asks whether the printed analysis arithmetic follows from those tables.

Where Layer A and Layer B disagree, the claim is **DISPUTED** as a property of the daily series independently indexed, and Layer B is reported beside it. Table-cell claims that are defined as operations on the annual tables are scored on Layer B.

---

## 2. Verdict table — Target 1 (6.13, C1–C292)

**Counts:** CONFIRMED {c613_c} · DISPUTED {c613_d} · CANNOT VERIFY {c613_n} · n = 292.
""".format(c613_c=c613_counts.get("CONFIRMED",0), c613_d=c613_counts.get("DISPUTED",0), c613_n=c613_counts.get("CANNOT VERIFY",0)))

parts.append(md_table(v613))

parts.append("""

---

## 3. Verdict table — Target 2 (v7, V7-C1–V7-C1032)

**Counts:** CONFIRMED {v7_c} · DISPUTED {v7_d} · CANNOT VERIFY {v7_n} · n = 1032.

Table B1 (V7-C759–C890): all 132 envelope cells **CONFIRMED** from the authors' annual tables. Table C1 Historical medians rescored against those same tables below.
""".format(v7_c=v7_counts.get("CONFIRMED",0), v7_d=v7_counts.get("DISPUTED",0), v7_n=v7_counts.get("CANNOT VERIFY",0)))

# recount after C1 rescore
v7_counts = Counter(r["verdict"] for r in vv7)
parts[-1] = parts[-1].replace(
    "CONFIRMED {0}".format(Counter(json.load(open(OUT/"verdicts_v7.json"))[i]["verdict"] for i in range(0))),
    "CONFIRMED",
)  # no-op safety

parts.append(md_table(vv7))

# recompute counts after C1 fix
vc = Counter(r["verdict"] for r in vv7)

parts.append(f"""

**v7 counts after Table C1 rescore against author annual tables:** CONFIRMED {vc.get('CONFIRMED',0)} · DISPUTED {vc.get('DISPUTED',0)} · CANNOT VERIFY {vc.get('CANNOT VERIFY',0)}.

Remaining CANNOT VERIFY are concentrated in: (i) Appendix A p-value grids (individual three-decimal cells; Pass 2 recovered the printed pass-count rows exactly); (ii) monthly cells not bound to the automated matcher (the authors' `Monthly_upper_quartile_summary.xlsx` was used to confirm the headline monthly deltas that were bound); (iii) figure-only claims (`5_Figures` empty); (iv) literature citations.

---

## 4. Pass 2 audit log

### 4.1 Shared steps 01–04

| Topic | Executed (R) | Printed method | Printed numbers follow | Effect |
|---|---|---|---|---|
| London splice | Airport station file to 18 Sep 2002; London CS 19 Sep 2002–31 Dec 2017 with airport ECCC fill; **station file after 2017** | CS from 19 Sep 2002 with airport fill of isolated missing days; no mention of reverting to the station file | Executed merge. Printed-rule merge leaves London 2018–2023 empty (CS and airport ECCC CSVs end 2017-12-31). Station file has 2,100 finite tx days in 2018–2023. | Present-period London sample. Executed finite tx 26,882 vs printed-rule 24,782. |
| Fergus 29 Sep 2012 precip | Filled from ECCC daily | v7: “single continuous record”; step-02 README documents the fill | Executed | One rain day |
| tx < tn before homog | Both set missing | Not in 6.13 methods text | Executed | Pre-test cleaning |
| Homogenisation reference | Two-neighbour mean, two rounds, StepSize pruning, QM Mq=20, Ny4a=0 | **6.13 C14: PMF applied directly because no fully homogeneous reference was available.** v7 C66–C67: reference-series form with two-neighbour mean | **v7 text and the code.** 6.13 C14 does not describe the executed pipeline | Shared-layer methods contradiction between the two theses |
| Candidate list | Reviewed `candidates.csv`, not `detect.R` alone | v7 describes triangulation; step-02 README states the reviewed list plus metadata and re-datings | Executed reviewed list | Automatic detection branch does not recover the 22 candidates (Pass 1 auto-detect) |
| 18 vs 19 breaks | Fergus tn 1985-02 “No” in round 1, “Yes” in round 2 | v7 C73: 19 breaks | 19-break round-2 list | Between-branch tn MAD at Fergus 0.34 °C; 51 tn-clip days at Fergus after adjustment (matches the README) |
| Independent QM vs RHtests | Pass 1 QM RMSE vs authors' homog: London tx 0.18, Fergus tn 0.37, Harrow tn 0.46 °C | Quantile matching as printed | Authors' RHtests series | Independent QM does not reproduce RHtests daily adjustments |
| DTRgt15 | Computed in step04 from daily series (NA if any month >3 missing or year >15 missing), **not Climpact** | Table 2 definition (count of days DTR>15) | step04 rule | NA rule is stricter than a 15-day annual-only rule |
| HWA/CWA | Climpact EHF/ECF files; −99.9 → NA (event-conditional medians) | Study-specific, units °C²; v7 C211–C212 document the −99.9 rule | Climpact EHF | Independent EHF does not match Climpact HWA/CWA (Pass 1 HWA Historical London pooled ~24 vs printed ~15) |
| Median | 6.13 uses `py_median` (numpy even-n mean). v7 Test 2 uses R `median()` | Period medians | Both are even-n averages; last-bit differences only | Fork in the shared layer that does not move classifications except at 1e-9 walls |
| Envelope tolerance | `lo - 1e-9 <= o <= hi + 1e-9` | Printed: Δmin ≤ Δobs ≤ Δmax | Code | London CWA −1.26764 vs min −1.26332 is outside even with 1e-9 (printed as Unbounded) |
| Wilcoxon all-ties | `wilcox_p` returns 1 if all combined values equal | Printed: NA for missing; not this all-tie rule | Code | Explains some `nan` vs 1.000 cells (TXb3TNb3) |
| Arrow | `abs(d)<1e-9` → en dash; else sign of d; sig = p<0.05 and not dash | Direction of period medians; dash = no change; shading = p<0.05 | Code | Mandatory arrow-branch rule, reproduced |
| Ensemble arrow | Pooled ten-model sample per period, then median difference | 6.13 §2.6 three levels including ensemble-pooled | Code | Distinct from median-of-model-deltas used for C42 |

### 4.2 6.13 steps 05–10

- step05: model vs obs Wilcoxon, pass p≥0.05, cumulative scores, reference-model rule (highest cumulative; Fergus temperature tie broken by more indices passing in both periods). **Pass 2 on author tables recovers the printed London/Fergus/Harrow scores, including NorESM 52, EC/BCC 56 at Fergus, EC 44 at Harrow, BCC precip 57/78.**
- step06: median change, Wilcoxon, arrows for Observed / 10 models / pooled Ensemble.
- step07: 6.13 classes (within / reversal vs **ensemble median** / magnitude bias); also stores `rev_all_models` (v7 definition).
- step08: consensus = max(n up-sig, n down-sig) ≥ 8; projected change = `py_median` of 10 model Δ plus pooled Δ.
- step09: pooled ten-model median per period (boxplot numbers).
- step10: wide arrow tables.

### 4.3 v7 steps 05–10

- step05 Test 1: same Wilcoxon as 6.13 (shared).
- step06 Test 2: Bounded / Sign reversal (opposite **every** model) / Unbounded. **Pass 2 recovers 115/132, 3 sign reversals (CWA and SDII at Fergus, R95p at Harrow), 14 unbounded.**
- step07: skilful = ≥10 of 20 passes; 2×2 vs bounded; Fisher exact. **Pass 2 recovers 96, 10, 19, 7, misjudged 29, p = 0.04344.**
- step08: pooled projections and 8-of-10 consensus.
- step09: eight process groups; coherence uses expected sign (cold group: decrease except CWA increase); zeros rounded to 6 decimals; High/Moderate/Low rule as in V7-C192–195. Group names in code (“Loss of cold extremes”) differ slightly from the printed table (“Cold extremes and cold waves”).
- step10: key numbers.

**Shared-layer divergence between the two theses (defect, not a methods fork):** 6.13 C14 vs v7 C66 on homogenisation reference; 6.13 C42 TMm FF 6.39/6.17/6.53 (median of model deltas) vs v7 C403 6.1/6.0/6.1 (pooled-median difference). Both quantities exist in the same annual tables.

---

## 5. Discrepancy log

| Item | Printed | Layer A (Pass 1 independent) | Layer B (Pass 2 author tables) |
|---|---|---|---|
| Envelope bounded | 115/132 | **112/132** | **115/132** |
| 6.13 reversals vs median | 10 | 11 | 10 |
| v7 sign reversals | 3 | 1 (SDII Fergus only) | 3 (CWA+SDII Fergus, R95p Harrow) |
| Skill 2×2 | 96, 10, 19, 7 | 92, 13, 20, 7 | 96, 10, 19, 7 |
| Fisher p | 0.043 | **0.127** | **0.04344** |
| Misjudged | 29 | 33 | 29 |
| London temp NorESM | 52/62 | 46/62 | 52/62 |
| TMm ens-median Δ FF | 6.39, 6.17, 6.53 | 6.388, 6.166, 6.526 | 6.388, 6.166, 6.531 |
| TMm ens-median Δ NF | 3.29, 3.25, 3.25 | 3.287, 3.245, 3.262 | 3.287, 3.245, 3.253 |
| London FD pooled H→F | 144 → 68 | 144 → 67.5 | (Climpact tables) |
| London SU, TR, TXge30 FF | 130, 50, 75 | 130, 50, 75 | matches |
| HWA London hist/FF | ~15 / 43 | **23.8 / 77.9** (independent EHF) | Climpact ~15 / 43 |
| Fergus model files vs PCIC nearest | nearest cell | **byte-identical to FERGUS_SENS, not FERGUS** | authors' series = SENS |
| Independent homog vs RHtests | RHtests v4 | RMSE 0.14–0.46 °C | authors' series |
| London 2018–2023 | Present window includes these years | Printed splice empty; executed splice present | executed |

Near-tie: London CWA Δobs = −1.26764, Δmin = −1.26332 (printed −1.27 vs −1.26). Unbounded by 0.004 °C².

---

## 6. Composition audit

### 6.1 Calendar
Five models (BCC, CanESM, GFDL, INM, NorESM) have 55,115 days, 0 Feb 29 — 365-day calendar. Five (ACCESS, CNRM, EC, MIROC, MRI) have 55,152 days, 37 Feb 29 — Gregorian (1952–2096; 2100 not leap). Indices were computed on each model's own dates. Month-bound indices (JFM, JJAS, FD/ID around 1 Mar) therefore rest on 28-day Februaries in the 365-day models even in Gregorian leap years. BCC and NorESM (monthly reference models) are 365-day; EC (Fergus/Harrow temperature reference) is Gregorian. v7 C244 states this and is CONFIRMED.

### 6.2 Period
Historical 1950–1986 = 37 y; Present 1987–2023 = 37 y; Near 2024–2062 = 39 y; Far 2063–2100 = 38 y. Printed “about 37 years” / v7 C208 names 39 and 38 for the futures. Percentile baseline 1950–1986 matches Climpact settings. Observed Present n is not 37: valid years (Pass 1 homog19, median across indices) London T 34 / P 34; Fergus T 36 / P 36; Harrow T 31 / P 29. Printed v7 C81–C86: London Hist 37 T / 36 P, Present 33 T / 32 P; Fergus Hist 27–29 T / 29 P, Present 36; Harrow Hist 36–37 T / 37 P, Present 29–30 T / 27 P. Order of magnitude confirmed; exact n depends on the NA rule per index.

### 6.3 Station
**Merge.** Executed reconstruction is byte-identical to the package merged files for all three stations (on overlapping finite days). Printed London splice ≠ executed 2018–2023 (see audit log). Harrow April 1992 fill from 6133360 confirmed. Fergus 29 Sep 2012 precip fill confirmed.

**Grid cells (PCIC metadata, independent download).**
- London: authors' 10 series **byte-identical** to PCIC LONDON (cell 43.041667, −81.125002, 2.32 km).
- Harrow: **byte-identical** to PCIC HARROW (42.041667, −82.875002, 2.28 km).
- Fergus: authors' 10 series **byte-identical to FERGUS_SENS** (43.708333, −80.291669, 4.28 km), **not** the nearest FERGUS cell (43.708333, −80.375002, 1.49 km). Max abs differences vs nearest cell: 18–35 mm precipitation, 4.8–9.3 °C tmax.
- Climpact station settings use Fergus lat/lon 43.695, −80.377 (near the nearest cell, used for Thornthwaite), while the daily series is the farther cell.
- Printed method: “grid cell containing the station coordinates” / “nearest 43.735 N, 80.330 W”. **Executed Fergus series is the sensitivity cell.** This is a shared-layer defect. Pass 1 model indices used the PCIC nearest cell; TMm ensemble-median deltas still matched 6.13 C42, so that headline is robust to the cell choice. Envelope counts and pass counts are not.

### 6.4 Index
Study-specific indices:
- RX3day, CSDI3, WSDI3, DTRgt15, TXge30, GDDgrow10: definitions match Table 2; DTRgt15 is extra-Climpact with a monthly missingness rule.
- TXb3TNb3: txtn=3 compound TX90 and TN90 spells; some model-period tests return NA/nan (all-zero or undefined ranks) as printed.
- CWA/CWF/HWA/HWF: Climpact EHF/ECF, units °C². Independent EHF does not reproduce Climpact amplitudes. Printed HWA/CWA numbers follow Climpact, not the underspecified “study-specific” sentence in Table 2.
- If HWA/CWA are computed as independent EHF, envelope membership of CWA at Fergus (a v7 sign reversal) **moves**.

### 6.5 Homogenisation
Reviewed list ≠ automatic detection. Pass 1 auto-detect dates do not coincide with the 22 candidates (e.g. London tn 1961-06 metadata break is not an automatic top hit). Independent QM at the documented 19 breaks produces series with RMSE 0.14–0.46 °C vs RHtests. Mean adjustment (authors homog − merged): London tx −0.12 °C, Fergus tn +0.18 °C, Harrow tn −0.53 °C. Precipitation unadjusted (pr MAD = 0). 18-break vs 19-break: Fergus tn MAD 0.34 °C.

### 6.6 Envelope and consensus
Layer B: 115/132; 33 indices bounded at all three stations; DTRgt15 unbounded at all three.  
Leave-one-out (Pass 1 independent): bounded per station min 32–35 of 44 (one model can move the count).  
6.13 reversal (vs median) vs v7 reversal (vs every model): 10 vs 3 on Layer B. Applying the 6.13 reversal rule to v7's data is the 10-reversal list; applying the v7 rule to 6.13's data is the 3-reversal list. **Fork-dependent.** Consensus 26–27 NF and 36–37 FF is fork-independent on Layer B.

---

## 7. Alternative explanations (ranked by damage to headlines)

1. **Envelope width / null bracketing (not killed).** Permuting observed Δ across the 44 indices within station (2,000 draws): null mean bounded ≈ 16/44, 95th percentile 20–21, max 26. Printed 38–39/44 and Pass 1 37–38/44 both sit above every null draw. The 115/132 headline is **larger than a min–max envelope of ten unrelated numbers would produce by chance**, but a range of ten still brackets most series; the excess over the null is the actual content. Damage if ignored: the raw 87% figure is easy to over-read.

2. **Index definition / EHF (not killed for HWA/CWA; killed for TMm/FD/SU).** Independent EHF does not match Climpact HWA/CWF. Fergus CWA sign reversal is a Climpact-EHF result. Damage: the three v7 “structural failures” include CWA; that node is definition-dependent.

3. **Homogenisation (partially killed).** Observed Historical–Present TMm still warms without adjustment (layer not fully re-piped). Independent QM changes daily values by tenths of a degree (RMSE). Pass 1 envelope 112 vs 115: three-node movement. Damage: small for TMm; material for envelope membership of marginal nodes (London CWA, SDII).

4. **Fergus grid cell (not killed).** Authors used FERGUS_SENS. Printed method is the nearest cell. TMm FF deltas survived; pass counts and some precip nodes did not in Pass 1. Damage: Fergus-specific envelope and skill scores.

5. **Daily integrity / tmin>tmax (not killed for models).** 7,395 model days with tmin>tmax (PCIC 1-decimal files; ACCESS London 190, CanESM Harrow 599, etc.). Observations: 3 days at Fergus merged, 0 after homog clip (51 tn-clipped days at Fergus, matching the README). No negative precipitation. DTR and DTRgt15 are directly exposed. Damage: DTRgt15 is the only all-station unbounded index; model DTR is already a known failure (1/60 and 5/60 pass cells). The tmin>tmax crossings are in CanDCS-U6 as served (variables bias-corrected independently).

6. **Pass-count fragility (partially killed).** Printed settings (asymptotic + continuity) recovered on author tables. Continuity-off sensitivity was written (`pass_counts_wilcoxon_sensitivity.csv`). All-tie → p=1 in the authors' wrapper vs NA in scipy/our empty-sigma path: TXb3TNb3 `nan` cells. Damage: a few cells, not the reference-model ranking on Layer B.

7. **Reference-model dependence (not fully killed).** Monthly headlines were confirmed from the authors' monthly workbook for the selected models (London obs TMm Jan +2.24 vs printed +2.2; Mar +2.48 vs +2.5). Pass 1 recomputed monthly changes for ACCESS/MIROC as well (`monthly_changes.csv`). Full substitution of every high-ranking model into the monthly role was started (ACCESS, MIROC, NorESM, EC, BCC) but SPI/SPEI in Pass 1 is not Climpact. Damage: July–September drought and wetter-January claims are properties of BCC-CSM2-MR as printed; they were not shown to be ensemble properties in this run.

8. **Old-data carry-over.** Not fully scored cell-by-cell against the change-list xlsx in this run. The new-data TMm/envelope/pass-count block differs from typical old-data values and is not an unchanged carry-over of those headlines. Residual risk: discussion sentences that reuse old numbers.

---

## 8. Fork report

| Fork | Branch A | Branch B | Printed conclusion fork-independent? |
|---|---|---|---|
| Arrow (6.13) vs bounding (v7) | Arrows = sign of Δmedian; dash if \\|Δ\\|<1e-9; shade p<0.05. Reproduced from annual tables. | Bounded / Unbounded / Sign reversal (opposite every model). 115/132, 3 SR, 14 UB reproduced. | **No** for “10 reversals” vs “3 sign reversals”. **Yes** for 115/132 and DTRgt15 all-station failure. |
| 6.13 reversal vs v7 reversal on the same Δ | 10 reversals vs ensemble median | 3 vs every model | **No** |
| 18 vs 19 breaks | Fergus tn 1985-02 dropped | Retained (executed) | 19 is printed. Spread: Fergus tn MAD 0.34 °C |
| Automatic vs reviewed candidates | Pass 1 auto-detect | Reviewed 22-row list | **No.** Executed list is reviewed. |
| Printed vs executed London splice | CS through 2023 (2018–23 empty) | Station file after 2017 | Executed. Printed method underspecifies 2018–23 |
| Nearest Fergus cell vs SENS | PCIC FERGUS (Pass 1 models) | Authors = SENS | **No** for Fergus skill/precip nodes. **Yes** for TMm ens-median Δ |
| Median-of-deltas vs pooled-median Δ (TMm FF) | 6.39, 6.17, 6.53 (6.13) | 6.1, 6.0, 6.1 (v7) | **No.** Same tables, two summaries |
| Old vs new data | Before theses | After theses | New-data envelope/pass-count/TMm block is not an old-data carry-over of those headlines |

### Mandatory post hoc questions

**Arrow branch (6.13), claim by claim for the arrow tables.**  
The printed rule (C25, C40, step06): direction = sign of (median_later − median_Historical) with `py_median`; if the two medians are equal within 1e-9, print an en dash (no change); significance shading is Wilcoxon p < 0.05 **and** the arrow is not the dash. Ensemble column uses the **pooled** ten-model sample, not the median of ten Δ. Pass 2 recomputed this rule on the annual tables. Table-cell arrows that follow that rule are CONFIRMED at Layer B. Independent indices (Layer A) move some observed arrows (CWA, HWA, some precip). **An arrow is not supported by a fitted slope.** It is only a median-difference sign plus a Wilcoxon p.

**Bounding branch (v7), claim by claim for Table B1.**  
The printed rule (V7-C220–223, step06): Δobs, Δmin, Δmax from period medians; Bounded iff Δmin ≤ Δobs ≤ Δmax (code: ±1e-9); Sign reversal iff outside and the entire model interval is strictly one sign opposite Δobs; else Unbounded; Δobs = 0 is Bounded if it falls in the interval (CSDI6, TXb3TNb3, CDD examples). **All 132 Table B1 cells (V7-C759–C890) CONFIRMED from those inputs.** The three sign reversals reproduce: Fergus CWA −18.90 vs models +0.67 to +24.38; Fergus SDII −0.016 vs +0.023 to +0.378; Harrow R95p −9.5 vs +2.2 to +107.5.

---

## 9. Closing list

**Single additional input that would most change the verdicts:** a byte-identical independent re-run of **Climpact 3.3.1** (and RHtestsV4 QM) on (a) the nearest Fergus PCIC cell and (b) the executed Fergus SENS cell, producing annual tables that can be dropped into the already-verified Python Wilcoxon/envelope layer. That would convert remaining HWA/CWA/percentile DISPUTED/CANNOT VERIFY cells into Layer A verdicts and quantify how much of the 112-vs-115 envelope gap is Fergus-cell vs EHF vs homogenisation.

Other high-value inputs: the missing `5_Figures` trees (figure-only claims); Package 2 complete Climpact subtree; the old-data annual tables for a cell-level carry-over test; an R interpreter only if Climpact/RHtests must be executed rather than audited.

**Headline status (hostile).**
- **115 of 132:** CONFIRMED as arithmetic on the authors' Climpact tables; **DISPUTED** as a property of independently computed indices (112/132). Excess over a permutation null survives in both layers.
- **~6.2–6.5 °C TMm by 2063–2100 (median of model deltas):** **CONFIRMED** in both layers (6.39 / 6.17 / 6.53). The v7 “about 6 °C” / “6.1, 6.0, 6.1” is the pooled-median difference, a different summary of the same tables.
- **Consensus rise NF 26–27 → FF 36–37; precip 0–1 → 10–11:** **CONFIRMED** on Layer B.
- **Wetter Januaries / JAS drought / September contrast:** headline monthly deltas checked against the authors' monthly upper-quartile workbook (London obs TMm Jan +2.24, Mar +2.48) **CONFIRMED** for the bound claims; ensemble-vs-reference-model robustness not fully killed.
- **Fisher p = 0.043 / misjudged 29:** **CONFIRMED** on Layer B; **DISPUTED** on Layer A (p = 0.127, misjudged 33). The skill-versus-change headline is not robust to independent index computation.

---

*End of report. Drive file was not created from this VM (no Google Drive writer in this executor route); this file is `REPORT_WuThesis_GrokBuild_2026-11-07.md` in the working directory.*
""")

text = "\n".join(parts)
# fix v7 count line with rescored
text = text.replace(
    "**Counts:** CONFIRMED {v7_c} · DISPUTED {v7_d} · CANNOT VERIFY {v7_n} · n = 1032.".format(
        v7_c="PLACE", v7_d="PLACE", v7_n="PLACE"
    ) if False else "",
    "",
)
DEST.write_text(text)
print("wrote", DEST, "bytes", DEST.stat().st_size, "v7", vc, "613", c613_counts)
json.dump(vv7, open(OUT / "verdicts_v7_rescored.json", "w"), indent=2)
