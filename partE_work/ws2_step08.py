import numpy as np, pandas as pd, re, os, sys
sys.path.insert(0, ".")
from ws1_step11_port import quantile7, round_py, wilcox_p

V7 = os.path.expanduser("~/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/"
    "Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data")
ANN = os.path.join(V7, "2_Data", "3_Annual_index_tables")
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
TEMP = {"CSDI6","CSDI3","WSDI6","WSDI3","FD","ID","SU","TR","TNn","TNx","TXx","TXn","TXm","TMm","TNm",
        "TN10p","TN90p","TX10p","TX90p","DTR","DTRgt15","GDDgrow10","TXb3TNb3","TXge30","TXgt50p",
        "TNltm20","GSL","CWA","CWF","HWA","HWF"}

def load_annual(st):
    d = pd.read_excel(os.path.join(ANN, f"All_{st}_observed_and_10_models_1950-2100.xlsx"))
    d["Index"] = d["Index"].astype(str).str.strip().str.lower().map(INDEX_NAME)
    return d.replace(-99.9, np.nan)

def per(g, col, p):
    a, b = PERIODS[p]
    v = g.loc[(g["Year"] >= a) & (g["Year"] <= b), col]
    return v.dropna().to_numpy(dtype=float)

def pooled(g, cols, p):
    a, b = PERIODS[p]
    v = g.loc[(g["Year"] >= a) & (g["Year"] <= b), cols].to_numpy(dtype=float).ravel()
    v = v[~np.isnan(v)]
    q1, med, q3 = quantile7(v, 0.25), quantile7(v, 0.5), quantile7(v, 0.75)
    iqr = q3 - q1
    out = int(np.sum((v < q1 - 1.5 * iqr) | (v > q3 + 1.5 * iqr)))
    return med, q1, q3, out

def c1(x, models_only=False):
    rows = []
    for k in sorted(x["Index"].unique()):
        g = x[x["Index"] == k]
        r = {"Index": k}
        for p in PERIODS:
            cols = MODELS if (models_only or p in ("Near", "Far")) else ["Observed"] + MODELS
            med, q1, q3, out = pooled(g, cols, p)
            r[f"{p}_median"], r[f"{p}_Q1"], r[f"{p}_Q3"], r[f"{p}_outliers"] = med, q1, q3, out
        r["delta_m"] = r["Far_median"] - r["Hist_median"]
        ih, iff = r["Hist_Q3"] - r["Hist_Q1"], r["Far_Q3"] - r["Far_Q1"]
        r["IQR_ratio"] = (iff / ih) if ih > 0 else (np.nan if iff > 0 else 1.0)
        sh = "Increase" if r["delta_m"] > 0 else ("Decrease" if r["delta_m"] < 0 else "No Shift")
        if ih == 0 and iff == 0: sp = "Stable Spread"
        elif ih == 0: sp = "Spread Expanded"
        elif r["IQR_ratio"] < 0.8: sp = "Spread Contracted"
        elif r["IQR_ratio"] > 1.25: sp = "Spread Expanded"
        else: sp = "Stable Spread"
        r["label"] = f"{sh} ({sp})"
        rows.append(r)
    return pd.DataFrame(rows)

X = {s: load_annual(s) for s in STATIONS}
E = {s: c1(X[s]) for s in STATIONS}                 # executed branch
M = {s: c1(X[s], models_only=True) for s in STATIONS}

# ---- validation: parse the 132 printed Table C1 rows from the v7 inventory
inv = open(os.path.expanduser("~/workspace/jeremy_wu_redteam/thesis/CLAIMS_INVENTORY_v7.md")).read()
pat = re.compile(r"\*\*(V7-C(8[9][2-9]|9\d\d|10[01]\d|102[0-3]))\.\*\*.*?Table C1 row \((\w+), (\w+)\): "
                 r"Historical: (-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]; "
                 r"Present: (-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]; "
                 r"Near Future: (-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]; "
                 r"Far Future: (-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]; "
                 r"Overall Shift: ([^.]+)\.", re.S)
printed = {}
for mm in pat.finditer(inv):
    printed[(mm.group(3), mm.group(4))] = {"claim": "V7-C" + mm.group(2), "groups": mm.groups(), "label": mm.group(22)}
