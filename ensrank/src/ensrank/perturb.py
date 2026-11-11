"""The perturbation module: the same diagnostic on an alternative input set.

A perturbation branch is any defensible alternative extraction of the same
cases: the neighbouring grid cell of a downscaled product in place of the
thesis cell, or an alternative processing layer such as an independent
homogenisation of the observed series. The module recomputes the unified
record on the alternative frame and reports, case by case, which outputs
changed, because the programme's central empirical lesson is that the
classification layer is fragile at its edges and a diagnostic that prints a
position without its stability overstates its own findings.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .diagnostic import diagnose
from .schema import INDEX, STATION

__all__ = ["TRACKED_FIELDS", "compare_records", "run_perturbation", "stability_field", "combine_stability"]

#: The record fields whose movement under a perturbation branch is reported.
TRACKED_FIELDS = (
    "obs_change",
    "median_model_change",
    "pooled_ensemble_change",
    "pooled_wilcoxon_p",
    "model_agreement_count",
    "obs_rank",
    "signed_margin",
    "bounding_class_613",
    "bounding_class_v7",
    "arrow_median_sign",
    "arrow_pooled_sign",
    "sign_disagreement",
)

_NUMERIC_FIELDS = {
    "obs_change", "median_model_change", "pooled_ensemble_change", "pooled_wilcoxon_p",
    "obs_rank", "signed_margin",
}


def _values_differ(a, b, field: str, tol: float) -> bool:
    if field in _NUMERIC_FIELDS:
        a_nan = a is None or (isinstance(a, float) and math.isnan(a))
        b_nan = b is None or (isinstance(b, float) and math.isnan(b))
        if a_nan or b_nan:
            return a_nan != b_nan
        return abs(float(a) - float(b)) > tol
    return a != b


def compare_records(base_record: pd.DataFrame, alt_record: pd.DataFrame, tol: float = 1e-9) -> pd.DataFrame:
    """Compare two diagnostic records case by case.

    Both records must cover the same station-and-index cases. The comparison
    has one row per case and reports the tuple of tracked fields that changed,
    whether each envelope classification changed, the movement of the signed
    margin, and a stability sentence that names each change, which is empty
    when no tracked field moved. A case whose classification survives every
    branch the user runs is stable against exactly those branches, and the
    sentence says so by its emptiness rather than by a claim about branches
    that were never run.
    """
    base = base_record.set_index([STATION, INDEX])
    alt = alt_record.set_index([STATION, INDEX])
    if set(base.index) != set(alt.index):
        raise ValueError(
            "The two records do not cover the same cases: "
            f"{len(base)} cases in the first record and {len(alt)} in the second, "
            "with differing station-and-index pairs."
        )
    rows = []
    for key in base.index:
        b, a = base.loc[key], alt.loc[key]
        changed = tuple(f for f in TRACKED_FIELDS if _values_differ(b[f], a[f], f, tol))
        parts = []
        for field in changed:
            if field in _NUMERIC_FIELDS:
                parts.append(f"{field}: {float(b[field]):.6g} -> {float(a[field]):.6g}")
            else:
                parts.append(f"{field}: {b[field]} -> {a[field]}")
        rows.append({
            STATION: key[0],
            INDEX: key[1],
            "changed_fields": changed,
            "n_changed": len(changed),
            "classification_flip_613": "bounding_class_613" in changed,
            "classification_flip_v7": "bounding_class_v7" in changed,
            "signed_margin_base": b["signed_margin"],
            "signed_margin_alt": a["signed_margin"],
            "margin_change": (float(a["signed_margin"]) - float(b["signed_margin"]))
            if not (isinstance(b["signed_margin"], float) and math.isnan(b["signed_margin"])
                    or isinstance(a["signed_margin"], float) and math.isnan(a["signed_margin"])) else math.nan,
            "stability": "; ".join(parts),
        })
    return pd.DataFrame(rows)


def run_perturbation(df, df_alternative, base=(1950, 1986), window=(1987, 2023), family_map: dict | None = None):
    """Diagnose a base frame and an alternative frame and compare the records.

    Returns the triple ``(base_record, alternative_record, comparison)`` so
    the user keeps both full records beside the case-by-case account of what
    the alternative extraction changed.
    """
    base_record = diagnose(df, base=base, window=window, family_map=family_map)
    alt_record = diagnose(df_alternative, base=base, window=window, family_map=family_map)
    return base_record, alt_record, compare_records(base_record, alt_record)


def stability_field(comparison: pd.DataFrame, branch_label: str) -> pd.Series:
    """The prototype-shaped stability field for one perturbation branch.

    The result is indexed by station and index and carries ``branch_label``
    for exactly the cases whose 6.13-lineage classification changed on this
    branch, and an empty string for every other case.
    """
    field = pd.Series(
        [branch_label if flip else "" for flip in comparison["classification_flip_613"]],
        index=pd.MultiIndex.from_frame(comparison[[STATION, INDEX]]),
        name="perturbation_flip",
    )
    return field


def combine_stability(branch_fields) -> pd.Series:
    """Combine per-branch stability fields into one field per case.

    ``branch_fields`` is a sequence of series as returned by
    :func:`stability_field`, in the order the branches are to be named. For
    each case the combined field joins the non-empty branch labels with
    ``"; "`` in that order, and is empty for a case that flipped on no branch.
    """
    if not branch_fields:
        raise ValueError("combine_stability needs at least one branch field.")
    index = branch_fields[0].index
    combined = []
    for key in index:
        labels = [field.loc[key] for field in branch_fields]
        combined.append("; ".join(label for label in labels if label))
    return pd.Series(combined, index=index, name="perturbation_flip")
