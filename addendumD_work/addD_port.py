"""Addendum D port: does the v7 step 08 pooling defect run in the 6.13 chain?

Reproduces the pooled quantities archived in the 6.13 results workbook
(4_Results/Thesis_6.13_results_new_data.xlsx) under two pooling branches,
from the 6.13 package's own annual index tables:

  Branch E (the branch the 6.13 code executes, per step06/step09 source):
      every pool is the ten models alone, in every window.
  Branch D (the defect branch, mirroring v7's executed step 08):
      pools in the Historical and Present windows are the observations
      folded together with the ten models; Near/Far pools are models alone
      (the observation series has no values in those windows).

Pooled products reproduced (the only pooled quantities in the workbook):
  1. step09 period medians, sheet "Period medians (Sec 3.3)":
     Pooled Historical / Present / Near / Far medians, 132 rows x 4 windows.
     Workbook rounding: py_round (round half to even on the exact binary
     value, as C printf) to 2 decimals for the pooled columns.
  2. step06 Ensemble rows, sheet "Changes long (Δ, p)":
     Δ median and Wilcoxon p for Hist->Present / Near / Far, and the two
     sample sizes. Workbook rounding: py_round to 4 decimals.
  3. step08 projected pooled Δ, sheet "Projected Δ (Sec 3.2.2)":
     Near and Far pooled Δ (the step06 Ensemble Δ at coarser precision).
     Workbook rounding: np_round (scale, round half to even, unscale), 2 dp.

Median is the numpy median, which is what the authors' py_median computes.
Wilcoxon p reuses the Part E port's validated wilcox_p (normal
approximation, continuity correction, average ranks for ties), which
reproduced R wilcox.test(exact = FALSE, correct = TRUE) in Part E.
"""
import importlib.util, math, os, sys
import numpy as np
import pandas as pd

WS = os.path.expanduser("~/workspace/jeremy_wu_redteam")
PKG = os.path.join(WS, "drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2",
                   "Thesis_6.13_method_new_data")
ANN = os.path.join(PKG, "2_Data", "3_Annual_index_tables")
WB = os.path.join(PKG, "4_Results", "Thesis_6.13_results_new_data.xlsx")
OUT = os.path.join(WS, "reports", "addendumD_work")

spec = importlib.util.spec_from_file_location(
    "ws1", os.path.join(WS, "reports", "partE_work", "ws1_step11_port.py"))
ws1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ws1)
wilcox_p = ws1.wilcox_p
round_py = ws1.round_py

STATIONS = ["London", "Fergus", "Harrow"]
MODELS = ["ACCESS", "BCC", "CanESM", "CNRM", "EC", "GFDL", "INM", "MIROC", "MRI", "NorESM"]
PERIODS = {"Hist": (1950, 1986), "Pres": (1987, 2023), "Near": (2024, 2062), "Far": (2063, 2100)}
INDEX_NAME = dict(csdi="CSDI6", csdi3="CSDI3", wsdi="WSDI6", wsdi3="WSDI3", fd="FD", id="ID", su="SU",
    tr="TR", tnn="TNn", tnx="TNx", txx="TXx", txn="TXn", txm="TXm", tmm="TMm", tnm="TNm",
    tn10p="TN10p", tn90p="TN90p", tx10p="TX10p", tx90p="TX90p", dtr="DTR", dtrgt15="DTRgt15",
    gddgrow10="GDDgrow10", txb3tnb3="TXb3TNb3", txge30="TXge30", txgt50p="TXgt50p", tnltm20="TNltm20",
    gsl="GSL", cwa="CWA", cwf="CWF", hwa="HWA", hwf="HWF", prcptot="PRCPTOT", r10mm="R10mm",
    r20mm="R20mm", rx1day="RX1day", rx3day="RX3day", rx5day="RX5day", sdii="SDII", r95p="R95p",
    r95ptot="R95pTOT", r99p="R99p", r99ptot="R99pTOT", cdd="CDD", cwd="CWD")
ORDER = ["SDII", "RX1day", "RX3day", "RX5day", "R99pTOT", "R99p", "R95pTOT", "R95p", "R10mm", "R20mm",
         "PRCPTOT", "CWD", "CDD", "CSDI6", "CSDI3", "DTR", "DTRgt15", "FD", "GDDgrow10", "ID", "SU",
         "TMm", "TN10p", "TN90p", "TNltm20", "TNm", "TR", "TX10p", "TX90p", "TXb3TNb3", "TXge30",
         "TXgt50p", "TXm", "TXn", "WSDI6", "WSDI3", "CWA", "CWF", "GSL", "HWA", "HWF", "TNn", "TNx", "TXx"]


def np_round(x, d):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    return float(np.rint(x * 10.0 ** d) / 10.0 ** d)


