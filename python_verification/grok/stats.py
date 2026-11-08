"""Wilcoxon, period medians, envelope (both forks), consensus, skill-vs-change."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm, fisher_exact, rankdata

from config import (
    ALL_INDICES, PERIODS, TEMP_INDICES, PREC_INDICES, MODELS, STATIONS,
    PROCESS_GROUPS,
)


def wilcoxon_r(x, y, exact=False, continuity=True, alternative="two-sided"):
    """R wilcox.test two-sample: midranks, asymptotic, continuity correction 0.5.

    Returns p-value (float) or np.nan if undefined (empty sample or all ties / zero sigma).
    Primary printed settings: exact=False, continuity=True, alternative='two-sided'.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    x = x[np.isfinite(x)]
    y = y[np.isfinite(y)]
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return np.nan
    ranks = rankdata(np.concatenate([x, y]), method="average")
    r1 = ranks[:n1]
    # Mann-Whitney U for sample x
    u = r1.sum() - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    n = n1 + n2
    _, counts = np.unique(np.concatenate([x, y]), return_counts=True)
    tie = np.sum(counts ** 3 - counts)
    sigma2 = n1 * n2 / 12.0 * ((n + 1) - (tie / (n * (n - 1)) if n > 1 else 0.0))
    if sigma2 <= 0:
        return np.nan
    sigma = np.sqrt(sigma2)
    z = u - mu
    if continuity:
        if z > 0:
            z -= 0.5
        elif z < 0:
            z += 0.5
    z = z / sigma
    if alternative == "two-sided":
        p = 2.0 * float(norm.sf(abs(z)))
    elif alternative == "greater":
        p = float(norm.sf(z))
    else:
        p = float(norm.cdf(z))
    return min(1.0, max(0.0, p))


def period_mask(years, name):
    lo, hi = PERIODS[name]
    return (years >= lo) & (years <= hi)


def period_values(annual: pd.DataFrame, index: str, period: str):
    y = annual.year.to_numpy()
    v = annual[index].to_numpy(float)
    m = period_mask(y, period) & np.isfinite(v)
    return v[m]


def period_median(annual, index, period):
    v = period_values(annual, index, period)
    return float(np.median(v)) if v.size else np.nan


def delta_medians(annual, index, p1, p2):
    m1, m2 = period_median(annual, index, p1), period_median(annual, index, p2)
    if np.isfinite(m1) and np.isfinite(m2):
        return m2 - m1, m1, m2
    return np.nan, m1, m2


def arrow_from_delta(delta, p, alpha=0.05):
    """Printed arrow rule: direction from period medians; dash if no change; shading from p<0.05."""
    if not np.isfinite(delta):
        return "n/a", False
    if delta > 0:
        d = "up"
    elif delta < 0:
        d = "down"
    else:
        d = "none"
    sig = bool(np.isfinite(p) and p < alpha)
    return d, sig


def classify_envelope_613(d_obs, d_models):
    """6.13: within envelope / magnitude bias / directional reversal vs ensemble MEDIAN."""
    d_models = np.asarray(d_models, float)
    d_models = d_models[np.isfinite(d_models)]
    if not np.isfinite(d_obs) or d_models.size == 0:
        return "unknown", np.nan, np.nan, np.nan
    dmin, dmax = float(d_models.min()), float(d_models.max())
    dmed = float(np.median(d_models))
    if dmin <= d_obs <= dmax:
        return "within", dmin, dmax, dmed
    # reversal if opposite sign to ensemble median; zero obs is not a reversal
    if d_obs != 0 and dmed != 0 and np.sign(d_obs) != np.sign(dmed):
        return "reversal_vs_median", dmin, dmax, dmed
    return "magnitude_bias", dmin, dmax, dmed


def classify_envelope_v7(d_obs, d_models):
    """v7 Test 2: Bounded / Unbounded / Sign reversal (opposite to EVERY model)."""
    d_models = np.asarray(d_models, float)
    d_models = d_models[np.isfinite(d_models)]
    if not np.isfinite(d_obs) or d_models.size == 0:
        return "unknown", np.nan, np.nan
    dmin, dmax = float(d_models.min()), float(d_models.max())
    if dmin <= d_obs <= dmax:
        return "Bounded", dmin, dmax
    # sign reversal: Δmin and Δmax share a sign opposite to obs
    if dmin > 0 and dmax > 0 and d_obs < 0:
        return "Sign reversal", dmin, dmax
    if dmin < 0 and dmax < 0 and d_obs > 0:
        return "Sign reversal", dmin, dmax
    return "Unbounded", dmin, dmax


