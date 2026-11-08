import numpy as np, pandas as pd, openpyxl, os, sys
sys.path.insert(0, ".")
from ws1_step11_port import (monthly_cdd, series_files, run_11b, round_py, MON_DIR)

def ismiss(x):
    return x is None or (isinstance(x, float) and np.isnan(x))

# ---- in-memory validation of the 11b port against the archived sheet
tab, _ = run_11b()
wb = openpyxl.load_workbook(os.path.join(MON_DIR, "Monthly_upper_quartile_summary.xlsx"), read_only=True)
rows = list(wb["Monthly (Sec 3.4)"].iter_rows(values_only=True))
arch = pd.DataFrame(rows[1:], columns=rows[0])
m = tab.merge(arch, on=["Station", "Source", "Index", "Month"], suffixes=("_mine", "_arch"))
bad = 0
for _, r in m.iterrows():
    for c in ["Historical", "Present", "Near", "Far"]:
        a, b = round_py(r[c + "_mine"], 2), r[c + "_arch"]
        if not ((ismiss(a) and ismiss(b)) or (not ismiss(a) and not ismiss(b) and a == float(b))):
            bad += 1; print("median mismatch:", r["Station"], r["Index"], r["Month"], c, a, b)
    for cm, ca in [("p_Hist_vs_Present", "Wilcoxon p H vs P (all monthly values)"),
                   ("p_Near_vs_Far", "Wilcoxon p Near vs Far (all monthly values)")]:
        a, b = round_py(r[cm], 3), r[ca]
        if not ((ismiss(a) and ismiss(b)) or (not ismiss(a) and not ismiss(b) and a == float(b))):
            bad += 1; print("p mismatch:", r["Station"], r["Index"], r["Month"], cm, a, b)
print(f"IN-MEMORY VALIDATION: {bad} mismatches across {len(m)} rows (2352 medians, 1176 p-values)")

# ---- corrected branch: replace CDD in the monthly workbooks with mask-corrected CDD
files = series_files()
overrides = {}
diff_months = {}
for name, path in files.items():
    dfc, _ = monthly_cdd(path, corrected=True)
    dfe, _ = monthly_cdd(path, corrected=False)
    ov = {}
    nd = 0
    for (_, rc), (_, re_) in zip(dfc.iterrows(), dfe.iterrows()):
        y, mo = int(rc["ym"][:4]), int(rc["ym"][5:7])
        ov[(y, mo)] = rc["v"]
        a, b = rc["v"], re_["v"]
        if not ((np.isnan(a) and np.isnan(b)) or a == b):
            nd += 1
    wbkey = {"OBS_LONDON": "OBS_London", "OBS_FERGUS": "OBS_Fergus",
             "OBS_HARROW": "OBS_Harrow"}.get(name, name)
    overrides[wbkey] = ov
    diff_months[name] = nd
print("months whose CDD value or missingness changes under the corrected mask:")
for k, v in diff_months.items():
    print(f"   {k}: {v}")
tab_c, _ = run_11b(cdd_overrides=overrides)
tab_c.to_csv("ws1_tab_corrected.csv", index=False)
tab.to_csv("ws1_tab_executed_inmem.csv", index=False)

# ---- CDD rows: executed beside corrected
e = tab[tab["Index"] == "CDD"].set_index(["Station", "Source", "Month"])
c = tab_c[tab_c["Index"] == "CDD"].set_index(["Station", "Source", "Month"])
out = []
for k in e.index:
    re_, rc = e.loc[k], c.loc[k]
    changed = any(not ((np.isnan(re_[x]) and np.isnan(rc[x])) or re_[x] == rc[x])
                  for x in ["Historical", "Present", "Near", "Far"])
    out.append({"Station": k[0], "Source": k[1], "Month": k[2],
                "H_exec": re_["Historical"], "H_corr": rc["Historical"],
                "P_exec": re_["Present"], "P_corr": rc["Present"],
                "N_exec": re_["Near"], "N_corr": rc["Near"],
                "F_exec": re_["Far"], "F_corr": rc["Far"],
                "chgHP_exec": re_["Change_Hist_to_Present"], "chgHP_corr": rc["Change_Hist_to_Present"],
                "chgNF_exec": re_["Change_Near_to_Far"], "chgNF_corr": rc["Change_Near_to_Far"],
                "changed": changed})
o = pd.DataFrame(out)
o.to_csv("ws1_cdd_compare.csv", index=False)
print("\nCDD statistic rows changed:", int(o["changed"].sum()), "of", len(o))
print(o[o["changed"]].to_string(index=False))