def load_annual(st):
    d = pd.read_excel(os.path.join(ANN, f"All_{st}_observed_and_10_models_1950-2100.xlsx"))
    d["Index"] = d["Index"].astype(str).str.strip().str.lower().map(INDEX_NAME)
    return d.replace(-99.9, np.nan)


def per(g, col, p):
    a, b = PERIODS[p]
    v = g.loc[(g["Year"] >= a) & (g["Year"] <= b), col]
    return v.dropna().to_numpy(dtype=float)


def pool(g, p, branch):
    """The pooled sample of one window under a branch. Branch E: ten models.
    Branch D: observations folded in, in the Hist and Pres windows only."""
    v = np.concatenate([per(g, m, p) for m in MODELS]) if any(len(per(g, m, p)) for m in MODELS) \
        else np.array([], dtype=float)
    if branch == "D" and p in ("Hist", "Pres"):
        v = np.concatenate([per(g, "Observed", p), v])
    return v


def med(v):
    return float(np.median(v)) if len(v) else np.nan


X = {s: load_annual(s) for s in STATIONS}

# ---------------------------------------------------------------- step 09
def step09(branch):
    rows = []
    for st in STATIONS:
        x = X[st]
        for k in ORDER:
            g = x[x["Index"] == k]
            r = {"Station": st, "Index": k}
            for p in PERIODS:
                r[f"Pooled {p}"] = med(pool(g, p, branch))
            mf = [med(per(g, m, "Far")) for m in MODELS]
            mf = [v for v in mf if not np.isnan(v)]
            r["Lowest model median Far"] = min(mf) if mf else np.nan
            r["Highest model median Far"] = max(mf) if mf else np.nan
            r["Obs Hist"] = med(per(g, "Observed", "Hist"))
            r["Obs Pres"] = med(per(g, "Observed", "Pres"))
            rows.append(r)
    return pd.DataFrame(rows)

# ---------------------------------------------------------------- step 06
def step06_ensemble(branch):
    rows = []
    for st in STATIONS:
        x = X[st]
        for k in ORDER:
            g = x[x["Index"] == k]
            h = pool(g, "Hist", branch)
            for later in ("Pres", "Near", "Far"):
                f = pool(g, later, branch)
                d = med(f) - med(h) if len(h) and len(f) else np.nan
                p = wilcox_p(h, f) if len(h) and len(f) else np.nan
                rows.append({"Station": st, "Index": k, "Comp": later,
                             "nH": len(h), "nL": len(f), "d": d, "p": p})
    return pd.DataFrame(rows)

E09, D09 = step09("E"), step09("D")
E06, D06 = step06_ensemble("E"), step06_ensemble("D")
E09.to_csv(os.path.join(OUT, "addD_step09_branchE.csv"), index=False)
D09.to_csv(os.path.join(OUT, "addD_step09_branchD.csv"), index=False)
E06.to_csv(os.path.join(OUT, "addD_step06ens_branchE.csv"), index=False)
D06.to_csv(os.path.join(OUT, "addD_step06ens_branchD.csv"), index=False)

# ---------------------------------------------------------------- workbook
wb = pd.read_excel(WB, sheet_name=None)
for name in wb:
    print("sheet:", repr(name), wb[name].shape)

def is_missing(v):
    return v is None or (isinstance(v, float) and np.isnan(v)) or \
        (isinstance(v, str) and v.strip() in ("n/a", "", "NA", "nan"))

def eq_printed(mine, archived, rule, nd):
    """True when my full-precision value rounds (by the workbook's own rule)
    to the archived printed value; missing equals missing."""
    if is_missing(archived):
        return mine is None or (isinstance(mine, float) and np.isnan(mine))
    if mine is None or (isinstance(mine, float) and np.isnan(mine)):
        return False
    return rule(float(mine), nd) == float(archived)

# ---- 1. period medians sheet
pm = wb["Period medians (Sec 3.3)"]
pm_cols = {c: c for c in pm.columns}
print("period-medians columns:", list(pm.columns))
win_of_col = {"Pooled Historical": "Hist", "Pooled Present": "Pres",
              "Pooled Near": "Near", "Pooled Far": "Far"}
res09 = {}
for branch, mine_df in (("E", E09), ("D", D09)):
    mine = mine_df.set_index(["Station", "Index"])
    for col, w in win_of_col.items():
        diffs, ties = [], []
        for _, row in pm.iterrows():
            key = (row["Station"], row["Index"])
            v = mine.loc[key, f"Pooled {w}"]
            arch = row[col]
            if not eq_printed(v, arch, round_py, 2):
                diffs.append((key, v, arch))
            elif not is_missing(arch) and abs(float(v) - float(arch)) > 0.005 + 1e-12:
                ties.append((key, v, arch))
        res09[(branch, w)] = diffs
        print(f"step09 branch {branch} window {w}: {132 - len(diffs)}/132 reproduced "
              f"at printed precision; differing: {len(diffs)}")
        for t in diffs[:6]:
            print("    diff:", t)
