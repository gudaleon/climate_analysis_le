"""Reporting functions for the unified record, with the two output rules built in.

The design binds every output of the package with two rules, and they are
encoded here rather than left to the user. First, no reporting function
describes an envelope classification with verdict language: a position
outside the models' range is a position, reported as a rank and a margin,
never as a verdict on the ensemble. Second, every tally carries the ensemble
size and the expected outside fraction ``2/(N+1)`` beside the observed count,
because a count of cases outside a range is uninterpretable without the
fraction a reliable ensemble of that size is expected to leave outside by
construction.
"""
from __future__ import annotations

import pandas as pd

from .diagnostic import (
    CLASS_613_MAGNITUDE, CLASS_613_REVERSAL, CLASS_613_WITHIN,
    CLASS_V7_BOUNDED, CLASS_V7_REVERSAL, CLASS_V7_UNBOUNDED,
)
from .schema import INDEX, STATION

__all__ = ["tally", "rank_distribution", "summary_text"]

_SCHEMES = {
    "bounding_class_613": (CLASS_613_WITHIN, CLASS_613_MAGNITUDE, CLASS_613_REVERSAL),
    "bounding_class_v7": (CLASS_V7_BOUNDED, CLASS_V7_UNBOUNDED, CLASS_V7_REVERSAL),
}


def _ensemble_size(record: pd.DataFrame) -> int:
    sizes = sorted({int(n) for n in record["n_models"].dropna().unique() if int(n) > 0})
    if len(sizes) != 1:
        raise ValueError(
            "The record mixes ensemble sizes ("
            + ", ".join(str(s) for s in sizes)
            + "), so no single expected outside fraction applies; "
            "tally one ensemble size at a time."
        )
    return sizes[0]


def _outside_rows(record: pd.DataFrame) -> pd.Series:
    return record["signed_margin"].notna() & (record["signed_margin"] < 0)


def tally(record: pd.DataFrame, scheme: str = "bounding_class_613") -> pd.DataFrame:
    """Count the record's cases under one envelope classification scheme.

    Every row of the result carries the ensemble size, the number and
    fraction of cases outside the models' range, and the expected outside
    fraction ``2/(N+1)``, so the tally can never be read without the
    benchmark that makes it interpretable.
    """
    if scheme not in _SCHEMES:
        raise ValueError(f"Unknown classification scheme {scheme!r}; use one of {sorted(_SCHEMES)}.")
    n = _ensemble_size(record)
    positioned = record[record[scheme].notna()]
    outside = _outside_rows(record)
    outside_count = int(outside.sum())
    total = int(len(positioned))
    rows = []
    for label in _SCHEMES[scheme]:
        rows.append({
            "classification": label,
            "cases": int((positioned[scheme] == label).sum()),
            "ensemble_size": n,
            "cases_with_position": total,
            "observed_outside_cases": outside_count,
            "observed_outside_fraction": outside_count / total if total else float("nan"),
            "expected_outside_fraction": 2.0 / (n + 1),
        })
    return pd.DataFrame(rows)


def rank_distribution(record: pd.DataFrame) -> pd.DataFrame:
    """Count the record's cases at each observed rank.

    The rank distribution is the reliability statement of the diagnostic in
    its fullest form: a reliable ensemble spreads the observed changes across
    the whole range of ranks from 1 to N + 1, and concentration at the two
    extreme ranks, beyond the share ``2/(N+1)`` expected there, is the
    pattern that would indicate the ensemble's spread is too narrow.
    """
    ranks = record["obs_rank"].dropna()
    counts = ranks.value_counts().sort_index()
    return pd.DataFrame({"obs_rank": counts.index, "cases": counts.values})


def summary_text(record: pd.DataFrame) -> str:
    """A full-sentence summary of a unified record, with both output rules applied.

    The text reports each classification scheme's tally with the ensemble
    size and the expected outside fraction beside the observed count, states
    the observed outside fraction against that expectation, and names the
    cases where the two ensemble summaries disagree in sign, since those are
    the cases where either summary read alone would misstate the ensemble.
    """
    n = _ensemble_size(record)
    positioned = record[record["bounding_class_613"].notna()]
    total = len(positioned)
    outside_count = int(_outside_rows(record).sum())
    expected = 2.0 / (n + 1)
    observed_fraction = outside_count / total if total else float("nan")
    lines = [
        f"The record covers {len(record)} station-and-index cases, {total} of them carrying an "
        f"observed change to position, each computed against an ensemble of {n} models.",
    ]
    for scheme, wording in (
        ("bounding_class_613", "the within-range, magnitude-offset and directional-reversal scheme"),
        ("bounding_class_v7", "the Bounded, Unbounded and Sign Reversal scheme"),
    ):
        counts = positioned[scheme].value_counts()
        parts = ", ".join(f"{int(counts.get(label, 0))} {label}" for label in _SCHEMES[scheme])
        lines.append(
            f"Under {wording}, the tally is {parts}, so {outside_count} of the {total} positioned cases "
            f"fall outside the models' range. Beside that count, a reliable ensemble of {n} models is "
            f"expected to leave a fraction 2/({n}+1) = {expected:.3f} of cases outside its range by "
            f"construction; the observed outside fraction here is {observed_fraction:.3f}."
        )
    ranks = record["obs_rank"].dropna()
    if len(ranks):
        extreme = int(ranks.isin([1.0, float(n + 1)]).sum())
        lines.append(
            f"The observed changes occupy ranks from {ranks.min():g} to {ranks.max():g} among the "
            f"{n + 1} values formed by the model changes and the observation, with {extreme} cases at "
            f"the two extreme ranks."
        )
    disagreements = record[record["sign_disagreement"] == True]  # noqa: E712
    if len(disagreements):
        named = ", ".join(f"{row[STATION]} {row[INDEX]}" for _, row in disagreements.iterrows())
        lines.append(
            f"In {len(disagreements)} case(s) the sign of the pooled ensemble change disagrees with the "
            f"sign of the median of the model changes ({named}); the record carries both summaries for "
            f"those cases, because either one read alone would misstate the direction of the ensemble's "
            f"movement."
        )
    return "\n".join(lines)
