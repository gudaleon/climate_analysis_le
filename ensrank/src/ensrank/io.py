"""Readers that produce the tidy input schema from annual index tables.

Climpact-style pipelines, including the ones the Wu thesis packages carry,
store annual index values as one wide table per series: the years run down
the rows and one extremes index occupies each column. The readers here turn
such tables into the tidy schema the diagnostic consumes, either one file at
a time or as a whole directory of files named in the Wu packages' form,
``{Station}_{Source}_annual.csv``, where the source token names an ensemble
member or an observational series whose token begins with ``OBS``.
"""
from __future__ import annotations

import pathlib

import pandas as pd

from .schema import FAMILY, INDEX, KIND, KIND_MODEL, KIND_OBSERVED, MODEL, STATION, VALUE, YEAR, validate_tidy

__all__ = ["annual_table_to_tidy", "read_annual_csv", "read_annual_directory"]


def annual_table_to_tidy(table: pd.DataFrame, station: str, kind: str,
                         model: str | None = None, family_map: dict | None = None) -> pd.DataFrame:
    """Convert one wide annual table to tidy rows for a single series.

    ``table`` is indexed by year and carries one column per extremes index.
    ``family_map``, when given, maps index names to process families and is
    recorded on the rows as the optional family annotation.
    """
    wide = table.copy()
    wide.index.name = YEAR
    long = wide.reset_index().melt(id_vars=YEAR, var_name=INDEX, value_name=VALUE)
    long[STATION] = station
    long[KIND] = kind
    long[MODEL] = model if kind == KIND_MODEL else None
    if family_map is not None:
        long[FAMILY] = long[INDEX].map(family_map)
    return long[[STATION, INDEX, YEAR, VALUE, KIND, MODEL] + ([FAMILY] if family_map is not None else [])]


def read_annual_csv(path, station: str, kind: str, model: str | None = None,
                    family_map: dict | None = None, round_ndigits: int | None = None) -> pd.DataFrame:
    """Read one wide annual index table from a CSV file into tidy rows.

    The file's first column is taken as the year. ``round_ndigits``, when
    given, rounds the values to that many decimal places as they are read,
    which is how an analysis layer that itself worked on rounded values is
    reproduced exactly.
    """
    table = pd.read_csv(path, index_col=0)
    if round_ndigits is not None:
        table = table.round(round_ndigits)
    return annual_table_to_tidy(table, station=station, kind=kind, model=model, family_map=family_map)


def read_annual_directory(directory, observed_source: str | None = None,
                          family_map: dict | None = None,
                          round_ndigits: int | None = None) -> pd.DataFrame:
    """Read a directory of Wu-form annual tables into one tidy frame.

    Every file named ``{Station}_{Source}_annual.csv`` contributes one
    series. A source token that names an ensemble member becomes that
    member's model series, and the observational series is the one whose
    source token equals ``observed_source``. A directory of the Wu form
    usually carries several observational variants side by side, for example
    the authors' own observed indices and an independently homogenised layer,
    so ``observed_source`` must name the intended variant whenever more than
    one is present; the function raises a ``ValueError`` naming the variants
    it found rather than choosing one silently.
    """
    directory = pathlib.Path(directory)
    files = sorted(directory.glob("*_annual.csv"))
    if not files:
        raise ValueError(f"No files named in the form {{Station}}_{{Source}}_annual.csv were found in {directory}.")
    parsed = []
    observed_tokens = set()
    for path in files:
        stem = path.name[: -len("_annual.csv")]
        station, _, source = stem.partition("_")
        if not station or not source:
            continue
        parsed.append((path, station, source))
        if source.startswith("OBS"):
            observed_tokens.add(source)
    if observed_source is None:
        if len(observed_tokens) == 1:
            observed_source = next(iter(observed_tokens))
        else:
            raise ValueError(
                "The directory carries more than one observational variant ("
                + ", ".join(sorted(observed_tokens))
                + "); name the intended one through the observed_source argument."
            )
    frames = []
    for path, station, source in parsed:
        if source.startswith("OBS"):
            if source != observed_source:
                continue
            frames.append(read_annual_csv(path, station=station, kind=KIND_OBSERVED,
                                          family_map=family_map, round_ndigits=round_ndigits))
        else:
            frames.append(read_annual_csv(path, station=station, kind=KIND_MODEL, model=source,
                                          family_map=family_map, round_ndigits=round_ndigits))
    if not frames:
        raise ValueError(f"No series could be read from {directory} with observed_source={observed_source!r}.")
    return validate_tidy(pd.concat(frames, ignore_index=True))
