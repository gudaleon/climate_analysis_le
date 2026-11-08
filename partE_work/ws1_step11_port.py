"""Faithful Python port of step11a monthly_cdd (executed + mask-corrected branches)
and step11b monthly statistics, for Part E workstream 1. R semantics replicated from
step11a_monthly_inputs.R / step11b_monthly_statistics.R / common.R."""
import os, math, json
import numpy as np
import pandas as pd
from datetime import date, timedelta

V7 = os.path.expanduser("~/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/"
    "Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data")
MON_DIR = os.path.join(V7, "2_Data", "4_Monthly_analysis")
CDD_DIR = os.path.join(MON_DIR, "monthly_CDD")

# ---------------- step 11a ----------------
def read_daily(path):
    rows = []
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) < 4:
                continue
            rows.append((int(p[0]), int(p[1]), int(p[2]), float(p[3])))
    # dedupe by (y,m,d) keeping LAST occurrence (R: !duplicated(..., fromLast=TRUE))
    seen = {}
    for r in rows:
        seen[(r[0], r[1], r[2])] = r[3]
    return seen

def monthly_cdd(path, corrected=False):
    d = read_daily(path)
    years = [k[0] for k in d]
    y0, y1 = min(years), max(years)
    has_feb29 = any(m == 2 and dd == 29 for (_, m, dd) in d)
    # calendar
    days = []
    cur = date(y0, 1, 1)
    end = date(y1, 12, 31)
    while cur <= end:
        if has_feb29 or not (cur.month == 2 and cur.day == 29):
            days.append(cur)
        cur += timedelta(days=1)
    pr = np.array([np.nan if (c.year, c.month, c.day) not in d else
                   (np.nan if d[(c.year, c.month, c.day)] == -99.9 else d[(c.year, c.month, c.day)])
                   for c in days], dtype=float)
    ym = np.array([f"{c.year:04d}-{c.month:02d}" for c in days])
    yr = np.array([c.year for c in days])
    ym_levels = sorted(set(ym.tolist()))
    yr_levels = sorted(set(yr.tolist()))
    # run lengths at ends; NA treated as FALSE inside the helper (as in R)
    x = np.where(np.isnan(pr), False, pr < 1)
    n = len(x)
    starts = np.zeros(n, dtype=int); ends = np.zeros(n, dtype=int)
    # start: x[i] and not x[i-1] (with x[-1] := FALSE); end: x[i] and not x[i+1] (x[n] := FALSE)
    prev = np.concatenate([[False], x[:-1]])
    nxt = np.concatenate([x[1:], [False]])
    st = np.where(x & ~prev)[0]; en = np.where(x & ~nxt)[0]
    spell = np.zeros(n, dtype=float)
    spell[en] = en - st + 1
    # per-month aggregates
    max_spell = np.zeros(len(ym_levels)); all_dry = []
    mask_month = np.ones(len(ym_levels))
    miss = np.isnan(pr)
    for i, m in enumerate(ym_levels):
        sel = ym == m
        max_spell[i] = spell[sel].max()
        dry_m = (pr[sel] < 1)  # NA -> nan comparisons; emulate R all(): NA if any NA and no FALSE
        vals = dry_m[~np.isnan(pr[sel])] if False else None
        # R: dry <- pr < 1 gives NA where pr is NA; all() over the month:
        raw = np.where(np.isnan(pr[sel]), np.nan, (pr[sel] < 1).astype(float))
        if np.any(raw == 0):
            all_dry.append(False)
        elif np.any(np.isnan(raw)):
            all_dry.append(None)  # NA
        else:
            all_dry.append(True)
        mask_month[i] = np.nan if miss[sel].sum() > 3 else 1.0
    # NA-month rule: max_spell==0 & all_dry -> multiplier NA (with R three-valued logic)
    mult = np.ones(len(ym_levels))
    for i in range(len(ym_levels)):
        if max_spell[i] == 0:
            if all_dry[i] is True or all_dry[i] is None:
                mult[i] = np.nan
            # all_dry False -> stays 1
    base = max_spell * mult
    # year masks
    mask_year = np.ones(len(yr_levels))
    for j, y in enumerate(yr_levels):
        sel = yr == y
        my = np.nan if miss[sel].sum() > 15 else 1.0
        mm = mask_month[j * 12:(j + 1) * 12]
        prod = np.nan if np.any(np.isnan(mm)) else float(np.prod(mm))
        mask_year[j] = my * prod if not (np.isnan(my) or np.isnan(prod)) else np.nan
    Y = len(yr_levels)
    if corrected:
        year_idx = np.arange(len(ym_levels)) // 12
        v = base * mask_year[year_idx]
    else:
        rec = np.array([mask_year[i % Y] for i in range(len(ym_levels))])
        v = base * rec
    return pd.DataFrame({"ym": ym_levels, "v": v}), pd.DataFrame(
        {"ym": ym_levels, "v_corrected": v if corrected else np.nan})

