# Reconciliation pass 2 recompute (Toby, 2026-11-07): Table B1 and Table C1 of the v7 thesis,
# recomputed independently in Python from the packages' 3_Annual_index_tables workbooks,
# following the executed rules in the authors' step06_change_test.R and step08_projections.R
# (which state the same classification rule as thesis section 2.8 for B1, and the executed
# pool composition for C1). Quantiles use R type 7 (= numpy 'linear').
import re, csv, math
import numpy as np
import openpyxl

PKG = ("drive_mirror/JW_October_2026/Thesis_v7_defence_framework_new_data-2/"
       "Thesis_v7_defence_framework_new_data/2_Data/3_Annual_index_tables")
INDEX_NAME = dict(csdi="CSDI6", csdi3="CSDI3", wsdi="WSDI6", wsdi3="WSDI3", fd="FD", id="ID",
    su="SU", tr="TR", tnn="TNn", tnx="TNx", txx="TXx", txn="TXn", txm="TXm", tmm="TMm", tnm="TNm",
    tn10p="TN10p", tn90p="TN90p", tx10p="TX10p", tx90p="TX90p", dtr="DTR", dtrgt15="DTRgt15",
    gddgrow10="GDDgrow10", txb3tnb3="TXb3TNb3", txge30="TXge30", txgt50p="TXgt50p",
    tnltm20="TNltm20", gsl="GSL", cwa="CWA", cwf="CWF", hwa="HWA", hwf="HWF", prcptot="PRCPTOT",
    r10mm="R10mm", r20mm="R20mm", rx1day="RX1day", rx3day="RX3day", rx5day="RX5day", sdii="SDII",
    r95p="R95p", r95ptot="R95pTOT", r99p="R99p", r99ptot="R99pTOT", cdd="CDD", cwd="CWD")
MODELS = ["ACCESS","BCC","CanESM","CNRM","EC","GFDL","INM","MIROC","MRI","NorESM"]
PERIODS = {"Hist": (1950,1986), "Pres": (1987,2023), "Near": (2024,2062), "Far": (2063,2100)}
STATIONS = ["London","Fergus","Harrow"]