def consensus_count(model_annuals: dict, index: str, p1: str, p2: str, k=8):
    """k of 10 models significant in the same direction (printed: 8 of 10)."""
    ups = downs = 0
    details = []
    for m, ann in model_annuals.items():
        d, m1, m2 = delta_medians(ann, index, p1, p2)
        v1 = period_values(ann, index, p1)
        v2 = period_values(ann, index, p2)
        p = wilcoxon_r(v1, v2)
        direction, sig = arrow_from_delta(d, p)
        details.append((m, d, p, direction, sig))
        if sig and direction == "up":
            ups += 1
        elif sig and direction == "down":
            downs += 1
    if ups >= k:
        return "up", ups, downs, details
    if downs >= k:
        return "down", ups, downs, details
    return "none", ups, downs, details


def pass_table(obs_ann, model_annuals, indices, periods=("Historical", "Present")):
    """Wilcoxon model vs obs per period; pass at p>=0.05. Returns nested dict."""
    out = {}
    for idx in indices:
        out[idx] = {}
        for per in periods:
            ov = period_values(obs_ann, idx, per)
            out[idx][per] = {}
            for m, ann in model_annuals.items():
                mv = period_values(ann, idx, per)
                p = wilcoxon_r(ov, mv)
                out[idx][per][m] = {"p": p, "pass": (p >= 0.05) if np.isfinite(p) else False, "nan": not np.isfinite(p)}
    return out


def pass_counts(ptable, indices, models=MODELS):
    rows = []
    for m in models:
        h = sum(1 for i in indices if ptable[i]["Historical"][m]["pass"])
        p = sum(1 for i in indices if ptable[i]["Present"][m]["pass"])
        rows.append({"model": m, "Historical": h, "Present": p, "cum": h + p})
    return pd.DataFrame(rows)


def pooled_period_values(model_annuals, index, period):
    chunks = [period_values(ann, index, period) for ann in model_annuals.values()]
    return np.concatenate(chunks) if chunks else np.array([])


def ensemble_stats(model_annuals, index, p1, p2):
    deltas = []
    meds = {per: [] for per in PERIODS}
    for m, ann in model_annuals.items():
        d, _, _ = delta_medians(ann, index, p1, p2)
        deltas.append(d)
        for per in PERIODS:
            meds[per].append(period_median(ann, index, per))
    deltas = np.asarray(deltas, float)
    pooled = {
        per: float(np.median(pooled_period_values(model_annuals, index, per)))
        if pooled_period_values(model_annuals, index, per).size else np.nan
        for per in PERIODS
    }
    model_meds = {per: np.asarray(meds[per], float) for per in PERIODS}
    return {
        "model_deltas": deltas,
        "ens_median_delta": float(np.nanmedian(deltas)),
        "ens_min_delta": float(np.nanmin(deltas)) if np.isfinite(deltas).any() else np.nan,
        "ens_max_delta": float(np.nanmax(deltas)) if np.isfinite(deltas).any() else np.nan,
        "pooled_median": pooled,
        "median_of_model_medians": {per: float(np.nanmedian(model_meds[per])) for per in PERIODS},
        "min_model_median": {per: float(np.nanmin(model_meds[per])) for per in PERIODS},
        "max_model_median": {per: float(np.nanmax(model_meds[per])) for per in PERIODS},
        "pooled_delta": (pooled[p2] - pooled[p1]) if np.isfinite(pooled[p1]) and np.isfinite(pooled[p2]) else np.nan,
    }


