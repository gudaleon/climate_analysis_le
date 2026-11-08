import numpy as np, pandas as pd, os, sys
sys.path.insert(0, ".")
from ws2_step08 import load_annual, MODELS, PERIODS, STATIONS

GROUPS = {
  "Baseline temperature regime": (["TMm", "TNm", "TXm", "TNn", "TNx", "TXn", "TXx"], 1),
  "Loss of cold extremes": (["FD", "ID", "TN10p", "TX10p", "TNltm20", "CSDI6", "CSDI3", "CWA", "CWF"], "cold"),
  "Heat extremes and heat waves": (["SU", "TR", "TN90p", "TX90p", "TXge30", "TXgt50p", "TXb3TNb3", "WSDI6", "WSDI3", "HWA", "HWF"], 1),
  "Precipitation amount and frequency": (["PRCPTOT", "R10mm", "R20mm"], 1),
  "Growing season and heat accumulation": (["GSL", "GDDgrow10"], 1),
  "Extreme precipitation intensity": (["RX1day", "RX3day", "RX5day", "SDII", "R95p", "R99p", "R95pTOT", "R99pTOT"], 1),
  "Diurnal temperature structure": (["DTR", "DTRgt15"], "dom"),
  "Wet-dry spell persistence": (["CDD", "CWD"], "dom"),
}

def sgn(vals):
    return np.sign(np.round(np.asarray(vals, dtype=float), 6))

def coh(vals, idx, sg, zero_ok=False):
    s = sgn(vals)
    if sg == "dom":
        return int(max(np.sum(s == 1), np.sum(s == -1)) + (np.sum(s == 0) if zero_ok else 0))
    if sg == "cold":
        ex = np.array([1 if i == "CWA" else -1 for i in idx])
    else:
        ex = np.full(len(idx), sg)
    return int(np.sum((s == ex) | ((s == 0) & zero_ok)))

def coh_fixed(vals, ex_map, idx):
    s = sgn(vals)
    ex = np.array([ex_map[i] for i in idx])
    return int(np.sum(s == ex))

B = pd.read_csv(os.path.expanduser("~/workspace/jeremy_wu_redteam/reports/pass2_b1_compare.csv"))
B = B.rename(columns={"mine_dobs": "dobs", "printed_cls": "cls", "station": "Station", "index": "Index"})
print("B1 substitute rows:", len(B), " class mismatches vs printed:", int((B.cls != B.mine_cls).sum()))
X = {s: load_annual(s) for s in STATIONS}

def pooled_models(s, k, p):
    g = X[s][X[s]["Index"] == k]
    a, b = PERIODS[p]
    v = g.loc[(g["Year"] >= a) & (g["Year"] <= b), MODELS].to_numpy(dtype=float).ravel()
    return float(np.median(v[~np.isnan(v)]))

def group_result(ks, sg, coh_hist, coh_near, coh_far, sub):
    n = len(sub)
    bnd = int(np.sum(sub["cls"] == "Bounded")); sr = int(np.sum(sub["cls"].str.lower() == "sign reversal"))
    zero_hist = float(np.mean(np.round(sub["dobs"].to_numpy(dtype=float), 6) == 0))
    pc = [100 * coh_hist / n, 100 * coh_near / n, 100 * coh_far / n]
    pb = 100 * bnd / n
    return pc, pb, sr, zero_hist

def confidence(pc, pb, sr, zero_hist, agree):
    if zero_hist >= 0.5 or pb < 60 or sum(1 for x in pc if x < 60) >= 2:
        return "Low"
    if sum(1 for x in pc if x >= 80) >= 2 and pb >= 80 and sr == 0 and agree:
        return "High"
    return "Moderate"

PRINTED = {  # claim: (hist, near, far, bounded, confidence)
 "Baseline temperature regime": (100.0, 100.0, 100.0, 100.0, "High"),
 "Loss of cold extremes": (81.5, 88.9, 88.9, 88.9, "Moderate"),
 "Heat extremes and heat waves": (90.9, 90.9, 90.9, 100.0, "High"),
 "Growing season and heat accumulation": (100.0, 100.0, 100.0, 83.3, "High"),
 "Diurnal temperature structure": (100.0, 50.0, 50.0, 50.0, "Low"),
 "Precipitation amount and frequency": (33.3, 100.0, 100.0, 88.9, "Moderate"),
 "Extreme precipitation intensity": (41.7, 100.0, 100.0, 66.7, "Moderate"),
 "Wet-dry spell persistence": (33.3, 16.7, 33.3, 83.3, "Low")}

print("\n=== executed branch, all eight groups ===")
for gname, (ks, sg) in GROUPS.items():
    sub = B[B["Index"].isin(ks)]
    fut = {}
    for p in ["Near", "Far"]:
        v, ix = [], []
        for s in STATIONS:
            for k in ks:
                v.append(pooled_models(s, k, p) - pooled_models(s, k, "Hist")); ix.append(k)
        fut[p] = (coh(v, ix, sg), coh(v, ix, sg, True))
    ch = coh(sub["dobs"].to_numpy(), sub["Index"].tolist(), sg)
    pc, pb, sr, zh = group_result(ks, sg, ch, fut["Near"][0], fut["Far"][0], sub)
    agree = all(coh(sub[sub.Station == s]["dobs"].to_numpy(), sub[sub.Station == s]["Index"].tolist(), sg)
                / max(len(sub[sub.Station == s]), 1) >= 0.6 for s in STATIONS)
    conf = confidence(pc, pb, sr, zh, agree)
    pr = PRINTED[gname]
    got = (round(pc[0], 1), round(pc[1], 1), round(pc[2], 1), round(pb, 1), conf)
    print(f"{gname:38s} mine {got}  printed {pr}  {'MATCH' if got == pr else 'MISMATCH'}  "
          f"(zero_hist {100*zh:.1f}%, sr {sr}, agree {agree})")