def load(st):
    wb = openpyxl.load_workbook(f"{PKG}/All_{st}_observed_and_10_models_1950-2100.xlsx",
                                read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    data = {}  # index -> col -> {year: val}
    for row in ws.iter_rows(min_row=2, values_only=True):
        year, idx = row[0], INDEX_NAME[str(row[1]).strip().lower()]
        d = data.setdefault(idx, {})
        for j, col in enumerate(["Observed"] + MODELS):
            v = row[2 + j]
            if v is None or (isinstance(v, (int, float)) and float(v) == -99.9):
                continue
            d.setdefault(col, {})[int(year)] = float(v)
    return data

def per(data, idx, col, p):
    lo, hi = PERIODS[p]
    return np.array([v for y, v in data[idx].get(col, {}).items() if lo <= y <= hi], dtype=float)

def q7(v, ps=(0.25, 0.5, 0.75)):
    return np.quantile(v, list(ps), method="linear") if len(v) else np.array([np.nan]*3)

# ---------- Table B1 (step06 rule = thesis 2.8 rule) ----------
def classify_b1(o, lo, hi):
    if math.isnan(o) or math.isnan(lo):
        return "NA"
    if lo - 1e-9 <= o <= hi + 1e-9:
        return "Bounded"
    if (lo > 0 and o < 0) or (hi < 0 and o > 0):
        return "Sign Reversal"
    return "Unbounded"

b1 = {}
for st in STATIONS:
    data = load(st)
    for idx in data:
        def dmed(col):
            a, b = per(data, idx, col, "Pres"), per(data, idx, col, "Hist")
            return float(np.median(a) - np.median(b)) if len(a) and len(b) else float("nan")
        dm = [dmed(m) for m in MODELS]
        o = dmed("Observed")
        lo, hi = min(dm), max(dm)
        b1[(st, idx)] = dict(dobs=o, dmin=lo, dmax=hi, cls=classify_b1(o, lo, hi))

# ---------- Table C1 (step08 executed rule; plus models-only branch) ----------
def pooled_stats(v):
    q1, med, q3 = q7(v)
    iqr = q3 - q1
    out = int(np.sum((v < q1 - 1.5 * iqr) | (v > q3 + 1.5 * iqr)))
    return med, q1, q3, out

def c1_label(h, f):
    dm = f["med"] - h["med"]
    ih, iff = h["q3"] - h["q1"], f["q3"] - f["q1"]
    sh = "Increase" if dm > 0 else ("Decrease" if dm < 0 else "No Shift")
    if ih == 0 and iff == 0:
        sp = "Stable Spread"
    elif ih == 0:
        sp = "Spread Expanded"
    else:
        ratio = iff / ih
        sp = "Spread Contracted" if ratio < 0.8 else ("Spread Expanded" if ratio > 1.25 else "Stable Spread")
    return f"{sh} ({sp})"

c1 = {}
for st in STATIONS:
    data = load(st)
    for idx in data:
        for branch in ("mixed", "models"):
            stats = {}
            for p in PERIODS:
                cols = (["Observed"] + MODELS) if (branch == "mixed" and p in ("Hist", "Pres")) else MODELS
                v = np.concatenate([per(data, idx, c, p) for c in cols]) if cols else np.array([])
                med, q1, q3, out = pooled_stats(v)
                stats[p] = dict(med=float(med), q1=float(q1), q3=float(q3), out=out, n=len(v))
            stats["label"] = c1_label(stats["Hist"], stats["Far"])
            c1[(st, idx, branch)] = stats

# ---------- Printed values parsed from the claims inventory ----------
inv = open("thesis/CLAIMS_INVENTORY_v7.md", encoding="utf-8").read().splitlines()
printed_b1, printed_c1 = {}, {}
for ln in inv:
    m = re.search(r"V7-C(\d+)\.", ln)
    if not m:
        continue
    n = int(m.group(1))
    if 759 <= n <= 890:
        mm = re.search(r"for (\w+) station index (\w+).*?observed shift \(Δobs\) of ([-\d.]+), a model minimum \(Δmin\) of ([-\d.]+) and a model maximum \(Δmax\) of ([-\d.]+).*?recorded as (TRUE|FALSE), a historical validation outcome of (\w+(?: \w+)?),", ln)
        if mm:
            printed_b1[n] = dict(claim=f"V7-C{n}", station=mm.group(1), index=mm.group(2),
                                 dobs=float(mm.group(3)), dmin=float(mm.group(4)), dmax=float(mm.group(5)),
                                 cls=mm.group(7))
        else:
            print("B1 PARSE FAIL", n, ln[:200])
    if 892 <= n <= 1023:
        mm = re.search(r"for (\w+) station index (\w+)", ln)
        ents = re.findall(r"\"([-\d.]+) \(([-\d.]+) to ([-\d.]+)\) \[Outliers: (\d+)\]\"", ln)
        lab = re.search(r"printed as \"((?:Increase|Decrease|No Shift) \((?:Spread Expanded|Spread Contracted|Stable Spread)\))\"", ln)
        if mm and len(ents) == 4 and lab:
            idx = {"R99pTO": "R99pTOT", "R95pTO": "R95pTOT"}.get(mm.group(2), mm.group(2))
            printed_c1[n] = dict(claim=f"V7-C{n}", station=mm.group(1), index=idx,
                                 periods=[dict(med=float(e[0]), q1=float(e[1]), q3=float(e[2]), out=int(e[3])) for e in ents],
                                 label=lab.group(1))
        else:
            print("C1 PARSE FAIL", n, len(ents), bool(lab), ln[:200])

print("parsed B1:", len(printed_b1), " parsed C1:", len(printed_c1))

# ---------- Compare B1 ----------
with open("reports/pass2_b1_compare.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["claim","station","index","printed_dobs","mine_dobs","printed_dmin","mine_dmin",
                "printed_dmax","mine_dmax","printed_cls","mine_cls","class_match","values_match_2dp"])
    tot_mine, tot_print = {}, {}
    nmatch = 0
    for n in sorted(printed_b1):
        p = printed_b1[n]; r = b1[(p["station"], p["index"])]
        cm = (p["cls"] == r["cls"])
        nmatch += cm
        vm = all(abs(round(r[k], 2) - p[k]) < 1e-9 for k in ("dobs", "dmin", "dmax"))
        tot_mine[r["cls"]] = tot_mine.get(r["cls"], 0) + 1
        tot_print[p["cls"]] = tot_print.get(p["cls"], 0) + 1
        w.writerow([p["claim"], p["station"], p["index"], p["dobs"], round(r["dobs"], 4), p["dmin"],
                    round(r["dmin"], 4), p["dmax"], round(r["dmax"], 4), p["cls"], r["cls"], cm, vm])
print("B1 class matches:", nmatch, "/132 ; my totals:", tot_mine, " printed totals:", tot_print)

# ---------- Compare C1 (both branches) ----------
def elem_diffs(p, s):
    d = []
    for i, pn in enumerate(["Hist", "Pres", "Near", "Far"]):
        for k in ("med", "q1", "q3"):
            d.append(abs(round(s[pn][k], 1) - p["periods"][i][k]))
        d.append(abs(s[pn]["out"] - p["periods"][i]["out"]))
    d.append(0 if s["label"] == p["label"] else 1)
    return d

with open("reports/pass2_c1_compare.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["claim","station","index","mixed_elems_off","mixed_maxdiff","mixed_label_ok",
                "models_elems_off","models_maxdiff","models_label_ok","off_elements_mixed"])
    full = {"mixed": 0, "models": 0}
    for n in sorted(printed_c1):
        p = printed_c1[n]
        row = [p["claim"], p["station"], p["index"]]
        details = {}
        for branch in ("mixed", "models"):
            s = c1[(p["station"], p["index"], branch)]
            d = elem_diffs(p, s)
            off = sum(1 for x in d if x > 1e-9)
            if off == 0:
                full[branch] += 1
            row += [off, max(d[:16]), d[16] == 0]
            details[branch] = (d, s)
        names = []
        d, s = details["mixed"]
        keys = [f"{pn}_{k}" for pn in ("Hist","Pres","Near","Far") for k in ("med","q1","q3","out")] + ["label"]
        for kname, dv in zip(keys, d):
            if dv > 1e-9:
                names.append(kname)
        row.append(";".join(names))
        w.writerow(row)
print("C1 rows reproduced in full: mixed =", full["mixed"], "/132 ; models-only =", full["models"], "/132")
