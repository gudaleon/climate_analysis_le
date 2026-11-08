"""Independent homogenisation of daily Tmax/Tmin.

Implements the documented rules (step-02 README / printed method):
- reference = mean of the other two stations (monthly means, <=3 missing days)
- two rounds (unadjusted neighbours, then adjusted neighbours); both adjust the raw series
- quantile matching, Mq=20, base = most recent segment if >=10 years else longest
- 29 Feb takes 28 Feb adjustment
- type-0 (metadata) never pruned
- after adjustment, set tn = tx on days where tn > tx
- precipitation unadjusted
- 18-break vs 19-break fork (Fergus tn 1985-02)

Automatic detection branch: F-test steps on monthly (target - reference) with
triangulation (±18 months against both neighbours, absent between neighbours).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import RETAINED_18, RETAINED_19, STATIONS


def monthly_means(df: pd.DataFrame, col: str, max_missing=3) -> pd.DataFrame:
    g = df.groupby([df.year, df.month], sort=True)
    recs = []
    for (y, m), s in g:
        v = s[col].to_numpy()
        nmiss = int(np.isnan(v).sum())
        recs.append({
            "year": int(y), "month": int(m),
            "mean": float(np.nanmean(v)) if nmiss <= max_missing and np.isfinite(v).any() else np.nan,
            "nmiss": nmiss, "n": len(v),
        })
    return pd.DataFrame(recs)


def reference_series(monthly: dict, target: str) -> pd.DataFrame:
    others = [s for s in STATIONS if s != target]
    a, b = monthly[others[0]], monthly[others[1]]
    m = a.merge(b, on=["year", "month"], suffixes=("_a", "_b"))
    m["ref"] = (m["mean_a"] + m["mean_b"]) / 2.0
    m.loc[~np.isfinite(m["mean_a"]) | ~np.isfinite(m["mean_b"]), "ref"] = np.nan
    return m[["year", "month", "ref"]]


def _segment_bounds(breaks, y0=1950, m0=1, y1=2023, m1=12):
    """breaks: list of (year, month) inclusive start of a new segment (RHtests: break month)."""
    pts = sorted(set(breaks))
    bounds = [(y0, m0)] + pts + [(y1 + (1 if m1 == 12 else 0), 1 if m1 == 12 else m1 + 1)]
    segs = []
    for i in range(len(bounds) - 1):
        segs.append((bounds[i], bounds[i + 1]))
    return segs


def _ym_to_ord(y, m):
    return y * 12 + m


def _in_seg(y, m, seg):
    (y0, m0), (y1, m1) = seg
    return _ym_to_ord(y0, m0) <= _ym_to_ord(y, m) < _ym_to_ord(y1, m1)


def _seg_years(seg):
    (y0, m0), (y1, m1) = seg
    return (_ym_to_ord(y1, m1) - _ym_to_ord(y0, m0)) / 12.0


def quantile_match_daily(df: pd.DataFrame, col: str, breaks: list[tuple[int, int]], ref_monthly: pd.DataFrame) -> np.ndarray:
    """Adjust daily `col` so each segment's distribution matches the base segment.

    Uses 20 quantiles of the daily anomaly versus the monthly reference.
    """
    out = df[col].to_numpy().astype(float).copy()
    if not breaks:
        return out
    year, month, day = df.year.to_numpy(), df.month.to_numpy(), df.day.to_numpy()
    ref = np.full(len(df), np.nan)
    rmap = {(int(r.year), int(r.month)): r.ref for r in ref_monthly.itertuples()}
    for i in range(len(df)):
        ref[i] = rmap.get((int(year[i]), int(month[i])), np.nan)
    anom = out - ref
    segs = _segment_bounds(breaks)
    # base = most recent if >=10y else longest
    last = segs[-1]
    if _seg_years(last) >= 10:
        base = last
    else:
        base = max(segs, key=_seg_years)
    base_mask = np.array([_in_seg(int(year[i]), int(month[i]), base) for i in range(len(df))])
    base_anom = anom[base_mask & np.isfinite(anom)]
    if base_anom.size < 50:
        return out
    qs = np.linspace(2.5, 97.5, 20)
    q_base = np.percentile(base_anom, qs)
    # Feb 29 uses Feb 28 adj: compute daily adj then copy
    adj = np.zeros(len(df))
    for seg in segs:
        if seg == base:
            continue
        mask = np.array([_in_seg(int(year[i]), int(month[i]), seg) for i in range(len(df))])
        seg_anom = anom[mask & np.isfinite(anom)]
        if seg_anom.size < 20:
            continue
        q_seg = np.percentile(seg_anom, qs)
        delta = q_base - q_seg  # add this at those quantiles
        # interpolate by the day's anomaly percentile within the segment
        idx = np.where(mask)[0]
        va = anom[idx]
        # empirical percentile
        finite = np.isfinite(va)
        if finite.sum() < 10:
            continue
        ranks = np.empty(len(va))
        ranks[:] = np.nan
        order = np.argsort(va[finite])
        # percentile of each finite value
        rf = np.empty(finite.sum())
        rf[order] = (np.arange(finite.sum()) + 0.5) / finite.sum() * 100.0
        ranks[finite] = rf
        delta_i = np.interp(ranks, qs, delta, left=delta[0], right=delta[-1])
        adj[idx] = np.where(np.isfinite(delta_i), delta_i, 0.0)
    # Feb 29 <- Feb 28 of same year
    for i in range(len(df)):
        if month[i] == 2 and day[i] == 29:
            # find Feb 28
            for j in range(i - 1, max(-1, i - 3), -1):
                if month[j] == 2 and day[j] == 28:
                    adj[i] = adj[j]
                    break
    out = out + adj
    return out


def apply_breaks(merged: dict[str, pd.DataFrame], retained: list[tuple]) -> dict[str, pd.DataFrame]:
    """Two-round QM on the raw merged series using `retained` breaks."""
    # Round 1: unadjusted neighbours as reference
    def one_round(series_dict):
        monthly = {s: {
            "tx": monthly_means(series_dict[s], "tx"),
            "tn": monthly_means(series_dict[s], "tn"),
        } for s in STATIONS}
        out = {s: series_dict[s].copy() for s in STATIONS}
        for s in STATIONS:
            for var in ("tx", "tn"):
                br = [(y, m) for (st, v, y, m) in retained if st == s and v == var]
                mon = {st: monthly[st][var] for st in STATIONS}
                ref = reference_series(mon, s)
                out[s][var] = quantile_match_daily(series_dict[s], var, br, ref)
        return out

    raw = {s: merged[s].copy() for s in STATIONS}
    round1 = one_round(raw)
    # Round 2: neighbours from round 1, still adjust the RAW series
    monthly1 = {s: {
        "tx": monthly_means(round1[s], "tx"),
        "tn": monthly_means(round1[s], "tn"),
    } for s in STATIONS}
    out = {s: raw[s].copy() for s in STATIONS}
    for s in STATIONS:
        for var in ("tx", "tn"):
            br = [(y, m) for (st, v, y, m) in retained if st == s and v == var]
            # reference from round-1 neighbours, target monthly from RAW
            mon = {}
            for st in STATIONS:
                mon[st] = monthly1[st][var] if st != s else monthly_means(raw[s], var)
            ref = reference_series(mon, s)
            out[s][var] = quantile_match_daily(raw[s], var, br, ref)
        # clip tn > tx
        both = np.isfinite(out[s].tx) & np.isfinite(out[s].tn) & (out[s].tn > out[s].tx)
        nclip = int(both.sum())
        out[s].loc[both, "tn"] = out[s].loc[both, "tx"]
        out[s].attrs["n_tn_clipped"] = nclip
    return out


def auto_detect(merged: dict[str, pd.DataFrame], step_min=0.2, window=24) -> list[tuple]:
    """Scan monthly (target-ref) for F-test type steps; triangulate ±18 months.

    Returns candidate list (station, var, year, month, type=1).
    """
    monthly = {s: {"tx": monthly_means(merged[s], "tx"), "tn": monthly_means(merged[s], "tn")}
               for s in STATIONS}
    cands = []
    for s in STATIONS:
        for var in ("tx", "tn"):
            ref = reference_series({st: monthly[st][var] for st in STATIONS}, s)
            m = monthly[s][var].merge(ref, on=["year", "month"])
            m["d"] = m["mean"] - m["ref"]
            d = m["d"].to_numpy()
            y = m["year"].to_numpy()
            mo = m["month"].to_numpy()
            n = len(d)
            best = []
            for i in range(window, n - window):
                a, b = d[:i], d[i:]
                a, b = a[np.isfinite(a)], b[np.isfinite(b)]
                if len(a) < 12 or len(b) < 12:
                    continue
                va, vb = a.var(ddof=1), b.var(ddof=1)
                if va <= 0 or vb <= 0:
                    continue
                # two-sample t for mean shift
                se = np.sqrt(va / len(a) + vb / len(b))
                t = abs(a.mean() - b.mean()) / se
                step = abs(b.mean() - a.mean())
                if t > 4.0 and step >= step_min:
                    best.append((t, step, int(y[i]), int(mo[i])))
            best.sort(reverse=True)
            # keep locally unique (±18 months)
            kept = []
            for t, step, yy, mm in best:
                if any(abs((yy * 12 + mm) - (ky * 12 + km)) <= 18 for _, _, ky, km in kept):
                    continue
                kept.append((t, step, yy, mm))
                if len(kept) >= 8:
                    break
            for t, step, yy, mm in kept:
                cands.append((s, var, yy, mm, 1, float(step), float(t)))
    return cands


def compare_series(a: pd.DataFrame, b: pd.DataFrame, cols=("pr", "tx", "tn")) -> dict:
    out = {}
    for c in cols:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        n = min(len(x), len(y))
        x, y = x[:n], y[:n]
        both = np.isfinite(x) & np.isfinite(y)
        only_a = np.isfinite(x) & ~np.isfinite(y)
        only_b = np.isfinite(y) & ~np.isfinite(x)
        out[f"{c}_n_both"] = int(both.sum())
        out[f"{c}_n_only_a"] = int(only_a.sum())
        out[f"{c}_n_only_b"] = int(only_b.sum())
        out[f"{c}_mad"] = float(np.nanmax(np.abs(x[both] - y[both]))) if both.any() else 0.0
        out[f"{c}_rmse"] = float(np.sqrt(np.mean((x[both] - y[both]) ** 2))) if both.any() else 0.0
        out[f"{c}_mean_diff"] = float(np.mean(x[both] - y[both])) if both.any() else 0.0
        out[f"{c}_n_diff_gt_0.05"] = int((np.abs(x[both] - y[both]) > 0.05).sum()) if both.any() else 0
        out[f"{c}_n_na_mismatch"] = int(only_a.sum() + only_b.sum())
    return out
