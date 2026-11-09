"""Render the error-framework figure (two panels) from plotted_data.csv.
Iteration 2: family labels moved outside the axes as tick labels; legend moved
to a horizontal strip under Panel A; region annotations repositioned so they
cannot collide; Panel B footnote moved to figure level below the axis label."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms as mtr
import numpy as np, pandas as pd

BASE = "/home/hatch/workspace/jeremy_wu_redteam/figures_error_framework/"
D = pd.read_csv(BASE + "plotted_data.csv")
A = D[D.panel == "A"].copy()
B = D[D.panel == "B"].copy()

med = A.groupby("family").margin_norm.median().sort_values()
ORDER = med.index.tolist()
N = len(ORDER)

rng = np.random.default_rng(20261108)
A["jit"] = [rng.uniform(-0.30, 0.30) for _ in range(len(A))]

SHAPE = {"London": "o", "Fergus": "^", "Harrow": "s"}
fig, (axA, axB) = plt.subplots(2, 1, figsize=(7.6, 9.6),
                               gridspec_kw=dict(height_ratios=[3.0, 1.9], hspace=0.55))

# ---------------- Panel A ----------------
axA.axvspan(-1.08, 0, color="0.93", zorder=0)
axA.axvline(0, color="black", lw=1.4, zorder=3)
for i, fam in enumerate(ORDER):
    y = N - 1 - i
    sub = A[A.family == fam]
    for _, r in sub.iterrows():
        yy = y + r.jit
        if r.width_zero:
            axA.plot(r.margin_norm, yy, marker="D", ms=6, mfc="white", mec="0.25",
                     mew=1.1, zorder=5)
        elif r.flipped:
            axA.plot(r.margin_norm, yy, marker=SHAPE[r.station], ms=7.5,
                     mfc="#d7301f", mec="black", mew=0.7, zorder=6)
        else:
            axA.plot(r.margin_norm, yy, marker=SHAPE[r.station], ms=5.2,
                     mfc="0.55", mec="0.35", mew=0.4, zorder=4)
axA.set_xlim(-1.08, 0.56); axA.set_ylim(-0.62, N - 0.38)
axA.set_yticks(range(N))
axA.set_yticklabels([f"{fam}\n(n={int((A.family==fam).sum())}, median {med[fam]:+.2f})"
                     for fam in reversed(ORDER)], fontsize=7.4)
blend = mtr.blended_transform_factory(axA.transData, axA.transAxes)
axA.text(-0.55, 1.015, "outside the range", fontsize=7.5, style="italic",
         color="0.3", ha="center", transform=blend)
axA.text(0.28, 1.015, "inside the range", fontsize=7.5, style="italic",
         color="0.3", ha="center", transform=blend)
axA.set_xlabel("Normalised margin: signed distance from the observed change to the nearest edge of the\n"
               "ten-model range, divided by the range width (positive = inside the range)", fontsize=8)
axA.set_title("Panel A — How far each of the 132 bounding cases sits from its edge (thesis branch, 6.13 scheme)",
              fontsize=9.5, loc="left", pad=10)
handles = [plt.Line2D([], [], marker=mk, ls="none", mfc="0.55", mec="0.35", ms=6, label=s)
           for s, mk in SHAPE.items()]
handles.append(plt.Line2D([], [], marker="o", ls="none", mfc="#d7301f", mec="black", ms=7.5,
                          label="Class flips under a grid-cell perturbation or on the H1 layer"))
handles.append(plt.Line2D([], [], marker="D", ls="none", mfc="white", mec="0.25", ms=6,
                          label="Degenerate all-zero range (width 0), plotted at 0"))
axA.legend(handles=handles, fontsize=6.9, loc="upper center",
           bbox_to_anchor=(0.5, -0.135), ncol=2, frameon=False)
axA.tick_params(labelsize=8)
for sp in ["top", "right"]:
    axA.spines[sp].set_visible(False)

# ---------------- Panel B ----------------
PERT = ["Fergus", "Harrow", "London"]
OFF = {"Fergus": 0.26, "Harrow": 0.0, "London": -0.26}
STYLE = {"Fergus": ("^", "0.15"), "Harrow": ("s", "0.45"), "London": ("o", "0.7")}
axB.axvline(0, color="black", lw=1.2, zorder=2)
for i, fam in enumerate(ORDER):
    y = N - 1 - i
    for p in PERT:
        row = B[(B.family == fam) & (B.perturbation_station == p)].iloc[0]
        d = int(row.delta_within_count); yy = y + OFF[p]
        mk, col = STYLE[p]
        if d == 0:
            axB.plot(0, yy, marker=mk, ms=6, mfc=col, mec="black", mew=0.5, zorder=5)
        else:
            axB.annotate("", xy=(d, yy), xytext=(0, yy),
                         arrowprops=dict(arrowstyle="-|>", color=col, lw=1.8,
                                         mutation_scale=13), zorder=4)
            axB.plot(0, yy, marker="|", ms=9, color="black", zorder=5)
axB.set_xlim(-1.35, 1.6); axB.set_ylim(-0.62, N - 0.38)
axB.set_yticks(range(N))
axB.set_yticklabels(list(reversed(ORDER)), fontsize=7.4)
axB.set_xticks([-1, 0, 1])
axB.set_xlabel("Change in the family's basin count of cases within the ensemble range\n"
               "when the named station's model series moves one grid cell west (6.13 scheme)", fontsize=8)
axB.set_title("Panel B — Family-level movement of the within-range count under each single-station perturbation",
              fontsize=9.5, loc="left", pad=10)
handlesB = [plt.Line2D([], [], marker=mk, ls="none", mfc=col, mec="black", ms=6,
                       label=f"{p} perturbed") for p, (mk, col) in STYLE.items()]
axB.legend(handles=handlesB, fontsize=7, loc="lower right", framealpha=0.95)
axB.tick_params(labelsize=8)
for sp in ["top", "right"]:
    axB.spines[sp].set_visible(False)

fig.text(0.115, 0.012,
         "Panel B: a point at zero means the family's count does not move. Wet–dry spell persistence at Fergus is a net zero\n"
         "with internal movement: CDD leaves the range as CWD enters it.",
         fontsize=6.8, style="italic", color="0.3")
fig.suptitle("The 6.13 thesis's bounding cases: margins and movements",
             fontsize=12, x=0.055, ha="left", fontweight="bold")
fig.savefig(BASE + "error_framework_figure.png", dpi=300, bbox_inches="tight")
fig.savefig(BASE + "error_framework_figure.pdf", bbox_inches="tight")
print("saved iteration 2")
