"""Section 3.3 sweep: reuse the validated ws2 step-08 port (import runs its own
Table C1 validation), then compute every quantity the section 3.3 claims and
their downstream citations rest on, on both pooling branches, at full precision."""
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import ws2_step08 as W   # prints its own validation log into buf
print("---- ws2 port import log (validation) ----")
print(buf.getvalue())
from ws1_step11_port import round_py

E, M = W.E, W.M
ST = W.STATIONS

def med(df, idx, p):
    return float(df[df["Index"] == idx].iloc[0][f"{p}_median"])

def q(df, idx, p, which):
    return float(df[df["Index"] == idx].iloc[0][f"{p}_{which}"])

def r1(x):  # print at the thesis's one-decimal precision, port convention
    return round_py(x, 1)

IDX = ["TMm","FD","SU","TXge30","TR","HWA","HWF","WSDI3","ID","CWF","TNltm20",
       "PRCPTOT","R95p","R99p","RX5day","SDII","CDD"]
print("==== Hist and Far medians, full precision (executed | models-only), printed 1dp in brackets ====")
for st in ST:
    for idx in IDX:
        eh, ef = med(E[st], idx, "Hist"), med(E[st], idx, "Far")
        mh, mf = med(M[st], idx, "Hist"), med(M[st], idx, "Far")
        flag = "  <-- Hist differs at 1dp" if r1(eh) != r1(mh) else ""
        print(f"{st:7s} {idx:8s} Hist {eh!r:>24} [{r1(eh)}] | {mh!r:>24} [{r1(mh)}]   Far {ef!r} [{r1(ef)}] (both branches){flag}")

print()
print("==== Pres and Near medians where a section 3.3 claim needs them ====")
for st in ST:
    for idx, p in [("CDD","Pres"),("CDD","Near"),("TMm","Pres"),("CWF","Near")]:
        ev, mv = med(E[st], idx, p), med(M[st], idx, p)
        print(f"{st:7s} {idx:8s} {p}: exec {ev!r} [{r1(ev)}] | models {mv!r} [{r1(mv)}]")

print()
print("==== TNltm20 quartiles, future windows (claim V7-C453) ====")
for st in ST:
    for br, D in [("exec", E), ("models", M)]:
        df = D[st]
        print(f"{st:7s} {br:6s} Hist med {med(df,'TNltm20','Hist')!r}  Near Q1/Q3 "
              f"{q(df,'TNltm20','Near','Q1')!r}/{q(df,'TNltm20','Near','Q3')!r}  Far Q1/Q3 "
              f"{q(df,'TNltm20','Far','Q1')!r}/{q(df,'TNltm20','Far','Q3')!r}")

print()
print("==== Percentage changes Hist -> Far at full precision (printed 1dp) ====")
for idx in ["PRCPTOT","R95p","R99p","RX5day"]:
    for st in ST:
        pe = (med(E[st], idx, "Far")/med(E[st], idx, "Hist") - 1)*100
        pm = (med(M[st], idx, "Far")/med(M[st], idx, "Hist") - 1)*100
        print(f"{idx:8s} {st:7s} exec {pe:.4f}% [{r1(pe)}] | models {pm:.4f}% [{r1(pm)}]")

print()
print("==== Factors Far/Hist (HWA, HWF, WSDI3) ====")
for idx in ["HWA","HWF","WSDI3"]:
    for st in ST:
        fe = med(E[st], idx, "Far")/med(E[st], idx, "Hist")
        fm = med(M[st], idx, "Far")/med(M[st], idx, "Hist")
        print(f"{idx:6s} {st:7s} exec {fe:.4f} | models {fm:.4f}")

print()
print("==== HWA spread relative to basin mean, (max-min)/mean x 100 ====")
for p in ["Hist","Far"]:
    for br, D in [("exec", E), ("models", M)]:
        vals = [med(D[st], "HWA", p) for st in ST]
        print(f"{p} {br:6s} medians {[round(v,4) for v in vals]} spread {(max(vals)-min(vals))/(sum(vals)/3)*100:.3f}%")

print()
print("==== TMm shifts Far-Hist and TR gains / ID losses (full precision) ====")
for st in ST:
    print(f"{st:7s} TMm shift exec {med(E[st],'TMm','Far')-med(E[st],'TMm','Hist'):.4f} | models "
          f"{med(M[st],'TMm','Far')-med(M[st],'TMm','Hist'):.4f} ; TR gain exec "
          f"{med(E[st],'TR','Far')-med(E[st],'TR','Hist'):.2f} | models {med(M[st],'TR','Far')-med(M[st],'TR','Hist'):.2f} ; "
          f"ID loss exec {med(E[st],'ID','Hist')-med(E[st],'ID','Far'):.2f} | models {med(M[st],'ID','Hist')-med(M[st],'ID','Far'):.2f}")

print()
print("==== Section 4.3 claim V7-C603 rates: mean of station percentages / 6.0 degC ====")
for idx in ["PRCPTOT","R95p"]:
    for br, D in [("exec", E), ("models", M)]:
        pcs = [(med(D[st], idx, "Far")/med(D[st], idx, "Hist") - 1)*100 for st in ST]
        print(f"{idx:8s} {br:6s} station % {[round(x,3) for x in pcs]} mean {sum(pcs)/3:.4f}  per-degC {(sum(pcs)/3)/6.0:.4f}")

print()
print("==== Tie detection: elements used by section 3.3 claims whose full-precision value")
print("     ends in exactly 5 at the second decimal (x.x5), both branches ====")
def is_tie(v):
    return abs(abs(v)*100 - int(abs(v)*100) - 5.0) < 1e-6 and abs(v*100 - round(v*100)) > 1e-9
for st in ST:
    for idx in IDX:
        for p in ["Hist","Pres","Near","Far"]:
            for br, D in [("exec", E), ("models", M)]:
                v = med(D[st], idx, p)
                if is_tie(v):
                    print(f"TIE {st} {idx} {p} {br}: {v!r} -> round_py {r1(v)}")
