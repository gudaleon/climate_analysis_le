"""The tidy input schema and its validation.

The diagnostic consumes one tidy table of annual index values. Every row is
one annual value of one extremes index for one series, and the columns are:

``station``
    The station or site the series belongs to.
``index``
    The extremes index the value belongs to, such as ``PRCPTOT``.
``year``
    The calendar year the annual value describes.
``value``
    The annual index value. Missing values are allowed and are dropped from
    each analysis window before any summary is computed.
``kind``
    Either ``"model"`` for an ensemble member's series or ``"observed"`` for
    the observational series.
``model``
    The ensemble member's identifier for rows whose kind is ``"model"``. It
    is ignored for rows whose kind is ``"observed"`` and may be left empty
    there.
``family``
    An optional annotation naming the process family the index belongs to.
    The diagnostic carries it through to the record unchanged; it plays no
    part in any computation.
"""
from __future__ import annotations

import pandas as pd

__all__ = [
    "STATION", "INDEX", "YEAR", "VALUE", "KIND", "MODEL", "FAMILY",
    "KIND_MODEL", "KIND_OBSERVED", "REQUIRED_COLUMNS", "validate_tidy",
]

STATION = "station"
INDEX = "index"
YEAR = "year"
VALUE = "value"
KIND = "kind"
MODEL = "model"
FAMILY = "family"

KIND_MODEL = "model"
KIND_OBSERVED = "observed"

REQUIRED_COLUMNS = (STATION, INDEX, YEAR, VALUE, KIND, MODEL)


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Validate a tidy input table and return a cleaned copy of it.

    The returned frame has the schema's column types (year as an integer,
    value as a float) and carries the optional family column through when it
    is present. A ``ValueError`` is raised with a sentence naming the problem
    when a required column is missing, when a kind is neither ``"model"`` nor
    ``"observed"``, or when a model row carries no model identifier.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "The tidy input table is missing required column(s): "
            + ", ".join(missing)
            + ". The schema requires station, index, year, value, kind and model."
        )
    out = df.copy()
    kinds = set(out[KIND].dropna().unique())
    unknown = kinds - {KIND_MODEL, KIND_OBSERVED}
    if unknown:
        raise ValueError(
            "The kind column carries value(s) the schema does not define: "
            + ", ".join(sorted(str(k) for k in unknown))
            + ". Every row's kind must be \"model\" or \"observed\"."
        )
    model_rows = out[out[KIND] == KIND_MODEL]
    if model_rows[MODEL].isna().any() or (model_rows[MODEL].astype(str).str.strip() == "").any():
        raise ValueError(
            "Every row whose kind is \"model\" must carry the ensemble member's "
            "identifier in the model column."
        )
    out[YEAR] = out[YEAR].astype(int)
    out[VALUE] = out[VALUE].astype(float)
    return out
