import numpy as np, pandas as pd, sys
sys.path.insert(0, ".")
from ws1_step11_port import read_monthly, mvals, uq_median

print("=== E2: SPEI6/SPI6 gaps at full precision (BCC-CSM2-MR workbooks, step 11b statistic) ===")
rows = []
for st in ["London", "Fergus", "Harrow"]:
    d = read_monthly(f"BCC_{st}")
    for p in ["Hist", "Near", "Far"]:
        for mo in range(6, 10):
            g = uq_median(mvals(d, "SPI6", mo, p)) - uq_median(mvals(d, "SPEI6", mo, p))
            rows.append({"Station": st, "Period": p, "Month": mo, "gap_SPI6_minus_SPEI6": g})
g = pd.DataFrame(rows)
far = g[g.Period == "Far"]
mn = far.loc[far.gap_SPI6_minus_SPEI6.idxmin()]; mx = far.loc[far.gap_SPI6_minus_SPEI6.idxmax()]
print(f"Far Future: min gap = {mn.gap_SPI6_minus_SPEI6:.6f} ({mn.Station}, month {int(mn.Month)}); "
      f"max gap = {mx.gap_SPI6_minus_SPEI6:.6f} ({mx.Station}, month {int(mx.Month)})")
hist = g[g.Period == "Hist"]
print(f"Historical: max |gap| = {hist.gap_SPI6_minus_SPEI6.abs().max():.6f}")
print(f"Near Future: min = {g[g.Period=='Near'].gap_SPI6_minus_SPEI6.min():.6f}, max = {g[g.Period=='Near'].gap_SPI6_minus_SPEI6.max():.6f}")
print(f"Far endpoints at print precisions: min {mn.gap_SPI6_minus_SPEI6:.2f} (2dp) / {mn.gap_SPI6_minus_SPEI6:.1f} (1dp); "
      f"max {mx.gap_SPI6_minus_SPEI6:.2f} (2dp) / {mx.gap_SPI6_minus_SPEI6:.1f} (1dp)")
g.to_csv("ws1_spei_gaps_full_precision.csv", index=False)

print("\n=== observed Fergus/London July CDD, both branches (for 6.13 C246) ===")
c = pd.read_csv("ws1_cdd_compare.csv")
print(c[(c.Source == "Observed") & (c.Month == 7)].to_string(index=False))
print("\n=== all observed CDD rows, changes both branches ===")
o = c[c.Source == "Observed"][["Station", "Month", "H_exec", "H_corr", "P_exec", "P_corr", "chgHP_exec", "chgHP_corr"]]
print(o.to_string(index=False))
print("\n=== BCC CDD rows: any full-precision change? ===")
b = c[c.Source != "Observed"]
print("BCC rows changed:", int(b["changed"].sum()), "of", len(b))
