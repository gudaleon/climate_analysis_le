import numpy as np, pandas as pd, openpyxl, os, sys
sys.path.insert(0, ".")
from ws1_step11_port import (monthly_cdd, series_files, run_11b, round_py, MON_DIR, V7)

V6 = os.path.expanduser("~/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/"
    "Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data")

# 1) workbook CDD rows vs archived monthly_CDD csvs
prob = []
WBN = {"OBS_LONDON": "OBS_London", "OBS_FERGUS": "OBS_Fergus", "OBS_HARROW": "OBS_Harrow"}
for name in series_files():
    wbname = WBN.get(name, name) + ".xlsx"
    d = pd.read_excel(os.path.join(MON_DIR, wbname))
    d.columns = ["Year", "Month", "Index", "v"]
    cdd = d[d["Index"] == "CDD"].sort_values(["Year", "Month"])
    arch = pd.read_csv(os.path.join(MON_DIR, "monthly_CDD", f"{name}.csv"), dtype={"ym": str})
    av = arch["v"].to_numpy(dtype=float)
    wv = cdd["v"].replace(-99.9, np.nan).to_numpy(dtype=float)
    ok = len(av) == len(wv) and np.all((np.isnan(av) & np.isnan(wv)) | (av == wv))
    if not ok:
        prob.append((name, len(av), len(wv)))
print("workbook CDD rows == archived CDD csvs for all 9 series:", not prob, prob)

# 2) step 11b port vs archived summary workbook (v7 package copy)
tab, _ = run_11b()
def load_sheet(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Monthly (Sec 3.4)"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]
    return pd.DataFrame(rows[1:], columns=hdr)
arch = load_sheet(os.path.join(MON_DIR, "Monthly_upper_quartile_summary.xlsx"))
print("archived sheet rows:", len(arch), "my rows:", len(tab))
key = ["Station", "Source", "Index", "Month"]
m = tab.merge(arch, on=key, suffixes=("_mine", "_arch"), how="outer", indicator=True)
print("merge:", m["_merge"].value_counts().to_dict())
mis = {"median": 0, "p": 0}
worst = []
for _, r in m.iterrows():
    for c in ["Historical", "Present", "Near", "Far"]:
        a = round_py(r[c + "_mine"], 2); b = r[c + "_arch"]
        if (np.isnan(a) and b is None) or (not np.isnan(a) and b is not None and a == float(b)):
            pass
        else:
            mis["median"] += 1; worst.append((r["Station"], r["Index"], r["Month"], c, a, b))
    for cm, ca in [("p_Hist_vs_Present", "Wilcoxon p H vs P (all monthly values)"),
                   ("p_Near_vs_Far", "Wilcoxon p Near vs Far (all monthly values)")]:
        a = round_py(r[cm], 3); b = r[ca]
        if (np.isnan(a) and b is None) or (not np.isnan(a) and b is not None and a == float(b)):
            pass
        else:
            mis["p"] += 1; worst.append((r["Station"], r["Index"], r["Month"], cm, a, b))
print("mismatches at printed precision:", mis, "of", len(m) * 4, "medians and", len(m) * 2, "p-values")
for w in worst[:12]:
    print("  ", w)

# 3) the two packages' summary workbooks compared cell by cell
arch6 = load_sheet(os.path.join(V6, "2_Data", "4_Monthly_analysis", "Monthly_upper_quartile_summary.xlsx"))
same_shape = arch.shape == arch6.shape
diff_cells = 0
if same_shape:
    for c in arch.columns:
        for a, b in zip(arch[c].tolist(), arch6[c].tolist()):
            if not ((a is None and b is None) or a == b):
                diff_cells += 1
print("6.13 vs v7 summary workbook: same shape:", same_shape, "differing cells:", diff_cells)
tab.to_csv("ws1_tab_executed.csv", index=False)