print("printed C1 rows parsed:", len(printed))
bad = []
for (st, idx), pr in printed.items():
    row = E[st][E[st]["Index"] == idx].iloc[0]
    g = pr["groups"]
    vals = [float(g[i]) for i in (5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19)]
    mine = []
    for p in ["Hist", "Pres", "Near", "Far"]:
        mine += [row[f"{p}_median"], row[f"{p}_Q1"], row[f"{p}_Q3"]]
    outs_p = [int(g[i]) for i in (8, 12, 16, 20)]
    outs_m = [int(row[f"{p}_outliers"]) for p in ["Hist", "Pres", "Near", "Far"]]
    ok = all(round_py(a, 1) == b for a, b in zip(mine, vals)) and outs_p == outs_m and row["label"] == pr["label"]
    if not ok:
        bad.append((pr["claim"], st, idx, pr["label"], row["label"]))
print("executed-branch rows mismatching printed Table C1:", len(bad))
for b in bad: print("   ", b)

# ---- models-only diff at printed precision
elem_off, label_changes = 0, []
for st in STATIONS:
    e = E[st].set_index("Index"); m = M[st].set_index("Index")
    for idx in e.index:
        for p in ["Hist", "Pres", "Near", "Far"]:
            for s_ in ["median", "Q1", "Q3"]:
                if round_py(e.loc[idx, f"{p}_{s_}"], 1) != round_py(m.loc[idx, f"{p}_{s_}"], 1):
                    elem_off += 1
            if int(e.loc[idx, f"{p}_outliers"]) != int(m.loc[idx, f"{p}_outliers"]):
                elem_off += 1
        if e.loc[idx, "label"] != m.loc[idx, "label"]:
            label_changes.append((st, idx, e.loc[idx, "label"], m.loc[idx, "label"]))
print("elements differing at printed precision (16 per row: 4 stats x 4 periods):", elem_off)
print("Overall Shift label changes:", label_changes)

# ---- consensus rerun (branch-independent)
for p in ["Near", "Far"]:
    line = []
    for s in STATIONS:
        x = X[s]; ok = {}
        for k in sorted(x["Index"].unique()):
            g = x[x["Index"] == k]
            sig = []
            for mdl in MODELS:
                a, b = per(g, mdl, "Hist"), per(g, mdl, p)
                pv = wilcox_p(a, b)
                sig.append(np.sign(np.median(b) - np.median(a)) if (not np.isnan(pv) and pv < 0.05) else 0)
            ok[k] = max(sig.count(1), sig.count(-1)) >= 8
        line.append((s, sum(ok.values()), sum(v for k, v in ok.items() if k in TEMP),
                     sum(v for k, v in ok.items() if k not in TEMP)))
    print(p, "consensus (station, all, temperature, precipitation):", line)

for s in STATIONS:
    E[s].to_csv(f"ws2_c1_executed_{s}.csv", index=False)
    M[s].to_csv(f"ws2_c1_models_{s}.csv", index=False)

# ---- section 3.2.2 claim numbers, both branches
def show(idx, note):
    print(f"\n-- {idx} ({note})")
    for s in STATIONS:
        e = E[s][E[s]["Index"] == idx].iloc[0]; m = M[s][M[s]["Index"] == idx].iloc[0]
        f = lambda r: (f"H {r.Hist_median:.2f} P {r.Pres_median:.2f} N {r.Near_median:.2f} F {r.Far_median:.2f} "
                       f"dN {r.Near_median-r.Hist_median:+.2f} dF {r.delta_m:+.2f} [{r.label}]")
        print(f"   {s:7s} exec: {f(e)}")
        print(f"   {s:7s} modl: {f(m)}")
for idx, note in [("TMm", "C401-C403"), ("SU", "C404"), ("TXge30", "C405/C406"), ("TR", "C407"),
                  ("GDDgrow10", "C408/C409"), ("FD", "C410"), ("PRCPTOT", "C412"), ("RX1day", "C413"),
                  ("R95p", "C414"), ("R99p", "C415"), ("SDII", "C416"), ("CDD", "C417"),
                  ("DTR", "C418"), ("RX3day", "C419"), ("ID", "label change"), ("CWA", "C420")]:
    show(idx, note)
