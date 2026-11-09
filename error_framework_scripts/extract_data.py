"""Extract Panel A/B plotted data for the error-framework figure from the audit's
saved record only: the envelope frames in executor_runs/wu_claude/out_addA|B|C
tables pkls (authors' v4 layer = thesis branch; S/P frames = perturbed branch;
tables_H1_reviewed.pkl = the audit's independent homogenisation layer)."""
import ast, pickle, sys
import numpy as np, pandas as pd

BASE = "/home/hatch/workspace/jeremy_wu_redteam/"
WU = BASE + "executor_runs/wu_claude/"

# --- process families: parse the GROUPS literal out of the step 09 port -------
src = open(BASE + "reports/partE_work/ws3_step09.py").read()
tree = ast.parse(src)
GROUPS = None
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "GROUPS":
        GROUPS = ast.literal_eval(node.value)
FAMILY = {}
for fam, (idxs, _sg) in GROUPS.items():
    for k in idxs:
        FAMILY[k] = fam
assert len(FAMILY) == 44, len(FAMILY)

# --- envelope frames -----------------------------------------------------------
def load(path, key):
    with open(path, "rb") as fh:
        return pickle.load(fh)[key]

ADD = {  # station -> (folder, perturbed key)
    "Fergus": ("out_addA", "eS"),
    "Harrow": ("out_addB", "eP"),
    "London": ("out_addC", "eP"),
}
frames_T, frames_P, frames_H1 = {}, {}, {}
for st, (folder, pkey) in ADD.items():
    frames_T[st] = load(WU + folder + "/tables_AUTHORS_v4.pkl", "eT")
    frames_P[st] = load(WU + folder + "/tables_AUTHORS_v4.pkl", pkey)
    frames_H1[st] = load(WU + folder + "/tables_H1_reviewed.pkl", "eT")

rows = []
for st in ["London", "Fergus", "Harrow"]:
    eT, eP, eH = frames_T[st], frames_P[st], frames_H1[st]
    for k in eT.index:
        obs, lo, hi = float(eT.loc[k, "obs"]), float(eT.loc[k, "lo"]), float(eT.loc[k, "hi"])
        width = hi - lo
        d = min(obs - lo, hi - obs)
        norm = d / width if width > 0 else 0.0
        cls_T = str(eT.loc[k, "c613"])
        flips, flip_classes = [], {}
        if str(eP.loc[k, "c613"]) != cls_T:
            flips.append(st + " grid-cell perturbation")
            flip_classes["perturbed_class"] = str(eP.loc[k, "c613"])
        if str(eH.loc[k, "c613"]) != cls_T:
            flips.append("H1 homogenisation layer")
            flip_classes["h1_class"] = str(eH.loc[k, "c613"])
        rows.append(dict(
            panel="A", station=st, index=k, family=FAMILY[k],
            obs_change=obs, range_lo=lo, range_hi=hi, range_width=width,
            margin_raw=d, margin_norm=norm, width_zero=bool(width == 0),
            class_613_T=cls_T, within_T=bool(cls_T == "within"),
            flipped=bool(flips), flip_sources="; ".join(flips),
            class_perturbed=flip_classes.get("perturbed_class", ""),
            class_H1=flip_classes.get("h1_class", ""),
            source_file=f"executor_runs/wu_claude/{ADD[st][0]}/tables_AUTHORS_v4.pkl (frames eT/{ADD[st][1]}) + tables_H1_reviewed.pkl (frame eT)",
        ))
A = pd.DataFrame(rows)
assert len(A) == 132

# --- cross-check obs/lo/hi against the pass-2 B1 comparison (independent file) --
B1 = pd.read_csv(BASE + "reports/pass2_b1_compare.csv")
B1["station"] = B1["station"].str.capitalize(); B1["index"] = B1["index"]
m = A.merge(B1, on=["station", "index"], how="left", suffixes=("", "_b1"))
assert m["mine_dobs"].notna().all()
for a, b in [("obs_change", "mine_dobs"), ("range_lo", "mine_dmin"), ("range_hi", "mine_dmax")]:
    print(f"cross-check {a}: max abs diff vs pass2_b1_compare = {np.abs(m[a]-m[b]).max():.6f}")

print("basin 6.13 totals, thesis branch:",
      {c: int((A.class_613_T == c).sum()) for c in ["within", "magnitude", "reversal"]})
for st in ["Fergus", "Harrow", "London"]:
    sub = A[A.station == st]
    print(f"  {st}: within T = {int(sub.within_T.sum())}")

# --- Panel B: per-family change in within-count per perturbation --------------
brows = []
for st, (folder, pkey) in ADD.items():
    eT, eP = frames_T[st], frames_P[st]
    for fam in GROUPS:
        idxs = GROUPS[fam][0]
        d = int((eP.loc[idxs, "c613"] == "within").sum() - (eT.loc[idxs, "c613"] == "within").sum())
        brows.append(dict(panel="B", perturbation_station=st, family=fam,
                          delta_within_count=d,
                          changed_indices="; ".join(
                              f"{k}:{eT.loc[k,'c613']}->{eP.loc[k,'c613']}" for k in idxs
                              if str(eP.loc[k, "c613"]) != str(eT.loc[k, "c613"])),
                          source_file=f"executor_runs/wu_claude/{folder}/tables_AUTHORS_v4.pkl (frames eT/{pkey})"))
B = pd.DataFrame(brows)
print(B.pivot(index="family", columns="perturbation_station", values="delta_within_count"))
print("basin within totals per perturbation:",
      {st: int(A.within_T.sum()) + int(B[B.perturbation_station == st].delta_within_count.sum()) for st in ADD})

out = pd.concat([A, B], ignore_index=True, sort=False)
out.to_csv(BASE + "figures_error_framework/plotted_data.csv", index=False)
A.to_csv(BASE + "figures_error_framework/panelA_margins.csv", index=False)
print("wrote plotted_data.csv:", len(out), "rows; flipped cases:", int(A.flipped.sum()))
print(A[A.flipped][["station", "index", "family", "class_613_T", "flip_sources", "class_perturbed", "class_H1"]].to_string())
print("margin_norm describe:"); print(A.margin_norm.describe())
print("width-zero cases:"); print(A[A.width_zero][["station", "index", "class_613_T"]].to_string())