def series_files():
    obs_day = os.path.join(V7, "2_Data", "1_Observations", "c_Homogenised_daily_series")
    mod_day = os.path.join(V7, "2_Data", "2_Models", "b_Daily_series")
    out = {}
    for st in ["London", "Fergus", "Harrow"]:
        out[f"OBS_{st.upper()}"] = os.path.join(obs_day, f"{st.upper()}_homogenised_v4.txt")
        out[f"BCC_{st}"] = os.path.join(mod_day, f"{st}_BCC.txt")
    out["NorESM_London"] = os.path.join(mod_day, "London_NorESM.txt")
    out["EC_Fergus"] = os.path.join(mod_day, "Fergus_EC.txt")
    out["EC_Harrow"] = os.path.join(mod_day, "Harrow_EC.txt")
    return out

def validate_cdd():
    res = {}
    for name, path in series_files().items():
        df, _ = monthly_cdd(path, corrected=False)
        arch = pd.read_csv(os.path.join(CDD_DIR, f"{name}.csv"), dtype={"ym": str})
        arch_v = arch["v"].to_numpy(dtype=float)
        mine = df["v"].to_numpy(dtype=float)
        same = (len(arch_v) == len(mine)) and np.all(
            (np.isnan(arch_v) & np.isnan(mine)) | (arch_v == mine))
        nmis = int(np.sum(~((np.isnan(arch_v) & np.isnan(mine)) | (arch_v == mine))))
        res[name] = {"months": len(mine), "match": bool(same), "mismatches": nmis}
    return res

# ---------------- step 11b ----------------
PERIODS = {"Hist": (1950, 1986), "Pres": (1987, 2023), "Near": (2024, 2062), "Far": (2063, 2100)}
TEMP_IDX = ["TMM", "TXX", "TXN", "ID", "SU"]
PREC_IDX = ["PRCPTOT", "R10MM", "RX1DAY", "RX5DAY", "CDD", "SPEI3", "SPEI6", "SPI3", "SPI6"]
MONTHS = [1, 2, 3, 6, 7, 8, 9]
TEMP_REF = {"London": "NorESM", "Fergus": "EC", "Harrow": "EC"}
MODEL_FULL = {"NorESM": "NorESM2-LM", "EC": "EC-Earth3-Veg", "BCC": "BCC-CSM2-MR"}

def quantile7(v, p):
    v = np.sort(np.asarray(v, dtype=float))
    n = len(v)
    if n == 0:
        return np.nan
    h = (n - 1) * p
    lo = int(math.floor(h)); hi = int(math.ceil(h))
    if lo == hi:
        return v[lo]
    return v[lo] + (h - lo) * (v[hi] - v[lo])

def uq_median(v, lower=False):
    v = np.array([x for x in v if not np.isnan(x)], dtype=float)
    if len(v) == 0:
        return np.nan
    t = quantile7(v, 0.25 if lower else 0.75)
    sub = v[v <= t] if lower else v[v >= t]
    return float(np.median(sub))

