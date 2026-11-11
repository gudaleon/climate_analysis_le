"""The unified glyph figures.

Each cell of a glyph grid is one station-and-index case, and every visual
channel is a coordinate of the unified record. The arrow gives the direction
of the median of the models' changes. The cell's colour gives the signed
margin of the observed change on a diverging scale, which cannot saturate to
one colour the way an agreement-count fill does, because inside positions
spread across the positive half of the scale and outside positions across the
negative half. A heavy border marks a case whose classification is not stable
under the perturbation branches recorded in the table's stability field, and
a corner diamond marks a case where the two ensemble summaries disagree in
sign. Every channel is defined in each figure's legend in full sentences, so
any one figure can be read on its own. The grids are split by index group,
following the prototype's composition, because a single grid of all indices
is illegible.
"""
from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import TwoSlopeNorm  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from .schema import INDEX, STATION  # noqa: E402

__all__ = ["PRECIPITATION_INDICES", "PERCENTILE_DURATION_INDICES", "default_groups",
           "plot_glyph_grid", "plot_group_figures"]

PRECIPITATION_INDICES = ["PRCPTOT", "R10mm", "R20mm", "RX1day", "RX3day", "RX5day", "SDII",
                         "R95p", "R95pTOT", "R99p", "R99pTOT", "CDD", "CWD"]
PERCENTILE_DURATION_INDICES = ["CSDI6", "CSDI3", "WSDI6", "WSDI3", "TN10p", "TN90p", "TX10p",
                               "TX90p", "TXb3TNb3", "GSL"]

plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif", "Times New Roman"]})
_CMAP = plt.get_cmap("RdBu")
_NORM = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=0.5)

_HEADER_IN, _LEGEND_IN, _PITCH_IN, _W_IN = 1.0, 3.35, 0.34, 7.8


def default_groups(record) -> list[tuple[str, list[str], str]]:
    """The prototype's three index groups, restricted to the record's indices.

    The groups are the precipitation indices, the temperature indices that
    are neither precipitation nor percentile-and-duration indices, and the
    percentile-and-duration temperature indices, in the record's own order.
    """
    present = list(dict.fromkeys(record[INDEX]))
    precipitation = [i for i in PRECIPITATION_INDICES if i in present]
    percentile = [i for i in PERCENTILE_DURATION_INDICES if i in present]
    absolute = [i for i in present if i not in PRECIPITATION_INDICES and i not in PERCENTILE_DURATION_INDICES]
    groups = []
    if precipitation:
        groups.append(("Precipitation indices", precipitation, "unified_precipitation"))
    if absolute:
        groups.append(("Temperature indices — absolute and fixed-threshold", absolute,
                       "unified_temperature_absolute"))
    if percentile:
        groups.append(("Temperature indices — percentile and duration", percentile,
                       "unified_temperature_percentile_duration"))
    return groups


def _luminance(rgba) -> float:
    return 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]


