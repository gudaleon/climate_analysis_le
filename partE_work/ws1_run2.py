import numpy as np, pandas as pd, openpyxl, os, sys
sys.path.insert(0, ".")
from ws1_step11_port import run_11b, round_py, MON_DIR

def ismiss(x):
    return x is None or (isinstance(x, float) and np.isnan(x))

def load_sheet(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Monthly (Sec 3.4)"]
    rows = list(ws.iter_rows(values_only=True))
    return pd.DataFrame(rows[1:], columns=rows[0])

tab = pd.read_csv("ws1_tab_executed.csv")
arch = load_sheet(os.path.join(MON_DIR, "Monthly_upper_quartile_summary.xlsx"))
key = ["Station", "Source", "Index", "Month"]
m = tab.merge(arch, on=key, suffixes=("_mine", "_arch"), how="outer", indicator=True)
print("merge:", m["_merge"].value_counts().to_dict())
med_bad, p_bad, examples = 0, 0, []
for _, r in m.iterrows():
    for c in ["Historical", "Present", "Near", "Far"]:
        a = round_py(r[c + "_mine"], 2); b = r[c + "_arch"]
        if ismiss(a) and ismiss(b):
            continue
        if not ismiss(a) and not ismiss(b) and a == float(b):
            continue
        med_bad += 1
        if len(examples) < 10: examples.append((r["Station"], r["Source"][:12], r["Index"], r["Month"], c, a, b))
    for cm, ca in [("p_Hist_vs_Present", "Wilcoxon p H vs P (all monthly values)"),
                   ("p_Near_vs_Far", "Wilcoxon p Near vs Far (all monthly values)")]:
        a = round_py(r[cm], 3); b = r[ca]
        if ismiss(a) and ismiss(b):
            continue
        if not ismiss(a) and not ismiss(b) and a == float(b):
            continue
        p_bad += 1
        if len(examples) < 20: examples.append((r["Station"], r["Source"][:12], r["Index"], r["Month"], cm, a, b))
print(f"median mismatches: {med_bad} / {len(m)*4}; p mismatches: {p_bad} / {len(m)*2}")
for e in examples: print("  ", e)

# packages compared again with missing-normalisation
V6 = os.path.expanduser("~/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/"
    "Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data")
arch6 = load_sheet(os.path.join(V6, "2_Data", "4_Monthly_analysis", "Monthly_upper_quartile_summary.xlsx"))
diff = 0; dex = []
for c in arch.columns:
    for a, b in zip(arch[c].tolist(), arch6[c].tolist()):
        if ismiss(a) and ismiss(b): continue
        if not ismiss(a) and not ismiss(b) and a == b: continue
        diff += 1
        if len(dex) < 8: dex.append((c, a, b))
print("6.13 vs v7 summary workbook differing cells (normalised):", diff)
for e in dex: print("  ", e)
