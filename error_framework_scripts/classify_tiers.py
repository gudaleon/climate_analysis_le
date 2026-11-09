"""Tier classification of the 292 claims of the 6.13 inventory.
Rules (stated in DESIGN_AND_EVALUATION.md):
  Structural - the claim rests on a defect that changes what a number means:
    C14 (homogenisation methods text, roster items A3/A4), C21 (TXb3TNb3
    definition, item A2), C22 (SPEI PET named Thornthwaite, executed
    Hargreaves, item A1), C246 (its London comparison is an artefact of the
    step 11a recycled-mask defect, Part E item E1 / roster item D7).
  Marginal - at least one check of the claim changes value across any of the
    three grid-cell perturbation branches (out_addA/B/C
    claim_check_changes_sec.csv, target 613), or the claim's value was
    restated under a ruling (C252, Part E item E2). Structural takes
    precedence where both apply.
  Robust - every remaining claim.
kind_change flags the claims whose printed statement changes in kind (not
only in value) on a perturbation branch: C5 (Harrow branch, Addendum B) and
C258 (London branch, Addendum C)."""
import re
import pandas as pd

BASE = "/home/hatch/workspace/jeremy_wu_redteam/"

# --- parse the inventory: claim -> (section path, text) -----------------------
claims, section = {}, ""
for line in open(BASE + "thesis/CLAIMS_INVENTORY_613.md"):
    h = re.match(r"^#{2,3}\s+(.*)", line)
    if h:
        section = h.group(1).strip()
    c = re.match(r"^- \*\*(C\d+)\.\*\*\s*(.*)", line)
    if c:
        claims[c.group(1)] = (section, c.group(2).strip())
assert len(claims) == 292

# --- changed checks per perturbation branch ------------------------------------
def changed(path, other_col):
    df = pd.read_csv(path)
    df = df[df.target.astype(str) == "613"]
    def diff(r):
        try:
            return abs(float(r["T"]) - float(r[other_col])) > 1e-9
        except (ValueError, TypeError):
            return str(r["T"]) != str(r[other_col])
    df = df[df.apply(diff, axis=1)]
    return df.groupby("claim").size().to_dict()

chg = {
    "Fergus": changed(BASE + "executor_runs/wu_claude/out_addA/claim_check_changes_sec.csv", "S"),
    "Harrow": changed(BASE + "executor_runs/wu_claude/out_addB/claim_check_changes_sec.csv", "P"),
    "London": changed(BASE + "executor_runs/wu_claude/out_addC/claim_check_changes_sec.csv", "P"),
}

STRUCTURAL = {
    "C14": "Homogenisation methods text misdescribes the executed step 02 in both its parts (roster items A3 and A4; reconciliation pass 3, group 1).",
    "C21": "Table 2 defines TXb3TNb3 as compound warm-event days; the executed index counts cold compound events (roster item A2; reconciliation pass 3, group 3).",
    "C22": "SPEI evapotranspiration named as Thornthwaite; the executed Climpact code computes the Hargreaves estimate (roster item A1; reconciliation pass 1).",
    "C246": "The claim's comparison of the Fergus July CDD decline to London's rests on London's mask-defective July shortening of 5.0 days; the corrected value is 2.5 days (Part E item E1; roster item D7).",
}
RESTATE = {"C252": "Conclusions endpoint restated under Part E item E2 (the Far Future SPEI-6 minus SPI-6 maximum prints as 2.1, not 2.2)."}
KIND = {
    "C5": "On the Harrow branch a second index (CWA) falls outside the envelope at all three stations, so the printed statement that DTRgt15 was the only such index no longer holds (Addendum B).",
    "C258": "On the London branch the September RX5day basin maximum is London's perturbed value, so the printed statement that the maximum is largest at Harrow no longer holds (Addendum C).",
}

rows = []
for cid in sorted(claims, key=lambda c: int(c[1:])):
    sec, text = claims[cid]
    n = {k: v.get(cid, 0) for k, v in chg.items()}
    if cid in STRUCTURAL:
        tier, basis = "Structural", STRUCTURAL[cid]
    elif sum(n.values()) > 0 or cid in RESTATE:
        tier = "Marginal"
        parts = [f"{v} check(s) change value on the {k} perturbation branch" for k, v in n.items() if v]
        if cid in RESTATE:
            parts.append(RESTATE[cid])
        basis = "; ".join(parts) + "."
    else:
        tier, basis = "Robust", "No check changes under the audit's corrections or on any perturbation branch; the claim stands on the recompute record."
    rows.append(dict(claim=cid, section=sec, tier=tier, basis=basis,
                     kind_change=bool(cid in KIND), kind_change_note=KIND.get(cid, ""),
                     checks_changed_fergus=n["Fergus"], checks_changed_harrow=n["Harrow"],
                     checks_changed_london=n["London"],
                     claim_text=text[:300]))
T = pd.DataFrame(rows)
T.to_csv(BASE + "figures_error_framework/tier_classification_613.csv", index=False)
print(T.tier.value_counts().to_dict())
abs_sec = T[T.section.str.contains("Abstract")]
con_sec = T[T.section.str.contains("Section 5")]
print("abstract claims:", abs_sec.claim.tolist(), abs_sec.tier.value_counts().to_dict())
print("conclusion claims:", con_sec.claim.tolist(), con_sec.tier.value_counts().to_dict())
print("structural:", T[T.tier == "Structural"].claim.tolist())
print("kind-change:", T[T.kind_change].claim.tolist())