print("\n=== line detail for the two dominant-sign groups ===")
for gname in ["Diurnal temperature structure", "Wet-dry spell persistence"]:
    ks, sg = GROUPS[gname]
    sub = B[B["Index"].isin(ks)].sort_values(["Index", "Station"])
    for _, r in sub.iterrows():
        dn = pooled_models(r.Station, r.Index, "Near") - pooled_models(r.Station, r.Index, "Hist")
        df_ = pooled_models(r.Station, r.Index, "Far") - pooled_models(r.Station, r.Index, "Hist")
        print(f"  {gname[:12]:12s} {r.Station:7s} {r.Index:8s} dobs {r.dobs:+9.3f} cls {r.cls:13s} "
              f"near {dn:+9.3f} far {df_:+9.3f}  signs obs/near/far: "
              f"{int(np.sign(round(r.dobs,6)))}/{int(np.sign(round(dn,6)))}/{int(np.sign(round(df_,6)))}")

print("\n=== rescoring under the direction statement filed before computation ===")
# Diurnal temperature structure: DTR -1, DTRgt15 -1 on all six lines of each comparison.
ks, _ = GROUPS["Diurnal temperature structure"]
sub = B[B["Index"].isin(ks)]
EX = {"DTR": -1, "DTRgt15": -1}
res = {}
for label, vals, ix in [("Hist", sub["dobs"].to_numpy(), sub["Index"].tolist())]:
    res[label] = coh_fixed(vals, EX, ix)
for p in ["Near", "Far"]:
    v, ix = [], []
    for s in STATIONS:
        for k in ks:
            v.append(pooled_models(s, k, p) - pooled_models(s, k, "Hist")); ix.append(k)
    res[p] = coh_fixed(v, EX, ix)
n = len(sub)
pc = [100 * res["Hist"] / n, 100 * res["Near"] / n, 100 * res["Far"] / n]
bnd = int(np.sum(sub["cls"] == "Bounded")); sr = int(np.sum(sub["cls"].str.lower() == "sign reversal"))
pb = 100 * bnd / n; zh = float(np.mean(np.round(sub["dobs"].to_numpy(dtype=float), 6) == 0))
agree = all(coh_fixed(sub[sub.Station == s]["dobs"].to_numpy(), EX, sub[sub.Station == s]["Index"].tolist())
            / max(len(sub[sub.Station == s]), 1) >= 0.6 for s in STATIONS)
print(f"Diurnal temperature structure rescored: coherence Hist {pc[0]:.1f}% Near {pc[1]:.1f}% Far {pc[2]:.1f}% "
      f"(counts {res['Hist']}/6, {res['Near']}/6, {res['Far']}/6); bounded {pb:.1f}%; sign reversals {sr}; "
      f"zero-change share {100*zh:.1f}%; per-station agreement {agree}; confidence {confidence(pc, pb, sr, zh, agree)}")

# Wet-dry spell persistence: CDD lines only against +1; CWD distributions reported, no score.
ks, _ = GROUPS["Wet-dry spell persistence"]
sub = B[B["Index"].isin(ks)]
cdd = sub[sub["Index"] == "CDD"]; cwd = sub[sub["Index"] == "CWD"]
res = {"Hist": int(np.sum(sgn(cdd["dobs"].to_numpy()) == 1))}
for p in ["Near", "Far"]:
    v = [pooled_models(s, "CDD", p) - pooled_models(s, "CDD", "Hist") for s in STATIONS]
    res[p] = int(np.sum(sgn(v) == 1))
pc = [100 * res["Hist"] / 3, 100 * res["Near"] / 3, 100 * res["Far"] / 3]
bnd = int(np.sum(sub["cls"] == "Bounded")); sr = int(np.sum(sub["cls"].str.lower() == "sign reversal"))
pb = 100 * bnd / len(sub); zh = float(np.mean(np.round(sub["dobs"].to_numpy(dtype=float), 6) == 0))
print(f"Wet-dry spell persistence, CDD lines rescored: coherence Hist {pc[0]:.1f}% Near {pc[1]:.1f}% Far {pc[2]:.1f}% "
      f"(counts {res['Hist']}/3, {res['Near']}/3, {res['Far']}/3); group bounded {pb:.1f}%; sign reversals {sr}; "
      f"group zero-change share {100*zh:.1f}%; confidence (CDD-line coherence, other inputs as executed) "
      f"{confidence(pc, pb, sr, zh, False)}")
for label, vals in [("observed Historical-to-Present", cwd["dobs"].to_numpy()),
                    ("pooled models Historical-to-Near", [pooled_models(s, "CWD", "Near") - pooled_models(s, "CWD", "Hist") for s in STATIONS]),
                    ("pooled models Historical-to-Far", [pooled_models(s, "CWD", "Far") - pooled_models(s, "CWD", "Hist") for s in STATIONS])]:
    s = sgn(vals)
    print(f"  CWD sign distribution, {label}: positive {int(np.sum(s==1))}, zero {int(np.sum(s==0))}, "
          f"negative {int(np.sum(s==-1))} of 3 station lines; values {[round(float(x),3) for x in vals]}")
