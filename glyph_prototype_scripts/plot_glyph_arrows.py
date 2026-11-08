"""Glyph summary prototype, one figure per index group (Alex Neumann's composition direction:
the combined 44-index panel was too busy). Contrasts: Far Future (2063-2100) vs Historical
(1950-1986) and Near Future (2024-2062) vs Historical (1950-1986), ten-model ensemble, thesis
branch, stations London, Fergus and Harrow. Usage: plot_glyph_arrows.py [far|near|all] (default all).
Reads glyph_channel_data_<contrast>.csv (built by build_glyph_data.py from the verified recompute layer).
Channels in every figure: arrow direction = sign of the median of the ten models' changes; arrow size =
|median change| / IQR of the models' changes, sqrt-scaled, capped at 5; disc fill = model agreement
count (cividis, numbers in the legend, one colour scale in every figure); border = Wilcoxon rank-sum
significance of the pooled ensemble change (p < 0.05 heavy black, otherwise light grey).
Each figure carries its own complete legend."""
import pathlib, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

HERE = pathlib.Path(__file__).parent
STATIONS = ['London', 'Fergus', 'Harrow']
PREC = ['PRCPTOT','R10mm','R20mm','RX1day','RX3day','RX5day','SDII','R95p','R95pTOT','R99p','R99pTOT','CDD','CWD']
PERC_DUR = ['CSDI6','CSDI3','WSDI6','WSDI3','TN10p','TN90p','TX10p','TX90p','TXb3TNb3','GSL']
CAP = 5.0
DISC_S = 380                        # disc diameter about 22 pt on a 24.5 pt row pitch: rows never touch
def arrow_s(ratio):
    return 24 + 150*np.sqrt(min(ratio, CAP)/CAP)

plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif", "Times New Roman"]})
cmap = plt.get_cmap("cividis")
def colour(a):
    return cmap(0.08 + 0.84*(a - 4)/6.0)          # agreement scale fixed at 4..10 in every figure; counts below 4 take the darkest end

CONTRASTS = {
    'far': dict(
        csv="glyph_channel_data_far_future.csv",
        subtitle="Far Future (2063–2100) against Historical (1950–1986), ten-model ensemble. One glyph per station and index:\n"
                 "direction is the sign of the median model change; size is the change relative to the model spread.",
        stems=["glyph_arrows_far_future_precipitation",
               "glyph_arrows_far_future_temperature_absolute",
               "glyph_arrows_far_future_temperature_percentile_duration"],
        swatches=list(range(4, 11)),
        agree_note="Counts of 4 to 6 occur only for cold-wave amplitude (CWA), whose change is\ndefined for only 4 to 6 of the models; every other cell counts out of 10."),
    'near': dict(
        csv="glyph_channel_data_near_future.csv",
        subtitle="Near Future (2024–2062) against Historical (1950–1986), ten-model ensemble. One glyph per station and index:\n"
                 "direction is the sign of the median model change; size is the change relative to the model spread.",
        stems=["glyph_arrows_near_future_precipitation",
               "glyph_arrows_near_future_temperature_absolute",
               "glyph_arrows_near_future_temperature_percentile_duration"],
        swatches=[2, 4, 5, 6, 7, 8, 9, 10],
        agree_note="Counts of 2 and 4 occur only in flat-dash cells (median change exactly zero),\nwhere the count is the number of models with exactly no change."),
}

