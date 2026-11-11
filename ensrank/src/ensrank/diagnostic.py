"""The unified ensemble-change diagnostic.

For one contrast between a base window and a comparison window, and for each
station-and-index case, the diagnostic computes one record that carries the
programme's two post hoc approaches as coordinates of a single object.

The direction coordinate summarises the ensemble's own movement. Changes are
computed inside each series first, one change per model, as the difference
between the series' median annual value in the comparison window and its
median in the base window; the record then carries both ensemble summaries of
those per-model changes side by side, namely the median of the model changes
and the pooled ensemble change, the latter computed on the annual values of
all models pooled together, with its Wilcoxon rank-sum p-value. Where the two
summaries carry different signs the record flags the disagreement rather than
letting either statistic silently stand for the ensemble.

The position coordinate places the observed change among the model changes.
The record carries the observed change's rank among the N + 1 values formed
by the N model changes and itself, as a midrank so that ties share a rank,
and its signed margin: the distance from the observed change to the nearest
edge of the models' range of changes, divided by that range's width, positive
inside the range and negative outside it, and zero when the range has no
width. Both envelope classifiers the programme used are derived on the
record, so a user migrating from either thesis lineage can reconcile the new
output against their printed tables. Neither classifier's labels are verdicts:
the reporting functions in :mod:`ensrank.report` state what an outside
position means against the outside fraction a reliable ensemble is expected
to produce.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .schema import FAMILY, INDEX, KIND, KIND_MODEL, KIND_OBSERVED, MODEL, STATION, VALUE, YEAR, validate_tidy
from .stats import wilcoxon_rank_sum

__all__ = [
    "CLASS_613_WITHIN", "CLASS_613_MAGNITUDE", "CLASS_613_REVERSAL",
    "CLASS_V7_BOUNDED", "CLASS_V7_UNBOUNDED", "CLASS_V7_REVERSAL",
    "classify_613", "classify_v7", "signed_margin", "observed_rank",
    "series_changes", "diagnose",
]

CLASS_613_WITHIN = "within range"
CLASS_613_MAGNITUDE = "magnitude offset"
CLASS_613_REVERSAL = "directional reversal"

CLASS_V7_BOUNDED = "Bounded"
CLASS_V7_UNBOUNDED = "Unbounded"
CLASS_V7_REVERSAL = "Sign Reversal"


def _sign(x: float) -> int:
    if x == 0:
        return 0
    return 1 if x > 0 else -1


def _sign_glyph(x) -> str | None:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if x == 0:
        return "–"
    return "↑" if x > 0 else "↓"


def classify_613(obs_change: float, range_lo: float, range_hi: float, ensemble_median_change: float) -> str:
    """Classify an observed change under the 6.13 lineage's envelope scheme.

    The case is within range when the observed change lies between the
    smallest and largest model changes inclusive. Outside the range, it is a
    directional reversal when the observed change's sign is the opposite of
    the sign of the median of the model changes, and a magnitude offset
    otherwise.
    """
    if range_lo <= obs_change <= range_hi:
        return CLASS_613_WITHIN
    if _sign(obs_change) != 0 and _sign(obs_change) == -_sign(ensemble_median_change):
        return CLASS_613_REVERSAL
    return CLASS_613_MAGNITUDE


def classify_v7(obs_change: float, range_lo: float, range_hi: float) -> str:
    """Classify an observed change under the v7 lineage's envelope scheme.

    The case is Bounded when the observed change lies between the smallest
    and largest model changes inclusive. Outside the range, it is a Sign
    Reversal only when the whole model range carries the opposite sign to the
    observed change, and Unbounded otherwise, including when the range
    straddles zero.
    """
    if range_lo <= obs_change <= range_hi:
        return CLASS_V7_BOUNDED
    if _sign(range_lo) == _sign(range_hi) and _sign(range_lo) == -_sign(obs_change) and obs_change != 0:
        return CLASS_V7_REVERSAL
    return CLASS_V7_UNBOUNDED


def signed_margin(obs_change: float, range_lo: float, range_hi: float) -> float:
    """The signed margin of an observed change against the models' range.

    The margin is the distance from the observed change to the nearest edge
    of the range, divided by the range's width. It is positive when the
    observed change sits inside the range, negative when it sits outside, and
    zero when it sits exactly on an edge or when the range has no width.
    """
    width = range_hi - range_lo
    if width <= 0:
        return 0.0
    return min(obs_change - range_lo, range_hi - obs_change) / width


def observed_rank(obs_change: float, model_changes) -> float:
    """The observed change's rank among the model changes plus itself.

    The rank is a midrank: it counts the model changes strictly below the
    observed change, plus one, plus half the model changes tied with it, so a
    case whose observed change ties with model changes carries a half-integer
    rank. The observed change sits outside the models' range exactly when
    this rank is 1 or N + 1 and no tie shares the extreme position.
    """
    d = np.asarray(model_changes, dtype=float)
    return 1.0 + float((d < obs_change).sum()) + 0.5 * float((d == obs_change).sum())


def _window_values(years: np.ndarray, values: np.ndarray, window) -> np.ndarray:
    a, b = window
    selected = values[(years >= a) & (years <= b)]
    return selected[~np.isnan(selected)]


def _period_change(years, values, base, window) -> float:
    base_values = _window_values(years, values, base)
    window_values = _window_values(years, values, window)
    if len(base_values) == 0 or len(window_values) == 0:
        return math.nan
    return float(np.median(window_values) - np.median(base_values))


def series_changes(df: pd.DataFrame, base=(1950, 1986), window=(1987, 2023)) -> pd.DataFrame:
    """Compute the per-series change for every series in a tidy frame.

    The change of one series is the difference between its median annual
    value in the comparison window and its median annual value in the base
    window, with missing annual values dropped from each window. The result
    has one row per station, index, kind and model, which is the level at
    which changes are computed before any ensemble summary is taken.
    """
    frame = validate_tidy(df)
    rows = []
    keys = [STATION, INDEX, KIND, MODEL]
    for (station, index, kind, model), group in frame.groupby(keys, dropna=False, sort=True):
        years = group[YEAR].to_numpy()
        values = group[VALUE].to_numpy(dtype=float)
        rows.append({
            STATION: station, INDEX: index, KIND: kind, MODEL: model,
            "change": _period_change(years, values, base, window),
        })
    return pd.DataFrame(rows)


def diagnose(df: pd.DataFrame, base=(1950, 1986), window=(1987, 2023),
             family_map: dict | None = None) -> pd.DataFrame:
    """Compute the unified diagnostic record for every case in a tidy frame.

    ``base`` and ``window`` are inclusive ``(first_year, last_year)`` pairs.
    The record has one row per station-and-index case and carries both
    ensemble summaries, the observed change's rank and signed margin, both
    envelope classifications, and the expected outside fraction ``2/(N+1)``
    for the case's ensemble size N. A case with no observational series, or
    with windows too empty to form an observed change, yields a
    direction-only record whose position fields are empty, which is the form
    the diagnostic takes for future contrasts where no observation exists.
    """
    frame = validate_tidy(df)
    series: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}
    for (station, index, kind, model), group in frame.groupby([STATION, INDEX, KIND, MODEL], dropna=False, sort=True):
        series[(station, index, kind, model)] = (group[YEAR].to_numpy(), group[VALUE].to_numpy(dtype=float))

    families: dict[tuple, object] = {}
    if FAMILY in frame.columns:
        for (station, index), group in frame.groupby([STATION, INDEX], sort=True):
            value = group[FAMILY].dropna()
            families[(station, index)] = value.iloc[0] if len(value) else None
    if family_map is not None:
        for station in frame[STATION].unique():
            for index, family in family_map.items():
                families[(station, index)] = family

    cases = sorted({(station, index) for (station, index, _, _) in series})
    rows = []
    for station, index in cases:
        model_ids = sorted({m for (s, i, k, m) in series if s == station and i == index and k == KIND_MODEL})
        changes = []
        pooled_base, pooled_window = [], []
        for model in model_ids:
            years, values = series[(station, index, KIND_MODEL, model)]
            change = _period_change(years, values, base, window)
            if not math.isnan(change):
                changes.append(change)
            pooled_base.append(_window_values(years, values, base))
            pooled_window.append(_window_values(years, values, window))
        d = np.array(changes, dtype=float)
        n = len(d)

        if pooled_base and pooled_window:
            base_pool = np.concatenate(pooled_base) if pooled_base else np.array([])
            window_pool = np.concatenate(pooled_window) if pooled_window else np.array([])
            if len(base_pool) and len(window_pool):
                pooled_change = float(np.median(window_pool) - np.median(base_pool))
                pooled_p = wilcoxon_rank_sum(base_pool, window_pool)
            else:
                pooled_change, pooled_p = math.nan, math.nan
        else:
            pooled_change, pooled_p = math.nan, math.nan

        obs_change = math.nan
        obs_keys = [key for key in series if key[0] == station and key[1] == index and key[2] == KIND_OBSERVED]
        if obs_keys:
            years, values = series[obs_keys[0]]
            obs_change = _period_change(years, values, base, window)

        if n:
            range_lo, range_hi = float(d.min()), float(d.max())
            median_change = float(np.median(d))
            if median_change != 0:
                agreement = int((np.sign(d) == np.sign(median_change)).sum())
            else:
                agreement = int((d == 0).sum())
        else:
            range_lo = range_hi = median_change = math.nan
            agreement = 0

        has_position = n > 0 and not math.isnan(obs_change)
        rows.append({
            STATION: station,
            INDEX: index,
            "process_family": families.get((station, index)),
            "n_models": n,
            "obs_change": obs_change if has_position else math.nan,
            "model_range_lo": range_lo,
            "model_range_hi": range_hi,
            "bounding_class_613": classify_613(obs_change, range_lo, range_hi, median_change) if has_position else None,
            "bounding_class_v7": classify_v7(obs_change, range_lo, range_hi) if has_position else None,
            "signed_margin": signed_margin(obs_change, range_lo, range_hi) if has_position else math.nan,
            "obs_rank": observed_rank(obs_change, d) if has_position else math.nan,
            "median_model_change": median_change,
            "arrow_median_sign": _sign_glyph(median_change) if n else None,
            "pooled_ensemble_change": pooled_change,
            "arrow_pooled_sign": _sign_glyph(pooled_change),
            "sign_disagreement": bool(_sign(median_change) != _sign(pooled_change)) if n and not math.isnan(pooled_change) else False,
            "pooled_wilcoxon_p": pooled_p,
            "model_agreement_count": agreement,
            "expected_outside_fraction": 2.0 / (n + 1) if n else math.nan,
            "model_changes": tuple(float(c) for c in d),
        })
    return pd.DataFrame(rows)