# branch-independent sanity: obs medians and Far extremes of branch E
mine = E09.set_index(["Station", "Index"])
for col, mycol in (("Obs Historical", "Obs Hist"), ("Obs Present", "Obs Pres"),
                   ("Lowest model median Far", "Lowest model median Far"),
                   ("Highest model median Far", "Highest model median Far")):
    bad = [( (r["Station"], r["Index"]), mine.loc[(r["Station"], r["Index"]), mycol], r[col])
           for _, r in pm.iterrows()
           if not eq_printed(mine.loc[(r["Station"], r["Index"]), mycol], r[col], np_round, 2)]
    print(f"step09 sanity {col}: differing {len(bad)}", bad[:4])

# ---- 2. changes-long Ensemble rows
cl = wb["Changes long (\u0394, p)"]
print("changes-long columns:", list(cl.columns))
ens = cl[cl["Source"] == "Ensemble"].copy()
comp_of = {"Hist\u2192Present": "Pres", "Hist\u2192Near": "Near", "Hist\u2192Far": "Far"}
ens["Comp"] = ens["Comparison"].map(comp_of)
print("Ensemble rows in workbook:", len(ens))
for branch, mine_df in (("E", E06), ("D", D06)):
    mine = mine_df.set_index(["Station", "Index", "Comp"])
    for comp in ("Pres", "Near", "Far"):
        sub = ens[ens["Comp"] == comp]
        nd = n_p = n_n = 0
        examples = []
        for _, r in sub.iterrows():
            m = mine.loc[(r["Station"], r["Index"], comp)]
            if not eq_printed(m["d"], r["\u0394 median"], round_py, 4):
                nd += 1; examples.append(("d", r["Station"], r["Index"], m["d"], r["\u0394 median"]))
            if not eq_printed(m["p"], r["Wilcoxon p"], round_py, 4):
                n_p += 1; examples.append(("p", r["Station"], r["Index"], m["p"], r["Wilcoxon p"]))
            if int(m["nH"]) != int(r["n Historical"]) or int(m["nL"]) != int(r["n later"]):
                n_n += 1; examples.append(("n", r["Station"], r["Index"],
                                           (int(m["nH"]), int(m["nL"])),
                                           (int(r["n Historical"]), int(r["n later"]))))
        print(f"step06 branch {branch} comp {comp}: of 132 rows, Δ differing {nd}, "
              f"p differing {n_p}, n differing {n_n}")
        for e in examples[:4]:
            print("    ", e)

# ---- 3. projected pooled Δ
pj = wb["Projected \u0394 (Sec 3.2.2)"]
print("projected columns:", list(pj.columns))
pool_cols = [c for c in pj.columns if "pooled" in str(c)]
print("pooled columns:", pool_cols)
for branch, mine_df in (("E", E06), ("D", D06)):
    mine = mine_df.set_index(["Station", "Index", "Comp"])
    for col in pool_cols:
        comp = "Near" if str(col).startswith("Near") else "Far"
        nd = 0; examples = []
        for _, r in pj.iterrows():
            v = mine.loc[(r["Station"], r["Index"], comp), "d"]
            if not eq_printed(v, r[col], np_round, 2):
                nd += 1; examples.append((r["Station"], r["Index"], v, r[col]))
        print(f"step08 branch {branch} {col}: {132 - nd}/132 reproduced; differing {nd}")
        for e in examples[:4]:
            print("    ", e)

# ---- branch D vs branch E at full precision (the size of the counterfactual)
d09 = 0
for w in PERIODS:
    a = E09[f"Pooled {w}"].to_numpy(dtype=float); b = D09[f"Pooled {w}"].to_numpy(dtype=float)
    both = ~np.isnan(a) & ~np.isnan(b)
    d09 += int(np.sum(np.abs(a[both] - b[both]) > 0))
    print(f"full precision, step09 pooled medians differing E vs D, window {w}: "
          f"{int(np.sum(np.abs(a[both] - b[both]) > 0))} of {int(both.sum())} defined")
for comp in ("Pres", "Near", "Far"):
    a = E06[E06["Comp"] == comp]; b = D06[D06["Comp"] == comp]
    md = np.abs(a["d"].to_numpy(dtype=float) - b["d"].to_numpy(dtype=float))
    mp = np.abs(a["p"].to_numpy(dtype=float) - b["p"].to_numpy(dtype=float))
    print(f"full precision, step06 Ensemble differing E vs D, comp {comp}: "
          f"Δ {int(np.sum(md > 0))}, p {int(np.sum(mp > 0))} of {len(a)}")
print("done")
