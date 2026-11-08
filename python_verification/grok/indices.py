"""Independent ETCCDI / Climpact-style annual and monthly indices.

Printed settings used: base 1950-1986, wsdin=csdin=3, Tb_GDD=10, rxnday=3, txtn=3.
Percentile thresholds: 5-day window around each calendar day; Zhang (2005) leave-one-out
for years inside the base period. Heat/cold waves: Excess Heat/Cold Factor (EHF/ECF)
so that amplitude is in °C² as printed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    ALL_INDICES, BASE_YEARS, MAX_MISSING_ANNUAL, MAX_MISSING_MONTHLY,
    TEMP_INDICES, PREC_INDICES, WET_THRESH,
)

MISSING = np.nan


def _md_key(month, day):
    return month * 100 + day


def calendar_doy_mday(month, day):
    """Month-day key ignoring year; Feb 29 -> 228 (Feb 28)."""
    md = month * 100 + day
    md = np.where((month == 2) & (day == 29), 228, md)
    return md


def _running_mean(a, w):
    """Trailing/centered running mean with NaN if window incomplete. Centered, odd w."""
    a = np.asarray(a, float)
    n = len(a)
    out = np.full(n, np.nan)
    half = w // 2
    csum = np.concatenate([[0.0], np.cumsum(np.nan_to_num(a, nan=0.0))])
    cfin = np.concatenate([[0], np.cumsum(np.isfinite(a).astype(int))])
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        nf = cfin[hi] - cfin[lo]
        if nf == (hi - lo) and nf == w:
            out[i] = (csum[hi] - csum[lo]) / nf
        elif nf == (hi - lo) and nf >= w:  # edges: require full available span
            out[i] = (csum[hi] - csum[lo]) / nf
        elif nf == (hi - lo):
            out[i] = (csum[hi] - csum[lo]) / nf
    return out


def _spell_days(flag, min_len):
    """Count days that fall inside runs of True of length >= min_len. flag boolean, NaN -> False."""
    f = np.asarray(flag, dtype=bool)
    n = len(f)
    out = np.zeros(n, dtype=int)
    i = 0
    while i < n:
        if not f[i]:
            i += 1
            continue
        j = i
        while j < n and f[j]:
            j += 1
        if j - i >= min_len:
            out[i:j] = 1
        i = j
    return out


def _max_spell(flag):
    f = np.asarray(flag, dtype=bool)
    best = cur = 0
    for v in f:
        if v:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _max_run_sum(x, w):
    x = np.asarray(x, float)
    n = len(x)
    if n < w:
        return np.nan
    # NaN in window -> that window invalid
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(x, nan=0.0))])
    nf = np.concatenate([[0], np.cumsum(np.isfinite(x).astype(int))])
    best = -np.inf
    for i in range(n - w + 1):
        if nf[i + w] - nf[i] == w:
            s = c[i + w] - c[i]
            if s > best:
                best = s
    return best if best != -np.inf else np.nan


def _daylength_hours(lat_deg, month):
    """Monthly mean day length (hours) for Thornthwaite L correction."""
    # Approximate using day-of-year mid-month
    mid = [16, 45, 75, 105, 136, 166, 197, 228, 258, 289, 319, 350][month - 1]
    decl = 0.409 * np.sin(2 * np.pi * mid / 365 - 1.39)
    lat = np.deg2rad(lat_deg)
    ws = np.arccos(np.clip(-np.tan(lat) * np.tan(decl), -1, 1))
    return 24 / np.pi * ws


def thornthwaite_monthly_pet(tmean_by_month, lat, n_days):
    """tmean_by_month: array (n_months,) of monthly mean T; n_days same shape; returns PET mm/month."""
    t = np.asarray(tmean_by_month, float)
    nd = np.asarray(n_days, float)
    # heat index from the 12 calendar-month means of the year if possible; caller passes I
    return t  # placeholder, real fn below


def annual_heat_index(year_month_tmean):
    """I = sum over 12 months of (T/5)^1.514 for T>0. year_month_tmean length 12."""
    t = np.asarray(year_month_tmean, float)
    pos = np.clip(t, 0, None)
    return float(np.nansum((pos / 5.0) ** 1.514))


def pet_thornthwaite(t, I, lat, month, ndays):
    if not np.isfinite(t) or t <= 0 or I <= 0:
        return 0.0 if np.isfinite(t) and t <= 0 else np.nan
    a = (6.75e-7) * I ** 3 - (7.71e-5) * I ** 2 + (1.792e-2) * I + 0.49239
    L = _daylength_hours(lat, month)
    return 16.0 * ((10.0 * t) / I) ** a * (ndays / 30.0) * (L / 12.0)


def _gamma_cdf(x, shape, scale):
    from math import gamma as gfn
    # regularized lower gamma P(shape, x/scale) via scipy
    from scipy.special import gammainc
    if x <= 0:
        return 0.0
    return float(gammainc(shape, x / scale))


def _norm_ppf(p):
    from scipy.special import erfinv
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.sqrt(2) * erfinv(2 * p - 1)


def spi_from_monthly(pr_m, year_m, month_m, scale, base_lo=1950, base_hi=1986):
    """SPI at `scale` months. Gamma fit per calendar month on baseline rolling sums."""
    n = len(pr_m)
    roll = np.full(n, np.nan)
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(pr_m, nan=0.0))])
    nf = np.concatenate([[0], np.cumsum(np.isfinite(pr_m).astype(int))])
    for i in range(scale - 1, n):
        if nf[i + 1] - nf[i + 1 - scale] == scale:
            roll[i] = c[i + 1] - c[i + 1 - scale]
    spi = np.full(n, np.nan)
    for cal in range(1, 13):
        idx = np.where((month_m == cal) & np.isfinite(roll))[0]
        if len(idx) < 8:
            continue
        base = idx[(year_m[idx] >= base_lo) & (year_m[idx] <= base_hi)]
        vals = roll[base]
        vals = vals[np.isfinite(vals)]
        if len(vals) < 8:
            continue
        # probability of zero
        q = float(np.mean(vals == 0))
        pos = vals[vals > 0]
        if len(pos) < 4:
            continue
        # method of moments for gamma
        m = pos.mean()
        v = pos.var(ddof=1) if len(pos) > 1 else pos.var()
        if v <= 0 or m <= 0:
            continue
        shape = m * m / v
        scale_g = v / m
        for i in idx:
            x = roll[i]
            if not np.isfinite(x):
                continue
            if x == 0:
                p = q
            else:
                p = q + (1 - q) * _gamma_cdf(x, shape, scale_g)
            spi[i] = _norm_ppf(p)
    return spi


def spei_from_monthly(d_m, year_m, month_m, scale, base_lo=1950, base_hi=1986):
    """SPEI at `scale` months. Log-logistic (PWM) fit per calendar month on P-PET rolling sums."""
    n = len(d_m)
    roll = np.full(n, np.nan)
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(d_m, nan=0.0))])
    nf = np.concatenate([[0], np.cumsum(np.isfinite(d_m).astype(int))])
    for i in range(scale - 1, n):
        if nf[i + 1] - nf[i + 1 - scale] == scale:
            roll[i] = c[i + 1] - c[i + 1 - scale]
    spei = np.full(n, np.nan)
    for cal in range(1, 13):
        idx = np.where((month_m == cal) & np.isfinite(roll))[0]
        base = idx[(year_m[idx] >= base_lo) & (year_m[idx] <= base_hi)]
        vals = roll[base]
        vals = vals[np.isfinite(vals)]
        if len(vals) < 8:
            continue
        xs = np.sort(vals)
        nn = len(xs)
        # PWM unbiased
        w0 = xs.mean()
        w1 = np.sum((np.arange(nn) / (nn - 1)) * xs) / nn if nn > 1 else w0
        # Hosking log-logistic: beta, alpha, gamma
        # Following SPEI package approximation
        beta = (2 * w1 - w0) / (6 * w1 - w0 - 6 * (w0 - 2 * w1)) if (6 * w1 - w0 - 6 * (w0 - 2 * w1)) != 0 else np.nan
        # simpler 3-parameter log-logistic via PWM (Vicente-Serrano):
        # alpha, beta, gamma
        try:
            gamma = (2 * w1 - w0) / (6 * w1 - w0 - 6 * ((w0 - 2 * w1)))  # can be unstable
        except Exception:
            gamma = np.nan
        # Use a robust log-logistic: F = 1/(1+(alpha/(x-gamma))^beta) with gamma = min-eps
        loc = xs[0] - 0.01 * (xs[-1] - xs[0] + 1)
        y = xs - loc
        y = y[y > 0]
        if len(y) < 8:
            continue
        # fit log(y) ~ logistic via moments
        ly = np.log(y)
        mu = ly.mean()
        sd = ly.std(ddof=1) if len(ly) > 1 else ly.std()
        # logistic scale s = sd * sqrt(3)/pi
        s = sd * np.sqrt(3) / np.pi if sd > 0 else 1.0
        for i in idx:
            x = roll[i]
            if not np.isfinite(x):
                continue
            z = (np.log(max(x - loc, 1e-9)) - mu) / s
            # logistic cdf
            p = 1.0 / (1.0 + np.exp(-z))
            spei[i] = _norm_ppf(p)
    return spei


def _doy365(md):
    month = md // 100
    day = md % 100
    nd = np.array([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334])
    return np.clip(nd[month - 1] + day, 1, 365)


def _group_by_doy(values, doy, mask):
    """values[mask] grouped into list of arrays indexed 1..365."""
    v = values[mask]
    d = doy[mask]
    by = [np.empty(0, dtype=float) for _ in range(366)]
    if v.size == 0:
        return by
    order = np.argsort(d, kind="mergesort")
    d_s, v_s = d[order], v[order]
    splits = np.flatnonzero(d_s[1:] != d_s[:-1]) + 1
    starts = np.concatenate([[0], splits])
    ends = np.concatenate([splits, [d_s.size]])
    for a, b in zip(starts, ends):
        by[int(d_s[a])] = v_s[a:b]
    return by


def _pct_from_groups(by, q, window_days):
    out = np.full(366, np.nan)
    for d in range(1, 366):
        chunks = []
        for k in range(-window_days, window_days + 1):
            dd = ((d - 1 + k) % 365) + 1
            if by[dd].size:
                chunks.append(by[dd])
        if chunks:
            sample = np.concatenate(chunks)
            out[d] = np.percentile(sample, q)
    return out


def _base_day_percentiles(values, years, md, q, base_lo, base_hi, window_days=2, leave_year=None):
    doy = _doy365(md)
    in_base = (years >= base_lo) & (years <= base_hi) & np.isfinite(values)
    if leave_year is not None:
        in_base = in_base & (years != leave_year)
    by = _group_by_doy(values, doy, in_base)
    lut = _pct_from_groups(by, q, window_days)
    return lut, doy


def _apply_pct_threshold(values, years, md, q, base_lo, base_hi, window_days=2):
    """Return daily threshold series. Zhang leave-one-out inside base period."""
    lut_all, doy = _base_day_percentiles(values, years, md, q, base_lo, base_hi, window_days, None)
    in_base_years = np.unique(years[(years >= base_lo) & (years <= base_hi)])
    lut_by_year = {int(y): _base_day_percentiles(values, years, md, q, base_lo, base_hi, window_days, int(y))[0]
                   for y in in_base_years}
    thr = lut_all[doy]
    in_base = (years >= base_lo) & (years <= base_hi)
    for y, lut in lut_by_year.items():
        m = in_base & (years == y)
        thr[m] = lut[doy[m]]
    return thr


def _wetday_percentile(pr, years, q, base_lo, base_hi):
    """Single threshold from wet days in base period (R95p/R99p)."""
    wet = pr[(years >= base_lo) & (years <= base_hi) & np.isfinite(pr) & (pr >= WET_THRESH)]
    if wet.size < 10:
        return np.nan
    return float(np.percentile(wet, q))


def _ehf_series(tmean, years, md, base_lo, base_hi):
    """Excess Heat Factor. T95 from calendar-day 15-day window of Tmean in base period.
    T3 = 3-day mean, T30 = 30-day mean ending yesterday.
    EHF = EHI_sig * max(1, EHI_accl).
    """
    n = len(tmean)
    t95 = _apply_pct_threshold(tmean, years, md, 95, base_lo, base_hi, window_days=7)
    t3 = np.full(n, np.nan)
    t30 = np.full(n, np.nan)
    # 3-day mean ending today (days i-2,i-1,i)
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(tmean, nan=0.0))])
    nf = np.concatenate([[0], np.cumsum(np.isfinite(tmean).astype(int))])
    for i in range(n):
        if i >= 2 and nf[i + 1] - nf[i - 2] == 3:
            t3[i] = (c[i + 1] - c[i - 2]) / 3.0
        if i >= 32 and nf[i - 2] - nf[i - 32] == 30:
            t30[i] = (c[i - 2] - c[i - 32]) / 30.0
    ehi_sig = t3 - t95
    ehi_accl = t3 - t30
    ehf = ehi_sig * np.maximum(1.0, ehi_accl)
    return ehf


def _ecf_series(tmean, years, md, base_lo, base_hi):
    t05 = _apply_pct_threshold(tmean, years, md, 5, base_lo, base_hi, window_days=7)
    n = len(tmean)
    t3 = np.full(n, np.nan)
    t30 = np.full(n, np.nan)
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(tmean, nan=0.0))])
    nf = np.concatenate([[0], np.cumsum(np.isfinite(tmean).astype(int))])
    for i in range(n):
        if i >= 2 and nf[i + 1] - nf[i - 2] == 3:
            t3[i] = (c[i + 1] - c[i - 2]) / 3.0
        if i >= 32 and nf[i - 2] - nf[i - 32] == 30:
            t30[i] = (c[i - 2] - c[i - 32]) / 30.0
    eci_sig = t05 - t3  # positive when colder than 5th
    eci_accl = t30 - t3
    ecf = -(eci_sig * np.maximum(1.0, eci_accl))  # signed negative for cold
    return ecf


def _hw_metrics(ehf, years):
    """HWA = peak EHF of hottest heatwave (NA if none); HWF = days in heatwaves of >=3d EHF>0."""
    flag = np.isfinite(ehf) & (ehf > 0)
    in_hw = _spell_days(flag, 3)
    hwa, hwf = {}, {}
    for y in np.unique(years):
        m = years == y
        days = in_hw[m]
        vals = ehf[m]
        hwf[int(y)] = int(days.sum())
        if days.any() and np.isfinite(vals[days.astype(bool)]).any():
            hwa[int(y)] = float(np.nanmax(vals[days.astype(bool)]))
        else:
            hwa[int(y)] = np.nan
    return hwa, hwf


def _cw_metrics(ecf, years):
    """CWA = peak (most negative) ECF of coldest cold-wave; CWF = days in >=3d ECF<0 spells."""
    flag = np.isfinite(ecf) & (ecf < 0)
    in_cw = _spell_days(flag, 3)
    cwa, cwf = {}, {}
    for y in np.unique(years):
        m = years == y
        days = in_cw[m]
        vals = ecf[m]
        cwf[int(y)] = int(days.sum())
        if days.any() and np.isfinite(vals[days.astype(bool)]).any():
            cwa[int(y)] = float(np.nanmin(vals[days.astype(bool)]))
        else:
            cwa[int(y)] = np.nan
    return cwa, cwf


def _gsl(tmean, month, day):
    """NH growing season: first 6d Tmean>5 to first 6d Tmean<5 after 1 July. Days."""
    n = len(tmean)
    warm = np.isfinite(tmean) & (tmean > 5.0)
    cold = np.isfinite(tmean) & (tmean < 5.0)
    start = None
    run = 0
    for i in range(n):
        if warm[i]:
            run += 1
            if run >= 6:
                start = i - 5
                break
        else:
            run = 0
    if start is None:
        return np.nan
    # after July 1
    july = None
    for i in range(n):
        if month[i] == 7 and day[i] == 1:
            july = i
            break
    if july is None:
        july = start
    run = 0
    end = None
    for i in range(max(july, start + 6), n):
        if cold[i]:
            run += 1
            if run >= 6:
                end = i - 5  # first day of the cold spell
                break
        else:
            run = 0
    if end is None:
        end = n
    return float(end - start)


def compute_annual(df: pd.DataFrame, lat: float, clip_tn_to_tx: bool = False) -> pd.DataFrame:
    """Return annual index table, one row per year, columns = ALL_INDICES plus n_days, n_missing_*."""
    year = df.year.to_numpy().astype(int)
    month = df.month.to_numpy().astype(int)
    day = df.day.to_numpy().astype(int)
    pr = df.pr.to_numpy().astype(float)
    tx = df.tx.to_numpy().astype(float)
    tn = df.tn.to_numpy().astype(float)
    if clip_tn_to_tx:
        both = np.isfinite(tx) & np.isfinite(tn) & (tn > tx)
        tn = tn.copy()
        tn[both] = tx[both]
    tmean = (tx + tn) / 2.0
    dtr = tx - tn
    md = calendar_doy_mday(month, day)
    years = np.unique(year)
    base_lo, base_hi = BASE_YEARS

    tx90 = _apply_pct_threshold(tx, year, md, 90, base_lo, base_hi)
    tx10 = _apply_pct_threshold(tx, year, md, 10, base_lo, base_hi)
    tn90 = _apply_pct_threshold(tn, year, md, 90, base_lo, base_hi)
    tn10 = _apply_pct_threshold(tn, year, md, 10, base_lo, base_hi)
    tx50 = _apply_pct_threshold(tx, year, md, 50, base_lo, base_hi)
    p95 = _wetday_percentile(pr, year, 95, base_lo, base_hi)
    p99 = _wetday_percentile(pr, year, 99, base_lo, base_hi)

    ehf = _ehf_series(tmean, year, md, base_lo, base_hi)
    ecf = _ecf_series(tmean, year, md, base_lo, base_hi)
    hwa, hwf = _hw_metrics(ehf, year)
    cwa, cwf = _cw_metrics(ecf, year)

    wsdi6 = _spell_days(np.isfinite(tx) & np.isfinite(tx90) & (tx > tx90), 6)
    wsdi3 = _spell_days(np.isfinite(tx) & np.isfinite(tx90) & (tx > tx90), 3)
    csdi6 = _spell_days(np.isfinite(tn) & np.isfinite(tn10) & (tn < tn10), 6)
    csdi3 = _spell_days(np.isfinite(tn) & np.isfinite(tn10) & (tn < tn10), 3)
    compound = _spell_days(
        np.isfinite(tx) & np.isfinite(tn) & np.isfinite(tx90) & np.isfinite(tn90) & (tx > tx90) & (tn > tn90),
        3,
    )

    rows = []
    for y in years:
        m = year == y
        n_days = int(m.sum())
        pr_y, tx_y, tn_y = pr[m], tx[m], tn[m]
        tm_y, dtr_y = tmean[m], dtr[m]
        mo_y, dy_y = month[m], day[m]
        miss_pr = int(np.isnan(pr_y).sum())
        miss_tx = int(np.isnan(tx_y).sum())
        miss_tn = int(np.isnan(tn_y).sum())
        miss_tm = int((~np.isfinite(tm_y)).sum())
        ok_t = miss_tx <= MAX_MISSING_ANNUAL and miss_tn <= MAX_MISSING_ANNUAL
        ok_pr = miss_pr <= MAX_MISSING_ANNUAL
        ok_tm = miss_tm <= MAX_MISSING_ANNUAL

        def cnt(cond, ok):
            return float(np.nansum(cond)) if ok else np.nan

        wet = np.isfinite(pr_y) & (pr_y >= WET_THRESH)
        rec = {"year": int(y), "n_days": n_days, "miss_pr": miss_pr, "miss_tx": miss_tx, "miss_tn": miss_tn}

        rec["PRCPTOT"] = float(np.nansum(pr_y[wet])) if ok_pr else np.nan
        rec["R10mm"] = cnt(np.isfinite(pr_y) & (pr_y >= 10), ok_pr)
        rec["R20mm"] = cnt(np.isfinite(pr_y) & (pr_y >= 20), ok_pr)
        rec["RX1day"] = float(np.nanmax(pr_y)) if ok_pr and np.isfinite(pr_y).any() else np.nan
        rec["RX3day"] = _max_run_sum(pr_y, 3) if ok_pr else np.nan
        rec["RX5day"] = _max_run_sum(pr_y, 5) if ok_pr else np.nan
        nwet = int(wet.sum())
        rec["SDII"] = (rec["PRCPTOT"] / nwet) if ok_pr and nwet > 0 else np.nan
        rec["R95p"] = float(np.nansum(pr_y[wet & (pr_y > p95)])) if ok_pr and np.isfinite(p95) else np.nan
        rec["R99p"] = float(np.nansum(pr_y[wet & (pr_y > p99)])) if ok_pr and np.isfinite(p99) else np.nan
        rec["R95pTOT"] = (100.0 * rec["R95p"] / rec["PRCPTOT"]) if ok_pr and rec["PRCPTOT"] not in (0, np.nan) and rec["PRCPTOT"] else np.nan
        rec["R99pTOT"] = (100.0 * rec["R99p"] / rec["PRCPTOT"]) if ok_pr and rec["PRCPTOT"] not in (0, np.nan) and rec["PRCPTOT"] else np.nan
        if rec.get("PRCPTOT") == 0:
            rec["R95pTOT"] = np.nan
            rec["R99pTOT"] = np.nan
        rec["CDD"] = float(_max_spell(np.isfinite(pr_y) & (pr_y < WET_THRESH))) if ok_pr else np.nan
        rec["CWD"] = float(_max_spell(wet)) if ok_pr else np.nan

        rec["FD"] = cnt(np.isfinite(tn_y) & (tn_y < 0), ok_t)
        rec["ID"] = cnt(np.isfinite(tx_y) & (tx_y < 0), ok_t)
        rec["SU"] = cnt(np.isfinite(tx_y) & (tx_y > 25), ok_t)
        rec["TR"] = cnt(np.isfinite(tn_y) & (tn_y > 20), ok_t)
        rec["TXge30"] = cnt(np.isfinite(tx_y) & (tx_y >= 30), ok_t)
        rec["TNltm20"] = cnt(np.isfinite(tn_y) & (tn_y < -20), ok_t)
        rec["DTRgt15"] = cnt(np.isfinite(dtr_y) & (dtr_y > 15), ok_t)
        rec["TNn"] = float(np.nanmin(tn_y)) if ok_t and np.isfinite(tn_y).any() else np.nan
        rec["TNx"] = float(np.nanmax(tn_y)) if ok_t and np.isfinite(tn_y).any() else np.nan
        rec["TXn"] = float(np.nanmin(tx_y)) if ok_t and np.isfinite(tx_y).any() else np.nan
        rec["TXx"] = float(np.nanmax(tx_y)) if ok_t and np.isfinite(tx_y).any() else np.nan
        rec["TXm"] = float(np.nanmean(tx_y)) if ok_t else np.nan
        rec["TNm"] = float(np.nanmean(tn_y)) if ok_t else np.nan
        rec["TMm"] = float(np.nanmean(tm_y)) if ok_tm else np.nan
        rec["DTR"] = float(np.nanmean(dtr_y)) if ok_t else np.nan
        rec["GDDgrow10"] = float(np.nansum(np.clip(tm_y - 10.0, 0, None))) if ok_tm else np.nan
        rec["GSL"] = _gsl(tm_y, mo_y, dy_y) if ok_tm else np.nan

        rec["WSDI6"] = float(wsdi6[m].sum()) if ok_t else np.nan
        rec["WSDI3"] = float(wsdi3[m].sum()) if ok_t else np.nan
        rec["CSDI6"] = float(csdi6[m].sum()) if ok_t else np.nan
        rec["CSDI3"] = float(csdi3[m].sum()) if ok_t else np.nan
        rec["TXb3TNb3"] = float(compound[m].sum()) if ok_t else np.nan

        nfin_tx = np.isfinite(tx_y) & np.isfinite(tx90[m])
        nfin_tn = np.isfinite(tn_y) & np.isfinite(tn10[m])
        rec["TX90p"] = 100.0 * np.mean(tx_y[nfin_tx] > tx90[m][nfin_tx]) if ok_t and nfin_tx.any() else np.nan
        rec["TX10p"] = 100.0 * np.mean(tx_y[nfin_tx] < tx10[m][nfin_tx]) if ok_t and nfin_tx.any() else np.nan
        rec["TN90p"] = 100.0 * np.mean(tn_y[nfin_tn] > tn90[m][nfin_tn]) if ok_t and nfin_tn.any() else np.nan
        rec["TN10p"] = 100.0 * np.mean(tn_y[nfin_tn] < tn10[m][nfin_tn]) if ok_t and nfin_tn.any() else np.nan
        nfin50 = np.isfinite(tx_y) & np.isfinite(tx50[m])
        rec["TXgt50p"] = 100.0 * np.mean(tx_y[nfin50] > tx50[m][nfin50]) if ok_t and nfin50.any() else np.nan

        rec["HWA"] = hwa.get(int(y), np.nan) if ok_tm else np.nan
        rec["HWF"] = float(hwf.get(int(y), np.nan)) if ok_tm else np.nan
        rec["CWA"] = cwa.get(int(y), np.nan) if ok_tm else np.nan
        rec["CWF"] = float(cwf.get(int(y), np.nan)) if ok_tm else np.nan
        rows.append(rec)

    out = pd.DataFrame(rows).sort_values("year")
    for c in ALL_INDICES:
        if c not in out.columns:
            out[c] = np.nan
    return out


def compute_monthly(df: pd.DataFrame, lat: float, clip_tn_to_tx: bool = False) -> pd.DataFrame:
    """Monthly values of the 14-index subset plus helper fields."""
    year = df.year.to_numpy().astype(int)
    month = df.month.to_numpy().astype(int)
    day = df.day.to_numpy().astype(int)
    pr = df.pr.to_numpy().astype(float)
    tx = df.tx.to_numpy().astype(float)
    tn = df.tn.to_numpy().astype(float)
    if clip_tn_to_tx:
        both = np.isfinite(tx) & np.isfinite(tn) & (tn > tx)
        tn = tn.copy()
        tn[both] = tx[both]
    tmean = (tx + tn) / 2.0

    # monthly CDD: dry spell counted in the month it ends
    dry = np.isfinite(pr) & (pr < WET_THRESH)
    # track current dry spell length and ending month
    # We'll compute max dry-spell-ending-this-month length
    n = len(pr)
    spell_end_len = np.zeros(n, dtype=int)
    cur = 0
    for i in range(n):
        if dry[i]:
            cur += 1
        else:
            if cur > 0 and i > 0:
                spell_end_len[i - 1] = cur
            cur = 0
    if cur > 0:
        spell_end_len[n - 1] = cur

    keys = list(zip(year.tolist(), month.tolist()))
    uniq = []
    seen = set()
    for k in keys:
        if k not in seen:
            seen.add(k)
            uniq.append(k)

    recs = []
    tmean_ym = {}
    pr_ym = {}
    nd_ym = {}
    for y, mo in uniq:
        m = (year == y) & (month == mo)
        n_days = int(m.sum())
        miss_pr = int(np.isnan(pr[m]).sum())
        miss_tx = int(np.isnan(tx[m]).sum())
        miss_tn = int(np.isnan(tn[m]).sum())
        ok_pr = miss_pr <= MAX_MISSING_MONTHLY
        ok_t = miss_tx <= MAX_MISSING_MONTHLY and miss_tn <= MAX_MISSING_MONTHLY
        pr_m, tx_m, tn_m, tm_m = pr[m], tx[m], tn[m], tmean[m]
        wet = np.isfinite(pr_m) & (pr_m >= WET_THRESH)
        rec = {"year": y, "month": mo}
        rec["PRCPTOT"] = float(np.nansum(pr_m[wet])) if ok_pr else np.nan
        rec["R10mm"] = float(np.nansum(np.isfinite(pr_m) & (pr_m >= 10))) if ok_pr else np.nan
        rec["RX1day"] = float(np.nanmax(pr_m)) if ok_pr and np.isfinite(pr_m).any() else np.nan
        rec["RX5day"] = _max_run_sum(pr_m, 5) if ok_pr else np.nan
        rec["TMm"] = float(np.nanmean(tm_m)) if ok_t else np.nan
        rec["TXx"] = float(np.nanmax(tx_m)) if ok_t and np.isfinite(tx_m).any() else np.nan
        rec["TXn"] = float(np.nanmin(tx_m)) if ok_t and np.isfinite(tx_m).any() else np.nan
        rec["ID"] = float(np.nansum(np.isfinite(tx_m) & (tx_m < 0))) if ok_t else np.nan
        rec["SU"] = float(np.nansum(np.isfinite(tx_m) & (tx_m > 25))) if ok_t else np.nan
        # CDD: max dry-spell length among spells that END in this month
        ends = spell_end_len[m]
        rec["CDD"] = float(ends.max()) if ok_pr and ends.size else (0.0 if ok_pr else np.nan)
        recs.append(rec)
        tmean_ym[(y, mo)] = rec["TMm"]
        pr_ym[(y, mo)] = rec["PRCPTOT"] if np.isfinite(rec["PRCPTOT"]) else 0.0
        nd_ym[(y, mo)] = n_days

    # Thornthwaite PET and SPI/SPEI on the monthly series in order
    recs.sort(key=lambda r: (r["year"], r["month"]))
    t_arr = np.array([r["TMm"] for r in recs], float)
    p_arr = np.array([r["PRCPTOT"] if np.isfinite(r["PRCPTOT"]) else np.nan for r in recs], float)
    y_arr = np.array([r["year"] for r in recs], int)
    mo_arr = np.array([r["month"] for r in recs], int)
    nd_arr = np.array([nd_ym[(r["year"], r["month"])] for r in recs], float)

    pet = np.full(len(recs), np.nan)
    for i, r in enumerate(recs):
        # heat index from the 12 months of this year in baseline-like way: use this year's 12 months
        y = r["year"]
        t12 = []
        for mo in range(1, 13):
            t12.append(tmean_ym.get((y, mo), np.nan))
        I = annual_heat_index(t12)
        pet[i] = pet_thornthwaite(t_arr[i], I, lat, r["month"], nd_arr[i])
    d_arr = p_arr - pet
    spi3 = spi_from_monthly(p_arr, y_arr, mo_arr, 3)
    spi6 = spi_from_monthly(p_arr, y_arr, mo_arr, 6)
    spei3 = spei_from_monthly(d_arr, y_arr, mo_arr, 3)
    spei6 = spei_from_monthly(d_arr, y_arr, mo_arr, 6)
    for i, r in enumerate(recs):
        r["SPI3"] = spi3[i]
        r["SPI6"] = spi6[i]
        r["SPEI3"] = spei3[i]
        r["SPEI6"] = spei6[i]
        r["PET"] = pet[i]
    return pd.DataFrame(recs)