def legend(axl, cfg):
    axl.axis("off"); axl.set_xlim(0, 100); axl.set_ylim(-0.6, 10)
    axl.plot([1, 99], [9.9, 9.9], color="0.4", lw=0.9)
    axl.text(1, 8.9, "Model agreement: models (of 10) whose change agrees in sign with the median change.", fontsize=9.2, va="center")
    x = 3.0
    for a in cfg['swatches']:
        fc = colour(a)
        axl.scatter([x], [7.35], s=300, marker="o", facecolor=fc, edgecolor="0.3", linewidth=0.7)
        lum = 0.299*fc[0] + 0.587*fc[1] + 0.114*fc[2]
        axl.text(x, 7.35, str(a), ha="center", va="center", fontsize=7.8, fontweight="bold",
                 color="black" if lum > 0.55 else "white")
        x += 4.4
    axl.text(x + 1.5, 7.35, cfg['agree_note'], fontsize=8.2, va="center")
    axl.text(1, 5.55, "Relative magnitude: |median change| divided by the interquartile range of the models' changes.", fontsize=9.2, va="center")
    x = 3.0
    for val, lab in [(0.5, "0.5"), (1, "1"), (2, "2"), (3, "3"), (5, "≥5 (cap)")]:
        axl.scatter([x], [4.05], s=arrow_s(val), marker="^", color="0.25")
        axl.text(x, 3.0, lab, ha="center", fontsize=8.2)
        x += 6.0
    axl.text(x + 1.0, 4.05, "Size compares a change with the spread of its own index only;\nit does not compare absolute changes between indices.",
             fontsize=8.2, va="center")
    axl.scatter([3.0], [1.75], s=260, marker="o", facecolor="white", edgecolor="black", linewidth=2.2)
    axl.text(5.2, 1.75, "Heavy border: ensemble change significant (two-sided Wilcoxon rank-sum test, p < 0.05).", fontsize=9.2, va="center")
    axl.scatter([3.0], [0.55], s=260, marker="o", facecolor="white", edgecolor="0.62", linewidth=0.8)
    axl.text(5.2, 0.55, "Light border: not significant.   —   Flat dash inside a disc: median change exactly zero.", fontsize=9.2, va="center")

def render(df, cfg, title, indices, fname):
    rows_in = len(indices) * 0.34
    fig = plt.figure(figsize=(8.27, 1.05 + rows_in + 2.75))
    gs = GridSpec(3, 1, height_ratios=[1.05, rows_in, 2.75], hspace=0.04,
                  left=0.055, right=0.985, top=0.99, bottom=0.012)
    axh = fig.add_subplot(gs[0]); axh.axis("off"); axh.set_xlim(0, 10); axh.set_ylim(0, 1)
    axh.text(5, 0.66, f"{title}", ha="center", va="center", fontsize=13, fontweight="bold")
    axh.text(5, 0.24, cfg['subtitle'], ha="center", va="center", fontsize=8.8)
    ax = fig.add_subplot(gs[1]); ax.axis("off")
    n = len(indices)
    ax.set_xlim(-1.15, 2.75); ax.set_ylim(n - 0.35, -1.85)
    for j, st in enumerate(STATIONS):
        ax.text(j, -1.15, st, ha="center", va="center", fontsize=11.5, fontweight="bold")
    ax.plot([-0.5, 2.5], [-0.62, -0.62], color="0.4", lw=0.9)
    for r, ix in enumerate(indices):
        ax.text(-0.18, r, ix, ha="right", va="center", fontsize=9.2)
        for j, st in enumerate(STATIONS):
            row = df[(df.station == st) & (df['index'] == ix)].iloc[0]
            sig = bool(row.significant)
            fc = colour(int(row.agreement))
            ax.scatter([j], [r], s=DISC_S, marker="o", facecolor=fc,
                       edgecolor="black" if sig else "0.62", linewidth=2.2 if sig else 0.8, zorder=3)
            lum = 0.299*fc[0] + 0.587*fc[1] + 0.114*fc[2]
            ac = "black" if lum > 0.55 else "white"
            marker = "^" if row.direction == "↑" else ("v" if row.direction == "↓" else "_")
            m = ax.scatter([j], [r], s=arrow_s(float(row.relative_magnitude_capped)), marker=marker, color=ac, zorder=4)
            if marker == "_":
                m.set_linewidths([2.4])
    legend(fig.add_subplot(gs[2]), cfg)
    fig.savefig(HERE/f"{fname}.png", dpi=300)
    fig.savefig(HERE/f"{fname}.pdf")
    plt.close(fig)
    print("saved", fname, f"({n} indices)")

def run(key):
    cfg = CONTRASTS[key]
    df = pd.read_csv(HERE/cfg['csv'])
    ORDER = list(dict.fromkeys(df['index']))
    TEMP = [i for i in ORDER if i not in PREC]
    ABSOLUTE = [i for i in TEMP if i not in PERC_DUR]
    groups = [
        ("Precipitation indices", PREC, cfg['stems'][0]),
        ("Temperature indices — absolute and fixed-threshold", ABSOLUTE, cfg['stems'][1]),
        ("Temperature indices — percentile and duration", [i for i in TEMP if i in PERC_DUR], cfg['stems'][2]),
    ]
    for title, idxs, fname in groups:
        render(df, cfg, title, idxs, fname)

which = sys.argv[1] if len(sys.argv) > 1 else 'all'
for k in (list(CONTRASTS) if which == 'all' else [which]):
    run(k)
