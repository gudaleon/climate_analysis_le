import numpy as np, pandas as pd, re, os, sys
sys.path.insert(0, ".")
from ws1_step11_port import round_py

inv = open(os.path.expanduser("~/workspace/jeremy_wu_redteam/thesis/CLAIMS_INVENTORY_v7.md")).read()
pat = re.compile(r"\*\*(V7-C\d+)\.\*\* Table C1 reports for (\w+) station index (\w+) the "
    r"Historical \(1950–1986\) entry printed as \"(-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]\", "
    r"the Present \(1987–2023\) entry printed as \"(-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]\", "
    r"the Near-Future \(2024–2062\) entry printed as \"(-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]\", "
    r"the Far-Future \(2063–2100\) entry printed as \"(-?[\d.]+) \((-?[\d.]+) to (-?[\d.]+)\) \[Outliers: (\d+)\]\", "
    r"and the Overall Shift \(Historical to Far-Future\) printed as \"([^\"]+)\"")
printed = {}
for mm in pat.finditer(inv):
    idxname = {"R99pTO": "R99pTOT", "CSDI": "CSDI6"}.get(mm.group(3), mm.group(3))
    printed[(mm.group(2), idxname)] = mm
print("printed C1 rows parsed:", len(printed))

E = {s: pd.read_csv(f"ws2_c1_executed_{s}.csv").set_index("Index") for s in ["London", "Fergus", "Harrow"]}
M = {s: pd.read_csv(f"ws2_c1_models_{s}.csv").set_index("Index") for s in ["London", "Fergus", "Harrow"]}
bad = []
for (st, idx), mm in printed.items():
    g = mm.groups()
    row = E[st].loc[idx]
    vals = [float(g[i]) for i in (3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 16, 17)]
    mine = []
    for p in ["Hist", "Pres", "Near", "Far"]:
        mine += [row[f"{p}_median"], row[f"{p}_Q1"], row[f"{p}_Q3"]]
    outs_p = [int(g[i]) for i in (6, 10, 14, 18)]
    outs_m = [int(row[f"{p}_outliers"]) for p in ["Hist", "Pres", "Near", "Far"]]
    ok = all(round_py(a, 1) == b for a, b in zip(mine, vals)) and outs_p == outs_m and row["label"] == g[19]
    if not ok:
        bad.append((g[0], st, idx, g[19], row["label"],
                    [(a, round_py(a, 1), b) for a, b in zip(mine, vals) if round_py(a, 1) != b], outs_p, outs_m))
print("executed-branch mismatches vs printed Table C1:", len(bad))
for b in bad: print("   ", b)

# element-count reconciliation with pass 2
p2 = pd.read_csv(os.path.expanduser("~/workspace/jeremy_wu_redteam/reports/pass2_c1_compare.csv"))
tot = 0; diffs = []
for _, r in p2.iterrows():
    st, idx = r["station"], r["index"]
    e, m = E[st].loc[idx], M[st].loc[idx]
    n = 0
    for p in ["Hist", "Pres", "Near", "Far"]:
        for c in ["median", "Q1", "Q3"]:
            if round_py(e[f"{p}_{c}"], 1) != round_py(m[f"{p}_{c}"], 1): n += 1
        if int(e[f"{p}_outliers"]) != int(m[f"{p}_outliers"]): n += 1
    tot += n
    if n != int(r["models_elems_off"]):
        diffs.append((r["claim"], st, idx, int(r["models_elems_off"]), n, r["models_maxdiff"]))
print("my models-only element count:", tot, " pass2:", int(p2.models_elems_off.sum()))
for d in diffs: print("   count differs:", d)

# full-precision deltas for the section 3.2.2 precipitation claims
print("\nfull-precision Far-minus-Historical median changes (executed | models-only):")
for idx in ["PRCPTOT", "RX1day", "R95p", "R99p", "SDII", "GDDgrow10", "TMm"]:
    for st in ["London", "Harrow", "Fergus"]:
        e, m = E[st].loc[idx], M[st].loc[idx]
        print(f"   {idx:9s} {st:7s} {e.delta_m:10.4f} | {m.delta_m:10.4f}   "
              f"printed-precision: {round_py(e.delta_m,1)} | {round_py(m.delta_m,1)}")