def monthly_quartile_value(monthly: pd.DataFrame, index: str, month: int, period: str, lower=False):
    lo, hi = PERIODS[period]
    v = monthly[(monthly.year >= lo) & (monthly.year <= hi) & (monthly.month == month)][index].to_numpy(float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return np.nan
    q = 25 if lower else 75
    return float(np.percentile(v, q))


def monthly_median_value(monthly, index, month, period):
    lo, hi = PERIODS[period]
    v = monthly[(monthly.year >= lo) & (monthly.year <= hi) & (monthly.month == month)][index].to_numpy(float)
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else np.nan


def monthly_wilcoxon(monthly, index, month, p1, p2):
    lo1, hi1 = PERIODS[p1]
    lo2, hi2 = PERIODS[p2]
    a = monthly[(monthly.year >= lo1) & (monthly.year <= hi1) & (monthly.month == month)][index].to_numpy(float)
    b = monthly[(monthly.year >= lo2) & (monthly.year <= hi2) & (monthly.month == month)][index].to_numpy(float)
    return wilcoxon_r(a, b)


def skill_vs_change(pass_by_station, env_v7_by_station, n_pass_skill=10):
    """2x2: skilful (>=10 of 20) vs bounded. Returns counts and Fisher p."""
    skill_b = skill_u = noskill_b = noskill_u = 0
    misjudged_keep_unbounded = 0
    misjudged_reject_bounded = 0
    for st in STATIONS:
        pt = pass_by_station[st]
        env = env_v7_by_station[st]
        for idx in ALL_INDICES:
            npass = 0
            for per in ("Historical", "Present"):
                for m in MODELS:
                    if pt[idx][per][m]["pass"]:
                        npass += 1
            skilful = npass >= n_pass_skill
            bounded = env[idx]["class"] == "Bounded"
            if skilful and bounded:
                skill_b += 1
            elif skilful and not bounded:
                skill_u += 1
                misjudged_keep_unbounded += 1
            elif (not skilful) and bounded:
                noskill_b += 1
                misjudged_reject_bounded += 1
            else:
                noskill_u += 1
    table = np.array([[skill_b, skill_u], [noskill_b, noskill_u]])
    _, p = fisher_exact(table, alternative="two-sided")
    return {
        "skill_bounded": skill_b,
        "skill_unbounded": skill_u,
        "noskill_bounded": noskill_b,
        "noskill_unbounded": noskill_u,
        "fisher_p": float(p),
        "misjudged": misjudged_keep_unbounded + misjudged_reject_bounded,
        "misjudged_keep_unbounded": misjudged_keep_unbounded,
        "misjudged_reject_bounded": misjudged_reject_bounded,
        "n": int(table.sum()),
    }


def process_confidence(env_v7_by_station, consensus_by_station):
    """v7 printed rules (V7-C192..195)."""
    results = {}
    for gname, idxs in PROCESS_GROUPS.items():
        # directional coherence: % of station-level results following the group pattern
        # We compute H->P, H->N, H->F coherence as % of (index,station) with the modal expected direction.
        # Bounding % of observed changes.
        n_obs = len(idxs) * 3
        n_bounded = 0
        n_reversal = 0
        n_zero = 0
        for idx in idxs:
            for st in STATIONS:
                cl = env_v7_by_station[st][idx]["class"]
                dobs = env_v7_by_station[st][idx]["d_obs"]
                if cl == "Bounded":
                    n_bounded += 1
                if cl == "Sign reversal":
                    n_reversal += 1
                if np.isfinite(dobs) and dobs == 0:
                    n_zero += 1
        bound_pct = 100.0 * n_bounded / n_obs if n_obs else np.nan
        # coherence per comparison using consensus direction of models? Printed: station-level results
        # following the pattern represented by the group. Use sign of observed H-P change vs group expectation.
        # Without running group-expected pattern empirically, compute pairwise agreement of observed signs.
        signs = []
        for idx in idxs:
            for st in STATIONS:
                dobs = env_v7_by_station[st][idx]["d_obs"]
                if np.isfinite(dobs) and dobs != 0:
                    signs.append(np.sign(dobs))
        if signs:
            modal = 1 if signs.count(1) >= signs.count(-1) else -1
            coh_hp = 100.0 * signs.count(modal) / (len(idxs) * 3)
        else:
            coh_hp = np.nan
        # High: coh>=80% in at least 2 of 3 comparisons (we only have H-P observed),
        # bound>=80%, no sign reversal, observed coh>=60% at every station.
        # We can fully evaluate bounding and reversals; future coherence uses consensus.
        has_rev = n_reversal >= 1
        if bound_pct < 60 or n_zero >= 0.5 * n_obs:
            rating = "Low"
        elif has_rev:
            rating = "Low"  # single sign reversal lowers a rating
        elif bound_pct >= 80 and coh_hp >= 80:
            rating = "High"
        else:
            rating = "Moderate"
        results[gname] = {
            "n": n_obs, "bounded": n_bounded, "bound_pct": bound_pct,
            "reversals": n_reversal, "zeros": n_zero, "coh_hp": coh_hp, "rating": rating,
        }
    return results