def plot_glyph_grid(record, indices, title, subtitle=None, stations=None,
                    flip_column="perturbation_flip"):
    """Draw one glyph grid for the given indices and return the figure.

    ``stations`` defaults to the record's stations in their order of first
    appearance. The heavy-border channel reads the record's ``flip_column``,
    which names the perturbation branches under which a case's classification
    changes and is empty for a stable case; when the record carries no such
    column, no border is drawn.
    """
    table = record.set_index([STATION, INDEX])
    if stations is None:
        stations = list(dict.fromkeys(record[STATION]))
    centres = [1.10 + 1.10 * j for j in range(len(stations))]
    n_models = int(record["n_models"].max())
    n = len(indices)
    grid_in = n * _PITCH_IN
    height = _HEADER_IN + grid_in + _LEGEND_IN
    fig = plt.figure(figsize=(_W_IN, height))

    axh = fig.add_axes([0.015, 1 - _HEADER_IN / height, 0.97, _HEADER_IN / height])
    axh.axis("off")
    axh.set_xlim(0, 100)
    axh.set_ylim(0, 10)
    axh.text(0, 8.6, title, fontsize=13.5, weight="bold", va="center")
    if subtitle is None:
        subtitle = ("Each cell positions the observed change against the models' changes and shows\n"
                    "the direction of the models' median change, for "
                    + ", ".join(stations) + ".")
    axh.text(0, 4.6, subtitle, fontsize=9.3, va="center")

    ax = fig.add_axes([0.015, _LEGEND_IN / height, 0.97, grid_in / height])
    ax.set_xlim(-0.05, centres[-1] + 0.55)
    ax.set_ylim(n - 0.30, -1.25)
    ax.axis("off")
    for j, station in enumerate(stations):
        ax.text(centres[j], -0.92, station, ha="center", va="center", fontsize=10.5, weight="bold")
    for i, index in enumerate(indices):
        ax.text(0.0, i, index, ha="left", va="center", fontsize=9.5)
        for j, station in enumerate(stations):
            if (station, index) not in table.index:
                continue
            row = table.loc[(station, index)]
            rgba = _CMAP(_NORM(float(row["signed_margin"])))
            flip = flip_column in table.columns and isinstance(row[flip_column], str) and row[flip_column] != ""
            ax.add_patch(Rectangle((centres[j] - 0.46, i - 0.44), 0.92, 0.88, facecolor=rgba,
                                   edgecolor="black" if flip else "0.55",
                                   linewidth=2.6 if flip else 0.6, zorder=2))
            ax.text(centres[j], i + 0.02, str(row["arrow_median_sign"]), ha="center", va="center",
                    fontsize=14, color="white" if _luminance(rgba) < 0.55 else "black", zorder=3)
            if bool(row["sign_disagreement"]):
                ax.plot([centres[j] + 0.33], [i - 0.31], marker="D", markersize=5.5,
                        markerfacecolor="black", markeredgecolor="white", markeredgewidth=0.9,
                        linestyle="none", zorder=4)

    axl = fig.add_axes([0.015, 0.0, 0.97, _LEGEND_IN / height])
    axl.axis("off")
    axl.set_xlim(0, 100)
    axl.set_ylim(0, 33.5)
    axl.plot([0, 100], [33.2, 33.2], color="0.4", lw=0.9)
    axl.text(0, 31.9, "How to read this figure", fontsize=10.5, weight="bold", va="center")
    axl.text(0, 29.0, f"The arrow in each cell points in the direction of the median of the {n_models} models' changes:\n"
                      "up for a positive median change, down for a negative one, and a flat dash where it is exactly zero.",
             fontsize=8.8, va="center")
    sm = plt.cm.ScalarMappable(norm=_NORM, cmap=_CMAP)
    cax = fig.add_axes([0.085, 2.46 / height, 0.40, 0.13 / height])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=[-1.0, -0.5, 0.0, 0.25, 0.5])
    cb.ax.tick_params(labelsize=8)
    axl.text(0, 19.8, f"The colour of each cell gives the signed margin of the observed change: its distance to the nearest\n"
                      f"edge of the {n_models} models' range of changes, divided by that range's width. Positive values (blue)\n"
                      "place the observed change inside the range and negative values (red) place it outside it, and\n"
                      "deeper colour marks a position farther from the nearest edge. Zero sits exactly on a range edge.",
             fontsize=8.8, va="center")
    axl.add_patch(Rectangle((0.5, 12.65), 3.2, 1.7, facecolor="0.85", edgecolor="black", linewidth=2.6))
    axl.text(5.2, 13.5, "A heavy black border marks a case whose bounding classification changes under at least one\n"
                        "alternative extraction of the same cases, as recorded in the table's stability field,\n"
                        "so a bordered case is one whose printed classification is not stable.", fontsize=8.8, va="center")
    axl.plot([2.1], [7.2], marker="D", markersize=7, markerfacecolor="black",
             markeredgecolor="white", markeredgewidth=0.9, linestyle="none", clip_on=False)
    axl.text(5.2, 7.2, "A small diamond in the corner of a cell marks a case where the sign of the pooled ensemble\n"
                       "change disagrees with the sign of the median of the models' changes, so the two ensemble\n"
                       f"summaries of the same {n_models} changes do not point the same way.",
             fontsize=8.8, va="center")
    return fig


def plot_group_figures(record, outdir, groups=None, dpi=300, formats=("png", "pdf")):
    """Draw the glyph figure set and write it into ``outdir``.

    ``groups`` defaults to :func:`default_groups`. Each group is written once
    per format under its stem, and the list of written paths is returned.
    """
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if groups is None:
        groups = default_groups(record)
    written = []
    for title, indices, stem in groups:
        fig = plot_glyph_grid(record, indices, title)
        for fmt in formats:
            path = outdir / f"{stem}.{fmt}"
            fig.savefig(path, dpi=dpi)
            written.append(path)
        plt.close(fig)
    return written
