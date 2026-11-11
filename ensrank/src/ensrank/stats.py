"""Small statistical helpers, implemented with numpy alone.

The Wilcoxon rank-sum p-value follows the normal approximation with the tie
correction and the continuity correction, in the form R's ``wilcox.test``
uses with ``exact = FALSE`` and ``correct = TRUE``. This is the form the Wu
thesis programme's recompute layer used, and reproducing it here keeps the
package free of any dependency beyond numpy, pandas and matplotlib.
"""
from __future__ import annotations

import math

import numpy as np

__all__ = ["midranks", "wilcoxon_rank_sum"]


def midranks(values) -> np.ndarray:
    """Return the ranks of a one-dimensional array, averaging ranks within ties.

    Ranks are one-based: the smallest value receives rank 1, and a group of
    ``k`` tied values that would occupy consecutive ranks receives the mean of
    those ranks for every member of the group.
    """
    x = np.asarray(values, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sorted_x = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def wilcoxon_rank_sum(x, y, correct: bool = True) -> float:
    """Two-sided Wilcoxon rank-sum p-value for two independent samples.

    Missing values are dropped from each sample before ranking. The statistic
    is computed on midranks, the variance carries the standard tie correction,
    and the normal approximation applies the continuity correction unless
    ``correct`` is false. The result is ``math.nan`` when either sample is
    empty or when the tie-corrected variance is zero, which happens when every
    pooled value is tied.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return math.nan
    pooled = np.concatenate([x, y])
    ranks = midranks(pooled)
    w = ranks[:n1].sum() - n1 * (n1 + 1) / 2.0
    z = w - n1 * n2 / 2.0
    _, counts = np.unique(pooled, return_counts=True)
    n = n1 + n2
    tie_term = np.sum(counts ** 3 - counts) / (n * (n - 1))
    sigma = math.sqrt(n1 * n2 / 12.0 * ((n + 1) - tie_term))
    if sigma == 0:
        return math.nan
    correction = 0.5 * np.sign(z) if correct else 0.0
    zz = (z - correction) / sigma
    # Two-sided normal p-value: 2 * Phi(-|zz|), written with erfc for accuracy.
    return float(math.erfc(abs(zz) / math.sqrt(2.0)))
