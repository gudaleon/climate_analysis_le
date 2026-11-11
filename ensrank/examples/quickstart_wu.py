"""Quickstart: reproduce the Wu thesis programme's unified table and figures.

This worked example runs the package end to end on the audit's own annual
index tables, which live outside the package in the programme's workspace.
It reads the thesis-cell tables with the authors' observed series, computes
the unified record for the Historical (1950-1986) to Present (1987-2023)
contrast, runs the four perturbation branches the programme executed (the
independent homogenisation layer and each station's one-step grid-cell
perturbation), attaches the resulting stability field, and writes the table,
the glyph figure set and the reporting summary into an output folder.

The thesis's index list and process-family assignment are analysis
configuration rather than package output, so the example reads them from the
prototype table the programme verified, and supplies them to the diagnostic
as its family mapping and index selection.

Run it with the package installed, from anywhere:

    python examples/quickstart_wu.py [output_dir]
"""
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ensrank import (  # noqa: E402
    combine_stability, diagnose, plot_group_figures, read_annual_directory,
    run_perturbation, stability_field, summary_text,
)

PACKAGE_DIR = pathlib.Path(__file__).resolve().parents[1]
ROOT = PACKAGE_DIR.parents[1]  # ~/workspace/jeremy_wu_redteam
WU = ROOT / "executor_runs" / "wu_claude"
PROTOTYPE_TABLE = PACKAGE_DIR.parent / "unified_cases.csv"
ADDENDA = {"Fergus": ("out_addA", "Addendum A"), "Harrow": ("out_addB", "Addendum B"),
           "London": ("out_addC", "Addendum C")}


def main(output_dir: str = "quickstart_output") -> None:
    prototype = pd.read_csv(PROTOTYPE_TABLE)
    indices = sorted(prototype["index"].unique())
    family = {(r.station, r.index): r.process_family for r in prototype.itertuples()}
    family_map = {index: fam for (_, index), fam in family.items()}

    def load(directory, observed):
        frame = read_annual_directory(directory, observed_source=observed, round_ndigits=6)
        return frame[frame["index"].isin(indices)]

    base_frame = load(WU / "out" / "idx", "OBS_AUTHORS_v4")
    record = diagnose(base_frame, family_map=family_map)

    _, _, comparison_h1 = run_perturbation(
        base_frame, load(WU / "out" / "idx", "OBS_H1_reviewed"), family_map=family_map)
    branch_fields = []
    for station, (folder, addendum) in ADDENDA.items():
        alt_full = load(WU / folder / "idx", "OBS_AUTHORS_v4")
        alt_frame = pd.concat(
            [base_frame[base_frame["station"] != station],
             alt_full[alt_full["station"] == station]], ignore_index=True)
        _, _, comparison = run_perturbation(base_frame, alt_frame, family_map=family_map)
        branch_fields.append(stability_field(
            comparison, f"{station} grid-cell perturbation ({addendum})"))
    branch_fields.append(stability_field(comparison_h1, "H1 homogenisation layer"))
    combined = combine_stability(branch_fields)
    record = record.set_index(["station", "index"])
    record["perturbation_flip"] = [combined.loc[key] for key in record.index]
    record = record.reset_index()

    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    table_path = out / "unified_cases_ensrank.csv"
    record.drop(columns=["model_changes"]).to_csv(table_path, index=False)
    written = plot_group_figures(record, out)
    print(summary_text(record))
    print(f"\nWrote {table_path} ({len(record)} cases) and {len(written)} figure files in {out}.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "quickstart_output")