def wilcox_p(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) == 0 or len(b) == 0:
        return np.nan
    allv = np.concatenate([a, b])
    if np.all(allv == allv[0]):
        return 1.0
    # average ranks
    order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(len(allv), dtype=float)
    sortedv = allv[order]
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and sortedv[j + 1] == sortedv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    n1, n2 = len(a), len(b)
    U = ranks[:n1].sum() - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    # tie correction
    _, counts = np.unique(allv, return_counts=True)
    tie = np.sum(counts ** 3 - counts)
    n = n1 + n2
    sigma2 = n1 * n2 / 12.0 * ((n + 1) - tie / (n * (n - 1)))
    if sigma2 <= 0:
        return 1.0
    sigma = math.sqrt(sigma2)
    diff = U - mu
    if diff > 0:
        z = (diff - 0.5) / sigma
    elif diff < 0:
        z = (diff + 0.5) / sigma
    else:
        z = 0.0
    from scipy.stats import norm
    return float(2 * norm.cdf(-abs(z)))

def monthly_p(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) == 0 or len(b) == 0:
        return np.nan
    if np.all(np.concatenate([a, b]) == a[0]):
        return np.nan
    return wilcox_p(a, b)

def read_monthly(name, cdd_override=None):
    d = pd.read_excel(os.path.join(MON_DIR, f"{name}.xlsx"))
    d.columns = ["Year", "Month", "Index", "v"]
    d["v"] = d["v"].replace(-99.9, np.nan)
    if cdd_override is not None:
        key = {(int(y), int(m)): v for (y, m), v in cdd_override.items()}
        mask = d["Index"] == "CDD"
        d.loc[mask, "v"] = [key.get((int(y), int(m)), np.nan)
                            for y, m in zip(d.loc[mask, "Year"], d.loc[mask, "Month"])]
    return d

def mvals(d, k, mo, p):
    r = PERIODS[p]
    v = d["v"][(d["Index"] == k) & (d["Month"] == mo) & (d["Year"] >= r[0]) & (d["Year"] <= r[1])]
    return v.dropna().to_numpy(dtype=float)

def run_11b(cdd_overrides=None):
    rows = []
    DAT = {}
    for st in ["London", "Fergus", "Harrow"]:
        m = TEMP_REF[st]
        srcs = [("Observed", f"OBS_{st}", TEMP_IDX + PREC_IDX),
                (f"{MODEL_FULL[m]} (temperature)", f"{m}_{st}", TEMP_IDX),
                ("BCC-CSM2-MR (precipitation)", f"BCC_{st}", PREC_IDX)]
        for lab, fname, ids in srcs:
            ov = None if cdd_overrides is None else cdd_overrides.get(fname)
            d = read_monthly(fname, ov)
            DAT[fname] = d
            for k in ids:
                for mo in MONTHS:
                    v = {p: mvals(d, k, mo, p) for p in PERIODS}
                    med = {p: uq_median(v[p], lower=(k == "TXN")) for p in PERIODS}
                    rows.append({
                        "Station": st, "Source": lab, "Index": k, "Month": mo,
                        "Historical": med["Hist"], "Present": med["Pres"],
                        "Near": med["Near"], "Far": med["Far"],
                        "Change_Hist_to_Present": med["Pres"] - med["Hist"],
                        "Change_Near_to_Far": med["Far"] - med["Near"],
                        "p_Hist_vs_Present": monthly_p(v["Hist"], v["Pres"]),
                        "p_Near_vs_Far": monthly_p(v["Near"], v["Far"]),
                        "n_Hist": len(v["Hist"]), "n_Present": len(v["Pres"]),
                        "n_Near": len(v["Near"]), "n_Far": len(v["Far"])})
    return pd.DataFrame(rows), DAT

def round_py(x, nd):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    return float(f"{x:.{nd}f}")

if __name__ == "__main__":
    print(json.dumps(validate_cdd(), indent=1))
