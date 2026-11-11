"""Unified diagnostic figure set: one glyph grid over the 132 station-and-index
cases of the Historical-to-Present contrast, split by index group because a
single 44-row grid is illegible (the glyph prototype's composition).

Each cell is one case, and every visual channel is a coordinate of the single
unified record in unified_cases.csv:
  - arrow direction = sign of the median of the ten models' changes;
  - cell fill = the signed margin of the observed change (distance to the
    nearest edge of the models' range of changes, divided by the range width;
    positive inside the range, negative outside), on a diverging scale, so the
    fill cannot saturate to one colour the way an agreement-count fill did;
  - heavy border = the case's bounding classification flips under a grid-cell
    perturbation or on the independent homogenisation layer;
  - corner diamond = the sign of the pooled ensemble change disagrees with the
    sign of the median of the models' changes.
Every channel is defined in the legend of each figure in full sentences, so any
one figure can be read on its own. Reads unified_cases.csv only. The layout is
computed in inches (header band, grid band, legend band) so that no text
overprints another element.
"""
import pathlib
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle

HERE = pathlib.Path(__file__).parent
STATIONS = ['London', 'Fergus', 'Harrow']
PREC = ['PRCPTOT', 'R10mm', 'R20mm', 'RX1day', 'RX3day', 'RX5day', 'SDII',
        'R95p', 'R95pTOT', 'R99p', 'R99pTOT', 'CDD', 'CWD']
PERC_DUR = ['CSDI6', 'CSDI3', 'WSDI6', 'WSDI3', 'TN10p', 'TN90p', 'TX10p', 'TX90p',
            'TXb3TNb3', 'GSL']

plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif", "Times New Roman"]})
CMAP = plt.get_cmap("RdBu")
NORM = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=0.5)

U = pd.read_csv(HERE / "unified_cases.csv").set_index(['station', 'index'])
ORDER = list(pd.read_csv(HERE / "unified_cases.csv").query("station=='London'")['index'])
ABSOLUTE = [i for i in ORDER if i not in PREC and i not in PERC_DUR]
GROUPS = [("Precipitation indices", PREC, "unified_precipitation"),
          ("Temperature indices — absolute and fixed-threshold", ABSOLUTE, "unified_temperature_absolute"),
          ("Temperature indices — percentile and duration", PERC_DUR, "unified_temperature_percentile_duration")]

HEADER_IN, LEGEND_IN, PITCH_IN, W_IN = 1.0, 3.35, 0.34, 7.8
CENTRES = [1.10, 2.20, 3.30]

def luminance(rgba):
    return 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]

def draw(title, indices, stem):
    n = len(indices)
    grid_in = n * PITCH_IN
    H = HEADER_IN + grid_in + LEGEND_IN
    fig = plt.figure(figsize=(W_IN, H))

    axh = fig.add_axes([0.015, 1 - HEADER_IN / H, 0.97, HEADER_IN / H]); axh.axis("off")
    axh.set_xlim(0, 100); axh.set_ylim(0, 10)
    axh.text(0, 8.6, title, fontsize=13.5, weight="bold", va="center")
    axh.text(0, 4.6, "Historical (1950–1986) to Present (1987–2023): each cell positions the observed change against the ten models'\n"
                     "changes and shows the direction of the models' median change, for London, Fergus and Harrow.",
             fontsize=9.3, va="center")

    ax = fig.add_axes([0.015, LEGEND_IN / H, 0.97, grid_in / H])
    ax.set_xlim(-0.05, 3.85); ax.set_ylim(n - 0.30, -1.25); ax.axis("off")
    for j, st in enumerate(STATIONS):
        ax.text(CENTRES[j], -0.92, st, ha="center", va="center", fontsize=10.5, weight="bold")
    for i, ix in enumerate(indices):
        ax.text(0.0, i, ix, ha="left", va="center", fontsize=9.5)
        for j, st in enumerate(STATIONS):
            r = U.loc[(st, ix)]
            rgba = CMAP(NORM(float(r.signed_margin)))
            flip = isinstance(r.perturbation_flip, str) and r.perturbation_flip != ''
            ax.add_patch(Rectangle((CENTRES[j] - 0.46, i - 0.44), 0.92, 0.88, facecolor=rgba,
                                   edgecolor="black" if flip else "0.55",
                                   linewidth=2.6 if flip else 0.6, zorder=2))
            ax.text(CENTRES[j], i + 0.02, str(r.arrow_median_sign), ha="center", va="center",
                    fontsize=14, color="white" if luminance(rgba) < 0.55 else "black", zorder=3)
            if bool(r.sign_disagreement):
                ax.plot([CENTRES[j] + 0.33], [i - 0.31], marker="D", markersize=5.5, markerfacecolor="black",
                        markeredgecolor="white", markeredgewidth=0.9, linestyle="none", zorder=4)

    axl = fig.add_axes([0.015, 0.0, 0.97, LEGEND_IN / H]); axl.axis("off")
    axl.set_xlim(0, 100); axl.set_ylim(0, 33.5)
    axl.plot([0, 100], [33.2, 33.2], color="0.4", lw=0.9)
    axl.text(0, 31.9, "How to read this figure", fontsize=10.5, weight="bold", va="center")
    axl.text(0, 29.0, "The arrow in each cell points in the direction of the median of the ten models' changes:\n"
                      "up for a positive median change, down for a negative one, and a flat dash where it is exactly zero.",
             fontsize=8.8, va="center")
    sm = plt.cm.ScalarMappable(norm=NORM, cmap=CMAP)
    cax = fig.add_axes([0.085, 2.46 / H, 0.40, 0.13 / H])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=[-1.0, -0.5, 0.0, 0.25, 0.5])
    cb.ax.tick_params(labelsize=8)
    axl.text(0, 19.8, "The colour of each cell gives the signed margin of the observed change: its distance to the nearest\n"
                      "edge of the ten models' range of changes, divided by that range's width. Positive values (blue)\n"
                      "place the observed change inside the range and negative values (red) place it outside it, and\n"
                      "deeper colour marks a position farther from the nearest edge. Zero sits exactly on a range edge.", fontsize=8.8, va="center")
    axl.add_patch(Rectangle((0.5, 12.65), 3.2, 1.7, facecolor="0.85", edgecolor="black", linewidth=2.6))
    axl.text(5.2, 13.5, "A heavy black border marks a case whose bounding classification changes when the station's\n"
                         "downscaled grid cell is moved one step, or on the audit's independent homogenisation layer,\n"
                         "so a bordered case is one whose printed classification is not stable.", fontsize=8.8, va="center")
    axl.plot([2.1], [7.2], marker="D", markersize=7, markerfacecolor="black",
             markeredgecolor="white", markeredgewidth=0.9, linestyle="none", clip_on=False)
    axl.text(5.2, 7.2, "A small diamond in the corner of a cell marks a case where the sign of the pooled ensemble\n"
                       "change disagrees with the sign of the median of the models' changes, so the two ensemble\n"
                       "summaries of the same ten changes do not point the same way.", fontsize=8.8, va="center")
    fig.savefig(HERE / f"{stem}.png", dpi=300)
    fig.savefig(HERE / f"{stem}.pdf")
    plt.close(fig)
    print("wrote", stem, f"({n} rows)")

for title, idxs, stem in GROUPS:
    draw(title, idxs, stem)
print("absolute group (21 expected):", len(ABSOLUTE))
